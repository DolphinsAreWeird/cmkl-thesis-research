# Study 3b value-level calibration with screened placebos

- step: 16
- written: 2026-10-14 05:31:32
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json, 2026-10-13_a_implementation_choices.json, 2026-10-14_b_backlist_robustness.json

## What was done
- Value-level one-sided rank p recomputed against screened placebo values: feasible fit at the same month 0, other parent, no interest shift start (any source, any class) in months -6 to +6, and an interest series exists for the value (Wikipedia or GDELT weekly value series: 604 of 28,464 values in the panel have one). Same as `p_cat_p_screened` of step 12. NOT IN RECORD: the exact screen (the README and addendum a only say "placebo values that have a series"); the record's shift screen was kept on top.
- Step 11 draws reused (same units, band edges and seed): 800 units; the recomputed record p equals the stored step 11 p for 100.0% of rows (a check of this code).
- NOT IN RECORD: an extended lift-0 calibration, 2000 draws per band (seed 20261014), because 200 draws only fix a rate to about 3 points.
- run time 11s, one process.

## Lift-0 false-positive rate (share of placebo units with one-sided p < 0.05; 5% expected)

### Step 11 draws (200 per band), with 95% Wilson intervals

| pool | band | draws | detected | rate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| record pool (all values, recomputed) | 1 | 200 | 5 | 0.025 | 0.011 | 0.057 |
| record pool (all values, recomputed) | 2 | 200 | 4 | 0.020 | 0.008 | 0.050 |
| record pool (all values, recomputed) | 3 | 200 | 10 | 0.050 | 0.027 | 0.090 |
| record pool (all values, recomputed) | 4 | 200 | 19 | 0.095 | 0.062 | 0.144 |
| record pool, units with an interest series | 1 | 2 | 1 | 0.500 | 0.095 | 0.905 |
| record pool, units with an interest series | 2 | 1 | 0 | 0.000 | 0.000 | 0.793 |
| record pool, units with an interest series | 3 | 2 | 0 | 0.000 | 0.000 | 0.658 |
| record pool, units with an interest series | 4 | 14 | 0 | 0.000 | 0.000 | 0.215 |
| screened pool | 1 | 200 | 1 | 0.005 | 0.001 | 0.028 |
| screened pool | 2 | 200 | 0 | 0.000 | 0.000 | 0.019 |
| screened pool | 3 | 200 | 1 | 0.005 | 0.001 | 0.028 |
| screened pool | 4 | 200 | 7 | 0.035 | 0.017 | 0.070 |
| screened pool, units with an interest series | 1 | 2 | 0 | 0.000 | 0.000 | 0.658 |
| screened pool, units with an interest series | 2 | 1 | 0 | 0.000 | 0.000 | 0.793 |
| screened pool, units with an interest series | 3 | 2 | 0 | 0.000 | 0.000 | 0.658 |
| screened pool, units with an interest series | 4 | 14 | 0 | 0.000 | 0.000 | 0.215 |

### Extended calibration (2000 draws per band)

| pool | band | draws | detected | rate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| record pool | 1 | 2000 | 35 | 0.018 | 0.013 | 0.024 |
| record pool | 2 | 2000 | 70 | 0.035 | 0.028 | 0.044 |
| record pool | 3 | 2000 | 100 | 0.050 | 0.041 | 0.060 |
| record pool | 4 | 2000 | 211 | 0.105 | 0.093 | 0.120 |
| record pool, units with a series | 1 | 11 | 0 | 0.000 | 0.000 | 0.259 |
| record pool, units with a series | 2 | 10 | 1 | 0.100 | 0.018 | 0.404 |
| record pool, units with a series | 3 | 20 | 4 | 0.200 | 0.081 | 0.416 |
| record pool, units with a series | 4 | 165 | 37 | 0.224 | 0.167 | 0.294 |
| screened pool | 1 | 2000 | 7 | 0.004 | 0.002 | 0.007 |
| screened pool | 2 | 2000 | 14 | 0.007 | 0.004 | 0.012 |
| screened pool | 3 | 2000 | 21 | 0.011 | 0.007 | 0.016 |
| screened pool | 4 | 2000 | 72 | 0.036 | 0.029 | 0.045 |
| screened pool, units with a series | 1 | 11 | 0 | 0.000 | 0.000 | 0.259 |
| screened pool, units with a series | 2 | 10 | 0 | 0.000 | -0.000 | 0.278 |
| screened pool, units with a series | 3 | 20 | 0 | 0.000 | -0.000 | 0.161 |
| screened pool, units with a series | 4 | 165 | 10 | 0.061 | 0.033 | 0.108 |
| screened pool, units without a series | 1 | 1989 | 7 | 0.004 | 0.002 | 0.007 |
| screened pool, units without a series | 2 | 1990 | 14 | 0.007 | 0.004 | 0.012 |
| screened pool, units without a series | 3 | 1980 | 21 | 0.011 | 0.007 | 0.016 |
| screened pool, units without a series | 4 | 1835 | 62 | 0.034 | 0.026 | 0.043 |

Units in the extended draws:

| band | units | with_series | median_pool_all | median_pool_screened |
| --- | --- | --- | --- | --- |
| 1 | 2000 | 11 | 16170.500 | 386.000 |
| 2 | 2000 | 10 | 16171.500 | 391.000 |
| 3 | 2000 | 20 | 16146.500 | 404.000 |
| 4 | 2000 | 165 | 16176.000 | 405.000 |

### Power with the screened pool, step 11 draws (detection rate at each lift)

Screened pool:

| band | 0.0 | 0.1 | 0.2 | 0.3 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.005 | 0.005 | 0.005 | 0.010 | 0.010 | 0.010 |
| 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.025 |
| 3 | 0.005 | 0.005 | 0.010 | 0.020 | 0.030 | 0.090 |
| 4 | 0.035 | 0.075 | 0.105 | 0.115 | 0.220 | 0.405 |

Record pool (recomputed, equals step 11):

| band | 0.0 | 0.1 | 0.2 | 0.3 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.025 | 0.030 | 0.035 | 0.035 | 0.035 | 0.065 |
| 2 | 0.020 | 0.020 | 0.030 | 0.030 | 0.060 | 0.110 |
| 3 | 0.050 | 0.070 | 0.105 | 0.150 | 0.195 | 0.355 |
| 4 | 0.095 | 0.145 | 0.220 | 0.275 | 0.410 | 0.570 |

## Value-level shift tests (step 12, non-sparse; main and seasonal families)

| analysis | tests | p_record_below_005 | share_record | p_screened_below_005 | share_screened | both | bh_record | bh_screened | bh_both | median_placebos_record | median_placebos_screened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | 1581 | 295 | 0.187 | 131 | 0.083 | 131 | 11 | 0 | 0 | 16241.000 | 367.000 |
| seasonal | 245 | 38 | 0.155 | 12 | 0.049 | 12 | 1 | 0 | 0 | 16267.000 | 374.000 |

By source:

| analysis | source | tests | p_record_below_005 | p_screened_below_005 | bh_screened |
| --- | --- | --- | --- | --- | --- |
| main | gdelt | 367 | 66 | 25 | 0 |
| main | wikipedia | 1214 | 229 | 106 | 0 |
| seasonal | gdelt | 37 | 8 | 2 | 0 |
| seasonal | wikipedia | 208 | 30 | 10 | 0 |

Share of record detections (p < 0.05) that also pass on the screened p: 143 of 333.

### BH q < 0.10 detections (record or screened)

| analysis | shift_id | source | node_id | month0 | duration_class | tau_p | p_record | bh_q | p_cat_p_screened | bh_q_screened | bh_record | bh_screened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | value:wikipedia:antiracism:2019-10-14 | wikipedia | antiracism | 2019-10 | fading | 3.068 | 0.000 | 0.066 | 0.003 | 0.447 | True | False |
| main | value:wikipedia:chess:2020-11-02 | wikipedia | chess | 2020-11 | sustained | 2.550 | 0.000 | 0.066 | 0.004 | 0.447 | True | False |
| main | value:wikipedia:civil war:2017-05-01 | wikipedia | civil war | 2017-05 | fading | 0.631 | 0.001 | 0.099 | 0.005 | 0.447 | True | False |
| main | value:wikipedia:cloning:2018-01-29 | wikipedia | cloning | 2018-01 | fading | 1.264 | 0.000 | 0.066 | 0.003 | 0.447 | True | False |
| main | value:wikipedia:god:2017-09-11 | wikipedia | god | 2017-09 | fading | 1.797 | 0.001 | 0.099 | 0.008 | 0.447 | True | False |
| main | value:wikipedia:politics:2024-07-29 | wikipedia | politics | 2024-07 | fading | 0.280 | 0.001 | 0.099 | 0.004 | 0.447 | True | False |
| main | value:wikipedia:race:2020-05-25 | wikipedia | race | 2020-05 | sustained | 0.761 | 0.001 | 0.099 | 0.004 | 0.447 | True | False |
| main | value:wikipedia:wildlife:2021-10-04 | wikipedia | wildlife | 2021-10 | fading | 2.672 | 0.000 | 0.066 | 0.003 | 0.447 | True | False |
| main | value:gdelt:race relations:2020-06-08 | gdelt | race relations | 2020-06 | sustained | 1.089 | 0.000 | 0.066 | 0.004 | 0.447 | True | False |
| main | value:gdelt:refugees:2017-09-11 | gdelt | refugees | 2017-09 | fading | 0.673 | 0.000 | 0.081 | 0.005 | 0.447 | True | False |
| main | value:wikipedia:spanish civil war:2020-02-10 | wikipedia | spanish civil war | 2020-02 | sustained | 2.038 | 0.001 | 0.099 | 0.009 | 0.467 | True | False |
| seasonal | value:gdelt:fascism:2018-05-07 | gdelt | fascism | 2018-05 | fading | 2.547 | 0.000 | 0.090 | 0.005 | 0.664 | True | False |
