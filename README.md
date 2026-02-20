# commit-skils-test

스킬 테스트

## Available Skills

| 스킬                    | 설명                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `review-and-commit-msg` | WBS 모달 텍스트를 입력받고, git diff 기반으로 변경사항을 요약/리뷰한 뒤 회사 템플릿에 맞는 커밋 메시지 3개를 생성한다. |

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

## Install skills from this repo

```bash
# 전체 스킬 설치
npx skills add g2e-YunSeongHun/commit-skils-test

# 특정 스킬만 설치
npx skills add g2e-YunSeongHun/commit-skils-test --skill review-and-commit-msg
```
