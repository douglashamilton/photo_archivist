# Delivery Workflow

1. **Research** - run `prompts/step-1-research.prompt.md` to collect the intake and create `docs/prd.md` from `.agent/PRD-template.md`.
2. **Design** - run `prompts/step-2-design.prompt.md` to produce `docs/tdd.md` using `.agent/TDD-template.md`.
3. **Plan & Execute** - loop with `prompts/step-3-plan-and-execute.prompt.md`, saving slice plans to `docs/slices/` via `.agent/plan-template.md` and updating `docs/build-log.md`.

Review the templates in `.agent/` before starting a new artefact.
