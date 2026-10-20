# Wikipedia-led tests: how much do the results depend on one choice? (checks R1 to R7)

Khant Phyo Wai, 01323050.

Made 2026-10-20 21:39 +0700 by `code/main_study/wiki_led/90_robustness.py` (the numbers) and `91_robustness_report.py` (this file). The seven checks are fixed in `prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json` (SHA-256 `36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52`). Every number is in `data/reports/wiki_led_robustness.json`.

## Does any conclusion depend on a single choice?

**Short answer: no decision rule depends on a single choice.** A1, A2 and A3 (Test A) and B1 and B2 (Test B) come out the same way under every check that applies to them, and so do the two alert-list results that matter most: the Wikipedia-only list beats chance, and it catches rises the library list misses. Two results do depend on one choice: in one short test year (2020) adding Wikipedia to the library list lowered its hit rate, and the answer to the 90% question of Test D depends on the length of the list. Each line gives the main result first, then the range it takes under the checks.

- **Wikipedia alone ranks which books will rise (A1, Test A): holds.** Change rank 0.133 (0.124 to 0.142). With each of five seeds 0.133 to 0.134; above zero in every test year, from 0.085 (2020) to 0.151 (2022); 0.134 without the three bot months.
- **Wikipedia adds to the library's own history (A2): holds.** HW minus H 0.0094 (0.0074 to 0.0113). Seeds 0.0088 to 0.0094; above zero in every year, 0.0035 (2020) to 0.0119 (2023); 0.0092 without the bot months.
- **Wikipedia alone flags surges (A3): holds.** Surge AP ratio 3.45 (3.13 to 3.78). Seeds 3.43 to 3.47; above 1 in all 8 years; 3.45 without the bot months.
- **The Wikipedia-only alert list beats a random pick: holds.** In its top 20, 57.9% of the books rose by 50% the next month, against 11.3% of all books. It stays above the base rate for every rise size (3.1 times at 25%, 5.1 at 50%, 9.7 at 100%), every list length (5.7 times at 10 places down to 3.5 at 100), every year and every seed, and in Test D.
- **Adding Wikipedia does not lower the library list's hit rate: holds, except in one year.** Top 20 over all months: HW 93.7%, H 92.1%; HW is not below H (0.5-point tie rule) at any rise size, list length or seed, without the bot months, or in Test D. **Difference 1:** in 2020 HW is below H, 85.0% against 89.0%. 2020 has only 5 scored months (April to September 2020 have missing library data and are not scored), so the gap is 4 of 100 list places. It comes from origin 2020-10 (2 places fewer) and origin 2020-11 (3 places fewer), the first scored months after that gap, when the six-month normal rests on only 1 and 2 months of loans. Over all 78 months HW is 2 or more places behind H in only 3 months, 2 of them in 2020; it is ahead in 27 months and level in 38.
- **Wikipedia catches rises the library list misses (R6): holds.** Of the rises that are not in the library's top 50, Wikipedia's top 50 catches 2.3%, against 0.70% for a random list of 50 (3.2 times, interval 3.0 to 3.5).
- **Wikipedia alone predicts new books' early demand (B1, Test B): holds.** Spearman 0.127 (0.115 to 0.138); interval above zero in all 8 years, from 0.068 (2026) to 0.167 (2019).
- **Wikipedia adds to the library model for new books (B2): holds.** 0.0237 (0.0191 to 0.0299) over L, above zero in every year. Over a stronger library model (R5) the addition is smaller but still above zero: 0.0107 without the theme, 0.0122 with the theme from first-month records, 0.0085 with the features as fixed. The review found that the theme as fixed is not known when a book arrives (it partly reflects loans inside the six-month outcome window), so the last number understates Wikipedia; see R5.
- **Test D (all books, by format): holds in both runs.** The Wikipedia-only list beats the base rate and HW is not below H at every rise size and list length, in the original and the corrected run (Wikipedia-only top 20: 47.4% and 45.5%, base rate 11.6%).
- **Difference 2: the 90% question for Test D depends on the list length.** Addendum d asks whether library + Wikipedia reaches 90% in every format with a top 20. The answer is no (corrected run: 2019-2026 print 87.3%, ebook 88.0%, audiobook 88.6%; 2024-2026 print 85.0%, ebook 92.3%, audiobook 93.1%). With a top 10 it is yes in every format and both periods (lowest 90.5%); with a top 50 or 100 it is no everywhere (highest 87.5%). So 90% describes a short list, not the model as such, and the corrected run gives the same answers as the original.

The full table of 41 comparisons is in the section "Every comparison" near the end.

## What this is

Each check changes one choice and looks at how the reported results move: the size of a rise that counts, the random seed, the test year, three months of unusual Wikipedia traffic, a stronger library model for new books, and the length of the alert list. The checks are descriptive. Nothing was tuned, and no setting of any model or alert list was chosen from these numbers.

- **Models.** W: Wikipedia features only (tree model, no library input). H: the book's own library history only (trees). HW: both. In Test B, L is the library model, W Wikipedia and LW both. "Naive" repeats last month's change; "rule" is the no-fitting Wikipedia rule of Test A.
- **Measures.** Change rank: the mean over months of the Spearman correlation between predicted and actual change in loans (Test B: Spearman between predicted and actual loans in the first six months, inside each test year). Surge AP ratio: average precision for surges divided by the share of surges, so 1 means no better than chance.
- **Rose by X%** means next month's loans are at least X% above the book's recent normal (M6, the median of its last six months), compared as ln(1 + loans) differences like everywhere else in the tests; 50% is the size used in the alert tables so far. **Surged** is the original surge flag (at least double and at least 5 more loans than normal).
- **Top k list** is the k books with the highest predicted rise in a month (Test D: within each format and month). **Hit rate** is the share of list places taken by a book that rose. **Base rate** is the share of all books that rose, which is what a randomly picked list would score (Test A: averaged over months; Test D: over all rows, as in the Test D report).
- **Data.** **Test A** uses the corrected files (`test_a_rows_c.parquet`, `test_a_preds_c.parquet`: weeks before an article existed are missing, not zero). **Test D** is shown for the original predictions (`test_d_preds.parquet`) and the corrected ones (`test_d_preds_c.parquet`, rows `test_d_rows_c.parquet`) side by side, written "original / corrected". **Test B** is unaffected by the correction.
- **Intervals** are 95% from 2,000 draws with seed 20261020: blocks of 3 consecutive months for Test A, author clusters for Test B (as `30_test_b.py`), exact binomial limits over list places for Test D (as addendum d). A test year holds 5 to 12 scored months, so by-year intervals are rough; a set of fewer than 6 months gets no interval.
- **Choices the addendum leaves open**, fixed here before looking: ties in a prediction are broken by one fixed random order (seed 20261020); the rise threshold is compared exactly, with equality counted (the stored single-precision flag differs from this in 3 of 1,984,302 Test D rows at 50%); R1 uses the top 20 and top 50 lists, the sizes of the earlier alert tables; in R6 the library model is the library-only tree model (H).

## R1. How big a rise counts (25%, 50%, 100%)

Hit rate of the top 20 and top 50 lists when a rise is counted from 25%, 50% or 100% above the normal. The last row of each block is the base rate.

**Test A**

| List | Model | Rose by 25% | Rose by 50% | Rose by 100% |
| :--- | :--- | ---: | ---: | ---: |
| top 20 | Wikipedia only (W) | 71.3% (67.6 to 74.6) | 57.9% (54.5 to 61.1) | 40.7% (37.4 to 43.9) |
| top 20 | Wikipedia rule (no fitting) | 39.4% (36.6 to 42.4) | 27.4% (24.8 to 30.2) | 16.0% (13.6 to 18.4) |
| top 20 | Library history (H) | 94.4% (92.9 to 95.9) | 92.1% (90.2 to 93.9) | 87.5% (85.1 to 90.1) |
| top 20 | Library + Wikipedia (HW) | 95.3% (93.5 to 96.9) | 93.7% (91.8 to 95.4) | 89.1% (86.7 to 91.5) |
| top 20 | Repeat last month (naive) | 92.8% (89.9 to 95.1) | 89.6% (86.1 to 92.4) | 84.7% (80.1 to 88.2) |
| top 20 | *base rate (any book)* | 22.8% | 11.3% | 4.2% |
| top 50 | Wikipedia only (W) | 62.9% (60.3 to 65.5) | 48.3% (46.1 to 50.5) | 31.7% (29.5 to 34.1) |
| top 50 | Wikipedia rule (no fitting) | 43.5% (41.2 to 45.9) | 30.6% (28.6 to 32.8) | 18.1% (16.5 to 19.7) |
| top 50 | Library history (H) | 89.3% (87.2 to 91.2) | 84.8% (82.5 to 87.0) | 75.2% (72.2 to 78.1) |
| top 50 | Library + Wikipedia (HW) | 90.3% (88.5 to 92.0) | 86.1% (84.2 to 88.0) | 76.6% (73.8 to 79.3) |
| top 50 | Repeat last month (naive) | 87.6% (84.3 to 90.0) | 82.2% (78.1 to 85.3) | 72.4% (67.9 to 76.0) |
| top 50 | *base rate (any book)* | 22.8% | 11.3% | 4.2% |

**Test D, all formats, 2019-2026** (original / corrected; the exact 95% intervals, in the JSON, are at most plus or minus 1.4 points for a top 20 and 0.9 for a top 50)

| List | Model | Rose by 25% | Rose by 50% | Rose by 100% |
| :--- | :--- | ---: | ---: | ---: |
| top 20 | Wikipedia only (W) | 60.1% / 58.7% | 47.4% / 45.5% | 30.4% / 29.2% |
| top 20 | Library history (H) | 90.3% / 90.3% | 87.3% / 87.3% | 81.4% / 81.4% |
| top 20 | Library + Wikipedia (HW) | 90.9% / 90.7% | 87.9% / 88.0% | 82.1% / 82.0% |
| top 20 | Repeat last month (naive) | 87.6% / 87.6% | 84.2% / 84.2% | 78.1% / 78.1% |
| top 20 | *base rate (any book)* | 23.0% / 23.0% | 11.6% / 11.6% | 4.2% / 4.2% |
| top 50 | Wikipedia only (W) | 51.4% / 51.1% | 37.6% / 37.2% | 21.8% / 21.7% |
| top 50 | Library history (H) | 85.1% / 85.1% | 80.1% / 80.1% | 69.5% / 69.5% |
| top 50 | Library + Wikipedia (HW) | 86.1% / 86.0% | 81.1% / 81.2% | 70.4% / 70.4% |
| top 50 | Repeat last month (naive) | 82.2% / 82.2% | 77.1% / 77.1% | 66.8% / 66.8% |
| top 50 | *base rate (any book)* | 23.0% / 23.0% | 11.6% / 11.6% | 4.2% / 4.2% |

- Test A: the Wikipedia-only list is above the base rate in all 6 cells. Its top-20 hit rate is 3.1 times the base rate at 25%, 5.1 times at 50% and 9.7 times at 100%, so a stricter rise makes the list look better against chance even though its hit rate falls.
- Test A: the library list (H) is above the Wikipedia-only list in 6 of 6 cells, and the Wikipedia-only list is above the no-fitting rule in 6 of 6. Library + Wikipedia is above the library list in 6 of 6 cells (and not more than 0.5 points below it in 6 of 6).
- Test D, all formats: the Wikipedia-only list is above the base rate in every cell of the original run and of the corrected run (top-20 hit rate over the base rate at 25%, 50% and 100%: original 2.6, 4.1 and 7.2 times; corrected 2.6, 3.9 and 6.9 times). Library + Wikipedia is not more than 0.5 points below the library list in 6 of 6 cells (original) and 6 of 6 cells (corrected).
- The correction moves the Wikipedia-only top 20 from 47.4% to 45.5% at a 50% rise. The library list is the same in both runs (87.3% and 87.3%), as it should be: it uses no Wikipedia input.

## R2. Five random seeds (Test A, corrected rows)

W, H and HW were refitted five times with the same settings and walk-forward as `10_test_a.py`, changing only the seed of the tree models (20261020 to 20261024). The top-20 hit rate counts rises of 50%.

| Seed | W change rank | H change rank | HW change rank | HW minus H | W top-20 hit | H top-20 hit | HW top-20 hit |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20261020 | 0.1335 | 0.3503 | 0.3597 | 0.0094 | 57.9% | 92.1% | 93.7% |
| 20261021 | 0.1333 | 0.3503 | 0.3595 | 0.0091 | 57.6% | 92.3% | 93.1% |
| 20261022 | 0.1338 | 0.3506 | 0.3595 | 0.0090 | 57.9% | 91.9% | 93.6% |
| 20261023 | 0.1337 | 0.3507 | 0.3598 | 0.0090 | 57.2% | 92.3% | 93.7% |
| 20261024 | 0.1336 | 0.3507 | 0.3595 | 0.0088 | 56.3% | 92.1% | 93.5% |
| **mean** | 0.1336 | 0.3505 | 0.3596 | 0.0091 | 57.4% | 92.1% | 93.5% |
| **range (highest minus lowest)** | 0.0005 | 0.0004 | 0.0003 | 0.0006 | 1.5 points | 0.4 points | 0.6 points |

- The 5 seeds differ by at most 0.0005 in W change rank, 0.0004 in H and 0.0003 in HW. The month-block 95% interval of the main run is about plus or minus 0.009 for W, 0.008 for H and 0.008 for HW, so the seed spread in W is 0.06 times that half-width.
- HW minus H is above zero in 5 of 5 seeds (lowest 0.0088, highest 0.0094; the half-width of its month-block interval is 0.0019).
- The top-20 hit rate moves by up to 1.5 points for W, 0.4 for H and 0.6 for HW between seeds; the W surge AP ratio runs from 3.43 to 3.47.
- Check: the refit with seed 20261020 reproduces the stored corrected predictions (largest difference 5.6e-17).

## R3. By test year

Test A: the headline measures inside each test year (the year of the month being predicted; 2019 starts with origin 2019-01; 2026 has origins 2025-12 to 2026-07). Test B: the same for new books, by year of their first library month.

**Test A**

| Year | Months | Base rate (50%) | W change rank | H change rank | HW change rank | HW minus H (interval) | W surge AP ratio | W top-20 hit | H top-20 hit | HW top-20 hit |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 11 | 9.8% | 0.123 | 0.335 | 0.344 | 0.0088 (0.0033 to 0.0136) | 3.31 | 53.2% | 85.9% | 89.1% |
| 2020 | 5 | 11.3% | 0.085 | 0.328 | 0.332 | 0.0035 | 3.29 | 52.0% | 89.0% | 85.0% |
| 2021 | 12 | 12.9% | 0.144 | 0.364 | 0.372 | 0.0078 (0.0036 to 0.0120) | 3.08 | 58.3% | 91.7% | 91.2% |
| 2022 | 12 | 11.3% | 0.151 | 0.358 | 0.370 | 0.0118 (0.0086 to 0.0159) | 3.91 | 58.8% | 92.9% | 95.4% |
| 2023 | 12 | 11.1% | 0.147 | 0.357 | 0.369 | 0.0119 (0.0086 to 0.0147) | 3.69 | 60.4% | 95.8% | 96.7% |
| 2024 | 8 | 11.4% | 0.125 | 0.365 | 0.373 | 0.0085 (0.0064 to 0.0111) | 3.17 | 55.6% | 95.6% | 97.5% |
| 2025 | 10 | 11.7% | 0.134 | 0.349 | 0.359 | 0.0107 (0.0037 to 0.0168) | 3.48 | 59.0% | 92.5% | 96.0% |
| 2026 | 8 | 10.9% | 0.124 | 0.330 | 0.338 | 0.0083 (0.0042 to 0.0132) | 3.92 | 63.1% | 91.9% | 95.0% |

Months: 2020 has 5 (library months with missing or near-empty data are not scored); a year with fewer than 6 months gets no interval.

- W change rank is above zero in 8 of 8 years (interval above zero in 7 of the 7 years that have one); it runs from 0.085 (2020) to 0.151 (2022).
- HW minus H is above zero in 8 of 8 years (interval above zero in 7 of 7); it runs from 0.0035 (2020) to 0.0119 (2023).
- The W surge AP ratio is above 1 in 8 of 8 years, and the W top-20 hit rate is above that year's base rate in 8 of 8.
- HW's top-20 hit rate is below H's in 2020 by 4.0 points (5 scored months) and in 2021 by 0.4 points (12 scored months, under 0.5 points, a tie by the rule of addendum c).
  - 2020, places taken by a book that rose, HW minus H, by origin month: 2019-12 0, 2020-01 0, 2020-02 +1, 2020-10 -2, 2020-11 -3 (list places: 100).
  - 2021, places taken by a book that rose, HW minus H, by origin month: 2020-12 -1, 2021-01 +1, 2021-02 0, 2021-03 -1, 2021-04 0, 2021-05 -1, 2021-06 +1, 2021-07 0, 2021-08 0, 2021-09 0, 2021-10 0, 2021-11 0 (list places: 240).
- Over all 78 scored months, the HW top 20 holds more rising books than the H top 20 in 27 months, as many in 38 and fewer in 13; HW is 2 or more places behind in 3 months.

**Test B** (top-10% precision: share of the predicted top 10% that is in the actual top 10%; the base rate is 10%)

| Year | New books | W Spearman | L Spearman | LW Spearman | LW minus L | W top-10% | L top-10% | LW top-10% |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 20,467 | 0.167 (0.151 to 0.184) | 0.407 (0.393 to 0.421) | 0.427 (0.414 to 0.440) | 0.0199 (0.0140 to 0.0265) | 24.4% | 36.0% | 38.4% |
| 2020 | 8,261 | 0.138 (0.111 to 0.167) | 0.320 (0.291 to 0.348) | 0.346 (0.319 to 0.373) | 0.0261 (0.0154 to 0.0375) | 21.5% | 32.5% | 35.8% |
| 2021 | 22,414 | 0.128 (0.110 to 0.147) | 0.347 (0.327 to 0.365) | 0.367 (0.349 to 0.385) | 0.0204 (0.0149 to 0.0264) | 23.7% | 31.8% | 35.3% |
| 2022 | 21,809 | 0.132 (0.115 to 0.149) | 0.366 (0.349 to 0.383) | 0.386 (0.371 to 0.402) | 0.0204 (0.0143 to 0.0274) | 23.8% | 35.4% | 38.0% |
| 2023 | 21,779 | 0.142 (0.120 to 0.162) | 0.364 (0.342 to 0.383) | 0.384 (0.361 to 0.404) | 0.0209 (0.0124 to 0.0313) | 22.1% | 35.3% | 38.1% |
| 2024 | 16,180 | 0.122 (0.102 to 0.140) | 0.340 (0.321 to 0.359) | 0.362 (0.344 to 0.380) | 0.0220 (0.0120 to 0.0358) | 21.3% | 32.8% | 34.6% |
| 2025 | 20,336 | 0.120 (0.100 to 0.139) | 0.371 (0.348 to 0.394) | 0.396 (0.376 to 0.420) | 0.0259 (0.0177 to 0.0347) | 20.5% | 34.0% | 36.0% |
| 2026 | 3,724 | 0.068 (0.030 to 0.108) | 0.275 (0.237 to 0.314) | 0.310 (0.275 to 0.346) | 0.0343 (0.0200 to 0.0495) | 21.2% | 32.4% | 37.0% |
| **all years** | 134,970 | 0.127 (0.115 to 0.138) | 0.349 (0.337 to 0.361) | 0.372 (0.362 to 0.383) | 0.0237 (0.0191 to 0.0299) | 22.3% | 33.8% | 36.6% |

- W Spearman has its interval above zero in 8 of 8 years and runs from 0.068 (2026) to 0.167 (2019). The 2026 books are few (3,724, first months January and February 2026).
- LW minus L is above zero in 8 of 8 years (interval above zero in 8); it runs from 0.0199 (2019) to 0.0343 (2026).

## R4. Without the origin months 2025-04 to 2025-06 (Test A)

Wikimedia reported automated traffic counted as user views in those months. The predictions are the same; only the scoring leaves the three origin months out (the models were not refitted). The last column shows the three months alone, without an interval (three months cannot be resampled in blocks of three).

| Measure | All scored months | Without 2025-04 to 2025-06 | Change | The three months alone |
| :--- | ---: | ---: | ---: | ---: |
| W change rank | 0.133 (0.124 to 0.142) | 0.134 (0.124 to 0.142) | +0.0003 | 0.125 |
| H change rank | 0.350 (0.343 to 0.358) | 0.352 (0.345 to 0.359) | +0.0017 | 0.307 |
| HW change rank | 0.360 (0.352 to 0.368) | 0.361 (0.354 to 0.369) | +0.0016 | 0.320 |
| naive change rank | 0.233 (0.217 to 0.246) | 0.234 (0.219 to 0.247) | +0.0011 | 0.206 |
| HW minus H | 0.0094 (0.0074 to 0.0113) | 0.0092 (0.0073 to 0.0112) | -0.0002 | 0.0135 |
| W minus no-fitting rule | 0.061 (0.056 to 0.067) | 0.061 (0.055 to 0.067) | -0.0002 | 0.067 |
| W surge AP ratio | 3.45 (3.13 to 3.78) | 3.45 (3.14 to 3.81) | 0.00 | 3.60 |
| H surge AP ratio | 10.78 (9.86 to 11.68) | 10.77 (9.81 to 11.77) | -0.01 | 10.31 |
| HW surge AP ratio | 11.19 (10.24 to 12.11) | 11.18 (10.21 to 12.23) | -0.01 | 10.90 |
| W top-20 hit rate (50%) | 57.9% (54.5 to 61.1) | 57.6% (54.2 to 60.9) | -0.3 points | 65.0% |
| H top-20 hit rate (50%) | 92.1% (90.2 to 93.9) | 92.3% (90.3 to 94.1) | +0.2 points | 86.7% |
| HW top-20 hit rate (50%) | 93.7% (91.8 to 95.4) | 93.7% (91.7 to 95.5) | 0.0 points | 93.3% |
| Base rate of a 50% rise | 11.3% | 11.4% | 0.0 points | 10.2% |
| Months scored | 78 | 75 | -3 | 3 |

- Without the three months, W change rank moves by +0.0003, HW minus H by -0.0002 and the W top-20 hit rate by -0.3 points. A1 (W change-rank interval above zero) holds, A2 (HW minus H interval above zero) holds and A3 (W surge-ratio interval above 1) holds.
- In the three months alone, W change rank is 0.125 against 0.133 over all months, and the W top-20 hit rate is 65.0% against 57.9%. Three months are too few to read this as a real difference.
- Limit: the inflated weeks also enter the 26-week normal behind r4, r1 and rmax for about six months after June 2025, and the 2026 models were trained on rows that include the three months; this check removes only the three origin months from the scoring, as the addendum fixes.

## R5. A stronger library model for new books (Test B)

L+ is the library model of Test B plus catalogue information the library has when it acquires a work, as fixed in the addendum: the broad theme (the level-1, or B-level, theme node with the highest strength in `work_theme.parquet`, or none; where nodes tie, the file's own first rank), the first year minus the publication year (`pub_year_min`), and whether the creator came only from the title field. L+W adds the Wikipedia features. Everything else is as in `30_test_b.py`: the same rows (books whose first month a data gap may have shifted are left out), the same walk-forward, the same tree settings and the same author-cluster bootstrap with the same draws.

**Are the three features known when a book arrives? Not fully (found in the review of 20 Oct 2026).** They are built from the work's catalogue records, and a record shows up in the Seattle data only when it is first lent. 57.2% of the works have a record first lent after the work's first month (47.2% after month 5, that is after the six-month outcome window), and the features as fixed use records of all years:

- **Theme:** 82.6% of the works have one as fixed, but only 70.1% when it is built from the records first lent in the work's first month. 22,214 works get their theme only from later records and 6,900 get a different one. Having a theme as fixed goes with more early loans: works with a theme had a median of 19 loans in their first six months and works without one 8; with the first-month theme the medians are 17 and 17. So the theme as fixed partly carries the outcome.
- **Publication year:** the gap differs for 1,753 works (1.0%). **Title-only creator:** differs for 232 works (0.1%).

**Two added library models, therefore** (descriptive, logged in `prereg/DEVIATIONS.md`): **L+0** builds the same three features only from the records first lent in the work's first month (theme as in `16_v3_assign.py`, but each record counts once, no loans are used and Goodreads shelves are left out; the code reproduces `work_theme.parquet`'s top node for 99.88% of the works without Goodreads evidence when it is given all records and their loans). L+0 is still not clean: a first-month record is visible only because it was lent in month 0, which is inside the outcome window, and the theme depends mainly on the subject headings of print records: works with print loans in month 0 have a first-month theme 92.6% of the time, against 37.8% without. That is the month-0 format information that correction B2 of the code audit took out of L. **Lq** leaves the theme out (L plus the first-month publication-year gap and title-only flag) and is the cleanest of the three.

**all new books** (134,970 books, 70,414 author clusters)

| Model | Spearman (interval) | Top-10% precision |
| :--- | ---: | ---: |
| W (Wikipedia only) | 0.127 (0.115 to 0.138) | 22.3% |
| L (library, as in Test B) | 0.349 (0.337 to 0.361) | 33.8% |
| LW (L + Wikipedia, as in Test B) | 0.372 (0.362 to 0.383) | 36.6% |
| Lq (L + first-month publication-year gap and title-only flag, no theme; added) | 0.496 (0.487 to 0.506) | 37.3% |
| Lq W (added) | 0.507 (0.499 to 0.515) | 39.7% |
| L+0 (the same three from first-month records; added) | 0.503 (0.494 to 0.511) | 37.0% |
| L+0 W (added) | 0.515 (0.507 to 0.523) | 39.5% |
| L+ (L + theme, publication-year gap, title-only flag; as fixed) | 0.545 (0.537 to 0.552) | 40.4% |
| L+W | 0.553 (0.546 to 0.560) | 42.3% |

**author matched to a Wikipedia article before release** (46,318 books, 19,921 author clusters)

| Model | Spearman (interval) | Top-10% precision |
| :--- | ---: | ---: |
| W (Wikipedia only) | 0.127 (0.109 to 0.146) | 16.9% |
| L (library, as in Test B) | 0.342 (0.321 to 0.362) | 33.3% |
| LW (L + Wikipedia, as in Test B) | 0.393 (0.372 to 0.412) | 38.2% |
| Lq (L + first-month publication-year gap and title-only flag, no theme; added) | 0.497 (0.480 to 0.513) | 37.7% |
| Lq W (added) | 0.523 (0.507 to 0.537) | 42.1% |
| L+0 (the same three from first-month records; added) | 0.511 (0.497 to 0.525) | 39.2% |
| L+0 W (added) | 0.537 (0.523 to 0.551) | 42.8% |
| L+ (L + theme, publication-year gap, title-only flag; as fixed) | 0.565 (0.551 to 0.578) | 45.0% |
| L+W | 0.588 (0.575 to 0.600) | 47.0% |

**matched author is a writer** (36,572 books, 13,642 author clusters)

| Model | Spearman (interval) | Top-10% precision |
| :--- | ---: | ---: |
| W (Wikipedia only) | 0.122 (0.100 to 0.144) | 16.0% |
| L (library, as in Test B) | 0.358 (0.334 to 0.381) | 33.1% |
| LW (L + Wikipedia, as in Test B) | 0.406 (0.384 to 0.430) | 38.1% |
| Lq (L + first-month publication-year gap and title-only flag, no theme; added) | 0.509 (0.489 to 0.528) | 38.0% |
| Lq W (added) | 0.534 (0.516 to 0.552) | 42.0% |
| L+0 (the same three from first-month records; added) | 0.523 (0.506 to 0.539) | 39.9% |
| L+0 W (added) | 0.547 (0.530 to 0.564) | 42.6% |
| L+ (L + theme, publication-year gap, title-only flag; as fixed) | 0.583 (0.567 to 0.598) | 45.9% |
| L+W | 0.604 (0.589 to 0.618) | 47.7% |

**Does Wikipedia still add?** (paired difference in Spearman, same draws; yes = interval above 0)

| Books | Comparison | Difference (interval) | Above 0? |
| :--- | :--- | ---: | ---: |
| all new books | Wikipedia on top of L (as in Test B) | 0.0237 (0.0191 to 0.0299) | yes |
| all new books | Wikipedia on top of Lq (no theme) | 0.0107 (0.0078 to 0.0145) | yes |
| all new books | Wikipedia on top of L+0 (first-month records) | 0.0122 (0.0098 to 0.0152) | yes |
| all new books | Wikipedia on top of L+ (as fixed) | 0.0085 (0.0066 to 0.0105) | yes |
| author matched to a Wikipedia article before release | Wikipedia on top of L (as in Test B) | 0.0504 (0.0423 to 0.0593) | yes |
| author matched to a Wikipedia article before release | Wikipedia on top of Lq (no theme) | 0.0256 (0.0207 to 0.0308) | yes |
| author matched to a Wikipedia article before release | Wikipedia on top of L+0 (first-month records) | 0.0258 (0.0214 to 0.0308) | yes |
| author matched to a Wikipedia article before release | Wikipedia on top of L+ (as fixed) | 0.0224 (0.0185 to 0.0265) | yes |
| matched author is a writer | Wikipedia on top of L (as in Test B) | 0.0486 (0.0388 to 0.0587) | yes |
| matched author is a writer | Wikipedia on top of Lq (no theme) | 0.0248 (0.0189 to 0.0312) | yes |
| matched author is a writer | Wikipedia on top of L+0 (first-month records) | 0.0240 (0.0189 to 0.0296) | yes |
| matched author is a writer | Wikipedia on top of L+ (as fixed) | 0.0206 (0.0165 to 0.0251) | yes |

**What the catalogue information adds to the library model alone**

| Books | Comparison | Difference in Spearman (interval) |
| :--- | :--- | ---: |
| all new books | Lq minus L (publication-year gap and title-only flag) | 0.1475 (0.1412 to 0.1539) |
| all new books | L+0 minus Lq (the first-month theme) | 0.0064 (0.0035 to 0.0094) |
| all new books | L+ minus L+0 (records first lent later) | 0.0420 (0.0385 to 0.0453) |
| all new books | L+ minus L (all of it, as fixed) | 0.1959 (0.1873 to 0.2046) |
| author matched to a Wikipedia article before release | Lq minus L (publication-year gap and title-only flag) | 0.1547 (0.1433 to 0.1668) |
| author matched to a Wikipedia article before release | L+0 minus Lq (the first-month theme) | 0.0144 (0.0102 to 0.0189) |
| author matched to a Wikipedia article before release | L+ minus L+0 (records first lent later) | 0.0538 (0.0479 to 0.0597) |
| author matched to a Wikipedia article before release | L+ minus L (all of it, as fixed) | 0.2229 (0.2078 to 0.2383) |
| matched author is a writer | Lq minus L (publication-year gap and title-only flag) | 0.1511 (0.1369 to 0.1640) |
| matched author is a writer | L+0 minus Lq (the first-month theme) | 0.0141 (0.0089 to 0.0198) |
| matched author is a writer | L+ minus L+0 (records first lent later) | 0.0602 (0.0532 to 0.0670) |
| matched author is a writer | L+ minus L (all of it, as fixed) | 0.2255 (0.2075 to 0.2423) |

- The library model rises from 0.349 (L) to 0.496 without the theme (Lq), 0.503 with the first-month theme (L+0) and 0.545 with the features as fixed (L+). So most of the gain comes with the publication-year gap and the title-only flag (+0.1475), the first-month theme adds +0.0064, and the records first lent later add +0.0420 (L+ minus L+0). The gap matters on its own: books first lent in the year after their publication year had a median of 5 loans in their first six months, against 20 for books first lent in their publication year (first-month records).
- Wikipedia's addition, 0.0237 over L, becomes 0.0107 over Lq (45%), 0.0122 over L+0 (51%) and 0.0085 over L+ (36%). Its interval is above zero for all three stronger models in all three sets of books (all, matched authors, writers).

## R6. Does Wikipedia catch rises the library list misses? (Test A, incremental early warning)

In each month: take the books that rose by 50% next month and were not in the library model's top 50. What share of them is in Wikipedia's top 50 (W, Wikipedia only)? A random list of 50 would catch 50 divided by the number of books that month (about 0.7%). The library list is the library-only tree model H (main) and, added, the naive repeat-last-month ranking. Averages are over months, with month-block intervals.

| Measure (top 50 lists, rise of 50%) | Library list = H (trees) | Library list = repeat last month |
| :--- | ---: | ---: |
| Books in a month, on average | 7,138 | 7,138 |
| Books that rose by 50%, per month | 810 | 810 |
| Share of all rises caught by the library top 50 | 5.4% (5.2 to 5.7) | 5.3% (4.9 to 5.6) |
| Share of all rises caught by the Wikipedia top 50 | 3.1% (2.9 to 3.3) | 3.1% (2.9 to 3.3) |
| Share of all rises caught by both lists together | 7.6% (7.2 to 8.0) | 7.5% (7.1 to 8.0) |
| Rises not in the library top 50, per month | 767 | 769 |
| **Share of those caught by the Wikipedia top 50** | 2.3% (2.1 to 2.4) | 2.4% (2.2 to 2.5) |
| Share a random list of 50 would catch (expected) | 0.70% | 0.70% |
| Wikipedia share divided by the random share | 3.23 (3.02 to 3.45) | 3.38 (3.15 to 3.61) |
| Months in which Wikipedia beats the random list | 100.0% | 100.0% |
| Books in both lists, per month | 7.6 | 6.8 |
| Books in the Wikipedia list that are not in the library list, per month | 42.4 | 43.2 |
| Share of those books that rose | 40.0% (37.8 to 42.4) | 40.9% (38.9 to 43.3) |
| Share of the books outside the library top 50 that rose | 10.8% (10.3 to 11.4) | 10.8% (10.3 to 11.4) |

- Among the rises the library history list (H) missed, Wikipedia's top 50 caught 2.3% (2.1 to 2.4), against 0.70% for a random list (3.2 times; interval 3.0 to 3.5). With the naive list as the library list the share is 2.4% (2.2 to 2.5), 3.4 times the random share.
- Of the 42.4 books per month that Wikipedia's list adds to the library list, 40.0% rose, against 10.8% of the books outside the library list. The two lists share 7.6 books a month.
- With lists of 20 the share caught is 1.2% (1.1 to 1.3) (random: 0.28%; 4.3 times). Counting rises of 25% or 100% instead, the top-50 share is 1.6% (2.2 times random) and 3.6% (5.1 times).

## R7. Length of the alert list (top 10, 20, 50, 100)

Hit rates for rises of 50% and for surges, by list length. Test D numbers are for all formats (lists drawn within each format and month), 2019 to 2026, unless a period is shown.

**Test A, rose by 50%**

| Model | Top 10 | Top 20 | Top 50 | Top 100 |
| :--- | ---: | ---: | ---: | ---: |
| Wikipedia only (W) | 64.6% (60.1 to 69.0) | 57.9% (54.5 to 61.1) | 48.3% (46.1 to 50.5) | 40.0% (38.0 to 42.3) |
| Wikipedia rule (no fitting) | 20.4% (17.2 to 23.8) | 27.4% (24.8 to 30.2) | 30.6% (28.6 to 32.8) | 28.5% (26.8 to 30.3) |
| Library history (H) | 93.8% (91.7 to 95.9) | 92.1% (90.2 to 93.9) | 84.8% (82.5 to 87.0) | 76.1% (74.0 to 78.3) |
| Library + Wikipedia (HW) | 94.9% (92.7 to 96.9) | 93.7% (91.8 to 95.4) | 86.1% (84.2 to 88.0) | 77.6% (75.5 to 79.7) |
| Repeat last month (naive) | 92.8% (88.8 to 95.9) | 89.6% (86.1 to 92.4) | 82.2% (78.1 to 85.3) | 72.3% (68.8 to 75.2) |
| *base rate (any book)* | 11.3% | 11.3% | 11.3% | 11.3% |

**Test A, surged**

| Model | Top 10 | Top 20 | Top 50 | Top 100 |
| :--- | ---: | ---: | ---: | ---: |
| Wikipedia only (W) | 46.4% (41.5 to 51.4) | 39.2% (36.0 to 42.4) | 30.4% (28.3 to 32.6) | 23.0% (21.3 to 24.8) |
| Wikipedia rule (no fitting) | 10.5% (8.1 to 13.1) | 15.4% (13.0 to 17.8) | 16.7% (15.2 to 18.2) | 14.5% (13.5 to 15.6) |
| Library history (H) | 85.1% (82.2 to 88.2) | 79.9% (76.9 to 83.0) | 64.7% (60.5 to 68.6) | 49.2% (45.8 to 52.7) |
| Library + Wikipedia (HW) | 87.4% (84.9 to 90.0) | 81.7% (79.0 to 84.4) | 66.0% (62.4 to 69.5) | 50.8% (47.5 to 54.2) |
| Repeat last month (naive) | 85.1% (80.3 to 89.0) | 75.6% (71.2 to 79.6) | 60.2% (55.9 to 64.2) | 45.8% (42.2 to 49.2) |
| *base rate (any book)* | 2.8% | 2.8% | 2.8% | 2.8% |

- Test A: library + Wikipedia is above the library list in 8 of 8 cells (4 lengths, two outcomes). The Wikipedia-only list is 5.7, 5.1, 4.3, 3.5 times the base rate at 10, 20, 50 and 100 places, so it works best in the shortest lists. The no-fitting rule is the exception: its hit rate is lowest in the shortest list (20.4% at 10 places, 30.6% at its best).

**Test D, all formats, rose by 50%** (original / corrected)

| Model | Top 10 | Top 20 | Top 50 | Top 100 |
| :--- | ---: | ---: | ---: | ---: |
| Wikipedia only (W) | 51.7% / 52.1% | 47.4% / 45.5% | 37.6% / 37.2% | 30.5% / 30.4% |
| Library history (H) | 90.3% / 90.3% | 87.3% / 87.3% | 80.1% / 80.1% | 70.4% / 70.4% |
| Library + Wikipedia (HW) | 91.6% / 90.9% | 87.9% / 88.0% | 81.1% / 81.2% | 71.5% / 71.3% |
| Repeat last month (naive) | 87.9% / 87.9% | 84.2% / 84.2% | 77.1% / 77.1% | 67.2% / 67.2% |
| *base rate (any book)* | 11.6% / 11.6% | 11.6% / 11.6% | 11.6% / 11.6% | 11.6% / 11.6% |

**Library + Wikipedia (HW) by format and period, rose by 50%** (original / corrected; * = at least 90%)

| Format | Years | Top 10 | Top 20 | Top 50 | Top 100 |
| :--- | :--- | ---: | ---: | ---: | ---: |
| print | 2019-2026 | 90.6%* / 90.5%* | 87.2% / 87.3% | 80.8% / 80.8% | 72.1% / 71.8% |
| print | 2024-2026 | 92.3%* / 91.2%* | 85.0% / 85.0% | 78.9% / 78.1% | 70.7% / 70.2% |
| ebook | 2019-2026 | 91.8%* / 90.8%* | 88.0% / 88.0% | 80.5% / 80.8% | 70.8% / 70.5% |
| ebook | 2024-2026 | 93.8%* / 93.5%* | 92.1%* / 92.3%* | 86.8% / 86.5% | 77.4% / 76.8% |
| audiobook | 2019-2026 | 92.3%* / 91.3%* | 88.6% / 88.6% | 81.9% / 81.8% | 71.6% / 71.5% |
| audiobook | 2024-2026 | 94.6%* / 95.0%* | 92.7%* / 93.1%* | 87.4% / 87.5% | 79.0% / 78.8% |
| all formats | 2019-2026 | 91.6%* / 90.9%* | 87.9% / 88.0% | 81.1% / 81.2% | 71.5% / 71.3% |
| all formats | 2024-2026 | 93.6%* / 93.2%* | 89.9% / 90.1%* | 84.4% / 84.0% | 75.7% / 75.3% |

- Library + Wikipedia reaches 90% in this many of the 6 format and period cells (original / corrected): top 10: 6 / 6; top 20: 2 / 2; top 50: 0 / 0; top 100: 0 / 0.
- Pooled over the three formats, the 2024-2026 top 20 is 89.9% in the original run and 90.1% in the corrected one, right on the line; the question of addendum d asks for every format, and print stays at 85.0%.

## Every comparison: does the result come out the same way?

Of 41 comparisons, 38 come out the same way as the main result and 3 do not. No change in any check: A1; A2; A3; Alert A (W); Early warning; B1; B2; Alert D original; Alert D corrected. At least one change: Alert A (HW vs H); D 90% original; D 90% corrected. The changes are listed under the table.

Each row is a decision rule of the records or a headline result of the alert lists. A cell says "holds" when the result comes out the same way under the alternative choice of that check, "**changes**" when it does not, and is empty when the check does not apply. Details follow the table.

| Decision or result | main | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| A1 (Test A): Wikipedia alone ranks which books rise; interval of W change rank above 0 | holds |  | holds | holds | holds |  |  |  |
| A2 (Test A): Wikipedia adds to library history; HW minus H above 0 | holds |  | holds | holds | holds |  |  |  |
| A3 (Test A): Wikipedia alone flags surges; interval of the W surge AP ratio above 1 | holds |  | holds | holds | holds |  |  |  |
| Alert list (Test A): the Wikipedia-only list beats the base rate |  | holds | holds | holds | holds |  |  | holds |
| Alert list (Test A): adding Wikipedia to the library list does not lower the hit rate (under 0.5 points counts as a tie) |  | holds | holds | **changes** | holds |  |  | holds |
| Early warning (Test A): Wikipedia's list catches rises that the library list misses |  |  |  |  |  |  | holds |  |
| B1 (Test B): Wikipedia alone predicts the early demand of new books; interval of W Spearman above 0 | holds |  |  | holds |  |  |  |  |
| B2 (Test B): Wikipedia adds to the library model for new books; LW minus L above 0 | holds |  |  | holds |  | holds |  |  |
| Alert list (Test D, original): W beats the base rate and HW is not below H (under 0.5 points counts as a tie) |  | holds |  |  |  |  |  | holds |
| 90% question (Test D, original): HW top 20, rise of 50%, at least 90% in every format; answer for 2019-2026 and 2024-2026 | holds | holds |  |  |  |  |  | **changes** |
| Alert list (Test D, corrected): W beats the base rate and HW is not below H (under 0.5 points counts as a tie) |  | holds |  |  |  |  |  | holds |
| 90% question (Test D, corrected): HW top 20, rise of 50%, at least 90% in every format; answer for 2019-2026 and 2024-2026 | holds | holds |  |  |  |  |  | **changes** |

**Where a result changes**

- Alert A (HW vs H), R3, each test year (top 20): HW not more than 0.5 points below H in 7 of 8 years; below in 2020 by 4.0 points (5 scored months)
- D 90% original, R7, top 10, 50, 100 (rise of 50%): top 10 2019-2026: yes (3 of 3); top 10 2024-2026: yes (3 of 3); top 50 2019-2026: no (0 of 3); top 50 2024-2026: no (0 of 3); top 100 2019-2026: no (0 of 3); top 100 2024-2026: no (0 of 3)
- D 90% corrected, R7, top 10, 50, 100 (rise of 50%): top 10 2019-2026: yes (3 of 3); top 10 2024-2026: yes (3 of 3); top 50 2019-2026: no (0 of 3); top 50 2024-2026: no (0 of 3); top 100 2019-2026: no (0 of 3); top 100 2024-2026: no (0 of 3)

**Detail of every comparison**

| Result | Check | Compared | Outcome | Detail |
| :--- | :--- | :--- | :--- | :--- |
| A1 | main | all months | holds | W change rank 0.133 (0.124 to 0.142) |
| A1 | R4 | without 2025-04 to 2025-06 | holds | 0.134 (0.124 to 0.142) |
| A1 | R3 | each test year | holds | point value above 0 in 8 of 8 years; interval above 0 in 7 of the 7 years that have one |
| A1 | R2 | each seed | holds | 0.1333 to 0.1338 over 5 seeds |
| A2 | main | all months | holds | HW minus H 0.0094 (0.0074 to 0.0113) |
| A2 | R4 | without 2025-04 to 2025-06 | holds | 0.0092 (0.0073 to 0.0112) |
| A2 | R3 | each test year | holds | point value above 0 in 8 of 8 years; interval above 0 in 7 of the 7 years that have one |
| A2 | R2 | each seed | holds | 0.0088 to 0.0094 over 5 seeds |
| A3 | main | all months | holds | W surge AP ratio 3.45 (3.13 to 3.78) |
| A3 | R4 | without 2025-04 to 2025-06 | holds | 3.45 (3.14 to 3.81) |
| A3 | R3 | each test year | holds | ratio above 1 in 8 of 8 years |
| A3 | R2 | each seed | holds | 3.43 to 3.47 over 5 seeds |
| Alert A (W) | R1 | rise of 25%, 50%, 100%; top 20 and 50 | holds | above the base rate in 6 of 6 cells |
| Alert A (W) | R7 | top 10, 20, 50, 100; rose 50% and surged | holds | above the base rate in 8 of 8 cells |
| Alert A (W) | R3 | each test year (top 20) | holds | above the year's base rate in 8 of 8 years |
| Alert A (W) | R4 | without 2025-04 to 2025-06 (top 20) | holds | 57.6% against a base rate of 11.4% |
| Alert A (W) | R2 | each seed (top 20) | holds | top-20 hit rate 56.3% to 57.9% over 5 seeds |
| Alert A (HW vs H) | R1 | rise of 25%, 50%, 100%; top 20 and 50 | holds | HW not more than 0.5 points below H in 6 of 6 cells |
| Alert A (HW vs H) | R7 | top 10, 20, 50, 100; rose 50% and surged | holds | HW not more than 0.5 points below H in 8 of 8 cells |
| Alert A (HW vs H) | R3 | each test year (top 20) | **changes** | HW not more than 0.5 points below H in 7 of 8 years; below in 2020 by 4.0 points (5 scored months) |
| Alert A (HW vs H) | R4 | without 2025-04 to 2025-06 (top 20) | holds | HW 93.7%, H 92.3% |
| Alert A (HW vs H) | R2 | each seed (top 20) | holds | HW minus H in the top-20 hit rate: +0.8 to +1.7 points over 5 seeds |
| Early warning | R6 | library list H, top 50 | holds | 2.3% (2.1 to 2.4) caught against 0.70% for a random list of 50 |
| Early warning | R6 | naive library list, top 50 | holds | 2.4% (2.2 to 2.5) caught against 0.70% |
| B1 | main | all years | holds | W Spearman 0.127 (0.115 to 0.138) |
| B1 | R3 | each test year | holds | interval above 0 in 8 of 8 years |
| B2 | main | all years | holds | LW minus L 0.0237 (0.0191 to 0.0299) |
| B2 | R3 | each test year | holds | interval above 0 in 8 of 8 years, point value above 0 in 8 |
| B2 | R5 | stronger library model L+, as fixed | holds | 0.0085 (0.0066 to 0.0105) (all books); interval above 0 in 3 of 3 book sets |
| B2 | R5 | L+0, first-month records (added) | holds | 0.0122 (0.0098 to 0.0152) (all books); interval above 0 in 3 of 3 book sets |
| B2 | R5 | Lq, no theme (added) | holds | 0.0107 (0.0078 to 0.0145) (all books); interval above 0 in 3 of 3 book sets |
| Alert D original | R1 | rise of 25%, 50%, 100%; top 20 and 50 | holds | HW not more than 0.5 points below H in 6 of 6 cells; W above the base rate in 6 of 6 |
| Alert D original | R7 | top 10, 20, 50, 100 (rise of 50%) | holds | HW not more than 0.5 points below H at 4 of 4 lengths; W above the base rate at 4 of 4 |
| D 90% original | main | top 20, rise of 50% | holds | 2019-2026: no (0 of 3 formats); 2024-2026: no (2 of 3 formats) |
| D 90% original | R1 | rise of 25% and 100% (top 20) | holds | 25% 2019-2026: no (2 of 3); 25% 2024-2026: no (2 of 3); 100% 2019-2026: no (0 of 3); 100% 2024-2026: no (1 of 3) |
| D 90% original | R7 | top 10, 50, 100 (rise of 50%) | **changes** | top 10 2019-2026: yes (3 of 3); top 10 2024-2026: yes (3 of 3); top 50 2019-2026: no (0 of 3); top 50 2024-2026: no (0 of 3); top 100 2019-2026: no (0 of 3); top 100 2024-2026: no (0 of 3) |
| Alert D corrected | R1 | rise of 25%, 50%, 100%; top 20 and 50 | holds | HW not more than 0.5 points below H in 6 of 6 cells; W above the base rate in 6 of 6 |
| Alert D corrected | R7 | top 10, 20, 50, 100 (rise of 50%) | holds | HW not more than 0.5 points below H at 4 of 4 lengths; W above the base rate at 4 of 4 |
| D 90% corrected | main | top 20, rise of 50% | holds | 2019-2026: no (0 of 3 formats); 2024-2026: no (2 of 3 formats) |
| D 90% corrected | R1 | rise of 25% and 100% (top 20) | holds | 25% 2019-2026: no (2 of 3); 25% 2024-2026: no (2 of 3); 100% 2019-2026: no (0 of 3); 100% 2024-2026: no (1 of 3) |
| D 90% corrected | R7 | top 10, 50, 100 (rise of 50%) | **changes** | top 10 2019-2026: yes (3 of 3); top 10 2024-2026: yes (3 of 3); top 50 2019-2026: no (0 of 3); top 50 2024-2026: no (0 of 3); top 100 2019-2026: no (0 of 3); top 100 2024-2026: no (0 of 3) |

## Notes

- Code check: run on the original Test A files, this code reproduces the stored alert list (`wiki_led_test_a_alert_list.csv`: top 20 and top 50, rose and surged, four models) to within 0.0008; the small gaps come from the order of tied predictions.
- Code check: Test D hit rates at 50% (all formats, top 20 and top 50, four models) agree with the stored files (original: `wiki_led_test_d.json`, within 0.0015; corrected: `wiki_led_test_d_c.json`, within 0.0015); the exact 50% rise flag differs from the stored `rose` column in 3 of 1,984,302 rows.
- Test D, corrected: its rows file (`test_d_rows_c.parquet`, 2,767,485 rows) has the same rows as the original (0 only in one, 0 only in the other) and the same loans (largest difference in next-month loans 0.0, in M6 0.0); only the Wikipedia features differ, so H and the naive list score the same in both runs.
- Code check: the refitted W, L and LW predictions of Test B equal the stored ones (largest difference 0.0e+00), and the LW minus L interval here (0.0191 to 0.0299) equals the stored one (0.0191 to 0.0299).
- Additions beyond the text of addendum e, all descriptive and not used to choose anything: the surge outcome and the top 50 and top 100 lists in R1 and R7; the naive library list, the 25% and 100% rises and the top 20 list in R6; the matched-author and writer sets in R5 (the sets of decision B3); the three months alone in R4; the by-format and by-period table for the 90% question in R7; and, from the review of 20 Oct 2026, the models L+0 and Lq in R5 (first-month records), the month-by-month top-20 places in R3, and the Test D corrected run beside the original.
- R3 and R4 reuse the stored predictions; only R2 (Test A) and R5 (Test B) refit models.

Run times and peak memory are in the part files (`data/db/wiki_led/robustness_part_*.json`) and the job logs (`data/reports/wl_rob_*.log`).
