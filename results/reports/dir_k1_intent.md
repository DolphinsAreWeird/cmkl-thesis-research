# K1: does reading intent on Open Library add to the alert list?

Khant Phyo Wai, 01323050. Run 2026-10-22 12:03 +0700.

**In plain words**

1. Open Library's public reading-log dump records the month in which someone put a book on a Want to Read, Currently Reading or Already Read shelf; 7,483 of the 7,747 study books (96.6%) have at least one entry between October 2017 (the first dated entry) and September 2026. Use of the site grew a lot and unevenly: 551,426 entries in 2018, 1,138,129 in 2020, 709,453 in 2021 and 2,564,120 in 2023.
2. Among books whose Seattle borrowing had not yet started to climb, the alert list from library history, the book's own Wikipedia pages and NYT lists (H+W+N) had 38.7% surging books in its monthly top 20 (base rate 1.7%); with reading intent added it had 38.7%, a difference of +0.0 points (interval -1.2 to +1.3).
3. The same model with every intent date moved 12 months earlier scored 38.5%; the real dates beat it by +0.2 points (interval -0.7 to +1.1). By the rule fixed in advance (both intervals above 0), reading intent does not add to the alert list.
4. Intent does carry some signal on its own: books whose Want to Read entries reached 3 times their usual level surged next month in 5.2% of cases (base 2.8%; at 2 times, 3.5%; the moved-date version at 2 times, 2.8%), but library history, Wikipedia and NYT lists already hold that information: intent gets 1.7% of the model's split gain, and over three months the difference is +0.7 points (-0.6 to +2.2).
5. For next month's NYT list appearance (D3), adding intent to library history and Wikipedia moves the AUC from 0.877 to 0.888 (difference +0.011, interval -0.002 to +0.023), and the moved-date version does the same (0.888), so this small gain does not depend on the month of the entries (the moved version keeps how much interest a book has on Open Library in general). Limit: the dump keeps only entries that still exist in September 2026, dated by their current shelf.

**Examples** (books the intent model listed and H+W+N did not, which then surged; picked by the rule fixed in advance, K14):

- **The Love Hypothesis** (Ali Hazelwood), list made at the end of 2021-09: rank 16 with intent, rank 25 without. Want to Read entries in the 7 months to 2021-09: 0, 0, 0, 0, 0, 0, 17 (this month 18.0 times the usual level); Seattle loans: usual level 57 a month, 57 in month t, 169 the next month (a new book in Seattle, first borrowed in 2021-09, so the usual level is its loans since then).
- **Flowers in the attic** (Andrews, V. C. (Virginia C.)), list made at the end of 2019-08: rank 14 with intent, rank 23 without. Want to Read entries in the 7 months to 2019-08: 5, 4, 4, 9, 6, 10, 20 (this month 3.2 times the usual level); Seattle loans: usual level 6 a month, 10 in month t, 14 the next month.

An example shows what the list contains; it does not prove why the model ranked the book high.

Addendum k (`prereg/addenda_wiki_led/2026-10-22_k_intent_dates_human.json`), section K1_intent; addendum j's settings otherwise. Choices the record leaves open: K1 to K14 in the header of `code/main_study/wiki_led/dirs/k1_intent.py` (written before any result). Every interval is a 95% interval (addendum j's month-block bootstrap). Tables: `data/db/wiki_led/dirs/k1_intent/`.

Terms (as addendum j). **Usual level** (M6): median monthly loans over the six months to t. **Surge**: next month's loans at least 2 times the usual level and at least 5 more. **Not yet risen**: loans in month t below 1.5 times the usual level. **Precision at 20**: the share of a month's top 20 that surge. **I** (intent): entries dated in month t by shelf and in total, Want to Read entries in t against the median of the 6 months before (1 added to both), and entries in t-2 to t.

## 1. The data

Dump: `data/raw/openlibrary_dump/ol_dump_reading-log_2026-09-30.txt.gz` (122,565,618 bytes, SHA-256 `b2c4be8ddcf1327b...`, the same file as the copy of 14 Oct: yes); 12,961,546 lines, 0 malformed; entries dated 2017-10 to 2026-09; 3,333,411 distinct works. Shelves: Want to Read 10,655,319, Currently Reading 612,675, Already Read 1,691,633, Stopped Reading 1,919 (not used, K2). Entries dated before 2017-01: 0; after 2026-09: 0.

Mapping (D4 collector, quality high or medium): 7,728 of the 7,747 works, 7,481 distinct Open Library works; 7,483 works (96.8% of the mapped) have at least one entry. Entries per mapped work over the whole period: median 53, 90th percentile 450, 99th percentile 3279.

Check of the dump against the live counts (weekly collector, _partial_2026-10-22.csv, 758 works fetched so far): Spearman correlation of Want to Read totals 0.997; the dump total is at most the live count for 99.5% of works (median ratio 1.00). Entries added after September and entries under older merged keys explain gaps.

Activity by year. Open Library's user base and reading-log use changed a lot over these years (the shelves were new in 2017 and use rose in steps after); the counts are raw, as the record fixes them, so the relative input (this month against the 6 months before) is the one least affected:

| Year | Entries, whole dump (3 shelves) | Want to Read, whole dump | Works with an entry, whole dump | Entries, study books | Study books with an entry |
| --- | --- | --- | --- | --- | --- |
| 2017 | 5,638 | 4,429 | 5,435 | 478 | 390 |
| 2018 | 551,426 | 468,487 | 279,405 | 43,033 | 3,916 |
| 2019 | 681,812 | 563,434 | 326,522 | 72,289 | 4,644 |
| 2020 | 1,138,129 | 932,431 | 467,780 | 195,325 | 5,938 |
| 2021 | 709,453 | 539,128 | 374,843 | 111,177 | 6,012 |
| 2022 | 1,800,790 | 1,549,895 | 842,785 | 322,984 | 6,554 |
| 2023 | 2,564,120 | 2,215,518 | 1,084,318 | 464,460 | 6,712 |
| 2024 | 1,678,982 | 1,441,315 | 768,939 | 303,637 | 6,451 |
| 2025 | 2,337,131 | 2,024,856 | 968,174 | 416,182 | 6,745 |
| 2026 (to Sep) | 1,492,146 | 915,826 | 894,562 | 196,585 | 6,534 |

In the scored rows (origins 2019-01 to 2026-07, 556,735 book-months) a book has at least one entry in month t in 45.1% of rows; I is missing in 814 rows (unmapped books) and the placebo I' in 77,118 (origins after 2025-09 or unmapped).

Next-month surge rate where an intent input is on (base 2.8% of all rows, 1.7% not yet risen; descriptive):

| Input (on) | Rows | Books | Surge rate where on | Same, not yet risen |
| --- | --- | --- | --- | --- |
| i_all > 0 | 250,955 | 7,450 | 2.6% | 1.4% |
| i_wtr > 0 | 220,007 | 7,358 | 2.6% | 1.4% |
| i_wtr_rel >= 2 | 81,764 | 7,350 | 3.5% | 1.8% |
| i_wtr_rel >= 3 | 16,791 | 5,549 | 5.2% | 2.3% |
| i_all_3m >= 10 | 80,268 | 3,057 | 2.4% | 1.2% |
| p_i_wtr_rel >= 2 (placebo) | 77,582 | 7,231 | 2.8% | 1.7% |
| p_i_all > 0 (placebo) | 232,647 | 7,382 | 2.6% | 1.5% |

## 2. Main result: next-month surges

**Books not yet risen at t (primary)**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history; addendum j) | 35.2% (31.3% to 39.0%) | 11.2% (10.2% to 12.3%) | 13.8% (12.6% to 15.1%) |
| H+W (+ own Wikipedia pages; addendum j) | 38.3% (33.7% to 43.0%) | 12.3% (11.2% to 13.5%) | 14.8% (13.6% to 16.0%) |
| H+W+E+N (addendum j, with the event calendar) | 39.8% (35.0% to 44.7%) | 12.6% (11.5% to 13.9%) | 15.0% (13.9% to 16.2%) |
| H+W+N (library, own Wikipedia pages, NYT lists) | 38.7% (33.8% to 43.5%) | 12.4% (11.3% to 13.6%) | 14.6% (13.4% to 15.9%) |
| H+W+N+I (+ reading intent) | 38.7% (33.7% to 43.7%) | 12.4% (11.2% to 13.6%) | 14.6% (13.5% to 15.8%) |
| Placebo H+W+N+I' (intent dates moved 12 months earlier) | 38.5% (33.6% to 43.3%) | 12.4% (11.2% to 13.6%) | 14.6% (13.4% to 15.9%) |

**All books**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history; addendum j) | 82.7% (79.5% to 85.6%) | 33.6% (31.7% to 35.5%) | 27.3% (25.7% to 28.8%) |
| H+W (+ own Wikipedia pages; addendum j) | 85.2% (82.9% to 87.5%) | 34.7% (32.8% to 36.5%) | 28.0% (26.4% to 29.5%) |
| H+W+E+N (addendum j, with the event calendar) | 85.7% (83.1% to 88.1%) | 35.0% (33.1% to 36.9%) | 28.2% (26.6% to 29.7%) |
| H+W+N (library, own Wikipedia pages, NYT lists) | 85.5% (83.1% to 88.0%) | 34.9% (33.0% to 36.7%) | 27.8% (26.2% to 29.3%) |
| H+W+N+I (+ reading intent) | 85.2% (82.6% to 87.6%) | 34.9% (32.9% to 36.8%) | 28.0% (26.3% to 29.5%) |
| Placebo H+W+N+I' (intent dates moved 12 months earlier) | 85.7% (83.3% to 87.9%) | 34.8% (32.8% to 36.6%) | 28.1% (26.4% to 29.5%) |

**Paired differences** (points, same months; interval):

| Comparison | Precision at 20, not yet risen | Precision at 20, all | Average precision, not yet risen | Coverage, not yet risen |
| --- | --- | --- | --- | --- |
| HWNI minus HWN | +0.0 (-1.2 to +1.3) | -0.3 (-1.1 to +0.4) | +0.0 (-0.1 to +0.1) | +0.1 (-0.2 to +0.4) |
| HWNI minus placebo_I | +0.2 (-0.7 to +1.1) | -0.5 (-1.3 to +0.4) | +0.1 (-0.1 to +0.2) | +0.0 (-0.3 to +0.4) |
| placebo_I minus HWN | -0.2 (-1.1 to +0.7) | +0.2 (-0.7 to +1.1) | -0.1 (-0.1 to +0.0) | +0.0 (-0.3 to +0.3) |
| HWN minus H | +3.5 (+1.0 to +6.1) | +2.8 (+1.1 to +4.7) | +1.2 (+0.8 to +1.7) | +0.8 (+0.3 to +1.3) |
| HWN minus HWEN | -1.2 (-2.1 to -0.3) | -0.2 (-1.0 to +0.6) | -0.2 (-0.4 to -0.1) | -0.4 (-0.8 to -0.1) |
| HWNI minus HWEN | -1.2 (-2.2 to -0.1) | -0.5 (-1.4 to +0.4) | -0.2 (-0.4 to -0.1) | -0.4 (-0.8 to -0.0) |

**Decision (fixed in advance).** H+W+N+I minus H+W+N: +0.0 (-1.2 to +1.3), not above 0; H+W+N+I minus the placebo: +0.2 (-0.7 to +1.1), not above 0. Both are needed, so by the rule fixed in advance reading intent does not clearly add to the alert list.
Check on the origins with complete placebo data (2025-09 and before, 68 months): H+W+N+I minus the placebo +0.2 (-0.7 to +1.2).
For context (not part of this test): H+W+N is -1.2 points (-2.1 to -0.3) against addendum j's H+W+E+N on the primary measure, the event calendar is not part of this test (addendum j's own E-only placebo comparison, H+W+E+N minus the same with E dates moved, was +1.2, +0.3 to +2.1).
Fit check: addendum j's H+W refitted with this script's copy of the fit gives j2's scores (largest difference 1.1e-19).

## 3. Surges within three months (models refitted on that target)

| Model | Precision at 20, not yet risen | Precision at 20, all |
| --- | --- | --- |
| H (library history; addendum j) | 52.0% (48.0% to 55.7%) | 85.7% (82.7% to 88.6%) |
| H+W (+ own Wikipedia pages; addendum j) | 52.6% (48.8% to 56.5%) | 88.1% (85.3% to 90.9%) |
| H+W+E+N (addendum j, with the event calendar) | 55.5% (51.9% to 59.4%) | 88.9% (86.2% to 91.5%) |
| H+W+N (library, own Wikipedia pages, NYT lists) | 53.0% (49.5% to 56.5%) | 88.6% (86.2% to 90.8%) |
| H+W+N+I (+ reading intent) | 53.7% (50.1% to 57.3%) | 88.8% (86.3% to 91.1%) |
| Placebo H+W+N+I' (intent dates moved 12 months earlier) | 53.9% (50.2% to 57.6%) | 88.2% (85.8% to 90.3%) |

| Comparison | Precision at 20, not yet risen | Precision at 20, all |
| --- | --- | --- |
| HWNI minus HWN | +0.7 (-0.6 to +2.2) | +0.2 (-0.5 to +1.0) |
| HWNI minus placebo_I | -0.2 (-1.6 to +1.2) | +0.6 (-0.5 to +1.6) |
| placebo_I minus HWN | +0.9 (-0.7 to +2.8) | -0.4 (-1.4 to +0.6) |

## 4. NYT list appearance next month (D3) with intent added

D3's rows (books not on a list in month t), target an NYT week in month t+1, D3's models and measures. Fit check: D3's H refitted here gives D3's scores (largest difference 0.0e+00). The placebo rows (I') are an extra check, not in the record.

**Books matched to NYT entries (D3 primary)** (194,692 rows, 78 months with an appearance, 1,283 appearances)

| Model | AUC (mean over months) | Top-20 share |
| --- | --- | --- |
| H (D3) | 0.856 (0.843 to 0.869) | 26.0% (22.6% to 29.5%) |
| H+W (D3) | 0.877 (0.862 to 0.892) | 30.4% (26.7% to 34.3%) |
| H+I | 0.856 (0.840 to 0.872) | 25.9% (22.2% to 29.7%) |
| H+W+I | 0.888 (0.874 to 0.901) | 29.9% (26.0% to 34.0%) |
| H+I' (placebo) | 0.855 (0.841 to 0.869) | 26.2% (22.2% to 30.2%) |
| H+W+I' (placebo) | 0.888 (0.876 to 0.899) | 29.3% (25.4% to 33.5%) |

| Comparison | AUC difference | Top-20 share difference (points) |
| --- | --- | --- |
| H+I minus H | -0.0006 (-0.0151 to +0.0130) | -0.1 (-1.0 to +0.8) |
| H+W+I minus H+W | +0.0110 (-0.0017 to +0.0231) | -0.4 (-1.5 to +0.6) |
| H+I minus H+I' | +0.0003 (-0.0121 to +0.0123) | -0.3 (-1.2 to +0.7) |
| H+W+I minus H+W+I' | +0.0001 (-0.0120 to +0.0119) | +0.6 (-0.3 to +1.6) |

**All 7,747 books** (549,923 rows, 78 months with an appearance, 1,283 appearances)

| Model | AUC (mean over months) | Top-20 share |
| --- | --- | --- |
| H (D3) | 0.885 (0.870 to 0.899) | 19.6% (17.0% to 22.3%) |
| H+W (D3) | 0.898 (0.884 to 0.912) | 24.7% (21.7% to 27.8%) |
| H+I | 0.895 (0.879 to 0.909) | 19.9% (17.4% to 22.4%) |
| H+W+I | 0.903 (0.890 to 0.915) | 25.1% (22.1% to 28.1%) |
| H+I' (placebo) | 0.884 (0.867 to 0.899) | 20.6% (17.8% to 23.4%) |
| H+W+I' (placebo) | 0.907 (0.894 to 0.919) | 24.8% (22.1% to 27.6%) |

| Comparison | AUC difference | Top-20 share difference (points) |
| --- | --- | --- |
| H+I minus H | +0.0095 (-0.0035 to +0.0211) | +0.3 (-0.7 to +1.3) |
| H+W+I minus H+W | +0.0049 (-0.0074 to +0.0182) | +0.4 (-0.6 to +1.3) |
| H+I minus H+I' | +0.0110 (-0.0027 to +0.0242) | -0.6 (-1.7 to +0.5) |
| H+W+I minus H+W+I' | -0.0044 (-0.0186 to +0.0099) | +0.3 (-0.8 to +1.3) |

## 5. What the intent model leans on

Share of the split gain by input group (H+W+N+I, next-month model, mean over the 8 test years): H 71.9%, W 25.7%, N 0.7%, I 1.7%. Intent inputs: `i_wtr` 0.2%, `i_cur` 0.0%, `i_read` 0.1%, `i_all` 0.2%, `i_wtr_rel` 0.8%, `i_all_3m` 0.4%.

Rows in the intent model's not-yet-risen top 20 that are not in H+W+N's: 258 over the 78 months, of which 39 surged.

## 6. Limits

- The dump holds only entries that still exist on 2026-09-30, dated by the entry's current shelf: entries later removed are missing and books moved between shelves are re-dated (for example from Want to Read to Already Read). Past months therefore look a little different from what could have been seen at the time (a mild look-ahead, as the record says).
- Open Library's activity grew several-fold and unevenly over these years (section 1); the counts are not adjusted for it. The walk-forward refits learn each year from earlier years, when the counts were smaller.
- Open Library users are a small, particular group of readers (often students and library users worldwide); the target is borrowing in one library (Seattle).
- Entries under older, merged Open Library keys of the same book are not counted (the dump has no redirect table); the live-count check above gives the size of the gap.
- Test A's models, not tuned.

## Files

`data/db/wiki_led/dirs/k1_intent/`: `parse_info.json`, `dump_month_totals.parquet` (whole dump by month and shelf), `ol_entries_mapped.parquet` (entries of the mapped works by month and shelf), `feats_i.parquet` (I and I' per book-month), `work_entries.parquet`, `preds_S1_*.parquet`, `preds_S3_*.parquet`, `d3_preds.parquet`, `measures.csv`, `paired_differences.csv`, `feature_on_surge_rates.csv`, `importance_*.json`, `check_reproduce_j2.json`, `check_reproduce_d3.json`, `k1_results.json`.
