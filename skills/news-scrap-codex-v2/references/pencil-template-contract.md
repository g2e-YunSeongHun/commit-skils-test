# Pencil Template Contract

`news-scrap-codex-v2`의 Pencil 출력은 scaffold 템플릿 기반으로 운영한다. 템플릿은 디자인, 컬럼, 카드, 제목, 여백을 유지하고, 실행마다 바뀌는 값은 `bind.*` 이름이 붙은 text node의 `content`만 교체한다.

## 템플릿 전제

- 템플릿은 `templates/news_slide_template.pen`이다.
- 슬라이드는 정확히 4개 top-level frame이다.
- 각 slide frame은 1280x720, 16:9 비율이다.

| Slide | Frame name | Content frame |
|---|---|---|
| 1 | `template.slide1` | `content.slide1` |
| 2 | `template.slide2` | `content.slide2` |
| 3 | `template.slide3` | `content.slide3` |
| 4 | `template.slide4` | `content.slide4` |

## Runtime Contract

1. `scripts/build_pencil_slide_spec_from_md.py`로 `news_briefing.md`에서 `pencil_slide_spec.json`을 만든다.
2. `pencil_slide_spec.json.template.mode`는 `update_named_bindings`여야 한다.
3. `scripts/prepare_pencil_template.py`로 기준 템플릿을 주차별 `.pen` 파일로 복사한다.
4. `scripts/apply_pencil_bindings.py <weekly_pen_file> <pencil_slide_spec.json> --strict`로 `template_bindings`의 key와 같은 `name`을 가진 text node의 `content`를 교체한다.
5. `content.slideN` 내부 scaffold child는 삭제하지 않는다.
6. binding 값이 비어 있으면 해당 text node를 빈 문자열로 두고, 가능한 반복 카드 frame은 `enabled:false`로 숨긴다.
7. 반복 binding은 템플릿의 최대 수용 개수일 뿐이다. 예를 들어 `point1~point3`, `capability1~capability4`, `offering1~offering3`은 확인된 항목 수만큼만 표시한다.
8. 갱신된 `.pen` 파일을 Pencil에서 열고 `snapshot_layout(problemsOnly=true)`로 clipping을 확인한다.
9. slide frame 4개를 `export_nodes(format="pdf")`로 export한다.
10. `scripts/finalize_pencil_slide_pdf.py`로 최종 PDF 이름을 정규화한다.

## Binding Groups

### Slide 1

- `bind.s1.category`
- `bind.s1.headline`
- `bind.s1.dek`
- `bind.s1.body`
- `bind.s1.point1`
- `bind.s1.point2`
- `bind.s1.point3`
- `bind.s1.visual_note`

### Slide 2

- `bind.s2.product_name`
- `bind.s2.one_liner`
- `bind.s2.description`
- `bind.s2.step1`
- `bind.s2.step2`
- `bind.s2.step3`
- `bind.s2.capability1.title`
- `bind.s2.capability1.detail`
- `bind.s2.capability2.title`
- `bind.s2.capability2.detail`
- `bind.s2.capability3.title`
- `bind.s2.capability3.detail`
- `bind.s2.capability4.title`
- `bind.s2.capability4.detail`

### Slide 3

- `bind.s3.logo_label`
- `bind.s3.category`
- `bind.s3.domain`
- `bind.s3.name`
- `bind.s3.tagline`
- `bind.s3.description`
- `bind.s3.founded`
- `bind.s3.headquarters`
- `bind.s3.scale`
- `bind.s3.focus`
- `bind.s3.offering1.title`
- `bind.s3.offering1.detail`
- `bind.s3.offering2.title`
- `bind.s3.offering2.detail`
- `bind.s3.offering3.title`
- `bind.s3.offering3.detail`

### Slide 4

- `bind.s4.takeaway`
- `bind.s4.dek`
- `bind.s4.what.title`
- `bind.s4.what.detail`
- `bind.s4.why.title`
- `bind.s4.why.detail`
- `bind.s4.how.title`
- `bind.s4.how.detail`
- `bind.s4.fact1.label`
- `bind.s4.fact1.value`
- `bind.s4.fact1.detail`
- `bind.s4.fact2.label`
- `bind.s4.fact2.value`
- `bind.s4.fact2.detail`
- `bind.s4.fact3.label`
- `bind.s4.fact3.value`
- `bind.s4.fact3.detail`
- `bind.s4.meaning1`
- `bind.s4.meaning2`
- `bind.s4.meaning3`
- `bind.s4.source`

## Why This Shape

- 디자인과 레이아웃은 안정적으로 유지된다.
- 리서치 단계에서 필요한 데이터가 명확해져 슬라이드가 빈약해지는 문제를 줄인다.
- 매번 새 block을 그리지 않으므로 카드 크기, 헤더, 여백이 흔들리지 않는다.
- 내부 점수나 후보 정보는 템플릿 binding에 포함하지 않는다.
- 반복 항목은 확인된 만큼만 노출하므로 템플릿 때문에 사실이 늘어나지 않는다.
