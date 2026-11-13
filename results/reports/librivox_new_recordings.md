# LibriVox new recordings: Wikipedia alone and added (exploratory)

Record: prereg/DEVIATIONS.md, LibriVox new recordings (14 November 2026). Recordings: 3,804; with an author article 3,024, with a book article 609. AUC for the top 20% of each test quarter, averaged over quarters; 95% intervals from author draws within quarters. W: Wikipedia alone; R: platform record (metadata and earlier recordings); RW: both.

| Model | Recordings | Quarters | Rows | W | R | RW | RW minus R | Spearman W / R / RW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LightGBM | all | 20 (2020Q1 to 2024Q4) | 2,651 | 0.558 (0.526 to 0.588) | 0.726 (0.694 to 0.748) | 0.725 (0.689 to 0.742) | -0.002 (-0.027 to +0.017) | 0.132 / 0.416 / 0.425 |
| LightGBM | author with no earlier recording | 20 (2020Q1 to 2024Q4) | 1,473 | 0.551 (0.506 to 0.588) | 0.683 (0.642 to 0.720) | 0.685 (0.642 to 0.719) | +0.002 (-0.033 to +0.033) | 0.094 / 0.351 / 0.360 |
| Ridge | all | 20 (2020Q1 to 2024Q4) | 2,651 | 0.579 (0.544 to 0.606) | 0.770 (0.738 to 0.787) | 0.766 (0.732 to 0.784) | -0.003 (-0.016 to +0.008) | 0.169 / 0.546 / 0.537 |
| Ridge | author with no earlier recording | 20 (2020Q1 to 2024Q4) | 1,473 | 0.563 (0.523 to 0.606) | 0.725 (0.682 to 0.756) | 0.731 (0.686 to 0.763) | +0.005 (-0.010 to +0.020) | 0.125 / 0.485 / 0.488 |
