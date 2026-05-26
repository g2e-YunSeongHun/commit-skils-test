#!/usr/bin/env python3
"""Select the weekly featured article with deterministic scoring rules."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_SECTIONS = (
    ("국내기사", ("국내기사", "domestic_articles")),
    ("해외기사", ("해외기사", "overseas_articles")),
)

CRITERIA = (
    ("emergency_relevance", "의료/응급/중환자의료 관련성"),
    ("ai_role", "AI 역할 명확성"),
    ("field_impact", "도입/검증/제품화 구체성"),
    ("source_completeness", "소스 완결성"),
    ("briefing_fit", "주간 대표성"),
)

EMERGENCY_TERMS = (
    "응급", "응급실", "응급의료", "119", "구급", "구급대", "이송", "전원",
    "중증", "외상", "심정지", "뇌졸중", "패혈증", "급성", "triage",
    "emergency", "emergency department", "ed", "ems", "ambulance", "trauma",
    "cardiac arrest", "stroke", "sepsis", "acute",
)
MEDICAL_CARE_TERMS = (
    "의료 ai", "의료 인공지능", "의료기기 ai", "의료기기",
    "의료 영상 ai", "의료 영상", "의료영상", "진단 ai", "판독 ai",
    "중환자실", "중환자의료",
    "critical care", "icu", "intensive care", "medical ai", "healthcare ai",
    "medical device ai", "medical imaging ai", "diagnostic ai", "radiology ai",
)
AI_STRONG_TERMS = (
    "ai", "인공지능", "머신러닝", "딥러닝", "llm", "생성형", "챗gpt",
    "chatgpt", "알고리즘", "machine learning", "deep learning",
    "artificial intelligence",
)
AI_SUPPORT_TERMS = (
    "모델", "예측", "분류", "자동", "판독",
    "predict", "prediction", "algorithm", "model",
)
IMPACT_TERMS = (
    "도입", "적용", "운영", "상용", "출시", "개발", "제휴", "협력", "검증",
    "임상", "연구", "승인", "허가", "fda", "ce", "pilot", "trial",
    "deployment", "launched", "validated", "approval", "partnership",
    "integrated", "product",
)
POLICY_TERMS = ("정책", "규제", "수가", "가이드라인", "정부", "법안", "policy", "regulation")
DEAD_PAGE_TERMS = (
    "page not found",
    "404",
    "페이지를 찾을 수",
    "not found",
    "없는 페이지",
    "삭제되었거나",
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_text(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def get_articles(payload: dict) -> list[dict]:
    articles: list[dict] = []
    for section_label, keys in ARTICLE_SECTIONS:
        section_items: list[dict] = []
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                section_items = [item for item in value if isinstance(item, dict)]
                break
        for index, article in enumerate(section_items, start=1):
            articles.append({"section": section_label, "index": index, "article": article})
    return articles


def article_title(article: dict) -> str:
    return get_text(article, "번역제목", "translated_title", "제목", "title") or "제목 미상"


def article_original_title(article: dict) -> str:
    return get_text(article, "원제목", "original_title")


def article_media(article: dict) -> str:
    return get_text(article, "기관/매체", "매체", "media") or "출처 미상"


def article_body(article: dict) -> str:
    return get_text(article, "본문", "body", "content")


def article_summary(article: dict) -> str:
    return get_text(
        article,
        "요약",
        "한국어요약",
        "한글요약",
        "번역요약",
        "summary_ko",
        "korean_summary",
        "summary",
    )


def joined_article_text(article: dict) -> str:
    return "\n".join(
        [
            article_title(article),
            article_original_title(article),
            get_text(article, "관련기관", "related_org", "organization"),
            article_body(article),
        ]
    )


def matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    raw = str(text or "").lower()
    matches: list[str] = []
    for term in terms:
        term_lower = term.lower()
        if re.fullmatch(r"[a-z0-9]{1,3}", term_lower):
            found = re.search(rf"(?<![a-z0-9]){re.escape(term_lower)}(?![a-z0-9])", raw) is not None
        else:
            found = term_lower in raw
        if found and term not in matches:
            matches.append(term)
    return matches


def points_from_matches(matches: list[str], *, step: int, cap: int, bonus: int = 0) -> int:
    return min(cap, len(matches) * step + bonus)


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+|(?<=요\.)\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def summarize_body(text: str, max_sentences: int = 4, max_chars: int = 650) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "본문 요약에 사용할 텍스트가 없습니다."
    summary = " ".join(sentences[:max_sentences]).strip()
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary


def summarize_article(article: dict, max_sentences: int = 4, max_chars: int = 650) -> str:
    summary = article_summary(article)
    if summary:
        return summarize_body(summary, max_sentences=max_sentences, max_chars=max_chars)
    return summarize_body(article_body(article), max_sentences=max_sentences, max_chars=max_chars)


def completeness_score(article: dict) -> int:
    if is_dead_page(article):
        return 0
    score = 0
    if article_title(article) != "제목 미상":
        score += 3
    if article_media(article) != "출처 미상":
        score += 3
    if get_text(article, "날짜", "date"):
        score += 3
    if get_text(article, "링크", "link", "url"):
        score += 3
    body_length = len(article_body(article))
    if body_length >= 2500:
        score += 8
    elif body_length >= 1200:
        score += 6
    elif body_length >= 600:
        score += 4
    elif body_length >= 250:
        score += 2
    return min(20, score)


def is_dead_page(article: dict) -> bool:
    title_and_body = normalize(f"{article_title(article)}\n{article_body(article)[:500]}")
    return any(term in title_and_body for term in DEAD_PAGE_TERMS)


def evidence_sentence(matches: list[str], fallback: str) -> str:
    if matches:
        return "확인 키워드: " + ", ".join(matches[:5])
    return fallback


def score_article(section: str, index: int, article: dict) -> dict:
    text = joined_article_text(article)
    emergency_matches = matched_terms(text, EMERGENCY_TERMS)
    medical_care_matches = matched_terms(text, MEDICAL_CARE_TERMS)
    relevance_matches = emergency_matches + medical_care_matches
    ai_strong_matches = matched_terms(text, AI_STRONG_TERMS)
    ai_support_matches = matched_terms(text, AI_SUPPORT_TERMS) if ai_strong_matches else []
    ai_matches = ai_strong_matches + ai_support_matches
    impact_matches = matched_terms(text, IMPACT_TERMS)
    policy_matches = matched_terms(text, POLICY_TERMS)

    domain = get_text(article, "적용분야", "domain")
    category = get_text(article, "구분", "category")
    body = article_body(article)
    dead_page = is_dead_page(article)

    emergency_bonus = 4 if any(term in f"{domain}\n{article_title(article)}" for term in ("응급", "의료", "중환자")) else 0
    ai_bonus = 4 if matched_terms(article_title(article), AI_STRONG_TERMS) else 0
    impact_bonus = 3 if category in {"도입/제휴", "기술/제품", "정책"} else 0

    scores = {
        "emergency_relevance": points_from_matches(
            relevance_matches, step=4, cap=20, bonus=emergency_bonus
        ),
        "ai_role": min(20, len(ai_strong_matches) * 6 + len(ai_support_matches) * 2 + ai_bonus),
        "field_impact": points_from_matches(
            impact_matches + policy_matches, step=3, cap=20, bonus=impact_bonus
        ),
        "source_completeness": completeness_score(article),
        "briefing_fit": 0,
    }

    fit = 0
    if scores["emergency_relevance"] >= 8 and scores["ai_role"] >= 8:
        fit += 9
    if scores["field_impact"] >= 8:
        fit += 4
    if category in {"도입/제휴", "기술/제품"}:
        fit += 3
    if section == "국내기사":
        fit += 2
    if len(body) >= 1000:
        fit += 2
    scores["briefing_fit"] = min(20, fit)
    if dead_page:
        scores["field_impact"] = min(scores["field_impact"], 4)
        scores["briefing_fit"] = min(scores["briefing_fit"], 4)

    limitations: list[str] = []
    if dead_page:
        limitations.append("본문이 오류 페이지 또는 유실 페이지로 보임")
    if scores["emergency_relevance"] < 8:
        limitations.append("의료 AI 관련성이 약함")
    if scores["ai_role"] < 8:
        limitations.append("AI 기술 역할 설명이 부족함")
    if scores["field_impact"] < 8:
        limitations.append("도입·검증·제품화 맥락이 약함")
    if scores["source_completeness"] < 12:
        limitations.append("본문 또는 출처 메타데이터가 부족함")

    total_score = sum(scores.values())
    evidence = {
        "emergency_relevance": evidence_sentence(relevance_matches, "의료 AI 관련 키워드가 뚜렷하지 않음"),
        "ai_role": evidence_sentence(ai_matches, "AI 기술 역할을 확인할 키워드가 부족함"),
        "field_impact": evidence_sentence(
            impact_matches + policy_matches,
            "도입·검증·제품화·정책 영향 키워드가 부족함",
        ),
        "source_completeness": f"본문 {len(body)}자, 날짜/링크/매체 필드 확인",
        "briefing_fit": f"섹션 {section}, 구분 {category or '미상'}, 적용분야 {domain or '미상'}",
    }

    return {
        "section": section,
        "index": index,
        "title": article_title(article),
        "original_title": article_original_title(article),
        "media": article_media(article),
        "date": get_text(article, "날짜", "date") or "미상",
        "related_org": get_text(article, "관련기관", "related_org", "organization"),
        "domain": domain,
        "category": category,
        "link": get_text(article, "링크", "link", "url"),
        "score": total_score,
        "scores": scores,
        "evidence": evidence,
        "limitations": limitations,
        "summary": summarize_article(article),
    }


def build_reason(candidate: dict) -> str:
    scores = candidate["scores"]
    if scores["emergency_relevance"] >= 8 and scores["ai_role"] >= 8:
        return (
            f"{candidate['title']}은 의료 AI 관련성, AI 역할, 현장 영향 근거가 함께 확인되어 "
            "주간 대표 기사로 선정되었습니다."
        )
    return (
        f"{candidate['title']}은 내부 검토에서 주간 대표성이 가장 높게 평가되었지만, "
        "의료 AI 관련성이 충분히 강하지 않아 조건부 대표 기사로 선정되었습니다."
    )


def make_featured(candidate: dict) -> dict:
    return {
        "title": candidate["title"],
        "original_title": candidate["original_title"],
        "media": candidate["media"],
        "date": candidate["date"],
        "section": candidate["section"],
        "related_org": candidate["related_org"],
        "domain": candidate["domain"],
        "category": candidate["category"],
        "link": candidate["link"],
        "reason": build_reason(candidate),
        "score": candidate["score"],
        "score_breakdown": candidate["scores"],
        "selection_evidence": candidate["evidence"],
        "limitations": candidate["limitations"],
        "source_id": "",
    }


def build_report(payload: dict, candidates: list[dict], featured: dict) -> dict:
    ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
    return {
        "period": {
            "start_date": get_text(payload, "시작일", "start_date"),
            "end_date": get_text(payload, "종료일", "end_date"),
            "generated_date": get_text(payload, "생성일", "generated_date"),
        },
        "criteria": [{"id": key, "label": label, "max_score": 20} for key, label in CRITERIA],
        "featured_article": featured,
        "candidates": [
            {
                "rank": rank,
                "title": item["title"],
                "media": item["media"],
                "date": item["date"],
                "section": item["section"],
                "score": item["score"],
                "scores": item["scores"],
                "evidence": item["evidence"],
                "limitations": item["limitations"],
                "summary": item["summary"],
                "link": item["link"],
            }
            for rank, item in enumerate(ranked, start=1)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("verified_json")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    verified_path = Path(args.verified_json).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else verified_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_json(verified_path)
    articles = get_articles(payload)
    if not articles:
        raise SystemExit("대표 기사 선정에 사용할 기사가 없습니다.")

    candidates = [
        score_article(item["section"], item["index"], item["article"])
        for item in articles
    ]
    candidates.sort(key=lambda item: item["score"], reverse=True)
    featured = make_featured(candidates[0])
    report = build_report(payload, candidates, featured)
    summaries = [
        {
            "title": item["title"],
            "media": item["media"],
            "date": item["date"],
            "section": item["section"],
            "summary": item["summary"],
            "score": item["score"],
        }
        for item in candidates
    ]

    write_json(output_dir / "featured_article.json", featured)
    write_json(output_dir / "selection_report.json", report)
    write_json(output_dir / "article_summaries.json", summaries)
    print(f"DONE:{output_dir / 'featured_article.json'}")


if __name__ == "__main__":
    main()
