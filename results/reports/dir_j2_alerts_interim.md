# J2: one alert list from library history, Wikipedia, an event calendar, NYT lists and book-linked Wikipedia pages

Khant Phyo Wai, 01323050. Run 2026-10-22 09:31 +0700.

**In plain words**

1. Among books whose borrowing had not yet started to climb, the library model alone (H) put 35.2% surging books in its monthly top 20 (against a base rate of 1.7%); the combined model with Wikipedia, the event calendar and NYT lists put 39.8%, a difference of +4.6 points (interval +2.4 to +7.0): a clear gain by the test fixed in advance.
2. Step by step (points of precision at 20, books not yet risen): the book's own Wikipedia pages +3.1 (+0.7 to +5.5); the event calendar +0.3 (-0.6 to +1.2); the NYT lists +1.2 (+0.4 to +2.2).
3. The cleanest test of the dates is the placebo, the same model with every event date moved 12 months earlier (same inputs in the same order, so only the timing differs): it scored 38.6%, and the real dates beat it by +1.2 points (interval +0.3 to +2.1), so the timing of the events adds information by the rule fixed in advance.
4. Among all books, most of every model's top 20 are books already climbing: H 82.7%, combined 85.7% surge next month (base rate 2.8%); over three months the combined model minus H is +3.6 points among books not yet risen.
5. Limit: event dates come from Wikidata and may have been entered after the event, so the calendar is a little better than what was known at the time; one library (Seattle), and Test A's untuned models.

Addendum j (`prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json`), sections features, models, targets, measures and decision. Choices the record leaves open: J1 to J14 in the header of `code/main_study/wiki_led/dirs/j2_alerts.py`, also logged in `prereg/DEVIATIONS.md` (Addendum j). The book-linked pages come from J1 (`data/reports/dir_j1_links.md`). Every interval is a 95% interval. Tables: `data/db/wiki_led/dirs/j_alerts/`.

**Interim report: the linked-page bursts (L) are not in yet. The ladder stops at H+W+E+N, which stands in for the full model, and the placebo moves the E dates only (J15).**

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

## 2. Main result: the ladder, next-month surges

**Books not yet risen at t (primary)**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history) | 35.2% (31.3% to 39.0%) | 11.2% (10.2% to 12.3%) | 13.8% (12.6% to 15.1%) |
| H+W (+ own Wikipedia pages) | 38.3% (33.7% to 43.0%) | 12.3% (11.2% to 13.5%) | 14.8% (13.6% to 16.0%) |
| H+W+E (+ event calendar) | 38.6% (34.1% to 43.1%) | 12.4% (11.3% to 13.6%) | 14.8% (13.6% to 16.0%) |
| H+W+E+N (+ NYT lists) | 39.8% (35.0% to 44.7%) | 12.6% (11.5% to 13.9%) | 15.0% (13.9% to 16.2%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 38.6% (33.7% to 43.5%) | 12.4% (11.2% to 13.6%) | 14.9% (13.8% to 16.2%) |
| Test A's H (change target, reference) | 29.9% (25.4% to 34.4%) | 8.9% (7.9% to 10.0%) | 10.9% (9.6% to 12.3%) |

**All books**

| Model | Precision at 20 | Average precision | Coverage in top 100 |
| --- | --- | --- | --- |
| H (library history) | 82.7% (79.5% to 85.6%) | 33.6% (31.7% to 35.5%) | 27.3% (25.7% to 28.8%) |
| H+W (+ own Wikipedia pages) | 85.2% (82.9% to 87.5%) | 34.7% (32.8% to 36.5%) | 28.0% (26.4% to 29.5%) |
| H+W+E (+ event calendar) | 85.4% (82.8% to 87.8%) | 34.9% (33.0% to 36.7%) | 28.1% (26.5% to 29.6%) |
| H+W+E+N (+ NYT lists) | 85.7% (83.1% to 88.1%) | 35.0% (33.1% to 36.9%) | 28.2% (26.6% to 29.7%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 85.5% (82.9% to 88.1%) | 34.9% (33.0% to 36.7%) | 28.1% (26.5% to 29.6%) |
| Test A's H (change target, reference) | 79.9% (76.9% to 83.0%) | 30.4% (28.5% to 32.3%) | 25.4% (23.8% to 26.9%) |

**Paired differences** (points, same months; interval):

| Comparison | Precision at 20, not yet risen | Precision at 20, all | Average precision, not yet risen | Coverage, not yet risen |
| --- | --- | --- | --- | --- |
| HW minus H | +3.1 (+0.7 to +5.5) | +2.5 (+0.7 to +4.4) | +1.2 (+0.8 to +1.6) | +1.0 (+0.4 to +1.4) |
| HWE minus HW | +0.3 (-0.6 to +1.2) | +0.2 (-0.9 to +1.2) | +0.1 (-0.0 to +0.3) | +0.0 (-0.3 to +0.3) |
| HWEN minus HWE | +1.2 (+0.4 to +2.2) | +0.3 (-0.5 to +1.2) | +0.2 (+0.0 to +0.3) | +0.2 (-0.1 to +0.6) |
| HWENL minus HWEN | n/a | n/a | n/a | n/a |
| HWEN minus H | +4.6 (+2.4 to +7.0) | +3.0 (+1.3 to +4.9) | +1.5 (+1.0 to +1.9) | +1.2 (+0.6 to +1.8) |
| placebo_E minus H | +3.4 (+1.0 to +5.8) | +2.8 (+1.2 to +4.7) | +1.2 (+0.8 to +1.7) | +1.1 (+0.5 to +1.7) |
| HWEN minus placebo_E | +1.2 (+0.3 to +2.1) | +0.2 (-0.6 to +1.0) | +0.3 (+0.1 to +0.4) | +0.1 (-0.3 to +0.5) |

**Decision (fixed in advance).** Primary: precision at 20 among books not yet risen, full model (HWEN) minus H: +4.6 (+2.4 to +7.0) points; the interval is above 0: passed.
Placebo rule: full minus placebo (Placebo E (H+W+E+N, E dates moved 12 months earlier)) on the same measure +1.2 (+0.3 to +2.1) points; the interval is above 0, so the event information counts.
Check on the origins with complete placebo data (2025-09 and before, 68 months): full minus placebo +1.3 (+0.3 to +2.3).

## 3. Surges within three months (models refitted on that target)

| Model | Precision at 20, not yet risen | Precision at 20, all | Coverage in top 100, not yet risen |
| --- | --- | --- | --- |
| H (library history) | 52.0% (48.0% to 55.7%) | 85.7% (82.7% to 88.6%) | 9.6% (9.0% to 10.3%) |
| H+W (+ own Wikipedia pages) | 52.6% (48.8% to 56.5%) | 88.1% (85.3% to 90.9%) | 9.8% (9.2% to 10.5%) |
| H+W+E (+ event calendar) | 54.0% (50.5% to 57.8%) | 88.6% (85.9% to 90.9%) | 10.2% (9.4% to 11.0%) |
| H+W+E+N (+ NYT lists) | 55.5% (51.9% to 59.4%) | 88.9% (86.2% to 91.5%) | 10.1% (9.4% to 10.9%) |
| Placebo E (H+W+E+N, E dates moved 12 months earlier) | 53.7% (49.9% to 57.4%) | 88.6% (86.0% to 91.1%) | 9.7% (9.1% to 10.4%) |

| Comparison | Precision at 20, not yet risen | Precision at 20, all |
| --- | --- | --- |
| HW minus H | +0.7 (-1.5 to +3.0) | +2.4 (+0.8 to +3.9) |
| HWE minus HW | +1.4 (-0.1 to +2.8) | +0.5 (-0.5 to +1.4) |
| HWEN minus HWE | +1.5 (+0.2 to +2.8) | +0.4 (-0.4 to +1.2) |
| HWEN minus H | +3.6 (+1.3 to +5.9) | +3.2 (+1.7 to +4.8) |
| placebo_E minus H | +1.7 (-0.2 to +3.6) | +2.9 (+1.4 to +4.4) |
| HWEN minus placebo_E | +1.8 (+0.4 to +3.4) | +0.3 (-0.5 to +1.1) |

## 4. What the full model leans on

Share of the split gain by input group (next-month model, mean over the 8 test years): H 72.2%, W 26.3%, E 0.8%, N 0.7%. Top inputs: `h_lt` 31.7%, `h_m6` 21.5%, `h_age` 8.6%, `h_lt1` 4.9%, `h_m12` 4.4%, `a_r1` 4.0%, `b_r4` 3.2%, `a_r4` 3.0%, `h_lyago` 2.4%, `b_r1` 2.1%.

## 5. Three books the full model listed and H did not

Picked by the rule fixed in advance (J14): books in the full model's top 20 among books not yet risen, not in H's top 20 of the same month, that surged next month; first the highest-scored one with an event input on, then one with a linked-page burst, then the next with either. The reasons are the inputs that were on at t; they show what the list contains, not proof of why the model ranked the book high.

1. **Tokyo vice : an American reporter on the police beat in Japan** (Adelstein, Jake), list made at the end of 2022-03: rank 2 in the full model's list, rank 535 in H's. Usual level 4 loans a month, 6 in month t, 24 the next month. Inputs on: tv adaptation 'Tokyo Vice (TV series)' released 2022-04. Linked pages that burst: Tokyo Vice (TV series) (adaptation, work; 2022-03: 96,168 views, 7.1 times its usual month, in the daily top 500).
2. **The art of racing in the rain** (Stein, Garth), list made at the end of 2019-07: rank 6 in the full model's list, rank 2896 in H's. Usual level 42 loans a month, 54 in month t, 112 the next month. Inputs on: film adaptation 'The Art of Racing in the Rain (film)' released 2019-08. Linked pages that burst: The Art of Racing in the Rain (film) (adaptation, work; 2019-07: 80,906 views, 5.5 times its usual month).
3. **Acid for the Children** (Flea), list made at the end of 2019-11: rank 6 in the full model's list, rank 28 in H's. Usual level 24 loans a month, 24 in month t, 68 the next month. Inputs on: on an NYT list in 2019-11 (1 week, entered that month).

## 6. Limits

- Wikidata dates (releases, deaths, linked events) may have been entered after the event, so the calendar is a little better than what was known at the time (as in D2).
- The placebo inputs at the last origins need months after the data end and are missing there; the check on the origins with complete placebo data is given above.
- NYT matches cover 2,892 of the 7,747 works (D3); other works count as never listed.
- One library (Seattle). The models are Test A's, not tuned; a tuned model might use the new inputs better or worse.

## Files

`data/db/wiki_led/dirs/j_alerts/`: `measures.csv` (every model, target, population and measure), `paired_differences.csv`, `feature_on_surge_rates.csv`, `preds_S1_*.parquet` and `preds_S3_*.parquet` (scores per book-month), `importance_*.json`, `j2_results.json`, `feats_*.parquet` (inputs), `prep_info.json`, `prep_l_info.json`.
