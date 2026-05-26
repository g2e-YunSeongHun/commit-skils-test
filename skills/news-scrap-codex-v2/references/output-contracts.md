# Output Contracts

## Final Outputs

최종 산출물은 `<run_dir>`에 아래 두 개만 남긴다.

```text
news_<week_id>.html
news_slide_<week_id>.pdf
```

예:

```text
news_26년_5월_1주차.html
news_slide_26년_5월_1주차.pdf
```

`_work` 아래의 JSON, Markdown, `.pen` 파일은 작업용이다. 성공 후 삭제한다.

## HTML

- 입력: `<work_dir>/news_briefing.md`
- 출력: `<run_dir>/news_<week_id>.html`
- 해외 기사 제목은 번역 제목을 우선 사용한다.
- 해외 기사 요약은 한국어여야 한다.
- 내부 점수, 후보 순위, 스코어링 기준, rubric은 포함하지 않는다.

## Pencil Spec

`pencil_slide_spec.json`은 작업용 파일이며 최종 산출물로 남기지 않는다.

```json
{
  "schema_version": "1.1",
  "week_id": "26년_5월_1주차",
  "output": {
    "pdf_filename": "news_slide_26년_5월_1주차.pdf"
  },
  "template": {
    "mode": "update_named_bindings",
    "binding_name_pattern": "^bind\\.",
    "export_frame_names": [
      "template.slide1",
      "template.slide2",
      "template.slide3",
      "template.slide4"
    ],
    "empty_binding_policy": "empty_string_and_hide_parent_card_when_possible",
    "repeating_binding_policy": "use_only_verified_items_up_to_template_capacity"
  },
  "template_bindings": {
    "bind.s1.headline": "대표 기사 제목",
    "bind.s2.product_name": "제품·기술명",
    "bind.s3.name": "회사·기관명",
    "bind.s4.takeaway": "기사 한 줄 정리"
  }
}
```

## PDF

- 입력: 주차별 `.pen` 작업 파일
- 출력: `<run_dir>/news_slide_<week_id>.pdf`
- `.pen` 파일은 export 전에 `scripts/apply_pencil_bindings.py`로 갱신되어 있어야 한다.
- PDF는 4장이어야 한다.
- `bind.*` placeholder 텍스트가 그대로 남으면 실패로 본다.
- 빈 반복 항목이 카드 형태로 남아 있으면 실패로 본다. 조사된 항목만 표시해야 한다.
- layout clipping이 있으면 실패로 본다.
