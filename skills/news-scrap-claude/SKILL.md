---
name: news-scrap-claude
description: Claude용 응급의료 AI 주간 뉴스 브리핑 스킬. Use when creating a Korean weekly emergency-medicine AI news briefing using Claude's built-in WebSearch/WebFetch tools for article collection and verification, then handing off to the same NotebookLM pipeline (notebooklm_gate.py, render_dashboard.py, notebooklm_slide_deck.py) for analysis and slide generation.
---

# 응급의료 AI 뉴스 브리핑 for Claude

모든 출력은 한국어로 작성한다.

## 언제 이 스킬을 쓰는가

- 주간 응급의료 AI 기사 브리핑을 만들어야 할 때
- Codex CLI 없이 Claude가 직접 기사 수집·검증·정리를 수행해야 할 때
- 기사 수집은 Claude의 WebSearch/WebFetch로, 분석과 슬라이드는 NotebookLM으로 처리해야 할 때
- NotebookLM을 필수 게이트로 써야 할 때
- 최종 슬라이드를 `python-pptx`가 아니라 NotebookLM `slide-deck`로 생성해야 할 때

## news-scrap-codex와의 차이

| 단계 | news-scrap-codex | news-scrap-claude |
|---|---|---|
| 기사 수집 | `build_search_queries.py` + Codex 웹 검색 | Claude WebSearch 직접 실행 |
| 후보 정규화 | `scan_candidates.py` | Claude가 직접 필터링·정규화 |
| 본문·날짜 검증 | `scripts/extract.py` | Claude WebFetch 직접 실행 |
| 점수화·고정 | `freeze_verified_articles.py` | Claude가 직접 점수화 후 JSON 저장 |
| Manifest 생성 | `build_notebook_sources.py` | Claude Write 도구로 직접 생성 |
| 주차 초기화 | `reset_week_outputs.py` | Claude Bash/Write 도구로 직접 삭제 |
| NotebookLM 게이트 | `notebooklm_gate.py` | **동일** (`notebooklm_gate.py`) |
| HTML 대시보드 | `render_dashboard.py` | **동일** (`render_dashboard.py`) |
| 슬라이드 생성 | `notebooklm_slide_deck.py` | **동일** (`notebooklm_slide_deck.py`) |

## 핵심 규칙

- 기사 수집·검증은 Claude의 WebSearch/WebFetch 도구를 직접 사용한다. Python 검색 스크립트를 호출하지 않는다.
- NotebookLM 단계(`notebooklm_gate.py`, `render_dashboard.py`, `notebooklm_slide_deck.py`)는 news-scrap-codex와 동일하게 실행한다.
- NotebookLM 단계가 실패하면 전체 작업을 실패로 간주한다.
- 새 실행마다 새 NotebookLM 노트를 만든다.
- 최종 슬라이드는 [references/slide_prompt.md](references/slide_prompt.md)의 5장 구조와 디자인 가이드를 따른다.
- 기본 경로는 `verified_articles.json -> notebook_manifest.json -> notebooklm_outputs.json -> slide_deck_artifact.json`이다.
- HTML 대시보드도 기본 산출물이다.
- 기본 슬라이드 생성 경로에서 `python-pptx`는 사용하지 않는다.
- 국내 기사가 비어 보이면 바로 `0건`으로 확정하지 말고, 필수 도메인 WebSearch와 보조 쿼리를 먼저 수행한다.
- 논문/프리프린트는 사용자가 명시적으로 요청할 때만 보조 후보로 포함한다.

## 입력 기준

- 권장 입력: `verified_articles.json` (이미 있으면 수집 단계를 건너뛰고 4단계부터 시작)
- 이 파일이 없으면 Claude가 직접 WebSearch/WebFetch로 기사 수집·검증·정리를 수행해 같은 스키마로 고정한다.
- 기사 수집 규칙과 건수 상한은 [references/search-rules.md](references/search-rules.md)를 따른다.
- 영문 기사 제목은 가능하면 `번역제목`과 `원제목`을 함께 저장하고, HTML은 `번역제목`을 우선 노출한다.
- 스키마는 [references/output-contracts.md](references/output-contracts.md)를 따른다.

## 실행 순서

1. 기사 범위를 계산한다 (종료일: 직전 금요일, 시작일: 종료일 기준 6일 전 토요일).
2. `<run_dir>`를 정한다 (`news_output/runs/<week_id>`).
3. `<run_dir>` 안의 기존 생성물을 Claude 도구로 직접 삭제한다 (`search_queries.json`, `candidates_raw.json`, `verified_articles*.json`, `notebook_manifest.json`, `notebooklm_outputs.json`, `featured_article.json`, `slide_deck_artifact.json`, `notebooklm_failure.json`, `news_*.html`, `news_slide_*.pdf`, `news_slide_*.pptx`, `*.tmp`, `sources/`).
4. [references/search-rules.md](references/search-rules.md)의 쿼리 묶음으로 **WebSearch**를 순차 실행해 후보 URL을 수집한다.
5. 수집한 후보를 관련성 기준으로 필터링하고 `candidates_raw.json` 스키마로 정규화해 저장한다.
6. 고득점 후보 URL을 **WebFetch**로 열어 본문과 발행일을 검증한다.
7. 검증 통과 기사만 남겨 점수화·정렬·건수 상한을 적용하고 `verified_articles.json`으로 저장한다.
8. `verified_articles.json`에서 기사별 텍스트 파일(`sources/*.txt`)과 `notebook_manifest.json`을 Claude Write 도구로 생성한다.
9. `python scripts/notebooklm_gate.py <run_dir>/notebook_manifest.json --output-dir <run_dir>`를 실행한다.
10. `python scripts/render_dashboard.py <verified_json> <run_dir>/notebooklm_outputs.json <run_dir>/news_<week_id>.html <run_dir>/featured_article.json`를 실행한다.
11. `python scripts/notebooklm_slide_deck.py <run_dir>/notebooklm_outputs.json <verified_json> --output-dir <run_dir>`를 실행한다.
12. 결과물이 템플릿에서 벗어나면 `notebooklm_slide_deck.py`를 다시 실행하거나 NotebookLM `revise-slide`를 추가 적용한다.

## 무엇을 읽을지

- 전체 단계와 실패 규칙: [references/workflow.md](references/workflow.md)
- 기사 검색/선정 고정 규칙: [references/search-rules.md](references/search-rules.md)
- 슬라이드 프롬프트와 수정 규칙: [references/slide_prompt.md](references/slide_prompt.md)
- 출력 파일 계약: [references/output-contracts.md](references/output-contracts.md)

## 실행 전 주차 산출물 초기화

- 사용자가 별도로 요청하지 않아도 스킬 실행을 시작할 때마다 `<run_dir>` 기존 산출물을 재사용하지 않는다.
- Python 스크립트 대신 Claude 도구로 대상 파일만 삭제한다.
- 삭제 대상: `search_queries.json`, `candidates_raw.json`, `verified_articles*.json`, `notebook_manifest.json`, `notebooklm_outputs.json`, `featured_article.json`, `slide_deck_artifact.json`, `notebooklm_failure.json`, `news_*.html`, `news_slide_*.pdf`, `news_slide_*.pptx`, `*.tmp`, `sources/`
- 사용자가 따로 보관한 메모, 수동 검토 자료, 원본 입력 파일처럼 위 패턴에 맞지 않는 파일은 삭제하지 않는다.
