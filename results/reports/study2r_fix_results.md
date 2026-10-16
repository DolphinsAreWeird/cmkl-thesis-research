# Study 2R results (mapping fix: one unit per Wikipedia article, all Seattle works summed)

<!-- begin controls -->
## Positive controls (run first, before any main analysis)

Built 2026-10-14 21:15 by code/study2r/12_controls.py. Event per addendum c: month 0 = month of the first ratio 1.5 shift within 8 weeks of the release date, else the release month. Outcome: joint print and ebook count event study of the largest matched Seattle work, tau = log(sum Y / sum mu) over months 0 to +2, z, one-sided rank p among 200 matched placebo works.

**Result: PASS.** Pooled mean tau = 1.669 (95% bootstrap interval 0.523 to 2.847; lift 430.5%, interval 68.8% to 1623.0%); 4 of 7 tests with one-sided p < 0.05 (rule: pooled interval above zero and at least 4 of 7).

| control | month0 | source | skip | pf | summu_p | sumy_p | tau_p | lift | z_p | n_placebos | plc_tau_median | p_p | tau_s | p_s | tau_p_print | tau_p_ebook | py_n | py_share_ge | tau_p_audio | p_p_audio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| The Queen's Gambit | 2020-10 | release month (no shift) |  | 0 | 0.682 | 42.000 | 4.120 | 6054.000 | 2.433 | 148 | 0.625 | 0.094 | 4.241 | 0.047 | 4.120 |  | 4 | 0.250 |  |  |
| The Duke and I | 2020-12 | release month (no shift) |  | 1 | 105.082 | 46.000 | -0.826 | -56.200 | -6.307 | 186 | -0.260 | 0.850 | -0.306 | 0.508 | 0.652 | -3.715 | 5 | 0.800 |  |  |
| Dune | 2021-10 | release month (no shift) |  | 1 | 737.955 | 843.000 | 0.133 | 14.200 | 2.283 | 200 | -1.253 | 0.070 | 0.270 | 0.025 | -0.556 | 0.256 | 1 | 0.000 | 0.164 | 0.045 |
| Where the Crawdads Sing | 2022-07 | release month (no shift) |  | 1 | 183.590 | 764.000 | 1.426 | 316.100 | 4.043 | 200 | -0.751 | 0.040 | 1.453 | 0.030 | 1.515 | 1.398 | 2 | 0.000 | 0.051 | 0.090 |
| American Prometheus | 2023-07 | release month (no shift) |  | 1 | 36.342 | 402.000 | 2.403 | 1006.200 | 16.217 | 200 | -0.111 | 0.005 | 2.513 | 0.005 | 1.885 | 2.625 | 6 | 0.000 | 2.793 | 0.005 |
| Killers of the Flower Moon | 2023-10 | release month (no shift) |  | 1 | 189.446 | 924.000 | 1.585 | 387.700 | 10.389 | 191 | -0.853 | 0.005 | 1.563 | 0.005 | 2.962 | 1.505 | 7 | 0.000 | 1.689 | 0.006 |
| Shogun | 2024-02 | release month (no shift) |  | 1 | 24.380 | 417.000 | 2.839 | 1610.400 | 21.706 | 200 | -0.131 | 0.005 | 2.686 | 0.005 |  | 2.839 | 4 | 0.000 | 2.573 | 0.005 |

Columns: summu_p = expected checkouts over months 0 to +2, sumy_p = observed; tau_p, p_p = months 0 to +2 (record primary); tau_s, p_s = months 0 to +5; tau_p_print and tau_p_ebook = the same from the joint fit, per format (descriptive); plc_tau_median = median tau of the 200 placebo works in the same months (diagnostic); py_n and py_share_ge = placebo years and their share with z at or above the treated z (descriptive); tau_p_audio, p_p_audio = separate audiobook model (secondary, descriptive).
<!-- end controls -->

<!-- begin main -->
## Main analysis and confirmatory duration tests

Built 2026-10-14 21:15 by code/study2r/13_effects.py and 14_inference.py.

### Main: calibrated rule (floor 300, ratio 4.0), print and ebook

Tests: 2422 work-shift rows, 2255 with a usable fit and window; 145 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 3 with no checkouts in the window (tau = -infinity; out of the pooled means); 2107 tests in the pooled analysis, 1295 works, 1295 articles. Mean placebo works per test 177.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 2110 tests; p < 0.05 in 431 (20.4%, 5% expected with no effect); p < 0.01 in 156 (7.4%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 21.6%. Placebo years: mean share of placebo-year z at or above the treated z 0.370 (0.5 expected with no effect) over 2050 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.3 and 9.0 (range 4.0 to 457.9).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 2107 | 1295 | 0.103 | 0.047 to 0.152 | 10.900 | 4.8% to 16.4% | 16.400 | 20.500 | 0.048 to 0.154 | positive: interval above 0; cannot rule out +10% |
| class: sustained | 523 | 395 | 0.261 | 0.159 to 0.357 | 29.800 | 17.2% to 42.9% | 42.900 | 31.000 | 0.153 to 0.352 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 210 | 192 | 0.017 | -0.286 to 0.233 | 1.700 | -24.9% to 26.2% | 26.200 | 24.300 | -0.280 to 0.244 | inconclusive: cannot rule out +10% |
| class: fading | 1374 | 995 | 0.056 | -0.008 to 0.113 | 5.800 | -0.7% to 11.9% | 11.900 | 15.900 | -0.009 to 0.117 | inconclusive: cannot rule out +10% |
| whole duration: 1-2 weeks | 1374 | 995 | 0.056 | -0.008 to 0.113 | 5.800 | -0.7% to 11.9% | 11.900 | 15.900 | -0.009 to 0.117 | inconclusive: cannot rule out +10% |
| whole duration: 3 weeks | 210 | 192 | 0.017 | -0.286 to 0.233 | 1.700 | -24.9% to 26.2% | 26.200 | 24.300 | -0.280 to 0.244 | inconclusive: cannot rule out +10% |
| whole duration: 4-5 weeks | 258 | 222 | 0.157 | -0.030 to 0.298 | 17.000 | -3.0% to 34.8% | 34.800 | 28.300 | -0.014 to 0.295 | inconclusive: cannot rule out +10% |
| whole duration: 6+ weeks | 265 | 223 | 0.361 | 0.253 to 0.477 | 43.500 | 28.8% to 61.1% | 61.100 | 33.600 | 0.250 to 0.480 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 703 | 598 | -0.019 | -0.126 to 0.076 | -1.900 | -11.9% to 7.9% | 7.900 | 13.100 | -0.127 to 0.070 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 702 | 576 | 0.099 | 0.007 to 0.183 | 10.400 | 0.7% to 20.0% | 20.000 | 19.100 | 0.003 to 0.185 | positive: interval above 0; cannot rule out +10% |
| size tercile: large | 702 | 546 | 0.229 | 0.143 to 0.305 | 25.700 | 15.3% to 35.6% | 35.600 | 29.200 | 0.143 to 0.311 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 2107 | 0.103 | -0.154 | 0.257 | -0.296 | 0.399 | 0.204 to 0.303 | 0.346 to 0.446 |
| class: sustained | 523 | 0.261 | -0.209 | 0.469 | -0.395 | 0.656 | 0.369 to 0.561 | 0.553 to 0.753 |
| class: intermediate | 210 | 0.017 | -0.161 | 0.177 | -0.293 | 0.310 | -0.105 to 0.378 | 0.033 to 0.502 |
| class: fading | 1374 | 0.056 | -0.132 | 0.188 | -0.258 | 0.314 | 0.129 to 0.241 | 0.256 to 0.368 |
| whole duration: 1-2 weeks | 1374 | 0.056 | -0.132 | 0.188 | -0.258 | 0.314 | 0.129 to 0.241 | 0.256 to 0.368 |
| whole duration: 3 weeks | 210 | 0.017 | -0.161 | 0.177 | -0.293 | 0.310 | -0.105 to 0.378 | 0.033 to 0.502 |
| whole duration: 4-5 weeks | 258 | 0.157 | -0.195 | 0.353 | -0.372 | 0.529 | 0.182 to 0.484 | 0.360 to 0.663 |
| whole duration: 6+ weeks | 265 | 0.361 | -0.221 | 0.583 | -0.418 | 0.779 | 0.482 to 0.686 | 0.671 to 0.892 |
| size tercile: small | 703 | -0.019 | -0.124 | 0.106 | -0.241 | 0.222 | 0.004 to 0.195 | 0.121 to 0.307 |
| size tercile: middle | 702 | 0.099 | -0.152 | 0.251 | -0.291 | 0.391 | 0.162 to 0.329 | 0.304 to 0.468 |
| size tercile: large | 702 | 0.229 | -0.185 | 0.414 | -0.355 | 0.584 | 0.329 to 0.487 | 0.495 to 0.663 |

Secondary window (months 0 to +5), all shifts: mean tau 0.104 (95% interval 0.046 to 0.154).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau 0.253 (0.199 to 0.304), 1695 tests; ebook alone (joint fit): mean tau 0.117 (0.059 to 0.170), 2017 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.082 per doubling (95% interval 0.039 to 0.125), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.039 to 0.125, p = 0.0005.
- H2, 6+ weeks minus 1 to 2 weeks: 0.305 (95% interval 0.177 to 0.438); mean tau 0.361 (265 tests) against 0.056 (1374 tests): **supported (95% interval above 0)**. Clustered by article: 0.174 to 0.435.
- Coefficient of log2 peak size given log2 duration (not tested): 0.152 (95% interval 0.085 to 0.229); log2 duration coefficient in the same model -0.022 (-0.093 to 0.042); correlation of log2 duration and log2 peak 0.72.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 4 weeks (shifts of 4 weeks or less: mean tau 0.050, 1714 tests; longer: 0.334, 393 tests; difference 0.284, 95% interval at the re-estimated threshold 0.181 to 0.432); bootstrap interval of the threshold 2 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.036, 3.0: 0.134, 4.0: 0.663, 5.0: 0.112, 6.0: 0.048, 7.0: 0.006}); likelihood-ratio set [3, 4, 5, 6]; the step explains 0.77% of the variance of tau. Article-clustered threshold interval 2 to 6.

<!-- end main -->

<!-- begin secondary -->
## Secondary analyses and sensitivities

### Secondary: same shifts, audiobook

Tests: 2143 work-shift rows, 1703 with a usable fit and window; 138 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 7 with no checkouts in the window (tau = -infinity; out of the pooled means); 1558 tests in the pooled analysis, 983 works, 983 articles. Mean placebo works per test 198.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 1565 tests; p < 0.05 in 283 (18.1%, 5% expected with no effect); p < 0.01 in 102 (6.5%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 20.6%. Placebo years: mean share of placebo-year z at or above the treated z 0.388 (0.5 expected with no effect) over 1525 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.4 and 9.2 (range 4.0 to 428.5).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 1558 | 983 | 0.050 | -0.022 to 0.118 | 5.100 | -2.2% to 12.5% | 12.500 | 18.200 | -0.025 to 0.119 | inconclusive: cannot rule out +10% |
| class: sustained | 414 | 321 | 0.203 | 0.075 to 0.309 | 22.500 | 7.8% to 36.2% | 36.200 | 24.900 | 0.087 to 0.302 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 175 | 160 | -0.226 | -0.608 to 0.089 | -20.300 | -45.5% to 9.3% | 9.300 | 15.400 | -0.596 to 0.089 | inconclusive (upper bound below +10% but only 160 works, fewer than 299) |
| class: fading | 969 | 728 | 0.034 | -0.057 to 0.116 | 3.400 | -5.6% to 12.3% | 12.300 | 15.800 | -0.058 to 0.114 | inconclusive: cannot rule out +10% |
| whole duration: 1-2 weeks | 969 | 728 | 0.034 | -0.057 to 0.116 | 3.400 | -5.6% to 12.3% | 12.300 | 15.800 | -0.058 to 0.114 | inconclusive: cannot rule out +10% |
| whole duration: 3 weeks | 175 | 160 | -0.226 | -0.608 to 0.089 | -20.300 | -45.5% to 9.3% | 9.300 | 15.400 | -0.596 to 0.089 | inconclusive (upper bound below +10% but only 160 works, fewer than 299) |
| whole duration: 4-5 weeks | 204 | 178 | 0.097 | -0.106 to 0.256 | 10.200 | -10.1% to 29.2% | 29.200 | 21.100 | -0.115 to 0.255 | inconclusive: cannot rule out +10% |
| whole duration: 6+ weeks | 210 | 183 | 0.306 | 0.185 to 0.432 | 35.800 | 20.3% to 54.0% | 54.000 | 28.600 | 0.177 to 0.431 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 520 | 444 | -0.074 | -0.223 to 0.057 | -7.100 | -20.0% to 5.9% | 5.900 | 12.700 | -0.218 to 0.052 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 519 | 440 | 0.070 | -0.058 to 0.179 | 7.200 | -5.7% to 19.7% | 19.700 | 18.700 | -0.060 to 0.180 | inconclusive: cannot rule out +10% |
| size tercile: large | 519 | 407 | 0.153 | 0.022 to 0.263 | 16.500 | 2.3% to 30.0% | 30.000 | 23.100 | 0.027 to 0.267 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 1558 | 0.050 | -0.160 | 0.209 | -0.376 | 0.425 | 0.138 to 0.276 | 0.347 to 0.496 |
| class: sustained | 414 | 0.203 | -0.190 | 0.393 | -0.425 | 0.628 | 0.277 to 0.494 | 0.512 to 0.741 |
| class: intermediate | 175 | -0.226 | -0.194 | -0.032 | -0.453 | 0.227 | -0.393 to 0.265 | -0.123 to 0.520 |
| class: fading | 969 | 0.034 | -0.140 | 0.174 | -0.341 | 0.374 | 0.085 to 0.252 | 0.287 to 0.454 |
| whole duration: 1-2 weeks | 969 | 0.034 | -0.140 | 0.174 | -0.341 | 0.374 | 0.085 to 0.252 | 0.287 to 0.454 |
| whole duration: 3 weeks | 175 | -0.226 | -0.194 | -0.032 | -0.453 | 0.227 | -0.393 to 0.265 | -0.123 to 0.520 |
| whole duration: 4-5 weeks | 204 | 0.097 | -0.193 | 0.291 | -0.418 | 0.515 | 0.092 to 0.442 | 0.319 to 0.680 |
| whole duration: 6+ weeks | 210 | 0.306 | -0.187 | 0.493 | -0.432 | 0.738 | 0.381 to 0.609 | 0.608 to 0.882 |
| size tercile: small | 520 | -0.074 | -0.131 | 0.057 | -0.314 | 0.240 | -0.082 to 0.176 | 0.104 to 0.355 |
| size tercile: middle | 519 | 0.070 | -0.163 | 0.232 | -0.387 | 0.456 | 0.112 to 0.332 | 0.332 to 0.559 |
| size tercile: large | 519 | 0.153 | -0.186 | 0.338 | -0.427 | 0.580 | 0.213 to 0.441 | 0.459 to 0.692 |

Secondary window (months 0 to +5), all shifts: mean tau 0.039 (95% interval -0.041 to 0.115).
Per format, from the joint fit (descriptive): audiobook alone (joint fit): mean tau 0.050 (-0.022 to 0.118), 1558 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.045 per doubling (95% interval -0.011 to 0.103), one-sided p = 0.0595: **not supported**. Clustered by article: interval -0.009 to 0.100, p = 0.0490.
- H2, 6+ weeks minus 1 to 2 weeks: 0.272 (95% interval 0.111 to 0.439); mean tau 0.306 (210 tests) against 0.034 (969 tests): **supported (95% interval above 0)**. Clustered by article: 0.124 to 0.430.
- Coefficient of log2 peak size given log2 duration (not tested): 0.184 (95% interval 0.094 to 0.279); log2 duration coefficient in the same model -0.081 (-0.174 to -0.003); correlation of log2 duration and log2 peak 0.72.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 4 weeks (shifts of 4 weeks or less: mean tau -0.007, 1246 tests; longer: 0.276, 312 tests; difference 0.283, 95% interval at the re-estimated threshold 0.171 to 0.443); bootstrap interval of the threshold 3 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.006, 3.0: 0.168, 4.0: 0.61, 5.0: 0.162, 6.0: 0.048, 7.0: 0.001, 8.0: 0.004}); likelihood-ratio set [3, 4, 5, 6, 7]; the step explains 0.59% of the variance of tau. Article-clustered threshold interval 3 to 6.

### Sensitivity (addendum c): ratio 1.5, print and ebook

Tests: 17120 work-shift rows, 15948 with a usable fit and window; 1138 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 22 with no checkouts in the window (tau = -infinity; out of the pooled means); 14788 tests in the pooled analysis, 3544 works, 3544 articles. Mean placebo works per test 154.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 14810 tests; p < 0.05 in 1249 (8.4%, 5% expected with no effect); p < 0.01 in 232 (1.6%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 9.0%. Placebo years: mean share of placebo-year z at or above the treated z 0.474 (0.5 expected with no effect) over 13589 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 1.7 and 2.2 (range 1.5 to 428.5).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 14788 | 3544 | -0.126 | -0.144 to -0.108 | -11.900 | -13.4% to -10.2% | -10.200 | 8.400 | -0.144 to -0.109 | no meaningful effect (upper bound below +10%) |
| class: sustained | 2983 | 1721 | -0.022 | -0.061 to 0.018 | -2.200 | -5.9% to 1.8% | 1.800 | 14.700 | -0.065 to 0.017 | no meaningful effect (upper bound below +10%) |
| class: intermediate | 1178 | 937 | -0.111 | -0.177 to -0.048 | -10.500 | -16.2% to -4.7% | -4.700 | 10.100 | -0.184 to -0.049 | no meaningful effect (upper bound below +10%) |
| class: fading | 10627 | 3252 | -0.157 | -0.179 to -0.136 | -14.500 | -16.4% to -12.7% | -12.700 | 6.500 | -0.180 to -0.137 | no meaningful effect (upper bound below +10%) |
| whole duration: 1-2 weeks | 10627 | 3252 | -0.157 | -0.179 to -0.136 | -14.500 | -16.4% to -12.7% | -12.700 | 6.500 | -0.180 to -0.137 | no meaningful effect (upper bound below +10%) |
| whole duration: 3 weeks | 1178 | 937 | -0.111 | -0.177 to -0.048 | -10.500 | -16.2% to -4.7% | -4.700 | 10.100 | -0.184 to -0.049 | no meaningful effect (upper bound below +10%) |
| whole duration: 4-5 weeks | 1176 | 938 | -0.078 | -0.141 to -0.017 | -7.500 | -13.1% to -1.7% | -1.700 | 11.100 | -0.144 to -0.019 | no meaningful effect (upper bound below +10%) |
| whole duration: 6+ weeks | 1807 | 1180 | 0.013 | -0.037 to 0.064 | 1.400 | -3.7% to 6.6% | 6.600 | 17.100 | -0.041 to 0.065 | no meaningful effect (upper bound below +10%) |
| size tercile: small | 4930 | 2539 | -0.146 | -0.173 to -0.120 | -13.600 | -15.9% to -11.4% | -11.400 | 6.200 | -0.174 to -0.121 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 4929 | 2469 | -0.179 | -0.216 to -0.147 | -16.400 | -19.4% to -13.6% | -13.600 | 7.300 | -0.214 to -0.145 | no meaningful effect (upper bound below +10%) |
| size tercile: large | 4929 | 2374 | -0.053 | -0.082 to -0.023 | -5.200 | -7.9% to -2.3% | -2.300 | 11.800 | -0.084 to -0.024 | no meaningful effect (upper bound below +10%) |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 14788 | -0.126 | -0.156 | 0.030 | -0.284 | 0.158 | 0.011 to 0.049 | 0.137 to 0.179 |
| class: sustained | 2983 | -0.022 | -0.191 | 0.168 | -0.342 | 0.320 | 0.131 to 0.205 | 0.280 to 0.359 |
| class: intermediate | 1178 | -0.111 | -0.167 | 0.057 | -0.313 | 0.203 | -0.006 to 0.115 | 0.138 to 0.264 |
| class: fading | 10627 | -0.157 | -0.146 | -0.011 | -0.265 | 0.108 | -0.033 to 0.010 | 0.085 to 0.130 |
| whole duration: 1-2 weeks | 10627 | -0.157 | -0.146 | -0.011 | -0.265 | 0.108 | -0.033 to 0.010 | 0.085 to 0.130 |
| whole duration: 3 weeks | 1178 | -0.111 | -0.167 | 0.057 | -0.313 | 0.203 | -0.006 to 0.115 | 0.138 to 0.264 |
| whole duration: 4-5 weeks | 1176 | -0.078 | -0.165 | 0.087 | -0.296 | 0.219 | 0.027 to 0.143 | 0.158 to 0.276 |
| whole duration: 6+ weeks | 1807 | 0.013 | -0.208 | 0.221 | -0.372 | 0.386 | 0.171 to 0.270 | 0.333 to 0.438 |
| size tercile: small | 4930 | -0.146 | -0.152 | 0.005 | -0.275 | 0.128 | -0.020 to 0.031 | 0.101 to 0.156 |
| size tercile: middle | 4929 | -0.179 | -0.151 | -0.029 | -0.277 | 0.098 | -0.064 to 0.003 | 0.062 to 0.132 |
| size tercile: large | 4929 | -0.053 | -0.167 | 0.114 | -0.301 | 0.248 | 0.085 to 0.143 | 0.217 to 0.279 |

Secondary window (months 0 to +5), all shifts: mean tau -0.126 (95% interval -0.144 to -0.107).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau -0.028 (-0.048 to -0.008), 11616 tests; ebook alone (joint fit): mean tau -0.097 (-0.117 to -0.079), 14052 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.052 per doubling (95% interval 0.037 to 0.067), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.037 to 0.068, p = 0.0005.
- H2, 6+ weeks minus 1 to 2 weeks: 0.171 (95% interval 0.115 to 0.226); mean tau 0.013 (1807 tests) against -0.157 (10627 tests): **supported (95% interval above 0)**. Clustered by article: 0.112 to 0.228.
- Coefficient of log2 peak size given log2 duration (not tested): 0.065 (95% interval 0.038 to 0.094); log2 duration coefficient in the same model 0.020 (-0.001 to 0.041); correlation of log2 duration and log2 peak 0.69.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 7 weeks (shifts of 7 weeks or less: mean tau -0.143, 13557 tests; longer: 0.060, 1231 tests; difference 0.203, 95% interval at the re-estimated threshold 0.119 to 0.261); bootstrap interval of the threshold 2 to 8 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.091, 3.0: 0.166, 4.0: 0.04, 5.0: 0.106, 6.0: 0.224, 7.0: 0.302, 8.0: 0.07, 9.0: 0.0}); likelihood-ratio set [3, 5, 6, 7, 8]; the step explains 0.26% of the variance of tau. Article-clustered threshold interval 2 to 8.

### Secondary: author-article shifts, print and ebook

Tests: 6779 work-shift rows, 5465 with a usable fit and window; 647 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 12 with no checkouts in the window (tau = -infinity; out of the pooled means); 4806 tests in the pooled analysis, 2619 works, 946 articles. Mean placebo works per test 163.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 4818 tests; p < 0.05 in 760 (15.8%, 5% expected with no effect); p < 0.01 in 246 (5.1%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 15.2%. Placebo years: mean share of placebo-year z at or above the treated z 0.399 (0.5 expected with no effect) over 4729 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.0 and 7.6 (range 4.0 to 552.4).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 4806 | 2619 | -0.000 | -0.038 to 0.035 | -0.000 | -3.8% to 3.5% | 3.500 | 15.800 | -0.047 to 0.046 | no meaningful effect (upper bound below +10%) |
| class: sustained | 707 | 539 | 0.166 | 0.056 to 0.267 | 18.000 | 5.8% to 30.6% | 30.600 | 24.300 | 0.039 to 0.293 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 411 | 398 | 0.144 | 0.056 to 0.231 | 15.500 | 5.8% to 26.0% | 26.000 | 20.900 | 0.019 to 0.273 | positive: interval above 0; cannot rule out +10% |
| class: fading | 3688 | 2145 | -0.048 | -0.091 to -0.007 | -4.700 | -8.7% to -0.7% | -0.700 | 13.600 | -0.100 to 0.004 | no meaningful effect (upper bound below +10%) |
| whole duration: 1-2 weeks | 3688 | 2145 | -0.048 | -0.091 to -0.007 | -4.700 | -8.7% to -0.7% | -0.700 | 13.600 | -0.100 to 0.004 | no meaningful effect (upper bound below +10%) |
| whole duration: 3 weeks | 411 | 398 | 0.144 | 0.056 to 0.231 | 15.500 | 5.8% to 26.0% | 26.000 | 20.900 | 0.019 to 0.273 | positive: interval above 0; cannot rule out +10% |
| whole duration: 4-5 weeks | 349 | 283 | 0.109 | 0.013 to 0.200 | 11.600 | 1.3% to 22.1% | 22.100 | 19.500 | -0.020 to 0.233 | positive: interval above 0; cannot rule out +10% |
| whole duration: 6+ weeks | 358 | 324 | 0.221 | 0.010 to 0.392 | 24.700 | 1.0% to 48.0% | 48.000 | 29.100 | -0.010 to 0.436 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 1603 | 1216 | -0.063 | -0.126 to -0.004 | -6.100 | -11.8% to -0.4% | -0.400 | 11.600 | -0.138 to 0.009 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 1603 | 1218 | -0.053 | -0.124 to 0.013 | -5.200 | -11.7% to 1.3% | 1.300 | 14.500 | -0.136 to 0.033 | no meaningful effect (upper bound below +10%) |
| size tercile: large | 1600 | 1156 | 0.115 | 0.054 to 0.174 | 12.200 | 5.5% to 19.0% | 19.000 | 21.400 | 0.034 to 0.192 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 4806 | -0.000 | -0.124 | 0.124 | -0.242 | 0.242 | 0.087 to 0.158 | 0.206 to 0.277 |
| class: sustained | 707 | 0.166 | -0.148 | 0.314 | -0.297 | 0.463 | 0.208 to 0.414 | 0.359 to 0.565 |
| class: intermediate | 411 | 0.144 | -0.074 | 0.218 | -0.165 | 0.309 | 0.138 to 0.303 | 0.232 to 0.392 |
| class: fading | 3688 | -0.048 | -0.125 | 0.077 | -0.240 | 0.192 | 0.034 to 0.116 | 0.148 to 0.230 |
| whole duration: 1-2 weeks | 3688 | -0.048 | -0.125 | 0.077 | -0.240 | 0.192 | 0.034 to 0.116 | 0.148 to 0.230 |
| whole duration: 3 weeks | 411 | 0.144 | -0.074 | 0.218 | -0.165 | 0.309 | 0.138 to 0.303 | 0.232 to 0.392 |
| whole duration: 4-5 weeks | 349 | 0.109 | -0.142 | 0.252 | -0.283 | 0.393 | 0.170 to 0.334 | 0.312 to 0.480 |
| whole duration: 6+ weeks | 358 | 0.221 | -0.154 | 0.375 | -0.311 | 0.532 | 0.174 to 0.545 | 0.331 to 0.704 |
| size tercile: small | 1603 | -0.063 | -0.131 | 0.068 | -0.247 | 0.185 | 0.006 to 0.125 | 0.122 to 0.241 |
| size tercile: middle | 1603 | -0.053 | -0.125 | 0.072 | -0.238 | 0.185 | 0.004 to 0.135 | 0.118 to 0.249 |
| size tercile: large | 1600 | 0.115 | -0.116 | 0.231 | -0.240 | 0.356 | 0.172 to 0.288 | 0.296 to 0.413 |

Secondary window (months 0 to +5), all shifts: mean tau -0.015 (95% interval -0.054 to 0.021).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau 0.155 (0.112 to 0.198), 3583 tests; ebook alone (joint fit): mean tau 0.011 (-0.029 to 0.052), 4560 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.092 per doubling (95% interval 0.043 to 0.136), one-sided p = 0.0010: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.036 to 0.146, p = 0.0015.
- H2, 6+ weeks minus 1 to 2 weeks: 0.269 (95% interval 0.051 to 0.451); mean tau 0.221 (358 tests) against -0.048 (3688 tests): **supported (95% interval above 0)**. Clustered by article: 0.021 to 0.488.
- Coefficient of log2 peak size given log2 duration (not tested): 0.078 (95% interval 0.029 to 0.123); log2 duration coefficient in the same model 0.046 (-0.001 to 0.091); correlation of log2 duration and log2 peak 0.63.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 2 weeks (shifts of 2 weeks or less: mean tau -0.048, 3688 tests; longer: 0.158, 1118 tests; difference 0.206, 95% interval at the re-estimated threshold 0.126 to 0.382); bootstrap interval of the threshold 2 to 4 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.755, 3.0: 0.008, 4.0: 0.23, 5.0: 0.004, 6.0: 0.003}); likelihood-ratio set [2, 4]; the step explains 0.45% of the variance of tau. Article-clustered threshold interval 2 to 4.

<!-- end secondary -->

<!-- begin calendar -->
## Calendar check of the forecasts (diagnostic, not in the record)

tau of ordinary placebo-pool works (no event) by calendar year of month 0, over all months of that year (print and ebook joint model; works feasible and not sparse); and the tested shifts of the main set by year.

| year | months | works/month | mean_tau | median_tau | share_tau_above_0 | tested_shifts | treated_mean_tau | placebo_median_same_months |
|---|---|---|---|---|---|---|---|---|
| 2017 | 12.000 | 3142.583 | -0.242 | -0.090 | 0.421 | 222 | 0.181 | -0.161 |
| 2018 | 12.000 | 3314.333 | -0.249 | -0.086 | 0.428 | 189 | 0.184 | -0.153 |
| 2019 | 12.000 | 3482.667 | -0.241 | -0.080 | 0.430 | 162 | 0.086 | -0.137 |
| 2020 | 12.000 | 3420.167 | -0.252 | -0.155 | 0.379 | 238 | -0.031 | -0.220 |
| 2021 | 12.000 | 3639.750 | -0.295 | -0.100 | 0.434 | 230 | 0.113 | -0.202 |
| 2022 | 12.000 | 3690.167 | -0.229 | -0.097 | 0.432 | 211 | 0.135 | -0.172 |
| 2023 | 12.000 | 3917.083 | -0.165 | -0.034 | 0.470 | 266 | -0.025 | -0.128 |
| 2024 | 12.000 | 3696.000 | -0.178 | -0.060 | 0.448 | 242 | 0.210 | -0.113 |
| 2025 | 12.000 | 4020.667 | -0.148 | -0.064 | 0.445 | 223 | 0.158 | -0.066 |
| 2026 | 7.000 | 4078.286 | -0.200 | -0.076 | 0.435 | 124 | 0.013 | -0.210 |
<!-- end calendar -->
