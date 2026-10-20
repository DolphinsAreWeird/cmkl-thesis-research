# Summary checks for the Wikipedia-led results

Khant Phyo Wai, student ID 01323050. Written by `code/main_study/wiki_led/15_summary_checks.py` on 20 October 2026 at 21:46 (+07); all numbers are in `data/reports/wiki_led_summary_checks.json`.

## What this is

One saved script for the numbers that the results summary (`paper/Wikipedia_Led_Results_2026-10-20_1924.md`) and the examiner review (`data/reports/wiki_led_examiner_review.md`) quote without a script behind them: the "different books" figures, the August 2026 example, a new June to July 2026 example, the persistence rule in Tests A, D and E, Test B's one-column baselines and the split by earlier Seattle books, the author-cap check of `prereg/DEVIATIONS.md` (17:07), and every "(check)" number of the review's appendix. It reads stored predictions only, fits no model and was written after all results were seen, so it is descriptive and changes no decision. Corrected files (addendum e) are used where they exist: Test A and Test D. Tests B and E have no corrected files.

**Rules** (as in the review's appendix). A book "rose" when next month's loans are at least 1.5 times the median of the last 6 months (stored D at least ln 1.5). A month's top k are its k highest scores, ties broken by work_id (book_id in Test E). A hit rate is the mean of the monthly shares (Test D: of the format-month shares). Rank is Spearman within month, or within first-month year in Test B, averaged. For each top-k hit rate the JSON also holds the lowest and highest value over all orders of tied scores and the value expected under a random order.

## Result

191 quoted numbers were compared (review, results summary, DEVIATIONS): 177 match after rounding to the printed decimals and 14 differ. Every difference comes from the order of tied scores, from how the quoted text rounded, or (author cap) from leaving out books without an author article; none changes what the summary or the review says. 
By group, matches of compared: Test A 85 of 92; Test B 28 of 30; Test D 32 of 35; Test E 22 of 24; live list 4 of 4; public timestamps 6 of 6. Peak memory 0.76 GB, run time 27 s.

## Main numbers (original files, ties by id)

- **Different books (Test A).** 77.7% of Wikipedia's monthly top 20 are not on the library model's top 50; 48.1% of those rose and 25.6% surged (base 11.3% and 2.8%). The library's next picks, ranked 51 to 70, rose 74.1%; library + Wikipedia picks ranked 21 to 40 rose 83.1%; Wikipedia picks off the combined top 50 rose 41.2%.
- **Already up in the origin month (Test A top 20).** Library 90.1%, library + Wikipedia 87.6%, Wikipedia 47.0%, persistence rule 98.7%. Books already up rose next month 41.9% of the time, the others 8.9%; 27.2% of all rises came from books already up.
- **Persistence rule, top 20 that rose.** Test A 89.2%; Test D 2024 to 2026: print 79.2%, ebook 90.6%, audiobook 91.0%; Test D all formats 2019 to 2026 84.1%; Test E main rows 77.5% (2024 to 2026: 67.2%).
- **Early warning (Test A, books not yet up).** Top 20 that rose: Wikipedia 31.3%, library 59.2%, library + Wikipedia 59.9%, persistence rule 19.4%, base 8.9%; 55.5% of the library's early list are books under 12 months old.
- **Restricted Test A rows** (24 or more months of loans, article already had views; 493,677 rows). Rank: Wikipedia 0.120, library 0.324, library + Wikipedia 0.335; top 20 rose 55.7%, 89.9% and 91.5% against 11.4%.
- **Test B, one column alone.** "Author has an article" 0.109, the author's 6-month view level 0.117, formats borrowed in month 0 0.585, the Wikipedia model 0.127; among authors with an article, view level 0.093 and model 0.127.
- **Test B, by earlier Seattle works.** None (45,303 books): Wikipedia 0.090, library 0.045, both 0.101, gain +0.056. Some (89,667 books): 0.115, 0.423, 0.443, gain +0.020.
- **Coverage.** Test D rows that are Test A books 48.9%; Test E main rows with stored views 20.5% (88,752 of 433,424), where Wikipedia alone ranks at 0.055 (retrained) and 0.053 (Seattle model), history at 0.364 and history + Wikipedia at 0.356.

## Numbers that differ

Difference = this script minus the quoted value, in the printed unit.

| Number | Quoted in | Quoted | This script | Difference | Why |
| --- | --- | ---: | ---: | ---: | --- |
| Test A: persistence-rule top 20 that rose (quoted from robustness_part_a_orig.json) | review | 89.6% | 89.231% | -0.369 points | order of tied scores: any order gives 88.59 to 90.64, a random order 89.21 |
| Test A early warning: library list under 12 months old (Q6) | review | 55% | 55.51% | +0.51 points | cut, not rounded: 55.5 written as 55 |
| Test A alert list: Wikipedia top 20 rose | results summary | 58.7% | 58.590% | -0.110 points | order of tied scores: any order gives 58.59 to 58.78, a random order 58.69 |
| Author cap: Wikipedia top 20 rose, no cap, 2019 to 2023 | DEVIATIONS 17:07 | 58.3% | 58.173% | -0.127 points | the 17:07 check left ties in no fixed order and its cap dropped books without an author article; done that way: 58.27 |
| Author cap: one book per author, 2019 to 2023 | DEVIATIONS 17:07 | 55.9% | 55.673% | -0.227 points | the 17:07 check left ties in no fixed order and its cap dropped books without an author article; done that way: 55.87 |
| Author cap: two books per author, 2024 to 2026 | DEVIATIONS 17:07; results summary | 57.7% | 57.308% | -0.392 points | the 17:07 check left ties in no fixed order and its cap dropped books without an author article; done that way: 57.69 |
| Author cap: one book per author, 2024 to 2026 | DEVIATIONS 17:07; results summary | 55.2% | 55.769% | +0.569 points | the 17:07 check left ties in no fixed order and its cap dropped books without an author article; done that way: 55.19 |
| Test B: author's 6-month view level alone | review | 0.118 | 0.11746 | -0.00054 | rounded twice: 0.11746 printed as 0.1175, then rounded up |
| Test B, authors with an article: view level alone | review | 0.094 | 0.09347 | -0.00053 | rounded twice: 0.09347 printed as 0.0935, then rounded up |
| Test D early warning: repeat-last-month top 20 rose | results summary | 15.7% | 15.983% | +0.283 points | order of tied scores: any order gives 12.82 to 21.41, a random order 15.85 |
| Test E: Wikipedia only, retrained, top 20 | results summary | 8.8% | 8.864% | +0.064 points | order of tied scores: any order gives 8.26 to 9.70, a random order 8.75 |
| Test E: Wikipedia only, Seattle model, top 20 | results summary | 11.7% | 10.985% | -0.715 points | order of tied scores: any order gives 9.39 to 13.03, a random order 11.18 |
| Test D table: Wikipedia only, print | results summary | 44.0% | 44.103% | +0.103 points | order of tied scores: any order gives 44.04 to 44.10, a random order 44.07 |
| Test D table: Wikipedia only, audiobook | results summary | 47.8% | 47.692% | -0.108 points | order of tied scores: any order gives 47.69 to 47.82, a random order 47.76 |

## Persistence rule: share of the top 20 that rose

The rule ranks books by this month's loans against their own 6-month median; it uses no model and no Wikipedia. "Random order" is the value expected when tied scores are ordered at random; the stored robustness files drew one random order and compare the threshold exactly, the stored test reports used the order of an unstable sort.

| Test and rows | Period | Ties by id | Random order | Range over tie orders | Stored value |
| --- | --- | ---: | ---: | --- | --- |
| Test A, all rows | 2019 to 2026 | 89.2% | 89.2% | 88.6% to 90.6% | 89.6% in `robustness_part_a_orig.json` (one random order, exact threshold) |
| Test D, print | 2019 to 2026 | 81.1% | 81.1% | 79.9% to 82.8% | 81.3% in `robustness_part_d.json` (one random order, exact threshold); 81.3% in `wiki_led_test_d.json` (unstable sort) |
| Test D, print | 2024 to 2026 | 79.2% | 79.0% | 78.3% to 79.6% | 79.0% in `robustness_part_d.json` (one random order, exact threshold) |
| Test D, ebook | 2019 to 2026 | 85.1% | 85.1% | 84.5% to 86.5% | 85.1% in `robustness_part_d.json` (one random order, exact threshold); 85.1% in `wiki_led_test_d.json` (unstable sort) |
| Test D, ebook | 2024 to 2026 | 90.6% | 90.8% | 90.4% to 91.0% | 90.8% in `robustness_part_d.json` (one random order, exact threshold) |
| Test D, audiobook | 2019 to 2026 | 86.2% | 86.2% | 85.7% to 87.5% | 86.2% in `robustness_part_d.json` (one random order, exact threshold); 86.2% in `wiki_led_test_d.json` (unstable sort) |
| Test D, audiobook | 2024 to 2026 | 91.0% | 90.8% | 90.6% to 91.0% | 90.8% in `robustness_part_d.json` (one random order, exact threshold) |
| Test D, all formats | 2019 to 2026 | 84.1% | 84.1% | 83.4% to 85.6% | 84.2% in `robustness_part_d.json` (one random order, exact threshold); 84.1% in `wiki_led_test_d.json` (unstable sort) |
| Test D, all formats | 2024 to 2026 | 86.9% | 86.8% | 86.4% to 87.2% | 86.9% in `robustness_part_d.json` (one random order, exact threshold) |
| Test E, main rows | 2019 to 2026 | 77.5% | 77.5% | 77.5% to 77.5% | 77.5% in `wiki_led_test_e.json` (unstable sort) |
| Test E, main rows | 2024 to 2026 | 67.2% | 67.2% | 67.2% to 67.2% |  |
| Test E, all rows | 2019 to 2026 | 77.0% | 77.0% | 77.0% to 77.0% | 77.0% in `wiki_led_test_e.json` (unstable sort) |
| Test E, all rows | 2024 to 2026 | 69.1% | 69.1% | 69.1% to 69.1% |  |
| Test E, main rows with stored views (new) | 2019 to 2026 | 52.3% | 52.4% | 52.3% to 52.4% |  |

Test A's persistence rule uses library loans only, so the corrected files give the same value (89.2%); so do Test D's corrected files (84.1% for all formats, 2019 to 2026).

## Corrected files against the original ones (Test A, Test D)

Addendum e, correction A1: weeks before an article had views are missing, not zero. Only the Wikipedia models change; the library model and the persistence rule do not (unchanged rows are left out here; every number is in the JSON). In the corrected files the rows "before the article had views" are those before the first month at which the book's own page has views; on the original files this marks 6.7% of rows against 7.0% for the review's rule (lvl4 at its floor), and the two rules agree on 99.67% of rows. The restricted rows below use the first-views rule on both files (495,298 rows in each).

| Number | Original | Corrected | Change |
| --- | ---: | ---: | ---: |
| Wikipedia's top 20 not on the library top 50 | 77.7% | 78.4% | +0.7 points |
| of those, rose | 48.1% | 47.5% | -0.6 points |
| Wikipedia top 20 rose | 58.6% | 57.9% | -0.6 points |
| Wikipedia top 50 rose | 48.1% | 48.3% | +0.2 points |
| Library + Wikipedia top 20 rose | 93.3% | 93.7% | +0.4 points |
| Wikipedia top 20 already up | 47.0% | 46.2% | -0.8 points |
| Wikipedia picks off the combined top 50, rose | 41.2% | 40.6% | -0.6 points |
| Early warning: Wikipedia top 20 rose | 31.3% | 30.1% | -1.2 points |
| Early warning: library + Wikipedia top 20 rose | 59.9% | 59.4% | -0.6 points |
| Restricted rows (first-views rule on both): rank, Wikipedia | 0.1196 | 0.1193 | -0.0003 |
| Restricted rows (first-views rule on both): Wikipedia top 20 rose | 55.6% | 55.3% | -0.3 points |
| Gain from Wikipedia, books under 12 months | -0.0034 | -0.0042 | -0.0008 |
| Wikipedia top 20 rose, 2024 to 2026 | 59.4% | 59.4% | 0.0 points |
| block interval, lower end | 52.9% | 53.8% | +1.0 points |
| block interval, upper end | 65.8% | 64.8% | -1.0 points |
| Months above the base rate (of 78) | 78 | 78 | 0 |
| Author cap, 2024 to 2026: two per author | 57.3% | 59.8% | +2.5 points |
| Author cap, 2024 to 2026: one per author | 55.8% | 54.8% | -1.0 points |
| Test D, all formats: Wikipedia top 20 rose | 47.4% | 45.5% | -1.9 points |
| Test D, all formats: library + Wikipedia top 20 rose | 87.9% | 88.0% | 0.0 points |
| Test D, print, 2024 to 2026: library + Wikipedia | 85.0% | 85.0% | 0.0 points |
| Test D, ebook, 2024 to 2026: library + Wikipedia | 92.1% | 92.3% | +0.2 points |
| Test D, audiobook, 2024 to 2026: library + Wikipedia | 92.7% | 93.1% | +0.4 points |

## August 2026 example (origin July 2026)

Origin 2026-07, predicting 2026-08; 7,650 books, of which 11.7% rose and 2.4% surged. Top 20 that rose (surged): Wikipedia 8 (6), library 20 (17), library + Wikipedia 20 (18). Top 50: Wikipedia 21 rose (42%) and 12 surged (24%); library 45 and 33; library + Wikipedia 45 and 35. The author with most books in Wikipedia's top 20 is Laura Ingalls Wilder (9 books, 0 rose); 8 of the other 11 rose. 7 of Wikipedia's 20 were already up at the origin, and 2 are also in the library's top 20.

Corrected files: Wikipedia 7 rose (6 surged) in the top 20 and 23 (15) in the top 50; 19 of the 20 books are the same; library + Wikipedia 20 (18).

Wikipedia's top 20 (original files). Loans in 2026-07, median of the 6 months to 2026-07, loans in 2026-08:

| # | Book | Author | 2026-07 | 6-month median | 2026-08 | Rose | Surged |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | Incidents Around the House | Josh Malerman | 41 | 18 | 81 | yes | yes |
| 2 | The Odyssey: The Story of Odysseus | Homer | 0 | 72.5 | 0 | no | no |
| 3 | The Odyssey | Homer | 1138 | 68 | 958 | yes | yes |
| 4 | The Iliad | Homer | 113 | 54.5 | 110 | yes | yes |
| 5 | Little house on the prairie | Laura Ingalls Wilder | 17 | 22.5 | 23 | no | no |
| 6 | On the banks of Plum Creek | Laura Ingalls Wilder | 17 | 15.5 | 13 | no | no |
| 7 | By the shores of Silver Lake | Laura Ingalls Wilder | 16 | 13 | 19 | no | no |
| 8 | Three Bags Full | Leonie Swann | 282 | 199 | 241 | no | no |
| 9 | Little house in the big woods | Laura Ingalls Wilder | 23 | 25 | 31 | no | no |
| 10 | Little town on the prairie | Laura Ingalls Wilder | 11 | 12 | 14 | no | no |
| 11 | These happy golden years | Laura Ingalls Wilder | 15 | 12.5 | 11 | no | no |
| 12 | Regime Change: Inside the Imperial Presidency of Donald Trump | Maggie Haberman | 335 | 199.5 | 448 | yes | yes |
| 13 | Farmer boy | Laura Ingalls Wilder | 14 | 15 | 21 | no | no |
| 14 | The first four years | Laura Ingalls Wilder | 16 | 12.5 | 11 | no | no |
| 15 | The long winter | Laura Ingalls Wilder | 12 | 11 | 10 | no | no |
| 16 | The Five-Star Weekend | Elin Hilderbrand | 125 | 44.5 | 138 | yes | yes |
| 17 | Asymmetry | Lisa Halliday | 15 | 3.5 | 17 | yes | yes |
| 18 | Spoiler Alert: The Hero Dies: A Memoir of Love, Loss, and Other Four-L | Michael Ausiello | 3 | 1.5 | 3 | yes | no |
| 19 | The Dog Stars | Peter Heller (writer) | 83 | 58.5 | 104 | yes | no |
| 20 | Scrublands | Chris Hammer | 5 | 7 | 5 | no | no |

## June to July 2026 example (origin June 2026)

No earlier text (results summary, review, DEVIATIONS, live-list README, reports) gives this example; the numbers are new.

Origin 2026-06, predicting 2026-07; 7,656 books, of which 11.7% rose and 2.4% surged. Top 20 that rose (surged): Wikipedia 13 (8), library 18 (17), library + Wikipedia 19 (17). Top 50: Wikipedia 22 rose (44%) and 15 surged (30%); library 42 and 31; library + Wikipedia 45 and 32. The author with most books in Wikipedia's top 20 is Mary H.K. Choi (3 books, 1 rose); 12 of the other 17 rose. 10 of Wikipedia's 20 were already up at the origin, and 2 are also in the library's top 20.

Corrected files: Wikipedia 11 rose (8 surged) in the top 20 and 23 (15) in the top 50; 16 of the 20 books are the same; library + Wikipedia 20 (17).

Wikipedia's top 20 (original files). Loans in 2026-06, median of the 6 months to 2026-06, loans in 2026-07:

| # | Book | Author | 2026-06 | 6-month median | 2026-07 | Rose | Surged |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | Persepolis | Marjane Satrapi | 10 | 9 | 7 | no | no |
| 2 | Angel Down | Daniel Kraus (author) | 196 | 98.5 | 225 | yes | yes |
| 3 | Whalefall | Daniel Kraus (author) | 46 | 19 | 50 | yes | yes |
| 4 | Regime Change: Inside the Imperial Presidency of Donald Trump | Maggie Haberman | 64 | 64 | 335 | yes | yes |
| 5 | Three Bags Full | Leonie Swann | 254 | 139.5 | 282 | yes | yes |
| 6 | The Vampire Lestat | Anne Rice | 19 | 18.5 | 18 | no | no |
| 7 | Super sad true love story | Gary Shteyngart | 119 | 8.5 | 92 | yes | yes |
| 8 | Owl moon | Jane Yolen | 17 | 15.5 | 12 | no | no |
| 9 | Permanent Record | Mary H.K. Choi | 1 | 1 | 3 | yes | no |
| 10 | Emergency Contact | Mary H.K. Choi | 10 | 6 | 7 | no | no |
| 11 | Taiwan Travelogue | Yang Shuang-zi | 251 | 68 | 208 | yes | yes |
| 12 | Confidence Man: The Making of Donald Trump and the Breaking of America | Maggie Haberman | 10 | 3.5 | 20 | yes | yes |
| 13 | Yolk | Mary H.K. Choi | 7 | 6.5 | 8 | no | no |
| 14 | Yesteryear | Burke, Caro Claire | 2925 | 2312 | 3260 | no | no |
| 15 | Strangers : a memoir of marriage | Belle Burden | 1118 | 574.5 | 1089 | yes | no |
| 16 | Spoiler Alert: The Hero Dies: A Memoir of Love, Loss, and Other Four-L | Michael Ausiello | 2 | 1.5 | 3 | yes | no |
| 17 | John of John | Douglas Stuart (writer) | 212 | 176 | 281 | yes | no |
| 18 | Go gentle | Maria Semple | 599 | 599 | 581 | no | no |
| 19 | Absurdistan | Gary Shteyngart | 16 | 5.5 | 9 | yes | no |
| 20 | Rivals | Jilly Cooper | 29 | 10.5 | 40 | yes | yes |

## Author cap on the Wikipedia-only list (DEVIATIONS 17:07)

At most one or two books per author (author = the author's article), then each month's top 20 that rose. Main rule: ties by work_id, and a book without an author article counts as its own author. "As logged" repeats the 17:07 check exactly: each period's rows sorted by score alone with pandas' default sort, which keeps no fixed order for tied scores, and a cap that leaves out books without an author article. It reproduces all six logged numbers; the gaps to the main rule (up to 0.6 points) come from those two choices, and the cap lowers the share under both.

| Cap | Main rule: 2019 to 2023, 2024 to 2026 | As logged | Logged in DEVIATIONS | Distinct authors per list, 2019 to 2026 | Corrected files, main rule |
| --- | --- | --- | --- | ---: | --- |
| none | 58.2%, 59.4% | 58.3%, 59.4% | 58.3%, 59.4% | 13.4 | 57.2%, 59.4% |
| two per author | 56.2%, 57.3% | 56.2%, 57.7% | 56.2%, 57.7% | 16.2 | 54.5%, 59.8% |
| one per author | 55.7%, 55.8% | 55.9%, 55.2% | 55.9%, 55.2% | 20.0 | 54.1%, 54.8% |

## Other numbers worth knowing (not quoted before)

- Test A: library picks ranked 21 to 40 rose 81.5%; Wikipedia's off-list picks average 15.5 books a month; pooled over months, 47.8% of them rose (the 48.1% above is the mean of monthly shares).
- Test A: the no-fitting Wikipedia rule's top 20 rose 15.5% (corrected files: 27.4%).
- Test E, main rows with stored Wikipedia views: the persistence rule's top 20 rose 52.3%, history + Wikipedia 54.4%, Wikipedia alone 8.9%.
- Test D, 2024 to 2026: 99.2% of Wikipedia's audiobook top 20 are Test A books, a little below the 99.7% to 100% of 2019 to 2026.
- Test B gain from Wikipedia by year: 2019 +0.020, 2020 +0.026, 2021 +0.020, 2022 +0.020, 2023 +0.021, 2024 +0.022, 2025 +0.026, 2026 +0.034.

## Not recomputable from stored predictions

- "The strongest features are the author's and the book's views relative to normal" (results summary, Test A). The Test A models were not saved, so their feature importances need a refit; the stored importance files belong to the improvement-round models. This script fits no model.
- The two-months-ahead comparison (library 0.336 against Wikipedia 0.138, 2019 to 2023; review, Threat 9 and Q3) comes from `wiki_led_test_a_horizon_2019_2023.csv`, an exploratory refit at another horizon with no script. It needs new model fits.
- Numbers that the review or the summary take from files written by other scripts (for example `wiki_led_test_a.json`, `wiki_led_test_b.json`, `wiki_led_test_d.json`, the robustness files) already have a source and are repeated here only where they show the tie rule.

## Inputs

Read only: `data/db/study2r/works.parquet` (2026-10-14 20:46), `data/db/wiki_led/test_a_preds.parquet` (2026-10-20 15:14), `data/db/wiki_led/test_a_rows.parquet` (2026-10-20 15:12), `data/db/wiki_led/test_a_preds_c.parquet` (2026-10-20 20:48), `data/db/wiki_led/test_a_rows_c.parquet` (2026-10-20 20:45), `data/reports/wiki_led_test_a_accuracy.csv` (2026-10-20 17:52), `data/db/wiki_led/test_b_preds.parquet` (2026-10-20 18:58), `data/db/wiki_led/test_b_rows.parquet` (2026-10-20 18:56), `data/db/wiki_led/test_d_preds.parquet` (2026-10-20 18:01), `data/db/wiki_led/test_d_preds_c.parquet` (2026-10-20 21:23), `data/db/wiki_led/test_e_preds.parquet` (2026-10-20 18:04), `data/db/wiki_led/test_e_rows.parquet` (2026-10-20 17:58), `data/db/wiki_led/live_alert_2026-10_all.parquet` (2026-10-20 17:00), `data/db/wiki_led/robustness_part_a_orig.json` (2026-10-20 20:46), `data/db/wiki_led/robustness_part_d.json` (2026-10-20 21:24), `data/reports/wiki_led_test_d.json` (2026-10-20 18:01), `data/reports/wiki_led_test_e.json` (2026-10-20 18:04); `git log` of `~/cmkl-thesis-research`.
