#!/usr/bin/env python3
"""Build a Pencil MCP slide specification from a selected article."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_SECTIONS = (
    ("국내기사", ("국내기사", "domestic_articles")),
    ("해외기사", ("해외기사", "overseas_articles")),
)
REQUIRED_RESEARCH_SECTIONS = (
    "이번 주 핵심 팩트",
    "AI 기술 설명",
    "회사·기관 팩트시트",
    "이번 주 인사이트",
)
MAX_TEMPLATE_BULLETS = 6
MAX_TEMPLATE_SOURCES = 3
SLIDE_DEFINITIONS = (
    {
        "id": "core_facts",
        "section": "이번 주 핵심 팩트",
        "layout": "headline_fact_grid",
        "visual": "핵심 팩트 3개와 발표·도입·제휴 관계를 보여주는 2열 표 또는 간단한 관계도",
    },
    {
        "id": "ai_technology",
        "section": "AI 기술 설명",
        "layout": "workflow_diagram",
        "visual": "입력 데이터 -> AI 처리 -> 현장 활용 흐름도",
    },
    {
        "id": "company_fact_sheet",
        "section": "회사·기관 팩트시트",
        "layout": "fact_sheet",
        "visual": "역할, 제품·역량, 파트너·도입, 검증 상태를 나누는 팩트시트",
    },
    {
        "id": "weekly_insight",
        "section": "이번 주 인사이트",
        "layout": "insight_summary",
        "visual": "시사점, 주의점, 불확실성, 추적 신호를 구분하는 요약 표",
    },
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


def normalize_week_id(value: str) -> str:
    match = re.search(
        r"(?P<year>\d{2})년[_\s-]*(?P<month>\d{1,2})월[_\s-]*(?P<week>\d{1,2})주차",
        str(value or ""),
    )
    if not match:
        return ""
    return f"{match.group('year')}년_{int(match.group('month'))}월_{int(match.group('week'))}주차"


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


def parse_research_sections(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"심층 리서치 파일을 찾지 못했습니다: {path}")
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise SystemExit(f"심층 리서치 파일이 비어 있습니다: {path}")

    heading_pattern = re.compile(r"^##\s*(?:\d+[\.\)]\s*)?(.+?)\s*$", re.MULTILINE)
    matches = list(heading_pattern.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()

    missing = [section for section in REQUIRED_RESEARCH_SECTIONS if section not in sections]
    if missing:
        raise SystemExit(
            "featured_research.md 구조 검증 실패: "
            f"{path}에 다음 섹션이 없습니다: {', '.join(missing)}"
        )
    return sections


def compact_points(text: str, limit: int = 7) -> list[str]:
    points: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if not line or line in {"소스에서 확인 안 됨:", "확인 필요:"}:
            continue
        points.append(line)
        if len(points) >= limit:
            break
    return points


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]>\"']+", text or "")
    seen: set[str] = set()
    unique_urls = []
    for url in urls:
        cleaned = url.rstrip(".,")
        if cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)
    return unique_urls[:6]


def public_selection_reason(featured: dict) -> str:
    reason = str(featured.get("reason", "")).strip()
    if reason and not re.search(r"(총점|점수|score|\d+\s*점)", reason, re.IGNORECASE):
        return reason
    title = str(featured.get("title", "대표 기사")).strip() or "대표 기사"
    return (
        f"{title}은 의료 AI 관련성, AI 역할, 현장 적용 맥락, 소스 완결성을 "
        "내부 검토한 결과 주간 대표 기사로 선정되었다."
    )


def build_featured_meta(featured: dict, article: dict, section: str) -> dict:
    return {
        "title": featured.get("title") or article_title(article),
        "original_title": featured.get("original_title") or get_text(article, "원제목", "original_title"),
        "media": featured.get("media") or get_text(article, "기관/매체", "매체", "media"),
        "date": featured.get("date") or get_text(article, "날짜", "date"),
        "section": featured.get("section") or section,
        "related_org": featured.get("related_org") or get_text(article, "관련기관", "related_org", "organization"),
        "domain": featured.get("domain") or get_text(article, "적용분야", "domain"),
        "category": featured.get("category") or get_text(article, "구분", "category"),
        "link": featured.get("link") or get_text(article, "링크", "link", "url"),
        "selection_reason": public_selection_reason(featured),
    }


def build_slides(featured_meta: dict, sections: dict[str, str]) -> list[dict]:
    slides = []
    for number, definition in enumerate(SLIDE_DEFINITIONS, start=1):
        section_title = definition["section"]
        section_text = sections[section_title]
        slide_title = featured_meta["title"] if number == 1 else section_title
        slides.append(
            {
                "number": number,
                "id": definition["id"],
                "title": slide_title,
                "section_title": section_title,
                "layout": definition["layout"],
                "visual_directive": definition["visual"],
                "body": section_text,
                "bullets": compact_points(section_text),
                "source_urls": extract_urls(section_text),
            }
        )
    return slides


def value_at(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    return ""


def build_template_slots(
    *,
    featured_meta: dict,
    slides: list[dict],
    week_id: str,
    period: dict,
) -> dict[str, str]:
    slots = {
        "slot.deck.week_id": week_id,
        "slot.deck.period": " ~ ".join(
            value for value in (period.get("start_date", ""), period.get("end_date", "")) if value
        ),
        "slot.deck.generated_date": period.get("generated_date", ""),
        "slot.article.title": featured_meta.get("title", ""),
        "slot.article.media": featured_meta.get("media", ""),
        "slot.article.date": featured_meta.get("date", ""),
        "slot.article.org": featured_meta.get("related_org", ""),
        "slot.article.domain": featured_meta.get("domain", ""),
        "slot.article.category": featured_meta.get("category", ""),
        "slot.article.link": featured_meta.get("link", ""),
        "slot.article.selection_reason": featured_meta.get("selection_reason", ""),
    }

    for slide in slides:
        number = int(slide["number"])
        prefix = f"slot.slide{number}"
        bullets = [str(item) for item in slide.get("bullets", [])]
        sources = [str(item) for item in slide.get("source_urls", [])]
        slots[f"{prefix}.section"] = str(slide.get("section_title", ""))
        slots[f"{prefix}.title"] = str(slide.get("title", ""))
        slots[f"{prefix}.layout"] = str(slide.get("layout", ""))
        slots[f"{prefix}.visual"] = str(slide.get("visual_directive", ""))
        slots[f"{prefix}.body"] = str(slide.get("body", ""))
        for index in range(MAX_TEMPLATE_BULLETS):
            slots[f"{prefix}.bullet{index + 1}"] = value_at(bullets, index)
        for index in range(MAX_TEMPLATE_SOURCES):
            slots[f"{prefix}.source{index + 1}"] = value_at(sources, index)
    return slots


def build_spec(
    *,
    verified: dict,
    featured_meta: dict,
    research_sections: dict[str, str],
    week_id: str,
) -> dict:
    period = {
        "start_date": get_text(verified, "시작일", "start_date"),
        "end_date": get_text(verified, "종료일", "end_date"),
        "generated_date": get_text(verified, "생성일", "generated_date"),
    }
    slides = build_slides(featured_meta, research_sections)
    return {
        "schema_version": "1.0",
        "generator": "news-scrap-codex-v2/scripts/build_pencil_slide_spec.py",
        "week_id": week_id,
        "period": period,
        "output": {
            "pdf_filename": f"news_slide_{week_id}.pdf",
        },
        "template": {
            "mode": "replace_named_text_slots",
            "recommended_template_name": "news-scrap-codex-v2 pencil slide template",
            "slot_name_pattern": "^slot\\.",
            "required_slide_frame_names": [
                "template.slide1.core_facts",
                "template.slide2.ai_technology",
                "template.slide3.company_fact_sheet",
                "template.slide4.weekly_insight",
            ],
            "export_frame_names": [
                "template.slide1.core_facts",
                "template.slide2.ai_technology",
                "template.slide3.company_fact_sheet",
                "template.slide4.weekly_insight",
            ],
        },
        "canvas": {
            "width": 1280,
            "height": 720,
            "slide_count": 4,
        },
        "style": {
            "background": "#FFFFFF",
            "text": "#1F2933",
            "muted_text": "#56616F",
            "accent": "#155EEF",
            "accent_secondary": "#0E9384",
            "line": "#D9E2EC",
            "font": "Inter",
        },
        "source_policy": {
            "language": "ko",
            "use_only_verified_facts": True,
            "exclude_internal_scores": True,
            "exclude_candidate_rankings": True,
            "mark_unknowns_as_unverified": True,
            "output_format": "pdf_only",
        },
        "featured_article": featured_meta,
        "template_slots": build_template_slots(
            featured_meta=featured_meta,
            slides=slides,
            week_id=week_id,
            period=period,
        ),
        "slides": slides,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("verified_json")
    parser.add_argument("featured_article_json")
    parser.add_argument("output_dir")
    parser.add_argument("--research-md", required=True)
    parser.add_argument("--week-id", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    verified_path = Path(args.verified_json).resolve()
    featured_path = Path(args.featured_article_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    verified = load_json(verified_path)
    featured = load_json(featured_path)
    section, article = find_featured_article(verified, featured)
    research_sections = parse_research_sections(Path(args.research_md).resolve())

    week_id = (
        normalize_week_id(args.week_id)
        or normalize_week_id(output_dir.name)
        or normalize_week_id(output_dir.parent.name)
    )
    if not week_id:
        week_id = normalize_week_id(verified_path.stem.replace("verified_articles_", ""))
    if not week_id:
        raise SystemExit("주차 ID를 확인하지 못했습니다. --week-id 또는 주차명이 포함된 output_dir를 사용하세요.")

    featured_meta = build_featured_meta(featured, article, section)
    spec = build_spec(
        verified=verified,
        featured_meta=featured_meta,
        research_sections=research_sections,
        week_id=week_id,
    )

    output_path = Path(args.output).resolve() if args.output else output_dir / "pencil_slide_spec.json"
    output_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
