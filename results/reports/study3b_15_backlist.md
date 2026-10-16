# Study 3b backlist robustness run

- step: 15
- written: 2026-10-14 05:31:18
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json, 2026-10-14_b_backlist_robustness.json

## What was run
- demand restricted to backlist works: first checkout in any Seattle format at least 13 months before month 0 of the test (addendum 2026-10-14 b, made after the 3b results were seen). Seattle formats only (LibriVox not run).
- everything else as in 3b: same shifts, joint quasi-Poisson model, fit window, windows 0 to +2 and 0 to +5, placebo categories (same month 0, same restricted demand, same shift screen), placebo years (each at its own month 0), BH families, pooling and bootstrap (2,000 resamples, seed 20261013).
- exposure N (all checkouts of the format that month) is unchanged; only Y is restricted. NOT IN RECORD, logged in DEVIATIONS.md.
- builder check: with every work eligible it reproduces the 3b count panel (largest relative difference: narrow 9.0e-16, middle 1.2e-15, value 2.1e-14).
- run time 2293s, one process.

## Positive controls: backlist demand beside the main 3b run

Pass rule as in 3b: tau > 0 and one-sided placebo-category rank p < 0.05 (months 0 to +2, joint Seattle model).

| control | main_tau | main_p | main_verdict | backlist_tau | backlist_p | backlist_verdict | backlist_tau_s | backlist_p_s | main_tau_pre | backlist_tau_pre | backlist_share_of_main_y | n_placebos | placebo_years | py_share_ge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COVID-19 | 0.294 | 0.017 | PASS | 0.122 | 0.043 | PASS | 0.052 | 0.096 | -0.043 | -0.358 | 0.755 | 114 | 5 | 0.000 |
| George Floyd / BLM | 1.243 | 0.009 | PASS | 0.957 | 0.009 | PASS | 0.673 | 0.009 | 0.002 | -0.192 | 0.686 | 114 | 4 | 0.000 |
| #MeToo | 0.274 | 0.061 | FAIL | -0.302 | 0.456 | FAIL | -0.272 | 0.395 | 0.230 | -0.164 | 0.478 | 146 | 6 | 0.833 |

main_tau_pre and backlist_tau_pre: log of observed over expected in months -6 to -1 (the earlier rise). backlist_share_of_main_y: backlist weighted checkouts over the main ones in months 0 to +2.

### COVID-19: monthly observed and expected weighted checkouts, backlist demand, months -6 to +5

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 507.134 | 692.249 | 0.733 |
| -5 | 518.002 | 735.641 | 0.704 |
| -4 | 452.436 | 685.477 | 0.660 |
| -3 | 456.066 | 684.413 | 0.666 |
| -2 | 525.039 | 737.253 | 0.712 |
| -1 | 498.812 | 693.636 | 0.719 |
| 0 | 656.525 | 632.708 | 1.038 |
| 1 | 599.337 | 514.456 | 1.165 |
| 2 | 700.721 | 585.432 | 1.197 |
| 3 | 555.008 | 560.453 | 0.990 |
| 4 | 566.005 | 584.761 | 0.968 |
| 5 | 573.725 | 589.135 | 0.974 |

### George Floyd / BLM: monthly observed and expected weighted checkouts, backlist demand, months -6 to +5

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 1664.946 | 1988.817 | 0.837 |
| -5 | 1924.583 | 2217.817 | 0.868 |
| -4 | 1811.597 | 2152.971 | 0.841 |
| -3 | 1410.381 | 1799.411 | 0.784 |
| -2 | 938.155 | 1254.930 | 0.748 |
| -1 | 1167.185 | 1393.309 | 0.838 |
| 0 | 5374.511 | 1342.988 | 4.002 |
| 1 | 2928.943 | 1346.061 | 2.176 |
| 2 | 2440.582 | 1437.766 | 1.697 |
| 3 | 2100.593 | 1324.789 | 1.586 |
| 4 | 2030.374 | 1514.173 | 1.341 |
| 5 | 1710.095 | 1495.548 | 1.143 |

### #MeToo: monthly observed and expected weighted checkouts, backlist demand, months -6 to +5

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 275.394 | 275.531 | 1.000 |
| -5 | 255.702 | 305.000 | 0.838 |
| -4 | 284.601 | 331.188 | 0.859 |
| -3 | 291.588 | 327.886 | 0.889 |
| -2 | 272.849 | 365.962 | 0.746 |
| -1 | 254.262 | 320.311 | 0.794 |
| 0 | 235.883 | 321.473 | 0.734 |
| 1 | 229.477 | 313.033 | 0.733 |
| 2 | 226.935 | 301.797 | 0.752 |
| 3 | 253.535 | 319.509 | 0.794 |
| 4 | 237.643 | 294.297 | 0.807 |
| 5 | 232.378 | 309.196 | 0.752 |

### Values inside the control nodes (backlist, descriptive)

| control | values_tested | tau_p_median | share_tau_positive | share_p_below_alpha | too_sparse |
| --- | --- | --- | --- | --- | --- |
| #MeToo | 64 | -0.403 | 0.250 | 0.031 | 35 |
| COVID-19 | 44 | 0.472 | 0.727 | 0.341 | 26 |
| George Floyd / BLM | 47 | 0.740 | 0.617 | 0.468 | 19 |

Single values: data/db/study3b/backlist_controls_values.csv.

## All shifts on backlist demand

### Detection beside main 3b (non-sparse tests; BH within level and family)

| analysis | level | tests_main | p_below_005_main | share_p_below_005_main | bh_q_below_010_main | tests_backlist | p_below_005_backlist | share_p_below_005_backlist | bh_q_below_010_backlist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | middle | 273 | 13 | 0.048 | 0 | 273 | 16 | 0.059 | 0 |
| main | narrow | 712 | 33 | 0.046 | 0 | 712 | 50 | 0.070 | 0 |
| main | value | 1581 | 295 | 0.187 | 11 | 1576 | 151 | 0.096 | 15 |
| seasonal | middle | 40 | 0 | 0.000 | 0 | 40 | 4 | 0.100 | 0 |
| seasonal | narrow | 120 | 2 | 0.017 | 0 | 120 | 6 | 0.050 | 0 |
| seasonal | value | 245 | 38 | 0.155 | 1 | 245 | 21 | 0.086 | 0 |

### Same shift tests, change in tau (main analysis, non-sparse in both runs)

| level | tests | mean_tau_main | mean_tau_backlist | mean_change |
| --- | --- | --- | --- | --- |
| middle | 273 | 0.010 | -0.212 | -0.222 |
| narrow | 712 | -0.016 | -0.228 | -0.212 |
| value | 1576 | -0.020 | -0.194 | -0.174 |

### Pooled mean tau (log lift, months 0 to +2; 95% bootstrap interval clustered by category), main 3b beside backlist (non-sparse, main analysis)

| source | level | duration_class | tests_main | tau_p_mean_main | tau_p_ci_low_main | tau_p_ci_high_main | tests_backlist | tau_p_mean_backlist | tau_p_ci_low_backlist | tau_p_ci_high_backlist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | middle | all | 273 | 0.010 | -0.008 | 0.026 | 273 | -0.212 | -0.231 | -0.193 |
| gdelt | middle | all | 123 | 0.005 | -0.019 | 0.031 | 123 | -0.219 | -0.246 | -0.193 |
| gdelt | middle | fading | 106 | 0.002 | -0.028 | 0.030 | 106 | -0.223 | -0.251 | -0.196 |
| gdelt | middle | sustained | 12 | 0.067 | -0.041 | 0.169 | 12 | -0.166 | -0.279 | -0.066 |
| wikipedia | middle | all | 150 | 0.013 | -0.011 | 0.036 | 150 | -0.206 | -0.235 | -0.180 |
| wikipedia | middle | fading | 129 | -0.001 | -0.031 | 0.026 | 129 | -0.217 | -0.250 | -0.188 |
| wikipedia | middle | sustained | 15 | 0.167 | 0.067 | 0.317 | 15 | -0.065 | -0.184 | 0.094 |
| all | narrow | all | 712 | -0.016 | -0.040 | 0.007 | 712 | -0.228 | -0.253 | -0.205 |
| gdelt | narrow | all | 237 | -0.022 | -0.043 | -0.001 | 237 | -0.232 | -0.258 | -0.209 |
| gdelt | narrow | fading | 194 | -0.039 | -0.063 | -0.014 | 194 | -0.244 | -0.271 | -0.216 |
| gdelt | narrow | sustained | 35 | 0.081 | 0.003 | 0.162 | 35 | -0.148 | -0.223 | -0.063 |
| wikipedia | narrow | all | 475 | -0.013 | -0.044 | 0.014 | 475 | -0.226 | -0.259 | -0.198 |
| wikipedia | narrow | fading | 368 | -0.021 | -0.057 | 0.012 | 368 | -0.234 | -0.269 | -0.201 |
| wikipedia | narrow | sustained | 67 | 0.018 | -0.063 | 0.101 | 67 | -0.197 | -0.280 | -0.114 |
| all | value | all | 1581 | -0.021 | -0.045 | -0.000 | 1576 | -0.194 | -0.217 | -0.171 |
| gdelt | value | all | 367 | -0.048 | -0.079 | -0.017 | 367 | -0.229 | -0.272 | -0.191 |
| gdelt | value | fading | 307 | -0.060 | -0.099 | -0.020 | 307 | -0.233 | -0.273 | -0.191 |
| gdelt | value | sustained | 47 | 0.150 | 0.043 | 0.265 | 47 | -0.082 | -0.222 | 0.044 |
| wikipedia | value | all | 1214 | -0.013 | -0.042 | 0.014 | 1209 | -0.184 | -0.207 | -0.161 |
| wikipedia | value | fading | 906 | -0.021 | -0.050 | 0.008 | 904 | -0.194 | -0.222 | -0.169 |
| wikipedia | value | sustained | 190 | 0.005 | -0.076 | 0.080 | 187 | -0.139 | -0.210 | -0.066 |

### Supplementary (NOT IN RECORD): sustained and fading shifts pooled over sources and levels

| duration_class | scope | tests_main | tau_mean_main | ci_low_main | ci_high_main | tests_backlist | tau_mean_backlist | ci_low_backlist | ci_high_backlist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sustained | all levels | 366 | 0.042 | -0.013 | 0.093 | 363 | -0.141 | -0.191 | -0.093 |
| fading | all levels | 2010 | -0.026 | -0.042 | -0.010 | 2008 | -0.215 | -0.231 | -0.199 |

Full tables: study3b_15_backlist_pooled.csv; shift-level results data/db/study3b/backlist_shift_effects.parquet.
