# Check of the corrected features for every article (correction A1, addendum e)

Written by `code/main_study/wiki_led/10c_check_features.py --full`: the stored original features (`test_a_wiki_features.parquet`) against the corrected ones (`test_a_wiki_features_c.parquet`), row by row on (kind, article, origin month); exact equality with NaN equal to NaN.

| kind | articles with original features | articles whose first view is in week 1 | their origin-month rows | of these rows differing | other articles | their rows | rows exactly identical | rows equal within 1e-9 | rows with no corrected row | articles with at least one row differing by more than 1e-9 | weeks after the first view week of the last such row: median / 99th percentile / max | articles with no view at all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | 7,427 | 4,282 | 535,250 | 0 | 3,144 | 393,000 | 190,399 | 197,882 | 174,651 | 3,071 | 30 / 34 / 47 | 1 |
| author | 3,001 | 2,310 | 288,750 | 0 | 689 | 86,125 | 47,542 | 50,379 | 31,338 | 666 | 30 / 34 / 40 | 2 |

- Rows in the original file 1,303,500, in the corrected file 1,097,136; rows in the corrected file that are not in the original: 0.
- Features that are finite in the original and missing in the corrected file on rows that exist in both (by feature): {'lvl4': 0, 'r4': 13004, 'r1': 13004, 'rmax': 13004, 'nrise8': 0, 'run': 0, 'dw': 0, 'chg': 3207, 'valid4': 0}.
