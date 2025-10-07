### Bottom line

Build a desktop MVP that connects to a user’s **OneDrive** (via Microsoft Graph), runs a **monthly** job that scores recent **JPG** photos for technical quality, picks the **top 10**, shows a **local HTML review gallery**, and—on approval—submits 6×4″ prints to a **Pwinty/Prodigi** sandbox order using **public read URLs** from OneDrive share links. This path is feasible now (Graph read + delta sync, share links; Pwinty accepts image URLs/JPG only) and aligns with printing quality guidance (≥1200×1800 px for 6×4) while avoiding copying/modifying images. [1][2][4][5]

---

### Problem Statement

Time-poor people accumulate thousands of phone photos but rarely curate or print them. There’s no simple **“cloud gallery → auto-curate → print”** flow that works hands-off for ordinary users. Photo Archivist automates curation and streamlines printing to make **physicals happen** without managing albums or uploads.

---

### Target Users / Personas

* **Busy parent** who wants monthly highlights printed without triage.
* **Memory-keeper** (grandparent/relative) who values tangible photos but dislikes tooling.
* **Casual shooter** with average photos; wants “set-and-forget” and quick review.

**Top JTBD**

1. “When I don’t have time to sort photos, help me automatically pick the best ones for printing.”
2. “Let me quickly veto/replace suggestions before ordering.”
3. “Ship prints to my address without manual uploading/cropping.”

---

### Comparable solutions / references

* **Google Photos prints**: integrated ordering; manual selection; home delivery in UK. No automated “best-of” to print pipeline. [8]
* **Photobox / Snapfish / FreePrints**: inexpensive 6×4″ prints; upload-and-order workflows; no OneDrive curation integration.
* **Open-source curation patterns**: quality metrics (BRISQUE/blur), dedup via perceptual hashing—useful patterns for MVP scoring. [6]

---

### User Stories

1. **Given** I’ve connected OneDrive and set monthly cadence, **when** the month ends, **then** I see a local gallery of ~10 shortlisted JPGs ready to approve.
2. **Given** I’m reviewing the shortlist, **when** I deselect some and add a few alternates from the same month, **then** the selection count updates and I can proceed to “Order”.
3. **Given** I click “Order”, **when** I confirm shipping details, **then** an order is created in the print service sandbox and I get a local confirmation with order ID.

---

### Must-Have Features (MVP)

* **OneDrive connect (OAuth)** with least-privilege read scopes; cache refresh tokens locally. [2]
* **Monthly scan (default)** using Graph **delta** to fetch only new/changed photos. [2]
* **JPG-only ingest**; ignore non-JPGs (surface count of skipped files).
* **Quality scoring** (technical): resolution gate (≥1200×1800 px for 6×4), blur/sharpness check, optional BRISQUE score; simple weighting to rank. [5][6]
* **Near-duplicate filter** (perceptual hash) to avoid printing multiples of same scene.
* **Local review gallery** (static HTML) with approve/decline and replace from same window.
* **Print submission (sandbox)** to **Pwinty/Prodigi**: create order, add photos by **URL**, 6×4 product type, submit. [4]
* **Linking to photos** via OneDrive **share links** (public view) per asset—no copies. [1]

---

### Nice-to-Have Features

* Face detection heuristic (boost images with faces, n>1).
* Basic exposure/noise checks (reject extreme under/over exposure).
* Selectable cadence (weekly/quarterly) and shortlist size.
* Simple “replace with next-best” suggestion during review.

---

### Non-functional Requirements

* **Platform**: Desktop app; Python 3.12; modern desktop browsers for local gallery.
* **Performance**: Score ≥1,000 images/min on a mid-range laptop; local gallery loads in ≤2 s for 10–30 thumbnails.
* **Security**: OAuth with Graph; store tokens encrypted at rest; no secrets in code; HTTPS only for any local callback endpoints. [2]
* **Privacy**: **No image copies** stored by the app; store only file IDs, scores, and user choices; minimize data per **ICO data minimisation**. [7]
* **Logging**: No EXIF, faces, or PII in logs; redact URLs/tokens.
* **Resilience**: Handle Graph throttling/retries; resume delta after failures. [2]

---

### Data Considerations

* **Sources**: OneDrive driveItems + **photo/EXIF** properties for dateTaken, dimensions, camera; Graph **delta** for incremental sync; thumbnails for gallery (optional). [2][3]
* **Quality gates**:

  * Minimum pixels for 6×4 at 300 DPI: **≥1200×1800**; soft-fail ≥200 DPI. [5]
  * Blur via **variance of Laplacian**; optional **BRISQUE** (OpenCV quality module). [6]
  * Dedup via dHash/pHash (Hamming distance threshold).
* **Structure**: Local cache table per user: {driveItemId, monthBucket, width, height, scores, shortlistFlag}.
* **Links**: Use **createLink** (anonymous “view” link) to supply a public URL to the print API. Note: per-link expiry can depend on tenant policy; the API doesn’t set arbitrary expirations. [1]
* **Edge cases**: Live Photos/bursts/HEIC ignored (MVP JPG-only); orientation metadata; panoramas auto-fail resolution gate for 6×4.

---

### Acceptance Criteria

* Connect OneDrive with **read scopes only**; revoke works.
* Default monthly job selects **top 10** JPGs; user can change count before run.
* Local gallery shows thumbnails, full-size preview, and approval controls in **≤2 clicks** to order.
* Prints created in **Pwinty/Prodigi sandbox** with **type “4x6”** items added by **URL**; order status returns “Submitted”. [4]
* **Zero persistent image copies**; only metadata cached locally.
* Run completes (1k images) without Graph throttling errors or, if throttled, with successful retry.

---

### Risks & Mitigations

1. **Pwinty API versioning**: v2.6 is **deprecated**; Prodigi v4 is current. *Mitigation*: target v4 early for longevity; use v2.6 docs only to validate model (URLs/JPG). [4]
2. **Expiring public URLs**: Graph **createLink** doesn’t let apps set per-link expirations; relies on tenant policy. *Mitigation*: short-lived orders; delete permissions post-submission; document policy requirement. [1]
3. **HEIC prevalence** on iPhone → low JPG coverage. *Mitigation*: clearly surface skipped counts; future optional client-side conversion (out-of-scope for MVP).
4. **Quality scoring mismatch** with user taste. *Mitigation*: conservative gates (resolution/blur) + easy manual overrides; log declined reasons to tune.
5. **Graph throttling** on large libraries. *Mitigation*: **delta** sync, backoff, resume tokens; nightly windows. [2]

---

### Out-of-Scope

* Multi-account/family galleries; social/Frameo pushes; user-tunable “best” definitions (content-aware); non-OneDrive sources; mobile apps; non-6×4 products; payment flows beyond print provider defaults.

---

### Assumptions

* Users allow public-read share links for selected photos (revoked after order completes). [1]
* OneDrive photo libraries have sufficient **JPG** coverage for MVP (HEIC ignored).
* UK shipping via the Prodigi network is acceptable for pilot; sandbox test is sufficient to validate flow. [4]
* **Monthly** default cadence; **10** default shortlist.

---

### Open questions (answer before planning)

1. Do we require **per-link expiration** for privacy, or is post-order permission revocation acceptable? (Graph cannot set per-link expiry directly.) [1]
2. What’s the **fallback** if fewer than 10 JPGs meet the 300 DPI gate—allow 200 DPI or carry over to next run? [5]
3. Should we **boost faces** in scoring for parents, or keep technical-only for MVP?
4. Confirm target: **Prodigi v4** integration (recommended) vs legacy Pwinty endpoints for the pilot. [4]
5. Shipping details: fixed **single address** per user for MVP, or prompt each run?

---

### Sources

1. **Microsoft Graph – Create sharing link (DriveItem createLink).** *Docs*, **Jul 23, 2025**. ([Microsoft Learn][1])
2. **Microsoft Graph – Delta query overview.** *Docs*, **Apr 30, 2025**. ([Microsoft Learn][2])
3. **Microsoft Graph – Photo resource (EXIF on driveItem).** *Docs*, **Jan 6, 2023**. ([Microsoft Learn][3])
4. **Pwinty API v2.6 (deprecated; use Prodigi v4).** *Docs*, *accessed Oct 4, 2025* — supports adding photos by **URL**, JPG-only validation, product type “4x6”, sandbox. ([Pwinty][4])
5. **Fujifilm UK – Top tips for printing photos from your phone** (1200×1800 px for 4×6). *Blog*, **Mar 11, 2024**. ([MyFUJIFILM][5])
6. **OpenCV – BRISQUE quality (no-reference IQA).** *Docs*, *accessed Oct 4, 2025*. ([OpenCV Documentation][6])
7. **ICO UK – Data minimisation principle (UK GDPR).** *Guidance*, *accessed Oct 4, 2025*. ([ICO][7])
8. **Google Photos – Photo prints product & shipping info (UK).** *Help Center*, *accessed Oct 4, 2025*. ([Google Help][8])

---

### Feasibility notes (for Step-2 design)

* **Graph integration**: Files.Read(.*) scopes suffice for personal OneDrive reading; **delta** keeps runs fast; consider **thumbnails** endpoint for fast gallery previews (optional). [2]
* **Print API**: Treat “Pwinty” as **Prodigi v4** going forward; still leverage the same **URL-pull** pattern for assets. [4]
* **Quality**: Start with deterministic gates (resolution + blur) and an optional BRISQUE threshold; keep weights/config hidden in code for MVP. [5][6]
* **Privacy**: Minimise data (IDs + scores), short-lived public links, revoke share permissions post-order; no image persistence. [1][7]

[1]: https://learn.microsoft.com/en-us/graph/api/driveitem-createlink?view=graph-rest-1.0&utm_source=chatgpt.com "Create a sharing link for a DriveItem"
[2]: https://learn.microsoft.com/en-us/graph/delta-query-overview?utm_source=chatgpt.com "Use delta query to track changes in Microsoft Graph data"
[3]: https://learn.microsoft.com/en-us/graph/api/resources/photo?view=graph-rest-1.0&utm_source=chatgpt.com "photo - Microsoft Graph v1.0"
[4]: https://pwinty.com/api/2.6/ "API documentation for v2.6 | Pwinty | On-Demand Print API"
[5]: https://my.fujifilm.com/uk/blog/prints/top-tips-for-printing-photos-from-your-phone?utm_source=chatgpt.com "Top Tips For Printing Photos From Your Phone"
[6]: https://docs.opencv.org/4.x/d8/d99/classcv_1_1quality_1_1QualityBRISQUE.html?utm_source=chatgpt.com "cv::quality::QualityBRISQUE Class Reference"
[7]: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/?utm_source=chatgpt.com "Principle (c): Data minimisation | ICO"
[8]: https://support.google.com/photos/answer/12318820?co=GENIE.CountryCode%3DGB&hl=en&utm_source=chatgpt.com "Check photo prints product & shipping info - United Kingdom"
