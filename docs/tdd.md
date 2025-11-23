## Photo Archivist Technical Design

### Bottom line

Photo Archivist MVP ships as a local FastAPI (Python 3.12) web app using Jinja + HTMX for a lightweight UI that lets the user choose a directory, filter images by date, run an extensible Pillow-backed scan pipeline in the background (cheap quality gates + perceptual dedupe + aesthetic scoring), render the five highest-scoring thumbnails with file metadata, and submit selected photos as 4×6" print orders to the Prodigi (Pwinty) sandbox.

### Architecture Overview

* **Stack:** Python 3.12, FastAPI 0.115, Uvicorn for dev server, Jinja2 templates with HTMX for partial updates, Pydantic models, Pillow 11 for image I/O, OpenCV-headless for Laplacian blur checks, imagehash for perceptual hashing, transformers + torch for the aesthetic model (with a stub fallback for offline/dev), httpx for outbound Prodigi calls, pytest + httpx for tests, Ruff (lint + format), and pre-commit to wire everything together.
* **App structure:** Server-rendered views served by FastAPI; HTMX drives form submissions and result refreshes, while domain logic lives in a `services` module (scan orchestration, metadata extraction, scoring, print ordering). The scanner is composed as a pipeline of strategies (file discovery, metadata resolver, scoring engine, selector) so future heuristics plug in without rewriting traversal. Application state (scan jobs) is kept in an in-memory registry owned by a `ScanManager`.
* **Data storage:** No persistent store; scan results are cached per job in memory until replaced. Thumbnail binaries are generated on demand and memoized in a temp directory for the session (cleaned on shutdown). Print order payloads and their Prodigi responses are tracked in memory long enough to surface confirmation.
* **Auth:** None; app runs locally and trusts the invoking user. Prodigi credentials (API key) are injected via environment variable (`PHOTO_ARCHIVIST_PRODIGI_API_KEY`) and never echoed back into the UI.
* **Deployment & environments:** Local dev via `uvicorn app.main:app --reload`; CI runs pytest and Ruff. Distribution via `pip install -e .` or packaged executable (future slice). Requires outbound HTTPS access to the Prodigi sandbox (`https://api.prodigi.com/v4.0/`).

### Tech Stack Decisions

* **Language/runtime:** Python 3.12 aligns with PRD requirement and provides `pathlib`/typing improvements.
* **Web framework:** FastAPI gives async routing, background tasks, and automatic validation via Pydantic for request payloads.
* **Templating/UI:** Jinja2 keeps rendering simple; HTMX enables partial HTML responses for progress/status without a SPA build step.
* **Image processing:** Pillow 11 handles JPEG EXIF parsing, resizing, and luminance scoring (`ImageStat.mean`). OpenCV Laplacian variance surfaces blur/sharpness, and a QualityGate drops/flags dark, low-contrast, blurry, low-res, or extreme-aspect images before heavier work. The scoring layer exposes a strategy interface to keep adding signals without disrupting traversal.
* **File system:** `pathlib` + `os.scandir` for performant recursive traversal and filtering; `piexif` is optional but not required because Pillow covers the needed EXIF tags.
* **Background execution:** FastAPI `BackgroundTasks` plus an internal thread pool (via `concurrent.futures.ThreadPoolExecutor`) isolate long-running scans while keeping the main loop responsive.
* **Validation & schema:** Pydantic models encapsulate `ScanRequest`, `ScanStatus`, `PhotoResult`, and print order DTOs with input validation.
* **Print integration:** httpx (async client) handles signed requests to Prodigi; payload construction is isolated so we can unit test against fixtures and mock responses.
* **Testing:** pytest with tmp-path fixtures for synthetic photo trees and httpx AsyncClient for endpoint tests. Coverage tracked via `pytest --cov`.
* **Quality tooling:** Ruff configured to enforce linting and formatting (Black-compatible mode) in a single tool; `pre-commit` runs Ruff (lint + format), pytest -q, and ensures `docs/tdd.md`/`docs/prd.md` stay tracked.

### Interfaces

* **UI entrypoint:** `GET /` renders the form (directory picker + date fields) and initial shortlist when available.
* **Start scan:** `POST /api/scans` (JSON) → `{ "id": "<uuid>", "status": "queued" }`. Validates directory exists and dates are logical. On success, enqueues the job and starts background scan.
* **Poll status/results:** `GET /api/scans/{scan_id}` → `{ "status": "running|complete|error", "progress": { "processed": int, "total": int }, "results": [PhotoResult] }`. Returns HTTP 404 if the job id is unknown or expired.
* **Render shortlist fragment:** `GET /fragments/shortlist/{scan_id}` returns HTML partial (HTMX target) for the current shortlist state, including spinner/progress text while running.
* **Thumbnail streaming:** `GET /api/thumbnails/{scan_id}/{photo_id}` streams the generated JPEG thumbnail (`Content-Type: image/jpeg`); raises 404 if cache missing.
* **Submit print order:** `POST /api/prints` accepts `{ scanId, photoIds, recipient, shippingMethod, copies }`, validates selection and credentials, kicks off order submission, and returns `{ "orderId": "...", "status": "submitted" }` with any warnings.
* **Track print order:** `GET /api/prints/{orderId}` proxies the last-known Prodigi status (cached locally) and updates it if sufficient polling interval has elapsed.
* **Error handling:** API returns JSON with `{ "detail": "..." }` and 4xx/5xx codes; HTML routes fall back to a friendly error template with actionable copy.

### Domain model

* **ScanRequest:** `{ id: UUID, directory: Path, start_date: date, end_date: date, requested_at: datetime }`.
* **ScanStatus:** `{ id: UUID, state: Enum[queued,running,complete,error], processed: int, total: int, matched: int, updated_at: datetime, message: str|None }`.
* **PhotoMetadata:** `{ path: Path, filename: str, captured_at: datetime, modified_at: datetime, used_fallback: bool }`.
* **PhotoResult:** `{ id: UUID, metadata: PhotoMetadata, brightness: float, metrics: Dict[str, float], quality_status: Literal["keep","soft"], quality_notes: list[str], cluster_id: str|None, cluster_rank: int|None, cluster_size: int|None, thumbnail_path: Path, generated_at: datetime, selected: bool }`.
* **PrintAsset:** `{ id: UUID, photo_id: UUID, source_path: Path, public_url: HttpUrl, uploaded_at: datetime, expires_at: datetime }`.
* **PrintOrderRequest:** `{ scan_id: UUID, photo_ids: List[UUID], recipient: Recipient, shipping_method: str, copies: int }`.
* **PrintOrderStatus:** `{ id: str, state: Enum[submitted,failed,complete], submitted_at: datetime, updated_at: datetime, prodigi_reference: str, failure_reason: str|None }`.
* **ScanManager:** orchestrates job lifecycle, holds an in-memory `Dict[UUID, ScanStatus]` and `Dict[UUID, List[PhotoResult]]`, exposes thread-safe read/write, limits retained completed jobs (default 5) so history doesn’t grow unbounded, and exposes a shutdown hook that drains executors plus thumbnail caches.
* **PrintOrderService:** coordinates asset publication, builds Prodigi payloads, handles HTTP requests, caches order status, and exposes polling helpers.

### Scan pipeline composition

* **FileEnumerator:** wraps `Path.rglob` with allowlisted extensions and emits total counts early so progress updates stay responsive even before scoring runs.
* **MetadataResolver:** centralises EXIF parsing + filesystem fallbacks and will host future enrichment (faces, GPS) without touching traversal logic.
* **QualityGate:** computes quick metrics (brightness, contrast, Laplacian variance, resolution, aspect ratio) and drops or flags dark, low-contrast, blurry, tiny, or extreme-aspect frames before heavier work. Metrics flow through for debugging and stub scoring.
* **PerceptualHasher + PhashClusterer:** compute perceptual hashes and cluster candidates by Hamming distance (≤5), keeping the best two per burst using sharpness/brightness as a pre-aesthetic tie-break.
* **AestheticScoringEngine:** lazily loads a Hugging Face aesthetic head (default LAION/AVA) with in-memory caching keyed by file hash; falls back to a cheap heuristic stub when disabled or unavailable.
* **Selector:** consumes `PhotoScore` objects, favors higher aesthetic scores with sharpness/quality status as tie-breakers, and truncates to the shortlist target, ensuring UI/API ordering is stable regardless of metric additions.

`run_scan` wires these strategies together but each component remains swappable for tests or future slices that add ML heuristics.

### Data flow & interfaces

* **Inbound scans:** Browser form submission (HTMX POST) -> FastAPI controller (/api/scans) -> ScanManager enqueues job -> background worker walks directory -> metadata extractor -> quality gate -> perceptual hash clustering -> aesthetic scoring -> shortlist reducer (top five) -> cache results.
* **Processing pipeline:** For each JPEG, the enumerator streams files to the metadata resolver (EXIF -> fallback). Skip files outside range, then apply the QualityGate; drop or flag low-quality frames, cluster near-duplicates via perceptual hashes, keep at most two per burst, and only then invoke the aesthetic scorer (cached per file hash). Maintain a selector/min-heap that always exposes the top five aggregate scores without holding the entire corpus.
* **Outbound shortlist:** When job completes, API response and HTML fragment include five results sorted by aesthetic score descending (sharpness tie-break), with filename, capture date, cheap metrics (brightness/contrast/sharpness/resolution/aspect), cluster info, aesthetic score, thumbnail URL, and selection state. HTMX swaps the shortlist section in place.
* **Print flow:** POST /api/prints validates the referenced scan and selection, ensures each photo has an accessible temporary HTTPS URL (via an AssetPublisher abstraction that can upload or share the original file), composes a Prodigi order payload with GLOBAL-PRINT-4X6 SKU (or configured variant), and submits it with httpx using the sandbox base URL. Responses cache the Prodigi orderId. A background poller (or lazy on-demand polling) hydrates PrintOrderStatus via GET /v4.0/orders/{id} until the order is acknowledged or fails, surfacing status to the UI.

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
      "selected": false,
      "thumbnail_url": "/api/thumbnails/.../..."
    }
  ]
}

POST /api/prints
Request: {
  "scanId": "c1c24f48-6d75-4fd7-8f3f-e6bf6adaf9fc",
  "photoIds": ["c0a801b1-0001-4a2a-b26c-2e39b28d12ea"],
  "recipient": { "name": "Ada Lovelace", "email": "ada@example.com", "address": { ... } },
  "shippingMethod": "STANDARD",
  "copies": 1
}
Response (202): { "orderId": "PO-123456", "status": "submitted" }
```

### Tooling & workflows

* **Testing:** Unit tests for metadata extraction (EXIF vs fallback), brightness scoring, shortlist selection, and Prodigi payload construction (mocking httpx); service-level tests for ScanManager concurrency and PrintOrderService retries; API tests using httpx AsyncClient to assert scan flows plus print submissions/polling. Target >=85% coverage on pipeline modules, and always install dev dependencies via `pip install -e .[dev]` so `pytest-asyncio` is present (pytest will otherwise refuse to run async tests).
* **Quality:** Ruff (rules + formatter) enforced via `ruff check .` and `ruff format .`; mypy optional but planned as follow-up once domain stabilizes. CI pipeline runs Ruff, pytest (with coverage), and builds the project.
* **Collaboration:** Feature slices branch off `main` using `feature/<slice-name>`; PRs reference relevant slice plan and document verification in `docs/build-log.md`. Docs (`prd.md`, `tdd.md`, slice plans) updated alongside code.

### Risks & mitigations

1. **Directory access errors (permissions/symlinks):** Wrap traversal in try/except, skip unreadable entries, and surface warnings in status.
2. **Long-running scans blocking server threads:** Fixed by delegating to a ThreadPoolExecutor with bounded workers and streaming progress updates.
3. **Inconsistent EXIF parsing across devices:** Normalize EXIF timestamps via Pillow, log fallbacks, and include regression tests with synthetic EXIF payloads.
4. **Thumbnail generation overhead:** Cache thumbnails per job and use Pillow `thumbnail` with `Image.LANCZOS` to avoid repeated processing.
5. **User-supplied directory path sanitization:** Validate that the path is absolute and exists; reject network paths by default to avoid latency spikes.
6. **Prodigi API downtime or credential issues:** Wrap outbound calls with retries/backoff, capture detailed error messages, and surface actionable guidance so users can retry once connectivity is restored.
7. **Temporary asset URL exposure:** Expire/upload assets promptly after order submission and avoid logging sensitive URLs; ensure publisher implementations generate HTTPS links with short TTLs.

### Assumptions

* Chromium-based browsers (Chrome/Edge) are the primary target; Firefox/Safari users can supply paths manually in a fallback input for MVP.
* Average library fits in memory for job metadata (<10k entries); scaling beyond this is a future slice.
* Users run the app from an account with read access to the chosen directory.
* Brightness-based scoring remains the first heuristic, but the pipeline is expected to fold in richer quality signals as soon as they are validated.
* Shortlist state is transient; users accept rescanning when the app restarts.
* Users will configure a Prodigi API key (sandbox for dev) via `PHOTO_ARCHIVIST_PRODIGI_API_KEY` (or a secrets manager) and payment method outside the app before ordering prints.
* The app can publish temporary HTTPS asset URLs for selected photos without manual intervention (e.g., via configurable storage).

### Open questions

*None at this time.*

### Iteration readiness checklist

* MVP scope ties directly to PRD stories (directory+dates, brightness shortlist, rerun flow, and fire-and-forget print ordering).
* All HTTP contracts, payloads, and error states defined for implementation.
* Domain entities, threading model, and caching strategy established with clear responsibilities.
* Tooling/tests plan supports automated validation for scan, selection, asset publishing, and print-order API layers.
* Identified risks have mitigations and remaining decisions tracked in open questions.
