# Pencil Slide Guide

이 문서는 `news_briefing.md`에서 생성한 `pencil_slide_spec.json`을 바탕으로 Pencil MCP에서 4장짜리 PDF 슬라이드를 export하는 기준이다. 디자인은 고정 템플릿에 두고, 실행마다 `slot.` text node의 `content`만 바꾼다.

## 기본 원칙

- 슬라이드는 정확히 4장이다.
- 모든 문구는 한국어로 작성한다.
- 기사 원문, 공식자료, 제품 페이지, 논문, 규제·인허가 자료, Codex 심층 리서치에서 확인된 사실만 본문 팩트로 쓴다.
- 추론은 `시사점`, `불확실한 지점`, `추적할 신호`로 분리한다.
- 내부 점수, 후보 순위, 스코어링 기준, rubric은 슬라이드에 넣지 않는다.
- PPTX는 만들지 않는다. 최종 산출물은 PDF다.

## Pencil MCP 작업 순서

1. `pencil_slide_spec.json`을 읽고 `template_slots`, `template.export_frame_names`, `canvas` 값을 확인한다.
2. `scripts/prepare_pencil_template.py`로 기준 `.pen` 템플릿을 주차별 작업 파일로 복사한다.
3. Pencil MCP `open_document(path=<weekly_pen_file>)` 또는 현재 active editor로 주차별 작업 파일을 연다.
4. Pencil MCP `get_editor_state(include_schema=true)`로 현재 문서와 schema를 확인한다.
5. `batch_get`으로 `type=text`, `name=^slot\\.`에 해당하는 slot node를 찾는다.
6. `batch_design`으로 각 slot node의 `content`만 `template_slots` 값으로 업데이트한다.
7. `export_nodes(format="pdf", nodeIds=[slide frame ids], outputDir=<run_dir>)`로 slide frame 4개를 하나의 PDF로 export한다.
8. export된 PDF 경로를 `scripts/finalize_pencil_slide_pdf.py`에 넘겨 `news_slide_26년_5월_1주차.pdf`로 정규화하고 작업용 `_work` 디렉터리를 삭제한다.

## 디자인 기준

- 캔버스: 16:9, 1280x720
- 배경: `#FFFFFF`
- 본문 텍스트: `#1F2933`
- 보조 텍스트: `#56616F`
- 주 강조색: `#155EEF`
- 보조 강조색: `#0E9384`
- 구분선: `#D9E2EC`
- 폰트: Inter 또는 문서에서 사용 가능한 산세리프
- 제목은 52px 안팎, 섹션 라벨은 22px 안팎, 본문은 26~30px 범위를 사용한다.
- 장식보다 관계도, 흐름도, 팩트시트처럼 기사 이해를 직접 돕는 구조를 우선한다.
- 템플릿에는 충분한 수의 text box와 최대 6개 bullet slot을 미리 둔다. 실행 중에는 레이아웃을 바꾸지 않고 텍스트만 치환한다.

## 4장 구성

### 1. 이번 주 핵심 팩트

- 제목은 대표 기사 제목 중심으로 둔다.
- 누가, 언제, 무엇을 발표·도입·제휴했는지 확인된 사실만 정리한다.
- 핵심 팩트 3개와 발표·도입·제휴 관계를 보여주는 간단한 구조를 넣는다.

### 2. AI 기술 설명

- 기사에서 다룬 AI 또는 의료·응급·중환자의료 기술의 이름과 역할을 설명한다.
- 해결하려는 의료 문제, 입력 데이터, AI 처리, 출력 결과, 현장 workflow 연결을 분리한다.
- `입력 데이터 -> AI 처리 -> 현장 사용` 흐름을 넣는다.

### 3. 회사·기관 팩트시트

- 관련 회사나 기관의 역할, 기존 제품·역량, 파트너십·도입 여부, 이번 기사와 연결되는 사업 맥락을 정리한다.
- 도입·검증·인허가·논문 상태는 확인된 범위에서만 제시한다.
- 확인되지 않은 항목은 `확인 필요`로 표시한다.

### 4. 이번 주 인사이트

- 의료기관, 응급실, 중환자실 workflow에 줄 수 있는 영향과 위험을 분리한다.
- 현장 적용 시 주의점과 아직 불확실한 지점을 함께 제시한다.
- 다음에 추적할 신호 3개를 명시한다.
