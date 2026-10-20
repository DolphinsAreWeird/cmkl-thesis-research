# Check of the corrected feature function on 20 articles (correction A1, addendum e)

Written by `code/main_study/wiki_led/10c_check_features.py`. The two functions are the `article_features` of `10_test_a.py` (original) and `10c_test_a.py` (corrected), read from the files with `ast` and run on the weekly series of 20 articles drawn with seed 20261020: 5 book and 5 author articles whose first week with views is the first week of the data (29 June 2015), and 5 + 5 whose first view is later. Each article has one row per origin month from 2016-03 to 2026-07 for which a week had ended.

| kind | article | first week with views | first view in week 1 of the data | origin months, original | corrected | identical origin months | differing origin months | all identical (week-1 articles) | largest difference where both are finite | origin months with no corrected row (original lvl4 -> corrected) | last origin month differing by more than 1e-9 | origin months differing only by rounding (below 1e-9) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | Calico Joe | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | The Seven Principles for Making Ma | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | The Stepford Wives | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Bleachers (novel) | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Odyssey | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| book | Prequel: An American Fight Against | 2023-11-27 | no | 125 | 32 | 25 | 100 | - | 101 | 93 (lvl4 -27.63 -> missing) | 2024-06 (31 wk after first view) | 0 |
| book | The Heart (novel) | 2017-12-11 | no | 125 | 104 | 58 | 67 | - | 85.5 | 21 (lvl4 -27.63 -> missing) | 2018-06 (29 wk after first view) | 39 |
| book | Thin Air (Parker novel) | 2019-10-14 | no | 125 | 82 | 75 | 50 | - | 76.7 | 43 (lvl4 -27.63 -> missing) | 2020-04 (28 wk after first view) | 0 |
| book | Barkskins | 2016-07-18 | no | 125 | 121 | 113 | 12 | - | 97.3 | 4 (lvl4 -27.63 -> missing) | 2017-02 (32 wk after first view) | 0 |
| book | Master of the Revels: A Return to  | 2022-10-10 | no | 125 | 46 | 42 | 83 | - | 5.52 | 79 (lvl4 -27.63 -> missing) | 2023-01 (16 wk after first view) | 0 |
| author | Daniel Yergin | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Susanna Clarke | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Roberto Bolaño | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Yotam Ottolenghi | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Paul Beatty | 2015-06-29 | yes | 125 | 125 | 125 | 0 | yes | 0 | 0 | - | 0 |
| author | Liz Pelly | 2025-12-29 | no | 125 | 7 | 0 | 125 | - | 94.2 | 118 (lvl4 -27.63 -> missing) | 2026-07 (31 wk after first view) | 0 |
| author | Laura Dave (novelist) | 2024-04-08 | no | 125 | 28 | 18 | 107 | - | 95.1 | 97 (lvl4 -27.63 -> missing) | 2024-10 (29 wk after first view) | 3 |
| author | C Pam Zhang | 2020-05-18 | no | 125 | 75 | 68 | 57 | - | 85.1 | 50 (lvl4 -27.63 -> missing) | 2020-11 (28 wk after first view) | 0 |
| author | Maria Reva | 2020-10-19 | no | 125 | 70 | 62 | 63 | - | 71.1 | 55 (lvl4 -27.63 -> missing) | 2021-05 (32 wk after first view) | 0 |
| author | Kathleen Belew | 2019-06-03 | no | 125 | 86 | 80 | 45 | - | 97.5 | 39 (lvl4 -27.63 -> missing) | 2019-11 (26 wk after first view) | 0 |

- The original function reproduces the stored original features (`test_a_wiki_features.parquet`) exactly for 20 of 20 articles.
- Articles whose first view is in the first week of the data: corrected and original features are identical in every origin month for 10 of 10 (same origin months, same values, NaN equal to NaN, no tolerance).
- Articles whose first view is later: the origin months that end before the article has a complete week of views have no corrected row (all nine features missing; the original gave the floor value of lvl4 and zero-based ratios there), the first months after the first view differ because the original compared the new article with weeks of zero views, and from the month after the one named in the second-last column onward the two agree (differences below 1e-9 are floating-point rounding: a rolling sum that starts in a different week carries a different rounding error in the 15th digit; they are not counted as differences there).
