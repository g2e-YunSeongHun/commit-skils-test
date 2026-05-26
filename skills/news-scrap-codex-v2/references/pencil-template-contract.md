# Pencil Template Contract

`news-scrap-codex-v2`의 Pencil 출력은 반고정 템플릿 기반으로 운영한다. 템플릿은 디자인 톤, 제목, 여백, slide frame만 고정하고, 본문은 매 실행마다 `content.slideN` frame 안에 새로 배치한다.

## 템플릿 전제

- 템플릿은 `templates/news_slide_template.pen`에 둔다.
- 슬라이드는 정확히 4개 top-level frame이다.
- 각 slide frame은 1280x720, 16:9 비율을 유지한다.
- slide frame 이름은 아래 값을 사용한다.

| Slide | Frame name | Content frame |
|---|---|---|
| 1 | `template.slide1` | `content.slide1` |
| 2 | `template.slide2` | `content.slide2` |
| 3 | `template.slide3` | `content.slide3` |
| 4 | `template.slide4` | `content.slide4` |

## Fixed vs Generated

고정 영역:

- 왼쪽 accent bar
- slide number
- slide title
- deck label
- header rule
- footer note

생성 영역:

- `content.slide1`
- `content.slide2`
- `content.slide3`
- `content.slide4`

본문 text node slot은 사용하지 않는다. Pencil MCP는 `pencil_slide_spec.json.slides[].blocks`를 읽고 해당 `content_frame_name` 안에 text, card, flow, callout 같은 요소를 새로 만든다.

## Runtime Workflow

1. `scripts/build_pencil_slide_spec_from_md.py`로 `news_briefing.md`에서 `pencil_slide_spec.json`을 만든다.
2. `scripts/prepare_pencil_template.py`로 기준 Pencil 템플릿 `.pen` 파일을 주차별 작업 파일로 복사한다.
3. Pencil에서 주차별 작업 `.pen` 파일을 열거나 Pencil MCP `open_document(path=...)`로 active editor로 둔다.
4. Pencil MCP `batch_get`으로 frame node 중 `name`이 `content.slide1`~`content.slide4`인 node를 읽는다.
5. 각 content frame에 기존 임시 child가 있으면 삭제한다.
6. `pencil_slide_spec.json.slides[]`의 `blocks`를 해당 `content_frame_name` 안에 생성한다.
7. 템플릿 slide frame 4개를 `export_nodes(format="pdf")`로 export한다.
8. `scripts/finalize_pencil_slide_pdf.py`로 최종 PDF 이름을 정규화한다.

## Block Types

Pencil MCP는 아래 block type을 지원하는 최소 렌더링 규칙을 사용한다.

- `headline`: 큰 제목 또는 주요 문장
- `meta`: 매체, 날짜, 기관, 분야 같은 짧은 메타 정보
- `callout`: 대표 기사 선정 이유처럼 강조해야 하는 문장
- `cards`: 2~6개의 짧은 정보 카드
- `summary`: label + text 형태의 설명 블록
- `flow`: 입력, 처리, 결과, 현장 사용 흐름
- `bullets`: 짧은 bullet 목록
- `narrative`: 기사 요약용 label + 문장
- `takeaway`: 마지막 한줄 정리

## Why This Shape

- 디자인 톤과 4장 구성은 고정한다.
- 실행마다 바뀌는 본문은 기사 내용에 맞춰 새로 배치한다.
- `bullet1~bullet6` 같은 고정 slot에 억지로 끼워 넣지 않아 슬라이드가 더 자연스럽다.
- Node ID가 바뀌어도 `name` 기반 content frame 검색으로 복구할 수 있다.
