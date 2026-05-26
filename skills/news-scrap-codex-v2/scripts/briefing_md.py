#!/usr/bin/env python3
"""Parse the structured news_briefing.md working file."""

from __future__ import annotations

import re
from pathlib import Path


SLIDE_SECTION_NAMES = (
    "이번 주 대표 기사",
    "제품 및 기술 설명",
    "회사 및 기관 소개",
    "기사 요약",
)


def normalize_key(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", value or "").lower()


def normalize_text(value: str) -> str:
    return normalize_key(value)


def clean_article_heading(value: str) -> str:
    cleaned = re.sub(r"^\s*\d+[\.\)]\s*", "", value or "").strip()
    return cleaned or "제목 미상"


def strip_markdown_link(value: str) -> str:
    match = re.fullmatch(r"\[.+?\]\((https?://[^)]+)\)", value.strip())
    if match:
        return match.group(1).strip()
    return value.strip()


def split_top_sections(text: str) -> dict[str, str]:
    heading_re = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    matches = list(heading_re.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def find_section(sections: dict[str, str], *needles: str, exclude_slide: bool = False) -> str:
    normalized_needles = [normalize_key(needle) for needle in needles]
    for title, body in sections.items():
        if exclude_slide and normalize_key(title).startswith("슬라이드"):
            continue
        normalized_title = normalize_key(title)
        if any(needle in normalized_title for needle in normalized_needles):
            return body
    return ""


def parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_key = ""
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            current_key = ""
            continue

        match = re.match(r"^(?:[-*]\s*)?([^:：]{1,40})\s*[:：]\s*(.*)$", line)
        if match:
            key = normalize_key(match.group(1))
            fields[key] = strip_markdown_link(match.group(2))
            current_key = key
            continue

        if current_key and not line.startswith("#"):
            fields[current_key] = f"{fields[current_key]} {line}".strip()

    return fields


def field(fields: dict[str, str], *names: str) -> str:
    for name in names:
        value = fields.get(normalize_key(name), "")
        if value:
            return value.strip()
    return ""


def split_article_blocks(section_body: str) -> list[tuple[str, str]]:
    article_re = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
    matches = list(article_re.finditer(section_body or ""))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        title = clean_article_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_body)
        blocks.append((title, section_body[start:end].strip()))
    return blocks


def parse_articles(section_body: str) -> list[dict]:
    articles: list[dict] = []
    for heading_title, block in split_article_blocks(section_body):
        fields = parse_fields(block)
        title = field(fields, "제목", "번역제목", "title") or heading_title
        translated_title = field(fields, "번역제목", "translated_title")
        original_title = field(fields, "원제목", "original_title")
        summary = field(fields, "요약", "한국어 요약", "summary_ko", "summary")

        articles.append(
            {
                "기관/매체": field(fields, "매체", "기관/매체", "source", "media"),
                "관련기관": field(fields, "관련기관", "회사", "기관", "organization", "related_org"),
                "적용분야": field(fields, "적용분야", "분야", "domain"),
                "구분": field(fields, "구분", "category"),
                "번역제목": translated_title,
                "원제목": original_title,
                "제목": title,
                "요약": summary,
                "summary_ko": summary,
                "본문": field(fields, "본문", "body", "content"),
                "날짜": field(fields, "날짜", "일자", "date"),
                "링크": field(fields, "링크", "url", "link"),
            }
        )
    return articles


def parse_period(section_body: str) -> dict[str, str]:
    fields = parse_fields(section_body)
    return {
        "시작일": field(fields, "시작일", "start_date"),
        "종료일": field(fields, "종료일", "end_date"),
        "생성일": field(fields, "생성일", "작성일", "generated_date"),
    }


def article_title(article: dict) -> str:
    return str(
        article.get("번역제목")
        or article.get("제목")
        or article.get("title")
        or "제목 미상"
    ).strip()


def find_article_match(articles: list[tuple[str, dict]], featured_fields: dict[str, str]) -> tuple[str, dict] | None:
    featured_link = field(featured_fields, "링크", "url", "link")
    featured_title = normalize_text(field(featured_fields, "제목", "번역제목", "title"))
    for section, article in articles:
        article_link = str(article.get("링크") or article.get("link") or "").strip()
        if featured_link and article_link == featured_link:
            return section, article
        titles = [
            article_title(article),
            str(article.get("원제목") or ""),
            str(article.get("제목") or ""),
        ]
        if featured_title and any(normalize_text(title) == featured_title for title in titles):
            return section, article
    return None


def parse_featured_article(section_body: str, verified: dict) -> dict:
    fields = parse_fields(section_body)
    all_articles = [
        ("국내기사", article) for article in verified["국내기사"]
    ] + [
        ("해외기사", article) for article in verified["해외기사"]
    ]
    matched = find_article_match(all_articles, fields)
    matched_section = matched[0] if matched else field(fields, "섹션", "section")
    matched_article = matched[1] if matched else {}

    return {
        "title": field(fields, "제목", "번역제목", "title") or article_title(matched_article),
        "original_title": field(fields, "원제목", "original_title") or str(matched_article.get("원제목") or ""),
        "media": field(fields, "매체", "기관/매체", "media") or str(matched_article.get("기관/매체") or ""),
        "date": field(fields, "날짜", "date") or str(matched_article.get("날짜") or ""),
        "section": matched_section,
        "related_org": field(fields, "관련기관", "회사", "기관", "related_org") or str(matched_article.get("관련기관") or ""),
        "domain": field(fields, "적용분야", "분야", "domain") or str(matched_article.get("적용분야") or ""),
        "category": field(fields, "구분", "category") or str(matched_article.get("구분") or ""),
        "link": field(fields, "링크", "url", "link") or str(matched_article.get("링크") or ""),
        "selection_reason": field(fields, "공개 선정 이유", "선정 이유", "reason"),
    }


def parse_slide_sections(sections: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for expected in SLIDE_SECTION_NAMES:
        body = find_section(sections, expected)
        if not body:
            raise SystemExit(f"news_briefing.md 구조 검증 실패: '{expected}' 섹션이 없습니다.")
        result[expected] = body
    return result


def parse_briefing_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    sections = split_top_sections(text)

    period = parse_period(find_section(sections, "기간"))
    domestic = parse_articles(find_section(sections, "국내 기사", "국내기사"))
    overseas = parse_articles(find_section(sections, "해외 기사", "해외기사"))
    verified = {
        **period,
        "start_date": period["시작일"],
        "end_date": period["종료일"],
        "generated_date": period["생성일"],
        "국내기사": domestic,
        "해외기사": overseas,
    }

    if not domestic and not overseas:
        raise SystemExit("news_briefing.md 구조 검증 실패: 국내 기사와 해외 기사가 모두 비어 있습니다.")

    featured_body = find_section(sections, "대표 기사", "대표기사", exclude_slide=True)
    if not featured_body:
        raise SystemExit("news_briefing.md 구조 검증 실패: '대표 기사' 섹션이 없습니다.")

    return {
        "verified": verified,
        "featured_meta": parse_featured_article(featured_body, verified),
        "research_sections": parse_slide_sections(sections),
    }
