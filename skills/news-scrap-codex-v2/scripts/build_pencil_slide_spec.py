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
        "layout": "featured_article_scaffold",
    },
    {
        "id": "product_technology",
        "section": "제품 및 기술 설명",
        "frame_name": "template.slide2",
        "content_frame_name": "content.slide2",
        "layout": "product_technology_scaffold",
    },
    {
        "id": "company_institution",
        "section": "회사 및 기관 소개",
        "frame_name": "template.slide3",
        "content_frame_name": "content.slide3",
        "layout": "organization_profile_scaffold",
    },
    {
        "id": "article_summary",
        "section": "기사 요약",
        "frame_name": "template.slide4",
        "content_frame_name": "content.slide4",
        "layout": "article_summary_scaffold",
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
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", str(text or "")).lower()


def normalize_week_id(value: str) -> str:
    match = re.search(
        r"(?P<year>\d{2})년?[_\s-]*(?P<month>\d{1,2})월?[_\s-]*(?P<week>\d{1,2})주차",
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
        raise SystemExit(f"리서치 파일을 찾지 못했습니다: {path}")
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise SystemExit(f"리서치 파일이 비어 있습니다: {path}")

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


def parse_labeled_points(text: str) -> list[dict[str, str]]:
    points: list[dict[str, str]] = []
    current_key = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            current_key = ""
            continue
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        match = re.match(r"^([^:：]{1,40})\s*[:：]\s*(.*)$", line)
        if match:
            label = match.group(1).strip()
            value = match.group(2).strip()
            points.append({"label": label, "text": value})
            current_key = label
            continue
        if current_key and points:
            points[-1]["text"] = f"{points[-1]['text']} {line}".strip()
        else:
            points.append({"label": "", "text": line})
    return points


def find_labeled(points: list[dict[str, str]], *labels: str) -> str:
    normalized_labels = {normalize(label) for label in labels}
    for point in points:
        if normalize(point.get("label", "")) in normalized_labels:
            return point.get("text", "").strip()
    return ""


def first_non_empty(*values: str) -> str:
    for value in values:
        if str(value or "").strip():
            return str(value).strip()
    return ""


def source_line(featured_meta: dict) -> str:
    parts = [
        featured_meta.get("media", ""),
        featured_meta.get("date", ""),
        featured_meta.get("link", ""),
    ]
    return " · ".join(part for part in parts if part)


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


def compact_points(text: str, limit: int = 7) -> list[str]:
    points: list[str] = []
    for point in parse_labeled_points(text):
        label = point.get("label", "")
        body = point.get("text", "")
        if not body:
            continue
        points.append(f"{label}: {body}" if label else body)
        if len(points) >= limit:
            break
    return points


def pair(points: list[dict[str, str]], title_key: str, detail_key: str, fallback_title: str = "") -> tuple[str, str]:
    title = find_labeled(points, title_key, f"{title_key} 제목") or fallback_title
    detail = find_labeled(points, detail_key, f"{title_key} 설명", f"{detail_key} 설명")
    return title, detail


def build_template_bindings(featured_meta: dict, sections: dict[str, str]) -> dict[str, str]:
    s1 = parse_labeled_points(sections["이번 주 대표 기사"])
    s2 = parse_labeled_points(sections["제품 및 기술 설명"])
    s3 = parse_labeled_points(sections["회사 및 기관 소개"])
    s4 = parse_labeled_points(sections["기사 요약"])

    bindings = {
        "bind.s1.category": first_non_empty(featured_meta.get("category", ""), featured_meta.get("domain", ""), "의료 AI"),
        "bind.s1.headline": first_non_empty(find_labeled(s1, "기사 제목", "대표 기사"), featured_meta.get("title", "")),
        "bind.s1.dek": first_non_empty(find_labeled(s1, "부제", "한 줄 요약", "한줄 요약"), featured_meta.get("selection_reason", "")),
        "bind.s1.body": find_labeled(s1, "요약 본문", "확인된 내용", "주요 내용"),
        "bind.s1.point1": find_labeled(s1, "핵심 포인트 1", "포인트 1"),
        "bind.s1.point2": find_labeled(s1, "핵심 포인트 2", "포인트 2"),
        "bind.s1.point3": find_labeled(s1, "핵심 포인트 3", "포인트 3"),
        "bind.s1.visual_note": f"출처: {source_line(featured_meta)}",
        "bind.s2.product_name": find_labeled(s2, "제품·기술", "제품 및 기술", "제품명", "기술명"),
        "bind.s2.one_liner": find_labeled(s2, "한 줄 소개", "한줄 소개", "해결하려는 의료 문제"),
        "bind.s2.description": find_labeled(s2, "설명", "제품 설명", "기술 설명"),
        "bind.s2.step1": first_non_empty(find_labeled(s2, "작동 단계 1"), find_labeled(s2, "입력 데이터")),
        "bind.s2.step2": first_non_empty(find_labeled(s2, "작동 단계 2"), find_labeled(s2, "처리 방식")),
        "bind.s2.step3": first_non_empty(find_labeled(s2, "작동 단계 3"), find_labeled(s2, "출력 결과", "현장 workflow 연결")),
        "bind.s3.category": first_non_empty(find_labeled(s3, "구분 태그"), featured_meta.get("category", "")),
        "bind.s3.domain": first_non_empty(find_labeled(s3, "분야 태그"), featured_meta.get("domain", "")),
        "bind.s3.logo_label": find_labeled(s3, "로고 라벨", "회사·기관", "회사 및 기관"),
        "bind.s3.name": first_non_empty(find_labeled(s3, "회사·기관", "회사 및 기관"), featured_meta.get("related_org", "")),
        "bind.s3.tagline": find_labeled(s3, "한 줄 소개", "한줄 소개", "역할"),
        "bind.s3.description": find_labeled(s3, "설명", "회사 설명", "기관 설명", "제품·역량"),
        "bind.s3.founded": find_labeled(s3, "설립"),
        "bind.s3.headquarters": find_labeled(s3, "본사"),
        "bind.s3.scale": find_labeled(s3, "규모"),
        "bind.s3.focus": find_labeled(s3, "핵심 분야", "분야"),
        "bind.s4.takeaway": find_labeled(s4, "한줄 정리", "한 줄 정리", "결론"),
        "bind.s4.dek": find_labeled(s4, "보충 문장", "의료 현장 의미"),
        "bind.s4.what.title": find_labeled(s4, "무엇 제목") or "무엇",
        "bind.s4.what.detail": find_labeled(s4, "무엇 설명", "주요 내용"),
        "bind.s4.why.title": find_labeled(s4, "왜 중요 제목") or "왜 중요",
        "bind.s4.why.detail": find_labeled(s4, "왜 중요 설명", "의료 현장 의미"),
        "bind.s4.how.title": find_labeled(s4, "어떻게 제목") or "어떻게",
        "bind.s4.how.detail": find_labeled(s4, "어떻게 설명", "배경"),
        "bind.s4.source": f"출처: {source_line(featured_meta)}",
    }

    for index in range(1, 5):
        title, detail = pair(s2, f"기능 {index}", f"기능 {index} 설명")
        bindings[f"bind.s2.capability{index}.title"] = title
        bindings[f"bind.s2.capability{index}.detail"] = detail

    for index in range(1, 4):
        title, detail = pair(s3, f"제품·서비스 {index}", f"제품·서비스 {index} 설명")
        bindings[f"bind.s3.offering{index}.title"] = title
        bindings[f"bind.s3.offering{index}.detail"] = detail

    for index in range(1, 4):
        bindings[f"bind.s4.fact{index}.label"] = find_labeled(s4, f"요약 항목 {index} 라벨")
        bindings[f"bind.s4.fact{index}.value"] = find_labeled(s4, f"요약 항목 {index} 값")
        bindings[f"bind.s4.fact{index}.detail"] = find_labeled(s4, f"요약 항목 {index} 설명")
        bindings[f"bind.s4.meaning{index}"] = find_labeled(s4, f"의료 현장 의미 {index}", f"의미 {index}")

    return bindings


def build_slide_blocks(number: int, featured_meta: dict, section_text: str) -> list[dict]:
    points = compact_points(section_text)
    if number == 1:
        return [
            {"type": "headline", "text": featured_meta.get("title", "")},
            {"type": "bullets", "items": points[:4]},
        ]
    return [{"type": "bullets", "items": points}]


def public_selection_reason(featured: dict) -> str:
    reason = str(featured.get("reason", "")).strip()
    if reason and not re.search(r"(총점|점수|score|\d+\s*점)", reason, re.IGNORECASE):
        return reason
    title = str(featured.get("title", "대표 기사")).strip() or "대표 기사"
    return f"{title}는 의료 AI 관련성과 현장 적용 맥락이 분명해 이번 주 대표 기사로 선정했습니다."


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
        slides.append(
            {
                "number": number,
                "id": definition["id"],
                "title": section_title,
                "section_title": section_title,
                "layout": definition["layout"],
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
    template_bindings = build_template_bindings(featured_meta, research_sections)
    return {
        "schema_version": "1.1",
        "generator": "news-scrap-codex-v2/scripts/build_pencil_slide_spec.py",
        "week_id": week_id,
        "period": period,
        "output": {
            "pdf_filename": f"news_slide_{week_id}.pdf",
        },
        "template": {
            "mode": "update_named_bindings",
            "recommended_template_name": "news-scrap-codex-v2 pencil slide template",
            "binding_name_pattern": "^bind\\.",
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
            "empty_binding_policy": "empty_string_and_hide_parent_card_when_possible",
            "repeating_binding_policy": "use_only_verified_items_up_to_template_capacity",
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
            "accent": "#17617C",
            "line": "#D8DDE3",
            "font": "Inter",
        },
        "source_policy": {
            "language": "ko",
            "use_only_verified_facts": True,
            "exclude_internal_scores": True,
            "exclude_candidate_rankings": True,
            "output_format": "pdf_only",
        },
        "featured_article": featured_meta,
        "template_bindings": template_bindings,
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
