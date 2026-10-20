# Test E rows (LibriVox, another platform): data build

Built 2026-10-20 17:59 by `code/main_study/wiki_led/50_test_e_data.py` (24 s); the independent checks and this report come from `code/main_study/wiki_led/51_test_e_report.py`. Rows file: `data/db/wiki_led/test_e_rows.parquet` (626,087 rows, 44 columns, 21 MB, SHA-256 3fbeb0f64b72ee01..., one row per book and origin month, ordered by origin month and book number). Data only: no model was fitted and no feature was related to an outcome; every number below is a count, the distribution of one column, or the base rate of the outcome by month (used to find bad months). Settings: addendum d of 20 Oct 2026, section test_E_librivox (Test A definitions with listens in place of loans, at least 24 listens over t-11..t, Wikipedia features where links and stored views exist, no new downloads). Nothing was downloaded. Rebuild: `cd code && nice ../.venv/bin/python main_study/wiki_led/50_test_e_data.py && nice ../.venv/bin/python main_study/wiki_led/51_test_e_report.py` (add `--raw-hist` to the first for the other reading of `h_lt1` and `h_lyago`, see the choices at the end).

## In short

- **Rows.** 626,087 rows for 7,848 LibriVox books, 98 origin months from 2017-12 to 2026-07; 563,651 rows have an origin from 2019-01 on (Test A's scored period). The first origin is 2017-12 because the listening data start in 2017-01 and a row needs 12 months. Three months are not used as origin or target (2023-12, 2024-10, 2025-01).
- **Wikipedia features.** Only series that were already stored were used. Book-article features `b_*` exist for 868 books (10.1% of rows), author-article features `a_*` for 1,219 books (16.4% of rows), either for 1,597 books (20.5% of rows). The other rows have these columns missing, as in Test D. Not stored, and not downloaded: 675 book articles and 2,091 author articles, listed in `data/db/wiki_led/test_e_articles_needed.csv`.
- **Counts.** The 12-month eligibility rule (24 listens) removes only 53 book-months, because after its first public month a LibriVox book almost always has views. The surge rate (Sg) is 4.03% over all rows and 4.23% from 2019-01 (Test A: 2.78% on its scored rows).
- **Problems to know before scoring** (details in section 7): (1) the Internet Archive level halved on 2 Aug 2018: rows with an origin up to 2018-06 sit wholly before it and rows with an origin from 2018-07 to 2019-06 straddle it (column `regime`); (2) in 9 further months the listens of the typical book jump or fall by a factor of 1.5 or more while the total moves much less, which looks like automated traffic spread over small books and not demand (column `flag_jump`; the surge rate is 11.5% on flagged rows and 2.4% on the others); (3) the author links are wrong for some authors with common names, and only the 139 authors with stored views are known to be right; (4) the book links point to an adaptation page for 13 of the most listened books.

## 1. What was found and where

| Path | What it holds | Rows | Dates |
| --- | --- | ---: | --- |
| `data/db/listening.parquet` | `book_id` (text), `period` (text `YYYY-MM`), `listens` (integer). `period` is a calendar month. `listens` is the Internet Archive Views API count (non-robot, per day) summed over the days of the month and over all single-author recordings of the book (`code/ia_views.py`, `code/build_db.py`). The thesis notes that these views count page visits and downloads, not time spent listening. | 910,484 | 2017-01 to 2026-08, 116 months for each of 7,849 book ids; no missing cell |
| `data/db/books.parquet` | `book_id`, `title` (the title of the book's first recording). `book_id` is the LibriVox book group number (`bookgroup`). Group -1 collects 304 unrelated recordings and is dropped here. | 7,849 | |
| `data/interim/recordings_linked.pkl` | The 8,854 English LibriVox recordings with `identifier` (Internet Archive item), `bookgroup`, `n_authors`, `author`, `publicdate`, `wiki_author`, `wiki_book`. Made by `code/link_titles.py` from `data/raw/wikidata_author_match.json` and `wikidata_author_works.json`. 8,568 recordings have one author (the ones summed into the listening table). `wiki_author` is set on 6,662 recordings and `wiki_book` on 1,802. | 8,854 | public dates 2005-10-17 to 2024-12-17; 27 recordings without a date |
| `data/raw/ia_views_monthly.json` | Monthly sums per recording, the source of `listening.parquet`. Rebuilt here for all 7,848 books: 0 differences. | 8,854 recordings | 2017-01 to 2026-09; 2026-09 is partial (data to 2026-09-19, 75% of August) and is not used |
| `data/raw/ia_views_daily_books.json` | Daily views of 887 recordings (the books that have a book article; 16.0% of all views). Used here only to date outages and floods. | 887 recordings | 2017-01-01 to 2026-09-19 |
| `data/raw/wiki_book_daily.json` | Daily English Wikipedia user views of 615 LibriVox book articles (`code/weekly_collect.py`). | 615 articles | 2016-07-01 to 2026-08-31 |
| `data/db/study2r/weekly_book.parquet`, `weekly_author.parquet` | The weekly shares Test A uses (own title plus redirects kept by the screen for books). 168 LibriVox book articles and 139 LibriVox author articles are in them. | 7,427 and 3,004 articles | weeks from 2015-06-29 to 2026-09-28 |
| `data/db/interest/wiki/weekly_total.parquet` | Weekly totals of all English Wikipedia user views (the denominator of the shares). | 588 weeks | 2015-06-29 to 2026-09-28 |
| `data/raw/wiki_pageviews_monthly.json`, `wiki_author_pageviews_monthly.json` | Monthly views only: 615 book articles and 1,803 LibriVox author articles in the first file (885 author articles in the second). They cannot feed the weekly features and stop in 2025-06, 13 months before the last origin, so they are not used. | | 2015-07 to 2025-06 |
| `data/interim/study2_panel.pkl`, `weekly_lift_panel.pkl`, `weekly_events.pkl`, `weekly_scope.json` | Derived tables of the earlier LibriVox burst studies (monthly attention, weekly panel, event list, the 615 articles and 887 recordings). Not used: the raw series they came from are stored. In the first two, `bg` = -1 is the dropped catch-all group. | | |

## 2. The links

- **One link per book.** A book (book group) is one or more recordings. A link is kept when all linked recordings of the book agree. 13 books have recordings with different book articles and 3 have different author articles (for example one group holds Aristotle's Magna Moralia and his Eudemian Ethics, another holds stories by Schiller, Musaeus and Goethe); they get no link. A further 14 books (book article) and 2 books (author article) are linked on only some of their recordings and keep the link.
- **Counts.** Of 7,848 books, 1,602 have a book article and 6,193 have an author article (1,601 have both).
- **How they were made** (`code/link_titles.py`, stored, not redone): the author's name was matched to a Wikidata person with that label or alias, and the recording's title to that person's works. The matching code took the first person returned for a name, not the best known one (its sitelink count was always 1), so a common name can land on the wrong person.
- **Author links.** The English Wikipedia title equals the LibriVox author's name (ignoring accents, punctuation, initials and honorifics) for 5,337 of 6,193 linked books (86.2%); it differs for 856. 558 linked books (251 titles) point to a title with a disambiguator such as '(footballer)', which usually means the wrong person; 498 of the name matches carry one (the name is compared without it), so a clean match (same name, no disambiguator) holds for 4,839 books (78.1%). Wrong persons found at the top of the list of needed articles: H. G. Wells linked to Henry Gordon Wells, William Shakespeare to William Harold Nelson Shakespeare, Joseph Conrad to a French colonel, James Allen to an Alabama politician, Henry James to a Regius Professor, Andrew Murray to a golfer. All 139 authors that have stored weekly views are right (the 19 books whose name differs only spell it differently: Dostoyevsky, Le Fanu, John D. MacDonald). So the `a_*` features are safe; the author links without stored views are not, which is why `test_e_articles_needed.csv` carries `name_exact` and `likely_ok`.
- **Book links.** In a random sample of 70 books with stored weekly book views (pandas seed 11, read by hand against title and author), 2 pointed to an adaptation page instead of the book (The Great Gatsby to the opera, A Christmas Carol to a 1988 play); multi-volume works point to the work's article, which I counted as right. Titles ending in a tag for a play, film, opera or similar are on 25 books, 17 of them with stored views. My read of those 17: A Christmas Carol (1988 play) on 5 books, The Great Gatsby (opera) on 3, The Wonderful Wizard of Oz (2005 graphic novel) on 4 and Porgy (play) on 1 point to an adaptation (13 books, 2,948,934 listens in all, among the most listened books), while Peter Pan, Saint Joan, Antigone and Candida are plays and fit. `test_e_links.parquet` carries `book_title_tag_nonbook` so they can be dropped or checked.
- The books with a book article were chosen by having an article in 2026, a look-ahead in the choice of books (not in their views or listens), as in Test A.

## 3. Coverage of the Wikipedia views

| group of books | books | of these with at least one row | share of all listens | rows | share of rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| book article linked | 1,602 | 1,602 | 38.2% | 135,404 | 21.6% |
| book article linked and weekly views stored | 868 | 868 | 28.1% | 63,513 | 10.1% |
| author article linked | 6,193 | 6,193 | 80.4% | 494,742 | 79.0% |
| author article linked and weekly views stored | 1,219 | 1,219 | 33.4% | 102,939 | 16.4% |
| weekly views stored for the book or the author article | 1,597 | 1,597 | 37.8% | 128,515 | 20.5% |
| weekly views stored for both | 490 | 490 | 23.7% | 37,937 | 6.1% |
| all books | 7,848 | 7,848 | 100.0% | 626,087 | 100.0% |

- Book articles: 168 come from Study 2R's weekly file (the Test A pipeline) and 520 from the raw daily file (the article's own title, no redirect screen). On the 84 articles that are in both, the two sources agree on every common day; the weekly features agree to 2e-15 on 75 of them and differ on the 9 that have a redirect with traffic. So about one article in ten from the raw file may miss some redirect traffic.
- Author articles: 139 authors, all from Study 2R's weekly file. Most LibriVox authors are not authors of Seattle books, so most are missing. An author's features are shared by all of the author's books.
- Missing features are NaN (the columns are double precision, as in Test A). `b_src` is 1 (Study 2R weekly file), 2 (raw daily file) or 0 (none); `a_src` is 1 or 0.

## 4. What the rows are

- **Books.** The 7,848 book groups of the listening table without group -1. Listens of a book are the sum over its recordings (7,556 books have one recording, 292 have more; 135 books gained 178 recordings after their first public month and inside the window, which adds views from that month on). `n_rec` is the number of recordings public at the origin.
- **Months.** `mi` = year x 12 + month - 1 of the origin month t; `year` and `test_year` are the year of the target month t+1. Months before a book's first public month are missing, not zero (the Internet Archive date of its earliest recording; 181,665 cells, every one a stored zero; 24 books have no date and are treated as public from 2017-01).
- **Excluded months** (never an origin or a target, missing inside every window and in the eligibility sum, and missing for `h_lt1` and `h_lyago` when t-1 or t-11 is one): 2023-12, 2024-10, 2025-01. Why: 2023-12: outage: 5 days under half of the local median in the daily sample, 0 with no views at all; 2024-10: outage: 13 days under half of the local median in the daily sample, 10 with no views at all; 2025-01: flood: month total 4.5 times its trailing 12-month median, largest sample day 70 times normal.
- **Origins.** 98 months, 2017-12 to 2026-07: the 104 months from 2017-12 to 2026-07 minus the 6 whose month t or t+1 is excluded (2023-11, 2023-12, 2024-09, 2024-10, 2024-12, 2025-01). Test A's origins start in 2016-03; no LibriVox origin can come before 2017-12.
- **Eligible** at t when the listens over t-11..t sum to at least 24 (excluded months and months before the first public month add nothing).
- **Columns** (as Test A unless noted): `L_t`, `L_next`, `M6` (median of the listens over t-5..t, missing months skipped), `h_lt` = ln(1+L_t), `h_lt1` = ln(1+L(t-1)), `h_m6` = ln(1+M6), `h_m12` = ln(1 + mean over t-11..t, missing months skipped), `h_lyago` = ln(1+L(t-11)), `h_age` = t minus the first month with listens > 0 in this panel (Test A's formula; it is 2017-01 for every book public before 2017, so it is cut off at the start of the data), `D` = ln(1+L_next) - ln(1+M6), `Sg` = 1 when D >= ln 2 and L_next - M6 >= 5, `Y` = ln(1+L_next), `article`, `author_article`, `b_*` and `a_*` (lvl4, r4, r1, rmax, nrise8, run, dw, chg, valid4 from a verbatim copy of `article_features` in `10_test_a.py`, weeks ending on or before the origin month's end), `year`, `test_year`. Extra columns: `h_age_pub` (months since the book's first public month, the true age), `n_rec`, `regime` (0 = target before 2018-08, 1 = the span from t-11 to t+1 crosses 2018-08, 2 = after), `flag_jump` (see section 7, item 5), `has_book_page`, `has_author_page` (a link exists, whether or not views are stored), `b_src`, `a_src`.
- `book_id` is text, as in `listening.parquet` and `books.parquet`. L, M6, h_* and D are float32 as in Test A. The other tables are `test_e_links.parquet` (one row per book: links, public month, flags, listens total, rows), `test_e_months.csv` (one row per month: totals, the rules, flags, outcome base rates by origin month) and `test_e_wiki_features.parquet` (features by article and origin month).

## 5. Counts by year of the target month

Shares are shares of rows. `flag_jump` is defined in section 7, item 5.

| target year | books | rows | origin months | rows per month | book page flag | b_ features present | author page flag | a_ features present | surge rate (Sg) | D >= ln 1.5 | rows with flag_jump |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 4,943 | 57,458 | 12 | 4,788 | 23.9% | 8.6% | 79.5% | 18.3% | 2.24% | 6.2% | 16.9% |
| 2019 | 5,310 | 61,769 | 12 | 5,147 | 23.2% | 9.0% | 79.4% | 17.5% | 1.79% | 4.7% | 0.0% |
| 2020 | 5,800 | 66,855 | 12 | 5,571 | 22.6% | 9.5% | 79.1% | 17.0% | 2.28% | 6.2% | 0.0% |
| 2021 | 6,315 | 73,147 | 12 | 6,095 | 21.9% | 9.9% | 79.0% | 16.7% | 2.29% | 6.4% | 0.0% |
| 2022 | 6,816 | 78,915 | 12 | 6,576 | 21.5% | 10.3% | 78.8% | 16.3% | 1.97% | 6.3% | 0.0% |
| 2023 | 7,315 | 78,105 | 11 | 7,100 | 20.9% | 10.6% | 78.8% | 15.9% | 4.16% | 10.2% | 18.0% |
| 2024 | 7,827 | 68,574 | 9 | 7,619 | 20.5% | 10.9% | 78.9% | 15.7% | 6.89% | 14.4% | 44.7% |
| 2025 | 7,848 | 78,480 | 10 | 7,848 | 20.4% | 11.1% | 78.9% | 15.5% | 3.47% | 9.1% | 0.0% |
| 2026 | 7,848 | 62,784 | 8 | 7,848 | 20.4% | 11.1% | 78.9% | 15.5% | 11.73% | 22.0% | 87.5% |
| **all** | **7,848** | **626,087** | **98** | **6,388** | **21.6%** | **10.1%** | **79.0%** | **16.4%** | **4.03%** | **9.4%** | **17.5%** |

From 2019-01 (Test A's scored period): 563,651 rows, surge rate 4.23%, D >= ln 1.5 in 9.8%. Rows by `regime`: 32,994 before the 2018 break (0), 59,976 straddling it (1), 533,117 after it (2).

## 6. Month by month

Listens are the total over the 7,848 books (all months, including the excluded ones). The median book is the median over the 4,236 books that were public before 2017-01. The ratio is the month's total over the median of the totals of the 12 months before it (Test A's rule fires below 0.50). Origin rows, surge share and median D are by origin month t, so they describe the change from t to t+1 (empty where t or t+1 is excluded). 'flood day' = a day of the 887-recording sample above 3 times its 29-day median.

| month | listens, all books | median book, books public before 2017 | ratio to trailing 12-month median of the total | origin rows | surge share (target = next month) | median D | note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2017-01 | 3,546,321 | 162 |  |  |  |  |  |
| 2017-02 | 3,457,791 | 156 |  |  |  |  |  |
| 2017-03 | 3,893,806 | 174 |  |  |  |  |  |
| 2017-04 | 3,828,246 | 176 |  |  |  |  |  |
| 2017-05 | 3,660,469 | 168 |  |  |  |  |  |
| 2017-06 | 3,618,559 | 176 |  |  |  |  |  |
| 2017-07 | 4,312,440 | 194 |  |  |  |  |  |
| 2017-08 | 5,132,115 | 231 |  |  |  |  |  |
| 2017-09 | 5,010,349 | 222 |  |  |  |  |  |
| 2017-10 | 5,678,549 | 236 |  |  |  |  |  |
| 2017-11 | 6,076,605 | 236 |  |  |  |  |  |
| 2017-12 | 6,335,628 | 240 |  | 4,625 | 5.9% | +0.22 |  |
| 2018-01 | 7,459,416 | 291 | 1.82 | 4,647 | 3.0% | +0.07 |  |
| 2018-02 | 7,062,385 | 260 | 1.52 | 4,678 | 1.9% | +0.06 |  |
| 2018-03 | 7,162,901 | 263 | 1.41 | 4,713 | 2.4% | -0.05 |  |
| 2018-04 | 6,750,298 | 254 | 1.25 | 4,749 | 2.7% | -0.04 |  |
| 2018-05 | 6,936,232 | 257 | 1.18 | 4,776 | 1.7% | -0.02 |  |
| 2018-06 | 6,450,503 | 256 | 1.04 | 4,806 | 1.3% | +0.15 |  |
| 2018-07 | 8,104,709 | 303 | 1.27 | 4,838 | 2.5% | -0.39 |  |
| 2018-08 | 3,997,954 | 183 | 0.61 | 4,866 | 2.1% | -0.44 | break and jump |
| 2018-09 | 3,535,530 | 161 | 0.54 | 4,895 | 2.0% | -0.38 |  |
| 2018-10 | 3,671,319 | 166 | 0.56 | 4,922 | 0.7% | -0.42 |  |
| 2018-11 | 3,091,420 | 141 | 0.47 | 4,943 | 1.0% | -0.30 | Test A rule fires |
| 2018-12 | 3,008,723 | 136 | 0.46 | 4,978 | 1.3% | +0.00 | Test A rule fires |
| 2019-01 | 4,238,304 | 165 | 0.64 | 5,010 | 1.1% | -0.17 | flood day |
| 2019-02 | 3,628,456 | 136 | 0.68 | 5,039 | 1.7% | -0.03 |  |
| 2019-03 | 3,534,935 | 150 | 0.86 | 5,079 | 3.3% | -0.09 |  |
| 2019-04 | 3,889,629 | 139 | 1.01 | 5,101 | 2.6% | -0.10 |  |
| 2019-05 | 3,790,645 | 133 | 1.00 | 5,135 | 2.3% | -0.18 |  |
| 2019-06 | 3,601,685 | 121 | 0.97 | 5,170 | 1.0% | -0.10 | flood day |
| 2019-07 | 3,668,211 | 129 | 1.01 | 5,197 | 1.0% | -0.04 |  |
| 2019-08 | 3,854,029 | 132 | 1.06 | 5,221 | 1.4% | -0.07 |  |
| 2019-09 | 3,505,529 | 128 | 0.96 | 5,247 | 2.2% | -0.04 |  |
| 2019-10 | 3,583,453 | 130 | 0.98 | 5,282 | 1.6% | -0.17 |  |
| 2019-11 | 3,503,043 | 114 | 0.97 | 5,310 | 1.8% | -0.20 |  |
| 2019-12 | 3,143,624 | 109 | 0.87 | 5,354 | 1.5% | -0.02 |  |
| 2020-01 | 3,545,771 | 124 | 0.98 | 5,389 | 1.1% | -0.14 |  |
| 2020-02 | 3,273,422 | 111 | 0.91 | 5,425 | 2.6% | +0.00 |  |
| 2020-03 | 3,871,457 | 121 | 1.09 | 5,453 | 4.4% | +0.07 |  |
| 2020-04 | 4,984,086 | 127 | 1.39 | 5,506 | 3.3% | +0.00 | flood day |
| 2020-05 | 4,072,759 | 118 | 1.13 | 5,550 | 5.2% | -0.07 | flood day |
| 2020-06 | 3,149,193 | 116 | 0.88 | 5,593 | 1.6% | -0.16 |  |
| 2020-07 | 3,493,022 | 107 | 0.98 | 5,631 | 1.6% | -0.17 |  |
| 2020-08 | 3,547,532 | 104 | 1.01 | 5,680 | 1.3% | -0.22 |  |
| 2020-09 | 3,504,444 | 96 | 0.99 | 5,717 | 1.3% | -0.20 |  |
| 2020-10 | 3,316,628 | 92 | 0.94 | 5,757 | 1.4% | -0.19 |  |
| 2020-11 | 3,976,871 | 88 | 1.14 | 5,800 | 2.1% | -0.13 | flood day |
| 2020-12 | 3,314,331 | 92 | 0.94 | 5,848 | 1.9% | +0.00 |  |
| 2021-01 | 3,640,362 | 100 | 1.03 | 5,898 | 2.3% | -0.10 |  |
| 2021-02 | 3,422,376 | 91 | 0.97 | 5,938 | 4.4% | +0.05 |  |
| 2021-03 | 4,035,574 | 109 | 1.14 | 5,999 | 2.3% | -0.10 | flood day |
| 2021-04 | 3,207,019 | 94 | 0.91 | 6,041 | 2.1% | -0.13 |  |
| 2021-05 | 3,042,238 | 89 | 0.87 | 6,089 | 1.5% | -0.25 |  |
| 2021-06 | 3,031,715 | 76 | 0.88 | 6,127 | 2.0% | -0.14 |  |
| 2021-07 | 2,923,357 | 83 | 0.85 | 6,163 | 2.5% | -0.08 |  |
| 2021-08 | 3,354,728 | 87 | 1.00 | 6,204 | 2.2% | -0.07 |  |
| 2021-09 | 2,799,566 | 85 | 0.84 | 6,240 | 2.4% | -0.04 |  |
| 2021-10 | 3,412,345 | 85 | 1.03 | 6,285 | 2.2% | -0.07 |  |
| 2021-11 | 2,934,249 | 79 | 0.88 | 6,315 | 1.7% | -0.17 | flood day |
| 2021-12 | 2,484,028 | 72 | 0.76 | 6,348 | 1.5% | +0.00 |  |
| 2022-01 | 3,284,026 | 81 | 1.05 | 6,383 | 1.2% | -0.15 | flood day |
| 2022-02 | 2,777,861 | 71 | 0.89 | 6,432 | 2.5% | -0.01 |  |
| 2022-03 | 3,256,342 | 81 | 1.07 | 6,477 | 1.7% | -0.09 | flood day |
| 2022-04 | 3,072,184 | 76 | 1.01 | 6,510 | 1.5% | -0.08 |  |
| 2022-05 | 2,771,695 | 73 | 0.91 | 6,552 | 1.4% | -0.11 |  |
| 2022-06 | 2,589,588 | 70 | 0.87 | 6,588 | 1.3% | -0.08 |  |
| 2022-07 | 2,743,108 | 72 | 0.94 | 6,636 | 1.7% | -0.02 |  |
| 2022-08 | 2,840,949 | 72 | 0.99 | 6,679 | 1.4% | -0.07 |  |
| 2022-09 | 3,035,681 | 70 | 1.08 | 6,726 | 4.1% | +0.04 |  |
| 2022-10 | 3,064,034 | 78 | 1.06 | 6,768 | 2.6% | -0.03 |  |
| 2022-11 | 3,765,622 | 74 | 1.30 | 6,816 | 2.5% | -0.07 |  |
| 2022-12 | 2,837,316 | 71 | 0.97 | 6,863 | 2.0% | +0.08 |  |
| 2023-01 | 4,104,768 | 78 | 1.40 | 6,918 | 2.8% | +0.01 | flood day |
| 2023-02 | 3,711,329 | 79 | 1.26 | 6,958 | 1.7% | -0.03 |  |
| 2023-03 | 3,295,514 | 73 | 1.08 | 7,013 | 17.3% | +0.17 |  |
| 2023-04 | 3,992,747 | 127 | 1.31 | 7,065 | 7.1% | +0.02 | jump |
| 2023-05 | 3,171,984 | 98 | 1.04 | 7,117 | 3.0% | -0.06 |  |
| 2023-06 | 3,205,024 | 78 | 1.03 | 7,154 | 1.9% | -0.06 |  |
| 2023-07 | 3,289,997 | 82 | 1.03 | 7,192 | 1.4% | -0.09 |  |
| 2023-08 | 3,309,486 | 73 | 1.02 | 7,231 | 1.9% | -0.08 |  |
| 2023-09 | 3,147,488 | 72 | 0.96 | 7,279 | 2.3% | -0.13 |  |
| 2023-10 | 3,096,589 | 72 | 0.94 | 7,315 | 4.4% | -0.08 |  |
| 2023-11 | 3,029,026 | 82 | 0.92 |  |  |  |  |
| 2023-12 | 1,435,651 | 33 | 0.44 |  |  |  | excluded |
| 2024-01 | 2,650,527 | 60 | 0.82 | 7,446 | 2.0% | -0.12 |  |
| 2024-02 | 3,279,774 | 67 | 1.03 | 7,488 | 3.9% | -0.01 |  |
| 2024-03 | 3,161,965 | 74 | 0.99 | 7,549 | 6.5% | +0.02 |  |
| 2024-04 | 3,054,395 | 81 | 0.96 | 7,585 | 1.5% | -0.09 |  |
| 2024-05 | 3,078,705 | 66 | 0.98 | 7,622 | 26.4% | +0.30 |  |
| 2024-06 | 3,080,041 | 128 | 0.99 | 7,649 | 1.5% | -0.08 | jump |
| 2024-07 | 2,690,904 | 70 | 0.87 | 7,685 | 17.4% | +0.24 | jump |
| 2024-08 | 3,308,593 | 122 | 1.07 | 7,723 | 1.9% | -0.04 | jump |
| 2024-09 | 3,105,316 | 78 | 1.01 |  |  |  | jump |
| 2024-10 | 1,675,856 | 36 | 0.54 |  |  |  | excluded |
| 2024-11 | 2,720,723 | 74 | 0.89 | 7,827 | 1.0% | -0.17 |  |
| 2024-12 | 2,617,999 | 65 | 0.85 |  |  |  |  |
| 2025-01 | 13,837,026 | 1394 | 4.51 |  |  |  | excluded |
| 2025-02 | 2,205,393 | 82 | 0.72 | 7,848 | 2.6% | +0.01 |  |
| 2025-03 | 2,123,261 | 78 | 0.69 | 7,848 | 5.9% | -0.11 |  |
| 2025-04 | 2,077,802 | 88 | 0.72 | 7,848 | 6.7% | +0.02 |  |
| 2025-05 | 2,169,523 | 89 | 0.80 | 7,848 | 9.1% | +0.01 |  |
| 2025-06 | 2,073,954 | 95 | 0.78 | 7,848 | 3.3% | +0.01 |  |
| 2025-07 | 2,123,231 | 81 | 0.88 | 7,848 | 1.3% | -0.05 |  |
| 2025-08 | 2,127,905 | 67 | 0.97 | 7,848 | 0.8% | -0.04 |  |
| 2025-09 | 2,089,488 | 66 | 0.97 | 7,848 | 2.5% | +0.11 |  |
| 2025-10 | 2,280,583 | 90 | 1.07 | 7,848 | 1.2% | -0.07 |  |
| 2025-11 | 2,027,629 | 75 | 0.94 | 7,848 | 1.2% | -0.14 |  |
| 2025-12 | 1,907,780 | 68 | 0.90 | 7,848 | 11.3% | +0.15 |  |
| 2026-01 | 2,568,862 | 106 | 1.21 | 7,848 | 5.0% | -0.04 | jump |
| 2026-02 | 2,128,001 | 83 | 1.00 | 7,848 | 4.0% | -0.01 |  |
| 2026-03 | 2,195,068 | 82 | 1.03 | 7,848 | 21.4% | +0.28 |  |
| 2026-04 | 2,564,033 | 148 | 1.21 | 7,848 | 11.3% | +0.02 | jump |
| 2026-05 | 2,455,595 | 118 | 1.15 | 7,848 | 29.6% | +0.24 |  |
| 2026-06 | 2,604,746 | 212 | 1.22 | 7,848 | 8.1% | -0.04 | jump |
| 2026-07 | 2,269,041 | 133 | 1.05 | 7,848 | 3.2% | -0.07 | jump |
| 2026-08 | 2,062,167 | 125 | 0.92 |  |  |  |  |

## 7. Gaps and quality problems in the listening data

1. **What a listen is.** Internet Archive views count page visits and downloads of a recording, not time spent listening, and the Archive filters automated traffic with its own rule (the non-robot count used here). After a book's first public month there are only 72 zero cells in the whole table, so there is no zero inflation. The typical book (median of the 4,236 books public before 2017, median of the monthly medians) gets 131 views a month in 2019, 72 in 2022 and 81 in 2025.
2. **A level break on 2 Aug 2018.** In the 887-recording daily sample the daily total halves overnight (3 to 31 August averages 0.47 times July). Monthly totals fall from 8,104,709 in July to 3,997,954 in August, after rising 2.3 times from 2017-01. It looks like a change in how the Archive classes robot traffic, not a change in demand. Rows with an origin up to 2018-06 sit entirely before it, rows with an origin from 2018-07 to 2019-06 have a span that crosses it (`regime` 1), and the 12-month features of those rows (`M6`, `h_m12`, `h_lyago`) mix both. Test A's half-of-median rule fires on 2018-11 and 2018-12 for this reason (the trailing median still holds months from before the break), which is not missing data, so those two months stay in. The median D at the origin 2018-07 is -0.39, an effect of the break and not of any book.
3. **Outages (excluded).** 2023-12: the sample has 5 days under half of normal and the total is 0.44 of its trailing median. 2024-10: the sample has 13 days under half of normal, 10 of them with no views at all (11 to 18, 20 and 23 Oct 2024); the total is 0.54 of its trailing median, so Test A's rule alone would not catch it. Both months are missing data, not low demand. If they were kept as target months, the median D would be -0.94 (origin 2023-11, 61% below the usual level) and -0.70 (origin 2024-09, 51% below), with almost no surges (0.8% and 0.2%).
4. **One-day flood (excluded).** On 12 Jan 2025 the sample total is 70 times normal, 33% of the 887 sampled recordings received more than 100 views that day (one received 46,139), and the month total is 4.5 times its trailing median. Kept as a target month, 2025-01 would give a surge share of 54.0% (origin 2024-12, median D +1.25). Smaller flood days (more than 3 times the 29-day median in the sample) occur in 2019-01 (1, up to 5 times), 2019-06 (1, up to 6 times), 2020-04 (3, up to 7 times), 2020-05 (2, up to 6 times), 2020-11 (2, up to 9 times), 2021-03 (2, up to 5 times), 2021-11 (1, up to 4 times), 2022-01 (2, up to 9 times), 2022-03 (1, up to 9 times), 2023-01 (1, up to 6 times). They are kept; they move the month total by 10 to 40% and the median book by much less.
5. **Months in which the typical book jumps (flagged, not removed).** The median listens of the books public before 2017 change by a factor of 1.5 or more from one month to the next in the months below (months after an excluded month have no ratio). '10th percentile ratio' is the same ratio for the 10th percentile of those books, 'total ratio' for the sum over all books.

| month | median book | month before | ratio | 10th percentile ratio | total ratio | surge share at the origin before |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-08 | 183 | 303 | 0.60 | 0.51 | 0.49 | 2.5% |
| 2023-04 | 127 | 73 | 1.74 | 2.10 | 1.21 | 17.3% |
| 2024-06 | 128 | 66 | 1.94 | 2.65 | 1.00 | 26.4% |
| 2024-07 | 70 | 128 | 0.55 | 0.40 | 0.87 | 1.5% |
| 2024-08 | 122 | 70 | 1.74 | 2.33 | 1.23 | 17.4% |
| 2024-09 | 78 | 122 | 0.64 | 0.64 | 0.94 | 1.9% |
| 2026-01 | 106 | 68 | 1.56 | 1.70 | 1.35 | 11.3% |
| 2026-04 | 148 | 82 | 1.81 | 1.92 | 1.17 | 21.4% |
| 2026-06 | 212 | 118 | 1.80 | 1.80 | 1.06 | 29.6% |
| 2026-07 | 133 | 212 | 0.63 | 0.71 | 0.87 | 8.1% |

   In 2023-04, 2024-06 and 2024-08 the median book is 1.7 to 1.9 times its level of the month before and the 10th percentile rises more (2.1 to 2.6 times), while the total moves by 0 to 23%, and the level is back within one or two months; the median book gains 52 to 62 views and the 10th percentile book 22 to 28. From 2026-04 the median book stays above its earlier level (82 in 2026-03, then 148, 118, 212, 133, 125). That pattern fits automated traffic spread over the catalogue, not demand for single books, but these tables cannot prove it. In such months the surge label is true for a large share of all books (surge share by origin month, highest: 2026-05 29.6%, 2024-05 26.4%, 2026-03 21.4%, 2024-07 17.4%, 2023-03 17.3%, 2025-12 11.3%, 2026-04 11.3%, 2025-05 9.1%, 2026-06 8.1%, 2023-04 7.1%), so a pooled surge average depends on them (flagged rows are 17.5% of the rows and hold 50% of the surge rows). `flag_jump` = 1 when the origin month or the target month is one of the months in the table (2018-08 is the level break). It looks at the target month's platform-wide median, so it is a filter for scoring and never a feature. A within-month rank measure is not affected by a shift that moves all books alike; pooled level, change and surge measures are.
6. **A long fall of the typical book.** The median book (public before 2017) has 240 listens in 2017-12, 303 in 2018-07, 109 in 2019-12, 72 in 2021-12, 71 in 2022-12 and 78 in 2025-03. Median D is below zero in 70 of the 98 origin months, so a book's own recent level is above next month's level for most of the period. The median monthly total (all books) is 3.6 million in 2019, 2.9 in 2022, 3.1 in 2024 and 2.1 in 2025.
7. **Books that appear inside the window.** 3,588 books (45.7%) were first public in 2017-01 or later. For them the months before the public month are missing and `h_age_pub` is the true age. The public dates end on 2024-12-17, so the data hold no book published after that and the months from 2025 on contain only older books; a new-book test is not possible on this source. The books are the 8,854 English recordings of the Spotify Research LibriVox dataset (Elisha et al., 2026; `data/raw/librivox_spotify_dataset.csv`), not the whole LibriVox catalogue, and I did not find in the project files how that set was chosen.
8. **What a book is.** LibriVox's group number sometimes joins different works (plays by one author, a collection and one story in it, volumes of one work). 292 books have more than one recording; they are one unit here, and a link may fit only part of them (section 2). The 304 unrelated recordings of group -1 are dropped; that group was the most listened single 'book' of the table (17,589,547 views in all).
9. **Dates.** The Internet Archive `publicdate` is the upload date of the recording, not the LibriVox release date; 26 recordings of the single-author set have none. The Internet Archive API had data to 2026-09-19 when it was pulled on 12 Oct 2026 (a lag of about three weeks), which is why 2026-08 is the last full month.
10. **Wikipedia side.** The weekly shares carry the known issues of the Wikipedia series: the Wikipedia-led work reports May to June 2025 separately (addendum d: Wikimedia bot traffic), redirect traffic is missing from the raw-file series, and weeks before an article existed count as 0 views (as in Test A), so the features of a young article show a jump when its views start. Articles whose first week with views is after 2017-06: 3 of 168 book articles from Study 2R's file, 78 of 520 from the raw file, 0 of 139 author articles.

## 8. What was looked at while building (for the record)

Before any Test E model result, in this order: the listening table (shape, zeros, totals by month); the first public month against the first month with listens; the daily sample (outage and flood days); the month totals against their trailing median (Test A's rule); the median, 10th and 90th percentile of listens of the older books by month; after the rows existed, the surge share and median D of the rows by origin month (section 6) and the shares by year (section 5), and the surge share the excluded months would have had. These are outcome-only statistics; no feature was compared with an outcome. The excluded months and `flag_jump` were chosen from the traffic series (totals, the daily sample, the median book), not from any feature or model; the factor 1.5 of `flag_jump` was set after seeing the monthly medians and is a judgement. The links, the book-link sample and the author-name check use no listening data.

## 9. Checks (no model involved)

1. **Listening table against the raw file.** Rebuilding `listens` for every book from `ia_views_monthly.json` (sum over its recordings, 116 months): 0 differing books.
2. **Features against Test A.** The copy of `article_features` run on Study 2R's weekly series reproduces `test_a_wiki_features.parquet` exactly: book articles 168 articles, 21,000 article-month cells, maximum absolute difference 0.0, 0 missing-pattern differences; author articles 139 articles, 17,375 cells, maximum difference 0.0, 0 differences.
3. **Raw daily series against Study 2R.** On the 84 articles in both sources, from origin 2017-12: 75 articles without a kept redirect agree to 2e-15 on every feature; the others differ because Study 2R adds redirect traffic.
4. **Rows against an independent recomputation.** 2,577 random (book, origin) pairs plus the origins around the excluded months for 60 books were recomputed one book at a time from `listening.parquet` and the public dates with separate code; 2,235 of them are in the rows file and 342 are not, both as the rules say, and 31,290 values (L_t, L_next, M6, h_lt, h_lt1, h_m6, h_m12, h_lyago, h_age, h_age_pub, D, Y, Sg, n_rec) agree: 0 mismatches. For 60 further books every origin was checked: the set of origins in the file equals the set the rules give (5,880 cells, 0 differences).
5. **Features in the rows against the feature table.** Every `b_*` and `a_*` value of the rows equals the value of `test_e_wiki_features.parquet` for the same article and origin month (book articles: 63,513 rows with features out of 135,404 with a link; author articles: 102,939 of 494,742; maximum difference 0.0 and 0.0, no difference in which cells are missing). Rows whose article has a stored series but no feature: 0 (book), 0 (author).
6. **Structure.** No duplicate (book, origin); no excluded month as origin or target; rows ordered by origin month and book number; 53 book-months dropped by the 24-listen rule; no row dropped for a missing M6.

## 10. Choices where the request left room

1. **Excluded months.** The request says only 'months where the listening data are complete'. I used documented outages and one flood (rules: at least 3 days of the sample under half of its 29-day median, or a month total above twice its trailing 12-month median). Test A's rule (below half of the trailing median) alone would exclude 2018-11, 2018-12 and 2023-12, which keeps 2024-10 and 2025-01 and drops 2018-11 and 2018-12 for the wrong reason. To change the list, edit `EXCL` in `50_test_e_data.py` (a check stops the build if the rules and the list disagree).
2. **Missing, not zero.** Excluded months and months before a book's first public month are missing inside M6, the 12-month mean and the eligibility sum, as Test A and Test D treat excluded months.
3. **`h_lt1` and `h_lyago` in excluded months.** Test A and Test D read the recorded value of an excluded month for these two columns. Here they are missing (3.7% and 3.8% of rows): the recorded value of an outage month is about half of the true one and that of 2025-01 is inflated many times. `--raw-hist` builds `test_e_rows_rawhist.parquet` with Test A's reading. A month before the first public month counts as 0, as in Test A.
4. **`h_age`.** Test A's formula (months since the first month with listens in the panel) is `h_age`; the true age is `h_age_pub`. With the first formula every book public before 2017 has the same first month, so `h_age` is a calendar-time count for those books.
5. **Level break and jump months.** Not removed: the request did not give a rule for them, and rows before 2019-07 are a large part of the training data of the first test years. `regime` and `flag_jump` let the analysis drop or keep them with one filter.
6. **Books without a stored series.** They are in the file (the H models need them), with `b_*` and `a_*` missing. A Wikipedia-only model has nothing to predict from on those rows, so a W or HW score on this file should say which rows it uses (`b_src > 0` or `a_src > 0`).
7. **Links.** Reused as stored; no new match and no clean-up of wrong ones. Conflicting links are dropped, not guessed.
8. **Features for raw-file articles.** Built from the article's own title only (as `code/weekly_collect.py` fetched them); the weekly shares are made exactly as in `study2r/04_weekly_series.py`; the series starts 2016-07-01.
9. **Rounding.** D and Sg are computed in float32 as in Test A and Test D. Exact doublings (L_next = 2 x M6 + 1, with L_next - M6 >= 5) sit on the boundary D = ln 2: 782 rows (0.12%); float32 rounding labels 739 of them as surges and 43 as not (a float64 computation would differ from the stored Sg on 212 rows). The pooled surge rate is 4.025% and would be 4.032% if every one of them counted as a surge.
10. **Prereg bookkeeping.** Choices 1, 3, 4 and 5 are not in addendum d; `prereg/DEVIATIONS.md` has no entry for them yet (this build did not touch `prereg/`).

## 11. For the models of addendum d (E1 and E2)

- **Columns.** The history columns of Test A (`h_lt`, `h_lt1`, `h_m6`, `h_m12`, `h_lyago`, `h_age`) and the 18 Wikipedia columns (`b_*`, `a_*`) have Test A's names and definitions, so Seattle-trained models can be applied unchanged (E2) and the same code can be retrained here (E1). `h_lt1` and `h_lyago` have NaN in 3.7% and 3.8% of rows (LightGBM takes NaN).
- **Scale.** The Seattle-trained models were fitted on loans: in Test A's scored rows the median `L_t` is 9 and the median `h_m6` is 2.30; here the median `L_t` is 125 and the median `h_m6` is 4.82 (rows from 2019-01). Tree models do not extrapolate, so E2 will see inputs far above most of what the Seattle models were trained on. `h_age` is 139 (median, Test A) against 55 here; `h_age_pub` has a median of 94, closer to Test A, so which of the two columns feeds the Seattle models in E2 matters and should be fixed before the run.
- **Rows with Wikipedia features.** 128,515 rows have `b_*` or `a_*` (20.5%); per origin month: smallest 981, median 1,309, largest 1,597. A top-20 or top-50 list drawn from these rows in one month is therefore drawn from about 1,309 books, against about 6,365 in the full file.
- **First test year.** Rows whose target month is before 2019-01 number 57,458 (origins 2017-12 to 2018-11, all of regime 0 or 1, i.e. before or across the 2018 break); that is all that a model for test year 2019 can train on, and 4,937 of them have `b_*` and 10,496 have `a_*`.

## 12. Articles still needed (not downloaded)

The Wikimedia REST API is busy with another job, so nothing was fetched. `data/db/wiki_led/test_e_articles_needed.csv` lists the 2,766 linked articles with no stored weekly series: 2,091 author articles and 675 book articles (columns: kind, priority by listens within kind, article, api_title, LibriVox author and title of the most listened book that uses it, number of books, number of rows, listens, `likely_ok`, `name_exact`, `title_has_parenthesis`, `tag_nonbook`, `monthly_views_stored`). One daily per-article request each for 2016-07-01 to 2026-08-31 gives the series (the weekly shares are then made as here); about 2,800 requests, roughly 15 to 20 minutes at 3 a second.
- `likely_ok` marks the articles whose title equals the LibriVox author's name and has no disambiguator (authors: 1,536 of 2,091) or has no play or film tag (books: 667 of 675). The rest include the wrong persons named above and should not be fetched without a look.
- Rows that would gain `a_*` features if the most listened `likely_ok` authors were fetched (523,148 rows have no `a_*` now):

| authors fetched | books | rows | share of the rows without `a_*` |
| ---: | ---: | ---: | ---: |
| 50 | 726 | 57,938 | 11.1% |
| 100 | 1,098 | 88,346 | 16.9% |
| 200 | 1,598 | 128,530 | 24.6% |
| 500 | 2,329 | 185,734 | 35.5% |
| 1,536 | 3,635 | 287,690 | 55.0% |

- Monthly views to 2025-06 are stored for 1,646 of the needed authors and none of the needed books; they do not replace the weekly series.

## 13. Memory and runtime

- `50_test_e_data.py`: 24 s, peak resident memory 533 MB (limit 1,500 MB), run with `nice` 10 beside the Wikipedia views download. `51_test_e_report.py`: 5 s, peak 694 MB.
