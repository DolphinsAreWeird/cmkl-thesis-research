# Final test, regression check: the final-test code at known origins against the stored benchmark forecasts

Written 2026-10-17 03:29. Code: code/main_study/benchmark/25_final_test_forecast.py (mode regression). The same code that makes the frozen forecasts is run at origins whose target months are known, and its forecasts are compared row by row with the forecasts stored from the benchmark (data/db/benchmark/wide2.parquet). Differences are in log-share units.

| Origin | Horizon | Pipeline | Rows compared | Rows only in one | Max abs difference | Mean abs difference | Rows differing by more than the limit |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2026-05 | 1 | naive | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 2 | naive | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 3 | naive | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 1 | chronos | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 2 | chronos | 713 | 0 | 4.77e-07 | 1.34e-09 | 0 |
| 2026-05 | 3 | chronos | 713 | 0 | 9.54e-07 | 3.18e-08 | 0 |
| 2026-05 | 1 | chronos2 | 713 | 0 | 4.77e-07 | 4.01e-08 | 0 |
| 2026-05 | 2 | chronos2 | 713 | 0 | 4.77e-07 | 4.38e-08 | 0 |
| 2026-05 | 3 | chronos2 | 713 | 0 | 4.77e-07 | 4.61e-08 | 0 |
| 2026-05 | 1 | chronos2_cur | 713 | 0 | 9.54e-07 | 4.61e-08 | 0 |
| 2026-05 | 2 | chronos2_cur | 713 | 0 | 4.77e-07 | 4.31e-08 | 0 |
| 2026-05 | 3 | chronos2_cur | 713 | 0 | 4.77e-07 | 4.78e-08 | 0 |
| 2026-05 | 1 | chronos2_curdw | 713 | 0 | 7.15e-07 | 4.55e-08 | 0 |
| 2026-05 | 2 | chronos2_curdw | 713 | 0 | 4.77e-07 | 4.11e-08 | 0 |
| 2026-05 | 3 | chronos2_curdw | 713 | 0 | 4.77e-07 | 4.85e-08 | 0 |
| 2026-05 | 1 | chronos2_bk | 713 | 0 | 4.77e-07 | 5.38e-08 | 0 |
| 2026-05 | 2 | chronos2_bk | 713 | 0 | 4.77e-07 | 5.32e-08 | 0 |
| 2026-05 | 3 | chronos2_bk | 713 | 0 | 4.77e-07 | 4.75e-08 | 0 |
| 2026-05 | 1 | catchg_D | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 2 | catchg_D | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 3 | catchg_D | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 1 | catchg_DW | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 2 | catchg_DW | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 3 | catchg_DW | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 1 | catchg_DWS | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 2 | catchg_DWS | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-05 | 3 | catchg_DWS | 713 | 0 | 0.00e+00 | 0.00e+00 | 0 |
| 2026-06 | 1 | naive | 713 | 0 | 6.54e-03 | 1.79e-04 | 0 |
| 2026-06 | 2 | naive | 713 | 0 | 6.54e-03 | 1.79e-04 | 0 |
| 2026-06 | 1 | chronos | 713 | 0 | 7.27e-03 | 1.46e-04 | 0 |
| 2026-06 | 2 | chronos | 713 | 0 | 6.60e-03 | 1.35e-04 | 0 |
| 2026-06 | 1 | chronos2 | 713 | 0 | 6.11e-03 | 1.40e-04 | 0 |
| 2026-06 | 2 | chronos2 | 713 | 0 | 6.16e-03 | 1.31e-04 | 0 |
| 2026-06 | 1 | chronos2_cur | 713 | 0 | 6.34e-03 | 1.44e-04 | 0 |
| 2026-06 | 2 | chronos2_cur | 713 | 0 | 6.35e-03 | 1.38e-04 | 0 |
| 2026-06 | 1 | chronos2_curdw | 713 | 0 | 5.79e-03 | 1.41e-04 | 0 |
| 2026-06 | 2 | chronos2_curdw | 713 | 0 | 5.91e-03 | 1.37e-04 | 0 |
| 2026-06 | 1 | chronos2_bk | 713 | 0 | 5.74e-03 | 1.40e-04 | 0 |
| 2026-06 | 2 | chronos2_bk | 713 | 0 | 5.80e-03 | 1.33e-04 | 0 |
| 2026-06 | 1 | catchg_D | 713 | 0 | 2.72e-02 | 1.93e-03 | 0 |
| 2026-06 | 2 | catchg_D | 713 | 0 | 2.69e-02 | 3.98e-03 | 0 |
| 2026-06 | 1 | catchg_DW | 713 | 0 | 1.73e-02 | 1.79e-03 | 0 |
| 2026-06 | 2 | catchg_DW | 713 | 0 | 5.11e-02 | 4.57e-03 | 1 |
| 2026-06 | 1 | catchg_DWS | 713 | 0 | 2.91e-02 | 2.02e-03 | 0 |
| 2026-06 | 2 | catchg_DWS | 713 | 0 | 5.49e-02 | 4.41e-03 | 1 |
| 2026-07 | 1 | naive | 714 | 0 | 1.27e-02 | 3.44e-04 | 0 |
| 2026-07 | 1 | chronos | 714 | 0 | 1.14e-02 | 2.93e-04 | 0 |
| 2026-07 | 1 | chronos2 | 714 | 0 | 1.14e-02 | 2.90e-04 | 0 |
| 2026-07 | 1 | chronos2_cur | 714 | 0 | 1.10e-02 | 2.89e-04 | 0 |
| 2026-07 | 1 | chronos2_curdw | 714 | 0 | 1.20e-02 | 2.87e-04 | 0 |
| 2026-07 | 1 | chronos2_bk | 714 | 0 | 1.22e-02 | 2.89e-04 | 0 |
| 2026-07 | 1 | catchg_D | 714 | 0 | 2.04e-02 | 2.73e-03 | 0 |
| 2026-07 | 1 | catchg_DW | 714 | 0 | 2.25e-02 | 2.45e-03 | 0 |
| 2026-07 | 1 | catchg_DWS | 714 | 0 | 2.50e-02 | 2.93e-03 | 0 |

Result: DIFFERENCES FOUND (see the rows above); the final forecasts must not be made until they are explained.

## How to read this report (note added after reading it, 2026-10-17 03:50)

This run is on the dry-run world with the freeze month 2026-06 (`27_final_test_dryrun.py`), where the inputs of the months from 2026-06 on come from the extension rule of `_final_extend.py`, so differences from the stored forecasts are expected from origin 2026-06 on. The line 'DIFFERENCES FOUND' above only says that two rows exceeded the tolerance of 0.05 set for this run. What the table shows:

- Origin 2026-05, whose inputs are identical to the stored ones: naive and CatBoost reproduce the stored forecasts exactly and the Chronos models to within 1e-6, at all three horizons.
- Origins 2026-06 and 2026-07, with inputs from the extension: the mean absolute difference is at most 0.0046 for CatBoost and 0.0003 for the Chronos models (the mean absolute forecast error is about 0.05).
- The two rows beyond 0.05 (0.0511 and 0.0549: CatBoost D+W and D+W+S, origin 2026-06, horizon 2) come from the few narrow themes with a very small share whose log share the extension changes by 0.04 to 0.06. In the dry-run panel only 5 of 3,123 series-months differ from the stored panel by more than 0.03: audiobook 'rhetoric / public speaking', 'critical theory / critical thinking' and 'existentialism / fate and destiny', and ebook 'critical theory / critical thinking'.
