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

## 2025-10-28 - Slice 2
- Introduced an asynchronous `ScanManager` with background execution and status tracking (app/services/scan_manager.py) per docs/slices/slice-2.md and docs/tdd.md Interfaces section.
- Updated FastAPI routes and HTMX workflow to enqueue scans, poll `/fragments/shortlist/{id}`, and expose `/api/scans/{id}` JSON status (app/main.py, app/templates/partials/shortlist.html).
- Refined scanner progress to stream totals while enumerating files and broadened JPEG extension support (app/services/scanner.py, app/templates/partials/shortlist.html).
- Expanded coverage with polling-focused tests for HTML and JSON clients plus incremental progress callbacks (tests/test_app.py, tests/test_scanner.py); ran `.venv\Scripts\python -m pytest`.
- Manual check: Start `uvicorn app.main:app --reload`, submit a scan against a directory with sample JPEGs, observe the "Preparing scan" hand-off to incremental counts, and wait for the shortlist to refresh automatically.
- Follow-up: Implement thumbnail generation/streaming and richer progress metrics in upcoming slices.

## 2025-10-29 - Slice 3
- Implemented cached thumbnail generation for shortlist results via a new service, wiring it into `ScanManager` after scans complete (app/services/thumbnails.py, app/services/scan_manager.py) per docs/slices/slice-3.md and docs/tdd.md thumbnail flow.
- Added `/api/thumbnails/{scan_id}/{photo_id}` streaming endpoint, surfaced thumbnail URLs in JSON, and rendered previews in the shortlist UI (app/main.py, app/templates/partials/shortlist.html).
- Extended the domain model with per-photo IDs and thumbnail metadata to track cached files (app/models.py, app/services/scanner.py).
- Updated automated coverage to assert thumbnail rendering and API delivery (tests/test_app.py, tests/test_scanner.py); ran `.venv\Scripts\python.exe -m pytest`.
- Manual check: Launch `uvicorn app.main:app --reload`, run a scan against a directory with sample JPEGs, and confirm each shortlist entry displays its corresponding thumbnail image in the browser.
- Follow-up: Plan a later slice to clean up cached thumbnails post-scan and surface thumbnail generation progress in status updates.

## 2025-11-01 - Slice 4
- Added shortlist selection state to `PhotoResult` and persisted it within `ScanManager`, aligning with docs/slices/slice-4.md and the TDD domain model.
- Introduced `/api/scans/{scan_id}/photos/{photo_id}/selection` to toggle selection, refreshing either the HTMX fragment or JSON payload, and adjusted serializers to expose the new flag (app/main.py, app/services/scan_manager.py).
- Updated the shortlist UI with select/deselect controls and visual feedback for chosen photos (app/templates/partials/shortlist.html, app/templates/index.html).
- Expanded tests to cover selection toggling in both HTML and JSON flows; ran `.venv\Scripts\python.exe -m pytest`.
- Manual check: Run `uvicorn app.main:app --reload`, scan a directory with multiple photos, toggle selection for any shortlist item, and confirm the button/indicator swaps between “Select” and “Deselect” without rerunning the scan.
- Follow-up: Evaluate later whether a bulk “clear selections” control or persistence across sessions is needed.



