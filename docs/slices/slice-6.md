# Slice 6: Stabilize print refresh JS

## Context
- PRD section / link: docs/prd.md (Print order submission story)
- TDD component / link: docs/tdd.md (Print flow / POST /api/prints)
- Current state summary (1–2 sentences). The print controls fragment injects an `hx-vals` expression that relies on `this.dataset.scanId`; when HTMX evaluates it for validation and confirm hooks, `this` is undefined, so the print form crashes before the POST runs.

## Tasks
- [x] Guard the `hx-vals` scan id lookup so HTMX can always resolve the value (event detail or DOM query) without throwing.
- [x] Add regression coverage to ensure the rendered fragment keeps the new JS fallback and exposes the scan id for refresh requests.
- [x] Run `pytest` and capture a manual verification note covering the browser submission flow.

## Tests & Validation
- Automated: `pytest`.
- Manual check: Start `uvicorn app.main:app --reload`, run a scan, select at least one photo, open the browser console, submit the print form, and verify the fragment refresh completes without console errors.

## Decisions & Follow-ups
- Consider replacing inline JS with a server-provided query parameter or hidden field if future HTMX events need additional context.
