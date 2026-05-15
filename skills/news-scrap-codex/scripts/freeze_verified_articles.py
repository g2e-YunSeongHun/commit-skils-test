#!/usr/bin/env python3
"""Normalize, deduplicate, score, and cap verified_articles.json."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


EMERGENCY_KEYWORDS = (
    "응급",
    "응급실",
    "응급의료",
    "구급",
    "119",
    "중증",
    "트리아지",
    "emergency",
    "emergency department",
    "acute care",
    "triage",
    "ambulance",
    "ems",
    "trauma",
)

AI_KEYWORDS = (
    "ai",
    "인공지능",
    "생성형 ai",
    "의료 ai",
    "대형언어모델",
    "artificial intelligence",
    "llm",
    "foundation model",
    "machine learning",
)

IMPLEMENTATION_KEYWORDS = (
    "도입",
    "적용",
    "활용",
    "실사용",
    "안착",
    "업무협약",
    "통합",
    "상용화",
    "수주",
    "workflow",
    "deployment",
    "implementation",
    "adoption",
    "partnership",
    "integration",
    "rollout",
    "contract",
    "clearance",
    "launch",
)

ACUTE_USECASE_KEYWORDS = (
    "뇌졸중",
    "뇌출혈",
    "stroke",
    "sepsis",
    "ct",
    "mri",
    "초음파",
    "심장초음파",
    "pocus",
    "radiograph",
    "영상",
)


OPERATIONS_KEYWORDS = (
    "119",
    "소방",
    "신고접수",
    "출동지령",
    "상황관제",
    "이송",
    "병상",
    "과밀",
    "대기시간",
    "환자 흐름",
    "전원",
    "문서화",
    "진료기록",
    "ems",
    "911",
    "epcr",
    "dispatch",
    "routing",
    "documentation",
    "ambient scribe",
    "protocol",
)

BLOCKED_SOURCE_DOMAINS = (
    "news-medical.net",
    "medicalxpress.com",
    "sciencedaily.com",
    "eurekalert.org",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "medrxiv.org",
    "biorxiv.org",
    "arxiv.org",
    "researchsquare.com",
    "papers.ssrn.com",
    "annemergmed.com",
    "jamanetwork.com",
    "nejm.org",
    "ai.nejm.org",
    "bmj.com",
    "thelancet.com",
    "jmir.org",
    "medinform.jmir.org",
    "nature.com",
    "science.org",
    "frontiersin.org",
    "mdpi.com",
    "sciencedirect.com",
    "link.springer.com",
    "biomedcentral.com",
    "onlinelibrary.wiley.com",
    "academic.oup.com",
    "journals.sagepub.com",
    "tandfonline.com",
)

BLOCKED_SOURCE_MARKERS = (
    "doi",
    "abstract",
    "preprint",
    "peer-reviewed",
    "journal",
    "clinical trial",
    "clinical study",
    "observational study",
    "retrospective",
    "systematic review",
    "review article",
    "pubmed",
    "medrxiv",
    "biorxiv",
    "arxiv",
)

CATEGORY_WEIGHTS = {
    "도입/제휴": 34,
    "운영/인프라": 32,
    "정책/공공사업": 28,
    "기술/제품": 26,
    "정책": 24,
}

DOMAIN_WEIGHTS = {
    "mohw.go.kr": 10,
    "medicaltimes.com": 8,
    "medigatenews.com": 8,
    "dailymedi.com": 7,
    "rapportian.com": 7,
    "docdocdoc.co.kr": 7,
    "mdtoday.co.kr": 6,
    "hitnews.co.kr": 6,
    "jems.com": 7,
    "firehouse.com": 7,
    "emsworld.com": 7,
    "healthcareitnews.com": 6,
    "beckershospitalreview.com": 6,
    "fiercehealthcare.com": 6,
    "mobihealthnews.com": 5,
    "healthitanalytics.com": 5,
    "ems1.com": 5,
    "globenewswire.com": 4,
    "businesswire.com": 4,
    "prnewswire.com": 4,
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_text(article: dict, *keys: str) -> str:
    for key in keys:
        value = article.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text).lower()


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def parse_date(text: str) -> tuple[int, str]:
    try:
        dt = datetime.strptime(text, "%Y-%m-%d")
        return (int(dt.strftime("%Y%m%d")), text)
    except ValueError:
        return (0, text)


def domain_from_link(link: str) -> str:
    hostname = urlparse(link).hostname or ""
    return hostname.lower().lstrip("www.")


def is_listed_domain(hostname: str, domains: tuple[str, ...]) -> bool:
    return hostname in domains or any(hostname.endswith(f".{domain}") for domain in domains)


def is_blocked_article(article: dict) -> bool:
    link = get_text(article, "링크", "link", "url")
    hostname = domain_from_link(link) if link else ""
    if hostname and is_listed_domain(hostname, BLOCKED_SOURCE_DOMAINS):
        return True
    title = get_text(article, "제목", "title")
    body = get_text(article, "본문", "body", "content")
    category = get_text(article, "구분", "category")
    combined = f"{title}\n{body}\n{category}"
    return category.lower() == "research" or category == "\uc5f0\uad6c" or contains_any(combined, BLOCKED_SOURCE_MARKERS)


def article_key(article: dict) -> str:
    link = get_text(article, "링크", "link", "url")
    title = get_text(article, "제목", "title")
    if link:
        return f"link::{normalize(link)}"
    return f"title::{normalize(title)}"


def score_article(article: dict) -> int:
    title = get_text(article, "제목", "title")
    body = get_text(article, "본문", "body", "content")
    related_org = get_text(article, "관련기관", "related_org", "organization")
    category = get_text(article, "구분", "category")
    link = get_text(article, "링크", "link", "url")
    combined = f"{title}\n{body}"

    score = 0
    if contains_any(combined, EMERGENCY_KEYWORDS):
        score += 40
    if contains_any(combined, AI_KEYWORDS):
        score += 25
    score += CATEGORY_WEIGHTS.get(category, 10)
    if contains_any(combined, IMPLEMENTATION_KEYWORDS):
        score += 12
    if contains_any(combined, OPERATIONS_KEYWORDS):
        score += 10
    if contains_any(combined, ACUTE_USECASE_KEYWORDS) and contains_any(combined, EMERGENCY_KEYWORDS):
        score += 5
    if related_org:
        score += 5
    if len(body) >= 200:
        score += 5
    if link:
        score += 3
        score += DOMAIN_WEIGHTS.get(domain_from_link(link), 0)
    return score

def dedupe_and_rank(items: list[dict], limit: int) -> list[dict]:
    chosen: dict[str, dict] = {}
    for article in items:
        if is_blocked_article(article):
            continue
        key = article_key(article)
        article_copy = dict(article)
        article_copy["_score"] = score_article(article_copy)
        current = chosen.get(key)
        if current is None or article_copy["_score"] > current["_score"]:
            chosen[key] = article_copy

    ranked = list(chosen.values())
    ranked.sort(
        key=lambda article: (
            -int(article.get("_score", 0)),
            -parse_date(get_text(article, "날짜", "date"))[0],
            get_text(article, "기관/매체", "매체", "media").lower(),
            get_text(article, "제목", "title").lower(),
        )
    )

    trimmed = ranked[:limit]
    for article in trimmed:
        article.pop("_score", None)
    return trimmed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", default="")
    parser.add_argument("--domestic-limit", type=int, default=3)
    parser.add_argument("--overseas-limit", type=int, default=3)
    args = parser.parse_args()

    input_path = Path(args.input_json).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path
    payload = load_json(input_path)

    domestic = payload.get("국내기사")
    if not isinstance(domestic, list):
        domestic = []

    overseas = payload.get("해외기사")
    if not isinstance(overseas, list):
        overseas = []

    payload["국내기사"] = dedupe_and_rank(domestic, args.domestic_limit)
    payload["해외기사"] = dedupe_and_rank(overseas, args.overseas_limit)
    payload.pop("\ud574\uc678\ub17c\ubb38", None)

    dump_json(output_path, payload)
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
