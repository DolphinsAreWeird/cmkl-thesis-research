# K2: were the film and TV release dates in Wikidata before the releases?

Khant Phyo Wai, 01323050. Run 22 Oct 2026 14:27 +07. Addendum k, section K2_dates_known_in_time (`prereg/addenda_wiki_led/2026-10-22_k_intent_dates_human.json`, fixed 2026-10-22 11:45 +07). Choices the record leaves open: K2-C1 to K2-C11 in the header of `code/main_study/wiki_led/dirs/k2_date_history.py`. Descriptive; every interval is a 95% interval. Coverage: 609 of 609 adaptation items done.

## In plain words

1. For 609 film and TV adaptations released 2016 to 2026 that D2 and addendum j used, we looked back through each Wikidata page's edit history for the first edit that held the release month.
2. The release date was already on Wikidata before the release month for 34% of them, at least a month before for 24%, and at least three months before for 13%.
3. 18% of the adaptation pages did not exist on Wikidata until the release month or later, so for those the date could not have been known there in advance.
4. Of D2's 1,134 scored release alerts (a film or TV release in the next three months), 313 (28%) had the release date on Wikidata by the end of the alert month. Those books rose in the next three months in 60% (53% to 67%) of cases and surged in 38% (31% to 46%), against 54% (50% to 59%) and 35% (30% to 39%) for all of D2's alerts and 23% and 6% for all books in the same months.
5. So the release alert still works on dates that were really known in time (it beats books with the same H score by 31 points, interval 24 to 37), but a calendar read from Wikidata at the time would have flagged only about 28% as many book-months as D2's list; alerts whose date reached Wikidata only later rose about as often (52% against 60%; in time minus late +8 points, interval -1 to +16).

## Two real examples

1. **Oppenheimer (film)** (film, Wikidata Q108839994), adapted from the Seattle library works 'American Prometheus: The Inspiration for the Major Motion Picture OPPENHEIMER', 'American Prometheus: The Triumph and Tragedy of J. Robert Oppenheimer'. Release date used: 2023-07-20 (P577), month 2023-07. Page created 2021-10-08; the release month first appeared on 2022-02-24, 17 calendar months before the release month (492 days before the release month began). D2's alert for the book: end of 2023-04: date already on Wikidata, rose in the next three months, surged; end of 2023-05: date already on Wikidata, rose in the next three months, surged; end of 2023-06: date already on Wikidata, rose in the next three months, surged.
2. **Go, Dog. Go! (TV series)** (tv, Wikidata Q104750296), adapted from the Seattle library work 'Go, dog, go!'. Release date used: 2021-01-26 (P580), month 2021-01. Page created 2021-01-09; the release month first appeared on 2021-01-29, in the release month itself (28 days after the release month began). D2's alert for the book: end of 2020-10: date not yet on Wikidata, did not rise in the next three months; end of 2020-11: date not yet on Wikidata, rose in the next three months; end of 2020-12: date not yet on Wikidata, rose in the next three months.

Terms. **Rose**: loans at least 1.5 times the book's usual level (M6, the median of its last six months); **surged**: at least 2 times and at least 5 loans more (Test A's arithmetic). **H**: Test A's library-history model. An alert at the end of month **t** names books with a film or TV release in t+1 to t+3 (D2's list).

## 1. What was checked

- Items: every film or TV adaptation release in D2's table (the same table as addendum j's `events_releases.parquet`, checked) with a release month from 2016-01 to 2026-09: 609 items (351 films, 258 TV), linked to 692 work links.
- For each item, its whole Wikidata revision list, then a binary search over revision contents for the first revision with a P577 (publication date) or P580 (start time) statement in the release month used (month precision or finer, not deprecated). Wikidata Action API, maxlag 5, at most 2 requests a second, the project user agent, every answer cached.
- Requests: every answer is cached (6,858 answers, 31.0 MB compressed in `data/interim/k2_wikidata_revisions/`), one network request each; this run made 0 network requests and read 7,561 answers from the cache (maxlag pauses 0, retries 0; the fetch log is `data/reports/k2_wd_revisions.log`). Item status: {'ok': 609}.
- Monotonicity (a date added, removed and added again): 60 random items were checked at 578 more revisions. Earlier addition found: 0 (none); removed for a while after the first addition: 0 (none). Where an earlier addition was found, the first addition is used.

## 2. Was the date in Wikidata in time?

| Group | Items | Before the release month | At least 1 month before | At least 3 months before | Page created in or after the release month |
|---|---|---|---|---|---|
| all | 609 | 34% (30% to 38%; 208 of 609) | 24% (20% to 27%; 144 of 609) | 13% (10% to 16%; 78 of 609) | 18% (15% to 21%; 111 of 609) |
| film | 351 | 44% (39% to 50%; 156 of 351) | 32% (28% to 38%; 114 of 351) | 21% (17% to 26%; 74 of 351) | 12% (9% to 16%; 43 of 351) |
| tv | 258 | 20% (16% to 25%; 52 of 258) | 12% (8% to 16%; 30 of 258) | 2% (1% to 4%; 4 of 258) | 26% (21% to 32%; 68 of 258) |
| property P577 | 381 | 42% (37% to 47%; 160 of 381) | 30% (26% to 35%; 116 of 381) | 20% (16% to 24%; 75 of 381) | 15% (12% to 19%; 58 of 381) |
| property P580 | 228 | 21% (16% to 27%; 48 of 228) | 12% (9% to 17%; 28 of 228) | 1% (0% to 4%; 3 of 228) | 23% (18% to 29%; 53 of 228) |
| released 2016-2018 | 178 | 30% (24% to 37%; 53 of 178) | 20% (14% to 26%; 35 of 178) | 12% (8% to 18%; 22 of 178) | 22% (17% to 29%; 40 of 178) |
| released 2019-2022 | 224 | 24% (19% to 30%; 53 of 224) | 15% (11% to 20%; 34 of 224) | 9% (6% to 14%; 21 of 224) | 20% (15% to 25%; 44 of 224) |
| released 2023-2026 | 207 | 49% (43% to 56%; 102 of 207) | 36% (30% to 43%; 75 of 207) | 17% (12% to 23%; 35 of 207) | 13% (9% to 18%; 27 of 207) |

- Day-precision dates only: the date was on Wikidata before the release day itself for 41% (37% to 45%; 249 of 605).
- Page created after the end of the release month: 10% (8% to 13%; 62 of 609). The date was already in the first revision of the page for 0% (0% to 1%; 1 of 609).
- At the first revision carrying the release month, 71's rule (earliest dated release) already gave that month for 99% (97% to 99%; 600 of 609); for the rest an earlier dated release was listed then and removed or deprecated later.
- Day-precision dates: the exact day used was already there at that first revision for 85% (517 of 605); otherwise the month came first and the day later.
- What the item held just before the release month first appeared (all 609 items): no release date 353 (58%), a year-only date 159 (26%), a date in another month 96 (16%), page created with the date 1 (0%). Among the 401 items whose date was not there before the release month: no release date 243, a year-only date 94, a date in another month 64. A year-only date cannot place a release in a month (D2 and 71 do not use them); a date in another month is often a planned date that moved or another country's release.
- Possible merges (the first revision with the date adds more than 20 KB to a page under 1 KB, so the date may have come from another item's history, which is not searched): 2 (Q25136484, Q65156762). Their times are kept as found. (These two checks were added after a first look at 499 items.)

## 3. Lead time

Calendar months from the first revision holding the release month to the release month (by type).

| Lead time | Items | Share | Film | TV |
|---|---|---|---|---|
| after the release month | 280 | 46.0% | 130 | 150 |
| in the release month | 121 | 19.9% | 65 | 56 |
| 1 month before | 64 | 10.5% | 42 | 22 |
| 2 months before | 44 | 7.2% | 24 | 20 |
| 3 months before | 22 | 3.6% | 16 | 6 |
| 4 to 6 months before | 26 | 4.3% | 23 | 3 |
| 7 to 12 months before | 33 | 5.4% | 33 | 0 |
| 13 to 24 months before | 18 | 3.0% | 17 | 1 |
| more than 24 months before | 1 | 0.2% | 1 | 0 |

Lead time in days to the first day of the release month: 10th percentile -961, quartiles -234 / -24 / 26, 90th percentile 134 (negative = added after the release month began).

## 4. D2's release alerts re-scored

An alert at the end of month t (a release in t+1..t+3) counts as known in time when at least one of its adaptations had the release month on Wikidata before the end of t. Scored alert rows (origins 2019-01 to 2026-07): {'not_known': 828, 'known': 326, 'unknown': 8}; with t+3 observed (origins 2019-01 to 2026-05): {'not_known': 821, 'known': 313}. Of the 821 not-known rows with t+3 observed, the adaptation's Wikidata page already existed at t (without the date) for 610; for the rest the page did not exist yet. The 8 rows of unknown status are at the last origins (2026-07) and are triggered only by releases after 2026-09, outside the record's range; none is in the three-month scoring.

| Alert list | Rows | Works | Rose in t+1..t+3 | Base | Excess over books of the same month and H decile | Surged in t+1..t+3 | Base | Excess over same H decile |
|---|---|---|---|---|---|---|---|---|
| All release alerts (D2) | 1134 | 380 | 54% (50% to 59%) | 23% | +29 (+25 to +33) points | 35% (30% to 39%) | 6% | +27 (+23 to +32) points |
| Date on Wikidata by the end of t | 313 | 136 | 60% (53% to 67%) | 23% | +31 (+24 to +37) points | 38% (31% to 46%) | 6% | +29 (+22 to +36) points |
| Date not yet on Wikidata at t | 821 | 313 | 52% (47% to 57%) | 23% | +29 (+24 to +34) points | 33% (28% to 39%) | 6% | +27 (+22 to +32) points |
| D2 "already public" list | 787 | 295 | 59% (54% to 64%) | 23% | +33 (+29 to +38) points | 40% (35% to 46%) | 6% | +33 (+28 to +38) points |
| Already public, date on Wikidata at t | 263 | 119 | 63% (55% to 70%) | 23% | +33 (+26 to +41) points | 42% (34% to 51%) | 6% | +33 (+26 to +41) points |
| Already public, date not yet on Wikidata | 524 | 227 | 57% (51% to 63%) | 23% | +33 (+28 to +39) points | 39% (33% to 45%) | 6% | +32 (+26 to +38) points |
| *Books not yet risen at t (D2 C11)* | | | | | | | | |
| All release alerts (D2) | 994 | 370 | 49% (45% to 54%) | 20% | +29 (+25 to +34) points | 29% (25% to 33%) | 5% | +24 (+20 to +28) points |
| Date on Wikidata by the end of t | 256 | 123 | 52% (44% to 60%) | 19% | +30 (+23 to +38) points | 27% (21% to 34%) | 5% | +22 (+16 to +29) points |
| Date not yet on Wikidata at t | 738 | 309 | 48% (43% to 53%) | 20% | +29 (+24 to +34) points | 29% (25% to 34%) | 5% | +25 (+20 to +29) points |

- Known in time minus not known (t+1..t+3, all books): rose3 60% vs 52%, difference +8 points (-1 to +16); surge3 38% vs 33%, difference +5 points (-4 to +13).
- Known in time minus not known (next month (t+1), all books): rose1 34% vs 24%, difference +11 points (+4 to +18); surge1 21% vs 11%, difference +10 points (+4 to +16).
- Known in time minus not known (t+1..t+3, books not yet risen): rose3 52% vs 48%, difference +4 points (-5 to +13); surge3 27% vs 29%, difference -2 points (-9 to +6).
- Alerts known in time sit closer to the release: the release falls in t+1 for 45% of them against 29% of the late ones (t+2: 33% against 34%; t+3: 22% against 37%). Compared within the same number of months to the release and weighted to the same mix, known minus late is +7 points for rising next month (raw +11), +8 for surging next month (raw +10), +7 for rising in t+1..t+3 (raw +8) and +5 for surging in t+1..t+3 (raw +5); table by month: `known_vs_late_by_months_to_release.csv`.
- Next month only (Test A's outcome), known in time: rose 34% (28% to 41%), surged 21% (16% to 27%); all release alerts: rose 27% (23% to 30%), surged 14% (11% to 17%).
- Check: the alert rows rebuilt here are exactly D2's `al_adapt` rows, and the all-alert shares equal D2's stored ones ({'three_months_rose3': 0.5432, 'three_months_surge3': 0.3474, 'next_month_rose1': 0.2685, 'next_month_surge1': 0.1394}). Intervals differ slightly from D2's because the bootstrap draws differ.

## 5. Addendum j's release features

Addendum j's release features (e_rel_film, e_rel_tv, e_rel_soon) are on for the same (book, month) pairs as D2's list. Over all Test A origins (2016-03 to 2026-07): 1,661 pairs, known in time 446 (27%), not yet known 1,207, status unknown 8. By year: `data/db/wiki_led/dirs/k2_dates/alert_rows_status_by_year.csv`. j's models were not refitted here.

## 6. Limits

- The first revision holding a date shows when Wikidata had it, not when it was public elsewhere (studio announcements, trade press); a calendar built from other sources could know more.
- Month boundaries are in UTC; the query service lags edits by minutes. Items merged into another item lose the merged-away history.
- The date used is the earliest dated release (often a festival premiere or first broadcast); the search asks for that month, not for the US date.
- Monotonicity was checked on a sample of 60 items; for the rest the binary search assumes the date stayed once added.
- Descriptive; many shares are shown without adjustment.

## 7. Files

- Code: `code/main_study/wiki_led/dirs/k2_date_history.py` (run from `code/`; a rerun uses the cache in `data/interim/k2_wikidata_revisions/` and makes no request).
- `data/db/wiki_led/dirs/k2_dates/`: `items_date_history.parquet` and `.csv` (one row per item: release month, created, first revision with the date, lead time, flags), `shares.csv`, `lead_time_bins.csv`, `alerts_rescored.csv`, `alert_rows_scored.csv`, `alert_rows_status_by_year.csv`, `known_vs_late_by_months_to_release.csv`, `monotonicity_sample.csv`, `k2_results.json`.
