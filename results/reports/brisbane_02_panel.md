# Brisbane replication, step 2: match and panel (structure only)

- written: 2026-10-15 02:54:40; Brisbane record SHA-256 `08dd33d36c91af4235c684572d87601e8e5d9a2af4003df31e6121d0c639495d`
- Seattle match index: 650,052 works keyed by (normalised main title, author family name); 13,148 keys had more than one Seattle work (the work with the most Seattle checkouts is taken)
- theme strength: stored strength; only works with a narrow or middle theme profile (753,987) add to theme counts
- months 2015-06 to 2025-12: 127; usable 116; unusable 11

## Match rate by year (loans)
| year | loans | dates_with_loans | sampled_days | loans_with_author | matched_loans | match_rate | loans_with_theme_profile | theme_rate | unique_title_author_pairs | matched_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 261400 | 21 | 21 | 231623 | 90547 | 0.346 | 82626 | 0.316 | 72402 | 25659 |
| 2016 | 614670 | 36 | 36 | 543005 | 213169 | 0.347 | 195477 | 0.318 | 117673 | 41051 |
| 2017 | 636227 | 36 | 36 | 534077 | 206878 | 0.325 | 190823 | 0.300 | 124358 | 43344 |
| 2018 | 722097 | 36 | 36 | 646470 | 253056 | 0.350 | 234303 | 0.325 | 137995 | 49066 |
| 2019 | 713216 | 36 | 36 | 584554 | 250044 | 0.351 | 231264 | 0.324 | 190598 | 71607 |
| 2020 | 515888 | 50 | 36 | 405891 | 158108 | 0.306 | 145634 | 0.282 | 123679 | 40619 |
| 2021 | 615320 | 36 | 36 | 500476 | 218513 | 0.355 | 200427 | 0.326 | 118309 | 45482 |
| 2022 | 619261 | 45 | 36 | 512042 | 204995 | 0.331 | 188107 | 0.304 | 129183 | 45354 |
| 2023 | 568440 | 37 | 37 | 479649 | 187683 | 0.330 | 172860 | 0.304 | 125164 | 44353 |
| 2024 | 579911 | 36 | 36 | 497364 | 209296 | 0.361 | 192340 | 0.332 | 113688 | 45613 |
| 2025 | 545282 | 37 | 36 | 474179 | 200337 | 0.367 | 184086 | 0.338 | 109430 | 44524 |

Overall: 2,192,626 of 6,391,712 loans matched (34.3%), 31.6% carry a narrow or middle theme profile.

## Unusable months
| month | days | total_checkouts | title_share | reason | closure_ratio |
| --- | --- | --- | --- | --- | --- |
| 2017-03 | 3 | 66424 | 0.708 | source file has too few titles (under 90% of loans) | 1.146 |
| 2017-08 | 3 | 44523 | 0.405 | source file has too few titles (under 90% of loans) | 0.951 |
| 2020-04 | 3 | 2591 | 1.000 | library-wide total below closure threshold | 0.048 |
| 2020-05 | 3 | 1770 | 1.000 | library-wide total below closure threshold | 0.034 |
| 2020-06 | 3 | 19425 | 1.000 | library-wide total below closure threshold | 0.393 |
| 2020-07 | 3 | 58927 | 0.000 | source file has too few titles (under 90% of loans) | 1.237 |
| 2021-08 | 3 | 17987 | 1.000 | library-wide total below closure threshold | 0.377 |
| 2022-10 | 3 | 53542 | 0.000 | source file has too few titles (under 90% of loans) | 0.999 |
| 2023-04 | 3 | 4386 | 1.000 | library-wide total below closure threshold | 0.079 |
| 2023-08 | 3 | 51250 | 0.000 | source file has too few titles (under 90% of loans) | 0.981 |
| 2025-03 | 3 | 1318 | 1.000 | library-wide total below closure threshold | 0.026 |

## Sampled days per usable month
| days | months |
| --- | --- |
| 3 | 115 |
| 4 | 1 |

## Identities
- narrow: weighted-sum identity True; share of usable-month loans carrying a narrow theme (weighted) 28.0%
- middle: weighted-sum identity True; share of usable-month loans carrying a middle theme (weighted) 29.9%

## Categories with counts
- narrow: 242
- middle: 86
