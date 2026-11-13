"""Read scripts/script_config.json and decide which inputs to run against which expected files."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "scripts" / "script_config.json"
KEYS = ("lang", "style_guide", "inputs_dir", "expected_dir", "output_dir", "cases")


def load_config():
    """The config, with every path made absolute from the project root."""
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    missing = [key for key in KEYS if key not in cfg]
    if missing:
        sys.exit(f"{CONFIG.name} is missing: " + ", ".join(missing))
    for key in ("style_guide", "inputs_dir", "expected_dir", "output_dir"):
        cfg[key] = ROOT / cfg[key]
    return cfg


def resolve(path):
    candidate = Path(path)
    if candidate.is_file():
        return candidate.resolve()
    under_root = ROOT / candidate
    if under_root.is_file():
        return under_root.resolve()
    return candidate


def jobs_from_config(cfg):
    inputs, expected = cfg["inputs_dir"], cfg["expected_dir"]
    names = cfg["cases"]
    files = sorted(inputs.glob("*.xml")) if not names else [inputs / f"{name}.xml" for name in names]
    jobs = [(path, expected / path.name) for path in files]
    missing = [f"{src.name} or {exp.name}" for src, exp in jobs
               if not src.is_file() or not exp.is_file()]
    if missing:
        sys.exit("Not found: " + ", ".join(missing))
    return jobs


def jobs_from_args(cfg, inputs, expected):
    sources = [resolve(path) for path in inputs]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        sys.exit("Not found: " + ", ".join(missing))
    if expected is not None:
        if len(sources) != 1:
            sys.exit("--expected can be used with one input file")
        expected_path = resolve(expected)
        if not expected_path.is_file():
            sys.exit(f"Not found: {expected}")
        return [(sources[0], expected_path)]
    jobs = []
    for src in sources:
        expected_path = cfg["expected_dir"] / f"{src.stem}.xml"
        if not expected_path.is_file():
            sys.exit(f"No expected file for {src.name}. Pass it with --expected.")
        jobs.append((src, expected_path))
    return jobs
