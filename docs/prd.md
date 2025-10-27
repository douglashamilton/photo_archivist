## PRD Template

### Bottom line

Build Photo Archivist as a lightweight, local Python web app that lets a user choose a photo directory, filter images by date, score each image by brightness, and immediately display the top five thumbnails for quick review.

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

### Must-Have Features (MVP)

* Simple UI to choose a local directory and input start/end dates.
* Recursive scan that filters images by EXIF DateTimeOriginal with fallback to file modified time.
* Brightness-based scoring applied to each in-range image.
* Automatic selection and display of the five highest-scoring thumbnails with filename, capture date, and score.
* Clear shortlist count and ability to rerun the pipeline when the user changes the date window.
* Automated tests covering date filtering, metadata fallback, brightness scoring, and shortlist selection rules.

### Nice-to-Have Features

* None for MVP; future enhancements will be captured in later slices.

### Non-functional Requirements

* Runs entirely on the user's machine; no network calls required for core workflows.
* Built with Python 3.12+ using a minimal web stack (for example, FastAPI plus a lightweight front end).
* Responds with the shortlist within a reasonable time for medium libraries (benchmark: 5,000 images in under 30 seconds on a modern laptop).
* Works in current desktop browsers (Chromium, Firefox, Safari).

### Data Considerations

* Primary metadata source is EXIF DateTimeOriginal; fall back to file modified time when EXIF is missing.
* Non-image files must be skipped quickly to keep scans fast.
* MVP targets JPEG (.jpg) files; other formats are ignored.
* Brightness scoring can use mean pixel luminance and should be isolated for future metric swaps.

### Acceptance Criteria

* User selects a directory and date range and receives feedback that the scan is in progress.
* Only images inside the date range are included in scoring.
* Exactly five images with the highest brightness scores are shown with thumbnails, file names, capture dates, and scores.
* Updating the date range reruns the scan and refreshes the shortlist without a page reload.
* Automated tests for filtering and scoring logic run successfully.

### Risks & Mitigations

* Missing EXIF data could exclude valid photos -> fall back to file modified time and flag when the fallback occurs.
* Large directories might slow scans -> stream progress feedback and set expectations in the UI.
* Brightness may not reflect perceived quality -> encapsulate scoring so alternative metrics can replace it with minimal changes.

### Out-of-Scope

* Cloud sync, external storage integration, or multi-user accounts.
* Export, tagging, rating, or other management features.
* Persistent storage of shortlist results beyond the current session.

### Assumptions

* Users can navigate their filesystem via a standard directory picker.
* The local machine has enough resources to scan the selected directory.
* Brightness scoring is acceptable as the initial quality proxy.

### Open questions (answer before planning)

None.

### Sources

* PhotoPrism Team. "PhotoPrism Release 240915-e1280b2fb." GitHub Releases, 2024-09-15. https://github.com/photoprism/photoprism/releases/tag/240915-e1280b2fb
* Immich Maintainers. "Immich v1.110.0." GitHub Releases, 2024-07-26. https://github.com/immich-app/immich/releases/tag/v1.110.0
* Pillow Contributors. "Pillow 11.0.0 Release." GitHub Releases, 2024-10-15. https://github.com/python-pillow/Pillow/releases/tag/11.0.0
* FastAPI Team. "FastAPI 0.115.6." GitHub Releases, 2024-12-03. https://github.com/fastapi/fastapi/releases/tag/0.115.6
* pytest Developers. "pytest 8.3.4." GitHub Releases, 2024-12-01. https://github.com/pytest-dev/pytest/releases/tag/8.3.4
