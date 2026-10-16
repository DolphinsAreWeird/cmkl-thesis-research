# Study 4b: forecasting the change in category demand and catching rare surges

Made 2026-10-14 06:14. 4b record SHA-256 `a34ab8e2279d4f13409a8786848a1179bd28964d35766c647acbefd44eab9bb4`; Study 4 record `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`. Forecast rows: 1,457,657 from 90 origins (2019-01 to 2026-07). Seattle formats; print and ebook are primary, audiobook secondary. The target is the change in log share, d(t+h) - d(t); skill = 1 - MAE(new) / MAE(base), so a positive skill means the new model has the smaller error (the error of the level forecast equals the error of the change forecast). DM is one-sided with Newey-West lag 3; the bootstrap uses moving blocks of 3 months, 2,000 resamples, seed 20261013, 95% percentile intervals. Interest helps if skill > 0, the interval is above zero and DM p < 0.05. Study 4b is a second, informed test (see the record), not a replication.

## Part A. Change forecasts, primary horizon 2

Test origins 2019-01 to 2026-07. Main rule: CatBoost D+W (or D+W+S) against CatBoost D, print and ebook pooled at each level.

### Verdicts

- catboost D+W vs D, print and ebook pooled, narrow level: **does not help** (skill 0.001, interval -0.005 to 0.007, DM p 0.503).
- catboost D+W vs D, print and ebook pooled, middle level: **does not help** (skill 0.007, interval -0.012 to 0.025, DM p 0.256).
- catboost D+W+S vs D, print and ebook pooled, narrow level: **does not help** (skill 0.005, interval -0.001 to 0.012, DM p 0.160).
- catboost D+W+S vs D, print and ebook pooled, middle level: **does not help** (skill 0.016, interval -0.000 to 0.034, DM p 0.100).

Same comparisons per format (not the pooled verdict):

- catboost D+W vs D, print, narrow: does not help (skill 0.003, interval -0.005 to 0.012, DM p 0.292).
- catboost D+W vs D, print, middle: does not help (skill 0.021, interval -0.006 to 0.042, DM p 0.108).
- catboost D+W vs D, ebook, narrow: does not help (skill -0.003, interval -0.010 to 0.002, DM p 0.867).
- catboost D+W vs D, ebook, middle: does not help (skill -0.014, interval -0.041 to 0.002, DM p 0.892).
- catboost D+W vs D, audiobook, narrow: does not help (skill 0.001, interval -0.008 to 0.009, DM p 0.245).
- catboost D+W vs D, audiobook, middle: does not help (skill -0.004, interval -0.026 to 0.009, DM p 0.652).
- catboost D+W+S vs D, print, narrow: does not help (skill 0.007, interval -0.004 to 0.017, DM p 0.157).
- catboost D+W+S vs D, print, middle: does not help (skill 0.025, interval -0.002 to 0.048, DM p 0.098).
- catboost D+W+S vs D, ebook, narrow: does not help (skill 0.002, interval -0.005 to 0.008, DM p 0.333).
- catboost D+W+S vs D, ebook, middle: does not help (skill 0.001, interval -0.011 to 0.015, DM p 0.448).
- catboost D+W+S vs D, audiobook, narrow: does not help (skill 0.007, interval -0.000 to 0.013, DM p 0.038).
- catboost D+W+S vs D, audiobook, middle: does not help (skill 0.010, interval -0.001 to 0.022, DM p 0.052).

### Interest comparisons at horizon 2

| h | comparison | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | catboost D+W vs D | format x level | print | narrow | 12,953 | 78 | 0.083 | 0.083 | 0.003 | -0.005 | 0.012 | 0.547 | 0.292 | no |
| 2 | catboost D+W vs D | format x level | print | middle | 6,577 | 78 | 0.079 | 0.077 | 0.021 | -0.006 | 0.042 | 1.235 | 0.108 | no |
| 2 | catboost D+W vs D | format x level | ebook | narrow | 11,783 | 84 | 0.059 | 0.059 | -0.003 | -0.010 | 0.002 | -1.111 | 0.867 | no |
| 2 | catboost D+W vs D | format x level | ebook | middle | 6,856 | 84 | 0.048 | 0.048 | -0.014 | -0.041 | 0.002 | -1.238 | 0.892 | no |
| 2 | catboost D+W vs D | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.066 | 0.066 | 0.001 | -0.008 | 0.009 | 0.689 | 0.245 | no |
| 2 | catboost D+W vs D | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.056 | 0.056 | -0.004 | -0.026 | 0.009 | -0.391 | 0.652 | no |
| 2 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.071 | 0.071 | 0.001 | -0.005 | 0.007 | -0.007 | 0.503 | no |
| 2 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.063 | 0.062 | 0.007 | -0.012 | 0.025 | 0.655 | 0.256 | no |
| 2 | catboost D+W+S vs D | format x level | print | narrow | 12,953 | 78 | 0.083 | 0.082 | 0.007 | -0.004 | 0.017 | 1.006 | 0.157 | no |
| 2 | catboost D+W+S vs D | format x level | print | middle | 6,577 | 78 | 0.079 | 0.077 | 0.025 | -0.002 | 0.048 | 1.294 | 0.098 | no |
| 2 | catboost D+W+S vs D | format x level | ebook | narrow | 11,783 | 84 | 0.059 | 0.058 | 0.002 | -0.005 | 0.008 | 0.432 | 0.333 | no |
| 2 | catboost D+W+S vs D | format x level | ebook | middle | 6,856 | 84 | 0.048 | 0.048 | 0.001 | -0.011 | 0.015 | 0.130 | 0.448 | no |
| 2 | catboost D+W+S vs D | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.066 | 0.066 | 0.007 | -0.000 | 0.013 | 1.770 | 0.038 | no |
| 2 | catboost D+W+S vs D | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.056 | 0.055 | 0.010 | -0.001 | 0.022 | 1.622 | 0.052 | no |
| 2 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.071 | 0.071 | 0.005 | -0.001 | 0.012 | 0.993 | 0.160 | no |
| 2 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.063 | 0.062 | 0.016 | -0.000 | 0.034 | 1.281 | 0.100 | no |
| 2 | catboost D+W+S vs D+W | format x level | print | narrow | 12,953 | 78 | 0.083 | 0.082 | 0.004 | -0.002 | 0.010 | 1.382 | 0.083 | no |
| 2 | catboost D+W+S vs D+W | format x level | print | middle | 6,577 | 78 | 0.077 | 0.077 | 0.005 | -0.011 | 0.016 | 0.705 | 0.240 | no |
| 2 | catboost D+W+S vs D+W | format x level | ebook | narrow | 11,783 | 84 | 0.059 | 0.058 | 0.005 | -0.001 | 0.014 | 1.152 | 0.125 | no |
| 2 | catboost D+W+S vs D+W | format x level | ebook | middle | 6,856 | 84 | 0.048 | 0.048 | 0.015 | -0.006 | 0.050 | 0.953 | 0.170 | no |
| 2 | catboost D+W+S vs D+W | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.066 | 0.066 | 0.005 | -0.002 | 0.016 | 1.003 | 0.158 | no |
| 2 | catboost D+W+S vs D+W | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.056 | 0.055 | 0.014 | -0.002 | 0.040 | 1.177 | 0.120 | no |
| 2 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.071 | 0.071 | 0.004 | -0.001 | 0.010 | 1.591 | 0.056 | no |
| 2 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.062 | 0.062 | 0.009 | -0.005 | 0.023 | 1.068 | 0.143 | no |
| 2 | ridge D+W vs D | format x level | print | narrow | 12,953 | 78 | 0.087 | 0.087 | 0.001 | -0.002 | 0.003 | 0.566 | 0.286 | no |
| 2 | ridge D+W vs D | format x level | print | middle | 6,577 | 78 | 0.078 | 0.077 | 0.004 | -0.000 | 0.008 | 1.656 | 0.049 | no |
| 2 | ridge D+W vs D | format x level | ebook | narrow | 11,783 | 84 | 0.064 | 0.064 | -0.004 | -0.007 | -0.000 | -2.101 | 0.982 | no |
| 2 | ridge D+W vs D | format x level | ebook | middle | 6,856 | 84 | 0.054 | 0.054 | 0.001 | -0.004 | 0.007 | 0.341 | 0.367 | no |
| 2 | ridge D+W vs D | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.070 | 0.070 | -0.003 | -0.006 | -0.000 | -2.240 | 0.987 | no |
| 2 | ridge D+W vs D | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.060 | 0.060 | 0.001 | -0.004 | 0.005 | 0.151 | 0.440 | no |
| 2 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.076 | 0.076 | -0.001 | -0.003 | 0.001 | -1.032 | 0.849 | no |
| 2 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.065 | 0.065 | 0.003 | -0.001 | 0.007 | 0.866 | 0.193 | no |
| 2 | ridge D+W+S vs D | format x level | print | narrow | 12,953 | 78 | 0.087 | 0.087 | -0.001 | -0.003 | 0.002 | -0.697 | 0.757 | no |
| 2 | ridge D+W+S vs D | format x level | print | middle | 6,577 | 78 | 0.078 | 0.077 | 0.004 | -0.000 | 0.009 | 1.710 | 0.044 | no |
| 2 | ridge D+W+S vs D | format x level | ebook | narrow | 11,783 | 84 | 0.064 | 0.064 | -0.002 | -0.006 | 0.001 | -1.478 | 0.930 | no |
| 2 | ridge D+W+S vs D | format x level | ebook | middle | 6,856 | 84 | 0.054 | 0.054 | 0.002 | -0.003 | 0.008 | 0.634 | 0.263 | no |
| 2 | ridge D+W+S vs D | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.070 | 0.070 | -0.003 | -0.007 | 0.001 | -1.081 | 0.860 | no |
| 2 | ridge D+W+S vs D | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.060 | 0.060 | 0.002 | -0.003 | 0.007 | 0.565 | 0.286 | no |
| 2 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.076 | 0.076 | -0.001 | -0.004 | 0.001 | -1.237 | 0.892 | no |
| 2 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.065 | 0.065 | 0.003 | -0.001 | 0.008 | 1.204 | 0.114 | no |
| 2 | ridge D+W+S vs D+W | format x level | print | narrow | 12,953 | 78 | 0.087 | 0.087 | -0.002 | -0.004 | 0.000 | -1.400 | 0.919 | no |
| 2 | ridge D+W+S vs D+W | format x level | print | middle | 6,577 | 78 | 0.077 | 0.077 | 0.000 | -0.002 | 0.004 | 0.314 | 0.377 | no |
| 2 | ridge D+W+S vs D+W | format x level | ebook | narrow | 11,783 | 84 | 0.064 | 0.064 | 0.001 | -0.001 | 0.003 | 1.212 | 0.113 | no |
| 2 | ridge D+W+S vs D+W | format x level | ebook | middle | 6,856 | 84 | 0.054 | 0.054 | 0.001 | -0.003 | 0.004 | 0.467 | 0.320 | no |
| 2 | ridge D+W+S vs D+W | format x level (secondary) | audiobook | narrow | 9,271 | 84 | 0.070 | 0.070 | 0.000 | -0.003 | 0.003 | 0.316 | 0.376 | no |
| 2 | ridge D+W+S vs D+W | format x level (secondary) | audiobook | middle | 6,364 | 84 | 0.060 | 0.060 | 0.001 | -0.002 | 0.005 | 0.635 | 0.263 | no |
| 2 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.076 | 0.076 | -0.001 | -0.002 | 0.001 | -0.250 | 0.599 | no |
| 2 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.065 | 0.065 | 0.001 | -0.002 | 0.004 | 0.689 | 0.245 | no |

### Interest comparisons at horizons 1 and 3 (secondary), print and ebook pooled

| h | comparison | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.053 | 0.052 | 0.004 | -0.001 | 0.010 | 1.383 | 0.083 | no |
| 1 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.043 | 0.043 | 0.009 | -0.002 | 0.023 | 1.431 | 0.076 | no |
| 1 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.053 | 0.052 | 0.003 | -0.004 | 0.011 | 1.066 | 0.143 | no |
| 1 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.043 | 0.043 | 0.008 | -0.006 | 0.024 | 1.024 | 0.153 | no |
| 1 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.052 | 0.052 | -0.001 | -0.004 | 0.002 | -0.075 | 0.530 | no |
| 1 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.043 | 0.043 | -0.002 | -0.012 | 0.007 | -0.261 | 0.603 | no |
| 1 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.056 | 0.056 | 0.001 | -0.001 | 0.002 | 0.410 | 0.341 | no |
| 1 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.047 | 0.047 | 0.001 | -0.003 | 0.005 | 0.281 | 0.389 | no |
| 1 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.056 | 0.056 | 0.001 | -0.001 | 0.003 | 0.757 | 0.225 | no |
| 1 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.047 | 0.047 | 0.002 | -0.003 | 0.006 | 0.591 | 0.277 | no |
| 1 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.056 | 0.056 | 0.000 | -0.001 | 0.001 | 0.536 | 0.296 | no |
| 1 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.047 | 0.047 | 0.000 | -0.001 | 0.002 | 0.775 | 0.219 | no |
| 3 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.087 | 0.088 | -0.002 | -0.009 | 0.006 | -0.614 | 0.730 | no |
| 3 | catboost D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.080 | 0.080 | -0.001 | -0.014 | 0.010 | -0.140 | 0.556 | no |
| 3 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.087 | 0.087 | 0.005 | -0.004 | 0.015 | 0.793 | 0.214 | no |
| 3 | catboost D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.080 | 0.080 | 0.004 | -0.007 | 0.015 | 0.745 | 0.228 | no |
| 3 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.088 | 0.087 | 0.007 | -0.002 | 0.017 | 1.159 | 0.123 | no |
| 3 | catboost D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.080 | 0.080 | 0.006 | -0.005 | 0.019 | 0.869 | 0.192 | no |
| 3 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.092 | 0.091 | 0.001 | -0.002 | 0.003 | 0.167 | 0.434 | no |
| 3 | ridge D+W vs D | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.079 | 0.079 | -0.000 | -0.005 | 0.004 | -0.461 | 0.678 | no |
| 3 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.092 | 0.091 | 0.001 | -0.003 | 0.006 | 0.514 | 0.304 | no |
| 3 | ridge D+W+S vs D | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.079 | 0.079 | 0.001 | -0.005 | 0.007 | 0.551 | 0.291 | no |
| 3 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.091 | 0.091 | -0.000 | -0.003 | 0.004 | 0.556 | 0.289 | no |
| 3 | ridge D+W+S vs D+W | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.079 | 0.079 | 0.001 | -0.002 | 0.006 | 0.975 | 0.165 | no |

(All strata and horizons: `study4b_a_interest_comparison.csv`.)

### Each model against zero change (print and ebook pooled)

| h | comparison | scope | format | level | n | months | mae_base | mae_new | skill | ci_lo | ci_hi | dm_stat | dm_p | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.053 | 0.033 | -0.009 | 0.063 | 1.804 | 0.036 | no |
| 1 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.043 | 0.026 | -0.062 | 0.085 | 0.694 | 0.244 | no |
| 1 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.052 | 0.037 | -0.000 | 0.064 | 2.286 | 0.011 | no |
| 1 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.043 | 0.035 | -0.044 | 0.087 | 1.042 | 0.149 | no |
| 1 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.052 | 0.036 | 0.001 | 0.062 | 2.367 | 0.009 | yes |
| 1 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.043 | 0.034 | -0.040 | 0.082 | 1.092 | 0.137 | no |
| 1 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.056 | -0.028 | -0.076 | 0.011 | -1.178 | 0.881 | no |
| 1 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.047 | -0.059 | -0.137 | 0.003 | -1.547 | 0.939 | no |
| 1 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.056 | -0.027 | -0.075 | 0.012 | -1.175 | 0.880 | no |
| 1 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.047 | -0.057 | -0.136 | 0.004 | -1.535 | 0.938 | no |
| 1 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 89 | 0.054 | 0.056 | -0.027 | -0.076 | 0.012 | -1.153 | 0.876 | no |
| 1 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 89 | 0.044 | 0.047 | -0.057 | -0.136 | 0.005 | -1.509 | 0.934 | no |
| 2 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.071 | 0.013 | -0.128 | 0.091 | 0.285 | 0.388 | no |
| 2 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.063 | -0.043 | -0.325 | 0.112 | -0.335 | 0.631 | no |
| 2 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.071 | 0.014 | -0.123 | 0.089 | 0.297 | 0.383 | no |
| 2 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.062 | -0.036 | -0.303 | 0.112 | -0.295 | 0.616 | no |
| 2 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.071 | 0.018 | -0.115 | 0.091 | 0.372 | 0.355 | no |
| 2 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.062 | -0.027 | -0.283 | 0.114 | -0.231 | 0.591 | no |
| 2 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.076 | -0.052 | -0.150 | 0.022 | -1.166 | 0.878 | no |
| 2 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.065 | -0.087 | -0.218 | 0.013 | -1.418 | 0.922 | no |
| 2 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.076 | -0.053 | -0.149 | 0.021 | -1.211 | 0.887 | no |
| 2 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.065 | -0.085 | -0.214 | 0.016 | -1.384 | 0.917 | no |
| 2 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 87 | 0.072 | 0.076 | -0.054 | -0.151 | 0.021 | -1.205 | 0.886 | no |
| 2 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 87 | 0.060 | 0.065 | -0.084 | -0.214 | 0.018 | -1.356 | 0.912 | no |
| 3 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.087 | -0.025 | -0.250 | 0.108 | -0.165 | 0.566 | no |
| 3 | catboost/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.080 | -0.126 | -0.581 | 0.133 | -0.581 | 0.719 | no |
| 3 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.088 | -0.027 | -0.251 | 0.106 | -0.188 | 0.575 | no |
| 3 | catboost/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.080 | -0.128 | -0.574 | 0.131 | -0.597 | 0.725 | no |
| 3 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.087 | -0.020 | -0.233 | 0.105 | -0.127 | 0.551 | no |
| 3 | catboost/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.080 | -0.121 | -0.560 | 0.131 | -0.571 | 0.716 | no |
| 3 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.092 | -0.073 | -0.203 | 0.024 | -1.219 | 0.889 | no |
| 3 | ridge/D vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.079 | -0.114 | -0.275 | 0.012 | -1.474 | 0.930 | no |
| 3 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.091 | -0.072 | -0.200 | 0.024 | -1.231 | 0.891 | no |
| 3 | ridge/D+W vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.079 | -0.114 | -0.274 | 0.008 | -1.503 | 0.934 | no |
| 3 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 87 | 0.085 | 0.091 | -0.072 | -0.203 | 0.026 | -1.190 | 0.883 | no |
| 3 | ridge/D+W+S vs zero change | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 87 | 0.071 | 0.079 | -0.113 | -0.274 | 0.011 | -1.445 | 0.926 | no |

(All strata: `study4b_a_vs_zero.csv`.)

### MAE of every model on the same rows (change in log share)

| h | scope | format | level | n | mae zero | mae ridge/D | mae ridge/D+W | mae ridge/D+W+S | mae catboost/D | mae catboost/D+W | mae catboost/D+W+S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | format x level | print | narrow | 13,463 | 0.0620 | 0.0633 | 0.0633 | 0.0634 | 0.0593 | 0.0590 | 0.0590 |
| 1 | format x level | print | middle | 6,831 | 0.0516 | 0.0548 | 0.0547 | 0.0547 | 0.0504 | 0.0496 | 0.0496 |
| 1 | format x level | ebook | narrow | 12,086 | 0.0459 | 0.0476 | 0.0476 | 0.0476 | 0.0452 | 0.0451 | 0.0452 |
| 1 | format x level | ebook | middle | 7,022 | 0.0375 | 0.0395 | 0.0395 | 0.0394 | 0.0363 | 0.0363 | 0.0364 |
| 1 | format x level (secondary) | audiobook | narrow | 9,557 | 0.0524 | 0.0529 | 0.0528 | 0.0528 | 0.0510 | 0.0508 | 0.0510 |
| 1 | format x level (secondary) | audiobook | middle | 6,528 | 0.0436 | 0.0444 | 0.0442 | 0.0442 | 0.0423 | 0.0419 | 0.0422 |
| 1 | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 0.0544 | 0.0559 | 0.0559 | 0.0559 | 0.0526 | 0.0524 | 0.0524 |
| 1 | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 0.0444 | 0.0471 | 0.0470 | 0.0470 | 0.0433 | 0.0429 | 0.0429 |
| 2 | format x level | print | narrow | 12,953 | 0.0832 | 0.0871 | 0.0870 | 0.0871 | 0.0828 | 0.0825 | 0.0822 |
| 2 | format x level | print | middle | 6,577 | 0.0709 | 0.0776 | 0.0774 | 0.0773 | 0.0785 | 0.0769 | 0.0765 |
| 2 | format x level | ebook | narrow | 11,783 | 0.0601 | 0.0638 | 0.0640 | 0.0639 | 0.0585 | 0.0587 | 0.0585 |
| 2 | format x level | ebook | middle | 6,856 | 0.0500 | 0.0538 | 0.0538 | 0.0537 | 0.0478 | 0.0485 | 0.0478 |
| 2 | format x level (secondary) | audiobook | narrow | 9,271 | 0.0685 | 0.0696 | 0.0698 | 0.0698 | 0.0663 | 0.0662 | 0.0658 |
| 2 | format x level (secondary) | audiobook | middle | 6,364 | 0.0582 | 0.0599 | 0.0599 | 0.0598 | 0.0557 | 0.0559 | 0.0551 |
| 2 | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 0.0722 | 0.0760 | 0.0760 | 0.0761 | 0.0712 | 0.0712 | 0.0709 |
| 2 | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 0.0602 | 0.0655 | 0.0653 | 0.0653 | 0.0628 | 0.0624 | 0.0618 |
| 3 | format x level | print | narrow | 12,615 | 0.0981 | 0.1049 | 0.1046 | 0.1049 | 0.1039 | 0.1039 | 0.1032 |
| 3 | format x level | print | middle | 6,408 | 0.0841 | 0.0945 | 0.0943 | 0.0943 | 0.1051 | 0.1045 | 0.1045 |
| 3 | format x level | ebook | narrow | 11,628 | 0.0713 | 0.0770 | 0.0771 | 0.0768 | 0.0694 | 0.0698 | 0.0694 |
| 3 | format x level | ebook | middle | 6,774 | 0.0592 | 0.0651 | 0.0654 | 0.0651 | 0.0569 | 0.0576 | 0.0568 |
| 3 | format x level (secondary) | audiobook | narrow | 9,122 | 0.0801 | 0.0818 | 0.0820 | 0.0819 | 0.0771 | 0.0770 | 0.0767 |
| 3 | format x level (secondary) | audiobook | middle | 6,281 | 0.0673 | 0.0709 | 0.0712 | 0.0709 | 0.0652 | 0.0651 | 0.0644 |
| 3 | print+ebook pooled (primary) | print+ebook | narrow | 24,243 | 0.0853 | 0.0915 | 0.0914 | 0.0914 | 0.0874 | 0.0876 | 0.0870 |
| 3 | print+ebook pooled (primary) | print+ebook | middle | 13,182 | 0.0713 | 0.0794 | 0.0794 | 0.0793 | 0.0803 | 0.0804 | 0.0799 |

## Part B. Surges at horizon 2

A surge is a change of log share of at least log(1.3) = 0.2624 at horizon 2. Average precision (AP) is primary; a model with no skill has AP equal to the base rate. Recall: the share of surges that fall among the 10 highest-scored category-formats in their origin and format (random ranking gives the "random" column). Brier: mean squared error of the probability; the last column is the Brier score of always forecasting the test base rate. Rows with no surge in a stratum are omitted from the bootstrap table.

### Metrics

| scope | format | level | model | n | surges | base_rate | ap | ap_over_base | recall_top | recall_random | origins_with_surge | brier | brier_base_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D | 12,953 | 302 | 0.0233 | 0.0806 | 3.4552 | 0.3146 | 0.0595 | 76 | 0.0316 | 0.0228 |
| format x level | print | narrow | catboost_clf/D+W | 12,953 | 302 | 0.0233 | 0.0986 | 4.2287 | 0.3311 | 0.0595 | 76 | 0.0280 | 0.0228 |
| format x level | print | narrow | catboost_clf/D+W+S | 12,953 | 302 | 0.0233 | 0.0801 | 3.4362 | 0.3344 | 0.0595 | 76 | 0.0339 | 0.0228 |
| format x level | print | narrow | logistic/D | 12,953 | 302 | 0.0233 | 0.0866 | 3.7161 | 0.3079 | 0.0595 | 76 | 0.0313 | 0.0228 |
| format x level | print | narrow | logistic/D+W | 12,953 | 302 | 0.0233 | 0.0891 | 3.8227 | 0.3079 | 0.0595 | 76 | 0.0317 | 0.0228 |
| format x level | print | narrow | logistic/D+W+S | 12,953 | 302 | 0.0233 | 0.0912 | 3.9129 | 0.3079 | 0.0595 | 76 | 0.0320 | 0.0228 |
| format x level | print | middle | catboost_clf/D | 6,577 | 109 | 0.0166 | 0.0959 | 5.7857 | 0.6147 | 0.1186 | 58 | 0.0341 | 0.0163 |
| format x level | print | middle | catboost_clf/D+W | 6,577 | 109 | 0.0166 | 0.1156 | 6.9771 | 0.5963 | 0.1186 | 58 | 0.0294 | 0.0163 |
| format x level | print | middle | catboost_clf/D+W+S | 6,577 | 109 | 0.0166 | 0.0963 | 5.8119 | 0.5596 | 0.1186 | 58 | 0.0338 | 0.0163 |
| format x level | print | middle | logistic/D | 6,577 | 109 | 0.0166 | 0.1175 | 7.0906 | 0.5872 | 0.1186 | 58 | 0.0201 | 0.0163 |
| format x level | print | middle | logistic/D+W | 6,577 | 109 | 0.0166 | 0.1312 | 7.9150 | 0.5872 | 0.1186 | 58 | 0.0209 | 0.0163 |
| format x level | print | middle | logistic/D+W+S | 6,577 | 109 | 0.0166 | 0.1295 | 7.8155 | 0.6055 | 0.1186 | 58 | 0.0212 | 0.0163 |
| format x level | ebook | narrow | catboost_clf/D | 11,783 | 120 | 0.0102 | 0.1765 | 17.3313 | 0.3167 | 0.0717 | 58 | 0.0094 | 0.0101 |
| format x level | ebook | narrow | catboost_clf/D+W | 11,783 | 120 | 0.0102 | 0.2148 | 21.0887 | 0.3583 | 0.0717 | 58 | 0.0086 | 0.0101 |
| format x level | ebook | narrow | catboost_clf/D+W+S | 11,783 | 120 | 0.0102 | 0.1914 | 18.7893 | 0.3417 | 0.0717 | 58 | 0.0090 | 0.0101 |
| format x level | ebook | narrow | logistic/D | 11,783 | 120 | 0.0102 | 0.1369 | 13.4385 | 0.3417 | 0.0717 | 58 | 0.0093 | 0.0101 |
| format x level | ebook | narrow | logistic/D+W | 11,783 | 120 | 0.0102 | 0.1728 | 16.9631 | 0.3333 | 0.0717 | 58 | 0.0091 | 0.0101 |
| format x level | ebook | narrow | logistic/D+W+S | 11,783 | 120 | 0.0102 | 0.1726 | 16.9491 | 0.3250 | 0.0717 | 58 | 0.0090 | 0.0101 |
| format x level | ebook | middle | catboost_clf/D | 6,856 | 60 | 0.0088 | 0.2916 | 33.3150 | 0.4500 | 0.1232 | 41 | 0.0079 | 0.0087 |
| format x level | ebook | middle | catboost_clf/D+W | 6,856 | 60 | 0.0088 | 0.3368 | 38.4831 | 0.4333 | 0.1232 | 41 | 0.0063 | 0.0087 |
| format x level | ebook | middle | catboost_clf/D+W+S | 6,856 | 60 | 0.0088 | 0.3223 | 36.8265 | 0.4667 | 0.1232 | 41 | 0.0069 | 0.0087 |
| format x level | ebook | middle | logistic/D | 6,856 | 60 | 0.0088 | 0.2395 | 27.3634 | 0.4833 | 0.1232 | 41 | 0.0073 | 0.0087 |
| format x level | ebook | middle | logistic/D+W | 6,856 | 60 | 0.0088 | 0.3159 | 36.1014 | 0.5000 | 0.1232 | 41 | 0.0068 | 0.0087 |
| format x level | ebook | middle | logistic/D+W+S | 6,856 | 60 | 0.0088 | 0.3116 | 35.6094 | 0.5000 | 0.1232 | 41 | 0.0068 | 0.0087 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D | 9,271 | 131 | 0.0141 | 0.1380 | 9.7672 | 0.3359 | 0.0905 | 58 | 0.0139 | 0.0139 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W | 9,271 | 131 | 0.0141 | 0.1857 | 13.1446 | 0.3130 | 0.0905 | 58 | 0.0123 | 0.0139 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S | 9,271 | 131 | 0.0141 | 0.1759 | 12.4498 | 0.2977 | 0.0905 | 58 | 0.0127 | 0.0139 |
| format x level (secondary) | audiobook | narrow | logistic/D | 9,271 | 131 | 0.0141 | 0.1333 | 9.4330 | 0.3206 | 0.0905 | 58 | 0.0129 | 0.0139 |
| format x level (secondary) | audiobook | narrow | logistic/D+W | 9,271 | 131 | 0.0141 | 0.1508 | 10.6703 | 0.2824 | 0.0905 | 58 | 0.0128 | 0.0139 |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S | 9,271 | 131 | 0.0141 | 0.1451 | 10.2716 | 0.2824 | 0.0905 | 58 | 0.0128 | 0.0139 |
| format x level (secondary) | audiobook | middle | catboost_clf/D | 6,364 | 66 | 0.0104 | 0.2619 | 25.2520 | 0.5000 | 0.1330 | 41 | 0.0098 | 0.0103 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W | 6,364 | 66 | 0.0104 | 0.3070 | 29.6034 | 0.4545 | 0.1330 | 41 | 0.0078 | 0.0103 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S | 6,364 | 66 | 0.0104 | 0.2951 | 28.4517 | 0.4545 | 0.1330 | 41 | 0.0085 | 0.0103 |
| format x level (secondary) | audiobook | middle | logistic/D | 6,364 | 66 | 0.0104 | 0.2340 | 22.5643 | 0.4394 | 0.1330 | 41 | 0.0087 | 0.0103 |
| format x level (secondary) | audiobook | middle | logistic/D+W | 6,364 | 66 | 0.0104 | 0.2602 | 25.0912 | 0.4242 | 0.1330 | 41 | 0.0084 | 0.0103 |
| format x level (secondary) | audiobook | middle | logistic/D+W+S | 6,364 | 66 | 0.0104 | 0.2563 | 24.7155 | 0.4242 | 0.1330 | 41 | 0.0084 | 0.0103 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D | 24,736 | 422 | 0.0171 | 0.0799 | 4.6855 | 0.3152 | 0.0630 | 134 | 0.0210 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W | 24,736 | 422 | 0.0171 | 0.1113 | 6.5250 | 0.3389 | 0.0630 | 134 | 0.0187 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S | 24,736 | 422 | 0.0171 | 0.0851 | 4.9872 | 0.3365 | 0.0630 | 134 | 0.0220 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D | 24,736 | 422 | 0.0171 | 0.0822 | 4.8178 | 0.3175 | 0.0630 | 134 | 0.0208 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W | 24,736 | 422 | 0.0171 | 0.0881 | 5.1657 | 0.3152 | 0.0630 | 134 | 0.0209 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S | 24,736 | 422 | 0.0171 | 0.0898 | 5.2631 | 0.3128 | 0.0630 | 134 | 0.0211 | 0.0168 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D | 13,433 | 169 | 0.0126 | 0.0974 | 7.7429 | 0.5562 | 0.1203 | 99 | 0.0207 | 0.0124 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W | 13,433 | 169 | 0.0126 | 0.1360 | 10.8108 | 0.5385 | 0.1203 | 99 | 0.0176 | 0.0124 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S | 13,433 | 169 | 0.0126 | 0.1084 | 8.6178 | 0.5266 | 0.1203 | 99 | 0.0201 | 0.0124 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D | 13,433 | 169 | 0.0126 | 0.1258 | 9.9954 | 0.5503 | 0.1203 | 99 | 0.0136 | 0.0124 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W | 13,433 | 169 | 0.0126 | 0.1487 | 11.8183 | 0.5562 | 0.1203 | 99 | 0.0137 | 0.0124 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S | 13,433 | 169 | 0.0126 | 0.1479 | 11.7532 | 0.5680 | 0.1203 | 99 | 0.0139 | 0.0124 |

### AP difference with block bootstrap

- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, narrow level: **interest helps** (AP 0.0799 to 0.1113, difference +0.0314, interval +0.0096 to +0.0519, 422 surges).
- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, middle level: **interest helps** (AP 0.0974 to 0.1360, difference +0.0386, interval +0.0054 to +0.0766, 169 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, narrow level: **does not help** (AP 0.0799 to 0.0851, difference +0.0051, interval -0.0019 to +0.0232, 422 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, middle level: **does not help** (AP 0.0974 to 0.1084, difference +0.0110, interval -0.0019 to +0.0769, 169 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.0822 to 0.0881, difference +0.0059, interval +0.0014 to +0.0334, 422 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1258 to 0.1487, difference +0.0229, interval +0.0063 to +0.0758, 169 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.0822 to 0.0898, difference +0.0076, interval +0.0017 to +0.0346, 422 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1258 to 0.1479, difference +0.0221, interval +0.0063 to +0.0703, 169 surges).

| scope | format | level | comparison | model_class | surges | ap_base | ap_new | ap_diff | ci_lo | ci_hi | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 302 | 0.0806 | 0.0986 | 0.0180 | -0.0006 | 0.0351 | no |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 302 | 0.0806 | 0.0801 | -0.0004 | -0.0084 | 0.0168 | no |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 302 | 0.0986 | 0.0801 | -0.0185 | -0.0323 | -0.0003 | no |
| format x level | print | narrow | logistic/D+W vs logistic/D | logistic | 302 | 0.0866 | 0.0891 | 0.0025 | -0.0007 | 0.0254 | no |
| format x level | print | narrow | logistic/D+W+S vs logistic/D | logistic | 302 | 0.0866 | 0.0912 | 0.0046 | -0.0007 | 0.0250 | no |
| format x level | print | narrow | logistic/D+W+S vs logistic/D+W | logistic | 302 | 0.0891 | 0.0912 | 0.0021 | -0.0018 | 0.0065 | no |
| format x level | print | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 109 | 0.0959 | 0.1156 | 0.0197 | -0.0062 | 0.0491 | no |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 109 | 0.0959 | 0.0963 | 0.0004 | -0.0106 | 0.0578 | no |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 109 | 0.1156 | 0.0963 | -0.0193 | -0.0415 | 0.0186 | no |
| format x level | print | middle | logistic/D+W vs logistic/D | logistic | 109 | 0.1175 | 0.1312 | 0.0137 | -0.0002 | 0.0509 | no |
| format x level | print | middle | logistic/D+W+S vs logistic/D | logistic | 109 | 0.1175 | 0.1295 | 0.0120 | -0.0030 | 0.0464 | no |
| format x level | print | middle | logistic/D+W+S vs logistic/D+W | logistic | 109 | 0.1312 | 0.1295 | -0.0016 | -0.0090 | 0.0028 | no |
| format x level | ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 120 | 0.1765 | 0.2148 | 0.0383 | 0.0019 | 0.0654 | yes |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 120 | 0.1765 | 0.1914 | 0.0148 | -0.0067 | 0.0432 | no |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 120 | 0.2148 | 0.1914 | -0.0234 | -0.0431 | 0.0067 | no |
| format x level | ebook | narrow | logistic/D+W vs logistic/D | logistic | 120 | 0.1369 | 0.1728 | 0.0359 | 0.0098 | 0.0640 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 120 | 0.1369 | 0.1726 | 0.0358 | 0.0080 | 0.0645 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 120 | 0.1728 | 0.1726 | -0.0001 | -0.0067 | 0.0071 | no |
| format x level | ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 60 | 0.2916 | 0.3368 | 0.0452 | -0.0012 | 0.0914 | no |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 60 | 0.2916 | 0.3223 | 0.0307 | -0.0046 | 0.0744 | no |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 60 | 0.3368 | 0.3223 | -0.0145 | -0.0391 | 0.0147 | no |
| format x level | ebook | middle | logistic/D+W vs logistic/D | logistic | 60 | 0.2395 | 0.3159 | 0.0765 | 0.0068 | 0.1482 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D | logistic | 60 | 0.2395 | 0.3116 | 0.0722 | 0.0038 | 0.1357 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 60 | 0.3159 | 0.3116 | -0.0043 | -0.0222 | 0.0057 | no |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 131 | 0.1380 | 0.1857 | 0.0477 | 0.0165 | 0.0817 | yes |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 131 | 0.1380 | 0.1759 | 0.0379 | 0.0098 | 0.0731 | yes |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 131 | 0.1857 | 0.1759 | -0.0098 | -0.0252 | 0.0101 | no |
| format x level (secondary) | audiobook | narrow | logistic/D+W vs logistic/D | logistic | 131 | 0.1333 | 0.1508 | 0.0175 | 0.0007 | 0.0307 | yes |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D | logistic | 131 | 0.1333 | 0.1451 | 0.0118 | 0.0003 | 0.0234 | yes |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 131 | 0.1508 | 0.1451 | -0.0056 | -0.0145 | 0.0026 | no |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 66 | 0.2619 | 0.3070 | 0.0451 | 0.0071 | 0.0879 | yes |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 66 | 0.2619 | 0.2951 | 0.0332 | -0.0060 | 0.0759 | no |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 66 | 0.3070 | 0.2951 | -0.0119 | -0.0374 | 0.0171 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W vs logistic/D | logistic | 66 | 0.2340 | 0.2602 | 0.0262 | 0.0011 | 0.0523 | yes |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D | logistic | 66 | 0.2340 | 0.2563 | 0.0223 | -0.0001 | 0.0487 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D+W | logistic | 66 | 0.2602 | 0.2563 | -0.0039 | -0.0130 | 0.0038 | no |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 422 | 0.0799 | 0.1113 | 0.0314 | 0.0096 | 0.0519 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 422 | 0.0799 | 0.0851 | 0.0051 | -0.0019 | 0.0232 | no |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 422 | 0.1113 | 0.0851 | -0.0262 | -0.0438 | -0.0048 | no |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W vs logistic/D | logistic | 422 | 0.0822 | 0.0881 | 0.0059 | 0.0014 | 0.0334 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 422 | 0.0822 | 0.0898 | 0.0076 | 0.0017 | 0.0346 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 422 | 0.0881 | 0.0898 | 0.0017 | -0.0015 | 0.0053 | no |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 169 | 0.0974 | 0.1360 | 0.0386 | 0.0054 | 0.0766 | yes |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 169 | 0.0974 | 0.1084 | 0.0110 | -0.0019 | 0.0769 | no |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 169 | 0.1360 | 0.1084 | -0.0276 | -0.0544 | 0.0103 | no |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W vs logistic/D | logistic | 169 | 0.1258 | 0.1487 | 0.0229 | 0.0063 | 0.0758 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D | logistic | 169 | 0.1258 | 0.1479 | 0.0221 | 0.0063 | 0.0703 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 169 | 0.1487 | 0.1479 | -0.0008 | -0.0083 | 0.0039 | no |

## Showcases

Two cases named in the record (chosen knowing their Study 3 outcome; they are illustrations, not tests). Changes are in log share; "rank" is the position among the eligible category-formats of the same level, format and origin (1 = highest score). `s_resp` is the earlier-shift responsiveness.

| category | level | node_id | format | origin | target_month | note | actual_change | surge | rank_actual_change | n_in_group | w_ratio | w_shift8 | s_sustained | s_resp | zero | chg ridge/D | chg ridge/D+W | chg ridge/D+W+S | chg catboost/D | chg catboost/D+W | chg catboost/D+W+S | p catboost_clf/D | rank catboost_clf/D | p catboost_clf/D+W | rank catboost_clf/D+W | p catboost_clf/D+W+S | rank catboost_clf/D+W+S | p logistic/D | rank logistic/D | p logistic/D+W | rank logistic/D+W | p logistic/D+W+S | rank logistic/D+W+S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Race and racism | narrow | B05.M02.N02 | print | 2020-04 | 2020-06 | not forecast at this origin (below the size rule, or a month missing) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Race and racism | narrow | B05.M02.N02 | ebook | 2020-04 | 2020-06 |  | 1.633 | 1.000 | 1.000 | 124.000 | 0.866 | 0.000 | 0.000 | 0.000 | 0.000 | 0.026 | 0.022 | 0.022 | -0.004 | 0.000 | -0.006 | 0.002 | 85.000 | 0.002 | 90.000 | 0.003 | 86.000 | 0.002 | 55.000 | 0.003 | 61.000 | 0.003 | 60.000 |
| Epidemics and plagues | narrow | B15.M04.N05 | ebook | 2020-01 | 2020-03 |  | 0.188 | 0.000 | 11.000 | 122.000 | 5.010 | 0.000 | 0.000 | 0.000 | 0.000 | -0.004 | -0.049 | -0.050 | 0.016 | -0.011 | -0.031 | 0.002 | 51.000 | 0.002 | 71.000 | 0.002 | 68.000 | 0.002 | 57.000 | 0.001 | 83.000 | 0.001 | 87.000 |

## Reference: Study 4 level forecasts on the same rows

Study 4 forecast the level; its error against the zero-change forecast (the same as its naive) and against the 4b CatBoost D change model, on the rows both cover (horizons 1 and 2).

| h | scope | format | level | n | mae_zero | mae_study4_catboost_D_level | mae_4b_catboost_D_change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | format x level | print | narrow | 13,463 | 0.0620 | 0.0630 | 0.0593 |
| 1 | format x level | print | middle | 6,831 | 0.0516 | 0.0586 | 0.0504 |
| 1 | format x level | ebook | narrow | 12,086 | 0.0459 | 0.0491 | 0.0452 |
| 1 | format x level | ebook | middle | 7,022 | 0.0375 | 0.0432 | 0.0363 |
| 1 | format x level (secondary) | audiobook | narrow | 9,557 | 0.0524 | 0.0543 | 0.0510 |
| 1 | format x level (secondary) | audiobook | middle | 6,528 | 0.0436 | 0.0481 | 0.0423 |
| 1 | print+ebook pooled (primary) | print+ebook | narrow | 25,549 | 0.0544 | 0.0564 | 0.0526 |
| 1 | print+ebook pooled (primary) | print+ebook | middle | 13,853 | 0.0444 | 0.0508 | 0.0433 |
| 2 | format x level | print | narrow | 12,953 | 0.0832 | 0.0875 | 0.0828 |
| 2 | format x level | print | middle | 6,577 | 0.0709 | 0.0883 | 0.0785 |
| 2 | format x level | ebook | narrow | 11,783 | 0.0601 | 0.0636 | 0.0585 |
| 2 | format x level | ebook | middle | 6,856 | 0.0500 | 0.0557 | 0.0478 |
| 2 | format x level (secondary) | audiobook | narrow | 9,271 | 0.0685 | 0.0702 | 0.0663 |
| 2 | format x level (secondary) | audiobook | middle | 6,364 | 0.0582 | 0.0621 | 0.0557 |
| 2 | print+ebook pooled (primary) | print+ebook | narrow | 24,736 | 0.0722 | 0.0761 | 0.0712 |
| 2 | print+ebook pooled (primary) | print+ebook | middle | 13,433 | 0.0602 | 0.0717 | 0.0628 |
