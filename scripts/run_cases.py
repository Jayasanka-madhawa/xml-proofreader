"""Run the proofreader and write SUMMARY.md. Settings are in scripts/script_config.json.

    python scripts/run_cases.py
    python scripts/run_cases.py tests/inputs/s7_capitalization.xml tests/inputs/general.xml
    python scripts/run_cases.py data/example_input.xml --expected data/example_output.xml
"""

import argparse
import subprocess
import sys
from datetime import datetime

from case_utils.jobs import ROOT, jobs_from_args, jobs_from_config, load_config
from case_utils.report import write_summary


def run_case(cfg, src, dst):
    return subprocess.call([
        sys.executable, "-m", "xml_proofreader", str(src),
        "--lang", cfg["lang"], "--style-guide", str(cfg["style_guide"]), "-o", str(dst), "-v",
    ], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description="Proofread the case files and write SUMMARY.md.")
    parser.add_argument("inputs", nargs="*", help="XML files to proofread (default: cases in scripts/script_config.json)")
    parser.add_argument("--expected", help="annotated XML to compare against, when one input is given")
    args = parser.parse_args()

    cfg = load_config()
    jobs = jobs_from_args(cfg, args.inputs, args.expected) if args.inputs else jobs_from_config(cfg)

    folder = cfg["output_dir"] / datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    folder.mkdir(parents=True)
    for src, _expected_path in jobs:
        rc = run_case(cfg, src, folder / f"{src.stem}.corrected.xml")
        if rc != 0:
            sys.exit(rc)
    write_summary(folder, jobs)
    print(folder / "SUMMARY.md")


if __name__ == "__main__":
    main()
