# Improvement round v2 for existing books (Test A): early warning, count loss, gate, burst features and events

Khant Phyo Wai, 01323050. Run 20 Oct 2026. Settings: `prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json` (fixed before any result), which adopts Section 3 of `paper/lit_search/Improvement_Methods_2026-10-20.md`. Choices the note leaves open are in `prereg/DEVIATIONS.md` (section "Wikipedia-led tests", entries of 20 Oct 17:27 and 17:29 and later ones). Code: `code/main_study/wiki_led/80_improve_v2.py` (stages c1, c4, c2, c5) and `81_improve_v2_report.py`. Stage files: `data/reports/wiki_led_improve_v2_<stage>.json`.

## 1. In plain words

**Short answer.**

1. **Precision@20 of the early-warning list: at most a small gain, and only from the burst-shape features.** v0 29.2%; the change-1 ranker 27.9% (no gain); the ranker with the burst columns 31.5%, which is +3.7 points over the same ranker without them (interval +0.4 to +6.9) and +2.3 points over v0 (interval -1.3 to +6.0, not clear). Over five LightGBM seeds the burst columns add +1.7 to +3.7 points to the ranker (mean +2.6). For scale, adding the same number of columns of random numbers moves the ranker by -1.5 to +2.3 points over three seeds, so a gain of this size is small next to the noise from the model's own sampling.
2. **Change ranking: no clear gain.** Library + Wikipedia stays at 0.363; the gate lowered it by 0.0078 (interval -0.0097 to -0.0059). For Wikipedia alone the burst columns moved it +0.0025 (interval -0.0007 to +0.0058).
3. **Accuracy in loans: unchanged.** Neither the Tweedie loss nor the gate was chosen, so v1 is v0: an average error of 4.59 loans (20.9% of the loans).
4. **Range for next month's loans: works.** The 80% interval covered 80.2% of the actual loans in 2024 to 2026, with a median width of 7.8 loans.
5. **Events and adaptation views: no gain from the events.** Change ranking +0.0012 (interval -0.0005 to +0.0028); early list of the Wikipedia model +1.2 points (interval -1.7 to +3.7); ranker +1.0 points (interval -2.1 to +3.8). With the events moved 12 months later the same measures move +0.0012 and +1.0 points, so there is nothing specific to the real dates.

**Detail.** v0 is the Test A model of 20 October, unchanged. Each change was tuned on 2019 to 2023, one variant was chosen by the stated rule, and then v0 and the chosen variant were run once on 2024 to 2026 on the same rows. The 2024 to 2026 results of v0 were known before the changes were chosen, so this is a single pre-declared test of new settings, not a blind test; the frozen live lists are the blind check.

- **Precision@20 of the early-warning list** (the 20 books a month that are not yet rising, scored on whether they rose by 50% or more next month). On average 29.2% of the 20 books that Test A's Wikipedia model (v0) put first rose by 50% or more in 2024 to 2026, against a base rate of 8.9% (3.3 times chance). The ranker of change 1 (R100e) had a tuning gain of 1.3 points and was adopted by the rule, but on 2024 to 2026 it got 27.9%: -1.3 points (95% interval -5.8 to +2.5; no clear difference). With the burst-shape features of change 2 the ranker got 31.5%: +3.7 points (95% interval +0.4 to +6.9; a clear gain) from the same ranker without them, and +2.3 points (95% interval -1.3 to +6.0; no clear difference) from v0. The Wikipedia regression with the same features got 30.4%: +1.2 points (95% interval -1.9 to +3.8; no clear difference) from v0. Refitting that ranker with four other seeds moves it between -1.3 and +1.5 points from v0 (mean +0.1), so the run above is at the low end and the ranker alone is no better than v0. For the burst columns, the same five seeds give a gain of +1.7 to +3.7 points over the ranker without them (mean +2.6; 5 of 5 above 0), so the gain is smaller than the run above suggests but has the same sign every time. Adding 16 columns of random numbers instead moves the ranker by -1.5 to +2.3 points over three seeds (mean +0.4), which is the size of noise that a real gain has to be read against.
- **Rank correlation between predicted and actual change** (within month, averaged). Library + Wikipedia (v0, unchanged as v1): 0.363. The gate was not adopted; for information it scored -0.0078 from that (interval -0.0097 to -0.0059). For Wikipedia alone the burst-shape features moved it from 0.129 to 0.131: +0.0025 (interval -0.0007 to +0.0058; no clear difference). Surges were flagged at 3.68 times chance against 3.43.
- **Accuracy in loans (next month).** The Tweedie count loss was not chosen: on 2019 to 2023 the regression on ln(1 + loans) had the best mean rank for both the library model and the library + Wikipedia model, so v1 equals v0. The gate was not chosen either (on 2020 to 2023 HW_lgbm had the best mean rank). The average error stays at 4.59 loans (interval 4.40 to 4.78; WAPE 20.9%), 49.8% of forecasts within 2 loans. For information the gate was +0.024 loans from v0 (interval -0.012 to +0.070). The burst-shape features lowered the error of the Wikipedia-only level model from 15.60 to 15.33 loans (-0.27, interval -0.29 to -0.25), which is still more than three times the error of the library model. In the placebo the same columns change the Wikipedia-only level error (in ln(1 + loans)) by -0.0058 against -0.0183 in the real run, so part of that gain is about how popular the book is (the donor books are matched on traffic) and part belongs to the book's own pages.
- **Range for next month's loans.** The split-conformal 80% interval covered 80.2% of the actual loans in 2024 to 2026 (79.9% in 2020 to 2023), with a median width of 7.8 loans. By year the coverage ran from 76.8% to 81.3%; for burst rows it was 78.7% and for books with under 12 months of history 86.7% on average over the years.
- **Placebo.** change 1: with another book's pages the ranker gets 9.2% against a base rate of 8.9%, so the early signal belongs to the book's own pages; change 2: with another book's pages the burst columns add -0.8 points to the ranker (interval -4.0 to +2.3) against +3.7 in the real run, and -0.0034 to the change ranking of the Wikipedia model, so the early-warning gain does not appear without the book's own pages; change 5: with the events and adaptation columns moved 12 months later the ranker changes by +1.0 points against +1.0 in the real run, so the small differences there are not tied to the real event dates. There is no placebo for change 4: no Wikipedia-only variant was chosen there.
- **Events and adaptation views (change 5).** Events are rare in this data: in the scored rows 621 work-months have an author death in t or t-1, 262 a dated award and 931 a film or tv release within a month that was already public. Tuning chose E2_flags_views for the Wikipedia model (adopted: yes) and E1_flags for the ranker (adopted: no). On 2024 to 2026 the change ranking moved +0.0012 (interval -0.0005 to +0.0028; no clear difference), the early list of the Wikipedia model +1.2 points (95% interval -1.7 to +3.7; no clear difference), and the ranker with minus without the new columns +1.0 points (95% interval -2.1 to +3.8; no clear difference). With the same columns moved 12 months later (placebo) the same measures move +0.0012, +1.2 points and +1.0 points, so these differences are no larger than what changing the set of columns does by itself; they do not come from the real event dates. On the 1,215 book-months within 2 months of an event, the change ranking moved +0.0204 (interval +0.0006 to +0.0398) against +0.0037 in the placebo: the one place where the events may matter, resting on few rows. The error of the Wikipedia-only level model (MAE of ln(1 + loans)) changed by -0.0116 (interval -0.0126 to -0.0108); in the placebo it changes by -0.0119, so what the adaptation views add to the level is about how popular the book is, not about the timing of events.

**What ran:**

| Change | Chosen variant | Adopted by the rule | Tuning | 2024 to 2026 against v0 |
| --- | --- | --- | --- | --- |
| 1. Early-warning ranker (books not yet risen) | R100e | yes | +1.3 points of precision@20 | precision@20 of rises 29.2% to 27.9%, -1.3 points (interval -5.8 to +2.5): no clear difference |
| 4a. Tweedie count loss | H: v0, HW: v0 | no | regression on ln(1 + loans) had the best mean rank | v1 equals v0: the count loss was not chosen |
| 4b. Gate between library and Wikipedia | HW | no | mean rank 2020-2023: HW_lgbm 1.00, Equal-weight average 3.00, Gate 2.00 | for information, gate minus HW_lgbm: average error +0.024 loans (interval -0.012 to +0.070); change ranking -0.0078 (interval -0.0097 to -0.0059) |
| 4c. Split-conformal 80% intervals | HW_lgbm (v0) | added | not tuned | coverage 80.2% in 2024 to 2026, median width 7.8 loans |
| 2. Burst-shape features | W model: B1_all; ranker: B1_all | W model yes; ranker yes | change ranking +0.0054; ranker +0.3 points | change ranking +0.0025 (interval -0.0007 to +0.0058); W-model early list +1.2 points (interval -1.9 to +3.8); ranker with minus without the new columns +3.7 points (interval +0.4 to +6.9) |
| 5. Events and adaptation views | W model: E2_flags_views; ranker: E1_flags | W model yes; ranker no | change ranking +0.0021; ranker -0.3 points | change ranking +0.0012 (interval -0.0005 to +0.0028); W-model early list +1.2 points (interval -1.7 to +3.7); ranker with minus without the new columns +1.0 points (interval -2.1 to +3.8) |

## 2. How the runs were done

Terms. A **rise** is next month's loans at least 1.5 times the book's median of the last 6 months; a **surge** is at least double and at least 5 loans more. A book is **not yet risen** when this month's loans are below 1.5 times that median. **Precision@20** is the share of a month's 20 highest-scored books that rose (or surged), averaged over months; **lift** divides it by the share of all eligible books that rose. **NDCG@20** gives credit for putting surges first, then rises, within the 20 (1 is the best possible list). **Change ranking** is the Spearman rank correlation, within month, between the predicted and the actual change. **Surge AP over base** is the average precision for surges divided by the surge rate (1 is chance). **MAE in loans** is the average absolute error of next month's loans, **WAPE** the total absolute error divided by the total loans, **top-10% hit** the share of the books a model puts in its top 10% by predicted loans that are in the actual top 10%.

- Rows: the 556,735 book-months of Test A (7,747 books, origins 2019-01 to 2026-07 without the closure months, 78 scored months: 52 in 2019 to 2023 and 26 in 2024 to 2026). v0 is the stored Test A prediction for those rows.
- Walk-forward by year: a model for year Y trains on rows whose target month is before 1 January of Y. LightGBM settings of Test A (300 trees, 31 leaves, seed 20261020, 4 threads).
- Intervals: 95%, 2,000 draws of circular blocks of 3 consecutive scored months (seed 20261020), paired by month. May and June 2025 (Wikimedia found bot traffic counted as human in those months) are given separately as point values for the two origin months 2025-05 and 2025-06.
- Placebo: each book gets the Wikipedia pages of another book with similar traffic (the donor matching of `11_placebo_a.py`, rebuilt and checked: it reproduces the stored placebo predictions to 1e-17).
- Peak memory and run time of the final full runs (one heavy job at a time, `nice`, LightGBM with 4 threads): change 1 1.35 GB, 317 s; change 4 1.22 GB, 49 s; change 2 1.24 GB, 593 s; change 5 1.0 GB, 518 s.

## 3. Change 1: early-warning ranker for books that have not risen yet

**Tuning, 2019 to 2023** (books not yet risen, mean over 52 months; the base rate of rises is 8.9%).

| Model | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows | Months above base rate |
| --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model (regression on the change) | 32.3% | 14.3% | 0.218 | 0.120 | 100% |
| Ranker, truncation 20, trained on books not yet risen | 28.8% | 14.0% | 0.206 | 0.041 | 98% |
| Ranker, truncation 100, trained on books not yet risen | 33.7% | 15.5% | 0.239 | 0.049 | 98% |
| Ranker, truncation 20, trained on all books (risen ones labelled 0) | 24.6% | 12.1% | 0.181 | 0.053 | 94% |
| Ranker, truncation 100, trained on all books (risen ones labelled 0) | 26.2% | 12.9% | 0.199 | 0.047 | 94% |

Choice (highest precision@20 of rises): **Ranker, truncation 100, trained on books not yet risen** (R100e), 33.7% against 32.3% for v0, a tuning gain of +1.3 points. Adopted by the rule: **yes**.

**One run on 2024 to 2026** (26 months, 515,830 eligible book-months over 2019 to 2026; base rate of rises 8.9%, of surges 1.6%). Intervals: 95%, 2,000 draws of 3-month blocks.

| Model | Precision@20, rises | Precision@20, surges | Lift over base rate (rises) | NDCG@20 | Spearman, eligible rows | Months above base rate |
| --- | --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model | 29.2% (23.7% to 36.0%) | 14.0% (10.6% to 18.1%) | 3.28 | 0.221 (0.175 to 0.272) | 0.112 (0.104 to 0.120) | 96% |
| v1: Ranker, truncation 100, trained on books not yet risen | 27.9% (24.4% to 32.5%) | 13.8% (10.4% to 17.7%) | 3.13 | 0.227 (0.188 to 0.270) | 0.050 (0.040 to 0.061) | 96% |
| v1 minus v0 (paired by month, points for the shares) | -1.3 (-5.8 to +2.5) | -0.2 (-2.7 to +2.5) |  | +0.006 (-0.027 to +0.038) | -0.062 (-0.074 to -0.050) |  |

The chosen ranker beat v0 in 31% of the 26 months on precision@20 of rises.

By test year (precision@20 of rises, v0 then v1): 2024: 25.0% then 30.0%; 2025: 37.0% then 30.0%; 2026: 23.8% then 23.1%.

**Seed check** (descriptive, 5 LightGBM seeds, 2024 to 2026): the ranker's precision@20 of rises is 27.9% to 30.8% (mean 29.3%) against 29.2% for v0, a difference from v0 of -1.3 to +1.5 points (mean +0.1). The seed used in the run above (-1.3 points) is at the low end, so differences of about 1.5 points between two models are within what the seed alone changes.

**May and June 2025** (origin months 2025-05 and 2025-06, two months, point values, no interval): precision@20 of rises 35.0% for v0 and 27.5% for v1; surges 10.0% and 10.0%; base rate 8.1%. Without these two months the 2024 to 2026 values are 28.8% for v0 and 27.9% for v1 (difference -0.8 points).

**Placebo** (each book given the Wikipedia pages of another book with similar traffic): precision@20 of rises 8.1% for v0 and 9.2% for the ranker, against a base rate of 8.9%; paired difference +1.2 (-1.3 to +4.0) points. Both sit at the base rate, so the early signal belongs to the book's own pages.

## 4. Change 4: count loss, gate and range for next month's loans

**Count loss, tuning 2019 to 2023** (all rows; lower is better for the two errors, higher for Spearman).

Library history only (H):

| Loss | MAE in loans | MAE in ln(1 + loans) | Spearman of the level | Mean rank (1 = best) |
| --- | --- | --- | --- | --- |
| v0: regression on ln(1 + loans) | 4.574 | 0.2701 | 0.9059 | 1.00 |
| Tweedie loss, variance power 1.2 | 4.595 | 0.2724 | 0.9052 | 2.67 |
| Tweedie loss, variance power 1.5 | 4.587 | 0.2721 | 0.9052 | 2.33 |

Choice: **v0: regression on ln(1 + loans)**.

Library history + Wikipedia (HW):

| Loss | MAE in loans | MAE in ln(1 + loans) | Spearman of the level | Mean rank (1 = best) |
| --- | --- | --- | --- | --- |
| v0: regression on ln(1 + loans) | 4.577 | 0.2689 | 0.9071 | 1.33 |
| Tweedie loss, variance power 1.2 | 4.592 | 0.2711 | 0.9063 | 3.00 |
| Tweedie loss, variance power 1.5 | 4.574 | 0.2704 | 0.9065 | 1.67 |

Choice: **v0: regression on ln(1 + loans)**.

**Gate, tuning on 2020 to 2023** (the years in which the gate is fitted; 2019 uses equal weights and is shown below).

| Model | MAE in loans | MAE in ln(1 + loans) | Spearman of the level | Mean rank |
| --- | --- | --- | --- | --- |
| HW_lgbm (library + Wikipedia, one model) | 4.534 | 0.2730 | 0.9057 | 1.00 |
| Equal-weight average of the library and Wikipedia predictions | 10.950 | 0.4208 | 0.8650 | 3.00 |
| Gate (ridge on the two predictions and three states) | 4.579 | 0.2744 | 0.9049 | 2.00 |

Same comparison on 2019 to 2023 (2019 counts with equal weights for the gate):

| Model | MAE in loans | MAE in ln(1 + loans) | Spearman of the level |
| --- | --- | --- | --- |
| HW_lgbm (library + Wikipedia, one model) | 4.577 | 0.2689 | 0.9071 |
| Equal-weight average of the library and Wikipedia predictions | 11.209 | 0.4194 | 0.8662 |
| Gate (ridge on the two predictions and three states) | 6.070 | 0.3013 | 0.8977 |

Choice: **HW_lgbm (library + Wikipedia, one model)**. Gate adopted: **no**.

**One run on 2024 to 2026** (26 months). v1 for next month's loans is: **v1 library + Wikipedia**; count-loss choice H: v0, HW: v0. When v0 is kept, v1 and v0 are the same predictions. The gate is shown for information even when it was not adopted. Intervals: 95%, 3-month blocks.

| Model | MAE in loans | MAE in ln(1 + loans) | WAPE | Within 2 loans | Top-10% hit | Spearman of the level | Change ranking | Top-20 rose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Library only (H_lgbm, v0) | 4.62 (4.44 to 4.81) | 0.2634 (0.2603 to 0.2669) | 21.0% | 49.8% | 90.4% | 0.9169 (0.9137 to 0.9197) | 0.352 (0.335 to 0.372) | 93.3% |
| Library + Wikipedia (HW_lgbm, v0) | 4.59 (4.40 to 4.78) | 0.2623 (0.2592 to 0.2658) | 20.9% | 49.8% | 90.5% | 0.9178 (0.9147 to 0.9206) | 0.363 (0.346 to 0.382) | 95.6% |
| Equal-weight average | 11.05 (10.66 to 11.43) | 0.4095 (0.4066 to 0.4125) | 50.3% | 36.8% | 82.0% | 0.8787 (0.8750 to 0.8822) | 0.194 (0.178 to 0.211) | 52.9% |
| Gate | 4.61 (4.44 to 4.80) | 0.2630 (0.2598 to 0.2663) | 21.0% | 49.8% | 90.4% | 0.9172 (0.9141 to 0.9199) | 0.356 (0.337 to 0.375) | 94.6% |
| v1 (the adopted model) | 4.59 (4.40 to 4.78) | 0.2623 (0.2592 to 0.2658) | 20.9% | 49.8% | 90.5% | 0.9178 (0.9147 to 0.9206) | 0.363 (0.346 to 0.382) | 95.6% |

Paired difference to v0 (library + Wikipedia, HW_lgbm); for the errors a negative number is better:

| Model minus v0 HW | MAE in loans | MAE in ln(1 + loans) | Spearman of the level | Top-10% hit (points) | Change ranking | Top-20 rose (points) |
| --- | --- | --- | --- | --- | --- | --- |
| Library only (H_lgbm, v0) | +0.032 (+0.009 to +0.065) | +0.0011 (+0.0006 to +0.0016) | -0.0009 (-0.0012 to -0.0007) | -0.11 (-0.29 to +0.07) | -0.0112 (-0.0135 to -0.0090) | -2.3 (-3.7 to -1.2) |
| Equal-weight average | +6.462 (+6.159 to +6.762) | +0.1471 (+0.1443 to +0.1499) | -0.0390 (-0.0406 to -0.0375) | -8.45 (-8.83 to -8.08) | -0.1695 (-0.1775 to -0.1616) | -42.7 (-49.0 to -35.4) |
| Gate | +0.024 (-0.012 to +0.070) | +0.0006 (+0.0001 to +0.0012) | -0.0006 (-0.0008 to -0.0003) | -0.10 (-0.27 to +0.04) | -0.0078 (-0.0097 to -0.0059) | -1.0 (-1.9 to -0.2) |

**Subgroups, 2024 to 2026** (point values):

| Rows | Model | MAE in loans | MAE in ln(1 + loans) | Spearman of the level | Top-10% hit |
| --- | --- | --- | --- | --- | --- |
| Burst on the book or author page (14.3% of rows) | Library + Wikipedia (HW_lgbm, v0) | 7.48 | 0.2751 | 0.9280 | 90.7% |
| Burst on the book or author page (14.3% of rows) | Gate | 7.58 | 0.2774 | 0.9267 | 90.2% |
| Under 12 months of history (1.6% of rows) | Library + Wikipedia (HW_lgbm, v0) | 32.10 | 0.2204 | 0.9525 | 88.3% |
| Under 12 months of history (1.6% of rows) | Gate | 32.82 | 0.2236 | 0.9507 | 87.1% |

**May and June 2025** (two origin months, point values): Library + Wikipedia (HW_lgbm, v0): MAE 4.15 loans, Spearman 0.9226; Gate: MAE 4.24 loans, Spearman 0.9220. Without these months the 2024 to 2026 MAE is Library + Wikipedia (HW_lgbm, v0) 4.625; Gate 4.644.

**Split-conformal 80% intervals for next month's loans** (10th and 90th percentile of the previous year's errors on the log scale; coverage should be near 80%).

| Model |  | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Library + Wikipedia (HW_lgbm, v0) | coverage | 76.8% | 78.7% | 81.3% | 80.9% | 80.2% | 79.9% | 80.6% |
|  | median width (loans) | 7.7 | 7.8 | 8.3 | 8.3 | 8.0 | 7.7 | 7.9 |
| Gate | coverage | - | 78.4% | 81.1% | 80.7% | 80.3% | 79.9% | 80.7% |
|  | median width (loans) | - | 7.7 | 8.2 | 8.3 | 8.2 | 7.8 | 8.0 |
| Library + Wikipedia (HW_lgbm, v0), burst rows | coverage | 76.8% | 78.4% | 80.2% | 79.8% | 78.6% | 77.6% | 79.8% |
| Library + Wikipedia (HW_lgbm, v0), under 12 months | coverage | 82.4% | 85.0% | 87.4% | 86.8% | 85.7% | 88.9% | 90.9% |

## 5. Change 2: burst-shape and noise features

Variants: **B1_all** (16 added columns); **B2_reduced** (9 added columns).

not run: same_name and other_r4 are not in burst_features.parquet (they need the Wikimedia REST API).

**Tuning, 2019 to 2023.** Wikipedia-only model of the change (LightGBM, Test A settings) and next month's level:

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Early list: precision@20 of rises | Level Spearman | Level MAE in ln(1 + loans) | Change ranking, burst rows | Early list precision@20, burst rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v0 | 0.138 | 58.2% | 3.46 | 32.3% | 0.418 | 0.6865 | 0.288 | 28.2% |
| B1_all | 0.143 | 58.3% | 3.55 | 33.8% | 0.452 | 0.6725 | 0.293 | 29.7% |
| B2_reduced | 0.140 | 57.9% | 3.48 | 32.4% | 0.450 | 0.6737 | 0.291 | 27.3% |

Early-warning ranker of change 1 (R100e, adopted in change 1: yes) with and without the new columns:

| Ranker | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| ranker without new columns | 33.7% | 15.5% | 0.239 | 0.049 |
| ranker + B1_all | 33.9% | 17.2% | 0.263 | 0.054 |
| ranker + B2_reduced | 31.1% | 15.4% | 0.239 | 0.052 |

Choices: Wikipedia model of the change **B1_all** (tuning change ranking 0.143 against 0.138 for v0, gain +0.0054; adopted: **yes**); ranker **B1_all** (precision@20 33.9% against 33.7% without the new columns, gain +0.3 points; adopted: **yes**).

**One run on 2024 to 2026** (26 months): Wikipedia model B1_all (adopted: yes), ranker B1_all (adopted: yes). Intervals: 95%, 3-month blocks.

**All rows** (197,114 book-months, 182,630 not yet risen).

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Level Spearman | Level MAE in ln(1 + loans) |
| --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model | 0.129 (0.122 to 0.136) | 59.4% (52.9% to 65.8%) | 3.43 (3.07 to 3.98) | 0.512 (0.495 to 0.527) | 0.6663 (0.6630 to 0.6698) |
| v2: with B1_all | 0.131 (0.123 to 0.140) | 61.3% (54.8% to 67.9%) | 3.68 (3.27 to 4.23) | 0.546 (0.532 to 0.560) | 0.6480 (0.6444 to 0.6518) |
| v2 minus v0 (paired) | +0.002 (-0.001 to +0.006) | +1.9 (-0.2 to +4.4) | +0.24 (+0.08 to +0.37) | +0.034 (+0.032 to +0.037) | -0.0183 (-0.0191 to -0.0174) |

Early-warning list (books not yet risen):

| Model | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| v0 Wikipedia model, early list | 29.2% (23.7% to 36.0%) | 14.0% (10.6% to 18.1%) | 0.221 (0.175 to 0.272) | 0.112 (0.104 to 0.120) |
| v2 Wikipedia model, early list | 30.4% (24.0% to 36.5%) | 15.6% (11.0% to 20.0%) | 0.246 (0.188 to 0.304) | 0.115 (0.105 to 0.124) |
| ranker of change 1 | 27.9% (24.4% to 32.5%) | 13.8% (10.4% to 17.7%) | 0.227 (0.188 to 0.270) | 0.050 (0.040 to 0.061) |
| ranker of change 1 with the new columns | 31.5% (26.2% to 37.3%) | 15.4% (11.7% to 19.2%) | 0.250 (0.208 to 0.295) | 0.052 (0.042 to 0.063) |
| v2 minus v0 (Wikipedia model) | +1.2 (-1.9 to +3.8) | +1.5 (-0.8 to +3.7) | +0.025 (+0.002 to +0.048) | +0.003 (+0.000 to +0.006) |
| ranker with minus without new columns | +3.7 (+0.4 to +6.9) | +1.5 (-0.2 to +3.5) | +0.023 (+0.002 to +0.046) | +0.002 (-0.001 to +0.004) |
| ranker with new columns minus v0 | +2.3 (-1.3 to +6.0) | +1.3 (-0.8 to +3.7) | +0.029 (-0.002 to +0.067) | -0.060 (-0.073 to -0.047) |
| ranker of change 1 minus v0 | -1.3 (-5.8 to +2.5) | -0.2 (-2.7 to +2.5) | +0.006 (-0.027 to +0.038) | -0.062 (-0.074 to -0.050) |

**Rows where the book article had a burst (b_rmax at least ln 2, a rise of at least 2 times its normal)** (16,872 book-months, 14,292 not yet risen).

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Level Spearman | Level MAE in ln(1 + loans) |
| --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model | 0.245 (0.226 to 0.266) | 58.7% (51.9% to 65.2%) | 3.39 (3.03 to 3.92) | 0.580 (0.565 to 0.594) | 0.7421 (0.7239 to 0.7602) |
| v2: with B1_all | 0.255 (0.237 to 0.275) | 60.2% (53.8% to 66.3%) | 3.64 (3.20 to 4.19) | 0.605 (0.594 to 0.616) | 0.7217 (0.7068 to 0.7370) |
| v2 minus v0 (paired) | +0.010 (+0.005 to +0.016) | +1.5 (-1.0 to +4.0) | +0.26 (+0.01 to +0.45) | +0.025 (+0.019 to +0.031) | -0.0203 (-0.0254 to -0.0154) |

Early-warning list (books not yet risen):

| Model | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| v0 Wikipedia model, early list | 27.1% (22.5% to 32.9%) | 11.9% (8.7% to 15.6%) | 0.228 (0.185 to 0.275) | 0.168 (0.147 to 0.188) |
| v2 Wikipedia model, early list | 28.5% (23.1% to 33.8%) | 13.7% (9.4% to 17.7%) | 0.261 (0.206 to 0.317) | 0.178 (0.160 to 0.197) |
| ranker of change 1 | 24.0% (20.2% to 28.7%) | 11.0% (7.9% to 14.4%) | 0.217 (0.179 to 0.258) | 0.139 (0.119 to 0.162) |
| ranker of change 1 with the new columns | 28.7% (24.4% to 33.3%) | 12.5% (10.2% to 15.0%) | 0.252 (0.218 to 0.288) | 0.132 (0.114 to 0.148) |
| v2 minus v0 (Wikipedia model) | +1.3 (-1.7 to +4.0) | +1.7 (-0.4 to +3.5) | +0.033 (+0.010 to +0.055) | +0.011 (+0.004 to +0.017) |
| ranker with minus without new columns | +4.6 (+1.2 to +8.1) | +1.5 (-0.4 to +3.3) | +0.034 (+0.004 to +0.066) | -0.007 (-0.025 to +0.008) |
| ranker with new columns minus v0 | +1.5 (-2.3 to +5.0) | +0.6 (-1.9 to +2.7) | +0.024 (-0.010 to +0.057) | -0.036 (-0.048 to -0.022) |
| ranker of change 1 minus v0 | -3.1 (-5.8 to -0.6) | -1.0 (-2.3 to +0.4) | -0.010 (-0.041 to +0.019) | -0.029 (-0.044 to -0.015) |

By test year, precision@20 of rises on books not yet risen (v0 Wikipedia model / v2 Wikipedia model / ranker of change 1 / ranker with the new columns): 2024: 25.0% / 25.0% / 30.0% / 30.0%; 2025: 37.0% / 38.0% / 30.0% / 38.5%; 2026: 23.8% / 26.2% / 23.1% / 24.4%.

**May and June 2025** (two origin months, point values): v0: change ranking 0.107, early list 35.0%; v2: change ranking 0.112, early list 37.5%; ranker without new columns 27.5%, with 35.0%. Without these months: v0: change ranking 0.130, early list 28.8%; v2: change ranking 0.133, early list 29.8%.

**Seed check** (descriptive, 5 LightGBM seeds, 2024 to 2026): the ranker without the new columns gets 27.9% to 30.8% and with them 30.6% to 32.9% (precision@20 of rises); the difference with minus without is +1.7 to +3.7 points over the five seeds (mean +2.6), and 5 of 5 seeds are above 0.

**Noise-column check** (descriptive, 3 LightGBM seeds, 2024 to 2026): adding 16 columns of random numbers to the Wikipedia model changes its change ranking by -0.0026 to -0.0009 (mean -0.0016) and its early-list precision@20 by +0.4 to +1.0 points; adding 16 random columns to the ranker changes its precision@20 by -1.5 to +2.3 points (mean +0.4). Each is compared with the same model and seed without the extra columns.

**Which columns the models use** (descriptive, gain share, models fitted for test year 2026). Wikipedia model of the change: the new columns carry 47% of the gain; largest columns: a_hi28 13%, a_r1 10%, b_r4 9%, b_r1 6%, a_lvl4 5%, b_pre7 5%. Ranker: the new columns carry 36%; largest columns: a_run 19%, a_r1 17%, b_rec 5%, a_rmax 4%, a_dec 4%, a_lvl4 4%.

**Placebo** (placebo features of another book (donor map of 11_placebo_a.py) for every feature of the variant; the gain over placebo v0 should vanish). The new columns should add nothing there. Real and placebo differences, 2024 to 2026 (95% intervals):

| Measure | Real run | Placebo run |
| --- | --- | --- |
| Change ranking, Wikipedia model with minus without the new columns | +0.0025 (-0.0007 to +0.0058) | -0.0034 (-0.0072 to +0.0002) |
| Surge AP over base | +0.24 (+0.08 to +0.37) | -0.01 (-0.04 to +0.02) |
| Early list precision@20 of rises (points), Wikipedia model | +1.2 (-1.9 to +3.8) | -1.3 (-4.4 to +1.5) |
| Early list precision@20 of rises (points), ranker with minus without the new columns | +3.7 (+0.4 to +6.9) | -0.8 (-4.0 to +2.3) |
| Level of next month's loans: MAE in ln(1 + loans) | -0.0183 (-0.0191 to -0.0174) | -0.0058 (-0.0066 to -0.0050) |
| Level of next month's loans: Spearman | +0.0343 (+0.0318 to +0.0370) | +0.0215 (+0.0172 to +0.0253) |
| Change ranking on rows with a burst on the book article | +0.0103 (+0.0051 to +0.0159) | +0.0087 (-0.0052 to +0.0222) |
| Early list precision@20 of rises (points), Wikipedia model, on rows with a burst on the book article | +1.3 (-1.7 to +4.0) | -1.2 (-3.5 to +1.3) |
| Early list precision@20 of rises (points), ranker with minus without the new columns, on rows with a burst on the book article | +4.6 (+1.2 to +8.1) | -1.9 (-5.0 to +1.2) |
| Level MAE in ln(1 + loans) on rows with a burst on the book article | -0.0203 (-0.0254 to -0.0154) | -0.0075 (-0.0087 to -0.0060) |

## 6. Change 5: dated events and the adaptation article's views

Variants: **E1_flags** (4 added columns); **E2_flags_views** (7 added columns).

ad_rel requires that the adaptation article already had views before the end of t: 1,995 work-months with a release in t-1..t+1 become 1,568; rows within 2 months of an event: 0.8% of the rows; scored rows with the flag set: died 621, award 262, ad_rel 931.

**Tuning, 2019 to 2023.** Wikipedia-only model of the change (LightGBM, Test A settings) and next month's level:

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Early list: precision@20 of rises | Level Spearman | Level MAE in ln(1 + loans) | Change ranking, near-event rows | Early list precision@20, near-event rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v0 | 0.138 | 58.2% | 3.46 | 32.3% | 0.418 | 0.6865 | 0.353 | 21.6% |
| E1_flags | 0.139 | 58.5% | 3.55 | 32.1% | 0.417 | 0.6866 | 0.352 | 21.6% |
| E2_flags_views | 0.140 | 59.6% | 3.56 | 32.1% | 0.449 | 0.6731 | 0.354 | 21.2% |

Early-warning ranker of change 1 (R100e, adopted in change 1: yes) with and without the new columns:

| Ranker | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| ranker without new columns | 33.7% | 15.5% | 0.239 | 0.049 |
| ranker + E1_flags | 33.4% | 15.9% | 0.237 | 0.052 |
| ranker + E2_flags_views | 33.0% | 15.3% | 0.228 | 0.053 |

Choices: Wikipedia model of the change **E2_flags_views** (tuning change ranking 0.140 against 0.138 for v0, gain +0.0021; adopted: **yes**); ranker **E1_flags** (precision@20 33.4% against 33.7% without the new columns, gain -0.3 points; adopted: **no**).

**One run on 2024 to 2026** (26 months): Wikipedia model E2_flags_views (adopted: yes), ranker E1_flags (adopted: no). Intervals: 95%, 3-month blocks.

**All rows** (197,114 book-months, 182,630 not yet risen).

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Level Spearman | Level MAE in ln(1 + loans) |
| --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model | 0.129 (0.122 to 0.136) | 59.4% (52.9% to 65.8%) | 3.43 (3.07 to 3.98) | 0.512 (0.495 to 0.527) | 0.6663 (0.6630 to 0.6698) |
| v2: with E2_flags_views | 0.130 (0.123 to 0.138) | 61.3% (55.8% to 65.8%) | 3.50 (3.16 to 3.97) | 0.528 (0.515 to 0.541) | 0.6546 (0.6513 to 0.6582) |
| v2 minus v0 (paired) | +0.001 (-0.001 to +0.003) | +1.9 (-1.3 to +5.2) | +0.07 (-0.04 to +0.15) | +0.017 (+0.014 to +0.020) | -0.0116 (-0.0126 to -0.0108) |

Early-warning list (books not yet risen):

| Model | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| v0 Wikipedia model, early list | 29.2% (23.7% to 36.0%) | 14.0% (10.6% to 18.1%) | 0.221 (0.175 to 0.272) | 0.112 (0.104 to 0.120) |
| v2 Wikipedia model, early list | 30.4% (25.6% to 35.6%) | 15.4% (12.1% to 18.7%) | 0.231 (0.190 to 0.270) | 0.113 (0.105 to 0.122) |
| ranker of change 1 | 27.9% (24.4% to 32.5%) | 13.8% (10.4% to 17.7%) | 0.227 (0.188 to 0.270) | 0.050 (0.040 to 0.061) |
| ranker of change 1 with the new columns | 28.8% (25.6% to 32.1%) | 15.0% (12.3% to 17.9%) | 0.238 (0.202 to 0.271) | 0.051 (0.041 to 0.061) |
| v2 minus v0 (Wikipedia model) | +1.2 (-1.7 to +3.7) | +1.3 (-0.4 to +2.9) | +0.010 (-0.009 to +0.027) | +0.001 (-0.001 to +0.003) |
| ranker with minus without new columns | +1.0 (-2.1 to +3.8) | +1.2 (-1.2 to +3.3) | +0.011 (-0.012 to +0.032) | +0.001 (-0.001 to +0.003) |
| ranker with new columns minus v0 | -0.4 (-4.6 to +3.3) | +1.0 (-1.7 to +3.5) | +0.017 (-0.015 to +0.046) | -0.061 (-0.074 to -0.050) |
| ranker of change 1 minus v0 | -1.3 (-5.8 to +2.5) | -0.2 (-2.7 to +2.5) | +0.006 (-0.027 to +0.038) | -0.062 (-0.074 to -0.050) |

**Rows within 2 months of an event (death, dated award, film or tv release of the book or its author)** (1,215 book-months, 955 not yet risen).

| Model | Change ranking (Spearman) | Top-20 rose (all rows) | Surge AP over base | Level Spearman | Level MAE in ln(1 + loans) |
| --- | --- | --- | --- | --- | --- |
| v0: Test A Wikipedia model | 0.344 (0.286 to 0.411) | 46.3% (40.6% to 51.1%) | 2.65 (2.36 to 3.04) | 0.549 (0.511 to 0.591) | 0.8512 (0.7669 to 0.9529) |
| v2: with E2_flags_views | 0.365 (0.300 to 0.436) | 46.6% (39.8% to 52.5%) | 2.57 (2.22 to 2.98) | 0.565 (0.530 to 0.602) | 0.8328 (0.7503 to 0.9339) |
| v2 minus v0 (paired) | +0.020 (+0.001 to +0.040) | +0.3 (-1.4 to +2.0) | -0.08 (-0.32 to +0.18) | +0.016 (-0.006 to +0.036) | -0.0184 (-0.0328 to -0.0046) |

Early-warning list (books not yet risen):

| Model | Precision@20, rises | Precision@20, surges | NDCG@20 | Spearman, eligible rows |
| --- | --- | --- | --- | --- |
| v0 Wikipedia model, early list | 18.3% (10.0% to 25.0%) | 7.5% (5.0% to 10.0%) | 0.346 (0.243 to 0.527) | 0.120 (0.018 to 0.285) |
| v2 Wikipedia model, early list | 19.2% (15.0% to 25.0%) | 7.5% (4.0% to 15.0%) | 0.357 (0.209 to 0.548) | 0.130 (0.021 to 0.317) |
| ranker of change 1 | 23.3% (16.2% to 35.0%) | 7.5% (4.0% to 15.0%) | 0.330 (0.202 to 0.585) | 0.063 (-0.040 to 0.273) |
| ranker of change 1 with the new columns | 21.7% (15.0% to 30.0%) | 8.3% (5.0% to 15.0%) | 0.316 (0.193 to 0.445) | 0.097 (0.003 to 0.226) |
| v2 minus v0 (Wikipedia model) | +0.8 (-2.5 to +10.0) | -0.0 (-1.7 to +5.0) | +0.010 (-0.044 to +0.101) | +0.009 (-0.014 to +0.046) |
| ranker with minus without new columns | -1.7 (-7.5 to +2.5) | +0.8 (+0.0 to +1.7) | -0.014 (-0.140 to +0.035) | +0.034 (-0.062 to +0.098) |
| ranker with new columns minus v0 | +3.3 (-1.3 to +15.0) | +0.8 (+0.0 to +5.0) | -0.031 (-0.084 to +0.010) | -0.024 (-0.143 to +0.049) |
| ranker of change 1 minus v0 | +5.0 (-0.4 to +15.0) | -0.0 (-1.7 to +5.0) | -0.016 (-0.060 to +0.058) | -0.058 (-0.123 to +0.057) |

By test year, precision@20 of rises on books not yet risen (v0 Wikipedia model / v2 Wikipedia model / ranker of change 1 / ranker with the new columns): 2024: 25.0% / 26.9% / 30.0% / 28.7%; 2025: 37.0% / 37.0% / 30.0% / 30.5%; 2026: 23.8% / 25.6% / 23.1% / 26.9%.

**May and June 2025** (two origin months, point values): v0: change ranking 0.107, early list 35.0%; v2: change ranking 0.113, early list 30.0%; ranker without new columns 27.5%, with 22.5%. Without these months: v0: change ranking 0.130, early list 28.8%; v2: change ranking 0.131, early list 30.4%.

**Which columns the models use** (descriptive, gain share, models fitted for test year 2026). Wikipedia model of the change: the new columns carry 10% of the gain; largest columns: a_r1 16%, b_r4 14%, a_run 8%, a_r4 8%, b_lvl4 7%, b_r1 7%. Ranker: the new columns carry 4%; largest columns: a_r1 33%, b_lvl4 11%, a_lvl4 8%, a_run 6%, a_chg 6%, a_dw 5%.

**Placebo** (the new columns moved 12 months later (value at origin t taken from origin t - 12) with the Test A features left as they are; the gain over the real v0 should vanish). The new columns should add nothing there. Real and placebo differences, 2024 to 2026 (95% intervals):

| Measure | Real run | Placebo run |
| --- | --- | --- |
| Change ranking, Wikipedia model with minus without the new columns | +0.0012 (-0.0005 to +0.0028) | +0.0012 (-0.0003 to +0.0028) |
| Surge AP over base | +0.07 (-0.04 to +0.15) | +0.07 (-0.02 to +0.14) |
| Early list precision@20 of rises (points), Wikipedia model | +1.2 (-1.7 to +3.7) | +1.2 (-1.3 to +3.7) |
| Early list precision@20 of rises (points), ranker with minus without the new columns | +1.0 (-2.1 to +3.8) | +1.0 (-2.3 to +4.2) |
| Level of next month's loans: MAE in ln(1 + loans) | -0.0116 (-0.0126 to -0.0108) | -0.0119 (-0.0162 to -0.0063) |
| Level of next month's loans: Spearman | +0.0169 (+0.0139 to +0.0203) | +0.0179 (+0.0073 to +0.0269) |
| Change ranking on rows within 2 months of an event | +0.0204 (+0.0006 to +0.0398) | +0.0037 (-0.0110 to +0.0200) |
| Early list precision@20 of rises (points), Wikipedia model, on rows within 2 months of an event | +0.8 (-2.5 to +10.0) | +2.5 (+0.0 to +10.0) |
| Early list precision@20 of rises (points), ranker with minus without the new columns, on rows within 2 months of an event | -1.7 (-7.5 to +2.5) | -0.8 (-7.5 to +3.3) |
| Level MAE in ln(1 + loans) on rows within 2 months of an event | -0.0184 (-0.0328 to -0.0046) | -0.0231 (-0.0404 to -0.0070) |

## 7. Choices the note leaves open, and cautions

Each of these was written into `prereg/DEVIATIONS.md` before the result it affects was seen (entries of 20 Oct 17:27, 17:29 and later).

- v0 is the stored Test A prediction (nothing refitted; a refit of W_lgbm for 2019 reproduces it to 3e-17). The main table's rows are the 556,735 rows of `test_a_preds.parquet`.
- "Not yet risen" uses the stored columns of Test A: ln(1 + loans this month) minus ln(1 + median of the last 6 months) below ln 1.5, the same arithmetic as the rise flag, so the threshold is treated the same on both sides.
- Change 1: four variants (truncation level 20 or 100; trained on books not yet risen or on all books with risen ones labelled 0). Choice by the highest tuning precision@20 of rises; adopted when above v0 on the same rows; the chosen variant is run on 2024 to 2026 whether or not it is adopted. Ties in score are ordered by work_id.
- Change 4: the note names three tuning measures and no single one, so the choice among v0 and the two Tweedie powers (and among HW, equal weights and the gate) takes the lowest mean rank over MAE in loans, MAE in ln(1 + loans) and the within-month Spearman. The gate (ridge, 10 inputs, no state main effects, standardized, alpha 1) is judged on 2020 to 2023, because 2019 has no earlier predictions and uses equal weights. Intervals are the 10th and 90th percentile of the previous year's log errors.
- Changes 2 and 5: the Wikipedia regression is chosen by the tuning within-month Spearman of the change, the ranker by tuning precision@20 of rises; each is adopted when above the same model without the new columns. One feature set serves the change and the level model. The ranker is the one chosen in change 1.
- Change 2: the third variant (with same_name and other_r4) was not run because those two columns are not in `burst_features.parquet`; the columns `top500_lists` and `nrm0` of that file are not used.
- Change 5: the release flag e_ad_rel is the file's ad_rel (a film or tv adaptation released in t-1, t or t+1) multiplied by "the adaptation article already had views before the end of t", which this script computes from `events_long.parquet` and the `has_data` column of `adaptation_page_features.parquet` (the empty ad_rel_public column of `events.parquet` is not used). Both variants were run once, after the adaptation views were complete (19:38 on 20 Oct). Only the columns ad_lvl4, ad_r4 and ad_rmax of the adaptation table are used. The placebo moves every new column 12 months later (the value at origin t is the one at origin t - 12 of the same work) and leaves the Test A columns as they are. Events are rare (see section 6), so this change had little to work with.
- Articles that did not exist yet. In Test A the weekly series hold zero views for weeks before an article existed, not missing values (audit of 20 Oct, `prereg/DEVIATIONS.md`), so the 18 Test A columns are always finite there (lvl4 sits at the floor ln 1e-12). v0 is unchanged. The burst columns follow the same rule for days (days before the page existed count as zero views, a zero normal is floored at 1e-12), but a 28-day window with no views at all gives missing values for pk28, dpk, pre7 and rec, and dec is also missing when the peak is on the last 2 days. In the scored rows that is 7.0% of book-article rows and 3.3% of author-article rows for pk28, 14.8% and 11.1% for dec, 10.2% for corr28 and 5.9% for co (hi28 and top500 are 0, not missing). So the new columns treat 'no views in the window' as missing where Test A treats it as the floor value; LightGBM handles both, and the pattern of missing values carries similar information to the floor. The event columns are 0 (not missing) when there is no event, and months since the latest event is 24 when there is none.
- May and June 2025 mean the origin months 2025-05 and 2025-06.
- The top-10% hit rate is the accuracy panel's (it reproduces the stored values for HW_lgbm and H_lgbm); the within-25% share was dropped because the panel's rule could not be reproduced.

Cautions. (1) 2024 to 2026 is not blind: v0's results there were known when the changes were chosen; the frozen live lists are the blind test. (2) Many measures are reported and the intervals are per measure, with no adjustment, so one interval that only just clears zero (for example a lower end of +0.4 points) is weak evidence alone. (3) There are 26 test months, so intervals for precision@20 are wide. (4) The 2024 library gap and May to June 2025 (bot traffic counted as human) are in the 2024 to 2026 numbers; the second is also given alone. (5) Several books of one author can sit in the same top 20. (6) The ranker's precision@20 moves by about 1.5 points with the LightGBM seed alone, and by about as much when random columns are added (sections 3 and 5), so differences below roughly 2 points in precision@20 cannot be told apart from that noise.
