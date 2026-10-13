# Study 3 injected-lift power

- step: 11
- written: 2026-10-13 21:05:00
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

- draws per lift size: 200 (record 200); lifts [0.1, 0.2, 0.24, 0.3, 0.43, 0.5]; seed 20261013; detection: one-sided p < 0.05; MDE: smallest lift detected in >= 80% of draws
- positive-controls status when run: FAIL
- shift screen: applied (1491 shifts in the interest table, all classes and both sources)
- run time 11s with 3 workers

### middle, audiobook: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 198 | 46 | 0.232 | 0.101 |
| 0.200 | 0.182 | 198 | 88 | 0.444 | 0.188 |
| 0.240 | 0.215 | 198 | 101 | 0.510 | 0.221 |
| 0.300 | 0.262 | 198 | 116 | 0.586 | 0.268 |
| 0.430 | 0.358 | 198 | 130 | 0.657 | 0.363 |
| 0.500 | 0.405 | 198 | 141 | 0.712 | 0.411 |

### middle, ebook: minimum detectable lift 0.5

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 193 | 42 | 0.218 | 0.097 |
| 0.200 | 0.182 | 193 | 89 | 0.461 | 0.184 |
| 0.240 | 0.215 | 193 | 100 | 0.518 | 0.217 |
| 0.300 | 0.262 | 193 | 126 | 0.653 | 0.264 |
| 0.430 | 0.358 | 193 | 154 | 0.798 | 0.359 |
| 0.500 | 0.405 | 193 | 164 | 0.850 | 0.407 |

### middle, librivox: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 200 | 13 | 0.065 | 0.102 |
| 0.200 | 0.182 | 200 | 25 | 0.125 | 0.189 |
| 0.240 | 0.215 | 200 | 31 | 0.155 | 0.222 |
| 0.300 | 0.262 | 200 | 35 | 0.175 | 0.269 |
| 0.430 | 0.358 | 200 | 47 | 0.235 | 0.364 |
| 0.500 | 0.405 | 200 | 53 | 0.265 | 0.412 |

### middle, print: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 162 | 36 | 0.222 | 0.094 |
| 0.200 | 0.182 | 162 | 66 | 0.407 | 0.181 |
| 0.240 | 0.215 | 162 | 80 | 0.494 | 0.213 |
| 0.300 | 0.262 | 162 | 90 | 0.556 | 0.261 |
| 0.430 | 0.358 | 162 | 116 | 0.716 | 0.356 |
| 0.500 | 0.405 | 162 | 122 | 0.753 | 0.404 |

### narrow, audiobook: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 194 | 29 | 0.149 | 0.101 |
| 0.200 | 0.182 | 194 | 65 | 0.335 | 0.188 |
| 0.240 | 0.215 | 194 | 73 | 0.376 | 0.221 |
| 0.300 | 0.262 | 194 | 85 | 0.438 | 0.268 |
| 0.430 | 0.358 | 194 | 115 | 0.593 | 0.363 |
| 0.500 | 0.405 | 194 | 134 | 0.691 | 0.411 |

### narrow, ebook: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 195 | 46 | 0.236 | 0.089 |
| 0.200 | 0.182 | 195 | 80 | 0.410 | 0.176 |
| 0.240 | 0.215 | 195 | 95 | 0.487 | 0.209 |
| 0.300 | 0.262 | 195 | 115 | 0.590 | 0.256 |
| 0.430 | 0.358 | 195 | 138 | 0.708 | 0.351 |
| 0.500 | 0.405 | 195 | 144 | 0.738 | 0.399 |

### narrow, librivox: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 200 | 11 | 0.055 | 0.093 |
| 0.200 | 0.182 | 200 | 15 | 0.075 | 0.180 |
| 0.240 | 0.215 | 200 | 17 | 0.085 | 0.213 |
| 0.300 | 0.262 | 200 | 20 | 0.100 | 0.260 |
| 0.430 | 0.358 | 200 | 28 | 0.140 | 0.355 |
| 0.500 | 0.405 | 200 | 32 | 0.160 | 0.403 |

### narrow, print: minimum detectable lift none of the sizes

| lift | true_log_lift | draws | detected | rate | mean_effect |
| --- | --- | --- | --- | --- | --- |
| 0.100 | 0.095 | 157 | 24 | 0.153 | 0.110 |
| 0.200 | 0.182 | 157 | 40 | 0.255 | 0.197 |
| 0.240 | 0.215 | 157 | 48 | 0.306 | 0.229 |
| 0.300 | 0.262 | 157 | 64 | 0.408 | 0.277 |
| 0.430 | 0.358 | 157 | 94 | 0.599 | 0.372 |
| 0.500 | 0.405 | 157 | 105 | 0.669 | 0.420 |

