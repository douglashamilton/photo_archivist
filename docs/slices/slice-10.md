# Slice 10: Quality filter, dedupe, and aesthetic ranking

## Context
- PRD section / link: Must-Have shortlist quality signal expansion (docs/prd.md Bottom line, Must-Have Features, Data Considerations).
- TDD component / link: Scan pipeline composition and ScoringEngine design (docs/tdd.md Architecture Overview, Scan pipeline composition).
- Current state summary (1–2 sentences).
  - Scanner emits brightness-only scores into a shortlist without quality gating or deduplication, leaving blurry/dark frames and near-duplicates in the top 5 and lacking an aesthetic model hook.

## Tasks
- [x] Update PRD/TDD to capture the cheap quality filter, phash dedupe, and aesthetic scoring flow plus dependencies.
- [x] Extend scanner pipeline with fast quality gates (brightness/contrast/blur/resolution/aspect), metrics capture, and pass-through debug values.
- [x] Add perceptual hash clustering with per-burst retention rules and tie-breaking via cheap metrics.
- [x] Introduce aesthetic scoring (configurable model, cached by file hash), integrate into selection ordering, and expose metrics in API/UI.
- [x] Refresh shortlist template to surface key metrics and states (dropped, soft, cluster info) and wire any new configuration defaults.
- [x] Expand automated tests for quality gating, dedupe, and aesthetic scoring hooks; document manual verification and update build log.

## Tests & Validation
- Automated: `python -m pytest` (scanner pipeline, clustering/dedupe rules, API shortlist payloads, template rendering).
- Manual check: Run a scan on a folder with sharp/blurred, bright/dim, and duplicate-like photos; confirm low-quality frames are dropped/flagged, near-duplicates cluster with only top picks kept, and shortlist ordered by aesthetic score with cheap metrics visible.

## Decisions & Follow-ups
- Decisions.
  - Default aesthetic backend points at a LAION/AVA head via Hugging Face with a cached stub fallback when disabled or unavailable.
  - Quality gates enforce brightness/contrast/blur/resolution/aspect thresholds before dedupe; clusters keep up to two shots with sharpness-first tie-breaks.
- Deferred work or dependency.
  - Add CLIP embedding-based clustering for finer dedupe and balance people/scenery in a later slice.
