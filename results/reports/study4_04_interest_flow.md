# Study 4, step 04: interest flow (secondary task)

Made 2026-10-13 23:00. Record SHA-256 `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`. Target: log mean weekly Wikipedia share of the category in month t+1. Naive: last 4 weeks' mean. CatBoost: W features plus log weekly shares at lags 1, 2, 3, 4, 5, 6, 7, 8, 52 (see README for the lag convention). Origins 2019-01 to 2026-08; 30,176 category-months, 328 categories (narrow and middle levels).

Skill = 1 - MAE(CatBoost) / MAE(naive); interval from the moving-block bootstrap (3-month blocks, 2,000 resamples, seed 20261013); DM one-sided, Newey-West lag 3. Spearman: forecast change against actual change (both measured from the naive level) across categories within each month, averaged. AUC: score = forecast minus log of the normal level (median of the 26 weeks before the last week), outcome = next month at least 1.5 times normal; base_rate is the share of category-months that reached it.

| level | n | months | mae_naive | mae_catboost | skill | ci_lo | ci_hi | dm_stat | dm_p | spearman | auc_naive | auc_catboost | base_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle | 7,912 | 92 | 0.089 | 0.078 | 0.127 | 0.101 | 0.150 | 10.042 | 0.000 | 0.217 | 0.773 | 0.772 | 0.020 |
| narrow | 22,264 | 92 | 0.095 | 0.086 | 0.086 | 0.067 | 0.105 | 8.142 | 0.000 | 0.209 | 0.806 | 0.801 | 0.021 |
| all | 30,176 | 92 | 0.093 | 0.084 | 0.096 | 0.076 | 0.115 | 8.973 | 0.000 | 0.213 | 0.798 | 0.794 | 0.021 |
