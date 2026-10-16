# Study 3b power by injected lifts

- step: 11
- written: 2026-10-14 00:20:09
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json

- draws per lift size and band: 200 (record 200); lifts [0.1, 0.2, 0.3, 0.5, 1.0] (plus 0 as a calibration check); seed 20261013; detection: one-sided rank p < 0.05; MDE: smallest lift detected in >= 80% of draws
- positive-controls status when run: FAIL
- size band edges (sum mu, quartiles per level): 
| level | units | edge_0 | edge_1 | edge_2 | edge_3 | edge_4 |
| --- | --- | --- | --- | --- | --- | --- |
| narrow | 18553 | 0.005 | 1106.594 | 2720.810 | 5835.759 | 69629.000 |
| middle | 6584 | 389.864 | 5927.505 | 11109.014 | 21781.144 | 81436.703 |
| value | 1772721 | 0.000 | 1.401 | 5.542 | 26.632 | 583862417620992.000 |
- run time 408s with 3 workers

### narrow, size band 1 of 4 (sum mu 0.0 to 1106.6): minimum detectable lift 1.0

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 10 | 0.050 | 163.500 |
| 0.100 | 200 | 15 | 0.075 | 163.500 |
| 0.200 | 200 | 33 | 0.165 | 163.500 |
| 0.300 | 200 | 52 | 0.260 | 163.500 |
| 0.500 | 200 | 101 | 0.505 | 163.500 |
| 1.000 | 200 | 160 | 0.800 | 163.500 |

### narrow, size band 2 of 4 (sum mu 1106.6 to 2720.8): minimum detectable lift 1.0

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 19 | 0.095 | 174.000 |
| 0.100 | 200 | 33 | 0.165 | 174.000 |
| 0.200 | 200 | 61 | 0.305 | 174.000 |
| 0.300 | 200 | 99 | 0.495 | 174.000 |
| 0.500 | 200 | 148 | 0.740 | 174.000 |
| 1.000 | 200 | 184 | 0.920 | 174.000 |

### narrow, size band 3 of 4 (sum mu 2720.8 to 5835.8): minimum detectable lift 1.0

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 10 | 0.050 | 176.000 |
| 0.100 | 200 | 29 | 0.145 | 176.000 |
| 0.200 | 200 | 78 | 0.390 | 176.000 |
| 0.300 | 200 | 104 | 0.520 | 176.000 |
| 0.500 | 200 | 150 | 0.750 | 176.000 |
| 1.000 | 200 | 190 | 0.950 | 176.000 |

### narrow, size band 4 of 4 (sum mu 5835.8 to 69629.0): minimum detectable lift 0.5

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 3 | 0.015 | 172.500 |
| 0.100 | 200 | 34 | 0.170 | 172.500 |
| 0.200 | 200 | 90 | 0.450 | 172.500 |
| 0.300 | 200 | 139 | 0.695 | 172.500 |
| 0.500 | 200 | 180 | 0.900 | 172.500 |
| 1.000 | 200 | 199 | 0.995 | 172.500 |

### middle, size band 1 of 4 (sum mu 389.9 to 5927.5): minimum detectable lift 1.0

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 10 | 0.050 | 59.000 |
| 0.100 | 200 | 21 | 0.105 | 59.000 |
| 0.200 | 200 | 74 | 0.370 | 59.000 |
| 0.300 | 200 | 109 | 0.545 | 59.000 |
| 0.500 | 200 | 154 | 0.770 | 59.000 |
| 1.000 | 200 | 191 | 0.955 | 59.000 |

### middle, size band 2 of 4 (sum mu 5927.5 to 11109.0): minimum detectable lift 0.5

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 8 | 0.040 | 56.000 |
| 0.100 | 200 | 30 | 0.150 | 56.000 |
| 0.200 | 200 | 70 | 0.350 | 56.000 |
| 0.300 | 200 | 120 | 0.600 | 56.000 |
| 0.500 | 200 | 180 | 0.900 | 56.000 |
| 1.000 | 200 | 198 | 0.990 | 56.000 |

### middle, size band 3 of 4 (sum mu 11109.0 to 21781.1): minimum detectable lift 0.5

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 7 | 0.035 | 60.000 |
| 0.100 | 200 | 36 | 0.180 | 60.000 |
| 0.200 | 200 | 91 | 0.455 | 60.000 |
| 0.300 | 200 | 130 | 0.650 | 60.000 |
| 0.500 | 200 | 179 | 0.895 | 60.000 |
| 1.000 | 200 | 197 | 0.985 | 60.000 |

### middle, size band 4 of 4 (sum mu 21781.1 to 81436.7): minimum detectable lift 0.5

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 14 | 0.070 | 61.000 |
| 0.100 | 200 | 61 | 0.305 | 61.000 |
| 0.200 | 200 | 118 | 0.590 | 61.000 |
| 0.300 | 200 | 159 | 0.795 | 61.000 |
| 0.500 | 200 | 182 | 0.910 | 61.000 |
| 1.000 | 200 | 195 | 0.975 | 61.000 |

### value, size band 1 of 4 (sum mu 0.0 to 1.4): minimum detectable lift none of the sizes

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 5 | 0.025 | 16178.000 |
| 0.100 | 200 | 6 | 0.030 | 16178.000 |
| 0.200 | 200 | 7 | 0.035 | 16178.000 |
| 0.300 | 200 | 7 | 0.035 | 16178.000 |
| 0.500 | 200 | 7 | 0.035 | 16178.000 |
| 1.000 | 200 | 13 | 0.065 | 16178.000 |

### value, size band 2 of 4 (sum mu 1.4 to 5.5): minimum detectable lift none of the sizes

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 4 | 0.020 | 16190.500 |
| 0.100 | 200 | 4 | 0.020 | 16190.500 |
| 0.200 | 200 | 6 | 0.030 | 16190.500 |
| 0.300 | 200 | 6 | 0.030 | 16190.500 |
| 0.500 | 200 | 12 | 0.060 | 16190.500 |
| 1.000 | 200 | 22 | 0.110 | 16190.500 |

### value, size band 3 of 4 (sum mu 5.5 to 26.6): minimum detectable lift none of the sizes

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 10 | 0.050 | 16178.000 |
| 0.100 | 200 | 14 | 0.070 | 16178.000 |
| 0.200 | 200 | 21 | 0.105 | 16178.000 |
| 0.300 | 200 | 30 | 0.150 | 16178.000 |
| 0.500 | 200 | 39 | 0.195 | 16178.000 |
| 1.000 | 200 | 71 | 0.355 | 16178.000 |

### value, size band 4 of 4 (sum mu 26.6 to 583862417620992.0): minimum detectable lift none of the sizes

| lift | draws | detected | rate | median_placebos |
| --- | --- | --- | --- | --- |
| 0.000 | 200 | 19 | 0.095 | 16200.500 |
| 0.100 | 200 | 29 | 0.145 | 16200.500 |
| 0.200 | 200 | 44 | 0.220 | 16200.500 |
| 0.300 | 200 | 55 | 0.275 | 16200.500 |
| 0.500 | 200 | 82 | 0.410 | 16200.500 |
| 1.000 | 200 | 114 | 0.570 | 16200.500 |

