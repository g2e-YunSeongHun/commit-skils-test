# Workflow

## 목표

`news-scrap-codex`는 주간 응급의료 AI 기사 묶음을 검증된 JSON으로 고정한 뒤, NotebookLM으로 분석하고, 최종 슬라이드를 NotebookLM `slide-deck`로 생성한다.

## 단계

### 1. Scan

- 대상 주간의 국내/해외 기사와 논문 후보를 수집한다.
- `scripts/build_search_queries.py --output <run_dir>/search_queries.json`으로 주차별 query set을 만든다.
- broad query, site-pass query, 수동 URL 목록으로 raw search hit JSON 또는 URL 목록을 준비한다.
- raw search hit JSON 또는 URL 목록을 `scripts/scan_candidates.py`로 `candidates_raw.json`으로 정규화한다.
- 검색 쿼리, 소스 우선순위, 필수 도메인 순회 규칙은 [search-rules.md](search-rules.md)를 따른다.
- 국내 기사 `0건` 확정 전에는 국내 필수 도메인 전체에 대한 site-pass를 수행한다.
- broad query에서 잡히지 않는 기사 보완을 위해 `뇌졸중 AI`, `응급 CT 판독 AI`, `POCUS AI` 같은 질환/제품 축 보조 쿼리를 추가 수행한다.

### 2. Freeze

- `candidates_raw.json`에서 고득점 후보를 추려 `scripts/extract.py`로 검증한다.
- 응급의료 직접 관련 기사만 남긴다.
- 원문과 발행일을 확인한다.
- 중복 URL과 중복 기사 제목을 정리한다.
- `scripts/freeze_verified_articles.py`로 정렬과 건수 상한을 고정한다.
- 결과를 `verified_articles.json`으로 저장한다.

### 3. Build Manifest

- `scripts/build_notebook_sources.py`를 실행한다.
- 기사별 텍스트 파일과 `notebook_manifest.json`을 만든다.

### 4. NotebookLM Gate

- `scripts/notebooklm_gate.py`를 실행한다.
- 새 NotebookLM 노트를 만든다.
- 모든 기사 텍스트를 업로드하고 `ready` 상태를 기다린다.
- Q0~Q6 질문을 실행해 `notebooklm_outputs.json`을 만든다.
- Q6은 대표 기사 제목을 기계적으로 읽을 수 있는 형식으로 남긴다.

### 5. Slide Deck

- `scripts/render_dashboard.py`를 먼저 실행한다.
- `verified_articles.json`과 `notebooklm_outputs.json`을 바탕으로 `news_<week_id>.html`을 만든다.
- `scripts/notebooklm_slide_deck.py`를 실행한다.
- Q6과 기사 목록을 사용해 대표 기사를 고른다.
- `references/slide_prompt.md`의 메인 프롬프트로 5장 슬라이드 덱을 생성한다.
- 슬라이드 1~5에 대해 `revise-slide`를 순차 적용해 구조를 보정한다.
- 최종 덱을 PDF와 PPTX로 다운로드한다.

## 실패 규칙

- NotebookLM 로그인 또는 권한 확인 실패
- 노트 생성 실패
- 소스 업로드 또는 소스 `ready` 대기 실패
- Q0~Q6 중 하나라도 실패
- slide-deck 생성 또는 revise-slide 실패
- PDF/PPTX 다운로드 실패

위 경우 즉시 종료하고 `notebooklm_failure.json`을 남긴다.

## 산출물

- `candidates_raw.json`
- `verified_articles.json`
- `notebook_manifest.json`
- `notebooklm_outputs.json`
- `featured_article.json`
- `slide_deck_artifact.json`
- `news_<week_id>.html`
- `news_slide_<week_id>.pdf`
- `news_slide_<week_id>.pptx`
