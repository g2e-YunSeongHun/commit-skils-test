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
    "응급의료 AI 현장 적용 {period}",
    "응급의학 인공지능 병원 도입 {period}",
    "응급실 AI 인공지능 {period}",
    "응급환자 AI 트리아지 분류 {period}",
    "응급의료 AI 정책 정부 {period}",
    "119 AI 신고접수 음성인식 {period}",
    "119 AI 출동지령 상황관제 {period}",
    "119 AI 시스템 구급 {period}",
    "구급대 AI 심전도 이송 병원 선정 {period}",
    "응급실 AI 병상 배정 과밀 대기시간 {period}",
    "응급실 AI 환자 흐름 운영 {period}",
    "응급의료센터 AI 운영 시스템 {period}",
)

DOMESTIC_SUPPLEMENTAL_QUERIES = (
    "응급실 AI 문서화 진료기록 {period}",
    "응급실 AI 실사용 도구 {period}",
    "응급 협진 AI 전원 조정 {period}",
    "소방청 AI 응급의료 {period}",
    "재난응급 AI 상황실 {period}",
    "권역응급의료센터 AI {period}",
    "뇌졸중 AI 응급 치료 판단 {period}",
    "뇌출혈 AI 응급 영상 분석 {period}",
    "응급 CT AI 판독 {period}",
    "응급 MRI AI 판독 {period}",
    "응급 심장초음파 AI {period}",
    "POCUS AI 응급 {period}",
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
    "site:{domain} (119 OR 구급 OR 소방 OR 응급실 OR 응급의료 OR 권역응급의료센터) (AI OR 인공지능 OR \"의료 AI\") {period}",
    "site:{domain} (신고접수 OR 출동지령 OR 상황관제 OR 이송 OR 병상 OR 과밀 OR 전원 OR 문서화 OR 진료기록) (AI OR 인공지능) (응급 OR 응급실 OR 구급 OR 소방) {period}",
    "site:{domain} (도입 OR 적용 OR 활용 OR 실사용 OR 안착 OR 업무협약 OR 통합 OR 상용화 OR 수주) (AI OR 인공지능) (응급 OR 응급실 OR 구급 OR 소방 OR 병원) {period}",
    "site:{domain} (트리아지 OR 중증도 OR 분류 OR 예측 OR 뇌졸중 OR 심전도 OR CT OR POCUS) (AI OR 인공지능) (응급 OR 응급실 OR 중증 OR 구급) {period}",
)

OVERSEAS_CORE_QUERIES = (
    "emergency care AI deployment news {period}",
    "emergency medicine artificial intelligence hospital deployment {period}",
    "EMS AI documentation ePCR {period}",
    "911 AI dispatch emergency medical services {period}",
    "emergency department AI patient flow operations {period}",
    "emergency department AI bed management overcrowding {period}",
    "emergency department AI triage {period}",
    "prehospital AI EMS clinical workflow {period}",
    "ambulance AI routing dispatch real-time {period}",
    "emergency department ambient AI scribe documentation {period}",
    "hospital command center AI emergency department {period}",
)

OVERSEAS_SUPPLEMENTAL_QUERIES = (
    "EMS AI protocol platform integration {period}",
    "AI clinical workflow platform EMS {period}",
    "emergency care AI partnership integration {period}",
    "emergency department AI documentation scribe {period}",
    "emergency department AI clinical decision support deployment {period}",
    "stroke AI emergency workflow {period}",
    "sepsis AI emergency department {period}",
    "POCUS AI emergency {period}",
    "radiology AI acute care emergency {period}",
)

OVERSEAS_PRIORITY_DOMAINS = (
    "jems.com",
    "firehouse.com",
    "emsworld.com",
    "healthcareitnews.com",
    "beckershospitalreview.com",
    "statnews.com",
    "fiercehealthcare.com",
    "mobihealthnews.com",
    "healthitanalytics.com",
    "ems1.com",
    "globenewswire.com",
    "businesswire.com",
    "prnewswire.com",
)

OVERSEAS_SITE_PASS_PATTERNS = (
    "site:{domain} (\"emergency department\" OR \"emergency medicine\" OR EMS OR ambulance OR 911) (AI OR \"artificial intelligence\" OR \"machine learning\") {period}",
    "site:{domain} (documentation OR ePCR OR dispatch OR routing OR \"patient flow\" OR overcrowding OR \"bed management\" OR \"command center\" OR \"ambient scribe\") (AI OR \"artificial intelligence\") (emergency OR EMS OR hospital OR 911) {period}",
    "site:{domain} (deployment OR implementation OR adoption OR partnership OR integration OR rollout OR contract OR clearance) (AI OR \"artificial intelligence\") (hospital OR EMS OR emergency OR ambulance OR 911) {period}",
    "site:{domain} (triage OR stroke OR sepsis OR ultrasound OR POCUS OR radiology) (AI OR \"artificial intelligence\") (emergency OR triage OR \"acute care\" OR EMS) {period}",
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


def build_payload(start_date: str, end_date: str, include_papers: bool = False) -> dict:
    period = f"{start_date}..{end_date}"
    payload = {
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
        "process_notes": [
            "기본 수집은 국내/해외 기사 중심이다. 논문/프리프린트는 사용자가 요청한 경우에만 --include-papers로 별도 수집한다.",
            "국내 기사 0건을 선언하기 전에 domestic.mandatory_domains 전체에 대한 site_pass_queries와 119/구급/응급실 운영 축 보조 검색을 최소 1회 수행한다.",
            "뉴스 전용 검색 결과는 후보 시드로만 사용하고, 최종 포함 여부는 원문 URL 기준으로 판단한다.",
            "트리아지는 제외하지 않되, 병상/환자흐름/문서화/상황관제/EMS/ePCR/도입·통합 축 검색을 함께 수행한다.",
            "후보 URL은 extract.py로 발행일과 본문을 검증한 뒤 verified_articles.json에 반영한다.",
        ],
    }
    if include_papers:
        payload["papers"] = {
            "core_queries": render_queries(PAPER_CORE_QUERIES, period),
            "supplemental_queries": render_queries(PAPER_SUPPLEMENTAL_QUERIES, period),
            "priority_domains": list(PAPER_PRIORITY_DOMAINS),
            "site_pass_queries": render_site_pass(
                PAPER_PRIORITY_DOMAINS,
                PAPER_SITE_PASS_PATTERNS,
                period,
            ),
        }
        payload["process_notes"].append("papers 섹션은 보조 검토용이며, 기사 후보가 충분하면 기본 산출물에서 제외한다.")
    return payload

def to_text(payload: dict) -> str:
    lines: list[str] = []
    period = payload["period"]["label"]
    lines.append(f"[Period] {period}")
    lines.append("")
    for section_name in ("domestic", "overseas", "papers"):
        section = payload.get(section_name)
        if not isinstance(section, dict):
            continue
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
    parser.add_argument("--include-papers", action="store_true", help="include paper/preprint queries as optional backup")
    args = parser.parse_args()

    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    if start_date > end_date:
        raise SystemExit("start-date must be <= end-date")

    payload = build_payload(start_date, end_date, include_papers=args.include_papers)
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
