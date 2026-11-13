# Test coverage

The project has two kinds of tests:

- **Unit tests** (`tests/unit/`) check the code with a fake model. They are
  free, run in about a second, and need no API key.
- **Proofreading cases** (`tests/inputs/` and `tests/expected/`) send real XML
  to Claude and compare the result with a hand-annotated answer.

```bash
python -m pytest tests -q          # unit tests
python scripts/run_cases.py        # every case listed in scripts/cases.json
```

## Unit tests

27 tests in six files, one file per module.

### `test_scan.py` - finding `<p>` elements (`xml_scan.py`)

| Test | Data | Checks |
|---|---|---|
| `test_paragraph_inside_a_comment_is_ignored` | `<!-- only <p>, not a paragraph --><p>real</p>` | A `<p>` inside a comment is not a paragraph |
| `test_paragraph_inside_cdata_is_kept_as_text` | `<p><![CDATA[keep <p> this]]></p>` | CDATA is kept as text, and the `<p>` inside it is not a paragraph |
| `test_nested_paragraphs_are_both_found` | `<doc><p>outer <p>inner</p> tail</p></doc>` | Both the outer and the nested `<p>` are found |
| `test_namespace_on_the_document_does_not_hide_paragraphs` | `<doc xmlns="http://example.com" xmlns:meta="...">` | Namespaces do not hide `<p>` |
| `test_a_heading_is_not_a_paragraph` | `<doc><heading>Bad Title</heading><p>real</p></doc>` | Only `<p>` is proofread |

### `test_annotate.py` - placing the model's answer (`annotate.py`)

| Test | Data | Checks |
|---|---|---|
| `test_prefix_picks_the_later_copy` | `the court and the court`, prefix `and the ` | When a word appears twice, the prefix selects the right copy |

### `test_verify.py` - the length invariant (`verify.py`)

Data: the official pair `data/example_input.xml` and `data/example_output.xml`.

| Test | Data | Checks |
|---|---|---|
| `test_good_output_passes` | the official output | Removing the `<error>` tags gives back the input exactly |
| `test_changed_text_is_caught` | output with `committe` changed to `committee` | Changed text is reported for that paragraph |
| `test_extra_space_is_caught` | output with `members  will` (two spaces) | A changed space is reported |

### `test_proofreader.py` - batching, cache, retries (`proofreader.py`)

Data: eleven `<p>teh cat N</p>` paragraphs (one repeated), plus `<p>- . -</p>`
which has nothing to proofread. The model is replaced by a fake that marks
`teh` as a spelling error.

| Test | Checks |
|---|---|
| `test_make_batches_by_count_and_size` | Batches respect both the paragraph count and the character limit |
| `test_batching_dedupe_skip_and_cache` | A repeated paragraph is sent once, punctuation-only text is skipped, and a second run makes no model calls |
| `test_retry_then_success_and_giving_up` | A failed call is retried; if every attempt fails, the paragraph is left unchanged |
| `test_requests_run_in_parallel` | Three batches run at the same time |
| `test_a_heading_is_left_unchanged` | `<heading>Bad Title</heading>` comes back untouched while the `<p>` is tagged |

### `test_cli.py` - the command (`cli.py`, `metrics.py`)

Data: temporary files in pytest's `tmp_path`, `data/example_input.xml`, and
`data/Style_Guide.docx`. A fake API key is set, and the model is faked.

| Test | Checks |
|---|---|
| `test_output_path` | With `--output-dir`, output is named `NAME.corrected.TIME.xml`; a second run in the same second gets `-2` and nothing is overwritten |
| `test_end_to_end_writes_beside_the_input` | By default the result is `NAME.corrected.xml` beside the input; Windows line endings are kept; the performance summary is printed and the same text is saved to the `.txt` |
| `test_output_dir_keeps_earlier_runs` | Two runs with `--output-dir` give two files |
| `test_bad_arguments_exit_2` (4 cases) | Missing input, invalid `--lang`, missing style guide, and writing over the input all exit with code 2 |
| `test_malformed_xml_exit_2` | `<r><p>oops</r>` exits with code 2 |
| `test_missing_key_exit_2` | No `ANTHROPIC_API_KEY` exits with code 2 |
| `test_rejected_key_exit_1` | A key the API rejects is not retried, exits with code 1, and writes no output |

### `test_styleguide.py` - reading the style guide (`styleguide.py`)

| Test | Data | Checks |
|---|---|---|
| `test_guide_text_is_loaded` | `data/Style_Guide.docx` | The guide's text is read, including a known rule and `HIPAA` |
| `test_fingerprint_changes_with_text` | `"a"`, `"b"` | The fingerprint changes when the text changes |
| `test_empty_docx_is_rejected` | an empty `.docx` made in the test | An empty guide is rejected |

## Proofreading cases

Each case is `tests/inputs/<name>.xml` (input) and `tests/expected/<name>.xml`
(hand-annotated answer). `scripts/run_cases.py` writes the result to
`tests/outputs/<time>/` with a `SUMMARY.md` that lists missed, wrong and extra
errors.

Paragraph numbers count `<p>` elements only, starting at 0, in file order.
"Must not be flagged" means the text is already correct, so the expected file
has no `<error>` there.

| Case | What it covers | Paragraphs | Errors | Latest result |
|---|---|---|---|---|
| `s1_dates_time` | Dates, time | 33 | 31 styleguide | 31/31 |
| `s2_numbers_money` | Numbers, currency | 25 | 18 styleguide | 18/18, 2 extra |
| `s3_hyphenation` | Hyphenated words | 18 | 13 styleguide | 13/13, 1 extra |
| `s4_wordlist_a_h` | Preferred word usage, A to H | 29 | 26 styleguide | 26/26 |
| `s5_wordlist_i_z` | Preferred word usage, I to Z | 36 | 43 styleguide | 42/43, 2 extra |
| `s6_exceptions_quotes` | Hot spots, quotations, exceptions | 16 | 9 styleguide | 9/9, 1 extra |
| `s7_capitalization` | Capitalization of prose | 20 | 26 capitalization | 23/26 |
| `general` | Spelling, grammar, punctuation, capitalization | 19 | 15 | 14/15 |
| `sample_input` | The provided sample (copy of `data/sample_input.xml`) | 14 | 45 | 45/45, 1 extra |
| `example_input` | The official example (copy of `data/example_input.xml` and `data/example_output.xml`) | 4 | 10 | 10/10 |

Latest result is run `tests/outputs/2026-11-14T00-59-57` (prompt version 12):
231 of 236 errors found (98%). `docs/FIXES.md` explains how the results
improved and lists what is still wrong.

`general`, `sample_input` and `example_input` were written by us, not provided
as ground truth, except `data/example_output.xml`.

### s1_dates_time

#### Dates (0-19)

| Rule | Paragraphs | Example |
|---|---|---|
| No comma between month and year | 0-2 | January, 2022 -> January 2022 |
| Abbreviated month with comma (two rules, one correction) | 3 | Jan., 2022 -> January 2022 |
| Spell out months in text | 4-6 | Feb. / Sept. / Mar. / Jun. / Jul. |
| Years in full | 7 | '21 -> 2021 |
| No apostrophe in plural years | 8-9 | 1990's -> 1990s |
| No apostrophe in plurals | 10-11 | CEO's -> CEOs, PDF's -> PDFs |
| Correct usage (must not be flagged) | 12-19 | June 1, 2022 / 1990s / the CEO's decision |

#### Time (20-32)

| Rule | Paragraphs | Example |
|---|---|---|
| Lowercase a.m./p.m. with periods | 20-24 | 9:00 AM -> 9:00 a.m., 3 P.M. -> 3 p.m. |
| Space between number and a.m./p.m. | 25-27 | 9am -> 9 a.m., 11a.m. -> 11 a.m. |
| Correct usage (must not be flagged) | 28-31 | 4:45 p.m. / noon / midnight |
| Trap: AM / PM that are not times | 32 | AM radio, the PM attended |

Judgement calls: `Jan., 2022` is one error covering both rules; `the CEO's
decision` is correct.

### s2_numbers_money

| Rule | Paragraphs | Example |
|---|---|---|
| Spell out one to ninety-nine | 0-3 | 6 -> six, 45 -> forty-five, 99 -> ninety-nine |
| Figures from 100 (must not be flagged) | 4 | 100 defendants, 250 appeals |
| Number at start of a sentence is spelled out | 5-6 | 15 -> Fifteen, 100 -> One hundred |
| Year at start of a sentence stays (must not be flagged) | 7 | 2020 was a difficult year |
| Fractions spelled out | 8-9 | 1/2 -> one-half, 1/3 -> one-third |
| Commas for 1,000+ | 10-11 | 1000 -> 1,000, 12500 -> 12,500 |
| Correct commas (must not be flagged) | 12 | 48,000 and 1,000 |
| No commas in SEC releases, executive orders (must not be flagged) | 13 | Release No. 34-12345 |
| Citation numbers follow the source (must not be flagged) | 14 | 60 Fed. Reg. 50,381 and 8469 |
| Dates and names with numbers (must not be flagged) | 15-16 | June 5, Form 8-K, Rule 10b-5 |
| Percentages keep figures (must not be flagged) | 17 | 5 percent, 12 percent |
| Close up space after currency symbol | 18-20 | $ 3,000 -> $3,000, US$ 5,000, USD 250,000 |
| Spell out million, billion | 21-22 | $3,000,000 -> $3 million, $4,000,000,000 -> $4 billion |
| Correct money forms (must not be flagged) | 23-24 | $3,000, $3 million, $5, $2.5 billion |

Judgement calls: fractions beyond "one-half" (1/3); percentages with figures
(the model currently spells them out); citation commas.

### s3_hyphenation

| Rule | Paragraphs | Example |
|---|---|---|
| third-party as adjective | 0-1 | third party claim -> third-party claim |
| third party as noun | 2-3 | a third-party -> a third party, third-parties -> third parties |
| -ly adverbs not hyphenated | 4-6 | wholly-owned, publicly-owned, closely-held, privately-funded |
| common-law (adjective) vs common law (noun) | 7-8 | common law principles -> common-law principles |
| General compound adjectives (judgement call) | 9-10 | risk based -> risk-based, long term -> long-term |
| Correct usage (must not be flagged) | 11-17 | third parties, third-party status, wholly owned, closely held |

Judgement calls: "closely held" and "privately funded" (the guide names only
wholly and publicly); the general compound adjectives in 9-10.

### s4_wordlist_a_h

| Entry | Paragraphs | Example |
|---|---|---|
| acknowledgment | 0 | acknowledgement -> acknowledgment |
| Administration (presidential) | 1 | Biden administration -> Biden Administration |
| adviser (investment) / advisor (other) | 2-3 | investment advisor -> adviser; financial adviser -> advisor |
| antifraud, attorney fees, attorney-client | 4-6 | anti-fraud, attorneys' fees, attorney client |
| breakup, broker-dealer | 7-8 | break-up, broker dealer |
| business judgment rule/test, bylaws | 9-11 | business-judgment, by-laws |
| carryback, carveout | 12-13 | carry-back, carve-out |
| co-author, co-editor, COVID-19 | 14-15 | coauthor, coeditor, Covid-19 |
| cross-anything hyphenated | 16-17 | cross examination, cross border, cross default |
| cybersecurity, email, fintech | 18-20 | cyber security, e-mail, FinTech |
| for-profit, healthcare | 21-22 | for profit, health care |
| Correct usage incl. verb forms (must not be flagged) | 23-28 | break up, carry back, carve out |

Judgement call: `attorneys' fees` -> `attorney fees`. Left out: intellectual
property / IP (depends on the book or chapter).

### s5_wordlist_i_z

| Entry | Paragraphs | Example |
|---|---|---|
| internet, judgment, know-how, lookback | 0-3 | Internet, judgement, know how, look-back |
| non- words, one word | 4-5 | non-profit, non-party, non-binding |
| non- exceptions keep hyphen | 6-8 | nonbankruptcy, nondebtor, nonlawyer, nonpriority |
| Of Counsel, online, UK, U.C.C., versus, website | 9-14 | of counsel, on-line, U.K., UCC, vs., web site |
| pre- words | 15-17 | pre-condition, pre-existing, pre-filing, pre-trial, preconfirmation, prepetition |
| post- words | 18 | postfiling, postpetition |
| publicly held, recordkeeping, subsection, redetermine, undersecured | 19-21 | publicly-held, record-keeping, sub-section |
| rollover, rollup, setoff (nouns) | 22 | roll-over, roll-up, set-off |
| super lien (noun) / super-lien (modifier), superpriority | 23-24 | super-lien -> super lien; super lien claim -> super-lien claim |
| then-anything, time frame, toward | 25-27 | then current, then Commissioner, timeframe, towards, afterwards |
| workers' compensation (curly apostrophe) | 28-29 | workers compensation, worker's compensation |
| Correct usage (must not be flagged) | 30-35 | verbs roll over / roll up / set off, UCC-1, post petition (adverbial) |

Left out: `opt-out` (the guide's entry contradicts itself); intellectual
property / IP.

### s6_exceptions_quotes

| Rule | Paragraphs | Example |
|---|---|---|
| principle / principal | 0-1 | repay the principle -> principal |
| ensure / insure | 2-3 | insure compliance -> ensure |
| HIPAA, FATCA, FACTA | 4-6 | HIPPA -> HIPAA, (FACTA) -> (FATCA) |
| Curly double quotes | 7 | "unworkable" -> curly quotes |
| Curly apostrophe (judgement call) | 8 | court's -> court’s |
| Quoted material never edited (must not be flagged) | 9-10 | quote containing e-mail, acknowledgement, a typo |
| Titles of laws and works keep source form (must not be flagged) | 11-12 | Health Care Quality Improvement Act |
| Case name keeps "vs." (judgement call, must not be flagged) | 13 | Smith vs. Jones |
| Correct usage (must not be flagged) | 14-15 | principal / principle / ensure / insure, HIPAA, FATCA, FACTA |

### s7_capitalization

Capitalization in normal prose that is written in lowercase. The three
`<heading>` elements are badly capitalized on purpose and must come back
unchanged, because the tool proofreads only `<p>`.

| Rule | Paragraphs | Example |
|---|---|---|
| First word of a sentence, the pronoun I | 0-1 | the -> The, i -> I |
| Names of people, places, months and days | 2-4 | maria, london, march, tuesday |
| A title and a surname are separate errors | 5-6 | president lincoln -> President + Lincoln, judge brown |
| Languages and nationalities | 7-8 | english, french, american, british |
| A multi-word name is one error | 9-10 | securities and exchange commission, supreme court of the united states |
| Acronyms | 11 | hipaa -> HIPAA, fatca -> FATCA |
| Constitution (judgement call) | 12 | constitution -> Constitution |
| Correct usage (must not be flagged) | 13-19 | the court, the president of the company, state court, email |

Judgement call: `constitution` (the prompt says never edit the names of laws).

### general

General rules outside the style guide.

| Rule | Paragraphs | Example |
|---|---|---|
| Spelling | 0-1 | defendent, recieved, seperate |
| Grammar | 2-7 | documents was, Each ... were, Their going, should of, less witnesses, Its a |
| Punctuation | 8-10 | However the, comma splice, courts decision |
| Capitalization | 11-12 | supreme court, monday, the chair |
| Correct usage (must not be flagged) | 13-18 | the same sentences, already correct |

Judgement call: the comma splice in 9 could also be fixed with a period or a
conjunction.

## Not covered

- Footnote-specific rules (dates, numbers): the cases have body text only.
- Title case for real `<heading>` elements: the tool does not proofread them.
- Clarity: no case tests it, and the style guide never defines it.
- Other languages: every case uses `--lang en`.

## Known issues

- Curly vs straight apostrophes: correct text in s1 to s5 contains straight
  apostrophes (for example "the CEO's decision"). The model sometimes flags
  them, as in s3 `party's` -> `party’s`, and sometimes adds a straight one, as
  in general `Their` -> `They're` instead of `They’re`.
