# Implement Manual OneDrive Scan and Shortlist API

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Deliver the first end-to-end slice that turns a successful Microsoft sign-in into something tangible: a manual API-triggered scan that walks OneDrive via the Microsoft Graph delta endpoint, records JPEG photo metadata in SQLite, and responds with the top ten candidates for a given month. After this change a user can authenticate, invoke `/api/run/scan`, and immediately fetch `/api/shortlist` to review which photos were shortlisted and why.

## Progress

- [ ] Extend storage models and configuration to capture Graph item identity, resolution, month buckets, and delta cursors.
- [ ] Expose an access-token retrieval path in `MSALClient` and wrap the Microsoft Graph delta API in `graph/client.py`.
- [ ] Implement `ScanService.run` with JPG filtering, resolution gating, and shortlist persistence.
- [ ] Add `/api/run/scan` and `/api/shortlist` endpoints plus Pydantic schemas for requests and responses.
- [ ] Cover the new logic with service-level and API tests using mocked Graph responses.
- [ ] Update developer docs and `.env.example` so the flow is discoverable.

## Surprises & Discoveries

None yet.

## Decision Log

- Decision: _pending_
  Rationale: _pending_
  Date/Author: _pending_

## Outcomes & Retrospective

To be written after the slice lands.

## Context and Orientation

The FastAPI entrypoint in `src/photo_archivist/app.py` currently serves `/health` and `/api/auth/connect`; there is no capability to read files from OneDrive or to populate the database beyond table creation. `src/photo_archivist/auth/msal_client.py` can start a PKCE or device flow and caches tokens, but it does not surface a method to fetch an access token for Microsoft Graph. The storage layer in `src/photo_archivist/storage/models.py` defines `PhotoItem`, `Run`, `ShortlistEntry`, and `Order`, yet these models lack Graph-specific identifiers, width or height columns, or a place to store the Graph delta cursor. There is no repository helper (`storage/repo.py` in the TDD), no `graph` or `services` packages, and no shortlist endpoints. Tests exist for the health route, the auth connect behavior, and storage initialization, but nothing exercises a scan workflow. A “delta cursor” is the opaque URL returned by `GET /me/drive/root/delta` via `@odata.deltaLink`; keeping it allows the next scan to ask for only new or changed files. A “month bucket” will be the `YYYY-MM` string derived from a photo’s `takenDateTime` to decide which shortlist it belongs to.

## Plan of Work

Start by expanding configuration and dependencies. In `pyproject.toml` add `requests` to the main dependencies (Graph calls) and `responses` to the `dev` extras (HTTP mocking). Update `src/photo_archivist/config.py` and `.env.example` with defaults for `SCAN_SHORTLIST_SIZE` (default 10), `GRAPH_ROOT_PATH` (default `/me/drive/root`), and `GRAPH_PAGE_SIZE` (limit 200 items per delta request).

Modify `src/photo_archivist/auth/msal_client.py` to expose a `get_token(scopes: list[str]) -> str` method that first tries `acquire_token_silent` with cached accounts and only falls back to interactive flows if needed. Store the last successful account identifier so scans can run without re-prompting. Add logging whenever silent token acquisition fails.

Introduce `src/photo_archivist/graph/client.py` and `src/photo_archivist/graph/__init__.py`. Implement a thin `GraphClient` that accepts a token supplier callable, constructs `requests` sessions with retry-friendly headers, and exposes `get_delta(cursor: str | None) -> tuple[list[DriveItem], str]`. Each call should honor `GRAPH_PAGE_SIZE`, follow `@odata.nextLink` until all pages for the call are retrieved, and return both the collected DriveItems and the final `@odata.deltaLink`. Define a light `DriveItem` dataclass capturing `id`, `drive_id`, `name`, `mime_type`, `download_url`, `captured_at`, `width`, `height`, and `last_modified`. Implement helpers to normalise ISO8601 timestamps (replace trailing `Z` with `+00:00`) and skip entries that have no `file` payload or whose `file.mimeType` is not `image/jpeg`.

Expand the storage schema. In `src/photo_archivist/storage/models.py` add columns to `PhotoItem` for `drive_item_id` (unique string), `drive_id`, `download_url`, `width`, `height`, `month`, and `quality_score` (float). Keep `source_url` but re-label it via a comment as the future share link placeholder. Add indexes on `drive_item_id`, `month`, and `quality_score`. Extend `Run` with `month`, `delta_cursor`, `total_items`, `eligible_items`, `shortlisted_items`, and `error_message`. Add a `score` column to `ShortlistEntry`. Regenerate SQLAlchemy metadata accordingly and update `tests/storage/test_db.py` to assert that these new columns exist. Provide `src/photo_archivist/storage/repo.py` with a `Repository` class that wraps `get_session()` and offers methods such as `create_run(month: str)`, `update_run_stats(...)`, `upsert_photo(...)`, `replace_shortlist(run, photo_ids_with_scores)`, and `latest_run()` returning the most recent completed run for lookup of the prior delta cursor.

Create `src/photo_archivist/services/__init__.py` and `src/photo_archivist/services/scan_service.py`. Implement `ScanService` so that `run(month: str | None, limit: int | None)` determines the month bucket (default to the previous calendar month if not provided), pulls the latest delta cursor from the repository, requests delta pages via `GraphClient`, filters the incoming items to JPEGs whose `captured_at` month matches, and enforces the 4x6 resolution gate by requiring the longer edge to be at least 1800 pixels and the shorter edge at least 1200 pixels. Compute a simple `quality_score` using resolution (e.g., `width * height`) and use it for sorting. Upsert photos so reruns update metadata but never duplicate rows. Persist shortlist entries for the top `limit` items and record counts (`total`, `eligible`, `shortlisted`) plus the new `delta_cursor`. Mark run status transitions (`PENDING` -> `RUNNING` -> `COMPLETED` or `FAILED`) through the repository. Surface a structured return that includes the run id, month, and stats.

Update the web API. Extend `src/photo_archivist/schemas.py` with models for `ScanRequest`, `ScanResponse`, `ShortlistItem`, and `ShortlistResponse`. Patch `src/photo_archivist/app.py` to instantiate `GraphClient` and `ScanService` lazily (using the singleton MSAL client) and add two routes: `POST /api/run/scan` that triggers a scan and responds with the run metadata, and `GET /api/shortlist` that accepts a `month` query parameter and returns the stored shortlist (joining `PhotoItem` and `ShortlistEntry` and exposing filename, taken date, width, height, and quality score). Ensure the shortlist endpoint errors with 404 when no run exists for the requested month, and that both endpoints guard against missing tokens by surfacing a 409 with a helpful message asking the user to connect first.

Testing is critical. Add `tests/services/test_scan_service.py` with a fake Graph client that yields crafted DriveItems covering eligible photos, low-resolution rejects, and different months, and assert that only the expected items are shortlisted and that reruns reuse the delta cursor. Introduce `tests/api/test_scan_endpoints.py` to patch the service layer and verify FastAPI wiring, payload validation, and error handling. Store reusable Graph fixtures under `tests/fixtures/sample_drive_payloads.json` if needed. Update `tests/api/__init__.py` as necessary and extend `tests/test_api_contracts.py` to include the new routes. Ensure tests patch `get_msal_client()` to avoid real authentication.

Finally, document the flow. Update `README.md` with a short “Run a manual OneDrive scan” section showing how to call the new endpoints from PowerShell, and extend `.env.example` with the new settings so developers know which knobs exist. If new directories (`graph`, `services`, `storage/repo.py`) are created, ensure they contain `__init__.py` markers.

## Concrete Steps

Implementers should run commands from the project root (`c:\Projects\VS Code\Source\photo_archivist`).

    pip install -e .[dev]

    ruff check src tests

    pytest tests/storage/test_db.py

    pytest tests/services/test_scan_service.py

    pytest tests/api/test_scan_endpoints.py

    pytest

    uvicorn src.photo_archivist.app:app --host 127.0.0.1 --port 8787 --reload

While the dev server is running, exercise the endpoints from another shell once authentication is complete:

    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8787/api/run/scan" -Body (@{ month = "2025-08"; limit = 10 } | ConvertTo-Json) -ContentType "application/json"

    Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8787/api/shortlist?month=2025-08"

## Validation and Acceptance

Acceptance hinges on observable behavior. After authenticating via `/api/auth/connect`, POST `/api/run/scan` with a target month and confirm a 202 response containing the run id, month, counts, and delta cursor fragment. Follow with `GET /api/shortlist?month=YYYY-MM` and confirm a 200 response that lists at most ten entries, each with the expected filename, capture timestamp, width, height, and quality score. On a second scan the shortlist should update without duplicating database rows, and the run record should show the new delta cursor. Unit and service tests must pass, and manual runs should log `storage.initialized`, `scan.started`, and `scan.completed` events without stack traces.

## Idempotence and Recovery

The scan endpoint should be safe to retry: rerunning for the same month should idempotently update metadata thanks to unique `drive_item_id` constraints and shortlist replacement. If a scan fails mid-run, mark the run as `FAILED` with an error message; a subsequent call should detect the failed state, reuse the last successful delta cursor, and continue. Document how to delete a run record or reset the delta cursor (for now, clearing the `runs` table) should a developer need to restart from scratch.

## Artifacts and Notes

Capture sanitized excerpts of scan logs (for example, counts per month and the stored delta cursor URL) and paste them into this section as indented blocks when available. Note any anomalies such as Graph throttling responses or unexpected MIME types so future readers understand production behavior.

## Interfaces and Dependencies

Add `requests` (runtime) and `responses` (tests) as declared dependencies in `pyproject.toml`. In `src/photo_archivist/graph/client.py` define:

    @dataclass
    class DriveItem:
        id: str
        drive_id: str
        name: str
        mime_type: str
        download_url: str | None
        captured_at: datetime
        width: int | None
        height: int | None
        last_modified: datetime

    class GraphClient:
        def __init__(self, token_supplier: Callable[[], str], *, root_path: str, page_size: int) -> None: ...
        def get_delta(self, cursor: str | None = None) -> tuple[list[DriveItem], str]: ...

In `src/photo_archivist/services/scan_service.py` provide:

    class ScanService:
        def __init__(self, graph_client: GraphClient, repo: Repository, shortlist_size: int) -> None: ...
        def run(self, month: str | None = None, limit: int | None = None) -> RunResult: ...
        def shortlist_for_month(self, month: str) -> list[ShortlistItem]: ...

In `src/photo_archivist/storage/repo.py` add:

    class Repository:
        def latest_run(self) -> Run | None: ...
        def create_run(self, month: str) -> Run: ...
        def mark_run_running(self, run: Run) -> None: ...
        def mark_run_completed(self, run: Run, *, delta_cursor: str, totals: RunTotals) -> None: ...
        def upsert_photo(self, item: DriveItem, month: str, quality_score: float) -> PhotoItem: ...
        def replace_shortlist(self, run: Run, ranked_photo_ids: list[tuple[int, float]]) -> None: ...
        def shortlist_for_month(self, month: str) -> list[ShortlistProjection]: ...

Ensure these interfaces are fully exercised by the new test suites and that all modules import types using absolute package paths (`photo_archivist.*`) to keep imports clean.
