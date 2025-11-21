# Slice 9: Scanner pipeline refactor

## Context
- PRD section / link: docs/prd.md (Bottom line, Must-Have extensible scoring pipeline, Data considerations).
- TDD component / link: docs/tdd.md (Architecture overview, Scan pipeline composition, Data flow).
- Current state summary (1–2 sentences). The scanner service is a monolith that mixes file walking, metadata resolution, brightness scoring, and shortlist selection, making it hard to plug in richer heuristics or test specific stages.

## Tasks
- [x] Split `app/services/scanner.py` into pipeline components (enumerator, metadata resolver, scoring engine, selector) and update `run_scan` to compose them without changing external behavior.
- [x] Add focused unit tests for the new components plus regression coverage so existing brightness-only results still match prior expectations.
- [x] Ensure progress callbacks and public models remain stable and document the refactor in the build log.

## Tests & Validation
- Automated: `pytest`.
- Manual check: Run `uvicorn app.main:app --reload`, trigger a scan over a sample directory, and confirm the shortlist still lists the brightest photos with accurate metadata and progress counts.

## Decisions & Follow-ups
- Decision: Keep brightness as the only active metric for this slice but expose a metrics dict on `PhotoResult`/`PhotoScore` so future heuristics can slot in.
- Follow-up: Plan subsequent slices to add portrait/composition signals leveraging the new scoring interface.
