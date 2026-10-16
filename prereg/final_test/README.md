# Final unseen test: frozen forecasts

Files in this folder are forecasts made BEFORE the months they forecast were released by the library. They are records, like the JSON files in `../addenda_benchmark/`: read-only, with a SHA-256 printed in `../README.md`.

| File | What it is |
| --- | --- |
| `forecasts_origin_2026-08.csv` | Forecasts of log share (Study 4 target) made from the data to August 2026, for the target months September, October and November 2026 (horizons 1, 2, 3). One row per series and horizon (714 series: print, ebook and audiobook; narrow and middle themes). Columns: `ls_t` the log share at the origin, `naive` repeat last month, then the pipelines `chronos`, `chronos2`, `chronos2_cur`, `chronos2_curdw`, `chronos2_bk`, `catchg_D`, `catchg_DW`, `catchg_DWS`. |
| `forecasts_origin_2026-08_meta.json` | When they were made, the SHA-256 of the CSV and of every input file, the software versions, the settings, the number of training rows and counts. |

Protocol: `../addenda_benchmark/2026-10-17_c_final_test_forecasts.json` (what was forecast and how). The targets, the scoring and the decision rules are in a later addendum (d), fixed before any month after August 2026 is downloaded.

Check: `shasum -a 256 forecasts_origin_2026-08.csv` must print the value in `../README.md` and in the meta file. The date of publication is the commit time of this repository: https://github.com/DolphinsAreWeird/cmkl-thesis-research.

Code: `code/main_study/benchmark/25_final_test_forecast.py` (`--mode final`), with `_final_test.py`. The code that made them was first run at four known origins and reproduced the stored benchmark forecasts of every pipeline (`results/reports/benchmark_final_test_regression.md`).
