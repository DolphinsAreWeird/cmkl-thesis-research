# Study 3b count panels (structural checks only)

- step: 01
- written: 2026-10-14 00:10:44
- mode: real data
- panel build: `20261014-001042-382abdb190c4`
- taxonomy: v3
- Study 3b settings record SHA-256: `7d27f0f9147ad0e7636d2e0ebe070c1cef3e829338472b2602b5dad9196b55a0`
- Study 3 settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json, 2026-10-13_h_gdelt_durations.json, 2026-10-13_i_gdelt_single_site.json

## Source
- taxonomy: v3
- theme strength (narrow, middle): stored strength
- values with a node: 29,600
- values without a node (left out of the shares): 149,217
- works with value evidence: 776,732

## Months covered (all categories share the format calendar)
- audiobook: 2005-09 to 2026-08, 252 months, 249 usable; missing in record: 2024-05, 2024-06, 2025-08
- ebook: 2005-09 to 2026-08, 252 months, 249 usable; missing in record: 2024-05, 2024-06, 2025-08
- print: 2005-04 to 2026-08, 257 months, 249 usable; library-wide total below closure threshold: 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2024-06, 2024-07
- librivox: 2017-01 to 2026-08, 116 months, 116 usable; no unusable months

## Reconciliation (whole-format totals and identities only)
- audiobook: raw rows 4,697,512; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; narrow: weighted-sum identity True, theme coverage 64.8% of checkouts; middle: weighted-sum identity True, theme coverage 73.2% of checkouts; value: weighted-sum identity True, theme coverage 90.0% of checkouts; values with any checkout 13,415, kept (>= 12 nonzero months in the format) 12,782
- ebook: raw rows 9,685,032; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; narrow: weighted-sum identity True, theme coverage 63.9% of checkouts; middle: weighted-sum identity True, theme coverage 73.0% of checkouts; value: weighted-sum identity True, theme coverage 86.5% of checkouts; values with any checkout 18,399, kept (>= 12 nonzero months in the format) 17,243
- print: raw rows 25,791,712; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; narrow: weighted-sum identity True, theme coverage 76.3% of checkouts; middle: weighted-sum identity True, theme coverage 82.9% of checkouts; value: weighted-sum identity True, theme coverage 91.6% of checkouts; values with any checkout 29,600, kept (>= 12 nonzero months in the format) 28,421
- narrow and middle weighted checkouts equal the Study 3 panel: True (238,678 category-format-months compared, 0 present in only one table, largest absolute difference 0.00e+00)

## Panel size
- narrow: 242 categories in the Seattle count panel (of 242 in the taxonomy); LibriVox 157
- middle: 86 categories in the Seattle count panel (of 86 in the taxonomy); LibriVox 79
- value: 28,464 categories in the Seattle count panel (of 28,464 in the taxonomy); LibriVox 368
- rows in counts_seattle.parquet: 7,449,891
- LibriVox: built (stored strength); values kept 368

## Feasibility (record: nonzero weighted checkout in >= 12 of the 24 fit months in at least one format; a format enters the joint model only with that many nonzero months itself and >= 75% of the fit months usable)
| kind | level | month0 | categories | feasible | feasible_share | usable_formats | in_1_formats | in_2_formats | in_3_formats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Seattle joint model | narrow | 2017-10 | 242 | 242 | 1.000 | audiobook,ebook,print | 1 | 0 | 241 |
| Seattle joint model | narrow | 2020-03 | 242 | 242 | 1.000 | audiobook,ebook,print | 1 | 0 | 241 |
| Seattle joint model | narrow | 2020-06 | 242 | 242 | 1.000 | audiobook,ebook,print | 1 | 0 | 241 |
| Seattle joint model | middle | 2017-10 | 86 | 86 | 1.000 | audiobook,ebook,print | 0 | 0 | 86 |
| Seattle joint model | middle | 2020-03 | 86 | 86 | 1.000 | audiobook,ebook,print | 0 | 0 | 86 |
| Seattle joint model | middle | 2020-06 | 86 | 86 | 1.000 | audiobook,ebook,print | 0 | 0 | 86 |
| Seattle joint model | value | 2017-10 | 28464 | 16530 | 0.581 | audiobook,ebook,print | 7526 | 3858 | 5146 |
| Seattle joint model | value | 2020-03 | 28464 | 16828 | 0.591 | audiobook,ebook,print | 6646 | 3707 | 6475 |
| Seattle joint model | value | 2020-06 | 28464 | 16826 | 0.591 | audiobook,ebook,print | 6593 | 3721 | 6512 |
| LibriVox | narrow | 2017-10 | 157 | 0 | 0.000 | none | 0 |  |  |
| LibriVox | narrow | 2020-03 | 157 | 154 | 0.981 | librivox | 154 |  |  |
| LibriVox | narrow | 2020-06 | 157 | 154 | 0.981 | librivox | 154 |  |  |
| LibriVox | middle | 2017-10 | 79 | 0 | 0.000 | none | 0 |  |  |
| LibriVox | middle | 2020-03 | 79 | 79 | 1.000 | librivox | 79 |  |  |
| LibriVox | middle | 2020-06 | 79 | 79 | 1.000 | librivox | 79 |  |  |
| LibriVox | value | 2017-10 | 368 | 0 | 0.000 | none | 0 |  |  |
| LibriVox | value | 2020-03 | 368 | 346 | 0.940 | librivox | 346 |  |  |
| LibriVox | value | 2020-06 | 368 | 347 | 0.943 | librivox | 347 |  |  |

## The three control categories (structure of the fit window only)
| kind | control | month0 | format | usable_fit_months | nonzero_fit_months | enters_model | control_feasible | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Seattle | COVID-19 | 2020-03 | audiobook | 24 | 24 | True | True |  |
| Seattle | COVID-19 | 2020-03 | ebook | 24 | 24 | True | True |  |
| Seattle | COVID-19 | 2020-03 | print | 24 | 24 | True | True |  |
| Seattle | COVID-19 | 2020-03 | value level |  |  |  |  | 102 values placed in the node, 102 with any stored counts, 50 feasible |
| Seattle | George Floyd / BLM | 2020-06 | audiobook | 24 | 24 | True | True |  |
| Seattle | George Floyd / BLM | 2020-06 | ebook | 24 | 24 | True | True |  |
| Seattle | George Floyd / BLM | 2020-06 | print | 24 | 24 | True | True |  |
| Seattle | George Floyd / BLM | 2020-06 | value level |  |  |  |  | 181 values placed in the node, 181 with any stored counts, 60 feasible |
| Seattle | #MeToo | 2017-10 | audiobook | 24 | 24 | True | True |  |
| Seattle | #MeToo | 2017-10 | ebook | 24 | 24 | True | True |  |
| Seattle | #MeToo | 2017-10 | print | 24 | 24 | True | True |  |
| Seattle | #MeToo | 2017-10 | value level |  |  |  |  | 188 values placed in the node, 188 with any stored counts, 64 feasible |

## Interest series at the value level
- Wikipedia: 614 value series, 604 of them have a demand count panel row set (>= 12 nonzero months in some format); GDELT: 185 value series, 183 of them have a demand count panel row set (>= 12 nonzero months in some format)

No category demand series, count, effect or p-value is shown here (hard rule).
