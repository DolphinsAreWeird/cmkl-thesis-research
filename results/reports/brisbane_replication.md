# Brisbane replication: do sustained rises in Wikipedia interest predict more borrowing in a second city?

Khant Phyo Wai, student ID 01323050. Written 2026-10-15 02:56. Record: `prereg/brisbane_replication_settings_2026-10-15.json` (SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`, checked on every run). Code: `code/brisbane/` (steps 01 to 06; the Study 3b count model and inference are reused unchanged from `code/main_study/study3b/`). Outputs: `data/db/brisbane/`. Every choice the record does not make is a row in `prereg/DEVIATIONS.md` (Brisbane replication section).

## What this is

A second-city replication of the Seattle theme-level design: Brisbane City Council library loans (Australia, CC BY 4.0), matched to Seattle works to inherit theme profiles, tested against the same global English Wikipedia interest shifts. Brisbane publishes three sampled days a month (the 7th to 9th), so each month is a small sample, and the loans per theme are small. That limits what can be detected (see power).

## Short answer

- Data: Brisbane loans June 2015 to December 2025, 6,391,712 loans, 34.3% matched to Seattle works (31.6% carry a theme profile).
- Positive controls: neither control can be tested as the record specifies, because Brisbane was closed or had no titles in most of the months 0 to +2 (details below). They are reported, not passed.
- H1 (sustained rises, pooled tau above 0): not supported: tau 0.028 (95% interval -0.066 to 0.115), 53 tests.
- H2 (sustained minus fading above 0): not supported: sustained minus fading = 0.024 (95% interval -0.076 to 0.116; share of resamples at or below 0: 0.286); fading pooled tau = 0.003 (-0.018 to 0.027), 376 tests in 184 themes; 190 themes in the difference.
- Power: with this little data a single theme test needs about +50% (middle) to +100% (narrow) loans to be found; the pooled sustained estimate has a 95% interval of about plus or minus 0.09 in log units, so the smallest pooled lift it could reliably show (80% power, one sided 5%) is about 12%. A null here is therefore weak evidence against a small effect, not strong evidence against it.

## Download

- library-checkouts-branch-date-2015-2019.csv: 294.4 MB CSV, 2,947,633 rows; source https://data.brisbane.qld.gov.au/explore/dataset/library-checkouts-branch-date-2015-2019 (also data.qld.gov.au, CC-BY-4.0)
- library-checkouts-2020-2022.csv: 162.8 MB CSV, 1,750,469 rows; source https://data.brisbane.qld.gov.au/explore/dataset/library-checkouts-2020-2022 (also data.qld.gov.au, CC-BY-4.0)
- library-checkouts-2015.parquet: 261,400 loans, 21 distinct days sampled, 2015-06-07 to 2015-12-09, 10.6 MB, unparsable dates 0
- library-checkouts-2016.parquet: 614,670 loans, 36 distinct days sampled, 2016-01-07 to 2016-12-09, 26.6 MB, unparsable dates 0
- library-checkouts-2017.parquet: 636,227 loans, 36 distinct days sampled, 2017-01-07 to 2017-12-09, 26.1 MB, unparsable dates 0
- library-checkouts-2018.parquet: 722,097 loans, 36 distinct days sampled, 2018-01-07 to 2018-12-09, 32.2 MB, unparsable dates 0
- library-checkouts-2019.parquet: 713,216 loans, 36 distinct days sampled, 2019-01-07 to 2019-12-09, 24.2 MB, unparsable dates 0
- library-checkouts-2020.parquet: 515,888 loans, 61 distinct days sampled, 2020-01-06 to 2020-12-09, 15.3 MB, unparsable dates 0
- library-checkouts-2021.parquet: 615,320 loans, 48 distinct days sampled, 2021-01-06 to 2021-12-09, 19.2 MB, unparsable dates 0
- library-checkouts-2022.parquet: 619,261 loans, 57 distinct days sampled, 2022-01-06 to 2022-12-09, 18.6 MB, unparsable dates 0
- library-checkouts-2023.parquet (already in the project): 568,440 loans, 49 distinct days, 2023-01-06 to 2023-12-09, 16.7 MB
- library-checkouts-2024.parquet (already in the project): 579,911 loans, 48 distinct days, 2024-01-06 to 2024-12-09, 17.7 MB
- library-checkouts-2025.parquet (already in the project): 545,282 loans, 48 distinct days, 2025-01-06 to 2025-12-09, 16.6 MB

The distinct-day counts in this list are UTC dates, which include a few stray dates with a handful of loans each; the sampled days by Brisbane local date (about 36 a year, three a month) are in the match table below.

All years are in `data/raw/brisbane/` as parquet with the columns of the 2023 to 2025 files. New files for 2015 to 2022: about 0.17 GB. Raw CSVs (457 MB) were deleted after conversion.

- written: 2026-10-15 02:54:40; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- Seattle match index: 650,052 works keyed by (normalised main title, author family name); 13,148 keys had more than one Seattle work (the work with the most Seattle checkouts is taken)
- theme strength: stored strength; only works with a narrow or middle theme profile (753,987) add to theme counts
- months 2015-06 to 2025-12: 127; usable 116; unusable 11

### Match rate by year (loans)
| year | loans | dates_with_loans | sampled_days | loans_with_author | matched_loans | match_rate | loans_with_theme_profile | theme_rate | unique_title_author_pairs | matched_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 261400 | 21 | 21 | 231623 | 90547 | 0.346 | 82626 | 0.316 | 72402 | 25659 |
| 2016 | 614670 | 36 | 36 | 543005 | 213169 | 0.347 | 195477 | 0.318 | 117673 | 41051 |
| 2017 | 636227 | 36 | 36 | 534077 | 206878 | 0.325 | 190823 | 0.300 | 124358 | 43344 |
| 2018 | 722097 | 36 | 36 | 646470 | 253056 | 0.350 | 234303 | 0.325 | 137995 | 49066 |
| 2019 | 713216 | 36 | 36 | 584554 | 250044 | 0.351 | 231264 | 0.324 | 190598 | 71607 |
| 2020 | 515888 | 50 | 36 | 405891 | 158108 | 0.306 | 145634 | 0.282 | 123679 | 40619 |
| 2021 | 615320 | 36 | 36 | 500476 | 218513 | 0.355 | 200427 | 0.326 | 118309 | 45482 |
| 2022 | 619261 | 45 | 36 | 512042 | 204995 | 0.331 | 188107 | 0.304 | 129183 | 45354 |
| 2023 | 568440 | 37 | 37 | 479649 | 187683 | 0.330 | 172860 | 0.304 | 125164 | 44353 |
| 2024 | 579911 | 36 | 36 | 497364 | 209296 | 0.361 | 192340 | 0.332 | 113688 | 45613 |
| 2025 | 545282 | 37 | 36 | 474179 | 200337 | 0.367 | 184086 | 0.338 | 109430 | 44524 |

Overall: 2,192,626 of 6,391,712 loans matched (34.3%), 31.6% carry a narrow or middle theme profile.

### Unusable months
| month | days | total_checkouts | title_share | reason | closure_ratio |
| --- | --- | --- | --- | --- | --- |
| 2017-03 | 3 | 66424 | 0.708 | source file has too few titles (under 90% of loans) | 1.146 |
| 2017-08 | 3 | 44523 | 0.405 | source file has too few titles (under 90% of loans) | 0.951 |
| 2020-04 | 3 | 2591 | 1.000 | library-wide total below closure threshold | 0.048 |
| 2020-05 | 3 | 1770 | 1.000 | library-wide total below closure threshold | 0.034 |
| 2020-06 | 3 | 19425 | 1.000 | library-wide total below closure threshold | 0.393 |
| 2020-07 | 3 | 58927 | 0.000 | source file has too few titles (under 90% of loans) | 1.237 |
| 2021-08 | 3 | 17987 | 1.000 | library-wide total below closure threshold | 0.377 |
| 2022-10 | 3 | 53542 | 0.000 | source file has too few titles (under 90% of loans) | 0.999 |
| 2023-04 | 3 | 4386 | 1.000 | library-wide total below closure threshold | 0.079 |
| 2023-08 | 3 | 51250 | 0.000 | source file has too few titles (under 90% of loans) | 0.981 |
| 2025-03 | 3 | 1318 | 1.000 | library-wide total below closure threshold | 0.026 |

### Sampled days per usable month
| days | months |
| --- | --- |
| 3 | 115 |
| 4 | 1 |

### Identities
- narrow: weighted-sum identity True; share of usable-month loans carrying a narrow theme (weighted) 28.0%
- middle: weighted-sum identity True; share of usable-month loans carrying a middle theme (weighted) 29.9%

### Categories with counts
- narrow: 242
- middle: 86

- written: 2026-10-15 02:54:57; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- data: Brisbane library loans 2015-06 to 2025-12, formats pooled; model: Study 3b count model, one pooled series; window months 0 to +2
- pass reading (Study 3b): tau > 0 with one-sided placebo-category rank p < 0.05

- Brisbane months out of the data (closure rule or too few sampled days): 2017-03, 2017-08, 2020-04, 2020-05, 2020-06, 2020-07, 2021-08, 2022-10, 2023-04, 2023-08, 2025-03

### COVID-19: NOT TESTABLE (window too short)

Epidemics and plagues (narrow, B15.M04.N05), month 0 = 2020-03

The record's primary window (months 0 to +2) has only 1 usable Brisbane month(s) (2020-03); the rule needs at least 2, so the control cannot be tested as the record specifies.
Descriptive only, not the record's test: secondary window months 0 to +5 has 2 usable months (2020-03, 2020-08).

Secondary window: tau_s = 0.171 (ratio 1.19), observed 48 against expected 40 weighted loans, z = 1.88, placebo-category rank p = 0.186 among 112 placebo themes.

Monthly observed and expected weighted loans, months -6 to +5 (descriptive; "usable" false = out of the data):

| rel | month | observed_loans_weighted | expected | ratio | usable |
| --- | --- | --- | --- | --- | --- |
| -6 | 2019-09 | 18.78 | 18.41 | 1.02 | True |
| -5 | 2019-10 | 20.91 | 21.41 | 0.9769 | True |
| -4 | 2019-11 | 32.4 | 27.22 | 1.19 | True |
| -3 | 2019-12 | 24.4 | 26.45 | 0.9226 | True |
| -2 | 2020-01 | 43.98 | 47.19 | 0.932 | True |
| -1 | 2020-02 | 26.1 | 25.74 | 1.014 | True |
| 0 | 2020-03 | 20.18 | 19.98 | 1.01 | True |
| 1 | 2020-04 |  |  |  | False |
| 2 | 2020-05 |  |  |  | False |
| 3 | 2020-06 |  |  |  | False |
| 4 | 2020-07 |  |  |  | False |
| 5 | 2020-08 | 27.82 | 20.49 | 1.358 | True |

### George Floyd / BLM: NOT TESTABLE (window too short)

Race and racism (narrow, B05.M02.N02), month 0 = 2020-06

The record's primary window (months 0 to +2) has only 1 usable Brisbane month(s) (2020-08); the rule needs at least 2, so the control cannot be tested as the record specifies.
Descriptive only, not the record's test: secondary window months 0 to +5 has 4 usable months (2020-08, 2020-09, 2020-10, 2020-11).

Secondary window: tau_s = 0.391 (ratio 1.48), observed 99 against expected 67 weighted loans, z = 5.90, placebo-category rank p = 0.018 among 111 placebo themes.

Monthly observed and expected weighted loans, months -6 to +5 (descriptive; "usable" false = out of the data):

| rel | month | observed_loans_weighted | expected | ratio | usable |
| --- | --- | --- | --- | --- | --- |
| -6 | 2019-12 | 15.53 | 17.94 | 0.8657 | True |
| -5 | 2020-01 | 36.11 | 32.77 | 1.102 | True |
| -4 | 2020-02 | 24.7 | 20.77 | 1.189 | True |
| -3 | 2020-03 | 25.12 | 16.06 | 1.565 | True |
| -2 | 2020-04 |  |  |  | False |
| -1 | 2020-05 |  |  |  | False |
| 0 | 2020-06 |  |  |  | False |
| 1 | 2020-07 |  |  |  | False |
| 2 | 2020-08 | 26.8 | 17.42 | 1.538 | True |
| 3 | 2020-09 | 21.45 | 17.32 | 1.238 | True |
| 4 | 2020-10 | 31.46 | 16.46 | 1.911 | True |
| 5 | 2020-11 | 19.75 | 16.04 | 1.232 | True |

- written: 2026-10-15 02:55:44; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- shifts: Wikipedia, narrow and middle, labelled, quality OK, non-seasonal, month 0 2016-01 to 2025-06: 593 shifts with a theme in the Brisbane panel, in 186 (level, month 0) units
- shift rows tested (feasible fit, usable window of at least 2 months): 472 of 593; skip reasons: {'not feasible': 79, 'window too short': 42}
- main set (not too sparse, i.e. at least 5 expected weighted loans in months 0 to +2, and loans above 0): 461 tests in 200 themes; too sparse: 11; zero loans in window: 2
- bootstrap: 2000 resamples of themes, seed 20261015, 95% percentile intervals

### Hypotheses (pooled mean tau over months 0 to +2; tau is the log of observed over expected weighted loans)

- **H1 NOT SUPPORTED**: pooled tau of sustained rises = 0.028 (95% interval -0.066 to 0.115; about +2.8% loans against the fitted trend), 53 tests in 41 themes.
- **H2 NOT SUPPORTED**: sustained minus fading = 0.024 (95% interval -0.076 to 0.116; share of resamples at or below 0: 0.286); fading pooled tau = 0.003 (-0.018 to 0.027), 376 tests in 184 themes; 190 themes in the difference.
- Sensitivity, including too-sparse tests: sustained minus fading = 0.060 (-0.034 to 0.148), 56 sustained and 382 fading tests.

### Pooled tau by duration class and level
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

### Detection (placebo-category rank, one-sided p < 0.05; about 5% expected under no effect)
- fading: 12 of 376 (3.2%); median expected weighted loans in the window 92.0
- intermediate: 1 of 32 (3.1%); median expected weighted loans in the window 87.2
- sustained: 3 of 53 (5.7%); median expected weighted loans in the window 85.4

### Joint regression: tau on log2 whole duration (weeks) and log2 whole peak ratio (bootstrap clustered by theme)

| set | tests | themes | b_dur | dur_lo | dur_hi | b_peak | peak_lo | peak_hi | corr_ld_lp | dur_alone | peak_alone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wikipedia, narrow and middle | 461 | 200 | 0.006 | -0.044 | 0.044 | 0.010 | -0.046 | 0.071 | 0.546 | 0.009 | 0.016 |
| narrow only | 352 | 150 | 0.003 | -0.056 | 0.051 | 0.013 | -0.049 | 0.091 | 0.540 | 0.007 | 0.016 |
| middle only | 109 | 50 | 0.026 | -0.003 | 0.068 | -0.010 | -0.153 | 0.061 | 0.578 | 0.023 | 0.019 |

Seattle, same specification (exploratory, Study 3b tau, 625 tests): duration 0.021 (-0.013 to 0.053), size -0.008 (-0.055 to 0.043).
run time 6s

- written: 2026-10-15 02:56:03; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- 200 draws per lift and size band, lifts [0.2, 0.5, 1.0] (+0 as a calibration check), seed 20261015; month 0 2016-01 to 2025-06; detection one-sided rank p < 0.05; MDE = smallest lift detected in >= 80% of draws
- size band edges (expected weighted loans in months 0 to +2, quartiles of all placebo units per level):
| level | units | edge_0 | edge_1 | edge_2 | edge_3 | edge_4 |
| --- | --- | --- | --- | --- | --- | --- |
| narrow | 14924 | 0.0 | 33.8 | 79.8 | 196.4 | 4471.5 |
| middle | 5306 | 5.8 | 145.5 | 292.3 | 604.9 | 5220.6 |

### Detection by lift, all size bands together (an average over small and large themes)
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

### By size band

#### narrow, size band 1 of 4 (expected loans 0.0 to 33.8): minimum detectable lift none of the sizes

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 11 | 0.055 |
| 0.200 | 200 | 25 | 0.125 |
| 0.500 | 200 | 58 | 0.290 |
| 1.000 | 200 | 123 | 0.615 |

#### narrow, size band 2 of 4 (expected loans 33.8 to 79.8): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 9 | 0.045 |
| 0.200 | 200 | 41 | 0.205 |
| 0.500 | 200 | 99 | 0.495 |
| 1.000 | 200 | 162 | 0.810 |

#### narrow, size band 3 of 4 (expected loans 79.8 to 196.4): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 12 | 0.060 |
| 0.200 | 200 | 61 | 0.305 |
| 0.500 | 200 | 154 | 0.770 |
| 1.000 | 200 | 192 | 0.960 |

#### narrow, size band 4 of 4 (expected loans 196.4 to 4471.5): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 6 | 0.030 |
| 0.200 | 200 | 90 | 0.450 |
| 0.500 | 200 | 184 | 0.920 |
| 1.000 | 200 | 200 | 1.000 |

#### middle, size band 1 of 4 (expected loans 5.8 to 145.5): minimum detectable lift 1.0

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 11 | 0.055 |
| 0.200 | 200 | 39 | 0.195 |
| 0.500 | 200 | 125 | 0.625 |
| 1.000 | 200 | 178 | 0.890 |

#### middle, size band 2 of 4 (expected loans 145.5 to 292.3): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 8 | 0.040 |
| 0.200 | 200 | 81 | 0.405 |
| 0.500 | 200 | 179 | 0.895 |
| 1.000 | 200 | 199 | 0.995 |

#### middle, size band 3 of 4 (expected loans 292.3 to 604.9): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 14 | 0.070 |
| 0.200 | 200 | 98 | 0.490 |
| 0.500 | 200 | 189 | 0.945 |
| 1.000 | 200 | 200 | 1.000 |

#### middle, size band 4 of 4 (expected loans 604.9 to 5220.6): minimum detectable lift 0.5

| lift | draws | detected | rate |
| --- | --- | --- | --- |
| 0.000 | 200 | 9 | 0.045 |
| 0.200 | 200 | 126 | 0.630 |
| 0.500 | 200 | 190 | 0.950 |
| 1.000 | 200 | 198 | 0.990 |

run time 1s

## Reading and limits

- Months and sampling: three days a month; loans per theme per month are in the tens, so each test has a wide error. The model's dispersion and the placebo-category rank handle this, and the false-positive rate of the tests in the power run is about 5% as it should be.
- Match rate: about one third of loans match a Seattle work by exact normalised title and author family name; about 15% of loans have no author (magazines, DVDs), and the rest are mostly books Seattle never lent or spelled differently. Matched titles are a selected sample of the collection (popular, English, published in the US market); this is the record's rule and was not tuned.
- Months out of the data: closures (April to June 2020, August 2021, April 2023, March 2025) and five months where the source file has few or no titles (March and August 2017, July 2020, October 2022, August 2023). The title rule was added after the first control table; see DEVIATIONS.
- Controls: the 2020 closures fall inside both control windows, so the record's primary window has only one usable month each. The secondary window 0 to +5 is shown for information only.
- Brisbane does not publish item type in the 2023 to 2025 files, so the print versus other split was not possible.
- The Wikipedia interest series is global English, as in the record; Brisbane readers are a small part of it.
