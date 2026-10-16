# LibriVox bursts: two redone checks

Scripts (new, beside the old ones; old code and reports untouched): `code/librivox_bursts_redo_weekly.py`, `code/librivox_bursts_redo_monthly.py`, `code/librivox_bursts_redo_monthly_placebo.py`. All intervals are 95% bootstrap intervals clustered by book (2,000 resamples).

## 1. Weekly spike vs sustained, using only weeks up to the peak

Same data, burst rule (3x the median of the previous 26 weeks, at least 2,000 raw views), launch exclusions and listening response as `weekly_analysis.py` (769 books, 291 bursts; the old counts 118/130/43 are reproduced). New class rule: sustained = attention at least 1.5x normal in each of the 3 weeks before the peak week; spike = below 1.5x in the week before the peak; otherwise mixed.

| Rule | Class | Bursts (books) | Peak-week lift | Median lift, weeks 0 to 4 | Share above +20% |
|---|---|---|---|---|---|
| New | Sustained | 22 (21) | +19% [-18, +66] | +28% [-7, +52] | 55% [35, 73] |
| New | Spike | 183 (102) | +3% [-7, +15] | +2% [-8, +11] | 36% [29, 43] |
| New | Mixed | 86 (59) | +20% [-10, +55] | +17% [+5, +29] | 45% [33, 56] |
| Old (reproduced) | Sustained | 118 (79) | +16% [-5, +40] | +12% [+2, +20] | 42% [33, 50] |
| Old | Spike | 130 (79) | +6% [-9, +20] | +4% [-8, +16] | 39% [31, 46] |
| Old | Mixed | 43 (37) | -1% [-27, +32] | +13% [-14, +28] | 42% [28, 57] |

Reading: with the pre-peak-only rule the sustained group shrinks from 118 to 22 (most old "sustained" bursts were counted only because of weeks after the peak: 70 became mixed, 26 spikes). The direction holds (sustained and mixed lift more than spikes) but no interval excludes zero for sustained, and sustained vs spike is not significantly different at n = 22. The old "+16% vs +6%" is not contradicted but is weaker evidence than it looked. Per-event data: `librivox_bursts_redo_weekly_events.csv`; mean curves by week: `librivox_bursts_redo_weekly_curves.csv`.

## 2. Monthly event study with an out-of-sample pre-trend

Same data and burst rule as `study2b.py` (monthly, 2.5x the median of the previous 12 months). The book's own log-listening trend is fitted on months -18 to -7 only and extended to months -6 to +6. Fitting from month -18 needs 18 months of history, so 83 of the 2,807 bursts (1 of the 51 strongest) drop out: 2,724 bursts in 1,560 books; strongest: 50 bursts in 37 books (book's own article, at least 3x normal, at least 20,000 views).

| Set | Bursts | Lift, months 0 to 2 | Pre-period gap, months -6 to -1 |
|---|---|---|---|
| All, new out-of-sample trend | 2,724 | -27% [-32, -21] | -18% [-21, -14] |
| Strongest, new | 50 | -52% [-77, -8] | -41% [-62, -17] |
| All, old in-sample trend, same events | 2,724 | +2.1% [-0.7, +5.0] | -0.6% [-1.1, 0.0] |
| Strongest, old trend, same events | 50 | +10.8% [-17, +42] | -3.1% [-9, +1] |
| All, old, full old set | 2,807 | +1.3% [-1.4, +4.1] | -0.6% [-1.2, 0.0] |

(The old report's +2.5% was the month-0 value only; the months 0 to 2 mean under the old trend is +1.3 to +2.1%.)

The large negative numbers are mostly a bias of the out-of-sample method, not a burst effect. Books are kept when their listening in months -12 to -2 is at least 20 views per month, which selects books whose recent level is high relative to months -18 to -13; the fitted trend then points upward and over-shoots when extended. A placebo run (same fit and filters, centred on non-burst months of the same books, weighted to the bursts' book mix; `librivox_bursts_redo_monthly_placebo.csv`) gives the same gap without any burst:

| Set | Months 0 to 2: burst | placebo | burst minus placebo | Months -6 to -1: burst | placebo | difference |
|---|---|---|---|---|---|---|
| All (2,715 bursts) | -26% | -29% | +3.8% [-4.8, +13.2] | -17% | -17% | +0.2% [-4.4, +5.0] |
| Strongest (50) | -52% | -8% | -47% [-75, +8] | -41% | -6% | -37% [-59, -8] |

Reading: for all bursts, once the method bias is removed there is no pre-trend (+0.2%) and no lift (+3.8%, interval spans zero), consistent with the old null. For the strongest bursts the book's listening was already well below its earlier trend in months -6 to -1 (about 37 points below placebo), and months 0 to 2 are no better relative to that; the old "half lifted more than 20%" is not supported by this check on a sample of 50. This sample is small and the strongest bursts include a few cases of very large moves, so the interval is wide. The old in-sample trend result for the strongest (+10.8%, interval -17 to +42) also did not exclude zero once clustered by book. Curves by month: `librivox_bursts_redo_monthly_curves.csv`.

Files: `librivox_bursts_redo_weekly.csv`, `librivox_bursts_redo_monthly.csv`, plus the CSVs named above, all in `data/reports/`.
