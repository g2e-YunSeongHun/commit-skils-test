# Output Contracts

## verified_articles.json

```json
{
  "시작일": "2026-03-28",
  "종료일": "2026-04-03",
  "생성일": "2026-04-03",
  "국내기사": [
    {
      "기관/매체": "매체명",
      "관련기관": "기관명",
      "적용분야": "응급의료",
      "구분": "연구",
      "번역제목": "기사 제목 한글 번역",
      "원제목": "Original English Title",
      "제목": "기사 제목",
      "본문": "검증된 원문",
      "날짜": "2026-04-01",
      "링크": "https://example.com/article"
    }
  ],
  "해외기사": []
}
```

## candidates_raw.json

```json
{
  "period": {
    "start_date": "2026-04-04",
    "end_date": "2026-04-10"
  },
  "counts": {
    "domestic": 3,
    "overseas": 4,
    "papers": 2
  },
  "candidates": [
    {
      "url": "https://example.com/article",
      "domain": "medicaltimes.com",
      "title": "기사 제목",
      "snippet": "검색 결과 스니펫",
      "section_guess": "domestic",
      "score": 71,
      "matched_rules": ["emergency", "ai", "domestic_priority_domain"],
      "query": "응급실 AI 인공지능 2026-04-04..2026-04-10",
      "source": "search-engine",
      "published": "2026-04-09",
      "source_title": "MedicalTimes"
    }
  ]
}
```

## notebook_manifest.json

```json
{
  "week_id": "26년_4월_1주차",
  "notebook_title": "응급의료_AI_주간브리핑_26년_4월_1주차",
  "source_dir": "C:/.../sources",
  "sources": [
    {
      "title": "01_응급의료_AI_기사",
      "file_path": "C:/.../sources/01_응급의료_AI_기사.txt",
      "section": "국내기사",
      "article_title": "응급의료 AI 기사",
      "date": "2026-04-01",
      "link": "https://example.com/article"
    }
  ]
}
```

## notebooklm_outputs.json

```json
{
  "week_id": "26년_4월_1주차",
  "notebook": {
    "id": "uuid",
    "title": "응급의료_AI_주간브리핑_26년_4월_1주차"
  },
  "sources": [
    {
      "source_id": "uuid",
      "title": "01_응급의료_AI_기사",
      "file_path": "C:/.../sources/01_응급의료_AI_기사.txt",
      "section": "국내기사",
      "article_title": "응급의료 AI 기사",
      "date": "2026-04-01",
      "link": "https://example.com/article"
    }
  ],
  "questions": [
    {
      "id": "Q6",
      "note_title": "Q6_대표기사_26년_4월_1주차",
      "question": "질문 원문",
      "answer": "TITLE: 응급의료 AI 기사\nMEDIA: 매체명\nDATE: 2026-04-01\nREASON: ...",
      "references": []
    }
  ]
}
```

## featured_article.json

```json
{
  "title": "응급의료 AI 기사",
  "media": "매체명",
  "date": "2026-04-01",
  "section": "국내기사",
  "related_org": "기관명",
  "link": "https://example.com/article",
  "reason": "대표 기사 선정 이유",
  "source_id": "uuid"
}
```

## slide_deck_artifact.json

```json
{
  "notebook_id": "uuid",
  "artifact_id": "uuid",
  "featured_article": {
    "title": "응급의료 AI 기사"
  },
  "generation": {
    "status": "completed"
  },
  "revisions": [
    {
      "slide_index": 0,
      "status": "completed"
    }
  ],
  "downloads": {
    "pdf": "C:/.../news_slide_26년_4월_1주차.pdf",
    "pptx": "C:/.../news_slide_26년_4월_1주차.pptx"
  }
}
```

## notebooklm_failure.json

```json
{
  "step": "slide_generate",
  "detail": "NotebookLM slide-deck generation failed",
  "notebook_id": "uuid",
  "command": ["notebooklm", "generate", "slide-deck", "..."]
}
```
