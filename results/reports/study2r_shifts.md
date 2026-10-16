# Study 2R: detected shifts (interest side only)

Built 2026-10-14 20:40 by code/study2r/07_detect_shifts.py. Rule: Study 3 rule unchanged, rise ratio **4.0**, floor **300** user views a week (prereg/addenda_2r/2026-10-14_b_calibration_values.json, filed before this run). Nothing here is joined to borrowing; no borrowing effect around any event was computed.

Series: 7,427 book articles (33039 series-years at or above the floor); 3,004 author articles (19894 series-years).

### Book articles, ratio 4.0

| Class | All shifts | Quality OK (no flag) | Articles |
|---|---|---|---|
| sustained | 658 | 620 | 494 |
| intermediate | 265 | 252 | 244 |
| fading | 2170 | 1707 | 1427 |
| censored | 0 | 0 | 0 |
| interrupted | 12 | 10 | 12 |
| **total** | 3105 | 2589 | 1735 |

Flags among the three final classes (3093): one_day 495, desktop_only 39, any 514.

By whole duration (known only after the shift ends; used for the confirmatory duration test):

| Whole duration | Shifts | Quality OK |
|---|---|---|
| 1-2 weeks | 2170 | 1707 |
| 3 weeks | 265 | 252 |
| 4-5 weeks | 323 | 306 |
| 6+ weeks | 335 | 314 |
| not final | 12 | 10 |

### Book articles, sensitivity ratio 1.5 (floor 300; no desktop check)

| Class | All shifts | Quality OK (no flag) | Articles |
|---|---|---|---|
| sustained | 3853 | 3664 | 2044 |
| intermediate | 1535 | 1447 | 1176 |
| fading | 14371 | 13304 | 3562 |
| censored | 0 | 0 | 0 |
| interrupted | 72 | 71 | 72 |
| **total** | 19831 | 18486 | 3824 |

Flags among the three final classes (19759): one_day 1344, desktop_only 0, any 1344.

By whole duration (known only after the shift ends; used for the confirmatory duration test):

| Whole duration | Shifts | Quality OK |
|---|---|---|
| 1-2 weeks | 14371 | 13304 |
| 3 weeks | 1535 | 1447 |
| 4-5 weeks | 1536 | 1450 |
| 6+ weeks | 2317 | 2214 |
| not final | 72 | 71 |

### Author articles (secondary), ratio 4.0

| Class | All shifts | Quality OK (no flag) | Articles |
|---|---|---|---|
| sustained | 399 | 337 | 329 |
| intermediate | 241 | 202 | 221 |
| fading | 2481 | 1914 | 1164 |
| censored | 0 | 0 | 0 |
| interrupted | 10 | 7 | 10 |
| **total** | 3131 | 2460 | 1297 |

Flags among the three final classes (3121): one_day 658, desktop_only 25, any 668.

By whole duration (known only after the shift ends; used for the confirmatory duration test):

| Whole duration | Shifts | Quality OK |
|---|---|---|
| 1-2 weeks | 2481 | 1914 |
| 3 weeks | 241 | 202 |
| 4-5 weeks | 189 | 152 |
| 6+ weeks | 210 | 185 |
| not final | 10 | 7 |

### Positive controls on the interest side

Book article, release date used (month of the record, day approximate), shifts starting within 8 weeks before or after it.

| Control article | Release | Shifts within +/- 8 weeks (start week, class, size, whole duration, flag) |
|---|---|---|
| The Queen's Gambit (novel) | 2020-10-23 | none detected |
| The Duke and I | 2020-12-25 | none detected |
| Dune (novel) | 2021-10-22 | none detected |
| Where the Crawdads Sing | 2022-07-15 | none detected |
| American Prometheus | 2023-07-21 | none detected |
| Killers of the Flower Moon | 2023-10-20 | none detected |
| Shōgun (novel) | 2024-02-27 | 2024-01-22, fading, x4.7, 1 wk, ok |
