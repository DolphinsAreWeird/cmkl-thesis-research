# Burst features and Wikidata events for the Wikipedia-led tests: data report

Built on 20 October 2026. Data only: no model was fitted and no feature was related to loans. 

## 1. What was built

| File | Rows | Key | Built by |
| --- | --- | --- | --- |
| data/db/wiki_led/burst_features.parquet | 1,332,484 | (article, kind in book/author, mi) | code/main_study/wiki_led/70_burst_features.py |
| data/db/wiki_led/events.parquet | 983,869 | (work_id, mi) | code/main_study/wiki_led/71_wikidata_events.py |
| data/db/wiki_led/events_long.parquet | 15,070 | one row per dated event or adaptation link | code/main_study/wiki_led/71_wikidata_events.py |
| data/db/wiki_led/events_adaptation_dates.parquet | 6,897 | every P577 and P580 statement of the adaptation items (ad, prop, rank, precision, date) | code/main_study/wiki_led/71_wikidata_events.py |

mi = year*12 + month - 1, origins 2016-03 to 2026-09 (127 months) in both tables. Every feature uses only days up to the last day of the origin month. Burst features cover 7,427 book articles (the 7,747 works in this table share 7,427 distinct articles) and 3,065 author articles. The report script is 72_report_burst_events.py; the summaries are burst_features_summary.json and events_summary.json in the same folder.

Not built, as agreed: same_name and other_r4 (they need the busy REST API). Left missing on purpose: ad_rel_public (a later job fills it from the adaptation article views).

## 2. Burst features

### Definitions as built

- Daily series. Book article: user views of the canonical title plus the redirects kept by the Study 2R screen, exactly the series behind the weekly Test A features (checked: summed by week, they equal the stored weekly views on every one of the compared weeks). Author article: the title itself, no redirects, as in Test A. A day missing from a file counts as 0 views. Share = the day's views divided by the day's total English Wikipedia user views (data/db/interest/wiki/total_daily.parquet).
- Window = the last 28 days of the origin month. Normal = the median daily share of the 182 days just before the window (days 29 to 210 before the month end, counting the month end as day 1); this is the daily version of the Test A normal (median of the 26 weeks before the last 4 weeks). Log ratios use the Test A floor, ln((x + 1e-12) / (normal + 1e-12)).
- pk28: largest day divided by the sum of the last 28 days. dpk: days from the peak to the month end (0 = the peak is on the last day). pre7: ln(mean share of the 7 days before the peak / normal). dec: ln(mean share of up to 7 days after the peak / share on the peak day), missing when the peak is on the last 2 days. hi28: days of the last 28 with share at least 1.5 times normal. rec: ln(largest share in the last 28 days / largest share on any earlier day since 2015-07-01). top500: days of the last 28 on which the article (for books also a kept redirect title) was in the English daily top 500 (data/raw/wiki_top_daily.json). corr28 (books): Pearson correlation of the daily shares of the book and its author article over the last 28 days. co (books): 1 when b_r4 and a_r4 of Test A are both at least ln 1.5, else 0.

### Choices I made (the note leaves them open)

1. Shares or raw views. One rule: shares of total views wherever a level is compared with a baseline or with another article (pre7, dec, hi28, rec, corr28, as the Test A normal implies); raw daily views inside one article's own last 28 days (pk28, dpk and the choice of the peak day). The peak day is the day with most raw views. Over all 1,119,074 article-origin windows with views, the day with the largest share was the same day in 84.3% (they differ mostly for flat, low-traffic windows, where a few views decide the peak), so the choice matters little for real bursts.
2. Ties for the peak go to the latest day (days since the high, as in a "days since 28-day high" rule). With no views at all in the 28 days there is no peak, so pk28, dpk, pre7, dec and rec are missing; hi28 and top500 are 0.
3. top500: wiki_top_daily.json is one dictionary keyed by day (YYYYMMDD) with 500 [title, views] pairs per day and underscores in the titles; it holds 3,915 days from 2016-01-01 to 2026-09-30. 11 days in that range have no list (2017-01-11, 2017-08-12, 2018-07-31, 2019-08-31, 2020-02-14, 2022-04-07, 2022-04-23, 2022-10-26, 2023-05-16, 2023-08-22, 2023-10-02). A day without a list counts as not listed, so the 9 affected origins undercount by at most 2 days; top500_lists gives the number of days with a list in the window (28 on all other origins).
4. corr28 is missing when either raw daily series is constant over the window (shares of two constant series would be correlated only through the common daily total), when the book has no author article series, or when the book and author article are the same page (84 works). Author articles whose title is not a canonical page (the page redirects to a book or another person) have no series of their own and no features, as in Test A.
5. co: Test A stops at origin 2026-07. For 2026-08 and 2026-09 r4 was computed with the identical Test A formula from the weekly files; the same code reproduced the stored r4 on 2026-05 to 2026-07 (book: 22,281 values, largest difference 2.4e-14; author: 9,003 values, largest difference 2.0e-14).
6. Extra helper columns: top500_lists (above) and nrm0 (1 when the normal is zero, so pre7, hi28 and rec rest on the 1e-12 floor, usually a page that did not exist yet).
7. Author articles that are also book article titles (53 titles, a wrong book match that is really the person's page) have burst features here although Test A's weekly author file leaves them out.

### Coverage

| kind | rows | no views in the 28 days (pk28, dpk, pre7, rec missing) | zero normal among rows with views | dec missing | corr28 missing | co missing |
| --- | --- | --- | --- | --- | --- | --- |
| book | 943,229 | 19.0% | 2.4% | 25.8% | 21.5% | 5.8% |
| author | 389,255 | 8.9% | 1.1% | 16.2% | not defined | not defined |

Book articles with no daily file: 0. Author articles with no daily file under their own title: 9 (all-missing rows, kept in the table so the coverage is visible). Almost all of the "no views" rows are origins before the page existed: 97.5% of the book rows and 95.9% of the author rows with no views in the window fall before the article's first day with views.

Share of rows missing, by feature:

| feature | book rows | author rows |
| --- | --- | --- |
| pk28 | 18.97% | 8.86% |
| dpk | 18.97% | 8.86% |
| pre7 | 18.97% | 8.86% |
| dec | 25.85% | 16.24% |
| hi28 | 0.00% | 0.29% |
| rec | 18.97% | 8.86% |
| top500 | 0.00% | 0.29% |
| corr28 | 21.46% | not defined |
| co | 5.84% | not defined |
| top500_lists | 0.00% | 0.29% |
| nrm0 | 0.00% | 0.29% |

### Distributions (rows where the feature exists)

**Book articles**

| feature | rows | p5 | p25 | median | p75 | p95 | p99 | max | share above 0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pk28 | 764,305 | 0.044 | 0.050 | 0.058 | 0.074 | 0.140 | 0.303 | 1.000 | 100.0% |
| dpk | 764,305 | 1.000 | 6.000 | 13.000 | 21.000 | 26.000 | 27.000 | 27.000 | 95.7% |
| pre7 | 764,305 | -0.334 | -0.108 | 0.016 | 0.167 | 0.769 | 10.541 | 18.952 | 53.4% |
| dec | 699,431 | -1.386 | -0.725 | -0.466 | -0.298 | -0.149 | -0.078 | 0.095 | 0.1% |
| hi28 | 943,229 | 0.000 | 0.000 | 1.000 | 3.000 | 14.000 | 28.000 | 28.000 | 50.6% |
| rec | 764,305 | -4.212 | -2.580 | -1.718 | -1.011 | -0.188 | 0.873 | 20.144 | 3.3% |
| top500 | 943,229 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 28.000 | 0.2% |
| corr28 | 740,843 | -0.145 | 0.097 | 0.289 | 0.502 | 0.839 | 0.969 | 1.000 | 85.1% |
| co | 888,111 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 2.7% |
| top500_lists | 943,229 | 27.000 | 28.000 | 28.000 | 28.000 | 28.000 | 28.000 | 28.000 | 100.0% |
| nrm0 | 943,229 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 20.9% |

**Author articles**

| feature | rows | p5 | p25 | median | p75 | p95 | p99 | max | share above 0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pk28 | 354,769 | 0.043 | 0.049 | 0.059 | 0.077 | 0.158 | 0.314 | 1.000 | 100.0% |
| dpk | 354,769 | 1.000 | 6.000 | 14.000 | 21.000 | 27.000 | 27.000 | 27.000 | 95.9% |
| pre7 | 354,769 | -0.313 | -0.097 | 0.023 | 0.179 | 0.815 | 3.595 | 21.459 | 55.0% |
| dec | 326,053 | -1.428 | -0.739 | -0.462 | -0.286 | -0.136 | -0.069 | 0.084 | 0.1% |
| hi28 | 388,112 | 0.000 | 0.000 | 1.000 | 4.000 | 16.000 | 28.000 | 28.000 | 56.4% |
| rec | 354,769 | -4.504 | -2.903 | -1.974 | -1.204 | -0.283 | 0.737 | 18.054 | 2.9% |
| top500 | 388,112 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2.000 | 28.000 | 1.7% |
| top500_lists | 388,112 | 27.000 | 28.000 | 28.000 | 28.000 | 28.000 | 28.000 | 28.000 | 100.0% |
| nrm0 | 388,112 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 9.6% |

### Checks run on the burst features

- Independent check (73_check_burst_features.py): a separate plain-pandas version of every definition, with top500 read from the raw file as text, on 1,020 random article-origin pairs (80 books and 40 authors at 8 origins, plus 60 pairs where top500 is above 0), taken from all parts of the full file: 10,256 values compared, 0 mismatches (largest relative difference 4e-08, the float32 storage; hi28, dpk, top500, top500_lists, nrm0 and co agreed exactly).
- Plausibility against the weekly Test A features at the same origins (rows with views in the window and a non-zero normal; Spearman correlation): books (731,097 rows): hi28 with r4 0.64, pre7 with r4 0.78, hi28 with nrise8 0.53, rec with rmax 0.26; authors (338,532 rows): hi28 with r4 0.69, pre7 with r4 0.79, hi28 with nrise8 0.58, rec with rmax 0.28. They move together without being the same thing (daily against weekly, a 28-day window against 4 weeks, rec against the all-time high instead of the normal).
- Positive controls, known events in the real data. The two deaths should show a one-day spike in the event month. A book with a new series or film is lifted for weeks around the release (trailers, announcements, premieres in other countries), so the month before is already high; the last two columns show it:

| article | event and origin | pk28 | hi28 | rec | top500 | corr28 | hi28 month before | top500 month before |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Toni Morrison (author) | died 5 Aug 2019, origin 2019-08 | 0.40 | 26 | 3.55 | 10 |  | 2 | 0 |
| Philip Roth (author) | died 22 May 2018, origin 2018-05 | 0.58 | 9 | 3.45 | 5 |  | 0 | 0 |
| The Handmaid's Tale (book) | Hulu series from 26 Apr 2017, origin 2017-04 | 0.17 | 26 | -0.20 | 14 | 0.99 | 26 | 7 |
| Dune (novel) (book) | film 22 Oct 2021, origin 2021-10 | 0.11 | 28 | 0.07 | 28 | 0.99 | 28 | 28 |
| Where the Crawdads Sing (book) | film 15 Jul 2022, origin 2022-07 | 0.07 | 28 | -0.19 | 28 | 0.82 | 28 | 12 |
| Normal People (book) | series from 26 Apr 2020, origin 2020-04 | 0.16 | 28 | 1.43 | 8 | 0.98 | 24 | 0 |

## 3. Wikidata events

### What was fetched

Wikidata SPARQL (query.wikidata.org), fetched 2026-10-20 11:14 UTC: 143 queries over the network in batches of up to 300 items, at least 1.5 s apart, 0 back-offs, project user agent from code/config.py, no Wikimedia REST call. Items: 7,510 book items and 3,186 author items for 7,747 works.

- Author: the author of works.author_article where the work has one (so the events belong to the same person as the author page views); for the other works the first P50 author that matches a family name of the Seattle creator string. 7,711 of 7,747 works have an author item. Only this one author is used even when a book has several.
- Death: P570 of the author item; statements of deprecated rank are dropped, a preferred rank wins, then the most precise date, then the earliest.
- Awards: P166 on the book item and on the author item, dated by the qualifier P585. Only dates with month precision or finer can be placed in a month; year-only dates are kept in events_long.parquet (mi_event missing) and not used in the flags.
- Adaptations: items linked to the book item by P144 (queried again to get P577 and P580 with their precision), by P4969, and the pairs of the existing adaptations.parquet. For each adaptation item: all P31 types, a class group (film, tv or other, by P31/P279* to film, television series, television programme, season, episode or web series), the English article title and all P577/P580 dates. The release date is the earliest P577 or P580 date with month precision or finer among the best-rank statements (a preferred rank wins over normal ones, as in Wikidata's own truthy statements; deprecated statements are dropped, which is how Wikidata marks rescheduled dates: the postponed film Dune: Part Two keeps its old 2023 dates as deprecated statements, so its release is taken as February 2024); later regional dates are not used. Only film and tv adaptations feed ad_rel; other types (plays, video games, comics, novels, music) are kept in events_long.parquet only.

| Adaptation links | Count |
| --- | --- |
| book-adaptation pairs (union of both sources) | 4,351 |
| found by P144 in the new query | 4,329 |
| found by P4969 | 2,919 |
| found only through P4969 (new compared with P144) | 22 |
| in the existing adaptations.parquet | 4,329 |
| in the existing file but not found now | 0 |
| books with at least one adaptation | 1,620 |
| distinct adaptation items | 4,266 |
| of which film, tv, other | 2,501, 695, 1,070 |
| with an English Wikipedia article | 3,193 |
| with a release date at month precision or finer | 2,189 |
| without a usable month (year-only or no date) | 2,077 |
| P577 and P580 date statements of the adaptation items (events_adaptation_dates.parquet) | 6,897 |
| of which deprecated (rescheduled dates, dropped) | 24 |

| Death and award dates | Count |
| --- | --- |
| authors with a usable death date (month or finer) | 773 |
| authors with a death date at year precision only | 13 |
| authors with conflicting death dates | 3 |
| P166 award statements (book and author items, no deprecated rank) | 11,646 |
| undated (no P585) | 1,684 |
| dated at month precision or finer (used) | 481 |
| dated at year precision only (not used) | 9,481 |

The award flag is sparse because most P585 dates are year-only: 9,481 of 9,962 dated award statements (95.2%) cannot be placed in a month. That group holds the Hugo, Newbery, National Book Award, Pulitzer and Booker prizes (second table below); the month-precision group (first table) is mostly honorary degrees, orders and fellowships, plus the Nebula Award for Best Novel.

| Most frequent awards with a month-precision date (used) | Statements |
| --- | --- |
| honorary doctorate (Q11415564) | 31 |
| Nebula Award for Best Novel (Q266012) | 31 |
| MacArthur Fellows Program (Q1543268) | 13 |
| The New Vanguard (Q50376726) | 10 |
| Commandeur des Arts et des Lettres (Q13452531) | 9 |
| Presidential Medal of Freedom (Q17144) | 9 |
| honorary doctor of the University of Miami (Q110471679) | 8 |
| Academy Award for Best Original Song (Q112243) | 6 |
| Knight of the Legion of Honour (Q10855271) | 6 |
| Academy Award for Best Writing, Adapted Screenplay (Q107258) | 6 |
| star on Hollywood Walk of Fame (Q17985761) | 5 |
| Commander of the Order of the British Empire (Q12201477) | 5 |

| Most frequent awards with a year-only date (not used) | Statements |
| --- | --- |
| Guggenheim Fellowship (Q1316544) | 208 |
| Fellow of the Royal Society of Literature (Q39477935) | 112 |
| Hugo Award for Best Novel (Q255032) | 109 |
| Newbery Medal (Q622813) | 105 |
| National Book Award (Q572316) | 97 |
| Pulitzer Prize for Fiction (Q833633) | 92 |
| Caldecott Medal (Q1026417) | 92 |
| Booker Prize (Q160082) | 78 |
| Locus Award for Best Fantasy Novel (Q607354) | 67 |
| Locus Award for Best Science Fiction Novel (Q2576795) | 67 |
| Anisfield-Wolf Book Awards (Q4765305) | 56 |
| Time 100 (Q604370) | 53 |

| Most frequent P31 types of the adaptation items (an item can have several) | Items |
| --- | --- |
| film (Q11424) | 1872 |
| television series (Q5398426) | 399 |
| television film (Q506240) | 379 |
| literary work (Q7725634) | 291 |
| dramatico-musical work (Q58483083) | 241 |
| miniseries (Q1259759) | 239 |
| animated film (Q202866) | 107 |
| television series episode (Q21191270) | 70 |
| short film (Q24862) | 66 |
| video game (Q7889) | 62 |
| television series season (Q3464665) | 57 |
| painting (Q3305213) | 55 |
| animated television series (Q117467246) | 39 |
| musical work/composition (Q105543609) | 36 |
| film project (Q18011172) | 35 |
| animated short film (Q17517379) | 35 |
| theatrical production (Q7777570) | 33 |
| written work (Q47461344) | 30 |
| anime television series (Q63952888) | 28 |
| radio drama (Q2635894) | 27 |
| performing arts production (Q43099500) | 27 |
| ballet (Q15079786) | 22 |
| television program (Q15416) | 16 |
| version, edition or translation (Q3331189) | 16 |
| comic book series (Q14406742) | 14 |

Cross-check with the library catalogue: 568 works have a death year in the Seattle creator string and an author item here; Wikidata has a death date for 567 of them, and the year agrees for 567 (100.0%). Authors the catalogue says are dead but Wikidata has no usable death date for: 1 works.

### Events by type and year

| Event | before 2015 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| author deaths (distinct authors, month or finer) | 548 | 17 | 19 | 17 | 19 | 21 | 21 | 15 | 18 | 20 | 25 | 18 | 15 | 773 |
| dated awards of books (month or finer) | 26 | 1 | 1 | 1 | 12 | 2 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 48 |
| dated awards of authors (month or finer) | 292 | 11 | 8 | 15 | 15 | 22 | 11 | 9 | 16 | 8 | 12 | 11 | 3 | 433 |
| film adaptations, first release (book-adaptation pairs) | 1,128 | 31 | 43 | 38 | 36 | 33 | 27 | 23 | 35 | 37 | 34 | 31 | 27 | 1,528 |
| tv adaptations, first release (pairs) | 300 | 18 | 17 | 25 | 30 | 20 | 34 | 22 | 37 | 26 | 36 | 23 | 12 | 601 |
| other adaptation types, first release (pairs, not used) | 81 | 0 | 5 | 9 | 2 | 4 | 2 | 5 | 6 | 5 | 1 | 1 | 2 | 123 |
| awards of books dated by year only (not used) | 770 | 39 | 41 | 44 | 52 | 43 | 50 | 50 | 41 | 28 | 24 | 11 | 8 | 1,201 |
| awards of authors dated by year only (not used) | 6,075 | 248 | 222 | 250 | 281 | 200 | 176 | 189 | 179 | 140 | 136 | 96 | 59 | 8,251 |
| film and tv adaptations with a year but no month (not used) | 935 | 12 | 8 | 7 | 10 | 6 | 7 | 8 | 7 | 6 | 3 | 3 | 1 | 1,015 |

Years are the year of the event date. 2026 is partial.

### The per-work, per-month table (events.parquet)

| Column | Share of rows = 1 | Rows = 1 |
| --- | --- | --- |
| died (author died in t or t-1) | 0.106% | 1,043 |
| award (dated award of book or author in t or t-1) | 0.061% | 597 |
| ad_rel (film or tv release in t-1, t or t+1) | 0.203% | 1,995 |
| any of the three | 0.369% | 3,631 |

months_since_event (capped at 24): median 24, share at the cap 96.4%; 5th and 25th percentile 24 and 24. ad_rel_public is missing in all 983,869 rows, as agreed. Works: 7,747; works with at least one died, award or ad_rel month: 1,293.

### Positive controls for the events

| Case | Event | Flag in the months around it | Meaning |
| --- | --- | --- | --- |
| Toni Morrison (author, 13 works) | died 2019-08, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 |
| Philip Roth (author, 6 works) | died 2018-05, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 |
| Ursula K. Le Guin (author, 20 works) | died 2018-01, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 |
| Elie Wiesel (author, 1 work) | died 2016-07, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 |
| The Handmaid's Tale (book) | release near 2017-04; film and tv release months on Wikidata: 1990-02, 2017-04 | 0 / 0 / 1 / 1 / 1 / 0 / 0 | ad_rel at 3 months before to 3 months after the release month |
| Dune (novel) (book) | release near 2021-10; film and tv release months on Wikidata: 1984-12, 2000-12, 2021-09, 2024-02 | 0 / 1 / 1 / 1 / 0 / 0 / 0 | ad_rel at 3 months before to 3 months after the release month |
| Where the Crawdads Sing (book) | release near 2022-07; film and tv release months on Wikidata: 2022-07 | 0 / 0 / 1 / 1 / 1 / 0 / 0 | ad_rel at 3 months before to 3 months after the release month |
| Normal People (book) | release near 2020-04; film and tv release months on Wikidata: 2020-04 | 0 / 0 / 1 / 1 / 1 / 0 / 0 | ad_rel at 3 months before to 3 months after the release month |
| The Queen's Gambit (novel) (book) | release near 2020-10; film and tv release months on Wikidata: 2020-10 | 0 / 0 / 1 / 1 / 1 / 0 / 0 | ad_rel at 3 months before to 3 months after the release month |
| Stella Prize (author award; e.g. "The weekend", 3 work(s)) | dated 2016-04-19, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 unless another award is near |
| Deutscher Memorial Prize (author award; e.g. "Slow Down: The Degrowth Manife", 1 work(s)) | dated 2018-11-01, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 unless another award is near |
| Queen Elizabeth II Platinum Jubilee Medal (author award; e.g. "Spare", 2 work(s)) | dated 2022-02-06, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 unless another award is near |
| International Booker Prize (book award; e.g. "Taiwan Travelogue", 1 work(s)) | dated 2026-05-19, flags at t-1 / t / t+1 / t+2 | 0 / 1 / 1 / 0 | expected 0 / 1 / 1 / 0 unless another award is near |

## 4. Runtime, memory and load

| Script | Run time | Peak memory | Notes |
| --- | --- | --- | --- |
| 70_burst_features.py | 21 s | 769 MB | one process, articles in chunks of 400; run with nice -n 10 through jobs/bg.sh (job wl_burst) |
| 71_wikidata_events.py | 258 s | 246 MB | 143 queries (172 s of query time), run with nice -n 10 through jobs/bg.sh (job wl_events) |

Both full runs were started only after a test on 50 articles (burst features) and about 50 items (events). The independent check (73) took about 90 s and the report (72) a few seconds. No Wikimedia REST call was made by any of these scripts; Wikidata queries ran one at a time with at least 1.5 s between them and no back-off was needed.

## 5. How to join the tables to the Test A rows

- Burst features, book part: rows with kind == "book", merge on (article, mi) with the work's article (prefix b_). Author part: rows with kind == "author", merge on (author_article = article, mi) (prefix a_). mi is the Test A origin month (year*12 + month - 1). Test A rows stop at origin 2026-07; both new tables go to 2026-09.
- Events: merge on (work_id, mi). The columns died, award, ad_rel and months_since_event have no missing values; ad_rel_public is missing everywhere for now.

## 6. Cautions for whoever uses the tables

- Rows with no views in the window have missing shape features, not zeros (the page did not exist yet in almost all cases). Trees handle this; ridge models need the missing-value flags Test A already uses.
- 2025-05 and 2025-06: Wikimedia later found that part of the unusual "human" traffic was bots, so burst features for those months (pk28, hi28, rec, top500 and the shares behind them) are noisier. They are not corrected here.
- The adaptation release date is the first dated release among the best-rank Wikidata statements (a festival premiere can be the first date); about half of the adaptation items (2,077 of 4,266) have only a year or no date, so ad_rel covers only part of all adaptations; for film and tv adaptations whose first date is in 2016 or later, 90.6% of the 720 book-adaptation pairs have a month.
- The award flag has few positives (month-precision dates only) and misses most of the big literary prizes (Pulitzer, Booker, National Book Award, Hugo, Newbery), whose dates are year-only on Wikidata. A calendar of announcement months for the ten or twenty biggest prizes would add them; I did not add one because it would be my own input, not Wikidata data.
- events.parquet uses only dates up to the end of the origin month for died, award and months_since_event. ad_rel looks one month ahead (release in t+1); a later job must set ad_rel_public so that such a row is used only when the adaptation article already had views before the end of t.
- For the placebo "event dates moved 12 months later", move events_long.parquet mi_event by 12 and rebuild the flags with the same rules.

