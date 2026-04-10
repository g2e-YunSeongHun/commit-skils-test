#!/usr/bin/env python3
"""Build a structured weekly query set for news-scrap-codex collection."""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


DOMESTIC_CORE_QUERIES = (
    "응급실 AI 인공지능 {period}",
    "응급의학 인공지능 병원 도입 {period}",
    "응급환자 AI 트리아지 분류 {period}",
    "응급의료 AI 정책 정부 {period}",
    "응급실 과밀 AI 병상 배정 {period}",
    "119 AI 시스템 구급 {period}",
    "중증환자 AI 분류 예측 {period}",
    "의료 AI 인공지능 병원 도입 {period}",
)

DOMESTIC_SUPPLEMENTAL_QUERIES = (
    "뇌졸중 AI 응급 치료 판단 {period}",
    "뇌출혈 AI 응급 영상 분석 {period}",
    "응급 CT AI 판독 {period}",
    "응급 MRI AI 판독 {period}",
    "응급 심장초음파 AI {period}",
    "POCUS AI 응급 {period}",
    "응급실 AI 실사용 도구 {period}",
    "응급 협진 AI 영상 {period}",
)

DOMESTIC_MANDATORY_DOMAINS = (
    "medicaltimes.com",
    "medigatenews.com",
    "dailymedi.com",
    "rapportian.com",
    "docdocdoc.co.kr",
    "mdtoday.co.kr",
    "hitnews.co.kr",
    "pharm.edaily.co.kr",
    "mohw.go.kr",
)

DOMESTIC_SITE_PASS_PATTERNS = (
    'site:{domain} (응급 OR 응급실 OR 응급의료 OR 구급 OR 중증 OR 트리아지) (AI OR 인공지능 OR "의료 AI") {period}',
    'site:{domain} (뇌졸중 OR 뇌출혈 OR CT OR MRI OR 초음파 OR POCUS) (AI OR 인공지능) (응급 OR 응급실 OR 중증) {period}',
    'site:{domain} (도입 OR 적용 OR 활용 OR 실사용 OR 안착) (AI OR 인공지능) (응급 OR 뇌졸중 OR 구급) {period}',
)

OVERSEAS_CORE_QUERIES = (
    "emergency department AI triage {period}",
    "emergency medicine artificial intelligence {period}",
    "emergency room AI clinical decision support {period}",
    "emergency department overcrowding AI patient flow {period}",
    "prehospital AI EMS prediction {period}",
    "ambulance AI routing dispatch real-time {period}",
    "hospital AI clinical workflow automation {period}",
)

OVERSEAS_SUPPLEMENTAL_QUERIES = (
    "stroke AI emergency workflow {period}",
    "sepsis AI emergency department {period}",
    "POCUS AI emergency {period}",
    "radiology AI acute care emergency {period}",
    "ambient AI emergency medicine {period}",
    "AI documentation emergency department {period}",
)

OVERSEAS_PRIORITY_DOMAINS = (
    "healthcareitnews.com",
    "beckershospitalreview.com",
    "statnews.com",
    "fiercehealthcare.com",
    "mobihealthnews.com",
    "ems1.com",
    "globenewswire.com",
    "businesswire.com",
    "prnewswire.com",
)

OVERSEAS_SITE_PASS_PATTERNS = (
    'site:{domain} ("emergency department" OR "emergency medicine" OR EMS OR ambulance OR triage) (AI OR "artificial intelligence" OR "machine learning") {period}',
    'site:{domain} (stroke OR sepsis OR ultrasound OR POCUS OR radiology) (AI OR "artificial intelligence") (emergency OR triage OR "acute care") {period}',
    'site:{domain} (deployment OR implementation OR adoption OR partnership) (AI OR "artificial intelligence") (hospital OR EMS OR emergency) {period}',
)

PAPER_CORE_QUERIES = (
    "emergency triage AI machine learning site:pubmed.ncbi.nlm.nih.gov {period}",
    "emergency medicine artificial intelligence peer-reviewed {period}",
    "emergency department AI clinical trial {period}",
    "emergency department crowding AI resource allocation {period}",
    "prehospital emergency AI prediction model {period}",
)

PAPER_SUPPLEMENTAL_QUERIES = (
    "stroke AI emergency department paper {period}",
    "sepsis AI emergency department paper {period}",
    "ultrasound AI emergency medicine paper {period}",
    "radiograph AI emergency department paper {period}",
)

PAPER_PRIORITY_DOMAINS = (
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "annemergmed.com",
    "jmir.org",
    "medinform.jmir.org",
    "ai.nejm.org",
    "nature.com",
    "frontiersin.org",
    "mdpi.com",
    "sciencedirect.com",
    "link.springer.com",
    "biomedcentral.com",
)

PAPER_SITE_PASS_PATTERNS = (
    'site:{domain} ("emergency department" OR triage OR EMS OR ambulance) (AI OR "machine learning") {period}',
    'site:{domain} (stroke OR sepsis OR ultrasound OR radiograph) (AI OR "machine learning") (emergency OR "acute care") {period}',
)


def parse_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def render_queries(templates: tuple[str, ...], period: str) -> list[str]:
    return [template.format(period=period) for template in templates]


def render_site_pass(domains: tuple[str, ...], templates: tuple[str, ...], period: str) -> list[str]:
    queries: list[str] = []
    for domain in domains:
        for template in templates:
            queries.append(template.format(domain=domain, period=period))
    return queries


def build_payload(start_date: str, end_date: str) -> dict:
    period = f"{start_date}..{end_date}"
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "label": period,
        },
        "domestic": {
            "core_queries": render_queries(DOMESTIC_CORE_QUERIES, period),
            "supplemental_queries": render_queries(DOMESTIC_SUPPLEMENTAL_QUERIES, period),
            "mandatory_domains": list(DOMESTIC_MANDATORY_DOMAINS),
            "site_pass_queries": render_site_pass(
                DOMESTIC_MANDATORY_DOMAINS,
                DOMESTIC_SITE_PASS_PATTERNS,
                period,
            ),
        },
        "overseas": {
            "core_queries": render_queries(OVERSEAS_CORE_QUERIES, period),
            "supplemental_queries": render_queries(OVERSEAS_SUPPLEMENTAL_QUERIES, period),
            "priority_domains": list(OVERSEAS_PRIORITY_DOMAINS),
            "site_pass_queries": render_site_pass(
                OVERSEAS_PRIORITY_DOMAINS,
                OVERSEAS_SITE_PASS_PATTERNS,
                period,
            ),
        },
        "papers": {
            "core_queries": render_queries(PAPER_CORE_QUERIES, period),
            "supplemental_queries": render_queries(PAPER_SUPPLEMENTAL_QUERIES, period),
            "priority_domains": list(PAPER_PRIORITY_DOMAINS),
            "site_pass_queries": render_site_pass(
                PAPER_PRIORITY_DOMAINS,
                PAPER_SITE_PASS_PATTERNS,
                period,
            ),
        },
        "process_notes": [
            "국내 기사 0건을 선언하기 전에 domestic.mandatory_domains 전체에 대한 site_pass_queries를 최소 1회 수행한다.",
            "뉴스 전용 검색 결과는 후보 시드로만 사용하고, 최종 포함 여부는 원문 URL 기준으로 판단한다.",
            "질환명 또는 제품명 중심 기사라도 본문에서 응급실/응급치료/구급 워크플로가 확인되면 포함 후보로 유지한다.",
            "후보 URL은 extract.py로 발행일과 본문을 검증한 뒤 verified_articles.json에 반영한다.",
        ],
    }


def to_text(payload: dict) -> str:
    lines: list[str] = []
    period = payload["period"]["label"]
    lines.append(f"[Period] {period}")
    lines.append("")
    for section_name in ("domestic", "overseas", "papers"):
        section = payload[section_name]
        lines.append(f"[{section_name.upper()}]")
        lines.append("core_queries")
        for item in section["core_queries"]:
            lines.append(f"- {item}")
        lines.append("supplemental_queries")
        for item in section["supplemental_queries"]:
            lines.append(f"- {item}")
        domain_key = "mandatory_domains" if section_name == "domestic" else "priority_domains"
        lines.append(domain_key)
        for item in section[domain_key]:
            lines.append(f"- {item}")
        lines.append("site_pass_queries")
        for item in section["site_pass_queries"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("[NOTES]")
    for item in payload["process_notes"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--output", default="", help="optional output path")
    args = parser.parse_args()

    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    if start_date > end_date:
        raise SystemExit("start-date must be <= end-date")

    payload = build_payload(start_date, end_date)
    rendered = to_text(payload) if args.format == "text" else json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"DONE:{output_path}")
        return
    print(rendered)


if __name__ == "__main__":
    main()
