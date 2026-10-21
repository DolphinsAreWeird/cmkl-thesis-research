# Test F, check G2: borrowing after rises of the AI theme series S2C (real data) (robustness run with flagged rises)

- written 2026-10-21 22:01; Study 3 record `eeeb6c80425a`; bootstrap 2000 resamples, seed 20261013
- donor and placebo-year screen: new+gdelt; desktop flag applied (2,360 rises checked, 0 without desktop data, 126 flagged); run time 634s
- rises: {'total': 2360, 'labelled': 2352, 'quality_flags': {'clean': 2058, 'one_day': 176, 'desktop_only': 86, 'one_day,desktop_only': 40}, 'by_class': {'fading': 1947, 'intermediate': 145, 'sustained': 260}, 'screen_rises': 2810}

## Decision (panel a, rises of 4 weeks or more, mean effect in months 0 to 2, log share; 95% interval)

- narrow, synthetic control: +0.034 [+0.001, +0.073] (+3.5%), 266 tests in 82 themes; interval above 0: yes
- narrow, own trend: -0.001 [-0.045, +0.044] (-0.1%), 266 tests in 82 themes; interval above 0: no
- middle, synthetic control: +0.029 [-0.012, +0.077] (+3.0%), 119 tests in 33 themes; interval above 0: no
- middle, own trend: +0.027 [-0.017, +0.078] (+2.8%), 119 tests in 33 themes; interval above 0: no
- both, synthetic control: +0.033 [+0.006, +0.062] (+3.3%), 385 tests in 115 themes; interval above 0: yes
- both, own trend: +0.008 [-0.026, +0.042] (+0.8%), 385 tests in 115 themes; interval above 0: no

## Pooled effects by panel (all formats; months 0 to 2; sc = synthetic control, es = own trend)

| panel | level | duration_class | tests | categories | sc_effect_p_mean | sc_effect_p_ci_low | sc_effect_p_ci_high | es_effect_p_mean | es_effect_p_ci_low | es_effect_p_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | middle | all | 1299 | 83 | 0.002 | -0.007 | 0.013 | -0.007 | -0.020 | 0.007 |
| a | narrow | all | 2598 | 190 | 0.006 | -0.002 | 0.014 | -0.019 | -0.031 | -0.007 |
| a | middle | fading | 1094 | 83 | -0.001 | -0.011 | 0.010 | -0.013 | -0.028 | 0.002 |
| a | middle | sustained | 119 | 33 | 0.029 | -0.012 | 0.077 | 0.027 | -0.017 | 0.078 |
| a | narrow | fading | 2202 | 188 | 0.002 | -0.006 | 0.010 | -0.022 | -0.035 | -0.010 |
| a | narrow | sustained | 266 | 82 | 0.034 | 0.001 | 0.073 | -0.001 | -0.045 | 0.044 |
| a | both | all | 3897 | 273 | 0.005 | -0.001 | 0.011 | -0.015 | -0.025 | -0.006 |
| a | both | sustained | 385 | 115 | 0.033 | 0.006 | 0.062 | 0.008 | -0.026 | 0.042 |
| a | both | fading | 3296 | 271 | 0.001 | -0.005 | 0.008 | -0.019 | -0.030 | -0.010 |
| b | middle | all | 1049 | 80 | 0.013 | -0.001 | 0.026 | -0.009 | -0.027 | 0.010 |
| b | narrow | all | 2094 | 172 | 0.011 | 0.002 | 0.020 | -0.030 | -0.048 | -0.014 |
| b | middle | fading | 878 | 80 | 0.004 | -0.010 | 0.017 | -0.026 | -0.048 | -0.005 |
| b | middle | sustained | 103 | 31 | 0.078 | 0.019 | 0.145 | 0.082 | 0.005 | 0.164 |
| b | narrow | fading | 1766 | 169 | 0.008 | -0.003 | 0.018 | -0.042 | -0.062 | -0.023 |
| b | narrow | sustained | 217 | 71 | 0.055 | 0.018 | 0.097 | 0.066 | 0.008 | 0.126 |
| b | both | all | 3143 | 252 | 0.012 | 0.004 | 0.020 | -0.023 | -0.036 | -0.011 |
| b | both | sustained | 320 | 102 | 0.062 | 0.031 | 0.096 | 0.071 | 0.024 | 0.118 |
| b | both | fading | 2644 | 249 | 0.006 | -0.002 | 0.015 | -0.037 | -0.052 | -0.022 |
| c | middle | all | 868 | 72 | 0.009 | -0.004 | 0.021 | -0.008 | -0.028 | 0.013 |
| c | narrow | all | 1347 | 132 | 0.001 | -0.012 | 0.013 | -0.052 | -0.078 | -0.029 |
| c | middle | fading | 731 | 72 | 0.005 | -0.009 | 0.018 | -0.015 | -0.041 | 0.009 |
| c | middle | sustained | 80 | 25 | 0.047 | -0.014 | 0.121 | 0.052 | -0.031 | 0.149 |
| c | narrow | fading | 1154 | 128 | -0.001 | -0.015 | 0.012 | -0.055 | -0.082 | -0.029 |
| c | narrow | sustained | 136 | 46 | 0.034 | -0.016 | 0.090 | -0.004 | -0.084 | 0.074 |
| c | both | all | 2215 | 204 | 0.004 | -0.005 | 0.013 | -0.035 | -0.051 | -0.019 |
| c | both | sustained | 216 | 71 | 0.039 | -0.003 | 0.086 | 0.017 | -0.041 | 0.078 |
| c | both | fading | 1885 | 200 | 0.002 | -0.008 | 0.011 | -0.039 | -0.060 | -0.021 |
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
| narrow | sustained | 125 | 44 | 0.010 | -0.023 | 0.041 | 0.026 | -0.024 | 0.079 |
| narrow | fading | 1077 | 120 | 0.010 | -0.002 | 0.022 | 0.012 | -0.006 | 0.030 |
| narrow | all | 1257 | 124 | 0.010 | -0.001 | 0.022 | 0.017 | 0.002 | 0.034 |
| middle | sustained | 80 | 25 | 0.023 | -0.011 | 0.055 | 0.023 | -0.041 | 0.081 |
| middle | fading | 718 | 72 | 0.004 | -0.008 | 0.018 | -0.008 | -0.029 | 0.010 |
| middle | all | 855 | 72 | 0.008 | -0.001 | 0.019 | 0.000 | -0.017 | 0.017 |
| both | sustained | 205 | 69 | 0.015 | -0.008 | 0.037 | 0.024 | -0.015 | 0.064 |
| both | fading | 1795 | 192 | 0.008 | -0.001 | 0.016 | 0.004 | -0.010 | 0.017 |
| both | all | 2112 | 196 | 0.010 | 0.002 | 0.018 | 0.010 | -0.002 | 0.022 |

## Tests per panel

- panel a: {'rises_tested': 2109, 'tests': 8436, 'tests_ok': 4373, 'formats': ['audiobook', 'ebook', 'librivox', 'print'], 'skips': {'tested': 4373, 'below minimum size': 3152, 'no data': 656, 'too few fit months': 255}, 'single_p_lt_alpha': 138, 'bh_detected': 0}
- panel b: {'rises_tested': 2109, 'tests': 6327, 'tests_ok': 3446, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'tested': 3446, 'below minimum size': 2721, 'too few fit months': 160}, 'single_p_lt_alpha': 137, 'bh_detected': 0}
- panel c: {'rises_tested': 2109, 'tests': 6327, 'tests_ok': 2495, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'below minimum size': 3705, 'tested': 2495, 'too few fit months': 121, 'no data': 6}, 'single_p_lt_alpha': 73, 'bh_detected': 0}
