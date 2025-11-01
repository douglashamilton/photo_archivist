# Slice 2: Background scan workflow and status polling

## Context
- PRD section / link: docs/prd.md (Acceptance Criteria: user sees in-progress feedback; Must-Have Features: rerun pipeline with refreshed shortlist)
- TDD component / link: docs/tdd.md (Interfaces: `/api/scans`, `/api/scans/{scan_id}`, `/fragments/shortlist/{scan_id}`; Architecture Overview: ScanManager background execution)
- Current state summary (1-2 sentences). `POST /api/scans` runs synchronously, blocking the request until the shortlist is ready, and there is no job manager or progress endpoint for polling.

## Tasks
- [x] Add a `ScanManager` service with a background `ThreadPoolExecutor` to execute scans asynchronously and track status/results.
- [x] Update FastAPI routes to create scan jobs (`POST /api/scans` returning an id), expose a status endpoint, and render a polling-friendly shortlist fragment.
- [x] Refresh templates/HTMX flow to kick off background scans, show progress placeholders, and poll for completion.
- [x] Expand automated tests covering job lifecycle, status responses, and partial rendering states.

## Tests & Validation
- Automated: `pytest`
- Manual check: Start `uvicorn app.main:app --reload`, submit a scan against a sample directory, confirm the UI shows an in-progress message then updates to the shortlist without reloading the page.

## Decisions & Follow-ups
- Defer thumbnail generation to a later slice per TDD pipeline plan.
- Revisit progress granularity (per-file updates vs completed-only) once basic status polling is stable.
