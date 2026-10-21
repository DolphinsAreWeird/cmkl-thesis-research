# Test F, check G2: borrowing after rises of the AI theme series S2 (real data) (robustness run with flagged rises)

- written 2026-10-21 20:31; Study 3 record `eeeb6c80425a`; bootstrap 2000 resamples, seed 20261013
- donor and placebo-year screen: new+gdelt; desktop flag applied (2,944 rises checked, 0 without desktop data, 49 flagged); run time 595s
- rises: {'total': 2944, 'labelled': 2933, 'quality_flags': {'clean': 2819, 'one_day': 76, 'desktop_only': 41, 'one_day,desktop_only': 8}, 'by_class': {'fading': 2165, 'intermediate': 254, 'sustained': 514}, 'screen_rises': 3394}

## Decision (panel a, rises of 4 weeks or more, mean effect in months 0 to 2, log share; 95% interval)

- narrow, synthetic control: +0.021 [+0.001, +0.042] (+2.1%), 587 tests in 132 themes; interval above 0: yes
- narrow, own trend: -0.001 [-0.027, +0.025] (-0.1%), 587 tests in 132 themes; interval above 0: no
- middle, synthetic control: +0.028 [-0.006, +0.065] (+2.8%), 227 tests in 51 themes; interval above 0: no
- middle, own trend: +0.013 [-0.029, +0.057] (+1.3%), 227 tests in 51 themes; interval above 0: no
- both, synthetic control: +0.023 [+0.005, +0.041] (+2.3%), 814 tests in 183 themes; interval above 0: yes
- both, own trend: +0.003 [-0.020, +0.024] (+0.3%), 814 tests in 183 themes; interval above 0: no

## Pooled effects by panel (all formats; months 0 to 2; sc = synthetic control, es = own trend)

| panel | level | duration_class | tests | categories | sc_effect_p_mean | sc_effect_p_ci_low | sc_effect_p_ci_high | es_effect_p_mean | es_effect_p_ci_low | es_effect_p_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | middle | all | 1733 | 84 | 0.009 | -0.001 | 0.019 | -0.000 | -0.012 | 0.010 |
| a | narrow | all | 3508 | 197 | 0.008 | 0.001 | 0.014 | -0.010 | -0.019 | -0.001 |
| a | middle | fading | 1327 | 84 | 0.004 | -0.005 | 0.015 | -0.000 | -0.012 | 0.012 |
| a | middle | sustained | 227 | 51 | 0.028 | -0.006 | 0.065 | 0.013 | -0.029 | 0.057 |
| a | narrow | fading | 2612 | 194 | 0.004 | -0.004 | 0.012 | -0.013 | -0.024 | -0.002 |
| a | narrow | sustained | 587 | 132 | 0.021 | 0.001 | 0.042 | -0.001 | -0.027 | 0.025 |
| a | both | all | 5241 | 281 | 0.008 | 0.003 | 0.014 | -0.007 | -0.014 | -0.000 |
| a | both | sustained | 814 | 183 | 0.023 | 0.005 | 0.041 | 0.003 | -0.020 | 0.024 |
| a | both | fading | 3939 | 278 | 0.004 | -0.002 | 0.010 | -0.009 | -0.017 | -0.000 |
| b | middle | all | 1391 | 82 | -0.002 | -0.013 | 0.008 | -0.012 | -0.026 | 0.001 |
| b | narrow | all | 2700 | 181 | 0.002 | -0.008 | 0.012 | -0.031 | -0.046 | -0.018 |
| b | middle | fading | 1052 | 82 | -0.014 | -0.025 | -0.004 | -0.026 | -0.045 | -0.008 |
| b | middle | sustained | 191 | 49 | 0.058 | 0.023 | 0.098 | 0.077 | 0.032 | 0.130 |
| b | narrow | fading | 1995 | 178 | -0.003 | -0.015 | 0.009 | -0.045 | -0.063 | -0.028 |
| b | narrow | sustained | 463 | 116 | 0.028 | 0.004 | 0.055 | 0.020 | -0.013 | 0.055 |
| b | both | all | 4091 | 263 | 0.001 | -0.006 | 0.008 | -0.025 | -0.035 | -0.014 |
| b | both | sustained | 654 | 165 | 0.037 | 0.017 | 0.059 | 0.037 | 0.011 | 0.065 |
| b | both | fading | 3047 | 260 | -0.007 | -0.016 | 0.002 | -0.038 | -0.051 | -0.025 |
| c | middle | all | 1149 | 75 | 0.003 | -0.009 | 0.014 | -0.010 | -0.025 | 0.004 |
| c | narrow | all | 1756 | 140 | 0.005 | -0.006 | 0.014 | -0.034 | -0.049 | -0.020 |
| c | middle | fading | 876 | 75 | -0.005 | -0.019 | 0.007 | -0.011 | -0.034 | 0.009 |
| c | middle | sustained | 156 | 41 | 0.032 | -0.014 | 0.080 | 0.014 | -0.040 | 0.072 |
| c | narrow | fading | 1310 | 134 | -0.002 | -0.015 | 0.010 | -0.048 | -0.068 | -0.027 |
| c | narrow | sustained | 287 | 84 | 0.024 | -0.005 | 0.054 | 0.011 | -0.028 | 0.054 |
| c | both | all | 2905 | 215 | 0.004 | -0.004 | 0.011 | -0.024 | -0.035 | -0.014 |
| c | both | sustained | 443 | 125 | 0.026 | 0.002 | 0.053 | 0.012 | -0.020 | 0.048 |
| c | both | fading | 2186 | 209 | -0.003 | -0.014 | 0.006 | -0.033 | -0.049 | -0.018 |
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
| narrow | sustained | 269 | 77 | -0.001 | -0.020 | 0.019 | 0.005 | -0.026 | 0.036 |
| narrow | fading | 1212 | 127 | 0.001 | -0.010 | 0.012 | 0.007 | -0.005 | 0.021 |
| narrow | all | 1622 | 133 | -0.002 | -0.012 | 0.007 | 0.005 | -0.006 | 0.016 |
| middle | sustained | 155 | 41 | 0.019 | -0.006 | 0.045 | 0.057 | 0.016 | 0.100 |
| middle | fading | 859 | 75 | -0.010 | -0.021 | -0.001 | -0.015 | -0.032 | 0.001 |
| middle | all | 1129 | 75 | -0.005 | -0.014 | 0.003 | -0.001 | -0.013 | 0.012 |
| both | sustained | 424 | 118 | 0.007 | -0.009 | 0.023 | 0.024 | -0.001 | 0.050 |
| both | fading | 2071 | 202 | -0.004 | -0.012 | 0.004 | -0.002 | -0.012 | 0.008 |
| both | all | 2751 | 208 | -0.003 | -0.010 | 0.003 | 0.003 | -0.005 | 0.011 |

## Tests per panel

- panel a: {'rises_tested': 2658, 'tests': 10632, 'tests_ok': 5561, 'formats': ['audiobook', 'ebook', 'librivox', 'print'], 'skips': {'tested': 5561, 'below minimum size': 3914, 'no data': 814, 'too few fit months': 343}, 'single_p_lt_alpha': 166, 'bh_detected': 0}
- panel b: {'rises_tested': 2658, 'tests': 7974, 'tests_ok': 4281, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'tested': 4281, 'below minimum size': 3482, 'too few fit months': 210, 'too few donors': 1}, 'single_p_lt_alpha': 120, 'bh_detected': 0}
- panel c: {'rises_tested': 2658, 'tests': 7974, 'tests_ok': 3029, 'formats': ['audiobook', 'ebook', 'print'], 'skips': {'below minimum size': 4795, 'tested': 3029, 'too few fit months': 150}, 'single_p_lt_alpha': 77, 'bh_detected': 0}
