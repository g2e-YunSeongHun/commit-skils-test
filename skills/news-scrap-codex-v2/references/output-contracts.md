# Output Contracts

## Final Artifacts

`news-scrap-codex-v2`의 최종 산출물은 `<run_dir>`에 아래 두 파일만 남긴다.

```text
<run_dir>/news_26년_5월_1주차.html
<run_dir>/news_slide_26년_5월_1주차.pdf
```

- HTML 파일명은 `news_<week_id>.html` 형식이다.
- PDF 파일명은 `news_slide_<week_id>.pdf` 형식이다.
- `<run_dir>` 또는 임시 파일명에 `_codex` 같은 실행 구분 suffix가 있어도 최종 파일명에는 포함하지 않는다.
- PPTX는 생성하지 않는다.
- 내부 점수, 후보 순위, 스코어링 기준, rubric은 최종 HTML/PDF에 포함하지 않는다.

## Work Directory

작업용 파일은 `<work_dir> = <run_dir>/_work` 아래에서만 사용한다. 성공 후 `finalize_pencil_slide_pdf.py --work-dir <work_dir>`가 `_work`를 삭제하므로 최종 산출물로 남기지 않는다.

대표적인 작업 파일은 아래와 같다.

```text
<work_dir>/search_queries.json
<work_dir>/candidates_raw.json
<work_dir>/news_briefing.md
<work_dir>/pencil_slide_spec.json
<work_dir>/news_slide_26년_5월_1주차.pen
```

`news_briefing.md`가 v2의 단일 작업 원본이다. 검색·검증·요약·대표 기사 선정·심층 리서치·슬라이드 문안은 모두 이 파일에 반영한다.

디버깅이 필요하면 `finalize_pencil_slide_pdf.py`에 `--keep-work-dir`를 사용해 `_work`를 보존한다. 기본 운영에서는 보존하지 않는다.

## Briefing Markdown

`news_briefing.md`는 [briefing-md-contract.md](briefing-md-contract.md)의 구조를 따른다. 최소 섹션은 아래와 같다.

```markdown
# 의료 AI 주간 브리핑

## 기간

## 국내 기사

## 해외 기사

## 대표 기사

## 슬라이드 1. 이번 주 핵심 팩트

## 슬라이드 2. AI 기술 설명

## 슬라이드 3. 회사·기관 팩트시트

## 슬라이드 4. 이번 주 인사이트
```

HTML 대시보드의 기사 요약은 `요약` 필드를 사용한다. 해외 기사도 `요약`은 한국어여야 하며, 영어 요약이 그대로 들어가면 렌더링 검증 실패로 처리한다.

## Pencil Spec

`pencil_slide_spec.json`은 내부 작업 파일이다. Pencil MCP가 템플릿의 named text slot을 채울 때만 사용하고 최종 산출물로 남기지 않는다.

```json
{
  "week_id": "26년_5월_1주차",
  "output": {
    "pdf_filename": "news_slide_26년_5월_1주차.pdf"
  },
  "template": {
    "mode": "replace_named_text_slots",
    "slot_name_pattern": "^slot\\.",
    "export_frame_names": [
      "template.slide1.core_facts",
      "template.slide2.ai_technology",
      "template.slide3.company_fact_sheet",
      "template.slide4.weekly_insight"
    ]
  },
  "template_slots": {
    "slot.article.title": "대표 기사 제목",
    "slot.slide1.title": "대표 기사 제목",
    "slot.slide1.bullet1": "확인된 핵심 팩트"
  }
}
```

`template_slots`의 key는 Pencil text node의 `name`과 매칭하며 `content`만 업데이트한다.
