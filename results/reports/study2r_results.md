# Study 2R results

Run 2026-10-14 (about 30 minutes on the 8 GB Mac, 2 workers). Settings: prereg/study2r_settings_2026-10-14.json with addenda a, b, c; implementation choices in prereg/DEVIATIONS.md (Study 2R). Code: code/study2r/10 to 15. Simulation tests (an injected lift is recovered, 6.0% of null tests reach p < 0.05, the bootstrap, H1, H2 and Hansen tools recover known truths): data/reports/study2r_sim_tests.md, all pass.

<!-- begin summary -->
## Reading guide and caveats

1. **Positive controls failed** (pooled interval above zero, but only 2 of 7 with p < 0.05; the rule needs 4). Under addendum c none of the seven had a ratio 1.5 shift within 8 weeks of release, so month 0 is the release month for all seven. Queen's Gambit has only 0.7 expected checkouts in its window (too sparse to rank reliably). The measurement recovered the large library effects (American Prometheus, Killers of the Flower Moon, Where the Crawdads Sing) but not the others. The main analysis was run as the record's pass rule has no stop, and its results must be read with this failure in mind.
2. **Raw pooled tau is centred below zero for ordinary works.** Matched placebo works have mean tau of about -0.31 and median -0.16 in the same months in the main set (see the diagnostic tables and the calendar check): conditioning on a window that is expected to have at least 5 checkouts, and a log-linear forecast, give a downward bias that is the same in every year. The record pools raw tau and the equivalence verdicts use it, so a raw interval that sits below +10% is partly this bias. The placebo ranks (one-sided p) and the placebo-adjusted diagnostic are not affected. Read every 'no meaningful effect' verdict together with the adjusted column.
3. Single-book Benjamini-Hochberg finds nothing because 200 placebo works give a smallest possible p of 0.005, and q < 0.10 over about 2,200 tests would need more than 100 tests at that p.
4. Positive tests at p < 0.05: 19.6% (main), against 5% expected under no effect; the effects concentrate in long and large shifts (duration and size are correlated at 0.72).
<!-- end summary -->

<!-- begin controls -->
## Positive controls (run first, before any main analysis)

Built 2026-10-14 21:04 by code/study2r/12_controls.py. Event per addendum c: month 0 = month of the first ratio 1.5 shift within 8 weeks of the release date, else the release month. Outcome: joint print and ebook count event study of the largest matched Seattle work, tau = log(sum Y / sum mu) over months 0 to +2, z, one-sided rank p among 200 matched placebo works.

**Result: FAIL.** Pooled mean tau = 1.152 (95% bootstrap interval 0.217 to 2.383; lift 216.6%, interval 24.2% to 983.5%); 2 of 7 tests with one-sided p < 0.05 (rule: pooled interval above zero and at least 4 of 7).

| control | month0 | source | skip | pf | summu_p | sumy_p | tau_p | lift | z_p | n_placebos | plc_tau_median | p_p | tau_s | p_s | tau_p_print | tau_p_ebook | py_n | py_share_ge | tau_p_audio | p_p_audio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| The Queen's Gambit | 2020-10 | release month (no shift) |  | 0 | 0.682 | 42.000 | 4.120 | 6054.000 | 2.433 | 166 | 0.666 | 0.072 | 4.241 | 0.024 | 4.120 |  | 4 | 0.250 |  |  |
| The Duke and I | 2020-12 | release month (no shift) |  | 1 | 60.544 | 46.000 | -0.275 | -24.000 | -1.818 | 197 | -0.259 | 0.429 | 0.038 | 0.232 | 0.711 | -2.968 | 5 | 0.800 |  |  |
| Dune | 2021-10 | release month (no shift) |  | 1 | 737.955 | 730.000 | -0.011 | -1.100 | -0.186 | 200 | -1.398 | 0.114 | 0.101 | 0.075 | -0.556 | 0.094 | 1 | 0.000 | 0.164 | 0.045 |
| Where the Crawdads Sing | 2022-07 | release month (no shift) |  | 1 | 183.590 | 764.000 | 1.426 | 316.100 | 4.043 | 200 | -0.881 | 0.055 | 1.453 | 0.040 | 1.515 | 1.398 | 2 | 0.000 | 0.051 | 0.090 |
| American Prometheus | 2023-07 | release month (no shift) |  | 1 | 36.342 | 167.000 | 1.525 | 359.500 | 10.290 | 200 | -0.085 | 0.005 | 1.435 | 0.005 | 1.885 | 1.216 | 6 | 0.000 | 2.793 | 0.005 |
| Killers of the Flower Moon | 2023-10 | release month (no shift) |  | 1 | 189.446 | 924.000 | 1.585 | 387.700 | 10.389 | 200 | -0.848 | 0.005 | 1.563 | 0.005 | 2.962 | 1.505 | 7 | 0.000 | 1.689 | 0.006 |
| Shogun | 2024-02 | release month (no shift) |  | 1 | 24.380 | 18.000 | -0.303 | -26.200 | -2.319 | 200 | -0.133 | 0.746 | -0.293 | 0.761 |  | -0.303 | 4 | 0.750 | -0.061 | 0.483 |

Columns: summu_p = expected checkouts over months 0 to +2, sumy_p = observed; tau_p, p_p = months 0 to +2 (record primary); tau_s, p_s = months 0 to +5; tau_p_print and tau_p_ebook = the same from the joint fit, per format (descriptive); plc_tau_median = median tau of the 200 placebo works in the same months (diagnostic); py_n and py_share_ge = placebo years and their share with z at or above the treated z (descriptive); tau_p_audio, p_p_audio = separate audiobook model (secondary, descriptive).
<!-- end controls -->

<!-- begin main -->
## Main analysis and confirmatory duration tests

Built 2026-10-14 21:05 by code/study2r/13_effects.py and 14_inference.py.

### Main: calibrated rule (floor 300, ratio 4.0), print and ebook

Tests: 2619 work-shift rows, 2372 with a usable fit and window; 173 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 21 with no checkouts in the window (tau = -infinity; out of the pooled means); 2178 tests in the pooled analysis, 1347 works, 1289 articles. Mean placebo works per test 177.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 2199 tests; p < 0.05 in 430 (19.6%, 5% expected with no effect); p < 0.01 in 150 (6.8%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 21.1%. Placebo years: mean share of placebo-year z at or above the treated z 0.376 (0.5 expected with no effect) over 2124 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.3 and 9.1 (range 4.0 to 457.9).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 2178 | 1347 | 0.084 | 0.030 to 0.137 | 8.800 | 3.1% to 14.7% | 14.700 | 19.700 | 0.026 to 0.136 | positive: interval above 0; cannot rule out +10% |
| class: sustained | 545 | 410 | 0.251 | 0.148 to 0.340 | 28.500 | 15.9% to 40.5% | 40.500 | 29.900 | 0.144 to 0.339 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 218 | 197 | -0.004 | -0.292 to 0.221 | -0.400 | -25.3% to 24.7% | 24.700 | 21.600 | -0.280 to 0.220 | inconclusive: cannot rule out +10% |
| class: fading | 1415 | 1032 | 0.033 | -0.032 to 0.096 | 3.400 | -3.2% to 10.1% | 10.100 | 15.500 | -0.039 to 0.096 | inconclusive: cannot rule out +10% |
| whole duration: 1-2 weeks | 1415 | 1032 | 0.033 | -0.032 to 0.096 | 3.400 | -3.2% to 10.1% | 10.100 | 15.500 | -0.039 to 0.096 | inconclusive: cannot rule out +10% |
| whole duration: 3 weeks | 218 | 197 | -0.004 | -0.292 to 0.221 | -0.400 | -25.3% to 24.7% | 24.700 | 21.600 | -0.280 to 0.220 | inconclusive: cannot rule out +10% |
| whole duration: 4-5 weeks | 264 | 227 | 0.160 | -0.017 to 0.300 | 17.400 | -1.7% to 35.0% | 35.000 | 27.700 | -0.014 to 0.302 | inconclusive: cannot rule out +10% |
| whole duration: 6+ weeks | 281 | 235 | 0.335 | 0.228 to 0.445 | 39.900 | 25.6% to 56.0% | 56.000 | 32.000 | 0.225 to 0.455 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 726 | 620 | -0.023 | -0.131 to 0.068 | -2.200 | -12.3% to 7.0% | 7.000 | 12.300 | -0.131 to 0.065 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 726 | 596 | 0.058 | -0.042 to 0.153 | 6.000 | -4.1% to 16.5% | 16.500 | 19.400 | -0.049 to 0.160 | inconclusive: cannot rule out +10% |
| size tercile: large | 726 | 561 | 0.217 | 0.134 to 0.298 | 24.200 | 14.3% to 34.7% | 34.700 | 27.500 | 0.129 to 0.295 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 2178 | 0.084 | -0.164 | 0.248 | -0.309 | 0.393 | 0.198 to 0.298 | 0.342 to 0.445 |
| class: sustained | 545 | 0.251 | -0.219 | 0.469 | -0.408 | 0.659 | 0.370 to 0.554 | 0.559 to 0.749 |
| class: intermediate | 218 | -0.004 | -0.171 | 0.167 | -0.309 | 0.306 | -0.112 to 0.374 | 0.047 to 0.499 |
| class: fading | 1415 | 0.033 | -0.142 | 0.175 | -0.270 | 0.303 | 0.116 to 0.233 | 0.242 to 0.362 |
| whole duration: 1-2 weeks | 1415 | 0.033 | -0.142 | 0.175 | -0.270 | 0.303 | 0.116 to 0.233 | 0.242 to 0.362 |
| whole duration: 3 weeks | 218 | -0.004 | -0.171 | 0.167 | -0.309 | 0.306 | -0.112 to 0.374 | 0.047 to 0.499 |
| whole duration: 4-5 weeks | 264 | 0.160 | -0.203 | 0.363 | -0.375 | 0.535 | 0.195 to 0.494 | 0.370 to 0.665 |
| whole duration: 6+ weeks | 281 | 0.335 | -0.234 | 0.569 | -0.440 | 0.775 | 0.472 to 0.668 | 0.675 to 0.883 |
| size tercile: small | 726 | -0.023 | -0.128 | 0.105 | -0.240 | 0.217 | 0.003 to 0.189 | 0.123 to 0.299 |
| size tercile: middle | 726 | 0.058 | -0.167 | 0.225 | -0.314 | 0.372 | 0.127 to 0.313 | 0.275 to 0.460 |
| size tercile: large | 726 | 0.217 | -0.198 | 0.414 | -0.372 | 0.588 | 0.335 to 0.489 | 0.510 to 0.661 |

Secondary window (months 0 to +5), all shifts: mean tau 0.084 (95% interval 0.029 to 0.138).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau 0.240 (0.186 to 0.294), 1703 tests; ebook alone (joint fit): mean tau 0.104 (0.046 to 0.159), 2030 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.086 per doubling (95% interval 0.045 to 0.128), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.042 to 0.131, p = 0.0005.
- H2, 6+ weeks minus 1 to 2 weeks: 0.302 (95% interval 0.182 to 0.424); mean tau 0.335 (281 tests) against 0.033 (1415 tests): **supported (95% interval above 0)**. Clustered by article: 0.173 to 0.434.
- Coefficient of log2 peak size given log2 duration (not tested): 0.146 (95% interval 0.080 to 0.218); log2 duration coefficient in the same model -0.013 (-0.086 to 0.051); correlation of log2 duration and log2 peak 0.72.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 4 weeks (shifts of 4 weeks or less: mean tau 0.031, 1766 tests; longer: 0.313, 412 tests; difference 0.282, 95% interval at the re-estimated threshold 0.184 to 0.410); bootstrap interval of the threshold 2 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.043, 3.0: 0.208, 4.0: 0.606, 5.0: 0.088, 6.0: 0.05, 7.0: 0.004}); likelihood-ratio set [3, 4, 5, 6]; the step explains 0.73% of the variance of tau. Article-clustered threshold interval 2 to 6.

<!-- end main -->

<!-- begin secondary -->
## Secondary analyses and sensitivities

### Secondary: same shifts, audiobook

Tests: 2251 work-shift rows, 1732 with a usable fit and window; 144 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 21 with no checkouts in the window (tau = -infinity; out of the pooled means); 1567 tests in the pooled analysis, 999 works, 979 articles. Mean placebo works per test 199.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 1588 tests; p < 0.05 in 286 (18.0%, 5% expected with no effect); p < 0.01 in 102 (6.4%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 20.1%. Placebo years: mean share of placebo-year z at or above the treated z 0.394 (0.5 expected with no effect) over 1546 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.3 and 9.1 (range 4.0 to 428.5).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 1567 | 999 | 0.036 | -0.044 to 0.109 | 3.600 | -4.3% to 11.6% | 11.600 | 18.300 | -0.048 to 0.107 | inconclusive: cannot rule out +10% |
| class: sustained | 413 | 320 | 0.205 | 0.076 to 0.311 | 22.800 | 7.9% to 36.5% | 36.500 | 24.700 | 0.077 to 0.309 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 176 | 161 | -0.247 | -0.620 to 0.063 | -21.900 | -46.2% to 6.5% | 6.500 | 15.300 | -0.612 to 0.071 | inconclusive (upper bound below +10% but only 161 works, fewer than 299) |
| class: fading | 978 | 740 | 0.015 | -0.083 to 0.104 | 1.500 | -8.0% to 10.9% | 10.900 | 16.100 | -0.082 to 0.103 | inconclusive: cannot rule out +10% |
| whole duration: 1-2 weeks | 978 | 740 | 0.015 | -0.083 to 0.104 | 1.500 | -8.0% to 10.9% | 10.900 | 16.100 | -0.082 to 0.103 | inconclusive: cannot rule out +10% |
| whole duration: 3 weeks | 176 | 161 | -0.247 | -0.620 to 0.063 | -21.900 | -46.2% to 6.5% | 6.500 | 15.300 | -0.612 to 0.071 | inconclusive (upper bound below +10% but only 161 works, fewer than 299) |
| whole duration: 4-5 weeks | 205 | 179 | 0.112 | -0.099 to 0.281 | 11.800 | -9.4% to 32.5% | 32.500 | 21.500 | -0.107 to 0.271 | inconclusive: cannot rule out +10% |
| whole duration: 6+ weeks | 208 | 181 | 0.298 | 0.166 to 0.428 | 34.600 | 18.1% to 53.4% | 53.400 | 27.900 | 0.164 to 0.428 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 523 | 449 | -0.115 | -0.282 to 0.029 | -10.900 | -24.5% to 2.9% | 2.900 | 12.800 | -0.272 to 0.026 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 522 | 444 | 0.070 | -0.054 to 0.184 | 7.300 | -5.3% to 20.1% | 20.100 | 19.200 | -0.066 to 0.177 | inconclusive: cannot rule out +10% |
| size tercile: large | 522 | 409 | 0.152 | 0.027 to 0.262 | 16.500 | 2.7% to 30.0% | 30.000 | 22.800 | 0.026 to 0.263 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 1567 | 0.036 | -0.158 | 0.194 | -0.370 | 0.405 | 0.120 to 0.261 | 0.329 to 0.477 |
| class: sustained | 413 | 0.205 | -0.194 | 0.400 | -0.427 | 0.632 | 0.282 to 0.504 | 0.519 to 0.744 |
| class: intermediate | 176 | -0.247 | -0.187 | -0.060 | -0.437 | 0.190 | -0.415 to 0.238 | -0.159 to 0.478 |
| class: fading | 978 | 0.015 | -0.137 | 0.152 | -0.333 | 0.348 | 0.060 to 0.236 | 0.254 to 0.436 |
| whole duration: 1-2 weeks | 978 | 0.015 | -0.137 | 0.152 | -0.333 | 0.348 | 0.060 to 0.236 | 0.254 to 0.436 |
| whole duration: 3 weeks | 176 | -0.247 | -0.187 | -0.060 | -0.437 | 0.190 | -0.415 to 0.238 | -0.159 to 0.478 |
| whole duration: 4-5 weeks | 205 | 0.112 | -0.193 | 0.305 | -0.415 | 0.527 | 0.109 to 0.465 | 0.337 to 0.691 |
| whole duration: 6+ weeks | 208 | 0.298 | -0.196 | 0.493 | -0.439 | 0.736 | 0.377 to 0.611 | 0.604 to 0.878 |
| size tercile: small | 523 | -0.115 | -0.126 | 0.011 | -0.301 | 0.186 | -0.145 to 0.140 | 0.036 to 0.311 |
| size tercile: middle | 522 | 0.070 | -0.158 | 0.228 | -0.377 | 0.447 | 0.108 to 0.330 | 0.323 to 0.552 |
| size tercile: large | 522 | 0.152 | -0.191 | 0.343 | -0.431 | 0.583 | 0.225 to 0.448 | 0.460 to 0.694 |

Secondary window (months 0 to +5), all shifts: mean tau 0.024 (95% interval -0.064 to 0.103).
Per format, from the joint fit (descriptive): audiobook alone (joint fit): mean tau 0.036 (-0.044 to 0.109), 1567 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.056 per doubling (95% interval -0.001 to 0.114), one-sided p = 0.0295: **supported (p < 0.05, slope > 0)**. Clustered by article: interval -0.000 to 0.111, p = 0.0260.
- H2, 6+ weeks minus 1 to 2 weeks: 0.283 (95% interval 0.128 to 0.444); mean tau 0.298 (208 tests) against 0.015 (978 tests): **supported (95% interval above 0)**. Clustered by article: 0.131 to 0.445.
- Coefficient of log2 peak size given log2 duration (not tested): 0.194 (95% interval 0.103 to 0.288); log2 duration coefficient in the same model -0.078 (-0.169 to 0.004); correlation of log2 duration and log2 peak 0.72.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 4 weeks (shifts of 4 weeks or less: mean tau -0.025, 1256 tests; longer: 0.282, 311 tests; difference 0.307, 95% interval at the re-estimated threshold 0.182 to 0.467); bootstrap interval of the threshold 3 to 6 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.003, 3.0: 0.188, 4.0: 0.666, 5.0: 0.085, 6.0: 0.054, 7.0: 0.001, 8.0: 0.003}); likelihood-ratio set [3, 4, 5, 6, 7]; the step explains 0.63% of the variance of tau. Article-clustered threshold interval 3 to 6.

### Sensitivity (addendum c): ratio 1.5, print and ebook

Tests: 18145 work-shift rows, 16508 with a usable fit and window; 1268 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 59 with no checkouts in the window (tau = -infinity; out of the pooled means); 15181 tests in the pooled analysis, 3696 works, 3538 articles. Mean placebo works per test 154.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 15240 tests; p < 0.05 in 1237 (8.1%, 5% expected with no effect); p < 0.01 in 251 (1.6%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 8.8%. Placebo years: mean share of placebo-year z at or above the treated z 0.475 (0.5 expected with no effect) over 13927 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 1.7 and 2.2 (range 1.5 to 428.5).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 15181 | 3696 | -0.133 | -0.152 to -0.115 | -12.500 | -14.1% to -10.9% | -10.900 | 8.100 | -0.151 to -0.116 | no meaningful effect (upper bound below +10%) |
| class: sustained | 3074 | 1784 | -0.032 | -0.073 to 0.007 | -3.200 | -7.0% to 0.7% | 0.700 | 13.900 | -0.072 to 0.007 | no meaningful effect (upper bound below +10%) |
| class: intermediate | 1208 | 963 | -0.136 | -0.205 to -0.069 | -12.700 | -18.6% to -6.7% | -6.700 | 9.600 | -0.212 to -0.070 | no meaningful effect (upper bound below +10%) |
| class: fading | 10899 | 3382 | -0.161 | -0.183 to -0.141 | -14.900 | -16.7% to -13.1% | -13.100 | 6.400 | -0.182 to -0.141 | no meaningful effect (upper bound below +10%) |
| whole duration: 1-2 weeks | 10899 | 3382 | -0.161 | -0.183 to -0.141 | -14.900 | -16.7% to -13.1% | -13.100 | 6.400 | -0.182 to -0.141 | no meaningful effect (upper bound below +10%) |
| whole duration: 3 weeks | 1208 | 963 | -0.136 | -0.205 to -0.069 | -12.700 | -18.6% to -6.7% | -6.700 | 9.600 | -0.212 to -0.070 | no meaningful effect (upper bound below +10%) |
| whole duration: 4-5 weeks | 1222 | 970 | -0.081 | -0.146 to -0.024 | -7.800 | -13.6% to -2.4% | -2.400 | 10.800 | -0.149 to -0.023 | no meaningful effect (upper bound below +10%) |
| whole duration: 6+ weeks | 1852 | 1218 | 0.000 | -0.053 to 0.049 | 0.000 | -5.2% to 5.0% | 5.000 | 16.000 | -0.054 to 0.051 | no meaningful effect (upper bound below +10%) |
| size tercile: small | 5061 | 2629 | -0.145 | -0.171 to -0.121 | -13.500 | -15.7% to -11.4% | -11.400 | 6.100 | -0.171 to -0.121 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 5060 | 2551 | -0.183 | -0.219 to -0.150 | -16.800 | -19.6% to -14.0% | -14.000 | 7.100 | -0.219 to -0.148 | no meaningful effect (upper bound below +10%) |
| size tercile: large | 5060 | 2460 | -0.071 | -0.103 to -0.040 | -6.800 | -9.8% to -4.0% | -4.000 | 11.300 | -0.104 to -0.040 | no meaningful effect (upper bound below +10%) |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 15181 | -0.133 | -0.163 | 0.030 | -0.293 | 0.160 | 0.010 to 0.048 | 0.139 to 0.181 |
| class: sustained | 3074 | -0.032 | -0.197 | 0.165 | -0.351 | 0.319 | 0.126 to 0.203 | 0.280 to 0.359 |
| class: intermediate | 1208 | -0.136 | -0.175 | 0.039 | -0.321 | 0.185 | -0.027 to 0.102 | 0.120 to 0.250 |
| class: fading | 10899 | -0.161 | -0.152 | -0.009 | -0.274 | 0.113 | -0.030 to 0.011 | 0.091 to 0.135 |
| whole duration: 1-2 weeks | 10899 | -0.161 | -0.152 | -0.009 | -0.274 | 0.113 | -0.030 to 0.011 | 0.091 to 0.135 |
| whole duration: 3 weeks | 1208 | -0.136 | -0.175 | 0.039 | -0.321 | 0.185 | -0.027 to 0.102 | 0.120 to 0.250 |
| whole duration: 4-5 weeks | 1222 | -0.081 | -0.169 | 0.088 | -0.303 | 0.222 | 0.028 to 0.139 | 0.166 to 0.274 |
| whole duration: 6+ weeks | 1852 | 0.000 | -0.216 | 0.216 | -0.383 | 0.383 | 0.164 to 0.263 | 0.329 to 0.434 |
| size tercile: small | 5061 | -0.145 | -0.157 | 0.012 | -0.283 | 0.138 | -0.013 to 0.036 | 0.111 to 0.165 |
| size tercile: middle | 5060 | -0.183 | -0.158 | -0.025 | -0.287 | 0.103 | -0.060 to 0.006 | 0.068 to 0.136 |
| size tercile: large | 5060 | -0.071 | -0.174 | 0.103 | -0.310 | 0.239 | 0.071 to 0.133 | 0.206 to 0.271 |

Secondary window (months 0 to +5), all shifts: mean tau -0.132 (95% interval -0.152 to -0.115).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau -0.033 (-0.053 to -0.013), 11686 tests; ebook alone (joint fit): mean tau -0.105 (-0.124 to -0.087), 14148 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.049 per doubling (95% interval 0.034 to 0.064), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.033 to 0.064, p = 0.0005.
- H2, 6+ weeks minus 1 to 2 weeks: 0.161 (95% interval 0.104 to 0.214); mean tau 0.000 (1852 tests) against -0.161 (10899 tests): **supported (95% interval above 0)**. Clustered by article: 0.102 to 0.217.
- Coefficient of log2 peak size given log2 duration (not tested): 0.060 (95% interval 0.032 to 0.088); log2 duration coefficient in the same model 0.019 (-0.002 to 0.040); correlation of log2 duration and log2 peak 0.70.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 7 weeks (shifts of 7 weeks or less: mean tau -0.150, 13913 tests; longer: 0.048, 1268 tests; difference 0.198, 95% interval at the re-estimated threshold 0.113 to 0.253); bootstrap interval of the threshold 2 to 8 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.036, 3.0: 0.215, 4.0: 0.022, 5.0: 0.073, 6.0: 0.287, 7.0: 0.309, 8.0: 0.053, 9.0: 0.004}); likelihood-ratio set [3, 5, 6, 7, 8]; the step explains 0.24% of the variance of tau. Article-clustered threshold interval 2 to 8.

### Secondary: author-article shifts, print and ebook

Tests: 7069 work-shift rows, 5579 with a usable fit and window; 673 too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); 35 with no checkouts in the window (tau = -infinity; out of the pooled means); 4871 tests in the pooled analysis, 2669 works, 944 articles. Mean placebo works per test 164.

Single-book tests (one-sided rank p among placebo works, months 0 to +2): 4906 tests; p < 0.05 in 757 (15.4%, 5% expected with no effect); p < 0.01 in 245 (5.0%); Benjamini-Hochberg q < 0.10: 0 (0.0%) in 0 works. Months 0 to +5: p < 0.05 in 15.6%. Placebo years: mean share of placebo-year z at or above the treated z 0.400 (0.5 expected with no effect) over 4805 tests.

Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).

Size terciles are of whole peak ratio: cut points 5.0 and 7.6 (range 4.0 to 552.4).

| group | tests | works | mean_tau | interval | lift | lift_interval | largest_lift_ruled_out | p05 | interval_by_article | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| all shifts | 4871 | 2669 | -0.003 | -0.041 to 0.033 | -0.300 | -4.0% to 3.3% | 3.300 | 15.500 | -0.051 to 0.044 | no meaningful effect (upper bound below +10%) |
| class: sustained | 718 | 549 | 0.166 | 0.059 to 0.268 | 18.100 | 6.1% to 30.7% | 30.700 | 24.200 | 0.046 to 0.288 | positive: interval above 0; cannot rule out +10% |
| class: intermediate | 415 | 402 | 0.149 | 0.063 to 0.238 | 16.100 | 6.5% to 26.8% | 26.800 | 21.000 | 0.023 to 0.280 | positive: interval above 0; cannot rule out +10% |
| class: fading | 3738 | 2182 | -0.052 | -0.094 to -0.011 | -5.100 | -9.0% to -1.0% | -1.000 | 13.300 | -0.107 to -0.001 | no meaningful effect (upper bound below +10%) |
| whole duration: 1-2 weeks | 3738 | 2182 | -0.052 | -0.094 to -0.011 | -5.100 | -9.0% to -1.0% | -1.000 | 13.300 | -0.107 to -0.001 | no meaningful effect (upper bound below +10%) |
| whole duration: 3 weeks | 415 | 402 | 0.149 | 0.063 to 0.238 | 16.100 | 6.5% to 26.8% | 26.800 | 21.000 | 0.023 to 0.280 | positive: interval above 0; cannot rule out +10% |
| whole duration: 4-5 weeks | 356 | 290 | 0.107 | 0.012 to 0.203 | 11.300 | 1.2% to 22.5% | 22.500 | 19.100 | -0.021 to 0.228 | positive: interval above 0; cannot rule out +10% |
| whole duration: 6+ weeks | 362 | 328 | 0.224 | 0.019 to 0.402 | 25.100 | 2.0% to 49.5% | 49.500 | 29.300 | -0.003 to 0.426 | positive: interval above 0; cannot rule out +10% |
| size tercile: small | 1631 | 1238 | -0.073 | -0.138 to -0.011 | -7.000 | -12.9% to -1.1% | -1.100 | 11.200 | -0.151 to 0.001 | no meaningful effect (upper bound below +10%) |
| size tercile: middle | 1616 | 1230 | -0.056 | -0.128 to 0.006 | -5.500 | -12.1% to 0.6% | 0.600 | 14.100 | -0.140 to 0.026 | no meaningful effect (upper bound below +10%) |
| size tercile: large | 1624 | 1176 | 0.120 | 0.061 to 0.175 | 12.800 | 6.2% to 19.1% | 19.100 | 21.300 | 0.045 to 0.199 | positive: interval above 0; cannot rule out +10% |

p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.

Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).

| group | tests | mean_tau | placebo_median_tau | adjusted | placebo_mean_tau | adjusted_vs_placebo_mean | interval | interval_vs_mean |
|---|---|---|---|---|---|---|---|---|
| all shifts | 4871 | -0.003 | -0.134 | 0.131 | -0.254 | 0.251 | 0.095 to 0.166 | 0.216 to 0.287 |
| class: sustained | 718 | 0.166 | -0.162 | 0.328 | -0.317 | 0.483 | 0.222 to 0.424 | 0.374 to 0.581 |
| class: intermediate | 415 | 0.149 | -0.088 | 0.238 | -0.184 | 0.333 | 0.161 to 0.318 | 0.261 to 0.413 |
| class: fading | 3738 | -0.052 | -0.134 | 0.082 | -0.250 | 0.198 | 0.039 to 0.121 | 0.155 to 0.237 |
| whole duration: 1-2 weeks | 3738 | -0.052 | -0.134 | 0.082 | -0.250 | 0.198 | 0.039 to 0.121 | 0.155 to 0.237 |
| whole duration: 3 weeks | 415 | 0.149 | -0.088 | 0.238 | -0.184 | 0.333 | 0.161 to 0.318 | 0.261 to 0.413 |
| whole duration: 4-5 weeks | 356 | 0.107 | -0.155 | 0.262 | -0.303 | 0.410 | 0.174 to 0.346 | 0.326 to 0.497 |
| whole duration: 6+ weeks | 362 | 0.224 | -0.169 | 0.393 | -0.330 | 0.554 | 0.198 to 0.564 | 0.359 to 0.724 |
| size tercile: small | 1631 | -0.073 | -0.138 | 0.065 | -0.257 | 0.184 | 0.002 to 0.122 | 0.122 to 0.241 |
| size tercile: middle | 1616 | -0.056 | -0.139 | 0.083 | -0.255 | 0.198 | 0.014 to 0.142 | 0.130 to 0.259 |
| size tercile: large | 1624 | 0.120 | -0.126 | 0.246 | -0.252 | 0.372 | 0.187 to 0.300 | 0.312 to 0.426 |

Secondary window (months 0 to +5), all shifts: mean tau -0.019 (95% interval -0.057 to 0.017).
Per format, from the joint fit (descriptive): print alone (joint fit): mean tau 0.152 (0.111 to 0.194), 3578 tests; ebook alone (joint fit): mean tau 0.007 (-0.035 to 0.044), 4532 tests.

**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):

- H1, slope of tau on log2 whole duration in weeks: 0.096 per doubling (95% interval 0.047 to 0.137), one-sided p = 0.0005: **supported (p < 0.05, slope > 0)**. Clustered by article: interval 0.041 to 0.152, p = 0.0005.
- H2, 6+ weeks minus 1 to 2 weeks: 0.276 (95% interval 0.057 to 0.446); mean tau 0.224 (362 tests) against -0.052 (3738 tests): **supported (95% interval above 0)**. Clustered by article: 0.018 to 0.504.
- Coefficient of log2 peak size given log2 duration (not tested): 0.084 (95% interval 0.035 to 0.128); log2 duration coefficient in the same model 0.046 (-0.002 to 0.092); correlation of log2 duration and log2 peak 0.64.
- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold 2 weeks (shifts of 2 weeks or less: mean tau -0.052, 3738 tests; longer: 0.160, 1133 tests; difference 0.212, 95% interval at the re-estimated threshold 0.124 to 0.399); bootstrap interval of the threshold 2 to 4 weeks (percentiles over resamples; share of resamples by threshold {2.0: 0.746, 3.0: 0.004, 4.0: 0.244, 5.0: 0.004, 6.0: 0.002}); likelihood-ratio set [2, 4]; the step explains 0.47% of the variance of tau. Article-clustered threshold interval 2 to 4.

<!-- end secondary -->

<!-- begin calendar -->
## Calendar check of the forecasts (diagnostic, not in the record)

tau of ordinary placebo-pool works (no event) by calendar year of month 0, over all months of that year (print and ebook joint model; works feasible and not sparse); and the tested shifts of the main set by year.

| year | months | works/month | mean_tau | median_tau | share_tau_above_0 | tested_shifts | treated_mean_tau | placebo_median_same_months |
|---|---|---|---|---|---|---|---|---|
| 2017 | 12.000 | 3242.333 | -0.252 | -0.093 | 0.417 | 237 | 0.160 | -0.158 |
| 2018 | 12.000 | 3424.167 | -0.253 | -0.087 | 0.428 | 190 | 0.192 | -0.155 |
| 2019 | 12.000 | 3608.083 | -0.252 | -0.080 | 0.429 | 169 | 0.082 | -0.136 |
| 2020 | 12.000 | 3486.750 | -0.255 | -0.156 | 0.377 | 247 | -0.048 | -0.218 |
| 2021 | 12.000 | 3751.333 | -0.307 | -0.111 | 0.429 | 232 | 0.103 | -0.235 |
| 2022 | 12.000 | 3805.167 | -0.239 | -0.102 | 0.430 | 214 | 0.137 | -0.189 |
| 2023 | 12.000 | 4033.750 | -0.175 | -0.041 | 0.465 | 278 | -0.025 | -0.136 |
| 2024 | 12.000 | 3768.667 | -0.189 | -0.066 | 0.444 | 252 | 0.203 | -0.121 |
| 2025 | 12.000 | 4127.583 | -0.158 | -0.070 | 0.441 | 229 | 0.126 | -0.093 |
| 2026 | 7.000 | 4196.286 | -0.219 | -0.084 | 0.428 | 130 | -0.147 | -0.222 |
<!-- end calendar -->
