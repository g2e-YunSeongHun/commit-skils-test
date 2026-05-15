# Search Rules

`news-scrap-codex`의 기사 수집은 `검색 회수율 확보 -> 원문 검증 -> freeze 고정`의 3단 구조로 고정한다. 목표는 단순히 많이 모으는 것이 아니라, 국내 기사 누락을 줄이면서도 매주 비슷한 품질과 구조의 기사 묶음을 만드는 것이다.

## 기간 고정

- 종료일: 해당 주 금요일
- 시작일: 종료일 기준 6일 전 토요일
- 예시: `2026-03-28 ~ 2026-04-03`

## 섹션 고정

- 국내 기사: 최대 3건
- 해외 기사: 최대 3건
- 최종 출력은 총 4~6건을 유지한다.

## 수집 단계

### 1. Scan

- 먼저 `python scripts/build_search_queries.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --format text`로 주차별 기사 중심 쿼리 세트를 만든다.
- 넓은 검색으로 후보를 수집한 뒤, 국내는 `필수 도메인 순회`, 해외는 `우선 기사 도메인 순회`를 추가 수행한다.
- 뉴스 전용 검색 결과나 포털 뉴스 결과는 후보 시드로만 사용한다. 최종 포함 여부는 반드시 원문 URL을 열어 판단한다.
- 국내 기사 `0건`을 선언하기 전에 `국내 필수 도메인` 전체에 대한 site-pass와 `진료 AI/급성 악화 예측/119·구급/문서화` 축 보조 검색을 수행한다.

### 2. Verify

- 후보 URL은 `python scripts/extract.py`로 본문과 발행일을 검증한다.
- 발행일이 범위를 벗어나면 제외한다.
- 원문 검증이 안 되는 재배포 단문은 제외한다.
- 제목보다 본문이 더 중요하다. 제목이 질환명/제품명 중심이어도 본문에서 응급실, 응급치료, 구급 워크플로, 급성 악화/중증화 예측 맥락이 확인되면 포함 후보로 유지한다.

### 3. Freeze

- 중복 URL과 사실상 동일한 재보도는 1건만 남긴다.
- 이전 주차에 이미 포함된 같은 제품/사업 발표를 이번 주 국내 재보도만으로 대표 기사에 올리지 않는다.
- `scripts/freeze_verified_articles.py`로 점수화, 정렬, 건수 상한을 고정한다.
- 대표 기사 선정은 검색 단계가 아니라 freeze 이후 고정된 `verified_articles.json`을 기준으로 수행한다.

## 직접 관련성 기준

아래 키워드 중 하나 이상이 기사 제목 또는 본문 핵심에 직접 등장해야 한다.

- 국문: `응급`, `응급실`, `응급의료`, `구급`, `119`, `중증`, `트리아지`, `환자 악화`, `임상 악화`, `중증화`, `입원 환자 악화`, `조기경보점수`, `병동 모니터링`
- 영문: `emergency`, `emergency department`, `ED`, `acute care`, `triage`, `ambulance`, `EMS`, `911`, `prehospital`, `trauma`, `patient deterioration`, `clinical deterioration`, `early warning score`, `ward monitoring`, `inpatient deterioration`

보완 규칙:

- `소방`은 단독 직접 관련성 키워드로 보지 않는다. `119`, `구급`, `신고접수`, `출동지령`, `상황관제`, `이송`, `응급의료` 같은 워크플로가 함께 확인될 때만 포함 후보로 유지한다.
- `뇌졸중 AI`, `뇌출혈 AI`, `CT/MR 판독 AI`, `POCUS AI`, `심전도 AI`처럼 질환/제품 축으로 노출된 기사라도 본문에서 응급 치료 판단, 응급 환자 대응, 응급실/구급 워크플로가 확인되면 포함 후보로 유지한다.
- 반대로 `의료 AI`나 `영상 AI`만 언급되고 응급의료 문맥이 약하면 제외한다.
- `트리아지`는 `응급의료/응급실 진료 AI` 축에 포함한다. 다만 `의료 AI` 단독 검색은 너무 넓으므로 `응급`, `응급실`, `119`, `구급`, `중증`, `트리아지`, `환자분류` 같은 응급 문맥어와 함께 사용할 때만 보조 검색으로 수행한다.
- `환자 악화`, `임상 악화`, `입원 환자 악화`, `조기경보점수`, `병동 모니터링`은 응급실 이전 또는 중환자실 전 단계의 급성 악화 위험 포착 기사로 포함 후보에 둔다. 단순 병동 운영 자동화나 일반 건강 모니터링은 제외한다.

## AI 관련성 기준

아래 키워드 중 하나 이상이 명시돼야 한다.

- 국문: `AI`, `인공지능`, `생성형 AI`, `의료 AI`, `대형언어모델`, `음성인식`, `자동화`
- 영문: `AI`, `artificial intelligence`, `LLM`, `foundation model`, `machine learning`, `automation`, `ambient`, `scribe`

## 검색 쿼리 구성

국내 검색은 4개 묶음으로 수행한다.

- 응급의료/응급실 진료 AI: `응급의료 AI`, `응급실 AI`, `응급환자 AI 트리아지`, `중증환자 AI 분류`, `응급 CT AI 판독`, `뇌졸중 AI 응급`, `심전도 AI 구급`, `POCUS AI 응급`
- 급성 악화/중증화 예측 AI: `환자 악화 AI`, `임상 악화 예측 AI`, `입원 환자 악화 예측 AI`, `조기경보점수 AI`, `병동 모니터링 AI`
- 119/구급 현장 AI: `119 AI 신고접수`, `119 AI 출동지령`, `119 AI 상황관제`, `구급대 AI`, `소방청 AI 119`, `소방청 AI 구급`
- 응급실 문서화/업무부담 AI: `응급실 AI 문서화`, `응급실 AI 진료기록`, `응급실 음성인식 AI`, `응급실 생성형 AI`, `응급실 실사용 AI`

국내 보조 검색에서 `의료 AI`는 단독으로 쓰지 않고 아래처럼 응급 문맥어를 붙인다.

- `의료 AI 응급실`
- `의료 AI 응급환자`
- `의료 AI 중증환자`

아래 쿼리는 기본 국내 수집에서 제외한다. 사용자가 명시적으로 운영/정책 축까지 넓혀 달라고 요청할 때만 fallback으로 검토한다.

- `응급실 AI 병상 배정`, `응급실 AI 환자 흐름`, `응급의료센터 AI 운영 시스템`, `응급 협진 AI 전원 조정`
- `소방 AI`, `AI 로봇`, `AI 기술위원회`처럼 119/구급/응급의료 워크플로가 제목 또는 본문 핵심에 없는 일반 소방·재난 기술 기사

해외 검색은 5개 묶음으로 수행한다.

- EMS/911: `EMS AI documentation ePCR`, `911 AI dispatch emergency medical services`, `ambulance AI routing dispatch`, `EMS AI protocol platform`
- 문서화/업무부담: `emergency department ambient AI scribe`, `AI documentation emergency department`
- 도입/상용화: `emergency care AI deployment news`, `emergency care AI partnership integration`, `AI clinical workflow platform EMS`
- 임상 보조/트리아지: `emergency department AI triage`, `emergency department AI clinical decision support deployment`, `AI fracture triage emergency department clearance`, `stroke AI emergency workflow`, `sepsis AI emergency department`, `POCUS AI emergency`
- 급성 악화/병동 모니터링: `patient deterioration AI ward monitoring`, `clinical deterioration prediction AI early warning score`, `inpatient deterioration AI ward monitoring`

`patient flow`, `bed management`, `hospital command center`는 기본 해외 수집에서 제외한다. 사용자가 응급실 운영/병상/전원 축까지 넓히라고 명시할 때만 fallback으로 검토한다.

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

### 해외 기사 우선 도메인

- `jems.com`
- `firehouse.com`
- `emsworld.com`
- `healthcareitnews.com`
- `beckershospitalreview.com`
- `fiercehealthcare.com`
- `mobihealthnews.com`
- `healthitanalytics.com`
- `ems1.com`
- `globenewswire.com`
- `businesswire.com`
- `prnewswire.com`

## 기사 유형 우선순위

동점이면 아래 순서를 우선한다.

1. 실제 도입/운영 사례
2. 병원, 소방, 공공기관 발표
3. 제품 통합, 수주, 파트너십, 상용화 기사
4. 정책 또는 공공사업
5. 응급의료 현장 영향이 큰 기술·제품 기사

## 제외 규칙

- 응급의료와 직접 관련 없는 일반 헬스케어 AI 기사
- 119/구급/응급의료 워크플로가 확인되지 않는 일반 소방 AI, 로봇, 위원회, 조직 신설 기사
- 응급의료 직접성이 약한 병상 배정, 환자 흐름, 전원 조정, 병원 운영 자동화 기사
- 단, 환자 악화/중증화 예측, 조기경보점수, 중환자실 전 단계 위험 포착이 본문 핵심이면 병동 기반 기사라도 제외하지 않는다.
- 해외 기본 모드에서 `patient flow`, `bed management`, `hospital command center`만 핵심인 병원 운영 기사
- 기사 원문 확인이 어려운 단문 재배포 기사
- 날짜가 범위를 벗어난 기사
- 같은 내용의 중복 기사
- 블로그, 커뮤니티, 영상 플랫폼, 개인 브런치형 글

## 동률 해소 규칙

여러 기사가 비슷하면 아래 순서로 선택한다.

1. 응급의료 또는 급성 악화 예측 직접성
2. 실제 도입 또는 운영 여부
3. 신규성: 이전 주차에 이미 다룬 같은 제품/사업 발표가 아닌지
4. 기관 신뢰도
5. 날짜 최신성
6. 제목 명확성

## 정렬 규칙

- 섹션 내부 정렬: `score desc -> date desc -> source asc -> title asc`
- 최종 JSON은 항상 이 정렬을 유지한다.
