### Bottom line

Ship a **local desktop MVP** called **Photo Archivist** that (1) connects to the user’s **OneDrive** via Microsoft Graph (read-only, OAuth), (2) runs a **monthly** scan of recent **JPG** photos using **delta sync**, (3) scores and deduplicates to pick the **top 10** for print quality, (4) serves a **local HTML review gallery** to approve/replace selections, and (5) submits a **6×4″** print order to **Prodigi/Pwinty sandbox** using **public read URLs** from OneDrive share links. Built with **Python 3.12**, a tiny **FastAPI** local server, **SQLite** (single-file) storage, **OpenCV** + **ImageHash** for scoring/dedup, **MSAL** for Graph auth, and **Requests** for APIs.

---

## Architecture Overview

**Stack:**

* Runtime: **Python 3.12**
* Web/API: **FastAPI** (+ Uvicorn for dev)
* Job scheduling: **APScheduler** (in-process)
* Auth: **MSAL (Microsoft Authentication Library for Python)** (OAuth PKCE/device code)
* HTTP: **requests**
* Image scoring: **opencv-contrib-python**, **Pillow**, **ImageHash**
* Persistence: **SQLite** via **SQLAlchemy** (single local file)
* Crypto: **cryptography** (Fernet) + **keyring** (OS keystore)
* Testing: **pytest**, **pytest-asyncio**, **responses** (HTTP mocking), **hypothesis** (optional property tests)
* Quality: **ruff** (lint), **black** (format), **mypy** (types), **pre-commit**

**App structure:**

* **Hybrid**: local REST API + static SPA page (Vanilla JS + Tailwind) served by FastAPI.
* State: persisted server-side in SQLite; UI pulls `/api/*` JSON.
* Images proxied via API to avoid exposing Graph tokens to the browser.

**Data storage:**

* **SQLite** file `photo_archivist.db` for all metadata (drive item IDs, scores, hashes, selections, runs, orders).
* No image binaries stored—**metadata only**.
* Lightweight migrations via **Alembic** (optional; or SQLAlchemy `create_all` for MVP).

**Auth:**

* Microsoft Graph **read-only scopes** (`Files.Read`, `Files.Read.All` if needed for thumbnails/share) using **OAuth PKCE** (preferred) or **device code flow** as fallback.
* Tokens cached locally; **encrypted at rest** with Fernet; key stored in **OS keyring**.

**Deployment & environments:**

* Local-only: `uvicorn photo_archivist.app:app --reload` then open `http://localhost:8787/`.
* CI (GitHub Actions): run lint + mypy + tests.
* No external hosting or secrets beyond developer sandbox keys.

---

## Tech Stack Decisions

1. **Language / Runtime:** Python 3.12 – rich ecosystem (OpenCV, MSAL), easy local distribution.
2. **Web framework:** **FastAPI** – type-hinted contracts, built-in validation via Pydantic, async-friendly; small footprint.
3. **Scheduling:** **APScheduler** – in-process, cron-like monthly job; serialized “next run” persisted to avoid duplicate fires.
4. **Storage:** **SQLite + SQLAlchemy** – single-file DB, ACID, robust indexing; meets “local file” constraint while simplifying queries.
5. **Graph integration:** **MSAL** + `requests` – fewer moving parts than the Graph SDK; explicit control of endpoints (`/me/drive/root`, `/delta`, `/thumbnails`, `/createLink`).
6. **Scoring & dedup:** **OpenCV** for blur (variance of Laplacian) and optional **BRISQUE**; **Pillow + ImageHash (pHash or dHash)** for perceptual dedup.
7. **UI:** Static HTML/JS (Vanilla + Tailwind) – minimal build, snappy; API-first makes later UI swaps easy.
8. **Print API:** **Prodigi v4 (Pwinty)** via `requests`. Product SKU/config injected via config; sandbox key from env.

---

## Interfaces

### External APIs

* **Microsoft Graph**

  * `GET /me/drive/root/delta` — incremental file listing
  * `GET /drives/{driveId}/items/{itemId}` — metadata including `photo` EXIF, width/height
  * `GET /drives/{driveId}/items/{itemId}/thumbnails` — thumbnail for gallery
  * `POST /drives/{driveId}/items/{itemId}/createLink` with `type:"view", scope:"anonymous"` — public URL for Prodigi
* **Prodigi/Pwinty Sandbox**

  * Create order, add item(s) (6×4), submit; **assets by public URL (JPG)**

### Local REST API (served by FastAPI)

```http
GET /health
200 { "ok": true, "version": "0.1.0" }

POST /api/auth/connect
Body: { "flow": "pkce" | "device_code" }
200 { "status":"connected" } | 400/401 { "error":{code,msg} }

POST /api/run/scan
Body: { "month": "YYYY-MM", "limit": 10 }  // limit optional; default 10
202 { "run_id": "<uuid>", "status":"started" }

GET /api/shortlist?month=YYYY-MM
200 { "month":"YYYY-MM", "items":[{...PhotoSummary}] }

POST /api/selection
Body: { "month":"YYYY-MM", "selected_ids":[ "<drive_item_id>", ... ] }
200 { "count": N, "ok": true } | 400 { "error":{...} }

GET /api/thumb/{drive_item_id}
200 image/jpeg  // proxied Graph thumbnail (size: medium), cached

POST /api/order
Body: {
  "month":"YYYY-MM",
  "shipping": { "name": "...", "address1":"...", "city":"...", "postcode":"...", "country":"GB" },
  "quantity_per_photo": 1,
  "product_sku": "PRINT-4X6"   // configurable; default 6x4
}
201 { "order_id":"...", "provider":"prodigi", "status":"Submitted" }
4xx/5xx { "error": { "code":"...", "message":"...", "details":... } }
```

**Validation rules & errors (common):**

* All IDs are strings; months use `^\d{4}-\d{2}$`.
* Only **JPG** items are eligible.
* Resolution gate: `min(width,height)` satisfies **≥1200×1800 px** (orientation-aware).
* Error shape: `{ "error": { "code": "BadRequest|Unauthorized|Conflict|UpstreamError", "message": "human text", "details": any } }`.

---

## Domain model

**PhotoItem**

* `id` (PK, int)
* `drive_item_id` (str, unique)
* `drive_id` (str)
* `name` (str)
* `file_extension` (str, ".jpg")
* `date_taken` (datetime, nullable)
* `width` (int), `height` (int)
* `month_bucket` (str "YYYY-MM", indexed)
* `blur_score` (float, nullable)
* `brisque_score` (float, nullable)
* `quality_score` (float, indexed)  // composite from gates + weights
* `phash` (str, length 16/64)
* `duplicate_of` (nullable str drive_item_id)
* `skipped_reason` (enum: NOT_JPG|LOW_RES|DUPLICATE|OTHER, nullable)
* `share_link_url` (nullable str)
* `share_permission_id` (nullable str)
* `created_at`, `updated_at` (timestamps)

**ShortlistEntry**

* `id` (PK)
* `photo_drive_item_id` (FK → PhotoItem.drive_item_id, unique per month)
* `month_bucket` (str, indexed)
* `rank` (int)
* `selected` (bool)
* `created_at`, `updated_at`

**Run**

* `id` (UUID PK)
* `started_at`, `finished_at`
* `month_bucket`
* `scanned_count` (int), `eligible_count` (int), `shortlisted_count` (int)
* `status` (enum: STARTED|SUCCESS|FAILED|PARTIAL)
* `error_message` (nullable)

**Order**

* `id` (PK)
* `provider_order_id` (str, indexed)
* `month_bucket`
* `items_count` (int)
* `status` (enum: CREATED|SUBMITTED|FAILED)
* `created_at`, `updated_at`

**Invariants & validations**

* **No binaries saved**; URLs only.
* **Shortlist** max size defaults to **10**, but configurable per run.
* Only **eligible** (JPG, resolution-gated, non-duplicate) photos can enter shortlist.
* `duplicate_of` must point to an existing `PhotoItem` for that month.

**Indexing**

* `PhotoItem.month_bucket`, `PhotoItem.quality_score`, `PhotoItem.drive_item_id` (unique)
* `ShortlistEntry.month_bucket`
* `Order.provider_order_id`

---

## Data flow & interfaces

**Inbound (scan):**
Scheduler → `ScanService.run(month)`

1. **Delta** fetch: Graph delta cursor for Camera Roll subtree (configurable root).
2. Filter **JPG-only**; collect EXIF dims & `dateTaken`.
3. Gate by resolution (≥1200×1800).
4. Compute **pHash** for dedup; mark near-duplicates (Hamming distance ≤ 8, configurable).
5. Compute **blur score** (variance of Laplacian); optionally **BRISQUE** if model available.
6. Compose **quality_score**; persist `PhotoItem`.
7. Rank top-N, write `ShortlistEntry` with `rank`.
8. Emit `Run` stats.

**UI / Review:**
Browser loads `/` → static HTML pulls `/api/shortlist?month=YYYY-MM`.
User selects/deselects; POST `/api/selection`.
(Optionally) “Replace” button fetches next-best eligible for month.

**Outbound (order):**
`OrderService.create_and_submit(month, selection, shipping)`

1. For each selected photo: ensure **public share link** exists (Graph `createLink`). Store `share_permission_id` for later revoke.
2. Build Prodigi order payload with **6×4 SKU**, shipping to GB (MVP).
3. POST create & submit; persist `Order`.
4. Surface result: `{order_id, status:"Submitted"}`.
5. **Cleanup**: optionally remove share permissions after order submitted (configurable delay).

---

## App structure (repo map)

```
photo-archivist/
├─ pyproject.toml                 # deps: fastapi, uvicorn, msal, requests, sqlalchemy, opencv-contrib-python, pillow, ImageHash, apscheduler, cryptography, keyring, python-dotenv, pydantic
├─ README.md
├─ .env.example
├─ .pre-commit-config.yaml
├─ alembic/                       # optional migrations
├─ src/photo_archivist/
│  ├─ app.py                      # FastAPI app, routes, startup (scheduler)
│  ├─ config.py                   # settings (pydantic BaseSettings)
│  ├─ auth/
│  │  ├─ msal_client.py           # PKCE/device code flows, token cache (encrypted)
│  ├─ graph/
│  │  ├─ client.py                # thin wrapper: get_delta, get_item, get_thumbs, create_link
│  │  ├─ parsers.py               # normalize driveItem → PhotoItem fields
│  ├─ scoring/
│  │  ├─ gates.py                 # resolution gate, filetype gate
│  │  ├─ blur.py                  # variance of Laplacian
│  │  ├─ brisque.py               # optional (model files path)
│  │  ├─ ranker.py                # weighting & composite score
│  ├─ dedup/
│  │  ├─ phash.py                 # compute & compare hamming distance
│  ├─ services/
│  │  ├─ scan_service.py          # end-to-end monthly scan
│  │  ├─ shortlist_service.py     # fetch/replace/update selection
│  │  ├─ order_service.py         # prodigi submit, link mgmt
│  ├─ storage/
│  │  ├─ db.py                    # engine/session
│  │  ├─ models.py                # SQLAlchemy models
│  │  ├─ repo.py                  # CRUD, queries
│  ├─ web/
│  │  ├─ static/
│  │  │  ├─ index.html            # gallery UI
│  │  │  ├─ app.js
│  │  │  └─ styles.css            # Tailwind (prebuilt or CDN)
│  ├─ utils/
│  │  ├─ crypto.py                # Fernet key mgmt via keyring
│  │  ├─ images.py                # safe decode, orientation
│  │  └─ time.py                  # month bucket helpers
│  └─ schemas.py                  # Pydantic request/response models
├─ tests/
│  ├─ test_scan_service.py
│  ├─ test_order_service.py
│  ├─ test_api_contracts.py
│  ├─ test_scoring.py
│  ├─ fixtures/
│  │  ├─ sample_drive_payloads.json
│  │  └─ sample_images/ (tiny JPGs for blur/hash tests)
└─ scripts/
   ├─ dev_run.sh
   └─ seed_fake_data.py
```

---

## Interfaces (module contracts)

**Auth.MSALClient**

* `begin_pkce()` → launches browser, returns tokens; caches refresh token encrypted.
* `get_token(scopes: list[str]) -> str` (access token).

**Graph.Client**

* `get_delta(cursor: str|None) -> (items: list[DriveItem], next_cursor: str)`
* `get_item(item_id) -> DriveItem`
* `get_thumbnail(item_id, size="medium") -> bytes`
* `create_anon_view_link(item_id) -> (url, permission_id)`

**Scoring**

* `passes_resolution(width:int, height:int) -> bool`
* `blur_score(image_bytes) -> float`
* `brisque_score(image_bytes) -> float|None`
* `composite(blur, brisque|None, width, height) -> float`

**Dedup**

* `phash(image_bytes) -> str`
* `is_near_duplicate(hash_a, hash_b, threshold:int=8) -> bool`

**Services.ScanService**

* `run(month:str, limit:int=10) -> Run`  // populates DB with shortlist

**Services.ShortlistService**

* `get_shortlist(month:str) -> list[PhotoSummary]`
* `set_selection(month:str, selected_ids:list[str]) -> int`
* `next_best(month:str, exclude_ids:list[str]) -> PhotoSummary|None`

**Services.OrderService**

* `submit_order(month, selected_ids, shipping, product_sku="PRINT-4X6") -> Order`

---

## Acceptance Criteria

* Connects to OneDrive with **read-only scopes**; token stored **encrypted**; revoke path tested.
* Monthly job (default) scans via **delta**, handles throttling/backoff; persists **top 10** JPGs.
* Shortlist visible in a local gallery with thumbnails, full-size preview, **approve/decline/replace**; ordering in ≤2 clicks.
* **Resolution gate ≥1200×1800**; blur check applied; dedup via perceptual hash.
* **Order created & submitted** in Prodigi/Pwinty **sandbox** with **URL-based JPG assets**; returns an **order ID** and **Submitted** status.
* **No image binaries** persist locally; metadata & share links only.
* Run of ~1k images completes without fatal Graph throttling; resumes if interrupted.

---

## Tooling & workflows

**Testing**

* Unit: scoring (blur/brisque), dedup thresholds, delta parser.
* Service: scan → shortlist → selection → order (mock Graph/Prodigi with **responses**).
* API: contract tests for `/api/*`.
* Coverage: **≥85%** on services and API layers; smoke test for UI JSON flows.

**Quality**

* `ruff` + `black` on commit; `mypy --strict` for `src/`.
* `pre-commit` runs lint, type-check, and tests on changed files.

**Collaboration**

* Branching: `main` (protected), feature branches via PR; require 1 review + green CI.
* Docs: update `README.md` (setup, scopes), API docs (FastAPI `/docs`), and CHANGELOG per release.

---

## Risks & mitigations

1. **Prodigi product SKU/contract mismatch** → *Mitigation:* make SKU configurable; write contract test against sandbox; assert JPG URL acceptance.
2. **Graph share link expiry/tenant policy** → *Mitigation:* create links just-in-time; submit order immediately; store `permission_id` and revoke after submission (toggle).
3. **HEIC prevalence lowers candidate pool** → *Mitigation:* surface “skipped non-JPG” count; optional 200 DPI soft gate fallback if <10 items.
4. **OpenCV BRISQUE model availability** → *Mitigation:* treat BRISQUE as optional; ship blur+resolution as sufficient MVP; feature-flag BRISQUE.
5. **Token security on disk** → *Mitigation:* encrypt with Fernet; key in OS keyring; redact tokens/URLs in logs.

---

## Assumptions

* OneDrive **Camera Roll** (or root) contains enough **JPGs** for MVP.
* Users accept creating **anonymous view** links for selected items and understand they’re short-lived for ordering.
* UK shipping via Prodigi network is OK for pilot.
* Local browser is available; default port **8787** is free.
* Timezone: **Europe/London**; month boundaries aligned to local time.

---

## Open questions

1. **Per-link expiration requirement?** If mandated, we may need a timed revoke or tenant policy—confirm with stakeholders.
2. **Fallback when <10 meet 300 DPI?** Choose: allow ≥200 DPI **or** carry over to next run. Decision impacts scoring weights/UI message.
3. **Face boost in MVP?** If yes, add lightweight face detection (OpenCV Haar/cv2.dnn) and minor score bump.
4. **Final target API:** Confirm **Prodigi v4** endpoints & 6×4 SKU string; lock config names.
5. **Shipping address UX:** Fixed per user (saved locally) vs prompt each order; default for MVP?

*Resolution plan:* capture decisions in `config.json`, add tests for the chosen behavior, and mark anti-choices as feature flags.

---

## Iteration readiness checklist

* [ ] Scopes & OAuth flow decided; app registration values recorded in `.env.example`.
* [ ] Product SKU + sandbox credentials confirmed; contract test green.
* [ ] Database schema frozen; indices defined; (optional) Alembic migration created.
* [ ] API contracts stable and documented; example requests added.
* [ ] Quality-scoring weights and dedup thresholds checked into config with sane defaults.
* [ ] Scheduler default set to monthly; manual trigger endpoint working.
* [ ] Logging/redaction policy implemented; PII-safe by default.
* [ ] CI pipeline runs lint, mypy, tests on PR; pre-commit hooks documented.
* [ ] “Change Request” process noted for any file/contract additions post-approval.

---

### Guardrails

* **System design scope only**; no slice-by-slice dev plan here.
* No silent scope changes—API contracts & files added only via explicit **Change Request**.
* Favor batteries-included libs; keep everything local-first; **single SQLite file** store.
* Examples and tests must run without external secrets (use mocks/fixtures); real keys only during manual sandbox runs.
* Never store image binaries; only IDs, hashes, scores, and share links.
* Respect least-privilege Graph scopes and **avoid logging** tokens, EXIF contents, or face data.
