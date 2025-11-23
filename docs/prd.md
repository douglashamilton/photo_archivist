## PRD Template

### Bottom line

 Build Photo Archivist as a lightweight, local Python web app that lets a user choose a photo directory, filter images by date, drop low-quality frames via cheap CPU-friendly gates (brightness/contrast/blur/resolution/aspect), de-duplicate bursts with perceptual hashes, rank remaining shots with a single aesthetic score, display the top five thumbnails with their metrics for quick review, and fire-and-forget a 4×6" print order for any (or all) shortlisted photos via the Prodigi (Pwinty) print API sandbox.

### Problem Statement

People with large local photo libraries struggle to surface highlights from specific time periods. Manual scanning is tedious, so they need a private, fast way to filter by date and surface only a handful of representative shots without uploading files or managing a heavy photo suite.

### Target Users / Personas

* Memory Curator: wants to revisit a trip or event quickly by narrowing a folder to the best photos from a date range.
* Top jobs-to-be-done:
  * Pick a directory and date window to trim thousands of photos to a manageable shortlist.
  * View the shortlisted thumbnails with basic details (file name, capture date, brightness score).
  * Rerun the scan with a different window if the initial results are off.

### Comparable solutions / references

* PhotoPrism - powerful self-hosted photo manager; more complex than a quick shortlist tool.
* Immich - modern self-hosted gallery; focuses on sync and sharing rather than lightweight curation.
* Apple Photos / Google Photos - polished but cloud-first ecosystems that require uploads and accounts.

### User Stories

* Given a local photo library, when I select a root directory and provide a start and end date, then the app scans and shows only images in that range.
* Given the filtered results, when the app finishes scoring, then I immediately see thumbnails for the top five brightest images so I can decide what to do next.
* Given the shortlist, when I adjust the date range, then the app rescans and replaces the shortlist with updated thumbnails.
* Given a shortlist, when I select one or more photos and choose to print them, then the app submits a 4×6" print order to the Prodigi sandbox and confirms the order reference.

### Must-Have Features (MVP)

* Simple UI to choose a local directory and input start/end dates.
* Recursive scan that filters images by EXIF DateTimeOriginal with fallback to file modified time.
* Extensible scoring pipeline applied to each in-range image with cheap gates first (brightness/contrast/blur/resolution/aspect) so mushy or tiny frames are dropped before heavier work.
* Perceptual-hash deduplication that groups near-duplicates (Hamming distance ≤5) and keeps only the best two per burst, with cluster metadata passed through for debugging.
* Aesthetic scoring (LAION/AVA head via Hugging Face) on the remaining images, cached per file hash, with sharpness as a tie-breaker so the five most appealing thumbnails surface first.
* Automatic selection and display of the five highest-scoring thumbnails with filename, capture date, aesthetic score, and cheap quality metrics.
* Clear shortlist count and ability to rerun the pipeline when the user changes the date window.
* Automated tests covering date filtering, metadata fallback, brightness scoring, and shortlist selection rules.
* Fire-and-forget order submission for selected shortlist photos to the Prodigi print API sandbox using temporary public asset URLs, capturing the returned order reference for user feedback.

### Nice-to-Have Features

* None for MVP; future enhancements will be captured in later slices.

### Non-functional Requirements

* Runs entirely on the user's machine; outbound network calls limited to the Prodigi print API for order submission.
* Built with Python 3.12+ using a minimal web stack (for example, FastAPI plus a lightweight front end).
* Responds with the shortlist within a reasonable time for medium libraries (benchmark: 5,000 images in under 30 seconds on a modern laptop).
* Works in current desktop browsers (Chromium, Firefox, Safari).

### Data Considerations

* Primary metadata source is EXIF DateTimeOriginal; fall back to file modified time when EXIF is missing.
* Non-image files must be skipped quickly to keep scans fast.
* MVP targets JPEG (.jpg) files; other formats are ignored.
* Cheap quality metrics include mean luminance, luminance standard deviation (contrast), Laplacian variance (blur/sharpness), resolution, and aspect ratio with defaults: drop if mean L < 30 or contrast < 10, flag soft if L < 50 or blur variance < 120 (drop < 50), and drop if min dimension < 600px or aspect outside 0.33–3.
* Perceptual hashes use a Hamming distance threshold of 5; keep the top two images per cluster before running the aesthetic model.
* Scoring engine records all metrics per photo so alternate heuristics (faces, composition, weather cues) can be layered in later without rescan of the directory traversal stage.
* Print orders require HTTPS-accessible temporary URLs for each original-resolution asset; thumbnails are insufficient for fulfillment.

### Acceptance Criteria

* User selects a directory and date range and receives feedback that the scan is in progress.
* Only images inside the date range are included in scoring.
* Exactly five images with the highest aesthetic scores are shown with thumbnails, file names, capture dates, cheap metrics (brightness/contrast/sharpness), and aesthetic score; sharpness breaks ties.
* Low-quality frames are dropped when mean luminance < 30, contrast < 10, Laplacian variance < 50, min dimension < 600px, or aspect ratio < 0.33/>3. Frames between thresholds (e.g., dim or soft blur) are marked “soft” but kept.
* Near-duplicate images are grouped via perceptual hash distance ≤5 and trimmed to the best two per cluster before aesthetic scoring; cluster identifiers are surfaced for debugging.
* Updating the date range reruns the scan and refreshes the shortlist without a page reload.
* Submitting a print request for a subset of shortlist photos creates a Prodigi sandbox order with the `GLOBAL-PRINT-4X6` (or equivalent) SKU, returning an order identifier and indicating success/failure to the user.
* Automated tests for filtering, scoring logic, shortlist selection, and order payload construction run successfully.

### Risks & Mitigations

* Missing EXIF data could exclude valid photos -> fall back to file modified time and flag when the fallback occurs.
* Large directories might slow scans -> stream progress feedback and set expectations in the UI.
* Brightness may not reflect perceived quality -> encapsulate scoring so alternative metrics can replace it with minimal changes.
* External print API outages or credential misconfiguration could block orders -> surface order failures with actionable error messages and allow retry.

### Out-of-Scope

* Cloud sync, external storage integration, or multi-user accounts.
* Export, tagging, rating, or other management features.
* Persistent storage of shortlist results beyond the current session.

### Assumptions

* Users can navigate their filesystem via a standard directory picker.
* The local machine has enough resources to scan the selected directory.
* Brightness scoring is acceptable as the initial quality proxy.
* Users supply their own Prodigi API key and have pre-configured payment details; MVP relies on the Prodigi sandbox for testing.
* The app can expose temporary HTTPS URLs for selected assets (for example, through an ephemeral file-sharing service or user-provided hosting).

### Open questions (answer before planning)

None.

### Sources

* PhotoPrism Team. "PhotoPrism Release 240915-e1280b2fb." GitHub Releases, 2024-09-15. https://github.com/photoprism/photoprism/releases/tag/240915-e1280b2fb
* Immich Maintainers. "Immich v1.110.0." GitHub Releases, 2024-07-26. https://github.com/immich-app/immich/releases/tag/v1.110.0
* Pillow Contributors. "Pillow 11.0.0 Release." GitHub Releases, 2024-10-15. https://github.com/python-pillow/Pillow/releases/tag/11.0.0
* FastAPI Team. "FastAPI 0.115.6." GitHub Releases, 2024-12-03. https://github.com/fastapi/fastapi/releases/tag/0.115.6
* pytest Developers. "pytest 8.3.4." GitHub Releases, 2024-12-01. https://github.com/pytest-dev/pytest/releases/tag/8.3.4
