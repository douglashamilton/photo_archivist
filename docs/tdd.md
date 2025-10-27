## Photo Archivist Technical Design

### Bottom line

Photo Archivist MVP ships as a local FastAPI (Python 3.12) web app using Jinja + HTMX for a lightweight UI that lets the user choose a directory, filter images by date, run a Pillow-backed brightness scan in the background, and render the five brightest thumbnails with file metadata without leaving the browser.

### Architecture Overview

* **Stack:** Python 3.12, FastAPI 0.115, Uvicorn for dev server, Jinja2 templates with HTMX for partial updates, Pydantic models, Pillow 11 for image I/O, pytest + httpx for tests, Ruff (lint + format), and pre-commit to wire everything together.
* **App structure:** Server-rendered views served by FastAPI; HTMX drives form submissions and result refreshes, while domain logic lives in a `services` module (scan orchestration, metadata extraction, scoring). Application state (scan jobs) is kept in an in-memory registry owned by a `ScanManager`.
* **Data storage:** No persistent store; scan results are cached per job in memory until replaced. Thumbnail binaries are generated on demand and memoized in a temp directory for the session (cleaned on shutdown).
* **Auth:** None; app runs locally and trusts the invoking user.
* **Deployment & environments:** Local dev via `uvicorn app.main:app --reload`; CI runs pytest and Ruff. Distribution via `pip install -e .` or packaged executable (future slice). No external services required.

### Tech Stack Decisions

* **Language/runtime:** Python 3.12 aligns with PRD requirement and provides `pathlib`/typing improvements.
* **Web framework:** FastAPI gives async routing, background tasks, and automatic validation via Pydantic for request payloads.
* **Templating/UI:** Jinja2 keeps rendering simple; HTMX enables partial HTML responses for progress/status without a SPA build step.
* **Image processing:** Pillow 11 handles JPEG EXIF parsing, resizing, and luminance scoring (`ImageStat.mean`).
* **File system:** `pathlib` + `os.scandir` for performant recursive traversal and filtering; `piexif` is optional but not required because Pillow covers the needed EXIF tags.
* **Background execution:** FastAPI `BackgroundTasks` plus an internal thread pool (via `concurrent.futures.ThreadPoolExecutor`) isolate long-running scans while keeping the main loop responsive.
* **Validation & schema:** Pydantic models encapsulate `ScanRequest`, `ScanStatus`, and `PhotoResult` payloads with date parsing and directory validation.
* **Testing:** pytest with tmp-path fixtures for synthetic photo trees and httpx AsyncClient for endpoint tests. Coverage tracked via `pytest --cov`.
* **Quality tooling:** Ruff configured to enforce linting and formatting (Black-compatible mode) in a single tool; `pre-commit` runs Ruff (lint + format), pytest -q, and ensures `docs/tdd.md`/`docs/prd.md` stay tracked.

### Interfaces

* **UI entrypoint:** `GET /` renders the form (directory picker + date fields) and initial shortlist when available.
* **Start scan:** `POST /api/scans` (JSON) → `{ "id": "<uuid>", "status": "queued" }`. Validates directory exists and dates are logical. On success, enqueues the job and starts background scan.
* **Poll status/results:** `GET /api/scans/{scan_id}` → `{ "status": "running|complete|error", "progress": { "processed": int, "total": int }, "results": [PhotoResult] }`. Returns HTTP 404 if the job id is unknown or expired.
* **Render shortlist fragment:** `GET /fragments/shortlist/{scan_id}` returns HTML partial (HTMX target) for the current shortlist state, including spinner/progress text while running.
* **Thumbnail streaming:** `GET /api/thumbnails/{scan_id}/{photo_id}` streams the generated JPEG thumbnail (`Content-Type: image/jpeg`); raises 404 if cache missing.
* **Error handling:** API returns JSON with `{ "detail": "..." }` and 4xx/5xx codes; HTML routes fall back to a friendly error template with actionable copy.

### Domain model

* **ScanRequest:** `{ id: UUID, directory: Path, start_date: date, end_date: date, requested_at: datetime }`.
* **ScanStatus:** `{ id: UUID, state: Enum[queued,running,complete,error], processed: int, total: int, updated_at: datetime, message: str|None }`.
* **PhotoMetadata:** `{ path: Path, filename: str, captured_at: datetime, modified_at: datetime, used_fallback: bool }`.
* **PhotoResult:** `{ id: UUID, metadata: PhotoMetadata, brightness: float, thumbnail_path: Path, generated_at: datetime }`.
* **ScanManager:** orchestrates job lifecycle, holds an in-memory `Dict[UUID, ScanStatus]` and `Dict[UUID, List[PhotoResult]]`, exposes thread-safe read/write, purges stale jobs after timeout.

### Data flow & interfaces

* **Inbound:** Browser form submission (HTMX POST) → FastAPI controller (`/api/scans`) → ScanManager enqueues job → background worker walks directory → metadata extractor → scoring service → shortlist reducer (top five) → cache results.
* **Processing pipeline:** For each JPEG, read EXIF `DateTimeOriginal`; if missing/unparseable, use file modified time. Skip files outside range. Generate downscaled thumbnail (max 256px longest edge) and compute brightness (mean luminance). Maintain a min-heap of top five by brightness to avoid storing the full set.
* **Outbound:** When job completes, API response and HTML fragment include five results sorted by brightness descending, with filename, capture date, brightness score, and thumbnail URL. HTMX swaps the shortlist section in place.

```http
POST /api/scans
Request: {
  "directory": "C:\\Users\\me\\Pictures\\Trip",
  "start_date": "2023-05-01",
  "end_date": "2023-05-31"
}
Response (202): { "id": "c1c24f48-6d75-4fd7-8f3f-e6bf6adaf9fc", "status": "queued" }
Limits: local only | Auth: none

GET /api/scans/c1c24f48-6d75-4fd7-8f3f-e6bf6adaf9fc
Response (200): {
  "status": "complete",
  "progress": { "processed": 523, "total": 523 },
  "results": [
    {
      "id": "c0a801b1-0001-4a2a-b26c-2e39b28d12ea",
      "filename": "IMG_1023.jpg",
      "captured_at": "2023-05-12T14:03:24",
      "brightness": 198.4,
      "thumbnail_url": "/api/thumbnails/.../..."
    }
  ]
}
```

### Tooling & workflows

* **Testing:** Unit tests for metadata extraction (EXIF vs fallback), brightness scoring, shortlist selection; service-level tests for ScanManager concurrency; API tests using httpx AsyncClient to assert 202 responses, polling, and final payload shape. Target ≥85% coverage on pipeline modules.
* **Quality:** Ruff (rules + formatter) enforced via `ruff check .` and `ruff format .`; mypy optional but planned as follow-up once domain stabilizes. CI pipeline runs Ruff, pytest (with coverage), and builds the project.
* **Collaboration:** Feature slices branch off `main` using `feature/<slice-name>`; PRs reference relevant slice plan and document verification in `docs/build-log.md`. Docs (`prd.md`, `tdd.md`, slice plans) updated alongside code.

### Risks & mitigations

1. **Directory access errors (permissions/symlinks):** Wrap traversal in try/except, skip unreadable entries, and surface warnings in status.
2. **Long-running scans blocking server threads:** Fixed by delegating to a ThreadPoolExecutor with bounded workers and streaming progress updates.
3. **Inconsistent EXIF parsing across devices:** Normalize EXIF timestamps via Pillow, log fallbacks, and include regression tests with synthetic EXIF payloads.
4. **Thumbnail generation overhead:** Cache thumbnails per job and use Pillow `thumbnail` with `Image.LANCZOS` to avoid repeated processing.
5. **User-supplied directory path sanitization:** Validate that the path is absolute and exists; reject network paths by default to avoid latency spikes.

### Assumptions

* Chromium-based browsers (Chrome/Edge) are the primary target; Firefox/Safari users can supply paths manually in a fallback input for MVP.
* Average library fits in memory for job metadata (<10k entries); scaling beyond this is a future slice.
* Users run the app from an account with read access to the chosen directory.
* Brightness scoring using mean luminance is an acceptable proxy for MVP despite subjective quality differences.
* Shortlist state is transient; users accept rescanning when the app restarts.

### Open questions

*None at this time.*

### Iteration readiness checklist

* MVP scope ties directly to PRD stories (directory+dates, brightness shortlist, rerun flow).
* All HTTP contracts, payloads, and error states defined for implementation.
* Domain entities, threading model, and caching strategy established with clear responsibilities.
* Tooling/tests plan supports automated validation for pipeline and API layers.
* Identified risks have mitigations and remaining decisions tracked in open questions.
