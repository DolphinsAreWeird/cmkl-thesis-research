# Brisbane replication: H1 and H2, joint regression

- written: 2026-10-15 02:55:44; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- shifts: Wikipedia, narrow and middle, labelled, quality OK, non-seasonal, month 0 2016-01 to 2025-06: 593 shifts with a theme in the Brisbane panel, in 186 (level, month 0) units
- shift rows tested (feasible fit, usable window of at least 2 months): 472 of 593; skip reasons: {'not feasible': 79, 'window too short': 42}
- main set (not too sparse, i.e. at least 5 expected weighted loans in months 0 to +2, and loans above 0): 461 tests in 200 themes; too sparse: 11; zero loans in window: 2
- bootstrap: 2000 resamples of themes, seed 20261015, 95% percentile intervals

## Hypotheses (pooled mean tau over months 0 to +2; tau is the log of observed over expected weighted loans)

- **H1 NOT SUPPORTED**: pooled tau of sustained rises = 0.028 (95% interval -0.066 to 0.115; about +2.8% loans against the fitted trend), 53 tests in 41 themes.
- **H2 NOT SUPPORTED**: sustained minus fading = 0.024 (95% interval -0.076 to 0.116; share of resamples at or below 0: 0.286); fading pooled tau = 0.003 (-0.018 to 0.027), 376 tests in 184 themes; 190 themes in the difference.
- Sensitivity, including too-sparse tests: sustained minus fading = 0.060 (-0.034 to 0.148), 56 sustained and 382 fading tests.

## Pooled tau by duration class and level
| set | duration_class | level | tests | themes | tau_mean | ci_low | ci_high | lift_pct | share_p_below_05 | median_expected_loans |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main (not too sparse) | sustained | both | 53 | 41 | 0.028 | -0.066 | 0.115 | 2.801 | 0.057 | 85.442 |
| main (not too sparse) | sustained | narrow | 45 | 35 | 0.026 | -0.088 | 0.122 | 2.618 | 0.067 | 69.221 |
| main (not too sparse) | sustained | middle | 8 | 6 | 0.038 | -0.010 | 0.074 | 3.837 | 0.000 | 340.237 |
| main (not too sparse) | intermediate | both | 32 | 26 | -0.031 | -0.097 | 0.027 | -3.093 | 0.031 | 87.172 |
| main (not too sparse) | intermediate | narrow | 28 | 23 | -0.043 | -0.113 | 0.020 | -4.251 | 0.036 | 87.172 |
| main (not too sparse) | intermediate | middle | 4 | 3 | 0.053 | -0.067 | 0.177 | 5.415 | 0.000 | 79.421 |
| main (not too sparse) | fading | both | 376 | 184 | 0.003 | -0.018 | 0.027 | 0.342 | 0.032 | 92.044 |
| main (not too sparse) | fading | narrow | 279 | 136 | 0.002 | -0.025 | 0.032 | 0.161 | 0.022 | 63.038 |
| main (not too sparse) | fading | middle | 97 | 48 | 0.009 | -0.018 | 0.038 | 0.864 | 0.062 | 285.150 |
| main (not too sparse) | all | both | 461 | 200 | 0.004 | -0.016 | 0.024 | 0.379 | 0.035 | 87.503 |
| main (not too sparse) | all | narrow | 352 | 150 | 0.001 | -0.023 | 0.025 | 0.113 | 0.028 | 67.337 |
| main (not too sparse) | all | middle | 109 | 50 | 0.012 | -0.014 | 0.039 | 1.244 | 0.055 | 279.111 |
| including too sparse | sustained | both | 56 | 42 | 0.066 | -0.018 | 0.150 | 6.863 | 0.054 | 79.252 |
| including too sparse | sustained | narrow | 48 | 36 | 0.071 | -0.029 | 0.169 | 7.375 | 0.062 | 54.540 |
| including too sparse | sustained | middle | 8 | 6 | 0.038 | -0.010 | 0.074 | 3.837 | 0.000 | 340.237 |
| including too sparse | intermediate | both | 32 | 26 | -0.031 | -0.097 | 0.027 | -3.093 | 0.031 | 87.172 |
| including too sparse | intermediate | narrow | 28 | 23 | -0.043 | -0.113 | 0.020 | -4.251 | 0.036 | 87.172 |
| including too sparse | intermediate | middle | 4 | 3 | 0.053 | -0.067 | 0.177 | 5.415 | 0.000 | 79.421 |
| including too sparse | fading | both | 382 | 187 | 0.006 | -0.016 | 0.030 | 0.611 | 0.034 | 86.845 |
| including too sparse | fading | narrow | 285 | 139 | 0.005 | -0.023 | 0.035 | 0.525 | 0.025 | 60.937 |
| including too sparse | fading | middle | 97 | 48 | 0.009 | -0.018 | 0.038 | 0.864 | 0.062 | 285.150 |
| including too sparse | all | both | 470 | 204 | 0.011 | -0.011 | 0.032 | 1.078 | 0.036 | 85.402 |
| including too sparse | all | narrow | 361 | 154 | 0.010 | -0.016 | 0.037 | 1.028 | 0.030 | 63.038 |
| including too sparse | all | middle | 109 | 50 | 0.012 | -0.014 | 0.039 | 1.244 | 0.055 | 279.111 |

- narrow only: sustained minus fading = 0.024 (-0.105 to 0.137), 45 and 279 tests, 140 themes.
- middle only: sustained minus fading = 0.029 (-0.025 to 0.071), 8 and 97 tests, 50 themes.

## Detection (placebo-category rank, one-sided p < 0.05; about 5% expected under no effect)
- fading: 12 of 376 (3.2%); median expected weighted loans in the window 92.0
- intermediate: 1 of 32 (3.1%); median expected weighted loans in the window 87.2
- sustained: 3 of 53 (5.7%); median expected weighted loans in the window 85.4

## Joint regression: tau on log2 whole duration (weeks) and log2 whole peak ratio (bootstrap clustered by theme)

| set | tests | themes | b_dur | dur_lo | dur_hi | b_peak | peak_lo | peak_hi | corr_ld_lp | dur_alone | peak_alone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wikipedia, narrow and middle | 461 | 200 | 0.006 | -0.044 | 0.044 | 0.010 | -0.046 | 0.071 | 0.546 | 0.009 | 0.016 |
| narrow only | 352 | 150 | 0.003 | -0.056 | 0.051 | 0.013 | -0.049 | 0.091 | 0.540 | 0.007 | 0.016 |
| middle only | 109 | 50 | 0.026 | -0.003 | 0.068 | -0.010 | -0.153 | 0.061 | 0.578 | 0.023 | 0.019 |

Seattle, same specification (exploratory, Study 3b tau, 625 tests): duration 0.021 (-0.013 to 0.053), size -0.008 (-0.055 to 0.043).
run time 6s
