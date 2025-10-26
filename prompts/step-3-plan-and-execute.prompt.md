# Plan and Execute

**Prerequisites**
- `docs/prd.md` and `docs/tdd.md` exist and reflect the current scope. If either is missing, return to the earlier steps before continuing.

**Deliverables**
- Slice plans saved as `../docs/slices/slice-<id>.md` using `templates/plan-template.md`.
- Running project log in `../docs/build-log.md`.

**Next Action**
- After every slice, report implementation status, share the manual check, and confirm with the user before starting the next slice.

## Step 1 — Review

Read the PRD and TDD. Assess the current codebase to understand the remaining gap to the MVP.

## Step 2 — Plan the Slice

Choose the next vertical slice. Capture the plan in `../docs/slices/slice-<id>.md` using `templates/plan-template.md`. Include dependencies, tasks, automated tests, and a manual verification step for the user.

## Step 3 — Execute

Implement the slice, keeping work within the agreed scope. Add or update automated tests to prove the behaviour and guard against regressions.

## Step 4 — Log and Share

Update `../docs/build-log.md` with a concise summary of the slice, key decisions, and follow-ups. Report progress to the user together with the manual check instructions.

## Step 5 — Repeat

Continue iterating through Steps 1–4 until the MVP acceptance criteria from `docs/prd.md` are satisfied, re-appraising the plan after each slice.
