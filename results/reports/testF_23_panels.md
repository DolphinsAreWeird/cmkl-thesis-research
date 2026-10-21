# Test F, step 23: demand panels b and c (real data; structural checks only)

- written 2026-10-21 19:22; code main_study/wiki_led/testF/23_panels.py; Study 3 record `eeeb6c80425a`
- works: 20,000 (key books.parquet); with an AI theme 19,968; with a heading theme 18,741 (stored strength)

## Months (usable = month_ok of the Study 3 panel and at least one loan of these works)
- audiobook: 2005-09 to 2026-08, 252 months, 249 usable; works with loans 13,205; excluded in the Study 3 panel: 2024-05, 2024-06, 2025-08
- ebook: 2005-09 to 2026-08, 252 months, 249 usable; works with loans 16,171; excluded in the Study 3 panel: 2024-05, 2024-06, 2025-08
- print: 2005-04 to 2026-08, 257 months, 249 usable; works with loans 19,239; excluded in the Study 3 panel: 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2024-06, 2024-07

## Panel b (AI-sorted works)
- rows 264,067; donor-overlap pairs 78,436
- audiobook: narrow: weighted-sum identity True, theme coverage 100.0% of loans; middle: weighted-sum identity True, theme coverage 100.0% of loans; broad: weighted-sum identity True, theme coverage 100.0% of loans
- ebook: narrow: weighted-sum identity True, theme coverage 100.0% of loans; middle: weighted-sum identity True, theme coverage 100.0% of loans; broad: weighted-sum identity True, theme coverage 100.0% of loans
- print: narrow: weighted-sum identity True, theme coverage 98.5% of loans; middle: weighted-sum identity True, theme coverage 98.5% of loans; broad: weighted-sum identity True, theme coverage 98.5% of loans
- categories passing the minimum-size rule (>= 20 works with loans and median >= 200 weighted loans a month in the 24 months before the window):
| format | level | categories | pass size at 2017-10 | pass size at 2020-03 | pass size at 2020-06 |
| --- | --- | --- | --- | --- | --- |
| audiobook | narrow | 242 | 29 | 112 | 115 |
| audiobook | middle | 86 | 45 | 71 | 72 |
| audiobook | broad | 19 | 19 | 19 | 19 |
| ebook | narrow | 242 | 74 | 128 | 131 |
| ebook | middle | 86 | 67 | 78 | 78 |
| ebook | broad | 19 | 19 | 19 | 19 |
| print | narrow | 242 | 139 | 152 | 149 |
| print | middle | 86 | 80 | 81 | 81 |
| print | broad | 19 | 19 | 19 | 19 |

## Panel c (librarian headings)
- rows 263,306; donor-overlap pairs 92,510
- audiobook: narrow: weighted-sum identity True, theme coverage 70.4% of loans; middle: weighted-sum identity True, theme coverage 78.3% of loans; broad: weighted-sum identity True, theme coverage 94.2% of loans
- ebook: narrow: weighted-sum identity True, theme coverage 73.0% of loans; middle: weighted-sum identity True, theme coverage 80.8% of loans; broad: weighted-sum identity True, theme coverage 94.1% of loans
- print: narrow: weighted-sum identity True, theme coverage 75.8% of loans; middle: weighted-sum identity True, theme coverage 82.5% of loans; broad: weighted-sum identity True, theme coverage 94.6% of loans
- categories passing the minimum-size rule (>= 20 works with loans and median >= 200 weighted loans a month in the 24 months before the window):
| format | level | categories | pass size at 2017-10 | pass size at 2020-03 | pass size at 2020-06 |
| --- | --- | --- | --- | --- | --- |
| audiobook | narrow | 241 | 21 | 55 | 59 |
| audiobook | middle | 86 | 33 | 56 | 58 |
| audiobook | broad | 19 | 19 | 19 | 19 |
| ebook | narrow | 241 | 47 | 71 | 78 |
| ebook | middle | 86 | 53 | 62 | 64 |
| ebook | broad | 19 | 19 | 19 | 19 |
| print | narrow | 241 | 96 | 101 | 100 |
| print | middle | 86 | 71 | 72 | 72 |
| print | broad | 19 | 19 | 19 | 19 |

No theme demand series, effect or p-value is shown here.
- run time 19s; peak memory 1.34 GB
