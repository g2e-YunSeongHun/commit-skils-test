---
name: spring-boot-review
description: 'Spring Boot 프로젝트에 특화된 코드 리뷰 체크리스트를 적용한다.'
---

# Spring Boot Review Specialist

이 스킬은 Spring Boot + Java 17 환경을 기준으로 동작한다.

---

## 1. 트랜잭션 및 이벤트

- @Transactional 범위가 적절한가?
- @TransactionalEventListener phase 설정이 의도와 일치하는가?
- AFTER_COMMIT 이벤트가 실제로 필요한가?
- 중복 실행 가능성은 없는가?

---

## 2. 동시성 / 데이터 무결성

- race condition 가능성
- 중복 insert 가능성
- unique constraint로 방어되는지 여부
- tryLock / synchronized 사용 시 범위 적절성

---

## 3. DB 영향 분석

- 새로운 컬럼 nullable 여부 적절한가?
- 인덱스 필요성 검토했는가?
- 대량 데이터에서 성능 영향은 없는가?
- N+1 쿼리 발생 가능성

---

## 4. 예외 처리

- RuntimeException 남발 여부
- 의미 있는 커스텀 예외 사용 여부
- ControllerAdvice로 일관 처리하는가?

---

## 5. Docker / Runtime

- Java 17 기준 코드인가?
- 특정 JDK 구현(예: Temurin) 의존 코드 없는가?
- 환경 변수 하드코딩 여부

---

## 6. 로그 전략

- 민감 정보 로그 출력 여부
- ERROR 레벨 과다 사용 여부
- 운영 로그 노이즈 가능성

---

## Output Format

### 🔍 구조적 문제

...

### ⚠ 리스크

...

### 🛠 개선 제안

...dd

### ✅ 종합 판단

- 안정적
  또는
- 개선 필요
