# commit-skils-test

## 커밋 자동화 테스트

## Available Skills

| 스킬     | 설명                                                                                      |
| -------- | ----------------------------------------------------------------------------------------- |
| `commit` | 커밋 메시지 생성. git diff 리뷰 후 회사 템플릿 기반 커밋 메시지 3개 제안. (WBS 번호 필요) |

## Skills CLI Commands

| 명령어                     | 역할                                       |
| -------------------------- | ------------------------------------------ |
| `npx skills add`           | 스킬 설치 (GitHub, GitLab, 로컬 경로 지원) |
| `npx skills find`          | 스킬 검색/탐색                             |
| `npx skills list` (`ls`)   | 설치된 스킬 목록 확인                      |
| `npx skills remove` (`rm`) | 스킬 제거                                  |
| `npx skills check`         | 업데이트 가능한 스킬 확인                  |
| `npx skills update`        | 설치된 스킬 전체 최신화                    |
| `npx skills init`          | 새 SKILL.md 템플릿 생성                    |

### Common Flags

| 플래그              | 적용 명령어          | 설명                                         |
| ------------------- | -------------------- | -------------------------------------------- |
| `-y`, `--yes`       | add, remove, sync    | 확인 프롬프트 건너뛰기                       |
| `-g`, `--global`    | add, remove, list    | 글로벌(유저 레벨) 스킬로 설치/제거/조회      |
| `-s`, `--skill`     | add, remove          | 특정 스킬만 지정 (예: `--skill commit`)      |
| `-a`, `--agent`     | add, remove, list    | 특정 에이전트 지정 (예: `--agent claude-code`)|
| `--all`             | add, remove          | 모든 스킬 + 모든 에이전트 + 확인 건너뛰기   |
| `--copy`            | add                  | symlink 대신 파일 복사로 설치                |

## Install skills from this repo

```bash
# 전체 스킬 설치
npx skills add g2e-YunSeongHun/commit-skils-test

# 특정 스킬만 설치
npx skills add g2e-YunSeongHun/commit-skils-test --skill commit

# 특정 스킬만 삭제
npx skills rm commit
```
