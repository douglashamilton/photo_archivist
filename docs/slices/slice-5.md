# Slice 5: Submit print order requests

## Context
- PRD section / link: docs/prd.md (User Story: "Given a shortlist ... when I select one or more photos and choose to print them...")
- TDD component / link: docs/tdd.md (Interfaces: POST /api/prints; Domain model: PrintOrderRequest/PrintOrderService)
- Current state summary (1-2 sentences). The shortlist supports selection toggles, but there is no way to submit the chosen photos for printing or collect the recipient details required by Prodigi.

## Tasks
- [ ] Extend domain models/config to capture print recipient details, API credentials, and selected photos for order submission.
- [ ] Implement a PrintOrderService that validates selections, maps photos to publishable URLs, builds the Prodigi payload, and (for now) fakes the API call while returning an order reference.
- [ ] Add `/api/prints` FastAPI endpoint plus UI controls to gather recipient info and kick off print submission when shortlist selections exist.
- [ ] Cover the new service and endpoint with automated tests (mocking the Prodigi call) and ensure existing suites still pass.

## Tests & Validation
- Automated: `.venv\Scripts\python.exe -m pytest`
- Manual check: Run `uvicorn app.main:app --reload`, perform a scan with selectable photos, mark at least one as selected, fill the print form (name + email), submit, and confirm a success message returns an order reference.

## Decisions & Follow-ups
- Keep asset publishing as a simple environment-driven URL join for now; follow up with real upload/expiry handling before shipping the final MVP.
- Shipping method and copies default to `STANDARD` and `1` in the UI; revisit configurability once the core flow works end-to-end.
