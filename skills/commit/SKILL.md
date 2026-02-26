---
name: commit
description: 'Use this skill when user mentions "commit", "커밋", "커밋해줘", "커밋 메시지", "git commit" or wants to create a commit message. Reviews git diff and generates structured commit message following company template with WBS task selection support.'
---

# Review + Commit Message Automation (Company Base)

## Trigger

Use this skill when the user intends to create a git commit and/or wants commit message candidates, especially when they mention:

- 커밋해줘 / 커밋 쳐줘 / 커밋 올려줘
- 커밋 메시지 만들어줘 / 커밋메시지 / 커밋 메세지(오타 포함)
- git commit / commit message / 커밋 메시지 추천
- "WBS 1234로 커밋" 같이 WBS+커밋을 같이 언급
- "메시지만" (커밋 실행 없이 메시지 1개만)

Non-trigger:

- 단순 git 개념 질문(예: “커밋이 뭐야?”)에는 적용하지 말 것

## Inputs (Mandatory)

1. WBS 작업 번호 (recommended)
   - 숫자만 입력 (예: 1234)
2. git diff (when available)
   - If staged changes exist: `git diff --staged`
   - Otherwise: `git diff`

If no WBS number is provided:

- MANDATORY: Automatically run `git log --format="%s|%b" -n 10` WITHOUT asking for permission or notifying the user.
  - Parse Context section to extract WBS numbers and corresponding subjects
  - Extract 1-3 unique recent WBS tasks (exclude "N/A")
- Present options with clear visual formatting:
  ```
  ========================================
  WBS 작업 선택:
  ========================================
  1. 직접입력
  [2-4: Previous WBS tasks if found, e.g., "2. WBS-23 (MQTT 개선)"]
  [Last]: 취소
  ========================================
  선택 (숫자 입력):
  ```
- Wait for user selection.
- Never invent a WBS number.

## Step 1) Parse WBS (source of truth)

- If user selected "직접입력":
  - Ask with clear formatting:
    ```
    WBS 작업 번호를 입력해주세요 (숫자만, 예: 1234):
    없으면 '없음' 입력:
    ```
- If user selected a previous task: use that WBS number
- If user selected "취소": exit without proceeding
- Format WBS as WBS-<number> (예: 1234 → WBS-1234)
- If user provided "없음" or no number, set WBS to "N/A"

## Step 2) Inspect changes (diff-driven)

- Summarize `git status -sb`
- Read diffs:
  - Prefer: `git diff --staged`
  - Else: `git diff`
- Summarize "What changed" in 3–5 lines.
- If changes look unrelated, suggest splitting into multiple commits (backend vs frontend, refactor vs feature, formatting vs logic, deps vs behavior).

### Commit Split Guide (when split is suggested)

- Clearly explain the split criteria and reasoning (e.g., "API changes" and "UI fixes" should be separate commits).
- List the files belonging to each commit unit.
- On user approval:
  - Stage the first unit via `git add <files>` → review → generate commit message → commit.
  - Proceed with the next unit in the same manner.
- If the user says "just do it all at once", skip splitting and proceed as a single commit.

### Diff Scope Rule (Mandatory)

- Review must focus strictly on lines added/removed in the current diff.
- Only inspect minimal surrounding context needed to understand impact.
- Do NOT audit unrelated existing code.
- Ignore legacy technical debt not introduced by this change.

## Step 3) Review (Company Common Checklist)

### Common checks (always)

- Potential bugs: null/edge cases, error handling, broken logic
- Debug leftovers: console/log/print, TODO/FIXME
- Security: secrets/tokens, sensitive data in logs
- Quality: duplication, naming, overly large functions/files
- Unintended changes: unrelated formatting churn, stray files, generated artifacts

## Step 4) Output format (must)

Output the review in the following format (in Korean):

### 🔍 변경 요약

- ...

### ⚠ 리스크 / 주의점

- ...

### 🛠 개선 제안

- 파일/라인 중심으로 구체적으로

### ✅ 결론

- 리뷰 통과 / 수정 필요 / 커밋 분리 권장

## Step 4 → Step 5 Branching Rule

### Review Passed

- Proceed to Step 5.

### Changes Required

- Do NOT generate commit messages.
- Show the review output (Step 4) and instruct: "위 이슈를 수정한 뒤 다시 커밋을 요청해주세요."
- If the user explicitly says "ignore and commit anyway", proceed to Step 5.

### Split Recommended

- Follow the Commit Split Guide in Step 2 before proceeding to Step 5 for each unit.

## Step 5) Commit Message Generation (must)

- First, try to read `templates/commit-msg-template.md` from the skill directory (do not ask for permission, just check).
- If found: use it as the source of truth for commit message format.
- If not found: use the built-in company template below.
- Generate exactly 1 best candidate.
- Do not run git commands.

### Built-in company template (fallback)

<emoji> <subject>

Context:

- <WBS-number | N/A>

Change:

- <2-4 bullets derived from diff>

Impact:

- <risk / migration notes>

## Step 6) User Selection & Commit Execution

- Present the 1 generated commit message to the user with clear visual formatting:
  ```
  ========================================
  제안된 커밋 메시지:
  ========================================
  [Display the commit message]
  ========================================
  1. 제안된 커밋 사용
  2. 제안된 커밋 수정
  3. 취소
  ========================================
  선택 (1-3):
  ```
- On selection:
  - Option 1: Proceed to commit
    - If staged files exist → `git commit -m "..."`
    - If nothing is staged → show `git add` targets and confirm with the user before committing.
  - Option 2: Ask the user "수정할 내용을 입력해주세요 (전체 커밋 메시지 또는 수정 지시):", then commit with the modified message.
  - Option 3: Cancel and exit without committing.
- If the trigger was "메시지만" → skip this step entirely (message generation only).
