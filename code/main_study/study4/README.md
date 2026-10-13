# Study 4 code: forecasting next month's demand for book categories from public interest

Does adding public-interest signals to a model that already knows a category's own demand history improve one-month-ahead
forecasts of that category's demand? The settings are fixed in `prereg/forecast_settings_2026-10-13.json` (13 Oct 2026).

## Ground rules
- Settings come only from the fixed record. `_settings.py` checks the record's SHA-256 against the Study 4 line of
  `prereg/README.md` and stops on a mismatch, applies `prereg/addenda_forecast/*.json` in file-name order, and parses
  every number from the record's own wording (a parse that does not match stops the run). No script hard-codes a
  threshold, window, seed or parameter that is in the record.
- Choices the record does not make are marked `# NOT IN RECORD:` in the code and listed below.
- No setting is tuned after seeing forecast results. The tests use simulated worlds only.
- Machine rule: at most 3 threads in all. `--workers` (default 3, at most 4 per the record) times the CatBoost threads per
  worker stays within 3 (`thread_count = 3 // workers`, so 1 each at 3 workers). The forecast does not depend on the thread
  count (checked in the tests: the same seed gives the same CatBoost forecast with 1 or 2 threads). Run long jobs with `nice`.

## Run order (from `code/`, with `../.venv/bin/python`)

| Step | Script | Needs | Writes | Run time (this Mac) |
| --- | --- | --- | --- | --- |
| 01 | `main_study/study4/01_features.py` | Study 3 panel files, interest series, shifts | `data/db/study4/features.parquet`, `data/reports/study4_01_features.md` | about 10 s |
| 02 | `main_study/study4/02_forecast.py [--workers 3] [--limit-origins N]` | step 01 | `data/db/study4/forecast_parts/origin_YYYY-MM.parquet` (one per origin), `data/db/study4/forecasts.parquet` | hours; see the final line below |
| 03 | `main_study/study4/03_evaluate.py` | step 02 | `data/reports/study4_03_evaluation.md`, `study4_03_*.csv` | about a minute |
| 04 | `main_study/study4/04_interest_flow.py [--workers 3]` | interest series, shifts | `data/reports/study4_04_interest_flow.md`, `.csv`, `data/db/study4/interest_flow_forecasts.parquet` | about 30 to 60 minutes (one CatBoost fit per origin) |

Long job: from the project root, `bash jobs/bg.sh s4_forecast main_study/study4/02_forecast.py --workers 3`, then
`renice -n 10 -p $(cat data/reports/s4_forecast.pid)`. The job is resumable: part files are written per origin
(atomically), a restart skips the origins already saved, and `forecasts.parquet` is rebuilt from the parts at the end of each
run. Parts carry a fingerprint of the features file and the settings; `--reset` is needed to start again with other inputs.
Tests: `../.venv/bin/python main_study/study4/tests/run_tests.py [name-filter]` (about 2 minutes; pytest is not installed).

## Inputs (all made by earlier steps; never edited here)
- `data/db/study3/demand_panel.parquet` (category x month x Seattle format) and `demand_panel_librivox.parquet`
  (LibriVox, its own file). Columns used: `level`, `node_id`, `broad_id`, `format`, `mi`, `month_ok`, `total_checkouts`,
  `log_share` (a zero share is already missing), `size_ok`. `month_ok` is False for the missing, closure and partial months
  (Study 3 rules), so those months have no log share and are never an origin, a target or a training target.
  The Study 3 minimum-size rule is applied through the panel's own `size_ok` column (made by Study 3's `_build.size_columns`
  from the 24 months before the row's month, never including that month). It is not copied here: step 01 checks that the
  panel was built from the Study 3 record in `prereg/` and is not a development build.
- `data/db/interest/wiki/weekly_node.parquet` (weekly Wikipedia share per node), `data/db/interest/gdelt/weekly_node.parquet`
  (weekly GDELT volume share and tone; partial weeks are missing), `data/db/interest/shifts.parquet` and
  `shift_weekly.parquet` (real-time shift states). Only `start_week`, `label`, `label_week`, the weekly `ratio` and (for
  the scoring split only) `quality_ok` are read. `seasonal`, `quality_flag` and `title_confusion` are never read.
- Week alignment: ISO weeks, Monday start; the last week used at origin t is the last Monday whose Sunday is on or before
  the last day of t. A shift counts only if its start week is within the last 8 weeks up to that week, and its label only if
  its labelling week is on or before it.

## Modules
- `_settings.py` record, hash check, addenda, parsing, thread plan. `_features.py` pure feature functions (demand, weekly
  interest, shift states, tone). `_models.py` naive, seasonal naive, ridge, CatBoost, walk-forward and all metrics.
  `_forecast.py` one origin's forecasts and the worker. `_eval.py` evaluation tables. `_flow.py` interest-flow task.
- Feature table: one row per origin, category, format and horizon (h = 1, 2), long format, with `group` = `seattle` or
  `librivox`. Non-feature columns (`y`, `m12_last`, `m12_prev`, `split_qok_shift8`, keys) are listed in
  `_features.NON_FEATURES`; the test suite checks that no feature set uses them.

## What is forecast and how
- Target: log share of the category in the format in month t+h (h = 1 main, h = 2 secondary). The models learn the log-share
  level (as the record states the target); forecasts of change are the forecast minus the log share at t.
- Eligibility: a category-format series is forecast at origin t only if `size_ok` holds at t. A forecast is scored only when
  month t and the target month are both available.
- Models: naive, seasonal naive, ridge, CatBoost, each on feature sets D, D+W, D+W+G, D+W+G+T (naive models need none).
  D+W+G and D+W+G+T only up to origin 2021-05. Walk-forward by origin with an expanding window; at origin t the training rows
  are the origins s with s + h <= t (target observed); retrained at every origin.
- LibriVox is a separate group with its own models trained on LibriVox rows only; it is evaluated separately.
- The pooled models cover narrow and middle categories and all three Seattle formats; broad is not forecast.

## `NOT IN RECORD` choices (also marked in the code)
1. Target form: the models predict the log-share level, as the record's target reads. No change-from-last-month
   re-parametrisation is used. (If the main session wants one, it needs an addendum before results are read.)
2. Horizon 2 year-ago term: for h = 2 the "target month one year earlier" feature is y(t-10) and the seasonal naive uses
   y(t-10) + (mean t-11..t) - (mean t-23..t-12). For h = 1 these are the record's y(t-11) and formula.
3. Window means (mean of 6 months; 12-month means in the seasonal naive) use the available months and need at least half of them.
4. Interest windows must be complete: the 4-week means, the 8-week Mann-Kendall tau, the 26-week median and the tone windows
   need all their weeks present and not partial; otherwise the feature is missing. Tone: mean of the weekly values over the
   last 4 weeks minus the median over the 26 weeks before those 4.
5. 8-week Mann-Kendall tau is S / 28 on the last 8 weekly shares (no tie correction), computed here, not read from the shifts file.
6. Shift features: the label is three 0/1 columns (sustained, intermediate, fading); "none yet" is all zeros. A label counts
   as given only if its labelling week is on or before the last week and it is one of the three classes (interrupted and
   censored count as none yet). Size so far is the peak ratio to normal over the shift's weeks up to the last week; weeks since
   start is in whole weeks. If several shifts started in the window, the latest one is used. A node-origin with no shift in
   the window gets 0 for the five shift columns; they are missing only when the node has no usable interest series.
7. The conditional split uses Wikipedia shifts only, with `quality_ok` true, started in the 8 weeks up to the last week.
8. Ridge: only numeric columns are standardised; categoricals are one-hot (categories from training rows); 0 plus a 0/1
   indicator for every numeric column with a missing value in the training rows. Alpha is chosen by MAE (ties go to the smaller
   alpha) with models fitted on the training rows whose target month is on or before the first validation origin. With fewer
   than 36 training origins the validation block is a third of them; with fewer than 3 origins the middle alpha is used.
9. CatBoost: all other parameters at CatBoost defaults (l2 leaf regularisation 3, default borders and CTR settings); missing
   numeric values are left to CatBoost; target month is a categorical string.
10. A model is fitted only if the training set has at least 30 rows (LibriVox early on); naive forecasts are always made.
11. Training starts at the first eligible origin in each panel (no earliest-origin cut). Early rows have missing W or G values.
12. Diebold-Mariano: monthly mean absolute errors, p-value from the standard normal (no small-sample correction), lag-3
    Bartlett weights. Bootstrap: overlapping blocks of 3 consecutive test months, not wrapped, resampling the monthly sums of
    absolute errors of both models together; percentile 95% interval; each comparison starts its own generator from the seed.
13. MASE is the model's MAE divided by the seasonal naive MAE on the rows where both exist.
14. Spearman, top-10% hit rate: computed within each (month, format) group (and level when a table is by level), groups with
    fewer than 10 categories skipped; k = ceil(10% of the group). Direction accuracy counts a zero forecast change as wrong.
15. Workers: default 3 (record: at most 4); CatBoost threads per worker = 3 // workers.
16. Interest flow: lags k = 1..8 and 52 are the weeks k weeks before the origin's last week; categoricals are level, broad
    category and target month; no size rule (no demand); the normal level is the median of the 26 weeks before the last week
    (last week excluded); a target month needs all its weeks (a week belongs to the month holding its Sunday); AUC score =
    forecast minus log normal; Spearman uses changes measured from the naive level.
17. Showcase categories are found by their label in `nodes.parquet` (narrow and middle level only).

## Notes for the main session
- In the timing run of one origin, one CatBoost fit and its test-set mean absolute error were printed to check speed. No
  setting was changed afterwards; all code and settings were fixed before that.
