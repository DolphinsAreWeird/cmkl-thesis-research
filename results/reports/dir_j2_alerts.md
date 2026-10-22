# J2: one alert list from library history, Wikipedia, an event calendar, NYT lists and book-linked Wikipedia pages

Khant Phyo Wai, 01323050. Run 2026-10-22 10:17 +0700.

**In plain words**

1. Among books whose borrowing had not yet started to climb, the library model alone (H) put 35.2% surging books in its monthly top 20 (against a base rate of 1.7%); the combined model with Wikipedia, the event calendar, NYT lists and linked pages put 39.4%, a difference of +4.2 points (interval +1.8 to +6.5): a clear gain by the test fixed in advance.
2. Step by step (points of precision at 20, books not yet risen): the book's own Wikipedia pages +3.1 (+0.7 to +5.5); the event calendar +0.3 (-0.6 to +1.2); the NYT lists +1.2 (+0.4 to +2.2); the linked pages -0.4 (-1.5 to +0.6).
3. The cleanest test of the dates is the placebo, the same model with every event and linked-page date moved 12 months earlier (same inputs in the same order, so only the timing differs): it scored 38.6%, and the real dates beat it by +0.8 points (interval -0.3 to +1.7), so the timing of events and linked-page bursts does not clearly add information by the rule fixed in advance. Most of the gain over H does not depend on the dates: the placebo itself is +3.4 points above H, from the book's own Wikipedia pages and the NYT lists, which it keeps. For surges within three months the real dates do beat the placebo (+2.2, +0.6 to +3.8; a secondary measure).
4. Each kind of linked page added alone to H+W (points of precision at 20, books not yet risen): concept or other -0.6 (-1.5 to +0.2); event -0.1 (-0.9 to +0.7); person -0.1 (-0.7 to +0.6); place -0.4 (-1.5 to +0.5); work -0.3 (-1.2 to +0.4). Over three months the combined model minus H is +3.0 points (+0.7 to +5.3) among books not yet risen.
5. Among all books, most of every model's top 20 are books already climbing (H 82.7%, combined 85.4% surge next month, base rate 2.8%). Limit: Wikidata dates may have been entered after the event, so the calendar is a little better than what was known at the time; one library (Seattle), Test A's untuned models.

Addendum j (`prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json`), sections features, models, targets, measures and decision. Choices the record leaves open: J1 to J14 in the header of `code/main_study/wiki_led/dirs/j2_alerts.py`, also logged in `prereg/DEVIATIONS.md` (Addendum j). The book-linked pages come from J1 (`data/reports/dir_j1_links.md`). Every interval is a 95% interval. Tables: `data/db/wiki_led/dirs/j_alerts/`.

Terms. **Usual level** (M6): the median of a book's monthly loans over the six months to t (all formats, Test A). **Surge**: next month's loans at least 2 times the usual level and at least 5 loans more (Test A's arithmetic, ln(1 + loans) against ln(1 + M6)). **Not yet risen**: loans in month t below 1.5 times the usual level (same arithmetic), 92.7% of the rows. **Precision at 20**: the share of a month's top 20 that surge. **Coverage**: the share of a month's surges that are in the top 100. A month **t** is the month at whose end the list is made; every input is known by then.

## 1. Rows, targets and inputs

Rows: Test A's corrected rows (`test_a_rows_c.parquet`), 750,501 book-months of the 7,747 works, origins 2016-03 to 2026-07; scored: 556,735 rows of 78 origin months (2019-01 to 2026-07), each test year fitted on the years before (Test A's walk-forward). Check: the surge rule gives 20,484 next-month surges in all rows, the same as D2. Three-month target (surge in the largest of months t+1 to t+3): 76 origin months (2019-01 to 2026-05).

Base rates (mean over months): next-month surge 2.8% of all books and 1.7% of books not yet risen; three-month surge 6.5% and 4.9%. About 7,138 books are ranked each month, 6,613 of them not yet risen.

Inputs. **H**: the book's own loans (6 columns of Test A). **W**: the book's and author's own Wikipedia pages (18 columns of Test A, corrected). **E**: film or TV releases in the next three months (D2's dates), the author's death this month, and round anniversaries (25, 50, 75 ... years) in the next three months of dated events linked to the book and of the author's birth and death (J1). **N**: on an NYT list this month, entered a list this month, weeks on lists (D3). **L**: bursts of the book's linked Wikipedia pages this month and last month (a month with at least 3 times the page's usual views and 3,000 views, or a day in the top 500), by link type and by page kind (J1).

How often each input is on in the scored rows, and the next-month surge rate where it is on (base: 2.8% of all rows, 1.7% of rows not yet risen). A check that the inputs carry signal (descriptive, not a test):

| Input (on) | Rows | Books | Surge rate where on | Same, not yet risen |
| --- | --- | --- | --- | --- |
| `e_rel_film` | 647 | 219 | 15.3% | 7.6% |
| `e_rel_tv` | 517 | 183 | 12.2% | 7.4% |
| `e_rel_soon` | 1,162 | 391 | 13.9% | 7.5% |
| `e_death` | 322 | 322 | 37.6% | 12.1% |
| `e_ann_event` | 80 | 27 | 2.5% | 0.0% |
| `e_ann_birth` | 5,238 | 1,915 | 2.5% | 1.6% |
| `e_ann_death` | 988 | 370 | 3.1% | 1.9% |
| `n_on` | 6,812 | 1,034 | 5.5% | 1.5% |
| `n_enter` | 1,581 | 970 | 14.4% | 4.7% |
| `n_weeks` | 6,812 | 1,034 | 5.5% | 1.5% |
| `l_all_a0` | 63,064 | 3,107 | 3.8% | 1.9% |
| `l_lt_adaptation_a0` | 5,440 | 1,023 | 11.4% | 3.4% |
| `l_lt_character_a0` | 1,744 | 364 | 9.8% | 3.3% |
| `l_lt_event_period_a0` | 9,003 | 391 | 4.0% | 2.0% |
| `l_lt_person_a0` | 2,229 | 104 | 4.4% | 2.4% |
| `l_lt_place_a0` | 39,680 | 1,300 | 2.8% | 1.6% |
| `l_lt_series_a0` | 5,052 | 893 | 6.9% | 2.5% |
| `l_lt_subject_a0` | 4,927 | 513 | 3.7% | 1.6% |
| `l_cat_concept_other_a0` | 4,439 | 957 | 7.0% | 2.5% |
| `l_cat_event_a0` | 8,986 | 382 | 4.1% | 2.0% |
| `l_cat_person_a0` | 2,684 | 130 | 3.9% | 2.2% |
| `l_cat_place_a0` | 41,622 | 1,297 | 2.8% | 1.6% |
| `l_cat_work_a0` | 10,282 | 1,769 | 8.8% | 2.9% |

Linked pages (J1, file of 2026-10-22 10:11:12): 10,283 pages linked, 10,283 selected, 10,276 with views used here; 4,530 works have at least one linked page with views; download complete: yes.

L covers burst months 2016-01 to 2026-09; 4,530 of the 7,747 works have linked pages with views in J1's file. Placebo inputs (dates moved 12 months earlier) have complete data for origins up to 2025-09; later they are missing.

## 2. Main result: the ladder, next-month surges

**Books not yet risen at t (primary)**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history) | 35.2% (31.3% to 39.0%) | 11.2% (10.2% to 12.3%) | 13.8% (12.6% to 15.1%) |
| H+W (+ own Wikipedia pages) | 38.3% (33.7% to 43.0%) | 12.3% (11.2% to 13.5%) | 14.8% (13.6% to 16.0%) |
| H+W+E (+ event calendar) | 38.6% (34.1% to 43.1%) | 12.4% (11.3% to 13.6%) | 14.8% (13.6% to 16.0%) |
| H+W+E+N (+ NYT lists) | 39.8% (35.0% to 44.7%) | 12.6% (11.5% to 13.9%) | 15.0% (13.9% to 16.2%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 38.6% (33.7% to 43.5%) | 12.4% (11.2% to 13.6%) | 14.9% (13.8% to 16.2%) |
| H+W+E+N+L (full: + linked pages) | 39.4% (34.8% to 43.9%) | 12.4% (11.3% to 13.6%) | 14.7% (13.5% to 15.9%) |
| Placebo (full, E and L dates moved 12 months earlier) | 38.6% (33.8% to 43.5%) | 12.4% (11.2% to 13.6%) | 14.7% (13.4% to 15.9%) |
| Test A's H (change target, reference) | 29.9% (25.4% to 34.4%) | 8.9% (7.9% to 10.0%) | 10.9% (9.6% to 12.3%) |

**All books**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history) | 82.7% (79.5% to 85.6%) | 33.6% (31.7% to 35.5%) | 27.3% (25.7% to 28.8%) |
| H+W (+ own Wikipedia pages) | 85.2% (82.9% to 87.5%) | 34.7% (32.8% to 36.5%) | 28.0% (26.4% to 29.5%) |
| H+W+E (+ event calendar) | 85.4% (82.8% to 87.8%) | 34.9% (33.0% to 36.7%) | 28.1% (26.5% to 29.6%) |
| H+W+E+N (+ NYT lists) | 85.7% (83.1% to 88.1%) | 35.0% (33.1% to 36.9%) | 28.2% (26.6% to 29.7%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 85.5% (82.9% to 88.1%) | 34.9% (33.0% to 36.7%) | 28.1% (26.5% to 29.6%) |
| H+W+E+N+L (full: + linked pages) | 85.4% (82.9% to 87.8%) | 34.9% (33.0% to 36.7%) | 28.2% (26.5% to 29.6%) |
| Placebo (full, E and L dates moved 12 months earlier) | 85.3% (82.8% to 87.9%) | 34.9% (33.0% to 36.8%) | 28.1% (26.5% to 29.6%) |
| Test A's H (change target, reference) | 79.9% (76.9% to 83.0%) | 30.4% (28.5% to 32.3%) | 25.4% (23.8% to 26.9%) |

**Paired differences** (points, same months; interval):

| Comparison | Precision at 20, not yet risen | Precision at 20, all | Average precision, not yet risen | Coverage, not yet risen |
| --- | --- | --- | --- | --- |
| HW minus H | +3.1 (+0.7 to +5.5) | +2.5 (+0.7 to +4.4) | +1.2 (+0.8 to +1.6) | +1.0 (+0.4 to +1.4) |
| HWE minus HW | +0.3 (-0.6 to +1.2) | +0.2 (-0.9 to +1.2) | +0.1 (-0.0 to +0.3) | +0.0 (-0.3 to +0.3) |
| HWEN minus HWE | +1.2 (+0.4 to +2.2) | +0.3 (-0.5 to +1.2) | +0.2 (+0.0 to +0.3) | +0.2 (-0.1 to +0.6) |
| HWENL minus HWEN | -0.4 (-1.5 to +0.6) | -0.3 (-1.2 to +0.4) | -0.2 (-0.3 to -0.1) | -0.3 (-0.7 to -0.0) |
| HWENL minus H | +4.2 (+1.8 to +6.5) | +2.7 (+1.1 to +4.4) | +1.3 (+0.9 to +1.7) | +0.9 (+0.4 to +1.4) |
| placebo_E minus H | +3.4 (+1.0 to +5.8) | +2.8 (+1.2 to +4.7) | +1.2 (+0.8 to +1.7) | +1.1 (+0.5 to +1.7) |
| HWEN minus placebo_E | +1.2 (+0.3 to +2.1) | +0.2 (-0.6 to +1.0) | +0.3 (+0.1 to +0.4) | +0.1 (-0.3 to +0.5) |
| placebo minus H | +3.4 (+1.0 to +6.0) | +2.6 (+1.2 to +4.3) | +1.3 (+0.8 to +1.7) | +0.8 (+0.2 to +1.5) |
| HWENL minus placebo | +0.8 (-0.3 to +1.7) | +0.1 (-0.8 to +0.9) | +0.0 (-0.2 to +0.2) | +0.0 (-0.3 to +0.5) |

**Decision (fixed in advance).** Primary: precision at 20 among books not yet risen, full model (HWENL) minus H: +4.2 (+1.8 to +6.5) points; the interval is above 0: passed.
Placebo rule: full minus the placebo model (E and L dates moved 12 months earlier) on the same measure +0.8 (-0.3 to +1.7) points; the interval is not above 0, so by the rule fixed in advance the event and linked-page information does not count (the point gain is above the placebo).
Check on the origins with complete placebo data (2025-09 and before, 68 months): full minus placebo +0.4 (-0.6 to +1.4).
Beside it (J15, the interim test): H+W+E+N minus its E-only placebo +1.2 (+0.3 to +2.1). The interim report read this as the event information counting; with L added, the record's full model and placebo decide, and they do not pass the rule.

## 3. Each kind of linked page added alone to H+W (next month)

| Model | Precision at 20, not yet risen | Minus H+W, not yet risen | Minus H+W, all | Average precision minus H+W, not yet risen |
| --- | --- | --- | --- | --- |
| H+W (reference) | 38.3% (33.7% to 43.0%) |  |  |  |
| H+W + concept or other pages | 37.6% (32.9% to 42.2%) | -0.6 (-1.5 to +0.2) | -0.3 (-1.3 to +0.6) | -0.1 (-0.2 to +0.1) |
| H+W + event pages (note a) | 38.1% (33.7% to 42.7%) | -0.1 (-0.9 to +0.7) | -0.6 (-1.5 to +0.3) | +0.0 (-0.1 to +0.1) |
| H+W + person pages (note b) | 38.2% (33.6% to 42.8%) | -0.1 (-0.7 to +0.6) | -0.1 (-1.0 to +0.9) | -0.0 (-0.1 to +0.1) |
| H+W + place pages (note b) | 37.8% (33.3% to 42.4%) | -0.4 (-1.5 to +0.5) | -0.3 (-1.3 to +0.7) | -0.0 (-0.1 to +0.1) |
| H+W + work pages | 37.9% (33.3% to 42.6%) | -0.3 (-1.2 to +0.4) | -0.4 (-1.5 to +0.7) | -0.0 (-0.2 to +0.1) |

Notes from J1 (the fixed inputs were not changed because of them). (a) The event kind follows Wikidata's occurrence class, which also holds concepts such as marriage, love, sleep and crime: of 148 event items that Test F's AI also sorted, it called 88 events and 54 concepts (`ai_kind` in `links.parquet`). (b) The top-500 part of the burst rule saturates for very popular pages (China, New York City, World War II and Donald Trump burst in all 129 months), so for big place and person pages a burst says little; place pages burst in 35% of their months and person pages in 26%.

## 4. Surges within three months (models refitted on that target)

| Model | Precision at 20, not yet risen | Precision at 20, all | Coverage in top 100, not yet risen |
| --- | --- | --- | --- |
| H (library history) | 52.0% (48.0% to 55.7%) | 85.7% (82.7% to 88.6%) | 9.6% (9.0% to 10.3%) |
| H+W (+ own Wikipedia pages) | 52.6% (48.8% to 56.5%) | 88.1% (85.3% to 90.9%) | 9.8% (9.2% to 10.5%) |
| H+W+E (+ event calendar) | 54.0% (50.5% to 57.8%) | 88.6% (85.9% to 90.9%) | 10.2% (9.4% to 11.0%) |
| H+W+E+N (+ NYT lists) | 55.5% (51.9% to 59.4%) | 88.9% (86.2% to 91.5%) | 10.1% (9.4% to 10.9%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 53.7% (49.9% to 57.4%) | 88.6% (86.0% to 91.1%) | 9.7% (9.1% to 10.4%) |
| H+W+E+N+L (full: + linked pages) | 54.9% (51.1% to 58.9%) | 88.4% (85.7% to 90.9%) | 10.0% (9.3% to 10.8%) |
| Placebo (full, E and L dates moved 12 months earlier) | 52.8% (49.2% to 56.4%) | 87.7% (84.9% to 90.2%) | 9.7% (9.0% to 10.4%) |

| Comparison | Precision at 20, not yet risen | Precision at 20, all |
| --- | --- | --- |
| HW minus H | +0.7 (-1.5 to +3.0) | +2.4 (+0.8 to +3.9) |
| HWE minus HW | +1.4 (-0.1 to +2.8) | +0.5 (-0.5 to +1.4) |
| HWEN minus HWE | +1.5 (+0.2 to +2.8) | +0.4 (-0.4 to +1.2) |
| HWENL minus HWEN | -0.6 (-1.9 to +0.7) | -0.5 (-1.4 to +0.3) |
| HWENL minus H | +3.0 (+0.7 to +5.3) | +2.7 (+1.1 to +4.3) |
| placebo_E minus H | +1.7 (-0.2 to +3.6) | +2.9 (+1.4 to +4.4) |
| HWEN minus placebo_E | +1.8 (+0.4 to +3.4) | +0.3 (-0.5 to +1.1) |
| placebo minus H | +0.8 (-1.4 to +2.7) | +2.0 (+0.3 to +3.7) |
| HWENL minus placebo | +2.2 (+0.6 to +3.8) | +0.7 (-0.3 to +1.8) |

## 5. What the full model leans on

Share of the split gain by input group (next-month model, mean over the 8 test years): H 71.7%, W 25.7%, E 0.8%, N 0.7%, L 1.1%. Top inputs: `h_lt` 30.4%, `h_m6` 21.5%, `h_age` 9.4%, `h_lt1` 4.9%, `h_m12` 4.2%, `a_r1` 3.8%, `a_r4` 3.1%, `h_lyago` 2.5%, `b_r4` 2.4%, `b_r1` 2.3%.

## 6. Three books the full model listed and H did not

Picked by the rule fixed in advance (J14): books in the full model's top 20 among books not yet risen, not in H's top 20 of the same month, that surged next month; first the highest-scored one with an event input on, then one with a linked-page burst, then the next with either. The reasons are the inputs that were on at t; they show what the list contains, not proof of why the model ranked the book high.

1. **Tokyo vice : an American reporter on the police beat in Japan** (Adelstein, Jake), list made at the end of 2022-03: rank 4 in the full model's list, rank 535 in H's. Usual level 4 loans a month, 6 in month t, 24 the next month. Inputs on: tv adaptation 'Tokyo Vice (TV series)' released 2022-04; 1 linked adaptation page bursting in 2022-03. Linked pages that burst: Tokyo Vice (TV series) (adaptation, work; 2022-03: 96,168 views, 7.1 times its usual month, in the daily top 500).
2. **Chapterhouse Dune** (Frank Herbert), list made at the end of 2021-10: rank 7 in the full model's list, rank 1231 in H's. Usual level 6 loans a month, 8 in month t, 13 the next month. Inputs on: 5 linked series pages bursting in 2021-10; 5 linked series pages bursting in 2021-09. Linked pages that burst: Dune (novel) (series, work; 2021-10: 2,542,861 views, 9.0 times its usual month, in the daily top 500), Dune (novel) (series, work; 2021-09: 787,543 views, 5.0 times its usual month, in the daily top 500), God Emperor of Dune (series, work; 2021-10: 239,059 views, 9.4 times its usual month, in the daily top 500), God Emperor of Dune (series, work; 2021-09: 60,918 views, 3.7 times its usual month), Heretics of Dune (series, work; 2021-10: 159,568 views, 8.8 times its usual month, in the daily top 500), Heretics of Dune (series, work; 2021-09: 43,072 views, 3.8 times its usual month).
3. **The Winds of War** (Herman Wouk), list made at the end of 2019-05: rank 8 in the full model's list, rank 173 in H's. Usual level 4 loans a month, 7 in month t, 13 the next month. Inputs on: author died in 2019-05; 2 linked event or period pages bursting in 2019-05; 2 linked event or period pages bursting in 2019-04. Linked pages that burst: The Holocaust (event_period, event; 2019-05: 392,435 views, 1.2 times its usual month, in the daily top 500), The Holocaust (event_period, event; 2019-04: 355,392 views, 1.1 times its usual month, in the daily top 500), World War II (event_period, event; 2019-05: 813,357 views, 1.1 times its usual month, in the daily top 500), World War II (event_period, event; 2019-04: 756,106 views, 1.0 times its usual month, in the daily top 500).

A page listed at about its usual level (1.0 to 1.2 times) counts as bursting only through the daily top 500 (note b in section 3), as World War II and The Holocaust do above.

## 7. Limits

- Wikidata dates (releases, deaths, linked events) may have been entered after the event, so the calendar is a little better than what was known at the time (as in D2).
- The placebo inputs at the last origins need months after the data end and are missing there; the check on the origins with complete placebo data is given above.
- NYT matches cover 2,892 of the 7,747 works (D3); other works count as never listed.
- One library (Seattle). The models are Test A's, not tuned; a tuned model might use the new inputs better or worse.
- L: each (book, page) pair counts once, under its first link type (J1). The event kind includes concepts that Wikidata files under occurrence, and very popular place and person pages burst almost every month through the top-500 rule (notes a and b in section 3).

## Files

`data/db/wiki_led/dirs/j_alerts/`: `measures.csv` (every model, target, population and measure), `paired_differences.csv`, `feature_on_surge_rates.csv`, `preds_S1_*.parquet` and `preds_S3_*.parquet` (scores per book-month), `importance_*.json`, `j2_results.json`, `feats_*.parquet` (inputs), `prep_info.json`, `prep_l_info.json`.
