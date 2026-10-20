# Test B (new books): data for the Wikipedia-led test

Built 20 Oct 2026 from the settings fixed in `prereg/wiki_led_settings_2026-10-20.json`, section `test_B_new_books`. This file reports counts and match rates only. No model was fitted and no Wikipedia feature was related to loans.

Code: `code/main_study/wiki_led/` (`01_population.py`, `01b_loans_library.py`, `02_author_match.py`, `03_author_views.py`, `04_rows.py`, `05_report.py`, `06_checks.py`). Data: `data/db/wiki_led/` (`test_b_population`, `test_b_loans_library`, `author_match`, `wikidata_items`, `author_monthly_views`, `test_b_rows`). HTTP cache: `data/interim/wiki_led_cache/`.

## 1. Population

Works in `spl_works.parquet`: 1,013,659. First Seattle month 2017-01 to 2026-02: 266,253. With a publication year: 241,189. New releases (publication year at least the year of the first month minus 1): **194,741** (the figure in the record), with 91,885 distinct `creator_key`.

Of these, 1,945 works have an empty creator string, so no name parses and they are dropped. For the remaining **192,796** works `parse_author` returned a name every time: **0 further parse failures**. Population: **192,796 works**, 91,885 distinct `creator_key` (the record's 'about 92,000'), 94,249 distinct first-author display names. Two works have a non-empty creator string but an empty `creator_key` ('Mrs. & Mr. MacLeod'); in the rows file their `creator_key` is set to `__nokey_<work_id>` so that they do not form one cluster with the other empty keys, and their library features are 0. 3,336 population works have a creator taken from the title statement only (`creator_from_title_only`); they are kept, as the record does not exclude them.

| test year | works before dropping | empty creator, dropped | works | distinct names |
| --- | --- | --- | --- | --- |
| 2017 | 21757 | 274 | 21,483 | 16483 |
| 2018 | 21438 | 241 | 21,197 | 16454 |
| 2019 | 20741 | 274 | 20,467 | 16071 |
| 2020 | 15424 | 93 | 15,331 | 11754 |
| 2021 | 22644 | 230 | 22,414 | 16891 |
| 2022 | 22031 | 222 | 21,809 | 16806 |
| 2023 | 22007 | 228 | 21,779 | 17003 |
| 2024 | 21235 | 153 | 21,082 | 16489 |
| 2025 | 23717 | 207 | 23,510 | 17692 |
| 2026 | 3747 | 23 | 3,724 | 3287 |

Test year = calendar year of `first_ym`. 2026 holds the months 2026-01 and 2026-02 only.

## 2. Outcome and library features

Monthly checkouts of all three formats come from the record-level files (25,791,712 book, 9,685,032 ebook, 4,697,512 audiobook rows; rows without a work: 0). `loans6` = loans in months `first_ym` to `first_ym`+5, `Y6` = ln(1 + loans6). Every population work has a row in its first month, none has a row before it, and none has `loans6` = 0. Library features follow the record: earlier works of the same `creator_key` in all of `spl_works`, and ln(1 + their loans before the work's first month). Checked against a plain-pandas recomputation from the raw rows (`06_checks.py`) for 70 works (60 random, 10 of the three most prolific creators): 0 differences in `loans6`, `n_prior_works` and `prior_loans`.

Library-wide low months (the benchmark rule: the total of a format below half of its median over the previous 12 months), 2017-01 onward: 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2024-05, 2024-06, 2024-07, 2025-08. The record does not exclude months for Test B, so no row was dropped or changed. `flag_months6` in the rows file counts, per work, how many of its six outcome months are such months: **36,328 works** (18.8%) have at least one. These windows (2020 closures, the 2024 outage, 2025-08) lower `loans6` for reasons unrelated to the book; the model script may want to check its results with and without them.

## 3. Author matching (English Wikipedia and Wikidata)

94,249 distinct display names; 43 of them cannot be a page title (they contain # < > [ ] | { } or are too long) and were not queried. Wikipedia batches of 50 via `prop=pageprops&redirects=1&maxlag=5`, Wikidata `wbgetentities` (50 per call, claims). 29,393 Wikidata items were read. Network requests: 6,433; cache hits during that run: 0; back-offs: 6.

**By distinct name:** matched to a human article **28,922 of 94,249 (30.7%)**; with a writer occupation **19,590 (20.8% of all names, 67.7% of the matches)**.

Which title was accepted: plain 27,828; writer 580; author 431; novelist 83; no title accepted 65,327.

Status of the plain-name title for all names: missing 61,045; human 27,828; disambiguation 4,017; not_human 1,314; invalid_title 43; no_item 1; invalid 1. ("human" = accepted at once; "missing" = no page; "disambiguation"; "not_human" = page exists but its Wikidata item is not P31 = Q5; "no_item" = page without a Wikidata item.)

**By work and year** (a work counts when its first author matched; a name that appears in several years counts in each):

| test_year | works | works matched, any human | works matched, writer_type | names matched |
| --- | --- | --- | --- | --- |
| 2017 | 21,483 | 9,331 (43.4%) | 7,539 (35.1%) | 6,707 / 16,483 (40.7%) |
| 2018 | 21,197 | 8,768 (41.4%) | 6,946 (32.8%) | 6,464 / 16,454 (39.3%) |
| 2019 | 20,467 | 8,449 (41.3%) | 6,680 (32.6%) | 6,285 / 16,071 (39.1%) |
| 2020 | 15,331 | 7,131 (46.5%) | 5,903 (38.5%) | 5,227 / 11,754 (44.5%) |
| 2021 | 22,414 | 9,023 (40.3%) | 7,191 (32.1%) | 6,445 / 16,891 (38.2%) |
| 2022 | 21,809 | 8,486 (38.9%) | 6,660 (30.5%) | 6,150 / 16,806 (36.6%) |
| 2023 | 21,779 | 7,985 (36.7%) | 6,204 (28.5%) | 5,876 / 17,003 (34.6%) |
| 2024 | 21,082 | 7,425 (35.2%) | 5,768 (27.4%) | 5,483 / 16,489 (33.3%) |
| 2025 | 23,510 | 8,345 (35.5%) | 6,543 (27.8%) | 5,766 / 17,692 (32.6%) |
| 2026 | 3,724 | 1,337 (35.9%) | 1,051 (28.2%) | 1,140 / 3,287 (34.7%) |
| all | 192,796 | 76,280 (39.6%) | 60,485 (31.4%) | 28,922 / 94,249 (30.7%) |

## 4. Monthly views

Accepted articles (distinct titles after redirects): 28,155. REST per-article monthly, all-access, user agents, 2015-07 to 2026-09. **Titles with views data: 28,146**; titles with a 404 (no views at all, nothing stored): **9**; rejected with status 400: 0. 3,199,095 title-month rows.

Download behaviour. The job was started and restarted 8 times while the request rate was tuned (every finished title stays in the cache, none is fetched twice). Settings of the runs: `defaults (6 threads, 0.11 s gap)`; `defaults (6 threads, 0.11 s gap)`; `--gap 0.3 --threads 4`; `--gap 0.0067 --threads 24`; `--gap 0.00667 --threads 24`; `--gap 0.125 --threads 8`; `--gap 0.30 --threads 4 --recover`; `--gap 0.30 --threads 4 --recover`. At about 150 requests per second (24 threads) and again at 8 per second the Wikimedia gateway answered 429 (header x-envoy-ratelimited, Retry-After 6 to 7 s) and the rate fell to 1 to 2 per second; a run at 0.30 s gap with 4 threads (3.3 per second) drew almost none. Counts from the logs: 25,124 requests logged, response codes {200: 25089, 404: 8, 429: 27, 'ConnectionError': 2}, 6 separate slow-down episodes after a 429 (lower bounds for the runs that were stopped by hand, as the counters are printed every 500 titles). All 429s were honoured with the server's Retry-After pause and nothing was lost. The last run (gap 0.30 s, 4 threads, slow-down after a 429 and recovery after a run of successes) made 15,446 requests, 12,710 answered from the cache, 1 back-off.

## 5. Rows

`data/db/wiki_led/test_b_rows.parquet`: **192,796 rows**, one per work. Wikipedia features use only months strictly before `first_ym` (the 12 months ending the month before). Recomputed independently from the long views file for 450 rows (`06_checks.py`): 0 differences; unmatched rows with a non-zero Wikipedia feature: 0; matched rows without a title: 0. `matched` = 1 for 76,280 rows (39.6%), of which 60,485 are writer_type. **Rows with matched = 1 and v6 > 0: 66,530** (87.2% of the matched rows, 34.5% of all rows). Matched rows whose title had no views data at all: 16 (they get 0 views).

| test_year | matched | matched, v6 > 0 |
| --- | --- | --- |
| 2017 | 9,331 | 7,627 (81.7%) |
| 2018 | 8,768 | 7,229 (82.4%) |
| 2019 | 8,449 | 7,031 (83.2%) |
| 2020 | 7,131 | 6,135 (86.0%) |
| 2021 | 9,023 | 7,811 (86.6%) |
| 2022 | 8,486 | 7,374 (86.9%) |
| 2023 | 7,985 | 7,206 (90.2%) |
| 2024 | 7,425 | 6,885 (92.7%) |
| 2025 | 8,345 | 7,938 (95.1%) |
| 2026 | 1,337 | 1,294 (96.8%) |

Columns: work_id, creator_key, display_name, first_ym, test_year, Y6, loans6, top10 (Y6 at or above the 90th percentile of Y6 among works of the same first-month year; share by year 2017 10.0%, 2018 10.1%, 2019 10.1%, 2020 10.0%, 2021 10.0%, 2022 10.1%, 2023 10.0%, 2024 10.1%, 2025 10.0%, 2026 10.1%), fmt_print / fmt_ebook / fmt_audiobook (format available in the first month), n_prior_works, ln_prior_loans, month, matched, v6, v12, trend, vmax, writer_type, enwiki_title, qid, flag_months6, titles_with_no_views_data. The columns `top10`, `enwiki_title`, `qid`, `flag_months6` and `titles_with_no_views_data` are additions for checking; the model code should use only the columns the record lists.

## 6. Things worth knowing

- **Same person matched from several names.** 711 article titles are reached from more than one display name (for example spelling variants or a pseudonym redirect), so author clusters in the bootstrap should use `creator_key` (as planned) or the article title, not the name. The 12 articles with the most works: James Patterson (277 works, 1 name); Jeff Kinney (159 works, 1 name); Dav Pilkey (151 works, 1 name); Jane Kurtz (101 works, 1 name); Aaron Blabey (93 works, 1 name); J. K. Rowling (88 works, 3 names); Saadia Faruqi (85 works, 1 name); Rumiko Takahashi (84 works, 1 name); Heather Graham (83 works, 1 name); Jane Yolen (78 works, 1 name); Tracey West (77 works, 1 name); Kōhei Horikoshi (77 works, 2 names).
- Share of the matched works that belong to the 100 most frequent articles: 7.5%; to the 1,000 most frequent: 27.7%.
- **writer_type counts only the 14 occupation items named in the build instructions (the record's 'memoirist' is taken as Q18814623, autobiographer), with no subclasses**, so a person whose only occupation is a subtype (for example comics writer or manga artist) is a human match without writer_type. 9,332 matched names (32.3%) have no writer_type; 571 of them have no occupation at all. The most common occupations among them: actor (Q33999) 923; university teacher (Q1622272) 893; politician (Q82955) 729; film actor (Q10800557) 591; singer (Q177220) 558; television actor (Q10798782) 508; musician (Q639669) 450; composer (Q36834) 371; businessperson (Q43845) 311; lawyer (Q40348) 311; songwriter (Q753110) 275; association football player (Q937857) 260.
- Names with the most works that matched (a quick look for wrong-person matches; not checked by hand): James Patterson -> James Patterson (277); Jeff Kinney -> Jeff Kinney (159); Dav Pilkey -> Dav Pilkey (151); Jane Kurtz -> Jane Kurtz (101); Aaron Blabey -> Aaron Blabey (93); Saadia Faruqi -> Saadia Faruqi (85); Rumiko Takahashi -> Rumiko Takahashi (84); Heather Graham -> Heather Graham (83); Jane Yolen -> Jane Yolen (78); Tracey West -> Tracey West (77).
- Matched articles with the highest v6 (a look for namesakes of very famous people; not checked by hand): Charlie Kirk (v6 up to 15.8, 2 works); Kobe Bryant (v6 up to 15.4, 4 works); Ozzy Osbourne (v6 up to 14.8, 1 work, no writer occupation); Pope Francis (v6 up to 14.7, 23 works); Donald Trump (v6 up to 14.6, 5 works); Anne Heche (v6 up to 14.5, 1 work); Barack Obama (v6 up to 14.5, 10 works, no writer occupation); Jimmy Carter (v6 up to 14.4, 4 works); Anthony Bourdain (v6 up to 14.4, 6 works); Ruth Bader Ginsburg (v6 up to 14.3, 5 works, no writer occupation).
- Matched names with the most works but **no writer_type** (occupations in brackets, from Wikidata; not checked by hand). Some are plainly the right person whose occupation item is outside the list of 14 (for example comics writer or manga artist), others look like namesakes (an actor, a footballer): James Dean -> James Dean (66 works; racing automobile driver, television actor, film actor, stage actor); Gege Akutami -> Gege Akutami (60 works; comics creator, comics writer, penciller, mangaka); Paul Noble -> Paul Noble (49 works; draftsperson, artist); Hirohiko Araki -> Hirohiko Araki (46 works; mangaka); Kohei Horikoshi -> Kōhei Horikoshi (41 works; draftsperson, mangaka, illustrator); Haruichi Furudate -> Haruichi Furudate (39 works; comics creator, mangaka); Paul Tobin -> Paul Tobin (author) (38 works; comics creator, comics writer); Kōhei Horikoshi -> Kōhei Horikoshi (36 works; draftsperson, mangaka, illustrator); Martin Edwards -> Martin Edwards (34 works; sports executive); Kelly Thompson -> Kelly Thompson (32 works; comics writer); Steve Jenkins -> Steve Jenkins (32 works; association football coach, association football player); Christopher Kimball -> Christopher Kimball (29 works; radio personality, chef).
- Manga artists (Wikidata Q191633) without any listed writer occupation: 76 matched names, 689 works. They are correct matches that get writer_type = 0 under the 14-item list.
- Names with the most works that did NOT match: DK (535; plain title disambiguation); Pimsleur (523; plain title disambiguation); Lonely Planet (203; plain title not_human); Erin Hunter (139; plain title not_human); Harvard Business Review (109; plain title not_human); America's Test Kitchen (109; plain title not_human); Ma Isabel (María Isabel) Sánchez Vegara (105; plain title missing); Maria Isabel Sanchez Vegara (99; plain title missing); Hidenori Kusaka (98; plain title not_human); Jake Maddox (94; plain title missing).
- Works whose creator string holds more than one author are matched on the first author only, as in the record. Organisations and corporate authors are not excluded; a few can match a human by chance (for example a name shared with a person).
- **Views are those of the article title after redirects, as the record says.** The REST API counts a visit under the title that was requested, so traffic that arrives through a redirect (a pseudonym such as the pen name that redirects to a real name, or the old title of a page that was later moved) is not in the target's series. Such authors' views are understated. This is not corrected; it is one more source of noise in W.
- Wikidata items read: 29,393; missing items: 0; items that were human: 28,155.

## 7. Runtime

All on 20 Oct 2026, one long download at a time, `nice -n 10`. Population and loans/library features: 9 s for the loans script (the population script takes about 1 s). Author matching (`02_author_match.py`, detached with `jobs/bg.sh wiki_led_match`): 15:14:40 to 16:09:23, 54 min, 6,433 requests to the Action API and Wikidata (sequential, at most 5 per second, `maxlag=5`, 6 back-offs). Views download (`03_author_views.py`, `jobs/bg.sh wiki_led_views`): 16:09:29 to 18:56:44, 2 h 47 min of wall clock including the rate tuning and restarts described in section 4; the last, steady run needed 77 min. Rows 1 s, checks 7 s, report 2 s. From the first script to the last: 15:11 to 19:00 (about 3 h 50 min), almost all of it waiting for the APIs. Everything fetched is cached under `data/interim/wiki_led_cache/`, so a rerun of the chain should take minutes rather than hours (not timed).
