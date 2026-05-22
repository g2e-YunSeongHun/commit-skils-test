#!/usr/bin/env python3
"""Build a single NotebookLM source for slide-deck generation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_SECTIONS = (
    ("국내기사", ("국내기사", "domestic_articles")),
    ("해외기사", ("해외기사", "overseas_articles")),
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def get_text(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize(text: str) -> str:
    return "".join(re.findall(r"[0-9A-Za-z가-힣]+", str(text or ""))).lower()


def slugify(value: str) -> str:
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", value)
    slug = "_".join(tokens).strip("_")
    return slug[:80] or "featured_deck_source"


def get_articles(payload: dict) -> list[tuple[str, dict]]:
    articles: list[tuple[str, dict]] = []
    for section_label, keys in ARTICLE_SECTIONS:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                articles.extend((section_label, item) for item in value if isinstance(item, dict))
                break
    return articles


def article_title(article: dict) -> str:
    return get_text(article, "번역제목", "translated_title", "제목", "title") or "제목 미상"


def find_featured_article(verified: dict, featured: dict) -> tuple[str, dict]:
    featured_link = get_text(featured, "link", "링크", "url")
    featured_title = normalize(get_text(featured, "title", "제목"))
    for section, article in get_articles(verified):
        article_link = get_text(article, "링크", "link", "url")
        if featured_link and article_link == featured_link:
            return section, article
        article_titles = [
            article_title(article),
            get_text(article, "제목", "title"),
            get_text(article, "원제목", "original_title"),
        ]
        if featured_title and any(normalize(title) == featured_title for title in article_titles):
            return section, article
    raise SystemExit("featured_article.json에 해당하는 기사를 verified_articles.json에서 찾지 못했습니다.")


def read_optional_text(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value).resolve()
    if not path.exists():
        raise SystemExit(f"심층 리서치 파일을 찾지 못했습니다: {path}")
    return path.read_text(encoding="utf-8-sig").strip()


def format_scores(featured: dict) -> str:
    scores = featured.get("score_breakdown")
    if not isinstance(scores, dict):
        return "점수 정보 없음"
    labels = {
        "emergency_relevance": "응급의료 직접성",
        "ai_role": "AI 역할 명확성",
        "field_impact": "도입/검증/제품화 구체성",
        "source_completeness": "소스 완결성",
        "briefing_fit": "주간 대표성",
    }
    lines = []
    for key, label in labels.items():
        value = scores.get(key)
        if isinstance(value, (int, float)):
            lines.append(f"- {label}: {value}/20")
    return "\n".join(lines) if lines else "점수 정보 없음"


def format_candidate_comparison(selection_report: dict) -> str:
    candidates = selection_report.get("candidates")
    if not isinstance(candidates, list):
        return "후보 비교 정보 없음"
    lines = []
    for candidate in candidates[:4]:
        if not isinstance(candidate, dict):
            continue
        limitations = candidate.get("limitations")
        limitation_text = ", ".join(limitations) if isinstance(limitations, list) and limitations else "주요 약점 없음"
        lines.append(
            f"- {candidate.get('rank')}. {candidate.get('title')} / "
            f"{candidate.get('media')} / {candidate.get('score')}점 / {limitation_text}"
        )
    return "\n".join(lines) if lines else "후보 비교 정보 없음"


def build_source_text(
    *,
    verified: dict,
    featured: dict,
    selection_report: dict,
    section: str,
    article: dict,
    research_text: str,
) -> str:
    body = get_text(article, "본문", "body", "content")
    research_block = research_text or "추가 심층 리서치 자료가 제공되지 않았습니다."
    evidence = featured.get("selection_evidence")
    evidence_text = json.dumps(evidence, ensure_ascii=False, indent=2) if isinstance(evidence, dict) else "근거 정보 없음"
    limitations = featured.get("limitations")
    limitation_text = ", ".join(limitations) if isinstance(limitations, list) and limitations else "명시된 한계 없음"

    return f"""# NotebookLM 슬라이드 생성용 소스

이 소스는 Codex가 검색, 검증, 요약, 룰베이스 대표 기사 선정, 심층 리서치를 수행한 뒤 NotebookLM slide-deck 생성을 위해 제공하는 단일 자료다.
NotebookLM은 새 대표 기사를 고르거나 추가 리서치를 수행하지 말고, 이 소스와 slide_prompt 가이드에 근거해 슬라이드만 생성한다.

## 주간 범위

- 시작일: {get_text(verified, "시작일", "start_date") or "미상"}
- 종료일: {get_text(verified, "종료일", "end_date") or "미상"}
- 생성일: {get_text(verified, "생성일", "generated_date") or "미상"}

## 대표 기사 메타데이터

- 제목: {featured.get("title") or article_title(article)}
- 원제목: {featured.get("original_title") or get_text(article, "원제목", "original_title") or "없음"}
- 매체: {featured.get("media") or get_text(article, "기관/매체", "매체", "media") or "미상"}
- 날짜: {featured.get("date") or get_text(article, "날짜", "date") or "미상"}
- 섹션: {featured.get("section") or section}
- 관련 기관/회사: {featured.get("related_org") or get_text(article, "관련기관", "related_org", "organization") or "미상"}
- 적용 분야: {featured.get("domain") or get_text(article, "적용분야", "domain") or "미상"}
- 구분: {featured.get("category") or get_text(article, "구분", "category") or "미상"}
- 링크: {featured.get("link") or get_text(article, "링크", "link", "url") or "미상"}

## Codex 룰베이스 선정 결과

선정 이유: {featured.get("reason") or "선정 이유 없음"}
총점: {featured.get("score", "미상")}

기준별 점수:
{format_scores(featured)}

기준별 근거:
{evidence_text}

한계:
{limitation_text}

후보 비교:
{format_candidate_comparison(selection_report)}

## Codex 심층 리서치

{research_block}

## 대표 기사 원문

{body or "본문 없음"}
""".strip() + "\n"


def build_manifest(week_id: str, notebook_title: str, source_path: Path, featured: dict) -> dict:
    return {
        "week_id": week_id,
        "notebook_title": notebook_title,
        "source_dir": str(source_path.parent.resolve()),
        "sources": [
            {
                "title": source_path.stem,
                "file_path": str(source_path.resolve()),
                "section": featured.get("section", "대표기사"),
                "article_title": featured.get("title", "대표 기사"),
                "date": featured.get("date", ""),
                "link": featured.get("link", ""),
                "source_kind": "featured_deck_source",
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("verified_json")
    parser.add_argument("featured_article_json")
    parser.add_argument("output_dir")
    parser.add_argument("--selection-report", default="")
    parser.add_argument("--research-md", default="")
    parser.add_argument("--week-id", default="")
    parser.add_argument("--notebook-title", default="")
    args = parser.parse_args()

    verified_path = Path(args.verified_json).resolve()
    featured_path = Path(args.featured_article_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    source_dir = output_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    verified = load_json(verified_path)
    featured = load_json(featured_path)
    selection_report = load_json(Path(args.selection_report).resolve()) if args.selection_report else {}
    section, article = find_featured_article(verified, featured)
    research_text = read_optional_text(args.research_md)

    source_name = f"featured_{slugify(str(featured.get('title') or article_title(article)))}.txt"
    source_path = source_dir / source_name
    source_path.write_text(
        build_source_text(
            verified=verified,
            featured=featured,
            selection_report=selection_report,
            section=section,
            article=article,
            research_text=research_text,
        ),
        encoding="utf-8",
    )

    default_week_id = (
        output_dir.name
        if verified_path.stem == "verified_articles"
        else verified_path.stem.replace("verified_articles_", "")
    )
    week_id = args.week_id.strip() or default_week_id
    notebook_title = args.notebook_title.strip() or f"응급의료_AI_대표기사_슬라이드_{week_id}"
    manifest = build_manifest(week_id, notebook_title, source_path, featured)
    manifest_path = output_dir / "notebook_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE:{manifest_path}")


if __name__ == "__main__":
    main()
