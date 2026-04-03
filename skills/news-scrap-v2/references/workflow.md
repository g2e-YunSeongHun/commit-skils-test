# Workflow

## 목표

응급의료 AI 주간 뉴스 브리핑을 `로컬 검증 -> NotebookLM 필수 게이트 -> 최종 산출물 생성`의 3단 구조로 고정한다.

## 단계

### 1. Scan

- 기간 계산
- 국내 기사, 해외 기사, 학술 논문 후보 수집
- 노이즈 도메인 제외
- 제목 기반 1차 관련성 필터링

출력:

- `candidates_raw.json`

### 2. Freeze

- `extract.py`로 URL별 본문/발행일 검증
- 기간 밖 기사 제외
- 발행일 불명확 기사 제외
- 중복 URL 제거
- 재보도 대표 기사 선택
- 응급의료 직접 관련성이 약한 일반 의료 AI 기사 제거

출력:

- `verified_articles.json`

이 파일이 이번 주차의 단일 진실원본이다.

### 3. NotebookLM Gate

- `build_notebook_sources.py` 실행
- 새 NotebookLM 노트 생성
- 기사별 개별 텍스트 파일 업로드
- 모든 소스 `ready` 확인
- Q0~Q5 수행
- 답변 저장

출력:

- `notebook_manifest.json`
- `notebooklm_outputs.json`

### 4. Publish

- NotebookLM 결과를 바탕으로 대시보드 입력 JSON 작성
- 대표 기사와 심층 리서치 정리
- 슬라이드 입력 JSON 작성
- HTML/PPT 생성
- 폴더 정리

출력:

- `news_*.html`
- `slide_*_vN.pptx`

## 실패 정책

아래 중 하나라도 실패하면 즉시 종료한다.

- NotebookLM 노트 생성 실패
- 소스 업로드 실패
- 소스 준비 상태 대기 실패
- Q0~Q5 중 하나라도 실패
- NotebookLM JSON 파싱 실패

실패 시 동작:

- `notebooklm_failure.json` 저장
- HTML 생성 안 함
- PPT 생성 안 함
- 기존 최종본 건드리지 않음

## 재실행 정책

- 기존 NotebookLM 노트 재사용 금지
- 실패 후 재실행은 `verified_articles.json`부터 다시 시작 가능
- 기사 구성 변경 시 `Freeze`부터 다시 수행
