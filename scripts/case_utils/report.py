"""Write SUMMARY.md for a folder of corrected case files."""

from .compare import compare


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
