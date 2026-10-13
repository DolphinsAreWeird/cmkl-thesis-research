# Study 4, step 03: evaluation

Made 2026-10-13 22:55. Record SHA-256 `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`. Forecasts: 955,578 rows from 91 origins (2019-01 to 2026-07). Skill = 1 - MAE(new) / MAE(base); a positive skill means the new model has the smaller error. Errors are on the log-share scale. Only category-format-months with an observed target month and an observed month t are scored.

## 1. Main comparison: CatBoost D+W against CatBoost D, horizon 1 (Seattle)

Test origins 2019-01 to 2026-07. Bootstrap: moving blocks of 3 months, 2,000 resamples, seed 20261013, 95% percentile interval. DM: one-sided, Newey-West lag 3.

| scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | audiobook | middle | 6,528 | 86 | 0.048 | 0.047 | 0.024 | -0.004 | 0.063 | 1.273 | 0.101 | no |
| format x level | audiobook | narrow | 9,557 | 86 | 0.054 | 0.054 | 0.006 | -0.008 | 0.025 | 0.542 | 0.294 | no |
| format x level | ebook | middle | 7,022 | 86 | 0.043 | 0.042 | 0.024 | -0.006 | 0.070 | 1.187 | 0.118 | no |
| format x level | ebook | narrow | 12,086 | 86 | 0.049 | 0.049 | 0.009 | -0.004 | 0.024 | 1.139 | 0.127 | no |
| format x level | print | middle | 6,831 | 81 | 0.059 | 0.060 | -0.023 | -0.068 | 0.011 | -0.991 | 0.839 | no |
| format x level | print | narrow | 13,463 | 81 | 0.063 | 0.064 | -0.024 | -0.056 | -0.002 | -1.380 | 0.916 | no |
| formats pooled | all | middle | 20,381 | 89 | 0.050 | 0.050 | 0.005 | -0.023 | 0.037 | 0.244 | 0.404 | no |
| formats pooled | all | narrow | 35,106 | 89 | 0.056 | 0.056 | -0.006 | -0.026 | 0.009 | -0.738 | 0.770 | no |
| all pooled | all | all | 55,487 | 89 | 0.054 | 0.054 | -0.002 | -0.024 | 0.018 | -0.318 | 0.625 | no |

### MAE of every model on the same rows

| scope | format | level | n | mae naive | mae seasonal_naive | mae ridge/D | mae ridge/D+W | mae catboost/D | mae catboost/D+W |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | audiobook | middle | 6,281 | 0.0439 | 0.0915 | 0.0435 | 0.0433 | 0.0482 | 0.0471 |
| format x level | audiobook | narrow | 9,120 | 0.0526 | 0.1137 | 0.0519 | 0.0518 | 0.0544 | 0.0540 |
| format x level | ebook | middle | 6,771 | 0.0377 | 0.0856 | 0.0389 | 0.0389 | 0.0434 | 0.0423 |
| format x level | ebook | narrow | 11,620 | 0.0461 | 0.1109 | 0.0474 | 0.0473 | 0.0493 | 0.0489 |
| format x level | print | middle | 6,160 | 0.0515 | 0.0975 | 0.0500 | 0.0500 | 0.0547 | 0.0565 |
| format x level | print | narrow | 12,121 | 0.0618 | 0.1210 | 0.0598 | 0.0599 | 0.0614 | 0.0629 |
| formats pooled | all | middle | 19,212 | 0.0441 | 0.0914 | 0.0439 | 0.0439 | 0.0486 | 0.0484 |
| formats pooled | all | narrow | 32,861 | 0.0537 | 0.1154 | 0.0532 | 0.0532 | 0.0552 | 0.0555 |
| all pooled | all | all | 52,073 | 0.0502 | 0.1065 | 0.0498 | 0.0498 | 0.0528 | 0.0529 |

## 2. Helps-rule verdicts (horizon 1)

Interest helps if skill > 0, the 95% bootstrap interval is above zero and DM p < 0.05. The overall verdict uses all formats pooled at each level.

- Overall, middle level: **interest does not help** (skill 0.005, interval -0.023 to 0.037, DM p 0.404).
- Overall, narrow level: **interest does not help** (skill -0.006, interval -0.026 to 0.009, DM p 0.770).
- audiobook, middle: does not help (skill 0.024, DM p 0.101).
- audiobook, narrow: does not help (skill 0.006, DM p 0.294).
- ebook, middle: does not help (skill 0.024, DM p 0.118).
- ebook, narrow: does not help (skill 0.009, DM p 0.127).
- print, middle: does not help (skill -0.023, DM p 0.839).
- print, narrow: does not help (skill -0.024, DM p 0.916).

## 3. Secondary metrics (horizon 1)

MASE: MAE divided by the seasonal naive MAE (below 1 beats it). Spearman: across categories within each month and format, forecast change against actual change, averaged over months (groups of fewer than 10 categories skipped). Top-10% hit rate: base rate 10%. Direction accuracy: category-months with |actual change| > 0.1.

| scope | format | level | model | n | mase | spearman | top_hit | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | audiobook | middle | ridge/D | 6,528 | 0.475 | 0.187 | 0.206 | 0.661 |
| format x level | audiobook | middle | ridge/D+W | 6,528 | 0.474 | 0.198 | 0.227 | 0.673 |
| format x level | audiobook | middle | catboost/D | 6,528 | 0.527 | 0.200 | 0.192 | 0.661 |
| format x level | audiobook | middle | catboost/D+W | 6,528 | 0.514 | 0.203 | 0.200 | 0.679 |
| format x level | audiobook | narrow | ridge/D | 9,557 | 0.457 | 0.178 | 0.186 | 0.652 |
| format x level | audiobook | narrow | ridge/D+W | 9,557 | 0.456 | 0.183 | 0.212 | 0.662 |
| format x level | audiobook | narrow | catboost/D | 9,557 | 0.479 | 0.198 | 0.195 | 0.659 |
| format x level | audiobook | narrow | catboost/D+W | 9,557 | 0.475 | 0.198 | 0.191 | 0.671 |
| format x level | ebook | middle | ridge/D | 7,022 | 0.454 | 0.130 | 0.182 | 0.664 |
| format x level | ebook | middle | ridge/D+W | 7,022 | 0.454 | 0.141 | 0.186 | 0.698 |
| format x level | ebook | middle | catboost/D | 7,022 | 0.507 | 0.166 | 0.170 | 0.711 |
| format x level | ebook | middle | catboost/D+W | 7,022 | 0.494 | 0.169 | 0.167 | 0.730 |
| format x level | ebook | narrow | ridge/D | 12,086 | 0.427 | 0.132 | 0.170 | 0.633 |
| format x level | ebook | narrow | ridge/D+W | 12,086 | 0.426 | 0.138 | 0.172 | 0.641 |
| format x level | ebook | narrow | catboost/D | 12,086 | 0.445 | 0.171 | 0.165 | 0.661 |
| format x level | ebook | narrow | catboost/D+W | 12,086 | 0.441 | 0.162 | 0.178 | 0.665 |
| format x level | print | middle | ridge/D | 6,831 | 0.512 | 0.267 | 0.235 | 0.706 |
| format x level | print | middle | ridge/D+W | 6,831 | 0.513 | 0.275 | 0.251 | 0.721 |
| format x level | print | middle | catboost/D | 6,831 | 0.561 | 0.263 | 0.225 | 0.701 |
| format x level | print | middle | catboost/D+W | 6,831 | 0.579 | 0.258 | 0.229 | 0.691 |
| format x level | print | narrow | ridge/D | 13,463 | 0.494 | 0.275 | 0.218 | 0.691 |
| format x level | print | narrow | ridge/D+W | 13,463 | 0.495 | 0.276 | 0.223 | 0.701 |
| format x level | print | narrow | catboost/D | 13,463 | 0.507 | 0.262 | 0.236 | 0.673 |
| format x level | print | narrow | catboost/D+W | 13,463 | 0.520 | 0.255 | 0.229 | 0.676 |
| formats pooled | all | middle | ridge/D | 20,381 | 0.481 | 0.193 | 0.207 | 0.682 |
| formats pooled | all | middle | ridge/D+W | 20,381 | 0.481 | 0.203 | 0.221 | 0.701 |
| formats pooled | all | middle | catboost/D | 20,381 | 0.532 | 0.208 | 0.195 | 0.690 |
| formats pooled | all | middle | catboost/D+W | 20,381 | 0.530 | 0.209 | 0.198 | 0.695 |
| formats pooled | all | narrow | ridge/D | 35,106 | 0.461 | 0.193 | 0.191 | 0.668 |
| formats pooled | all | narrow | ridge/D+W | 35,106 | 0.461 | 0.197 | 0.202 | 0.678 |
| formats pooled | all | narrow | catboost/D | 35,106 | 0.478 | 0.209 | 0.198 | 0.667 |
| formats pooled | all | narrow | catboost/D+W | 35,106 | 0.481 | 0.204 | 0.199 | 0.672 |
| all pooled | all | all | ridge/D | 55,487 | 0.467 | 0.194 | 0.201 | 0.672 |
| all pooled | all | all | ridge/D+W | 55,487 | 0.467 | 0.199 | 0.212 | 0.684 |
| all pooled | all | all | catboost/D | 55,487 | 0.495 | 0.209 | 0.197 | 0.673 |
| all pooled | all | all | catboost/D+W | 55,487 | 0.496 | 0.206 | 0.197 | 0.679 |

## 4. Conditional split: shift months and other months (horizon 1)

"Shift months": a quality-ok Wikipedia interest shift started in the 8 weeks before the origin. The quality flag only splits the scoring; it is never a feature.

| split | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shift months | format x level | audiobook | middle | 245 | 77 | 0.075 | 0.069 | 0.081 | -0.003 | 0.172 | 1.856 | 0.032 | no |
| shift months | format x level | audiobook | narrow | 406 | 83 | 0.071 | 0.069 | 0.021 | -0.021 | 0.063 | 0.975 | 0.165 | no |
| shift months | format x level | ebook | middle | 272 | 80 | 0.061 | 0.059 | 0.034 | -0.040 | 0.125 | 0.937 | 0.174 | no |
| shift months | format x level | ebook | narrow | 489 | 86 | 0.058 | 0.058 | 0.014 | -0.020 | 0.055 | 0.553 | 0.290 | no |
| shift months | format x level | print | middle | 236 | 75 | 0.069 | 0.073 | -0.071 | -0.192 | 0.026 | -1.285 | 0.901 | no |
| shift months | format x level | print | narrow | 512 | 80 | 0.075 | 0.081 | -0.083 | -0.200 | 0.024 | -0.550 | 0.709 | no |
| shift months | formats pooled | all | middle | 753 | 83 | 0.068 | 0.067 | 0.018 | -0.041 | 0.082 | 1.087 | 0.138 | no |
| shift months | formats pooled | all | narrow | 1,407 | 89 | 0.068 | 0.070 | -0.023 | -0.090 | 0.031 | 0.103 | 0.459 | no |
| shift months | all pooled | all | all | 2,160 | 89 | 0.068 | 0.069 | -0.009 | -0.069 | 0.045 | 0.687 | 0.246 | no |
| other months | format x level | audiobook | middle | 6,283 | 86 | 0.047 | 0.046 | 0.020 | -0.006 | 0.058 | 1.117 | 0.132 | no |
| other months | format x level | audiobook | narrow | 9,151 | 86 | 0.054 | 0.053 | 0.005 | -0.009 | 0.023 | 0.415 | 0.339 | no |
| other months | format x level | ebook | middle | 6,750 | 86 | 0.043 | 0.042 | 0.024 | -0.006 | 0.069 | 1.188 | 0.117 | no |
| other months | format x level | ebook | narrow | 11,597 | 86 | 0.049 | 0.048 | 0.009 | -0.004 | 0.023 | 1.145 | 0.126 | no |
| other months | format x level | print | middle | 6,595 | 81 | 0.058 | 0.060 | -0.021 | -0.064 | 0.011 | -0.981 | 0.837 | no |
| other months | format x level | print | narrow | 12,951 | 81 | 0.063 | 0.064 | -0.021 | -0.049 | -0.002 | -1.398 | 0.919 | no |
| other months | formats pooled | all | middle | 19,628 | 89 | 0.049 | 0.049 | 0.005 | -0.022 | 0.035 | 0.191 | 0.424 | no |
| other months | formats pooled | all | narrow | 33,699 | 89 | 0.055 | 0.056 | -0.005 | -0.022 | 0.009 | -0.770 | 0.779 | no |
| other months | all pooled | all | all | 53,327 | 89 | 0.053 | 0.053 | -0.002 | -0.022 | 0.017 | -0.354 | 0.638 | no |

## 5. Horizon 2 (target month t+2, same information)

| scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | audiobook | middle | 6,364 | 84 | 0.062 | 0.061 | 0.016 | -0.037 | 0.069 | 0.541 | 0.294 | no |
| format x level | audiobook | narrow | 9,271 | 84 | 0.070 | 0.069 | 0.011 | -0.015 | 0.040 | 0.675 | 0.250 | no |
| format x level | ebook | middle | 6,856 | 84 | 0.056 | 0.055 | 0.010 | -0.047 | 0.064 | 0.313 | 0.377 | no |
| format x level | ebook | narrow | 11,783 | 84 | 0.064 | 0.063 | 0.004 | -0.019 | 0.035 | 0.227 | 0.410 | no |
| format x level | print | middle | 6,577 | 78 | 0.088 | 0.087 | 0.020 | -0.014 | 0.047 | 1.104 | 0.135 | no |
| format x level | print | narrow | 12,953 | 78 | 0.088 | 0.086 | 0.020 | -0.003 | 0.043 | 1.410 | 0.079 | no |
| formats pooled | all | middle | 19,797 | 87 | 0.069 | 0.067 | 0.016 | -0.024 | 0.054 | 0.813 | 0.208 | no |
| formats pooled | all | narrow | 34,007 | 87 | 0.074 | 0.074 | 0.013 | -0.007 | 0.035 | 1.139 | 0.127 | no |
| all pooled | all | all | 53,804 | 87 | 0.072 | 0.071 | 0.014 | -0.012 | 0.042 | 0.986 | 0.162 | no |

## 6. GDELT and tone, over the shorter period

Origins 2019-01 to 2021-05 (15,999 rows). Only categories GDELT covers have GDELT features; the others carry missing values in the G and T sets.

| comparison | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D+W against D (same period) | format x level | audiobook | middle | 1,966 | 29 | 0.049 | 0.049 | -0.001 | -0.019 | 0.018 | -0.167 | 0.566 | no |
| D+W against D (same period) | format x level | audiobook | narrow | 2,272 | 29 | 0.056 | 0.056 | -0.006 | -0.020 | 0.009 | -0.929 | 0.823 | no |
| D+W against D (same period) | format x level | ebook | middle | 2,284 | 29 | 0.044 | 0.044 | -0.011 | -0.029 | 0.001 | -1.450 | 0.926 | no |
| D+W against D (same period) | format x level | ebook | narrow | 3,598 | 29 | 0.051 | 0.051 | -0.003 | -0.012 | 0.007 | -0.753 | 0.774 | no |
| D+W against D (same period) | format x level | print | middle | 1,877 | 22 | 0.089 | 0.093 | -0.049 | -0.141 | 0.030 | -0.905 | 0.817 | no |
| D+W against D (same period) | format x level | print | narrow | 4,002 | 22 | 0.079 | 0.084 | -0.054 | -0.126 | 0.002 | -1.293 | 0.902 | no |
| D+W against D (same period) | formats pooled | all | middle | 6,127 | 29 | 0.059 | 0.061 | -0.026 | -0.072 | 0.011 | -1.127 | 0.870 | no |
| D+W against D (same period) | formats pooled | all | narrow | 9,872 | 29 | 0.064 | 0.065 | -0.030 | -0.078 | 0.002 | -1.322 | 0.907 | no |
| D+W against D (same period) | all pooled | all | all | 15,999 | 29 | 0.062 | 0.064 | -0.028 | -0.075 | 0.003 | -1.283 | 0.900 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | audiobook | middle | 1,966 | 29 | 0.049 | 0.049 | -0.006 | -0.024 | 0.012 | -0.623 | 0.733 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | audiobook | narrow | 2,272 | 29 | 0.056 | 0.056 | 0.000 | -0.018 | 0.015 | 0.006 | 0.498 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | ebook | middle | 2,284 | 29 | 0.044 | 0.045 | -0.016 | -0.030 | -0.001 | -2.402 | 0.992 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | ebook | narrow | 3,598 | 29 | 0.051 | 0.051 | -0.003 | -0.016 | 0.011 | -0.369 | 0.644 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | print | middle | 1,877 | 22 | 0.093 | 0.091 | 0.021 | -0.102 | 0.134 | 0.296 | 0.384 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | print | narrow | 4,002 | 22 | 0.084 | 0.080 | 0.043 | -0.034 | 0.127 | 0.811 | 0.209 | no |
| D+W+G against D+W (adds GDELT volume) | formats pooled | all | middle | 6,127 | 29 | 0.061 | 0.061 | 0.004 | -0.058 | 0.070 | 0.127 | 0.449 | no |
| D+W+G against D+W (adds GDELT volume) | formats pooled | all | narrow | 9,872 | 29 | 0.065 | 0.064 | 0.021 | -0.020 | 0.081 | 0.734 | 0.232 | no |
| D+W+G against D+W (adds GDELT volume) | all pooled | all | all | 15,999 | 29 | 0.064 | 0.063 | 0.015 | -0.035 | 0.077 | 0.491 | 0.312 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | audiobook | middle | 1,966 | 29 | 0.049 | 0.049 | 0.005 | -0.011 | 0.024 | 0.629 | 0.265 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | audiobook | narrow | 2,272 | 29 | 0.056 | 0.057 | -0.005 | -0.016 | 0.012 | -0.384 | 0.649 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | ebook | middle | 2,284 | 29 | 0.045 | 0.045 | 0.008 | -0.006 | 0.029 | 0.914 | 0.180 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | ebook | narrow | 3,598 | 29 | 0.051 | 0.051 | -0.009 | -0.017 | -0.002 | -2.327 | 0.990 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | print | middle | 1,877 | 22 | 0.091 | 0.091 | 0.000 | -0.027 | 0.024 | 0.005 | 0.498 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | print | narrow | 4,002 | 22 | 0.080 | 0.080 | -0.003 | -0.025 | 0.019 | -0.262 | 0.603 | no |
| D+W+G+T against D+W+G (adds tone) | formats pooled | all | middle | 6,127 | 29 | 0.061 | 0.060 | 0.004 | -0.010 | 0.018 | 0.460 | 0.323 | no |
| D+W+G+T against D+W+G (adds tone) | formats pooled | all | narrow | 9,872 | 29 | 0.064 | 0.064 | -0.005 | -0.018 | 0.007 | -0.885 | 0.812 | no |
| D+W+G+T against D+W+G (adds tone) | all pooled | all | all | 15,999 | 29 | 0.063 | 0.063 | -0.002 | -0.015 | 0.011 | -0.330 | 0.629 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | audiobook | middle | 1,966 | 29 | 0.049 | 0.049 | -0.001 | -0.015 | 0.015 | -0.026 | 0.510 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | audiobook | narrow | 2,272 | 29 | 0.056 | 0.057 | -0.005 | -0.018 | 0.015 | -0.350 | 0.637 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | ebook | middle | 2,284 | 29 | 0.044 | 0.045 | -0.008 | -0.025 | 0.019 | -0.590 | 0.722 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | ebook | narrow | 3,598 | 29 | 0.051 | 0.051 | -0.012 | -0.028 | 0.003 | -1.351 | 0.912 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | print | middle | 1,877 | 22 | 0.093 | 0.091 | 0.021 | -0.077 | 0.118 | 0.364 | 0.358 | no |
| D+W+G+T against D+W (GDELT volume and tone) | format x level | print | narrow | 4,002 | 22 | 0.084 | 0.080 | 0.040 | -0.019 | 0.107 | 0.954 | 0.170 | no |
| D+W+G+T against D+W (GDELT volume and tone) | formats pooled | all | middle | 6,127 | 29 | 0.061 | 0.060 | 0.008 | -0.042 | 0.064 | 0.286 | 0.387 | no |
| D+W+G+T against D+W (GDELT volume and tone) | formats pooled | all | narrow | 9,872 | 29 | 0.065 | 0.064 | 0.016 | -0.018 | 0.065 | 0.624 | 0.266 | no |
| D+W+G+T against D+W (GDELT volume and tone) | all pooled | all | all | 15,999 | 29 | 0.064 | 0.063 | 0.013 | -0.026 | 0.064 | 0.504 | 0.307 | no |

Rows restricted to categories with GDELT series:

| comparison | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D+W+G against D+W (adds GDELT volume) | format x level | audiobook | middle | 1,466 | 29 | 0.049 | 0.050 | -0.012 | -0.035 | 0.014 | -0.945 | 0.828 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | audiobook | narrow | 1,274 | 29 | 0.058 | 0.058 | -0.006 | -0.026 | 0.013 | -0.498 | 0.691 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | ebook | middle | 1,701 | 29 | 0.046 | 0.046 | -0.008 | -0.023 | 0.010 | -0.942 | 0.827 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | ebook | narrow | 1,885 | 29 | 0.050 | 0.050 | -0.005 | -0.028 | 0.017 | -0.338 | 0.632 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | print | middle | 1,386 | 22 | 0.097 | 0.093 | 0.033 | -0.099 | 0.153 | 0.421 | 0.337 | no |
| D+W+G against D+W (adds GDELT volume) | format x level | print | narrow | 1,977 | 22 | 0.088 | 0.084 | 0.042 | -0.036 | 0.128 | 0.779 | 0.218 | no |
| D+W+G against D+W (adds GDELT volume) | formats pooled | all | middle | 4,553 | 29 | 0.063 | 0.062 | 0.010 | -0.053 | 0.080 | 0.272 | 0.393 | no |
| D+W+G against D+W (adds GDELT volume) | formats pooled | all | narrow | 5,136 | 29 | 0.067 | 0.065 | 0.019 | -0.022 | 0.075 | 0.609 | 0.271 | no |
| D+W+G against D+W (adds GDELT volume) | all pooled | all | all | 9,689 | 29 | 0.065 | 0.064 | 0.015 | -0.035 | 0.077 | 0.446 | 0.328 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | audiobook | middle | 1,466 | 29 | 0.050 | 0.049 | 0.015 | -0.005 | 0.041 | 1.437 | 0.075 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | audiobook | narrow | 1,274 | 29 | 0.058 | 0.059 | -0.007 | -0.027 | 0.022 | -0.392 | 0.653 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | ebook | middle | 1,701 | 29 | 0.046 | 0.046 | 0.007 | -0.009 | 0.034 | 0.627 | 0.265 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | ebook | narrow | 1,885 | 29 | 0.050 | 0.051 | -0.006 | -0.017 | 0.012 | -0.588 | 0.722 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | print | middle | 1,386 | 22 | 0.093 | 0.094 | -0.006 | -0.036 | 0.023 | -0.328 | 0.629 | no |
| D+W+G+T against D+W+G (adds tone) | format x level | print | narrow | 1,977 | 22 | 0.084 | 0.085 | -0.004 | -0.027 | 0.019 | -0.352 | 0.638 | no |
| D+W+G+T against D+W+G (adds tone) | formats pooled | all | middle | 4,553 | 29 | 0.062 | 0.062 | 0.003 | -0.010 | 0.021 | 0.452 | 0.326 | no |
| D+W+G+T against D+W+G (adds tone) | formats pooled | all | narrow | 5,136 | 29 | 0.065 | 0.066 | -0.006 | -0.018 | 0.011 | -0.644 | 0.740 | no |
| D+W+G+T against D+W+G (adds tone) | all pooled | all | all | 9,689 | 29 | 0.064 | 0.064 | -0.002 | -0.014 | 0.014 | -0.117 | 0.546 | no |

## 7. LibriVox (secondary series, reported separately)

| scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | librivox | middle | 4,956 | 91 | 0.218 | 0.220 | -0.008 | -0.018 | 0.000 | -1.827 | 0.966 | no |
| format x level | librivox | narrow | 7,051 | 91 | 0.246 | 0.247 | -0.004 | -0.010 | 0.003 | -1.143 | 0.874 | no |
| formats pooled | all | middle | 4,956 | 91 | 0.218 | 0.220 | -0.008 | -0.018 | 0.000 | -1.827 | 0.966 | no |
| formats pooled | all | narrow | 7,051 | 91 | 0.246 | 0.247 | -0.004 | -0.010 | 0.003 | -1.143 | 0.874 | no |
| all pooled | all | all | 12,007 | 91 | 0.235 | 0.236 | -0.006 | -0.012 | 0.001 | -1.781 | 0.963 | no |

## 8. Showcase cases (examples chosen knowing their Study 3 outcome; not tests)

Log shares; the target month is the month after the origin. "interest ratio" is the last week against its 26-week median.

| category | level | node_id | format | origin | target | last_log_share | naive | catboost_D | catboost_D+W | ridge_D | ridge_D+W | actual | interest_ratio_to_normal | shift_in_last_8_weeks | abs_err_D | abs_err_D+W | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Race and racism | narrow | B05.M02.N02 | ebook | 2020-05 | 2020-06 | -5.739 | -5.739 | -5.729 | -5.725 | -5.730 | -5.727 | -4.146 | 2.087 | 1.000 | 1.583 | 1.579 |  |
| Race and racism | narrow | B05.M02.N02 | audiobook | 2020-05 | 2020-06 | -5.252 | -5.252 | -5.279 | -5.299 | -5.294 | -5.292 | -3.509 | 2.087 | 1.000 | 1.770 | 1.790 |  |
| Epidemics and plagues | narrow | B15.M04.N05 | ebook | 2020-02 | 2020-03 | -6.426 | -6.426 | -6.431 | -6.382 | -6.430 | -6.364 | -6.245 | 3.302 | 1.000 | 0.186 | 0.137 |  |
| Epidemics and plagues | narrow | B15.M04.N05 | ebook | 2020-03 | 2020-04 | -6.245 | -6.245 | -6.322 | -6.280 | -6.310 | -6.199 | -6.137 | 20.779 | 0.000 | 0.185 | 0.143 |  |
