# Theme level: does duration still carry the effect once size is in the model?

Khant Phyo Wai, student ID 01323050. Exploratory, theme level, outcomes already seen; not in any record. Code: code/study2r_fix/20_theme_size_vs_duration.py (run 2026-10-14 21:16).

## Question and method

Study 2R (single books) found that once log2 peak size is in the model, log2 whole duration adds nothing (duration -0.022, size 0.152 per doubling). Here the same joint model is fitted on theme shifts: effect = a + b1 * log2(whole duration in weeks) + b2 * log2(whole peak ratio). Both coefficients are per doubling. Whole duration and whole peak come from the interest shift table (data/db/interest/shifts.parquet), joined to each effect row on source, theme and start week. Intervals are 95% percentile intervals of a bootstrap that resamples themes (2,000 resamples, seed 20261013). "corr(dur, peak)" is the correlation of the two predictors across shifts; "corr of coefficients" is the correlation of the two bootstrap coefficient estimates. Effects: Study 3 synthetic-control effect for months 0 to +2 (Wikipedia, narrow and middle themes, main non-seasonal analysis, one row per shift and format); Study 3b tau for months 0 to +2 (Wikipedia, narrow and middle, Seattle formats jointly, sparse and zero-count tests left out).

Study 3 rows (Wikipedia, narrow and middle, main analysis, tested, synthetic control ok): 1333; with a finite effect and a joined duration and peak: 1261.
Study 3b rows (Wikipedia, narrow and middle, main analysis, tested, not sparse, finite tau): 625; with duration and peak: 625.
Rows that did not join to the interest shift table (72 of Study 3) are dropped. Value-level (book subject) shifts in Study 3b have no whole duration or peak in the interest table and are not included.

## Results

| set | shifts | themes | duration coefficient | size (peak) coefficient | corr(dur, peak) | corr of coefficients | duration alone | size alone |
|---|---|---|---|---|---|---|---|---|
| Study 3 SC, print | 365 | 163 | 0.037 (0.011 to 0.065) | -0.025 (-0.074 to 0.006) | 0.55 | -0.34 | 0.029 | 0.010 |
| Study 3 SC, ebook | 379 | 153 | 0.033 (0.008 to 0.062) | -0.014 (-0.045 to 0.021) | 0.55 | -0.32 | 0.029 | 0.019 |
| Study 3 SC, audiobook | 312 | 135 | 0.044 (0.014 to 0.080) | -0.003 (-0.055 to 0.049) | 0.56 | 0.10 | 0.044 | 0.047 |
| Study 3 SC, librivox | 205 | 99 | 0.018 (-0.035 to 0.079) | -0.016 (-0.104 to 0.058) | 0.59 | -0.46 | 0.012 | 0.001 |
| Study 3 SC, print + ebook stacked | 744 | 188 | 0.035 (0.014 to 0.057) | -0.020 (-0.049 to 0.008) | 0.55 | -0.33 | 0.029 | 0.014 |
| Study 3 SC, print + ebook, narrow only | 492 | 133 | 0.031 (0.008 to 0.056) | -0.017 (-0.050 to 0.014) | 0.52 | -0.22 | 0.026 | 0.011 |
| Study 3 SC, print + ebook, middle only | 252 | 55 | 0.044 (-0.002 to 0.093) | -0.031 (-0.123 to 0.029) | 0.63 | -0.50 | 0.034 | 0.023 |
| Study 3 SC, print + ebook, clustered by broad theme | 744 | 19 | 0.035 (0.007 to 0.067) | -0.020 (-0.062 to 0.016) | 0.55 | -0.15 | 0.029 | 0.014 |
| Study 3b tau, Seattle (all formats jointly) | 625 | 230 | 0.021 (-0.013 to 0.053) | -0.008 (-0.055 to 0.043) | 0.57 | -0.52 | 0.019 | 0.015 |
| Study 3b tau, narrow only | 475 | 175 | 0.011 (-0.027 to 0.045) | -0.006 (-0.061 to 0.054) | 0.56 | -0.51 | 0.009 | 0.005 |
| Study 3b tau, middle only | 150 | 55 | 0.071 (0.021 to 0.133) | -0.026 (-0.112 to 0.032) | 0.63 | -0.33 | 0.063 | 0.064 |
| Study 3b tau, clustered by broad theme | 625 | 19 | 0.021 (-0.030 to 0.073) | -0.008 (-0.059 to 0.057) | 0.57 | -0.39 | 0.019 | 0.015 |

"duration alone" and "size alone" are single-predictor slopes for comparison (no interval). One-sided bootstrap p-values (slope at or below 0) are in data/reports/theme_size_vs_duration.csv.

## Reading

- Study 3 (print and ebook stacked, 744 shift-format rows in 188 themes): duration keeps a positive coefficient with size in the model, 0.035 (0.014 to 0.057), and its interval stays above zero in print, ebook and audiobook separately. Size does not carry the effect: -0.020 (-0.049 to 0.008), a slightly negative point estimate with an interval that includes zero in every format. The two predictors correlate at 0.55 (lower than the 0.72 of single books) and the two estimates trade off against each other (correlation -0.33), which is why each is less precise than when alone.
- Study 3b (Seattle tau, 625 shifts in 230 themes): the same sign pattern but weaker: duration 0.021 (-0.013 to 0.053), size -0.008 (-0.055 to 0.043). Both intervals include zero in the pooled fit; duration is clearly positive in middle themes only (0.071 (0.021 to 0.133)).
- So at theme level the pattern is the reverse of single books: in Study 2R size carried the effect and duration did not; for themes duration carries it (Study 3 clearly, Study 3b weakly) and size does not add. The effect at theme level is small in absolute terms (a doubling of duration is worth about 0.03 to 0.04 on the effect scale, against 0.08 per doubling of duration alone in 2R single books).
- Caveats: shifts of one theme overlap in time and across narrow and middle levels, so the cluster bootstrap by theme (node) is the honest unit, and clustering by broad theme (19 clusters) gives the same sign with a wider interval (duration 0.035, 0.007 to 0.067 in Study 3; 0.021, -0.030 to 0.073 in Study 3b). The two effect scales differ (Study 3 synthetic-control effect against Study 3b log ratio), so coefficients are not comparable across the two studies in size, only in sign and relative weight. This is exploratory; no p-value here counts as a test.
