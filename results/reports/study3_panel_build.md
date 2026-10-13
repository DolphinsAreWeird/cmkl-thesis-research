# Study 3 demand panel build (structural checks only)

- step: 01
- written: 2026-10-13 21:00:04
- mode: real data
- panel build: `20261013-210004-a772613ac300`
- taxonomy: v3
- settings record SHA-256: `eeeb6c80425a1d1c2a35e409e57e49d633155ad879f0147be9287bed48ded0b5`
- addenda applied: 2026-10-13_a_ranking_clarification.json, 2026-10-13_b_synthetic_control_demeaned.json, 2026-10-13_c_implementation_choices.json, 2026-10-13_d_shift_start_reading.json, 2026-10-13_e_closure_months.json, 2026-10-13_f_control_mapping_fixes.json, 2026-10-13_g_suspect_wikipedia_shifts.json

## Source
- taxonomy: v3
- theme strength: stored strength
- work_theme works missing from the work table: 0
- work_theme nodes missing from theme_nodes: 0
- interest inputs present: shifts.parquet, gdelt/weekly_node.parquet, gdelt_duration_scaling.json; interest checkpoint report present

## Months covered (all categories share the format calendar)
- audiobook: 2005-09 to 2026-08, 252 months, 249 usable; missing in record: 2024-05, 2024-06, 2025-08
- ebook: 2005-09 to 2026-08, 252 months, 249 usable; missing in record: 2024-05, 2024-06, 2025-08
- print: 2005-04 to 2026-08, 257 months, 249 usable; library-wide total below closure threshold: 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2024-06, 2024-07
- librivox: 2017-01 to 2026-08, 116 months, 116 usable; no unusable months

## Reconciliation (whole-format totals only)
- audiobook: raw rows 4,697,512; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; work table reconciles: True; SPL API months compared 249, rows equal 249, checkouts equal 249; narrow: weighted-sum identity True, theme coverage 64.8% of checkouts; middle: weighted-sum identity True, theme coverage 73.2% of checkouts; broad: weighted-sum identity True, theme coverage 90.0% of checkouts
- ebook: raw rows 9,685,032; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; work table reconciles: True; SPL API months compared 249, rows equal 249, checkouts equal 249; narrow: weighted-sum identity True, theme coverage 63.9% of checkouts; middle: weighted-sum identity True, theme coverage 73.0% of checkouts; broad: weighted-sum identity True, theme coverage 86.5% of checkouts
- print: raw rows 25,791,712; rows whose record has no work 0; denominator equals raw checkouts: True; checkouts on records with a work 100.00%; work table reconciles: True; SPL API months compared 257, rows equal 257, checkouts equal 257; narrow: weighted-sum identity True, theme coverage 76.3% of checkouts; middle: weighted-sum identity True, theme coverage 82.9% of checkouts; broad: weighted-sum identity True, theme coverage 91.6% of checkouts

## Panel size
- rows: 264,067; donor-overlap pairs: 165,118
- narrow: 242 categories with data (of 242 nodes)
- middle: 86 categories with data (of 86 nodes)
- broad: 19 categories with data (of 19 nodes)

## Categories passing the minimum-size rule (>= 20 works with checkouts and median >= 200 weighted checkouts per month in the 24 months before the window)
| format | level | categories | pass size at 2017-10 | pass size at 2020-03 | pass size at 2020-06 |
| --- | --- | --- | --- | --- | --- |
| audiobook | narrow | 242 | 41 | 79 | 85 |
| audiobook | middle | 86 | 50 | 67 | 69 |
| audiobook | broad | 19 | 19 | 19 | 19 |
| ebook | narrow | 242 | 96 | 124 | 127 |
| ebook | middle | 86 | 73 | 79 | 80 |
| ebook | broad | 19 | 19 | 19 | 19 |
| print | narrow | 242 | 184 | 185 | 181 |
| print | middle | 86 | 86 | 85 | 85 |
| print | broad | 19 | 19 | 19 | 19 |

- LibriVox: built (stored strength)

No category demand series, effect or p-value is shown here (hard rule until the positive controls are run).
