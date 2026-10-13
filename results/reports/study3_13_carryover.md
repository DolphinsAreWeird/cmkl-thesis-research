# Study 3 carry-over model

- step: 13
- written: 2026-10-13 21:13:27
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

- tests in the model: 1989 (main analysis, synthetic control estimated); classic (LibriVox) tests: 330
- bootstrap clustered by category: 2000 resamples (record 2000), seed 20261013; 95% percentile intervals
- outcome: synthetic-control effect, months 0 to +2; reference duration class: fading

## Coefficients
| source | level | term | coef | ci_low | ci_high | boot_p | boot_valid | n_tests | n_categories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gdelt | middle | const | -0.100 | -0.156 | 0.060 | 0.264 | 2000 | 333 | 45 |
| gdelt | middle | log_size | 0.130 | -0.027 | 0.246 | 0.145 | 2000 | 333 | 45 |
| gdelt | middle | class_intermediate | -0.005 | -0.068 | 0.062 | 0.884 | 1988 | 333 | 45 |
| gdelt | middle | class_sustained | -0.111 | -0.236 | -0.031 | 0.005 | 2000 | 333 | 45 |
| gdelt | middle | broad_B02 | 0.064 | -0.069 | 0.115 | 0.124 | 1237 | 333 | 45 |
| gdelt | middle | broad_B03 | 0.080 | -0.067 | 0.158 | 0.376 | 1903 | 333 | 45 |
| gdelt | middle | broad_B04 | 0.050 | -0.088 | 0.149 | 0.626 | 1988 | 333 | 45 |
| gdelt | middle | broad_B05 | 0.160 | 0.029 | 0.272 | 0.009 | 1909 | 333 | 45 |
| gdelt | middle | broad_B06 | 0.021 | -0.083 | 0.055 | 0.858 | 1277 | 333 | 45 |
| gdelt | middle | broad_B07 | 0.043 | -0.074 | 0.116 | 0.572 | 1719 | 333 | 45 |
| gdelt | middle | broad_B08 | -0.033 | -0.170 | 0.063 | 0.313 | 1969 | 333 | 45 |
| gdelt | middle | broad_B09 | 0.076 | -0.031 | 0.107 | 0.310 | 1972 | 333 | 45 |
| gdelt | middle | broad_B10 | -0.015 | -0.124 | 0.013 | 0.188 | 1757 | 333 | 45 |
| gdelt | middle | broad_B11 | 0.089 | -0.036 | 0.188 | 0.221 | 1919 | 333 | 45 |
| gdelt | middle | broad_B12 | 0.074 | -0.045 | 0.141 | 0.298 | 1962 | 333 | 45 |
| gdelt | middle | broad_B13 | 0.080 | -0.043 | 0.190 | 0.275 | 1738 | 333 | 45 |
| gdelt | middle | broad_B14 | 0.028 | -0.084 | 0.076 | 0.857 | 1281 | 333 | 45 |
| gdelt | middle | broad_B15 | 0.043 | -0.097 | 0.162 | 0.728 | 1901 | 333 | 45 |
| gdelt | middle | broad_B16 | 0.065 | -0.050 | 0.124 | 0.343 | 1282 | 333 | 45 |
| gdelt | middle | broad_B17 | 0.119 | 0.008 | 0.152 | 0.030 | 1272 | 333 | 45 |
| gdelt | middle | broad_B19 | 0.082 | -0.029 | 0.109 | 0.256 | 1280 | 333 | 45 |
| gdelt | middle | format_ebook | -0.033 | -0.070 | 0.007 | 0.113 | 2000 | 333 | 45 |
| gdelt | middle | format_print | -0.024 | -0.069 | 0.020 | 0.350 | 2000 | 333 | 45 |
| gdelt | middle | classic | 0.056 | -0.020 | 0.116 | 0.137 | 2000 | 333 | 45 |
| gdelt | narrow | const | -0.064 | -0.142 | 0.077 | 0.420 | 2000 | 395 | 72 |
| gdelt | narrow | log_size | 0.069 | -0.052 | 0.221 | 0.299 | 2000 | 395 | 72 |
| gdelt | narrow | class_intermediate | -0.032 | -0.129 | 0.074 | 0.600 | 1996 | 395 | 72 |
| gdelt | narrow | class_sustained | 0.052 | -0.064 | 0.176 | 0.478 | 2000 | 395 | 72 |
| gdelt | narrow | broad_B02 | 0.097 | -0.041 | 0.166 | 0.109 | 1703 | 395 | 72 |
| gdelt | narrow | broad_B03 | 0.078 | -0.052 | 0.131 | 0.330 | 1962 | 395 | 72 |
| gdelt | narrow | broad_B04 | 0.123 | -0.024 | 0.181 | 0.119 | 1996 | 395 | 72 |
| gdelt | narrow | broad_B05 | 0.081 | -0.078 | 0.197 | 0.360 | 1985 | 395 | 72 |
| gdelt | narrow | broad_B06 | -0.032 | -0.157 | 0.028 | 0.224 | 1304 | 395 | 72 |
| gdelt | narrow | broad_B07 | 0.066 | -0.068 | 0.199 | 0.384 | 1962 | 395 | 72 |
| gdelt | narrow | broad_B08 | -0.031 | -0.162 | 0.049 | 0.409 | 1999 | 395 | 72 |
| gdelt | narrow | broad_B09 | 0.109 | -0.033 | 0.178 | 0.166 | 2000 | 395 | 72 |
| gdelt | narrow | broad_B10 | -0.009 | -0.141 | 0.055 | 0.558 | 2000 | 395 | 72 |
| gdelt | narrow | broad_B11 | 0.152 | 0.018 | 0.267 | 0.022 | 1728 | 395 | 72 |
| gdelt | narrow | broad_B12 | 0.067 | -0.056 | 0.130 | 0.387 | 1985 | 395 | 72 |
| gdelt | narrow | broad_B13 | 0.133 | -0.029 | 0.201 | 0.113 | 1992 | 395 | 72 |
| gdelt | narrow | broad_B15 | 0.041 | -0.108 | 0.138 | 0.730 | 1999 | 395 | 72 |
| gdelt | narrow | broad_B16 | -0.018 | -0.150 | 0.055 | 0.425 | 1265 | 395 | 72 |
| gdelt | narrow | broad_B17 | 0.117 | -0.005 | 0.156 | 0.057 | 1266 | 395 | 72 |
| gdelt | narrow | broad_B19 | -0.017 | -0.156 | 0.069 | 0.582 | 1743 | 395 | 72 |
| gdelt | narrow | format_ebook | -0.063 | -0.107 | -0.016 | 0.003 | 2000 | 395 | 72 |
| gdelt | narrow | format_print | -0.025 | -0.078 | 0.034 | 0.435 | 2000 | 395 | 72 |
| gdelt | narrow | classic | -0.009 | -0.114 | 0.108 | 0.918 | 2000 | 395 | 72 |
| wikipedia | middle | const | 0.045 | -0.060 | 0.142 | 0.436 | 2000 | 452 | 55 |
| wikipedia | middle | log_size | 0.048 | -0.049 | 0.154 | 0.250 | 2000 | 452 | 55 |
| wikipedia | middle | class_intermediate | -0.041 | -0.124 | 0.021 | 0.148 | 1991 | 452 | 55 |
| wikipedia | middle | class_sustained | 0.043 | -0.072 | 0.186 | 0.490 | 2000 | 452 | 55 |
| wikipedia | middle | broad_B02 | 0.035 | -0.112 | 0.150 | 0.601 | 1824 | 452 | 55 |
| wikipedia | middle | broad_B03 | -0.064 | -0.160 | 0.001 | 0.059 | 1733 | 452 | 55 |
| wikipedia | middle | broad_B04 | -0.065 | -0.170 | 0.047 | 0.250 | 1997 | 452 | 55 |
| wikipedia | middle | broad_B05 | 0.001 | -0.122 | 0.122 | 0.961 | 1960 | 452 | 55 |
| wikipedia | middle | broad_B06 | -0.092 | -0.204 | 0.017 | 0.122 | 1998 | 452 | 55 |
| wikipedia | middle | broad_B08 | -0.081 | -0.194 | -0.002 | 0.036 | 1998 | 452 | 55 |
| wikipedia | middle | broad_B09 | 0.013 | -0.092 | 0.131 | 0.643 | 1752 | 452 | 55 |
| wikipedia | middle | broad_B10 | -0.176 | -0.304 | -0.049 | 0.002 | 1723 | 452 | 55 |
| wikipedia | middle | broad_B11 | -0.110 | -0.206 | -0.048 | 0.000 | 1254 | 452 | 55 |
| wikipedia | middle | broad_B12 | -0.087 | -0.193 | 0.030 | 0.084 | 1907 | 452 | 55 |
| wikipedia | middle | broad_B13 | -0.025 | -0.123 | 0.059 | 0.645 | 1985 | 452 | 55 |
| wikipedia | middle | broad_B14 | -0.092 | -0.184 | -0.002 | 0.043 | 1724 | 452 | 55 |
| wikipedia | middle | broad_B15 | -0.085 | -0.210 | 0.039 | 0.250 | 1731 | 452 | 55 |
| wikipedia | middle | broad_B16 | -0.072 | -0.237 | 0.053 | 0.297 | 1738 | 452 | 55 |
| wikipedia | middle | broad_B17 | 0.076 | -0.181 | 0.353 | 0.383 | 1904 | 452 | 55 |
| wikipedia | middle | broad_B18 | -0.076 | -0.170 | -0.010 | 0.021 | 1259 | 452 | 55 |
| wikipedia | middle | broad_B19 | -0.156 | -0.250 | -0.086 | 0.000 | 1249 | 452 | 55 |
| wikipedia | middle | format_ebook | -0.013 | -0.031 | 0.004 | 0.159 | 2000 | 452 | 55 |
| wikipedia | middle | format_print | -0.012 | -0.040 | 0.020 | 0.523 | 2000 | 452 | 55 |
| wikipedia | middle | classic | 0.040 | -0.023 | 0.100 | 0.233 | 2000 | 452 | 55 |
| wikipedia | narrow | const | 0.059 | 0.001 | 0.111 | 0.047 | 2000 | 809 | 140 |
| wikipedia | narrow | log_size | -0.031 | -0.102 | 0.042 | 0.439 | 2000 | 809 | 140 |
| wikipedia | narrow | class_intermediate | 0.059 | -0.011 | 0.124 | 0.109 | 2000 | 809 | 140 |
| wikipedia | narrow | class_sustained | 0.067 | 0.015 | 0.140 | 0.010 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B02 | 0.094 | -0.046 | 0.167 | 0.159 | 1996 | 809 | 140 |
| wikipedia | narrow | broad_B03 | -0.029 | -0.072 | 0.011 | 0.126 | 1994 | 809 | 140 |
| wikipedia | narrow | broad_B04 | -0.052 | -0.118 | 0.054 | 0.262 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B05 | 0.013 | -0.052 | 0.115 | 0.788 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B06 | -0.031 | -0.110 | 0.054 | 0.484 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B07 | -0.067 | -0.171 | 0.005 | 0.064 | 1999 | 809 | 140 |
| wikipedia | narrow | broad_B08 | -0.074 | -0.123 | -0.023 | 0.007 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B09 | -0.018 | -0.090 | 0.048 | 0.579 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B10 | -0.099 | -0.174 | 0.009 | 0.053 | 1990 | 809 | 140 |
| wikipedia | narrow | broad_B11 | -0.073 | -0.107 | -0.041 | 0.000 | 1281 | 809 | 140 |
| wikipedia | narrow | broad_B12 | -0.005 | -0.073 | 0.127 | 0.898 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B13 | -0.040 | -0.104 | 0.012 | 0.122 | 2000 | 809 | 140 |
| wikipedia | narrow | broad_B14 | -0.031 | -0.111 | 0.032 | 0.425 | 1999 | 809 | 140 |
| wikipedia | narrow | broad_B15 | -0.056 | -0.118 | 0.048 | 0.290 | 1991 | 809 | 140 |
| wikipedia | narrow | broad_B16 | 0.027 | -0.069 | 0.329 | 0.656 | 1996 | 809 | 140 |
| wikipedia | narrow | broad_B17 | 0.071 | -0.060 | 0.180 | 0.267 | 1999 | 809 | 140 |
| wikipedia | narrow | broad_B18 | -0.055 | -0.107 | 0.228 | 0.562 | 1910 | 809 | 140 |
| wikipedia | narrow | broad_B19 | 0.004 | -0.125 | 0.161 | 0.934 | 1999 | 809 | 140 |
| wikipedia | narrow | format_ebook | -0.009 | -0.030 | 0.011 | 0.357 | 2000 | 809 | 140 |
| wikipedia | narrow | format_print | 0.005 | -0.023 | 0.030 | 0.738 | 2000 | 809 | 140 |
| wikipedia | narrow | classic | 0.021 | -0.044 | 0.090 | 0.542 | 2000 | 809 | 140 |

## Lag of the peak gap (months 0 to +6)
| source | level | duration_class | tests | mean | median |
| --- | --- | --- | --- | --- | --- |
| gdelt | middle | fading | 285 | 2.726 | 2.000 |
| gdelt | middle | intermediate | 16 | 3.375 | 3.500 |
| gdelt | middle | sustained | 32 | 3.188 | 3.000 |
| gdelt | narrow | fading | 317 | 2.722 | 2.000 |
| gdelt | narrow | intermediate | 13 | 2.692 | 3.000 |
| gdelt | narrow | sustained | 65 | 2.277 | 2.000 |
| wikipedia | middle | fading | 388 | 2.433 | 2.000 |
| wikipedia | middle | intermediate | 16 | 2.250 | 2.000 |
| wikipedia | middle | sustained | 48 | 2.646 | 2.500 |
| wikipedia | narrow | fading | 621 | 2.541 | 2.000 |
| wikipedia | narrow | intermediate | 81 | 2.679 | 2.000 |
| wikipedia | narrow | sustained | 107 | 2.664 | 2.000 |
