# AI Assistant Instructions (Router)

## Canonical artifacts (single source of truth)
- **Step-1 Research Brief:** ./docs/step-1-research-output.md
- **Build Spec (this plan):** ./docs/step-2-planning-output.md
- **Non-goals / Constraints:** see Build Spec → “Assumptions” & “Non-goals”

> If anything in code or this file conflicts with the Build Spec, **treat the Build Spec as authoritative**. Propose a **Change Request** in PR before deviating.

## Change control (for Copilot + contributors)
1. **Do not invent files/dirs/APIs** not listed in Build Spec’s “File & folder map” or “Data flow & interfaces”.
2. If a change is necessary, add a “Change Request” section to the PR describing: rationale, impacted modules, and updated acceptance tests.
3. Keep this file aligned whenever you touch architecture, env vars, or routes.

## Env var contract (canonical names)
- `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET?`, `MS_SCOPES`, `MS_REDIRECT_URI`
- `ENCRYPTION_KEY`
- `KITE_API_KEY`, `KITE_MODE`, `KITE_SKU`
- `DATABASE_URL` **or** local default (`sqlite:///photo_archivist.db`)

> Back-compat mapping allowed: accept `AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` but **normalize** to `MS_*` at startup and warn once.

## Architecture pins
- **Stack:** Python 3.13, FastAPI, HTMX+Jinja, httpx, SQLModel (SQLite), MSAL, OpenCV+Pillow+imagehash, APScheduler, pytest, Ruff, Black, mypy.
- **Async policy:** External I/O (`httpx`, DB) may be async; keep route handlers consistent (don’t mix sync/async in one module).
- **Storage:** No originals on disk; store only metadata, scores, shortlist, and provider order ids.
- **Scopes:** `Files.Read`, `offline_access`. No face identification in MVP.

## Directory contract (must match Build Spec)
- `app/auth/`, `app/sync/`, `app/scoring/`, `app/shortlist/`, `app/print/`, `app/ui/`, `app/models/`, `app/telemetry/`
- Each `routes.py` exposes `router = APIRouter()` and is included by `app/main.py`.

## API contracts (authoritative in Build Spec)
Implement exactly as defined under “Data flow & interfaces”. If edits are needed, submit Change Request + test updates.

## Acceptance tests = Definition of Done
Mirror Build Spec → “Acceptance tests”. Add/modify tests only with a Change Request.
