# Slice 1: Synchronous scan pipeline and shortlist

## Context
- PRD section / link: docs/prd.md (Must-Have Features: filter images by date, brightness scoring, shortlist of top five)
- TDD component / link: docs/tdd.md (Data flow & interfaces: `/api/scans`, processing pipeline, shortlist reducer)
- Current state summary (1-2 sentences). Landing page form renders but no backend endpoint or scan logic exists to process requests.

## Tasks
- [x] Add domain models and scanning service to filter JPEGs by date with EXIF fallback to file modified time and compute brightness scores.
- [x] Implement `POST /api/scans` FastAPI endpoint that processes the form synchronously and returns an HTML partial for the shortlist.
- [x] Create shortlist template partial, integrate HTMX response flow, and add tests covering scanner behaviour and the endpoint response.

## Tests & Validation
- Automated: `pytest`
- Manual check: Run `uvicorn app.main:app --reload`, point the form at a directory with sample JPEGs, submit with a date range, and confirm the shortlist updates with up to five results sorted by brightness.

## Decisions & Follow-ups
- Run scans synchronously for now; move work to background execution plus progress updates in later slices.
