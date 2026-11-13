# Test coverage

Each manual test is a pair: `tests/cases/<name>.xml` (input) and
`tests/expected/<name>.xml` (hand-written expected output).
Run one with `scripts/run_case.sh <name>`.

Paragraph numbers below count `<p>` elements only, starting at 0, in file order.
"Must not be flagged" means the text is already correct, so the expected file
has no `<error>` there. Every error in s1-s6 is `type="styleguide"` with a
`reason`; s7 uses `styleguide` as well, because its rules come from the guide.

## Summary

| Case | Style guide section | Paragraphs | Errors | Status |
|---|---|---|---|---|
| `s1_dates_time` | Dates (months, days, years), Time | 33 | 31 | written |
| `s2_numbers_money` | Numbers, Symbols (currency) | 25 | 18 | written |
| `s3_hyphenation` | Hyphenated Words | 18 | 13 | written |
| `s4_wordlist_a_h` | Preferred Word Usage, A to H | 29 | 26 | written |
| `s5_wordlist_i_z` | Preferred Word Usage, I to Z | 36 | 43 | written |
| `s6_exceptions_quotes` | Hot Spots for Errors, Quotations, exceptions | 16 | 9 | written |
| `s7_capitalization` | Capitalization Style (title case) | 24 | 14 | written |

Status values: `written` = files exist; `reviewed` = run against the real model
and every MISSING / WRONG FIX / EXTRA decided.

## s1_dates_time

### Dates (0-19)

| Rule | Paragraphs | Example |
|---|---|---|
| No comma between month and year | 0-2 | January, 2022 -> January 2022 |
| Abbreviated month with comma (two rules, one correction) | 3 | Jan., 2022 -> January 2022 |
| Spell out months in text | 4-6 | Feb. / Sept. / Mar. / Jun. / Jul. |
| Years in full | 7 | '21 -> 2021 |
| No apostrophe in plural years | 8-9 | 1990's -> 1990s |
| No apostrophe in plurals | 10-11 | CEO's -> CEOs, PDF's -> PDFs |
| Correct usage (must not be flagged) | 12-19 | June 1, 2022 / 1990s / the CEO's decision |

### Time (20-32)

| Rule | Paragraphs | Example |
|---|---|---|
| Lowercase a.m./p.m. with periods | 20-24 | 9:00 AM -> 9:00 a.m., 3 P.M. -> 3 p.m. |
| Space between number and a.m./p.m. | 25-27 | 9am -> 9 a.m., 11a.m. -> 11 a.m. |
| Correct usage (must not be flagged) | 28-31 | 4:45 p.m. / noon / midnight |
| Trap: AM / PM that are not times | 32 | AM radio, the PM attended |

Judgement calls: `Jan., 2022` expected as one error covering both rules;
`'21` may be skipped by a model; `the CEO's decision` is correct.

## s2_numbers_money

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

Judgement calls: fractions beyond "one-half" (1/3); percentages with figures;
citation commas.

## s3_hyphenation

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

## s4_wordlist_a_h

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

## s5_wordlist_i_z

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

## s6_exceptions_quotes

| Rule | Paragraphs | Example |
|---|---|---|
| principle / principal | 0-1 | repay the principle -> principal |
| ensure / insure | 2-3 | insure compliance -> ensure |
| HIPAA, FATCA, FACTA | 4-6 | HIPPA -> HIPAA, (FACTA) -> (FATCA) |
| Curly double quotes | 7 | "unworkable" -> curly quotes |
| Curly apostrophe (judgement call) | 8 | court's -> court's (curly) |
| Quoted material never edited (must not be flagged) | 9-10 | quote containing e-mail, acknowledgement, a typo |
| Titles of laws and works keep source form (must not be flagged) | 11-12 | Health Care Quality Improvement Act |
| Case name keeps "vs." (judgement call, must not be flagged) | 13 | Smith vs. Jones |
| Correct usage (must not be flagged) | 14-15 | principal / principle / ensure / insure, HIPAA, FATCA, FACTA |

## s7_capitalization

The guide's rules apply to headings, but the tool only proofreads `<p>`. The
headings here are `<p>` elements shaped like table and figure titles. The one
real `<heading>` element is miscapitalized on purpose and must come back
unchanged (it checks that nothing outside `<p>` is touched).

| Rule | Paragraphs | Example |
|---|---|---|
| Capitalize major words | 0-1 | Key findings -> Key Findings, As good -> As Good |
| Lowercase only articles, in/on/from/upon, short prepositions | 2-5 | In -> in, Upon -> upon, both -> Both, over -> Over |
| Forms of "to be" always capitalized (hot spot) | 6-7 | This is -> This Is, are Seeking -> Are Seeking |
| Last word always capitalized | 8 | Came from -> Came From |
| Each part of a hyphenated word capitalized | 9-10 | Work-product, Cross-default, Non-party |
| Answer Book questions in sentence case (judgement call) | 11 | What Is a Subpoena? -> What is a subpoena? |
| Correct headings (must not be flagged) | 12-23 | the guide's own examples |

Judgement calls: paragraph 11 (nothing marks the file as an Answer Book); a
model may return a whole heading as one correction instead of one word.

## Not covered

- Footnote-specific rules (dates, numbers): the test files have body text only.
- Title case for real `<heading>` elements: the tool does not proofread them
  (see the trap in s7).
- General Grammar, Spelling, Punctuation, Capitalization and Clarity rules (no
  separate case, so the type labels for those categories are untested).
- Structure and CLI behaviour (tags, CDATA, entities, encodings, bad API key):
  planned separately as A1 to E4.

## Known issues to settle

- Curly vs straight quotes: s1 to s5 contain straight apostrophes in correct
  text (for example "the CEO's decision"). A strict model may flag them. Decide
  whether to convert them to curly or accept the extra flags.
