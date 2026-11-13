# xml-proofreader

A command-line tool that proofreads the `<p>` elements of an XML file with
Claude and wraps each error in an `<error>` tag:

```xml
<p>My name is <error type="capitalization" correction="John" reason="Proper nouns are capitalized">john</error>.</p>
```

It checks grammar, spelling, punctuation, capitalization, clarity, and the
rules of a style guide given as a `.docx` file. Error types are `grammar`,
`spelling`, `punctuation`, `capitalization`, `clarity` and `styleguide`, and
every error has a short `reason`.

Only the error spans change. Text outside `<p>`, other tags, attributes,
namespaces, comments, CDATA and line endings are kept exactly. Paragraphs with
no errors come back identical to the input, and each paragraph's text without
the `<error>` tags is checked to be identical to the original.

## Setup

Requires Python 3.11 or newer and an Anthropic API key.

```bash
conda create -n xmlproofreader python=3.11
conda activate xmlproofreader
pip install -r requirements.txt
```

Put your API key in a `.env` file in the project root:

```bash
cp .env.example .env
# then edit .env:
ANTHROPIC_API_KEY=your-key-here
```

## Usage

```bash
python -m xml_proofreader data/example_input.xml --lang en --style-guide data/Style_Guide.docx -v
```

| Option | Meaning |
|---|---|
| `INPUT` | The XML file to proofread |
| `--lang` | Language tag in BCP-47 form, such as `en`, `fr` or `en-GB` (required) |
| `--style-guide` | The style guide `.docx` (required) |
| `-o`, `--output` | Write the result to this exact path |
| `--output-dir` | Write `DIR/<name>.corrected.<time>.xml`, so earlier runs are kept |
| `--batch-size` | Paragraphs per request (default 6) |
| `--workers` | Requests sent at the same time (default 8) |
| `--cache-dir` | Where answers are remembered (default `.cache`) |
| `--no-cache` | Do not read or write the answer cache |
| `-v`, `--verbose` | Show progress messages |

### Output

By default the result is written beside the input with a `.corrected.xml`
suffix: `data/example_input.xml` becomes `data/example_input.corrected.xml`.
Running again replaces that file.

To keep every run, use `--output-dir`. Each run then gets its own file with
the time in its name, and nothing is overwritten:

```bash
python -m xml_proofreader data/example_input.xml --lang en --style-guide data/Style_Guide.docx \
  --output-dir outputs
# -> outputs/example_input.corrected.2026-11-14T00-59-57.xml
```

The tool refuses to write over the input file.

### Performance summary

Each run prints a summary and saves the same text next to the output, with a
`.txt` extension:

```
--- Performance summary for example_input.xml ---
  time         : 3.75s
  peak memory  : 92.3 MiB
  paragraphs   : 4
  errors tagged: 10
  model calls  : 1 (325 tokens in, 573 out, 5389 read from prompt cache)
```

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Proofreading failed (for example, the API key was rejected) |
| 2 | Bad input: missing file, invalid `--lang`, malformed XML, missing API key, or output path equal to the input |

## How it works

1. Read the style guide `.docx` as plain text.
2. Find every `<p>` in document order, including nested ones. A `<p>` inside a
   comment or CDATA is not a paragraph.
3. Send paragraphs to Claude in batches, several batches in parallel. The
   style guide is sent with prompt caching, so later requests reuse it.
   Identical paragraphs are sent once.
4. Claude returns a structured list of errors for each paragraph. Each error
   is placed only if its text is found exactly in the paragraph.
5. Insert the `<error>` tags and check that every paragraph's text is
   unchanged. A paragraph that fails the check is written without its edits.
6. Write the result and the performance summary.

Failed model calls are retried, then sent one paragraph at a time. A paragraph
that still fails is left unchanged.

Answers are cached on disk in `.cache/`. The cache key includes the prompt
version, the model, the language, the style guide and the paragraph text, so a
rerun of unchanged text makes no model calls. Use `--no-cache` to force fresh
answers.

## Project layout

```
xml_proofreader/   the tool
  cli.py           command-line options, checks, output path
  proofreader.py   batching, parallel requests, cache, retries
  llm.py           the Claude request
  prompts.py       the instructions sent to Claude
  xml_scan.py      finding <p> elements and applying edits
  annotate.py      placing errors and building <error> tags
  verify.py        the text-unchanged check
  styleguide.py    reading the .docx style guide
  cache.py         the on-disk answer cache
  metrics.py       the performance summary
tests/
  unit/            unit tests (fake model, no API key needed)
  inputs/          proofreading cases
  expected/        hand-annotated answers for those cases
scripts/
  run_cases.py     runs the cases and writes SUMMARY.md
  script_config.json  cases to run, language, style guide and folders
  case_utils/
    jobs.py        reading the config, choosing inputs and expected files
    compare.py     matching output errors against expected errors
    report.py      writing SUMMARY.md
data/              style guide and the provided example files
docs/
  COVERAGE.md      what each test and case covers
  FIXES.md         accuracy fixes and results after each one
```

## Tests

Unit tests use a fake model, so they are free and need no API key:

```bash
python -m pytest tests -q
```

Proofreading cases call the real model and compare each result with
`tests/expected/<name>.xml`:

```bash
python scripts/run_cases.py                                  # every case in scripts/script_config.json
python scripts/run_cases.py tests/inputs/s7_capitalization.xml
python scripts/run_cases.py data/example_input.xml --expected data/example_output.xml
```

Results go to `tests/outputs/<time>/`, with a `SUMMARY.md` that lists missed,
wrong and extra errors for each case. On the latest run the tool found 231 of
236 expected errors (98%). See `docs/COVERAGE.md` and `docs/FIXES.md`.
