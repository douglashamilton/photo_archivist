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
- Manual check: Run `uvicorn app.main:app --reload`, scan a directory with multiple photos, toggle selection for any shortlist item, and confirm the button/indicator swaps between "Select" and "Deselect" without rerunning the scan.
- Follow-up: Evaluate later whether a bulk "clear selections" control or persistence across sessions is needed.

## 2025-11-06 - Slice 5
- Introduced a `PrintOrderService` with payload construction and Prodigi submission plumbing plus `/api/prints` form/JSON handling, supporting configurable asset host and API key (app/services/print_orders.py, app/main.py, app/models.py).
- Added a print controls partial with recipient form, selection-aware hidden fields, and HTMX refresh triggers so users can submit selected photos for printing (app/templates/index.html, app/templates/partials/print_controls.html).
- Hardened UX for HTMX submissions so even Prodigi failures return the refreshed partial rather than surfacing 4xx/5xx blank states (app/main.py, tests/test_app.py).
- Eliminated HTMX swap errors by moving the refresh behavior onto the `section#print-controls` element so fragments can replace themselves cleanly (app/templates/partials/print_controls.html).
- Normalised the Prodigi API key input, asserted outgoing requests include Prodigi’s expected `X-API-Key` header, and added a stdlib HTTPS fallback so Windows/Python 3.13 environments that hit the `httpcore`/`IntEnum` import bug can still submit orders (app/models.py, app/services/print_orders.py, tests/test_app.py).
- Updated dependencies to include `httpx` and `email-validator`, and extended test coverage for print submission flows plus error states; ran `.venv\Scripts\python.exe -m pytest`.
- Manual check: Run `uvicorn app.main:app --reload`, complete a scan, select shortlist photos, fill the print form (including a valid sandbox API key), and confirm either a success banner with an order reference or an inline error panel with Prodigi’s message.
- Follow-up: Implement real asset publishing for HTTPS-accessible originals, hook up Prodigi status polling, and consider mirroring the HTMX response helper on other form endpoints if similar issues arise.

## 2025-11-07 - Slice 6
- Scope: docs/slices/slice-6.md tightened the print refresh flow so it can’t crash during HTMX validation.
- Updated `app/templates/partials/print_controls.html` so the `hx-vals` expression pulls the scan id from the DOM via `document.getElementById(...)` when an event detail is missing, eliminating the `Cannot read properties of undefined (reading 'scanId')` error surfaced in the browser console.
- Added a regression assertion to `tests/test_app.py::test_print_controls_fragment_requires_scan_id` to lock in the new fallback.
- Automated: `.venv\Scripts\python.exe -m pytest`.
- Manual check: Launch `uvicorn app.main:app --reload`, run a scan, select at least one photo, open the browser console, submit the print form, and confirm the fragment refresh completes without HTMX errors.

## 2025-11-08 - Slice 7
- Scope: docs/slices/slice-7.md adds Prodigi exchange diagnostics so failed print orders can be debugged without digging through server logs.
- Extended `ProdigiAPIError` and `PrintOrderService` to capture sanitized request and response details, propagating them through `/api/prints` responses and HTMX feedback (`app/services/print_orders.py`, `app/main.py`).
- Corrected the outbound header to `X-API-Key` (Prodigi’s expected name) and aligned the automated tests with the new casing so sandbox submissions authenticate again.
- Updated the print controls partial with a collapsible debug block that renders the captured payloads, giving operators immediate visibility into what Prodigi saw (`app/templates/partials/print_controls.html`).
- Added API/HTML coverage to assert the debug contract plus the existing Prodigi error path, and ran `.venv\Scripts\python.exe -m pytest` (`tests/test_app.py`).
- Manual check: Trigger a failing print submission (e.g., send an invalid API key), expand the “Prodigi debug details” panel, and confirm the request/response JSON matches expectations.

## 2025-11-09 - Slice 8
- Scope: docs/slices/slice-8.md completes the secure credential + cleanup work requested by the stakeholder.
- Removed the Prodigi API key input entirely; the print form now trusts the server’s `PHOTO_ARCHIVIST_PRODIGI_API_KEY`, `PrintOrderRequest` no longer accepts a key, and `PrintOrderService` trims/validates the env var with new regression coverage so missing config surfaces as a 400 (`app/models.py`, `app/services/print_orders.py`, `app/main.py`, `app/templates/partials/print_controls.html`, `tests/test_app.py`).
- Documented the need to install the `[dev]` extra (to bring in `pytest-asyncio`) in `docs/tdd.md` so fresh environments don’t see “async def functions are not natively supported” warnings when running pytest.
- Hardened background cleanup: `ScanManager` now limits completed history, removes thumbnail folders as it prunes, and exposes a shutdown hook that the FastAPI app calls to close the executor and delete cached assets; added targeted tests to prove pruning/shutdown behavior (`app/services/scan_manager.py`, `app/services/thumbnails.py`, `app/main.py`, `tests/test_scan_manager.py`).
- Automated: `pytest`.
- Manual check: Set `PHOTO_ARCHIVIST_PRODIGI_API_KEY`, run `uvicorn app.main:app --reload`, submit a print order without supplying an API key in the UI, observe the success banner, then stop the server and verify the temporary thumbnail folders under your temp directory disappear.

