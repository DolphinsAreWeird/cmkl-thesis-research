# D2: an event calendar (films, TV series, deaths, awards) to flag books whose borrowing will jump

Khant Phyo Wai, 01323050. Run 22 Oct 2026 03:34 +07. Direction D2 of addendum i (`prereg/addenda_wiki_led/2026-10-22_i_directions.json`, section D2_event_calendar). Choices the addendum leaves open: C1 to C11 in the header of `code/main_study/wiki_led/dirs/d2_events.py`, also logged in `prereg/DEVIATIONS.md` (Addendum i). Exploratory and descriptive; every interval is a 95% interval. Tables and the figure: `data/db/wiki_led/dirs/d2_events/`.

**In plain words**

1. When a film or TV version of a book comes out, its borrowing jumps and stays up for a year: in the release month and the two months after, 45.9% of these books were borrowed at least 1.5 times their usual amount, against 10.4% of books with the same usual level and no event (made-up dates two years earlier give a gap of +4.5 points instead of +35.5). An author's death does the same (49.5% against 17.2%) with no rise before it; an award dated to the month in Wikidata barely moves borrowing (+3.0 points).
2. Known release dates work as an alert: of the books with a film or TV release in the next three months, 54.3% rose and 34.7% surged (at least double and 5 loans more) in those months, against 22.8% and 6.4% of all books, and against 25.2% and 7.3% of books that the library's own model (H) scored about the same. So the calendar knows something the loan history does not.
3. Still, the alert list does not beat H's own top 20, which are mostly books whose borrowing is already climbing (95.4% of them rose in the next three months). Putting the alert books into H's top 20 lowered its hit rate clearly in 43 of the 48 versions tried and left it within noise in 4; the one gain is small (surges among books not yet risen, at most 5 public releases swapped in: +1.9 points, interval +0.2 to +3.6).
4. Events explain few of the big jumps: 4.8% of the 20,484 surges of 2016 to 2026 had a known event of the book or its author within two months (chance: 0.8% of all book-months). Events are rare (about 15 release alerts a month among about 7,100 books), which helps explain why the improvement round v2, which gave similar event flags to the models as extra columns, found no gain.
5. Limit: Wikidata dates may have been entered after the event, so this calendar is not exactly what was known at the time. Keeping only adaptations whose Wikipedia article already had views at the alert month gives the same picture (59.1% rose, 40.3% surged).

Terms. **Usual level** (M6): the median of a book's monthly loans over six months (all formats, as in Test A). **Rose**: loans at least 1.5 times the usual level; **surged**: at least 2 times and at least 5 loans more (Test A's arithmetic, ln(1 + loans) against ln(1 + M6)). **H**: Test A's library-history model (LightGBM on the book's own loan history), whose predictions for 2019-01 to 2026-07 are in `test_a_preds_c.parquet`. A month **t** is the month at whose end the list is made.

## 1. Events used

From `data/db/wiki_led/events_long.parquet` (Wikidata, fetched 20 Oct 2026 for the 7,747 Test A works): film and TV adaptations with a release month (earliest best-rank P577 or P580 date at month precision), the death month of the author (P570), and awards with a month-precision date (P166 with P585, book or author). Year-only dates cannot be placed in a month and are not used: that leaves out 95% of the dated award statements, including the Booker, Pulitzer, Hugo and Newbery prizes, so the award result is about honorary degrees, orders, fellowships and the Nebula Award, not about the big book prizes. Event study events, 2006-07 to 2026-08: film 632 (525 works), TV 353 (323 works), deaths 774 (774 works, 268 authors), dated awards 397 (295 works). The `ad_rel` flag of `events.parquet` (a release in t-1, t or t+1) is not used: the alert here needs releases in t+1 to t+3, built from the release months. Its `ad_rel_public` column is empty on purpose; the 'already public' check is made here as in v2 (the adaptation's English article had views by the end of t).

## 2. Event study: borrowing from 3 months before to 12 months after the event

Each event is compared with books that had no dated event from 9 months before to 12 months after it, matched on the same month and the same tenth of usual loan level (usual level M6 = median of months -9 to -4, so the months -3 to -1 show any rise before the event). The difference is the event books' share minus the matched books' share. Placebo: the same books with their dates moved 24 months earlier (fake events with a real event in their window dropped). Intervals: 2,000 bootstrap draws over works (deaths also over authors, since one death touches all of an author's books).

![Event study](../db/wiki_led/dirs/d2_events/d2_event_study.png)

**Months 0 to 2** (the event month and the two after):

| Event | Events (works) | Rose: event / matched | Difference, points (interval) | Placebo difference | Surged: event / matched | Difference, points (interval) | Placebo difference | Loans against usual level, relative to matched |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Film or TV release | 985 (807) | 45.9% / 10.4% | +35.5 (+32.7 to +38.4) | +4.5 | 31.0% / 2.9% | +28.1 (+25.3 to +30.9) | +2.0 | 1.77x |
| of which film | 632 (525) | 47.2% / 10.4% | +36.8 (+33.4 to +40.4) | +5.4 | 33.0% / 2.8% | +30.2 (+26.6 to +33.7) | +2.2 | 1.82x |
| of which TV | 353 (323) | 43.3% / 10.4% | +32.9 (+28.3 to +37.3) | +2.7 | 27.0% / 2.9% | +24.1 (+19.9 to +28.5) | +1.7 | 1.69x |
| Author's death | 774 (774) | 49.5% / 17.2% | +32.3 (+29.5 to +35.0) | -1.4 | 28.3% / 4.6% | +23.7 (+21.0 to +26.3) | -1.0 | 1.58x |
| Dated award | 397 (295) | 15.3% / 12.4% | +3.0 (+0.2 to +5.7) | -0.9 | 5.3% / 3.4% | +2.0 (+0.2 to +3.9) | -0.0 | 1.05x |

For deaths, resampling authors instead of works gives a wider interval for the rose difference: +26.1 to +38.3. The last column is exp of the difference in mean ln((1 + loans) / (1 + usual level)): 1.77x means the event books' loans relative to their usual level were about 1.77 times those of the matched books.

**Difference in points by window** (event minus matched; interval):

| Event | Measure | months -3 to -1 | months 0 to 2 | months 3 to 5 | months 6 to 12 |
| --- | --- | --- | --- | --- | --- |
| Film or TV release | rose | +13.1 (+10.9 to +15.3) | +35.5 (+32.7 to +38.4) | +35.0 (+31.9 to +38.1) | +29.5 (+26.8 to +32.3) |
| Film or TV release | surged | +7.9 (+6.3 to +9.5) | +28.1 (+25.3 to +30.9) | +28.1 (+25.1 to +31.2) | +22.2 (+19.8 to +24.7) |
| of which film | rose | +16.2 (+13.4 to +18.9) | +36.8 (+33.4 to +40.4) | +36.1 (+32.1 to +40.4) | +31.0 (+27.5 to +34.6) |
| of which film | surged | +9.4 (+7.4 to +11.6) | +30.2 (+26.6 to +33.7) | +30.3 (+26.7 to +34.4) | +23.9 (+20.8 to +27.3) |
| of which TV | rose | +7.5 (+4.4 to +10.6) | +32.9 (+28.3 to +37.3) | +33.0 (+28.4 to +37.5) | +26.9 (+22.8 to +31.1) |
| of which TV | surged | +5.1 (+3.0 to +7.4) | +24.1 (+19.9 to +28.5) | +23.9 (+19.8 to +28.5) | +19.1 (+15.6 to +23.3) |
| Author's death | rose | +0.3 (-1.5 to +2.0) | +32.3 (+29.5 to +35.0) | +26.4 (+23.5 to +29.4) | +14.5 (+12.1 to +17.0) |
| Author's death | surged | -0.2 (-1.1 to +0.7) | +23.7 (+21.0 to +26.3) | +18.9 (+16.2 to +21.7) | +10.6 (+8.6 to +12.6) |
| Dated award | rose | +3.4 (+0.8 to +5.9) | +3.0 (+0.2 to +5.7) | +1.9 (-1.0 to +4.9) | +3.2 (+0.4 to +6.0) |
| Dated award | surged | +1.3 (-0.2 to +2.9) | +2.0 (+0.2 to +3.9) | +2.4 (+0.3 to +4.7) | +3.2 (+1.1 to +5.4) |

Reading. Film and TV releases lift borrowing before the release month (films +16.2 points in months -3 to -1: trailers, premieres abroad, tie-in editions) and the lift lasts: still +29.5 points in months 6 to 12. Deaths give no rise before (+0.3 points in months -3 to -1), a peak in the month after the death, and a slow fade (+14.5 points in months 6 to 12). The placebo is near 0 for deaths and awards but not for adaptations (+4.5 points in months 0 to 2, +5.5 in months 6 to 12): books that will be adapted were already gaining readers two years before, which matching on the usual level does not remove. So about 31 of the 35 points in months 0 to 2 belong to the release itself.

## 3. Prediction test: alert lists against the base rate and against H

Rows: Test A's scored book-months (origins 2019-01 to 2026-07, 78 months with library data, about 7,100 books a month). 'Rose in t+1..t+3' means rose in at least one of the next three months (each against the usual level at t); it needs month t+3, so origins 2019-01 to 2026-05 (76 months). Base = all books of the same months. 'Same H tenth' = books that are not on the alert list in the same month and the same tenth of H's score: the difference against them is what the alert adds to the library's own history. Intervals: bootstrap over works (alert lists) or over blocks of 3 months (H's top 20).

**All books; outcome in t+1..t+3:**

| Alert list at the end of month t | Book-months (books) | Rose in t+1..t+3 | Surged in t+1..t+3 | Base: rose / surged | Surged: times base | Rose: difference to same H tenth, points | Surged: difference to same H tenth, points |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Film or TV release in t+1..t+3 | 1,134 (380) | 54.3% (50.0% to 58.9%) | 34.7% (30.4% to 39.3%) | 22.8% / 6.4% | 5.4 | +29.2 (+25.4 to +33.2) | +27.4 (+23.3 to +31.8) |
| Film or TV release in t+1..t+3, article already public at t | 787 (295) | 59.1% (53.9% to 64.0%) | 40.3% (35.1% to 45.5%) | 22.7% / 6.3% | 6.3 | +33.3 (+28.7 to +38.0) | +32.7 (+27.8 to +37.7) |
| Film or TV release in month t (extra) | 390 (354) | 52.1% (47.2% to 57.3%) | 34.4% (29.7% to 39.5%) | 23.1% / 6.5% | 5.3 | +14.6 (+10.6 to +19.0) | +22.0 (+17.8 to +26.3) |
| Author died in month t | 316 (316) | 63.9% (58.5% to 69.3%) | 43.7% (38.0% to 48.7%) | 22.7% / 6.3% | 6.9 | +25.3 (+20.7 to +29.8) | +30.5 (+25.4 to +35.1) |
| Dated award in month t | 131 (109) | 22.9% (15.7% to 29.8%) | 8.4% (3.9% to 13.7%) | 22.2% / 6.3% | 1.3 | +0.3 (-6.5 to +6.8) | +2.1 (-2.4 to +7.3) |
| Any of the three alerts above | 1,580 (789) | 53.7% (50.0% to 57.1%) | 34.4% (30.7% to 37.8%) | 22.7% / 6.4% | 5.4 | +26.0 (+22.8 to +29.1) | +26.0 (+22.6 to +29.2) |
| H's top 20 each month | 1,520 | 95.4% (93.9% to 96.7%) | 84.7% (82.0% to 87.2%) | 23.2% / 6.5% | 13.1 |  |  |

**All books; next month only (Test A's own target, 78 months):**

| Alert list | Book-months | Rose next month | Surged next month | Base: rose / surged | Surged: difference to same H tenth, points |
| --- | --- | --- | --- | --- | --- |
| Film or TV release in t+1..t+3 | 1,162 | 26.9% | 13.9% | 11.2% / 2.7% | +10.6 (+8.1 to +13.1) |
| Film or TV release in t+1..t+3, article already public at t | 811 | 29.3% | 16.2% | 11.1% / 2.7% | +12.6 (+9.9 to +15.3) |
| Film or TV release in month t (extra) | 393 | 42.5% | 28.5% | 11.3% / 2.8% | +22.0 (+17.7 to +26.4) |
| Author died in month t | 322 | 54.7% | 37.6% | 11.5% / 2.8% | +30.3 (+25.7 to +35.5) |
| Dated award in month t | 131 | 9.2% | 2.3% | 10.9% / 2.8% | -0.5 (-2.7 to +2.3) |
| Any of the three alerts above | 1,614 | 31.0% | 17.7% | 11.2% / 2.8% | +13.6 (+11.6 to +15.8) |
| H's top 20 each month | 1,560 | 92.1% | 79.9% | 11.3% / 2.8% |  |

Check of the H matching with hundredths of H's score instead of tenths: public release alerts 59.1% rose against 26.4% of books in the same hundredth; 40.3% surged against 8.6%. By band of H's score (alert books against the other books of the band, outcome in t+1..t+3):

| Alert list | Band of H's score that month | Alert book-months | Rose: alert / others | Surged: alert / others |
| --- | --- | --- | --- | --- |
| Film or TV release in t+1..t+3, article already public at t | below the median | 316 | 49.7% / 12.6% | 33.9% / 3.0% |
| Film or TV release in t+1..t+3, article already public at t | 50th to 90th percentile | 344 | 56.7% / 25.9% | 32.6% / 6.2% |
| Film or TV release in t+1..t+3, article already public at t | 90th to 99th percentile | 101 | 86.1% / 62.5% | 71.3% / 20.1% |
| Film or TV release in t+1..t+3, article already public at t | top 1% | 26 | 100.0% / 89.4% | 100.0% / 66.7% |
| Author died in month t | below the median | 87 | 32.2% / 12.6% | 13.8% / 3.0% |
| Author died in month t | 50th to 90th percentile | 100 | 62.0% / 25.9% | 35.0% / 6.2% |
| Author died in month t | 90th to 99th percentile | 78 | 79.5% / 62.5% | 56.4% / 20.1% |
| Author died in month t | top 1% | 51 | 98.0% / 89.4% | 92.2% / 66.6% |

Only 1.9% of the release alerts were already in H's top 20, and 42% sat below H's median. In every band the alert books rose and surged more often than the other books, and the alerted books that H also scores in its top 10% surged most often.

**Swapping the alert books into H's top 20.** Version 20: the alert books of the month, in H's order (at most 20), go first and H's own picks fill the rest. Version 5: at most 5 alert books (those H scores highest) replace H's places 16 to 20. Difference = swapped list minus H's top 20, mean over months, in points (the list changed in every month). "Not yet risen" (C11, added after the first run): the same among books whose loans in month t were below 1.5 times the usual level (92.7% of the book-months), where H's top 20 rose in 72.2% of cases in t+1..t+3 and surged in 40.0%.

| Books | Alert list | Version | Books swapped in a month | Rose next month: H to swapped, difference | Rose in t+1..t+3 | Surged in t+1..t+3 |
| --- | --- | --- | --- | --- | --- | --- |
| All books | Film or TV release in t+1..t+3 | up to 20 | 14.3 | 92.1% to 45.6%: -46.5 (-51.8 to -41.2) | 95.4% to 66.4%: -29.0 (-32.8 to -25.0) | 84.7% to 49.8%: -34.9 (-39.9 to -29.7) |
| All books | Film or TV release in t+1..t+3 | up to 5 | 5.0 | 92.1% to 80.8%: -11.3 (-13.2 to -9.3) | 95.4% to 89.2%: -6.2 (-7.8 to -4.5) | 84.7% to 75.7%: -9.0 (-11.0 to -7.0) |
| All books | Film or TV release in t+1..t+3, article already public at t | up to 20 | 10.2 | 92.1% to 60.6%: -31.5 (-36.2 to -26.9) | 95.4% to 77.0%: -18.4 (-21.2 to -15.5) | 84.7% to 62.6%: -22.1 (-25.9 to -18.2) |
| All books | Film or TV release in t+1..t+3, article already public at t | up to 5 | 4.9 | 92.1% to 80.1%: -11.9 (-13.7 to -10.1) | 95.4% to 88.9%: -6.5 (-8.2 to -4.8) | 84.7% to 76.1%: -8.7 (-10.8 to -6.6) |
| All books | Any of the three alerts above | up to 20 | 16.7 | 92.1% to 42.4%: -49.6 (-54.3 to -44.7) | 95.4% to 62.9%: -32.5 (-36.3 to -28.5) | 84.7% to 44.5%: -40.2 (-45.3 to -35.0) |
| All books | Any of the three alerts above | up to 5 | 5.0 | 92.1% to 84.4%: -7.7 (-9.3 to -6.0) | 95.4% to 90.8%: -4.6 (-5.9 to -3.2) | 84.7% to 77.7%: -7.0 (-8.8 to -5.2) |
| Not yet risen | Film or TV release in t+1..t+3 | up to 20 | 12.9 | 59.2% to 36.7%: -22.5 (-26.4 to -18.3) | 72.2% to 59.5%: -12.8 (-16.8 to -8.6) | 40.0% to 36.9%: -3.1 (-6.6 to +0.7) |
| Not yet risen | Film or TV release in t+1..t+3 | up to 5 | 5.0 | 59.2% to 53.2%: -6.0 (-7.8 to -4.0) | 72.2% to 69.6%: -2.6 (-4.5 to -0.7) | 40.0% to 41.4%: +1.4 (-0.5 to +3.2) |
| Not yet risen | Film or TV release in t+1..t+3, article already public at t | up to 20 | 9.0 | 59.2% to 45.2%: -14.0 (-16.9 to -11.2) | 72.2% to 66.4%: -5.8 (-8.3 to -3.2) | 40.0% to 41.6%: +1.6 (-0.8 to +4.0) |
| Not yet risen | Film or TV release in t+1..t+3, article already public at t | up to 5 | 4.8 | 59.2% to 52.9%: -6.3 (-7.8 to -4.7) | 72.2% to 69.7%: -2.5 (-4.2 to -0.7) | 40.0% to 41.9%: +1.9 (+0.2 to +3.6) |
| Not yet risen | Any of the three alerts above | up to 20 | 15.5 | 59.2% to 31.3%: -27.9 (-32.2 to -23.1) | 72.2% to 53.9%: -18.4 (-23.0 to -13.2) | 40.0% to 30.7%: -9.3 (-13.7 to -5.0) |
| Not yet risen | Any of the three alerts above | up to 5 | 5.0 | 59.2% to 53.9%: -5.3 (-7.0 to -3.5) | 72.2% to 69.9%: -2.4 (-4.1 to -0.7) | 40.0% to 40.9%: +0.9 (-1.0 to +2.7) |

Of the 48 differences in the two swap tables (`swap_into_H_top20*.csv`, which also hold the surged-next-month column), 43 have an interval below 0, 4 an interval that holds 0 and 1 an interval above 0. H's top 20 are hard to beat because they are mostly books already climbing: a book at 1.4 times its usual level this month very often passes 1.5 times next month. Release alerts point to books that have not started to climb yet, which is earlier but less certain.

## 4. Practical summary: coverage and precision

Coverage: of the next-month surges in Test A's rows (origins 2016-03 to 2026-07), the share with a dated event of the book or its author within two months of the surge month. Chance: the same share among all book-months. Moved: with every event moved 24 months earlier.

| Event | Surges with an event within 2 months | Coverage | Chance (all book-months) | Coverage, events moved 24 months |
| --- | --- | --- | --- | --- |
| Any event | 988 of 20,484 | 4.8% (4.4% to 5.3%) | 0.8% | 0.7% |
| Film or TV release | 513 of 20,484 | 2.5% (2.1% to 2.9%) | 0.4% | 0.4% |
| Author's death | 446 of 20,484 | 2.2% (1.9% to 2.5%) | 0.3% | 0.2% |
| Dated award | 32 of 20,484 | 0.2% (0.1% to 0.2%) | 0.1% | 0.1% |

Precision: of the flagged book-months (all Test A origins 2016-03 to 2026-05), the share that surged or rose in t+1..t+3.

| Flag | Book-months (books) | Surged in t+1..t+3 | Base | Times base | Rose in t+1..t+3 | Base |
| --- | --- | --- | --- | --- | --- | --- |
| Film or TV release in t+1..t+3 | 1,633 (524) | 36.7% (32.6% to 40.5%) | 6.3% | 5.8 | 54.5% (50.4% to 58.3%) | 22.6% |
| Film or TV release in t+1..t+3, article already public at t | 1,127 (405) | 43.5% (39.2% to 47.8%) | 6.3% | 6.9 | 61.0% (56.7% to 65.4%) | 22.6% |
| Film or TV release in month t (extra) | 564 (507) | 35.1% (31.3% to 39.1%) | 6.3% | 5.5 | 53.7% (49.4% to 57.9%) | 22.9% |
| Author died in month t | 439 (439) | 45.3% (40.5% to 49.9%) | 6.4% | 7.1 | 64.2% (60.1% to 68.6%) | 22.9% |
| Dated award in month t | 199 (169) | 7.5% (4.0% to 11.4%) | 6.5% | 1.2 | 20.1% (14.6% to 26.0%) | 23.1% |
| Any of the three alerts above | 2,270 (1,099) | 35.8% (32.9% to 38.8%) | 6.3% | 5.7 | 53.4% (50.3% to 56.5%) | 22.7% |

So a release or a death is a strong flag when it happens (about 4 in 10 flagged books surge), but it touches few books: about 1 in 20 big surges has a known event nearby.

## 5. Two real examples

**One hundred years of solitude** (García Márquez, Gabriel, 1927-2014). Adaptation: *One Hundred Years of Solitude (TV series)*, first released 2024-12-11 according to Wikidata. Monthly loans, all formats, Seattle Public Library:

| Month | 2024-07 (excluded) | 2024-08 | 2024-09 | 2024-10 | 2024-11 | 2024-12 (release) | 2025-01 | 2025-02 | 2025-03 | 2025-04 | 2025-05 | 2025-06 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Loans | 19 | 29 | 24 | 24 | 152 | 710 | 778 | 591 | 530 | 391 | 296 | 243 |

Alert months: end of 2024-09: H rank 3,070 of 7,523, not yet risen, alert, surged in the next three months; end of 2024-10: H rank 4,030 of 7,543, not yet risen, alert (article public), surged in the next three months; end of 2024-11: H rank 9 of 7,545, already risen, alert (article public), surged in the next three months.

**American Prometheus: The Triumph and Tragedy of J. Robert Oppenheimer** (Kai Bird). Adaptation: *Oppenheimer (film)*, first released 2023-07-20 according to Wikidata. Monthly loans, all formats, Seattle Public Library:

| Month | 2023-02 | 2023-03 | 2023-04 | 2023-05 | 2023-06 | 2023-07 (release) | 2023-08 | 2023-09 | 2023-10 | 2023-11 | 2023-12 | 2024-01 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Loans | 12 | 30 | 43 | 76 | 133 | 798 | 786 | 502 | 342 | 270 | 252 | 256 |

Alert months: end of 2023-04: H rank 3,465 of 7,340, not yet risen, alert (article public), surged in the next three months; end of 2023-05: H rank 186 of 7,371, already risen, alert (article public), surged in the next three months; end of 2023-06: H rank 32 of 7,384, already risen, alert (article public), surged in the next three months.

Excluded months are the library-wide gaps of the benchmark (missing, not low). In both cases the release calendar flagged the book one to three months before its loans moved, while H, which only sees the loan history, ranked it in the thousands until the climb had started. Not every case is this clean: Wuthering Heights (2026 film, February 2026) was already climbing five months before the release (443 loans in 2025-09 against about 110 a month earlier in 2025), and H had it around place 150 to 280 in the three alert months.

## 6. Beside: the improvement round v2 (events as model columns)

In v2 (data/reports/wiki_led_improve_v2.md, section 6 (change 5), and wiki_led_improve_v2_c5.json), the event flags (author death in t or t-1, dated award in t or t-1, a film or tv release in t-1..t+1 whose article was already public, months since the last event) and the adaptation-page views were added to the models as columns. On 2024 to 2026 the change ranking moved +0.0012 (interval -0.0005 to +0.0028), the early list of the Wikipedia model +1.2 points (-1.7 to +3.7) and the ranker +1.0 points (-2.1 to +3.8); with the same columns moved 12 months later the moves were +0.0012, +1.2 and +1.0 points, so no gain was tied to the real dates. On the 1,215 book-months within 2 months of an event the change ranking moved +0.0204 (+0.0006 to +0.0398) against +0.0037 in the placebo.

The two results agree. The events carry real information about the few books they touch (sections 2 and 3), but those books are 0.3% of the scored book-months, so model-wide measures (Spearman over all books, top-20 hit rates) can hardly move. v2 also used flags at t-1..t+1, which often fall on books already climbing that H sees anyway: 35% of the books with a release in month t had already risen at t, against 7% of all books. The rows near an event are the one place where v2 saw a gain, which fits what is found here.

## 7. Limits

- **Wikidata dates may have been entered after the event.** The calendar is today's Wikidata, not what was known at t. For releases, the "already public" list keeps only adaptations whose Wikipedia article had views by the end of t, and it does as well as the full list; it shows that the film or series was known, not that its date was. Deaths and awards are used in their own month, so they are known by the end of t, but a death in the last days of a month leaves little time to act.
- The release month is the earliest dated release (often a festival premiere or the first broadcast), not always the US release (Dune: 2021-09 Venice premiere, US release 2021-10).
- Awards: 95% of dated award statements are year-only and were not used, so the big book prizes are not tested; placing them in their usual announcement month would be a next step.
- Matching is on month and usual loan level only. Books that will be adapted were already gaining readers (placebo), so part of the release gap is selection; the placebo gives its size.
- One book item can have several Seattle works, and one death touches all of an author's works; intervals resample works (and authors for deaths).
- The event study uses 2006-07 to 2026-08 (longer than Test A); the comparison with H uses Test A's scored months only.
- Many measures are reported without adjustment; one interval that just clears 0 among many (the swap gain) is weak evidence.
- C11 (books not yet risen) was added after the first run had been seen; the addendum's comparison on all books is the main one.

## 8. Files

- Code: `code/main_study/wiki_led/dirs/d2_events.py` (run from `code/`: `../.venv/bin/python main_study/wiki_led/dirs/d2_events.py`, about 30 seconds).
- `data/db/wiki_led/dirs/d2_events/`: `event_study_by_month.csv`, `event_study_windows.csv`, `event_study_events.parquet`, `alert_lists_scored_months.csv`, `swap_into_H_top20.csv`, `swap_into_H_top20_not_yet_risen.csv`, `alert_by_H_band.csv`, `coverage_of_surges.csv`, `alert_precision_all_months.csv`, `example_candidates.csv`, `scored_rows_alerts.parquet`, `d2_results.json`, `d2_event_study.png`.
- Check: the loans rebuilt here reproduce Test A's stored change D exactly on all 556,735 scored rows (largest difference 0.0).
