import sys
from pathlib import Path

# Ensure both project root and src/ are on sys.path so tests can import packages
ROOT_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT_PATH / "src"
for path in (ROOT_PATH, SRC_PATH):
    as_str = str(path)
    if as_str not in sys.path:
        sys.path.insert(0, as_str)
