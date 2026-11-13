# xml-proofreader

A command-line tool that proofreads the `<p>` elements of an XML file with
Claude, wraps every error in an `<error>` tag, and guarantees that the text of
each paragraph is otherwise unchanged.

Input:

```xml
<p>My name is john and the firm earned $2,000,000 in January, 2024.</p>
```

Output (one line in the real file, wrapped here to fit):

```xml
<p>My name is <error type="capitalization" correction="John" reason="Proper nouns are capitalized">john</error>
and the firm earned <error type="styleguide" correction="$2 million" reason="Spell out million, billion, etc.">$2,000,000</error>
in <error type="styleguide" correction="January 2024" reason="No comma between month and year">January, 2024</error>.</p>
```

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output](#output)
- [How it works](#how-it-works)
- [Performance](#performance)
- [Error handling](#error-handling)
- [Testing and evaluation](#testing-and-evaluation)
- [Project layout](#project-layout)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

## Features

- **Error categories:** `grammar`, `spelling`, `punctuation`, `capitalization`,
  `clarity` and `styleguide`.
- **Style guide rules:** read from a `.docx` file, covering dates, numbers, time,
  hyphenation, quotations, capitalization and preferred word usage.
- **A reason on every error:** a short `reason` attribute names the rule that was
  broken. For `styleguide` errors it names the style guide rule.
- **Text is never changed:** only `<error>` tags are added. Tags outside `<p>`,
  attributes, namespaces, comments, CDATA, entities and line endings are kept
  exactly. A paragraph with no errors comes back identical to the input.
- **Checked output:** the text of every paragraph, without the `<error>` tags, is
  compared with the original. A paragraph that fails is written without its edits.
- **Locale aware:** `--lang` (BCP-47, such as `en`, `en-GB` or `fr`) sets the
  language the text is proofread in.
- **Fast:** paragraphs are batched and sent in parallel, the style guide is reused
  through prompt caching, and answers are cached on disk.
- **Performance log:** each run prints and saves the time, peak memory, paragraph
  count, error count and token use.

## Requirements

- Python 3.11 or newer
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))
- Packages in `requirements.txt`: `anthropic`, `lxml`, `python-docx`,
  `python-dotenv`, and `pytest` for the tests

## Setup

### 1. Get the code

```bash
git clone https://github.com/Jayasanka-madhawa/xml-proofreader.git
cd xml-proofreader
```

### 2. Create an environment and install the packages

With conda:

```bash
conda create -n xmlproofreader python=3.11 -y
conda activate xmlproofreader
pip install -r requirements.txt
```

Or with the built-in `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your API key

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder with your key:

```
ANTHROPIC_API_KEY=your-key-here
```

`.env` is ignored by git, so the key is never committed.

### 4. Check that it works

```bash
python -m pytest tests -q
python -m xml_proofreader data/example_input.xml --lang en --style-guide data/Style_Guide.docx -v
```

The tests need no API key. The second command writes
`data/example_input.corrected.xml` and prints a performance summary.

## Configuration

The Claude model is set in `config.json` in the project root:

```json
{
  "model": "claude-sonnet-5-5"
}
```

Change the name there to use another Claude model. If the file is missing, the
tool uses `claude-sonnet-5-5`. The model is part of the cache key, so a new
model always gets fresh answers.

Other settings are command-line options (see [Usage](#usage)).

## Usage

```bash
python -m xml_proofreader INPUT --lang LANG --style-guide GUIDE.docx [options]
```

Example:

```bash
python -m xml_proofreader data/example_input.xml --lang en --style-guide data/Style_Guide.docx -v
```

| Option | Meaning |
|---|---|
| `INPUT` | The XML file to proofread |
| `--lang` | Language tag in BCP-47 form, such as `en`, `fr` or `en-GB` (required) |
| `--style-guide` | The style guide `.docx` (required) |
| `-o`, `--output` | Write the result to this exact path |
| `--output-dir DIR` | Write `DIR/<name>.corrected.<time>.xml`, so earlier runs are kept |
| `--batch-size` | Paragraphs per request (default 6) |
| `--workers` | Requests sent at the same time (default 8) |
| `--cache-dir` | Where answers are remembered (default `.cache`) |
| `--no-cache` | Do not read or write the answer cache |
| `-v`, `--verbose` | Show progress messages |

`-o` and `--output-dir` cannot be used together. Run
`python -m xml_proofreader --help` for the full list.

## Output

### The corrected file

By default the result is written beside the input with a `.corrected.xml`
suffix: `data/example_input.xml` becomes `data/example_input.corrected.xml`.
Running again replaces that file.

To keep every run, use `--output-dir`. Each run gets its own file with the time
in its name, and nothing is overwritten:

```bash
python -m xml_proofreader data/example_input.xml --lang en --style-guide data/Style_Guide.docx \
  --output-dir outputs
# -> outputs/example_input.corrected.2026-11-14T00-59-57.xml
```

The tool refuses to write over the input file.

### The `<error>` tag

```xml
<error type="CATEGORY" correction="CORRECTED TEXT" reason="SHORT REASON">original text</error>
```

- `type` is one of `grammar`, `spelling`, `punctuation`, `capitalization`,
  `clarity` or `styleguide`.
- `correction` is the text that should replace the wrapped text.
- `reason` is a few words naming the broken rule.

The wrapped text is always copied exactly from the input. For a missing
character, such as a missing comma, the neighbouring word is wrapped and the
correction shows it with the comma added.

### The performance summary

Each run prints a summary to the terminal and saves the same text beside the
output, with a `.txt` extension (for example `data/example_input.corrected.txt`):

```
--- Performance summary for example_input.xml ---
  time         : 4.04s
  peak memory  : 93.9 MiB
  paragraphs   : 4
  errors tagged: 10
  model calls  : 1 (5714 tokens in, 576 out, 0 read from prompt cache)
```

## How it works

1. **Read the style guide.** The `.docx` is read as plain text.
2. **Find the paragraphs.** Every `<p>` is found in document order, including
   nested ones. A `<p>` inside a comment or CDATA is not a paragraph, and other
   elements such as `<heading>` are left alone.
3. **Ask Claude.** Paragraphs are sent in batches of 6, up to 8 batches at the
   same time. The style guide is part of the system prompt and is marked for
   prompt caching, so later requests reuse it. Identical paragraphs are sent once.
4. **Get a structured answer.** Claude answers through a tool with a fixed JSON
   schema. Each error gives the exact wrong text, a few characters before it (to
   tell repeated words apart), the type, the correction and the reason.
5. **Place the errors safely.** An error is used only if its text is found exactly
   in the paragraph. Unknown types, empty or unchanged corrections, and errors
   that overlap another error are dropped.
6. **Insert the tags and verify.** The `<error>` tags are added as text edits, so
   everything else in the file stays byte for byte the same. Each paragraph's
   text, without the tags, is then compared with the original, and a paragraph
   that differs is written without its edits.
7. **Write the result** and the performance summary.

The instructions sent to Claude are in `xml_proofreader/prompts.py`.

## Performance

| Technique | Effect |
|---|---|
| Batching | 6 paragraphs per request instead of one request per paragraph |
| Parallel requests | Up to 8 batches at once, so a file takes about as long as its slowest batch |
| Prompt caching | The style guide is sent once and then read from Anthropic's cache |
| Duplicate paragraphs | Identical paragraphs are sent once |
| Answer cache | A rerun of unchanged text makes no model calls and finishes in under a second |

On the test files (4 to 36 paragraphs each), a run with model calls takes about
3.5 to 7.5 seconds and about 92 to 96 MiB of memory. Most of the time is spent
waiting for the model, and memory does not grow with the file size.

The answer cache is in `.cache/`. Its key includes the prompt version, the model,
the language, the style guide and the paragraph text, so a change to any of them
gets a fresh answer. Use `--no-cache` to ignore it.

## Error handling

Everything that can be checked is checked before any request is sent.

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | Proofreading failed, for example because the API key was rejected |
| 2 | Bad input: missing file, invalid `--lang`, malformed XML, an empty style guide, a missing API key, or an output path equal to the input |

- **Failed requests are retried.** A failed batch is retried, then sent one
  paragraph at a time with a short wait. A paragraph that still fails is left
  unchanged and logged.
- **No retry when it cannot help.** A rejected API key or an invalid request
  stops the run straight away with exit code 1.
- **Skipped paragraphs are retried.** If Claude leaves out a paragraph, it is
  sent again on its own.
- **Logs go to stderr.** Warnings and errors are always shown. Use `-v` to also
  see progress.

## Testing and evaluation

### Unit tests

30 unit tests check the code with a fake model, so they are free, take about a
second, and need no API key:

```bash
python -m pytest tests -q
```

| File | What it checks |
|---|---|
| `test_scan.py` | Finding `<p>`: comments, CDATA, nesting, namespaces, headings |
| `test_annotate.py` | Choosing the right copy of a repeated word |
| `test_verify.py` | The text-unchanged check, with the official example files |
| `test_proofreader.py` | Batching, duplicates, the answer cache, retries, parallel requests |
| `test_cli.py` | Output paths, line endings, the performance summary, exit codes |
| `test_styleguide.py` | Reading the `.docx` and its fingerprint |
| `test_config.py` | Reading the model from `config.json` |

`docs/COVERAGE.md` lists every test and the data it uses.

### Accuracy cases

Accuracy is measured on 10 cases. Each case is an input in `tests/inputs/` and a
hand-annotated answer in `tests/expected/`:

| Case | What it tests |
|---|---|
| `s1_dates_time` | Style guide: dates and times |
| `s2_numbers_money` | Style guide: numbers and currency |
| `s3_hyphenation` | Style guide: hyphenated words |
| `s4_wordlist_a_h`, `s5_wordlist_i_z` | Style guide: the preferred word usage list |
| `s6_exceptions_quotes` | Style guide: commonly confused words, quotations, exceptions |
| `s7_capitalization` | Capitalization in prose written in lowercase |
| `general` | Spelling, grammar, punctuation and capitalization |
| `sample_input` | The provided sample file |
| `example_input` | The provided example, compared with `data/example_output.xml` |

Every case also contains correct text that must not be flagged, to catch false
alarms. Apart from `data/example_output.xml`, the expected files were written by
hand for this project.

Run them with:

```bash
python scripts/run_cases.py                                   # every case in the config
python scripts/run_cases.py tests/inputs/general.xml          # one case
python scripts/run_cases.py data/example_input.xml --expected data/example_output.xml
```

The cases to run, the language, the style guide and the folders are set in
`scripts/script_config.json`. Each run writes the corrected files and a
`SUMMARY.md` to `tests/outputs/<time>/`.

### How a result is scored

Each expected error is matched with an error in the output, in the same
paragraph:

| Result | Meaning |
|---|---|
| Correct fix | The output makes the same change. A wider or narrower tag still counts if it gives the same corrected text, for example `January, 2024` → `January 2024` versus `, 2024` → ` 2024`. |
| Wrong fix | The output tags the same text but corrects it differently. |
| Missed | No output error covers the expected one. |
| Extra | The output flags something the expected file does not. |

`SUMMARY.md` lists every missed, wrong and extra error, separately from fixes
that are correct but worded differently. It also reports how often the `type`
matches, and how often the `reason` uses exactly the same words. Reasons are
usually right but phrased differently, so that last number is low by design.

### Results

Latest full run (`tests/outputs/2026-11-14T00-59-57`):

| Case | Expected | Correct fix | Missed | Extra | Type matches |
|---|---|---|---|---|---|
| s1_dates_time | 31 | 31 (100%) | 0 | 0 | 97% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 2 | 100% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 69% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 2 | 100% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 44% |
| s7_capitalization | 26 | 23 (88%) | 2 | 0 | 100% |
| general | 15 | 14 (93%) | 0 | 0 | 100% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 91% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% |
| **Total** | **236** | **231 (98%)** | **3** | **7** | |

The 5 errors not counted as correct are 3 misses and 2 wrong fixes. Most of them,
and most of the extras, are judgement calls where the style guide and the
expected file can reasonably disagree, such as whether `5 percent` is spelled out
or whether `vs.` stays in a case name. Each one is listed in `docs/FIXES.md`.

### How accuracy was improved

The prompt was improved one change at a time. After each change every case was
run again, and a change was kept only if it helped. Total accuracy went from
215 of 239 (90%) to 231 of 236 (98%).

| Fix | Effect |
|---|---|
| Capitalize prose written in lowercase | Sentence starts, `I`, names and months are tagged |
| Ignore a `<p>` inside a comment | Good tags were no longer removed by the text check; `s7` went from 14 to 23 of 26 |
| Stop shortening acceptable stock phrases | Removed false alarms such as `Moving forward` → `Going forward` |
| Make only the change the rule requires | `9am` becomes `9 a.m.`, not `9:00 a.m.`; `s1` reached 31 of 31 |
| Tag a title and a surname separately | `president lincoln` gives two errors, as in the expected file |

`docs/FIXES.md` describes each fix with the failing example, the change, and the
full before-and-after results.

## Project layout

```
xml-proofreader/
├── config.json            the Claude model
├── requirements.txt
├── .env.example           template for the API key
├── xml_proofreader/       the tool
│   ├── __main__.py        entry point for python -m xml_proofreader
│   ├── cli.py             command-line options, input checks, output path
│   ├── config.py          reading config.json
│   ├── proofreader.py     batching, parallel requests, answer cache, retries
│   ├── llm.py             the Claude request and token counts
│   ├── prompts.py         the instructions and answer schema sent to Claude
│   ├── xml_scan.py        finding <p> elements and applying edits
│   ├── annotate.py        placing errors and building <error> tags
│   ├── verify.py          the text-unchanged check
│   ├── styleguide.py      reading the .docx style guide
│   ├── cache.py           the on-disk answer cache
│   └── metrics.py         the performance summary
├── tests/
│   ├── unit/              unit tests (fake model, no API key needed)
│   ├── inputs/            accuracy case inputs
│   └── expected/          hand-annotated answers for those cases
├── scripts/
│   ├── run_cases.py       runs the accuracy cases and writes SUMMARY.md
│   ├── script_config.json cases to run, language, style guide and folders
│   └── case_utils/
│       ├── jobs.py        reading the config, choosing inputs and expected files
│       ├── compare.py     matching output errors against expected errors
│       └── report.py      writing SUMMARY.md
├── data/                  the style guide and the provided example files
└── docs/
    ├── COVERAGE.md        what every test and case covers
    └── FIXES.md           accuracy fixes, with results before and after each
```

## Known limitations

- **Only `<p>` is proofread.** Headings and other elements are left unchanged,
  as the assignment asks.
- **Accuracy is measured for English only.** `--lang` changes the language the
  model proofreads in, but every accuracy case uses `--lang en`.
- **Results can vary slightly between runs**, because the model may answer the
  same paragraph a little differently. The answer cache keeps repeated runs the
  same.
- **Some style guide rules are judgement calls.** The remaining misses and extras
  are listed in `docs/FIXES.md`.
- **A suggestion is dropped if its text is not found exactly** in the paragraph,
  so an error the model copies wrongly is lost rather than misplaced.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ANTHROPIC_API_KEY is not set` | Create `.env` from `.env.example` and add your key |
| Exit code 1 with `Proofreading failed` | Check that the API key is valid |
| `Giving up on paragraph ...` and the output has no errors | The requests are failing: check the network and that the model in `config.json` exists |
| `ModuleNotFoundError` | Activate the environment and run `pip install -r requirements.txt` |
| `Cannot read the input` | The XML is malformed, or the style guide is empty |
| The result did not change after editing the prompt | Bump `PROMPT_VERSION` in `prompts.py`, or run with `--no-cache` |
| Zero model calls in the summary | The answers came from the cache; use `--no-cache` to call the model |
