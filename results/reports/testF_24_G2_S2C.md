# Test F, check G2: borrowing after rises of the AI theme series S2C (real data)

- written 2026-10-21 21:51; Study 3 record `eeeb6c80425a`; bootstrap 2000 resamples, seed 20261013
- donor and placebo-year screen: new+gdelt; desktop flag applied (2,360 rises checked, 0 without desktop data, 126 flagged); run time 514s
- rises: {'total': 2360, 'labelled': 2352, 'quality_flags': {'clean': 2058, 'one_day': 176, 'desktop_only': 86, 'one_day,desktop_only': 40}, 'by_class': {'fading': 1947, 'intermediate': 145, 'sustained': 260}, 'screen_rises': 2810}

## Decision (panel a, rises of 4 weeks or more, mean effect in months 0 to 2, log share; 95% interval)

- narrow, synthetic control: +0.029 [-0.005, +0.063] (+3.0%), 243 tests in 76 themes; interval above 0: no
- narrow, own trend: +0.002 [-0.042, +0.047] (+0.2%), 243 tests in 76 themes; interval above 0: no
- middle, synthetic control: +0.026 [-0.015, +0.068] (+2.6%), 102 tests in 30 themes; interval above 0: no
- middle, own trend: +0.036 [-0.010, +0.076] (+3.6%), 102 tests in 30 themes; interval above 0: no
- both, synthetic control: +0.028 [+0.001, +0.055] (+2.9%), 345 tests in 106 themes; interval above 0: yes
- both, own trend: +0.012 [-0.023, +0.045] (+1.2%), 345 tests in 106 themes; interval above 0: no

## Pooled effects by panel (all formats; months 0 to 2; sc = synthetic control, es = own trend)

| panel | level | duration_class | tests | categories | sc_effect_p_mean | sc_effect_p_ci_low | sc_effect_p_ci_high | es_effect_p_mean | es_effect_p_ci_low | es_effect_p_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | middle | all | 1175 | 82 | 0.002 | -0.008 | 0.013 | -0.006 | -0.021 | 0.007 |
| a | narrow | all | 2286 | 186 | 0.006 | -0.002 | 0.015 | -0.019 | -0.033 | -0.006 |
| a | middle | fading | 991 | 82 | -0.000 | -0.011 | 0.010 | -0.013 | -0.029 | 0.002 |
| a | middle | sustained | 102 | 30 | 0.026 | -0.015 | 0.068 | 0.036 | -0.010 | 0.076 |
| a | narrow | fading | 1927 | 184 | 0.003 | -0.006 | 0.012 | -0.023 | -0.036 | -0.009 |
| a | narrow | sustained | 243 | 76 | 0.029 | -0.005 | 0.063 | 0.002 | -0.042 | 0.047 |
| a | both | all | 3461 | 268 | 0.005 | -0.002 | 0.012 | -0.015 | -0.025 | -0.005 |
| a | both | sustained | 345 | 106 | 0.028 | 0.001 | 0.055 | 0.012 | -0.023 | 0.045 |
| a | both | fading | 2918 | 266 | 0.002 | -0.005 | 0.009 | -0.019 | -0.030 | -0.009 |
| b | middle | all | 958 | 79 | 0.012 | -0.002 | 0.026 | -0.010 | -0.028 | 0.008 |
| b | narrow | all | 1859 | 170 | 0.014 | 0.004 | 0.025 | -0.026 | -0.045 | -0.009 |
| b | middle | fading | 800 | 79 | 0.003 | -0.011 | 0.016 | -0.030 | -0.051 | -0.008 |
| b | middle | sustained | 93 | 30 | 0.082 | 0.022 | 0.143 | 0.103 | 0.023 | 0.185 |
| b | narrow | fading | 1559 | 167 | 0.011 | -0.000 | 0.023 | -0.040 | -0.062 | -0.018 |
| b | narrow | sustained | 199 | 67 | 0.055 | 0.015 | 0.096 | 0.081 | 0.024 | 0.146 |
| b | both | all | 2817 | 249 | 0.014 | 0.005 | 0.021 | -0.021 | -0.035 | -0.008 |
| b | both | sustained | 292 | 97 | 0.064 | 0.031 | 0.100 | 0.088 | 0.042 | 0.138 |
| b | both | fading | 2359 | 246 | 0.008 | -0.000 | 0.017 | -0.036 | -0.053 | -0.021 |
| c | middle | all | 789 | 71 | 0.012 | -0.001 | 0.026 | -0.004 | -0.027 | 0.018 |
| c | narrow | all | 1196 | 128 | 0.004 | -0.009 | 0.017 | -0.049 | -0.077 | -0.024 |
| c | middle | fading | 663 | 71 | 0.007 | -0.008 | 0.023 | -0.015 | -0.044 | 0.012 |
| c | middle | sustained | 72 | 24 | 0.068 | 0.006 | 0.139 | 0.092 | 0.013 | 0.183 |
| c | narrow | fading | 1016 | 122 | 0.002 | -0.012 | 0.016 | -0.054 | -0.088 | -0.026 |
| c | narrow | sustained | 128 | 44 | 0.042 | -0.008 | 0.101 | 0.015 | -0.068 | 0.096 |
| c | both | all | 1985 | 199 | 0.008 | -0.002 | 0.017 | -0.031 | -0.050 | -0.014 |
| c | both | sustained | 200 | 68 | 0.052 | 0.013 | 0.098 | 0.043 | -0.020 | 0.103 |
| c | both | fading | 1679 | 193 | 0.004 | -0.006 | 0.015 | -0.039 | -0.060 | -0.018 |
| chapter6_concept_pages | middle | all | 479 | 56 | 0.033 | 0.015 | 0.052 | 0.010 | -0.014 | 0.031 |
| chapter6_concept_pages | narrow | all | 854 | 142 | 0.033 | 0.016 | 0.051 | -0.004 | -0.024 | 0.018 |
| chapter6_concept_pages | middle | fading | 406 | 55 | 0.026 | 0.004 | 0.049 | 0.001 | -0.027 | 0.024 |
| chapter6_concept_pages | middle | sustained | 56 | 13 | 0.105 | 0.018 | 0.227 | 0.115 | 0.053 | 0.193 |
| chapter6_concept_pages | narrow | fading | 650 | 123 | 0.019 | 0.002 | 0.037 | -0.022 | -0.046 | 0.001 |
| chapter6_concept_pages | narrow | sustained | 121 | 37 | 0.088 | 0.029 | 0.156 | 0.078 | 0.021 | 0.142 |

panel chapter6_concept_pages = the stored Chapter 6 result (hand-checked concept pages), for comparison.

## G4: panel b minus panel c on the same rises and formats (descriptive)

| level | duration_class | tests | categories | d_sc_mean | d_sc_ci_low | d_sc_ci_high | d_es_mean | d_es_ci_low | d_es_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narrow | sustained | 117 | 42 | 0.004 | -0.027 | 0.037 | 0.016 | -0.032 | 0.064 |
| narrow | fading | 945 | 114 | 0.010 | -0.004 | 0.024 | 0.011 | -0.011 | 0.034 |
| narrow | all | 1112 | 120 | 0.010 | -0.002 | 0.022 | 0.015 | -0.003 | 0.034 |
| middle | sustained | 72 | 24 | 0.017 | -0.020 | 0.052 | 0.009 | -0.058 | 0.075 |
| middle | fading | 653 | 71 | 0.002 | -0.011 | 0.016 | -0.011 | -0.035 | 0.009 |
| middle | all | 779 | 71 | 0.006 | -0.005 | 0.017 | -0.003 | -0.023 | 0.014 |
| both | sustained | 189 | 66 | 0.009 | -0.016 | 0.034 | 0.013 | -0.025 | 0.053 |
| both | fading | 1598 | 185 | 0.007 | -0.003 | 0.017 | 0.002 | -0.014 | 0.018 |
| both | all | 1891 | 191 | 0.008 | -0.000 | 0.017 | 0.008 | -0.006 | 0.022 |

## Tests per panel

- panel a: {'rises_tested': 1874, 'tests': 7496, 'tests_ok': 3926, 'formats': ['audiobook', 'ebook', 'librivox', 'print'], 'skips': {'tested': 3926, 'below minimum size': 2746, 'no data': 582, 'too few fit months': 242}, 'single_p_lt_alpha': 117, 'bh_detected': 0}
- panel b: {'rises_tested': 1874, 'tests': 5622, 'tests_ok': 3113, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'tested': 3113, 'below minimum size': 2358, 'too few fit months': 151}, 'single_p_lt_alpha': 129, 'bh_detected': 0}
- panel c: {'rises_tested': 1874, 'tests': 5622, 'tests_ok': 2257, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'below minimum size': 3246, 'tested': 2257, 'too few fit months': 113, 'no data': 6}, 'single_p_lt_alpha': 65, 'bh_detected': 0}
