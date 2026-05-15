#!/usr/bin/env python3
"""Normalize raw search hits into candidates_raw.json for news-scrap-codex."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from build_search_queries import (
    DOMESTIC_MANDATORY_DOMAINS,
    OVERSEAS_PRIORITY_DOMAINS,
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")


NOISE_DOMAINS = {
    "youtube.com",
    "m.youtube.com",
    "blog.naver.com",
    "tistory.com",
    "brunch.co.kr",
    "medium.com",
    "velog.io",
    "reddit.com",
}

BLOCKED_SOURCE_DOMAINS = (
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
    "news-medical.net",
    "medicalxpress.com",
    "sciencedaily.com",
    "eurekalert.org",
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

TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

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

ACUTE_DETERIORATION_KEYWORDS = (
    "환자 악화",
    "환자악화",
    "임상 악화",
    "악화 예측",
    "중증화",
    "입원 환자",
    "일반 병동",
    "병동 모니터링",
    "조기경보",
    "조기경보점수",
    "early warning score",
    "patient deterioration",
    "clinical deterioration",
    "acute deterioration",
    "inpatient deterioration",
    "ward monitoring",
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

ACUTE_SUPPORT_KEYWORDS = (
    "뇌졸중",
    "뇌출혈",
    "stroke",
    "sepsis",
    "ct",
    "mri",
    "초음파",
    "심장초음파",
    "pocus",
    "x-ray",
    "radiograph",
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

def load_items(path: str) -> list[object]:
    if path == "-":
        raw = sys.stdin.read().strip()
    else:
        raw = Path(path).read_text(encoding="utf-8-sig").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [line.strip() for line in raw.splitlines() if line.strip()]
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("candidates", "results", "items", "hits", "urls"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise SystemExit("input must be a JSON array")


def get_text(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query_items = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in TRACKING_KEYS]
    clean_query = urlencode(query_items)
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.params, clean_query, ""))


def host_from_url(url: str) -> str:
    return (urlparse(url).hostname or "").lower().lstrip("www.")


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def is_noise_domain(hostname: str) -> bool:
    return hostname in NOISE_DOMAINS or any(hostname.endswith(f".{domain}") for domain in NOISE_DOMAINS)


def is_listed_domain(hostname: str, domains: tuple[str, ...]) -> bool:
    return hostname in domains or any(hostname.endswith(f".{domain}") for domain in domains)


def infer_section(hostname: str, haystack: str) -> str:
    if hostname.endswith(".kr") or hostname in DOMESTIC_MANDATORY_DOMAINS:
        return "domestic"
    return "overseas"


def normalize_section_hint(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"domestic", "overseas"}:
        return lowered
    return ""


def score_candidate(
    hostname: str,
    title: str,
    snippet: str,
    query: str,
    section: str,
) -> tuple[int, list[str]]:
    combined = f"{title}\n{snippet}\n{query}".lower()
    score = 0
    reasons: list[str] = []

    if contains_any(combined, EMERGENCY_KEYWORDS):
        score += 40
        reasons.append("emergency")
    if contains_any(combined, ACUTE_DETERIORATION_KEYWORDS):
        score += 34
        reasons.append("acute_deterioration")
    if contains_any(combined, AI_KEYWORDS):
        score += 25
        reasons.append("ai")
    if contains_any(combined, OPERATIONS_KEYWORDS):
        score += 12
        reasons.append("operations_signal")
    if contains_any(combined, IMPLEMENTATION_KEYWORDS):
        score += 10
        reasons.append("implementation_signal")
    if contains_any(combined, ACUTE_SUPPORT_KEYWORDS):
        score += 6
        reasons.append("acute_support")

    if section == "domestic" and hostname in DOMESTIC_MANDATORY_DOMAINS:
        score += 6
        reasons.append("domestic_priority_domain")
    if section == "overseas" and hostname in OVERSEAS_PRIORITY_DOMAINS:
        score += 6
        reasons.append("overseas_priority_domain")
    if not (title.strip() or snippet.strip()) and query.strip():
        score += 3
        reasons.append("query_seed")

    return score, reasons

def normalize_item(raw_item: object) -> dict | None:
    if isinstance(raw_item, str):
        url = raw_item.strip()
        if not url:
            return None
        item = {
            "url": url,
            "title": "",
            "snippet": "",
            "query": "",
            "source": "",
            "published": "",
            "source_title": "",
            "section_hint": "",
        }
    elif isinstance(raw_item, dict):
        url = get_text(raw_item, "url", "link")
        if not url:
            return None
        item = {
            "url": url,
            "title": get_text(raw_item, "title"),
            "snippet": get_text(raw_item, "snippet", "description"),
            "query": get_text(raw_item, "query"),
            "source": get_text(raw_item, "source", "engine"),
            "published": get_text(raw_item, "published", "date"),
            "source_title": get_text(raw_item, "source_title", "media"),
            "section_hint": get_text(raw_item, "section_hint", "section"),
        }
    else:
        return None

    canonical_url = canonicalize_url(item["url"])
    hostname = host_from_url(canonical_url)
    if not hostname or is_noise_domain(hostname):
        return None
    if is_listed_domain(hostname, BLOCKED_SOURCE_DOMAINS):
        return None

    haystack = f"{item['title']}\n{item['snippet']}\n{item['query']}".lower()
    if contains_any(haystack, BLOCKED_SOURCE_MARKERS):
        return None
    section = normalize_section_hint(item["section_hint"])
    if not section:
        section = infer_section(hostname, haystack)
    score, reasons = score_candidate(
        hostname,
        item["title"],
        item["snippet"],
        item["query"],
        section,
    )

    return {
        "url": canonical_url,
        "domain": hostname,
        "title": item["title"],
        "snippet": item["snippet"],
        "section_guess": section,
        "score": score,
        "matched_rules": reasons,
        "query": item["query"],
        "source": item["source"],
        "published": item["published"],
        "source_title": item["source_title"],
    }


def dedupe_candidates(candidates: list[dict]) -> list[dict]:
    chosen: dict[str, dict] = {}
    for candidate in candidates:
        current = chosen.get(candidate["url"])
        if current is None or candidate["score"] > current["score"]:
            chosen[candidate["url"]] = candidate
    return list(chosen.values())


def sort_key(candidate: dict) -> tuple[object, ...]:
    section_order = {"domestic": 0, "overseas": 1}
    return (
        section_order.get(candidate["section_guess"], 9),
        -int(candidate["score"]),
        candidate["domain"],
        candidate["title"].lower(),
        candidate["url"],
    )


def build_payload(candidates: list[dict], start_date: str, end_date: str) -> dict:
    grouped = {"domestic": 0, "overseas": 0}
    for candidate in candidates:
        grouped[candidate["section_guess"]] = grouped.get(candidate["section_guess"], 0) + 1
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "counts": grouped,
        "candidates": candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="JSON array of URLs or search-hit objects, or '-' for stdin")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--output", default="", help="optional output path for candidates_raw.json")
    args = parser.parse_args()

    items = load_items(args.input_json)
    normalized = [item for item in (normalize_item(raw_item) for raw_item in items) if item is not None]
    candidates = dedupe_candidates(normalized)
    candidates.sort(key=sort_key)
    payload = build_payload(candidates, args.start_date, args.end_date)

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        sys.stderr.write(f"DONE:{output_path}\n")
        return
    sys.stdout.write(rendered + "\n")


if __name__ == "__main__":
    main()
