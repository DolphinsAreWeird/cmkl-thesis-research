# Test E (LibriVox) rerun with correction A1

Khant Phyo Wai, 01323050. Written 2026-10-20 22:09 by `code/main_study/wiki_led/63c_test_e_corrected_report.py` from stored files only; it fits no model of the data (section 8 uses one small example on random numbers). Original run: `50_test_e_data.py` and `62_test_e_models.py` (result file of 2026-10-20 18:04). Corrected run: `50c_test_e_data.py` (rows of 2026-10-20 21:54; 14 s, peak 725 MB) and `62c_test_e_models.py` (result file of 2026-10-20 21:56; 104 s, peak 705 MB), both started with `jobs/bg.sh wl_test_e_c` and run under `nice`. The reason and the plan were written into `prereg/DEVIATIONS.md` (section "Wikipedia-led tests", entry of 20 Oct 2026 21:45 +07) before anything was computed. The original files are untouched; every new file has the suffix `_c`.

## Short answer

No conclusion about Test E changes. Wikipedia alone is still close to chance on LibriVox, it still adds nothing to listening history, and the 90% target is still missed in all eight lines (the closest is 80.2%). Listening history alone (E1 H, E2 H) and the persistence rule do not move at all, as they should not. The largest change is in the Seattle model with Wikipedia only (E2 W): change rank 0.0165 to -0.0030, surge ratio 1.213 to 0.975, so it is now at chance rather than just above it (section 8 explains why E2 moves more than E1). The retrained Wikipedia-only list (E1 W) loses 1.5 points in its top 20 (8.8% to 7.3%), which leaves it at the base rate of all books (7.0%).

The Test E table of the results draft, original and corrected (main rows; change rank, and share of each month's top 20 that rose):

| Model (original / corrected) | Retrained: rank | Retrained: top 20 | Seattle unchanged: rank | Seattle unchanged: top 20 |
| --- | ---: | ---: | ---: | ---: |
| Wikipedia only | 0.028 / 0.026 | 8.8% / 7.3% | 0.016 / -0.003 | 11.7% / 10.5% |
| Listening history | 0.349 / 0.349 | 80.4% / 80.4% | 0.278 / 0.278 | 68.9% / 68.9% |
| History + Wikipedia | 0.348 / 0.350 | 80.4% / 80.2% | 0.284 / 0.276 | 68.7% / 68.2% |
| Repeat last month (persistence) | 0.349 / 0.349 | 77.5% / 77.5% |  |  |

Other numbers of the draft's Test E paragraph: rows with stored Wikipedia views 20.5% of main rows (unchanged; 98.7% of them still have at least one feature after the correction, against 100.0%); the 90% target: 80.4% to 80.2%, and 68.8% to 66.9% in 2024 to 2026; with all months included 79.4% to 79.3% (retrained) and 69.6% to 69.2% (Seattle model). On the rows with stored views (the examiner review's figures): Wikipedia alone 0.055 to 0.052 (retrained) and 0.053 to 0.045 (Seattle model), history 0.364 (unchanged), history + Wikipedia 0.356 to 0.359.

## 1. What was corrected

- **The correction (A1 of addendum e).** A Wikipedia article that did not exist yet was stored as an article with zero views, so its first weeks looked like a huge rise and a tree model could tell "this page will exist later" from "no page". In the corrected run the weeks before an article's first week with at least one view are missing: they are removed before any rolling computation, with the same code as the corrected Test A (`10c_test_a.py`). Addendum e named Tests A, C, D and the placebo; Test E was left out, so its LibriVox rows still had the zeros, and so did the Seattle rows its E2 models are trained on.
- **How much of Test E it touches.** Of the 688 book articles with a stored weekly series, 92 have their first view after the first week of their series (3 of 168 Study 2R series, which start on 2015-06-29, and 89 of 520 series built from the raw daily file, which start in the week of 2016-06-27); all 139 author articles have their first view in the first week, so no author feature changes. 3,170 of 626,087 rows (0.5%) have a different Wikipedia value; among the main scored rows 2,170 of 433,424 (0.5%), from 71 books. Main rows with a book-page feature: 10.3% before, 9.9% after; with any Wikipedia feature: 20.5% before, 20.2% after.
- **E2's training rows.** E2 applies the Seattle Test A models, so it is now trained on the corrected Test A rows (`test_a_rows_c.parquet`): the same 750,501 rows in the same order with the same target and history columns (0 differing values), of which 91,347 (12.2%) have new Wikipedia values. This choice was fixed in `prereg/DEVIATIONS.md` before the run.
- **Unchanged:** rows, outcomes, excluded months, the 2018 break rule, the automated-traffic filter, models, settings, seeds and the scoring code.

## 2. Checks: same rows, same models, and identical features where nothing should change

- **The feature function.** The copy of the corrected function in `50c_test_e_data.py` gives exactly the corrected Test A features (`test_a_wiki_features_c.parquet`) on the 168 book and 139 author articles the two tests share (20,829 and 17,375 origin-month rows): largest difference 0, no difference in which values are missing or in which origin months have features.
- **The original code first.** The original `article_features`, read from `50_test_e_data.py` itself and run again on today's inputs, reproduces the stored original features (`test_e_wiki_features.parquet`) exactly for all three sources. So the inputs have not changed since the original run and every difference below comes from A1.
- **Articles whose first view is in the first week of their series: identical.** For them the correction removes nothing, and the corrected features equal the original ones exactly: the same origin months, the same values, missing equal to missing, no tolerance.

| source | first week of the series | articles | first view in that week | their origin-month rows | of these differing or missing in one file | first view later | their rows, original / corrected | rows differing beyond rounding | last differing row, weeks after first view (median / max) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book articles, Study 2R series | 2015-06-29 | 168 | 165 | 20,625 | 0 | 3 | 375 / 204 | 22 | 31 / 31 |
| book articles, raw daily file | 2016-06-27 | 520 | 431 | 52,151 | 0 | 89 | 10,769 / 5,563 | 617 | 29 / 34 |
| author articles, Study 2R series | 2015-06-29 | 139 | 139 | 17,375 | 0 | 0 | - | - | - |

  For the articles whose first view is later, the origin months that end before the article has a complete week of views lose all nine features (5,377 origin-month rows), and the first months after the first view differ because the original compared the new page with weeks of zeros. The last origin month that differs is at most 34 weeks after the first view; after that the two agree (differences below 1e-9 are rounding: 359 rows). The corrected file has no origin month that the original lacks.
- **Rows.** The corrected rows file has the same 626,087 rows in the same order; the 26 columns other than the 18 Wikipedia features are identical (0 differing values). The links table, the months table and the list of articles still needed, recomputed by `50c`, equal the stored originals (test_e_months.csv, test_e_links.parquet, test_e_articles_needed.csv), so they were not written again.
- **Models without Wikipedia.** E1 H and the persistence rule give exactly the original predictions; E2 H differs on 1 of 533,117 rows, by at most 7e-18 (thread order inside LightGBM). Their headline numbers are identical to every digit. The models with Wikipedia are refitted on changed features, so all their predictions shift a little (largest change of a single prediction: E1 W 0.62, E2 W 0.63, on the scale of D).
- **The result files come from these predictions.** Every headline number of `wiki_led_test_e.json` and `wiki_led_test_e_c.json` was recomputed here from the stored predictions with the scoring code of `62_test_e_models.py`: largest difference 0 and 0. The figures on the rows with stored views (section 6) reproduce `wiki_led_summary_checks.json` exactly (largest difference 0).
- **Side check (does not touch the rows).** For the 84 book articles stored in both sources, the raw daily series and the Study 2R series still give the same features on the 75 articles without redirects (largest difference 1.8e-15). With A1, 10 cells now differ in being missing, all in articles whose Study 2R series also counts the views of redirects (0 in articles without redirects), where the two series can have different first weeks with views. Test E uses the Study 2R series for these articles.

## 3. Headline numbers, original and corrected

Main rows: 433,424 book-months without automated-traffic months, 2019 to 2026; 7.04% of them rose at least 50% above the 6-month median (5.52% among books that had not yet risen, the base of the early-warning list). All rows (the check): 533,117 book-months; 10.06% rose (8.14% among books not yet risen). The same rows in both runs. Difference = corrected minus original.

### Change rank (Spearman of predicted and actual next-month change, per month, averaged)

| model | main: original | main: corrected | difference | all rows: original | all rows: corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.0278 | 0.0263 | -0.0016 | 0.0281 | 0.0264 | -0.0016 |
| E1 H: history only, retrained | 0.3492 | 0.3492 | +0.0000 | 0.3447 | 0.3447 | +0.0000 |
| E1 HW: history + Wikipedia, retrained | 0.3485 | 0.3501 | +0.0016 | 0.3445 | 0.3456 | +0.0011 |
| E2 W: Wikipedia only, Seattle model | 0.0165 | -0.0030 | -0.0195 | 0.0192 | 0.0022 | -0.0170 |
| E2 H: history only, Seattle model | 0.2779 | 0.2779 | +0.0000 | 0.2795 | 0.2795 | +0.0000 |
| E2 HW: history + Wikipedia, Seattle model | 0.2840 | 0.2758 | -0.0081 | 0.2873 | 0.2772 | -0.0101 |
| naive: repeat last month (persistence rule) | 0.3492 | 0.3492 | +0.0000 | 0.3402 | 0.3402 | +0.0000 |

### Surge average precision, as a ratio to the base rate

| model | main: original | main: corrected | difference | all rows: original | all rows: corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.964 | 0.959 | -0.006 | 1.047 | 1.045 | -0.002 |
| E1 H: history only, retrained | 7.943 | 7.943 | +0.000 | 4.139 | 4.139 | +0.000 |
| E1 HW: history + Wikipedia, retrained | 7.853 | 7.888 | +0.034 | 4.149 | 4.163 | +0.014 |
| E2 W: Wikipedia only, Seattle model | 1.213 | 0.975 | -0.238 | 1.215 | 1.040 | -0.175 |
| E2 H: history only, Seattle model | 7.785 | 7.785 | +0.000 | 3.733 | 3.733 | +0.000 |
| E2 HW: history + Wikipedia, Seattle model | 7.709 | 7.485 | -0.224 | 3.801 | 3.612 | -0.189 |
| naive: repeat last month (persistence rule) | 8.946 | 8.946 | +0.000 | 4.045 | 4.045 | +0.000 |

### Top-20 hit rate (share of each month's top 20 that rose at least 50% above the 6-month median)

| model | main: original | main: corrected | difference | all rows: original | all rows: corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.0879 | 0.0727 | -0.0152 | 0.0968 | 0.0892 | -0.0076 |
| E1 H: history only, retrained | 0.8038 | 0.8038 | +0.0000 | 0.7943 | 0.7943 | +0.0000 |
| E1 HW: history + Wikipedia, retrained | 0.8038 | 0.8015 | -0.0023 | 0.7943 | 0.7930 | -0.0013 |
| E2 W: Wikipedia only, Seattle model | 0.1167 | 0.1053 | -0.0114 | 0.1266 | 0.1234 | -0.0032 |
| E2 H: history only, Seattle model | 0.6894 | 0.6894 | +0.0000 | 0.6930 | 0.6930 | +0.0000 |
| E2 HW: history + Wikipedia, Seattle model | 0.6871 | 0.6818 | -0.0053 | 0.6962 | 0.6918 | -0.0044 |
| naive: repeat last month (persistence rule) | 0.7750 | 0.7750 | +0.0000 | 0.7696 | 0.7696 | +0.0000 |

### Top-50 hit rate

| model | main: original | main: corrected | difference | all rows: original | all rows: corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.0748 | 0.0697 | -0.0052 | 0.0873 | 0.0878 | +0.0005 |
| E1 H: history only, retrained | 0.6294 | 0.6294 | +0.0000 | 0.6390 | 0.6390 | +0.0000 |
| E1 HW: history + Wikipedia, retrained | 0.6291 | 0.6282 | -0.0009 | 0.6365 | 0.6352 | -0.0013 |
| E2 W: Wikipedia only, Seattle model | 0.0876 | 0.0921 | +0.0045 | 0.1008 | 0.1063 | +0.0056 |
| E2 H: history only, Seattle model | 0.5564 | 0.5564 | +0.0000 | 0.5790 | 0.5790 | +0.0000 |
| E2 HW: history + Wikipedia, Seattle model | 0.5458 | 0.5485 | +0.0027 | 0.5701 | 0.5709 | +0.0008 |
| naive: repeat last month (persistence rule) | 0.6124 | 0.6124 | +0.0000 | 0.6263 | 0.6263 | +0.0000 |

### Early warning: top-20 hit rate among books that had not yet risen

| model | main: original | main: corrected | difference | all rows: original | all rows: corrected | difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.0530 | 0.0439 | -0.0091 | 0.0639 | 0.0608 | -0.0032 |
| E1 H: history only, retrained | 0.3318 | 0.3318 | +0.0000 | 0.3722 | 0.3722 | +0.0000 |
| E1 HW: history + Wikipedia, retrained | 0.3333 | 0.3235 | -0.0098 | 0.3715 | 0.3627 | -0.0089 |
| E2 W: Wikipedia only, Seattle model | 0.0652 | 0.0682 | +0.0030 | 0.0804 | 0.0880 | +0.0076 |
| E2 H: history only, Seattle model | 0.2455 | 0.2455 | +0.0000 | 0.2443 | 0.2443 | +0.0000 |
| E2 HW: history + Wikipedia, Seattle model | 0.2341 | 0.2258 | -0.0083 | 0.2367 | 0.2241 | -0.0127 |
| naive: repeat last month (persistence rule) | 0.1811 | 0.1811 | +0.0000 | 0.2133 | 0.2133 | +0.0000 |

## 4. The 90% lines: is the top-20 hit rate of history + Wikipedia at least 0.90?

| rows | model | period | list slots | original | exact 95% interval | at least 0.90 | corrected | exact 95% interval | at least 0.90 | difference | answer changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | E1 HW | 2019-2026 | 1,320 | 0.8038 | [0.7813, 0.8249] | no | 0.8015 | [0.7790, 0.8227] | no | -0.0023 | no |
| main | E1 HW | 2024-2026 | 320 | 0.6875 | [0.6336, 0.7379] | no | 0.6687 | [0.6142, 0.7201] | no | -0.0188 | no |
| main | E2 HW | 2019-2026 | 1,320 | 0.6871 | [0.6613, 0.7121] | no | 0.6818 | [0.6559, 0.7069] | no | -0.0053 | no |
| main | E2 HW | 2024-2026 | 320 | 0.6469 | [0.5918, 0.6992] | no | 0.6375 | [0.5822, 0.6902] | no | -0.0094 | no |
| all | E1 HW | 2019-2026 | 1,580 | 0.7943 | [0.7735, 0.8140] | no | 0.7930 | [0.7722, 0.8128] | no | -0.0013 | no |
| all | E1 HW | 2024-2026 | 540 | 0.7019 | [0.6613, 0.7402] | no | 0.6926 | [0.6518, 0.7313] | no | -0.0093 | no |
| all | E2 HW | 2019-2026 | 1,580 | 0.6962 | [0.6729, 0.7188] | no | 0.6918 | [0.6683, 0.7145] | no | -0.0044 | no |
| all | E2 HW | 2024-2026 | 540 | 0.6741 | [0.6327, 0.7135] | no | 0.6722 | [0.6308, 0.7117] | no | -0.0019 | no |

The answer is no in all eight lines in both runs, and no interval reaches 0.90. The largest move is the retrained model in 2024 to 2026, 0.6875 to 0.6687: 220 and 214 of 320 list slots. Ties do not affect these lists (lowest and highest value over all orders of tied scores equal the stored value in every line).

## 5. Ties at the cut-off of the top-k lists (main rows)

`62_test_e_models.py` takes each month's top k with an unstable sort, so books with exactly the same score at the cut-off enter in an order that depends on the data. The Wikipedia-only models give many books the same score (every book without a Wikipedia feature gets one value), so their stored top-k rates can move without any real change. The table gives the stored value, the value expected when tied books are taken in random order, and the lowest and highest value over all orders of the tied scores (code of `15_summary_checks.py`). The history models (H) and the persistence rule are not listed: their predictions did not change.

| model | list | original: stored | original: random tie order | original: range over tie orders | corrected: stored | corrected: random tie order | corrected: range over tie orders | difference (random tie order) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 W | top 20 | 0.0879 | 0.0875 | 0.0826 to 0.0970 | 0.0727 | 0.0720 | 0.0674 to 0.0811 | -0.0155 |
| E1 W | top 50 | 0.0748 | 0.0752 | 0.0679 to 0.0827 | 0.0697 | 0.0700 | 0.0639 to 0.0761 | -0.0051 |
| E1 W | early warning, top 20 | 0.0530 | 0.0544 | 0.0508 to 0.0614 | 0.0439 | 0.0447 | 0.0417 to 0.0508 | -0.0097 |
| E1 HW | top 20 | 0.8038 | 0.8038 | 0.8038 to 0.8038 | 0.8015 | 0.8015 | 0.8015 to 0.8015 | -0.0023 |
| E1 HW | top 50 | 0.6291 | 0.6291 | 0.6291 to 0.6291 | 0.6282 | 0.6282 | 0.6282 to 0.6282 | -0.0009 |
| E1 HW | early warning, top 20 | 0.3333 | 0.3333 | 0.3333 to 0.3333 | 0.3235 | 0.3239 | 0.3235 to 0.3242 | -0.0095 |
| E2 W | top 20 | 0.1167 | 0.1118 | 0.0939 to 0.1303 | 0.1053 | 0.1071 | 0.0879 to 0.1280 | -0.0047 |
| E2 W | top 50 | 0.0876 | 0.0866 | 0.0812 to 0.1109 | 0.0921 | 0.0916 | 0.0876 to 0.0985 | +0.0050 |
| E2 W | early warning, top 20 | 0.0652 | 0.0646 | 0.0561 to 0.0765 | 0.0682 | 0.0687 | 0.0561 to 0.0811 | +0.0041 |
| E2 HW | top 20 | 0.6871 | 0.6871 | 0.6871 to 0.6871 | 0.6818 | 0.6818 | 0.6818 to 0.6818 | -0.0053 |
| E2 HW | top 50 | 0.5458 | 0.5457 | 0.5445 to 0.5464 | 0.5485 | 0.5483 | 0.5479 to 0.5488 | +0.0027 |
| E2 HW | early warning, top 20 | 0.2341 | 0.2375 | 0.2182 to 0.2697 | 0.2258 | 0.2186 | 0.1879 to 0.2500 | -0.0189 |

Reading: the drop of E1 W's top 20 is larger than anything tie order can do: its range was 8.26% to 9.70% and is now 6.74% to 8.11%, which contains the base rate (7.04%). The moves of E2 W lie inside its tie ranges (9.39% to 13.03% before, 8.79% to 12.80% after), so they say nothing. E2 HW's early-warning list also has ties at the cut-off in 54 of 66 months, and its move (-0.0189) lies inside its tie ranges. The other HW lists have almost no ties, so their small moves come from the refitted models, not from tie order.

## 6. Rows with stored Wikipedia views

The examiner review restated the Test E result on the main rows whose book or author article has a stored weekly series: 88,752 rows, 20.5% of the main rows, the same set in both runs (5.85% of them rose). After the correction 98.7% of them still have at least one Wikipedia feature (100.0% before) and 48.3% a book-page feature (50.1% before); 2,170 of them changed. Change rank and top-20 hit rate as in `15_summary_checks.py` (Spearman within month for months with more than 20 rows, averaged; ties in the top 20 broken by book_id, with the range over all tie orders for the Wikipedia-only models).

| model | change rank: original | corrected | difference | top 20 that rose: original / corrected (range over tie orders) |
| --- | ---: | ---: | ---: | ---: |
| E1 W: Wikipedia only, retrained | 0.0554 | 0.0525 | -0.0029 | 0.0886 / 0.0720 (0.0826 to 0.0970 / 0.0674 to 0.0811) |
| E1 H: history only, retrained | 0.3644 | 0.3644 | +0.0000 | 0.5295 / 0.5295 |
| E1 HW: history + Wikipedia, retrained | 0.3556 | 0.3591 | +0.0035 | 0.5439 / 0.5379 |
| E2 W: Wikipedia only, Seattle model | 0.0529 | 0.0447 | -0.0082 | 0.1106 / 0.1045 (0.0947 to 0.1280 / 0.0879 to 0.1280) |
| E2 H: history only, Seattle model | 0.2522 | 0.2522 | +0.0000 | 0.4295 / 0.4295 |
| E2 HW: history + Wikipedia, Seattle model | 0.2670 | 0.2620 | -0.0050 | 0.4356 / 0.4348 |
| naive: repeat last month (persistence rule) | 0.3733 | 0.3733 | +0.0000 | 0.5235 / 0.5235 |

The restated claim ("there it ranks weakly and adds nothing to listening history") holds: Wikipedia alone 0.052 retrained and 0.045 with the Seattle model (was 0.055 and 0.053); history + Wikipedia 0.359 against 0.364 for history alone (was 0.356).

## 7. Does any conclusion change?

Test E has no intervals for its change ranks, so its readings are point readings. The table lists 36 of them: the yes-or-no lines of the 90% question, and the signs behind the statements in the results draft and the examiner review. 7 change.

| reading | original | corrected | value, original | value, corrected | changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1 W change rank above 0 | yes | yes | 0.0278 | 0.0263 | no |
| E1 W surge ratio above 1 | no | no | 0.964 | 0.959 | no |
| E1 W top-20 hit rate above the base rate (7.04%) | yes | yes | 8.79% | 7.27% | no |
| E1 HW minus H, change rank, above 0 | no | yes | -0.0007 | +0.0009 | YES |
| E1 HW top 20 not below H by 0.5 points or more (tie rule of addendum c) | yes | yes | +0.00 points | -0.23 points | no |
| E2 W change rank above 0 | yes | no | 0.0165 | -0.0030 | YES |
| E2 W surge ratio above 1 | yes | no | 1.213 | 0.975 | YES |
| E2 W top-20 hit rate above the base rate (7.04%) | yes | yes | 11.67% | 10.53% | no |
| E2 HW minus H, change rank, above 0 | yes | no | +0.0060 | -0.0021 | YES |
| E2 HW top 20 not below H by 0.5 points or more (tie rule of addendum c) | yes | no | -0.23 points | -0.76 points | YES |
| E2 H change rank below E1 H (the Seattle model transfers worse) | yes | yes | 0.2779 vs 0.3492 | 0.2779 vs 0.3492 | no |
| E2 HW change rank below E1 HW (the Seattle model transfers worse) | yes | yes | 0.2840 vs 0.3485 | 0.2758 vs 0.3501 | no |
| E1 W change rank above 0 (all rows) | yes | yes | 0.0281 | 0.0264 | no |
| E1 W surge ratio above 1 (all rows) | yes | yes | 1.047 | 1.045 | no |
| E1 W top-20 hit rate above the base rate (10.06%) (all rows) | no | no | 9.68% | 8.92% | no |
| E1 HW minus H, change rank, above 0 (all rows) | no | yes | -0.0002 | +0.0009 | YES |
| E1 HW top 20 not below H by 0.5 points or more (tie rule of addendum c) (all rows) | yes | yes | +0.00 points | -0.13 points | no |
| E2 W change rank above 0 (all rows) | yes | yes | 0.0192 | 0.0022 | no |
| E2 W surge ratio above 1 (all rows) | yes | yes | 1.215 | 1.040 | no |
| E2 W top-20 hit rate above the base rate (10.06%) (all rows) | yes | yes | 12.66% | 12.34% | no |
| E2 HW minus H, change rank, above 0 (all rows) | yes | no | +0.0078 | -0.0023 | YES |
| E2 HW top 20 not below H by 0.5 points or more (tie rule of addendum c) (all rows) | yes | yes | +0.32 points | -0.13 points | no |
| E2 H change rank below E1 H (the Seattle model transfers worse) (all rows) | yes | yes | 0.2795 vs 0.3447 | 0.2795 vs 0.3447 | no |
| E2 HW change rank below E1 HW (the Seattle model transfers worse) (all rows) | yes | yes | 0.2873 vs 0.3445 | 0.2772 vs 0.3456 | no |
| 90% line: E1 HW top 20 at least 0.90, 2019-2026, main rows | no | no | 0.8038 | 0.8015 | no |
| 90% line: E1 HW top 20 at least 0.90, 2024-2026, main rows | no | no | 0.6875 | 0.6687 | no |
| 90% line: E2 HW top 20 at least 0.90, 2019-2026, main rows | no | no | 0.6871 | 0.6818 | no |
| 90% line: E2 HW top 20 at least 0.90, 2024-2026, main rows | no | no | 0.6469 | 0.6375 | no |
| 90% line: E1 HW top 20 at least 0.90, 2019-2026, all rows | no | no | 0.7943 | 0.7930 | no |
| 90% line: E1 HW top 20 at least 0.90, 2024-2026, all rows | no | no | 0.7019 | 0.6926 | no |
| 90% line: E2 HW top 20 at least 0.90, 2019-2026, all rows | no | no | 0.6962 | 0.6918 | no |
| 90% line: E2 HW top 20 at least 0.90, 2024-2026, all rows | no | no | 0.6741 | 0.6722 | no |
| rows with stored views: E1 W change rank above 0 | yes | yes | 0.0554 | 0.0525 | no |
| rows with stored views: E1 HW minus H, change rank, above 0 | no | no | -0.0088 | -0.0053 | no |
| rows with stored views: E2 W change rank above 0 | yes | yes | 0.0529 | 0.0447 | no |
| rows with stored views: E2 HW minus H, change rank, above 0 | yes | yes | +0.0148 | +0.0097 | no |

**What the changes mean.** No statement in the results draft or the examiner review changes; only some of their numbers do.

- "Wikipedia alone is close to chance" holds, more firmly than before: change rank 0.0263 retrained (was 0.0278) and -0.0030 with the Seattle model (was 0.0165); surge ratio 0.959 and 0.975 (was 0.964 and 1.213); the retrained top 20 rose 7.3% of the time against 7.0% for all books (was 8.8%). Two of the flipped readings belong here: E2 W's change rank is no longer above 0 and its surge ratio no longer above 1. That is a move from just above chance to chance, not a change of conclusion.
- "It adds nothing to listening history" holds. HW minus H in change rank is +0.0009 retrained (was -0.0007) and -0.0021 with the Seattle model (was +0.0060); the top 20 of HW rose 80.2% against 80.4% for H retrained, and 68.2% against 68.9% with the Seattle model. Five of the flipped readings are about these differences: their signs in both row sets, and the 0.5-point tie rule for E2's top 20 (-0.76 points, was -0.23). For E1 the differences are the size of refit noise: in Test A, changing only the seed of the trees moved HW minus H by up to 0.0006 in change rank and by up to 1.0 points in the top-20 rate (5 seeds, check R2 of `wiki_led_robustness.md`), so the sign carries no weight before or after. For E2 the original gain (+0.0060) was larger than that noise, and it is gone after the correction (section 8 gives a likely reason). That makes "adds nothing" firmer, not weaker.
- "The 90% target is not met" holds in all eight lines (section 4).
- "The Seattle model transfers worse than the retrained one" holds: E2 is below E1 for H and for HW in both row sets.
- On the rows with stored views, "a weak signal that adds nothing to listening history" holds (section 6).

## 8. Why E2 moves more than E1

E1 sees one change: 2,170 of its 433,424 main rows have new Wikipedia values. E2 sees a second one: its Seattle training rows are the corrected Test A rows, 12.2% of which have new values. The second change also alters how E2 reads LibriVox books that have no book page, which is 90.1% of the main rows.

- In the original Seattle rows a book-page feature was never missing (0.0% of the training rows for 2019 and for 2026): every Test A work has its own article, and the stored zeros filled the time before the article existed.
- When a feature had no missing value in training, LightGBM reads a missing value as 0. Checked here with the installed LightGBM 4.6.0 on 50 trees fitted to random numbers: the prediction for a missing value equals the prediction for 0 (0.9818 and 0.9818).
- For the book-page level (lvl4, the log of the page's share of all Wikipedia views; median -15.6 in the original Seattle rows, 99th percentile -11.5, highest -7.5), 0 means a page with all of Wikipedia's views; the other eight book-page features were read as 0 too. So in the original run the Seattle models scored the 89.7% of LibriVox main rows without a book page as if that page had a larger share of views than any real page.
- In the corrected Seattle rows 8.6% of the training rows for 2026 (12.1% for 2019) have no book-page feature yet, so the models have learned a branch for "no page", and LibriVox books without a page now follow it.

This run does not separate the two changes. E1, which has only the first, moves its Wikipedia-only change rank by -0.0016; E2 moves by -0.0195. So part of the original E2 numbers with Wikipedia may have come from how the model filled in a missing page it had never seen in training; in the corrected run it has seen such pages.

## 9. Files and choices

- New code (in `code/main_study/wiki_led/`): `50c_test_e_data.py` and `62c_test_e_models.py` (copies of `50` and `62` with only the changes listed in their headers), and this report script `63c_test_e_corrected_report.py`.
- New data: `data/db/wiki_led/test_e_rows_c.parquet`, `test_e_wiki_features_c.parquet`, `test_e_build_info_c.json` (all checks of `50c`), `test_e_preds_c.parquet`; results `data/reports/wiki_led_test_e_c.json`; this report and `wiki_led_test_e_corrected.json`; log `data/reports/wl_test_e_c.log`.
- Choices made while coding, none changed after a result: (1) `b_src` and `a_src` (which stored series an article has) are read from the stored series, not from the feature table, so that a page with a stored series but no corrected feature keeps its source; the values equal the original ones. (2) E2 trains on the corrected Seattle rows (fixed in `DEVIATIONS.md` before the run). (3) `62c` reads only the columns the models use from the Seattle file, to keep memory low; rows and order are unchanged. (4) The unchanged links, months and needed-articles tables are compared with the stored ones instead of being written again.
- How it was run: `50c` was started three times. The first run stopped in its own row check (a text-column comparison that failed under pandas 3; fixed in the check, not in the build); the third added one count to the side check of section 2 (the missing-value cells by redirects). The code that builds the features and rows did not change between the runs. `62c` ran once.
- Added after the corrected results were seen (logged in `prereg/DEVIATIONS.md`; descriptive, nothing chosen from them): the missing-feature shares of E2's training rows and the LightGBM example (section 8), the table of point readings (section 7), and the base rates of the early-warning list.

