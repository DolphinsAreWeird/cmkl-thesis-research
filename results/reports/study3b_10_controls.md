# Study 3b positive controls

- step: 10
- written: 2026-10-14 00:12:45
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json

- controls status: FAIL
- control COVID-19: PASS
- control George Floyd / BLM: PASS
- control #MeToo: FAIL
- shift screen for placebos: applied (3997 interest shifts, narrow, middle and value)

Pass rule: tau_p > 0 with one-sided placebo-category rank p < 0.05 in the joint Seattle model (months 0 to +2). tau = log(sum Y / sum mu); z = tau / sqrt(phi / sum mu); p_cat = (1 + number of placebo categories with z >= treated z) / (placebos + 1); _s = months 0 to +5; py_share_ge = share of placebo years with z at or above the treated z. LibriVox is shown and does not decide.

If a control fails (record): check data and mappings for errors only; log any fix in prereg/DEVIATIONS.md; do not tune settings on other categories. Step 11 refuses to run until --accept-failed-controls is given.

### COVID-19: PASS

Epidemics and plagues (narrow, B15.M04.N05), month 0 = 2020-03

| control | kind | formats | phi | sumy_p | summu_p | tau_p | z_p | p_cat_p | n_placebos | too_sparse | tau_s | z_s | p_cat_s | tau_pre | py_share_ge | py_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COVID-19 | seattle | audiobook,ebook,print | 0.755 | 2591.336 | 1930.382 | 0.294 | 14.890 | 0.017 | 114 | False | 0.267 | 19.453 | 0.017 | -0.043 | 0.000 | 5 |
| COVID-19 | librivox | librivox | 677.148 | 165705.770 | 13063.069 | 2.540 | 11.158 | 0.072 | 68 | False | 2.102 | 12.137 | 0.087 | 0.105 | 0.000 | 4 |

Per format (secondary; z uses the joint dispersion):

| format | sumy_p | summu_p | tau_p | z_p | tau_s | z_s |
| --- | --- | --- | --- | --- | --- | --- |
| audiobook | 882.663 | 515.056 | 0.539 | 14.070 | 0.548 | 21.051 |
| ebook | 1488.814 | 1251.038 | 0.174 | 7.083 | 0.123 | 7.398 |
| print | 219.859 | 164.288 | 0.291 | 4.298 | 0.291 | 4.298 |

Monthly observed and expected weighted checkouts, months -6 to +5 (joint model, descriptive):

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 780.795 | 758.190 | 1.030 |
| -5 | 777.668 | 805.434 | 0.966 |
| -4 | 702.245 | 750.687 | 0.935 |
| -3 | 696.842 | 748.556 | 0.931 |
| -2 | 757.659 | 806.641 | 0.939 |
| -1 | 719.978 | 759.016 | 0.949 |
| 0 | 856.224 | 701.695 | 1.220 |
| 1 | 771.620 | 572.875 | 1.347 |
| 2 | 963.492 | 655.812 | 1.469 |
| 3 | 822.665 | 647.183 | 1.271 |
| 4 | 869.766 | 689.273 | 1.262 |
| 5 | 938.953 | 730.780 | 1.285 |

### George Floyd / BLM: PASS

Race and racism (narrow, B05.M02.N02), month 0 = 2020-06

| control | kind | formats | phi | sumy_p | summu_p | tau_p | z_p | p_cat_p | n_placebos | too_sparse | tau_s | z_s | p_cat_s | tau_pre | py_share_ge | py_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| George Floyd / BLM | seattle | audiobook,ebook,print | 4.927 | 15667.670 | 4520.636 | 1.243 | 37.649 | 0.009 | 114 | False | 0.928 | 41.388 | 0.009 | 0.002 | 0.000 | 4 |
| George Floyd / BLM | librivox | librivox | 11270.879 | 11791.352 | 139006.641 | -2.467 | -8.664 | 1.000 | 69 | False | -2.256 | -9.315 | 1.000 | -0.103 | 1.000 | 4 |

Per format (secondary; z uses the joint dispersion):

| format | sumy_p | summu_p | tau_p | z_p | tau_s | z_s |
| --- | --- | --- | --- | --- | --- | --- |
| audiobook | 7846.286 | 2285.610 | 1.233 | 26.565 | 0.887 | 27.547 |
| ebook | 7821.384 | 2235.026 | 1.253 | 26.678 | 1.013 | 30.598 |
| print |  |  |  |  | 0.457 | 4.826 |

Monthly observed and expected weighted checkouts, months -6 to +5 (joint model, descriptive):

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 2175.447 | 2223.504 | 0.978 |
| -5 | 2630.476 | 2483.123 | 1.059 |
| -4 | 2508.243 | 2410.173 | 1.041 |
| -3 | 1905.516 | 1990.323 | 0.957 |
| -2 | 1237.211 | 1337.415 | 0.925 |
| -1 | 1493.821 | 1481.763 | 1.008 |
| 0 | 7896.511 | 1438.273 | 5.490 |
| 1 | 4267.616 | 1449.365 | 2.944 |
| 2 | 3503.543 | 1632.997 | 2.145 |
| 3 | 3079.944 | 1554.322 | 1.982 |
| 4 | 3186.987 | 1835.248 | 1.737 |
| 5 | 2859.675 | 1893.580 | 1.510 |

### #MeToo: FAIL

Sexual violence and domestic violence (narrow, B12.M01.N02), month 0 = 2017-10

| control | kind | formats | phi | sumy_p | summu_p | tau_p | z_p | p_cat_p | n_placebos | too_sparse | tau_s | z_s | p_cat_s | tau_pre | py_share_ge | py_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #MeToo | seattle | audiobook,ebook,print | 0.517 | 1447.266 | 1099.936 | 0.274 | 12.657 | 0.061 | 146.000 | False | 0.348 | 22.934 | 0.041 | 0.230 | 0.167 | 6.000 |
| #MeToo | librivox |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

Per format (secondary; z uses the joint dispersion):

| format | sumy_p | summu_p | tau_p | z_p | tau_s | z_s |
| --- | --- | --- | --- | --- | --- | --- |
| audiobook | 255.737 | 215.091 | 0.173 | 3.530 | 0.201 | 5.985 |
| ebook | 467.396 | 356.092 | 0.272 | 7.138 | 0.351 | 13.171 |
| print | 724.134 | 528.753 | 0.314 | 10.056 | 0.403 | 18.262 |

Monthly observed and expected weighted checkouts, months -6 to +5 (joint model, descriptive):

| month | observed | expected | ratio |
| --- | --- | --- | --- |
| -6 | 368.799 | 309.302 | 1.192 |
| -5 | 334.681 | 342.024 | 0.979 |
| -4 | 381.075 | 370.853 | 1.028 |
| -3 | 500.092 | 368.038 | 1.359 |
| -2 | 571.712 | 410.598 | 1.392 |
| -1 | 561.120 | 359.208 | 1.562 |
| 0 | 526.403 | 364.667 | 1.444 |
| 1 | 480.533 | 369.195 | 1.302 |
| 2 | 440.330 | 366.074 | 1.203 |
| 3 | 456.992 | 393.410 | 1.162 |
| 4 | 576.945 | 358.503 | 1.609 |
| 5 | 703.141 | 397.213 | 1.770 |

### Values inside the control nodes (descriptive, outside the pass rule)

| control | values_tested | tau_p_median | share_tau_positive | share_p_below_alpha | too_sparse |
| --- | --- | --- | --- | --- | --- |
| #MeToo | 64 | -0.206 | 0.406 | 0.078 | 35 |
| COVID-19 | 44 | 0.488 | 0.727 | 0.318 | 26 |
| George Floyd / BLM | 47 | 0.740 | 0.681 | 0.468 | 19 |

Single values are in controls_values.csv.
