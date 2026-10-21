# Test F, check G3: forecasts with the AI theme series (real data)

- written 2026-10-21 20:31; main rows 36,081 (510 series, 88 months); bootstrap 2000 draws

## Decision
- Chronos-2 + S2 against Chronos-2 alone: MAE ratio 0.9979 [0.9958, 0.9999] (-0.21%); interval below 1: yes

## Accuracy and rank correlation (AvgRelMAE against naive with the category bootstrap; rho of forecast and actual change)

| pipeline | AvgRelMAE | ci_lo | ci_hi | share_beats_naive | rho | rho_lo | rho_hi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| naive | 1.0000 | 1.0000 | 1.0000 | 0.0000 |  |  |  |
| chronos2 | 0.9200 | 0.9001 | 0.9375 | 0.6176 | 0.3079 | 0.2744 | 0.3396 |
| chronos2_cur | 0.9143 | 0.8948 | 0.9315 | 0.6294 | 0.3190 | 0.2829 | 0.3522 |
| chronos2_nli | 0.9182 | 0.8984 | 0.9356 | 0.6333 | 0.3162 | 0.2807 | 0.3486 |
| chronos2_ais2 | 0.9181 | 0.8984 | 0.9357 | 0.6216 | 0.3172 | 0.2836 | 0.3490 |
| chronos2_ais1 | 0.9180 | 0.8981 | 0.9353 | 0.6176 | 0.3167 | 0.2806 | 0.3503 |

## Paired comparisons (MAE ratio other / base by series; rho difference)

| base | other | mae_ratio | mae_lo | mae_hi | share_series_better | rho_diff | rho_diff_lo | rho_diff_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2 | chronos2_ais2 | 0.9979 | 0.9958 | 0.9999 | 0.5314 | 0.0093 | 0.0041 | 0.0151 |
| chronos2 | chronos2_ais1 | 0.9978 | 0.9959 | 0.9998 | 0.5490 | 0.0089 | 0.0032 | 0.0146 |
| chronos2_cur | chronos2_ais2 | 1.0042 | 1.0020 | 1.0062 | 0.4431 | -0.0018 | -0.0064 | 0.0032 |
| chronos2_nli | chronos2_ais2 | 0.9999 | 0.9981 | 1.0018 | 0.5255 | 0.0010 | -0.0030 | 0.0051 |
| chronos2_cur | chronos2_ais1 | 1.0040 | 1.0019 | 1.0060 | 0.4000 | -0.0023 | -0.0066 | 0.0019 |
| chronos2_nli | chronos2_ais1 | 0.9998 | 0.9982 | 1.0015 | 0.5000 | 0.0006 | -0.0026 | 0.0038 |
| chronos2_ais1 | chronos2_ais2 | 1.0001 | 0.9988 | 1.0015 | 0.5098 | 0.0004 | -0.0025 | 0.0036 |
| chronos2 | chronos2_cur | 0.9938 | 0.9916 | 0.9959 | 0.6157 | 0.0112 | 0.0041 | 0.0185 |
| chronos2 | chronos2_nli | 0.9980 | 0.9960 | 1.0001 | 0.5275 | 0.0083 | 0.0027 | 0.0142 |

## Wikipedia-only ranking, no fitting (the Test C measure)

| series | rho | lo | hi | groups | rows_with_value |
| --- | --- | --- | --- | --- | --- |
| S2 (AI pages) | 0.0085 | -0.0073 | 0.0231 | 308 | 1.0000 |
| S1 (AI pages, top-500 days) | 0.0041 | -0.0104 | 0.0189 | 308 | 0.8088 |
| concept pages | 0.0260 | 0.0085 | 0.0424 | 308 | 1.0000 |
| zero-shot routing | 0.0016 | -0.0123 | 0.0157 | 308 | 0.5708 |
| embedding routing | 0.0149 | 0.0014 | 0.0284 | 308 | 0.2232 |

Paired differences (other minus base):
- S2 (AI pages) minus concept pages: -0.0175 [-0.0371, +0.0032]
- S2 (AI pages) minus zero-shot routing: +0.0069 [-0.0102, +0.0244]
- S2 (AI pages) minus embedding routing: -0.0063 [-0.0253, +0.0123]
- S2 (AI pages) minus S1 (AI pages, top-500 days): +0.0045 [-0.0071, +0.0153]

## G4: the same ranking on panels a, b, c (36,081 common rows)

| series | panel | rows | rho | lo | hi | groups | rows_with_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S2 (AI pages) | a | 36081 | 0.0085 | -0.0073 | 0.0231 | 308 | 1.0000 |
| S2 (AI pages) | b | 36081 | 0.0008 | -0.0163 | 0.0177 | 308 | 1.0000 |
| S2 (AI pages) | c | 36081 | 0.0054 | -0.0073 | 0.0180 | 308 | 1.0000 |
| S1 (AI pages, top-500 days) | a | 36081 | 0.0041 | -0.0104 | 0.0189 | 308 | 0.8088 |
| S1 (AI pages, top-500 days) | b | 36081 | 0.0049 | -0.0103 | 0.0203 | 308 | 0.8088 |
| S1 (AI pages, top-500 days) | c | 36081 | 0.0063 | -0.0062 | 0.0183 | 308 | 0.8088 |

Paired differences:
- S2 (AI pages): panel b minus panel c: -0.0046 [-0.0188, +0.0093]
- S2 (AI pages): panel b minus panel a: -0.0077 [-0.0212, +0.0062]
- S2 (AI pages): panel c minus panel a: -0.0032 [-0.0126, +0.0072]
- S1 (AI pages, top-500 days): panel b minus panel c: -0.0014 [-0.0129, +0.0102]
- S1 (AI pages, top-500 days): panel b minus panel a: +0.0009 [-0.0117, +0.0138]
- S1 (AI pages, top-500 days): panel c minus panel a: +0.0022 [-0.0063, +0.0112]

## Chronos-2 run time on this Mac

- chronos2_ais1: {'tasks': 36081, 'seconds': 454.6, 'tasks_per_s': 79.4, 'full_run_estimate_min': 7.6, 'mock': False, 'when': '2026-10-21 19:00'}
- chronos2_ais2: {'tasks': 36081, 'seconds': 436.0, 'tasks_per_s': 82.7, 'full_run_estimate_min': 7.3, 'mock': False, 'when': '2026-10-21 19:50'}
