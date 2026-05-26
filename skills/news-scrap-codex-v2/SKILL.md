---
name: news-scrap-codex-v2
description: Codex용 의료·응급의료 AI 주간 뉴스 브리핑 스킬. Use when creating a Korean weekly medical AI briefing covering medical AI, emergency-medicine AI, emergency department AI, and ICU/critical-care AI, where Codex searches, verifies, summarizes, writes one structured Markdown briefing, fills a fixed Pencil template, and exports a PDF briefing.
---

# 의료·응급의료 AI 뉴스 브리핑 v2 for Codex

모든 출력은 한국어로 작성한다.

## 언제 이 스킬을 쓰는가

- 주간 의료 AI, 응급의료 AI, 응급실 AI, 중환자실 AI 기사 브리핑을 만들어야 할 때
- Codex가 직접 웹 검색, 원문 검증, 기사 요약, 대표 기사 선정, 심층 리서치를 수행해야 할 때
- 최종 산출물을 HTML 1개와 Pencil 기반 PDF 슬라이드 1개로만 남겨야 할 때
- 고정된 4장 Pencil 템플릿의 slot text만 바꿔 팩트 기반 슬라이드를 만들어야 할 때

## 핵심 규칙

- 최종 산출물은 `<run_dir>/news_26년_5월_1주차.html`과 `<run_dir>/news_slide_26년_5월_1주차.pdf` 두 개만 남긴다.
- NotebookLM과 PPTX는 사용하지 않는다.
- Codex는 검색·검증·요약·대표 기사 선정·심층 리서치 결과를 `<work_dir>/news_briefing.md` 하나로 구조화한다.
- HTML과 Pencil 슬라이드 spec은 모두 `news_briefing.md`에서 생성한다. `verified_articles.json`은 v1 호환용 helper 입력일 뿐, v2 기본 원본이 아니다.
- 작업용 JSON, Markdown, `.pen` 파일은 `<work_dir> = <run_dir>/_work` 아래에서만 사용하고 성공 후 삭제한다.
- HTML과 PDF에는 내부 점수, 후보 순위, 스코어링 기준, rubric을 넣지 않는다.
- 해외 기사 요약도 HTML에 들어가는 문장은 한국어로 번역하고, 어색한 직역·영어 잔재·의미 누락을 검토한다.
- 국내 기사가 0건처럼 보이면 바로 확정하지 말고 국내 필수 도메인 site-pass와 보조 검색어를 다시 수행한다.

## 수집 범위

포함 범위는 의료 AI, 응급의료 AI, 응급실 AI, 중환자실 AI다. 의료기기 AI, 의료영상 AI, 진단 AI도 병원 진료, 응급의료, 중환자의료 맥락이 있으면 포함할 수 있다.

아래 주제는 단독으로는 제외한다.

- 퇴원 후 관리
- 예후 예측
- 일반 환자 관리
- 재택의료
- 병상 배정, patient flow, hospital command center 같은 병원 운영 자동화

단, 위 주제라도 원문에서 응급실, 응급의료, 중환자실, 급성 악화 조기 인지, 의료진 의사결정 지원과 직접 연결되면 포함 후보로 볼 수 있다.

## 실행 순서

1. 기사 범위 날짜를 계산한다.
2. 같은 주차 `<run_dir>`를 정한 뒤 `python scripts/reset_week_outputs.py <run_dir>`를 먼저 실행한다.
3. `<work_dir>`는 `<run_dir>/_work`로 둔다.
4. `python scripts/build_search_queries.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --format json --output <work_dir>/search_queries.json`로 검색 힌트를 만든다.
5. Codex가 웹 검색을 수행하고 raw hit 또는 URL 목록을 준비한다. 검색 규칙은 [references/search-rules.md](references/search-rules.md)를 따른다.
6. 필요하면 `python scripts/scan_candidates.py <input_json> --start-date YYYY-MM-DD --end-date YYYY-MM-DD --output <work_dir>/candidates_raw.json`로 후보를 정규화한다.
7. 후보 URL은 `python scripts/extract.py`로 원문, 날짜, 본문을 확인한다.
8. Codex가 검증된 기사, 한국어 요약, 대표 기사, 심층 리서치, 4장 슬라이드 내용을 `<work_dir>/news_briefing.md`로 작성한다. 구조는 [references/briefing-md-contract.md](references/briefing-md-contract.md)를 따른다.
9. `python scripts/render_dashboard_from_md.py <work_dir>/news_briefing.md <run_dir>/news_<week_id>.html`로 HTML 대시보드를 만든다.
10. `python scripts/build_pencil_slide_spec_from_md.py <work_dir>/news_briefing.md <work_dir> --week-id <week_id>`로 Pencil slot 값을 포함한 슬라이드 spec을 만든다.
11. `python scripts/prepare_pencil_template.py <work_dir> --spec-json <work_dir>/pencil_slide_spec.json`로 기준 Pencil 템플릿을 주차별 작업 파일로 복사한다.
12. 복사된 `<work_dir>/news_slide_<week_id>.pen` 파일을 Pencil에서 열거나 Pencil MCP `open_document(path=...)`로 active editor로 만든다.
13. [references/pencil-template-contract.md](references/pencil-template-contract.md)에 따라 `slot.` text node의 `content`만 업데이트한다.
14. Pencil MCP `export_nodes(format="pdf")`로 slide frame 4개를 PDF로 export한다.
15. `python scripts/finalize_pencil_slide_pdf.py <exported_pdf> <run_dir> --spec-json <work_dir>/pencil_slide_spec.json --pen-file <work_dir>/news_slide_<week_id>.pen --work-dir <work_dir>`로 PDF 파일명을 정규화하고 `_work`를 삭제한다.

## 무엇을 읽을지

- 전체 workflow: [references/workflow.md](references/workflow.md)
- 검색·선정 규칙: [references/search-rules.md](references/search-rules.md)
- `news_briefing.md` 구조: [references/briefing-md-contract.md](references/briefing-md-contract.md)
- 대표 기사 심층 리서치 기준: [references/research_prompt.md](references/research_prompt.md)
- Pencil 슬라이드 제작 기준: [references/pencil-slide-guide.md](references/pencil-slide-guide.md)
- Pencil 템플릿 slot 계약: [references/pencil-template-contract.md](references/pencil-template-contract.md)
- 출력 파일 계약: [references/output-contracts.md](references/output-contracts.md)

## 포함 스크립트

- `scripts/build_search_queries.py`: 주차별 검색어와 site-pass 힌트를 생성한다.
- `scripts/scan_candidates.py`: raw search hit 또는 URL 목록을 후보 JSON으로 정규화한다.
- `scripts/extract.py`: 후보 URL의 본문과 발행일을 추출해 검증 단계에 사용한다.
- `scripts/render_dashboard_from_md.py`: `news_briefing.md`에서 최종 HTML 대시보드를 만든다.
- `scripts/build_pencil_slide_spec_from_md.py`: `news_briefing.md`에서 Pencil template slot 값을 만든다.
- `scripts/prepare_pencil_template.py`: 기준 `.pen` 템플릿을 주차별 작업 파일로 복사한다.
- `scripts/finalize_pencil_slide_pdf.py`: Pencil MCP가 export한 PDF를 `news_slide_<week_id>.pdf`로 정규화하고 기본적으로 `_work`를 삭제한다.
- `scripts/reset_week_outputs.py`: 같은 주차 재실행 전에 기존 생성물을 삭제한다.

호환용 helper인 `freeze_verified_articles.py`, `select_featured_article.py`, `render_dashboard.py`, `build_pencil_slide_spec.py`는 남겨 두지만 v2 기본 경로에서는 `news_briefing.md`를 원본으로 사용한다.
