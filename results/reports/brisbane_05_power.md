# Brisbane replication: power by injected lifts

- written: 2026-10-15 02:56:03; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- 200 draws per lift and size band, lifts [0.2, 0.5, 1.0] (+0 as a calibration check), seed 20261015; month 0 2016-01 to 2025-06; detection one-sided rank p < 0.05; MDE = smallest lift detected in >= 80% of draws
- size band edges (expected weighted loans in months 0 to +2, quartiles of all placebo units per level):
| level | units | edge_0 | edge_1 | edge_2 | edge_3 | edge_4 |
| --- | --- | --- | --- | --- | --- | --- |
| narrow | 14924 | 0.0 | 33.8 | 79.8 | 196.4 | 4471.5 |
| middle | 5306 | 5.8 | 145.5 | 292.3 | 604.9 | 5220.6 |

## Detection by lift, all size bands together (an average over small and large themes)
| level | lift | draws | detected | rate | mde_all_bands |
| --- | --- | --- | --- | --- | --- |
| middle | 0.000 | 800 | 42 | 0.052 | 0.500 |
| middle | 0.200 | 800 | 344 | 0.430 | 0.500 |
| middle | 0.500 | 800 | 683 | 0.854 | 0.500 |
| middle | 1.000 | 800 | 775 | 0.969 | 0.500 |
| narrow | 0.000 | 800 | 38 | 0.048 | 1.000 |
| narrow | 0.200 | 800 | 217 | 0.271 | 1.000 |
| narrow | 0.500 | 800 | 495 | 0.619 | 1.000 |
| narrow | 1.000 | 800 | 677 | 0.846 | 1.000 |

## By size band

### narrow, size band 1 of 4 (expected loans 0.0 to 33.8): minimum detectable lift none of the sizes

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 11 | 0.055 |
| 0.200 | 200 | 25 | 0.125 |
| 0.500 | 200 | 58 | 0.290 |
| 1.000 | 200 | 123 | 0.615 |

### narrow, size band 2 of 4 (expected loans 33.8 to 79.8): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 9 | 0.045 |
| 0.200 | 200 | 41 | 0.205 |
| 0.500 | 200 | 99 | 0.495 |
| 1.000 | 200 | 162 | 0.810 |

### narrow, size band 3 of 4 (expected loans 79.8 to 196.4): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 12 | 0.060 |
| 0.200 | 200 | 61 | 0.305 |
| 0.500 | 200 | 154 | 0.770 |
| 1.000 | 200 | 192 | 0.960 |

### narrow, size band 4 of 4 (expected loans 196.4 to 4471.5): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 6 | 0.030 |
| 0.200 | 200 | 90 | 0.450 |
| 0.500 | 200 | 184 | 0.920 |
| 1.000 | 200 | 200 | 1.000 |

### middle, size band 1 of 4 (expected loans 5.8 to 145.5): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 11 | 0.055 |
| 0.200 | 200 | 39 | 0.195 |
| 0.500 | 200 | 125 | 0.625 |
| 1.000 | 200 | 178 | 0.890 |

### middle, size band 2 of 4 (expected loans 145.5 to 292.3): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 8 | 0.040 |
| 0.200 | 200 | 81 | 0.405 |
| 0.500 | 200 | 179 | 0.895 |
| 1.000 | 200 | 199 | 0.995 |

### middle, size band 3 of 4 (expected loans 292.3 to 604.9): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 14 | 0.070 |
| 0.200 | 200 | 98 | 0.490 |
| 0.500 | 200 | 189 | 0.945 |
| 1.000 | 200 | 200 | 1.000 |

### middle, size band 4 of 4 (expected loans 604.9 to 5220.6): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 9 | 0.045 |
| 0.200 | 200 | 126 | 0.630 |
| 0.500 | 200 | 190 | 0.950 |
| 1.000 | 200 | 198 | 0.990 |

run time 1s
