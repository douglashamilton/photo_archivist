# Slice 5: Submit print order requests

## Context
- PRD section / link: docs/prd.md (User Story: "Given a shortlist ... when I select one or more photos and choose to print them...")
- TDD component / link: docs/tdd.md (Interfaces: POST /api/prints; Domain model: PrintOrderRequest/PrintOrderService)
- Current state summary (1-2 sentences). The shortlist supports selection toggles, but there is no way to submit the chosen photos for printing or collect the recipient details required by Prodigi.

## Tasks
- [x] Extend domain models/config to capture print recipient details, API credentials, and selected photos for order submission.
- [x] Implement a PrintOrderService that validates selections, maps photos to publishable URLs, builds the Prodigi payload, and (for now) fakes the API call while returning an order reference.
- [x] Add `/api/prints` FastAPI endpoint plus UI controls to gather recipient info and kick off print submission when shortlist selections exist.
- [x] Cover the new service and endpoint with automated tests (mocking the Prodigi call) and ensure existing suites still pass.
- [x] Normalize HTML responses for the print form so HTMX swaps the error/success fragment even when Prodigi rejects the order (fixing “blank UI” regressions).
- [x] Trim and validate the Prodigi API key input, and assert outgoing requests include the Prodigi-required `X-API-Key` header to avoid sandbox `NotAuthenticated` errors caused by whitespace.
- [x] Add a stdlib HTTPS fallback so the app can still submit orders if the environment’s `httpx/httpcore` stack fails to initialize (e.g., the Windows `IntEnum` import bug).

## Tests & Validation
- Automated: `.venv\Scripts\python.exe -m pytest` (covers scanner/endpoint flows, HTMX fragment handling, and Prodigi header assertions).
- Manual check: Run `uvicorn app.main:app --reload`, perform a scan with selectable photos, mark at least one as selected, fill the print form (including a valid sandbox API key without extra spaces), submit, and confirm either a success banner with an order reference or an inline error panel with Prodigi’s message—no blank UI or console-only errors.

## Decisions & Follow-ups
- Keep asset publishing as a simple environment-driven URL join for now; follow up with real upload/expiry handling before shipping the final MVP.
- Shipping method and copies default to `STANDARD` and `1` in the UI; revisit configurability once the core flow works end-to-end.
- Secrets (API keys) never echo back into the HTML form; if future observability is required, add redacted logging instead of rendering keys for the user.
- Consider reusing the HTMX-friendly response helper across other form endpoints if validation errors need similar treatment.
- Provide better diagnostics/metrics before swapping to fully async `httpx` once upstream fixes the Windows/py3.13 import issue; the fallback keeps print submission unblocked meanwhile.
