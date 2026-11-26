# The Transformer check, blind month (REHEARSAL on a known month): 2026-08

Made by `code/main_study/wiki_led/o_transformer_check/o06_blind_score.py --rehearsal` on 2026-11-26 15:03 +0700 (08:03 UTC). Forecasts: walk-forward predictions at origin 2026-07 (rehearsal). Rules: `prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json`, O3.

18,622 book-format rows; 12.6% of them rose by half or more.

| Model | Change rank | Print | Ebook | Audiobook | Top 20 that rose | Early-warning top 20 |
| --- | --- | --- | --- | --- | --- | --- |
| This month minus the six-month average (no model) | 0.185 | 0.135 | 0.203 | 0.219 | 0.87 (0.75 to 0.94) | 0.18 |
| Library + own and author pages | 0.318 | 0.310 | 0.313 | 0.331 | 0.85 (0.73 to 0.93) | 0.37 |
| ... + the two Transformer forecasts | 0.334 | 0.318 | 0.332 | 0.354 | 0.92 (0.82 to 0.97) | 0.48 |
| ... + the same 60 months in plain form | 0.337 | 0.325 | 0.331 | 0.357 | 0.88 (0.77 to 0.95) | 0.55 |
| ... + plain 60 months + the two Transformer forecasts | 0.342 | 0.326 | 0.338 | 0.363 | 0.93 (0.84 to 0.98) | 0.50 |

| Comparison | Difference (95% interval) | Rule |
| --- | --- | --- |
| Transformer forecasts added to library + own pages | +0.0168 (+0.0107 to +0.0229) | passed |
| Transformer forecasts added on top of the plain 60 months | +0.0050 (+0.0020 to +0.0081) | passed |
| Plain 60 months added to library + own pages | +0.0198 (+0.0127 to +0.0269) | no rule |

One month is a small test; it adds to the backtest, it does not replace it.

