# Small circulation datasets: profile

Khant Phyo Wai, student ID 01323050
Profiled 2026-10-15. Structure only (rows, columns, date range, granularity). No analysis beyond this.

Files were read with `.venv/bin/python -I` (CSV module, no extra packages). Raw files and source notes are in `data/raw/<folder>/`, each with a `source.txt` giving the export URL, dataset page, licence or terms URL, and download date.

## Summary

| Dataset | Folder | File | Rows | Columns | Date range | Granularity | Size |
|---|---|---|---|---|---|---|---|
| Timberland Regional Library, Combined Circulation | timberland_circ/ | timberland_combined_circulation.csv | 12,665 | 6 | Jan 2011 to Sep 2026 (189 months) | Monthly; one row per month x library code x type (Physical or Digital) | 586,883 bytes |
| Norfolk Public Library, Library Circulation Statistics | norfolk_circ/ | norfolk_library_circulation.csv | 1,798 | 63 | Jul 2016 to Jul 2026 (119 months) | Monthly; one row per month x location (wide format, one column per item type) | 262,001 bytes |
| City of Mesa, Library Materials Circulation | mesa_circ/ | mesa_library_circulation.csv | 6,285 | 13 | Jul 2015 to Sep 2026 (135 months) | Monthly; one row per month x branch x material category x material type | 695,376 bytes |
| Edmonton Public Library, Most Popular Books by Branch (weekly top-10 holds) | edmonton_holds/ | not downloaded | 47,764 (from the portal's SQL count, not profiled from a file) | 8 | 2 Feb 2015 to 18 Oct 2021 (from the earlier hunt report, not re-checked) | Weekly; top 10 per branch | n/a |

## Timberland Regional Library

- Rows: 12,665. Columns (6): Date, Circulation, Library Code, Year, Month, Type.
- Date range: 1 Jan 2011 to 1 Sep 2026 (Date is the first of the month, stored as text with a 12:00 AM time).
- Granularity: monthly. Each month has one row per library code and type, so 49 distinct library codes and two types (Physical, Digital).
- Personal data: none. Columns are counts by library, month and format.

## Norfolk Public Library

- Rows: 1,798. Columns: 63 (Year, Month, Location, Total, then 59 item-type count columns such as Adult Fiction Digital Books, Digital Audiobooks, Hoopla E-Books, Equipment).
- Date range: July 2016 to July 2026 (119 months).
- Granularity: monthly, one row per month x location. 19 distinct Location values.
- Data quality notes, recorded and not corrected: the Month column has spelling errors ("Febuary", "Febraruay" for February, 30 rows in total); Location has variants for the same site ("Litte Creek" and "Little Creek"; "ONLINE" and "Online"). Location also includes non-branch entries such as "Storage" and "Book Mobile".
- Personal data: none. Columns are aggregate counts. No column is dropped.

## City of Mesa

- Rows: 6,285. Columns (13): Month, Month Number, Month Name, Year, Branch Name, Branch, Material Category, Material Type, Materials, Checkouts, Renewals, Transactions, Branch Name Full.
- Date range: July 2015 to September 2026 (135 months; Month is the first of the month).
- Granularity: monthly, one row per month x branch x material category x material type. 10 distinct Branch values. Material Category has 9 values (Audio CD, Blu-ray, Book, DVD, Electronic, InterLibrary Loan, Magazine, Stuffbrary, and blank).
- Personal data: none. Counts by branch and material type. No column is dropped.

## Edmonton Public Library (not profiled)

The Edmonton CSV was not downloaded. The full export is about 12.8 MB (estimated from a 1,000-row sample; 47,764 rows), which is above the about-10 MB limit Khant set. A capped attempt wrote a partial file, which was deleted. The earlier hunt report gives 47,764 rows, 5,585 distinct titles and 22 branches; those figures were not checked against a file. Download is pending Khant's approval.

## Personal data

None of the four datasets holds patron or personal data. Columns are aggregate counts by branch, month, format or item type. No column was dropped.
