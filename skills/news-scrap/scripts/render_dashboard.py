#!/usr/bin/env python3
"""주간 뉴스 대시보드 HTML 렌더러.

Usage:
  python render_dashboard.py <input_json_path> <output_html_path> [template_path]

입력 JSON 예시:
  {
    "시작일": "2026년 3월 21일(토)",
    "종료일": "2026년 3월 27일(금)",
    "생성일": "2026년 3월 27일",
    "국내기사": [...],
    "해외기사": [...],
    "주간요약": {
      "핵심동향": ["..."],
      "주목할기관/기업": ["..."],
      "시사점": "..."
    }
  }
"""

from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR.parent / "templates" / "dashboard.html"
TAG_CLASS_MAP = {"연구": "tag-연구", "도입": "tag-도입", "정책": "tag-정책", "트렌드": "tag-트렌드"}
DETAIL_KEYS = [
    ("관련 기업/기관", ("관련 기업/기관", "related_orgs")),
    ("기술/제품", ("기술/제품", "tech_product")),
    ("핵심 수치", ("핵심 수치", "key_metrics")),
    ("연구 방법/결과", ("연구 방법/결과", "research_method")),
]


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _escape_text(value: object) -> str:
    text = str(value or "").strip()
    return html.escape(text).replace("\n", "<br />")


def _extract_articles(payload: dict, *keys: str) -> list[dict]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _extract_summary(payload: dict) -> dict:
    summary = payload.get("주간요약") or payload.get("summary") or {}
    if isinstance(summary, dict):
        return summary
    return {}


def _summary_items(summary: dict, *keys: str) -> list[str]:
    for key in keys:
        value = summary.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    return []


def _summary_text(summary: dict, *keys: str) -> str:
    for key in keys:
        value = summary.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _article_summary(article: dict) -> str:
    for key in ("기사요약", "article_summary", "summary", "핵심내용"):
        value = article.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "원문 미확보"


def _article_details(article: dict) -> list[tuple[str, str]]:
    details = article.get("세부분석") or article.get("detail") or {}
    rows: list[tuple[str, str]] = []

    if isinstance(details, dict):
        for label, aliases in DETAIL_KEYS:
            for alias in aliases:
                value = details.get(alias)
                if isinstance(value, str) and value.strip():
                    rows.append((label, value.strip()))
                    break

    for label, aliases in DETAIL_KEYS:
        if any(existing_label == label for existing_label, _ in rows):
            continue
        for alias in aliases:
            value = article.get(alias)
            if isinstance(value, str) and value.strip():
                rows.append((label, value.strip()))
                break

    return rows


def _build_detail_block(article: dict) -> str:
    rows = _article_details(article)
    if not rows:
        return ""

    items = []
    for label, value in rows:
        items.append(f"<dt>{_escape_text(label)}</dt><dd>{_escape_text(value)}</dd>")

    return (
        '        <div class="article-detail">\n'
        "          <h4>세부 분석</h4>\n"
        "          <dl>\n"
        f"            {' '.join(items)}\n"
        "          </dl>\n"
        "        </div>\n"
    )


def _build_article(article: dict) -> str:
    title = _escape_text(article.get("제목", "제목 미상"))
    category = str(article.get("구분", "트렌드")).strip() or "트렌드"
    category_class = TAG_CLASS_MAP.get(category, "tag-트렌드")
    field = _escape_text(article.get("활용분야", "미분류"))
    date = _escape_text(article.get("날짜", "날짜 미상"))
    source = _escape_text(article.get("기관매체", "출처 미상"))
    related = _escape_text(article.get("관련기관", ""))
    source_line = source if not related else f"{source} · {related}"
    summary = _escape_text(_article_summary(article))
    detail_block = _build_detail_block(article)
    link = str(article.get("링크", "")).strip()

    link_block = ""
    if link:
        safe_link = html.escape(link, quote=True)
        link_block = (
            '        <div class="link">\n'
            f'          <a href="{safe_link}" target="_blank" rel="noreferrer">원문 보기 &rarr;</a>\n'
            "        </div>\n"
        )

    return f"""<details class="article">
  <summary>
    <span class="title">{title}</span>
    <span class="meta">
      <span class="tag {category_class}">{_escape_text(category)}</span>
      <span class="tag tag-field">{field}</span>
      <span class="date">{date}</span>
    </span>
  </summary>
  <div class="article-body">
    <div class="source">{source_line}</div>
    <div class="article-summary">{summary}</div>
{detail_block}{link_block}  </div>
</details>"""


def _build_article_list(articles: list[dict]) -> str:
    if not articles:
        return '<div class="empty-notice">수집된 기사가 없습니다.</div>'
    return "\n\n".join(_build_article(article) for article in articles)


def _build_list_items(items: list[str], empty_message: str) -> str:
    if not items:
        items = [empty_message]
    return "\n".join(f"          <li>{_escape_text(item)}</li>" for item in items)


def _replace_markers(template: str, replacements: dict[str, str]) -> str:
    result = template
    for marker, value in replacements.items():
        result = result.replace(marker, value)
    return result


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python render_dashboard.py <input_json_path> <output_html_path> [template_path]")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    template_path = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else DEFAULT_TEMPLATE

    payload = _read_json(input_path)
    template = template_path.read_text(encoding="utf-8")

    domestic_articles = _extract_articles(payload, "국내기사", "domestic_articles")
    overseas_articles = _extract_articles(payload, "해외기사", "해외논문", "overseas_articles")
    summary = _extract_summary(payload)

    replacements = {
        "{시작일}": str(payload.get("시작일", "")).strip(),
        "{시작일(월)}": str(payload.get("시작일", "")).strip(),
        "{종료일}": str(payload.get("종료일", "")).strip(),
        "{종료일(일)}": str(payload.get("종료일", "")).strip(),
        "{오늘 날짜}": str(payload.get("생성일", "")).strip(),
        "{총건수}": str(len(domestic_articles) + len(overseas_articles)),
        "{국내건수}": str(len(domestic_articles)),
        "{해외건수}": str(len(overseas_articles)),
        "<!--DOMESTIC_ARTICLES-->": _build_article_list(domestic_articles),
        "<!--OVERSEAS_ARTICLES-->": _build_article_list(overseas_articles),
        "<!--SUMMARY_TRENDS-->": _build_list_items(
            _summary_items(summary, "핵심동향", "이번 주 핵심 동향", "trends"),
            "이번 주 핵심 동향이 없습니다.",
        ),
        "<!--SUMMARY_FEATURED_ORGS-->": _build_list_items(
            _summary_items(summary, "주목할기관/기업", "주목기관", "featured_orgs"),
            "주목할 기관 정보가 없습니다.",
        ),
        "<!--SUMMARY_IMPLICATIONS-->": _escape_text(
            _summary_text(summary, "시사점", "implications") or "시사점이 없습니다."
        ),
    }

    rendered = _replace_markers(template, replacements)

    os.makedirs(output_path.parent, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
