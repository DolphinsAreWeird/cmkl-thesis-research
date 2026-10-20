# Code audit of the Wikipedia-led tests (Test B data and scoring, Tests A and C, placebo, live list, improvement round)

Khant Phyo Wai, 01323050. Independent review, 20 Oct 2026 (about 18:00 +07).

Scope: `code/main_study/wiki_led/` checked against `prereg/wiki_led_settings_2026-10-20.json`, the three addenda in `prereg/addenda_wiki_led/` and the section "Wikipedia-led tests" of `prereg/DEVIATIONS.md`. No code, data or settings file was changed. Every check was read-only; the helper scripts and a scratch copy of the Test B rows were kept in the session scratchpad, outside the project. The running views download (`03_author_views.py`) was not touched; its HTTP cache was only read.

To keep Test B blind, no Test B feature was related to `Y6` or `top10`. The Test B checks below are counts, definitions and recomputations only. Test A and C results were already public, so their outcomes were used where a check needed them.

Severity: **changes a number** = would change a reported number (for Test B, a number it is about to report); **minor**; **cosmetic**.

## 1. Summary, ranked (Test B first)

| # | Severity | Where | Finding |
|---|---|---|---|
| B1 | changes a number | `04_rows.py`:37-38; `30_test_b.py`:23, 125-126 | `matched` and `writer_type` describe Wikipedia in October 2026, not at the book's first month. 12.7% of checked matched works had no views of the author article in the 12 months before the first month (17.9% for 2017 books, 3.2% for 2026 books). |
| B2 | changes a number | `01b_loans_library.py`:121-124; `30_test_b.py`:24 | The three format flags are checkouts in month 0, which is inside the outcome window. |
| B3 | changes a number (small) | `01b_loans_library.py`:119; `30_test_b.py`:127 | Data gaps push the recorded first month of about 1,200 digital works from 2025-08 to 2025-09 (and of some print works into 2024-08). Their "before release" views include the real release month, and `flag_months6` is 0 for them. |
| B4 | minor | `30_test_b.py`:80-82 | 557 matched people appear in more than one `creator_key` cluster (3,715 works), so the bootstrap treats them as independent. |
| B5 | minor | `03_author_views.py`:25 | Views are fetched for the current title only; a page moved after 2015 loses its earlier views. |
| B6 | cosmetic | `30_test_b.py`:86, 127; `02_author_match.py`:24 | Unlogged extra subset, unused variable, the record's "memoirist" taken as Q18814623. |
| A1 | changes a number | `code/study2r/04_weekly_series.py`:26; `10_test_a.py`:84 | Weeks before an article existed are 0 views, not missing as the record says. The no-fitting rule mostly ranks newly created articles; with the record's rule its change rank goes from 0.067 to 0.072, its surge ratio from 1.77 to 2.08, its top-20 rise share from 15.5% to 27.4%. Author articles created later form a look-ahead group (W_lgbm change rank 0.001 to 0.002 lower without it). No decision changes. |
| I1 | changes a number (tuning only) | `40_extra_features.py`:41 | `age` is calendar time (one value for every article at an origin), not the article's age. |
| P1 | minor | `11_placebo_a.py`:59-69 | One donor serves 1,564 books (19% of scored rows). With a random tie-break the placebo change rank rises by 0.000 to 0.004. Conclusion unchanged. |
| C1 | minor | `20_test_c.py`:74-75, 83-84 | The candidate pool includes articles of works first lent after the test year began (7.9% of selected author articles, 0.8% of selected book articles). |
| A2 | minor | `10_test_a.py`:70-71, 161-162 | Months before a book's first loan are treated as missing in M6 and the 12-month mean. Sensible, but not in DEVIATIONS (1.25% of scored rows, 6.1% of surges). |
| I2 | minor | `41_improve_a.py`:48 | Configuration W3c (31 leaves) is not in the addendum's grid. It was not chosen. |
| R1 | minor | no script | `wiki_led_test_a_accuracy.csv` and `wiki_led_test_a_alert_list.csv` have no generating script in `code/`. |
| A3 | cosmetic | `10_test_a.py`:101; DEVIATIONS line 153 | `rmax` is not computed the way DEVIATIONS item 1 says (small differences). |
| A4 | cosmetic | `10_test_a.py`:170-171 | `h_lt1` and `h_lyago` use the raw count of an excluded month. |
| A5 | cosmetic | `10_test_a.py`:243, 277-283 | At origin 2020-10 the naive change is 0 for every book; scored as 0 and the book interval is NaN. |
| I3 | cosmetic | `41_improve_a.py`:77 | The 2019 tuning set includes origin 2018-12 (6,161 rows), which Test A does not score. |
| C2 | cosmetic | `20_test_c.py`:130 | Ties in the selection correlation are not broken by "more months" as the addendum says. |

**Before Test B runs:** B1 to B3 should be decided and written into DEVIATIONS before `30_test_b.py` is run, because each one is a change to the record's feature or sample definitions. Suggested changes are given under each finding. The other Test B items can be logged at the same time.

## 2. Test B (new books), not yet scored

### B1. `matched` and `writer_type` use the state of Wikipedia in October 2026 (changes a number)

- **Where:** `04_rows.py`:34-38 (`matched` = the name was accepted as a human article in the October 2026 lookup by `02_author_match.py`; `writer_type` = that item's occupations today); `30_test_b.py`:23 puts both in `WCOLS`; `30_test_b.py`:125-126 defines the B3 subsets with them.
- **What is wrong:** the record's principle is "inputs only from before the prediction point", and its v6, v12 and vmax follow it. `matched` and `writer_type` do not: an author whose article was created after the book came out (often because the book did well) gets `matched = 1` with all view features at 0. The W model can tell this group apart from unmatched authors (`matched = 0`, views 0) only through information from after release. The code follows the record as written; the gap is in the record's feature definition.
- **Evidence** (prevalence only, no outcome): for the 12,076 of 28,155 accepted titles already in the download cache (alphabetical, so not a random sample), 32,443 population works are matched. Of these, **4,128 (12.7%) had zero views of the matched article in the 12 months before `first_ym`**, and 12.2% had no views at all under this title until `first_ym` or later. By first-month year: 2017 17.9%, 2018 17.7%, 2019 16.3%, 2020 13.5%, 2021 13.9%, 2022 13.2%, 2023 10.0%, 2024 7.4%, 2025 4.5%, 2026 3.2%. The fall with time is the pattern expected from articles created after release. 74% of these works are `writer_type`. In Test A, where outcomes are public, the same kind of group (author article that exists in 2026 but had no views yet at the origin) has a surge rate of 5.4%, against 3.3% for books with no author article (finding A1).
- **Fix:** before scoring, define both features at the first month: `matched_pre` = 1 when the matched article has at least one view in a month before `first_ym` (views start 2015-07, so every work has at least 18 months of history); `writer_type_pre` = `writer_type` x `matched_pre`; use them in `WCOLS` and for the B3 subsets. A tighter version would use each article's creation date (its first revision), which also keeps moved pages (B5). Log in DEVIATIONS as a correction made to keep the record's own time rule.

### B2. The first-month format flags are part of the outcome (changes a number)

- **Where:** `01b_loans_library.py`:121-124 sets `fmt_<format>` = 1 when `first_ym_<format>` equals `first_ym`; `30_test_b.py`:24 puts them in `LCOLS`, so they enter L_lgbm and LW_lgbm.
- **What is wrong:** `first_ym_<format>` is the first month with a checkout in that format (`code/main_study/11_v3_work_table.py`:23, 36-40), and the record-level files hold only months with at least one checkout. So `fmt_print = 1` means "at least one print loan in month 0", and month 0 is inside `loans6`. The flags do not come from later months, but they do come from the first outcome month. They are in the record ("format flags of the first month"); the principle "inputs only from before the prediction point" says otherwise.
- **Evidence:** the minimum `checkouts` in `spl_rows_book`, `spl_rows_ebook` and `spl_rows_audiobook` is 1. The sum of the three flags is 1 for 149,369 works, 2 for 33,201 and 3 for 10,226 (22.5% of works have two or three). Each flag is at least one loan counted in `loans6`. A recomputation from the raw rows for 60 works agrees with this definition (0 mismatches).
- **Effect:** W_lgbm and B1 are not affected. L_lgbm and LW_lgbm get partial month-0 demand, so "what the library already knows" is overstated. B2 (LW minus L) is then measured against a stronger baseline than a real pre-release library model would be.
- **Fix:** before scoring, either drop the flags (L = `n_prior_works`, `ln_prior_loans`, `month`) or keep them only in a labelled check ("library knows which formats were borrowed in the first month"). Log the choice.

### B3. Data gaps move some books' first month (changes a number, small)

- **Where:** `01_population.py`:38 and `01b_loans_library.py`:119 (`flag_months6` counts flagged months in `first_ym` to `first_ym`+5 only); `30_test_b.py`:127 (the `no_flagged_months` check).
- **What is wrong:** ebook and audiobook checkouts are missing for 2024-05, 2024-06 and 2025-08; print is near zero in 2020-04 to 2020-07 and about a quarter of normal in 2024-06 and 2024-07. A book first borrowed in a gap month is recorded at the next month with data. For such a book, (a) v6 and vmax cover the real release month, and (b) `Y6` covers its months 2 to 7. When the shifted month is not itself flagged, `flag_months6` is 0 and the `no_flagged_months` check keeps the book.
- **Evidence** (works by recorded first month, no outcome): digital first-month works are 0 in 2025-08 and **2,534 in 2025-09**, against 1,135 in 2025-07 and 1,332 in 2025-10, so about 1,200 books moved into 2025-09, all with `flag_months6` = 0. Digital: 0 in 2024-05 and 2024-06, 2,374 in 2024-07 (these are flagged, since 2024-07 is a flagged month). Print: 138 in 2024-07, 1,263 in 2024-08 (about 1,000 in a normal month), and 2024-08 is not flagged. Share of works with `flag_months6` > 0 by year: 2019 15.5%, 2020 69.8%, 2023 6.8%, 2024 48.1%, 2025 46.0%.
- **Fix:** extend the flag to the month before `first_ym` (flag a work when any of `first_ym`-1 to `first_ym`+5 is a flagged month). This adds the works first recorded in 2020-10, 2024-08 and 2025-09 (1,423 + 2,201 + 3,174 works). Either drop those works from the main scoring or report the check with the wider flag. Log it.

### B4. Some people are split across bootstrap clusters (minor)

- **Where:** `30_test_b.py`:80-82 resamples `creator_key` clusters.
- **Evidence:** 557 matched Wikipedia people (`enwiki_title`) appear under more than one `creator_key`, covering 3,715 of 76,280 matched works (for example Leo Tolstoy under 5 keys). Their rows share the same Wikipedia features but are resampled as independent authors, so the intervals are a little too narrow. 2,433 `creator_key` values also carry more than one display name.
- **Fix:** cluster on connected groups of `creator_key` and `enwiki_title` (merge keys that share an article). Small effect expected.

### B5. Views of the current title only (minor)

- **Where:** `03_author_views.py`:25, 31 request the per-article series of the title reached after redirects.
- **Evidence:** of the 12,070 fetched titles with any views, 4,163 have their first views after 2015-07 (2,603 after 2018-12). These are pages created later or moved to their present title later; for moved pages the earlier views sit under the old title and count as 0 here. `05_report.py`:180-182 already notes the redirect case.
- **Fix:** the creation-date version of B1 sorts out existence; to recover the lost views, add the views of the article's redirects (as `code/study2r/03_pageviews.py` did for book articles). Otherwise disclose as noise.

### B6. Small items (cosmetic)

- `30_test_b.py`:127: the `no_flagged_months` subset is not in the record. It is a sensible check; it should be listed in DEVIATIONS as an added check.
- `30_test_b.py`:86: `diff_w_n0` is never filled or used.
- `02_author_match.py`:24 takes the record's "memoirist" as Q18814623 (autobiographer). `05_report.py`:166 says so; DEVIATIONS does not.

## 3. Tests A and C, placebo, live list, improvement round (already run)

### A1. Weeks before an article existed are zeros, not missing (changes a number; no decision changes)

- **Where:** `code/study2r/04_weekly_series.py`:26 fills every day missing from the API with 0 views from 2015-07-01, so every article's weekly series starts on 2015-06-29 with zero shares. `10_test_a.py`:84 uses the share as it is. The record says: "Weeks before an article existed are missing (LightGBM missing values; ridge fills 0 and adds a missing indicator)". This is not in DEVIATIONS.
- **Evidence:** all 7,427 book articles start on 2015-06-29. 57,596 Test A rows at origins before the book article had any views carry `b_lvl4` = -27.63 (ln 1e-12) instead of missing. The record's file `wiki_led_test_a.json` reports `rows_with_book_features` = 1.0, which would be about 0.93 with the record's rule. Three effects:
  1. **Article creation counts as a large rise.** Right after an article appears, its "normal" is the median of zero weeks, so r4, r1, rmax, nrise8, run and dw become very large. 92.7% of the top 1% of scored rows by `b_dw` fall within 0 to 6 months after the book article's first views (median `b_dw` 25.1 there, 0 elsewhere). **87.6% of the no-fitting rule's top 20 each month are such books.** Rerun with the same feature code but weeks before an article's first week with views set to missing (the record's rule), the rule (`Wrule_D` = b_dw + a_dw) changes from change rank 0.0673 to **0.0721**, surge AP ratio 1.77 to **2.08**, and top-20 share that rose 15.5% to **27.4%**. So the reported rule numbers understate the rule, and "W_lgbm minus W_rule" (0.067) would be smaller.
  2. **A look-ahead group for author articles.** The author article is the one that exists in 2026. Before it existed the features are -27.63; a book with no author article at all has missing values. The tree models can tell "the author will have an article" apart from "no article". In scored rows, 7,681 rows (372 books) are in that group, with a surge rate of 5.4% against 3.3% for no author article and 2.7% for author articles with views. Refitting W_lgbm with those rows set to missing (2 test years): change rank 2019 0.1281 to 0.1261, 2022 0.1530 to 0.1517. HW minus H does not move (2019 0.0091 to 0.0093, 2022 0.0109 to 0.0109). A1 to A3 keep their decisions.
  3. **The placebo matching value.** See P1.
- **Fix:** rebuild `test_a_wiki_features.parquet` with each article's share set to missing before its first week with views, rerun 10, 11, 40 and 41, and report both versions; or log the deviation with the numbers above. The frozen live list (`12_live_alert_october.py`) cannot change; note that it inherits this rule, so new articles can rank high on it.

### I1. `age` is calendar time (changes the tuning numbers)

- **Where:** `40_extra_features.py`:41 sets `age = np.arange(len(grid))`, the number of weeks since the start of the article's series. Because every series starts on 2015-06-29 (A1), this is the same number for every article at a given origin.
- **Evidence:** in `extra_wiki_features.parquet` every (kind, origin) has exactly one `age` value: 186 at 2019-01 and 416 at 2023-06 for both book and author articles. The script's own description is "weeks since the article's first week with views (new articles)". Test years always lie beyond the training range of this counter.
- **Effect:** W1, W2, W3a to W3c, HW1 and HW2 contain a time counter instead of article age. The chosen configurations were the baselines W0 and HW0, so the 2024 to 2026 check is not affected. However, HW1's 2019 to 2023 alert share (0.9283) was 0.47 points above HW0's (0.9236), just inside the 0.5-point tie rule, so a corrected `age` could change which HW configuration is chosen.
- **Fix:** `age` = weeks since the first week with views above 0; rerun the 2019 to 2023 tuning; log.

### P1. One placebo donor serves 1,564 books (minor)

- **Where:** `11_placebo_a.py`:40-44 (matching value) and 59-69 (donor search in a window of plus or minus 50 positions, ties to the smaller work id).
- **What is wrong:** because of A1, books whose article had no views for most of 2016-03 to 2018-12 get the floor value -27.63 as their matching value. For all of them the window around the first floor position holds the same candidates, and the smaller-id rule picks the same donor. The addendum's fallback ("books with no b_lvl4 in that window are matched on their first 12 available origins") never applies to them, since every book has a value.
- **Evidence:** recomputing the donors with the script's own code: work 31175 is the donor of **1,564 books**, all at the floor value, covering 105,569 of 556,735 scored rows. These books all receive identical placebo features. With a seeded random choice among floor books by a different author (largest reuse 10), the placebo W_lgbm change rank goes from 0.0063 to 0.0103 in 2019 and from 0.0114 to 0.0117 in 2022 (real W_lgbm 0.128 and 0.153). The coded version gives the stored placebo change ranks to 4 decimals. The conclusion (the signal belongs to the book's own pages) stands.
- **Fix:** break ties at random with the seed, or match floor books on the month of their article's first views; cap donor reuse; rerun and log.

### C1. Test C's candidate pool knows which works Seattle will lend later (minor)

- **Where:** `20_test_c.py`:74-75 and 83-84 build the book and author candidates from `data/db/study2r/works.parquet`, the 7,747 works chosen by at least 500 loans in 2016 to 2026.
- **Evidence:** in `test_c_selection.json`, 0.8% of the selected book-article candidates and **7.9% of the selected author-article candidates** come only from works that had no Seattle loan before 1 January of the test year (2019: 10.2% of selected book and author candidates; 2023: 2.4%; 2026: 0%). The selection itself uses only earlier months, so the look-ahead is in who may be selected, not in the correlation. The record discloses this choice of works for Test A; addendum a does not repeat it for Test C.
- **Fix:** for each test year keep only candidates whose works had a Seattle loan before 1 January of that year (stricter: whose qualifying loans fell before that date), rerun C1, or disclose.

### A2. Months before a book's first loan are missing in M6 (minor, not logged)

- **Where:** `10_test_a.py`:70-71 sets months before the first loan to missing, so M6 (line 161) and the 12-month mean (line 162) skip them. The record says "a month without a row is 0 loans"; DEVIATIONS item 2 covers excluded months only.
- **Evidence:** 6,982 scored rows (1.25%) have an M6 window that starts before the book's first loan; they hold 952 of the 15,489 surges (6.1%). Counting those months as 0 would lower M6 and raise D for new books.
- **Fix:** log as a clarification; the code's choice is the more sensible one.

### I2. W3c is not in the addendum's grid (minor)

- **Where:** `41_improve_a.py`:48 adds num_leaves 31 with min_child_samples 200, 600 trees and learning rate 0.03. Addendum c lists num_leaves {15, 63}. W3c was not chosen (alert share 0.577 against W0's 0.586), but it was one more candidate in the selection. Log it.

### R1. Two reported CSV files have no script (minor)

- `data/reports/wiki_led_test_a_accuracy.csv` and `wiki_led_test_a_alert_list.csv` are not written by any file in `code/`. Recomputing the alert list from `test_a_preds.parquet`: W_lgbm top 20 rose 0.5859 (file 0.5865) and surged 0.3968 (0.3974); rule top 20 rose 0.1551 (0.1545) and surged 0.0763 (0.0756). The small differences come from the order of ties. The MAE of W_lgbm (15.77 loans) matches `wiki_led_placebo_a.json`. **Fix:** save the script that wrote the two files.

### Cosmetic items

- **A3** (`10_test_a.py`:101, same in `12_live_alert_october.py`:51): `rmax` takes each of the last 4 weeks against that week's own normal, not against the single normal of the 26 weeks before the last 4, which is what DEVIATIONS item 1 states. On 300 sampled book articles, 31% of weeks differ by more than 0.01 (median difference 0, 90th percentile 0.037). Fix the DEVIATIONS wording; the code's version produced all results.
- **A4** (`10_test_a.py`:170-171): `h_lt1` and `h_lyago` use the raw count of t-1 and t-11 even when that month is excluded. For example, at origin 2026-07, `h_lyago` is L(2025-08), a month with no ebook or audiobook data. Affects the H and HW models only. Set to missing or log.
- **A5** (`10_test_a.py`:243 and 277-283): at origin 2020-10 every other month of the M6 window is excluded, so M6 = L(t) and `Hnaive_D` is 0 for every book. That month is scored 0 (mean 0.2329; 0.2359 without it) and the book interval of `Hnaive_D` is NaN in `wiki_led_test_a.json`. Footnote it or skip constant months.
- **I3** (`41_improve_a.py`:77): the 2019 tuning rows include origin 2018-12 (6,161 rows), which Test A does not score. Add `& (R.mi >= 2019 * 12)`.
- **C2** (`20_test_c.py`:130): ties in rho are ordered by `argsort`, not by "more months" as the addendum says. With continuous correlations, ties are very unlikely.

## 4. What was checked and found correct

**Test B data and scoring**
- `01_population.py`: filters as in the record (first month 2017-01 to 2026-02, `pub_year_min` at least the year of the first month minus 1, non-empty creator); `parse_author` is the unchanged copy; 194,741 new releases, 192,796 after the 1,945 empty creators, 0 parse failures.
- Month indexes: `_common.ym_to_idx` (2005 base) is used only inside `01b` and `04` for window arithmetic, and `01b`:55 builds the same 2005-based index explicitly. `30_test_b.py`:34 computes its own index (year x 12 + month - 1) from `first_ym` and never mixes it with 2005-based indexes. The record-level data, `counts_work` and the demand panel all run from 2005-04 to 2026-08, so the last window (2026-02 to 2026-07) is complete.
- `01b_loans_library.py`: `loans6` = all formats in `first_ym` to `first_ym`+5; `prior_loans` = loans of all works of the same `creator_key` in all of `spl_works`, strictly before `first_ym`; `n_prior_works` = works of the creator with an earlier first month. Recomputed from the raw rows for 60 works (25 random, 25 with prior loans, 10 with more than 20 earlier works): 0 mismatches in `loans6`, the format flags, `n_prior_works` and `prior_loans`. No population work has a row before its first month; none has `loans6` = 0. The flagged months equal the panel's (2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08).
- `02_author_match.py`: the title order, redirect following, and the handling of disambiguation pages and non-humans follow the record.
- `03_author_views.py`: monthly, all-access, user agent, 2015-07 to 2026-09; titles quoted with `/` encoded; a 404 means no views.
- `04_rows.py`, run unchanged on a scratch copy with the views of the 12,076 titles fetched so far: v6, v12 and vmax use months f-6 to f-1, f-12 to f-7 and f-12 to f-1 only, never the first month or later (3,000 works recomputed independently, 0 mismatches); `top10` covers 10.0% to 10.1% of each year. Nothing was written to the project.
- `30_test_b.py`: training rows satisfy `fm + 5 < Y*12`, so only works whose six-month window ended before 1 January of the test year are used; the LightGBM settings equal Test A's; the record's fingerprint is checked. The scoring functions were run verbatim on made-up outcomes with the real author clusters: a model with no information scored 0.002 [-0.004, 0.007], a weak one 0.139 [0.134, 0.146], LW minus L was 0 when the two were equal, and the output serializes to JSON. 200 draws took 29 seconds, so the full run (2,000 draws, 4 subsets) should take about 20 minutes.

**Test A**
- Excluded months come from the panel's `month_ok`, which is constant within each format and month. The panel and `counts_work` both use year x 12 + month - 1 (checked against the panel's `ym` column), and the first loan month in `counts_work` equals `spl_works.first_ym` for all 7,747 works.
- Rows: 4,000 sampled rows rebuilt independently (L(t), L(t+1), M6 with excluded and pre-first-loan months skipped, `h_lt1`, `h_m12`, `h_lyago` = L(t-11), the same month a year before the target, `h_age`) and the entry rule at 4 origins: 0 mismatches. D, the surge flag and Y match the record on all 750,501 rows. No origin or target month is excluded; `year` is the year of the target month.
- Time safety: weeks are ISO weeks labelled by Monday, so week + 6 days is the Sunday end used by the code. Truncation test (features at origin t equal those computed from the series cut at the end of month t): 240 comparisons, 0 difference; the extra features of `40_extra_features.py`: 180 comparisons, 0 difference.
- Walk-forward: a refit of W_lgbm for 2019 reproduces the stored predictions exactly (69,559 rows), with training targets ending in 2018-12.
- Scoring: per-month Spearman, circular blocks of 3 months, pooled AP with block intervals, HW minus H paired by month; W_lgbm's change rank recomputed as 0.1346, as reported.

**Placebo, live list, improvement round**
- Placebo: no donor shares the recipient's book article or author key; scored rows align with Test A's 556,735 rows; a refit with the coded donors gives the stored placebo change rank for 2019 and 2022 to 4 decimals.
- Live list (`12_live_alert_october.py`): origin September 2026 (2026 x 12 + 8); features from weeks ending by 30 September (the last full week, 21 to 27 September, has views for at least 99.9% of book and author articles; the partial week from 28 September is not used); trained on every Test A row with a target month up to 2026-08; eligible books had a loan in 2025-09 to 2026-08; the feature code is the same as Test A's.
- Improvement round: lambdarank groups are contiguous months; the selection rule is applied as written (W0 and HW0 chosen); W0 equals Test A's W_lgbm exactly on 2024 to 2026 (change rank 0.1287, alert share 0.5942 for both).

**Test C**
- Main rows: rebuilt with the benchmark's own rule (`benchmark/03_evaluate.py` class `Cmp`: pipelines with over 90% coverage, rows with all of them, series with at least 12 origins), giving the same 36,081 (format, level, theme, origin) keys as `test_c_preds.parquet`, 510 series, middle and narrow themes only; the 52 pipelines of `A2_table.csv` are exactly the covered set.
- The training target from the demand panel equals `wide2`'s `y_t` and `y_true` exactly on all 36,081 rows; excluded months are set to missing; the panel's months run without a break from 2005-04 to 2026-08.
- x(t) uses the weeks whose Sunday end falls in month t; selection uses only origins whose target month is before 1 January of the test year and at least 24 months; the ridge centres to fit an intercept; scoring uses groups of at least 10 series and the block bootstrap of the addendum. Middle themes have book candidates (`work_theme` holds all three levels), and 99.8% of rows have a Wikipedia forecast.
