# PHOTO_ARCHIVIST

Quick start and developer setup instructions (PowerShell)

## Requirements
- Python 3.12

## Quick start (PowerShell)
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
```

2. Install the project in editable mode with developer extras (recommended):

```powershell
pip install -e .[dev]
```

If your environment or build backend doesn't support installing extras from `pyproject.toml`, install packages directly:

```powershell
pip install "fastapi" "uvicorn[standard]" "pydantic" "pydantic-settings" "python-dotenv"
pip install pytest pytest-asyncio httpx ruff black mypy types-requests pre-commit
```

3. Install and enable pre-commit hooks:

```powershell
pre-commit install
```

4. Run tests:

```powershell
pytest -q
```

5. Run the development server (from project root):

```powershell
uvicorn src.photo_archivist.app:app --host 127.0.0.1 --port 8787 --reload
```

6. View the health endpoint in your browser or from PowerShell:

Open in default browser:

```powershell
Start-Process "http://127.0.0.1:8787/health"
```

Or fetch JSON from PowerShell using Invoke-RestMethod:

```powershell
Invoke-RestMethod "http://127.0.0.1:8787/health"
```

Notes
- To stop the server, press Ctrl+C in the terminal running uvicorn.
- If you get import errors like `ModuleNotFoundError: No module named 'src'`, run uvicorn from the project root (so `src/` is on sys.path) or install the package in editable mode (`pip install -e .`).
- To update the reported version, set `VERSION` in a `.env` file at the project root and restart the server (the app uses pydantic-settings to read `.env`).
