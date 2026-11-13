# Fixes

Five problems were fixed and committed. Each section shows the failure, then the full score table from the run before the fix and the run after it.

Correct fix counts a tag when the resulting text matches, even if the reason uses different words. The latest run is `tests/outputs/2026-11-14T00-59-57`: **231 of 236 (98%)**.

## 1. Lowercase prose was left lowercase

Commit `d9f86b6`.

A paragraph written in lowercase is still normal prose. The prompt now capitalizes the first word of a sentence, the pronoun I, and names of people, places, and months.

Failures before, run `2026-11-13T20-17-45`:

- `the` → `The` (twice)
- `i` → `I`
- `maria` → `Maria`
- `john` → `John`
- `london` → `London`
- `paris` → `Paris`
- `texas` → `Texas`
- `march` → `March`

`s7` was 11 of 26. The next run, `2026-11-13T20-19-30`, has the new prompt, but the comment bug in section 2 deleted those tags, so the same nine words are still listed as missed and `s7` is only 14 of 26. They show up in the file after section 2.

Before: `tests/outputs/2026-11-13T20-17-45` — 215 of 239 (90%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 31 (100%) | 0 | 1 | 97% | 48% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 0 | 100% | 22% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 0% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 1 | 98% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 56% | 0% |
| s7_capitalization | 26 | 11 (42%) | 12 | 0 | 100% | 0% |
| general | 18 | 14 (78%) | 3 | 1 | 93% | 0% |
| sample_input | 45 | 41 (91%) | 0 | 2 | 87% | 9% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

After the prompt, still blocked by the comment bug: `tests/outputs/2026-11-13T20-19-30` — 214 of 239 (90%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 27 (87%) | 0 | 1 | 97% | 52% |
| s2_numbers_money | 18 | 17 (94%) | 1 | 2 | 100% | 59% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 0% |
| s5_wordlist_i_z | 43 | 41 (95%) | 0 | 2 | 98% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 44% | 11% |
| s7_capitalization | 26 | 14 (54%) | 12 | 0 | 100% | 0% |
| general | 18 | 12 (67%) | 3 | 0 | 93% | 7% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 98% | 11% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

## 2. A `<p>` inside a comment was proofread

Commit `72d99b7`.

`s7` contains a comment with the characters `<p>` in it. The scanner treated that as a paragraph. The edit landed inside the comment, the check failed, and the retry deleted the real tags. The model had already returned the nine tags in section 1. The written file looked untagged.

After the fix, tags inside `<!-- -->` are ignored. Those nine words are tagged, and `s7` goes from 14 of 26 to 23 of 26.

Before: the `2026-11-13T20-19-30` table in section 1 — 214 of 239 (90%).

After: `tests/outputs/2026-11-13T21-38-15` — 223 of 239 (93%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 27 (87%) | 0 | 1 | 97% | 52% |
| s2_numbers_money | 18 | 17 (94%) | 1 | 2 | 100% | 59% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 0% |
| s5_wordlist_i_z | 43 | 41 (95%) | 0 | 2 | 98% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 44% | 11% |
| s7_capitalization | 26 | 23 (88%) | 3 | 0 | 100% | 4% |
| general | 18 | 12 (67%) | 3 | 0 | 93% | 7% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 98% | 11% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

Still missed on `s7` after this run: `lincoln`, `brown`, and `constitution`.

## 3. Stock phrases were shortened when they were not errors

Commit `93bcb66`. This removes the rule added in `a2d383e`.

The assignment lists Clarity as a category and gives no rule for wordy phrases. A prompt line treated any stock phrase as an error. It did tag the three phrases in `general`:

- `at this point in time` → `now`
- `due to the fact that` → `because`
- `In the event that` → `If`

It also invented a change the test does not want:

- `Moving forward` → `Going forward`

Those three sentences were removed from `general`, and the prompt line was removed. `sample_input` extras fell from 2 to 1. The remaining extra is `organisations` → `organizations`.

Before: `tests/outputs/2026-11-13T22-52-20` — 228 of 239 (95%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 27 (87%) | 0 | 1 | 97% | 52% |
| s2_numbers_money | 18 | 17 (94%) | 1 | 2 | 100% | 47% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 1 | 100% | 4% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 2 | 100% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 56% | 11% |
| s7_capitalization | 26 | 23 (88%) | 2 | 0 | 100% | 4% |
| general | 18 | 16 (89%) | 0 | 0 | 100% | 28% |
| sample_input | 45 | 45 (100%) | 0 | 2 | 93% | 9% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 10% |

After: `tests/outputs/2026-11-13T23-32-38` — 227 of 236 (96%). `general` expects 15 because the three wordy sentences are gone.

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 29 (94%) | 0 | 1 | 97% | 39% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 0 | 100% | 11% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 12% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 1 | 100% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 0 | 44% | 0% |
| s7_capitalization | 26 | 23 (88%) | 2 | 0 | 100% | 8% |
| general | 15 | 12 (80%) | 0 | 0 | 93% | 13% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 91% | 9% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

## 4. A time with no minutes gained `:00`

Commit `ace65b5`.

The style guide's only time sample is `6:00 a.m.` The model copied the minutes. The prompt now says to change only the characters the rule requires.

Failures before, run `2026-11-14T00-17-33`:

- `9am` → `9:00 a.m.` (expected `9 a.m.`)
- `6pm` → `6:00 p.m.` (expected `6 p.m.`)
- `12:15 p.m` was wrapped as `p.m and` → `p.m. and`, so the period counted as a miss and an extra

After, run `2026-11-14T00-46-39`:

- `9am` → `9 a.m.`
- `6pm` → `6 p.m.`
- `12:15 p.m` → `12:15 p.m.`

`s1` is 31 of 31, with no misses and no extras.

Before: `tests/outputs/2026-11-14T00-17-33` — 226 of 236 (96%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 28 (90%) | 1 | 2 | 100% | 37% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 0 | 100% | 50% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 8% |
| s5_wordlist_i_z | 43 | 42 (98%) | 0 | 2 | 100% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 0 | 56% | 0% |
| s7_capitalization | 26 | 23 (88%) | 2 | 0 | 100% | 4% |
| general | 15 | 12 (80%) | 0 | 0 | 93% | 7% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 91% | 11% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

After: `tests/outputs/2026-11-14T00-46-39` — 226 of 236 (96%). `s1` is clean. `s7` fell to 21 of 26 on this run because `president lincoln` was one tag. Section 5 fixes that.

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 31 (100%) | 0 | 0 | 97% | 42% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 0 | 100% | 50% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 85% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 0% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 1 | 100% | 0% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 44% | 0% |
| s7_capitalization | 26 | 21 (81%) | 3 | 0 | 91% | 4% |
| general | 15 | 14 (93%) | 0 | 1 | 93% | 7% |
| sample_input | 45 | 42 (93%) | 3 | 1 | 93% | 12% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

## 5. A title and a surname were one tag

Commit `13b5709`.

A title and the person's name are separate tags. A proper name of more than one word is one tag. `of` and `the` stay outside when they only join two names.

Failure before, run `2026-11-14T00-46-39`:

- `president lincoln` → `President Lincoln`

That one tag made `president` a wrong fix and `lincoln` a miss.

After, run `2026-11-14T00-59-57`:

- `president` → `President`
- `lincoln` → `Lincoln`

`Securities and Exchange Commission` stays one tag. `s7` rose from 21 of 26 to 23 of 26. `sample_input` rose from 42 of 45 to 45 of 45.

Before: the table in section 4, 226 of 236 (96%).

After: `tests/outputs/2026-11-14T00-59-57` — 231 of 236 (98%)

| Case | Expected | Correct fix | Missed | Extra | Type | Reason, same words |
|---|---|---|---|---|---|---|
| s1_dates_time | 31 | 31 (100%) | 0 | 0 | 97% | 52% |
| s2_numbers_money | 18 | 18 (100%) | 0 | 2 | 100% | 22% |
| s3_hyphenation | 13 | 13 (100%) | 0 | 1 | 69% | 0% |
| s4_wordlist_a_h | 26 | 26 (100%) | 0 | 0 | 100% | 8% |
| s5_wordlist_i_z | 43 | 42 (98%) | 1 | 2 | 100% | 2% |
| s6_exceptions_quotes | 9 | 9 (100%) | 0 | 1 | 44% | 0% |
| s7_capitalization | 26 | 23 (88%) | 2 | 0 | 100% | 4% |
| general | 15 | 14 (93%) | 0 | 0 | 100% | 0% |
| sample_input | 45 | 45 (100%) | 0 | 1 | 91% | 11% |
| example_input | 10 | 10 (100%) | 0 | 0 | 90% | 20% |

Still wrong after this run:

- `s5`: `super lien` was not changed to `super-lien` before `claim`
- `s7`: `supreme court of the united states` is still one tag, so `united states` is missed
- `s7`: `constitution` is still lowercase
- `general`: `Their` → `They're` instead of `They’re`
- `s2`: `5 percent` → `five`, and `12 percent` → `twelve`
- `s3`: `party's` → `party’s`
- `s5`: `postfiling` → `post-filing`, and `post petition` → `post-petition`
- `s6`: `vs.` → `versus` in `Smith vs. Jones`
- `sample_input`: `organisations` → `organizations`
