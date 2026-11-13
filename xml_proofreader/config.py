"""Settings from config.json in the project root."""

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "config.json"
DEFAULTS = {"model": "claude-sonnet-5-5"}


def load(path=PATH):
    """The settings in `path`, with DEFAULTS for anything missing (or for a missing file)."""
    settings = dict(DEFAULTS)
    if Path(path).is_file():
        settings.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return settings


SETTINGS = load()
