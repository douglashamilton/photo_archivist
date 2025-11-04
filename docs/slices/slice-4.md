# Slice 4: Toggle shortlist selections

## Context
- PRD section / link: docs/prd.md (User Stories: shortlist review and rerun flow)
- TDD component / link: docs/tdd.md (Domain model: PhotoResult; UI entrypoint shortlist fragment)
- Current state summary (1-2 sentences). The shortlist renders the five brightest photos with thumbnails, but the user cannot mark which ones they want to keep; no selection state exists in the domain or UI.

## Tasks
- [ ] Extend shortlist domain models and ScanManager storage to track per-photo selection state.
- [ ] Add a FastAPI endpoint that toggles selection for a shortlist photo and returns the refreshed shortlist partial or JSON payload.
- [ ] Update the shortlist template/UI to expose select/deselect controls with visible state feedback.
- [ ] Cover selection toggling with automated tests (HTML fragment + JSON) and adjust serializers as needed.

## Tests & Validation
- Automated: `.venv\Scripts\python -m pytest`
- Manual check: Run `uvicorn app.main:app --reload`, submit a scan with at least two photos, toggle selection state for multiple items, and confirm the UI reflects select/deselect actions without rerunning the scan.

## Decisions & Follow-ups
- Confirm whether selection state should persist beyond the active session in a future slice (out of scope now).
- Consider surfacing a "clear selections" action later if user research demands it.
