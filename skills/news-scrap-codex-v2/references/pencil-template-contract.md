# Pencil Template Contract

`news-scrap-codex-v2`의 Pencil 출력은 템플릿 기반으로 운영한다. 매 실행마다 디자인을 새로 만들지 않고, 고정된 `.pen` 템플릿을 복사한 뒤 named text slot의 `content`만 바꾼다.

## 템플릿 전제

- 템플릿은 `templates/news_slide_template.pen`에 둔다.
- 슬라이드는 정확히 4개 top-level frame이다.
- 각 slide frame은 1280x720, 16:9 비율을 유지한다.
- slide frame 이름은 아래 값을 사용한다.

| Slide | Frame name |
|---|---|
| 1 | `template.slide1.core_facts` |
| 2 | `template.slide2.ai_technology` |
| 3 | `template.slide3.company_fact_sheet` |
| 4 | `template.slide4.weekly_insight` |

## Slot Naming

내용이 바뀌는 text node는 `name`을 `slot.`으로 시작하게 만든다. Pencil MCP는 `batch_get`으로 `name`이 `^slot\\.`에 맞는 text node를 찾고, `pencil_slide_spec.json`의 `template_slots` 값으로 `content`만 업데이트한다.

공통 slot:

- `slot.deck.week_id`
- `slot.deck.period`
- `slot.deck.generated_date`
- `slot.article.title`
- `slot.article.media`
- `slot.article.date`
- `slot.article.org`
- `slot.article.domain`
- `slot.article.category`
- `slot.article.link`
- `slot.article.selection_reason`

슬라이드별 slot:

- `slot.slide1.section`
- `slot.slide1.title`
- `slot.slide1.visual`
- `slot.slide1.bullet1` ... `slot.slide1.bullet6`
- `slot.slide1.source1` ... `slot.slide1.source3`
- `slot.slide2.section`
- `slot.slide2.title`
- `slot.slide2.visual`
- `slot.slide2.bullet1` ... `slot.slide2.bullet6`
- `slot.slide2.source1` ... `slot.slide2.source3`
- `slot.slide3.section`
- `slot.slide3.title`
- `slot.slide3.visual`
- `slot.slide3.bullet1` ... `slot.slide3.bullet6`
- `slot.slide3.source1` ... `slot.slide3.source3`
- `slot.slide4.section`
- `slot.slide4.title`
- `slot.slide4.visual`
- `slot.slide4.bullet1` ... `slot.slide4.bullet6`
- `slot.slide4.source1` ... `slot.slide4.source3`

필요하면 `slot.slideN.body`를 긴 원문 재료를 담는 작업용 text나 note로 둘 수 있다. 최종 PDF에는 보이지 않게 처리한다.

## Runtime Workflow

1. `scripts/build_pencil_slide_spec_from_md.py`로 `news_briefing.md`에서 `pencil_slide_spec.json`을 만든다.
2. `scripts/prepare_pencil_template.py`로 기준 Pencil 템플릿 `.pen` 파일을 주차별 작업 파일로 복사한다.
3. Pencil에서 주차별 작업 `.pen` 파일을 열거나 Pencil MCP `open_document(path=...)`로 active editor로 둔다.
4. Pencil MCP `batch_get`으로 text node 중 `name`이 `^slot\\.`인 node를 읽는다.
5. `pencil_slide_spec.json.template_slots`의 key와 text node `name`을 매칭한다.
6. Pencil MCP `batch_design`에서 각 slot node의 `content`만 업데이트한다.
7. 템플릿 slide frame 4개를 `export_nodes(format="pdf")`로 export한다.
8. `scripts/finalize_pencil_slide_pdf.py`로 최종 PDF 이름을 정규화한다.

## Why This Shape

- 디자인은 템플릿에서 고정한다.
- 실행마다 바뀌는 것은 기사 내용과 날짜뿐이다.
- Pencil MCP가 빈 `.pen` 파일을 안정적으로 생성하지 못해도, 기존 템플릿 파일을 파일시스템에서 복사하고 열린 문서를 업데이트하는 방식은 일관적으로 운영할 수 있다.
- Node ID가 바뀌어도 `name` 기반 slot 검색으로 복구할 수 있다.
