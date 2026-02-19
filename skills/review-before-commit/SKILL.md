---
name: review-before-commit
description: '커밋 요청 시 git diff 기반 코드 리뷰를 선행하고, 통과 시에만 고품질 커밋 메시지를 생성한다.'
---

# Rule: Review Before Commit (Mandatory Workflow)

사용자가 다음과 같이 요청하면:

- "커밋해줘"
- "commit"
- "커밋 메시지 만들어줘"
- "이거 커밋하자"

즉시 커밋하지 말고 반드시 아래 절차를 따른다.

---

## 1. Pre-Check

1. `git status -sb`를 기반으로 변경 파일 목록 요약
2. staged 변경이 있다면 `git diff --staged`
3. 없다면 `git diff`
4. 변경 의도를 3~5줄로 요약

---

## 2. Code Review Checklist

아래 항목을 점검하고 "문제 있음 / 없음"으로 명확히 구분한다.

### 공통

- ❗ 잠재적 버그 (null, 경계값, 예외 처리 누락)
- ❗ console.log / debug 코드 잔존 여부
- ❗ TODO/FIXME 미처리
- ❗ 보안 위험 (API key, 토큰 하드코딩)
- ❗ 성능 저하 가능성

### 품질

- 가독성 개선 가능 여부
- 중복 코드 여부
- 함수/메서드 길이 과도 여부
- 네이밍 일관성

### Spring Boot Specific Review (if applicable)

- Transaction boundary correctness (@Transactional usage)
- Event listener phase correctness (AFTER_COMMIT safety)
- Concurrency / race condition risks
- DB performance / N+1 / index requirement
- Exception handling consistency
- Logging of sensitive data

---

## 3. Review Output Format

반드시 아래 형식 유지:

### 🔍 변경 요약

- ...

### ⚠ 리스크

- ...

### 🛠 개선 제안

- 파일:라인 기준으로 구체적으로 제시

### ✅ 결론

- "리뷰 통과"
  또는
- "수정 후 재검토 필요"

---

## 4. Commit Message Generation (리뷰 통과 후에만)

- Conventional Commits 형식 사용
- 제목은 50자 이내
- 필요 시 본문에 이유/영향 포함

형식 예시:
