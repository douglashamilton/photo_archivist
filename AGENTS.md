# AGENTS.md

Guidance for any agent contributing to the Photo Archivist workspace.

## Mission
- Deliver incremental value that aligns with the latest `docs/prd.md`.
- Keep the technical approach consistent with `docs/tdd.md`.
- Default to vertical slices so stakeholders can review working software after every loop.

## Workflow Overview
1. **Research** - run `prompts/step-1-research.prompt.md` to collect the intake and create `docs/prd.md` from `templates/PRD-template.md`.
2. **Design** - run `prompts/step-2-design.prompt.md` to produce `docs/tdd.md` using `templates/TDD-template.md`.
3. **Plan & Execute** - loop with `prompts/step-3-plan-and-execute.prompt.md`, saving slice plans to `docs/slices/` via `templates/plan-template.md` and updating `docs/build-log.md`.

Each slice must finish with automated tests plus a manual verification note for the user before moving on.

## Repo Tour
- `prompts/` - step-by-step playbooks. Start here.
- `templates/` - PRD, TDD, and slice-plan templates.
- `docs/` - live artefacts (`prd.md`, `tdd.md`, `build-log.md`, `slices/`).
- `docs/apis/` - API documentation, static. 

Review these folders and the relevant template before creating or updating an artefact.

## Development Practices
- Work in small, reviewable increments tied to a slice plan.
- Fold bug fixes into the latest slice so that each slice is a complete, **working**, feature. 
- Keep scope tight; raise follow-up tasks for broader refactors.
- Maintain or add automated tests that prove the change.
- Run the relevant test suites before sharing work. If no suite exists, document the chosen manual verification in the build log.
- Ensure any generated or transient files are covered by `.gitignore`.

## Collaboration & PRs
- Summarise user-facing and technical changes, referencing the PRD/TDD or slice plan sections that guided decisions.
- Note outstanding questions or follow-ups in both the PR and `docs/build-log.md`.
- Confirm tests and manual checks ran successfully before requesting review.
