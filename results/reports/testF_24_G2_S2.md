# Test F, check G2: borrowing after rises of the AI theme series S2 (real data)

- written 2026-10-21 20:21; Study 3 record `eeeb6c80425a`; bootstrap 2000 resamples, seed 20261013
- donor and placebo-year screen: new+gdelt; desktop flag applied (2,944 rises checked, 0 without desktop data, 49 flagged); run time 561s
- rises: {'total': 2944, 'labelled': 2933, 'quality_flags': {'clean': 2819, 'one_day': 76, 'desktop_only': 41, 'one_day,desktop_only': 8}, 'by_class': {'fading': 2165, 'intermediate': 254, 'sustained': 514}, 'screen_rises': 3394}

## Decision (panel a, rises of 4 weeks or more, mean effect in months 0 to 2, log share; 95% interval)

- narrow, synthetic control: +0.015 [-0.005, +0.036] (+1.5%), 570 tests in 127 themes; interval above 0: no
- narrow, own trend: -0.006 [-0.032, +0.018] (-0.6%), 570 tests in 127 themes; interval above 0: no
- middle, synthetic control: +0.026 [-0.009, +0.066] (+2.6%), 223 tests in 50 themes; interval above 0: no
- middle, own trend: +0.009 [-0.035, +0.052] (+0.9%), 223 tests in 50 themes; interval above 0: no
- both, synthetic control: +0.018 [+0.001, +0.035] (+1.8%), 793 tests in 177 themes; interval above 0: yes
- both, own trend: -0.002 [-0.025, +0.019] (-0.2%), 793 tests in 177 themes; interval above 0: no

## Pooled effects by panel (all formats; months 0 to 2; sc = synthetic control, es = own trend)

| panel | level | duration_class | tests | categories | sc_effect_p_mean | sc_effect_p_ci_low | sc_effect_p_ci_high | es_effect_p_mean | es_effect_p_ci_low | es_effect_p_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | middle | all | 1673 | 84 | 0.009 | -0.000 | 0.019 | 0.000 | -0.011 | 0.011 |
| a | narrow | all | 3403 | 197 | 0.006 | -0.001 | 0.013 | -0.011 | -0.020 | -0.002 |
| a | middle | fading | 1278 | 84 | 0.005 | -0.005 | 0.015 | 0.001 | -0.011 | 0.013 |
| a | middle | sustained | 223 | 50 | 0.026 | -0.009 | 0.066 | 0.009 | -0.035 | 0.052 |
| a | narrow | fading | 2535 | 194 | 0.003 | -0.005 | 0.011 | -0.014 | -0.025 | -0.003 |
| a | narrow | sustained | 570 | 127 | 0.015 | -0.005 | 0.036 | -0.006 | -0.032 | 0.018 |
| a | both | all | 5076 | 281 | 0.007 | 0.002 | 0.013 | -0.007 | -0.015 | -0.001 |
| a | both | sustained | 793 | 177 | 0.018 | 0.001 | 0.035 | -0.002 | -0.025 | 0.019 |
| a | both | fading | 3813 | 278 | 0.004 | -0.003 | 0.010 | -0.009 | -0.018 | -0.001 |
| b | middle | all | 1344 | 82 | -0.001 | -0.012 | 0.010 | -0.011 | -0.025 | 0.002 |
| b | narrow | all | 2629 | 181 | 0.002 | -0.008 | 0.012 | -0.031 | -0.046 | -0.017 |
| b | middle | fading | 1012 | 82 | -0.013 | -0.024 | -0.002 | -0.024 | -0.044 | -0.006 |
| b | middle | sustained | 188 | 48 | 0.059 | 0.023 | 0.100 | 0.076 | 0.029 | 0.130 |
| b | narrow | fading | 1943 | 178 | -0.005 | -0.017 | 0.007 | -0.046 | -0.065 | -0.029 |
| b | narrow | sustained | 452 | 113 | 0.028 | 0.003 | 0.056 | 0.021 | -0.013 | 0.056 |
| b | both | all | 3973 | 263 | 0.001 | -0.007 | 0.009 | -0.024 | -0.035 | -0.014 |
| b | both | sustained | 640 | 161 | 0.037 | 0.017 | 0.061 | 0.038 | 0.011 | 0.067 |
| b | both | fading | 2955 | 260 | -0.008 | -0.017 | 0.001 | -0.038 | -0.052 | -0.025 |
| c | middle | all | 1115 | 75 | 0.005 | -0.007 | 0.016 | -0.009 | -0.025 | 0.005 |
| c | narrow | all | 1711 | 140 | 0.005 | -0.007 | 0.015 | -0.034 | -0.049 | -0.018 |
| c | middle | fading | 848 | 75 | -0.003 | -0.017 | 0.010 | -0.011 | -0.035 | 0.009 |
| c | middle | sustained | 153 | 40 | 0.034 | -0.014 | 0.088 | 0.013 | -0.046 | 0.072 |
| c | narrow | fading | 1277 | 132 | -0.002 | -0.015 | 0.011 | -0.047 | -0.069 | -0.028 |
| c | narrow | sustained | 279 | 82 | 0.023 | -0.006 | 0.055 | 0.010 | -0.032 | 0.054 |
| c | both | all | 2826 | 215 | 0.005 | -0.003 | 0.012 | -0.024 | -0.035 | -0.013 |
| c | both | sustained | 432 | 122 | 0.027 | 0.002 | 0.053 | 0.011 | -0.021 | 0.047 |
| c | both | fading | 2125 | 207 | -0.002 | -0.012 | 0.007 | -0.033 | -0.049 | -0.017 |
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
| narrow | sustained | 262 | 76 | -0.000 | -0.019 | 0.020 | 0.008 | -0.027 | 0.040 |
| narrow | fading | 1185 | 126 | 0.001 | -0.010 | 0.012 | 0.007 | -0.006 | 0.021 |
| narrow | all | 1584 | 133 | -0.002 | -0.011 | 0.008 | 0.006 | -0.005 | 0.017 |
| middle | sustained | 152 | 40 | 0.018 | -0.009 | 0.045 | 0.056 | 0.018 | 0.100 |
| middle | fading | 833 | 75 | -0.011 | -0.023 | -0.001 | -0.015 | -0.033 | 0.001 |
| middle | all | 1097 | 75 | -0.006 | -0.015 | 0.003 | -0.001 | -0.013 | 0.011 |
| both | sustained | 414 | 116 | 0.007 | -0.009 | 0.023 | 0.026 | -0.001 | 0.052 |
| both | fading | 2018 | 201 | -0.004 | -0.012 | 0.003 | -0.002 | -0.013 | 0.008 |
| both | all | 2681 | 208 | -0.003 | -0.010 | 0.003 | 0.003 | -0.004 | 0.011 |

## Tests per panel

- panel a: {'rises_tested': 2559, 'tests': 10236, 'tests_ok': 5386, 'formats': ['audiobook', 'ebook', 'librivox', 'print'], 'skips': {'tested': 5386, 'below minimum size': 3731, 'no data': 785, 'too few fit months': 334}, 'single_p_lt_alpha': 161, 'bh_detected': 0}
- panel b: {'rises_tested': 2559, 'tests': 7677, 'tests_ok': 4158, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'tested': 4158, 'below minimum size': 3308, 'too few fit months': 210, 'too few donors': 1}, 'single_p_lt_alpha': 118, 'bh_detected': 0}
- panel c: {'rises_tested': 2559, 'tests': 7677, 'tests_ok': 2945, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'below minimum size': 4582, 'tested': 2945, 'too few fit months': 150}, 'single_p_lt_alpha': 77, 'bh_detected': 0}
