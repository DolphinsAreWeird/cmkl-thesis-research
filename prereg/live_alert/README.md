# Live test: Wikipedia-only alert list for October 2026

- Made and frozen: 2026-10-20 17:00 +07, by code/main_study/wiki_led/12_live_alert_october.py, before the Seattle Public Library released September or October 2026 (the open data held months to 2026-08; no later month has been downloaded or read).
- Inputs: English Wikipedia weekly views of each book's own article and its author's article up to the week ending 27 September 2026 (data to 30 September). No library data after August 2026; the model (Test A's W_lgbm: Wikipedia features only, change target) was trained on every Test A row whose target month is at most 2026-08.
- Books: the 7,650 Test A books with at least one loan in 2025-09 to 2026-08.
- Files: `alert_list_2026-10.csv` (top 50 with reasons), `ranking_all_2026-10.csv` (all 7,650 books ranked).

## How it will be scored (fixed now, once, when the library has released September and October 2026)
- For each of the 7,650 books: L = October 2026 loans (all formats); M6 = median of monthly loans over April to September 2026, months failing the benchmark's month_ok rule treated as missing.
- Rose: ln(1+L) - ln(1+M6) >= ln 1.5. Surged: ln(1+L) - ln(1+M6) >= ln 2 and L - M6 >= 5.
- Reported: share of the top 20 and top 50 that rose and that surged, with exact binomial 95% intervals, beside the base rate over all 7,650 books, and beside the backtest of 2019 to 2026 (top 20: 59% rose, 40% surged; top 50: 48% and 30%; base about 11% and 3%).
- Main statement: the top-20 share that rose is above the base rate. Whatever the result, it is reported.
