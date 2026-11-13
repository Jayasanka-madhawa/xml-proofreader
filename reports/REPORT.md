# Evaluation report

## 1. Overview

- **What was tested:** seven hand-written test cases, one per style-guide topic, with expected outputs written by hand (`tests/cases/` and `tests/expected/`). Coverage of each rule is in `tests/COVERAGE.md`.
- **How it was run:** `scripts/run_case.sh <case>` with `claude-sonnet-5-5`, one real run per case, then compared with `scripts/compare.py`.
- **Result in one line:** 141 of 154 expected errors found with the correct fix (92%), 3 false alarms (precision 98%), and the reason given matches the expected rule in meaning for 98% of the errors found. The one weak topic is capitalization of headings and captions (2 of 14).
- **A rerun after this** (all seven cases again) returned identical output with 0 model calls in 0.00 to 0.01 s each, which shows the on-disk cache works. The accuracy figures below therefore come from the first real runs.

## 2. Accuracy by topic

| Topic | Expected | Found | Correct fix | Missed | False alarms | Detection | Fix accuracy | Precision | Reason meaning | Type match |
|---|---|---|---|---|---|---|---|---|---|---|
| Dates and Time | 31 | 31 | 31 | 0 | 1 | 100% | 100% | 97% | 95% | 97% |
| Numbers and Money | 18 | 18 | 18 | 0 | 0 | 100% | 100% | 100% | 100% | 100% |
| Hyphenation | 13 | 13 | 13 | 0 | 1 | 100% | 100% | 93% | 100% | 85% |
| Preferred Word List | 69 | 68 | 68 | 1 | 0 | 99% | 99% | 100% | 99% | 99% |
| Hot Spots, Quotes and Exceptions | 9 | 9 | 9 | 0 | 1 | 100% | 100% | 90% | 100% | 56% |
| Capitalization | 14 | 2 | 2 | 12 | 0 | 14% | 14% | 100% | 100% | 0% |
| **All topics** | **154** | **141** | **141** | **13** | **3** | **92%** | **92%** | **98%** | **98%** | **93%** |

How the numbers are worked out:

- **Detection** = errors found / errors expected.
- **Fix accuracy** = errors found with the correct fix / errors expected. A fix counts as correct when it gives the same text, even if the tool wrapped a few extra neighbouring words (for example "6 witnesses" → "six witnesses" for an expected "6" → "six").
- **Precision** = correct fixes / everything the tool reported, so false alarms lower it.
- **Reason meaning** is judged on meaning, not wording, over the errors found: 1 point if the reason states the same rule, half a point if it states the right rule but is vague or leaves part out, 0 if it is a different rule. For example "No comma between month and year" and "Do not add a comma after the month" would both score 1.
- **Type match** = errors found whose `type` equals the expected type. It is the least reliable column, since a word like "principle/principal" can reasonably be `spelling` or `styleguide`.
- One false alarm in `s5` (paragraph 31, "postfiling") is left out of the totals, because the test paragraph itself had the wrong form; the test file is now fixed.

## 3. Performance summary

One real run per case (cold cache for the paragraphs, prompt cache warm from the second case on):

| Case | Paragraphs | Errors tagged | Time | Peak memory | Model calls | Tokens in | Tokens out | Read from prompt cache |
|---|---|---|---|---|---|---|---|---|
| s1_dates_time | 33 | 32 | 4.96 s | 95.7 MiB | 6 | 31,469 | 2,525 | 0 |
| s2_numbers_money | 25 | 18 | 4.08 s | 95.1 MiB | 4 | 21,004 | 1,537 | 0 |
| s3_hyphenation | 18 | 14 | 4.06 s | 95.1 MiB | 3 | 1,039 | 1,162 | 14,730 |
| s4_wordlist_a_h | 29 | 26 | 3.97 s | 95.5 MiB | 5 | 1,634 | 2,056 | 24,550 |
| s5_wordlist_i_z | 36 | 43 | 4.39 s | 95.4 MiB | 6 | 2,106 | 3,143 | 29,460 |
| s6_exceptions_quotes | 16 | 10 | 3.78 s | 94.6 MiB | 3 | 1,017 | 962 | 14,730 |
| s7_capitalization | 25 (see problem 8) | 2 | 12.21 s | 95.9 MiB | 5 | 2,236 | 3,884 | 24,550 |
| **Total** | **182** | **145** | **37.5 s** | **about 95 MiB** | **32** | **60,505** | **15,269** | **108,020** |

- **Speed:** about 4.9 paragraphs per second overall, 3.8 to 5.0 s for a case of 16 to 36 paragraphs. `s7_capitalization` took 12.2 s because the model wrote 3,884 output tokens for only 2 errors (it deliberated over the headings).
- **Memory:** flat at about 95 MiB regardless of case size.
- **Cache hit:** a repeat run takes 0.00 to 0.01 s, makes 0 model calls and uses about 87 MiB.
- **Prompt caching:** from `s3` on, 14,730 to 29,460 tokens were read from cache per run instead of being sent again. `s1` and `s2` show 0 cache reads (problem 6 below).

## 4. Problems and solutions

| # | Problem | Evidence | Solution | Priority |
|---|---|---|---|---|
| 1 | A typo inside quoted text was corrected, but the guide says never to edit quoted material | `s6` paragraph 10: "Febuary" inside “…” → "February" | Code guard in `annotate.locate` that drops any suggestion lying inside a curly-quote pair; add a prompt line and a unit test | High |
| 2 | Title case is skipped for heading-like paragraphs | `s7`: 12 of 14 missed; only the hyphenated words were fixed | Prompt line: short Table/Figure captions are headings and take title case. Optional, depends on whether real inputs have such `<p>` captions | Medium |
| 3 | Straight apostrophes are flagged inconsistently | "CEO's" (`s1`) and "party's" (`s3`) flagged as false alarms, while other straight apostrophes in correct text were left alone | Prompt line: corrections use curly quotes and apostrophes; convert the straight apostrophes in the correct-text paragraphs of `s1` to `s5`; bump `PROMPT_VERSION` | Medium |
| 4 | Bad API key exits 0 (predicted, not yet tested) | In the from-scratch code only `BadRequestError` is re-raised, so an authentication error is retried and the paragraphs are left unchanged | Re-raise `AuthenticationError`, `PermissionDeniedError` and `NotFoundError`; exit 1 when any paragraph failed | High |
| 5 | A modifier form was missed | `s5` paragraph 24: "super lien claim" should be "super-lien claim" | Add the modifier rule as an explicit example in the prompt, or accept it as a limitation | Low |
| 6 | Prompt cache not used on the first batch | `s1` and `s2` show 0 cache reads with 31,469 and 21,004 tokens in, because parallel workers start before the first call has written the cache | Send the first batch alone to warm the cache, then run the rest in parallel | Medium |
| 7 | Wider spans than the minimal change | 18 fixes wrapped a neighbouring word ("6 witnesses" → "six witnesses"); the result is the same text and the invariant still holds | Harmless; optionally add a prompt line to wrap only the words that change. `compare.py` already treats these as correct | Low |
| 8 | Paragraph count mismatch (to verify) | `s7` reports 25 paragraphs but the file has 24 `<p>` elements. The only difference from the other files is a comment that contains `<p>`. The reference scanner counts 24, so your `find_paragraphs` may be counting the `<p>` inside the comment | Run your scanner on `s7` and check the paragraph count; if it is 25, make sure comments are skipped before tag matching, and add a unit test with a comment that contains `<p>` | Medium |
| 9 | Type labels differ from expected | 14 type differences, mostly `spelling`, `grammar` or `punctuation` where `styleguide` was expected | Accept; the labels are defensible and the type is the least reliable column | Low |
| 10 | Two mistakes in my own test files (fixed) | `s5` paragraph 31 used "postfiling" in a "correct" paragraph; the `s1` expected file wrapped more than needed for "Mar. 5, 2022" | Corrected files are in `fixes.zip`; the run above still used the old `s5` input, so the "postfiling" false alarm disappears on the next run | Done |
| 11 | General categories are only lightly tested | A separate run of the removed general case found 15 of 18 errors; the 3 misses were the wordy-phrase clarity fixes, and it added one false alarm ("appeal, because") | Accept clarity as a known limitation, or add a clarity line to the prompt | Low |

## 5. Detailed results by topic

Every error with its expected and actual fix, expected and actual reason, and whether the two reasons mean the same.

### Dates and Time

Cases: `s1_dates_time`. Expected errors: **31**. Found: **31**, correct fix: **31** (0 with a wider span than expected), missed: **0**, false alarms: **1**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s1 | 0 | January, 2022 | January 2022 | January 2022 | ✓ | No comma between month and year | No comma between month and year | ✓ | styleguide |
| s1 | 1 | March, 1998 | March 1998 | March 1998 | ✓ | No comma between month and year | No comma between month and year | ✓ | styleguide |
| s1 | 1 | October, 2004 | October 2004 | October 2004 | ✓ | No comma between month and year | No comma between month and year | ✓ | styleguide |
| s1 | 2 | May, 2022 | May 2022 | May 2022 | ✓ | No comma between month and year | No comma between month and year | ✓ | styleguide |
| s1 | 2 | June, 2022 | June 2022 | June 2022 | ✓ | No comma between month and year | No comma between month and year | ✓ | styleguide |
| s1 | 3 | Jan., 2022 | January 2022 | January 2022 | ✓ | Spell out months in text; no comma between month and year | No comma between month and year; spell out months in text | ✓ | styleguide |
| s1 | 4 | Feb. 2022 | February 2022 | February 2022 | ✓ | Spell out months in text | Spell out months in text | ✓ | styleguide |
| s1 | 4 | Sept. 2022 | September 2022 | September 2022 | ✓ | Spell out months in text | Spell out months in text | ✓ | styleguide |
| s1 | 5 | Mar. | March | March | ✓ | Spell out months in text | Spell out months in text | ✓ | styleguide |
| s1 | 6 | Jun. 2023 | June 2023 | June 2023 | ✓ | Spell out months in text; June is never abbreviated | Spell out months in text; June is never abbreviated | ✓ | styleguide |
| s1 | 6 | Jul. 2023 | July 2023 | July 2023 | ✓ | Spell out months in text; July is never abbreviated | Spell out months in text; July is never abbreviated | ✓ | styleguide |
| s1 | 7 | '21 | 2021 | 2021 | ✓ | Give years in full | Years are given in full; use curled apostrophe style otherwise | ~ adds an unrelated clause (curled apostrophe) | styleguide |
| s1 | 8 | 1990's | 1990s | 1990s | ✓ | No apostrophe in plural years | No apostrophes in plural years | ✓ | styleguide |
| s1 | 8 | 2000's | 2000s | 2000s | ✓ | No apostrophe in plural years | No apostrophes in plural years | ✓ | styleguide |
| s1 | 9 | 1930's | 1930s | 1930s | ✓ | No apostrophe in plural years | No apostrophes in plural years | ✓ | styleguide |
| s1 | 9 | 1970's | 1970s | 1970s | ✓ | No apostrophe in plural years | No apostrophes in plural years | ✓ | styleguide |
| s1 | 10 | CEO's | CEOs | CEOs | ✓ | No apostrophes in plurals | No apostrophes in plurals | ✓ | styleguide |
| s1 | 10 | CFO's | CFOs | CFOs | ✓ | No apostrophes in plurals | No apostrophes in plurals | ✓ | styleguide |
| s1 | 11 | PDF's | PDFs | PDFs | ✓ | No apostrophes in plurals | No apostrophes in plurals | ✓ | styleguide |
| s1 | 19 | CEO's | none expected | CEO’s | ✗ false alarm | | Use curled apostrophes | | punctuation |
| s1 | 20 | 9:00 AM | 9:00 a.m. | 9:00 a.m. | ✓ | Use lowercase a.m. and p.m. | Use lowercase a.m. with periods | ✓ | styleguide |
| s1 | 20 | 5:30PM | 5:30 p.m. | 5:30 p.m. | ✓ | Lowercase p.m., with a space after the time | Use lowercase p.m. with space before it | ✓ | styleguide |
| s1 | 21 | 6:00 am | 6:00 a.m. | 6:00 a.m. | ✓ | Use a.m. with periods | Use a.m. with periods | ✓ | styleguide |
| s1 | 21 | 7:15 pm | 7:15 p.m. | 7:15 p.m. | ✓ | Use p.m. with periods | Use p.m. with periods | ✓ | styleguide |
| s1 | 22 | 3 P.M. | 3 p.m. | 3 p.m. | ✓ | Use lowercase a.m. and p.m. | Use lowercase p.m. | ✓ | styleguide |
| s1 | 23 | 10:30 A.M. | 10:30 a.m. | 10:30 a.m. | ✓ | Use lowercase a.m. and p.m. | Use lowercase a.m. | ✓ | styleguide |
| s1 | 24 | 12:15 p.m | 12:15 p.m. | 12:15 p.m. | ✓ | Use periods in p.m. | Missing period in abbreviation "p.m." | ✓ | styleguide / **punctuation** |
| s1 | 25 | 9am | 9 a.m. | 9 a.m. | ✓ | Space between the time and a.m./p.m.; use periods | Use "a.m." with space before it | ~ mentions only the space, not the periods | styleguide |
| s1 | 25 | 6pm | 6 p.m. | 6 p.m. | ✓ | Space between the time and a.m./p.m.; use periods | Use "p.m." with space before it | ~ mentions only the space, not the periods | styleguide |
| s1 | 26 | 11a.m. | 11 a.m. | 11 a.m. | ✓ | Add a space between the time and a.m. | Space required between time and meridiem | ✓ | styleguide |
| s1 | 26 | 8p.m. | 8 p.m. | 8 p.m. | ✓ | Add a space between the time and p.m. | Space required between time and meridiem | ✓ | styleguide |
| s1 | 27 | 4:45PM | 4:45 p.m. | 4:45 p.m. | ✓ | Lowercase p.m., with a space after the time | Lowercase "p.m." with periods and a space before it | ✓ | styleguide |

### Numbers and Money

Cases: `s2_numbers_money`. Expected errors: **18**. Found: **18**, correct fix: **18** (8 with a wider span than expected), missed: **0**, false alarms: **0**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s2 | 0 | 6 witnesses | six | six witnesses | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 1 | 12 lawyers | twelve | twelve lawyers | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 1 | 45 paralegals | forty-five | forty-five paralegals | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 2 | 23 months | twenty-three | twenty-three months | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 3 | 3 of | three | three of | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 3 | 99 defendants | ninety-nine | ninety-nine defendants | ✓ wider span | Spell out one to ninety-nine | Spell out numbers one to ninety-nine | ✓ | styleguide |
| s2 | 5 | 15 firms | Fifteen | Fifteen firms | ✓ wider span | Spell out a number that begins a sentence | Spell out number beginning a sentence | ✓ | styleguide |
| s2 | 6 | 100 witnesses | One hundred | One hundred witnesses | ✓ wider span | Spell out a number that begins a sentence | Numbers at the start of a sentence are spelled out (not a year) | ✓ | styleguide |
| s2 | 8 | 1/2 | one-half | one-half | ✓ | Spell out fractions in text | Spell out fractions in text | ✓ | styleguide |
| s2 | 9 | 1/3 | one-third | one-third | ✓ | Spell out fractions in text | Spell out fractions in text | ✓ | styleguide |
| s2 | 10 | 1000 | 1,000 | 1,000 | ✓ | Use a comma in numbers of 1,000 or more | Use commas for 1,000+ | ✓ | styleguide |
| s2 | 10 | 12500 | 12,500 | 12,500 | ✓ | Use a comma in numbers of 1,000 or more | Use commas for 1,000+ | ✓ | styleguide |
| s2 | 11 | 48000 | 48,000 | 48,000 | ✓ | Use a comma in numbers of 1,000 or more | Use commas for 1,000+ | ✓ | styleguide |
| s2 | 18 | $ 3,000 | $3,000 | $3,000 | ✓ | Close up the space between the currency symbol and the amount | Close up space between currency symbol and amount | ✓ | styleguide |
| s2 | 19 | US$ 5,000 | US$5,000 | US$5,000 | ✓ | Close up the space between the currency symbol and the amount | Close up space between currency symbol and amount | ✓ | styleguide |
| s2 | 20 | USD 250,000 | USD250,000 | USD250,000 | ✓ | Close up the space between the currency symbol and the amount | Close up space between currency designation and amount | ✓ | styleguide |
| s2 | 21 | $3,000,000 | $3 million | $3 million | ✓ | Spell out million, billion, etc. | Spell out million, billion, etc. | ✓ | styleguide |
| s2 | 22 | $4,000,000,000 | $4 billion | $4 billion | ✓ | Spell out million, billion, etc. | Spell out million, billion, etc. | ✓ | styleguide |

### Hyphenation

Cases: `s3_hyphenation`. Expected errors: **13**. Found: **13**, correct fix: **13** (3 with a wider span than expected), missed: **0**, false alarms: **1**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s3 | 0 | third party infringement | third-party | third-party infringement | ✓ wider span | Hyphenate third-party when it modifies another word | Hyphenate third-party as adjective | ✓ | styleguide |
| s3 | 1 | third party status | third-party | third-party status | ✓ wider span | Hyphenate third-party when it modifies another word | Hyphenate third-party as adjective | ✓ | styleguide |
| s3 | 2 | third-party | third party | third party | ✓ | Do not hyphenate third party when used as a noun | Noun use takes no hyphen | ✓ | styleguide |
| s3 | 3 | third-parties | third parties | third parties | ✓ | Do not hyphenate third party when used as a noun | Noun use takes no hyphen | ✓ | styleguide |
| s3 | 4 | wholly-owned | wholly owned | wholly owned | ✓ | Do not hyphenate compound adjectival phrases whose first element is an -ly adverb | Do not hyphenate ly adverbs | ✓ | styleguide |
| s3 | 5 | publicly-owned | publicly owned | publicly owned | ✓ | Do not hyphenate compound adjectival phrases whose first element is an -ly adverb | Do not hyphenate ly adverbs | ✓ | styleguide |
| s3 | 5 | wholly-owned | wholly owned | wholly owned | ✓ | Do not hyphenate compound adjectival phrases whose first element is an -ly adverb | Do not hyphenate ly adverbs | ✓ | styleguide |
| s3 | 6 | closely-held | closely held | closely held | ✓ | Do not hyphenate compound adjectival phrases whose first element is an -ly adverb | Do not hyphenate -ly adverb compounds | ✓ | styleguide |
| s3 | 6 | privately-funded | privately funded | privately funded | ✓ | Do not hyphenate compound adjectival phrases whose first element is an -ly adverb | Do not hyphenate -ly adverb compounds | ✓ | styleguide |
| s3 | 7 | common law principles | common-law | common-law principles | ✓ wider span | Hyphenate common-law when used as an adjective | Hyphenate when used adjectivally | ✓ | styleguide |
| s3 | 8 | common-law | common law | common law | ✓ | Do not hyphenate common law when used as a noun | Noun usage omits hyphen | ✓ | styleguide |
| s3 | 9 | risk based | risk-based | risk-based | ✓ | Hyphenate compound words that modify another word | Compound adjective needs hyphen | ✓ | styleguide / **grammar** |
| s3 | 10 | long term | long-term | long-term | ✓ | Hyphenate compound words that modify another word | Compound adjective needs hyphen | ✓ | styleguide / **grammar** |
| s3 | 13 | party's | none expected | party’s | ✗ false alarm | | Use curled apostrophes | | styleguide |

### Preferred Word List

Cases: `s4_wordlist_a_h`, `s5_wordlist_i_z`. Expected errors: **69**. Found: **68**, correct fix: **68** (6 with a wider span than expected), missed: **1**, false alarms: **0**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s4 | 0 | acknowledgement | acknowledgment | acknowledgment | ✓ | Preferred spelling is acknowledgment | Preferred spelling | ~ does not say which spelling is preferred | styleguide |
| s4 | 1 | administration | Administration | Administration | ✓ | Uppercase Administration when referring to a presidential administration | Uppercase for presidential administration | ✓ | styleguide |
| s4 | 2 | advisor | adviser | adviser | ✓ | Use adviser for an investment adviser | Investment adviser spelling | ✓ | styleguide |
| s4 | 3 | financial adviser | advisor | financial advisor | ✓ wider span | Use advisor for types other than investment | Advisor for non-investment types | ✓ | styleguide |
| s4 | 3 | tax adviser | advisor | tax advisor | ✓ wider span | Use advisor for types other than investment | Advisor for non-investment types | ✓ | styleguide |
| s4 | 4 | anti-fraud | antifraud | antifraud | ✓ | Antifraud is one word, not hyphenated | One word, no hyphen | ✓ | styleguide |
| s4 | 5 | attorneys' fees | attorney fees | attorney fees | ✓ | Preferred form is attorney fees | Preferred format | ~ does not say what the preferred format is | styleguide |
| s4 | 6 | attorney client | attorney-client | attorney-client | ✓ | Attorney-client is hyphenated | Preferred usage: hyphenated | ✓ | styleguide |
| s4 | 7 | break-up | breakup | breakup | ✓ | Breakup is one word as a noun or adjective | Preferred usage: one word, no hyphen | ✓ | styleguide |
| s4 | 8 | broker dealer | broker-dealer | broker-dealer | ✓ | Broker-dealer is hyphenated | Preferred usage: hyphenated | ✓ | styleguide |
| s4 | 9 | business-judgment rule | business judgment | business judgment rule | ✓ wider span | Business judgment rule is three separate words | Preferred usage: separate words, no hyphen | ✓ | styleguide |
| s4 | 10 | business-judgment test | business judgment | business judgment test | ✓ wider span | Business judgment test is three separate words | Preferred usage: separate words, no hyphen | ✓ | styleguide |
| s4 | 11 | by-laws | bylaws | bylaws | ✓ | Bylaws is one word, no hyphen | Preferred usage: one word, no hyphen | ✓ | styleguide |
| s4 | 12 | carry-back | carryback | carryback | ✓ | Carryback is one word as a noun or adjective | Preferred: carryback, one word, no hyphen | ✓ | styleguide |
| s4 | 13 | carve-out | carveout | carveout | ✓ | Carveout is one word as a noun or adjective | Preferred: carveout, one word, no hyphen | ✓ | styleguide |
| s4 | 14 | coauthor | co-author | co-author | ✓ | Co-author is hyphenated | Preferred: co-author, hyphenated | ✓ | styleguide |
| s4 | 14 | coeditor | co-editor | co-editor | ✓ | Co-editor is hyphenated | Preferred: co-editor, hyphenated | ✓ | styleguide |
| s4 | 15 | Covid-19 | COVID-19 | COVID-19 | ✓ | COVID-19 is written in all caps | COVID-19 must be all caps | ✓ | styleguide |
| s4 | 16 | cross examination | cross-examination | cross-examination | ✓ | Cross- compounds take a hyphen | cross-anything uses a hyphen | ✓ | styleguide |
| s4 | 17 | cross border | cross-border | cross-border | ✓ | Cross- compounds take a hyphen | cross-anything uses a hyphen | ✓ | styleguide |
| s4 | 17 | cross default | cross-default | cross-default | ✓ | Cross- compounds take a hyphen | cross-anything uses a hyphen | ✓ | styleguide |
| s4 | 18 | cyber security | cybersecurity | cybersecurity | ✓ | Cybersecurity is one word | Preferred usage: one word | ✓ | styleguide |
| s4 | 19 | e-mail | email | email | ✓ | Email is lowercase, no hyphen | Preferred usage: lowercase, no hyphen | ✓ | styleguide |
| s4 | 20 | FinTech | fintech | fintech | ✓ | Fintech is lowercase | Preferred usage: lowercase | ✓ | styleguide |
| s4 | 21 | for profit company | for-profit | for-profit company | ✓ wider span | For-profit is hyphenated | Preferred usage: hyphenated | ✓ | styleguide |
| s4 | 22 | health care | healthcare | healthcare | ✓ | Healthcare is one word | Preferred usage: one word | ✓ | styleguide |
| s5 | 0 | Internet | internet | internet | ✓ | Internet is lowercase | internet is lowercase | ✓ | styleguide |
| s5 | 1 | judgement | judgment | judgment | ✓ | Preferred spelling is judgment | Preferred spelling: judgment | ✓ | styleguide / **spelling** |
| s5 | 2 | know how | know-how | know-how | ✓ | Know-how is hyphenated | know-how is hyphenated | ✓ | styleguide |
| s5 | 3 | look-back | lookback | lookback | ✓ | Lookback is one word as a noun or adjective | lookback is one word, no hyphen | ✓ | styleguide |
| s5 | 4 | non-profit | nonprofit | nonprofit | ✓ | Most non- words are one word, no hyphen | non words are one word, no hyphen | ✓ | styleguide |
| s5 | 5 | non-party | nonparty | nonparty | ✓ | Most non- words are one word, no hyphen | non words are one word, no hyphen | ✓ | styleguide |
| s5 | 5 | non-binding | nonbinding | nonbinding | ✓ | Most non- words are one word, no hyphen | non words are one word, no hyphen | ✓ | styleguide |
| s5 | 6 | nonbankruptcy | non-bankruptcy | non-bankruptcy | ✓ | Non-bankruptcy is a listed exception and keeps its hyphen | Preferred word usage: non-bankruptcy is hyphenated | ✓ | styleguide |
| s5 | 7 | nondebtor | non-debtor | non-debtor | ✓ | Non-debtor is a listed exception and keeps its hyphen | Preferred word usage: non-debtor is hyphenated | ✓ | styleguide |
| s5 | 8 | nonlawyer | non-lawyer | non-lawyer | ✓ | Non-lawyer is a listed exception and keeps its hyphen | Preferred word usage: non-lawyer is hyphenated | ✓ | styleguide |
| s5 | 8 | nonpriority | non-priority | non-priority | ✓ | Non-priority is a listed exception and keeps its hyphen | Preferred word usage: non-priority is hyphenated | ✓ | styleguide |
| s5 | 9 | of counsel | Of Counsel | Of Counsel | ✓ | Capitalize both words when used for status at a law firm | Of Counsel capitalized when referring to law firm status | ✓ | styleguide |
| s5 | 10 | on-line | online | online | ✓ | Online is one word, lowercase | Preferred usage: online, one word | ✓ | styleguide |
| s5 | 11 | U.K. | UK | UK | ✓ | UK is written without periods | UK without periods | ✓ | styleguide |
| s5 | 12 | UCC | U.C.C. | U.C.C. | ✓ | Write U.C.C. with periods | Style guide: include periods in U.C.C. | ✓ | styleguide |
| s5 | 13 | vs. | versus | versus | ✓ | Write versus, never vs. | Never use "vs."; use "versus" | ✓ | styleguide |
| s5 | 14 | web site | website | website | ✓ | Website is one word, lowercase | Preferred: website (one word) | ✓ | styleguide |
| s5 | 15 | pre-condition | precondition | precondition | ✓ | Precondition is one word, no hyphen | Preferred: precondition (no hyphen) | ✓ | styleguide |
| s5 | 15 | pre-existing | preexisting | preexisting | ✓ | Preexisting is one word, no hyphen | Preferred: preexisting (no hyphen) | ✓ | styleguide |
| s5 | 16 | pre-filing | prefiling | prefiling | ✓ | Prefiling is one word, no hyphen | Preferred: prefiling (no hyphen) | ✓ | styleguide |
| s5 | 16 | pre-trial | pretrial | pretrial | ✓ | Pretrial is one word, no hyphen | Preferred: pretrial (no hyphen) | ✓ | styleguide |
| s5 | 17 | preconfirmation | pre-confirmation | pre-confirmation | ✓ | Pre-confirmation is hyphenated | Preferred: pre-confirmation (hyphenated) | ✓ | styleguide |
| s5 | 17 | prepetition | pre-petition | pre-petition | ✓ | Pre-petition is hyphenated | Preferred: pre-petition (hyphenated) | ✓ | styleguide |
| s5 | 18 | postfiling | post-filing | post-filing | ✓ | Post-filing is hyphenated | Preferred: post-filing (hyphenated) | ✓ | styleguide |
| s5 | 18 | postpetition | post-petition | post-petition | ✓ | Post-petition is hyphenated | Preferred: post-petition (hyphenated) | ✓ | styleguide |
| s5 | 19 | publicly-held | publicly held | publicly held | ✓ | Publicly held is two words, no hyphen | Do not hyphenate ly adverbs; publicly held | ✓ | styleguide |
| s5 | 20 | record-keeping | recordkeeping | recordkeeping | ✓ | Recordkeeping is one word, no hyphen | Preferred: recordkeeping, one word | ✓ | styleguide |
| s5 | 20 | sub-section | subsection | subsection | ✓ | Subsection has no hyphen | Preferred: subsection, no hyphen | ✓ | styleguide |
| s5 | 21 | re-determine | redetermine | redetermine | ✓ | Redetermine is one word, no hyphen | Preferred: redetermine, one word | ✓ | styleguide |
| s5 | 21 | under-secured | undersecured | undersecured | ✓ | Undersecured is one word, no hyphen | Preferred: undersecured, one word | ✓ | styleguide |
| s5 | 22 | roll-over | rollover | rollover | ✓ | Rollover is one word as a noun | Preferred: rollover, one word | ✓ | styleguide |
| s5 | 22 | roll-up | rollup | rollup | ✓ | Rollup is one word as a noun | Preferred: rollup, one word | ✓ | styleguide |
| s5 | 22 | set-off | setoff | setoff | ✓ | Setoff is one word as a noun | Preferred: setoff, one word | ✓ | styleguide |
| s5 | 23 | super-lien | super lien | super lien | ✓ | Super lien is two words as a noun | Noun use: super lien, two words, no hyphen | ✓ | styleguide |
| s5 | 24 | super lien | super-lien | not reported | ✗ missed | Super-lien is hyphenated as a modifier | | | styleguide |
| s5 | 24 | super-priority | superpriority | superpriority | ✓ | Superpriority is one word, no hyphen | Preferred: one word, no hyphen | ✓ | styleguide |
| s5 | 25 | then current | then-current | then-current | ✓ | Use a hyphen in then-anything | then-anything uses hyphen | ✓ | styleguide |
| s5 | 25 | then Commissioner's | then-Commissioner | then-Commissioner's | ✓ wider span | Use a hyphen in then-anything | then-anything uses hyphen | ✓ | styleguide |
| s5 | 26 | timeframe | time frame | time frame | ✓ | Time frame is two words, no hyphen | Preferred: two words | ✓ | styleguide |
| s5 | 27 | towards | toward | toward | ✓ | Use toward, not towards | Use singular form | ✓ | styleguide |
| s5 | 27 | afterwards | afterward | afterward | ✓ | Use the singular afterward | Use singular form | ✓ | styleguide |
| s5 | 28 | workers compensation | workers’ compensation | workers’ compensation | ✓ | Use the plural possessive workers’ compensation | Plural possessive required | ✓ | styleguide |
| s5 | 29 | worker's compensation | workers’ compensation | workers’ compensation | ✓ | Use the plural possessive workers’ compensation | Plural possessive required | ✓ | styleguide |
| s5 | 31 | postfiling | none expected | post-filing | ✗ test bug, since fixed | | Preferred usage: post-filing (hyphenated) | | styleguide |

### Hot Spots, Quotes and Exceptions

Cases: `s6_exceptions_quotes`. Expected errors: **9**. Found: **9**, correct fix: **9** (1 with a wider span than expected), missed: **0**, false alarms: **1**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s6 | 0 | principle | principal | principal | ✓ | Principal is the correct word for a sum of money | Commonly confused words: principal (money) vs. principle | ✓ | styleguide / **spelling** |
| s6 | 1 | principal | principle | principle | ✓ | Principle is the correct word for a rule or doctrine | Commonly confused words: principle (rule) vs. principal | ✓ | styleguide / **spelling** |
| s6 | 2 | insure | ensure | ensure | ✓ | Ensure means to make certain; insure refers to insurance | Commonly confused words: ensure vs. insure | ✓ | styleguide / **spelling** |
| s6 | 3 | ensure | insure | insure | ✓ | Insure refers to insurance coverage | Commonly confused words: insure (against loss) vs. ensure | ✓ | styleguide / **spelling** |
| s6 | 4 | HIPPA | HIPAA | HIPAA | ✓ | The acronym is HIPAA | Correct acronym is HIPAA | ✓ | styleguide |
| s6 | 5 | FACTA | FATCA | FATCA | ✓ | FATCA is the Foreign Account Tax Compliance Act | FATCA is the acronym for Foreign Account Tax Compliance Act | ✓ | styleguide |
| s6 | 6 | (FATCA) | FACTA | (FACTA) | ✓ wider span | FACTA is the Fair and Accurate Credit Transactions Act | FACTA is the acronym for Fair and Accurate Credit Transactions Act; FATCA is the Foreign Account Tax Compliance Act | ✓ | styleguide |
| s6 | 7 | "unworkable" | “unworkable” | “unworkable” | ✓ | Use curled (smart) quotes | Use curled quotes | ✓ | styleguide |
| s6 | 8 | court's | court’s | court’s | ✓ | Use curled apostrophes | Use curled apostrophe | ✓ | styleguide |
| s6 | 10 | Febuary | none expected | February | ✗ false alarm | | Misspelling | | spelling |

### Capitalization

Cases: `s7_capitalization`. Expected errors: **14**. Found: **2**, correct fix: **2** (0 with a wider span than expected), missed: **12**, false alarms: **0**.

| Case | Para | Flagged text | Expected fix | Actual fix | Fix | Expected reason | Actual reason | Reason meaning | Type (expected / actual) |
|---|---|---|---|---|---|---|---|---|---|
| s7 | 0 | findings | Findings | not reported | ✗ missed | Capitalize major words in a title | | | styleguide |
| s7 | 1 | good | Good | not reported | ✗ missed | Capitalize major words in a title | | | styleguide |
| s7 | 2 | In | in | not reported | ✗ missed | Articles, the words in/on/from/upon and short prepositions stay lowercase in title case (but the last word is always capitalized) | | | styleguide |
| s7 | 3 | Upon | upon | not reported | ✗ missed | Articles, the words in/on/from/upon and short prepositions stay lowercase in title case (but the last word is always capitalized) | | | styleguide |
| s7 | 4 | both | Both | not reported | ✗ missed | Capitalize major words in a title | | | styleguide |
| s7 | 5 | over | Over | not reported | ✗ missed | Capitalize major words in a title | | | styleguide |
| s7 | 6 | is | Is | not reported | ✗ missed | Forms of to be (Is, Are, Was, Be, ...) are always capitalized in title case | | | styleguide |
| s7 | 7 | are | Are | not reported | ✗ missed | Forms of to be (Is, Are, Was, Be, ...) are always capitalized in title case | | | styleguide |
| s7 | 8 | from | From | not reported | ✗ missed | The last word of a title is always capitalized | | | styleguide |
| s7 | 9 | product | Product | not reported | ✗ missed | Capitalize each part of a hyphenated word in title case | | | styleguide |
| s7 | 10 | default | Default | Default | ✓ | Capitalize each part of a hyphenated word in title case | Each part of hyphenated word capitalized in headings | ✓ | styleguide / **capitalization** |
| s7 | 10 | party | Party | Party | ✓ | Capitalize each part of a hyphenated word in title case | Each part of hyphenated word capitalized in headings | ✓ | styleguide / **capitalization** |
| s7 | 11 | Is | is | not reported | ✗ missed | Questions are in sentence case | | | styleguide |
| s7 | 11 | Subpoena | subpoena | not reported | ✗ missed | Questions are in sentence case | | | styleguide |

### Notes by topic

- **Dates and Time:** all 31 found and fixed. One false alarm: "the CEO's decision" was flagged for a curled apostrophe (the open straight-vs-curly quote question). "Lunch is at 12:15 p.m" was typed `punctuation`, which is fair.
- **Numbers and Money:** everything found and fixed; eight fixes wrapped a neighbouring word ("6 witnesses"). Percentages, SEC release numbers and citation numbers were correctly left alone.
- **Hyphenation:** all found. One false alarm ("A third party's obligation" flagged for a curled apostrophe). The two general compound adjectives ("risk based", "long term") were typed `grammar` instead of `styleguide`.
- **Preferred Word List:** 68 of 69. Missed: "super lien claim" → "super-lien claim" (the modifier form). The verb forms (break up, carry back, roll over) and the "post petition" adverb were correctly left alone.
- **Hot Spots, Quotes and Exceptions:** all nine found. One real rule violation: "Febuary" inside a quotation was corrected, but quoted material must never be edited. The low type match is because the model used `spelling` for principle/principal and ensure/insure, which is defensible.
- **Capitalization:** 2 of 14. The model treated "Table A: Key findings and Recommendations" as plain text and skipped title case, apart from the two hyphenated words. The 0% type match is only because I labelled these `styleguide` and the model labelled them `capitalization`, which is arguably the better label.
