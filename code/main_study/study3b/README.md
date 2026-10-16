# Study 3b code: small and fine-grained categories with count models, and sentiment direction

Does a rise in public interest in a theme carry over into library borrowing when the category is small or fine-grained? Study 3b
replaces the minimum-size rule of Study 3 by a count model, tests the narrow, middle and value levels, and adds a sentiment-direction
test. Settings: `prereg/study3b_settings_2026-10-13.json` (fixed 13 Oct 2026, read-only); everything it does not change comes from
`prereg/study3_settings_2026-10-13.json` and `prereg/addenda/*.json`. Study 3 stays the primary analysis and is not touched.

## Ground rules
- `_settings.py` checks both SHA-256 values (Study 3 record against its line in `prereg/README.md`, Study 3b record against its line in
  the Study 3b section), applies `prereg/addenda/` (through the Study 3 loader) and `prereg/addenda_3b/`, and parses every number from the
  records' own wording. A hash or parse failure stops every script (`SettingsError` is a `SystemExit`). The record's "unchanged from
  Study 3" list is checked against the parsed Study 3 values. No script hard-codes a setting from a record (the tests check the values).
- Study 3 modules are reused through `_s3.py` (panel functions, month rules, interest adapter, BH, percentile intervals, tone
  functions). Study 3 and Study 3b both have modules called `_settings` and `_methods`; `_s3.py` imports the Study 3 ones with the Study 3
  folder first on the path and then removes them from `sys.modules`, so the two sets never meet (the clash noted for Study 4, item 17
  of its README). Study 3 functions are only called inside a process; nothing from Study 3 is sent to joblib workers.
- Choices the record does not make are marked `# NOT IN RECORD:` in the code and listed below. Log them in `prereg/DEVIATIONS.md`
  (Study 3b section) if they are kept; `prereg/addenda_3b/` is empty so far.
- Order is enforced. 10 refuses to run without the reports of 01 and 02; each later step refuses without the report of the step
  before it, or if that report was made on another panel build. The positive controls (10) run first. 02 is tied to the file it wrote
  (its report holds the SHA-256 of `shifts_value.parquet`), not to the panel build.
- Machine rule: at most 3 workers (`--workers`, default and maximum 3), run long jobs with `nice -n 10` or `jobs/bg.sh`.
- Real data: 01 and 02 write structural and interest-only outputs. 10 to 14 are run by the main session. Every method was
  developed and tested on simulated worlds only.

## Run order (from `code/main_study/study3b/`, with `../../../.venv/bin/python`)

| Step | Script | Needs | Writes (data/db/study3b/) | Report (data/reports/) |
| --- | --- | --- | --- | --- |
| 01 | `01_panels.py` | taxonomy v3 files, Study 3 panel (one check) | `counts_seattle.parquet`, `counts_librivox.parquet`, `month_status.parquet`, `categories.parquet`, `panel_meta.json` | `study3b_01_panels.md` |
| 02 | `02_value_shifts.py [--skip-api]` | interest files (`wiki/weekly_value`, `gdelt/weekly_value`, pages, caches) | `shifts_value.parquet`, `_desktop_cache_value.json` | `study3b_02_value_shifts.md` |
| 10 | `10_controls.py` | reports 01, 02 | `controls.csv`, `controls_values.csv` | `study3b_10_controls.md` |
| 11 | `11_power.py` | report 10 with PASS (or `--accept-failed-controls`) | `power_draws.parquet`, `power_summary.csv`, `ztables/` | `study3b_11_power.md` |
| 12 | `12_shifts.py [--include-flagged]` | report 11 | `shift_effects.parquet`, `shift_effects_librivox.parquet`, `pooled_effects.csv` | `study3b_12_shifts.md` |
| 13 | `13_carryover.py` | report 12 | `carryover_coefs.csv` | `study3b_13_carryover.md` |
| 14 | `14_sentiment.py` | report 13, GDELT weekly tone | `sentiment_features.parquet`, `sentiment_models.csv` | `study3b_14_sentiment.md` |

Options: `--sim DIR` (run on a simulated world, see Tests), `--workers N`; simulation-only: `--draws` (11), `--boot` (12, 13, 14),
`--placebos` (14). Real runs use the record's sizes (200 draws, 2,000 resamples, 200 placebo windows).
After the GDELT tone backfill, rerun 12 to 14 with the same settings and the longer tone files.

## What the code does
- **Counts** (`_panel.py`, 01). Y = weighted checkouts per category, format and month: narrow and middle through the Study 3 function
  (`node_month`, same record-to-work mapping and the same missing, partial and closure month rules; the narrow and middle counts equal the
  Study 3 panel exactly, checked in the 01 report). Value level: per source the work's value weights become shares among the values placed
  in a node, and the work's strength for a value is the mean share over the sources with evidence (the node rule of `16_v3_assign.py`),
  multiplied by checkouts with a sparse matrix product. Exposure N = all checkouts of the format that month. Unusable months are NaN, usable
  months without a row are zeros. LibriVox is built the same way with its own exposure (all LibriVox views).
- **Count event study** (`_methods.event_study`). Quasi-Poisson GLM with offset log N, joint across the Seattle formats, on the 24 months
  ending at month -7, format-specific level and trend, shared month-of-year effects; phi = Pearson chi-square / residual df; mu predicted
  for months 0..+2 and 0..+5 (and -6..-1 as a pre-trend); tau = log(sum Y / sum mu); z = tau / sqrt(phi / sum mu); per-format versions
  with the joint phi. All categories of a level share one design at a given month 0 and format set, so the Poisson fits run in batches
  (IRLS). Checked against statsmodels (dispersion, expected counts, tau, z).
- **Inference** (`_inference.py`). The z table of a level and month 0 (the fit of every category) is cached in `ztables/`. The placebo
  categories of a test are the other categories of the level with a feasible fit, no interest shift start (any source or class) in months
  -6..+6, not sharing the parent; one-sided p = (1 + placebos with z >= treated z) / (placebos + 1). Placebo years: same category and
  calendar months in other years from 2017 without a shift in the window. BH within level; pooled means with the category-clustered
  bootstrap; carry-over regression with tau as the outcome; power by injected lifts; sentiment tests.
- **Power shortcut**. The fit months end at month -7, so multiplying Y by (1 + L) in months 0..+2 changes only sum Y; mu and phi stay as
  fitted and the lifted z is z + log(1 + L) / sqrt(phi / sum mu). A test confirms it equals a full refit with the lift injected.

## Inputs
- Seattle and LibriVox: as Study 3 (`data/db/taxonomy_v3/`, `spl_api_counts`), plus `work_theme_value.parquet` and
  `librivox_work_theme_value.parquet` (value level).
- Interest: Study 3's `data/db/interest/shifts.parquet` (narrow, middle), the value-level `shifts_value.parquet` of step 02, and for
  tone `gdelt/weekly_node.parquet` and `gdelt/weekly_value.parquet`. The adapter is the Study 3 one (`_interest.normalise_shifts`), so
  Mondays, classes, `large`, quality flags and the GDELT single-site flag are checked or applied as in Study 3. Value level is level 4
  in `shifts_value.parquet` (node_id holds the value, `parent_node` its placed node) and `level == 'value'` after loading.
- Nothing in `prereg/`, `study3/`, `study4/` or the existing interest outputs is changed. New files only: this folder,
  `data/db/study3b/`, `data/reports/study3b_*`.

## Tests
`../../../.venv/bin/python tests/run_tests.py [name-filter]` (pytest is not installed; about 2 minutes). They cover:
- settings: both hashes, a changed Study 3b or Study 3 record or README stops `load`, and stops a script run on a copy of the project;
  the "unchanged" claims are checked; no module-name clash;
- methods: agreement with statsmodels; per-format sums add up; a known injected effect recovered in a small-count category (about 12
  expected checkouts, +100%: mean tau near log 2, detected far more often than the 5% of a null category) and a large one; rank p-values
  about uniform on null data at six size bands from very small (sum mu < 2) to large, never anti-conservative; z spread comparable from
  5 expected checkouts; fit windows never touch months -6 and later (changing Y in months -6..+5 changes nothing, month -7 and -30 do,
  months before -30 do not); missing and closure months drop out (also with junk values in them) and an unusable month is never a zero;
  feasibility rule (exactly 12 nonzero months is enough); lifted z equals a refit; size bands; power summary; clustered bootstrap; BH;
  carry-over regression recovers known coefficients; sentiment features;
- panel: value strengths follow the node rule, the sparse product equals the merge computation, dense counts;
- pipeline on a simulated world: order and refusals, placebo rules, caching of z tables, controls with injected lifts pass, BH within level
  and family over non-sparse tests, a stale panel or changed shifts file stops later steps, record sizes cannot be overridden.

What the null tests show (simulated Poisson data, 120 months, three months 0, 9,000 category tests, categories from 0.3 to 1,000 mean
checkouts per format-month): with the record's z the spread of z is 1.7 to 2.1 at every size from 5 expected checkouts (not 1, because the
trend is extrapolated 7 to 9 months from a 24-month fit and the estimation error of mu is left out of the record's formula). It is about the
same at every size, which is what the placebo rank needs. Rank-p false-positive rates at 0.05, by sum mu: 0.01 below 2, 0.02 at 2 to 20, 0.04
at 20 to 100, 0.05 at 100 to 600, 0.07 above 600 (conservative for small categories, mildly liberal for the largest). Below 5 expected
checkouts the discreteness makes z behave differently (spread 0.8 to 1.4), which is why the record sets those tests apart.

## Choices not in the record (`# NOT IN RECORD:`)
Model and data
1. A format enters a category's joint model only if at least 18 of its 24 fit months are usable (the 75% coverage rule of Study 3
   addendum c) and it has at least 12 nonzero months itself (the record's feasibility threshold applied per format). The category is
   feasible when at least one format enters. Formats that do not enter contribute neither Y nor mu to that test.
2. A window needs at least 2 usable months (the analogue of addendum b); a calendar month never seen in the fit gets no prediction and
   its Y is left out of the window sums, so Y and mu always cover the same format-months.
3. The trend t is in years centred on the middle of the fit window; month-of-year dummies for the calendar months present, with the
   first as reference (the format intercepts absorb it). Same model as the record's formula.
4. phi has no floor (record formula); the per-format z uses the joint phi; sum Y = 0 gives tau = -inf and z = -inf (kept for ranking), and
   such tests leave the pooled means and the carry-over regression and are counted.
5. Value level: shares among the values placed in a node (values without a node are left out, as in the node assignment); a format
   keeps only values with at least 12 nonzero months in that format over all time (a value below that can never be feasible); zero months
   inside usable months count as zeros. Counts are stored sparsely.
6. LibriVox: every month with views is complete (Study 3 choice); its tests are separate, with their own exposure and placebos from
   LibriVox categories, and are outside BH, pooling and the carry-over regression.
Inference
7. Placebo categories include too-sparse ones; the shift screen counts any shift start (both sources, every class, seasonal and flagged
   included, as in Study 3). At the value level only 614 Wikipedia and 185 GDELT value series exist, so values without a series are
   treated as shift-free; `p_cat_p_screened` ranks the same test among placebo values that have a series (robustness, not the record's p).
8. Placebo years: "no shift in that window" uses months -6..+6 around the placebo month; the placebo fit must be feasible and its full
   primary window available; the comparison is on the primary window; a year needs its fit window inside the data.
9. Month 0 is the month of the shift week's Monday (Study 3). Several shifts of one category in one month 0 share one test.
10. BH family: all non-sparse joint Seattle tests of the main analysis (labelled, quality-ok, not seasonal) at a level, both sources
    together; seasonal shifts form a separate family; too-sparse tests are reported separately. Pooled means by source x level x
    duration class, source x level, and level, with and without the too-sparse tests; bootstrap intervals are 95% percentile intervals.
11. Shifts without a record duration class (interrupted, censored) are not tested; they still count in the screens. Flagged shifts
    (addenda g and i) are tested only in the `--include-flagged` robustness run.
12. Per-format effects have no placebo p (the placebo table holds joint fits only).
Power
13. The same draws are used for every lift (common random numbers), drawn uniformly without replacement within a size band (with
    replacement if a band has fewer units); bands are the quartiles of sum mu over all placebo units of the level (category x month 0 with a
    feasible fit, no shift in -6..+6, from the study start); detection uses the primary window. A lift of 0 is run as a false-positive
    check and is not part of the minimum detectable effect. Power is run for the Seattle joint model only.
Carry-over and sentiment
14. The carry-over regression is fitted per source and level on main-analysis shifts; there is no format term; too-sparse tests are
    left out of the main model and added in a sensitivity model; the Study 3 lag of the peak gap is not repeated.
15. Each sentiment feature enters its own model (the tone features are collinear); the two-sided placebo p is the share of placebo
    coefficients with |coef| >= |real coef| (every shift's feature replaced in turn by a placebo window of its category); a shift blocks
    max(4 weeks, class bound, real-time count, whole duration) of its category for the placebo windows; windows are drawn with the
    bootstrap seed, without replacement when enough exist; the interaction model holds negative shift, the sustained dummy and their product
    and the placebo test replaces negative shift (and so the product); models are per level on GDELT main-analysis shifts that are non-sparse
    with sum Y > 0; partial GDELT weeks are missing.
Positive controls
16. A control is "not testable" only when its model cannot be fitted (not feasible); the pass rule is the record's (tau > 0, one-sided
    placebo-category p < 0.05, joint Seattle model). Values inside a control node (parent equal to the node) are reported descriptively.
Interest side (02)
17. The value-level shifts use the Study 3 interest code unchanged (armed reading, GDELT thresholds equal to Wikipedia's). Value level =
    level 4. The existing weekly value files are used after a check that recomputes eight Wikipedia value series from the daily page views.
18. Quality flags: `one_day` from the weekly `top_day_share` of the value series; `desktop_only` from the driver page's desktop share (the
    rules of interest/09, not tuned), using cached answers where the same page and window exist and at most one new request per second
    with the project user agent otherwise; `title_confusion` only where the same page and a start week within 2 weeks carry a verdict in
    `wiki/review_title_confusion.csv`; GDELT `single_site` only where the driver code and day have a sampled URL list. Computed for
    labelled shifts from 2017-01 (the tested set). Nothing was checked by hand; what could not be screened is counted in the 02 report.
19. Implementation: z tables are stored as float32 for placebos while the treated category is refitted in float64; the cache file records
    the panel build and the settings hash.
