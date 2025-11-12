# Photo Archivist

Photo Archivist is a FastAPI application for scanning a local photo directory, filtering images by
capture date and brightness, and shortlisting the best shots for printing or sharing.

## Features
- 📂 **Directory scans** – point the app at any local folder and filter photos by a start/end date.
- ✨ **Smart shortlist** – analyze exposure, blur, and duplicates to surface the strongest images.
- 📨 **Print-ready exports** – select the winning shots and submit a print order via the built-in
  HTMX-powered form.

## Getting started
1. **Install dependencies** (Python 3.12+)
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. **Run the app**
   ```bash
   uvicorn app.main:app --reload
   ```
3. **Open** `http://127.0.0.1:8000` to access the UI and start a scan.

## Tests
Run the automated suite before sharing changes:
```bash
pytest
```

## Project docs
Detailed product and technical context lives in `docs/`:
- `docs/prd.md` – product requirements
- `docs/tdd.md` – technical design decisions
- `docs/build-log.md` – slice-by-slice delivery history
