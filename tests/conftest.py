import sys
from pathlib import Path

# Ensure src/ is on sys.path so tests can import photo_archivist
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
