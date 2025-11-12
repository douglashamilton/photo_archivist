# Slice 0: Bootstrap web app shell

## Context
- PRD section / link: docs/prd.md (Must-Have Features: UI to choose a local directory and input start/end dates)
- TDD component / link: docs/tdd.md (Architecture Overview - GET / entrypoint and templated UI)
- Current state summary (1-2 sentences). No application code or Python project structure exists yet; repo only contains planning artefacts.

## Tasks
- [x] Set up a Python project scaffold (pyproject, app package, tooling configs) with FastAPI, Jinja2, and pytest dependencies.
- [x] Implement `GET /` route in FastAPI that renders a Jinja template with directory + start/end date inputs (HTMX-ready form markup).
- [x] Add initial pytest ensuring the landing page returns 200 and includes expected form fields.

## Tests & Validation
- Automated: `pytest`
- Manual check: Run `uvicorn app.main:app --reload`, open `http://localhost:8000/`, and confirm the landing page renders the directory picker and date inputs.

## Decisions & Follow-ups
- Defer actual scan orchestration, HTMX partials, and background execution to later slices.
