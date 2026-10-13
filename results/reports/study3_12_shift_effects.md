# Study 3 shift effects

- step: 12
- written: 2026-10-13 21:09:07
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

- interest inputs present: shifts.parquet, gdelt/weekly_node.parquet, gdelt_duration_scaling.json; interest checkpoint report present
- bootstrap resamples: 2000 (record 2000), seed 20261013
- last demand month per format: audiobook: 2026-08, ebook: 2026-08, librivox: 2026-08, print: 2026-08
- run time 215s

## Shifts
- in the interest table: 1491; without a record duration class (interrupted, censored): 19; labelled, at tested levels, from 2017-01: 1160
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

## Tests (shift x format)
| analysis | format | skip | tests |
| --- | --- | --- | --- |
| main | audiobook | below minimum size | 526 |
| main | audiobook | tested | 472 |
| main | ebook | below minimum size | 377 |
| main | ebook | tested | 621 |
| main | librivox | below minimum size | 374 |
| main | librivox | no data | 263 |
| main | librivox | tested | 335 |
| main | librivox | too few fit months | 26 |
| main | print | below minimum size | 217 |
| main | print | tested | 680 |
| main | print | too few fit months | 101 |
| seasonal | audiobook | below minimum size | 62 |
| seasonal | audiobook | tested | 100 |
| seasonal | ebook | below minimum size | 40 |
| seasonal | ebook | tested | 122 |
| seasonal | librivox | below minimum size | 61 |
| seasonal | librivox | no data | 35 |
| seasonal | librivox | tested | 62 |
| seasonal | librivox | too few fit months | 4 |
| seasonal | print | below minimum size | 25 |
| seasonal | print | tested | 119 |
| seasonal | print | too few fit months | 18 |

## Detection (synthetic control, months 0 to +2)
- main: 2108 tests; one-sided p < 0.05: 102; BH q < 0.1: 0
- seasonal: 403 tests; one-sided p < 0.05: 7; BH q < 0.1: 0

## Pooled mean effects (log share; 95% intervals from a bootstrap clustered by category)
| analysis | source | level | format | duration_class | tests | categories | sc_effect_p_mean | sc_effect_p_ci_low | sc_effect_p_ci_high | es_effect_p_mean | es_effect_p_ci_low | es_effect_p_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | gdelt | middle | audiobook | all | 75 | 35 | 0.050 | 0.015 | 0.087 | 0.016 | -0.020 | 0.050 |
| main | gdelt | middle | ebook | all | 112 | 43 | 0.007 | -0.015 | 0.031 | -0.002 | -0.029 | 0.026 |
| main | gdelt | middle | librivox | all | 57 | 24 | 0.098 | 0.025 | 0.167 | -0.060 | -0.149 | 0.030 |
| main | gdelt | middle | print | all | 105 | 45 | 0.015 | -0.018 | 0.049 | 0.005 | -0.032 | 0.042 |
| main | gdelt | narrow | audiobook | all | 76 | 36 | 0.048 | 0.004 | 0.100 | -0.019 | -0.067 | 0.029 |
| main | gdelt | narrow | ebook | all | 121 | 48 | -0.008 | -0.033 | 0.017 | -0.023 | -0.054 | 0.007 |
| main | gdelt | narrow | librivox | all | 68 | 28 | 0.059 | -0.025 | 0.151 | -0.013 | -0.124 | 0.110 |
| main | gdelt | narrow | print | all | 161 | 71 | 0.028 | 0.001 | 0.056 | -0.000 | -0.033 | 0.030 |
| main | wikipedia | middle | audiobook | all | 131 | 52 | 0.035 | 0.008 | 0.065 | 0.009 | -0.019 | 0.037 |
| main | wikipedia | middle | ebook | all | 148 | 55 | 0.022 | 0.003 | 0.040 | 0.010 | -0.020 | 0.039 |
| main | wikipedia | middle | librivox | all | 75 | 37 | 0.070 | 0.013 | 0.124 | 0.001 | -0.088 | 0.086 |
| main | wikipedia | middle | print | all | 125 | 53 | 0.022 | -0.004 | 0.047 | 0.018 | -0.010 | 0.043 |
| main | wikipedia | narrow | audiobook | all | 190 | 85 | 0.030 | 0.007 | 0.054 | -0.020 | -0.048 | 0.010 |
| main | wikipedia | narrow | ebook | all | 240 | 100 | 0.022 | 0.004 | 0.042 | -0.004 | -0.031 | 0.022 |
| main | wikipedia | narrow | librivox | all | 135 | 63 | 0.047 | -0.013 | 0.110 | -0.001 | -0.075 | 0.076 |
| main | wikipedia | narrow | print | all | 289 | 130 | 0.036 | 0.015 | 0.058 | 0.007 | -0.019 | 0.031 |
| seasonal | gdelt | middle | audiobook | all | 8 | 3 | 0.183 | -0.003 | 0.347 | 0.033 | 0.019 | 0.068 |
| seasonal | gdelt | middle | ebook | all | 10 | 3 | 0.195 | -0.028 | 0.431 | 0.026 | -0.006 | 0.041 |
| seasonal | gdelt | middle | librivox | all | 5 | 2 | 0.182 | 0.035 | 0.280 | 0.031 | 0.015 | 0.064 |
| seasonal | gdelt | middle | print | all | 10 | 3 | 0.261 | -0.056 | 0.487 | 0.056 | 0.035 | 0.097 |
| seasonal | gdelt | narrow | audiobook | all | 11 | 5 | 0.142 | -0.020 | 0.301 | 0.025 | -0.009 | 0.048 |
| seasonal | gdelt | narrow | ebook | all | 16 | 6 | 0.132 | -0.001 | 0.296 | 0.020 | -0.021 | 0.051 |
| seasonal | gdelt | narrow | librivox | all | 6 | 3 | 0.201 | 0.036 | 0.342 | 0.021 | -0.012 | 0.065 |
| seasonal | gdelt | narrow | print | all | 22 | 9 | 0.117 | -0.032 | 0.287 | 0.039 | -0.037 | 0.127 |
| seasonal | wikipedia | middle | audiobook | all | 23 | 3 | -0.037 | -0.046 | 0.005 | 0.005 | -0.039 | 0.016 |
| seasonal | wikipedia | middle | ebook | all | 30 | 3 | -0.032 | -0.038 | -0.017 | 0.028 | 0.004 | 0.049 |
| seasonal | wikipedia | middle | librivox | all | 21 | 2 | -0.061 | -0.084 | 0.015 | 0.016 | -0.006 | 0.022 |
| seasonal | wikipedia | middle | print | all | 25 | 3 | 0.003 | -0.072 | 0.034 | -0.015 | -0.039 | -0.007 |
| seasonal | wikipedia | narrow | audiobook | all | 58 | 10 | 0.012 | -0.029 | 0.076 | 0.014 | -0.019 | 0.058 |
| seasonal | wikipedia | narrow | ebook | all | 66 | 12 | 0.012 | -0.022 | 0.070 | 0.012 | -0.025 | 0.055 |
| seasonal | wikipedia | narrow | librivox | all | 30 | 4 | -0.103 | -0.225 | -0.001 | -0.012 | -0.087 | 0.029 |
| seasonal | wikipedia | narrow | print | all | 62 | 12 | 0.033 | -0.010 | 0.070 | -0.005 | -0.037 | 0.027 |
| main | gdelt | middle | all | all | 349 | 46 | 0.034 | 0.008 | 0.061 | -0.004 | -0.032 | 0.023 |
| main | gdelt | narrow | all | all | 426 | 72 | 0.026 | 0.004 | 0.050 | -0.013 | -0.042 | 0.014 |
| main | wikipedia | middle | all | all | 479 | 56 | 0.033 | 0.015 | 0.052 | 0.010 | -0.014 | 0.031 |
| main | wikipedia | narrow | all | all | 854 | 142 | 0.033 | 0.016 | 0.051 | -0.004 | -0.024 | 0.018 |
| seasonal | gdelt | middle | all | all | 33 | 3 | 0.209 | -0.017 | 0.400 | 0.037 | 0.031 | 0.045 |
| seasonal | gdelt | narrow | all | all | 55 | 9 | 0.136 | -0.003 | 0.275 | 0.029 | -0.016 | 0.066 |
| seasonal | wikipedia | middle | all | all | 99 | 3 | -0.031 | -0.035 | -0.017 | 0.010 | -0.014 | 0.016 |
| seasonal | wikipedia | narrow | all | all | 216 | 13 | 0.001 | -0.028 | 0.050 | 0.004 | -0.021 | 0.030 |
| main | gdelt | middle | all | fading | 296 | 44 | 0.036 | 0.011 | 0.059 | -0.004 | -0.035 | 0.026 |
| main | gdelt | middle | all | intermediate | 16 | 5 | 0.071 | -0.034 | 0.187 | 0.006 | -0.048 | 0.062 |
| main | gdelt | middle | all | sustained | 37 | 11 | -0.002 | -0.064 | 0.053 | -0.009 | -0.053 | 0.036 |
| main | gdelt | narrow | all | fading | 339 | 68 | 0.011 | -0.011 | 0.032 | -0.023 | -0.055 | 0.010 |
| main | gdelt | narrow | all | intermediate | 14 | 6 | 0.011 | -0.070 | 0.090 | -0.015 | -0.227 | 0.112 |
| main | gdelt | narrow | all | sustained | 73 | 22 | 0.104 | 0.027 | 0.177 | 0.035 | -0.030 | 0.109 |
| main | wikipedia | middle | all | fading | 406 | 55 | 0.026 | 0.004 | 0.049 | 0.001 | -0.027 | 0.024 |
| main | wikipedia | middle | all | intermediate | 17 | 5 | -0.004 | -0.035 | 0.060 | -0.074 | -0.170 | 0.004 |
| main | wikipedia | middle | all | sustained | 56 | 13 | 0.105 | 0.018 | 0.227 | 0.115 | 0.053 | 0.193 |
| main | wikipedia | narrow | all | fading | 650 | 123 | 0.019 | 0.002 | 0.037 | -0.022 | -0.046 | 0.001 |
| main | wikipedia | narrow | all | intermediate | 83 | 27 | 0.062 | 0.003 | 0.124 | 0.033 | -0.023 | 0.085 |
| main | wikipedia | narrow | all | sustained | 121 | 37 | 0.088 | 0.029 | 0.156 | 0.078 | 0.021 | 0.142 |
| seasonal | gdelt | middle | all | fading | 20 | 2 | 0.078 | -0.017 | 0.208 | 0.032 | 0.031 | 0.033 |
| seasonal | gdelt | middle | all | sustained | 13 | 1 | 0.400 |  |  | 0.045 |  |  |
| seasonal | gdelt | narrow | all | fading | 40 | 8 | 0.055 | -0.016 | 0.160 | 0.019 | -0.037 | 0.072 |
| seasonal | gdelt | narrow | all | sustained | 15 | 2 | 0.345 | -0.012 | 0.400 | 0.055 | 0.045 | 0.114 |
| seasonal | wikipedia | middle | all | fading | 62 | 3 | -0.134 | -0.228 | -0.013 | -0.006 | -0.025 | 0.005 |
| seasonal | wikipedia | middle | all | intermediate | 5 | 2 | -0.021 | -0.037 | -0.011 | 0.078 | -0.026 | 0.147 |
| seasonal | wikipedia | middle | all | sustained | 32 | 1 | 0.164 |  |  | 0.029 |  |  |
| seasonal | wikipedia | narrow | all | fading | 140 | 12 | -0.054 | -0.145 | 0.044 | -0.004 | -0.038 | 0.034 |
| seasonal | wikipedia | narrow | all | intermediate | 19 | 4 | 0.054 | -0.017 | 0.161 | 0.001 | -0.082 | 0.170 |
| seasonal | wikipedia | narrow | all | sustained | 57 | 4 | 0.121 | -0.012 | 0.210 | 0.027 | -0.040 | 0.330 |
