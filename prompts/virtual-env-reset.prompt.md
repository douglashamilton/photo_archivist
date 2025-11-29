# Virtual environment reset (Windows host + WSL)

Use this prompt in VS Code's Codex/Continue chat to recreate clean, in-sync virtual environments for both Windows and WSL.

## Goals
- Delete any stale `.venv` or `.venv-wsl` directories so neither points at the wrong interpreter.
- Rebuild Windows `.venv` with the Windows Python 3.12 interpreter.
- Rebuild WSL `.venv-wsl` with the Linux Python 3.12 interpreter.
- Install identical dependencies into both environments from `requirements.txt` to match `pyproject.toml`.
- Point VS Code at the Windows `.venv` interpreter and keep `requirements.txt` updated when dependencies change.

## Prompt
"""
You are running inside VS Code. Clean up and recreate the Python virtual environments for this workspace:

1) Open an integrated terminal at the repository root.
2) Remove any existing `.venv` and `.venv-wsl` folders to clear incorrect interpreter links.
3) Create a fresh Windows environment: `py -3.12 -m venv .venv`.
4) Create a fresh WSL environment (from the WSL terminal): `python3 -m venv .venv-wsl`.
5) For each environment, activate it and run `python -m pip install --upgrade pip` followed by `python -m pip install -r requirements.txt`.
   - Windows activation: `.venv\\Scripts\\activate`
   - WSL activation: `source .venv-wsl/bin/activate`
6) In VS Code, set the Python interpreter to `.venv\\Scripts\\python.exe` so tooling uses the Windows environment by default.
7) Confirm `requirements.txt` stays aligned with `pyproject.toml` whenever dependencies change.

Share the terminal output once finished.
"""
