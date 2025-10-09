Slice Build Plan — photo archivist
Plan Overview

Objective recap: Build a desktop MVP that connects to OneDrive, curates the top 10 monthly JPG photos, presents a local review gallery, and submits approved selections to the Prodigi/Pwinty sandbox using share-link URLs.

Stack confirmation: Python 3.12 with FastAPI, SQLite via SQLAlchemy, APScheduler, MSAL, OpenCV/Pillow/ImageHash, requests; pytest/pytest-asyncio; ruff/black/mypy; pre-commit.

Current repo state: Branch work, commit 8a4e645fccf3e31749220ce87948178cb77c2d9e.

Active slice: Slice 1 — SQLite persistence bootstrap (establishing the metadata store for scans/shortlists/orders).

Prerequisites: None (no external services or secrets required).

Global Guardrails (from TDD)

Scope fence: Work inside the existing FastAPI app and new src/photo_archivist/storage/ package (db.py, models.py, __init__.py), alongside updates to config.py, app.py, pyproject.toml, and targeted tests under tests/storage/ per the defined repo map.

Quality gates: Keep ruff, black, and mypy --strict green; expand pytest coverage with tests-first workflow and maintain trajectory toward ≥85 % coverage on services/API layers.

Security & privacy: Persist metadata only (no image binaries), honour shortlist eligibility invariants, and avoid logging PII/tokens; respect least-privilege design and future encryption requirements.

Observability: Continue structured startup logging and extend it to database initialization while preserving redaction/PII-safety expectations.

Config & tooling: Use BaseSettings/.env for runtime configuration, ensure SQLite path is configurable, and keep dependencies managed via pyproject.toml/pre-commit automation.

Slice Focus

Slice ID: 1

Slice name: SQLite persistence bootstrap

Why this slice now: Future scans, shortlist management, and order submission require a durable metadata store aligned with the defined domain model; this slice lays that foundation so later services have a typed persistence layer to build upon.

Dependencies: None

Slice Execution Plans

Slice 1 — SQLite persistence bootstrap
Goal: Introduce the storage package with SQLAlchemy models for PhotoItem/ShortlistEntry/Run/Order, ensure init_db creates the schema at startup, and expose a typed session factory for later services.

Definition of done:

init_db (invoked during FastAPI startup) creates the SQLite file at the configured path and materialises tables/indexes for the four core aggregates using SQLAlchemy metadata.

A helper yields SQLAlchemy sessions scoped for tests/services, and the first persistence test passes under pytest and mypy strict mode.

Preconditions: SQLAlchemy dependency available once added; no external credentials needed.

Touch-only files: pyproject.toml, src/photo_archivist/config.py, src/photo_archivist/app.py, src/photo_archivist/storage/__init__.py, src/photo_archivist/storage/db.py, src/photo_archivist/storage/models.py, tests/storage/test_db.py, plus optional tests/storage/__init__.py if needed for package discovery.

First failing test(s):

File: tests/storage/test_db.py

Test name: test_init_db_creates_expected_tables

Failure setup: Instantiate a temporary SQLite path, call init_db/create_engine_for_path, and assert that inspector reports the four expected table names with primary keys; this fails until storage layer exists.

Copilot prompt script:

Update pyproject.toml to add SQLAlchemy (and typing extensions if needed) to main dependencies, keeping tooling blocks unchanged.

Create tests/storage/test_db.py with pytest using tmp_path to assert init_db creates PhotoItem, ShortlistEntry, Run, and Order tables, and that get_session yields a Session bound to the same engine.

Generate src/photo_archivist/storage/models.py defining SQLAlchemy Base and ORM models for PhotoItem, ShortlistEntry, Run, and Order per the TDD domain fields, including indexes/unique constraints and Enum types where specified.

Create src/photo_archivist/storage/db.py providing get_engine(path: str | Path | None = None), init_db(engine: Engine | None = None), and get_session() contextmanager returning Session, plus ensure directories are created and logging emits an event.

Add src/photo_archivist/storage/__init__.py re-exporting Base, init_db, get_engine, and get_session for consumers.

Extend src/photo_archivist/config.py with DB_PATH (Path) defaulting to photo_archivist.db and ensure BaseSettings reads from .env.

Update src/photo_archivist/app.py startup hook to call init_db() once and log storage initialisation without leaking PII.

Implementation checkpoints:

Checkpoint A: Run pytest tests/storage/test_db.py to confirm the new test fails before implementation (missing storage module).

Checkpoint B: After adding models/db helpers, the test passes and mypy reports clean types for the new modules.

Checkpoint C: Full pytest, ruff, and mypy succeed, confirming integration with existing app startup.

Verification:

Command(s):
⚠️ pytest tests/storage/test_db.py
⚠️ pytest
⚠️ ruff check .
⚠️ mypy src

Manual QA: Run uvicorn src.photo_archivist.app:app --port 8787 and confirm that launching the server creates the configured SQLite file and logs a storage.init (or similar) event without sensitive data.

Telemetry/logging: Verify startup log includes both the existing boot event and a new storage initialisation message confirming DB path, ensuring tokens/URLs are absent.

Follow-ups / debts: Document or ticket future Alembic migrations and repository/query helpers for services once behaviour is implemented in later slices.

After-shipment actions

Documentation to update: Add DB_PATH explanation and schema overview to README/architecture notes; capture schema decisions in CHANGELOG for traceability.

Deployment / release steps: None beyond ensuring local dev instructions mention automatic DB creation.

Next review trigger: Re-run this planning prompt before starting Slice 2 (likely the MSAL auth/connect contract).