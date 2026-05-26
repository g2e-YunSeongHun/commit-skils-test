# Pencil Slide Guide

이 문서는 `news_briefing.md`에서 생성한 `pencil_slide_spec.json`을 바탕으로 Pencil MCP에서 4장짜리 PDF 슬라이드를 export하는 기준이다. 디자인은 반고정 템플릿에 두고, 본문은 각 장의 `content.slideN` frame 안에 새로 배치한다.

## 기본 원칙

- 슬라이드는 정확히 4장이다.
- 모든 문구는 한국어로 작성한다.
- 슬라이드 제목은 `이번 주 대표 기사`, `제품 및 기술 설명`, `회사 및 기관 소개`, `기사 요약`으로 고정한다.
- 기사 원문, 공식자료, 제품 페이지, 논문, 규제·인허가 자료, Codex 심층 리서치에서 확인된 사실만 본문에 쓴다.
- 확인되지 않은 항목은 슬라이드 문안에 넣지 않는다.
- 내부 점수, 후보 순위, 스코어링 기준, rubric은 슬라이드에 넣지 않는다.
- PPTX는 만들지 않는다. 최종 산출물은 PDF다.

## Pencil MCP 작업 순서

1. `pencil_slide_spec.json`을 읽고 `slides[].blocks`, `template.export_frame_names`, `template.content_frame_names`, `canvas` 값을 확인한다.
2. `scripts/prepare_pencil_template.py`로 기준 `.pen` 템플릿을 주차별 작업 파일로 복사한다.
3. Pencil MCP `open_document(path=<weekly_pen_file>)` 또는 현재 active editor로 주차별 작업 파일을 연다.
4. Pencil MCP `get_editor_state(include_schema=true)`로 현재 문서와 schema를 확인한다.
5. `batch_get`으로 `type=frame`, `name=^content\\.slide`에 해당하는 content frame을 찾는다.
6. 각 content frame 안에 기존 임시 child가 있으면 삭제한다.
7. `slides[].blocks`를 보고 text, card, flow, callout 요소를 content frame 안에 생성한다.
8. `export_nodes(format="pdf", nodeIds=[slide frame ids], outputDir=<run_dir>)`로 slide frame 4개를 하나의 PDF로 export한다.
9. export된 PDF 경로를 `scripts/finalize_pencil_slide_pdf.py`에 넘겨 `news_slide_26년_5월_1주차.pdf`로 정규화하고 작업용 `_work` 디렉터리를 삭제한다.

## 디자인 기준

- 캔버스: 16:9, 1280x720
- 배경: `#FFFFFF`
- 본문 텍스트: `#1F2933`
- 보조 텍스트: `#56616F`
- 주 강조색: `#155EEF`
- 보조 강조색: `#0E9384`
- 구분선: `#D9E2EC`
- 폰트: Inter 또는 문서에서 사용 가능한 산세리프
- content frame은 `x=60`, `y=150`, `width=1160`, `height=510`을 기준으로 사용한다.
- 장식보다 관계도, 흐름도, 소개 블록처럼 기사 이해를 직접 돕는 구조를 우선한다.

## 4장 구성

### 1. 이번 주 대표 기사

- 대표 기사 제목, 매체, 날짜, 관련기관을 분명히 보여준다.
- 왜 이 기사를 대표 기사로 봤는지 공개 가능한 문장으로 정리한다.
- 발표·도입·제휴·연구 등 이번 기사에서 확인된 내용을 요약한다.

### 2. 제품 및 기술 설명

- 기사에서 다룬 제품, 기술, 모델, 기능의 이름과 역할을 설명한다.
- 해결하려는 의료 문제, 입력 데이터, 처리 방식, 출력 결과, 현장 workflow 연결을 분리한다.
- 필요하면 `입력 데이터 -> 처리 방식 -> 현장 사용` 흐름을 넣는다.

### 3. 회사 및 기관 소개

- 관련 회사나 기관의 역할, 기존 제품·역량, 파트너십·도입 여부, 이번 기사와 연결되는 사업 맥락을 정리한다.
- 도입·검증·인허가·논문 상태는 확인된 범위에서만 제시한다.

### 4. 기사 요약

- 기사 배경과 주요 내용을 짧게 정리한다.
- 의료기관, 응급실, 중환자실 workflow에 줄 수 있는 의미를 자연스럽게 설명한다.
- 마지막은 한줄 정리로 닫는다.
