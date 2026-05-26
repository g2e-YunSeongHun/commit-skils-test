# Search Rules

`news-scrap-codex-v2`의 수집 목표는 많은 기사를 모으는 것이 아니라, 의료 AI·응급의료 AI·응급실 AI·중환자실 AI와 직접 관련된 주간 기사 묶음을 빠뜨리지 않고 검증하는 것이다.

## 기간

- 종료일은 해당 주 금요일이다.
- 시작일은 종료일 기준 6일 전 토요일이다.
- 예: `2026-05-16 ~ 2026-05-22`

## 건수

- 국내 기사: 최대 3건
- 해외 기사: 최대 3건
- 최종 HTML에는 총 4~6건을 권장한다.

## 포함 기준

아래 축 중 하나와 AI가 원문에서 직접 연결되어야 한다.

- 의료 AI
- 응급의료 AI
- 응급실 AI
- 중환자실 AI
- 의료기기 AI
- 의료영상 AI
- 병원 진료 workflow에 직접 들어가는 진단·문서화·의사결정 지원 AI

응급의료로만 좁히지 않는다. 의료기관 진료, 의료기기, 의료영상, 중환자실 맥락의 AI 기사도 포함할 수 있다.

## 제외 기준

아래 주제는 단독으로는 제외한다.

- 퇴원 후 관리
- 예후 예측
- 일반 환자 관리
- 재택의료
- 병상 배정, patient flow, hospital command center 같은 병원 운영 자동화
- 119·구급·응급의료 workflow가 확인되지 않는 일반 소방 AI, 로봇, 민원 자동화
- 의료 AI 직접성이 약한 보험, 마케팅, 행정 자동화

단, 위 제외 주제라도 원문에서 응급실, 응급의료, 중환자실, 급성 악화 조기 인지, 의료진 의사결정 지원과 직접 연결되면 포함 후보로 둘 수 있다.

## 국내 검색어

국내 검색은 넓은 의료 AI 축과 응급·중환자의료 축을 함께 수행한다.

- `의료 AI`
- `의료 인공지능`
- `의료기기 AI`
- `의료 영상 AI`
- `진단 AI`
- `응급의료 AI`
- `응급실 AI`
- `응급환자 AI`
- `중환자실 AI`
- `중환자의료 AI`
- `119 AI 응급`
- `구급 AI`

국내 기사가 0건처럼 보이면 아래 site-pass를 다시 수행한다.

- `site:dailymedi.com 의료 AI`
- `site:medicaltimes.com 의료 AI`
- `site:medigatenews.com 의료 AI`
- `site:rapportian.com 의료 AI`
- `site:docdocdoc.co.kr 의료 AI`
- `site:hitnews.co.kr 의료 AI`
- `site:mohw.go.kr 의료 AI`

## 해외 검색어

- `medical AI deployment healthcare news`
- `medical device AI healthcare`
- `medical imaging AI hospital`
- `emergency department AI`
- `emergency medicine AI`
- `EMS AI`
- `ICU AI`
- `critical care AI`
- `clinical deterioration AI ICU`

## 도메인 우선순위

### 국내

- `medicaltimes.com`
- `medigatenews.com`
- `dailymedi.com`
- `rapportian.com`
- `docdocdoc.co.kr`
- `mdtoday.co.kr`
- `hitnews.co.kr`
- `pharm.edaily.co.kr`
- `mohw.go.kr`
- `yna.co.kr`
- `newsis.com`

### 해외

- `healthcareitnews.com`
- `beckershospitalreview.com`
- `fiercehealthcare.com`
- `mobihealthnews.com`
- `healthitanalytics.com`
- `jems.com`
- `emsworld.com`
- `ems1.com`
- `globenewswire.com`
- `businesswire.com`
- `prnewswire.com`

## 검증 규칙

- 최종 포함 여부는 검색 결과 snippet이 아니라 원문 URL, 발행일, 본문으로 판단한다.
- 발행일이 범위를 벗어나면 제외한다.
- 중복 URL과 같은 발표를 옮긴 중복 기사는 하나만 남긴다.
- 원문 확인이 어려운 후보는 제외한다.
- 해외 기사 요약은 `news_briefing.md`에 한국어로 작성한다.

## 우선순위

동률이면 아래 순서로 선택한다.

1. 의료 AI 직접성
2. 응급실·응급의료·중환자실 직접성
3. 실제 도입·운영·제휴·제품 통합 여부
4. 병원, 공공기관, 회사 공식 발표 여부
5. 주간 대표성
6. 날짜 최신성
