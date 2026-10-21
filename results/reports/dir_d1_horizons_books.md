# Direction D1, books: does Wikipedia help more when we predict further ahead?

Khant Phyo Wai, 01323050. Run 22 Oct 2026, 03:18 to 03:22 +07, settings `prereg/addenda_wiki_led/2026-10-22_i_directions.json` (section D1_horizons_books).

1. **Question.** Test A ranked the 7,747 Seattle works with their own English Wikipedia article by how much their borrowing would rise next month above their normal (six-month median); here the same rows, features and models predict the average of the next 1, 3, 6 or 12 months, to see whether Wikipedia's value grows further ahead.
2. **Wikipedia alone gets a little better, the library record much more.** Mean within-month Spearman of Wikipedia only: 0.133, 0.158, 0.157, 0.160 at 1, 3, 6, 12 months (+0.02 over one month at each horizon, paired intervals above zero); library history only: 0.350, 0.444, 0.481, 0.509; library + Wikipedia: 0.360, 0.454, 0.492, 0.519.
3. **What Wikipedia adds to the library record does not grow.** Library + Wikipedia minus library alone: +0.009, +0.011, +0.011, +0.010 (all intervals above zero); against one month on the same months the change is +0.001 at 3, 6 and 12 months (intervals -0.001 to +0.003, -0.002 to +0.004, -0.005 to +0.006, all including zero).
4. **Top-20 lists.** Of the 20 books each model ranks highest per month, the share whose average rose to at least 1.5 times normal: library + Wikipedia 93.7%, 87.5%, 81.1%, 86.0%; library alone 92.1%, 85.9%, 79.7%, 85.6%; Wikipedia alone 57.9%, 56.6%, 52.8%, 48.7%; all books 11.3%, 9.1%, 9.7%, 11.1%. Adding Wikipedia lifts the library's list by 1.6, 1.6, 1.5 and 0.4 points, clearly above zero only at one month.
5. **Meaning.** A longer window does not make Wikipedia more useful for single books: its small added value is the same size at every horizon, and Wikipedia's own score as a share of the library model's falls from 38% to 31%, because the library record gains far more from the smoother target. The 12-month result rests on 34 origin months (2019-01 to 2023-04); the same pattern holds when every horizon is scored on those 34 months (Table 5). At one month the refit reproduces Test A's corrected scores, intervals, top-20 shares and predictions exactly (Table 7), so the other horizons differ from Test A only by the target and the rows and training windows that it requires.

## How it was done

- **Code:** `code/main_study/wiki_led/dirs/d1_horizons_books.py` (header written before any result; it lists the settings used and the choices c1 to c9 the addendum did not fix). **Data:** `data/db/wiki_led/dirs/d1_books/` (`targets.parquet`, `preds_k1.parquet` to `preds_k12.parquet`, `results.json`, `tables.md`). **Log:** `data/reports/dir_d1_horizons_books.log`. Run time 207 s, peak memory 849 MB, run through `jobs/heavy_lock.sh` with `nice`, LightGBM 4 threads.
- **Rows:** Test A's corrected rows (`data/db/wiki_led/test_a_rows_c.parquet`, 750,501 rows, origins 2016-03 to 2026-07; scored origins from 2019-01). Loans per work and month were rebuilt exactly as Test A does (`data/db/study2r/counts_work.parquet`, all formats summed, months before the first loan missing) and matched Test A's next-month and current-month loans on every row; the excluded months are Test A's (2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08).
- **Target for horizon k:** D_k = ln(1 + mean of loans in months t+1 to t+k) minus ln(1 + M6), with M6 the median of months t-5 to t (Test A's change target with the mean in place of next month). Rose: D_k at least ln 1.5, which is Test A's rule as its code applies it, (1 + mean) at least 1.5 times (1 + M6). Surged: D_k at least ln 2 and the mean at least 5 loans above M6. A row is kept only when all k months are observed: none excluded and none after 2026-08.
- **Models:** Test A's three LightGBM models, refit for each k with Test A's exact settings and seed (nothing tuned): W (the 18 book and author Wikipedia features), H (the 6 library history features), HW (both). Persistence is Test A's naive change ranking, ln(1 + L_t) minus ln(1 + M6), the same for every k. Walk-forward by test year 2019 to 2026; the test year of a row is the year of month t+1 (as in Test A), and a row trains the model for test year Y only when its whole window t+1 to t+k ends before 1 January of Y, so no model learns from loans in its test year.
- **Scoring:** Spearman of predicted and actual D_k across books within each origin month, averaged over months; 95% intervals from 2,000 draws of blocks of 3 consecutive scored months (seed 20261020, Test A's procedure); HW minus H and the change from k = 1 are paired by month. Top 20: each month's 20 highest-scored books (sorted as in Test A's alert-list code), share that rose, averaged over months, with the same month-block interval.
- **Not done here:** Test A's book-resampling interval, its ridge and no-fitting Wikipedia models and its level target (not named for D1); no placebo was rerun per horizon. All results are descriptive, as the addendum says.

## Things to keep in mind

- **Fewer months at long horizons.** The windows must not touch an excluded month or run past 2026-08, so k = 3 keeps 70 of the 78 scored origin months, k = 6 keeps 58, k = 12 keeps 34 (2019-01 to 2019-03 and 2020-10 to 2023-04). Table 5 scores every horizon on those same 34 months; within an origin month the books are the same at every horizon, so those are also the same rows.
- **Older training data at long horizons.** Because the whole window must end before the test year, the 12-month model for 2021 learns from origins up to 2019-03 only, and the 6-month model for 2026 from origins up to 2025-01 (Table 8). This is the honest cost of predicting a year ahead, and it falls on all three models alike.
- **Why every score rises with k.** The average of several months is a smoother target than one month, so all rankings find it easier; Wikipedia alone gains about +0.02 at every horizon (about what the persistence rule gains at 3 months), while the library model gains +0.09 to +0.15. The rise of W is therefore not evidence that Wikipedia sees further ahead than the library record does.
- **Persistence versus the library model in the top 20.** At 3 and 6 months the simple persistence rule's top 20 rose about as often as the library model's (86.8% against 85.9%, 82.3% against 79.7%), although its Spearman across all books is far lower (0.257 against 0.444, 0.242 against 0.481).
- **Test A's limits carry over:** the works were chosen by at least 500 loans in 2016 to 2026 and by having an article at the end of the period (a look-ahead in the choice of books, not in their views or loans).

## Tables

All intervals are 95% month-block bootstrap intervals. W = Wikipedia only, H = library history only, HW = library + Wikipedia, persistence = last month's change from normal.

### Table 1. Spearman per horizon, each horizon on all its own origin months

| Horizon k | Origin months | Rows | Wikipedia only (W) | Library history (H) | Library + Wikipedia (HW) | Persistence | HW minus H |
|---|---|---|---|---|---|---|---|
| 1 | 78 (2019-01 to 2026-07) | 556,735 | 0.133 [0.124, 0.142] | 0.350 [0.343, 0.358] | 0.360 [0.352, 0.368] | 0.233 [0.217, 0.246] | +0.009 [+0.007, +0.011] |
| 3 | 70 (2019-01 to 2026-05) | 498,278 | 0.158 [0.147, 0.170] | 0.444 [0.436, 0.451] | 0.454 [0.447, 0.461] | 0.257 [0.241, 0.270] | +0.011 [+0.008, +0.014] |
| 6 | 58 (2019-01 to 2026-02) | 410,815 | 0.157 [0.143, 0.172] | 0.481 [0.475, 0.488] | 0.492 [0.485, 0.499] | 0.242 [0.223, 0.257] | +0.011 [+0.006, +0.014] |
| 12 | 34 (2019-01 to 2023-04) | 237,316 | 0.160 [0.140, 0.179] | 0.509 [0.500, 0.520] | 0.519 [0.511, 0.527] | 0.214 [0.187, 0.235] | +0.010 [+0.003, +0.016] |

### Table 2. Share of each model's top 20 per month that rose (mean of next k months at least 1.5 times normal)

| Horizon k | Base rate (all books) | W | H | HW | Persistence | HW minus H (points) |
|---|---|---|---|---|---|---|
| 1 | 11.3% [10.8, 11.9] | 57.9% [54.5, 61.0] | 92.1% [90.2, 93.9] | 93.7% [91.8, 95.4] | 89.3% [85.4, 92.2] | +1.6 [+0.3, +3.1] |
| 3 | 9.1% [8.5, 9.8] | 56.6% [52.8, 60.6] | 85.9% [82.1, 89.2] | 87.5% [83.9, 90.9] | 86.8% [82.9, 89.9] | +1.6 [-0.1, +3.6] |
| 6 | 9.7% [9.1, 10.4] | 52.8% [49.4, 56.0] | 79.7% [74.0, 84.5] | 81.1% [75.4, 85.9] | 82.3% [76.6, 86.2] | +1.5 [-0.1, +3.2] |
| 12 | 11.1% [10.3, 12.1] | 48.7% [43.8, 53.5] | 85.6% [81.0, 90.3] | 86.0% [81.8, 90.1] | 79.9% [75.4, 83.8] | +0.4 [-1.5, +2.5] |

### Table 3. Share of each model's top 20 per month that surged (mean at least 2 times normal and 5 loans more)

| Horizon k | Base rate | W | H | HW | Persistence |
|---|---|---|---|---|---|
| 1 | 2.8% [2.6, 3.0] | 39.2% [36.0, 42.4] | 79.9% [76.9, 83.0] | 81.7% [79.0, 84.4] | 75.6% [71.2, 79.6] |
| 3 | 2.3% [2.1, 2.5] | 36.8% [33.9, 39.6] | 65.2% [60.6, 69.9] | 68.2% [63.1, 73.3] | 65.8% [61.1, 70.4] |
| 6 | 2.6% [2.4, 2.7] | 35.6% [32.5, 38.9] | 52.2% [46.8, 57.2] | 55.5% [49.8, 60.9] | 58.0% [52.4, 63.1] |
| 12 | 3.1% [2.9, 3.3] | 31.9% [28.5, 35.3] | 54.0% [46.2, 60.7] | 54.3% [46.5, 60.7] | 51.8% [45.4, 58.2] |

### Table 4. Change from k = 1, paired by origin month (months where both horizons exist)

| Horizon k | Months | W at k=1 (same months) | W: k minus 1 | H: k minus 1 | HW minus H at k=1 (same months) | HW minus H: k minus 1 | Top-20 rose, HW minus H: k minus 1 (points) |
|---|---|---|---|---|---|---|---|
| 3 | 70 | 0.135 [0.126, 0.145] | +0.023 [+0.019, +0.027] | +0.091 [+0.087, +0.095] | +0.010 [+0.008, +0.012] | +0.001 [-0.001, +0.003] | +0.3 [-1.1, +1.7] |
| 6 | 58 | 0.135 [0.124, 0.146] | +0.022 [+0.015, +0.030] | +0.125 [+0.118, +0.132] | +0.010 [+0.008, +0.012] | +0.001 [-0.002, +0.004] | -0.0 [-2.0, +2.3] |
| 12 | 34 | 0.137 [0.119, 0.153] | +0.023 [+0.010, +0.036] | +0.152 [+0.140, +0.167] | +0.009 [+0.006, +0.012] | +0.001 [-0.005, +0.006] | +0.3 [-2.4, +2.8] |

### Table 5. Every horizon on the same 34 origin months (those available at k = 12)

| Horizon k | W | H | HW | Persistence | HW minus H | Top-20 rose: base | Top-20 rose: H | Top-20 rose: HW | Top-20 rose: W |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.137 [0.119, 0.153] | 0.357 [0.349, 0.364] | 0.366 [0.357, 0.374] | 0.241 [0.213, 0.260] | +0.009 [+0.006, +0.012] | 11.9% [11.1, 12.7] | 92.6% [90.4, 94.7] | 92.8% [89.9, 95.1] | 56.9% [52.1, 61.6] |
| 3 | 0.163 [0.143, 0.182] | 0.448 [0.441, 0.456] | 0.458 [0.450, 0.466] | 0.260 [0.231, 0.280] | +0.010 [+0.005, +0.015] | 9.7% [8.9, 10.5] | 87.9% [85.1, 90.4] | 90.1% [86.8, 93.1] | 55.9% [50.7, 61.5] |
| 6 | 0.163 [0.141, 0.183] | 0.483 [0.476, 0.491] | 0.493 [0.486, 0.500] | 0.242 [0.214, 0.261] | +0.010 [+0.003, +0.015] | 10.1% [9.3, 10.9] | 85.1% [80.7, 89.4] | 86.0% [81.9, 90.0] | 52.8% [48.4, 56.9] |
| 12 | 0.160 [0.140, 0.179] | 0.509 [0.500, 0.520] | 0.519 [0.511, 0.527] | 0.214 [0.187, 0.235] | +0.010 [+0.003, +0.016] | 11.1% [10.3, 12.1] | 85.6% [81.0, 90.3] | 86.0% [81.8, 90.1] | 48.7% [43.8, 53.5] |

### Table 6. Spearman by test year (mean over that year's origin months; descriptive)

| Horizon k | Test year | Months | W | H | HW | Persistence | HW minus H |
|---|---|---|---|---|---|---|---|
| 1 | 2019 | 11 | 0.123 | 0.335 | 0.344 | 0.231 | +0.009 |
| 1 | 2020 | 5 | 0.085 | 0.328 | 0.332 | 0.133 | +0.003 |
| 1 | 2021 | 12 | 0.144 | 0.364 | 0.372 | 0.262 | +0.008 |
| 1 | 2022 | 12 | 0.151 | 0.358 | 0.370 | 0.250 | +0.012 |
| 1 | 2023 | 12 | 0.147 | 0.357 | 0.369 | 0.249 | +0.012 |
| 1 | 2024 | 8 | 0.125 | 0.365 | 0.373 | 0.222 | +0.008 |
| 1 | 2025 | 10 | 0.134 | 0.349 | 0.359 | 0.240 | +0.011 |
| 1 | 2026 | 8 | 0.124 | 0.330 | 0.338 | 0.205 | +0.008 |
| 3 | 2019 | 11 | 0.150 | 0.434 | 0.442 | 0.260 | +0.008 |
| 3 | 2020 | 3 | 0.087 | 0.435 | 0.434 | 0.116 | -0.000 |
| 3 | 2021 | 12 | 0.167 | 0.458 | 0.465 | 0.278 | +0.007 |
| 3 | 2022 | 12 | 0.178 | 0.441 | 0.457 | 0.270 | +0.016 |
| 3 | 2023 | 12 | 0.172 | 0.447 | 0.462 | 0.272 | +0.015 |
| 3 | 2024 | 6 | 0.141 | 0.461 | 0.472 | 0.228 | +0.012 |
| 3 | 2025 | 8 | 0.160 | 0.439 | 0.450 | 0.275 | +0.011 |
| 3 | 2026 | 6 | 0.140 | 0.426 | 0.432 | 0.226 | +0.007 |
| 6 | 2019 | 9 | 0.154 | 0.476 | 0.481 | 0.248 | +0.005 |
| 6 | 2020 | 2 | 0.064 | 0.484 | 0.474 | 0.035 | -0.010 |
| 6 | 2021 | 12 | 0.165 | 0.490 | 0.502 | 0.259 | +0.013 |
| 6 | 2022 | 12 | 0.179 | 0.475 | 0.489 | 0.250 | +0.014 |
| 6 | 2023 | 11 | 0.167 | 0.482 | 0.497 | 0.249 | +0.014 |
| 6 | 2024 | 4 | 0.135 | 0.498 | 0.512 | 0.207 | +0.015 |
| 6 | 2025 | 5 | 0.147 | 0.478 | 0.488 | 0.275 | +0.010 |
| 6 | 2026 | 3 | 0.123 | 0.471 | 0.471 | 0.229 | +0.000 |
| 12 | 2019 | 3 | 0.138 | 0.495 | 0.489 | 0.225 | -0.006 |
| 12 | 2020 | 2 | 0.079 | 0.552 | 0.533 | 0.024 | -0.018 |
| 12 | 2021 | 12 | 0.158 | 0.520 | 0.530 | 0.230 | +0.010 |
| 12 | 2022 | 12 | 0.176 | 0.499 | 0.512 | 0.219 | +0.014 |
| 12 | 2023 | 5 | 0.172 | 0.501 | 0.522 | 0.233 | +0.021 |

### Table 7. Check: k = 1 against Test A (corrected)

| Measure | This script | Test A |
|---|---|---|
| Spearman W | 0.133 [0.124, 0.142] | 0.133 [0.124, 0.142] |
| Spearman H | 0.350 [0.343, 0.358] | 0.350 [0.343, 0.358] |
| Spearman HW | 0.360 [0.352, 0.368] | 0.360 [0.352, 0.368] |
| Spearman Persistence | 0.233 [0.217, 0.246] | 0.233 [0.217, 0.246] |
| HW minus H | +0.009 [+0.007, +0.011] | +0.009 [+0.007, +0.011] |
| Top-20 rose W | 57.88% | 57.88% |
| Top-20 surged W | 39.23% | 39.23% |
| Top-20 rose H | 92.05% | 92.05% |
| Top-20 surged H | 79.94% | 79.94% |
| Top-20 rose HW | 93.65% | 93.65% |
| Top-20 surged HW | 81.67% | 81.67% |

Largest difference in a prediction (k = 1 against test_a_preds_c.parquet): W 2.78e-17, H 1.11e-16, HW 2.78e-17, persistence 0.00e+00; rows on one side only: 0; largest target difference 0.00e+00. Reproduced: yes.

### Table 8. Rows, months and base rates per horizon

| Horizon k | Rows scored | Origin months | Books | Rose (rows) | Surged (rows) | Training rows by test year |
|---|---|---|---|---|---|---|
| 1 | 556,735 | 78 | 7,747 | 11.3% | 2.8% | 2019: 187,605, 2020: 263,325, 2021: 296,295, 2022: 379,008, 2023: 464,943, 2024: 553,387, 2025: 613,396, 2026: 689,307 |
| 3 | 498,278 | 70 | 7,745 | 9.2% | 2.3% | 2019: 175,311, 2020: 250,409, 2021: 269,795, 2022: 351,928, 2023: 437,409, 2024: 525,451, 2025: 570,353, 2026: 630,883 |
| 6 | 410,815 | 58 | 7,736 | 9.7% | 2.6% | 2019: 157,116, 2020: 231,305, 2021: 250,409, 2022: 311,693, 2023: 396,417, 2024: 483,830, 2025: 513,521, 2026: 558,748 |
| 12 | 237,316 | 34 | 7,362 | 11.1% | 3.1% | 2019: 121,445, 2020: 193,766, 2021: 212,416, 2022: 232,664, 2023: 315,670 |
