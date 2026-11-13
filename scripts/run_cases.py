"""Run the proofreader and write SUMMARY.md.

    python scripts/run_cases.py
    python scripts/run_cases.py tests/inputs/s7_capitalization.xml tests/inputs/general.xml
    python scripts/run_cases.py data/example_input.xml --expected data/example_output.xml
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(__file__).resolve().parent / "cases.json"
INPUTS = ROOT / "tests" / "inputs"
EXPECTED = ROOT / "tests" / "expected"
GUIDE = ROOT / "data" / "Style_Guide.docx"


def paragraphs(path):
    return [el for el in etree.parse(str(path)).getroot().iter()
            if isinstance(el.tag, str) and etree.QName(el).localname == "p"]


def errors(paragraph):
    found = []
    for err in paragraph.iter("error"):
        parent = err.getparent()
        if parent is not None and etree.QName(parent).localname == "error":
            continue
        found.append({
            "span": "".join(err.itertext()),
            "correction": err.get("correction") or "",
            "type": err.get("type") or "",
            "reason": err.get("reason") or "",
        })
    return found


def same_change(expected, actual):
    if expected["span"] == actual["span"] and expected["correction"] == actual["correction"]:
        return True
    if expected["span"] and expected["span"] in actual["span"]:
        return actual["correction"] == actual["span"].replace(expected["span"], expected["correction"], 1)
    if actual["span"] and actual["span"] in expected["span"]:
        return expected["correction"] == expected["span"].replace(actual["span"], actual["correction"], 1)
    return False


def overlaps(a, b):
    return a == b or (a and b and (a in b or b in a))


def compare(expected_path, actual_path):
    rows = []
    expected_paras = paragraphs(expected_path)
    actual_paras = paragraphs(actual_path)
    if len(expected_paras) != len(actual_paras):
        rows.append((None, "paragraph count", {"span": str(len(expected_paras))}, {"span": str(len(actual_paras))}))
    for number, (exp_p, act_p) in enumerate(zip(expected_paras, actual_paras)):
        expected, actual = errors(exp_p), errors(act_p)
        used = [False] * len(actual)

        def take(test):
            for i, item in enumerate(actual):
                if not used[i] and test(item):
                    used[i] = True
                    return item
            return None

        for exp in expected:
            act = (take(lambda a: a["span"] == exp["span"] and a["correction"] == exp["correction"])
                   or take(lambda a: a["span"] == exp["span"])
                   or take(lambda a: overlaps(a["span"], exp["span"])))
            if act is None:
                rows.append((number, "missed", exp, None))
            elif same_change(exp, act):
                rows.append((number, "correct", exp, act))
            else:
                rows.append((number, "wrong fix", exp, act))
        for i, act in enumerate(actual):
            if not used[i]:
                rows.append((number, "extra", None, act))
    return rows


def pct(part, whole):
    return "n/a" if not whole else f"{100 * part / whole:.0f}%"


def detail_lines(name, number, kind, exp, act):
    where = "file" if number is None else f"paragraph {number}"
    lines = [f"- `{name}` {where}"]
    if kind == "paragraph count":
        lines.append(f"  - expected {exp['span']} paragraphs, output {act['span']}")
        return lines
    if exp:
        lines.append(f"  - expected `{exp['span']}` → `{exp['correction']}` ({exp['type']}; {exp['reason']})")
    if act:
        lines.append(f"  - output `{act['span']}` → `{act['correction']}` ({act['type']}; {act['reason']})")
    return lines


def write_summary(folder, jobs):
    lines = ["# Run summary", "", f"Folder: `{folder}`", "",
             "| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |",
             "|---|---|---|---|---|---|---|"]
    grouped = {kind: [] for kind in ("missed", "wrong fix", "extra", "paragraph count", "wording")}
    for src, expected_path in jobs:
        name = src.stem
        rows = compare(expected_path, folder / f"{name}.corrected.xml")
        expected = sum(1 for _, kind, _, _ in rows if kind not in ("extra", "paragraph count"))
        correct = sum(1 for _, kind, _, _ in rows if kind == "correct")
        missed = sum(1 for _, kind, _, _ in rows if kind == "missed")
        extra = sum(1 for _, kind, _, _ in rows if kind == "extra")
        paired = [row for row in rows if row[1] in ("correct", "wrong fix")]
        type_ok = sum(1 for _, _, exp, act in paired if exp["type"] == act["type"])
        reason_ok = sum(1 for _, _, exp, act in paired if exp["reason"] == act["reason"])
        lines.append(
            f"| {name} | {expected} | {correct} ({pct(correct, expected)}) | {missed} | {extra} | "
            f"{pct(type_ok, len(paired))} | {pct(reason_ok, len(paired))} |"
        )
        for number, kind, exp, act in rows:
            if kind == "correct" and exp["reason"] == act["reason"] and exp["type"] == act["type"]:
                continue
            bucket = "wording" if kind == "correct" else kind
            grouped[bucket].extend(detail_lines(name, number, kind, exp, act))
    sections = [
        ("Missed", "missed"),
        ("Wrong fix", "wrong fix"),
        ("Extra", "extra"),
        ("Paragraph count", "paragraph count"),
        ("Same fix, different wording", "wording"),
    ]
    for title, key in sections:
        lines += ["", f"## {title}", ""]
        lines += grouped[key] or ["None."]
    lines += ["", "## Performance", ""]
    for src, _expected_path in jobs:
        text = (folder / f"{src.stem}.corrected.txt").read_text(encoding="utf-8").strip()
        lines += ["```", text, "```", ""]
    (folder / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve(path):
    candidate = Path(path)
    if candidate.is_file():
        return candidate.resolve()
    under_root = ROOT / candidate
    if under_root.is_file():
        return under_root.resolve()
    return candidate


def jobs_from_config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    names = cfg.get("cases") or []
    files = sorted(INPUTS.glob("*.xml")) if not names else [INPUTS / f"{name}.xml" for name in names]
    jobs = [(path, EXPECTED / path.name) for path in files]
    missing = [f"{src.name} or {expected.name}" for src, expected in jobs
               if not src.is_file() or not expected.is_file()]
    if missing:
        sys.exit("Not found: " + ", ".join(missing))
    return cfg, jobs


def jobs_from_args(inputs, expected):
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
        expected_path = EXPECTED / f"{src.stem}.xml"
        if not expected_path.is_file():
            sys.exit(f"No expected file for {src.name}. Pass it with --expected.")
        jobs.append((src, expected_path))
    return jobs


def main():
    parser = argparse.ArgumentParser(description="Proofread the case files and write SUMMARY.md.")
    parser.add_argument("inputs", nargs="*", help="XML files to proofread (default: scripts/cases.json)")
    parser.add_argument("--expected", help="annotated XML to compare against, when one input is given")
    args = parser.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    jobs = jobs_from_args(args.inputs, args.expected) if args.inputs else jobs_from_config()[1]

    folder = ROOT / cfg.get("output_dir", "tests/outputs") / datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    folder.mkdir(parents=True)
    for src, _expected_path in jobs:
        dst = folder / f"{src.stem}.corrected.xml"
        rc = subprocess.call([
            sys.executable, "-m", "xml_proofreader", str(src),
            "--lang", "en", "--style-guide", str(GUIDE), "-o", str(dst), "-v",
        ], cwd=ROOT)
        if rc != 0:
            sys.exit(rc)
    write_summary(folder, jobs)
    print(folder / "SUMMARY.md")


if __name__ == "__main__":
    main()
