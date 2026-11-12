import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

from lxml import etree

from . import llm
from .cache import Cache
from .metrics import format_summary
from .proofreader import proofread_text
from .styleguide import load_style_guide
from .xml_scan import find_paragraphs

log = logging.getLogger("xml_proofreader")


def build_parser():
    p = argparse.ArgumentParser(
        prog="xml-proofread",
        description="Proofread the <p> elements of an XML file with Claude and wrap each error in an <error> tag.",
    )
    p.add_argument("input", type=Path, help="the XML file to proofread")
    p.add_argument("--lang", required=True, help="language tag such as en, fr or en-GB")
    p.add_argument("--style-guide", required=True, type=Path, help="the Style_Guide (.docx)")
    p.add_argument("-o", "--output", type=Path, help="where to write the result (default: INPUT.corrected.xml)")
    p.add_argument("--batch-size", type=int, default=6, help="paragraphs per request (default 6)")
    p.add_argument("--workers", type=int, default=8, help="requests sent at the same time (default 8)")
    p.add_argument("--cache-dir", type=Path, default=Path(".cache"), help="where answers are remembered")
    p.add_argument("--no-cache", action="store_true", help="do not read or write the answer cache")
    p.add_argument("-v", "--verbose", action="store_true", help="show progress messages")
    return p


def output_path(src):
    """data/input.xml -> data/input.corrected.xml (same folder)."""
    return src.with_name(f"{src.stem}.corrected{src.suffix or '.xml'}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s", stream=sys.stderr)

    # --- check everything we can before spending money on the model -------------
    if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*", args.lang):
        log.error("Invalid language tag %r (examples: en, fr, en-GB)", args.lang)
        return 2
    for path, what in ((args.input, "input file"), (args.style_guide, "Style_Guide")):
        if not path.is_file():
            log.error("The %s was not found: %s", what, path)
            return 2
    if args.batch_size < 1 or args.workers < 1:
        log.error("--batch-size and --workers must be at least 1")
        return 2
    dst = args.output or output_path(args.input)
    if dst.resolve() == args.input.resolve():
        log.error("Refusing to overwrite the input file")
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY is not set (put it in a .env file, see README)")
        return 2

    try:
        # newline="" keeps the file's own line endings (\r\n stays \r\n)
        with open(args.input, encoding="utf-8", newline="") as f:
            text = f.read()
        etree.fromstring(text.encode("utf-8"))                    # must be well-formed XML
        guide = load_style_guide(args.style_guide)
    except (etree.XMLSyntaxError, UnicodeDecodeError, ValueError, OSError) as exc:
        log.error("Cannot read the input: %s", exc)
        return 2

    start = time.perf_counter()
    try:
        cache = Cache(None if args.no_cache else args.cache_dir)
        result = proofread_text(text, args.lang, guide, cache=cache,
                                workers=args.workers, batch_size=args.batch_size)
    except Exception as exc:                                       # API down, bad key, ...
        log.error("Proofreading failed: %s", exc)
        return 1
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(result)

    elapsed = time.perf_counter() - start
    print(format_summary(args.input.name, elapsed, len(find_paragraphs(text)),
                         result.count("<error "), llm.USAGE), file=sys.stderr)
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())