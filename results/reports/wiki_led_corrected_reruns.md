# Corrected reruns of Test A, the placebo, Test C and Test D (addendum e)

Khant Phyo Wai, 01323050. Written 2026-10-20 21:29 by `code/main_study/wiki_led/90c_corrected_reruns_report.py` from the stored result files of the original runs and of the corrected runs. It fits nothing. Rules: `prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json` (fixed 20 Oct 2026 20:34 +07); the background is in `data/reports/wiki_led_code_audit_2026-10-20.md` (items A1, P1, C1) and `prereg/DEVIATIONS.md`, section "Wikipedia-led tests". The original runs and their files are untouched; every corrected file and job has the suffix `_c`.

## 1. What was corrected, and how

- **A1, weeks before an article existed.** In the weekly series of the book and author articles, the weeks before the article's first week with at least one view are now missing, not zero (the settings record says they are missing). In `article_features` (Test A, and through it the placebo and Test D) these weeks are removed before any rolling computation, so an origin month that falls before the first view has no features at all (all nine are missing), and every later feature is computed from the article's own weeks only. In Test C the same weeks are removed from the candidate series before the monthly means are made. Nothing else in the feature definitions changed.
- **P1, placebo donors.** Books are sorted by their matching value (as in addendum b); each book in that order takes the nearest book in the order with a different author key, searching one step down, one step up, two steps down and so on; ties in the matching value are ordered by a fixed random order (seed 20261020); a donor serves at most 3 books. Two choices the addendum left open: books are processed in the sorted order, and a donor must also have a different book article (4 articles are shared by works with different creator strings; without this rule such a work could be given its own article).
- **C1, time-safe candidates in Test C.** For test year Y the candidate book and author articles come only from works whose first Seattle loan (first month with loans in `counts_work.parquet`) is before 1 January of Y. The look-ahead version `Wsel_insample` (used only for C2) keeps the full pool, because it is the version that deliberately uses everything.

Scripts (all in `code/main_study/wiki_led/`, each a copy of the original with only these changes, every one asserts the SHA-256 of its record and of addendum e and runs with `nice`): `10c_test_a.py`, `11c_placebo_a.py`, `20c_test_c.py`, `60c_test_d_rows.py`, `61c_test_d_models.py`, `13c_accuracy_alert_panels.py`, the checks `10c_check_features.py` and `20c_check_series.py`, and this report script. Run times and peak memory of the corrected jobs: Test A 1172 s and 1,320 MB; placebo 114 s and 1,163 MB; Test C 81 s and 829 MB; Test D models 506 s and 1,215 MB (the Test D rows build prints its own footprint in `wiki_led_test_d_data_c.md`).

### Same rows, settings and seeds

- **Test A rows.** The rows of the corrected run are the rows of the original run: same number of rows (yes), and every library column (loans, M6, history features, D, surge flag, level, origin month, work, year) is identical (all 15 columns, 0 differing values). Only the Wikipedia columns differ. Share of scored rows with a book-article feature: 1.0000 original, 0.9338 corrected; with an author-article feature: 0.9409 original, 0.9283 corrected (the record's rule would give about 0.93 for the book articles).
- **Models that do not use Wikipedia.** The predictions of N0, the naive repeat and the library-history LightGBM must not change. Largest absolute difference between the original and the corrected predictions: N0_D 0.00e+00, N0_Y 0.00e+00, Hnaive_D 0.00e+00, Hnaive_Y 0.00e+00, Hlgbm_D 1.11e-16, Hlgbm_Y 8.88e-16 (same rows in the same order: yes). Same seed, same settings, same walk-forward years.
- **Test D rows.** 2,767,485 rows in both files; same rows in the same order: yes; library columns with a differing value: 0. Share of rows with a book-article feature: 0.4811 original, 0.4401 corrected; with an author-article feature: 0.5570 original, 0.5472 corrected. Predictions of the models that do not use Wikipedia (H, naive): largest absolute difference H 2.22e-16, naive 0.00e+00, H_Y 2.22e-16, naive_Y 0.00e+00.
- **Test C rows.** Same rows (format, level, theme, origin) in the same order: yes; differing values in the target and in the forecasts that do not use Wikipedia (repeat last month, seasonal repeat, mean of 6 months, Chronos-2, Chronos-2 + concept pages, median): 0.
- **Placebo rows.** 556,735 scored rows in both runs, same rows in the same order: yes; differing values of the outcome D: 0; library-history predictions carried beside the placebo (from Test A): largest absolute difference 1.11e-16.
- **Recomputation from the saved predictions.** The change rank of W LightGBM, library history and history + Wikipedia, recomputed here from `test_a_preds.parquet` and `test_a_preds_c.parquet` (Spearman within each month, averaged over the 78 months): Wlgbm 0.1346 original, 0.1335 corrected; Hlgbm 0.3503 original, 0.3503 corrected; HWlgbm 0.3597 original, 0.3597 corrected; the values in the tables below come from the result files and agree to four decimals: yes.
- **The corrected feature function.** On 20 articles (10 whose first view is in the first week of the data, 10 later) the corrected function gives exactly the original features for all 10 of the first group, in every origin month; the table is in `data/reports/wiki_led_features_check_c.md`. For every article, from the stored files (`wiki_led_features_check_full_c.md`): the 6,592 articles whose first view is in the first week of the data have 824,000 origin-month rows, of which 0 differ between the original and the corrected file; for the other articles the last row that differs by more than rounding is at most 47 weeks after the first view (median 30), the time the original needed to forget the zero weeks. The corrected file has 1,097,136 rows against 1,303,500: the 206,364 origin months before an article's first view no longer carry features; the corrected file has no row that the original lacks.

## 2. Test A (existing books): Wikipedia predicting next month's change

Rows scored: 556,735 (78 months, 7,747 books, surge rate 0.0278); the same in both runs. Difference = corrected minus original. Intervals are 95% month-block intervals of the corrected run.

### Change rank (Spearman of predicted and actual next-month change, per month, averaged)

| model | original | corrected | difference | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: |
| W rule (no fitting) | 0.0673 | 0.0721 | +0.0047 | [0.0651, 0.0790] |
| W ridge | 0.1017 | 0.1148 | +0.0131 | [0.1052, 0.1236] |
| W LightGBM | 0.1346 | 0.1335 | -0.0012 | [0.1236, 0.1419] |
| H naive (repeat last month) | 0.2329 | 0.2329 | +0.0000 | [0.2167, 0.2458] |
| H LightGBM (library history) | 0.3503 | 0.3503 | +0.0000 | [0.3425, 0.3581] |
| HW LightGBM (history + Wikipedia) | 0.3597 | 0.3597 | +0.0000 | [0.3520, 0.3676] |

### Surge average precision, as a ratio to the base rate

| model | original | corrected | difference | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: |
| W rule (no fitting) | 1.767 | 2.079 | +0.312 | [1.935, 2.237] |
| W ridge | 2.537 | 2.734 | +0.198 | [2.500, 2.992] |
| W LightGBM | 3.448 | 3.446 | -0.003 | [3.126, 3.778] |
| H naive (repeat last month) | 9.385 | 9.385 | +0.000 | [8.554, 10.231] |
| H LightGBM (library history) | 10.782 | 10.782 | +0.000 | [9.858, 11.684] |
| HW LightGBM (history + Wikipedia) | 11.142 | 11.188 | +0.046 | [10.239, 12.111] |

### Level of next month's borrowing (rank correlation within month, and mean absolute error of ln(1 + loans))

| model and measure | original | corrected | difference | corrected 95% interval of the rank |
| --- | ---: | ---: | ---: | ---: |
| N0 (average book): level rank | 0.0000 | 0.0000 | +0.0000 | [0.0000, 0.0000] |
| N0 (average book): MAE (log scale) | 0.7750 | 0.7750 | +0.0000 |  |
| W ridge: level rank | 0.4228 | 0.4224 | -0.0004 | [0.4017, 0.4438] |
| W ridge: MAE (log scale) | 0.6950 | 0.6957 | +0.0006 |  |
| W LightGBM: level rank | 0.4494 | 0.4465 | -0.0029 | [0.4271, 0.4662] |
| W LightGBM: MAE (log scale) | 0.6793 | 0.6812 | +0.0019 |  |
| H naive (repeat last month): level rank | 0.8806 | 0.8806 | +0.0000 | [0.8774, 0.8838] |
| H naive (repeat last month): MAE (log scale) | 0.3165 | 0.3165 | +0.0000 |  |
| H LightGBM: level rank | 0.9095 | 0.9095 | +0.0000 | [0.9062, 0.9127] |
| H LightGBM: MAE (log scale) | 0.2677 | 0.2677 | +0.0000 |  |
| HW LightGBM: level rank | 0.9106 | 0.9107 | +0.0000 | [0.9074, 0.9138] |
| HW LightGBM: MAE (log scale) | 0.2666 | 0.2665 | -0.0001 |  |

### Paired differences (by month, month-block interval)

| difference | original | corrected | change | original 95% interval | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| HW minus H, change rank (the gain of Wikipedia over library history) | 0.0094 | 0.0094 | +0.0000 | [0.0076, 0.0111] | [0.0074, 0.0113] |
| W LightGBM minus W rule, change rank | 0.0673 | 0.0614 | -0.0059 | [0.0616, 0.0731] | [0.0556, 0.0671] |

### The three decisions of the record

| decision | original | corrected | changed |
| --- | ---: | ---: | ---: |
| A1 (primary): W LightGBM change rank, interval above 0 | yes | yes | no |
| A2: HW minus H change rank, interval above 0 | yes | yes | no |
| A3: W LightGBM surge AP ratio, interval above 1 | yes | yes | no |

### Accuracy panel (level predictions, 13_accuracy_alert_panels.py logic on the corrected predictions)

The four models that do not use Wikipedia (no information, repeat last month, median of the last 6 months, library history) are unchanged: largest absolute difference over all nine measures 0.00e+00. The stored original file and a recomputation of the original predictions with the same code agree to 0.0e+00. The three models that use Wikipedia:

| model and measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| Wikipedia only (ridge): MAE_loans | 16.0961 | 16.1412 | +0.0450 |
| Wikipedia only (ridge): median_err | 5.1465 | 5.1527 | +0.0061 |
| Wikipedia only (ridge): WAPE | 0.7323 | 0.7344 | +0.0020 |
| Wikipedia only (ridge): within_2 | 0.2068 | 0.2064 | -0.0003 |
| Wikipedia only (ridge): within_25pct | 0.2638 | 0.2643 | +0.0005 |
| Wikipedia only (ridge): R2_log | 0.1900 | 0.1878 | -0.0023 |
| Wikipedia only (ridge): rank_corr | 0.4228 | 0.4224 | -0.0004 |
| Wikipedia only (ridge): direction_right | 0.5822 | 0.5824 | +0.0003 |
| Wikipedia only (ridge): top10_hit | 0.3508 | 0.3474 | -0.0034 |
| Wikipedia only (trees): MAE_loans | 15.7657 | 15.8253 | +0.0595 |
| Wikipedia only (trees): median_err | 4.9667 | 4.9903 | +0.0236 |
| Wikipedia only (trees): WAPE | 0.7173 | 0.7200 | +0.0027 |
| Wikipedia only (trees): within_2 | 0.2154 | 0.2146 | -0.0008 |
| Wikipedia only (trees): within_25pct | 0.2719 | 0.2709 | -0.0009 |
| Wikipedia only (trees): R2_log | 0.2291 | 0.2240 | -0.0051 |
| Wikipedia only (trees): rank_corr | 0.4494 | 0.4465 | -0.0029 |
| Wikipedia only (trees): direction_right | 0.5851 | 0.5850 | -0.0002 |
| Wikipedia only (trees): top10_hit | 0.3937 | 0.3889 | -0.0048 |
| Library + Wikipedia (trees): MAE_loans | 4.5810 | 4.5808 | -0.0001 |
| Library + Wikipedia (trees): median_err | 2.0847 | 2.0827 | -0.0021 |
| Library + Wikipedia (trees): WAPE | 0.2084 | 0.2084 | -0.0000 |
| Library + Wikipedia (trees): within_2 | 0.4846 | 0.4848 | +0.0002 |
| Library + Wikipedia (trees): within_25pct | 0.6207 | 0.6208 | +0.0001 |
| Library + Wikipedia (trees): R2_log | 0.8682 | 0.8683 | +0.0001 |
| Library + Wikipedia (trees): rank_corr | 0.9106 | 0.9107 | +0.0000 |
| Library + Wikipedia (trees): direction_right | 0.6973 | 0.6975 | +0.0002 |
| Library + Wikipedia (trees): top10_hit | 0.8979 | 0.8978 | -0.0001 |

### Alert lists (top 20 and top 50 books by predicted rise each month; share that rose at least 50% above M6, share that surged)

The same code, run on the original predictions (`13c_accuracy_alert_panels.py --orig`), reproduces the stored original alert file with a largest difference of 0.0e+00 and the stored accuracy file with 0.0e+00, so the original column below is the file written on 20 Oct 17:52 and the differences contain no change of method.

| list and measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| Wikipedia only, top 20: rose | 0.5865 | 0.5788 | -0.0077 |
| Wikipedia only, top 20: surged | 0.3974 | 0.3923 | -0.0051 |
| Wikipedia only, top 20: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Wikipedia only, top 50: rose | 0.4813 | 0.4826 | +0.0013 |
| Wikipedia only, top 50: surged | 0.3008 | 0.3036 | +0.0028 |
| Wikipedia only, top 50: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Wikipedia rule (no fitting), top 20: rose | 0.1545 | 0.2744 | +0.1199 |
| Wikipedia rule (no fitting), top 20: surged | 0.0756 | 0.1538 | +0.0782 |
| Wikipedia rule (no fitting), top 20: months beating the base rate | 0.6282 | 0.9487 | +0.3205 |
| Wikipedia rule (no fitting), top 50: rose | 0.1277 | 0.3064 | +0.1787 |
| Wikipedia rule (no fitting), top 50: surged | 0.0549 | 0.1674 | +0.1126 |
| Wikipedia rule (no fitting), top 50: months beating the base rate | 0.5385 | 0.9872 | +0.4487 |
| Library record, top 20: rose | 0.9205 | 0.9205 | +0.0000 |
| Library record, top 20: surged | 0.7994 | 0.7994 | +0.0000 |
| Library record, top 20: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Library record, top 50: rose | 0.8482 | 0.8482 | +0.0000 |
| Library record, top 50: surged | 0.6467 | 0.6467 | +0.0000 |
| Library record, top 50: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Library + Wikipedia, top 20: rose | 0.9327 | 0.9365 | +0.0038 |
| Library + Wikipedia, top 20: surged | 0.8077 | 0.8167 | +0.0090 |
| Library + Wikipedia, top 20: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Library + Wikipedia, top 50: rose | 0.8644 | 0.8613 | -0.0031 |
| Library + Wikipedia, top 50: surged | 0.6590 | 0.6603 | +0.0013 |
| Library + Wikipedia, top 50: months beating the base rate | 1.0000 | 1.0000 | +0.0000 |
| Page views >= 3x normal (simple rule), top all: rose | 0.2228 | 0.2976 | +0.0748 |
| Page views >= 3x normal (simple rule), top all: surged | 0.1102 | 0.1564 | +0.0462 |

## 3. Placebo: each book given another book's Wikipedia pages (corrected rows, P1 donors)

Donors: 7,744 of the 7,747 books have one (the other 3 books have no Wikipedia feature at all, 133 rows, and keep their own); 7,512 different donors are used, no donor serves more than 3 books (donors by number of books served: 1: 7,302, 2: 188, 3: 22). In the original run one donor served 1,564 books, 19% of the scored rows; now the most used donor has 234 scored rows (0.04%). The nearest donor in the order was found after a median of 1 step (at most 6); the median absolute gap in matching value is 0.0006 (90th percentile 0.0027). The different-article rule changes the donor of 1 book; without it 1 book would have been given its own article.

| model and measure | original | corrected | difference | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: |
| W LightGBM, real pages: change rank | 0.1346 | 0.1335 | -0.0012 | [0.1236, 0.1419] |
| W LightGBM, placebo pages: change rank | 0.0105 | 0.0098 | -0.0007 | [0.0042, 0.0154] |
| HW LightGBM, real pages: change rank | 0.3597 | 0.3597 | +0.0000 | [0.3520, 0.3676] |
| HW LightGBM, placebo pages: change rank | 0.3492 | 0.3496 | +0.0004 | [0.3415, 0.3577] |
| H LightGBM (library history): change rank | 0.3503 | 0.3503 | +0.0000 | [0.3425, 0.3581] |
| W LightGBM, real pages: surge AP ratio | 3.448 | 3.446 | -0.003 |  |
| W LightGBM, placebo pages: surge AP ratio | 0.975 | 0.975 | +0.000 |  |
| HW LightGBM, real pages: surge AP ratio | 11.142 | 11.188 | +0.046 |  |
| HW LightGBM, placebo pages: surge AP ratio | 10.735 | 10.750 | +0.014 |  |
| H LightGBM: surge AP ratio | 10.782 | 10.782 | +0.000 |  |

| difference | original | corrected | change | original 95% interval | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| W real minus W placebo, change rank | 0.1242 | 0.1237 | -0.0005 | [0.1139, 0.1341] | [0.1136, 0.1335] |
| HW real minus HW placebo, change rank | 0.0105 | 0.0101 | -0.0004 | [0.0089, 0.0122] | [0.0084, 0.0118] |
| HW placebo minus H, change rank | -0.0011 | -0.0007 | +0.0004 | [-0.0021, -0.0002] | [-0.0017, 0.0002] |

| model and measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| W LightGBM, real pages: MAE in loans | 15.766 | 15.825 | +0.060 |
| W LightGBM, real pages: WAPE | 0.7173 | 0.7200 | +0.0027 |
| W LightGBM, real pages: level rank | 0.4494 | 0.4465 | -0.0029 |
| W LightGBM, placebo pages: MAE in loans | 16.576 | 16.590 | +0.014 |
| W LightGBM, placebo pages: WAPE | 0.7541 | 0.7548 | +0.0007 |
| W LightGBM, placebo pages: level rank | 0.2608 | 0.2736 | +0.0128 |

Reading rule of addendum b: the signal is specific to the book's own pages when the interval of "real minus placebo" lies above 0.

| reading | original | corrected | changed |
| --- | ---: | ---: | ---: |
| W real minus W placebo, interval above 0 (signal belongs to the book's own pages) | yes | yes | no |
| HW real minus HW placebo, interval above 0 | yes | yes | no |

## 4. Test C (themes): Wikipedia-only forecasts of theme changes, library-guided choice of articles (A1 and C1)

Rows scored: 510 series, 308 groups; share of rows with a Wikipedia forecast 0.9985 original, 0.9978 corrected. C1 check on the corrected selection: of 18,690 selected book articles 0 and of 15,013 selected author articles 0 came only from works first lent on or after 1 January of the test year (the original run: 0.8% and 7.9%).

| forecast (rank correlation of forecast and actual change) | original | corrected | difference | original 95% interval | corrected 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| N0 (no change; rank 0 by definition) | 0.0000 | 0.0000 | +0.0000 | [0.0000, 0.0000] | [0.0000, 0.0000] |
| Wsel ridge (Wikipedia only, library-chosen articles) | 0.0718 | 0.0700 | -0.0018 | [0.0565, 0.0881] | [0.0521, 0.0873] |
| Wsel index (no fitting) | 0.0799 | 0.0703 | -0.0095 | [0.0642, 0.0956] | [0.0509, 0.0897] |
| Wsel in-sample (look-ahead, for C2 only) | 0.3480 | 0.3760 | +0.0280 | [0.3308, 0.3660] | [0.3592, 0.3933] |
| seasonal naive | 0.1887 | 0.1887 | +0.0000 | [0.1563, 0.2162] | [0.1563, 0.2162] |
| mean of the last 6 months | 0.1475 | 0.1475 | +0.0000 | [0.1176, 0.1760] | [0.1176, 0.1760] |
| Chronos-2 alone | 0.3201 | 0.3201 | +0.0000 | [0.2921, 0.3452] | [0.2921, 0.3452] |
| Chronos-2 + concept pages | 0.3317 | 0.3317 | +0.0000 | [0.3024, 0.3588] | [0.3024, 0.3588] |
| median of all months | 0.2730 | 0.2730 | +0.0000 | [0.2412, 0.2993] | [0.2412, 0.2993] |

The references (seasonal naive, mean of 6 months, Chronos-2, median) do not use Wikipedia and are the same rows in both runs; they are listed so that the Wikipedia rows can be read against them.

| measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| Wsel ridge level (y_t + forecast change), error ratio against repeating last month (AvgRelMAE) | 1.1278 | 1.1425 | +0.0147 |
| C2: in-sample minus walk-forward rank (descriptive) | 0.2763 | 0.3061 | +0.0298 |

| decision | original | corrected | changed |
| --- | ---: | ---: | ---: |
| C1 (primary): Wsel ridge rank correlation, interval above 0 | yes | yes | no |

## 5. Test D (all books by format): the Test A models on a 25% sample of all Seattle works plus the Test A works

Rows scored: 1,984,302 (print 640,752, ebook 740,315, audiobook 603,235), the same in both runs. Wikipedia features exist only for the Test A works (book pages) and for works sharing their author; these are the features that changed.

Base rates (same rows in both runs, so unchanged): share of rows that rose print 0.1333, ebook 0.1064, audiobook 0.1099, all 0.1162; share that surged print 0.0222, ebook 0.0154, audiobook 0.0199, all 0.0190. Same in the original file: yes.

### Alert hit rate: share of each month's top 20 and top 50 books (drawn within the format) that rose at least 50% above M6

| format and model | top 20 original | top 20 corrected | difference | corrected exact 95% interval | top 50 original | top 50 corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print, W (Wikipedia only) | 0.4404 | 0.4212 | -0.0192 | [0.3965, 0.4461] | 0.3605 | 0.3518 | -0.0087 |
| print, H (library history) | 0.8750 | 0.8750 | +0.0000 | [0.8576, 0.8910] | 0.8010 | 0.8010 | +0.0000 |
| print, HW (history + Wikipedia) | 0.8724 | 0.8731 | +0.0006 | [0.8555, 0.8892] | 0.8082 | 0.8085 | +0.0003 |
| print, naive (repeat last month) | 0.8135 | 0.8135 | +0.0000 | [0.7932, 0.8325] | 0.7608 | 0.7608 | +0.0000 |
| ebook, W (Wikipedia only) | 0.5038 | 0.4833 | -0.0205 | [0.4583, 0.5085] | 0.3910 | 0.3895 | -0.0015 |
| ebook, H (library history) | 0.8577 | 0.8577 | +0.0000 | [0.8394, 0.8747] | 0.7933 | 0.7933 | +0.0000 |
| ebook, HW (history + Wikipedia) | 0.8801 | 0.8801 | +0.0000 | [0.8630, 0.8958] | 0.8049 | 0.8085 | +0.0036 |
| ebook, naive (repeat last month) | 0.8513 | 0.8513 | +0.0000 | [0.8326, 0.8686] | 0.7597 | 0.7597 | +0.0000 |
| audiobook, W (Wikipedia only) | 0.4776 | 0.4603 | -0.0173 | [0.4353, 0.4854] | 0.3785 | 0.3746 | -0.0038 |
| audiobook, H (library history) | 0.8872 | 0.8872 | +0.0000 | [0.8704, 0.9025] | 0.8097 | 0.8097 | +0.0000 |
| audiobook, HW (history + Wikipedia) | 0.8859 | 0.8859 | +0.0000 | [0.8691, 0.9013] | 0.8190 | 0.8185 | -0.0005 |
| audiobook, naive (repeat last month) | 0.8615 | 0.8615 | +0.0000 | [0.8434, 0.8783] | 0.7890 | 0.7890 | +0.0000 |
| all, W (Wikipedia only) | 0.4741 | 0.4545 | -0.0197 | [0.4401, 0.4689] | 0.3766 | 0.3723 | -0.0043 |
| all, H (library history) | 0.8733 | 0.8733 | +0.0000 | [0.8634, 0.8827] | 0.8014 | 0.8014 | +0.0000 |
| all, HW (history + Wikipedia) | 0.8795 | 0.8797 | +0.0002 | [0.8700, 0.8889] | 0.8107 | 0.8118 | +0.0011 |
| all, naive (repeat last month) | 0.8415 | 0.8415 | +0.0000 | [0.8307, 0.8518] | 0.7693 | 0.7693 | +0.0000 |

### Early-warning hit rate: the same, among rows that had not yet risen (ln(1 + L_t) - ln(1 + M6) below ln 1.5)

| format and model | top 20 original | top 20 corrected | difference | corrected exact 95% interval | top 50 original | top 50 corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print, W (Wikipedia only) | 0.2628 | 0.2545 | -0.0083 | [0.2330, 0.2769] | 0.2110 | 0.2072 | -0.0038 |
| print, H (library history) | 0.4724 | 0.4724 | +0.0000 | [0.4474, 0.4976] | 0.4431 | 0.4431 | +0.0000 |
| print, HW (history + Wikipedia) | 0.4686 | 0.4705 | +0.0019 | [0.4455, 0.4956] | 0.4321 | 0.4356 | +0.0036 |
| print, naive (repeat last month) | 0.1423 | 0.1423 | +0.0000 | [0.1253, 0.1606] | 0.1446 | 0.1446 | +0.0000 |
| ebook, W (Wikipedia only) | 0.2122 | 0.2096 | -0.0026 | [0.1897, 0.2307] | 0.1864 | 0.1831 | -0.0033 |
| ebook, H (library history) | 0.4173 | 0.4173 | +0.0000 | [0.3927, 0.4422] | 0.3982 | 0.3982 | +0.0000 |
| ebook, HW (history + Wikipedia) | 0.4282 | 0.4365 | +0.0083 | [0.4117, 0.4616] | 0.3885 | 0.3890 | +0.0005 |
| ebook, naive (repeat last month) | 0.1660 | 0.1660 | +0.0000 | [0.1479, 0.1854] | 0.1377 | 0.1377 | +0.0000 |
| audiobook, W (Wikipedia only) | 0.2250 | 0.2192 | -0.0058 | [0.1989, 0.2406] | 0.1882 | 0.1869 | -0.0013 |
| audiobook, H (library history) | 0.4218 | 0.4218 | +0.0000 | [0.3971, 0.4467] | 0.4051 | 0.4051 | +0.0000 |
| audiobook, HW (history + Wikipedia) | 0.4378 | 0.4237 | -0.0141 | [0.3990, 0.4487] | 0.3903 | 0.3882 | -0.0021 |
| audiobook, naive (repeat last month) | 0.1622 | 0.1622 | +0.0000 | [0.1442, 0.1814] | 0.1428 | 0.1428 | +0.0000 |
| all, W (Wikipedia only) | 0.2333 | 0.2278 | -0.0056 | [0.2158, 0.2401] | 0.1951 | 0.1921 | -0.0030 |
| all, H (library history) | 0.4372 | 0.4372 | +0.0000 | [0.4229, 0.4515] | 0.4155 | 0.4155 | +0.0000 |
| all, HW (history + Wikipedia) | 0.4449 | 0.4436 | -0.0013 | [0.4293, 0.4580] | 0.4036 | 0.4043 | +0.0007 |
| all, naive (repeat last month) | 0.1575 | 0.1575 | +0.0000 | [0.1472, 0.1682] | 0.1426 | 0.1426 | +0.0000 |

### Accuracy of the level predictions in loans (models that predict the level; W has no level model in Test D)

| format, model and measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| print, naive (repeat last month): MAE in loans | 2.654 | 2.654 | +0.000 |
| print, naive (repeat last month): WAPE | 0.3923 | 0.3923 | +0.0000 |
| print, naive (repeat last month): within 25% | 0.4450 | 0.4450 | +0.0000 |
| print, H (library history): MAE in loans | 2.296 | 2.296 | +0.000 |
| print, H (library history): WAPE | 0.3395 | 0.3395 | +0.0000 |
| print, H (library history): within 25% | 0.3954 | 0.3954 | +0.0000 |
| print, HW (history + Wikipedia): MAE in loans | 2.289 | 2.285 | -0.003 |
| print, HW (history + Wikipedia): WAPE | 0.3383 | 0.3378 | -0.0005 |
| print, HW (history + Wikipedia): within 25% | 0.3972 | 0.3969 | -0.0003 |
| ebook, naive (repeat last month): MAE in loans | 2.597 | 2.597 | +0.000 |
| ebook, naive (repeat last month): WAPE | 0.2996 | 0.2996 | +0.0000 |
| ebook, naive (repeat last month): within 25% | 0.5345 | 0.5345 | +0.0000 |
| ebook, H (library history): MAE in loans | 2.312 | 2.312 | +0.000 |
| ebook, H (library history): WAPE | 0.2667 | 0.2667 | +0.0000 |
| ebook, H (library history): within 25% | 0.5291 | 0.5291 | +0.0000 |
| ebook, HW (history + Wikipedia): MAE in loans | 2.322 | 2.321 | -0.001 |
| ebook, HW (history + Wikipedia): WAPE | 0.2678 | 0.2677 | -0.0001 |
| ebook, HW (history + Wikipedia): within 25% | 0.5245 | 0.5250 | +0.0005 |
| audiobook, naive (repeat last month): MAE in loans | 3.090 | 3.090 | +0.000 |
| audiobook, naive (repeat last month): WAPE | 0.2968 | 0.2968 | +0.0000 |
| audiobook, naive (repeat last month): within 25% | 0.5297 | 0.5297 | +0.0000 |
| audiobook, H (library history): MAE in loans | 2.772 | 2.772 | +0.000 |
| audiobook, H (library history): WAPE | 0.2663 | 0.2663 | +0.0000 |
| audiobook, H (library history): within 25% | 0.5446 | 0.5446 | +0.0000 |
| audiobook, HW (history + Wikipedia): MAE in loans | 2.769 | 2.770 | +0.001 |
| audiobook, HW (history + Wikipedia): WAPE | 0.2660 | 0.2661 | +0.0001 |
| audiobook, HW (history + Wikipedia): within 25% | 0.5396 | 0.5401 | +0.0006 |
| all, naive (repeat last month): MAE in loans | 2.765 | 2.765 | +0.000 |
| all, naive (repeat last month): WAPE | 0.3222 | 0.3222 | +0.0000 |
| all, naive (repeat last month): within 25% | 0.5065 | 0.5065 | +0.0000 |
| all, H (library history): MAE in loans | 2.447 | 2.447 | +0.000 |
| all, H (library history): WAPE | 0.2851 | 0.2851 | +0.0000 |
| all, H (library history): within 25% | 0.4948 | 0.4948 | +0.0000 |
| all, HW (history + Wikipedia): MAE in loans | 2.447 | 2.446 | -0.001 |
| all, HW (history + Wikipedia): WAPE | 0.2851 | 0.2850 | -0.0001 |
| all, HW (history + Wikipedia): within 25% | 0.4920 | 0.4923 | +0.0003 |

### Change rank (Spearman of predicted and actual change within format and month, averaged) and surge AP ratio

| format, model and measure | original | corrected | difference |
| --- | ---: | ---: | ---: |
| print, W (Wikipedia only): change rank | 0.0721 | 0.0722 | +0.0001 |
| print, H (library history): change rank | 0.3272 | 0.3272 | +0.0000 |
| print, HW (history + Wikipedia): change rank | 0.3321 | 0.3320 | -0.0001 |
| print, naive (repeat last month): change rank | 0.1964 | 0.1964 | +0.0000 |
| ebook, W (Wikipedia only): change rank | 0.1164 | 0.1145 | -0.0019 |
| ebook, H (library history): change rank | 0.3482 | 0.3482 | +0.0000 |
| ebook, HW (history + Wikipedia): change rank | 0.3538 | 0.3534 | -0.0005 |
| ebook, naive (repeat last month): change rank | 0.2205 | 0.2205 | +0.0000 |
| audiobook, W (Wikipedia only): change rank | 0.1340 | 0.1308 | -0.0032 |
| audiobook, H (library history): change rank | 0.3470 | 0.3470 | +0.0000 |
| audiobook, HW (history + Wikipedia): change rank | 0.3571 | 0.3565 | -0.0006 |
| audiobook, naive (repeat last month): change rank | 0.2222 | 0.2222 | +0.0000 |
| all, W (Wikipedia only): change rank | 0.1075 | 0.1058 | -0.0017 |
| all, H (library history): change rank | 0.3408 | 0.3408 | +0.0000 |
| all, HW (history + Wikipedia): change rank | 0.3477 | 0.3473 | -0.0004 |
| all, naive (repeat last month): change rank | 0.2130 | 0.2130 | +0.0000 |
| HW minus H, change rank (paired by month, all formats) | 0.0069 | 0.0065 | -0.0004 |
| print, W (Wikipedia only): surge AP ratio | 2.127 | 2.100 | -0.027 |
| print, H (library history): surge AP ratio | 10.480 | 10.480 | +0.000 |
| print, HW (history + Wikipedia): surge AP ratio | 10.747 | 10.704 | -0.042 |
| print, naive (repeat last month): surge AP ratio | 8.764 | 8.764 | +0.000 |
| ebook, W (Wikipedia only): surge AP ratio | 3.970 | 3.937 | -0.033 |
| ebook, H (library history): surge AP ratio | 15.603 | 15.603 | +0.000 |
| ebook, HW (history + Wikipedia): surge AP ratio | 16.478 | 16.499 | +0.021 |
| ebook, naive (repeat last month): surge AP ratio | 13.940 | 13.940 | +0.000 |
| audiobook, W (Wikipedia only): surge AP ratio | 3.037 | 2.995 | -0.042 |
| audiobook, H (library history): surge AP ratio | 14.412 | 14.412 | +0.000 |
| audiobook, HW (history + Wikipedia): surge AP ratio | 14.892 | 14.815 | -0.077 |
| audiobook, naive (repeat last month): surge AP ratio | 13.375 | 13.375 | +0.000 |
| all, W (Wikipedia only): surge AP ratio | 2.817 | 2.782 | -0.035 |
| all, H (library history): surge AP ratio | 13.185 | 13.185 | +0.000 |
| all, HW (history + Wikipedia): surge AP ratio | 13.669 | 13.625 | -0.045 |
| all, naive (repeat last month): surge AP ratio | 11.787 | 11.787 | +0.000 |

Paired HW minus H, change rank: original [0.0059, 0.0078], corrected [0.0056, 0.0073].

### The 90% question (addendum d): is the HW top-20 hit rate at least 0.90?

| format, period | list slots | original hit rate | original interval | at least 0.90 | corrected hit rate | corrected interval | at least 0.90 | difference | answer changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print, 2019-2026 | 1,560 | 0.8724 | [0.8549, 0.8886] | no | 0.8731 | [0.8555, 0.8892] | no | +0.0006 | no |
| print, 2024-2026 | 520 | 0.8500 | [0.8164, 0.8796] | no | 0.8500 | [0.8164, 0.8796] | no | +0.0000 | no |
| ebook, 2019-2026 | 1,560 | 0.8801 | [0.8630, 0.8958] | no | 0.8801 | [0.8630, 0.8958] | no | +0.0000 | no |
| ebook, 2024-2026 | 520 | 0.9212 | [0.8946, 0.9428] | yes | 0.9231 | [0.8967, 0.9445] | yes | +0.0019 | no |
| audiobook, 2019-2026 | 1,560 | 0.8859 | [0.8691, 0.9013] | no | 0.8859 | [0.8691, 0.9013] | no | +0.0000 | no |
| audiobook, 2024-2026 | 520 | 0.9269 | [0.9011, 0.9478] | yes | 0.9308 | [0.9054, 0.9510] | yes | +0.0038 | no |
| all, 2019-2026 | 4,680 | 0.8795 | [0.8698, 0.8887] | no | 0.8797 | [0.8700, 0.8889] | no | +0.0002 | no |
| all, 2024-2026 | 1,560 | 0.8994 | [0.8833, 0.9138] | no | 0.9013 | [0.8854, 0.9156] | yes | +0.0019 | YES |

Addendum d asks whether the rate is at least 0.90 in each format. Every format at least 0.90: 2019-2026: no in the original run, no in the corrected run; 2024-2026: no in the original run, no in the corrected run. The line that changes is all, 2024-2026: 1,403 of 1,560 list slots rose in the original run and 1,406 in the corrected run (+3 slots), which moves the rate from 0.8994 to 0.9013, across 0.90; the exact 95% interval contains 0.90 in both runs.

## 6. What changed, in plain English

**The three corrections.** First (A1), a Wikipedia article that did not exist yet used to count as an article with zero views. Its first weeks then looked like a huge burst, because its "normal" level was zero, and a tree model could tell "this author will have a page later" from "this author has no page", which is information from the future. Now the weeks before an article's first view are missing. Second (P1), in the placebo one donor book used to lend its pages to 1,564 books (19% of the scored rows); now a donor serves at most 3 books, and the most used donor covers 234 scored rows (0.04%). Third (C1), in Test C the articles a theme could choose from used to include works that Seattle only started lending later; now, for each test year, only works first lent before 1 January of that year count, and none of the 18,690 selected book articles and 15,013 selected author articles breaks this rule. A second review of the corrected scripts against the originals found no other difference than these three corrections and the `_c` output names.

**What did not move.** Everything that uses only the library record is the same in both runs: the rows, the outcomes, and the predictions of the naive repeat and of the library-history model (largest difference 8.9e-16, rounding). So every change below comes from the Wikipedia features.

**Test A (existing books).** Wikipedia alone (LightGBM) ranks next month's changes at 0.1335 instead of 0.1346, 0.0012 lower, which is the size of the look-ahead the audit expected from author pages created later (0.001 to 0.002). The no-fitting rule gains the most, because newly created pages no longer fill its list: change rank 0.0673 to 0.0721, surge ratio 1.767 to 2.079, and the share of its top 20 that rose 0.1545 to 0.2744. The ridge model also gains (0.1017 to 0.1148). Library + Wikipedia does not move (0.3597), and Wikipedia's gain over the library record stays at 0.0094 (interval 0.0074 to 0.0113). The Wikipedia-only alert list is a little weaker at the very top (top 20 that rose 0.5865 to 0.5788; top 50 0.4813 to 0.4826), and its average error grows from 15.766 to 15.825 loans. The three decisions of the record (A1, A2, A3) stay yes.

**Placebo.** With fair donors and corrected features, the Wikipedia-only model given another book's pages ranks at 0.0098 (was 0.0105), against 0.1335 for the real pages; real minus placebo is 0.1237 (interval 0.1136 to 0.1335; was 0.1242). The reading of addendum b is unchanged: the signal belongs to each book's own pages. One detail moves: with placebo pages added, the library model used to lose a little (-0.0011, interval -0.0021 to -0.0002); now the change is -0.0007 and its interval (-0.0017 to 0.0002) includes 0, so placebo pages no longer clearly hurt the library model.

**Test C (themes).** The walk-forward Wikipedia forecast ranks theme changes at 0.0700 instead of 0.0718 (interval 0.0521 to 0.0873, still above 0, so decision C1 stays yes). The no-fitting index drops more (0.0799 to 0.0703). The version that chooses its articles with the whole period in view rises (0.3480 to 0.3760), so the look-ahead gap C2 grows from 0.2763 to 0.3061: the flu-paper way of choosing articles makes the method look 5.38 times better than it is, instead of 4.85 times. The library-history references are the same in both runs (Chronos-2 0.3201).

**Test D (all books, by format).** The Wikipedia-only list is weaker on all books: the share of its top 20 that rose falls by 0.0173 to 0.0205 in each format (all formats 0.4741 to 0.4545; print 0.4404 to 0.4212; ebook 0.5038 to 0.4833; audiobook 0.4776 to 0.4603). Among books that had not yet risen it falls from 0.2333 to 0.2278, still above the naive repeat (0.1575) and below the library record (0.4372). Library + Wikipedia hardly moves (top 20, all formats, 0.8795 to 0.8797; early warning 0.4449 to 0.4436), and Wikipedia's gain over the library record in change rank is 0.0065 (interval 0.0056 to 0.0073) instead of 0.0069 (0.0059 to 0.0078).

**The 90% question.** Addendum d asks whether library + Wikipedia's top 20 rose at least 90% of the time in each format. The answer stays no in both runs, because print stays below: 0.8500 in 2024 to 2026 in both runs and 0.8731 (was 0.8724) over 2019 to 2026. Ebooks (0.9212 to 0.9231) and audiobooks (0.9269 to 0.9308) stay above 0.90 in 2024 to 2026. One yes-or-no line flips: all formats together in 2024 to 2026 goes from 0.8994 to 0.9013, that is from 1,403 to 1,406 hits out of 1,560 list slots. Three slots cannot settle this. The exact interval contains 0.90 in both runs (0.8833 to 0.9138 before, 0.8854 to 0.9156 after), and in Test A, changing only the seed of the trees moves the library + Wikipedia top-20 hit rate by up to 0.6 points (check R2 in `wiki_led_robustness.md`), three times the 0.19 points seen here. In the text this line is best given as "0.901, interval 0.885 to 0.916", not as the target being met.

**Decisions.** Of the 16 yes-or-no readings compared (the record's A1 to A3, the two placebo readings, C1, the eight lines of addendum d's 90% question and the two "every format" answers), one changes, and it is not a decision of the record: the pooled all-formats line of the 90% question for 2024 to 2026, which crossed 0.90 by three list slots. The answer addendum d asks for, at least 0.90 in each format, stays no for both periods.

**In one sentence each.** Test A: Wikipedia alone still predicts which books' borrowing rises (0.1335, a little less than reported) and adds the same small amount to the library record (0.0094). Placebo: the signal still comes from each book's own pages. Test C: the theme version stays weak but above chance (0.0700), and choosing articles with hindsight now looks even more misleading. Test D: on all books the Wikipedia-only list is about two points weaker, library + Wikipedia is unchanged, and print still misses the 90% target.

## 7. Choices made while coding (logged in `prereg/DEVIATIONS.md`, section "Wikipedia-led tests", entry of 20 Oct 2026 21:30 +07)

The addendum fixes the three corrections; these are the points it left open. They were written into the scripts before the run that uses them (the scripts are saved under the `c` names) and were not changed after a result was seen.

1. **A1, how "missing" is represented.** The weeks before the first week with views are removed from the weekly series before any rolling computation. An origin month that ends before the article has a complete week of views therefore has all nine features missing together (not a mix of missing values and zero counts), which is what the record says and what removes the look-ahead group of author articles that appear later. An article with no view in any week up to the last origin month has no features: 23 of the 7,427 book articles and 7 of the 3,001 author articles of Test A with weekly data (1 book and 2 author articles have no view at all; the others have their first view in the last weeks of the data). In an article's first months some features are still missing because their windows need data (r4, r1 and rmax need 13 weekly values before the last 4 weeks, chg needs 5 weeks), exactly as at the start of the original series.
2. **P1, open points.** Books are processed in the sorted order (matching value, then the fixed random order). The random order is `numpy.random.default_rng(20261020).permutation` over the 7,747 work ids in ascending order. A donor must also have a different book article than the recipient (this changes the donor of 1 book). The 24 books with no book-article matching value are matched on the author-article value in a second pass over the same rule (21 books); the other 3 have neither value, have no Wikipedia feature in any row, and keep their own features, which are all missing (133 rows). The stepwise donor search is checked in the script against an independent brute-force search (identical donors).
3. **C1, open points.** An article is a candidate in test year Y when at least one of the theme's works that carries it (strength at least 0.25 on that theme) had its first loan before 1 January of Y. The look-ahead version `Wsel_insample` keeps the full pool, as it is the version that uses everything on purpose. The concept-term series are not article series and are unchanged.
4. **Test D rows, checks.** The data script checks the rows against fixed rules; two of them said "all b_ (or a_) features present or all missing". With corrected features an article's first months have some features missing, so these rules now read: features are missing for works without the page, and lvl4 is missing exactly when the whole set is.
5. **Alert and accuracy panels.** The corrected panels are written by `13c_accuracy_alert_panels.py`, the same logic as `13_accuracy_alert_panels.py`. The original panels were also recomputed with this code (`--orig`, written to `data/interim/wiki_led_panels_orig_recomputed/`): they equal the stored original files exactly, so the differences in section 2 contain no change of method. (The code audit's own recomputation of the alert list had differed by up to 0.0007 because it ordered tied scores differently.)

## 8. Not rerun here

The live October list (frozen and published) is not changed; improvement rounds v1 and v2 keep their stored results and are labelled as run on the uncorrected features; Test B is unaffected (monthly author views, `matched_pre` already time-safe). The robustness checks R1 to R7 of addendum e are reported separately (`data/reports/wiki_led_robustness.md`), not here. Figures quoted in the results draft that are not stored in the result files compared above (for example the overlap of the Wikipedia and library lists, or the share of each list already up at the origin) are not recomputed here; the summary-checks task (`data/reports/handoff_summary_checks.md`) plans to report them for the original and the corrected files.

Decisions compared: 16; changed: 1 (Test D q90: all|2024-2026).

## Appendix: the checks of the corrected feature functions

### A. The 20-article test of `article_features` (written before the Test A rerun was started)

Written by `code/main_study/wiki_led/10c_check_features.py`. The two functions are the `article_features` of `10_test_a.py` (original) and `10c_test_a.py` (corrected), read from the files with `ast` and run on the weekly series of 20 articles drawn with seed 20261020: 5 book and 5 author articles whose first week with views is the first week of the data (29 June 2015), and 5 + 5 whose first view is later. Each article has one row per origin month from 2016-03 to 2026-07 for which a week had ended.

| kind | article | first week with views | first view in week 1 of the data | origin months, original | corrected | identical origin months | differing origin months | all identical (week-1 articles) | largest difference where both are finite | origin months with no corrected row (original lvl4 -> corrected) | last origin month differing by more than 1e-9 | origin months differing only by rounding (below 1e-9) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | Calico Joe | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | The Seven Principles for Making Ma | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | The Stepford Wives | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Bleachers (novel) | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Odyssey | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Prequel: An American Fight Against | 2023-11-27 | no | 125 | 32 | 25 | 100 | - | 101 | 93 (lvl4 -27.63 -> missing) | 2024-06 (31 wk after first view) | 0 |
| book | The Heart (novel) | 2017-12-11 | no | 125 | 104 | 58 | 67 | - | 85.5 | 21 (lvl4 -27.63 -> missing) | 2018-06 (29 wk after first view) | 39 |
| book | Thin Air (Parker novel) | 2019-10-14 | no | 125 | 82 | 75 | 50 | - | 76.7 | 43 (lvl4 -27.63 -> missing) | 2020-04 (28 wk after first view) | 0 |
| book | Barkskins | 2016-07-18 | no | 125 | 121 | 113 | 12 | - | 97.3 | 4 (lvl4 -27.63 -> missing) | 2017-02 (32 wk after first view) | 0 |
| book | Master of the Revels: A Return to  | 2022-10-10 | no | 125 | 46 | 42 | 83 | - | 5.52 | 79 (lvl4 -27.63 -> missing) | 2023-01 (16 wk after first view) | 0 |
| author | Daniel Yergin | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Susanna Clarke | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Roberto Bolaño | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Yotam Ottolenghi | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Paul Beatty | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Liz Pelly | 2025-12-29 | no | 125 | 7 | 0 | 125 | - | 94.2 | 118 (lvl4 -27.63 -> missing) | 2026-07 (31 wk after first view) | 0 |
| author | Laura Dave (novelist) | 2024-04-08 | no | 125 | 28 | 18 | 107 | - | 95.1 | 97 (lvl4 -27.63 -> missing) | 2024-10 (29 wk after first view) | 3 |
| author | C Pam Zhang | 2020-05-18 | no | 125 | 75 | 68 | 57 | - | 85.1 | 50 (lvl4 -27.63 -> missing) | 2020-11 (28 wk after first view) | 0 |
| author | Maria Reva | 2020-10-19 | no | 125 | 70 | 62 | 63 | - | 71.1 | 55 (lvl4 -27.63 -> missing) | 2021-05 (32 wk after first view) | 0 |
| author | Kathleen Belew | 2019-06-03 | no | 125 | 86 | 80 | 45 | - | 97.5 | 39 (lvl4 -27.63 -> missing) | 2019-11 (26 wk after first view) | 0 |

- The original function reproduces the stored original features (`test_a_wiki_features.parquet`) exactly for 20 of 20 articles.
- Articles whose first view is in the first week of the data: corrected and original features are identical in every origin month for 10 of 10 (same origin months, same values, NaN equal to NaN, no tolerance).
- Articles whose first view is later: the origin months that end before the article has a complete week of views have no corrected row (all nine features missing; the original gave the floor value of lvl4 and zero-based ratios there), the first months after the first view differ because the original compared the new article with weeks of zero views, and from the month after the one named in the second-last column onward the two agree (differences below 1e-9 are floating-point rounding: a rolling sum that starts in a different week carries a different rounding error in the 15th digit; they are not counted as differences there).

### B. All articles, original and corrected feature files compared (after the rerun)

Written by `code/main_study/wiki_led/10c_check_features.py --full`: the stored original features (`test_a_wiki_features.parquet`) against the corrected ones (`test_a_wiki_features_c.parquet`), row by row on (kind, article, origin month); exact equality with NaN equal to NaN.

| kind | articles with original features | articles whose first view is in week 1 | their origin-month rows | of these rows differing | other articles | their rows | rows exactly identical | rows equal within 1e-9 | rows with no corrected row | articles with at least one row differing by more than 1e-9 | weeks after the first view week of the last such row: median / 99th percentile / max | articles with no view at all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | 7,427 | 4,282 | 535,250 | 0 | 3,144 | 393,000 | 190,399 | 197,882 | 174,651 | 3,071 | 30 / 34 / 47 | 1 |
| author | 3,001 | 2,310 | 288,750 | 0 | 689 | 86,125 | 47,542 | 50,379 | 31,338 | 666 | 30 / 34 / 40 | 2 |

- Rows in the original file 1,303,500, in the corrected file 1,097,136; rows in the corrected file that are not in the original: 0.
- Features that are finite in the original and missing in the corrected file on rows that exist in both (by feature): {'lvl4': 0, 'r4': 13004, 'r1': 13004, 'rmax': 13004, 'nrise8': 0, 'run': 0, 'dw': 0, 'chg': 3207, 'valid4': 0}.

### C. Test C: the monthly candidate series, original and corrected

Written by `code/main_study/wiki_led/20c_check_series.py`. `monthly()` of `20_test_c.py` and of `20c_test_c.py` are read from the files with `ast` and run on the weekly series of every Test A book and author article; x(t) is the month-on-month change of ln(mean weekly share). Exact equality with NaN equal to NaN.

| kind | articles | first view in week 1 | differing months among them | other articles | months before the first view month that are missing in the corrected series | months from two months after the first view month that are identical | articles without any view | as expected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | 7,427 | 4,282 | 0 | 3,144 | 198,687 of 198,687 | 222,609 of 222,609 | 1 | yes |
| author | 3,001 | 2,310 | 0 | 689 | 36,529 of 36,529 | 55,797 of 55,797 | 2 | yes |

