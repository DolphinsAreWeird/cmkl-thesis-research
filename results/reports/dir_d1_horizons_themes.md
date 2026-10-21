# Direction D1 (themes): longer horizons for the theme tests

1. Looking further ahead does not make a theme's Wikipedia attention a better guide to its borrowing. For the hand-checked concept pages the ranking link falls from 0.026 at one month to 0.015 at six months and about 0 at twelve months. For the AI-sorted pages it stays near 0 (S2) or turns slightly negative (S2C, -0.024 at twelve months).
2. The one-month ranking numbers and the months 0 to 2 effects reproduce the stored Test F and Chapter 6 results exactly. A placebo that swaps attention changes between themes gives about 0 at every horizon, and a lift added on purpose in months 6 to 11 is recovered (0.098 for an added 0.10).
3. After a lasting rise of the hand-checked concept pages, borrowing stays about 11% above the synthetic control in months 3 to 5, as high as in months 0 to 2 (about 10%). It then drops to about 5% in months 6 to 11, still above 0, and averages about 8% over the first year.
4. For the AI-sorted series the small months 0 to 2 effect (about 3% for S2C, 2% for S2) does not grow later. Months 3 to 5 and 6 to 11 give 1 to 2% with intervals that include 0, and the own-trend method finds no effect in any window.
5. So longer windows do not rescue the AI series, and the hand-checked effect lasts about half a year before it fades. The later windows are descriptive: they rest on longer projections and include later rises of the same theme.

- written 2026-10-22 03:34 +07 by code/main_study/wiki_led/dirs/d1_horizons_themes.py; record prereg/addenda_wiki_led/2026-10-22_i_directions.json (SHA-256 5659fbc6e63f..., fixed 22 Oct 03:13 before any result), key D1_horizons_themes; every interval is a 95% interval; descriptive (no decision rule).

## Part 1: Wikipedia-only ranking of themes, no fitting

Input: the change of a theme's attention series from last month to this month. Target: the change in the theme's borrowing share from this month to the mean of the next k months (log share). Score: the mean Spearman correlation within origin month, format and level (the Test C measure of Test F step 25), intervals from 2,000 draws of 3-month blocks of origin months. Rows: the benchmark's main rows (Seattle print and ebook, 510 theme series).

- Check: k = 1 reproduces the stored Test F numbers (g3_wikionly.csv, h_g3_wikionly.csv) exactly: yes (largest difference 7.6e-17).
- Rows: a row needs all k months observed. k = 1: 36,081 rows; k = 3: 33,622 rows; k = 6: 29,377 rows; k = 12: 20,429 rows. Apart from the end of the data, rows are lost when the window touches months that are missing for most series: 2020-04 to 2020-09 (the 2020 closure months) and 2024-05 to 2024-07 (missing in the benchmark history), so the k = 12 rows have few origins from mid-2019 to early 2020 and from mid-2023 to mid-2024 and none after 2025-08.

### Each k on its own rows

| series | k | rows | origin months | Spearman [95% interval] | interval with blocks of max(3, k) months |
| --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | 1 | 36,081 | 88 (2019-01 to 2026-07) | -0.006 [-0.022, +0.010] | [-0.022, +0.010] |
| S2 (AI pages) | 1 | 36,081 | 88 (2019-01 to 2026-07) | +0.009 [-0.007, +0.023] | [-0.007, +0.023] |
| concept pages (hand-checked) | 1 | 36,081 | 88 (2019-01 to 2026-07) | +0.026 [+0.009, +0.042] | [+0.009, +0.042] |
| S2C (AI concept pages) | 3 | 33,622 | 83 (2019-01 to 2026-05) | -0.017 [-0.032, -0.002] | [-0.032, -0.002] |
| S2 (AI pages) | 3 | 33,622 | 83 (2019-01 to 2026-05) | -0.002 [-0.018, +0.015] | [-0.018, +0.015] |
| concept pages (hand-checked) | 3 | 33,622 | 83 (2019-01 to 2026-05) | +0.018 [+0.003, +0.033] | [+0.003, +0.033] |
| S2C (AI concept pages) | 6 | 29,377 | 77 (2019-01 to 2026-02) | -0.016 [-0.026, -0.004] | [-0.027, -0.004] |
| S2 (AI pages) | 6 | 29,377 | 77 (2019-01 to 2026-02) | -0.007 [-0.021, +0.006] | [-0.019, +0.004] |
| concept pages (hand-checked) | 6 | 29,377 | 77 (2019-01 to 2026-02) | +0.015 [-0.001, +0.031] | [+0.002, +0.028] |
| S2C (AI concept pages) | 12 | 20,429 | 65 (2019-01 to 2025-08) | -0.023 [-0.036, -0.011] | [-0.035, -0.012] |
| S2 (AI pages) | 12 | 20,429 | 65 (2019-01 to 2025-08) | -0.011 [-0.027, +0.005] | [-0.023, +0.000] |
| concept pages (hand-checked) | 12 | 20,429 | 65 (2019-01 to 2025-08) | -0.002 [-0.019, +0.013] | [-0.015, +0.010] |

### All k on the same rows (the 20,429 rows that have k = 12), and k minus k = 1 from the same draws

| series | k = 1 | k = 3 | k = 6 | k = 12 | k = 3 minus 1 | k = 6 minus 1 | k = 12 minus 1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | -0.003 [-0.022, +0.016] | -0.017 [-0.033, +0.000] | -0.020 [-0.032, -0.006] | -0.023 [-0.036, -0.011] | -0.015 [-0.025, -0.003] | -0.017 [-0.030, -0.004] | -0.021 [-0.039, -0.002] |
| S2 (AI pages) | +0.003 [-0.015, +0.022] | -0.007 [-0.024, +0.011] | -0.007 [-0.022, +0.009] | -0.011 [-0.027, +0.005] | -0.009 [-0.022, +0.003] | -0.009 [-0.022, +0.004] | -0.014 [-0.029, +0.002] |
| concept pages (hand-checked) | +0.029 [+0.009, +0.050] | +0.022 [+0.005, +0.040] | +0.016 [-0.002, +0.034] | -0.002 [-0.019, +0.013] | -0.007 [-0.021, +0.008] | -0.013 [-0.032, +0.006] | -0.031 [-0.056, -0.008] |

### Series against each other at each k (other minus base, same draws)

- k = 1: S2C (AI concept pages) minus concept pages (hand-checked): -0.032 [-0.051, -0.012]
- k = 1: S2 (AI pages) minus concept pages (hand-checked): -0.017 [-0.037, +0.003]
- k = 1: S2C (AI concept pages) minus S2 (AI pages): -0.015 [-0.032, +0.003]
- k = 3: S2C (AI concept pages) minus concept pages (hand-checked): -0.035 [-0.053, -0.017]
- k = 3: S2 (AI pages) minus concept pages (hand-checked): -0.020 [-0.042, +0.002]
- k = 3: S2C (AI concept pages) minus S2 (AI pages): -0.015 [-0.033, +0.002]
- k = 6: S2C (AI concept pages) minus concept pages (hand-checked): -0.031 [-0.049, -0.013]
- k = 6: S2 (AI pages) minus concept pages (hand-checked): -0.022 [-0.042, -0.001]
- k = 6: S2C (AI concept pages) minus S2 (AI pages): -0.009 [-0.024, +0.006]
- k = 12: S2C (AI concept pages) minus concept pages (hand-checked): -0.021 [-0.037, -0.005]
- k = 12: S2 (AI pages) minus concept pages (hand-checked): -0.009 [-0.030, +0.012]
- k = 12: S2C (AI concept pages) minus S2 (AI pages): -0.012 [-0.030, +0.005]

### Placebo: each row's attention change swapped with another theme's in the same month, format and level

- S2C (AI concept pages), k = 1: -0.002 [-0.011, +0.009]; S2 (AI pages), k = 1: -0.004 [-0.014, +0.007]; concept pages (hand-checked), k = 1: -0.007 [-0.016, +0.002]; S2C (AI concept pages), k = 3: +0.004 [-0.007, +0.014]; S2 (AI pages), k = 3: -0.000 [-0.011, +0.011]; concept pages (hand-checked), k = 3: -0.006 [-0.015, +0.004]; S2C (AI concept pages), k = 6: -0.001 [-0.012, +0.009]; S2 (AI pages), k = 6: -0.002 [-0.016, +0.011]; concept pages (hand-checked), k = 6: -0.005 [-0.015, +0.007]; S2C (AI concept pages), k = 12: -0.005 [-0.017, +0.007]; S2 (AI pages), k = 12: -0.004 [-0.018, +0.010]; concept pages (hand-checked), k = 12: +0.000 [-0.012, +0.012]

## Part 2: borrowing after lasting rises, later months

Lasting rises (4 weeks or more at 1.5 times the normal level or more) of each attention series; borrowing in panel a (the Study 3 panel: Seattle print, ebook and audiobook loans, and LibriVox); narrow and middle themes pooled; effect = mean gap in log share between the theme and its synthetic control, or between the theme and its own trend (event study), in the window; intervals from 2,000 resamples of themes (seed 20261013). Everything else as Test F step 24 and Chapter 6.

### Checks

- S2C (AI concept pages): per-test months 0 to 2 and 0 to 5 effects and the stored gaps of months 3 to 6 reproduced: yes (7,496 tests, largest difference 0.0e+00); pooled rows reproduced: yes (40 rows, largest difference 9.9e-17); months 0 to 2, both levels, lasting rises: synthetic control +0.028 [+0.001, +0.055], own trend +0.012 [-0.023, +0.045].
- S2 (AI pages): per-test months 0 to 2 and 0 to 5 effects and the stored gaps of months 3 to 6 reproduced: yes (10,236 tests, largest difference 0.0e+00); pooled rows reproduced: yes (40 rows, largest difference 9.9e-17); months 0 to 2, both levels, lasting rises: synthetic control +0.018 [+0.001, +0.035], own trend -0.002 [-0.025, +0.019].
- concept pages (hand-checked, Chapter 6): per-test months 0 to 2 and 0 to 5 effects and the stored gaps of months 3 to 6 reproduced: yes (3,040 tests, largest difference 0.0e+00); pooled rows reproduced: yes (32 rows, largest difference 9.7e-17); months 0 to 2, both levels, lasting rises: synthetic control +0.093 [+0.042, +0.154], own trend +0.089 [+0.047, +0.137].
- Positive control (S2C): 0.10 added to the log share in months 6 to 11 after every tested lasting rise (3,674 theme-months); change of the pooled effect: synthetic control, months 0 to 2: +0.001; synthetic control, months 3 to 5: -0.002; synthetic control, months 6 to 11: +0.098; synthetic control, months 0 to 11: +0.050; own trend, months 0 to 2: -0.001; own trend, months 3 to 5: -0.003; own trend, months 6 to 11: +0.093; own trend, months 0 to 11: +0.047.

### Main table: lasting rises, both levels pooled, each window on every test where it is available

| series | method | months 0 to 2 | months 3 to 5 | months 6 to 11 | months 0 to 11 |
| --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | synthetic control | +0.028 [+0.001, +0.055] (+2.9%; 313 tests, 100 themes) | +0.012 [-0.014, +0.040] (+1.2%; 302 tests, 101 themes) | +0.019 [-0.010, +0.052] (+1.9%; 308 tests, 101 themes) | +0.022 [-0.004, +0.049] (+2.2%; 312 tests, 101 themes) |
| S2C (AI concept pages) | own trend | +0.012 [-0.023, +0.045] (+1.2%; 311 tests, 100 themes) | -0.002 [-0.037, +0.036] (-0.2%; 300 tests, 101 themes) | -0.012 [-0.053, +0.030] (-1.2%; 306 tests, 101 themes) | -0.005 [-0.041, +0.033] (-0.5%; 310 tests, 101 themes) |
| S2 (AI pages) | synthetic control | +0.018 [+0.001, +0.035] (+1.8%; 748 tests, 172 themes) | +0.016 [-0.002, +0.035] (+1.6%; 722 tests, 167 themes) | +0.008 [-0.010, +0.026] (+0.8%; 734 tests, 171 themes) | +0.014 [-0.003, +0.030] (+1.4%; 744 tests, 171 themes) |
| S2 (AI pages) | own trend | -0.002 [-0.025, +0.019] (-0.2%; 743 tests, 172 themes) | -0.014 [-0.039, +0.009] (-1.4%; 717 tests, 167 themes) | -0.016 [-0.044, +0.011] (-1.6%; 729 tests, 171 themes) | -0.013 [-0.036, +0.010] (-1.3%; 739 tests, 171 themes) |
| concept pages (hand-checked, Chapter 6) | synthetic control | +0.093 [+0.042, +0.154] (+9.7%; 155 tests, 46 themes) | +0.107 [+0.057, +0.159] (+11.3%; 143 tests, 46 themes) | +0.048 [+0.006, +0.097] (+5.0%; 154 tests, 47 themes) | +0.075 [+0.032, +0.122] (+7.7%; 155 tests, 47 themes) |
| concept pages (hand-checked, Chapter 6) | own trend | +0.089 [+0.047, +0.137] (+9.4%; 154 tests, 46 themes) | +0.076 [+0.023, +0.130] (+7.9%; 142 tests, 46 themes) | +0.048 [-0.007, +0.104] (+4.9%; 153 tests, 47 themes) | +0.064 [+0.019, +0.113] (+6.6%; 154 tests, 47 themes) |

### Same tests for every window (all lasting rises): window means and later window minus months 0 to 2

| series | method | tests (themes) | months 0 to 2 | months 3 to 5 | months 6 to 11 | months 0 to 11 | 3 to 5 minus 0 to 2 | 6 to 11 minus 0 to 2 | 0 to 11 minus 0 to 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | synthetic control | 272 (96) | +0.031 [+0.001, +0.061] | +0.016 [-0.013, +0.045] | +0.011 [-0.018, +0.041] | +0.017 [-0.007, +0.044] | -0.015 [-0.035, +0.008] | -0.020 [-0.049, +0.008] | -0.014 [-0.032, +0.003] |
| S2C (AI concept pages) | own trend | 270 (96) | +0.014 [-0.023, +0.052] | -0.001 [-0.043, +0.039] | -0.012 [-0.061, +0.033] | -0.003 [-0.046, +0.036] | -0.015 [-0.038, +0.008] | -0.026 [-0.058, +0.003] | -0.017 [-0.037, +0.001] |
| S2 (AI pages) | synthetic control | 679 (165) | +0.015 [-0.005, +0.034] | +0.016 [-0.003, +0.036] | +0.003 [-0.015, +0.021] | +0.010 [-0.007, +0.027] | +0.002 [-0.012, +0.015] | -0.012 [-0.027, +0.003] | -0.005 [-0.015, +0.005] |
| S2 (AI pages) | own trend | 674 (165) | -0.005 [-0.030, +0.019] | -0.015 [-0.041, +0.010] | -0.019 [-0.053, +0.013] | -0.014 [-0.042, +0.012] | -0.010 [-0.023, +0.004] | -0.013 [-0.033, +0.005] | -0.009 [-0.021, +0.003] |
| concept pages (hand-checked, Chapter 6) | synthetic control | 135 (44) | +0.107 [+0.052, +0.171] | +0.111 [+0.061, +0.167] | +0.045 [+0.000, +0.093] | +0.077 [+0.034, +0.125] | +0.004 [-0.037, +0.051] | -0.062 [-0.107, -0.021] | -0.029 [-0.059, -0.001] |
| concept pages (hand-checked, Chapter 6) | own trend | 134 (44) | +0.087 [+0.041, +0.142] | +0.074 [+0.017, +0.136] | +0.038 [-0.029, +0.103] | +0.059 [+0.004, +0.115] | -0.014 [-0.053, +0.029] | -0.049 [-0.097, -0.008] | -0.028 [-0.059, -0.000] |

### Same tests for every window (no other rise of the theme in months 1 to 11): window means and later window minus months 0 to 2

| series | method | tests (themes) | months 0 to 2 | months 3 to 5 | months 6 to 11 | months 0 to 11 | 3 to 5 minus 0 to 2 | 6 to 11 minus 0 to 2 | 0 to 11 minus 0 to 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | synthetic control | 162 (69) | +0.039 [+0.005, +0.076] | +0.019 [-0.015, +0.059] | +0.007 [-0.025, +0.043] | +0.018 [-0.010, +0.048] | -0.020 [-0.049, +0.012] | -0.032 [-0.073, +0.007] | -0.021 [-0.046, +0.001] |
| S2C (AI concept pages) | own trend | 160 (69) | +0.018 [-0.029, +0.070] | +0.009 [-0.048, +0.069] | -0.001 [-0.063, +0.069] | +0.006 [-0.047, +0.066] | -0.009 [-0.038, +0.024] | -0.019 [-0.058, +0.019] | -0.012 [-0.037, +0.011] |
| S2 (AI pages) | synthetic control | 423 (126) | +0.018 [-0.001, +0.039] | +0.027 [+0.006, +0.050] | +0.011 [-0.007, +0.030] | +0.017 [+0.001, +0.035] | +0.008 [-0.010, +0.028] | -0.007 [-0.026, +0.012] | -0.001 [-0.014, +0.012] |
| S2 (AI pages) | own trend | 421 (126) | -0.007 [-0.037, +0.023] | -0.005 [-0.037, +0.028] | -0.012 [-0.056, +0.029] | -0.008 [-0.043, +0.025] | +0.002 [-0.016, +0.022] | -0.005 [-0.031, +0.022] | -0.001 [-0.017, +0.016] |
| concept pages (hand-checked, Chapter 6) | synthetic control | 85 (33) | +0.130 [+0.059, +0.210] | +0.130 [+0.066, +0.202] | +0.058 [+0.010, +0.114] | +0.095 [+0.045, +0.150] | +0.001 [-0.060, +0.066] | -0.072 [-0.134, -0.011] | -0.035 [-0.079, +0.006] |
| concept pages (hand-checked, Chapter 6) | own trend | 84 (33) | +0.064 [+0.005, +0.129] | +0.042 [-0.026, +0.116] | -0.010 [-0.093, +0.066] | +0.021 [-0.045, +0.088] | -0.022 [-0.080, +0.042] | -0.075 [-0.142, -0.017] | -0.043 [-0.089, -0.005] |

### Mean gap by month after the start (same tests as above, all lasting rises), log share

| series | method | m-3 | m-2 | m-1 | m0 | m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8 | m9 | m10 | m11 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2C (AI concept pages) | synthetic control | +0.011 | +0.020 | +0.001 | -0.010 | +0.057 | +0.047 | +0.036 | +0.010 | +0.003 | +0.019 | +0.013 | +0.004 | +0.007 | +0.005 | +0.012 |
| S2C (AI concept pages) | own trend | +0.005 | +0.007 | +0.006 | -0.026 | +0.036 | +0.033 | +0.007 | -0.005 | -0.004 | -0.017 | -0.014 | -0.011 | -0.010 | -0.023 | +0.003 |
| S2 (AI pages) | synthetic control | +0.004 | -0.007 | +0.004 | +0.003 | +0.024 | +0.019 | +0.020 | +0.018 | +0.012 | +0.006 | +0.021 | +0.003 | +0.000 | -0.004 | -0.011 |
| S2 (AI pages) | own trend | -0.008 | -0.009 | +0.006 | -0.007 | -0.002 | -0.007 | -0.013 | -0.013 | -0.019 | -0.023 | -0.001 | -0.019 | -0.020 | -0.019 | -0.029 |
| concept pages (hand-checked, Chapter 6) | synthetic control | +0.008 | -0.000 | +0.026 | +0.044 | +0.145 | +0.126 | +0.130 | +0.121 | +0.083 | +0.108 | +0.035 | +0.041 | +0.042 | +0.015 | +0.020 |
| concept pages (hand-checked, Chapter 6) | own trend | +0.032 | +0.019 | +0.032 | +0.022 | +0.127 | +0.111 | +0.073 | +0.073 | +0.076 | +0.095 | +0.017 | +0.044 | +0.020 | +0.012 | +0.016 |

Intervals for each month are in effects_monthly_gaps.csv.

### Per level (lasting rises, each window on every test where it is available)

- S2C (AI concept pages), synthetic control, narrow: months 0 to 2 +0.029 [-0.005, +0.063] (218 tests); months 3 to 5 +0.016 [-0.014, +0.049] (212 tests); months 6 to 11 +0.023 [-0.015, +0.061] (213 tests); months 0 to 11 +0.024 [-0.007, +0.057] (216 tests)
- S2C (AI concept pages), own trend, narrow: months 0 to 2 +0.002 [-0.042, +0.047] (216 tests); months 3 to 5 -0.006 [-0.052, +0.041] (210 tests); months 6 to 11 -0.023 [-0.076, +0.034] (211 tests); months 0 to 11 -0.014 [-0.060, +0.033] (214 tests)
- S2C (AI concept pages), synthetic control, middle: months 0 to 2 +0.026 [-0.015, +0.068] (95 tests); months 3 to 5 +0.002 [-0.043, +0.050] (90 tests); months 6 to 11 +0.011 [-0.034, +0.061] (95 tests); months 0 to 11 +0.017 [-0.025, +0.064] (96 tests)
- S2C (AI concept pages), own trend, middle: months 0 to 2 +0.036 [-0.010, +0.076] (95 tests); months 3 to 5 +0.009 [-0.039, +0.058] (90 tests); months 6 to 11 +0.013 [-0.044, +0.071] (95 tests); months 0 to 11 +0.017 [-0.032, +0.064] (96 tests)
- S2 (AI pages), synthetic control, narrow: months 0 to 2 +0.015 [-0.005, +0.036] (535 tests); months 3 to 5 +0.010 [-0.010, +0.029] (519 tests); months 6 to 11 +0.003 [-0.013, +0.022] (527 tests); months 0 to 11 +0.009 [-0.007, +0.027] (535 tests)
- S2 (AI pages), own trend, narrow: months 0 to 2 -0.006 [-0.032, +0.018] (532 tests); months 3 to 5 -0.016 [-0.042, +0.010] (516 tests); months 6 to 11 -0.017 [-0.050, +0.016] (524 tests); months 0 to 11 -0.015 [-0.043, +0.011] (532 tests)
- S2 (AI pages), synthetic control, middle: months 0 to 2 +0.026 [-0.009, +0.066] (213 tests); months 3 to 5 +0.032 [-0.012, +0.072] (203 tests); months 6 to 11 +0.020 [-0.024, +0.067] (207 tests); months 0 to 11 +0.026 [-0.017, +0.068] (209 tests)
- S2 (AI pages), own trend, middle: months 0 to 2 +0.009 [-0.035, +0.052] (211 tests); months 3 to 5 -0.009 [-0.059, +0.043] (201 tests); months 6 to 11 -0.016 [-0.075, +0.047] (205 tests); months 0 to 11 -0.009 [-0.060, +0.046] (207 tests)
- concept pages (hand-checked, Chapter 6), synthetic control, narrow: months 0 to 2 +0.088 [+0.029, +0.156] (107 tests); months 3 to 5 +0.098 [+0.043, +0.162] (103 tests); months 6 to 11 +0.026 [-0.020, +0.076] (110 tests); months 0 to 11 +0.056 [+0.010, +0.108] (111 tests)
- concept pages (hand-checked, Chapter 6), own trend, narrow: months 0 to 2 +0.078 [+0.021, +0.142] (106 tests); months 3 to 5 +0.064 [-0.003, +0.129] (102 tests); months 6 to 11 +0.030 [-0.041, +0.094] (109 tests); months 0 to 11 +0.048 [-0.013, +0.106] (110 tests)
- concept pages (hand-checked, Chapter 6), synthetic control, middle: months 0 to 2 +0.105 [+0.018, +0.227] (48 tests); months 3 to 5 +0.129 [+0.051, +0.223] (40 tests); months 6 to 11 +0.105 [+0.028, +0.209] (44 tests); months 0 to 11 +0.120 [+0.038, +0.225] (44 tests)
- concept pages (hand-checked, Chapter 6), own trend, middle: months 0 to 2 +0.115 [+0.053, +0.193] (48 tests); months 3 to 5 +0.105 [+0.010, +0.200] (40 tests); months 6 to 11 +0.091 [-0.012, +0.197] (44 tests); months 0 to 11 +0.105 [+0.024, +0.198] (44 tests)

### Rises of 1 or 2 weeks, for contrast (both levels)

- S2C (AI concept pages), synthetic control: months 0 to 2 +0.002 [-0.005, +0.009] (2796 tests); months 3 to 5 +0.009 [+0.001, +0.017] (2684 tests); months 6 to 11 +0.010 [+0.002, +0.018] (2621 tests); months 0 to 11 +0.008 [+0.002, +0.015] (2647 tests)
- S2C (AI concept pages), own trend: months 0 to 2 -0.019 [-0.030, -0.009] (2762 tests); months 3 to 5 -0.014 [-0.026, -0.001] (2650 tests); months 6 to 11 -0.019 [-0.034, -0.004] (2587 tests); months 0 to 11 -0.017 [-0.029, -0.004] (2613 tests)
- S2 (AI pages), synthetic control: months 0 to 2 +0.004 [-0.003, +0.010] (3653 tests); months 3 to 5 +0.007 [-0.001, +0.014] (3522 tests); months 6 to 11 +0.009 [+0.001, +0.017] (3404 tests); months 0 to 11 +0.007 [+0.000, +0.014] (3438 tests)
- S2 (AI pages), own trend: months 0 to 2 -0.009 [-0.018, -0.001] (3616 tests); months 3 to 5 -0.007 [-0.017, +0.002] (3485 tests); months 6 to 11 -0.008 [-0.021, +0.003] (3367 tests); months 0 to 11 -0.009 [-0.020, +0.000] (3401 tests)
- concept pages (hand-checked, Chapter 6), synthetic control: months 0 to 2 +0.022 [+0.009, +0.035] (1009 tests); months 3 to 5 +0.007 [-0.008, +0.022] (979 tests); months 6 to 11 -0.005 [-0.019, +0.010] (894 tests); months 0 to 11 +0.006 [-0.007, +0.020] (910 tests)
- concept pages (hand-checked, Chapter 6), own trend: months 0 to 2 -0.014 [-0.032, +0.003] (999 tests); months 3 to 5 -0.022 [-0.043, -0.003] (969 tests); months 6 to 11 -0.045 [-0.072, -0.017] (884 tests); months 0 to 11 -0.031 [-0.053, -0.010] (900 tests)

## Choices the addendum did not fix (listed in the script header before any result)

- Part 1: the monthly log share is the benchmark history joined with its stored targets (they agree exactly; the history alone stops at 2026-07); a row needs all k months observed; the main comparison across k uses the same rows; intervals with blocks of max(3, k) months are a sensitivity because neighbouring targets share months; a placebo swaps attention changes across themes.
- Part 2: the synthetic control is carried to months 7 to 11 with the same weights and donors (a month is missing when a weighted donor is missing); the own-trend model is projected to month 11 with the same fit; a new window counts only when it ends inside the panel; the donor screen stays at months -6 to +6, so donors may rise later and the treated theme may rise again (one sensitivity keeps only rises with no other rise of the theme in months 1 to 11); placebo p-values are not computed for the new windows.

## Limits

- Descriptive only; the longer windows were not part of any earlier decision rule. Months 6 to 11 rely on long projections: the own trend is fitted on months -30 to -7 and carried 18 months forward, and the synthetic control is fitted on months -24 to -3.
- Rises from about 2025-09 on drop out of the windows that reach month 11. Many lasting rises started in 2020 (S2C 99 of 345 tests, S2 120 of 793, concept pages 75 of 177), and months 2020-04 to 2020-09 are missing: for rises in spring and summer 2020 months 0 to 2 are missing but months 6 to 11 exist, so the main table compares windows on partly different tests; the same-tests tables do not have this problem.
- Themes often rise again within a year: share of lasting-rise tests with another rise of the same theme in months 1 to 11: S2C 37%, S2 36%, concept pages 30%. Later months therefore mix the first rise with later ones; the sensitivity without such rises gives a similar pattern.
- The own-trend method shows positive gaps for the concept pages already in months -3 to -1 (about +0.02 to +0.03), so its numbers carry some pre-trend; the synthetic control has gaps near 0 before month 0.
- For rises of 1 or 2 weeks the two methods disagree in sign in the later windows (synthetic control about +1%, own trend about -1 to -2%), so no conclusion is drawn for them.
- The negative twelve-month ranking of S2C (themes whose AI concept pages gained attention lost borrowing share over the next year, relative to other themes) is not explained here; the placebo shows it is not built into the measure.

## Files

- data/db/wiki_led/dirs/d1_themes/: ranking_by_k.csv, ranking_same_rows.csv, ranking_pairs_by_k.csv, ranking_placebo.csv, effects_windows.csv, effects_same_tests.csv, effects_monthly_gaps.csv, effects_positive_control.csv, effects_tests_<series>.parquet, checks.json, summary.json
