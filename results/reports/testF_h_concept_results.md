# Test F, addendum h: the AI's concept pages only (real data)

- written 2026-10-21 22:01; record prereg/addenda_wiki_led/2026-10-21_h_concept_pages.json (SHA-256 0b3ad4aaf7f1..., fixed 21 Oct 21:07, public on GitHub 21:08, before any result)
- series S2C: 6,241 concept pages with a theme of confidence 2 or 3, 9,541 page-theme pairs, complete: True

## H1: borrowing after lasting rises of the concept-page series (decision fixed in advance)

- panel a, both levels pooled, synthetic control, months 0 to 2, rises of 4 weeks or more: 0.028 [0.001, 0.055] (+2.9%), 345 tests in 106 themes; interval above 0: yes
- own trend: 0.012 [-0.023, 0.045] (+1.2%)
- close to the hand-checked level (interval contains 0.088): no
- with flagged rises included: 0.033 [0.006, 0.062] (+3.3%)

## Beside S2 (all AI pages) and Chapter 6 (hand-checked concept pages), rises of 4 weeks or more

| series | panel | level | tests | themes | synthetic control | own trend |
| --- | --- | --- | --- | --- | --- | --- |
| S2C concept pages | a | both | 345 | 106 | 0.028 [0.001, 0.055] | 0.012 [-0.023, 0.045] |
| S2C concept pages | a | middle | 102 | 30 | 0.026 [-0.015, 0.068] | 0.036 [-0.010, 0.076] |
| S2C concept pages | a | narrow | 243 | 76 | 0.029 [-0.005, 0.063] | 0.002 [-0.042, 0.047] |
| S2C concept pages | b | both | 292 | 97 | 0.064 [0.031, 0.100] | 0.088 [0.042, 0.138] |
| S2C concept pages | b | middle | 93 | 30 | 0.082 [0.022, 0.143] | 0.103 [0.023, 0.185] |
| S2C concept pages | b | narrow | 199 | 67 | 0.055 [0.015, 0.096] | 0.081 [0.024, 0.146] |
| S2C concept pages | c | both | 200 | 68 | 0.052 [0.013, 0.098] | 0.043 [-0.020, 0.103] |
| S2C concept pages | c | middle | 72 | 24 | 0.068 [0.006, 0.139] | 0.092 [0.013, 0.183] |
| S2C concept pages | c | narrow | 128 | 44 | 0.042 [-0.008, 0.101] | 0.015 [-0.068, 0.096] |
| Chapter 6 concept pages | a | middle | 56 | 13 | 0.105 [0.018, 0.227] | 0.115 [0.053, 0.193] |
| Chapter 6 concept pages | a | narrow | 121 | 37 | 0.088 [0.029, 0.156] | 0.078 [0.021, 0.142] |
| S2 all pages | a | both | 793 | 177 | 0.018 [0.001, 0.035] | -0.002 [-0.025, 0.019] |
| S2 all pages | a | middle | 223 | 50 | 0.026 [-0.009, 0.066] | 0.009 [-0.035, 0.052] |
| S2 all pages | a | narrow | 570 | 127 | 0.015 [-0.005, 0.036] | -0.006 [-0.032, 0.018] |
| S2 all pages | b | both | 640 | 161 | 0.037 [0.017, 0.061] | 0.038 [0.011, 0.067] |
| S2 all pages | b | middle | 188 | 48 | 0.059 [0.023, 0.100] | 0.076 [0.029, 0.130] |
| S2 all pages | b | narrow | 452 | 113 | 0.028 [0.003, 0.056] | 0.021 [-0.013, 0.056] |
| S2 all pages | c | both | 432 | 122 | 0.027 [0.002, 0.053] | 0.011 [-0.021, 0.047] |
| S2 all pages | c | middle | 153 | 40 | 0.034 [-0.014, 0.088] | 0.013 [-0.046, 0.072] |
| S2 all pages | c | narrow | 279 | 82 | 0.023 [-0.006, 0.055] | 0.010 [-0.032, 0.054] |

Rises of 1 or 2 weeks (S2C):

- panel a, both: synthetic control 0.002 [-0.005, 0.009], own trend -0.019 [-0.030, -0.009] (2918 tests)
- panel a, middle: synthetic control -0.000 [-0.011, 0.010], own trend -0.013 [-0.029, 0.002] (991 tests)
- panel a, narrow: synthetic control 0.003 [-0.006, 0.012], own trend -0.023 [-0.036, -0.009] (1927 tests)
- panel b, both: synthetic control 0.008 [-0.000, 0.017], own trend -0.036 [-0.053, -0.021] (2359 tests)
- panel b, middle: synthetic control 0.003 [-0.011, 0.016], own trend -0.030 [-0.051, -0.008] (800 tests)
- panel b, narrow: synthetic control 0.011 [-0.000, 0.023], own trend -0.040 [-0.062, -0.018] (1559 tests)
- panel c, both: synthetic control 0.004 [-0.006, 0.015], own trend -0.039 [-0.060, -0.018] (1679 tests)
- panel c, middle: synthetic control 0.007 [-0.008, 0.023], own trend -0.015 [-0.044, 0.012] (663 tests)
- panel c, narrow: synthetic control 0.002 [-0.012, 0.016], own trend -0.054 [-0.088, -0.026] (1016 tests)
- panel a: 1,874 rises tested in 7,496 tests (3,926 with a synthetic control); single one-sided p < 0.05: 117; Benjamini-Hochberg q < 0.10: 0
- panel b: 1,874 rises tested in 5,622 tests (3,113 with a synthetic control); single one-sided p < 0.05: 129; Benjamini-Hochberg q < 0.10: 0
- panel c: 1,874 rises tested in 5,622 tests (2,257 with a synthetic control); single one-sided p < 0.05: 65; Benjamini-Hochberg q < 0.10: 0

## H2: forecasts (descriptive)

| pipeline | AvgRelMAE | rank correlation |
| --- | --- | --- |
| naive | 1.0000 [1.0000, 1.0000] | nan |
| chronos2 | 0.9200 [0.9001, 0.9375] | 0.3079 |
| chronos2_cur | 0.9143 [0.8948, 0.9315] | 0.3190 |
| chronos2_nli | 0.9182 [0.8984, 0.9356] | 0.3162 |
| chronos2_ais2 | 0.9181 [0.8984, 0.9357] | 0.3172 |
| chronos2_aic2 | 0.9169 [0.8972, 0.9343] | 0.3162 |

Paired (MAE ratio other / base; below 1 = the other is better):
- chronos2_aic2 against chronos2: 0.9966 [0.9943, 0.9991] (-0.34%)
- chronos2_aic2 against chronos2_cur: 1.0028 [1.0008, 1.0048] (+0.28%)
- chronos2_aic2 against chronos2_ais2: 0.9987 [0.9969, 1.0005] (-0.13%)

Wikipedia-only ranking, no fitting (the Test C measure):
- S2C (AI concept pages): -0.0062 [-0.0223, 0.0097]
- S2 (AI pages): 0.0085 [-0.0073, 0.0231]
- concept pages: 0.0260 [0.0085, 0.0424]
- S2C (AI concept pages) minus concept pages: -0.0322 [-0.0511, -0.0120]
- S2C (AI concept pages) minus S2 (AI pages): -0.0147 [-0.0323, +0.0031]
