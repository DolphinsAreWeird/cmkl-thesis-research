# Study 3b shift effects

- step: 12
- written: 2026-10-14 00:21:03
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json

- bootstrap resamples: 2000 (record 2000), seed 20261013
- last demand month per level (Seattle): narrow: 2026-08, middle: 2026-08, value: 2026-08
- run time 52s with 3 workers

## Shifts
- in the interest tables (narrow, middle, value): 3997; without a record duration class (interrupted, censored): 38; labelled, quality-ok (unless robustness), tested levels, from 2017-01, category with counts: 3231
| source | level | duration_class | seasonal | shifts |
| --- | --- | --- | --- | --- |
| gdelt | middle | fading | False | 106 |
| gdelt | middle | fading | True | 6 |
| gdelt | middle | intermediate | False | 5 |
| gdelt | middle | sustained | False | 12 |
| gdelt | middle | sustained | True | 4 |
| gdelt | narrow | fading | False | 194 |
| gdelt | narrow | fading | True | 25 |
| gdelt | narrow | intermediate | False | 8 |
| gdelt | narrow | sustained | False | 35 |
| gdelt | narrow | sustained | True | 5 |
| gdelt | value | fading | False | 336 |
| gdelt | value | fading | True | 35 |
| gdelt | value | intermediate | False | 16 |
| gdelt | value | sustained | False | 49 |
| gdelt | value | sustained | True | 6 |
| wikipedia | middle | fading | False | 130 |
| wikipedia | middle | fading | True | 20 |
| wikipedia | middle | intermediate | False | 6 |
| wikipedia | middle | intermediate | True | 2 |
| wikipedia | middle | sustained | False | 16 |
| wikipedia | middle | sustained | True | 9 |
| wikipedia | narrow | fading | False | 377 |
| wikipedia | narrow | fading | True | 67 |
| wikipedia | narrow | intermediate | False | 41 |
| wikipedia | narrow | intermediate | True | 7 |
| wikipedia | narrow | sustained | False | 68 |
| wikipedia | narrow | sustained | True | 17 |
| wikipedia | value | fading | False | 1025 |
| wikipedia | value | fading | True | 169 |
| wikipedia | value | intermediate | False | 125 |
| wikipedia | value | intermediate | True | 19 |
| wikipedia | value | sustained | False | 210 |
| wikipedia | value | sustained | True | 81 |

## Tests (joint Seattle model, one per category and month 0 shared by its shifts)
| analysis | level | skip | shift rows |
| --- | --- | --- | --- |
| main | middle | tested | 273 |
| main | middle | window too short | 2 |
| main | narrow | tested | 715 |
| main | narrow | window too short | 8 |
| main | value | not feasible | 23 |
| main | value | tested | 1720 |
| main | value | window too short | 18 |
| seasonal | middle | tested | 40 |
| seasonal | middle | window too short | 1 |
| seasonal | narrow | tested | 120 |
| seasonal | narrow | window too short | 1 |
| seasonal | value | not feasible | 23 |
| seasonal | value | tested | 284 |
| seasonal | value | window too short | 3 |

## Detection (placebo-category rank, months 0 to +2)
- main, middle: 273 shift rows tested, 0 too sparse (sum mu < 5, reported separately); among the other 273: one-sided p < 0.05: 13 (4.8%, 5% expected under no effect); BH q < 0.1: 0; sum Y = 0 tests: 0
- main, narrow: 715 shift rows tested, 3 too sparse (sum mu < 5, reported separately); among the other 712: one-sided p < 0.05: 33 (4.6%, 5% expected under no effect); BH q < 0.1: 0; sum Y = 0 tests: 0
- main, value: 1720 shift rows tested, 139 too sparse (sum mu < 5, reported separately); among the other 1581: one-sided p < 0.05: 295 (18.7%, 5% expected under no effect); BH q < 0.1: 11; sum Y = 0 tests: 0
- seasonal, middle: 40 shift rows tested, 0 too sparse (sum mu < 5, reported separately); among the other 40: one-sided p < 0.05: 0 (0.0%, 5% expected under no effect); BH q < 0.1: 0; sum Y = 0 tests: 0
- seasonal, narrow: 120 shift rows tested, 0 too sparse (sum mu < 5, reported separately); among the other 120: one-sided p < 0.05: 2 (1.7%, 5% expected under no effect); BH q < 0.1: 0; sum Y = 0 tests: 0
- seasonal, value: 284 shift rows tested, 39 too sparse (sum mu < 5, reported separately); among the other 245: one-sided p < 0.05: 38 (15.5%, 5% expected under no effect); BH q < 0.1: 1; sum Y = 0 tests: 0

## Pooled mean tau = log(sum Y / sum mu) (log lift; 95% intervals from a bootstrap clustered by category)
| include_sparse | analysis | source | level | duration_class | tests | categories | share_p_below_alpha | tau_p_mean | tau_p_ci_low | tau_p_ci_high | tau_s_mean | tau_s_ci_low | tau_s_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | main | gdelt | middle | fading | 106 | 44 | 0.047 | 0.002 | -0.028 | 0.030 | 0.009 | -0.014 | 0.031 |
| False | main | gdelt | middle | intermediate | 5 | 5 | 0.000 | -0.059 | -0.169 | 0.049 | -0.070 | -0.184 | 0.043 |
| False | main | gdelt | middle | sustained | 12 | 11 | 0.083 | 0.067 | -0.041 | 0.169 | 0.018 | -0.037 | 0.082 |
| False | main | gdelt | narrow | fading | 194 | 83 | 0.036 | -0.039 | -0.063 | -0.014 | -0.028 | -0.054 | -0.000 |
| False | main | gdelt | narrow | intermediate | 8 | 7 | 0.125 | -0.060 | -0.205 | 0.036 | -0.066 | -0.229 | 0.048 |
| False | main | gdelt | narrow | sustained | 35 | 28 | 0.029 | 0.081 | 0.003 | 0.162 | 0.062 | 0.005 | 0.129 |
| False | main | gdelt | value | fading | 307 | 121 | 0.163 | -0.060 | -0.099 | -0.020 | -0.057 | -0.103 | -0.009 |
| False | main | gdelt | value | intermediate | 13 | 12 | 0.000 | -0.470 | -0.701 | -0.243 | -0.420 | -0.627 | -0.183 |
| False | main | gdelt | value | sustained | 47 | 37 | 0.340 | 0.150 | 0.043 | 0.265 | 0.138 | -0.000 | 0.278 |
| False | main | wikipedia | middle | fading | 129 | 54 | 0.031 | -0.001 | -0.031 | 0.026 | 0.001 | -0.029 | 0.031 |
| False | main | wikipedia | middle | intermediate | 6 | 5 | 0.000 | -0.065 | -0.091 | -0.034 | -0.061 | -0.084 | -0.024 |
| False | main | wikipedia | middle | sustained | 15 | 12 | 0.200 | 0.167 | 0.067 | 0.317 | 0.149 | 0.067 | 0.268 |
| False | main | wikipedia | narrow | fading | 368 | 158 | 0.046 | -0.021 | -0.057 | 0.012 | -0.029 | -0.069 | 0.006 |
| False | main | wikipedia | narrow | intermediate | 40 | 33 | 0.050 | 0.015 | -0.023 | 0.056 | 0.018 | -0.020 | 0.062 |
| False | main | wikipedia | narrow | sustained | 67 | 48 | 0.075 | 0.018 | -0.063 | 0.101 | 0.010 | -0.069 | 0.089 |
| False | main | wikipedia | value | fading | 906 | 399 | 0.182 | -0.021 | -0.050 | 0.008 | -0.023 | -0.054 | 0.008 |
| False | main | wikipedia | value | intermediate | 118 | 97 | 0.271 | 0.019 | -0.060 | 0.096 | 0.002 | -0.084 | 0.086 |
| False | main | wikipedia | value | sustained | 190 | 133 | 0.168 | 0.005 | -0.076 | 0.080 | -0.022 | -0.106 | 0.056 |
| False | seasonal | gdelt | middle | fading | 6 | 2 | 0.000 | 0.019 | 0.006 | 0.031 | 0.025 | 0.016 | 0.034 |
| False | seasonal | gdelt | middle | sustained | 4 | 1 | 0.000 | 0.034 |  |  | 0.029 |  |  |
| False | seasonal | gdelt | narrow | fading | 25 | 10 | 0.000 | -0.007 | -0.070 | 0.057 | -0.006 | -0.067 | 0.061 |
| False | seasonal | gdelt | narrow | sustained | 5 | 2 | 0.000 | 0.052 | 0.034 | 0.126 | 0.047 | 0.029 | 0.121 |
| False | seasonal | gdelt | value | fading | 31 | 13 | 0.194 | 0.032 | -0.111 | 0.198 | -0.004 | -0.187 | 0.175 |
| False | seasonal | gdelt | value | sustained | 6 | 3 | 0.333 | 0.037 | -0.045 | 0.145 | 0.028 | -0.119 | 0.162 |
| False | seasonal | wikipedia | middle | fading | 19 | 3 | 0.000 | 0.003 | -0.020 | 0.019 | -0.009 | -0.025 | 0.005 |
| False | seasonal | wikipedia | middle | intermediate | 2 | 2 | 0.000 | 0.052 | -0.038 | 0.141 | 0.058 | -0.026 | 0.142 |
| False | seasonal | wikipedia | middle | sustained | 9 | 1 | 0.000 | -0.008 |  |  | 0.012 |  |  |
| False | seasonal | wikipedia | narrow | fading | 67 | 13 | 0.015 | -0.010 | -0.054 | 0.037 | -0.006 | -0.053 | 0.047 |
| False | seasonal | wikipedia | narrow | intermediate | 7 | 5 | 0.000 | -0.008 | -0.059 | 0.024 | 0.013 | -0.035 | 0.040 |
| False | seasonal | wikipedia | narrow | sustained | 16 | 4 | 0.062 | 0.026 | -0.016 | 0.321 | 0.027 | -0.025 | 0.282 |
| False | seasonal | wikipedia | value | fading | 122 | 24 | 0.139 | -0.059 | -0.113 | -0.008 | -0.059 | -0.126 | -0.001 |
| False | seasonal | wikipedia | value | intermediate | 13 | 11 | 0.154 | -0.019 | -0.181 | 0.106 | -0.009 | -0.176 | 0.109 |
| False | seasonal | wikipedia | value | sustained | 73 | 16 | 0.151 | 0.006 | -0.056 | 0.067 | 0.011 | -0.058 | 0.070 |
| False | main | gdelt | middle | all | 123 | 46 | 0.049 | 0.005 | -0.019 | 0.031 | 0.007 | -0.013 | 0.028 |
| False | main | gdelt | narrow | all | 237 | 87 | 0.038 | -0.022 | -0.043 | -0.001 | -0.016 | -0.038 | 0.005 |
| False | main | gdelt | value | all | 367 | 127 | 0.180 | -0.048 | -0.079 | -0.017 | -0.045 | -0.081 | -0.009 |
| False | main | wikipedia | middle | all | 150 | 55 | 0.047 | 0.013 | -0.011 | 0.036 | 0.014 | -0.010 | 0.036 |
| False | main | wikipedia | narrow | all | 475 | 175 | 0.051 | -0.013 | -0.044 | 0.014 | -0.019 | -0.054 | 0.011 |
| False | main | wikipedia | value | all | 1214 | 443 | 0.189 | -0.013 | -0.042 | 0.014 | -0.020 | -0.049 | 0.006 |
| False | seasonal | gdelt | middle | all | 10 | 3 | 0.000 | 0.025 | 0.006 | 0.034 | 0.026 | 0.016 | 0.034 |
| False | seasonal | gdelt | narrow | all | 30 | 11 | 0.000 | 0.003 | -0.055 | 0.059 | 0.003 | -0.049 | 0.060 |
| False | seasonal | gdelt | value | all | 37 | 14 | 0.216 | 0.033 | -0.087 | 0.183 | 0.001 | -0.160 | 0.165 |
| False | seasonal | wikipedia | middle | all | 30 | 3 | 0.000 | 0.003 | -0.017 | 0.012 | 0.002 | -0.024 | 0.008 |
| False | seasonal | wikipedia | narrow | all | 90 | 14 | 0.022 | -0.003 | -0.036 | 0.030 | 0.001 | -0.034 | 0.041 |
| False | seasonal | wikipedia | value | all | 208 | 30 | 0.144 | -0.034 | -0.069 | -0.001 | -0.031 | -0.077 | 0.007 |
| False | main | all | middle | all | 273 | 71 | 0.048 | 0.010 | -0.008 | 0.026 | 0.011 | -0.006 | 0.027 |
| False | main | all | narrow | all | 712 | 198 | 0.046 | -0.016 | -0.040 | 0.007 | -0.018 | -0.045 | 0.006 |
| False | main | all | value | all | 1581 | 470 | 0.187 | -0.021 | -0.045 | -0.000 | -0.026 | -0.050 | -0.004 |
| False | seasonal | all | middle | all | 40 | 5 | 0.000 | 0.008 | -0.007 | 0.017 | 0.008 | -0.012 | 0.020 |
| False | seasonal | all | narrow | all | 120 | 22 | 0.017 | -0.002 | -0.036 | 0.031 | 0.002 | -0.033 | 0.037 |
| False | seasonal | all | value | all | 245 | 40 | 0.155 | -0.024 | -0.060 | 0.013 | -0.026 | -0.072 | 0.015 |
| True | main | gdelt | middle | fading | 106 | 44 | 0.047 | 0.002 | -0.028 | 0.030 | 0.009 | -0.014 | 0.031 |
| True | main | gdelt | middle | intermediate | 5 | 5 | 0.000 | -0.059 | -0.169 | 0.049 | -0.070 | -0.184 | 0.043 |
| True | main | gdelt | middle | sustained | 12 | 11 | 0.083 | 0.067 | -0.041 | 0.169 | 0.018 | -0.037 | 0.082 |
| True | main | gdelt | narrow | fading | 194 | 83 | 0.036 | -0.039 | -0.063 | -0.014 | -0.028 | -0.054 | -0.000 |
| True | main | gdelt | narrow | intermediate | 8 | 7 | 0.125 | -0.060 | -0.205 | 0.036 | -0.066 | -0.229 | 0.048 |
| True | main | gdelt | narrow | sustained | 35 | 28 | 0.029 | 0.081 | 0.003 | 0.162 | 0.062 | 0.005 | 0.129 |
| True | main | gdelt | value | fading | 336 | 132 | 0.152 | -0.045 | -0.083 | -0.008 | -0.046 | -0.088 | -0.004 |
| True | main | gdelt | value | intermediate | 16 | 14 | 0.000 | -0.372 | -0.606 | -0.163 | -0.361 | -0.578 | -0.142 |
| True | main | gdelt | value | sustained | 49 | 39 | 0.327 | 0.124 | 0.003 | 0.243 | 0.125 | -0.010 | 0.269 |
| True | main | wikipedia | middle | fading | 129 | 54 | 0.031 | -0.001 | -0.031 | 0.026 | 0.001 | -0.029 | 0.031 |
| True | main | wikipedia | middle | intermediate | 6 | 5 | 0.000 | -0.065 | -0.091 | -0.034 | -0.061 | -0.084 | -0.024 |
| True | main | wikipedia | middle | sustained | 15 | 12 | 0.200 | 0.167 | 0.067 | 0.317 | 0.149 | 0.067 | 0.268 |
| True | main | wikipedia | narrow | fading | 371 | 160 | 0.046 | -0.019 | -0.056 | 0.012 | -0.019 | -0.051 | 0.010 |
| True | main | wikipedia | narrow | intermediate | 40 | 33 | 0.050 | 0.015 | -0.023 | 0.056 | 0.018 | -0.020 | 0.062 |
| True | main | wikipedia | narrow | sustained | 67 | 48 | 0.075 | 0.018 | -0.063 | 0.101 | 0.010 | -0.069 | 0.089 |
| True | main | wikipedia | value | fading | 991 | 431 | 0.173 | -0.007 | -0.036 | 0.022 | -0.009 | -0.039 | 0.021 |
| True | main | wikipedia | value | intermediate | 122 | 101 | 0.270 | -0.007 | -0.100 | 0.089 | -0.022 | -0.121 | 0.081 |
| True | main | wikipedia | value | sustained | 206 | 146 | 0.165 | 0.018 | -0.047 | 0.084 | -0.018 | -0.090 | 0.050 |
| True | seasonal | gdelt | middle | fading | 6 | 2 | 0.000 | 0.019 | 0.006 | 0.031 | 0.025 | 0.016 | 0.034 |
| True | seasonal | gdelt | middle | sustained | 4 | 1 | 0.000 | 0.034 |  |  | 0.029 |  |  |
| True | seasonal | gdelt | narrow | fading | 25 | 10 | 0.000 | -0.007 | -0.070 | 0.057 | -0.006 | -0.067 | 0.061 |
| True | seasonal | gdelt | narrow | sustained | 5 | 2 | 0.000 | 0.052 | 0.034 | 0.126 | 0.047 | 0.029 | 0.121 |
| True | seasonal | gdelt | value | fading | 35 | 14 | 0.171 | 0.042 | -0.088 | 0.203 | 0.004 | -0.167 | 0.179 |
| True | seasonal | gdelt | value | sustained | 6 | 3 | 0.333 | 0.037 | -0.045 | 0.145 | 0.028 | -0.119 | 0.162 |
| True | seasonal | wikipedia | middle | fading | 19 | 3 | 0.000 | 0.003 | -0.020 | 0.019 | -0.009 | -0.025 | 0.005 |
| True | seasonal | wikipedia | middle | intermediate | 2 | 2 | 0.000 | 0.052 | -0.038 | 0.141 | 0.058 | -0.026 | 0.142 |
| True | seasonal | wikipedia | middle | sustained | 9 | 1 | 0.000 | -0.008 |  |  | 0.012 |  |  |
| True | seasonal | wikipedia | narrow | fading | 67 | 13 | 0.015 | -0.010 | -0.054 | 0.037 | -0.006 | -0.053 | 0.047 |
| True | seasonal | wikipedia | narrow | intermediate | 7 | 5 | 0.000 | -0.008 | -0.059 | 0.024 | 0.013 | -0.035 | 0.040 |
| True | seasonal | wikipedia | narrow | sustained | 16 | 4 | 0.062 | 0.026 | -0.016 | 0.321 | 0.027 | -0.025 | 0.282 |
| True | seasonal | wikipedia | value | fading | 150 | 27 | 0.113 | -0.029 | -0.085 | 0.030 | -0.023 | -0.088 | 0.042 |
| True | seasonal | wikipedia | value | intermediate | 16 | 13 | 0.125 | -0.005 | -0.137 | 0.096 | -0.047 | -0.219 | 0.073 |
| True | seasonal | wikipedia | value | sustained | 77 | 17 | 0.143 | 0.010 | -0.035 | 0.061 | 0.025 | -0.019 | 0.074 |
| True | main | gdelt | middle | all | 123 | 46 | 0.049 | 0.005 | -0.019 | 0.031 | 0.007 | -0.013 | 0.028 |
| True | main | gdelt | narrow | all | 237 | 87 | 0.038 | -0.022 | -0.043 | -0.001 | -0.016 | -0.038 | 0.005 |
| True | main | gdelt | value | all | 401 | 137 | 0.167 | -0.038 | -0.068 | -0.006 | -0.038 | -0.072 | -0.002 |
| True | main | wikipedia | middle | all | 150 | 55 | 0.047 | 0.013 | -0.011 | 0.036 | 0.014 | -0.010 | 0.036 |
| True | main | wikipedia | narrow | all | 478 | 177 | 0.050 | -0.011 | -0.042 | 0.016 | -0.012 | -0.043 | 0.015 |
| True | main | wikipedia | value | all | 1319 | 474 | 0.180 | -0.003 | -0.028 | 0.022 | -0.011 | -0.038 | 0.014 |
| True | seasonal | gdelt | middle | all | 10 | 3 | 0.000 | 0.025 | 0.006 | 0.034 | 0.026 | 0.016 | 0.034 |
| True | seasonal | gdelt | narrow | all | 30 | 11 | 0.000 | 0.003 | -0.055 | 0.059 | 0.003 | -0.049 | 0.060 |
| True | seasonal | gdelt | value | all | 41 | 15 | 0.195 | 0.042 | -0.078 | 0.175 | 0.008 | -0.137 | 0.150 |
| True | seasonal | wikipedia | middle | all | 30 | 3 | 0.000 | 0.003 | -0.017 | 0.012 | 0.002 | -0.024 | 0.008 |
| True | seasonal | wikipedia | narrow | all | 90 | 14 | 0.022 | -0.003 | -0.036 | 0.030 | 0.001 | -0.034 | 0.041 |
| True | seasonal | wikipedia | value | all | 243 | 34 | 0.123 | -0.015 | -0.045 | 0.014 | -0.009 | -0.043 | 0.023 |
| True | main | all | middle | all | 273 | 71 | 0.048 | 0.010 | -0.008 | 0.026 | 0.011 | -0.006 | 0.027 |
| True | main | all | narrow | all | 715 | 200 | 0.046 | -0.014 | -0.039 | 0.007 | -0.013 | -0.035 | 0.009 |
| True | main | all | value | all | 1720 | 504 | 0.177 | -0.011 | -0.033 | 0.011 | -0.018 | -0.040 | 0.006 |
| True | seasonal | all | middle | all | 40 | 5 | 0.000 | 0.008 | -0.007 | 0.017 | 0.008 | -0.012 | 0.020 |
| True | seasonal | all | narrow | all | 120 | 22 | 0.017 | -0.002 | -0.036 | 0.031 | 0.002 | -0.033 | 0.037 |
| True | seasonal | all | value | all | 284 | 44 | 0.134 | -0.007 | -0.036 | 0.027 | -0.007 | -0.041 | 0.029 |

## LibriVox (its own exposure; outside BH, pooling and the carry-over regression)
- tests 1888 shift rows, 1394 usable and not too sparse; one-sided p < 0.05: 64; mean tau -0.036
| source | level | tests | mean_tau | share_p_below_alpha |
| --- | --- | --- | --- | --- |
| gdelt | middle | 73 | -0.119 | 0.027 |
| gdelt | narrow | 120 | -0.222 | 0.042 |
| gdelt | value | 115 | -0.002 | 0.043 |
| wikipedia | middle | 139 | -0.040 | 0.029 |
| wikipedia | narrow | 302 | -0.064 | 0.046 |
| wikipedia | value | 645 | 0.015 | 0.053 |
