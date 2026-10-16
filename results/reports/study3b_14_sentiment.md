# Study 3b sentiment direction

- step: 14
- written: 2026-10-14 00:22:47
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json

- GDELT shifts in the main analysis (non-sparse, sum Y > 0): 727; with a complete delta tone: 721; placebo windows per category: 200 (record 200)
- bootstrap: 2000 resamples (record 2000); seed 20261013; 95% percentile intervals
- placebo_p: share of placebo-feature coefficients with |coef| >= |real coef| (two-sided)
- tone data end: 2021-06-28 00:00:00

## Sentiment features added to the carry-over regression
| level | model | term | coef | ci_low | ci_high | boot_p | placebo_p | placebo_fits | n_tests | n_categories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle | d_tone alone | d_tone | 0.036 | -0.037 | 0.080 | 0.390 | 0.575 | 200 | 122 | 46 |
| middle | d_pos alone | d_pos | 0.081 | -0.124 | 0.254 | 0.466 | 0.540 | 200 | 122 | 46 |
| middle | d_neg alone | d_neg | -0.034 | -0.105 | 0.052 | 0.569 | 0.645 | 200 | 122 | 46 |
| middle | d_intensity alone | d_intensity | -0.030 | -0.130 | 0.048 | 0.623 | 0.745 | 200 | 122 | 46 |
| middle | neg_shift alone | neg_shift | 0.007 | -0.045 | 0.072 | 0.705 | 0.840 | 200 | 122 | 46 |
| middle | negative shift x sustained | neg_shift | 0.010 | -0.043 | 0.080 | 0.630 | 0.860 | 200 | 122 | 46 |
| middle | negative shift x sustained | neg_x_sustained | -0.037 | -0.249 | 0.130 | 0.592 | 0.785 | 200 | 122 | 46 |
| middle | negative shift x sustained | class_sustained | 0.019 | -0.145 | 0.152 | 0.864 |  | 0 | 122 | 46 |
| narrow | d_tone alone | d_tone | -0.053 | -0.111 | 0.004 | 0.076 | 0.070 | 200 | 235 | 87 |
| narrow | d_pos alone | d_pos | -0.139 | -0.239 | -0.035 | 0.013 | 0.010 | 200 | 235 | 87 |
| narrow | d_neg alone | d_neg | 0.051 | -0.026 | 0.134 | 0.213 | 0.185 | 200 | 235 | 87 |
| narrow | d_intensity alone | d_intensity | 0.001 | -0.076 | 0.083 | 0.992 | 0.960 | 200 | 235 | 87 |
| narrow | neg_shift alone | neg_shift | 0.073 | 0.015 | 0.144 | 0.014 | 0.000 | 200 | 235 | 87 |
| narrow | negative shift x sustained | neg_shift | 0.069 | 0.011 | 0.145 | 0.021 | 0.000 | 200 | 235 | 87 |
| narrow | negative shift x sustained | neg_x_sustained | 0.040 | -0.242 | 0.321 | 0.845 | 0.675 | 200 | 235 | 87 |
| narrow | negative shift x sustained | class_sustained | 0.030 | -0.225 | 0.310 | 0.761 |  | 0 | 235 | 87 |
| value | d_tone alone | d_tone | -0.035 | -0.105 | 0.047 | 0.349 | 0.415 | 200 | 364 | 127 |
| value | d_pos alone | d_pos | -0.106 | -0.238 | 0.034 | 0.130 | 0.260 | 200 | 364 | 127 |
| value | d_neg alone | d_neg | 0.026 | -0.072 | 0.115 | 0.582 | 0.555 | 200 | 364 | 127 |
| value | d_intensity alone | d_intensity | -0.011 | -0.094 | 0.064 | 0.737 | 0.825 | 200 | 364 | 127 |
| value | neg_shift alone | neg_shift | 0.035 | -0.061 | 0.123 | 0.450 | 0.400 | 200 | 364 | 127 |
| value | negative shift x sustained | neg_shift | 0.051 | -0.029 | 0.130 | 0.198 | 0.265 | 200 | 364 | 127 |
| value | negative shift x sustained | neg_x_sustained | -0.210 | -0.602 | 0.168 | 0.296 | 0.170 | 200 | 364 | 127 |
| value | negative shift x sustained | class_sustained | 0.325 | 0.003 | 0.708 | 0.048 |  | 0 | 364 | 127 |

## Mean tau of negative (1) and non-negative (0) shifts by duration class (descriptive)
| level | duration_class | negative_shift | tests | categories | mean_tau | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle | fading | 0 | 31 | 21 | 0.019 | -0.030 | 0.065 |
| middle | fading | 1 | 74 | 37 | -0.009 | -0.042 | 0.023 |
| middle | intermediate | 0 | 1 | 1 | -0.172 |  |  |
| middle | intermediate | 1 | 4 | 4 | -0.030 | -0.169 | 0.064 |
| middle | sustained | 0 | 2 | 2 | 0.040 | -0.039 | 0.119 |
| middle | sustained | 1 | 10 | 9 | 0.072 | -0.053 | 0.200 |
| narrow | fading | 0 | 73 | 48 | -0.088 | -0.143 | -0.038 |
| narrow | fading | 1 | 119 | 68 | -0.007 | -0.036 | 0.023 |
| narrow | intermediate | 0 | 3 | 3 | -0.049 | -0.069 | -0.016 |
| narrow | intermediate | 1 | 5 | 4 | -0.067 | -0.325 | 0.077 |
| narrow | sustained | 0 | 6 | 6 | -0.019 | -0.253 | 0.195 |
| narrow | sustained | 1 | 29 | 24 | 0.101 | 0.029 | 0.176 |
| value | fading | 0 | 132 | 78 | -0.068 | -0.117 | -0.018 |
| value | fading | 1 | 172 | 97 | -0.039 | -0.098 | 0.017 |
| value | intermediate | 0 | 6 | 5 | -0.767 | -1.112 | -0.464 |
| value | intermediate | 1 | 7 | 7 | -0.216 | -0.435 | -0.003 |
| value | sustained | 0 | 8 | 8 | 0.207 | -0.065 | 0.546 |
| value | sustained | 1 | 39 | 32 | 0.138 | 0.014 | 0.267 |
