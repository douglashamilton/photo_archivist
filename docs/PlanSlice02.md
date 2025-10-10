### Slice Build Plan - Photo Archivist

0) Plan Overview

* Objective recap: Build a desktop MVP that connects to OneDrive, curates the top 10 monthly JPG photos, renders a local review gallery, and submits approved selections to the Prodigi/Pwinty sandbox using share-link URLs.
* Stack confirmation: Python 3.12, FastAPI, SQLite/SQLAlchemy, APScheduler, MSAL, requests, OpenCV, Pillow, ImageHash, cryptography (Fernet) + keyring, pytest + responses, ruff/black/mypy.
* Current repo state: main @ 7e6a1d4ebf38dec2964057b13feb76e59f7fd915.
* Active slice: Slice 2 - Auth connect handshake.
* Prerequisites: Azure AD app registration values (client ID, tenant, redirect URI, scopes) documented; keyring backend accessible on developer machines; Slice 1 storage bootstrap merged and passing.

1) Global Guardrails (from TDD)

* Scope fence: Work within src/photo_archivist/app.py, src/photo_archivist/config.py, src/photo_archivist/schemas.py, new src/photo_archivist/auth/* and src/photo_archivist/utils/crypto.py, plus targeted tests under tests/api/ and tests/auth/; avoid touching other domains without a design change request.
* Quality gates: Keep pytest (including new tests) green, preserve ruff/black/mypy --strict compliance, and rely on deterministic mocks (no live Graph calls) to uphold the tests-first workflow.
* Security & privacy: Never log access or refresh tokens or share URLs; encrypt cached tokens with Fernet using a key stored in the OS keyring; honour least-privilege Graph scopes.
* Observability: Emit structured logs for auth connect attempts (event names, flow, outcome) with sensitive fields redacted; reuse existing logging patterns.
* Config & tooling: Extend Settings/.env.example for Graph/MSAL configuration, update pyproject dependencies explicitly, and keep pre-commit automation consistent.

2) Slice Focus

* Slice ID: 2
* Slice name: Auth connect handshake
* Why this slice now: A secure token acquisition path is required before delta scans or gallery endpoints; this slice unlocks Microsoft Graph access for subsequent work.
* Dependencies: Storage bootstrap (Slice 1) completed; Azure app registration details confirmed; no outstanding schema tasks.

3) Slice Execution Plans

#### Slice 2 - Auth connect handshake

* **Goal:** Deliver a `/api/auth/connect` endpoint backed by an MSAL client that acquires tokens (PKCE or device code), persists them encrypted, and reports connected status.
* **Definition of done:**
  * `POST /api/auth/connect` (with `{"flow":"device_code"}` or default PKCE) returns 200 and triggers MSAL to cache tokens encrypted on disk via a keyring-backed Fernet helper.
  * Subsequent calls detect existing cached refresh tokens and respond with `{"status":"already_connected"}` without re-running the flow.
* **Preconditions:** Azure registration values (client ID, tenant ID, redirect URI, scopes) populated in `.env`; msal/cryptography/keyring packages installed; developer machines can access the OS keyring or a configured fallback for tests.
* **Touch-only files:** pyproject.toml, .env.example, src/photo_archivist/config.py, src/photo_archivist/app.py, src/photo_archivist/schemas.py, src/photo_archivist/auth/__init__.py, src/photo_archivist/auth/msal_client.py, src/photo_archivist/utils/__init__.py (if needed), src/photo_archivist/utils/crypto.py, tests/api/test_auth_connect.py, tests/auth/test_msal_client.py, tests/conftest.py (only if new fixtures are required).
* **First failing test(s):**
  * File: `tests/api/test_auth_connect.py`
  * Test name: `test_auth_connect_device_flow_encrypts_cache_and_returns_connected`
  * Failure setup: Use FastAPI TestClient, patch `photo_archivist.auth.msal_client.MSALClient` with a stub that records `begin_device_flow` calls and writes a fake token payload; POST to `/api/auth/connect` with `{"flow": "device_code"}` and assert a 200 response with `{"status": "connected"}` plus confirmation that the stub invoked the encryption helper. This fails until the endpoint, schemas, and MSAL client wiring exist.
* **Copilot prompt script:**
  1. `Create tests/api/test_auth_connect.py with a FastAPI TestClient test for /api/auth/connect covering device_code success and unsupported flow error, using monkeypatched MSALClient and temporary cache fixtures.`
  2. `Draft tests/auth/test_msal_client.py asserting MSALClient encrypts/decrypts via Fernet+keyring helpers and respects cached tokens using a fake PublicClientApplication.`
  3. `Generate src/photo_archivist/utils/crypto.py providing get_or_create_fernet_key(key_name), encrypt_bytes, and decrypt_bytes leveraging keyring for key storage.`
  4. `Implement src/photo_archivist/auth/msal_client.py with MSALClient wrapping msal.PublicClientApplication, SerializableTokenCache encryption, and device code plus PKCE flow orchestration.`
  5. `Update src/photo_archivist/schemas.py with AuthConnectRequest/AuthConnectResponse models, extend config.Settings with Graph/MSAL fields, and wire the /api/auth/connect route in app.py using dependency injection.`
  6. `Adjust pyproject.toml and .env.example for new dependencies and settings, ensuring __init__.py re-exports MSALClient for imports.`
* **Implementation checkpoints:**
  * Checkpoint A: New auth endpoint test fails because the route and MSAL client scaffolding are absent.
  * Checkpoint B: After implementing MSALClient and crypto helpers, unit tests for auth utilities pass and encryption round-trip is verified.
  * Checkpoint C: Full suite (`pytest`, `ruff`, `black --check`, `mypy`) passes and manual POST to `/api/auth/connect` logs `auth.connect.success` without leaking secrets.
* **Verification:**
  * Command(s): `pytest tests/api/test_auth_connect.py tests/auth/test_msal_client.py`, `pytest`, `ruff check .`, `black --check .`, `mypy src`.
  * Manual QA: Run `uvicorn src.photo_archivist.app:app --reload`, POST to `/api/auth/connect` (device code flow using mock/test mode or real credentials) and confirm console messaging plus encrypted cache file creation; rerun endpoint to observe `already_connected` response.
  * Telemetry/logging: Ensure logs emit events like `auth.connect.start`, `auth.connect.success`, and `auth.connect.cached` with flow names only; failure paths should log `auth.connect.error` with sanitized reasons.
* **Follow-ups / debts:** Document token cache path and rotation, add a disconnect/revoke endpoint, and capture work to expose device-code instructions in the forthcoming web UI slice.

4) After-shipment actions

* Documentation to update: README auth setup, `.env.example` instructions, and architecture notes for token storage.
* Deployment / release steps: None beyond installing updated dependencies; remind the team to run dependency sync.
* Next review trigger: Re-run this planning prompt before starting Slice 3 (likely scan service bootstrap).
