# Study 3 positive controls

- step: 10
- written: 2026-10-13 21:03:42
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

- controls status: FAIL
- control COVID-19: FAIL
- control George Floyd / Black Lives Matter: PASS
- control #MeToo: NOT TESTABLE (below minimum size)
- shift part of the donor rule: applied (1491 shifts in the interest table, all classes and both sources)
- interest inputs present: shifts.parquet, gdelt/weekly_node.parquet, gdelt_duration_scaling.json; interest checkpoint report present

Pass rule: positive synthetic-control effect over months 0 to +2 with one-sided rank p < 0.05 in at least one Seattle format. Columns: _p = months 0 to +2, _s = months 0 to +5; pc_ = share of donor categories with an event-study effect >= the real one; py_ = share of placebo years with an effect >= the real one.

If a control fails (record): check data and mappings for errors only; log any fix in prereg/DEVIATIONS.md; do not tune thresholds on other categories. Step 11 refuses to run until --accept-failed-controls is given.

### COVID-19: FAIL

COVID-19: Epidemics and plagues (narrow, B15.M04.N05), month 0 = 2020-03, works in main assignment: 2133

| title_backup | format | skip | sc_n_donors | es_effect_p | es_effect_s | es_pretrend | sc_effect_p | sc_p_p | sc_effect_s | sc_p_s | pc_es_share_ge_p | py_sc_share_ge | py_sc_n | py_es_share_ge | lag_peak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | audiobook | below minimum size |  |  |  |  |  |  |  |  |  |  |  |  |  |
| False | ebook |  | 60.000 | 0.191 | 0.123 | -0.087 | 0.272 | 0.115 | 0.298 | 0.098 | 0.150 | 0.000 | 4.000 | 0.500 | 5.000 |
| False | librivox |  | 27.000 | 1.775 | 1.179 | 0.111 | 1.746 | 0.036 | 1.088 | 0.036 | 0.000 | 0.000 | 4.000 | 0.000 | 1.000 |
| False | print |  | 92.000 |  |  | -0.053 |  |  |  |  |  |  | 3.000 |  | 0.000 |

Monthly gaps (log share), months -6 to +6, descriptive:

| month | es_gap_ebook | es_gap_librivox | es_gap_print | sc_gap_ebook | sc_gap_librivox | sc_gap_print |
| --- | --- | --- | --- | --- | --- | --- |
| -6 | -0.011 | 0.345 | 0.040 | 0.051 | -0.040 | 0.048 |
| -5 | -0.059 | -0.132 | -0.082 | 0.084 | -0.004 | 0.013 |
| -4 | -0.114 | -0.017 | -0.076 | -0.050 | -0.009 | 0.002 |
| -3 | -0.116 | 0.155 | -0.114 | 0.002 | -0.092 | -0.016 |
| -2 | -0.125 | 0.247 | 0.019 | -0.058 | 0.008 | 0.084 |
| -1 | -0.095 | 0.071 | -0.102 | -0.002 | 0.049 | 0.059 |
| 0 | 0.112 | 0.791 | 0.350 | 0.148 | 0.690 | 0.387 |
| 1 | 0.257 | 3.130 |  | 0.323 | 3.258 |  |
| 2 | 0.203 | 1.404 |  | 0.344 | 1.288 |  |
| 3 | 0.031 | 0.586 |  | 0.303 | 0.448 |  |
| 4 | 0.080 | 0.509 |  | 0.298 | 0.440 |  |
| 5 | 0.053 | 0.655 |  | 0.370 | 0.405 |  |
| 6 | -0.107 | 0.706 |  | 0.338 | 0.250 |  |

### George Floyd / Black Lives Matter: PASS

George Floyd / Black Lives Matter: Race and racism (narrow, B05.M02.N02), month 0 = 2020-06, works in main assignment: 8529

| title_backup | format | skip | sc_n_donors | es_effect_p | es_effect_s | es_pretrend | sc_effect_p | sc_p_p | sc_effect_s | sc_p_s | pc_es_share_ge_p | py_sc_share_ge | py_sc_n | py_es_share_ge | lag_peak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | audiobook |  | 36 | 1.193 | 0.836 | -0.070 | 1.509 | 0.027 | 1.146 | 0.027 | 0.000 | 0.000 | 4 | 0.000 | 0 |
| False | ebook |  | 58 | 1.161 | 0.950 | 0.069 | 1.039 | 0.017 | 0.806 | 0.017 | 0.000 | 0.000 | 4 | 0.000 | 0 |
| False | librivox |  | 27 | -1.748 | -1.655 | -0.343 | -0.080 | 0.464 | -0.172 | 0.500 | 1.000 | 0.500 | 4 | 1.000 | 0 |
| False | print |  | 88 |  | 0.439 | 0.024 |  |  | 0.426 | 0.225 |  |  | 3 |  | 6 |

Monthly gaps (log share), months -6 to +6, descriptive:

| month | es_gap_audiobook | es_gap_ebook | es_gap_librivox | es_gap_print | sc_gap_audiobook | sc_gap_ebook | sc_gap_librivox | sc_gap_print |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -6 | -0.014 | 0.092 | 2.117 | -0.038 | -0.028 | -0.016 | 1.060 | -0.002 |
| -5 | 0.048 | 0.143 | -0.426 | 0.064 | 0.055 | 0.015 | -0.662 | 0.059 |
| -4 | 0.020 | 0.122 | -0.520 | 0.044 | 0.131 | 0.058 | -0.382 | 0.071 |
| -3 | -0.147 | 0.009 | -0.616 | 0.025 | 0.057 | -0.029 | -0.371 | 0.020 |
| -2 | -0.190 | 0.009 | -0.808 |  | -0.041 | -0.095 | -0.432 |  |
| -1 | -0.135 | 0.037 | -1.807 |  | 0.159 | -0.073 | -0.420 |  |
| 0 | 1.666 | 1.633 | -1.175 |  | 2.043 | 1.528 | 0.306 |  |
| 1 | 1.134 | 0.976 | -1.414 |  | 1.422 | 0.831 | -0.230 |  |
| 2 | 0.777 | 0.873 | -2.656 |  | 1.062 | 0.759 | -0.317 |  |
| 3 | 0.665 | 0.829 | -2.077 |  | 0.973 | 0.709 | -0.311 |  |
| 4 | 0.476 | 0.769 | -1.242 | 0.432 | 0.769 | 0.635 | -0.230 | 0.428 |
| 5 | 0.296 | 0.617 | -1.368 | 0.446 | 0.608 | 0.374 | -0.250 | 0.423 |
| 6 | 0.204 | 0.538 | -1.694 | 0.465 | 0.451 | 0.379 | -0.313 | 0.565 |

### #MeToo: NOT TESTABLE (below minimum size)

#MeToo: Sexual violence and domestic violence (narrow, B12.M01.N02), month 0 = 2017-10, works in main assignment: 2827

| title_backup | format | skip | sc_n_donors | es_effect_p | es_effect_s | es_pretrend | sc_effect_p | sc_p_p | sc_effect_s | sc_p_s | pc_es_share_ge_p | py_sc_share_ge | py_sc_n | py_es_share_ge | lag_peak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | audiobook | below minimum size |  |  |  |  |  |  |  |  |  |  |  |  |  |
| False | ebook | below minimum size |  |  |  |  |  |  |  |  |  |  |  |  |  |
| False | librivox | below minimum size |  |  |  |  |  |  |  |  |  |  |  |  |  |
| False | print | below minimum size |  |  |  |  |  |  |  |  |  |  |  |  |  |

Monthly gaps (log share), months -6 to +6, descriptive:


