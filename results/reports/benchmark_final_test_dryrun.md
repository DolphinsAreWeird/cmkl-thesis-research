# Final test, dry run of the data extension on known months

Written 2026-10-17 03:15. Code: code/main_study/benchmark/27_final_test_dryrun.py with _final_extend.py and 26_final_test_panel.py. Freeze month 2026-06: stored rows, records, works and strengths from 2026-06 on were left out and the rows of 2026-06 to 2026-08 were brought in again as new rows. All months here are known; this is a test of the machinery, not evidence about unseen months.

## Months before the freeze: the rebuilt panel equals the stored panel

- rows compared 260,944; rows only in one panel 0; log share: both missing 11,188, max abs difference 0.00e+00; size_ok differs in 0 rows; month_ok differs in 0 rows.

## Months from the freeze on: extended panel against stored panel (the stored panel used the full taxonomy)

- rows compared 3,123; rows only in one panel 0; month_ok differs in 0 rows
- log share rows with a value in both: 3,114; difference (extended minus stored): mean -0.0002, median abs 0.0000, 90th percentile abs 0.0007, 99th percentile abs 0.0062, max abs 0.0617

| Format | Level | Months | Rows | Mean difference | Median abs | 90th pct abs | Share of rows with abs difference > 0.05 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| audiobook | broad | 3 | 57 | -0.0000 | 0.0001 | 0.0008 | 0.000 |
| audiobook | middle | 3 | 258 | -0.0001 | 0.0000 | 0.0006 | 0.000 |
| audiobook | narrow | 3 | 723 | -0.0004 | 0.0000 | 0.0005 | 0.001 |
| ebook | broad | 3 | 57 | +0.0000 | 0.0001 | 0.0004 | 0.000 |
| ebook | middle | 3 | 258 | -0.0001 | 0.0001 | 0.0009 | 0.000 |
| ebook | narrow | 3 | 723 | -0.0002 | 0.0000 | 0.0010 | 0.000 |
| print | broad | 3 | 57 | -0.0001 | 0.0001 | 0.0004 | 0.000 |
| print | middle | 3 | 258 | +0.0001 | 0.0000 | 0.0006 | 0.000 |
| print | narrow | 3 | 723 | +0.0000 | 0.0000 | 0.0006 | 0.000 |

- format-month totals equal in 9 of 9 format-months

## Scoring rehearsal: origin 2026-05, stored forecasts, targets from the stored panel and from the extended world

Print and ebook, narrow and middle themes; error = absolute error in log share; pooled ratio = sum of absolute errors of the pipeline / of naive over the rows both targets exist for; AvgRelMAE = geometric mean over series of the ratio of mean absolute errors (series with a naive error of 0 left out).

| Horizon | Rows | Pipeline | Pooled ratio, stored target | Pooled ratio, extended target | AvgRelMAE, stored target | AvgRelMAE, extended target | Mean abs error x100, stored | Mean abs error x100, extended |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 4.92 | 4.91 |
| 1 | 479 | chronos | 0.943 | 0.943 | 0.908 | 0.882 | 4.64 | 4.63 |
| 1 | 479 | chronos2 | 0.935 | 0.935 | 0.876 | 0.861 | 4.59 | 4.59 |
| 1 | 479 | chronos2_cur | 0.911 | 0.911 | 0.834 | 0.810 | 4.48 | 4.48 |
| 1 | 479 | chronos2_curdw | 0.901 | 0.900 | 0.799 | 0.778 | 4.43 | 4.43 |
| 1 | 479 | chronos2_bk | 0.920 | 0.920 | 0.843 | 0.827 | 4.52 | 4.52 |
| 1 | 479 | catchg_D | 0.964 | 0.964 | 0.949 | 0.934 | 4.74 | 4.74 |
| 1 | 479 | catchg_DW | 0.968 | 0.967 | 0.963 | 0.954 | 4.76 | 4.75 |
| 1 | 479 | catchg_DWS | 0.963 | 0.963 | 0.983 | 0.964 | 4.73 | 4.73 |
| 2 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 6.07 | 6.07 |
| 2 | 479 | chronos | 0.963 | 0.963 | 0.904 | 0.911 | 5.84 | 5.85 |
| 2 | 479 | chronos2 | 0.967 | 0.966 | 0.922 | 0.912 | 5.86 | 5.86 |
| 2 | 479 | chronos2_cur | 0.945 | 0.945 | 0.915 | 0.912 | 5.73 | 5.74 |
| 2 | 479 | chronos2_curdw | 0.940 | 0.940 | 0.904 | 0.904 | 5.70 | 5.71 |
| 2 | 479 | chronos2_bk | 0.959 | 0.959 | 0.970 | 0.975 | 5.82 | 5.82 |
| 2 | 479 | catchg_D | 0.941 | 0.940 | 0.897 | 0.907 | 5.71 | 5.71 |
| 2 | 479 | catchg_DW | 0.931 | 0.931 | 0.890 | 0.899 | 5.65 | 5.65 |
| 2 | 479 | catchg_DWS | 0.933 | 0.933 | 0.908 | 0.913 | 5.66 | 5.66 |
| 3 | 479 | naive | 1.000 | 1.000 | 1.000 | 1.000 | 6.94 | 6.95 |
| 3 | 479 | chronos | 0.987 | 0.987 | 1.034 | 1.040 | 6.85 | 6.86 |
| 3 | 479 | chronos2 | 0.973 | 0.973 | 1.006 | 1.003 | 6.76 | 6.76 |
| 3 | 479 | chronos2_cur | 0.947 | 0.947 | 0.935 | 0.943 | 6.57 | 6.58 |
| 3 | 479 | chronos2_curdw | 0.946 | 0.945 | 0.932 | 0.942 | 6.56 | 6.57 |
| 3 | 479 | chronos2_bk | 0.978 | 0.977 | 1.008 | 1.029 | 6.78 | 6.79 |
| 3 | 479 | catchg_D | 0.972 | 0.972 | 1.041 | 1.047 | 6.75 | 6.75 |
| 3 | 479 | catchg_DW | 0.978 | 0.977 | 1.063 | 1.073 | 6.78 | 6.79 |
| 3 | 479 | catchg_DWS | 0.981 | 0.981 | 1.069 | 1.079 | 6.81 | 6.81 |
