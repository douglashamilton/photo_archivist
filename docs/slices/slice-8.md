# Slice 8: Secure credentials & background cleanup

## Context
- PRD section / link: docs/prd.md (Must-Have print submission & Non-functional requirements).
- TDD component / link: docs/tdd.md (Architecture > Print integration, Background execution, and Testing sections).
- Current state summary (1–2 sentences). The print form still exposes the Prodigi API key field, contributors hit pytest errors unless they manually install the optional async extra, and completed scans leave thread pools, in-memory registries, and thumbnail folders behind indefinitely.

## Tasks
- [x] Remove the Prodigi API key input/field from the UI and request model, sourcing credentials solely from `PHOTO_ARCHIVIST_PRODIGI_API_KEY` (or equivalent secret storage) and updating docs/tests accordingly.
- [x] Call out the async test dependency so new contributors know to install the `[dev]` extra (or provide pytest-asyncio) before running the suite.
- [x] Add executor/registry/thumbnail cleanup: expose a `ScanManager` shutdown + history pruning hook, wire it into FastAPI shutdown, and ensure completed scans release disk and memory.

## Tests & Validation
- Automated: `pytest`.
- Manual check: Run `uvicorn app.main:app --reload`, set `PHOTO_ARCHIVIST_PRODIGI_API_KEY`, submit a print order without entering a key in the UI, and then stop the server to confirm it shuts down cleanly without lingering thumbnail folders for old scans.

## Decisions & Follow-ups
- Documented the `[dev]` extra requirement rather than inflating the default install footprint; revisit later if tests need to run in production builds.
- History pruning keeps only the newest handful of completed scans in memory; capture telemetry later if stakeholders want configurable retention.
