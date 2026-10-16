# Study 4b code: forecasting the change in book-category demand, and catching rare surges, from public interest

Settings are fixed in `prereg/study4b_settings_2026-10-14.json` (SHA-256 in `prereg/README.md`, Study 4b section). It builds on
Study 4 (`prereg/forecast_settings_2026-10-13.json`, `prereg/addenda_forecast/`, `code/main_study/study4/`). Study 4 stays as run.

## Ground rules
- `_settings.py` checks the SHA-256 of both records against `prereg/README.md` (Study 4's through Study 4's own loader, which also
  applies `addenda_forecast/`), applies `prereg/addenda_4b/*.json` (empty today) in file-name order, parses every number from the
  record's wording, and stops on any mismatch (`SettingsError`, a `SystemExit`). Every entry script calls `ST.settings()` first.
- Module names: Study 4 and 4b both have `_settings`. `_s4.py` loads Study 4's modules once with the Study 4 folder first on the path
  and removes them from `sys.modules` again (same method as Study 3b's `_s3.py`); 4b's own modules are named `_b_*.py`. Study 4
  objects are never pickled: each worker loads the settings again (hashes checked again).
- Choices the record does not make are marked `# NOT IN RECORD:` in the code and listed below. No setting is changed after results.
- Machine rule: `--workers` default 3 (record: at most 4), 1 CatBoost thread each (`3 // workers`); run with `nice`.

## Run order (from `code/`, `../.venv/bin/python`)
| Step | Script | Writes | Run time |
| --- | --- | --- | --- |
| 01 | `main_study/study4b/01_features.py` | `data/db/study4b/features.parquet`, `data/reports/study4b_01_features.md` | about 10 s |
| 02 | `main_study/study4b/02_run.py [--workers 3] [--limit-origins N] [--only-origins YYYY-MM,..] [--reset]` | `data/db/study4b/forecast_parts/origin_YYYY-MM.parquet` (one per origin), `forecasts.parquet` | hours (see the report of the run) |
| 03 | `main_study/study4b/03_evaluate.py` | `data/reports/study4b_evaluation.md`, `data/reports/study4b_*.csv` | minutes (bootstrap of AP differences) |

Long job (from the project root): `bash jobs/bg.sh s4b main_study/study4b/02_run.py --workers 3`, then `renice -n 10 -p $(cat data/reports/s4b.pid)`.
Resumable: a part file per origin, written atomically; a restart skips saved origins; parts carry a fingerprint of the features file and
both records (`--reset` to start again). Tests: `.venv/bin/python code/main_study/study4b/tests/run_tests.py [name-filter]`.
| 04 | `main_study/study4b/04_secondary_surges.py --surge-def base98\|pct20 [--workers 3]` | `data/db/study4b/surge_parts_<def>/`, `forecasts_surge_<def>.parquet` | hours per definition |
| 05 | `main_study/study4b/05_evaluate_secondary.py` | `data/reports/study4b_secondary_surges.md`, `study4b_secondary_*.csv` | minutes |

Steps 04 and 05 implement the addendum `prereg/addenda_4b/2026-10-14_a_secondary_surges.json` (base-rate surge with a training-only 98th percentile by format and level; 20% surge). They are reported beside the primary log(1.3) surge, never instead of it. Tests: `tests/test_secondary_surges.py`.

## What is built
- Features: Study 4 D and W features for horizons 1, 2 (read from `data/db/study4/features.parquet`) and 3 (built with Study 4's own code
  from the Study 3 panel and the interest series; the rebuilt h = 1, 2 rows are checked equal to the Study 4 table). Seattle formats only.
  Eligibility is the panel's `size_ok` at the origin, as in Study 4.
- S features: `s_sustained` (a quality_ok Wikipedia shift labelled sustained, started in the 8 weeks up to the origin's last included week,
  labelling week on or before that week) and `s_resp` (mean `sc_effect_p` of the category's own earlier shifts in the same format whose
  month 0 + 2 is on or before the origin month; 0 when none).
- Part A: target = change in log share, d(t+h) - d(t), horizons 1, 2 (primary), 3. Models: zero change, ridge (Study 4 design and alpha rule)
  and CatBoost (record settings, Study 4 trainer) on the change; feature sets D, D+W, D+W+S; walk-forward, expanding window, retrained at every
  origin (training rows: origins s with s + h <= t); test origins 2019-01 to the last origin with a target month.
- Part B (horizon 2): surge = change >= log(1.3). CatBoost classifier (Logloss, same tree settings, same categoricals) and logistic regression,
  D, D+W, D+W+S, retrained at every origin. Metrics: average precision (primary), recall among the 10 highest-scored category-formats per
  origin and format, Brier score, base rate; block-bootstrap interval of the AP difference.
- Evaluation: skill, DM (one-sided, Newey-West lag 3), moving-block bootstrap (block 3, 2,000, seed 20261013), the helps rule, strata
  = format x level (print, ebook; audiobook secondary) and print+ebook pooled at each level (the verdict rows), showcases, and a reference to
  Study 4's level forecasts on the same rows.

## `NOT IN RECORD` choices (also marked in the code)
1. Responsiveness uses Wikipedia shifts in Study 3's main (non-seasonal) analysis only, with a fitted synthetic control (`sc_ok`), all duration
   classes, and the primary-window effect `sc_effect_p` (months 0 to +2). "Same level and format" is read as the category's own node and the
   row's own format; formats are not pooled (the outcome is format-specific). A shift is used at origin t only if month 0 + 2 <= t.
2. The sustained-shift feature counts quality_ok Wikipedia shifts only, with Study 4's window and week alignment (last Monday whose Sunday is
   on or before the last day of the origin month; start in the 8 weeks up to and including that week). It is 0 (never missing) when there is none.
3. Machine rule: 3 workers by default (record: at most 4), 3 threads in all.
4. A model is fitted only if the training set has at least 30 rows (as in Study 4); zero change is always forecast. A classifier whose training
   rows hold one class forecasts the training base rate.
5. Logistic regression: L2, C = 1.0 (scikit-learn default, not tuned), lbfgs, max_iter 2000; same design matrix as Study 4's ridge (numeric
   columns standardised on training rows, 0 plus a missing indicator, one-hot categoricals). No class weights anywhere.
6. Ridge on the change reuses Study 4's alpha rule (grid and 12 validation origins from the Study 4 record, MAE, ties to the smaller alpha).
7. The change models use the same feature columns as Study 4 (the level `ls_t` stays a feature); `tmonth` is the target month, as in Study 4.
8. Models are pooled over narrow and middle categories and the three Seattle formats (as in Study 4); LibriVox is not part of 4b.
9. Recall among the top 10: groups are the origins x formats of a stratum (so within a level in the level strata); recall = surges in the
   top 10 / surges, summed over groups that have a surge; the random-ranking expectation is reported beside it. Groups with fewer than 10 members use all members.
10. AP is computed by ranking the scores (ties broken by row order); the bootstrap resamples whole test months (overlapping blocks of 3, not
    wrapped), all rows of a drawn month entering the resample; draws with no surge are dropped. Each comparison starts its own generator from the seed.
11. The helps rule uses the primary horizon 2; the bootstrap interval for skill is a percentile interval at 95% (the record says "bootstrap
    interval"; Part B says 95%). Pooled verdict rows are print and ebook pooled at each level; format x level rows are shown beside them.
12. The DM test and block bootstrap follow Study 4's implementation (monthly mean absolute errors, standard normal p-value, Bartlett weights;
    skill bootstrap over monthly sums of absolute errors). Skill compares the new model against the base on the rows where both have a forecast.
13. `forecasts.parquet` of Study 4 is used only in a reference table (Study 4's CatBoost D level forecast against zero change and the 4b CatBoost D
    change model on the same rows, horizons 1 and 2).
14. Showcases are found by label in `nodes.parquet` (narrow and middle level; every match is shown) and use the horizon-2 forecasts of the named origin.
15. Tests use fewer CatBoost trees (60 to 150) than the record's 600 on small simulated worlds; the real run uses the record's settings.
