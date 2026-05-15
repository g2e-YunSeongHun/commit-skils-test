# Workflow

## 목표

`news-scrap-claude`는 Claude의 WebSearch/WebFetch 도구로 기사를 수집·검증·고정한 뒤, news-scrap-codex와 동일한 NotebookLM 파이프라인으로 분석과 슬라이드를 생성한다.

## 단계

### 1. Scan (Claude WebSearch)

- 대상 주간의 국내/해외 기사 후보를 수집한다.
- [search-rules.md](search-rules.md)의 쿼리 묶음을 순서대로 WebSearch로 실행한다.
- broad query, 필수 도메인 site-pass query(예: `site:medicaltimes.com 응급 AI`), 보조 운영 쿼리를 모두 수행한다.
- 국내 기사 `0건` 확정 전에는 국내 필수 도메인 전체에 대한 site-pass와 `119/구급/응급실 운영/병상/문서화` 축 보조 쿼리를 추가 수행한다.
- 수집한 후보를 `candidates_raw.json` 스키마로 정규화해 저장한다.
- 논문/프리프린트는 사용자 명시 요청 시에만 보조 후보로 수집한다.

### 2. Freeze (Claude WebFetch)

- `candidates_raw.json`의 고득점 후보 URL을 WebFetch로 열어 본문과 발행일을 검증한다.
- 발행일이 범위를 벗어나면 제외한다.
- 원문 확인이 안 되는 재배포 단문은 제외한다.
- 중복 URL과 중복 기사 제목을 정리한다.
- [search-rules.md](search-rules.md)의 점수화·정렬 규칙을 적용해 건수 상한을 고정한다.
- 결과를 `verified_articles.json`으로 저장한다.

#### WebFetch 403 처리 규칙

일부 해외 도메인(`healthcareitnews.com`, `beckershospitalreview.com`, `fiercehealthcare.com` 등)은 WebFetch를 차단한다. 이 경우:

1. 검색 결과 스니펫에서 발행일과 핵심 내용을 추출한다.
2. 스니펫에서 발행일이 확인되고 응급의료 AI 직접 관련성이 명확하면 `snippet_verified: true`로 표시해 후보에 포함한다.
3. 스니펫으로 발행일을 확인할 수 없으면 제외한다.
4. `verified_articles.json`의 해당 기사에 `"verified_method": "snippet"` 필드를 추가해 구분한다.
5. snippet 검증 기사는 건수 상한에 포함하되, 동점이면 WebFetch로 전문 검증된 기사를 우선한다.

### 3. Build Manifest (Claude Write)

- `verified_articles.json`의 각 기사를 개별 텍스트 파일(`sources/<순번>_<제목>.txt`)로 저장한다.
- 텍스트 파일 경로 목록과 메타데이터를 담은 `notebook_manifest.json`을 저장한다.
- 스키마는 [output-contracts.md](output-contracts.md)를 따른다.

### 4. NotebookLM Gate (notebooklm_gate.py — news-scrap-codex와 동일)

- `python scripts/notebooklm_gate.py <run_dir>/notebook_manifest.json --output-dir <run_dir>`를 실행한다.
- 새 NotebookLM 노트를 만든다.
- 모든 기사 텍스트를 업로드하고 `ready` 상태를 기다린다.
- Q0~Q6 질문을 실행해 `notebooklm_outputs.json`을 만든다.
- Q6은 대표 기사 제목을 기계적으로 읽을 수 있는 형식으로 남긴다.

### 5. Slide Deck (render_dashboard.py + notebooklm_slide_deck.py — news-scrap-codex와 동일)

- `python scripts/render_dashboard.py <verified_json> <run_dir>/notebooklm_outputs.json <run_dir>/news_<week_id>.html <run_dir>/featured_article.json`를 실행한다.
- `python scripts/notebooklm_slide_deck.py <run_dir>/notebooklm_outputs.json <verified_json> --output-dir <run_dir>`를 실행한다.
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

## Run Directory Reset

스킬 실행 시작 시, Claude 도구로 `<run_dir>` 안의 아래 파일/폴더를 직접 삭제한다.

대상: `search_queries.json`, `candidates_raw.json`, `verified_articles*.json`, `notebook_manifest.json`, `notebooklm_outputs.json`, `featured_article.json`, `slide_deck_artifact.json`, `notebooklm_failure.json`, `news_*.html`, `news_slide_*.pdf`, `news_slide_*.pptx`, `*.tmp`, `sources/`

`<run_dir>` 자체가 없으면 건너뛴다. 위 패턴 외 파일(사용자 메모, 수동 검토 자료 등)은 삭제하지 않는다.

사용자가 검증 완료 JSON을 직접 제공하는 경우, 그 입력 파일은 `<run_dir>` 밖에 두고 초기화 후 새 산출물 경로에 복사하거나 별도 출력 경로를 지정한다.
