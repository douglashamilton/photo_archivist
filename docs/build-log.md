# Build Log

Summarise each completed slice here. Include:
- Date and slice ID.
- Brief description of the change.
- Decisions made or follow-up items.
- Links to relevant slice plans, PRD/TDD sections, or code references.

## 2025-10-27 - Slice 0
- Bootstrapped FastAPI project skeleton and tooling (pyproject.toml, app/main.py) per docs/slices/slice-0.md.
- Delivered landing page route GET / with directory/date form tying to docs/prd.md Must-Have UI and docs/tdd.md Architecture entrypoint.
- Added tests/test_app.py using httpx ASGITransport; ran .venv\Scripts\python -m pytest.
- Manual check: Run uvicorn app.main:app --reload and open http://localhost:8000/ to confirm the form renders and fields match the test.
- Follow-up: implement scan API, HTMX interactions, and background processing in upcoming slices.

## 2025-10-27 - Slice 1
- Added scan domain models and synchronous service (app/models.py, app/services/scanner.py) to filter JPEGs by date with brightness scoring per docs/slices/slice-1.md and docs/prd.md Must-Have shortlist.
- Implemented /api/scans FastAPI endpoint with HTMX partial rendering (app/main.py, app/templates/partials/shortlist.html) aligning to docs/tdd.md data flow.
- Expanded automated tests for scanner and endpoint (tests/test_scanner.py, tests/test_app.py); ran .venv\Scripts\python -m pytest.
- Hardened UX so non-HTMX submissions render the full page and preserve form values, ensuring the shortlist appears even if the CDN script fails.
- Manual check: Launch uvicorn app.main:app --reload, submit the form against a directory of sample JPEGs, and confirm the shortlist updates or shows validation errors.
- Follow-up: Move scan execution to background workers, stream progress, and generate thumbnails in later slices.
