# Search Rules

`news-scrap-codex`의 기사 수집은 `검색 회수율 확보 -> 원문 검증 -> freeze 고정`의 3단 구조로 고정한다. 목표는 단순히 많이 모으는 것이 아니라, 국내 기사 누락을 줄이면서도 매주 비슷한 품질과 구조의 기사 묶음을 만드는 것이다.

## 기간 고정

- 종료일: 해당 주 금요일
- 시작일: 종료일 기준 6일 전 토요일
- 예시: `2026-03-28 ~ 2026-04-03`

## 섹션 고정

- 국내 기사: 최대 3건
- 해외 기사/논문: 최대 3건
- 최종 출력은 총 4~6건을 유지한다.

## 수집 단계

### 1. Scan

- 먼저 `python scripts/build_search_queries.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --format text`로 주차별 쿼리 세트를 만든다.
- 넓은 검색으로 후보를 수집한 뒤, 국내는 `필수 도메인 순회`, 해외와 논문은 `우선 도메인 순회`를 추가 수행한다.
- 뉴스 전용 검색 결과나 포털 뉴스 결과는 후보 시드로만 사용한다. 최종 포함 여부는 반드시 원문 URL을 열어 판단한다.
- 국내 기사 `0건`을 선언하기 전에 `국내 필수 도메인` 전체에 대해 site-pass 쿼리를 최소 1회씩 수행한다.

### 2. Verify

- 후보 URL은 `python scripts/extract.py`로 본문과 발행일을 검증한다.
- 발행일이 범위를 벗어나면 제외한다.
- 원문 검증이 안 되는 재배포 단문은 제외한다.
- 제목보다 본문이 더 중요하다. 제목이 질환명/제품명 중심이어도 본문에서 응급실, 응급치료, 구급 워크플로가 확인되면 포함 후보로 유지한다.

### 3. Freeze

- 중복 URL과 사실상 동일한 재보도는 1건만 남긴다.
- `scripts/freeze_verified_articles.py`로 점수화, 정렬, 건수 상한을 고정한다.
- 대표 기사 선정은 검색 단계가 아니라 freeze 이후 고정된 `verified_articles.json`을 기준으로 수행한다.

## 직접 관련성 기준

아래 키워드 중 하나 이상이 기사 제목 또는 본문 핵심에 직접 등장해야 한다.

- 국문: `응급`, `응급실`, `응급의료`, `구급`, `중증`, `트리아지`
- 영문: `emergency`, `emergency department`, `ED`, `acute care`, `triage`, `ambulance`, `EMS`, `trauma`

보완 규칙:

- `뇌졸중 AI`, `뇌출혈 AI`, `CT/MR 판독 AI`, `POCUS AI`, `심장초음파 AI`처럼 질환/제품 축으로 노출된 기사라도 본문에서 응급 치료 판단, 응급 환자 대응, 응급실 워크플로가 확인되면 포함 가능하다.
- 반대로 `의료 AI`나 `영상 AI`만 언급되고 응급의료 문맥이 약하면 제외한다.

## AI 관련성 기준

아래 키워드 중 하나 이상이 명시돼야 한다.

- 국문: `AI`, `인공지능`, `생성형 AI`, `의료 AI`, `대형언어모델`
- 영문: `AI`, `artificial intelligence`, `LLM`, `foundation model`, `machine learning`

## 검색 쿼리 구성

국내 검색은 3개 묶음으로 수행한다.

- 핵심 키워드: `응급실 AI`, `응급의학 인공지능 병원 도입`, `응급환자 AI 트리아지`, `119 AI 시스템`, `중증환자 AI 분류`
- 질환/제품 보완: `뇌졸중 AI 응급`, `뇌출혈 AI 응급`, `응급 CT AI 판독`, `응급 심장초음파 AI`, `POCUS AI 응급`
- 운영/적용 보완: `응급실 AI 실사용 도구`, `응급 협진 AI`, `AI 응급치료 판단`, `응급실 AI 안착`

해외 검색은 3개 묶음으로 수행한다.

- 핵심 키워드: `emergency department AI triage`, `emergency medicine artificial intelligence`, `prehospital AI EMS prediction`
- 임상 보완: `stroke AI emergency workflow`, `sepsis AI emergency department`, `POCUS AI emergency`
- 도입 보완: `AI documentation emergency department`, `deployment AI emergency hospital`, `partnership AI EMS`

논문 검색은 2개 묶음으로 수행한다.

- 핵심 키워드: `emergency triage AI machine learning`, `emergency department AI clinical trial`, `prehospital emergency AI prediction model`
- 질환/도구 보완: `stroke AI emergency department paper`, `sepsis AI emergency paper`, `ultrasound AI emergency medicine paper`

실제 쿼리 문자열은 `scripts/build_search_queries.py` 출력값을 기준으로 사용한다.

## 도메인 우선순위

### 국내 필수 도메인

- `medicaltimes.com`
- `medigatenews.com`
- `dailymedi.com`
- `rapportian.com`
- `docdocdoc.co.kr`
- `mdtoday.co.kr`
- `hitnews.co.kr`
- `pharm.edaily.co.kr`
- `mohw.go.kr`

### 해외 우선 도메인

- `healthcareitnews.com`
- `beckershospitalreview.com`
- `statnews.com`
- `fiercehealthcare.com`
- `mobihealthnews.com`
- `ems1.com`
- `globenewswire.com`
- `businesswire.com`
- `prnewswire.com`

### 논문 우선 도메인

- `pubmed.ncbi.nlm.nih.gov`
- `pmc.ncbi.nlm.nih.gov`
- `annemergmed.com`
- `jmir.org`
- `medinform.jmir.org`
- `ai.nejm.org`
- `nature.com`
- `frontiersin.org`
- `mdpi.com`
- `sciencedirect.com`
- `link.springer.com`
- `biomedcentral.com`

## 기사 유형 우선순위

동점이면 아래 순서를 우선한다.

1. 실제 도입/운영 사례
2. 병원 또는 공공기관 발표
3. 검증된 연구 결과
4. 제품 발표 또는 파트너십

## 제외 규칙

- 응급의료와 직접 관련 없는 일반 헬스케어 AI 기사
- 기사 원문 확인이 어려운 단문 재배포 기사
- 날짜가 범위를 벗어난 기사
- 같은 내용의 중복 기사
- 블로그, 커뮤니티, 영상 플랫폼, 개인 브런치형 글

## 동률 해소 규칙

여러 기사가 비슷하면 아래 순서로 선택한다.

1. 응급의료 직접성
2. 실제 도입 또는 운영 여부
3. 기관 신뢰도
4. 날짜 최신성
5. 제목 명확성

## 정렬 규칙

- 섹션 내부 정렬: `score desc -> date desc -> source asc -> title asc`
- 최종 JSON은 항상 이 정렬을 유지한다.
