# Slice 7: Prodigi exchange debugging

## Context
- PRD section / link: docs/prd.md (Print order submission diagnostics).
- TDD component / link: docs/tdd.md (Print flow / POST /api/prints error handling).
- Current state summary (1–2 sentences). Users see only a terse “Prodigi reported 'NotAuthenticated'” banner when submissions fail, so it’s impossible to inspect the payload or response details needed to debug why the sandbox rejected a request.

## Tasks
- [x] Plumb sanitized Prodigi request/response metadata through `PrintOrderService` so callers can access it when `ProdigiAPIError` raises.
- [x] Surface the debug payload via the `/api/prints` JSON response and the print controls HTMX fragment (e.g., a `<details>` block) so operators can inspect what was sent and received.
- [x] Cover the new debug contract with API and template tests, and run `pytest`.

## Tests & Validation
- Automated: `pytest`.
- Manual check: Trigger a failing print submission (e.g., missing API key), open the print form banner, and expand the debug details to review the Prodigi payload and response data. Confirm JSON clients receive the same debug structure.

## Decisions & Follow-ups
- Consider persisting only the last few exchanges or redacting photo URLs if stakeholders deem them sensitive in logs.
- Prodigi sandbox expects the header name `X-API-Key` (not `X-Prodigi-Api-Key`); updated service/tests accordingly so the documented debug info matches what Prodigi recognizes.
