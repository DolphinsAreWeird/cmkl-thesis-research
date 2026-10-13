# Study 4, step 01: feature table (structure only)

Built 2026-10-13 21:32. Record SHA-256 `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`. Demand panel build `20261013-210004-a772613ac300`. Counts only: this report holds no target values and no category-level demand.

## Rows (origin x category x format x horizon; eligible at the origin, target month observed)

### Horizon 1

| Group | Format | Level | Origin range | Rows | Categories | Origins |
| --- | --- | --- | --- | ---: | ---: | ---: |
| librivox | librivox | middle | 2019-01 to 2021-05 | 1,535 | 53 | 29 |
| librivox | librivox | middle | 2021-06 onward | 3,421 | 56 | 62 |
| librivox | librivox | middle | before test (training only) | 624 | 52 | 12 |
| librivox | librivox | narrow | 2019-01 to 2021-05 | 2,171 | 76 | 29 |
| librivox | librivox | narrow | 2021-06 onward | 4,880 | 80 | 62 |
| librivox | librivox | narrow | before test (training only) | 857 | 72 | 12 |
| seattle | audiobook | middle | 2019-01 to 2021-05 | 1,966 | 74 | 29 |
| seattle | audiobook | middle | 2021-06 onward | 4,562 | 83 | 57 |
| seattle | audiobook | middle | before test (training only) | 2,690 | 60 | 117 |
| seattle | audiobook | narrow | 2019-01 to 2021-05 | 2,272 | 95 | 29 |
| seattle | audiobook | narrow | 2021-06 onward | 7,285 | 151 | 57 |
| seattle | audiobook | narrow | before test (training only) | 1,846 | 53 | 115 |
| seattle | ebook | middle | 2019-01 to 2021-05 | 2,284 | 82 | 29 |
| seattle | ebook | middle | 2021-06 onward | 4,738 | 85 | 57 |
| seattle | ebook | middle | before test (training only) | 4,862 | 75 | 93 |
| seattle | ebook | narrow | 2019-01 to 2021-05 | 3,598 | 143 | 29 |
| seattle | ebook | narrow | 2021-06 onward | 8,488 | 160 | 57 |
| seattle | ebook | narrow | before test (training only) | 5,226 | 105 | 89 |
| seattle | print | middle | 2019-01 to 2021-05 | 1,877 | 86 | 22 |
| seattle | print | middle | 2021-06 onward | 4,954 | 85 | 59 |
| seattle | print | middle | before test (training only) | 12,965 | 86 | 153 |
| seattle | print | narrow | 2019-01 to 2021-05 | 4,002 | 187 | 22 |
| seattle | print | narrow | 2021-06 onward | 9,461 | 178 | 59 |
| seattle | print | narrow | before test (training only) | 28,709 | 201 | 153 |

### Horizon 2

| Group | Format | Level | Origin range | Rows | Categories | Origins |
| --- | --- | --- | --- | ---: | ---: | ---: |
| librivox | librivox | middle | 2019-01 to 2021-05 | 1,535 | 53 | 29 |
| librivox | librivox | middle | 2021-06 onward | 3,365 | 56 | 61 |
| librivox | librivox | middle | before test (training only) | 624 | 52 | 12 |
| librivox | librivox | narrow | 2019-01 to 2021-05 | 2,171 | 76 | 29 |
| librivox | librivox | narrow | 2021-06 onward | 4,800 | 80 | 61 |
| librivox | librivox | narrow | before test (training only) | 857 | 72 | 12 |
| seattle | audiobook | middle | 2019-01 to 2021-05 | 1,966 | 74 | 29 |
| seattle | audiobook | middle | 2021-06 onward | 4,398 | 83 | 55 |
| seattle | audiobook | middle | before test (training only) | 2,690 | 60 | 117 |
| seattle | audiobook | narrow | 2019-01 to 2021-05 | 2,272 | 95 | 29 |
| seattle | audiobook | narrow | 2021-06 onward | 6,999 | 151 | 55 |
| seattle | audiobook | narrow | before test (training only) | 1,846 | 53 | 115 |
| seattle | ebook | middle | 2019-01 to 2021-05 | 2,284 | 82 | 29 |
| seattle | ebook | middle | 2021-06 onward | 4,572 | 85 | 55 |
| seattle | ebook | middle | before test (training only) | 4,862 | 75 | 93 |
| seattle | ebook | narrow | 2019-01 to 2021-05 | 3,598 | 143 | 29 |
| seattle | ebook | narrow | 2021-06 onward | 8,185 | 160 | 55 |
| seattle | ebook | narrow | before test (training only) | 5,226 | 105 | 89 |
| seattle | print | middle | 2019-01 to 2021-05 | 1,792 | 86 | 21 |
| seattle | print | middle | 2021-06 onward | 4,785 | 85 | 57 |
| seattle | print | middle | before test (training only) | 12,965 | 86 | 153 |
| seattle | print | narrow | 2019-01 to 2021-05 | 3,818 | 186 | 21 |
| seattle | print | narrow | 2021-06 onward | 9,135 | 178 | 57 |
| seattle | print | narrow | before test (training only) | 28,709 | 201 | 153 |

Rows dropped because the target month (or month t) is missing, closed or partial, or has a zero share (never scored): horizon 1: 2,290, horizon 2: 4,109.

## Missing rate per feature

Share of rows with a missing value, by origin range (all groups, horizon 1). Interest features are missing before the series have enough history, for categories without a series, and (GDELT) outside July 2017 to June 2021 or for categories GDELT does not cover. In the shift columns a missing value means no usable interest series; "no shift in the window" is 0.

| Feature | 2019-01 to 2021-05 | 2021-06 onward | before test (training only) | All |
| --- | ---: | ---: | ---: | ---: |
| ls_t | 0.000 | 0.000 | 0.000 | 0.000 |
| ls_t1 | 0.014 | 0.025 | 0.000 | 0.012 |
| ls_t2 | 0.027 | 0.039 | 0.000 | 0.019 |
| ls_ly | 0.040 | 0.055 | 0.000 | 0.027 |
| mean6 | 0.027 | 0.000 | 0.000 | 0.004 |
| dlog_total | 0.014 | 0.025 | 0.000 | 0.012 |
| w_logmean4 | 0.000 | 0.000 | 0.609 | 0.281 |
| w_ratio | 0.000 | 0.000 | 0.650 | 0.300 |
| w_dlog4 | 0.000 | 0.000 | 0.609 | 0.281 |
| w_mk8 | 0.000 | 0.000 | 0.609 | 0.281 |
| w_shift8 | 0.000 | 0.000 | 0.650 | 0.300 |
| w_lab_sustained | 0.000 | 0.000 | 0.650 | 0.300 |
| w_lab_intermediate | 0.000 | 0.000 | 0.650 | 0.300 |
| w_lab_fading | 0.000 | 0.000 | 0.650 | 0.300 |
| w_shift_size | 0.000 | 0.000 | 0.650 | 0.300 |
| w_shift_weeks | 0.000 | 0.000 | 0.650 | 0.300 |
| g_logmean4 | 0.407 | 0.990 | 0.853 | 0.835 |
| g_ratio | 0.419 | 0.991 | 0.886 | 0.852 |
| g_dlog4 | 0.412 | 0.991 | 0.859 | 0.839 |
| g_mk8 | 0.384 | 0.990 | 0.855 | 0.832 |
| g_shift8 | 0.419 | 0.990 | 0.886 | 0.852 |
| g_lab_sustained | 0.419 | 0.990 | 0.886 | 0.852 |
| g_lab_intermediate | 0.419 | 0.990 | 0.886 | 0.852 |
| g_lab_fading | 0.419 | 0.990 | 0.886 | 0.852 |
| g_shift_size | 0.419 | 0.990 | 0.886 | 0.852 |
| g_shift_weeks | 0.419 | 0.990 | 0.886 | 0.852 |
| t_tone | 0.436 | 0.991 | 0.891 | 0.858 |
| t_pos | 0.436 | 0.991 | 0.891 | 0.858 |
| t_neg | 0.436 | 0.991 | 0.891 | 0.858 |

## Interest shift states (counts of rows, horizon 1)

| Range | Rows with a Wikipedia shift in the last 8 weeks | of which a quality-ok shift (scoring split only) | Rows with a GDELT shift |
| --- | ---: | ---: | ---: |
| 2019-01 to 2021-05 | 1,008 | 829 | 1,044 |
| 2021-06 onward | 1,994 | 1,778 | 88 |
| before test (training only) | 824 | 604 | 581 |

## Notes

- Features at origin t use demand months up to t and interest weeks whose Sunday is on or before the last day of t.
- `seasonal`, `quality_flag` and `title_confusion` are not used. `quality_ok` only sets the scoring split column `split_qok_shift8`, never a feature.
- Categorical columns: format, level, broad_id, tmonth. No category id is a feature.
