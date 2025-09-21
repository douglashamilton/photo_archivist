### Bottom line

Build a desktop Python MVP that (a) connects to the user’s OneDrive with delegated consent, (b) uses Microsoft Graph **delta queries** to scan only *new or changed* photos on a schedule, (c) scores images with lightweight, no-reference quality metrics and duplicate detection, (d) presents a shortlist for review, and (e) “prints” via a UK-ready provider in **test/sandbox mode** (e.g., Kite) to validate the end-to-end flow without shipping costs. This approach minimizes data handling (no image edits or copies), keeps sync fast and cheap, and proves the highest-risk integration points first. \[1]\[2]\[7]\[8] ([Microsoft Learn][1])

---

### Steps

* Set up OneDrive access (MSAL + Graph), implement **drive/root/delta** sync and basic metadata pull (EXIF/taken time), with throttling-safe retries. \[1]\[4] ([Microsoft Learn][1])
* Implement scoring pipeline: sharpness/exposure heuristics + **BRISQUE** for tie-breaks + **perceptual hashing** for dedupe; output top *N* with reasons. \[5]\[6] ([LearnOpenCV][2])
* Wire the “print” leg using **Kite API test keys** to place sandbox orders and capture artifacts (mock order IDs, previews). \[7] ([KITE][3])

---

### Research brief

**Users & jobs (pains → outcomes)**

* Camera rolls balloon (median \~2.8k photos), people rarely curate → want *hands-off triage* and a small, high-quality set to print. \[8] ([PhotoAid][4])
* Time-poor parents: prefer defaults; want trustworthy picks (in-focus, well-exposed, non-duplicates, faces visible).
* Don’t want cloud lock-in or migration; *read-only* access preferred; no image modification or copying.
* One-click checkout; predictable costs; no surprises.

**Comparable solutions / references**

* **OneDrive + Photos**: robust thumbnails, metadata, and preview tooling for photo workflows. \[2] ([Microsoft Learn][5])
* **Google Photos & print flows** (as pattern reference): in-app print journeys validate appetite for curated-to-print flows.
* **BRISQUE / OpenCV**: common, fast IQA & blur heuristics used in industry examples. \[5] ([LearnOpenCV][2])
* **Perceptual hashing (imagehash)**: standard approach for near-duplicate detection. \[6] ([PyPI][6])

**Data & APIs (what you’ll need)**

* **Microsoft Graph (OneDrive)**: `drive/root/delta` for incremental scans; `driveItem` photo facets/EXIF; thumbnails (for preview-only); OAuth2 delegated scopes (`Files.Read`, `offline_access`). \[1]\[2] ([Microsoft Learn][1])
* **Service protection**: handle 429s via `Retry-After` backoff; small, paged reads. \[4] ([Microsoft Learn][7])
* **Print provider (UK, testable)**: **Kite API** (REST, **test-mode keys** so no charges/shipments) for photo prints; alternative later (Gelato/Printful). \[7] ([KITE][3])
* **Local analysis**: Python + OpenCV/BRISQUE/imagehash libs (no server copy; stream bytes → memory). \[5]\[6] ([LearnOpenCV][2])

**Privacy & compliance**

* Treat photos as **personal data**; apply **data minimisation** (process only what’s needed; don’t store originals; keep minimal derived scores). \[3] ([ICO][8])
* Avoid **biometric identification**; simple face *detection* for quality (e.g., “eyes open”) is safer than identification; don’t build recognition or profiling in MVP. \[3] ([ICO][8])

**Performance & scale envelope (MVP)**

* Typical camera roll: \~2–4k photos baseline; weekly additions hundreds. Target: initial scan ≤10–15 min; incremental runs (delta) ≪2 min for <200 new items. \[1]\[8] ([Microsoft Learn][1])
* Local scoring per image: tens of ms (Laplacian/entropy), hundreds of ms (BRISQUE) on laptop-class CPU for shortlists. \[5] ([LearnOpenCV][2])

**Constraints & dependencies**

* Platform: desktop Python 3.10+; MSAL for auth; OpenCV/imagehash.
* Internet required; OneDrive account with Photos/Camera Roll.
* Print integration depends on provider sandbox availability (Kite OK). \[7] ([KITE][3])

---

### MVP scope (first shippable)

* OAuth sign-in to OneDrive (delegated **read-only**); store refresh token securely. \[2] ([Microsoft Learn][5])
* Scheduled **delta** scan; filter to images; collect EXIF (timestamp, dimensions). \[1] ([Microsoft Learn][1])
* Quality scoring: blur (Laplacian variance), exposure/contrast heuristic; optional **BRISQUE** tie-break. \[5] ([LearnOpenCV][2])
* **Duplicate detection** via perceptual hashing; cluster near-dupes; keep best of set. \[6] ([PyPI][6])
* Config: frequency (daily/weekly), shortlist size (e.g., 20), folders in scope.
* Review UI: grid of candidates with scores/reasons; user approve/replace.
* **Print sandbox**: create a mock order with **Kite test keys**; capture order ID + cost/size preview; no shipment. \[7] ([KITE][3])
* Logging: minimal (counts, item IDs, scores, errors); no image writes.

---

### Domain model candidates

**Entities & fields**

* **User**: userId (UUID), oneDriveTenant, consentScopes\[], schedule, shortlistSize.
* **Asset**: itemId (Graph id), path, takenAt, width/height, exif (subset), hash (pHash), lastSeenToken.
* **Score**: assetId → {sharpness, exposure, brisque?, faceCount?, finalScore}.
* **Shortlist**: shortlistId, createdAt, assetIds\[], rationale.
* **PrintOrder**: provider, mode(test/live), items\[{assetId, size}], status, providerOrderId?.

**Relationships**

* User 1—\* Assets; Asset 1—1 Score; User 1—\* Shortlists; Shortlist *—* Assets; Shortlist 1—0..1 PrintOrder.

**Events/flows**

1. **Sync run** → Input: `deltaLink` → Output: new/changed Assets; update Score for changed. \[1] ([Microsoft Learn][1])
2. **Scoring** → Input: asset bytes (stream) → compute heuristics + hash → persist Score. \[5]\[6] ([LearnOpenCV][2])
3. **Shortlist build** → Input: Scores, N → rank, de-dupe clusters → Shortlist.
4. **Print (test)** → Input: approved assets → Kite sandbox order → store providerOrderId. \[7] ([KITE][3])

---

### Acceptance criteria (testable)

* **Given** a connected OneDrive and an initial **delta** run, **when** the first scan completes, **then** the app stores a `deltaLink` and subsequent scans fetch only changes (no full re-read). \[1] ([Microsoft Learn][1])
* **Given** N=20 and a folder with >200 photos, **when** a scan runs, **then** the shortlist contains ≤20 unique assets with per-image score details (sharpness/exposure/dupe rationale).
* **Given** a set of near-duplicates, **when** hashed with pHash (Hamming distance ≤5), **then** only the highest-scoring member appears in the shortlist. \[6] ([PyPI][6])
* **Given** 429 responses from Graph, **when** the app retries using `Retry-After`, **then** the operation eventually succeeds without user action. \[4] ([Microsoft Learn][7])
* **Given** the user clicks **Print (Test)**, **when** an order is created with **Kite test keys**, **then** the app shows a sandbox order ID and no charges/shipments occur. \[7] ([KITE][3])
* **Given** the constraint “no image modifications or copies,” **when** the app runs, **then** it does not write original images to disk and stores only minimal metadata/scores (verified by logs/config).
* **Given** data-minimization, **when** logs are persisted, **then** they exclude PII/EXIF beyond what’s necessary for ranking and ordering. \[3] ([ICO][8])

---

### Sample I/O & UI hints

**Sample inputs**

* Config: `{ "frequency": "weekly", "shortlistSize": 20, "folders": ["Photos/Camera Roll"], "minSharpness": 100.0 }`
* User action: “Replace #7 with #22 (family portrait).”
* Edge: HEIC burst of 30 near-duplicates; include only 1.

**Expected outputs**

* Shortlist JSON: `[{ "itemId": "...", "finalScore": 0.86, "reasons": ["sharp","well-exposed","best-of-dup-cluster"]}, ...]`
* Print test result: `{ "provider":"kite", "mode":"test", "orderId":"ko_test_123", "status":"queued" }` \[7] ([KITE][3])

**UI reference links**

* **Fluent UI** list/grid & controls (aligns with Microsoft ecosystem). \[2] ([Microsoft Learn][5])
* Tailwind/Flowbite gallery layouts for image grids (fast shortlist review). ([Flowbite][9])

---

### Risks & unknowns (with mitigation)

1. **Print API volatility / fees** — Start with **Kite test mode**; abstract provider; add Gelato/Printful later. \[7] ([KITE][3])
2. **Scoring trust** — Combine simple heuristics + BRISQUE; surface rationale tooltips; allow user overrides. \[5] ([LearnOpenCV][2])
3. **Large libraries** — Use **delta**; paginate; throttle-aware retries. \[1]\[4] ([Microsoft Learn][1])
4. **Privacy** — Process in memory; minimize logs; avoid identification; document DPIA position if features expand. \[3] ([ICO][8])
5. **File types/EXIF variance** — Fallback to generic heuristics when metadata missing; test on HEIC/JPEG.

---

### Open questions (answer before planning)

1. **Which print sizes/products for MVP?** → Decide 1–2 SKUs (e.g., 6×4", 5×7"); verify availability in Kite sandbox. \[7] ([KITE][3])
2. **Review UI form** (native desktop vs. simple web UI) → Spike both; pick simplest path that allows image grid + approve/replace.
3. **Scope of folders** (Camera Roll only vs. all Photos) → Default to Photos/Camera Roll; expose include/exclude rules.
4. **Scheduling granularity** → Cron-style (daily/weekly) vs. manual run; confirm with target users.
5. **Face heuristics** → OK to use face *detection* for quality? If yes, specify models and disable any identification. \[3] ([ICO][8])

---

### Sources

\[1] **Microsoft Graph—Delta query overview** (Apr 30, 2025). ([Microsoft Learn][1])
\[2] **OneDrive file storage API overview (Microsoft Graph)** (Nov 7, 2024). ([Microsoft Learn][5])
\[3] **ICO—Principle (c): Data minimisation** (accessed Sep 2025). ([ICO][8])
\[4] **Microsoft Graph—Throttling guidance** (Jan 14, 2025). ([Microsoft Learn][7])
\[5] **LearnOpenCV—Image Quality Assessment: BRISQUE** (Jun 20, 2018; updated). ([LearnOpenCV][2])
\[6] **ImageHash (PyPI)** — perceptual hashing library (current project page). ([PyPI][6])
\[7] **Kite Print API docs—test vs. live keys (sandbox mode)** (accessed Sep 2025). ([KITE][3])
\[8] **PhotoAid—Mobile Photography Statistics 2025** (Mar 9, 2025). ([PhotoAid][4])

---

### Assumptions

* OneDrive is the only storage for MVP; delegated **Files.Read** + `offline_access` consent is acceptable to target users.
* “No copies” means we may *stream* image bytes for analysis but will not persist originals or transformed variants.
* Quality definition: “technically good” (sharp, balanced exposure) precedes content preferences.
* UK users; initial print provider is UK-capable; sandbox acceptable for validation.

[1]: https://learn.microsoft.com/en-us/graph/delta-query-overview?utm_source=chatgpt.com "Use delta query to track changes in Microsoft Graph data"
[2]: https://learnopencv.com/image-quality-assessment-brisque/?utm_source=chatgpt.com "Image Quality Assessment : BRISQUE"
[3]: https://www.kite.ly/docs/?utm_source=chatgpt.com "Print API Reference - Kite.ly"
[4]: https://photoaid.com/blog/mobile-photography-statistics/?srsltid=AfmBOoqqUEWCzGTm49SbEbE4qgQYKSIl2ogyoeNU2YS-Rxs-bBH7mZuE&utm_source=chatgpt.com "18+ Mobile Photography Statistics for 2025"
[5]: https://learn.microsoft.com/en-us/graph/onedrive-concept-overview?utm_source=chatgpt.com "OneDrive file storage API overview - Microsoft Graph"
[6]: https://pypi.org/project/ImageHash/?utm_source=chatgpt.com "ImageHash"
[7]: https://learn.microsoft.com/en-us/graph/throttling?utm_source=chatgpt.com "Microsoft Graph throttling guidance"
[8]: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/?utm_source=chatgpt.com "Principle (c): Data minimisation | ICO"
[9]: https://flowbite.com/docs/components/gallery/?utm_source=chatgpt.com "Tailwind CSS Gallery (Masonry)"

### Resolutions and Corrections
Open questions resolved:
1. Which print sizes/products for MVP? photos_4x6 
2. Review UI form (native desktop vs. simple web UI) → Spike both; pick simplest path that allows image grid + approve/replace. 
3. Scope of folders (Camera Roll only vs. all Photos) → Default to Photos/Camera Roll; expose include/exclude rules. 
4. Scheduling granularity → Cron-style (monthly/quarterly) with dev-mode manual trigger for testing. 
5. Face heuristics → MVP, no. However, expect the image quality analysis code to be extended to include quality, face identification, composition, etc (out of scope of MVP).
