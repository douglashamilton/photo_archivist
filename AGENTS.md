# AGENTS.md

Guidance for any agent contributing to the Photo Archivist workspace.

## Mission
- Deliver incremental value that aligns with the latest `docs/prd.md`.
- Keep the technical approach consistent with `docs/tdd.md`.
- Default to vertical slices so stakeholders can review working software after every loop.

## Workflow Overview
1. **Research** — collect the intake and produce the PRD (`docs/prd.md`) using `.agent/PRD-template.md`.
2. **Design** — derive the TDD (`docs/tdd.md`) from `.agent/TDD-template.md`.
3. **Plan & Execute** — iterate slices with `prompts/step-3-plan-and-execute.prompt.md`. Store slice plans in `docs/slices/`, and update `docs/build-log.md` with outcomes, decisions, and manual checks.

Each slice should end with automated tests plus a manual verification note for the user.

## Repo Tour
- `prompts/` — step-by-step playbooks. Start here before beginning work.
- `.agent/` — templates for PRD, TDD, and slice plans.
- `docs/` — live artefacts (`prd.md`, `tdd.md`, `build-log.md`, `slices/`).

Review these folders before making substantive changes.

## Development Practices
- Work in small, reviewable increments tied to a slice plan.
- Keep scope tight; raise follow-up tasks for broader refactors.
- Maintain or add automated tests that prove the change.
- Run the relevant test suites before sharing work. If no suite exists, document the chosen manual verification in the build log.
- Ensure any generated or transient files are covered by `.gitignore`.

## Collaboration & PRs
- Summarise user-facing and technical changes, referencing the PRD/TDD or slice plan sections that guided decisions.
- Note outstanding questions or follow-ups in both the PR and `docs/build-log.md`.
- Confirm tests and manual checks ran successfully before requesting review.
