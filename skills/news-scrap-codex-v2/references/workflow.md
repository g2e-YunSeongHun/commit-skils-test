# Workflow

## 목표

`news-scrap-codex-v2`는 주간 의료 AI·응급의료 AI·응급실 AI·중환자실 AI 기사 묶음을 Codex가 검색·검증·요약한 뒤, `news_briefing.md` 하나를 기준으로 HTML 대시보드와 Pencil PDF 슬라이드를 만든다.

## 단계

### 1. Reset

- 대상 주차와 `<run_dir>`를 정한다.
- 재실행이면 `python scripts/reset_week_outputs.py <run_dir>`를 실행한다.
- 모든 중간 파일은 `<work_dir> = <run_dir>/_work`에 둔다.

### 2. Search

- `scripts/build_search_queries.py --output <work_dir>/search_queries.json`로 주차별 검색 세트를 만든다.
- Codex가 최신 웹 검색으로 국내/해외 기사 후보를 수집한다.
- 국내 기사가 0건처럼 보이면 국내 필수 도메인 site-pass를 수행하고, 의료 AI/응급의료 AI/응급실 AI/중환자실 AI/의료기기 AI/의료영상 AI 보조 검색어를 다시 돌린다.
- 검색 규칙은 [search-rules.md](search-rules.md)를 따른다.

### 3. Verify

- 후보 URL은 `scripts/extract.py`로 본문과 발행일을 확인한다.
- 발행일이 대상 기간 밖이면 제외한다.
- 원문 검증이 어려운 페이지, 중복 본문, 본문 불충분 기사는 제외한다.
- 제목보다 본문 맥락을 우선한다. 응급실, 응급의료, 중환자실, 의료기관 진료, 의료기기·의료영상 맥락이 본문에서 확인되면 포함 후보로 둔다.

### 4. Write Briefing Markdown

- Codex가 검증된 기사 목록, 한국어 요약, 대표 기사, 심층 리서치, Pencil 템플릿 자리값을 `<work_dir>/news_briefing.md`에 작성한다.
- 구조는 [briefing-md-contract.md](briefing-md-contract.md)를 따른다.
- 해외 기사 요약은 영어 요약을 그대로 두지 않고 한국어로 자연스럽게 다듬는다.
- 대표 기사 선정 이유에는 내부 점수나 후보 순위를 쓰지 않는다.
- 슬라이드 섹션은 `bind.*` 템플릿에 들어갈 값이므로 비어 있는 항목을 최소화한다.

### 5. Dashboard

- `python scripts/render_dashboard_from_md.py <work_dir>/news_briefing.md <run_dir>/news_<week_id>.html`를 실행한다.
- HTML 파일명은 `news_26년_5월_1주차.html` 형식으로 정규화된다.
- 해외 기사 요약이 한국어로 보이지 않으면 렌더링 실패로 본다. 이 경우 `news_briefing.md`의 해당 요약을 다시 번역·검토한다.

### 6. Pencil Slide PDF

- `python scripts/build_pencil_slide_spec_from_md.py <work_dir>/news_briefing.md <work_dir> --week-id <week_id>`로 `<work_dir>/pencil_slide_spec.json`을 만든다.
- spec의 `template.mode`는 `update_named_bindings`이고, 실제 채울 값은 `template_bindings`에 들어간다.
- `python scripts/prepare_pencil_template.py <work_dir> --spec-json <work_dir>/pencil_slide_spec.json`로 기존 Pencil 템플릿을 주차별 `.pen` 파일로 복사한다.
- `python scripts/apply_pencil_bindings.py <work_dir>/news_slide_<week_id>.pen <work_dir>/pencil_slide_spec.json --strict`로 `bind.*` text node를 갱신한다.
- 빈 binding은 빈 문자열로 두고, 해당되는 반복 카드 frame은 `enabled:false`로 숨긴다.
- Pencil에서 갱신된 `.pen` 파일을 열거나 Pencil MCP `open_document(path=...)`로 active editor로 만든다.
- `content.slide1`~`content.slide4` 내부 scaffold는 삭제하지 않는다.
- 반복 binding은 조사된 만큼만 표시한다. 빈 point, capability, offering, fact, meaning 카드는 억지로 채우지 않는다.
- `snapshot_layout(problemsOnly=true)`로 clipping을 확인한다.
- Pencil MCP `export_nodes(format="pdf")`로 4개 frame을 하나의 PDF로 export한다.
- `python scripts/finalize_pencil_slide_pdf.py <exported_pdf> <run_dir> --spec-json <work_dir>/pencil_slide_spec.json --pen-file <work_dir>/news_slide_<week_id>.pen --work-dir <work_dir>`로 최종 파일명을 `news_slide_26년_5월_1주차.pdf`로 정규화하고 `<work_dir>`를 삭제한다.

## 실패 규칙

- `news_briefing.md` 필수 섹션 누락
- 해외 기사 요약이 한국어로 보이지 않음
- Pencil 템플릿 파일 복사 또는 열기 실패
- `bind.*` node 검색 또는 업데이트 실패
- 슬라이드가 4장이 아닌 상태
- layout clipping 발생
- PDF export 실패
- `finalize_pencil_slide_pdf.py` 정규화 실패

이 경우 즉시 종료하고, 가능하면 `<work_dir>/pencil_failure.json` 또는 실행 로그에 실패 단계와 원인을 남긴다.

## 최종 산출물

- `news_26년_5월_1주차.html`
- `news_slide_26년_5월_1주차.pdf`

작업용 JSON, Markdown, `.pen` 파일은 `<run_dir>/_work/`에서만 사용하고 성공 후 삭제한다. 디버깅이 필요하면 `finalize_pencil_slide_pdf.py`에 `--keep-work-dir`를 사용한다.
