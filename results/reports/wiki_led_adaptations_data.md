# Adaptation pages: data build and 5-title test (Wikipedia signal from the film and TV adaptations of a book)

Written 2026-10-20. Code: code/main_study/wiki_led/50_adaptation_views.py (screen the pages, download daily views) and 51_adaptation_features.py (features by origin month). Settings: prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json, change 5. Data only: no model was fitted and no feature was related to loans. The full download has not been run yet (section 4). The publication-date column of data/db/wiki_led/adaptations.parquet is not read by either script.

## 1. What was built

- **50_adaptation_views.py**, stage 1 (screen): looks up every distinct adaptation page in the English Wikipedia Action API (batches of 50, pageprops and redirects), drops the pages that are not specific to the adaptation (a disambiguation page, a redirect to the book's own article, or the book's own article), and writes adaptation_pairs.parquet (one row per book and page, with keep and reason) and adaptation_pages.parquet (one row per page, with the kind of adaptation and flags).
- **50_adaptation_views.py**, stage 2 (download): daily user views 2015-07-01 to 2026-09-30 (REST per-article, all-access, agent user) for the kept pages, through the Http class of _common.py (cache on disk, project user agent, gap 0.30 s, 4 threads, Retry-After honoured, the gap grows 30% after a 429 and shrinks again). Output: adaptation_daily_views.parquet (article, date, views), adaptation_fetch_status.parquet and adaptation_views_summary.json. A 404 means no views in the period. The script refuses to start while wiki_led_views is running (before any request), unless --force; with --offline it uses the cache only.
- **51_adaptation_features.py**: weekly sums (Monday to Sunday) divided by the weekly English Wikipedia totals exactly as in study2r/04_weekly_series.py, the nine page features of article_features in 10_test_a.py at every origin month 2016-03 to 2026-09 (mi = year*12 + month - 1, weeks that ended on or before the last day of the origin month), then the per-work columns below. Output: adaptation_features.parquet (work_id, mi, ad_*), adaptation_page_features.parquet (article, mi, the nine features, has_data, age_weeks, first_week, left_censored) and adaptation_features_summary.json. With --test both scripts read and write the *_test files.

Columns of adaptation_features.parquet (per work and origin month, over the kept adaptation pages of the work's book that have data at that origin):

| Column | Meaning |
| --- | --- |
| ad_n | number of adaptation pages with data (the first week with views ended on or before the origin month's end); 0 when none |
| ad_r4 | maximum of r4 |
| ad_rmax | maximum of rmax |
| ad_run | maximum of run |
| ad_dw | sum of dw |
| ad_lvl4 | maximum of lvl4 |
| ad_new_weeks | weeks from the first week with views of the newest page to the last week used at the origin (the "new adaptation" signal) |

All columns except ad_n are missing when ad_n is 0. ad_new_weeks ignores pages that already had views in the first week of the data (2015-06-29): their age is unknown, so it is also missing when all pages with data are of that kind. Every work with at least one kept page has a row for each of the 127 origin months; works without a kept page are not in the table (treat them as ad_n = 0). Several works can share one book (196 books have more than one work in works.parquet); they get the same values.

## 2. Counts from the screen (run on 2026-10-20)

| Item | Count |
| --- | ---: |
| Books with at least one adaptation item in Wikidata | 1,615 |
| Adaptation items | 4,247 |
| Distinct English Wikipedia pages of those items | 3,178 |
| Books with at least one such page | 1,409 |
| Works (works.parquet) of those books | 1,470 |
| Pairs of book and page | 3,233 |
| **Pages excluded** | **17** |
| of which disambiguation pages | 0 |
| of which redirects to the book's own article | 16 |
| of which the book's own article itself | 1 |
| **Pages kept (to download)** | **3,161** |
| Books with at least one kept page | 1,400 |
| **Works with at least one kept page** | **1,461** (the exclusions remove 9 works) |

The rule: a page is excluded for a book when, after following any redirect, it is a disambiguation page (pageprops), or when the title is a redirect to the book's own article (the target has the book's Wikidata item, or is the book's English article in works.parquet), or when the title is the book's own article. No page failed on more than one reason. There are no disambiguation pages among the 3,178 pages. The same call finds them (the author-name lookups of Test B flagged 4,017 with it), so zero is a result here: Wikidata does not allow a disambiguation page to be linked from a normal item. Nine books lose their only page. The 17 excluded pages:

| Page | The book's own article | Where the title leads | Reason |
| --- | --- | --- | --- |
| Americanah (miniseries) | Americanah | Americanah (section: Adaptations) | redirect_to_book |
| Artemis Fowl: The Graphic Novel | Artemis Fowl (novel) | Artemis Fowl (novel) (section: Adaptations) | redirect_to_book |
| Black Coffee (novel) | Black Coffee (play) | Black Coffee (play) | redirect_to_book |
| Coraline (2025 musical) | Coraline | Coraline (section: 2025 musical) | redirect_to_book |
| Death on the Nile (2004 film) | Death on the Nile | Death on the Nile (section: Agatha Christie's Poirot) | redirect_to_book |
| Harry Potter and the Cursed Child | Harry Potter and the Cursed Child | none, it is the same page | same_as_book |
| Kane & Abel (miniseries) | Kane and Abel (novel) | Kane and Abel (novel) (section: Adaptations) | redirect_to_book |
| Oh, the Places You'll Go! (film) | Oh, the Places You'll Go! | Oh, the Places You'll Go! (section: Film adaptation) | redirect_to_book |
| Pretty Things (TV series) | Pretty Things (novel) | Pretty Things (novel) | redirect_to_book |
| The Cricket in Times Square (TV special) | The Cricket in Times Square | The Cricket in Times Square | redirect_to_book |
| The Deep Blue Good-by (film) | The Deep Blue Good-by | The Deep Blue Good-by (section: Film adaptation) | redirect_to_book |
| The Glass Fortress (film) | We (novel) | We (novel) (section: Films) | redirect_to_book |
| The Man Who Fell to Earth (1987 film) | The Man Who Fell to Earth (novel) | The Man Who Fell to Earth (novel) (section: Adaptations) | redirect_to_book |
| The Mist (video game) | The Mist (novella) | The Mist (novella) (section: Games) | redirect_to_book |
| The Mystery of the Blue Train (film) | The Mystery of the Blue Train | The Mystery of the Blue Train | redirect_to_book |
| The Seven Husbands of Evelyn Hugo (film) | The Seven Husbands of Evelyn Hugo | The Seven Husbands of Evelyn Hugo (section: Film adaptation) | redirect_to_book |
| Tilting at windmills | Don Quixote | Don Quixote (section: Tilting at windmills) | redirect_to_book |

Most of the 16 redirects lead to a section of the book's article (Adaptations, Film adaptation, Films), so their views are views of the book. One page (Harry Potter and the Cursed Child) is one article that covers both the play and the published script, and works.parquet gives that article to the book.

Kept but flagged: 16 pages are redirects to a page that is not the book's own article. The rule does not exclude them, so they are kept. The download asks for the views of the title itself, which are the visits that came through that title. Their targets are mostly studio, filmography or list pages, so the targets' own views would not describe the adaptation, and the flag redirect_other in adaptation_pages.parquet lets them be dropped later.

| Page (redirect) | Leads to |
| --- | --- |
| A Question of Blood (Rebus) | Rebus (2000 TV series) |
| A Quintmas Carol | Mark Atkinson (actor) (section: Kahuna Productions) |
| Alice's Adventures in Wonderland Retold in Words of One Syllable | Works based on Alice in Wonderland (section: Literary retellings and sequels) |
| An Easter Carol | List of VeggieTales videos (section: ep20) |
| Black Beauty (1987 film) | Burbank Animation Studios |
| Dirk (play) | James Goss (producer) (section: Theatre) |
| Heidi (1995 film) | Jetlag Productions (section: Literary novel adaptations) |
| Patience (After Sebald) | W. G. Sebald (section: Patience (After Sebald)) |
| Royal Cat Nap | Tom and Jerry filmography (section: 1958) |
| The Mortal Instruments: City of Ashes (unproduced film) | The Mortal Instruments: City of Bones (section: Canceled sequels) |
| The Patio: A Bad Parody to a Bad Movie | Mark Atkinson (actor) (section: Kahuna Productions) |
| The Wonderful Wizard of Ha's | List of VeggieTales videos (section: ep30) |
| Tom and Chérie | Tom and Jerry filmography (section: 1955) |
| Tom and Jerry & the Wizard of Oz | List of Tom and Jerry feature films (section: Tom and Jerry & the Wizard of Oz) |
| Toto (film) | Toto: The Dog-Gone Amazing Story of the Wizard of Oz (section: Film adaptation) |
| Touché, Pussy Cat! | Tom and Jerry filmography (section: 1954) |

Other facts about the 3,161 kept pages:

- 47 pages are linked to more than one book (a series or a box set), up to 3 books. Each of those books gets the full attention of the page, not a share.
- Pages per work: 1,010 works have 1 page, 199 have 2, 140 have 3 to 5 and 112 have 6 or more (most: 66). Median 1, mean 2.49.
- The pages are not all film and television. The most frequent kinds in Wikidata (a page with two kinds counts in both):

| Kind (Wikidata P31) | Pages |
| --- | ---: |
| film | 1,703 |
| television series | 350 |
| television film | 259 |
| miniseries | 200 |
| dramatico-musical work | 168 |
| literary work | 115 |
| animated film | 88 |
| short film | 47 |
| video game | 47 |
| animated television series | 34 |
| television series episode | 29 |
| anime television series | 25 |

  Grouped by label (any kind whose English label contains film, television, miniseries or anime), 2,694 kept pages are film or television and 467 are other kinds (mostly stage works 164, literary works 109 and video games 47); 1,416 works have at least one film or television page. No filter by kind was applied. The kinds are in the columns classes and class_labels of adaptation_pages.parquet. Six pages have no kind.
- 16 kept pages lead (after a redirect) to a page whose Wikidata item is not the adaptation's item: these are the redirects flagged above. For all others the page's item is the adaptation item.

Requests made to build the screen: 92 Action API batches, 3 Wikidata label requests (the English names of the kinds) and 3 answers with status 429, retried after the pause (one pause of about 70 seconds). Everything is in the cache, so a rerun of the screen makes no request.

## 3. Test on 5 titles

The titles were chosen to cover two books and pages of different age: four pages of Dune (three works in works.parquet share that book) and one of The Lincoln Lawyer. Download: 5 requests, all status 200, 3 seconds, 16,312 daily rows, no 404.

| Page | Days with views | First day with views | Views in the period | First week with views | Already viewed in the first week of the data |
| --- | ---: | --- | ---: | --- | --- |
| Dune (1984 film) | 4,099 | 2015-07-01 | 9,337,646 | 2015-06-29 | yes |
| Dune (2021 film) | 2,187 | 2020-10-05 | 38,034,093 | 2020-10-05 | no |
| Dune: Part Two | 1,806 | 2021-10-14 | 20,670,103 | 2021-10-11 | no |
| Frank Herbert's Dune | 4,110 | 2015-07-01 | 2,711,706 | 2015-06-29 | yes |
| The Lincoln Lawyer (film) | 4,110 | 2015-07-01 | 7,579,907 | 2015-06-29 | yes |

51_adaptation_features.py on these pages gives 508 rows for 4 works and 127 origin months (2016-03 to 2026-09) in adaptation_features_test.parquet, and 635 page rows. Checks, all passed:

1. The copy of article_features is compared with the function read from the source text of 10_test_a.py on up to 12 pages at every run, exactly (no difference).
2. The weekly table made from daily views is identical to study2r/weekly_book.parquet (weeks, views, valid; share difference 0) on 12 book articles that have no added redirects.
3. The features computed from those 12 articles' daily views equal the stored Test A features (test_a_wiki_features.parquet) for every origin they have in common (largest difference 0).
4. The per-work columns, recomputed from the page-level table with a different code path (a pandas group-by), agree with the script on all 508 rows (largest difference 1.4e-14, in ad_dw).
5. No look-ahead. Multiplying the views after 2021-09-30 by 100 leaves the features of every origin up to 2021-09 unchanged. Multiplying the views of 2021-09-27 to 2021-09-30 (inside the week that ends 2021-10-03) by 1000 leaves origin 2021-09 unchanged and changes origin 2021-10. The week that ends on a Sunday that is the last day of a month (2021-10-31) is used at that origin. Origin 2026-09 does not use the partial last week (2026-09-28 to 09-30).
6. A page whose first views fall on Tuesday 2021-09-28 has no data at origin 2021-09 and has data from origin 2021-10. A page with views only in 2026-09-29 never has data. A page with views on 2015-07-01 has data at every origin and counts as already viewed in the first week.
7. The download stage run on 600 fake answers (36 with status 404, 11 with 400, no network): every page requested once, 404 and 400 pages are in adaptation_fetch_status.parquet and absent from the daily file, row groups of 250 pages, view sums equal the fake data.
8. The screen rule and the answer parser were run on crafted answers (normal page, redirect with a section, disambiguation page, missing page, redirect to a disambiguation page, double redirect, normalised title, other namespace, invalid title): all as expected.
9. Size test of 51_adaptation_features.py on synthetic daily views of all 3,161 kept pages: 185,547 work-month rows (1,461 works times 127 origins), 14 seconds, peak memory 0.49 GB.

How the features behave, for the work "Dune" (work 13343; the pages are the 1984 film, the 2000 miniseries, the 2021 film and Dune: Part Two):

| Origin | ad_n | ad_r4 | ad_rmax | ad_run | ad_dw | ad_lvl4 | ad_new_weeks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016-03 | 2 | 0.02 | 0.11 | 0 | 0.0 | -13.37 | missing |
| 2020-09 | 2 | 1.65 | 2.56 | 3 | 3.9 | -9.87 | missing |
| 2020-10 | 3 | 16.91 | 17.48 | 3 | 29.6 | -10.72 | 2 |
| 2021-09 | 3 | 1.88 | 2.14 | 10 | 26.7 | -8.41 | 50 |
| 2021-10 | 4 | 14.71 | 16.10 | 15 | 61.9 | -7.07 | 2 |
| 2022-06 | 4 | 0.68 | 0.93 | 8 | 4.3 | -9.95 | 36 |
| 2024-02 | 4 | 1.62 | 2.16 | 5 | 14.9 | -8.72 | 123 |
| 2024-03 | 4 | 2.97 | 3.56 | 10 | 64.4 | -7.39 | 128 |
| 2026-09 | 4 | 0.00 | 0.16 | 0 | 2.2 | -10.70 | 258 |

For "The Lincoln Lawyer" (work 13339, one page: the 2011 film; the television series came out on 2022-05-13 and is not in this 5-title test):

| Origin | ad_n | ad_r4 | ad_rmax | ad_run | ad_dw | ad_lvl4 | ad_new_weeks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-04 | 1 | 0.18 | 0.41 | 0 | 0.4 | -12.17 | missing |
| 2022-05 | 1 | 2.91 | 3.47 | 3 | 5.2 | -9.51 | missing |
| 2022-06 | 1 | 2.52 | 2.98 | 7 | 14.3 | -9.90 | missing |
| 2022-07 | 1 | 1.03 | 1.56 | 12 | 11.7 | -11.01 | missing |
| 2026-09 | 1 | 0.20 | 0.22 | 0 | 0.0 | -11.87 | missing |

Things to know before using the columns:

- **A new page looks like a very large rise.** Weeks before a page has views are 0 and the normal is floored at 1e-12, so r4 and rmax of a page in its first weeks are about +17 on the log scale (Dune 2021 film, origin 2020-10). The same happens for book articles created late in Test A. In the first months ad_r4, ad_rmax and ad_dw of a work are therefore a new-page marker as much as a rise; ad_new_weeks says how old the newest page is, and adaptation_page_features.parquet allows a version that ignores pages younger than 30 weeks.
- **Views before a page move stay under the old title.** The Dune 2021 page has views only from 2020-10-05 although the film was announced years before; the likely reason is a move of the page to this title (not checked, no further request was allowed). Such a page starts at its move, so it looks new then. Redirects with traffic are not added, unlike the book articles of study2r.
- Three of the five test pages (and, in the synthetic size test, 40% by construction) already had views in the first week of the data; for them the age is unknown.

## 4. Full download: command and time

The 3,161 kept pages need 3,161 REST requests, 5 of them already in the cache, so 3,156 requests. At 3 requests a second that is 1,052 seconds, about 17.5 minutes (16 minutes at the script's gap of 0.30 s, about 3.3 a second; about 26 minutes at the 2 a second that wiki_led_views managed in its last half hour, when the gateway answered 429). Disk: about 24 KB of cache per page (under 80 MB) and about 60 MB for the daily file (about 10 million rows).

Run from handoff/code, only when wiki_led_views has stopped (the script refuses to start otherwise):

    nice -n 10 bash ../jobs/bg.sh wiki_led_adapt_views main_study/wiki_led/50_adaptation_views.py

Log: data/reports/wiki_led_adapt_views.log (every 250 pages). A rerun after any stop continues from the cache. When it has ended (the log ends with a JSON summary; adaptation_views_summary.json), run the features (no network, about 20 seconds, under 0.6 GB):

    nice -n 10 ../.venv/bin/python main_study/wiki_led/51_adaptation_features.py
