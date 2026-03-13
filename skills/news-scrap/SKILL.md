---
name: news-scrap
description: '응급의료 AI 관련 주간 뉴스 스크랩. 매주 일주일간(월~일) 기간의 기사/논문을 수집·분석·정리. Keywords: 뉴스, news, 스크랩, scrap, 응급, emergency, AI 뉴스'
---

# 응급의료 AI 주간 뉴스 스크랩

## Purpose

매주 금요일 실행하여, 해당 주에 발행된 응급실/응급의학과 AI 관련 뉴스 기사 및 학술 논문을 자동 수집·분석·정리하고 대시보드 스타일 HTML 파일로 저장한다.

**IMPORTANT: 모든 출력은 한국어로 작성한다.**

## Trigger Conditions

### When to activate:

- /news-scrap, 뉴스 스크랩, 뉴스 수집, 주간 뉴스
- "이번 주 응급의료 뉴스 정리해줘"
- "뉴스 스크랩 돌려줘"

### When NOT to activate:

- 단순 뉴스 검색 질문 (e.g., "최근 AI 뉴스 뭐 있어?")
- 응급의료와 무관한 뉴스 요청

---

## Workflow

### Step 1: 날짜 범위 계산

1. 오늘 날짜를 기준으로 **이번 주 월~일요일** 범위를 계산한다. 만약, 월요일날 해당 스킬이 실행되면 지난 주 **월~일요일**범위로 계산한다.
   - 시작일: 이번주 월요일
   - 종료일: 이번주 일요일
2. 날짜 형식: `YYYY년 MM월 DD일` (한국어), `YYYY-MM-DD` (파일명용)
3. 사용자에게 수집 기간을 안내한다:
   ```
   수집 기간: 2026년 3월 9일(월) ~ 2026년 3월 15일(일) - 3월 2주차
   ```

---

### Step 2: 병렬 에이전트 수집

**Agent 도구를 사용하여 3개 전문 에이전트를 동시에 실행한다.** 각 에이전트는 자기 담당 도메인의 검색 → 발행일 확인 → 필터링 → 정리를 독립 수행하고, JSON 배열로 결과를 반환한다.

> **IMPORTANT:** 반드시 3개 Agent 도구 호출을 **하나의 메시지에서 동시에** 실행하여 병렬 처리한다.

#### 에이전트 1: 국내 기사 스크랩 전문가

**검색 키워드 (한국어):**

1. `응급실 AI 인공지능 {시작일}~{종료일}`
2. `응급의학 인공지능 병원 도입 {시작일}~{종료일}`
3. `응급환자 AI 트리아지 분류 {시작일}~{종료일}`
4. `응급의료 AI 정책 정부 {시작일}~{종료일}`
5. `응급실 뺑뺑이 AI 병상 배정 {시작일}~{종료일}`
6. `응급 환자 이송 자원 배분 AI {시작일}~{종료일}`

**우선 도메인:** `medigatenews.com`, `dailymedi.com`, `mdtoday.co.kr`, `amedinews.com`, `pharm.edaily.co.kr`, `mohw.go.kr`, `yna.co.kr`, `medicaltimes.com`

#### 에이전트 2: 해외 기사 스크랩 전문가

**검색 키워드 (영어):**

1. `emergency department AI triage {시작일}~{종료일}`
2. `emergency medicine artificial intelligence {시작일}~{종료일}`
3. `emergency room AI clinical decision support {시작일}~{종료일}`
4. `emergency department overcrowding AI bed management {시작일}~{종료일}`
5. `ambulance dispatch AI patient transfer optimization {시작일}~{종료일}`

**우선 도메인:** `healthcareitnews.com`, `beckershospitalreview.com`, `medpagetoday.com`, `statnews.com`, `fiercehealthcare.com`, `mobihealthnews.com`

#### 에이전트 3: 학술 논문 스크랩 전문가

**검색 키워드 (영어):**

1. `emergency triage AI machine learning site:pubmed.ncbi.nlm.nih.gov {시작일}~{종료일}`
2. `emergency medicine artificial intelligence peer-reviewed {시작일}~{종료일}`
3. `emergency department AI clinical trial {시작일}~{종료일}`
4. `emergency department crowding AI resource allocation {시작일}~{종료일}`
5. `prehospital AI ambulance dispatch machine learning {시작일}~{종료일}`

**우선 도메인:** `pubmed.ncbi.nlm.nih.gov`, `pmc.ncbi.nlm.nih.gov`, `medinform.jmir.org`, `jmir.org`, `annemergmed.com`, `emj.bmj.com`, `ai.nejm.org`, `nature.com`, `frontiersin.org`, `mdpi.com`, `sciencedirect.com`

#### 각 에이전트 공통 지침

각 에이전트 프롬프트에 아래 내용을 포함한다:

1. **blocked_domains:** `["youtube.com", "blog.naver.com", "tistory.com", "brunch.co.kr", "medium.com", "velog.io", "reddit.com"]`
2. **발행일 확인 순서 (필수):**
   - WebFetch로 기사 URL 접근 → prompt: `"이 기사/논문의 정확한 발행일(published date)을 YYYY-MM-DD 형식으로만 답해줘. 찾을 수 없으면 NOT_FOUND라고만 답해줘."`
   - WebFetch 실패 시(403/에러) → Playwright MCP (`playwright_navigate` → `playwright_get_visible_text`) 로 발행일 확인
   - Playwright도 실패 시 → URL 경로에서 날짜 패턴 추출 (`/2026/03/`, `2026-03-12` 등)
   - URL에도 없으면 → WebSearch 스니펫에서 날짜 추출
   - 위 모든 방법 실패 → 해당 기사 **제외**
3. **날짜 필터링:** 발행일이 해당 주차 범위({시작일}~{종료일}) 내인 기사만 포함. "추정" 날짜 금지.
4. **중복 제거**, **모든 출력은 한국어**
5. **반환 형식:** 아래 필드를 포함하는 JSON 배열로 최종 결과만 반환:
   ```json
   [
     {
       "기관매체": "출처 매체명",
       "관련기관": "기사에 등장하는 병원/기업/기관",
       "활용분야": "트리아지, 영상판독 등",
       "구분": "연구|도입|정책|트렌드",
       "제목": "기사 제목",
       "핵심내용": "3~5문장 상세 요약 (아래 가이드라인 참조)",
       "날짜": "YYYY-MM-DD",
       "링크": "원문 URL"
     }
   ]
   ```
6. **요약 작성 가이드라인 (핵심내용 필드):**
   - 기업/기관 첫 등장 시 **간략 소개** 포함 (예: "의료 AI 전문기업 뷰노(VUNO, 코스닥 상장)의...", "600만 사용자 기반 의료 AI 기업 August AI가...")
   - 기술/제품명 첫 등장 시 **어떤 기술인지 설명** 포함 (예: "AI 기반 신속대응시스템 딥카스(DeepCARS, 환자의 활력징후를 실시간 분석하여 24시간 내 심정지 위험을 예측하는 AI 의료기기)")
   - **수치/성과**가 있으면 반드시 포함 (정확도, 도입률, 비용 절감, AUC 등)
   - 연구/논문인 경우 **연구 방법과 주요 결과** 포함 (예: "N명 대상 후향적 코호트 연구에서 AUC 0.92 달성")
   - 단순 사실 나열이 아닌, 해당 기사가 **왜 중요한지** 맥락을 제공

---

### Step 3: 결과 통합 및 중복 제거

3개 에이전트의 결과 JSON 배열을 합친 후 아래 처리를 수행한다:

1. **URL 기준 중복 제거** — 같은 URL이 여러 에이전트에서 수집된 경우 1건만 남긴다
2. **같은 내용의 다른 매체 보도** — 대표 1건만 남긴다
3. **섹션 분류:**
   - 에이전트 1(국내) 결과 → **국내 기사** 섹션
   - 에이전트 2(해외 기사) + 에이전트 3(학술 논문) 결과 → **해외 기사 / 학술 논문** 섹션
4. **응급의료와 직접 관련 없는 일반 AI/헬스케어 기사는 제외**한다

---

### Step 4: 분석 및 정리

수집·필터링된 기사를 아래 기준으로 분석하고 아코디언 리스트 형태로 정리한다.

**분석 항목:**
| 필드 | 설명 |
|---|---|
| 기관/매체 | 기사 출처 언론사 또는 저널명 |
| 관련 기관 | 기사에 등장하는 병원, 기업, 정부기관 |
| 활용분야 | 트리아지, 영상판독, 패혈증 예측, 심정지 예측, 워크플로 최적화 등 |
| 구분 | 연구 / 도입 / 정책 / 트렌드 중 택 1 |
| 제목 | 기사 제목 |
| 핵심 내용 | 3~5문장 상세 요약 (Step 2 요약 작성 가이드라인 참조) |
| 기사 날짜 | WebFetch로 확인된 정확한 발행일 (YYYY-MM-DD) |
| 링크 | 원문 URL |

**국내 기사와 해외 기사/논문을 별도 섹션으로 분리한다.**

---

### Step 5: 주간 요약 작성

표 정리 후 아래 항목으로 주간 요약을 작성한다:

1. **이번 주 핵심 동향** (3~5개 bullet point)
2. **주목할 기관/기업** (어떤 곳이 어떤 활동을 했는지)
3. **시사점** (응급의료 AI 분야에서 어떤 흐름이 보이는지 2~3문장)

---

### Step 6: HTML 대시보드 파일 저장

1. 저장 경로: `news_output/` 폴더 (프로젝트 루트 기준)
   - 폴더가 없으면 생성한다
2. 파일명: `news_{해당년도월주차}.html` (예: `news_26년 3월 2주차.html`)
   - **같은 파일명이 이미 존재하면 삭제 후 새로 작성한다** (항상 최신 결과로 덮어쓰기)
3. 템플릿 파일 `templates/dashboard.html`을 읽어서 플레이스홀더를 실제 데이터로 채워 HTML을 생성한다.
   - 템플릿 경로: 이 스킬의 `templates/dashboard.html` 파일

**플레이스홀더 치환 규칙:**

- `{시작일}`, `{종료일}`, `{오늘 날짜}`: 날짜 문자열
- `{총건수}`, `{국내건수}`, `{해외건수}`: 실제 수집 건수
- `<!--ARTICLE_TEMPLATE: ... -->` 주석 내의 아코디언 구조를 참고하여, 수집된 기사마다 `<details class="article">` 를 반복 생성한다
- `<summary>` 안에 제목 + 태그 + 날짜 배치 (접힌 상태에서 보이는 정보)
- `<div class="article-body">` 안에 출처, 상세 요약(3~5문장), 원문 링크 배치 (펼친 상태에서 보이는 정보)
- `구분` 값(연구/도입/정책/트렌드)에 따라 태그 색상 클래스 적용: `tag-연구`, `tag-도입`, `tag-정책`, `tag-트렌드`
- `활용분야`는 `tag-field` 클래스로 별도 태그 생성
- `관련 기관`은 `.source`에 `{기관/매체} · {관련 기관}` 형태로 병기
- 링크는 `target="_blank"`로 새 탭에서 열리도록
- 주간 요약 섹션의 `<li>`, `<p>` 내용도 실제 분석 결과로 채운다

4. 저장 완료 후 사용자에게 파일 경로와 수집 건수를 안내한다:
   ```
   저장 완료: news_output/news_26년 3월 2주차.html (국내 X건, 해외 Y건)
   ```

---

## Error Handling

- WebSearch 결과가 0건인 키워드는 건너뛴다
- 해당 주 기사가 전혀 없는 경우: "이번 주 수집된 기사가 없습니다"로 안내
- 발행일을 확인할 수 없는 기사는 제외한다 (포함하지 않음)

## Notes

- 이 스킬은 외부 API 없이 Claude Code의 WebSearch와 분석 능력만으로 동작한다
- 결과물의 품질은 검색 시점의 웹 인덱싱 상태에 따라 달라질 수 있다
- 중복 기사는 제거하고, 같은 내용의 다른 매체 보도는 대표 1건만 남긴다

---

## Reference Sites

수집 시 참고할 사이트 목록. 수집 우선순위 순서로 정리. 각 섹션은 담당 에이전트에 매핑된다.

### 국내 뉴스 매체 → 에이전트 1 (국내 기사 전문가)

| 매체           | URL                | 주요 특성                                |
| -------------- | ------------------ | ---------------------------------------- |
| 메디게이트뉴스 | medigatenews.com   | 의료 AI·헬스케어 전문, 응급 AI 사례 다수 |
| 데일리메디     | dailymedi.com      | 병원/의료IT, AI 도입 사례                |
| 의학신문       | mdtoday.co.kr      | 의료 체계/AI 연구 소식                   |
| 의협신문       | amedinews.com      | 대한의사협회 공식, 의료정책/전문가 의견  |
| 팜이데일리     | pharm.edaily.co.kr | AI 의료기기/정책, 산업 트렌드            |
| 메디칼타임즈   | medicaltimes.com   | 의료 전문 인터넷신문                     |
| 보건복지부     | mohw.go.kr         | 정부 정책·보도자료                       |
| 연합뉴스       | yna.co.kr          | 주요 응급의료/AI 보도                    |

### 해외 뉴스 매체 → 에이전트 2 (해외 기사 전문가)

| 매체                     | URL                       | 주요 특성                         |
| ------------------------ | ------------------------- | --------------------------------- |
| Healthcare IT News       | healthcareitnews.com      | 헬스케어 IT + 응급실 AI 도입 사례 |
| Becker's Hospital Review | beckershospitalreview.com | 병원 운영 + AI 활용 사례          |
| MedPage Today            | medpagetoday.com          | 임상/응급의학 뉴스                |
| STAT News                | statnews.com              | 의료 AI 정책/윤리 심층분석        |
| Fierce Healthcare        | fiercehealthcare.com      | AI 도입 전략/파일럿               |
| MobiHealthNews           | mobihealthnews.com        | 디지털 헬스/AI 기술               |

### 학술 저널 / 논문 DB → 에이전트 3 (학술 논문 전문가)

| 저널/DB                      | URL                     | 주요 특성                                  |
| ---------------------------- | ----------------------- | ------------------------------------------ |
| PubMed / PMC                 | pubmed.ncbi.nlm.nih.gov | 의학 논문 인덱스 + 오픈 액세스             |
| JMIR Medical Informatics     | medinform.jmir.org      | AI·응급 트리아지/헬스케어 AI (peer-review) |
| Annals of Emergency Medicine | annemergmed.com         | 응급의학 국제 표준 저널                    |
| Emergency Medicine Journal   | emj.bmj.com             | BMJ 계열 응급의학 연구                     |
| NEJM AI                      | ai.nejm.org             | 고품질 임상 AI 연구                        |
| Nature                       | nature.com              | 응급/중환자 AI 논문 컬렉션                 |
| Frontiers in Digital Health  | frontiersin.org         | 디지털 헬스 오픈 액세스                    |
| MDPI                         | mdpi.com                | 오픈 액세스 종합                           |
| ScienceDirect                | sciencedirect.com       | Elsevier 논문 DB                           |
