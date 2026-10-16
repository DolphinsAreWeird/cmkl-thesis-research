# Study 3b value-level interest shifts (interest data only)

- step: 02
- written: 2026-10-14 00:05:40
- mode: real data
- panel build: `n/a`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json
- shifts_value file SHA-256: `794bcd3cd1b021a69b7fe379a7034922fad990ab9ce926ae1cd25eea1a5f3151`

## What was done
- value series: Wikipedia 614, GDELT 185 (files weekly_value.parquet of the interest side)
- Wikipedia value series recomputed from the daily page views for 8 values; largest relative difference to the stored weekly views 0.00e+00
- thresholds from the record (Study 3, addenda d and h): normal level 26 weeks, large size >= 3.0, sustained >= 4, intermediate == 3, fading <= 2 weeks; GDELT durations ratio 1.0

## Shifts
- all value-level shifts found: 2593; labelled (sustained, intermediate or fading): 2573; labelled and from 2017-01: 2400
| source | label | shifts |
| --- | --- | --- |
| gdelt | fading | 383 |
| gdelt | intermediate | 16 |
| gdelt | interrupted | 4 |
| gdelt | sustained | 58 |
| wikipedia | fading | 1585 |
| wikipedia | intermediate | 170 |
| wikipedia | interrupted | 16 |
| wikipedia | sustained | 361 |

## Tested set (labelled, from 2017-01) by source and quality
| source | labelled_from_2017 | seasonal | main_set | main_quality_ok | all_quality_ok | large_main |
| --- | --- | --- | --- | --- | --- | --- |
| gdelt | 457 | 41 | 416 | 416 | 457 | 50 |
| wikipedia | 1943 | 284 | 1659 | 1395 | 1668 | 245 |

## Quality flags (Wikipedia, tested set)
- flags: {'one_day': 113, 'desktop_only': 191, 'title_confusion': 7}; flagged in total 275 of 1943
- desktop check: 1943 shifts examined; cached answers of the interest side used 425, own cache 68, new requests 1450
- Wikipedia shifts without any desktop answer (desktop_only not screened): 23
- title confusion: verdict found for the same page and week on 141 shifts (7 title_confusion, 134 ok); NOT screened (no verdict for the page): 1802 of 1943 (178 of them large)

## GDELT (tested set)
- shifts 457; single-site check available for 43, flagged single_site 8; not screened (no sampled URL list for the driver code and day): 414
- driver code without a hand verdict on figurative use (not checked, no new hand check): 160

## NOT IN RECORD (interest side, value level)
- value level is level 4 in the table; node_id holds the value, parent_node its placed node
- title_confusion verdicts matched on the same page and a start week within 2 weeks; shifts without a verdict stay unscreened
- desktop_only and one_day computed only for labelled shifts from 2017-01 (the tested set); others get no flag
- single_site only where a URL sample exists for the driver code and day; no new URL samples were drawn
- GDELT quality_ok carries only the single_site flag (as for nodes)

- shifts_value.parquet SHA-256: `794bcd3cd1b021a69b7fe379a7034922fad990ab9ce926ae1cd25eea1a5f3151`
