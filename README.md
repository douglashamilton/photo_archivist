# Photo Archivist

Photo Archivist is a FastAPI + HTMX app that scans a local photo directory, filters images by date,
runs cheap quality gates plus perceptual dedupe, ranks the remaining shots with an aesthetic score,
and lets you send shortlisted photos to the Prodigi sandbox for printing.

## What it does
- Directory scan with date filtering and EXIF capture time fallback to file mtime.
- Cheap quality checks (brightness, contrast, blur/sharpness, resolution, aspect) to drop weak frames early.
- Perceptual-hash clustering to trim near-duplicates before scoring.
- Aesthetic scoring (Hugging Face model by default; stub fallback via env) and shortlist of the top five.
- HTMX UI with live progress, thumbnail streaming, selection toggles, and print controls.
- Prodigi (Pwinty) sandbox integration that submits 4×6" print orders for selected shortlist photos.

## Prerequisites
- Python 3.12+
- Local photo directories with JPEGs (other formats are skipped)
- For Linux/WSL, use the workspace virtual env at `.venv-wsl`; on Windows/macOS use `.venv`.

## Setup
1. Create and activate a virtual environment:
   ```bash
   # WSL/Linux
   python -m venv .venv-wsl
   source .venv-wsl/bin/activate

   # Windows/macOS
   python -m venv .venv
   source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
   ```
2. Install dependencies (include dev extras for tests/lint):
   ```bash
   pip install -e .[dev]
   ```

## Run locally
1. Set any needed environment variables (see below for options). Printing requires both:
   - `PHOTO_ARCHIVIST_PRODIGI_API_KEY` – Prodigi sandbox key.
   - `PHOTO_ARCHIVIST_ASSET_BASE_URL` – HTTPS base URL where Prodigi can fetch original files; it should serve each photo at `<base>/<scan_id>/<photo_id>/<filename>`.
2. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Open `http://127.0.0.1:8000`, choose a directory and date range, and watch the shortlist populate.

## Configuration
- `PHOTO_ARCHIVIST_AESTHETIC_BACKEND=stub` forces the lightweight scorer (skips model download/GPU).
- `PHOTO_ARCHIVIST_THUMBNAIL_DIR` overrides the temp directory used for cached thumbnails.
- Scan tuning (all optional, defaults in `app/services/config.py`):
  - `PHOTO_ARCHIVIST_SHORTLIST_LIMIT`, `PHOTO_ARCHIVIST_DISTANCE_THRESHOLD`, `PHOTO_ARCHIVIST_KEEP_PER_CLUSTER`
  - `PHOTO_ARCHIVIST_BRIGHTNESS_DROP|SOFT`, `PHOTO_ARCHIVIST_CONTRAST_DROP`,
    `PHOTO_ARCHIVIST_BLUR_DROP|SOFT`, `PHOTO_ARCHIVIST_MIN_DIMENSION`,
    `PHOTO_ARCHIVIST_MIN_ASPECT`, `PHOTO_ARCHIVIST_MAX_ASPECT`

## Tests and checks
- Run the suite: `pytest`
- Lint/format: `ruff check .` and `ruff format .`

## Project docs
See `docs/` for context:
- `docs/prd.md` – product requirements
- `docs/tdd.md` – technical design
- `docs/build-log.md` – slice-by-slice delivery history
