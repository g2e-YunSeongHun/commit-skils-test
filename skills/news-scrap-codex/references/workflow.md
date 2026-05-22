# Workflow

## 목표

`news-scrap-codex`는 주간 의료 AI·응급의료 AI·응급실 AI·중환자실 AI 기사 묶음을 검증된 JSON으로 고정한 뒤, Codex가 요약·대표 기사 선정·심층 리서치를 수행하고, NotebookLM은 최종 `slide-deck` 생성에만 사용한다.

## 단계

### 1. Scan

- 대상 주간의 국내/해외 의료 AI, 응급의료 AI, 응급실 AI, 중환자실 AI 기사 후보를 수집한다.
- `scripts/build_search_queries.py --output <run_dir>/search_queries.json`으로 주차별 query set을 만든다.
- broad query, site-pass query, 수동 URL 목록으로 raw search hit JSON 또는 URL 목록을 준비한다.
- raw search hit JSON 또는 URL 목록을 `scripts/scan_candidates.py`로 `candidates_raw.json`으로 정규화한다.
- 검색 쿼리, 소스 우선순위, 필수 도메인 순회 규칙은 [search-rules.md](search-rules.md)를 따른다.
- 국내 기사 `0건` 확정 전에는 국내 필수 도메인 전체에 대한 site-pass를 수행한다.
- broad query에서 잡히지 않는 기사 보완을 위해 `의료 AI`, `의료기기 AI`, `의료 영상 AI`, `중환자실 AI`, `응급의료 AI`, `응급실 AI`, `119 AI 신고접수`, `응급실 AI 문서화`, `응급 CT 판독 AI` 같은 의료/응급/중환자의료 축 보조 쿼리를 추가 수행한다.

### 2. Freeze

- `candidates_raw.json`에서 고득점 후보를 추려 `scripts/extract.py`로 검증한다.
- 의료 AI, 응급의료 AI, 응급실 AI, 중환자실 AI와 직접 관련된 기사만 남긴다.
- 원문과 발행일을 확인한다.
- 중복 URL과 중복 기사 제목을 정리한다.
- HTML 대시보드에 노출할 기사 요약은 `요약` 또는 `summary_ko` 필드에 한국어로 저장한다. 해외 기사는 영어 요약을 그대로 붙이지 않고, 핵심 의미를 한국어로 번역한 뒤 자연스러운지 검토해 별도 요약으로 둔다.
- `scripts/freeze_verified_articles.py`로 정렬과 건수 상한을 고정한다.
- 결과를 `verified_articles.json`으로 저장한다.

### 3. Codex Selection

- `scripts/select_featured_article.py`를 실행한다.
- `featured_article.json`, `selection_report.json`, `article_summaries.json`을 만든다.
- 대표 기사 선정 기준은 의료/응급/중환자의료 AI 관련성, AI 역할 명확성, 도입/검증/제품화 구체성, 소스 완결성, 주간 대표성이다.
- NotebookLM에는 대표 기사 선정을 맡기지 않는다.

### 4. Focused Research

- Codex가 대표 기사에 대해 심층 리서치를 수행한다.
- 리서치 대상은 대표 기사에 등장한 핵심 기관, 기업, 기술명, 제품명, 연구명이다.
- 공식 발표, 논문, 제품 페이지, 규제·인허가 자료, 병원·기관 공지를 우선한다.
- 리서치 구조는 최종 4장 슬라이드와 1:1로 맞춘다: `이번 주 핵심 팩트`, `AI 기술 설명`, `회사·기관 팩트시트`, `이번 주 인사이트`.
- 각 섹션은 확인된 사실, 근거 URL, 소스에서 확인되지 않은 항목을 분리한다. 추론은 `이번 주 인사이트` 안에서만 시사점으로 작성한다.
- 결과를 `<run_dir>/featured_research.md`에 한국어로 정리한다.
- `scripts/build_featured_deck_source.py`는 `featured_research.md`에 위 4개 섹션이 없으면 실패한다.

### 5. Dashboard

- `scripts/render_dashboard.py`를 실행한다.
- `verified_articles.json`만으로 `news_<week_id>.html`을 만든다.
- 렌더러는 `요약`, `한국어요약`, `summary_ko`, `korean_summary`를 본문보다 우선 사용한다.
- 해외기사 요약이 한국어로 보이지 않으면 렌더러가 실패한다. 이 경우 Codex가 해당 기사 요약을 다시 번역하고 어색한 직역, 과도한 영어 표현, 원문 의미 누락을 검토한 뒤 재실행한다.

### 6. NotebookLM Slide Deck

- `scripts/build_featured_deck_source.py`를 실행한다.
- 대표 기사 원문, 공개용 선정 배경, Codex 심층 리서치를 하나의 NotebookLM 소스로 묶어 `notebook_manifest.json`을 만든다.
- NotebookLM 소스와 최종 PPT/PDF에는 내부 선정 점수, 기준별 점수표, 후보 순위 비교, rubric을 포함하지 않는다.
- `scripts/notebooklm_upload_sources.py`를 실행한다.
- 새 NotebookLM 노트를 만들고 슬라이드용 소스만 업로드한 뒤 `ready` 상태를 기다린다.
- `notebooklm_session.json`에 노트 ID와 업로드된 소스 ID를 저장한다.
- `scripts/notebooklm_slide_deck.py`를 실행한다.
- `featured_article.json`을 사용해 대표 기사를 고정한다.
- `references/slide_prompt.md`의 메인 프롬프트로 4장 슬라이드 덱을 생성한다.
- 슬라이드 1~4에 대해 `revise-slide`를 순차 적용해 구조를 보정한다.
- 최종 덱을 PDF와 PPTX로 다운로드한다.

## 실패 규칙

- NotebookLM 로그인 또는 권한 확인 실패
- 노트 생성 실패
- 소스 업로드 또는 소스 `ready` 대기 실패
- slide-deck 생성 또는 revise-slide 실패
- PDF/PPTX 다운로드 실패

위 경우 즉시 종료하고 `notebooklm_failure.json`을 남긴다.

## 산출물

- `candidates_raw.json`
- `verified_articles.json`
- `article_summaries.json`
- `selection_report.json`
- `notebook_manifest.json`
- `notebooklm_session.json`
- `featured_article.json`
- `featured_research.md`
- `slide_deck_artifact.json`
- `news_<week_id>.html`
- `news_slide_<week_id>.pdf`
- `news_slide_<week_id>.pptx`

## Run Directory Reset

At the start of every run, after choosing the target week and `<run_dir>`, run:

```bash
python scripts/reset_week_outputs.py <run_dir>
```

If `<run_dir>` does not exist, the script skips reset. If it exists, the script deletes only generated artifacts in `<run_dir>`: `search_queries.json`, `candidates_raw.json`, `verified_articles*.json`, `notebook_manifest.json`, `notebooklm_session.json`, `featured_article.json`, `selection_report.json`, `article_summaries.json`, `featured_research.md`, `featured_research.json`, `slide_deck_artifact.json`, `notebooklm_failure.json`, `news_*.html`, `news_slide_*.pdf`, `news_slide_*.pptx`, `*.tmp`, and `sources/`. It also deletes the legacy `notebooklm_outputs.json` if present. It leaves unrelated manual files alone. After reset, repeat the full workflow from scan through Codex selection, focused research, dashboard, and NotebookLM slide-deck download.

If the user provides a preverified JSON input, keep that source file outside `<run_dir>` or write it back into `<run_dir>` only after reset.
