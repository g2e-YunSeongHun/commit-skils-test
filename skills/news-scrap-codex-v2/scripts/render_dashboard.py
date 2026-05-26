#!/usr/bin/env python3
"""Render the weekly HTML dashboard for a news-scrap-codex run."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR.parent / "templates" / "dashboard.html"
TAG_CLASS_MAP = {
    "도입/제휴": "tag-deploy",
    "정책": "tag-policy",
    "기술/제품": "tag-trend",
}
WEEK_ID_RE = re.compile(r"(?P<year>\d{2})년[_\s-]*(?P<month>\d{1,2})월[_\s-]*(?P<week>\d{1,2})주차")
KOREAN_TEXT_KEYS = (
    "요약",
    "한국어요약",
    "한글요약",
    "번역요약",
    "summary_ko",
    "korean_summary",
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def esc(value: object) -> str:
    return html.escape(str(value or "").strip())


def get_text(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def count_hangul(text: str) -> int:
    return len(re.findall(r"[가-힣]", text or ""))


def count_latin_words(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z][A-Za-z-]{2,}\b", text or ""))


def looks_korean_summary(text: str) -> bool:
    hangul_count = count_hangul(text)
    latin_words = count_latin_words(text)
    if hangul_count >= 20:
        return True
    return hangul_count >= 10 and latin_words <= 6


def strip_citations(text: str) -> str:
    return re.sub(r"\[[0-9,\s]+\]", "", text or "")


def strip_markdown(text: str) -> str:
    cleaned = re.sub(r"[*_`]+", "", text or "")
    cleaned = cleaned.replace("###", "").replace("##", "").replace("#", "")
    return cleaned


def strip_article_label(text: str) -> str:
    cleaned = strip_markdown(text)
    cleaned = re.sub(r"^\s*(?:기사|article)\s*\d+\s*[:.]\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def normalize_whitespace(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    normalized = re.sub(r"\s+([.,!?])", r"\1", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    return normalized


def clean_summary_text(text: str) -> str:
    return normalize_whitespace(strip_article_label(strip_citations(text)))


def split_sentences(text: str) -> list[str]:
    cleaned = clean_summary_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def first_sentences(text: str, max_sentences: int = 4, max_chars: int = 700) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "요약 정보가 없습니다."
    snippet = " ".join(sentences[:max_sentences]).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    return snippet


def collect_articles(verified: dict) -> tuple[list[dict], list[dict]]:
    domestic = verified.get("국내기사")
    if not isinstance(domestic, list):
        domestic = []

    overseas = verified.get("해외기사")
    if not isinstance(overseas, list):
        overseas = []

    return domestic, overseas


def get_article_title(article: dict) -> str:
    return (
        get_text(article, "번역제목", "translated_title", "제목", "title")
        or "제목 미상"
    )


def get_article_original_title(article: dict) -> str:
    translated = get_article_title(article)
    original = get_text(article, "원제목", "original_title")
    if original and original != translated:
        return original
    title = get_text(article, "제목", "title")
    if title and title != translated:
        return title
    return ""


def get_article_summary(article: dict) -> str:
    summary = get_text(article, *KOREAN_TEXT_KEYS, "summary")
    if summary:
        return first_sentences(summary, max_sentences=4, max_chars=700)
    return first_sentences(get_text(article, "본문", "body", "content"), max_sentences=4, max_chars=700)


def validate_summary_language(section: str, article: dict, summary: str) -> None:
    if section != "해외기사":
        return
    if looks_korean_summary(summary):
        return
    title = get_article_title(article)
    raise SystemExit(
        "HTML 요약 한국어 검증 실패: "
        f"해외기사 '{title}'의 대시보드 요약이 한국어로 보이지 않습니다. "
        "Codex가 원문 요약을 한국어로 번역하고 자연스러운 문장으로 다듬은 뒤 "
        "`요약` 또는 `summary_ko` 필드에 저장해야 합니다."
    )


def render_article(article: dict, section: str) -> str:
    title = esc(get_article_title(article))
    original_title = get_article_original_title(article)
    original_block = ""
    if original_title:
        original_block = f'    <div class="source">원제: {esc(original_title)}</div>\n'

    category = get_text(article, "구분", "category") or "동향"
    category_class = TAG_CLASS_MAP.get(category, "tag-trend")
    domain = esc(get_text(article, "적용분야", "domain") or "미분류")
    date = esc(get_text(article, "날짜", "date") or "날짜 미상")
    source = esc(get_text(article, "기관/매체", "매체", "media") or "출처 미상")
    related = esc(get_text(article, "관련기관", "related_org", "organization"))
    source_line = source if not related else f"{source} · {related}"

    summary = clean_summary_text(get_article_summary(article))
    validate_summary_language(section, article, summary)

    link = get_text(article, "링크", "link", "url")
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
      <span class="tag {category_class}">{esc(category)}</span>
      <span class="tag tag-field">{domain}</span>
      <span class="date">{date}</span>
    </span>
  </summary>
  <div class="article-body">
    <div class="source">{source_line}</div>
{original_block}    <div class="article-summary">{esc(summary)}</div>
{link_block}  </div>
</details>"""


def build_article_list(articles: list[dict], section: str) -> str:
    if not articles:
        return '<div class="empty-notice">수집된 기사가 없습니다.</div>'
    return "\n\n".join(render_article(article, section) for article in articles)


def render_template(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered


def resolve_template_path(extra_args: list[str]) -> Path:
    for raw_arg in extra_args:
        candidate = Path(raw_arg).resolve()
        if candidate.suffix.lower() in {".html", ".htm"}:
            return candidate
    return DEFAULT_TEMPLATE


def normalize_week_id(value: str) -> str:
    match = WEEK_ID_RE.search(str(value or ""))
    if not match:
        return ""
    return f"{match.group('year')}년_{int(match.group('month'))}월_{int(match.group('week'))}주차"


def normalize_news_output_path(output_path: Path) -> Path:
    week_id = normalize_week_id(output_path.stem) or normalize_week_id(output_path.parent.name)
    if not week_id:
        return output_path
    return output_path.with_name(f"news_{week_id}.html")


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: python render_dashboard.py <verified_json> <output_html_path> [template_path]"
        )
        sys.exit(1)

    verified_path = Path(sys.argv[1]).resolve()
    output_path = normalize_news_output_path(Path(sys.argv[2]).resolve())
    template_path = resolve_template_path(sys.argv[3:])

    verified = load_json(verified_path)
    template = template_path.read_text(encoding="utf-8")

    domestic_articles, overseas_articles = collect_articles(verified)

    replacements = {
        "{{page_title}}": "의료 AI 주간 브리핑",
        "{{period}}": f'{esc(get_text(verified, "시작일"))} ~ {esc(get_text(verified, "종료일"))}',
        "{{generated_date}}": esc(get_text(verified, "생성일")),
        "{{total_count}}": str(len(domestic_articles) + len(overseas_articles)),
        "{{domestic_count}}": str(len(domestic_articles)),
        "{{overseas_count}}": str(len(overseas_articles)),
        "{{domestic_articles}}": build_article_list(domestic_articles, "국내기사"),
        "{{overseas_articles}}": build_article_list(overseas_articles, "해외기사"),
    }

    rendered = render_template(template, replacements)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
