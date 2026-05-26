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
    "이번 주 대표 기사",
    "제품 및 기술 설명",
    "회사 및 기관 소개",
    "기사 요약",
)
SLIDE_DEFINITIONS = (
    {
        "id": "featured_article",
        "section": "이번 주 대표 기사",
        "frame_name": "template.slide1",
        "content_frame_name": "content.slide1",
        "layout": "article_overview",
        "visual": "대표 기사 제목, 매체, 날짜, 관련기관, 선정 이유가 보이는 요약 카드",
    },
    {
        "id": "product_technology",
        "section": "제품 및 기술 설명",
        "frame_name": "template.slide2",
        "content_frame_name": "content.slide2",
        "layout": "workflow_diagram",
        "visual": "제품이나 기술이 해결하는 문제, 입력, 처리, 결과, 현장 사용 흐름",
    },
    {
        "id": "company_institution",
        "section": "회사 및 기관 소개",
        "frame_name": "template.slide3",
        "content_frame_name": "content.slide3",
        "layout": "organization_profile",
        "visual": "회사와 기관의 역할, 제품·역량, 파트너십·도입 상태를 나누는 소개",
    },
    {
        "id": "article_summary",
        "section": "기사 요약",
        "frame_name": "template.slide4",
        "content_frame_name": "content.slide4",
        "layout": "article_summary",
        "visual": "기사의 배경, 주요 내용, 의료 현장 의미, 한줄 정리를 자연스럽게 정리",
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
        if re.match(r"^제목\s*[:：]", line):
            continue
        if not line:
            continue
        points.append(line)
        if len(points) >= limit:
            break
    return points


def parse_labeled_points(text: str) -> list[dict[str, str]]:
    points: list[dict[str, str]] = []
    for point in compact_points(text, limit=12):
        match = re.match(r"^([^:：]{1,30})\s*[:：]\s*(.+)$", point)
        if match:
            label = match.group(1).strip()
            value = match.group(2).strip()
            if value:
                points.append({"label": label, "text": value})
        elif point:
            points.append({"label": "", "text": point})
    return points


def find_labeled(points: list[dict[str, str]], *labels: str) -> str:
    normalized_labels = {normalize(label) for label in labels}
    for point in points:
        if normalize(point.get("label", "")) in normalized_labels:
            return point.get("text", "")
    return ""


def remaining_labeled(
    points: list[dict[str, str]],
    used_labels: set[str],
    *,
    limit: int = 6,
) -> list[str]:
    used = {normalize(label) for label in used_labels}
    items: list[str] = []
    for point in points:
        label = point.get("label", "")
        text = point.get("text", "")
        if not text or normalize(label) in used:
            continue
        items.append(f"{label}: {text}" if label else text)
        if len(items) >= limit:
            break
    return items


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


def build_slide_blocks(number: int, featured_meta: dict, section_text: str) -> list[dict]:
    points = parse_labeled_points(section_text)
    if number == 1:
        return [
            {"type": "headline", "text": featured_meta.get("title", "")},
            {
                "type": "meta",
                "items": [
                    item
                    for item in [
                        featured_meta.get("media", ""),
                        featured_meta.get("date", ""),
                        featured_meta.get("related_org", ""),
                        featured_meta.get("domain", ""),
                    ]
                    if item
                ],
            },
            {
                "type": "callout",
                "label": "선정 이유",
                "text": featured_meta.get("selection_reason", ""),
            },
            {
                "type": "cards",
                "items": remaining_labeled(points, {"대표 기사", "선정 이유", "근거"}, limit=3),
            },
        ]
    if number == 2:
        flow = [
            {"label": "입력", "text": find_labeled(points, "입력 데이터")},
            {"label": "처리", "text": find_labeled(points, "처리 방식", "AI 처리")},
            {"label": "결과", "text": find_labeled(points, "출력 결과")},
            {"label": "현장", "text": find_labeled(points, "현장 workflow 연결", "현장 연결")},
        ]
        return [
            {
                "type": "summary",
                "label": "제품·기술",
                "text": find_labeled(points, "제품·기술", "제품 및 기술") or featured_meta.get("domain", ""),
            },
            {
                "type": "summary",
                "label": "해결하려는 문제",
                "text": find_labeled(points, "해결하려는 의료 문제"),
            },
            {"type": "flow", "items": [item for item in flow if item["text"]]},
            {
                "type": "bullets",
                "items": remaining_labeled(
                    points,
                    {"제품·기술", "제품 및 기술", "해결하려는 의료 문제", "입력 데이터", "처리 방식", "AI 처리", "출력 결과", "현장 workflow 연결", "현장 연결", "근거"},
                    limit=4,
                ),
            },
        ]
    if number == 3:
        return [
            {
                "type": "headline",
                "text": find_labeled(points, "회사·기관", "회사", "기관") or featured_meta.get("related_org", ""),
            },
            {
                "type": "cards",
                "items": remaining_labeled(points, {"회사·기관", "회사", "기관", "근거"}, limit=6),
            },
        ]
    return [
        {"type": "narrative", "label": "배경", "text": find_labeled(points, "배경")},
        {"type": "narrative", "label": "주요 내용", "text": find_labeled(points, "주요 내용")},
        {"type": "narrative", "label": "의료 현장 의미", "text": find_labeled(points, "의료 현장 의미")},
        {"type": "takeaway", "text": find_labeled(points, "한줄 정리")},
    ]


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
        slide_title = section_title
        slides.append(
            {
                "number": number,
                "id": definition["id"],
                "title": slide_title,
                "section_title": section_title,
                "layout": definition["layout"],
                "visual_directive": definition["visual"],
                "frame_name": definition["frame_name"],
                "content_frame_name": definition["content_frame_name"],
                "body": section_text,
                "bullets": compact_points(section_text),
                "blocks": build_slide_blocks(number, featured_meta, section_text),
                "source_urls": extract_urls(section_text),
            }
        )
    return slides


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
            "mode": "populate_content_frames",
            "recommended_template_name": "news-scrap-codex-v2 pencil slide template",
            "required_slide_frame_names": [
                "template.slide1",
                "template.slide2",
                "template.slide3",
                "template.slide4",
            ],
            "export_frame_names": [
                "template.slide1",
                "template.slide2",
                "template.slide3",
                "template.slide4",
            ],
            "content_frame_names": [
                "content.slide1",
                "content.slide2",
                "content.slide3",
                "content.slide4",
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
