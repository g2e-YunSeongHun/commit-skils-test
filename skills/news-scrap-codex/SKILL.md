---
name: news-scrap-codex
description: Codex용 의료·응급의료 AI 주간 뉴스 브리핑 스킬. Use when creating a Korean weekly medical AI briefing covering medical AI, emergency-medicine AI, emergency department AI, and ICU/critical-care AI, where Codex searches, verifies, summarizes, selects one featured article with rule-based scoring, performs focused research, and NotebookLM is used only to generate the final slide deck.
---

# 의료·응급의료 AI 뉴스 브리핑 for Codex

모든 출력은 한국어로 작성한다.

## 언제 이 스킬을 쓰는가

- 주간 의료 AI, 응급의료 AI, 응급실 AI, 중환자실 AI 기사 브리핑을 만들어야 할 때
- 국내/해외 기사 검증 후 `verified_articles.json`을 기준점으로 삼을 때
- 기사, 현장 도입, 운영 개선, 제품 통합/제휴, 의료기기·의료영상, 중환자의료 AI 중심으로 수집해야 할 때
- NotebookLM은 최종 `slide-deck` 생성기로만 쓰고, 기사 판단은 Codex가 맡아야 할 때
- 최종 슬라이드를 `python-pptx`가 아니라 NotebookLM `slide-deck`로 생성해야 할 때

## 핵심 규칙

- 이 작업은 최신 기사에 의존하므로 기사 수집 단계에서는 반드시 웹 검색과 검증을 사용한다.
- 국내 기사가 비어 보이면 바로 `0건`으로 확정하지 말고, `필수 도메인 순회`와 `의료 AI/응급의료 AI/응급실 AI/중환자실 AI/의료기기·의료영상 AI 보조 검색`을 먼저 수행한다.
- 기본 수집은 국내/해외 기사 원문 중심이다.
- `의료 AI`, `의료기기 AI`, `의료 영상 AI`, `응급의료 AI`, `응급실 AI`, `중환자실/ICU AI`, `트리아지`는 기본 수집 축에 포함한다.
- 일반 소방 AI/로봇/위원회 기사는 119·구급·응급의료 또는 의료기관 진료 맥락이 없으면 제외한다.
- 해외 수집은 실제 도입·제품·제휴·인허가 기사를 우선한다.
- 대표 기사 선정은 NotebookLM에 맡기지 않는다. Codex가 `select_featured_article.py`의 룰베이스 점수와 기사 맥락 검토를 함께 사용해 1건을 선정한다.
- 대표 기사 선정 후 Codex가 해당 기사에 등장하는 핵심 기관, 기업, 기술, 연구를 추가 리서치해 `featured_research.md`로 정리한다. 이 리서치는 최종 4장 슬라이드 구조(`이번 주 핵심 팩트`, `AI 기술 설명`, `회사·기관 팩트시트`, `이번 주 인사이트`)와 같은 섹션으로 작성한다.
- NotebookLM은 Codex가 만든 대표 기사 소스와 슬라이드 가이드만 받아 slide-deck을 생성한다. NotebookLM에 주간 대표 기사 재선정이나 추가 리서치를 요청하지 않는다.
- NotebookLM 슬라이드용 소스와 최종 PPT/PDF에는 내부 선정 점수, 기준별 점수표, 후보 순위 비교, rubric을 포함하지 않는다.
- NotebookLM slide-deck 단계가 실패하면 전체 작업을 실패로 간주한다.
- 새 실행마다 새 NotebookLM 노트를 만든다.
- 최종 슬라이드는 [references/slide_prompt.md](references/slide_prompt.md)의 4장 팩트 기반 구조와 디자인 가이드를 따른다.
- 기본 경로는 `verified_articles.json -> featured_article.json/selection_report.json -> featured_research.md -> notebook_manifest.json -> notebooklm_session.json -> slide_deck_artifact.json`이다.
- HTML 대시보드도 기본 산출물이다.
- 기본 슬라이드 생성 경로에서 `python-pptx`는 사용하지 않는다.

## 입력 기준

- 권장 입력: `verified_articles.json`
- 이 파일이 없으면 Codex가 먼저 기사 수집, 중복 제거, 원문 검증을 수행해 같은 스키마로 고정한다.
- 기사 수집 규칙과 건수 상한은 [references/search-rules.md](references/search-rules.md)를 따른다.
- 영문 기사 제목은 가능하면 `번역제목`과 `원제목`을 함께 저장하고, HTML은 `번역제목`을 우선 노출한다.
- HTML 대시보드에 노출될 기사 요약은 한국어로 작성한다. 원문이 영어여도 먼저 핵심 요약을 만든 뒤 한국어로 번역하고, 어색한 직역·영어 잔재·의미 누락이 없는지 검토해 `verified_articles.json`의 `요약` 또는 `summary_ko` 필드에 저장한다.
- 스키마는 [references/output-contracts.md](references/output-contracts.md)를 따른다.

## 실행 순서

1. 기사 범위를 계산한다.
2. 해당 주차 `<run_dir>`를 정한 뒤 `python scripts/reset_week_outputs.py <run_dir>`를 먼저 실행한다. 폴더가 없으면 건너뛰고, 기존 생성물이 있으면 삭제한다.
3. `python scripts/build_search_queries.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --format json --output <run_dir>/search_queries.json`으로 주차별 검색 세트를 만든다.
4. broad query, site-pass query, 수동 URL 목록 중 하나로 raw search hit JSON 또는 URL 목록을 준비한다.
5. `python scripts/scan_candidates.py <input_json> --start-date YYYY-MM-DD --end-date YYYY-MM-DD --output <run_dir>/candidates_raw.json`로 정규화한다.
6. `candidates_raw.json`의 후보 URL을 `python scripts/extract.py`로 검증한다.
7. 검증된 기사만으로 `verified_articles.json`을 준비한다. 각 기사에는 HTML 렌더링용 한국어 요약(`요약` 또는 `summary_ko`)을 넣는다. 해외 기사는 영어 요약을 그대로 넣지 말고 한국어 번역본을 자연스럽게 다듬은 뒤 사용한다.
8. `python scripts/freeze_verified_articles.py <verified_json>`로 기사 순서와 건수 상한을 고정한다.
9. `python scripts/select_featured_article.py <verified_json> --output-dir <run_dir>`로 대표 기사, 기사별 요약, 선정 리포트를 만든다.
10. Codex가 대표 기사에 대해 심층 리서치를 수행하고 `<run_dir>/featured_research.md`에 정리한다. 리서치는 기사에 등장한 핵심 기관/기업/기술/연구의 공식 발표, 논문, 제품 페이지, 규제·인허가 자료를 우선하며 [references/research_prompt.md](references/research_prompt.md)의 4개 섹션을 그대로 따른다.
11. `python scripts/render_dashboard.py <verified_json> <run_dir>/news_<week_id>.html`로 HTML 대시보드를 만든다.
12. `python scripts/build_featured_deck_source.py <verified_json> <run_dir>/featured_article.json <run_dir> --selection-report <run_dir>/selection_report.json --research-md <run_dir>/featured_research.md`로 NotebookLM 슬라이드용 단일 소스와 manifest를 만든다.
13. `python scripts/notebooklm_upload_sources.py <run_dir>/notebook_manifest.json --output-dir <run_dir>`로 새 NotebookLM 노트에 슬라이드용 소스만 업로드한다.
14. `python scripts/notebooklm_slide_deck.py <run_dir>/notebooklm_session.json --featured-article-json <run_dir>/featured_article.json --output-dir <run_dir>`를 실행한다.
15. 결과물이 템플릿에서 벗어나면 `notebooklm_slide_deck.py`를 다시 실행하거나 NotebookLM `revise-slide`를 추가 적용한다.

## 무엇을 읽을지

- 전체 단계와 실패 규칙: [references/workflow.md](references/workflow.md)
- 기사 검색/선정 고정 규칙: [references/search-rules.md](references/search-rules.md)
- 대표 기사 심층 리서치 작성 규칙: [references/research_prompt.md](references/research_prompt.md)
- 슬라이드 프롬프트와 수정 규칙: [references/slide_prompt.md](references/slide_prompt.md)
- 출력 파일 계약: [references/output-contracts.md](references/output-contracts.md)

## 포함 스크립트

- `scripts/build_search_queries.py`
  기간별 핵심 검색어, 보조 검색어, 필수 도메인 site-pass 쿼리를 생성한다.
- `scripts/scan_candidates.py`
  raw search hit 또는 URL 목록을 `candidates_raw.json` 형식으로 정규화하고 노이즈 도메인을 제거한다.
- `scripts/extract.py`
  후보 URL에서 본문과 발행일을 일괄 추출해 검증 단계에 사용한다.
- `scripts/freeze_verified_articles.py`
  기사 중복 제거, 점수화, 정렬, 섹션별 건수 상한 적용을 수행한다.
- `scripts/select_featured_article.py`
  `verified_articles.json`에서 기사별 요약, 룰베이스 대표 기사 선정, 선정 리포트를 만든다.
- `scripts/build_featured_deck_source.py`
  대표 기사, 공개용 선정 배경, Codex 심층 리서치, 원문을 하나의 NotebookLM slide-deck 소스로 묶는다. 내부 점수와 후보 비교는 제외한다.
- `scripts/notebooklm_upload_sources.py`
  새 노트를 만들고 슬라이드용 소스를 업로드한 뒤 `notebooklm_session.json`을 저장한다.
- `scripts/reset_week_outputs.py`
  스킬 실행 시작 시 같은 주차 `<run_dir>`에 남아 있는 기존 생성물을 삭제한다.
- `scripts/render_dashboard.py`
  `verified_articles.json`에서 주간 HTML 대시보드를 만든다. 해외기사 대시보드 요약이 한국어로 보이지 않으면 실패한다.
- `scripts/notebooklm_slide_deck.py`
  Codex가 선정한 `featured_article.json`을 기준으로 NotebookLM `slide-deck` 생성, `revise-slide`, PPTX/PDF 다운로드를 수행한다.

## 실행 전 주차 산출물 초기화

- 사용자가 별도로 요청하지 않아도 스킬 실행을 시작할 때마다 해당 주차 `<run_dir>`의 기존 산출물을 재사용하지 않는다.
- 같은 주차의 기존 `<run_dir>`를 유지하되, 검색이나 NotebookLM 작업을 시작하기 전에 `python scripts/reset_week_outputs.py <run_dir>`를 실행해 스킬이 만든 생성물만 삭제한다.
- 이 초기화는 `search_queries.json`, `candidates_raw.json`, `verified_articles*.json`, `notebook_manifest.json`, `notebooklm_session.json`, `featured_article.json`, `selection_report.json`, `article_summaries.json`, `featured_research.md`, `featured_research.json`, `slide_deck_artifact.json`, `notebooklm_failure.json`, `news_*.html`, `news_slide_*.pdf`, `news_slide_*.pptx`, `*.tmp`, `sources/`만 대상으로 한다. 이전 버전 산출물인 `notebooklm_outputs.json`도 함께 정리 대상에 포함한다.
- 사용자가 따로 보관한 메모, 수동 검토 자료, 원본 입력 파일처럼 위 패턴에 맞지 않는 파일은 삭제하지 않는다.
- 사용자가 검증 완료 JSON을 직접 제공하는 경우, 그 입력 파일은 `<run_dir>` 밖에 두고 초기화 후 새 `<run_dir>` 산출물로 복사하거나 별도 출력 경로를 지정한다.
- 초기화 후에는 검색, 후보 정리, 검증, Codex 대표 기사 선정, Codex 심층 리서치, HTML, NotebookLM slide-deck까지 처음부터 다시 수행한다.
