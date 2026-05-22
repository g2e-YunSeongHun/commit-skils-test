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
      "적용분야": "의료 AI",
      "구분": "도입/제휴",
      "번역제목": "기사 제목 한글 번역",
      "원제목": "Original English Title",
      "제목": "기사 제목",
      "요약": "HTML 대시보드에 노출할 한국어 요약",
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
    "overseas": 4
  },
  "candidates": [
    {
      "url": "https://example.com/article",
      "domain": "medicaltimes.com",
      "title": "기사 제목",
      "snippet": "검색 결과 스니펫",
      "section_guess": "domestic",
      "score": 71,
      "matched_rules": ["medical_care", "ai", "domestic_priority_domain"],
      "query": "의료 AI 인공지능 2026-04-04..2026-04-10",
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
  "notebook_title": "의료_AI_대표기사_슬라이드_26년_4월_1주차",
  "source_dir": "C:/.../sources",
  "sources": [
    {
      "title": "featured_의료_AI_기사",
      "file_path": "C:/.../sources/featured_의료_AI_기사.txt",
      "section": "국내기사",
      "article_title": "의료 AI 기사",
      "date": "2026-04-01",
      "link": "https://example.com/article",
      "source_kind": "featured_deck_source"
    }
  ]
}
```

## article_summaries.json

```json
[
  {
    "title": "의료 AI 기사",
    "media": "매체명",
    "date": "2026-04-01",
    "section": "국내기사",
    "summary": "Codex가 원문에서 추출한 요약",
    "score": 84
  }
]
```

## selection_report.json

```json
{
  "period": {
    "start_date": "2026-03-28",
    "end_date": "2026-04-03",
    "generated_date": "2026-04-03"
  },
  "criteria": [
    {
      "id": "emergency_relevance",
      "label": "의료/응급/중환자의료 관련성",
      "max_score": 20
    }
  ],
  "featured_article": {
    "title": "의료 AI 기사",
    "score": 84
  },
  "candidates": [
    {
      "rank": 1,
      "title": "의료 AI 기사",
      "media": "매체명",
      "date": "2026-04-01",
      "section": "국내기사",
      "score": 84,
      "scores": {
        "emergency_relevance": 20,
        "ai_role": 18,
        "field_impact": 16,
        "source_completeness": 16,
        "briefing_fit": 14
      },
      "evidence": {
        "emergency_relevance": "확인 키워드: 의료 AI, 중환자실 AI"
      },
      "limitations": [],
      "summary": "기사 요약",
      "link": "https://example.com/article"
    }
  ]
}
```

## notebooklm_session.json

```json
{
  "week_id": "26년_4월_1주차",
  "notebook": {
    "id": "uuid",
    "title": "의료_AI_주간브리핑_26년_4월_1주차"
  },
  "sources": [
    {
      "source_id": "uuid",
      "title": "01_의료_AI_기사",
      "file_path": "C:/.../sources/01_의료_AI_기사.txt",
      "section": "국내기사",
      "article_title": "의료 AI 기사",
      "date": "2026-04-01",
      "link": "https://example.com/article"
    }
  ]
}
```

`notebooklm_session.json`은 `notebooklm_upload_sources.py`가 만든 세션 메타데이터이며 NotebookLM 분석 답변을 담지 않는다. 새 워크플로에서 NotebookLM은 슬라이드 생성만 담당한다.

`build_featured_deck_source.py`가 만드는 NotebookLM 슬라이드용 source에는 `featured_article.json`과 `selection_report.json`의 내부 점수, 기준별 점수표, 후보 순위 비교, rubric을 포함하지 않는다. 점수는 내부 선정·디버깅용 산출물에만 남긴다.

HTML 대시보드 요약은 `verified_articles.json`의 `요약`, `한국어요약`, `한글요약`, `번역요약`, `summary_ko`, `korean_summary`, `summary` 순서로 우선 사용한다. 해외 기사도 대시보드용 요약 필드는 한국어로 작성한다. 영어 요약을 만든 경우에는 HTML 렌더링 전에 한국어로 번역하고, 어색한 직역·과도한 영어 표현·원문 의미 누락이 없는지 검토한 결과만 `요약` 또는 `summary_ko`에 저장한다.

`render_dashboard.py`는 해외기사 요약이 한국어로 보이지 않으면 실패한다. 실패 시 해당 기사 요약을 다시 번역·검토한 뒤 렌더링을 재실행한다.

## featured_article.json

```json
{
  "title": "의료 AI 기사",
  "media": "매체명",
  "date": "2026-04-01",
  "section": "국내기사",
  "related_org": "기관명",
  "link": "https://example.com/article",
  "reason": "대표 기사 선정 이유",
  "score": 84,
  "score_breakdown": {
    "emergency_relevance": 20,
    "ai_role": 18,
    "field_impact": 16,
    "source_completeness": 16,
    "briefing_fit": 14
  },
  "selection_evidence": {
    "emergency_relevance": "확인 키워드: 의료 AI, 중환자실 AI"
  },
  "limitations": [],
  "source_id": "uuid"
}
```

## featured_research.md

```markdown
# 대표 기사 심층 리서치

## 확인한 사실

- 기관/기업/제품/연구에 대한 추가 확인 내용과 URL.

## 슬라이드 시사점

- 슬라이드에 반영할 수 있는 산업적, 임상적, 운영적 의미.

## 불확실한 지점

- 소스만으로 확인하지 못한 내용.
```

## slide_deck_artifact.json

```json
{
  "notebook_id": "uuid",
  "artifact_id": "uuid",
  "featured_article": {
    "title": "의료 AI 기사"
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
