# Study 1 reruns with the fixed pipeline (14 Oct 2026)

Plain summary: all three results hold. No conclusion changes. Small numbers moved by at most about 0.01 AUC (tree models) or 0.006 Spearman.

## What was fixed and how
- Narrator catalogue count: new function code/study1_rerun/pit.py counts only the same narrator's recordings released strictly before the target. The old features.py counted every recording the narrator ever made, including later ones. Test: code/study1_rerun/tests/test_pit.py (5 tests, all pass; includes a check that adding later recordings never changes an earlier count, a brute-force comparison, and a real-data check).
- Narrator identity is given to CatBoost only in history stages (the walk-forward script walkforward3_fix.py already did this). Experiment 1 has no history stage, so CatBoost there gets no narrator identity.
- Reruns 1 and 2 use walkforward3_fix.py unchanged (the pipeline behind wf3fix_full_m2to7.csv; it counts the narrator catalogue point in time, with same-timestamp recordings counted in file order, never a later timestamp). Reruns 3 uses new copies exp1_fixed.py and shapley_fixed.py. Old scripts and old outputs are untouched.
- Libraries as in requirements.lock; threads capped at 3; nice 10; one job at a time (log s1_rerun.log). Tree-model quarter results differ by about 0.01 between library versions, so differences below about 0.015 are not meaningful.

## Rerun 1: launch-window comparison (ridge, top 20% AUC, full pre-release inputs, 20 quarters 2020Q1 to 2024Q4)
Windows are the same seven as the old comparison (walkforward3.py via run_wf3.sh).
| Window (months after release month) | Includes month 1 | Old | New |
|---|---|---|---|
| 1-3 | yes | 0.602 | 0.602 |
| 1-6 | yes | 0.634 | 0.634 |
| 1-12 | yes | 0.665 | 0.665 |
| 2-4 | no | 0.767 | 0.768 |
| 2-7 | no | 0.771 | 0.772 |
| 3-8 | no | 0.763 | 0.763 |
| 2-13 | no | 0.729 | 0.729 |

Old: 0.60-0.66 with month 1, 0.73-0.77 without. New: 0.60-0.67 with, 0.73-0.77 without. Conclusion unchanged: windows that include the launch month are much harder to predict. (LightGBM columns are in the CSV; same pattern.) File: study1_reruns_1_launch_window.csv.

## Rerun 2: after launch, month 1 known (months 2-7, 20 quarters)
| Model | Old AUC | New AUC | Old hit rate top 10% | New hit rate |
|---|---|---|---|---|
| CatBoost | 0.832 | 0.829 | 37.2% | 36.0% |
| LightGBM | 0.830 | 0.833 | 38.5% | 37.7% |
| Ridge | 0.820 | 0.820 | 35.4% | 35.0% |
Old: CatBoost AUC 0.83, LightGBM hit rate 39%. New: CatBoost 0.83, LightGBM hit rate 38%. Conclusion unchanged (knowing month 1 lifts AUC from about 0.77 to about 0.83). All six models are in study1_reruns_2_after_launch.csv.

## Rerun 3: Experiment 1 (grouped CV, 5 folds x 3 repeats, grouped by book, released from July 2016)
Source gains (mean change in Spearman per step, 8 non-floor models; significant = bootstrap interval above 0):
| Step | Label | Old mean gain, models significant | New mean gain, models significant |
|---|---|---|---|
| + Wikipedia volume | views | +0.027, 8 of 8 | +0.030, 8 of 8 |
| + Wikipedia volume | favorites | +0.071, 8 of 8 | +0.077, 8 of 8 |
| + Wikipedia trend | views | -0.001, 3 of 8 | +0.003, 4 of 8 |
| + Wikipedia trend | favorites | -0.005, 1 of 8 | -0.003, 2 of 8 |
| + Goodreads | views | +0.007, 3 of 8 | +0.005, 2 of 8 |
| + Goodreads | favorites | +0.025, 8 of 8 | +0.026, 8 of 8 |
| + text | views | +0.006, 3 of 8 | +0.006, 2 of 8 |
| + text | favorites | +0.057, 8 of 8 | +0.069, 8 of 8 |

Wikipedia volume helps all 8 models on both labels, Goodreads and text help all 8 on favorites, and Wikipedia trend helps only boosted trees (CatBoost, LightGBM, LambdaMART; plus random forest on views). All as before. Per-model gains and intervals: study1_reruns_3_exp1_gains.csv; mean Spearman per model and stage: study1_reruns_3_exp1_spearman.csv.

Source Shapley (LightGBM, views, Spearman):
| Source | Old | New |
|---|---|---|
| Metadata | 0.142 | 0.135 |
| Text | 0.076 | 0.080 |
| Wikipedia trend | 0.037 | 0.038 |
| Wikipedia volume | 0.035 | 0.034 |
Order unchanged (metadata, text, trend, volume). Metadata fell by 0.007, consistent with a small leak removed. File: study1_reruns_3_shapley.csv.

## Verdict
Rerun 1: no change. Rerun 2: no change. Rerun 3: no change (the "PRE-FIX" labels in context/07_results.md can be replaced with the new values above).

## Files
code/study1_rerun/ (pit.py, tests/test_pit.py, exp1_fixed.py, shapley_fixed.py, run_wf_limited.py, run_all.py, report.py, threads.py). Outputs in data/reports/: wf3fix_robust_m*.csv, wf3fix_early_m2to7.csv, results3fix_y_view.csv, results3fix_y_fav.csv, shapley3fix_*.{csv,json}, study1_reruns_*.csv.
