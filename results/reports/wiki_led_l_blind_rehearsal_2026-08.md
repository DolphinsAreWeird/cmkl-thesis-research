# Addendum l, blind test (REHEARSAL on a known month): target 2026-08

Made by `code/main_study/wiki_led/l_books_in_time/l06_score.py --rehearsal` on 2026-10-30 03:50 +06:30 (21:20 UTC). Forecasts: `data/interim/l_rehearsal/forecasts_origin_2026-07.csv`.
Rehearsal: August 2026 is a known month that the backtest has already scored, so these numbers are not a test; they check the code.

- Library totals and the excluded-month rule: print 227,869 against half of 219,992: ok; ebook 284,218 against half of 265,627: ok; audiobook 304,633 against half of 270,520: ok
- Check, totals against the stored panel (here, stored): {'print': [227869, 227869], 'ebook': [284218, 284218], 'audiobook': [304633, 304633]}
- Check, target loans against the stored rows: {'rows_both': 18622, 'only_here': 0, 'only_stored': 0, 'equal': 18617, 'max_abs_diff': 3.0, 'rows_differing': 5}
- Forecast rows 18,622 {'ebook': 6595, 'audiobook': 6396, 'print': 5631}; with an article feature 11,397; base rate rose 0.126, surged 0.0188.

## Decision LB

HMW14 minus HM change rank, paired over works, 95% interval above 0: +0.0040 [+0.0007, +0.0073]; passed: yes.

## Scores (descriptive)

| Model | Change rank | print | ebook | audiobook | Top 20 rose [exact 95%] | Not yet risen, top 20 |
| --- | --- | --- | --- | --- | --- | --- |
| naive | 0.1855 | 0.1346 | 0.2032 | 0.2186 | 0.867 (52/60) [0.754, 0.941] | 0.183 (11/60) |
| H | 0.3189 | 0.3143 | 0.3130 | 0.3292 | 0.817 (49/60) [0.696, 0.905] | 0.433 (26/60) |
| HM | 0.3142 | 0.3104 | 0.3094 | 0.3229 | 0.867 (52/60) [0.754, 0.941] | 0.400 (24/60) |
| W14 | 0.0790 | 0.0352 | 0.0807 | 0.1210 | 0.433 (26/60) [0.306, 0.568] | 0.183 (11/60) |
| HMW14 | 0.3183 | 0.3096 | 0.3141 | 0.3312 | 0.850 (51/60) [0.734, 0.929] | 0.417 (25/60) |

W14 change rank, interval over works: [0.0637, 0.0940].

| Level model | MAE of Y | MAE in loans | Median error in loans |
| --- | --- | --- | --- |
| H | 0.3357 | 2.26 | 1.25 |
| HM | 0.3299 | 2.19 | 1.24 |
| HMW14 | 0.3298 | 2.19 | 1.24 |

HM minus H, MAE of Y: -0.0058 [-0.0065, -0.0052].

Run time 46 s.
