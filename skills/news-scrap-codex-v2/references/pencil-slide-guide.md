# Pencil Slide Guide

이 문서는 `news_briefing.md`에서 생성한 `pencil_slide_spec.json`을 바탕으로 Pencil MCP에서 4장짜리 PDF 슬라이드를 export하는 기준이다. 디자인은 템플릿 scaffold에 두고, 실행마다 바뀌는 내용은 `bind.*` text node의 `content`만 교체한다.

## 기본 원칙

- 슬라이드는 정확히 4장이다.
- 모든 문구는 한국어로 작성한다.
- 슬라이드 제목은 `이번 주 대표 기사`, `제품 및 기술 설명`, `회사 및 기관 소개`, `기사 요약`으로 고정한다.
- 기사 원문, 공식자료, 제품 페이지, 논문, 규제·인허가 자료, Codex 심층 리서치에서 확인된 사실만 본문에 넣는다.
- 내부 점수, 후보 순위, 스코어링 기준, rubric은 슬라이드에 넣지 않는다.
- PPTX는 만들지 않는다. 최종 산출물은 PDF다.

## Pencil MCP 작업 순서

1. `pencil_slide_spec.json`을 읽고 `template.mode`, `template_bindings`, `template.export_frame_names`를 확인한다.
2. `scripts/prepare_pencil_template.py`로 기존 `.pen` 템플릿을 주차별 작업 파일로 복사한다.
3. `scripts/apply_pencil_bindings.py <weekly_pen_file> <pencil_slide_spec.json> --strict`로 `bind.*` text node를 갱신한다.
4. 값이 빈 binding은 빈 문자열로 두고, 해당되는 반복 카드 frame은 `enabled:false`로 숨긴다.
5. Pencil MCP `open_document(path=<weekly_pen_file>)` 또는 현재 active editor로 갱신된 작업 파일을 연다.
6. 반복 항목은 조사된 만큼만 표시한다. 빈 point, capability, offering, fact, meaning 카드는 억지로 채우지 않는다.
7. `snapshot_layout(problemsOnly=true)`로 clipped element가 없는지 확인한다.
8. 4개 slide frame을 `export_nodes(format="pdf", nodeIds=[...], outputDir=<run_dir>)`로 PDF export한다.
9. export된 PDF 경로를 `scripts/finalize_pencil_slide_pdf.py`에 넘겨 `news_slide_26년_5월_1주차.pdf`로 정규화하고 `_work`를 삭제한다.

## 디자인 기준

- 캔버스: 16:9, 1280x720
- 배경: `#FFFFFF`
- 제목: `#0B3145`
- 본문: `#1F2933`
- 보조 텍스트: `#56616F`
- 강조색: `#17617C`
- 구분선: `#D8DDE3`
- 폰트: Inter
- content frame 기준 위치: `x=60`, `y=118`, `width=1160`, `height=552`
- 카드는 둥글지만 과하지 않게 `cornerRadius` 6~8 수준을 유지한다.

## 슬라이드별 의도

### 1. 이번 주 대표 기사

좌측은 기사 제목과 설명, 우측은 확인된 핵심 포인트를 최대 3개까지 보여준다.

### 2. 제품 및 기술 설명

좌측은 제품·기술명, 설명, 확인된 작동 단계를 최대 3개까지 보여주고 우측은 주요 기능을 최대 4개까지 카드로 보여준다.

### 3. 회사 및 기관 소개

상단은 회사·기관 개요, 중단은 확인된 기본 정보, 하단은 확인된 주요 제품·서비스를 최대 3개까지 보여준다.

### 4. 기사 요약

상단은 한 줄 결론, 중단은 무엇·왜 중요·어떻게 요약 카드, 하단은 확인된 사실 기반 요약 항목과 의료 현장 의미를 최대 3개까지 보여준다.
