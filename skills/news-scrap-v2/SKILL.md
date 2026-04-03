---
name: news-scrap-v2
description: NotebookLM을 필수 게이트로 두는 응급의료 AI 주간 뉴스 스크랩. 전주 토요일부터 이번 주 금요일까지의 국내 기사, 해외 기사, 논문을 수집·검증한 뒤 매주 새 NotebookLM 노트에 기사별 개별 소스를 업로드하고 Q0~Q5 분석이 모두 성공한 경우에만 HTML 대시보드와 슬라이드를 생성한다. 응급의료 AI 주간 뉴스, NotebookLM 기반 브리핑, 실패 시 즉시 종료가 필요한 뉴스 스크랩 작업에 사용한다.
---

# 응급의료 AI 주간 뉴스 스크랩 V2

**IMPORTANT: 모든 출력은 한국어로 작성한다.**

## Overview

이 스킬은 응급의료 AI 주간 뉴스 브리핑을 `NotebookLM 필수` 워크플로우로 생성한다. 기사 선별과 발행일 검증은 로컬에서 고정하고, 분석은 반드시 새 NotebookLM 노트에서 수행하며, NotebookLM 단계가 하나라도 실패하면 fallback 없이 즉시 종료한다.

## 핵심 원칙

- `NotebookLM 실패 = 전체 작업 실패`로 간주한다.
- 기존 NotebookLM 노트, 기존 HTML, 기존 슬라이드를 참고하지 않는다.
- 매주 항상 새 NotebookLM 노트를 만든다.
- 기사 본문은 반드시 기사별 개별 텍스트 파일로 분리해 업로드한다.
- 최종 산출물 생성 전의 단일 진실원본은 `verified_articles.json` 하나뿐이다.
- NotebookLM이 성공하기 전에는 HTML, PPTX, 최종 요약문을 만들지 않는다.

## Quick Start

1. 수집 기간을 계산한다.
2. 국내 기사, 해외 기사, 논문 후보를 병렬 수집한다.
3. `scripts/extract.py`로 본문과 발행일을 검증한다.
4. 중복 제거 후 `verified_articles.json`을 확정한다.
5. `scripts/build_notebook_sources.py`로 기사별 개별 소스 파일과 manifest를 만든다.
6. `scripts/notebooklm_gate.py`로 새 NotebookLM 노트를 만들고 Q0~Q5를 수행한다.
7. NotebookLM 결과가 모두 저장된 경우에만 대시보드 입력 JSON과 슬라이드 입력 JSON을 정리한다.
8. `scripts/render_dashboard.py`, `scripts/slide.py`로 최종본을 생성한다.
9. `scripts/cleanup_output.py`로 `news_output`을 정리한다.

상세 단계와 실패 규칙은 [workflow.md](references/workflow.md)를 본다.
NotebookLM 질의문은 [prompts.md](references/prompts.md)를 본다.
입출력 JSON 계약은 [output-contracts.md](references/output-contracts.md)를 본다.

## 기간 계산

- 종료일: 오늘 기준 가장 최근 금요일
- 시작일: 종료일 기준 6일 전 토요일
- 파일명용 형식: `YYYY-MM-DD`
- 표시용 형식: `YYYY년 M월 D일(요일)`

사용자에게 먼저 아래처럼 알린다.

```text
수집 기간: 2026년 3월 28일(토) ~ 2026년 4월 3일(금) - 4월 1주차
```

## 로컬 검증 단계

NotebookLM에 올리기 전까지는 아래 단계만 수행한다.

- 검색 후보 수집
- 노이즈 도메인 제거
- 응급의료 직접 관련성 판정
- `scripts/extract.py` 기반 발행일/본문 검증
- URL 중복 제거
- 재보도 대표 기사 선택
- `verified_articles.json` 확정

이 단계에서는 요약문을 확정하지 않는다. 분석은 NotebookLM에 넘긴다.

## NotebookLM 게이트

반드시 아래 순서로 진행한다.

1. 새 노트 생성
2. 기사별 개별 소스 업로드
3. 각 소스 `ready` 대기
4. Q0~Q5 질의
5. 모든 답변을 노트와 로컬 JSON에 저장

`scripts/notebooklm_gate.py`는 위 단계를 자동으로 수행하며, 하나라도 실패하면 `notebooklm_failure.json`을 쓰고 종료한다.

예시:

```powershell
python scripts/build_notebook_sources.py news_output\verified_articles_26년_4월_1주차.json news_output\runs\26년_4월_1주차
python scripts/notebooklm_gate.py news_output\runs\26년_4월_1주차\notebook_manifest.json --output-dir news_output\runs\26년_4월_1주차
```

## Publish 단계

NotebookLM이 모두 성공한 뒤에만 아래를 수행한다.

- 대시보드 입력 JSON 정리
- 슬라이드 입력 JSON 정리
- 대표 기사 심층 리서치 보강
- `scripts/render_dashboard.py` 실행
- `scripts/slide.py` 실행
- `scripts/cleanup_output.py` 실행

## Bundled Resources

### scripts/

- `extract.py`
  URL에서 본문과 발행일을 추출한다.
- `build_notebook_sources.py`
  `verified_articles.json`에서 기사별 NotebookLM 업로드용 텍스트 파일과 manifest를 생성한다.
- `notebooklm_gate.py`
  새 NotebookLM 노트를 만들고, 소스 업로드, 대기, Q0~Q5 질의를 수행하며 실패 시 즉시 종료한다.
- `render_dashboard.py`
  구조화된 입력 JSON으로 HTML 대시보드를 만든다.
- `slide.py`
  대표 기사용 3장 슬라이드를 만든다.
- `cleanup_output.py`
  `news_output`의 구버전과 중간 산출물을 정리한다.

### references/

- `workflow.md`
  단계별 실행 순서와 실패 정책
- `prompts.md`
  NotebookLM 질문 설계
- `output-contracts.md`
  로컬 JSON 및 NotebookLM 출력 계약

### templates/

- `dashboard.html`
  대시보드 렌더링 템플릿

## Environment

Required:

- `trafilatura`
- `python-pptx`
- `notebooklm-py`

Recommended:

- `playwright`
- Chromium 런타임

NotebookLM CLI가 로그인 상태가 아니거나 네트워크가 차단되면 이 스킬은 성공할 수 없다. 이 경우 fallback 없이 종료한다.
