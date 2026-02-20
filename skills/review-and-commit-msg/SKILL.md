---
name: review-and-commit-msg
description: 'WBS 모달 텍스트를 입력받고, git diff 기반으로 변경사항을 요약/리뷰한 뒤 회사 템플릿에 맞는 커밋 메시지 3개를 생성한다.'
---

# Review + Commit Message Automation (Company Base)

## Trigger

Apply when user says:

- 커밋해줘
- 커밋 메시지 만들어줘
- commit / commit message
- 메시지만

## Inputs (Mandatory)

1. WBS modal text (recommended)
   - WBS code: WBS-<number>
   - Title: usually the first line
2. git diff (when available)
   - If staged changes exist: `git diff --staged`
   - Otherwise: `git diff`

If no WBS text is provided:

- Ask the user: "WBS 모달 텍스트 붙여줘. 없으면 WBS 코드만이라도, 그것도 없으면 '없음'이라고 알려주세요." and wait for user input.
- Never invent a WBS code.

## Step 1) Parse WBS (source of truth)

- Extract WBS code by regex: `WBS-\d+`
- Extract title: first non-empty line near the top (usually first line)
- If multiple WBS codes appear (next/prev links), pick the one that matches the current item (heuristic: the code near the title/status block).

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

- Read `templates/commit-msg-template.md` if present and follow it as source of truth.
- If template file is not present, use the built-in company template below.
- Generate exactly 3 candidates.
- Do not run git commands.

### Built-in company template (fallback)

<emoji> <subject>

Context:

- <WBS Title> (<WBS Code or N/A>)

Change:

- <2-4 bullets derived from diff>

Impact:

- <risk / migration notes>

Refs:

- <WBS Code or N/A>

## Step 6) User Selection & Commit Execution

- Present the 3 candidates and ask the user to pick one (or request edits).
- On selection:
  - If staged files exist → `git commit -m "..."`
  - If nothing is staged → show `git add` targets and confirm with the user before committing.
- If the trigger was "메시지만" → skip this step entirely (message generation only).
