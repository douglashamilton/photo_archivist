### Slice Build Plan — Photo Archivist

0. **Plan Overview**

* **Objective recap:** Connect to OneDrive Camera Roll, shortlist the top 10 photos monthly, and submit them to a print API for 6×4″ sandbox prints. 
* **Stack confirmation:** Python 3.12, FastAPI, SQLite (SQLAlchemy), APScheduler, MSAL, OpenCV/Pillow/ImageHash, Requests; pytest/pytest-asyncio; ruff/black/mypy; pre-commit. 
* **Current repo state:** new repo (`main` empty)
* **Active slice:** **Slice 0 — Repo scaffolding & /health contract**
* **Prerequisites:** None (pure local scaffolding; no external secrets required)

---

1. **Global Guardrails (from TDD)**

* **Scope fence (what Copilot may modify now):**
  `/src/photo_archivist/{app.py,schemas.py,config.py}`, `/tests/test_api_contracts.py`, `pyproject.toml`, `.pre-commit-config.yaml`, `README.md`, `scripts/dev_run.sh`, `.env.example`, `ruff/mypy/pytest` config blocks. Keep any “future” folders stubbed but empty (no Graph/Prodigi code yet). 
* **Quality gates:** ruff + black clean; mypy (strict for `src/`); pytest green; CI ready to run lint/type/tests. Target ≥85% coverage on service/API layers overall (future), but this slice must include at least one failing test first, then green. 
* **Security & privacy:** No secrets in repo; `.env.example` only. No image persistence; no tokens yet. Prepare redaction logger (PII-safe) but keep it minimal for this slice.
* **Observability:** Add `/health` endpoint returning `{ok, version}`; structured JSON logs; include a startup log “boot” event. Keep logs free of EXIF/tokens. 
* **Config & tooling:** `BaseSettings` for app config (port, env name, version), `pre-commit` for ruff/black/mypy, `uvicorn` dev script. 

---

2. **Slice Focus**

* **Slice ID:** 0
* **Slice name:** Repo scaffolding & health contract
* **Why this slice now:** Establishes a tested, linted, typed FastAPI base with a single API surface (`/health`) to anchor later vertical slices (auth, delta scan, shortlist, order). Keeps us firmly tests-first and CI-ready. 
* **Dependencies:** None

---

3. **Slice Execution Plans**

#### Slice 0 — Repo scaffolding & health contract

* **Goal:** Have a runnable FastAPI app with `/health` returning `{ "ok": true, "version": "<semver>" }`, toolchain wired (ruff/black/mypy/pytest), and a passing contract test.
* **Definition of done:**

  * `pytest -q` passes with the new API contract test(s).
  * `ruff`, `black --check`, and `mypy` all pass on `src/`.
  * `uvicorn src.photo_archivist.app:app` serves `/health` on `http://localhost:8787/`.
  * README shows quick start and test commands.
* **Preconditions:** None (no DB, no Graph/Prodigi calls in this slice).
* **Touch-only files:**

  * `pyproject.toml` (deps + tool configs)
  * `.pre-commit-config.yaml`
  * `.env.example`
  * `src/photo_archivist/app.py`
  * `src/photo_archivist/config.py`
  * `src/photo_archivist/schemas.py`
  * `tests/test_api_contracts.py`
  * `scripts/dev_run.sh`
  * `README.md`
* **First failing test(s):**

  * **File:** `tests/test_api_contracts.py`
  * **Test name:** `test_health_returns_ok_and_version`
  * **Failure setup:**

    * Arrange: spin up FastAPI test client against `photo_archivist.app:app`.
    * Act: `GET /health`.
    * Assert (fails initially): status 200; JSON has keys `ok==True` and `version` matching `r"^\d+\.\d+\.\d+$"`.
    * Bonus assert: `content-type` is `application/json` and response includes `"service":"photo-archivist"`.
* **Copilot prompt script (ordered, concise):**

  1. **Create toolchain & deps**
     “Create `pyproject.toml` for a Python 3.12 project named `photo-archivist`. Add runtime deps: fastapi, uvicorn[standard], pydantic, pydantic-settings, python-dotenv. Add dev deps: pytest, pytest-asyncio, httpx, ruff, black, mypy, types-requests. Configure ruff, black, mypy (strict for `src/`).”
  2. **Add pre-commit hooks**
     “Generate `.pre-commit-config.yaml` to run ruff (fix), black, and mypy on changed files. Update README with install + `pre-commit install`.”
  3. **Author the failing test**
     “Create `tests/test_api_contracts.py` with a `FastAPI` TestClient test `test_health_returns_ok_and_version` as described. Import app from `src.photo_archivist.app`.”
  4. **Implement FastAPI app skeleton**
     “Create `src/photo_archivist/app.py` exposing `app = FastAPI(title='Photo Archivist')`. Add `/health` route returning `{ok:true, version:Settings.VERSION, service:'photo-archivist'}` and log a startup event. Use `Settings` from `config.py`.”
  5. **Settings module**
     “Create `src/photo_archivist/config.py` using `pydantic_settings.BaseSettings`. Fields: `APP_NAME='photo-archivist'`, `VERSION='0.1.0'`, `PORT=8787`, `ENV='dev'`. Load from `.env`. Export a singleton `settings`.”
  6. **Schemas (future-friendly)**
     “Create `src/photo_archivist/schemas.py` with a `HealthResponse` model: `{ok: bool, version: str, service: str}`; use it in the `/health` route for response_model.”
  7. **Dev script**
     “Add `scripts/dev_run.sh` to run: `uvicorn src.photo_archivist.app:app --host 127.0.0.1 --port 8787 --reload`.”
  8. **README quick start**
     “Document setup: create venv, `pip install -e .[dev]`, `pre-commit install`, run tests, run server, and curl `/health`.”
* **Implementation checkpoints:**

  * **Checkpoint A:** `pytest -q` shows 1 failing test (no app yet).
  * **Checkpoint B:** After `app.py` + `config.py` + `schemas.py`, test passes locally.
  * **Checkpoint C:** `ruff`, `black --check`, `mypy` all pass.
  * **Checkpoint D:** `./scripts/dev_run.sh` boots; `GET /health` returns JSON with version `0.1.0`.
* **Verification:**

  * **Commands:**

    * `pre-commit run --all-files`
    * `pytest -q`
    * `mypy src/`
    * `uvicorn src.photo_archivist.app:app --port 8787` then `curl localhost:8787/health`
  * **Manual QA:** Open `http://localhost:8787/health` in browser; confirm JSON shape/values. Change `VERSION` in `.env` (e.g., `VERSION=0.1.1`) → restart → confirm response updates.
  * **Telemetry/logging:** On startup, emit log `{event:"boot", service:"photo-archivist", version:"0.1.0", env:"dev"}`; on `/health`, emit `{event:"health.check"}` at debug level. (Ensure no PII, tokens, or URLs in logs.)
* **Follow-ups / debts:**

  * Add GitHub Actions CI (ruff/black/mypy/pytest matrix for 3.12).
  * Pin tool versions; add `coverage` config and badge.
  * ADR-0001: “Local FastAPI with single `/health` surface as contract base”.

---

4. **After-shipment actions**

* **Documentation to update:** `README.md` (setup/run/test), `CHANGELOG.md` (v0.1.0), add `CONTRIBUTING.md` with tests-first workflow note.
* **Deployment / release steps:** Tag `v0.1.0` after green; publish wheels optional (local app).
* **Next review trigger:** Re-run this SBP prompt **before starting Slice 1**.

---

## Next slices (for context only — not part of this build)

* **Slice 1 — DB & models bootstrap:** SQLite engine + `Run`/`PhotoItem` skeleton, migrations optional.
* **Slice 2 — Auth shell:** MSAL stub + `/api/auth/connect` contract (mocked).
* **Slice 3 — Scan service contract:** `/api/run/scan` (Graph mocked), scoring/dedup stubs.
* **Slice 4 — Shortlist API + static gallery:** `/api/shortlist`, basic HTML.
* **Slice 5 — Order contract:** `/api/order` with Prodigi mocked.

(These map directly to the PRD/TDD epic flow of connect → scan → shortlist → review → order. )

---

### Guardrails

* Stay aligned with the TDD; any new files beyond the **Touch-only files** list require a **Design Change Request** back to Step 2, not silent scope creep. 
* Copilot writes the code; you provide the exact prompt script above.
* Keep prompts short, sequential, and anchored to this single cohesive surface (`/health`).
* If the slice feels too big, split again—prefer the smallest viable end-to-end increment.
