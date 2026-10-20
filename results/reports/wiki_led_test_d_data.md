# Test D rows (all books, by format): data build

Built 2026-10-20 17:38 by `code/main_study/wiki_led/60_test_d_rows.py`. Rows file: `data/db/wiki_led/test_d_rows.parquet` (2,767,485 rows, 38 columns, 106 MB, float32 for all measures and features, rows ordered by format, origin month and work_id). Data only: no model was fitted and no feature was related to an outcome; every number below is a count or the distribution of one column. Settings: addendum d of 20 Oct 2026 (SHA-256 checked in the script), section test_D_all_books. Rebuild: `bash jobs/bg.sh wl_test_d_data main_study/wiki_led/60_test_d_rows.py` (add `--elig raw` for the other reading of the 12-month sum, see the choices at the end).

## What the rows are

- **Works.** 254,021 works from the fixed 25% sample of the 1,013,659 works in `spl_works.parquet` (first hex digit of md5(str(work_id)) is 0, 1, 2 or 3), plus all 7,747 Test A works (5,804 of them were not in the sample), 259,825 works in all. 49,107 of them have at least one row.
- **Series.** One per work and format: `print` (the `spl_rows_book` files), `ebook`, `audiobook`. Monthly loans are the checkouts of all records of the work in that format. Months before the series' first loan are missing (not in the collection); later months without a loan are 0.
- **Excluded months** (missing in every window, never an origin or a target; `month_ok` is False for any format in `demand_panel.parquet`, equal to the list in the request): 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2024-05, 2024-06, 2024-07, 2025-08.
- **Origins.** 112 months from 2016-03 to 2026-07 (125 months minus the 13 whose month t or t+1 is excluded). `mi` = year x 12 + month - 1 of the origin month t; `year` is the year of the target month t+1.
- **Eligible** at t when the loans over t-11..t sum to at least 24 (excluded months and months before the first loan add nothing to the sum).
- **Columns** (as Test A): `L_t`, `L_next` (month t+1), `M6` (median of L over t-5..t, missing months skipped), `h_lt` = ln(1+L_t), `h_lt1` = ln(1+L(t-1)), `h_m6` = ln(1+M6), `h_m12` = ln(1 + mean of L over t-11..t, missing months skipped), `h_lyago` = ln(1+L(t-11)), `h_age` = t minus the month of the first loan, `D` = ln(1+L_next) - ln(1+M6), `Sg` = 1 when D >= ln 2 and L_next - M6 >= 5, `Y` = ln(1+L_next). Also `work_id`, `format`, `mi`, `year`, `in_test_a`, `has_book_page`, `has_author_page`, the Wikipedia features `b_*` and `a_*` (lvl4, r4, r1, rmax, nrise8, run, dw, chg, valid4 as in `test_a_wiki_features.parquet`), and the extra column `loans12` (the 12-month loan sum used for eligibility).
- **Wikipedia features.** `b_*` for the 7,747 Test A works (their own article); `a_*` for any sampled work whose `creator_key` equals the `creator_key` of a Test A work that has an author article; missing for all other rows.

## Counts by format

| format | series with any loan in the sample | series with at least one row | rows | of these Test A series | Test A rows | rows per origin month |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| print | 236,280 | 35,624 | 1,056,368 | 6,804 | 356,735 | 9,432 |
| ebook | 64,329 | 25,532 | 966,350 | 7,199 | 527,927 | 8,628 |
| audiobook | 28,877 | 18,446 | 744,767 | 6,387 | 446,647 | 6,650 |
| all formats | 329,486 | 79,602 | 2,767,485 | 20,390 | 1,331,309 | 24,710 |

49,107 distinct works have rows in at least one format (7,747 of the 7,747 Test A works and 41,360 other sampled works). A series enters the file only if it was eligible at some origin; the second column counts every series that has any loan in the sample. The Test A works are 3.0% of the sampled works but 48.1% of the rows (print 33.8%, ebook 54.6%, audiobook 60.0%), because a series needs 24 loans in 12 months and most library books borrow less than that.

## Counts by format and year of the target month

Rows per month is the rows of that year divided by the number of origin months of that year that are in the file. Shares are shares of rows.

| format | year | series | rows | origin months | rows per month | book page flag | b_ features present | author page flag | a_ features present | surge rate (Sg) | D >= ln 1.5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print | 2016 | 15,203 | 111,151 | 9 | 12,350 | 30.6% | 30.6% | 40.5% | 38.9% | 1.66% | 11.6% |
| print | 2017 | 15,898 | 146,509 | 12 | 12,209 | 31.4% | 31.4% | 40.7% | 39.2% | 2.06% | 12.2% |
| print | 2018 | 15,917 | 145,869 | 12 | 12,156 | 33.0% | 33.0% | 41.8% | 40.3% | 1.92% | 11.6% |
| print | 2019 | 15,598 | 143,721 | 12 | 11,977 | 33.4% | 33.4% | 41.9% | 40.5% | 1.91% | 12.1% |
| print | 2020 | 12,947 | 45,279 | 5 | 9,056 | 35.1% | 35.1% | 43.9% | 42.6% | 1.78% | 13.7% |
| print | 2021 | 7,538 | 49,552 | 12 | 4,129 | 46.0% | 46.0% | 56.4% | 54.6% | 5.40% | 19.9% |
| print | 2022 | 11,287 | 105,410 | 12 | 8,784 | 34.1% | 34.1% | 43.5% | 42.2% | 1.87% | 12.0% |
| print | 2023 | 12,251 | 113,157 | 12 | 9,430 | 33.3% | 33.3% | 42.2% | 41.0% | 1.83% | 12.7% |
| print | 2024 | 11,049 | 63,996 | 8 | 8,000 | 34.3% | 34.3% | 43.2% | 42.1% | 2.15% | 14.0% |
| print | 2025 | 9,302 | 69,854 | 10 | 6,985 | 35.5% | 35.5% | 44.5% | 43.5% | 2.36% | 13.2% |
| print | 2026 | 9,444 | 61,870 | 8 | 7,734 | 34.8% | 34.8% | 43.9% | 42.9% | 2.00% | 13.6% |
| **print** | **all** | **35,624** | **1,056,368** | **112** | **9,432** | **33.8%** | **33.8%** | **42.9%** | **41.5%** | **2.10%** | **12.8%** |
| ebook | 2016 | 7,400 | 54,830 | 9 | 6,092 | 59.0% | 59.0% | 70.7% | 66.4% | 0.54% | 8.6% |
| ebook | 2017 | 8,193 | 76,440 | 12 | 6,370 | 60.3% | 60.3% | 71.2% | 66.9% | 1.20% | 9.7% |
| ebook | 2018 | 9,248 | 86,972 | 12 | 7,248 | 58.7% | 58.7% | 69.4% | 65.3% | 1.23% | 10.7% |
| ebook | 2019 | 10,146 | 97,543 | 12 | 8,129 | 57.1% | 57.1% | 68.0% | 64.2% | 1.21% | 10.5% |
| ebook | 2020 | 9,603 | 36,001 | 5 | 7,200 | 58.8% | 58.8% | 69.8% | 66.2% | 1.92% | 11.5% |
| ebook | 2021 | 11,377 | 96,883 | 12 | 8,074 | 55.9% | 55.9% | 66.9% | 63.6% | 1.39% | 8.5% |
| ebook | 2022 | 13,158 | 124,991 | 12 | 10,416 | 51.8% | 51.8% | 63.4% | 60.3% | 1.52% | 11.3% |
| ebook | 2023 | 13,676 | 130,348 | 12 | 10,862 | 51.2% | 51.2% | 62.6% | 59.7% | 1.51% | 11.3% |
| ebook | 2024 | 13,212 | 82,324 | 8 | 10,290 | 51.9% | 51.9% | 63.0% | 60.2% | 1.68% | 11.0% |
| ebook | 2025 | 12,422 | 95,195 | 10 | 9,520 | 53.0% | 53.0% | 63.4% | 60.8% | 1.81% | 10.8% |
| ebook | 2026 | 12,551 | 84,823 | 8 | 10,603 | 50.4% | 50.4% | 61.0% | 58.4% | 1.56% | 10.6% |
| **ebook** | **all** | **25,532** | **966,350** | **112** | **8,628** | **54.6%** | **54.6%** | **65.7%** | **62.4%** | **1.43%** | **10.5%** |
| audiobook | 2016 | 3,911 | 29,483 | 9 | 3,276 | 68.3% | 68.3% | 78.1% | 74.8% | 0.50% | 8.4% |
| audiobook | 2017 | 4,946 | 47,433 | 12 | 3,953 | 68.2% | 68.2% | 77.5% | 74.0% | 0.83% | 9.3% |
| audiobook | 2018 | 6,168 | 59,117 | 12 | 4,926 | 66.5% | 66.5% | 76.2% | 72.7% | 1.09% | 10.1% |
| audiobook | 2019 | 7,025 | 69,325 | 12 | 5,777 | 64.7% | 64.7% | 74.5% | 71.2% | 1.40% | 10.2% |
| audiobook | 2020 | 6,874 | 26,037 | 5 | 5,207 | 67.0% | 67.0% | 76.1% | 73.0% | 1.71% | 9.9% |
| audiobook | 2021 | 7,893 | 66,423 | 12 | 5,535 | 65.1% | 65.1% | 75.2% | 72.2% | 2.40% | 10.1% |
| audiobook | 2022 | 9,790 | 95,820 | 12 | 7,985 | 58.9% | 58.9% | 69.5% | 66.5% | 2.21% | 12.1% |
| audiobook | 2023 | 10,979 | 108,247 | 12 | 9,021 | 56.1% | 56.1% | 66.7% | 63.8% | 1.90% | 11.3% |
| audiobook | 2024 | 11,082 | 71,530 | 8 | 8,941 | 55.8% | 55.8% | 66.2% | 63.5% | 2.15% | 11.5% |
| audiobook | 2025 | 11,198 | 89,567 | 10 | 8,957 | 55.4% | 55.4% | 65.3% | 62.9% | 2.12% | 10.7% |
| audiobook | 2026 | 11,692 | 81,785 | 8 | 10,223 | 52.2% | 52.2% | 62.6% | 60.1% | 1.83% | 10.9% |
| **audiobook** | **all** | **18,446** | **744,767** | **112** | **6,650** | **60.0%** | **60.0%** | **70.1%** | **67.2%** | **1.79%** | **10.7%** |

## Surge rate and share of rises by format

Sg = 1 when D >= ln 2 and L_next - M6 >= 5; the rise share is the share of rows with D >= ln 1.5. "From 2019-01" is the period Test A scored.

| format | all rows | surge rate | D >= ln 1.5 | rows from 2019-01 | surge rate from 2019-01 | D >= ln 1.5 from 2019-01 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| print | 1,056,368 | 2.10% | 12.8% | 640,752 | 2.22% | 13.3% |
| ebook | 966,350 | 1.43% | 10.5% | 740,315 | 1.54% | 10.6% |
| audiobook | 744,767 | 1.79% | 10.7% | 603,235 | 1.99% | 11.0% |
| all formats | 2,767,485 | 1.78% | 11.4% | 1,984,302 | 1.90% | 11.6% |

For reference, Test A (all formats added together, 556,735 scored rows) had a surge rate of 2.78%.

## Eligible rows per origin month

| origin month | print | ebook | audiobook | all |
| --- | ---: | ---: | ---: | ---: |
| 2016-03 | 12,483 | 6,003 | 3,066 | 21,552 |
| 2016-04 | 12,412 | 6,053 | 3,112 | 21,577 |
| 2016-05 | 12,402 | 6,108 | 3,177 | 21,687 |
| 2016-06 | 12,505 | 6,121 | 3,206 | 21,832 |
| 2016-07 | 12,380 | 6,122 | 3,257 | 21,759 |
| 2016-08 | 12,328 | 6,119 | 3,337 | 21,784 |
| 2016-09 | 12,234 | 6,100 | 3,375 | 21,709 |
| 2016-10 | 12,217 | 6,091 | 3,442 | 21,750 |
| 2016-11 | 12,190 | 6,113 | 3,511 | 21,814 |
| 2016-12 | 12,202 | 6,117 | 3,582 | 21,901 |
| 2017-01 | 12,169 | 6,125 | 3,613 | 21,907 |
| 2017-02 | 12,189 | 6,157 | 3,659 | 22,005 |
| 2017-03 | 12,163 | 6,217 | 3,718 | 22,098 |
| 2017-04 | 12,178 | 6,285 | 3,819 | 22,282 |
| 2017-05 | 12,143 | 6,318 | 3,913 | 22,374 |
| 2017-06 | 12,200 | 6,385 | 4,017 | 22,602 |
| 2017-07 | 12,230 | 6,430 | 4,097 | 22,757 |
| 2017-08 | 12,247 | 6,509 | 4,183 | 22,939 |
| 2017-09 | 12,267 | 6,564 | 4,209 | 23,040 |
| 2017-10 | 12,288 | 6,629 | 4,282 | 23,199 |
| 2017-11 | 12,233 | 6,704 | 4,341 | 23,278 |
| 2017-12 | 12,218 | 6,757 | 4,393 | 23,368 |
| 2018-01 | 12,206 | 6,834 | 4,440 | 23,480 |
| 2018-02 | 12,202 | 6,900 | 4,531 | 23,633 |
| 2018-03 | 12,152 | 7,036 | 4,642 | 23,830 |
| 2018-04 | 12,152 | 7,119 | 4,760 | 24,031 |
| 2018-05 | 12,174 | 7,196 | 4,901 | 24,271 |
| 2018-06 | 12,168 | 7,265 | 5,028 | 24,461 |
| 2018-07 | 12,106 | 7,400 | 5,114 | 24,620 |
| 2018-08 | 12,130 | 7,520 | 5,212 | 24,862 |
| 2018-09 | 12,112 | 7,563 | 5,261 | 24,936 |
| 2018-10 | 12,135 | 7,658 | 5,389 | 25,182 |
| 2018-11 | 12,114 | 7,724 | 5,446 | 25,284 |
| 2018-12 | 12,087 | 7,793 | 5,499 | 25,379 |
| 2019-01 | 12,061 | 7,840 | 5,559 | 25,460 |
| 2019-02 | 12,014 | 7,950 | 5,596 | 25,560 |
| 2019-03 | 12,007 | 7,967 | 5,628 | 25,602 |
| 2019-04 | 11,953 | 8,020 | 5,647 | 25,620 |
| 2019-05 | 11,892 | 8,067 | 5,703 | 25,662 |
| 2019-06 | 11,867 | 8,165 | 5,755 | 25,787 |
| 2019-07 | 11,959 | 8,214 | 5,828 | 26,001 |
| 2019-08 | 11,957 | 8,269 | 5,898 | 26,124 |
| 2019-09 | 11,981 | 8,354 | 5,985 | 26,320 |
| 2019-10 | 11,973 | 8,413 | 6,068 | 26,454 |
| 2019-11 | 11,970 | 8,491 | 6,159 | 26,620 |
| 2019-12 | 12,009 | 8,584 | 6,208 | 26,801 |
| 2020-01 | 12,008 | 8,629 | 6,231 | 26,868 |
| 2020-02 | 12,028 | 8,700 | 6,293 | 27,021 |
| 2020-10 | 5,022 | 4,928 | 3,620 | 13,570 |
| 2020-11 | 4,212 | 5,160 | 3,685 | 13,057 |
| 2020-12 | 3,580 | 5,364 | 3,771 | 12,715 |
| 2021-01 | 2,792 | 5,582 | 3,805 | 12,179 |
| 2021-02 | 2,169 | 5,727 | 3,799 | 11,695 |
| 2021-03 | 2,051 | 5,828 | 3,901 | 11,780 |
| 2021-04 | 2,541 | 6,726 | 4,571 | 13,838 |
| 2021-05 | 3,066 | 7,702 | 5,253 | 16,021 |
| 2021-06 | 3,695 | 8,571 | 5,839 | 18,105 |
| 2021-07 | 4,479 | 9,363 | 6,396 | 20,238 |
| 2021-08 | 5,261 | 10,068 | 6,905 | 22,234 |
| 2021-09 | 6,099 | 10,725 | 7,334 | 24,158 |
| 2021-10 | 6,650 | 10,651 | 7,383 | 24,684 |
| 2021-11 | 7,169 | 10,576 | 7,466 | 25,211 |
| 2021-12 | 7,463 | 10,523 | 7,575 | 25,561 |
| 2022-01 | 7,868 | 10,464 | 7,668 | 26,000 |
| 2022-02 | 8,172 | 10,385 | 7,754 | 26,311 |
| 2022-03 | 8,440 | 10,302 | 7,839 | 26,581 |
| 2022-04 | 8,711 | 10,318 | 7,769 | 26,798 |
| 2022-05 | 8,973 | 10,308 | 7,880 | 27,161 |
| 2022-06 | 9,182 | 10,335 | 7,972 | 27,489 |
| 2022-07 | 9,234 | 10,376 | 8,081 | 27,691 |
| 2022-08 | 9,348 | 10,445 | 8,188 | 27,981 |
| 2022-09 | 9,359 | 10,481 | 8,294 | 28,134 |
| 2022-10 | 9,339 | 10,523 | 8,367 | 28,229 |
| 2022-11 | 9,321 | 10,531 | 8,433 | 28,285 |
| 2022-12 | 9,345 | 10,584 | 8,527 | 28,456 |
| 2023-01 | 9,368 | 10,603 | 8,568 | 28,539 |
| 2023-02 | 9,430 | 10,630 | 8,626 | 28,686 |
| 2023-03 | 9,466 | 10,704 | 8,731 | 28,901 |
| 2023-04 | 9,455 | 10,708 | 8,959 | 29,122 |
| 2023-05 | 9,421 | 10,733 | 9,041 | 29,195 |
| 2023-06 | 9,399 | 10,815 | 9,096 | 29,310 |
| 2023-07 | 9,474 | 10,906 | 9,180 | 29,560 |
| 2023-08 | 9,445 | 11,010 | 9,247 | 29,702 |
| 2023-09 | 9,452 | 11,114 | 9,333 | 29,899 |
| 2023-10 | 9,430 | 11,218 | 9,432 | 30,080 |
| 2023-11 | 9,472 | 11,323 | 9,507 | 30,302 |
| 2023-12 | 9,514 | 11,422 | 9,569 | 30,505 |
| 2024-01 | 9,471 | 11,551 | 9,616 | 30,638 |
| 2024-02 | 9,444 | 11,605 | 9,679 | 30,728 |
| 2024-03 | 9,418 | 11,685 | 9,726 | 30,829 |
| 2024-08 | 6,724 | 9,197 | 8,230 | 24,151 |
| 2024-09 | 6,548 | 9,062 | 8,228 | 23,838 |
| 2024-10 | 6,482 | 8,931 | 8,234 | 23,647 |
| 2024-11 | 6,395 | 8,871 | 8,248 | 23,514 |
| 2024-12 | 6,383 | 8,823 | 8,279 | 23,485 |
| 2025-01 | 6,339 | 8,707 | 8,259 | 23,305 |
| 2025-02 | 6,299 | 8,627 | 8,225 | 23,151 |
| 2025-03 | 6,278 | 8,573 | 8,212 | 23,063 |
| 2025-04 | 6,180 | 8,532 | 8,241 | 22,953 |
| 2025-05 | 6,924 | 9,558 | 8,978 | 25,460 |
| 2025-06 | 7,692 | 10,465 | 9,619 | 27,776 |
| 2025-09 | 7,928 | 10,594 | 9,832 | 28,354 |
| 2025-10 | 7,920 | 10,624 | 9,937 | 28,481 |
| 2025-11 | 7,911 | 10,692 | 9,985 | 28,588 |
| 2025-12 | 7,870 | 10,668 | 10,071 | 28,609 |
| 2026-01 | 7,833 | 10,715 | 10,122 | 28,670 |
| 2026-02 | 7,809 | 10,625 | 10,138 | 28,572 |
| 2026-03 | 7,742 | 10,568 | 10,160 | 28,470 |
| 2026-04 | 7,675 | 10,597 | 10,241 | 28,513 |
| 2026-05 | 7,665 | 10,550 | 10,311 | 28,526 |
| 2026-06 | 7,671 | 10,551 | 10,359 | 28,581 |
| 2026-07 | 7,605 | 10,549 | 10,383 | 28,537 |

## Wikipedia features

| format | rows with a book page | rows with b_ features | rows with an author page | rows with a_ features |
| --- | ---: | ---: | ---: | ---: |
| print | 33.8% | 33.8% | 42.9% | 41.5% |
| ebook | 54.6% | 54.6% | 65.7% | 62.4% |
| audiobook | 60.0% | 60.0% | 70.1% | 67.2% |
| all formats | 48.1% | 48.1% | 58.2% | 55.7% |

- Author links: 3,115 creator keys map to an author article (19,871 of the 259,825 sampled works have one; 7,590 Test A works have one and 157 do not). 86,364 sampled works have an empty creator key and never get author features.
- 3 creator keys have more than one author article among the Test A works; the article used by most of those works is taken (ties between two articles, 1: margret rey; the alphabetically first article is taken). 3 Test A works therefore get a different author article than Test A gave them, and 9 Test A works that had none now get one.
- 64 of the 3,063 author articles in use have no weekly view data, so their works carry the author page flag with `a_*` missing; every book article has data (0 without).

## Distributions of single columns (all rows)

| format | column | 5% | 25% | 50% | 75% | 95% | 99% | mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print | L_t | 0.0 | 2.0 | 4.0 | 7.0 | 20.0 | 50.0 | 7.22 |
| print | L_next | 0.0 | 2.0 | 4.0 | 7.0 | 20.0 | 48.0 | 6.90 |
| print | M6 | 1.5 | 2.5 | 4.0 | 7.0 | 20.5 | 53.0 | 7.60 |
| print | loans12 | 25.0 | 32.0 | 46.0 | 81.0 | 228.0 | 621.0 | 83.51 |
| print | h_age | 6.0 | 19.0 | 48.0 | 109.0 | 204.0 | 245.0 | 70.05 |
| print | D | -1.10 | -0.41 | -0.10 | 0.18 | 0.69 | 1.08 | -0.14 |
| ebook | L_t | 1.0 | 2.0 | 4.0 | 7.0 | 27.0 | 85.0 | 8.50 |
| ebook | L_next | 1.0 | 2.0 | 4.0 | 7.0 | 27.0 | 85.0 | 8.34 |
| ebook | M6 | 1.5 | 2.5 | 4.0 | 7.0 | 27.5 | 84.0 | 8.57 |
| ebook | loans12 | 25.0 | 32.0 | 45.0 | 79.0 | 285.0 | 867.0 | 92.76 |
| ebook | h_age | 7.0 | 26.0 | 64.0 | 111.0 | 171.0 | 207.0 | 73.25 |
| ebook | D | -0.97 | -0.29 | 0.00 | 0.18 | 0.54 | 0.92 | -0.10 |
| audiobook | L_t | 1.0 | 3.0 | 5.0 | 9.0 | 33.0 | 95.0 | 9.88 |
| audiobook | L_next | 1.0 | 3.0 | 5.0 | 9.0 | 32.0 | 95.0 | 9.74 |
| audiobook | M6 | 2.0 | 3.0 | 4.5 | 8.5 | 32.0 | 91.0 | 9.78 |
| audiobook | loans12 | 25.0 | 34.0 | 50.0 | 91.0 | 322.0 | 914.0 | 102.84 |
| audiobook | h_age | 6.0 | 22.0 | 58.0 | 114.0 | 190.0 | 224.0 | 73.71 |
| audiobook | D | -0.92 | -0.29 | 0.00 | 0.18 | 0.55 | 0.98 | -0.08 |

## Checks against Test A (no model involved)

1. **Loans.** For the Test A works, the monthly loans per format built here equal `study2r/counts_work.parquet` cell by cell: print: 0 differing cells (loans 8,323,715 here, 8,323,715 there); ebook: 0 differing cells (loans 8,030,332 here, 8,030,332 there); audiobook: 0 differing cells (loans 6,922,613 here, 6,922,613 there).
2. **Rows.** For Test A works with loans in one format only, the rows here are compared with `test_a_rows.parquet` on (work_id, origin month). Test D rows are a subset of Test A rows (an eligible row needs 24 loans, Test A needed one); where both exist the values are compared exactly (float32).

| format | Test A works in one format | Test D rows | Test A rows | rows in both | only in Test D | differing values in L, M6, h_*, D, Sg, Y | rows with a differing b_ value | rows with a differing a_ value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| print | 203 | 18,644 | 20,394 | 18,644 | 0 | 0 | 0 | 0 |
| ebook | 85 | 6,508 | 6,972 | 6,508 | 0 | 0 | 0 | 0 |
| audiobook | 45 | 3,446 | 3,620 | 3,446 | 0 | 0 | 0 | 0 |

3. **Order and keys.** Inside each format the rows are strictly increasing in (origin month, work_id): 2,767,482 adjacent pairs checked, all increasing = True. Rows dropped because M6 had no available month: 0.
4. **Excluded months** equal the list in the request (10 months); the panel has a total for every month of every format from 2015-01.

## Choices where the request left room

1. **Eligibility and excluded months.** The 12-month sum of 24 loans skips excluded months, like M6 and the 12-month mean (the request says excluded months are missing inside windows). Summing the recorded loans of all 12 months instead would make 109,859 more series-origin pairs eligible (4.0% on top of 2,767,485); they all sit at origins whose 12-month window contains an excluded month. Run the script with `--elig raw` to build that version.
2. **Test A's handling of single months.** `h_lt1` and `h_lyago` use the recorded loans of month t-1 and t-11 even if that month is excluded (Test A applies the exclusion to the M6 and 12-month windows only); a month before the first loan counts as 0 there. `L_t` and `L_next` are never excluded months.
3. **Rounding.** D and Sg are computed in float32 as in Test A. Exact doublings (L_next = 2 x M6 + 1) sit on the boundary D = ln 2 and follow float32 rounding, the same as in Test A.
4. **First loan.** The first loan month of a series is its first month with a recorded loan in that format. Series already in the collection when the data begin (2005-04 for print, 2005-09 for ebook and audiobook) have a first loan month equal to the first data month, so `h_age` is cut off at the start of the data (sampled series whose first loan is the first data month: print 20,878, ebook 116, audiobook 223).
5. **Flags.** `has_book_page` is 1 for the Test A works; `has_author_page` is 1 when the work's creator key maps to an author article, whether or not that article has weekly data. The share of rows with the features present is in the Wikipedia table above.
6. **Extra column.** `loans12` is not in the request; it holds the loan sum used for the eligibility rule so stricter cut-offs can be applied without a rebuild.
7. **Format labels.** `print`, `ebook`, `audiobook` (the labels of `counts_work.parquet` and the demand panel); the print row files are named `spl_rows_book`.
8. **Same name, different person.** `creator_key` is a normalised name, so two authors with the same name share author features.

## Memory and runtime

- Peak memory of the build process: 1,259 MB physical footprint (what `time -l` reports as peak memory footprint) and 790 MB resident (limit set for the job: 3,000 MB). One format at a time; the biggest object is the series by month loan matrix (float32, 232 MB for the largest format).
- Runtime 23 s in all: print 9 s, ebook 4 s, audiobook 2 s; the rest is set-up, the checks and this report. The job ran with `nice` 5 beside the Wikipedia views download.
