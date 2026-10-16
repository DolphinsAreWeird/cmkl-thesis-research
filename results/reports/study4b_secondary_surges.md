# Study 4b: secondary surge definitions (Part B, horizon 2)

Made 2026-10-14 09:17. Addendum `prereg/addenda_4b/2026-10-14_a_secondary_surges.json`. Two extra surge definitions, each with its own classifiers and average precision (AP), reported beside the primary log(1.3) surge and never instead of it. Models (CatBoost classifier, logistic regression), feature sets (D, D+W, D+W+S), horizon 2, walk-forward retraining at every origin, strata, 2,000-draw block bootstrap (blocks of 3 months, seed 20261013) and the helps rule (interval above zero) are the same as for the primary surge. In the base-rate surge the cut-off (98th percentile of the 2-month change in log share within the same format and level) is computed on the training rows of each origin only and then applied to that origin's training labels and test rows, so the label of a test row never uses the test month or later months; the share of surges in the test rows therefore differs a little from 2%. The primary evaluation was read before this step was built; no setting was changed after it.

## Side by side: primary and secondary definitions (print and ebook pooled)

AP difference for the interest comparisons (D+W and D+W+S against D):

| definition | level | model_class | comparison | surges | ap_base | ap_new | ap_diff | ci_lo | ci_hi | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base98 | middle | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 392 | 0.1273 | 0.1820 | 0.0547 | -0.0070 | 0.0811 | no |
| pct20 | middle | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 381 | 0.1233 | 0.1780 | 0.0547 | 0.0118 | 0.0775 | yes |
| primary (log 1.3) | middle | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 169 | 0.0974 | 0.1360 | 0.0386 | 0.0054 | 0.0766 | yes |
| base98 | middle | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 392 | 0.1273 | 0.2006 | 0.0733 | 0.0023 | 0.1001 | yes |
| pct20 | middle | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 381 | 0.1233 | 0.1650 | 0.0417 | 0.0137 | 0.0890 | yes |
| primary (log 1.3) | middle | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 169 | 0.0974 | 0.1084 | 0.0110 | -0.0019 | 0.0769 | no |
| base98 | middle | logistic | logistic/D+W vs logistic/D | 392 | 0.1370 | 0.1541 | 0.0171 | 0.0076 | 0.0359 | yes |
| pct20 | middle | logistic | logistic/D+W vs logistic/D | 381 | 0.1424 | 0.1596 | 0.0172 | 0.0058 | 0.0453 | yes |
| primary (log 1.3) | middle | logistic | logistic/D+W vs logistic/D | 169 | 0.1258 | 0.1487 | 0.0229 | 0.0063 | 0.0758 | yes |
| base98 | middle | logistic | logistic/D+W+S vs logistic/D | 392 | 0.1370 | 0.1556 | 0.0186 | 0.0090 | 0.0387 | yes |
| pct20 | middle | logistic | logistic/D+W+S vs logistic/D | 381 | 0.1424 | 0.1654 | 0.0230 | 0.0094 | 0.0529 | yes |
| primary (log 1.3) | middle | logistic | logistic/D+W+S vs logistic/D | 169 | 0.1258 | 0.1479 | 0.0221 | 0.0063 | 0.0703 | yes |
| base98 | narrow | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 725 | 0.1112 | 0.1587 | 0.0475 | 0.0048 | 0.0631 | yes |
| pct20 | narrow | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 945 | 0.1329 | 0.1638 | 0.0309 | 0.0058 | 0.0419 | yes |
| primary (log 1.3) | narrow | catboost_clf | catboost_clf/D+W vs catboost_clf/D | 422 | 0.0799 | 0.1113 | 0.0314 | 0.0096 | 0.0519 | yes |
| base98 | narrow | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 725 | 0.1112 | 0.1580 | 0.0468 | 0.0097 | 0.0641 | yes |
| pct20 | narrow | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 945 | 0.1329 | 0.1580 | 0.0251 | 0.0084 | 0.0468 | yes |
| primary (log 1.3) | narrow | catboost_clf | catboost_clf/D+W+S vs catboost_clf/D | 422 | 0.0799 | 0.0851 | 0.0051 | -0.0019 | 0.0232 | no |
| base98 | narrow | logistic | logistic/D+W vs logistic/D | 725 | 0.0963 | 0.1032 | 0.0069 | 0.0026 | 0.0293 | yes |
| pct20 | narrow | logistic | logistic/D+W vs logistic/D | 945 | 0.1161 | 0.1230 | 0.0069 | 0.0035 | 0.0201 | yes |
| primary (log 1.3) | narrow | logistic | logistic/D+W vs logistic/D | 422 | 0.0822 | 0.0881 | 0.0059 | 0.0014 | 0.0334 | yes |
| base98 | narrow | logistic | logistic/D+W+S vs logistic/D | 725 | 0.0963 | 0.1029 | 0.0066 | 0.0024 | 0.0281 | yes |
| pct20 | narrow | logistic | logistic/D+W+S vs logistic/D | 945 | 0.1161 | 0.1225 | 0.0064 | 0.0025 | 0.0223 | yes |
| primary (log 1.3) | narrow | logistic | logistic/D+W+S vs logistic/D | 422 | 0.0822 | 0.0898 | 0.0076 | 0.0017 | 0.0346 | yes |

AP and recall in the top 10 of every model:

| definition | level | model | surges | base_rate | ap | ap_over_base | recall_top | recall_random |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base98 | middle | catboost_clf/D | 392 | 0.0292 | 0.1273 | 4.3620 | 0.4209 | 0.1204 |
| pct20 | middle | catboost_clf/D | 381 | 0.0284 | 0.1233 | 4.3480 | 0.4409 | 0.1198 |
| primary (log 1.3) | middle | catboost_clf/D | 169 | 0.0126 | 0.0974 | 7.7429 | 0.5562 | 0.1203 |
| base98 | middle | catboost_clf/D+W | 392 | 0.0292 | 0.1820 | 6.2370 | 0.4133 | 0.1204 |
| pct20 | middle | catboost_clf/D+W | 381 | 0.0284 | 0.1780 | 6.2766 | 0.4436 | 0.1198 |
| primary (log 1.3) | middle | catboost_clf/D+W | 169 | 0.0126 | 0.1360 | 10.8108 | 0.5385 | 0.1203 |
| base98 | middle | catboost_clf/D+W+S | 392 | 0.0292 | 0.2006 | 6.8725 | 0.4235 | 0.1204 |
| pct20 | middle | catboost_clf/D+W+S | 381 | 0.0284 | 0.1650 | 5.8167 | 0.4252 | 0.1198 |
| primary (log 1.3) | middle | catboost_clf/D+W+S | 169 | 0.0126 | 0.1084 | 8.6178 | 0.5266 | 0.1203 |
| base98 | middle | logistic/D | 392 | 0.0292 | 0.1370 | 4.6934 | 0.4464 | 0.1204 |
| pct20 | middle | logistic/D | 381 | 0.0284 | 0.1424 | 5.0206 | 0.4462 | 0.1198 |
| primary (log 1.3) | middle | logistic/D | 169 | 0.0126 | 0.1258 | 9.9954 | 0.5503 | 0.1203 |
| base98 | middle | logistic/D+W | 392 | 0.0292 | 0.1541 | 5.2803 | 0.4464 | 0.1204 |
| pct20 | middle | logistic/D+W | 381 | 0.0284 | 0.1596 | 5.6285 | 0.4541 | 0.1198 |
| primary (log 1.3) | middle | logistic/D+W | 169 | 0.0126 | 0.1487 | 11.8183 | 0.5562 | 0.1203 |
| base98 | middle | logistic/D+W+S | 392 | 0.0292 | 0.1556 | 5.3314 | 0.4541 | 0.1204 |
| pct20 | middle | logistic/D+W+S | 381 | 0.0284 | 0.1654 | 5.8314 | 0.4567 | 0.1198 |
| primary (log 1.3) | middle | logistic/D+W+S | 169 | 0.0126 | 0.1479 | 11.7532 | 0.5680 | 0.1203 |
| base98 | narrow | catboost_clf/D | 725 | 0.0293 | 0.1112 | 3.7931 | 0.2786 | 0.0640 |
| pct20 | narrow | catboost_clf/D | 945 | 0.0382 | 0.1329 | 3.4776 | 0.2529 | 0.0628 |
| primary (log 1.3) | narrow | catboost_clf/D | 422 | 0.0171 | 0.0799 | 4.6855 | 0.3152 | 0.0630 |
| base98 | narrow | catboost_clf/D+W | 725 | 0.0293 | 0.1587 | 5.4153 | 0.2938 | 0.0640 |
| pct20 | narrow | catboost_clf/D+W | 945 | 0.0382 | 0.1638 | 4.2874 | 0.2540 | 0.0628 |
| primary (log 1.3) | narrow | catboost_clf/D+W | 422 | 0.0171 | 0.1113 | 6.5250 | 0.3389 | 0.0630 |
| base98 | narrow | catboost_clf/D+W+S | 725 | 0.0293 | 0.1580 | 5.3910 | 0.2855 | 0.0640 |
| pct20 | narrow | catboost_clf/D+W+S | 945 | 0.0382 | 0.1580 | 4.1354 | 0.2571 | 0.0628 |
| primary (log 1.3) | narrow | catboost_clf/D+W+S | 422 | 0.0171 | 0.0851 | 4.9872 | 0.3365 | 0.0630 |
| base98 | narrow | logistic/D | 725 | 0.0293 | 0.0963 | 3.2851 | 0.2841 | 0.0640 |
| pct20 | narrow | logistic/D | 945 | 0.0382 | 0.1161 | 3.0387 | 0.2508 | 0.0628 |
| primary (log 1.3) | narrow | logistic/D | 422 | 0.0171 | 0.0822 | 4.8178 | 0.3175 | 0.0630 |
| base98 | narrow | logistic/D+W | 725 | 0.0293 | 0.1032 | 3.5204 | 0.2745 | 0.0640 |
| pct20 | narrow | logistic/D+W | 945 | 0.0382 | 0.1230 | 3.2183 | 0.2466 | 0.0628 |
| primary (log 1.3) | narrow | logistic/D+W | 422 | 0.0171 | 0.0881 | 5.1657 | 0.3152 | 0.0630 |
| base98 | narrow | logistic/D+W+S | 725 | 0.0293 | 0.1029 | 3.5102 | 0.2745 | 0.0640 |
| pct20 | narrow | logistic/D+W+S | 945 | 0.0382 | 0.1225 | 3.2064 | 0.2455 | 0.0628 |
| primary (log 1.3) | narrow | logistic/D+W+S | 422 | 0.0171 | 0.0898 | 5.2631 | 0.3128 | 0.0630 |

## base-rate surge (top 2% of changes within format and level, cut-off from training rows only)

Forecast rows 322,824 from 87 origins (2019-01 to 2026-06).

Cut-offs applied to test rows (change in log share; range over origins):

| format | min | median | max |
| --- | --- | --- | --- |
| audiobook | 0.1364 | 0.1739 | 0.2114 |
| ebook | 0.1421 | 0.1815 | 0.1876 |
| print | 0.1780 | 0.2183 | 0.2297 |

### Metrics

| scope | format | level | model | n | surges | base_rate | ap | ap_over_base | recall_top | recall_random | origins_with_surge | brier | brier_base_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D | 12,953 | 459 | 0.0354 | 0.1213 | 3.4229 | 0.2832 | 0.0591 | 77 | 0.0394 | 0.0342 |
| format x level | print | narrow | catboost_clf/D+W | 12,953 | 459 | 0.0354 | 0.1618 | 4.5663 | 0.2898 | 0.0591 | 77 | 0.0343 | 0.0342 |
| format x level | print | narrow | catboost_clf/D+W+S | 12,953 | 459 | 0.0354 | 0.1601 | 4.5192 | 0.2767 | 0.0591 | 77 | 0.0351 | 0.0342 |
| format x level | print | narrow | logistic/D | 12,953 | 459 | 0.0354 | 0.1118 | 3.1542 | 0.2854 | 0.0591 | 77 | 0.0424 | 0.0342 |
| format x level | print | narrow | logistic/D+W | 12,953 | 459 | 0.0354 | 0.1152 | 3.2520 | 0.2789 | 0.0591 | 77 | 0.0426 | 0.0342 |
| format x level | print | narrow | logistic/D+W+S | 12,953 | 459 | 0.0354 | 0.1148 | 3.2390 | 0.2789 | 0.0591 | 77 | 0.0429 | 0.0342 |
| format x level | print | middle | catboost_clf/D | 6,577 | 232 | 0.0353 | 0.1415 | 4.0103 | 0.4698 | 0.1184 | 74 | 0.0464 | 0.0340 |
| format x level | print | middle | catboost_clf/D+W | 6,577 | 232 | 0.0353 | 0.1840 | 5.2173 | 0.4440 | 0.1184 | 74 | 0.0387 | 0.0340 |
| format x level | print | middle | catboost_clf/D+W+S | 6,577 | 232 | 0.0353 | 0.2055 | 5.8244 | 0.4655 | 0.1184 | 74 | 0.0385 | 0.0340 |
| format x level | print | middle | logistic/D | 6,577 | 232 | 0.0353 | 0.1532 | 4.3430 | 0.4871 | 0.1184 | 74 | 0.0362 | 0.0340 |
| format x level | print | middle | logistic/D+W | 6,577 | 232 | 0.0353 | 0.1639 | 4.6467 | 0.5000 | 0.1184 | 74 | 0.0359 | 0.0340 |
| format x level | print | middle | logistic/D+W+S | 6,577 | 232 | 0.0353 | 0.1645 | 4.6621 | 0.5086 | 0.1184 | 74 | 0.0361 | 0.0340 |
| format x level | ebook | narrow | catboost_clf/D | 11,783 | 266 | 0.0226 | 0.1368 | 6.0609 | 0.2707 | 0.0725 | 77 | 0.0214 | 0.0221 |
| format x level | ebook | narrow | catboost_clf/D+W | 11,783 | 266 | 0.0226 | 0.1692 | 7.4942 | 0.3008 | 0.0725 | 77 | 0.0202 | 0.0221 |
| format x level | ebook | narrow | catboost_clf/D+W+S | 11,783 | 266 | 0.0226 | 0.1669 | 7.3949 | 0.3008 | 0.0725 | 77 | 0.0202 | 0.0221 |
| format x level | ebook | narrow | logistic/D | 11,783 | 266 | 0.0226 | 0.1020 | 4.5162 | 0.2820 | 0.0725 | 77 | 0.0216 | 0.0221 |
| format x level | ebook | narrow | logistic/D+W | 11,783 | 266 | 0.0226 | 0.1251 | 5.5427 | 0.2669 | 0.0725 | 77 | 0.0212 | 0.0221 |
| format x level | ebook | narrow | logistic/D+W+S | 11,783 | 266 | 0.0226 | 0.1249 | 5.5307 | 0.2669 | 0.0725 | 77 | 0.0212 | 0.0221 |
| format x level | ebook | middle | catboost_clf/D | 6,856 | 160 | 0.0233 | 0.1863 | 7.9846 | 0.3500 | 0.1233 | 67 | 0.0216 | 0.0228 |
| format x level | ebook | middle | catboost_clf/D+W | 6,856 | 160 | 0.0233 | 0.2258 | 9.6738 | 0.3688 | 0.1233 | 67 | 0.0199 | 0.0228 |
| format x level | ebook | middle | catboost_clf/D+W+S | 6,856 | 160 | 0.0233 | 0.2202 | 9.4349 | 0.3625 | 0.1233 | 67 | 0.0199 | 0.0228 |
| format x level | ebook | middle | logistic/D | 6,856 | 160 | 0.0233 | 0.1599 | 6.8530 | 0.3875 | 0.1233 | 67 | 0.0212 | 0.0228 |
| format x level | ebook | middle | logistic/D+W | 6,856 | 160 | 0.0233 | 0.1833 | 7.8538 | 0.3688 | 0.1233 | 67 | 0.0208 | 0.0228 |
| format x level | ebook | middle | logistic/D+W+S | 6,856 | 160 | 0.0233 | 0.1841 | 7.8866 | 0.3750 | 0.1233 | 67 | 0.0208 | 0.0228 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D | 9,271 | 265 | 0.0286 | 0.1251 | 4.3779 | 0.2830 | 0.0930 | 73 | 0.0276 | 0.0278 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W | 9,271 | 265 | 0.0286 | 0.1547 | 5.4137 | 0.2868 | 0.0930 | 73 | 0.0261 | 0.0278 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S | 9,271 | 265 | 0.0286 | 0.1547 | 5.4110 | 0.2943 | 0.0930 | 73 | 0.0261 | 0.0278 |
| format x level (secondary) | audiobook | narrow | logistic/D | 9,271 | 265 | 0.0286 | 0.1116 | 3.9036 | 0.2792 | 0.0930 | 73 | 0.0271 | 0.0278 |
| format x level (secondary) | audiobook | narrow | logistic/D+W | 9,271 | 265 | 0.0286 | 0.1204 | 4.2139 | 0.2830 | 0.0930 | 73 | 0.0269 | 0.0278 |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S | 9,271 | 265 | 0.0286 | 0.1175 | 4.1107 | 0.2755 | 0.0930 | 73 | 0.0269 | 0.0278 |
| format x level (secondary) | audiobook | middle | catboost_clf/D | 6,364 | 184 | 0.0289 | 0.1544 | 5.3413 | 0.3261 | 0.1337 | 69 | 0.0277 | 0.0281 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W | 6,364 | 184 | 0.0289 | 0.1798 | 6.2194 | 0.3370 | 0.1337 | 69 | 0.0256 | 0.0281 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S | 6,364 | 184 | 0.0289 | 0.1860 | 6.4346 | 0.3587 | 0.1337 | 69 | 0.0256 | 0.0281 |
| format x level (secondary) | audiobook | middle | logistic/D | 6,364 | 184 | 0.0289 | 0.1320 | 4.5640 | 0.3043 | 0.1337 | 69 | 0.0269 | 0.0281 |
| format x level (secondary) | audiobook | middle | logistic/D+W | 6,364 | 184 | 0.0289 | 0.1436 | 4.9680 | 0.2989 | 0.1337 | 69 | 0.0268 | 0.0281 |
| format x level (secondary) | audiobook | middle | logistic/D+W+S | 6,364 | 184 | 0.0289 | 0.1348 | 4.6613 | 0.2826 | 0.1337 | 69 | 0.0269 | 0.0281 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D | 24,736 | 725 | 0.0293 | 0.1112 | 3.7931 | 0.2786 | 0.0640 | 154 | 0.0308 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W | 24,736 | 725 | 0.0293 | 0.1587 | 5.4153 | 0.2938 | 0.0640 | 154 | 0.0276 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S | 24,736 | 725 | 0.0293 | 0.1580 | 5.3910 | 0.2855 | 0.0640 | 154 | 0.0280 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D | 24,736 | 725 | 0.0293 | 0.0963 | 3.2851 | 0.2841 | 0.0640 | 154 | 0.0325 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W | 24,736 | 725 | 0.0293 | 0.1032 | 3.5204 | 0.2745 | 0.0640 | 154 | 0.0324 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S | 24,736 | 725 | 0.0293 | 0.1029 | 3.5102 | 0.2745 | 0.0640 | 154 | 0.0325 | 0.0285 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D | 13,433 | 392 | 0.0292 | 0.1273 | 4.3620 | 0.4209 | 0.1204 | 141 | 0.0337 | 0.0283 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W | 13,433 | 392 | 0.0292 | 0.1820 | 6.2370 | 0.4133 | 0.1204 | 141 | 0.0291 | 0.0283 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S | 13,433 | 392 | 0.0292 | 0.2006 | 6.8725 | 0.4235 | 0.1204 | 141 | 0.0290 | 0.0283 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D | 13,433 | 392 | 0.0292 | 0.1370 | 4.6934 | 0.4464 | 0.1204 | 141 | 0.0285 | 0.0283 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W | 13,433 | 392 | 0.0292 | 0.1541 | 5.2803 | 0.4464 | 0.1204 | 141 | 0.0282 | 0.0283 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S | 13,433 | 392 | 0.0292 | 0.1556 | 5.3314 | 0.4541 | 0.1204 | 141 | 0.0283 | 0.0283 |

### AP difference with block bootstrap

- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1112 to 0.1587, difference +0.0475, interval +0.0048 to +0.0631, 725 surges).
- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, middle level: **does not help** (AP 0.1273 to 0.1820, difference +0.0547, interval -0.0070 to +0.0811, 392 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1112 to 0.1580, difference +0.0468, interval +0.0097 to +0.0641, 725 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, middle level: **interest helps** (AP 0.1273 to 0.2006, difference +0.0733, interval +0.0023 to +0.1001, 392 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.0963 to 0.1032, difference +0.0069, interval +0.0026 to +0.0293, 725 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1370 to 0.1541, difference +0.0171, interval +0.0076 to +0.0359, 392 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.0963 to 0.1029, difference +0.0066, interval +0.0024 to +0.0281, 725 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1370 to 0.1556, difference +0.0186, interval +0.0090 to +0.0387, 392 surges).

| scope | format | level | comparison | model_class | surges | ap_base | ap_new | ap_diff | ci_lo | ci_hi | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 459 | 0.1213 | 0.1618 | 0.0405 | -0.0048 | 0.0554 | no |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 459 | 0.1213 | 0.1601 | 0.0388 | 0.0018 | 0.0584 | yes |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 459 | 0.1618 | 0.1601 | -0.0017 | -0.0077 | 0.0149 | no |
| format x level | print | narrow | logistic/D+W vs logistic/D | logistic | 459 | 0.1118 | 0.1152 | 0.0035 | 0.0008 | 0.0208 | yes |
| format x level | print | narrow | logistic/D+W+S vs logistic/D | logistic | 459 | 0.1118 | 0.1148 | 0.0030 | 0.0002 | 0.0192 | yes |
| format x level | print | narrow | logistic/D+W+S vs logistic/D+W | logistic | 459 | 0.1152 | 0.1148 | -0.0005 | -0.0043 | 0.0006 | no |
| format x level | print | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 232 | 0.1415 | 0.1840 | 0.0426 | -0.0245 | 0.0744 | no |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 232 | 0.1415 | 0.2055 | 0.0640 | -0.0092 | 0.0982 | no |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 232 | 0.1840 | 0.2055 | 0.0214 | 0.0014 | 0.0344 | yes |
| format x level | print | middle | logistic/D+W vs logistic/D | logistic | 232 | 0.1532 | 0.1639 | 0.0107 | 0.0025 | 0.0273 | yes |
| format x level | print | middle | logistic/D+W+S vs logistic/D | logistic | 232 | 0.1532 | 0.1645 | 0.0113 | 0.0017 | 0.0287 | yes |
| format x level | print | middle | logistic/D+W+S vs logistic/D+W | logistic | 232 | 0.1639 | 0.1645 | 0.0005 | -0.0049 | 0.0069 | no |
| format x level | ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 266 | 0.1368 | 0.1692 | 0.0324 | -0.0041 | 0.0623 | no |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 266 | 0.1368 | 0.1669 | 0.0301 | -0.0034 | 0.0548 | no |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 266 | 0.1692 | 0.1669 | -0.0022 | -0.0121 | 0.0069 | no |
| format x level | ebook | narrow | logistic/D+W vs logistic/D | logistic | 266 | 0.1020 | 0.1251 | 0.0232 | 0.0082 | 0.0404 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 266 | 0.1020 | 0.1249 | 0.0229 | 0.0066 | 0.0439 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 266 | 0.1251 | 0.1249 | -0.0003 | -0.0063 | 0.0073 | no |
| format x level | ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 160 | 0.1863 | 0.2258 | 0.0394 | -0.0092 | 0.0621 | no |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 160 | 0.1863 | 0.2202 | 0.0338 | -0.0122 | 0.0556 | no |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 160 | 0.2258 | 0.2202 | -0.0056 | -0.0130 | 0.0037 | no |
| format x level | ebook | middle | logistic/D+W vs logistic/D | logistic | 160 | 0.1599 | 0.1833 | 0.0234 | 0.0026 | 0.0452 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D | logistic | 160 | 0.1599 | 0.1841 | 0.0241 | 0.0058 | 0.0454 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 160 | 0.1833 | 0.1841 | 0.0008 | -0.0073 | 0.0074 | no |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 265 | 0.1251 | 0.1547 | 0.0296 | 0.0021 | 0.0533 | yes |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 265 | 0.1251 | 0.1547 | 0.0295 | 0.0022 | 0.0529 | yes |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 265 | 0.1547 | 0.1547 | -0.0001 | -0.0082 | 0.0064 | no |
| format x level (secondary) | audiobook | narrow | logistic/D+W vs logistic/D | logistic | 265 | 0.1116 | 0.1204 | 0.0089 | 0.0017 | 0.0176 | yes |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D | logistic | 265 | 0.1116 | 0.1175 | 0.0059 | -0.0004 | 0.0151 | no |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 265 | 0.1204 | 0.1175 | -0.0029 | -0.0088 | 0.0032 | no |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 184 | 0.1544 | 0.1798 | 0.0254 | 0.0036 | 0.0462 | yes |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 184 | 0.1544 | 0.1860 | 0.0316 | 0.0083 | 0.0508 | yes |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 184 | 0.1798 | 0.1860 | 0.0062 | -0.0049 | 0.0166 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W vs logistic/D | logistic | 184 | 0.1320 | 0.1436 | 0.0117 | 0.0002 | 0.0212 | yes |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D | logistic | 184 | 0.1320 | 0.1348 | 0.0028 | -0.0060 | 0.0135 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D+W | logistic | 184 | 0.1436 | 0.1348 | -0.0089 | -0.0187 | 0.0021 | no |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 725 | 0.1112 | 0.1587 | 0.0475 | 0.0048 | 0.0631 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 725 | 0.1112 | 0.1580 | 0.0468 | 0.0097 | 0.0641 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 725 | 0.1587 | 0.1580 | -0.0007 | -0.0049 | 0.0097 | no |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W vs logistic/D | logistic | 725 | 0.0963 | 0.1032 | 0.0069 | 0.0026 | 0.0293 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 725 | 0.0963 | 0.1029 | 0.0066 | 0.0024 | 0.0281 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 725 | 0.1032 | 0.1029 | -0.0003 | -0.0035 | 0.0007 | no |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 392 | 0.1273 | 0.1820 | 0.0547 | -0.0070 | 0.0811 | no |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 392 | 0.1273 | 0.2006 | 0.0733 | 0.0023 | 0.1001 | yes |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 392 | 0.1820 | 0.2006 | 0.0185 | -0.0005 | 0.0303 | no |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W vs logistic/D | logistic | 392 | 0.1370 | 0.1541 | 0.0171 | 0.0076 | 0.0359 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D | logistic | 392 | 0.1370 | 0.1556 | 0.0186 | 0.0090 | 0.0387 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 392 | 0.1541 | 0.1556 | 0.0015 | -0.0026 | 0.0065 | no |

### Showcases (illustrations, not tests)

| category | level | node_id | format | origin | target_month | note | actual_change | cutoff | surge | n_in_group | p catboost_clf/D | rank catboost_clf/D | p catboost_clf/D+W | rank catboost_clf/D+W | p catboost_clf/D+W+S | rank catboost_clf/D+W+S | p logistic/D | rank logistic/D | p logistic/D+W | rank logistic/D+W | p logistic/D+W+S | rank logistic/D+W+S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Race and racism | narrow | B05.M02.N02 | print | 2020-04 | 2020-06 | not forecast at this origin |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Race and racism | narrow | B05.M02.N02 | ebook | 2020-04 | 2020-06 |  | 1.633 | 0.181 | 1.000 | 124.000 | 0.006 | 78.000 | 0.009 | 65.000 | 0.012 | 62.000 | 0.019 | 32.000 | 0.021 | 28.000 | 0.021 | 29.000 |
| Epidemics and plagues | narrow | B15.M04.N05 | ebook | 2020-01 | 2020-03 |  | 0.188 | 0.168 | 1.000 | 122.000 | 0.020 | 26.000 | 0.010 | 75.000 | 0.011 | 60.000 | 0.006 | 72.000 | 0.005 | 85.000 | 0.005 | 84.000 |

## 20% surge (change >= log 1.2 = 0.1823)

Forecast rows 322,824 from 87 origins (2019-01 to 2026-06).

### Metrics

| scope | format | level | model | n | surges | base_rate | ap | ap_over_base | recall_top | recall_random | origins_with_surge | brier | brier_base_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D | 12,953 | 685 | 0.0529 | 0.1460 | 2.7614 | 0.2409 | 0.0593 | 78 | 0.0536 | 0.0501 |
| format x level | print | narrow | catboost_clf/D+W | 12,953 | 685 | 0.0529 | 0.1671 | 3.1599 | 0.2423 | 0.0593 | 78 | 0.0508 | 0.0501 |
| format x level | print | narrow | catboost_clf/D+W+S | 12,953 | 685 | 0.0529 | 0.1620 | 3.0627 | 0.2482 | 0.0593 | 78 | 0.0512 | 0.0501 |
| format x level | print | narrow | logistic/D | 12,953 | 685 | 0.0529 | 0.1342 | 2.5382 | 0.2350 | 0.0593 | 78 | 0.0590 | 0.0501 |
| format x level | print | narrow | logistic/D+W | 12,953 | 685 | 0.0529 | 0.1368 | 2.5874 | 0.2336 | 0.0593 | 78 | 0.0595 | 0.0501 |
| format x level | print | narrow | logistic/D+W+S | 12,953 | 685 | 0.0529 | 0.1363 | 2.5766 | 0.2336 | 0.0593 | 78 | 0.0596 | 0.0501 |
| format x level | print | middle | catboost_clf/D | 6,577 | 264 | 0.0401 | 0.1378 | 3.4325 | 0.4697 | 0.1184 | 77 | 0.0513 | 0.0385 |
| format x level | print | middle | catboost_clf/D+W | 6,577 | 264 | 0.0401 | 0.1765 | 4.3968 | 0.4621 | 0.1184 | 77 | 0.0447 | 0.0385 |
| format x level | print | middle | catboost_clf/D+W+S | 6,577 | 264 | 0.0401 | 0.1637 | 4.0788 | 0.4432 | 0.1184 | 77 | 0.0452 | 0.0385 |
| format x level | print | middle | logistic/D | 6,577 | 264 | 0.0401 | 0.1588 | 3.9552 | 0.4659 | 0.1184 | 77 | 0.0404 | 0.0385 |
| format x level | print | middle | logistic/D+W | 6,577 | 264 | 0.0401 | 0.1681 | 4.1890 | 0.4811 | 0.1184 | 77 | 0.0401 | 0.0385 |
| format x level | print | middle | logistic/D+W+S | 6,577 | 264 | 0.0401 | 0.1742 | 4.3390 | 0.4773 | 0.1184 | 77 | 0.0397 | 0.0385 |
| format x level | ebook | narrow | catboost_clf/D | 11,783 | 260 | 0.0221 | 0.1347 | 6.1063 | 0.2846 | 0.0722 | 77 | 0.0209 | 0.0216 |
| format x level | ebook | narrow | catboost_clf/D+W | 11,783 | 260 | 0.0221 | 0.1612 | 7.3048 | 0.2846 | 0.0722 | 77 | 0.0199 | 0.0216 |
| format x level | ebook | narrow | catboost_clf/D+W+S | 11,783 | 260 | 0.0221 | 0.1651 | 7.4838 | 0.2808 | 0.0722 | 77 | 0.0198 | 0.0216 |
| format x level | ebook | narrow | logistic/D | 11,783 | 260 | 0.0221 | 0.0915 | 4.1471 | 0.2923 | 0.0722 | 77 | 0.0213 | 0.0216 |
| format x level | ebook | narrow | logistic/D+W | 11,783 | 260 | 0.0221 | 0.1171 | 5.3077 | 0.2808 | 0.0722 | 77 | 0.0208 | 0.0216 |
| format x level | ebook | narrow | logistic/D+W+S | 11,783 | 260 | 0.0221 | 0.1156 | 5.2396 | 0.2769 | 0.0722 | 77 | 0.0209 | 0.0216 |
| format x level | ebook | middle | catboost_clf/D | 6,856 | 117 | 0.0171 | 0.1845 | 10.8136 | 0.3761 | 0.1230 | 58 | 0.0164 | 0.0168 |
| format x level | ebook | middle | catboost_clf/D+W | 6,856 | 117 | 0.0171 | 0.2184 | 12.7960 | 0.4017 | 0.1230 | 58 | 0.0146 | 0.0168 |
| format x level | ebook | middle | catboost_clf/D+W+S | 6,856 | 117 | 0.0171 | 0.2254 | 13.2058 | 0.3846 | 0.1230 | 58 | 0.0144 | 0.0168 |
| format x level | ebook | middle | logistic/D | 6,856 | 117 | 0.0171 | 0.1422 | 8.3340 | 0.4017 | 0.1230 | 58 | 0.0157 | 0.0168 |
| format x level | ebook | middle | logistic/D+W | 6,856 | 117 | 0.0171 | 0.1849 | 10.8319 | 0.3932 | 0.1230 | 58 | 0.0150 | 0.0168 |
| format x level | ebook | middle | logistic/D+W+S | 6,856 | 117 | 0.0171 | 0.1853 | 10.8595 | 0.4103 | 0.1230 | 58 | 0.0151 | 0.0168 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D | 9,271 | 290 | 0.0313 | 0.1331 | 4.2548 | 0.2759 | 0.0878 | 74 | 0.0298 | 0.0303 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W | 9,271 | 290 | 0.0313 | 0.1526 | 4.8777 | 0.2759 | 0.0878 | 74 | 0.0286 | 0.0303 |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S | 9,271 | 290 | 0.0313 | 0.1571 | 5.0218 | 0.2724 | 0.0878 | 74 | 0.0285 | 0.0303 |
| format x level (secondary) | audiobook | narrow | logistic/D | 9,271 | 290 | 0.0313 | 0.1054 | 3.3702 | 0.2552 | 0.0878 | 74 | 0.0298 | 0.0303 |
| format x level (secondary) | audiobook | narrow | logistic/D+W | 9,271 | 290 | 0.0313 | 0.1155 | 3.6920 | 0.2448 | 0.0878 | 74 | 0.0295 | 0.0303 |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S | 9,271 | 290 | 0.0313 | 0.1128 | 3.6054 | 0.2448 | 0.0878 | 74 | 0.0295 | 0.0303 |
| format x level (secondary) | audiobook | middle | catboost_clf/D | 6,364 | 132 | 0.0207 | 0.1761 | 8.4913 | 0.3712 | 0.1324 | 58 | 0.0193 | 0.0203 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W | 6,364 | 132 | 0.0207 | 0.1978 | 9.5385 | 0.3939 | 0.1324 | 58 | 0.0181 | 0.0203 |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S | 6,364 | 132 | 0.0207 | 0.2011 | 9.6933 | 0.3788 | 0.1324 | 58 | 0.0180 | 0.0203 |
| format x level (secondary) | audiobook | middle | logistic/D | 6,364 | 132 | 0.0207 | 0.1504 | 7.2492 | 0.3485 | 0.1324 | 58 | 0.0189 | 0.0203 |
| format x level (secondary) | audiobook | middle | logistic/D+W | 6,364 | 132 | 0.0207 | 0.1592 | 7.6747 | 0.3636 | 0.1324 | 58 | 0.0186 | 0.0203 |
| format x level (secondary) | audiobook | middle | logistic/D+W+S | 6,364 | 132 | 0.0207 | 0.1535 | 7.4027 | 0.3712 | 0.1324 | 58 | 0.0187 | 0.0203 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D | 24,736 | 945 | 0.0382 | 0.1329 | 3.4776 | 0.2529 | 0.0628 | 155 | 0.0380 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W | 24,736 | 945 | 0.0382 | 0.1638 | 4.2874 | 0.2540 | 0.0628 | 155 | 0.0361 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S | 24,736 | 945 | 0.0382 | 0.1580 | 4.1354 | 0.2571 | 0.0628 | 155 | 0.0362 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D | 24,736 | 945 | 0.0382 | 0.1161 | 3.0387 | 0.2508 | 0.0628 | 155 | 0.0411 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W | 24,736 | 945 | 0.0382 | 0.1230 | 3.2183 | 0.2466 | 0.0628 | 155 | 0.0411 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S | 24,736 | 945 | 0.0382 | 0.1225 | 3.2064 | 0.2455 | 0.0628 | 155 | 0.0412 | 0.0367 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D | 13,433 | 381 | 0.0284 | 0.1233 | 4.3480 | 0.4409 | 0.1198 | 135 | 0.0335 | 0.0276 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W | 13,433 | 381 | 0.0284 | 0.1780 | 6.2766 | 0.4436 | 0.1198 | 135 | 0.0293 | 0.0276 |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S | 13,433 | 381 | 0.0284 | 0.1650 | 5.8167 | 0.4252 | 0.1198 | 135 | 0.0295 | 0.0276 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D | 13,433 | 381 | 0.0284 | 0.1424 | 5.0206 | 0.4462 | 0.1198 | 135 | 0.0278 | 0.0276 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W | 13,433 | 381 | 0.0284 | 0.1596 | 5.6285 | 0.4541 | 0.1198 | 135 | 0.0273 | 0.0276 |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S | 13,433 | 381 | 0.0284 | 0.1654 | 5.8314 | 0.4567 | 0.1198 | 135 | 0.0271 | 0.0276 |

### AP difference with block bootstrap

- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1329 to 0.1638, difference +0.0309, interval +0.0058 to +0.0419, 945 surges).
- catboost_clf: catboost_clf|D+W vs catboost_clf|D, print and ebook pooled, middle level: **interest helps** (AP 0.1233 to 0.1780, difference +0.0547, interval +0.0118 to +0.0775, 381 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1329 to 0.1580, difference +0.0251, interval +0.0084 to +0.0468, 945 surges).
- catboost_clf: catboost_clf|D+W+S vs catboost_clf|D, print and ebook pooled, middle level: **interest helps** (AP 0.1233 to 0.1650, difference +0.0417, interval +0.0137 to +0.0890, 381 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1161 to 0.1230, difference +0.0069, interval +0.0035 to +0.0201, 945 surges).
- logistic: logistic|D+W vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1424 to 0.1596, difference +0.0172, interval +0.0058 to +0.0453, 381 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, narrow level: **interest helps** (AP 0.1161 to 0.1225, difference +0.0064, interval +0.0025 to +0.0223, 945 surges).
- logistic: logistic|D+W+S vs logistic|D, print and ebook pooled, middle level: **interest helps** (AP 0.1424 to 0.1654, difference +0.0230, interval +0.0094 to +0.0529, 381 surges).

| scope | format | level | comparison | model_class | surges | ap_base | ap_new | ap_diff | ci_lo | ci_hi | helps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| format x level | print | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 685 | 0.1460 | 0.1671 | 0.0211 | -0.0025 | 0.0306 | no |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 685 | 0.1460 | 0.1620 | 0.0159 | 0.0013 | 0.0374 | yes |
| format x level | print | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 685 | 0.1671 | 0.1620 | -0.0051 | -0.0153 | 0.0191 | no |
| format x level | print | narrow | logistic/D+W vs logistic/D | logistic | 685 | 0.1342 | 0.1368 | 0.0026 | 0.0001 | 0.0100 | yes |
| format x level | print | narrow | logistic/D+W+S vs logistic/D | logistic | 685 | 0.1342 | 0.1363 | 0.0020 | -0.0008 | 0.0123 | no |
| format x level | print | narrow | logistic/D+W+S vs logistic/D+W | logistic | 685 | 0.1368 | 0.1363 | -0.0006 | -0.0033 | 0.0041 | no |
| format x level | print | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 264 | 0.1378 | 0.1765 | 0.0387 | -0.0019 | 0.0598 | no |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 264 | 0.1378 | 0.1637 | 0.0259 | 0.0022 | 0.0764 | yes |
| format x level | print | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 264 | 0.1765 | 0.1637 | -0.0128 | -0.0249 | 0.0257 | no |
| format x level | print | middle | logistic/D+W vs logistic/D | logistic | 264 | 0.1588 | 0.1681 | 0.0094 | 0.0011 | 0.0303 | yes |
| format x level | print | middle | logistic/D+W+S vs logistic/D | logistic | 264 | 0.1588 | 0.1742 | 0.0154 | 0.0041 | 0.0380 | yes |
| format x level | print | middle | logistic/D+W+S vs logistic/D+W | logistic | 264 | 0.1681 | 0.1742 | 0.0060 | -0.0011 | 0.0156 | no |
| format x level | ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 260 | 0.1347 | 0.1612 | 0.0264 | -0.0028 | 0.0443 | no |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 260 | 0.1347 | 0.1651 | 0.0304 | -0.0016 | 0.0514 | no |
| format x level | ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 260 | 0.1612 | 0.1651 | 0.0039 | -0.0049 | 0.0102 | no |
| format x level | ebook | narrow | logistic/D+W vs logistic/D | logistic | 260 | 0.0915 | 0.1171 | 0.0256 | 0.0088 | 0.0436 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 260 | 0.0915 | 0.1156 | 0.0241 | 0.0070 | 0.0455 | yes |
| format x level | ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 260 | 0.1171 | 0.1156 | -0.0015 | -0.0080 | 0.0061 | no |
| format x level | ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 117 | 0.1845 | 0.2184 | 0.0338 | 0.0018 | 0.0557 | yes |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 117 | 0.1845 | 0.2254 | 0.0408 | 0.0115 | 0.0625 | yes |
| format x level | ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 117 | 0.2184 | 0.2254 | 0.0070 | 0.0002 | 0.0154 | yes |
| format x level | ebook | middle | logistic/D+W vs logistic/D | logistic | 117 | 0.1422 | 0.1849 | 0.0426 | 0.0064 | 0.0848 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D | logistic | 117 | 0.1422 | 0.1853 | 0.0431 | 0.0088 | 0.0853 | yes |
| format x level | ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 117 | 0.1849 | 0.1853 | 0.0005 | -0.0060 | 0.0059 | no |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 290 | 0.1331 | 0.1526 | 0.0195 | -0.0016 | 0.0385 | no |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 290 | 0.1331 | 0.1571 | 0.0240 | 0.0033 | 0.0427 | yes |
| format x level (secondary) | audiobook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 290 | 0.1526 | 0.1571 | 0.0045 | -0.0050 | 0.0146 | no |
| format x level (secondary) | audiobook | narrow | logistic/D+W vs logistic/D | logistic | 290 | 0.1054 | 0.1155 | 0.0101 | 0.0032 | 0.0202 | yes |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D | logistic | 290 | 0.1054 | 0.1128 | 0.0074 | 0.0004 | 0.0184 | yes |
| format x level (secondary) | audiobook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 290 | 0.1155 | 0.1128 | -0.0027 | -0.0074 | 0.0021 | no |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 132 | 0.1761 | 0.1978 | 0.0217 | 0.0071 | 0.0370 | yes |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 132 | 0.1761 | 0.2011 | 0.0249 | 0.0060 | 0.0411 | yes |
| format x level (secondary) | audiobook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 132 | 0.1978 | 0.2011 | 0.0032 | -0.0053 | 0.0101 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W vs logistic/D | logistic | 132 | 0.1504 | 0.1592 | 0.0088 | -0.0019 | 0.0204 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D | logistic | 132 | 0.1504 | 0.1535 | 0.0032 | -0.0051 | 0.0147 | no |
| format x level (secondary) | audiobook | middle | logistic/D+W+S vs logistic/D+W | logistic | 132 | 0.1592 | 0.1535 | -0.0056 | -0.0157 | 0.0047 | no |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 945 | 0.1329 | 0.1638 | 0.0309 | 0.0058 | 0.0419 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 945 | 0.1329 | 0.1580 | 0.0251 | 0.0084 | 0.0468 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 945 | 0.1638 | 0.1580 | -0.0058 | -0.0169 | 0.0163 | no |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W vs logistic/D | logistic | 945 | 0.1161 | 0.1230 | 0.0069 | 0.0035 | 0.0201 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D | logistic | 945 | 0.1161 | 0.1225 | 0.0064 | 0.0025 | 0.0223 | yes |
| print+ebook pooled (primary) | print+ebook | narrow | logistic/D+W+S vs logistic/D+W | logistic | 945 | 0.1230 | 0.1225 | -0.0005 | -0.0026 | 0.0042 | no |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W vs catboost_clf/D | catboost_clf | 381 | 0.1233 | 0.1780 | 0.0547 | 0.0118 | 0.0775 | yes |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D | catboost_clf | 381 | 0.1233 | 0.1650 | 0.0417 | 0.0137 | 0.0890 | yes |
| print+ebook pooled (primary) | print+ebook | middle | catboost_clf/D+W+S vs catboost_clf/D+W | catboost_clf | 381 | 0.1780 | 0.1650 | -0.0130 | -0.0261 | 0.0230 | no |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W vs logistic/D | logistic | 381 | 0.1424 | 0.1596 | 0.0172 | 0.0058 | 0.0453 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D | logistic | 381 | 0.1424 | 0.1654 | 0.0230 | 0.0094 | 0.0529 | yes |
| print+ebook pooled (primary) | print+ebook | middle | logistic/D+W+S vs logistic/D+W | logistic | 381 | 0.1596 | 0.1654 | 0.0058 | -0.0005 | 0.0153 | no |

### Showcases (illustrations, not tests)

| category | level | node_id | format | origin | target_month | note | actual_change | cutoff | surge | n_in_group | p catboost_clf/D | rank catboost_clf/D | p catboost_clf/D+W | rank catboost_clf/D+W | p catboost_clf/D+W+S | rank catboost_clf/D+W+S | p logistic/D | rank logistic/D | p logistic/D+W | rank logistic/D+W | p logistic/D+W+S | rank logistic/D+W+S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Race and racism | narrow | B05.M02.N02 | print | 2020-04 | 2020-06 | not forecast at this origin |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Race and racism | narrow | B05.M02.N02 | ebook | 2020-04 | 2020-06 |  | 1.633 | 0.182 | 1.000 | 124.000 | 0.007 | 68.000 | 0.008 | 78.000 | 0.010 | 69.000 | 0.017 | 31.000 | 0.019 | 35.000 | 0.018 | 39.000 |
| Epidemics and plagues | narrow | B15.M04.N05 | ebook | 2020-01 | 2020-03 |  | 0.188 | 0.182 | 1.000 | 122.000 | 0.009 | 48.000 | 0.005 | 92.000 | 0.010 | 53.000 | 0.004 | 73.000 | 0.004 | 81.000 | 0.004 | 82.000 |
