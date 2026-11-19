# Index of the numbers in the thesis results chapters

Khant Phyo Wai, student ID 01323050. Written by `code/main_study/wiki_led/99c_thesis_numbers_index.py` for the draft `Thesis_Draft_2026-11-19_1342.md`; it reads stored result files only and reruns no analysis.

## What it covers

`thesis_numbers_index.csv` lists every number in the Abstract and Chapters 5 to 8 of that draft: the running text, the tables and the figure captions of those chapters. Chapters 1 to 4, the appendices and the references are not covered. Dates, years used as labels, section, table and figure numbers, citation years and the settings themselves (list length, targets, interval level, window lengths, number of draws) are left out. An estimate printed with its interval is one row, and all its numbers must match.

Each row gives the script that wrote the value (path under `code/`), the stored file (path under `data/`; the frozen-forecast files sit in `prereg/`), the key inside it, the stored value at full precision, and the result of the comparison:

- **yes**: the stored value equals the printed one after rounding to the printed decimals (a share stored as a fraction and printed as percent counts as yes).
- **derived**: the printed number is computed from stored values (a difference, a ratio, a count, a log effect or error ratio turned into percent, or a word such as "about a fifth"); the formula is in `key` or `note`, and the result agrees with the print.
- **no**: the stored value, rounded to the printed decimals, differs from the print.
- **not found**: no stored output gives the number.

## Counts

250 numbers: 196 yes, 53 derived, 0 no, 1 not found.

| Chapter | yes | derived | no | not found |
| --- | ---: | ---: | ---: | ---: |
| Abstract | 11 | 3 | 0 | 0 |
| 5 | 163 | 35 | 0 | 0 |
| 6 | 4 | 0 | 0 | 1 |
| 7 | 16 | 14 | 0 | 0 |
| 8 | 2 | 1 | 0 | 0 |

## Rows that do not match or have no source

| id | Location | Printed | Stored | Note |
| --- | --- | --- | --- | --- |
| N217 | 6 paragraph "Status" | both | watcher holds one dataset: last update 2026-09-06 13:19 UTC, latest month 2026-08 | checked by hand on the city open data portal on 19 Nov 2026: Checkouts by Title (tmmm-ytt6) and Checkouts By Title (Physical Items) (5src-czff), both last updated 2026-09-06; no stored file records the second dataset |

## Notes

- Rows whose script column starts with "(none" have no script behind them: two counts made from Table B.1 of the thesis, and the check of the library datasets on the city portal.
- A few values come from Markdown reports rather than JSON or CSV files (events, release dates, linked pages, some counts); the `note` column quotes the line used, and the script stops if that line is no longer in the report.
- The well-known-books results use the corrected files of 20 October (`*_c.json`, `values_corrected` in the summary checks); the new-book split by earlier Seattle books uses `values_original` or `two_way_intervals.json`, as Test B has no corrected run.
- Intervals for the new-book groups are those of `98_two_way_intervals.py`: (i) authors only, (ii) first-loan years only, (iii) both; the `key` column names the one printed.
