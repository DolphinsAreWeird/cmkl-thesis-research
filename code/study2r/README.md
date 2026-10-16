# Study 2R preparation (14 Oct 2026)

Question: does a rise in attention to one modern book raise its Seattle borrowing? Fixed settings: `prereg/study2r_settings_2026-10-14.json`
and `prereg/addenda_2r/2026-10-14_a_book_rule_equivalence_threshold.json`. This folder builds everything up to the point where outcomes
would be computed, and stops there. **No borrowing effect around any real event is computed here.** The only checkout data read are the
yearly totals per work (to pick works with at least 500 checkouts) and the placebo windows of `05b` (random month 0, no attention data).

Run from `handoff/code`, one process at a time, with `nice -n 10 ../.venv/bin/python study2r/NAME.py` (long ones with `jobs/bg.sh`).
Every web answer is cached in `data/interim/study2r_cache/` (SPARQL and MediaWiki; at most 5 requests per second, User-Agent names
kwai@cmkl.ac.th), and the pageview files in `data/db/study2r/pv_daily/`, so any script resumes after a stop.

| Step | Script | What it does | Main output |
|---|---|---|---|
| 1a | `01_wikidata_bulk.py` | Bulk SPARQL: every Wikidata item with an English Wikipedia article in a written-work class (literary work, written work, book, graphic novel ...; series and films excluded), its label, description, authors, and the ISBNs of the item or of its editions (P629) | `data/db/study2r/wd_*.parquet` |
| 1b, 2, 3 | `02_match_books.py` | Seattle works with at least 500 checkouts in 2016-01..2026-08 matched by ISBN (10 and 13 reduced to 13 digits, so hyphens do not matter), else by title and author family name. Writes the 100-row hand-check sheet and the positive-control table | `book_matches.parquet`, `data/reports/study2r_match_check.csv`, `data/reports/study2r_book_set.md` |
| 4a | `03_pageviews.py` | Daily user views of each canonical article plus redirects with real traffic (the screen of `main_study/interest/06`), and of the author's article (canonical title only) | `pv_daily/`, `articles.parquet`, `redirect_screen.parquet` |
| 4b | `04_weekly_series.py` | ISO-week sums divided by total English Wikipedia user views (`data/db/interest/wiki/weekly_total.parquet`) | `weekly_book.parquet`, `weekly_author.parquet` |
| 5a | `05_calibrate_ratio.py` | Rise ratio from interest data only (addendum a): smallest of 1.5 to 5.0 with sustained-shift noise share at most 0.30 on block-resampled series; floor 300 views a week | `calibration.json`, `data/reports/study2r_ratio_calibration.csv` |
| 5b | `05b_feasibility.py` | Works a class needs for its upper 95% bound to fall below log 1.10 under zero effect, from placebo windows (method of `parameter_audit/calibrate_2r_noise.py`) | `feasibility.json` |
| 6 | `06_file_note.py` | Writes `prereg/addenda_2r/2026-10-14_b_calibration_values.json` (refuses to overwrite) | the note |
| 7 | `07_detect_shifts.py` | Shifts of every article with the calibrated rule, quality flags (one-day, desktop-only), counts by duration class. Refuses to run before the note exists | `shifts_book.parquet`, `shifts_author.parquet`, `data/reports/study2r_shifts.md` |

Notes on choices
- The book rule counts checkouts of all formats in 2016-01..2026-08 (the record says "in total over 2016-2026"); the feasibility step then keeps works with at least 500 print and ebook checkouts, as `calibrate_2r_noise.py` does.
- An ISBN hit is dropped only when title and author both disagree with the Wikidata item (none were). Title and author matches need the Seattle title to equal the Wikidata label or the Wikipedia title (parenthesis and leading article removed) and a Seattle creator's family name to be a word of an item author.
- Weeks are valid when full, not partial in the site total, and with views above zero (as in `calibrate_book_series.py`).
- Several Seattle works can share one article (editions); `shifts_book.parquet` has one row per article with the list of `work_ids`.
- Title-confusion (a same-named film or series) is a hand check in Study 3 and is not run here; the one-day and desktop-only flags are.

## Outcome side (steps 10 to 15, run 14 Oct 2026 after the record and addenda a, b, c were fixed)
Run from `handoff/code` through `bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python study2r/NAME.py` or `jobs/bg.sh NAME study2r/_locked.py NAME.py`.
`_lib2r.py` (counts, z tables, one test per work and shift, placebo works and years, bootstrap tools, Hansen), `_pipe2r.py` (tests, screens, pools).
| Step | Script | What it does |
|---|---|---|
| 10 | `10_counts.py` | monthly checkouts per matched work and format (`counts_work.parquet`), by format to limit memory |
| 11 | `11_sim_tests.py` | simulation tests (injected lift, null rate near 5%, bootstrap, H1, H2, Hansen); `study2r_sim_tests.md` |
| 12 | `12_controls.py` | positive controls first; writes the controls section of `study2r_results.md` |
| 13 | `13_effects.py` | every tested shift: main, audiobook, ratio 1.5, author article; `effects_*.parquet` |
| 14 | `14_inference.py` | single tests with BH, pooled tau by class and size tercile, equivalence, H1, H2, size coefficient, Hansen; CSVs `study2r_*.csv` |
| 15 | `15_calendar.py` | diagnostic: tau of ordinary works by year (not in the record) |
The Study 3b `_methods.event_study` is imported unchanged; implementation choices are in `prereg/DEVIATIONS.md` (Study 2R).
