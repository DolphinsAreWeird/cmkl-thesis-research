# Intervals that resample books and time together

Record: prereg/DEVIATIONS.md, 19 November 2026, part A. Stored predictions rescored; 2,000 draws, seed 20261119. (i) books only (author clusters for new books, works for the main set); (ii) time only (first-loan years; blocks of 3 months); (iii) both at once. 95% percentile intervals.

| Books | Score | Estimate | (i) books | (ii) time | (iii) both | (iii) above zero |
| --- | --- | --- | --- | --- | --- | --- |
| New books, all (134,970) | Wikipedia over L (main) | 0.0237 | 0.0189 to 0.0303 | 0.0210 to 0.0271 | 0.0174 to 0.0315 | yes |
| New books, all (134,970) | Wikipedia over Lq (no theme) | 0.0107 | 0.0077 to 0.0146 | 0.0099 to 0.0115 | 0.0070 to 0.0150 | yes |
| New books, all (134,970) | Wikipedia over L0 (first-month records) | 0.0122 | 0.0099 to 0.0152 | 0.0106 to 0.0145 | 0.0090 to 0.0163 | yes |
| New books, all (134,970) | Wikipedia over Lp (as fixed) | 0.0085 | 0.0066 to 0.0104 | 0.0069 to 0.0102 | 0.0056 to 0.0114 | yes |
| New books, all (134,970) | W_lgbm | 0.1273 | 0.1154 to 0.1391 | 0.1076 to 0.1438 | 0.1013 to 0.1484 | yes |
| New books, all (134,970) | L_lgbm | 0.3487 | 0.3357 to 0.3603 | 0.3220 to 0.3727 | 0.3178 to 0.3750 | yes |
| New books, all (134,970) | LW_lgbm | 0.3724 | 0.3617 to 0.3834 | 0.3486 to 0.3941 | 0.3441 to 0.3961 | yes |
| New books, no earlier Seattle work (45,303) | Wikipedia over L (main) | 0.0557 | 0.0478 to 0.0638 | 0.0466 to 0.0661 | 0.0429 to 0.0733 | yes |
| New books, no earlier Seattle work (45,303) | Wikipedia over Lq (no theme) | 0.0169 | 0.0135 to 0.0203 | 0.0131 to 0.0206 | 0.0108 to 0.0227 | yes |
| New books, no earlier Seattle work (45,303) | Wikipedia over L0 (first-month records) | 0.0152 | 0.0125 to 0.0183 | 0.0113 to 0.0178 | 0.0094 to 0.0199 | yes |
| New books, no earlier Seattle work (45,303) | Wikipedia over Lp (as fixed) | 0.0116 | 0.0094 to 0.0140 | 0.0084 to 0.0144 | 0.0069 to 0.0160 | yes |
| New books, no earlier Seattle work (45,303) | W_lgbm | 0.0901 | 0.0777 to 0.1012 | 0.0791 to 0.1010 | 0.0690 to 0.1093 | yes |
| New books, no earlier Seattle work (45,303) | L_lgbm | 0.0452 | 0.0324 to 0.0570 | -0.0013 to 0.0838 | -0.0034 to 0.0856 | no |
| New books, no earlier Seattle work (45,303) | LW_lgbm | 0.1009 | 0.0891 to 0.1124 | 0.0576 to 0.1353 | 0.0533 to 0.1375 | yes |
| New books, some earlier work (89,667) | Wikipedia over L (main) | 0.0204 | 0.0134 to 0.0298 | 0.0162 to 0.0255 | 0.0112 to 0.0326 | yes |
| New books, some earlier work (89,667) | Wikipedia over Lq (no theme) | 0.0100 | 0.0062 to 0.0147 | 0.0086 to 0.0117 | 0.0053 to 0.0152 | yes |
| New books, some earlier work (89,667) | Wikipedia over L0 (first-month records) | 0.0115 | 0.0082 to 0.0153 | 0.0087 to 0.0144 | 0.0069 to 0.0170 | yes |
| New books, some earlier work (89,667) | Wikipedia over Lp (as fixed) | 0.0075 | 0.0051 to 0.0101 | 0.0051 to 0.0100 | 0.0039 to 0.0115 | yes |
| New books, some earlier work (89,667) | W_lgbm | 0.1147 | 0.0996 to 0.1297 | 0.0927 to 0.1356 | 0.0845 to 0.1411 | yes |
| New books, some earlier work (89,667) | L_lgbm | 0.4226 | 0.4057 to 0.4375 | 0.3935 to 0.4474 | 0.3886 to 0.4535 | yes |
| New books, some earlier work (89,667) | LW_lgbm | 0.4429 | 0.4293 to 0.4564 | 0.4182 to 0.4654 | 0.4128 to 0.4692 | yes |
| Main set (1,258,807 rows, 34,813 works) | Wikipedia over HM (main) | 0.0047 | 0.0041 to 0.0052 | 0.0037 to 0.0057 | 0.0035 to 0.0060 | yes |
| Main set (1,258,807 rows, 34,813 works) | W14 | 0.0911 | 0.0881 to 0.0940 | 0.0846 to 0.0977 | 0.0832 to 0.0985 | yes |
| Main set (1,258,807 rows, 34,813 works) | HM | 0.3474 | 0.3449 to 0.3499 | 0.3398 to 0.3551 | 0.3390 to 0.3556 | yes |
| Main set (1,258,807 rows, 34,813 works) | HMW14 | 0.3521 | 0.3495 to 0.3546 | 0.3443 to 0.3600 | 0.3435 to 0.3603 | yes |
