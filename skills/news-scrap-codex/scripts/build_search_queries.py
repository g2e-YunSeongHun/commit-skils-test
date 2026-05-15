#!/usr/bin/env python3
"""Build a structured weekly query set for news-scrap-codex collection."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8")


DOMESTIC_CORE_QUERIES = (
    "응급의료 AI {period}",
    "응급실 AI {period}",
    "응급환자 AI 트리아지 {period}",
    "중증환자 AI 분류 {period}",
    "응급 CT AI 판독 {period}",
    "뇌졸중 AI 응급 {period}",
    "119 AI 신고접수 {period}",
    "119 AI 출동지령 {period}",
    "119 AI 상황관제 {period}",
    "구급대 AI {period}",
    "응급실 AI 문서화 진료기록 {period}",
)

DOMESTIC_SUPPLEMENTAL_QUERIES = (
    "의료 AI 응급실 {period}",
    "의료 AI 응급환자 {period}",
    "의료 AI 중증환자 {period}",
    "응급실 음성인식 AI {period}",
    "응급실 생성형 AI {period}",
    "응급실 실사용 AI {period}",
    "소방청 AI 119 {period}",
    "소방청 AI 구급 {period}",
    "심전도 AI 구급 {period}",
    "뇌출혈 AI 응급 영상 분석 {period}",
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
    "site:{domain} (119 OR 구급 OR 응급실 OR 응급의료 OR 중증 OR 트리아지) (AI OR 인공지능 OR \"의료 AI\") {period}",
    "site:{domain} (신고접수 OR 출동지령 OR 상황관제 OR 이송 OR 문서화 OR 진료기록 OR 음성인식) (AI OR 인공지능) (119 OR 응급 OR 응급실 OR 구급) {period}",
    "site:{domain} (도입 OR 적용 OR 활용 OR 실사용 OR 안착 OR 업무협약 OR 통합 OR 상용화 OR 수주) (AI OR 인공지능 OR \"의료 AI\") (응급 OR 응급실 OR 구급 OR 119 OR 중증 OR 트리아지 OR 환자분류) {period}",
    "site:{domain} (트리아지 OR 중증도 OR 분류 OR 예측 OR 뇌졸중 OR 심전도 OR CT OR POCUS) (AI OR 인공지능) (응급 OR 응급실 OR 중증 OR 구급) {period}",
)

OVERSEAS_CORE_QUERIES = (
    "emergency care AI deployment news {period}",
    "emergency medicine artificial intelligence hospital deployment {period}",
    "EMS AI documentation ePCR {period}",
    "911 AI dispatch emergency medical services {period}",
    "emergency department AI triage {period}",
    "prehospital AI EMS clinical workflow {period}",
    "ambulance AI routing dispatch real-time {period}",
    "emergency department ambient AI scribe documentation {period}",
    "emergency department AI clinical decision support deployment {period}",
    "AI fracture triage emergency department clearance {period}",
)

OVERSEAS_SUPPLEMENTAL_QUERIES = (
    "EMS AI protocol platform integration {period}",
    "AI clinical workflow platform EMS {period}",
    "emergency care AI partnership integration {period}",
    "emergency department AI documentation scribe {period}",
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
    "site:{domain} (documentation OR ePCR OR dispatch OR routing OR \"ambient scribe\" OR scribe) (AI OR \"artificial intelligence\") (emergency OR EMS OR ambulance OR 911 OR \"emergency department\") {period}",
    "site:{domain} (deployment OR implementation OR adoption OR partnership OR integration OR rollout OR contract OR clearance OR launch) (AI OR \"artificial intelligence\") (EMS OR emergency OR ambulance OR 911 OR \"emergency department\" OR triage) {period}",
    "site:{domain} (triage OR stroke OR sepsis OR ultrasound OR POCUS OR radiology OR fracture) (AI OR \"artificial intelligence\") (emergency OR triage OR \"acute care\" OR EMS OR \"emergency department\") {period}",
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
            "기본 수집은 국내/해외 기사 원문 중심이다.",
            "국내 기사 0건을 선언하기 전에 domestic.mandatory_domains 전체에 대한 site_pass_queries와 진료 AI/119·구급/문서화 축 보조 검색을 최소 1회 수행한다.",
            "뉴스 전용 검색 결과는 후보 시드로만 사용하고, 최종 포함 여부는 원문 URL 기준으로 판단한다.",
            "트리아지는 진료 AI 축으로 포함한다. 병상/환자흐름/전원 운영 쿼리와 일반 소방 AI/로봇/위원회 쿼리는 기본 국내 수집에서 제외한다.",
            "해외 기본 수집에서도 patient flow/bed management/hospital command center 단독 쿼리는 제외하고 응급실/EMS/트리아지/임상 의사결정/현장 배치 맥락으로 좁힌다.",
            "후보 URL은 extract.py로 발행일과 본문을 검증한 뒤 verified_articles.json에 반영한다.",
        ],
    }
    return payload

def to_text(payload: dict) -> str:
    lines: list[str] = []
    period = payload["period"]["label"]
    lines.append(f"[Period] {period}")
    lines.append("")
    for section_name in ("domestic", "overseas"):
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
