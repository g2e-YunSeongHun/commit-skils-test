# Output Contracts

## verified_articles.json

```json
{
  "시작일": "2026년 3월 28일(토)",
  "종료일": "2026년 4월 3일(금)",
  "생성일": "2026년 4월 3일",
  "국내기사": [
    {
      "기관매체": "매체명",
      "관련기관": "기관명",
      "활용분야": "트리아지",
      "구분": "연구",
      "제목": "기사 제목",
      "원문": "본문",
      "날짜": "2026-04-01",
      "링크": "https://..."
    }
  ],
  "해외기사": []
}
```

## notebook_manifest.json

```json
{
  "week_id": "26년_4월_1주차",
  "notebook_title": "응급의료_AI_주간브리핑_2026_04_1주차",
  "source_dir": "C:/.../sources",
  "sources": [
    {
      "title": "01_일산병원_의료_AI_임상실증",
      "file_path": "C:/.../sources/01_일산병원_의료_AI_임상실증.txt",
      "section": "국내기사",
      "article_title": "일산병원 ...",
      "date": "2026-04-01",
      "link": "https://..."
    }
  ]
}
```

## notebooklm_outputs.json

```json
{
  "notebook": {
    "id": "uuid",
    "title": "응급의료_AI_주간브리핑_2026_04_1주차"
  },
  "sources": [
    {
      "source_id": "uuid",
      "title": "01_일산병원_의료_AI_임상실증",
      "file_path": "C:/.../01.txt"
    }
  ],
  "questions": [
    {
      "id": "Q0",
      "note_title": "Q0_기사별상세요약_26년_4월_1주차",
      "question": "질문 원문",
      "answer": "답변",
      "references": []
    }
  ]
}
```

## notebooklm_failure.json

```json
{
  "step": "ask",
  "detail": "Q2 failed",
  "notebook_id": "uuid",
  "command": ["notebooklm", "ask", "..."]
}
```
