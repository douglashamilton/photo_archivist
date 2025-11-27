from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .interfaces import Enumerator

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".jpe", ".jfif")


class FileEnumerator(Enumerator):
    def __init__(self, allowed_extensions: Iterable[str] = ALLOWED_EXTENSIONS):
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)

    def iter_files(self, directory: Path) -> Iterable[Path]:
        for path in directory.rglob("*"):
            if path.is_file() and self._is_allowed_extension(path):
                yield path

    def _is_allowed_extension(self, path: Path) -> bool:
        name = path.name.lower().strip()
        return any(name.endswith(ext) for ext in self.allowed_extensions)
