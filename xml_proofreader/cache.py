import hashlib
import json
from pathlib import Path


class Cache:
    """Stores the model's answer for a paragraph on disk, one small file per answer."""

    def __init__(self, directory=None):
        self.dir = Path(directory) if directory else None
        if self.dir:
            self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(*parts):
        """A fingerprint of everything that influences the answer."""
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    def get(self, key):
        if not self.dir:
            return None
        try:
            return json.loads((self.dir / f"{key}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None                      # missing or damaged -> treat as not cached

    def put(self, key, errors):
        if self.dir:
            (self.dir / f"{key}.json").write_text(json.dumps(errors, ensure_ascii=False), encoding="utf-8")