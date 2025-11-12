# Slice 3: Generate thumbnails for shortlist

## Context
- PRD section / link: docs/prd.md (Must-Have Features: Automatic selection and display of the five highest-scoring thumbnails)
- TDD component / link: docs/tdd.md (Interfaces: Thumbnail streaming endpoint; Data flow: thumbnail generation cached per scan)
- Current state summary (1-2 sentences). Shortlist results expose filenames/metadata only; no thumbnails are generated or served, so the UI cannot show image previews.

## Tasks
- [ ] Extend scan results to include per-photo identifiers and thumbnail metadata so downstream routes/templates can reference generated files.
- [ ] Implement thumbnail generation for the top five results, caching JPEG thumbnails (max 256px) in a per-scan temp directory with predictable filenames.
- [ ] Add a FastAPI route to stream cached thumbnails and update the shortlist template to render `<img>` tags for each photo.
- [ ] Update automated tests to cover thumbnail creation, endpoint behaviour, and template rendering fallbacks.

## Tests & Validation
- Automated: `pytest`
- Manual check: Run `uvicorn app.main:app --reload`, trigger a scan against a directory with sample JPEGs, and confirm each shortlist entry displays its thumbnail image in the browser.

## Decisions & Follow-ups
- Defer cache eviction/cleanup policies to a later slice; current implementation stores thumbnails in temp space for the app lifetime.
- Consider expanding progress reporting to include thumbnail generation status once basic previews are in place.

