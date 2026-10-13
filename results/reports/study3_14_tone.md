# Study 3 tone

- step: 14
- written: 2026-10-13 21:16:04
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

- tone features for 804 shifts; placebo windows per category: 200 (record 200)
- bootstrap: 2000 resamples (record 2000); seed 20261013
- placebo_p: share of placebo-feature coefficients with |coef| >= |real coef|

## Tone added to the carry-over model
| source | level | feature | coef | ci_low | ci_high | boot_p | placebo_p | placebo_fits | n_tests | n_categories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gdelt | middle | tone_change | 0.023 | -0.022 | 0.053 | 0.286 | 0.575 | 200 | 331 | 45 |
| gdelt | middle | tone_pos_change | 0.037 | -0.129 | 0.156 | 0.675 | 0.690 | 200 | 331 | 45 |
| gdelt | middle | tone_neg_change | -0.025 | -0.066 | 0.024 | 0.331 | 0.595 | 200 | 331 | 45 |
| gdelt | narrow | tone_change | -0.019 | -0.066 | 0.017 | 0.251 | 0.600 | 200 | 390 | 72 |
| gdelt | narrow | tone_pos_change | -0.100 | -0.188 | -0.023 | 0.019 | 0.140 | 200 | 390 | 72 |
| gdelt | narrow | tone_neg_change | 0.005 | -0.041 | 0.072 | 0.700 | 0.900 | 200 | 390 | 72 |
| wikipedia | middle | tone_change | 0.024 | -0.051 | 0.284 | 0.765 | 0.715 | 200 | 133 | 26 |
| wikipedia | middle | tone_pos_change | 0.029 | -0.132 | 0.547 | 0.914 | 0.820 | 200 | 133 | 26 |
| wikipedia | middle | tone_neg_change | -0.059 | -0.398 | 0.078 | 0.560 | 0.545 | 200 | 133 | 26 |
| wikipedia | narrow | tone_change | -0.000 | -0.127 | 0.053 | 0.816 | 0.995 | 200 | 182 | 49 |
| wikipedia | narrow | tone_pos_change | -0.068 | -0.301 | 0.023 | 0.138 | 0.500 | 200 | 182 | 49 |
| wikipedia | narrow | tone_neg_change | -0.037 | -0.126 | 0.110 | 0.516 | 0.640 | 200 | 182 | 49 |

## Shift tone features against their own category's placebo windows (share of shifts outside the 5-95% range)
- tone_change_placebo_pct: 0.144 of 1104
- tone_pos_change_placebo_pct: 0.153 of 1104
- tone_neg_change_placebo_pct: 0.111 of 1104
