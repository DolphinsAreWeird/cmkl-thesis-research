# Final test, dry run of the data extension on known months

Written 2026-10-17 03:26. Code: code/main_study/benchmark/27_final_test_dryrun.py with _final_extend.py and 26_final_test_panel.py. Freeze month 2026-06: stored rows, records, works and strengths from 2026-06 on were left out and the rows of 2026-06 to 2026-08 were brought in again as new rows. All months here are known; this is a test of the machinery, not evidence about unseen months.

## Months before the freeze: the rebuilt panel equals the stored panel

- rows compared 260,944; rows only in one panel 0; log share: both missing 11,188, max abs difference 0.00e+00; size_ok differs in 0 rows; month_ok differs in 0 rows.

## Months from the freeze on: extended panel against stored panel (the stored panel used the full taxonomy)

- rows compared 3,123; rows only in one panel 0; month_ok differs in 0 rows
- log share rows with a value in both: 3,114; difference (extended minus stored): mean -0.0009, median abs 0.0006, 90th percentile abs 0.0064, 99th percentile abs 0.0354, max abs 0.3371

| Format | Level | Months | Rows | Mean difference | Median abs | 90th pct abs | Share of rows with abs difference > 0.05 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| audiobook | broad | 3 | 57 | -0.0001 | 0.0004 | 0.0019 | 0.000 |
| audiobook | middle | 3 | 258 | -0.0006 | 0.0006 | 0.0046 | 0.000 |
| audiobook | narrow | 3 | 723 | -0.0007 | 0.0002 | 0.0065 | 0.001 |
| ebook | broad | 3 | 57 | -0.0000 | 0.0003 | 0.0012 | 0.000 |
| ebook | middle | 3 | 258 | -0.0005 | 0.0006 | 0.0032 | 0.000 |
| ebook | narrow | 3 | 723 | -0.0006 | 0.0005 | 0.0056 | 0.001 |
| print | broad | 3 | 57 | -0.0006 | 0.0014 | 0.0056 | 0.000 |
| print | middle | 3 | 258 | -0.0001 | 0.0009 | 0.0081 | 0.008 |
| print | narrow | 3 | 723 | -0.0019 | 0.0009 | 0.0096 | 0.022 |

- format-month totals equal in 9 of 9 format-months

## Scoring rehearsal: origin 2026-05, stored forecasts, targets from the stored panel and from the extended world

Print and ebook, narrow and middle themes; error = absolute error in log share; pooled ratio = sum of absolute errors of the pipeline / of naive over the rows both targets exist for; AvgRelMAE = geometric mean over series of the ratio of mean absolute errors (series with a naive error of 0 left out).

| Horizon | Rows | Pipeline | Pooled ratio, stored target | Pooled ratio, extended target | AvgRelMAE, stored target | AvgRelMAE, extended target | Mean abs error x100, stored | Mean abs error x100, extended |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 4.92 | 4.90 |
| 1 | 479 | chronos | 0.943 | 0.943 | 0.908 | 0.883 | 4.64 | 4.63 |
| 1 | 479 | chronos2 | 0.935 | 0.936 | 0.876 | 0.840 | 4.59 | 4.59 |
| 1 | 479 | chronos2_cur | 0.911 | 0.914 | 0.834 | 0.816 | 4.48 | 4.48 |
| 1 | 479 | chronos2_curdw | 0.901 | 0.904 | 0.799 | 0.770 | 4.43 | 4.43 |
| 1 | 479 | chronos2_bk | 0.920 | 0.924 | 0.843 | 0.818 | 4.52 | 4.53 |
| 1 | 479 | catchg_D | 0.964 | 0.965 | 0.949 | 0.918 | 4.74 | 4.73 |
| 1 | 479 | catchg_DW | 0.968 | 0.968 | 0.963 | 0.940 | 4.76 | 4.75 |
| 1 | 479 | catchg_DWS | 0.963 | 0.963 | 0.983 | 0.958 | 4.73 | 4.72 |
| 2 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 6.07 | 6.10 |
| 2 | 479 | chronos | 0.963 | 0.966 | 0.904 | 0.942 | 5.84 | 5.89 |
| 2 | 479 | chronos2 | 0.967 | 0.970 | 0.922 | 0.952 | 5.86 | 5.92 |
| 2 | 479 | chronos2_cur | 0.945 | 0.949 | 0.915 | 0.923 | 5.73 | 5.79 |
| 2 | 479 | chronos2_curdw | 0.940 | 0.943 | 0.904 | 0.910 | 5.70 | 5.76 |
| 2 | 479 | chronos2_bk | 0.959 | 0.962 | 0.970 | 0.972 | 5.82 | 5.87 |
| 2 | 479 | catchg_D | 0.941 | 0.942 | 0.897 | 0.923 | 5.71 | 5.75 |
| 2 | 479 | catchg_DW | 0.931 | 0.933 | 0.890 | 0.899 | 5.65 | 5.69 |
| 2 | 479 | catchg_DWS | 0.933 | 0.934 | 0.908 | 0.923 | 5.66 | 5.70 |
| 3 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 6.94 | 7.05 |
| 3 | 479 | chronos | 0.987 | 0.986 | 1.034 | 1.071 | 6.85 | 6.95 |
| 3 | 479 | chronos2 | 0.973 | 0.975 | 1.006 | 1.017 | 6.76 | 6.88 |
| 3 | 479 | chronos2_cur | 0.947 | 0.949 | 0.935 | 0.952 | 6.57 | 6.70 |
| 3 | 479 | chronos2_curdw | 0.946 | 0.948 | 0.932 | 0.963 | 6.56 | 6.68 |
| 3 | 479 | chronos2_bk | 0.978 | 0.979 | 1.008 | 1.032 | 6.78 | 6.91 |
| 3 | 479 | catchg_D | 0.972 | 0.970 | 1.041 | 1.027 | 6.75 | 6.84 |
| 3 | 479 | catchg_DW | 0.978 | 0.975 | 1.063 | 1.068 | 6.78 | 6.87 |
| 3 | 479 | catchg_DWS | 0.981 | 0.978 | 1.069 | 1.073 | 6.81 | 6.90 |
