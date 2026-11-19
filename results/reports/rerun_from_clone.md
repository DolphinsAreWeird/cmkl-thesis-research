# Rerun from a fresh copy of the public repository

Record: prereg/DEVIATIONS.md, 19 November 2026, part C. Repository commit `e3b3032`, a new environment from `requirements.lock` (Python 3.12.11), `30_test_b.py` and `l_books_in_time/l04_backtest.py` run unchanged on copies of their stored inputs. Not independent of the author.

| Table 5.1 | Printed | Rerun | Same at printed precision |
| --- | --- | --- | --- |
| main set, Wikipedia alone | 0.091 | 0.0911 | yes |
| main set, library model | 0.347 | 0.3474 | yes |
| main set, library and Wikipedia | 0.352 | 0.3521 | yes |
| main set, added by Wikipedia | 0.005 | 0.0047 | yes |
| new books, Wikipedia alone | 0.127 | 0.1273 | yes |
| new books, library model | 0.349 | 0.3487 | yes |
| new books, library and Wikipedia | 0.372 | 0.3724 | yes |
| new books, added by Wikipedia | 0.024 | 0.0237 | yes |

| Output | Numbers or rows compared | Largest absolute difference | Differences above 1e-9 |
| --- | --- | --- | --- |
| report `wiki_led_test_b.json` | 336 numbers | 0.00e+00 | 0 |
| report `wiki_led_l_backtest.json` | 1,549 numbers | 3.23e-07 | 13 |
| predictions `test_b_preds` | 134,970 rows (same shape: yes) | 0.00e+00 | |
| predictions `l_preds` | 1,258,807 rows (same shape: yes) | 7.58e-03 | |
