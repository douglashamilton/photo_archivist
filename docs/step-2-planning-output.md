### Bottom line

We’ll ship a small, desktop-friendly Python MVP using **FastAPI + HTMX (web UI)**, **MSAL** for Microsoft Graph OAuth, **httpx** for Graph/Kite calls, and a **single local SQLite** file (via SQLModel) to persist only what’s necessary: auth tokens, delta links, scores, and shortlists. It scans OneDrive **incrementally with Graph delta**, ranks photos using simple no-reference metrics and perceptual dedupe, shows a review grid, and places a **sandbox “4×6 print” order via Kite** for end-to-end validation—no shipments or charges.&#x20;

---

### Steps (max 3 bullets)

* **Auth + Sync:** Implement MSAL sign-in, obtain/refresh tokens; build **`/drive/root/delta`** scanner with robust paging/backoff and store the **deltaLink**.&#x20;
* **Score + Shortlist:** Stream bytes → OpenCV heuristics (sharpness/exposure) + pHash clustering; surface top-N with rationales.&#x20;
* **Review + Print (test):** Simple HTMX grid for approve/replace → call Kite **test mode** to create a mock order; capture provider order id.&#x20;

---

### Architecture at a glance

* **Stack:** Python 3.13, FastAPI (+ Uvicorn), Jinja2 + HTMX for SSR/partial updates, MSAL (auth), httpx (HTTP), OpenCV + Pillow + imagehash (IQA + dedupe), SQLModel (SQLite), APScheduler (cron-style runs), Pydantic v2 (schemas). Tests: pytest. Lint/format: Ruff + Black.
* **App structure:** **Hybrid (API + server-rendered UI)**. State is persisted in SQLite; UI state driven by server (HTMX swaps).
* **Data storage:** **SQLite** file `photo_archivist.db` (tokens, deltaLink, asset metadata+scores, shortlists, print orders). Chosen for zero-ops and safe concurrent reads.
* **Auth:** Microsoft OAuth (Authorization Code + PKCE) via **MSAL**, scopes: `Files.Read`, `offline_access`.&#x20;

---

### File & folder map (initial)

```
photo-archivist/
  README.md                # Setup, run, env, limitations
  .env.example             # Client ID/Secret, tenant, provider keys (test)
  pyproject.toml           # deps, tooling (ruff/black), scripts
  app/
    main.py                # FastAPI app factory, routes include
    config.py              # Settings (pydantic) + env loading
    auth/
      msal_client.py       # OAuth helpers: build app, acquire/refresh tokens
      routes.py            # /auth/login, /auth/callback, /auth/logout
    sync/
      delta_scanner.py     # Graph delta paging, retry/backoff
      graph_client.py      # httpx calls to Graph (thumbnails, metadata)
      scheduler.py         # APScheduler (cron monthly/quarterly + manual)
    scoring/
      metrics.py           # Laplacian variance, exposure/contrast
      dedupe.py            # pHash clustering + best-of-cluster logic
    shortlist/
      builder.py           # Rank, filter, persist shortlist
      routes.py            # UI actions: approve/replace, build/regenerate
    print/
      kite_client.py       # Kite test-mode API wrapper
      routes.py            # /print/test submit + status
    ui/
      pages.py             # Home, shortlist review, settings
      templates/           # Jinja templates (HTMX partials + pages)
      static/              # Minimal CSS (Tailwind via CDN) + icons
    models/
      domain.py            # SQLModel entities + Pydantic schemas
      repo.py              # CRUD helpers
    telemetry/log.py       # Structured logging (counts, timings)
  tests/
    test_acceptance.py     # Gherkin-like acceptance tests (pytest-bdd optional)
    test_scoring.py        # Unit tests for metrics/dedupe
    test_sync.py           # Delta scanner behavior & throttling
    test_print.py          # Kite client contract tests (test keys)
  scripts/
    dev_bootstrap.sh       # Create venv, install deps
    seed_demo.py           # (Optional) Seed with sample metadata for UI smoke
```

---

### Domain model

**Entities (SQLModel)**

* **User**: `id: UUID`, `tenant_id: str`, `display_name: str?`, `scopes: list[str]`, `created_at`, `updated_at`.

  * Invariant: scopes ⊇ `{Files.Read, offline_access}`.&#x20;
* **AuthToken**: `id`, `user_id FK`, `access_token(enc)`, `refresh_token(enc)`, `expires_at`.

  * Invariant: one active refresh token per user.
* **SyncState**: `id`, `user_id FK`, `delta_link: str`, `last_run_at`, `last_status`.

  * Invariant: `delta_link` updated only after successful page completion.&#x20;
* **Asset**: `item_id(str)`, `user_id FK`, `path: str`, `taken_at: datetime?`, `width:int?`, `height:int?`, `mime:str`, `phash:str?`, `last_seen: datetime`.

  * Invariant: `(user_id, item_id)` unique; images only.
* **Score**: `asset_item_id FK`, `sharpness: float`, `exposure: float`, `final_score: float`, `rationale: list[str]`, `scored_at`.

  * Invariant: 0 ≤ scores ≤ 1 normalized.
* **Shortlist**: `id`, `user_id FK`, `created_at`, `size:int`, `items: list[ShortlistItem]`, `status:{draft,finalized}`.

  * **ShortlistItem**: `asset_item_id`, `rank:int`, `selected:bool`.
* **PrintOrder**: `id`, `shortlist_id FK`, `provider:'kite'`, `mode:'test'|'live'`, `sku:'photo_4x6'`, `items:[{asset_item_id, qty:int}]`, `provider_order_id:str?`, `status:{queued,submitted,failed}`, `created_at`.&#x20;

**Relationships:** User 1–\* Assets; Asset 1–1 Score; User 1–\* Shortlists; Shortlist *–* Assets; Shortlist 1–0..1 PrintOrder.&#x20;

**Validation rules**

* Only MIME types `image/jpeg`, `image/heic`, `image/png` accepted; HEIC requires decoder availability.
* Hamming distance threshold for near-dupes: ≤ **5** (pHash).&#x20;
* Shortlist size default **20**; folders default **Photos/Camera Roll**; **no face heuristics** in MVP.&#x20;

---

### Data flow & interfaces

**Inbound**

1. **Scheduled Sync** → `scheduler.py` fires
   Handler: `delta_scanner.scan()` → calls Graph **delta** endpoint → collects new/changed items → `graph_client.fetch_photo_facet()` → upsert `Asset`, enqueue scoring.&#x20;
2. **Scoring Pipeline** → for each new/changed Asset: `metrics.compute()` (Laplacian, exposure), `dedupe.cluster()` (pHash) → persist `Score`.&#x20;
3. **Shortlist Build** → rank by `final_score`, collapse dupe clusters, cap to N, persist `Shortlist`.
4. **User Actions** → UI approve/replace toggles `ShortlistItem.selected`.
5. **Print (Test)** → `kite_client.create_order()` using test keys; record `provider_order_id`.&#x20;

**Outbound (API contracts)**

```http
POST /api/sync/run
Request: { "mode": "manual" }
Response: { "startedAt": "...", "deltaLinkSet": true }
Errors: { "error": "auth_required" | "throttled", "detail": "..." }
Auth: session cookie (local desktop)

GET /api/shortlists/latest
Response: { "id":"...", "size":20, "items":[{ "itemId":"...", "thumbUrl":"...", "finalScore":0.86, "reasons":["sharp","well-exposed","best-of-dup-cluster"] }] }
Errors: { "error":"not_found" }
Auth: session cookie

POST /api/shortlists/{id}/select
Request: { "itemId":"...", "selected":true }
Response: { "ok": true }
Errors: { "error":"invalid_item" }

POST /api/print/test
Request: { "shortlistId":"...", "sku":"photo_4x6" }
Response: { "provider":"kite", "mode":"test", "orderId":"ko_test_123", "status":"queued" }
Errors: { "error":"provider_failed", "detail":"..." }
Limits: 1 req/min (local guard)
Auth: session cookie
```

---

### Components & responsibilities

**UI (HTMX/Jinja)**

* `GET /` Home: connection status, last sync, “Run now”.
* `GET /review` Shortlist grid: thumbnails, score badges, approve/replace controls.
* `GET /settings` Folders include/exclude, schedule (**monthly/quarterly**), shortlist size.&#x20;
* Partials: `/_thumb`, `/_item_card`, `/_flash`.

**Services / utilities**

* `msal_client`: build public client app, acquire/refresh token, cache to DB.
* `graph_client`: `list_delta(page_token)`, `get_thumb(item_id)`, `get_photo_facet(item_id)`.&#x20;
* `delta_scanner`: iterate until `@odata.nextLink` exhausted; store `@odata.deltaLink`.
* `metrics`: `sharpness(img) -> float`, `exposure(img) -> float`, `final_score(weights) -> float`.
* `dedupe`: `compute_phash(img) -> str`, `cluster(assets) -> list[sets]`, pick best per set.
* `builder`: `build_shortlist(user_id, N) -> Shortlist`.
* `kite_client`: `create_order(shortlist, sku) -> {order_id,status}` (test mode).&#x20;

---

### Acceptance tests (contract)

```
Scenario: Delta sync stores and reuses deltaLink
  Given a connected OneDrive account
  When the initial scan completes
  Then a deltaLink is stored and subsequent scans fetch only changes
```

```
Scenario: Shortlist capped to N with rationales
  Given a folder containing >200 images
  When scoring completes with shortlistSize=20
  Then the latest shortlist contains <=20 items each with finalScore and reasons
```

```
Scenario: Near-duplicate collapse by pHash
  Given a burst of similar images differing by slight motion
  When dedupe runs with Hamming threshold <=5
  Then only the highest-scoring image remains in the shortlist
```

```
Scenario: Graph throttling honored
  Given Graph returns HTTP 429 with Retry-After
  When the scanner retries
  Then the operation completes without user intervention
```

```
Scenario: Print test order created
  Given an approved shortlist and Kite test keys
  When the user clicks "Print (Test)"
  Then an order is created with providerOrderId and status queued
```

```
Scenario: No originals persisted
  Given the app runs a full scan and shortlist build
  Then no original image files are written to disk and only minimal metadata/scores are stored
```

(Behavior reflects the Step-1 brief decisions: delta, dedupe, test-mode print, data minimization.)&#x20;

---

### Non-functional requirements (NFRs)

* **Performance:** First scan of \~2–4k photos ≤ **15 min**; incremental runs with <200 new photos ≪ **2 min** on laptop-class CPU. Scoring per image: tens–hundreds of ms.&#x20;
* **Reliability:** Handle paging & retries; resume with `deltaLink` after failure.&#x20;
* **Privacy:** Process images in memory; store minimal metadata/scores only; no biometric identification.&#x20;
* **Security:** Secrets in `.env`; tokens encrypted at rest (Fernet key derived from local machine/user).
* **Accessibility:** Keyboard-navigable grid; text alternatives on thumbnails.
* **i18n:** English-only MVP; no user content translated.
* **Logging/telemetry:** Local structured logs (counts, timings, item ids; exclude EXIF beyond what’s necessary).&#x20;

---

### Tooling & workflows

* **Testing:** `pytest` unit + light integration (Graph/Kite clients mocked), optional `pytest-bdd` for scenarios; **80%** line coverage target.
* **Quality:** Black (format), Ruff (lint), mypy (type checks), pre-commit hooks.
* **CI (minimal):** GitHub Actions: setup Python → install → lint → type-check → tests; upload artifact (coverage HTML).
* **Run commands (via `pyproject.toml` scripts):**

  * `uv run app`: start dev server (Uvicorn auto-reload)
  * `uv run test`: run tests
  * `uv run lint` / `format` / `typecheck`
  * `uv run schedule`: kick the scheduler loop (dev)

---

### Prompt sequencing plan for Copilot (copy-paste scripts)

1. **Scaffold & config**

   ```
   You are my Copilot. Create the repo structure exactly as per the “File & folder map”. Initialize FastAPI, Jinja2, HTMX, SQLModel (SQLite), MSAL, httpx, OpenCV, Pillow, imagehash, APScheduler, pytest, Ruff, Black, mypy. Add .env.example and README skeleton. Do not invent files outside the spec. If a conflict arises, propose a Change Request.
   ```
2. **Domain & contracts**

   ```
   Generate SQLModel entities and Pydantic schemas from “Domain model”. Implement the API routes and request/response schemas from “Data flow & interfaces”. Add centralized error handling and 429 backoff utilities. Create repository layer for CRUD.
   ```
3. **UI/CLI implementation**

   ```
   Build the pages in “Components & responsibilities” using Jinja + HTMX. Implement shortlist grid with approve/replace. Wire buttons to APIs. Add loading/empty/error partials.
   ```
4. **Acceptance tests first**

   ```
   Create pytest files that implement all “Acceptance tests”. Stub Graph/Kite with fixtures. Run tests and show failures.
   ```
5. **Make tests pass**

   ```
   Implement missing logic until all acceptance tests pass. Do not change test intent without a Change Request.
   ```
6. **Docs & packaging**

   ```
   Fill README with setup/run steps, required env vars (Graph app, tenant, Kite test keys), and limitations. Populate .env.example with placeholders and comments.
   ```

---

### Risks & mitigations

1. **Python 3.13 library compatibility (MSAL/OpenCV/SQLModel)** → Pin versions, test locally; if blockers, vendor minimal shims or drop to 3.12 in dev container as fallback.
2. **HEIC support** on some OSes → Include `pillow-heif`; detect and degrade gracefully to JPEG-only if codec missing.
3. **Graph throttling/large libraries** → Strict paging + `Retry-After` backoff; nightly long-run tests on sample data.&#x20;
4. **Kite API changes** → Wrap in thin client with contract tests; keep provider abstraction for swap-out.&#x20;
5. **User trust in scoring** → Show reasons + side-by-side compares; easy override (replace/approve).&#x20;

---

### Open questions

1. **OS targets** (Win/macOS/Linux) and packaging (zip vs. installer) — propose `uv` + README for POC; decide installer later (owner: us; test: local).
2. **Local encryption key derivation** (machine vs. passphrase) — pick simple passphrase in `.env` for MVP; document risk.
3. **Max shortlist N and schedule defaults** — currently N=20, **monthly/quarterly**; confirm monthly default for MVP (owner: us).&#x20;
4. **BRISQUE tie-break** — include behind flag or defer to v2 (owner: us).&#x20;

---

### Iteration plan

* **v1 (this MVP):** OneDrive delta sync, scoring + dedupe, shortlist review, **Kite test order** for 4×6 prints.&#x20;
* **Validate next:** Reliability of delta sync, user trust in ranking, “approve/replace” ergonomics, Kite contract stability.
* **v2 (minimal changes):** Optional BRISQUE tie-break, face **detection** (not identification) quality hint, multi-SKU support (5×7), export shortlist JSON, provider abstraction finalized.&#x20;

---

### Assumptions

* OneDrive is the only source; delegated **read-only** (`Files.Read`, `offline_access`) consent is acceptable.
* **No face heuristics** in MVP; quality = sharp + well-exposed; dedupe via pHash.
* **Data minimization:** process in memory; store only derived scores, IDs, and minimal EXIF; no originals saved.
* Print provider uses **Kite test mode**; UK-ready; “photos\_4x6” is the sole SKU in MVP.&#x20;

---

**Notes:** This plan intentionally mirrors the Step-1 Research Brief decisions—**Graph delta**, **pHash**, **sandbox printing**, **monthly/quarterly schedule**, **Camera Roll default**, and **no face heuristics**—to keep scope tight and shippable for a POC.&#x20;
