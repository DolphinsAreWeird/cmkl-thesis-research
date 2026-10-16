# Study 2R: positive-control check (data and mapping only)

Khant Phyo Wai, student ID 01323050. Built 2026-10-14 21:16 by code/study2r_fix/21_control_check_report.py. Nothing was tuned: no setting, window, rule or threshold of the record changed. Only the list of Seattle works behind each article changed, for every book alike.

## Short answer

- A mapping error exists. The first run tested one Seattle work per book (the largest one). The same book often sits in several Seattle works: other editions, film tie-in editions, a "with 2nd Epilogue" edition, "Part One" and "Part Two" audio and ebook editions, other spellings of the creator. Loans that moved from one edition to another looked like a fall, and loans of omitted editions were lost.
- Fix (same for all 7,427 articles): one test unit per Wikipedia article, its checkouts summed over all Seattle works attached to it. 433 originally matched works shared an article with another work; 468 further Seattle works (most below the 500-checkout floor) were attached by the record's own matching rules (ISBN, or full title and author family name, plus plain edition markers, plus a given-name check); 391 articles gained works.
- Controls, old to new: 2 of 7 with one-sided p < 0.05 became 4 of 7. Pooled tau changed from 1.152 (mean of the seven) to 1.669. The record's pass rule (pooled interval above 0 and at least 4 of 7) is met after the fix. See the table below.
- Not a mapping error: The Queen's Gambit. Its 0.7 expected checkouts are real. The work has no ebook or audiobook record before November 2020 and 0 to 7 print loans a month in the 24 fit months (April 2018 to September 2019), so any model of its own past expects almost nothing. Observed 42, tau 4.1. The one-sided rank p (0.07 old, 0.09 new) is weak only because placebo works with a near-zero base also vary a lot. Dune: the expected count (738) is high because Dune's loans stepped up in mid-2020 inside the 24 fit months and the log-linear trend carries that step forward; that is the model, not the data.
- The Duke and I: its ebook loans stop in September 2020 (the "with 2nd Epilogue" edition took some, but with no loans in the window) so the fall is real in Seattle's data; the model expects 105 and sees 46 in months 0 to +2 (audiobook jumped after Bridgerton but audiobooks are not in the primary model). This control still fails after the fix.

## Control by control

Month 0 is the release month for all seven (addendum c: no shift of the ratio 1.5 table within 8 weeks of release was found). Release months used: The Queen's Gambit 2020-10; The Duke and I 2020-12; Dune 2021-10; Where the Crawdads Sing 2022-07; American Prometheus 2023-07; Killers of the Flower Moon 2023-10; Shogun 2024-02.

### The Queen's Gambit

- Article: The Queen's Gambit (novel). Release 2020-10-23, month 0 = 2020-10.
- Seattle works used in the first run: 47460 only ("The Queen's Gambit", 537 print, 2972 ebook, 1594 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (1): 47460 "The Queen's Gambit" (original, 5103).
- Left out on purpose or not found: Das Damengambit (19 audiobook loans, German edition) and Gambito de dama (3 print loans, Spanish): other languages, not added.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 40/42, ebook 0/1457, audiobook 0/176; after the fix: print 40/42, ebook 0/1457, audiobook 0/176.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 0.7 expected, 42 observed (tau 4.12, p 0.072); after the fix 0.7 expected, 42 observed (tau 4.12, p 0.094).

### The Duke and I

- Article: The Duke and I. Release 2020-12-25, month 0 = 2020-12.
- Seattle works used in the first run: 40237 only ("The Duke and I", 1034 print, 1229 ebook, 4924 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (2): 40237 "The Duke and I" (original, 7187); 126378 "The Duke and I with 2nd Epilogue" (title+edition marker, 312).
- Left out on purpose or not found: Bridgerton Collection, Volume 1 (203 ebook loans, a box set that contains three books): not added.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 73/44, ebook 280/2, audiobook 114/1320; after the fix: print 73/44, ebook 459/2, audiobook 114/1320.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 60.5 expected, 46 observed (tau -0.27, p 0.429); after the fix 105.1 expected, 46 observed (tau -0.83, p 0.850).

### Dune

- Article: Dune (novel). Release 2021-10-22, month 0 = 2021-10.
- Seattle works used in the first run: 13343 only ("Dune", 3476 print, 9210 ebook, 19032 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (3): 13343 "Dune" (original, 31718); 69873 "Dune: Book One in the Dune Chronicles" (original, 3227); 207859 "Dune: Serie Dune, libro 1" (original, 621).
- Left out on purpose or not found: Dune: Der Wüstenplanet and Dune: Livre premier (about 20 loans, German and French) were not added (title split at a colon is not allowed); Dune Messiah and the other Dune novels have their own articles. Brian Herbert prequels are other books and stay out.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 253/88, ebook 1733/642, audiobook 1744/823; after the fix: print 253/88, ebook 1733/755, audiobook 1744/823.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 738.0 expected, 730 observed (tau -0.01, p 0.114); after the fix 738.0 expected, 843 observed (tau 0.13, p 0.070).

### Where the Crawdads Sing

- Article: Where the Crawdads Sing. Release 2022-07-15, month 0 = 2022-07.
- Seattle works used in the first run: 36910 only ("Where the Crawdads Sing", 10676 print, 17940 ebook, 19724 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (1): 36910 "Where the Crawdads Sing" (original, 48340).
- Left out on purpose or not found: La chica salvaje (6 audiobook loans, Spanish): not added.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 2231/191, ebook 7969/573, audiobook 7440/935; after the fix: print 2231/191, ebook 7969/573, audiobook 7440/935.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 183.6 expected, 764 observed (tau 1.43, p 0.055); after the fix 183.6 expected, 764 observed (tau 1.43, p 0.040).

### American Prometheus

- Article: American Prometheus. Release 2023-07-21, month 0 = 2023-07.
- Seattle works used in the first run: 5121 only ("American Prometheus: The Triumph and Tragedy of J. Robert Oppenheimer", 939 print, 594 ebook, 4249 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (2): 5121 "American Prometheus: The Triumph and Tragedy of J. Robert Op" (original, 5782); 222589 "American Prometheus: The Inspiration for the Major Motion Pi" (original, 1155).
- Left out on purpose or not found: none missing; the Oppenheimer film tie-in edition (1,155 ebook loans) was matched in the first run but not summed.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 37/91, ebook 75/76, audiobook 159/1919; after the fix: print 37/91, ebook 75/311, audiobook 159/1919.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 36.3 expected, 167 observed (tau 1.53, p 0.005); after the fix 36.3 expected, 402 observed (tau 2.40, p 0.005).

### Killers of the Flower Moon

- Article: Killers of the Flower Moon (book). Release 2023-10-20, month 0 = 2023-10.
- Seattle works used in the first run: 30993 only ("Killers of the Flower Moon: The Osage Murders and the Birth of the FBI", 4810 print, 10520 ebook, 8926 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (2): 30993 "Killers of the Flower Moon: The Osage Murders and the Birth " (original, 24256); 80715 "Killers of the Flower Moon" (title+edition marker, 11).
- Left out on purpose or not found: Adapted for Young Readers (403 loans) is a different edition for children and stays out; the 11-loan audiobook was added.
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 237/92, ebook 1524/832, audiobook 1358/950; after the fix: print 237/92, ebook 1524/832, audiobook 1358/950.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 189.4 expected, 924 observed (tau 1.58, p 0.005); after the fix 189.4 expected, 924 observed (tau 1.58, p 0.005).

### Shogun

- Article: Shōgun (novel). Release 2024-02-27, month 0 = 2024-02.
- Seattle works used in the first run: 547 only ("Shogun", 213 print, 940 ebook, 1499 audiobook checkouts over the full catalogue period).
- Seattle works after the fix (3): 547 "Shogun" (original, 2652); 73582 "Shōgun, Part Two" (title+edition marker, 1585); 74075 "Shōgun, Part One" (title+edition marker, 3477).
- Left out on purpose or not found: Shōgun: the epic novel of Japan (157 print loans, Clavell, James), Polish edition (17) and James Clavell's Shōgun (141 print loans) were not added (colon split or different title).
- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: print 0/0, ebook 173/18, audiobook 361/43; after the fix: print 0/0, ebook 173/417, audiobook 361/599.
- Expected and observed checkouts, months 0 to +2, print + ebook model: first run 24.4 expected, 18 observed (tau -0.30, p 0.746); after the fix 24.4 expected, 417 observed (tau 2.84, p 0.005).

## Controls, old and new

| control | expected old | observed old | tau old | p old | expected new | observed new | tau new | p new |
|---|---|---|---|---|---|---|---|---|
| The Queen's Gambit | 0.7 | 42 | 4.12 | 0.072 | 0.7 | 42 | 4.12 | 0.094 |
| The Duke and I | 60.5 | 46 | -0.27 | 0.429 | 105.1 | 46 | -0.83 | 0.850 |
| Dune | 738.0 | 730 | -0.01 | 0.114 | 738.0 | 843 | 0.13 | 0.070 |
| Where the Crawdads Sing | 183.6 | 764 | 1.43 | 0.055 | 183.6 | 764 | 1.43 | 0.040 |
| American Prometheus | 36.3 | 167 | 1.53 | 0.005 | 36.3 | 402 | 2.40 | 0.005 |
| Killers of the Flower Moon | 189.4 | 924 | 1.58 | 0.005 | 189.4 | 924 | 1.58 | 0.005 |
| Shogun | 24.4 | 18 | -0.30 | 0.746 | 24.4 | 417 | 2.84 | 0.005 |

Record pass rule, first run: ('FAIL', '1.152', '0.217', '2.383', '2'); after the fix: ('PASS', '1.669', '0.523', '2.847', '4') (result, pooled tau, interval low, high, number of tests with p < 0.05).

## Full 2R analysis, old and new (steps 10 to 15 rerun on the article-level counts; main set, print and ebook)

| quantity | first run | after the fix |
|---|---|---|
| tests | Tests: 2619 work-shift rows, 2372 with a usable fit and window; 173 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 21 with no checkouts in the window (tau = -infinity; out of the pooled means); 2178 tests in the pooled | Tests: 2422 work-shift rows, 2255 with a usable fit and window; 145 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 3 with no checkouts in the window (tau = -infinity; out of the pooled means); 2107 tests in the pooled  |
| pooled | 2178 tests, 1347 works, mean tau 0.084 (0.030 to 0.137) | 2107 tests, 1295 works, mean tau 0.103 (0.047 to 0.152) |
| H1 | 0.086 per doubling (95% interval 0.045 to 0.128), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.042 to 0.131, p = 0.0005. | 0.082 per doubling (95% interval 0.039 to 0.125), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.039 to 0.125, p = 0.0005. |
| H2 | 0.302 (95% interval 0.182 to 0.424); mean tau 0.335 (281 tests) against 0.033 (1415 tests): **supported (95% interval above 0)**. Clustered by article: 0.173 to 0.434. | 0.305 (95% interval 0.177 to 0.438); mean tau 0.361 (265 tests) against 0.056 (1374 tests): **supported (95% interval above 0)**. Clustered by article: 0.174 to 0.435. |
| size | 0.146 (95% interval 0.080 to 0.218); log2 duration coefficient in the same model -0.013 (-0.086 to 0.051); correlation of log2 duration and log2 peak 0.72. | 0.152 (95% interval 0.085 to 0.229); log2 duration coefficient in the same model -0.022 (-0.093 to 0.042); correlation of log2 duration and log2 peak 0.72. |
| Hansen | threshold 4 weeks (shifts of 4 weeks or less: mean tau 0.031, 1766 tests; longer: 0.313, 412 tests; difference 0.282, 95% interval at the re-estimated threshold 0.184 to 0.410); bootstrap interval of the threshold 2 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.043, 3.0: 0.208, 4.0: 0.606, 5.0: 0.088, 6.0: 0.05, 7.0: 0.004}); likelihood-ratio set [3, 4, 5, 6]; the step explains 0.73% | threshold 4 weeks (shifts of 4 weeks or less: mean tau 0.050, 1714 tests; longer: 0.334, 393 tests; difference 0.284, 95% interval at the re-estimated threshold 0.181 to 0.432); bootstrap interval of the threshold 2 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.036, 3.0: 0.134, 4.0: 0.663, 5.0: 0.112, 6.0: 0.048, 7.0: 0.006}); likelihood-ratio set [3, 4, 5, 6]; the step explains 0.77 |

Full tables: data/reports/study2r_fix_results.md (new) and study2r_results.md (first run, unchanged). Code: code/study2r_fix/ (09 builds the article-level counts; 12 to 15 are the 2R steps with outputs redirected to data/db/study2r_fix and data/reports/study2r_fix_*). The log row is in prereg/DEVIATIONS.md (Study 2R, 21:12). The simulation tests (step 11) test the tools, not the mapping, and were not rerun.

Limits. The attached editions follow the record's own matching rules, made stricter for added works; some editions with colon subtitles or other languages are still missing, so a few books remain partly under-counted. The article list is the original one (articles with a single work of at least 500 checkouts); books whose editions only reach 500 together are not added. Works on a series article (for example several books redirecting to one series page) are now one unit, as the user asked.
