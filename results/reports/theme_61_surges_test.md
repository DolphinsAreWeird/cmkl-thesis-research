Khant Phyo Wai

# Test behind the surge comparison with placebo years (theme-level demand)

## Where the data came from

- Script: `code/subject_surges.py` (the "scalable theme test"). It takes the 361 Wikidata book subjects (P921), builds monthly long-tail Wikipedia page views for each subject, flags surges (at least 3x the subject's own 12-month median, on a page with at least 3,000 views), and for each surge computes a matched difference-in-differences effect for the 10 books closest to the subject.
- Per-surge table: `data/reports/subject_surges.csv` (log `data/reports/subject_surges.log`, summary `data/reports/subject_surges_summary.json`). The script writes this file directly.
- The table has 89 rows (56 subjects), not 61. The script has no seasonal filter, and no file in `code/`, `data/` or `context/` contains the figure 61 or a seasonal exclusion rule. The 61 count in `context/07_results.md` could not be reproduced.

## Variables

- `effect`: mean over the surge's matched books of the change in log(1 + listens), months 0 to +2 versus months -12 to -2, minus the same change for each book's matched controls. Its exponential is the "this-year" lift ratio.
- `placebo`: the mean of the same quantity computed at 4 placebo dates (surge year -24, -12, +12, +24 months), where it could be computed. Its exponential is the placebo ratio. Every row in the table has a placebo value.
- Per-surge paired difference: d = effect - placebo, which is log(this-year ratio / placebo ratio). d > 0 means the books rose more at the surge than at the placebo dates.

## Test definitions

- n: number of surges with both values present (all 89).
- Median ratio: exp(median of d), the median of this-year ratio to placebo ratio.
- Share above placebo: proportion of surges with d > 0.
- Primary test: one-sided Wilcoxon signed-rank test of d > 0 (scipy.stats.wilcoxon, alternative "greater", zero_method "wilcox").
- Robustness check: one-sided exact sign test of d > 0 (scipy.stats.binomtest, k = surges with d > 0, p = 0.5).
- Reference: one-sided paired t-test of d > 0 (scipy.stats.ttest_1samp, alternative "greater").

## Numbers (computed on the 89 rows in the saved table)

| Quantity | Value |
|---|---|
| n | 89 |
| Median this-year ratio | 1.044 |
| Median placebo ratio | 1.029 |
| Median of per-surge ratio (this-year / placebo) | 0.976 |
| Surges above placebo | 43 of 89 (48.3%) |
| Ties at zero | 0 |
| One-sided Wilcoxon signed-rank p | 0.297 (W = 2133) |
| One-sided sign test p | 0.664 |
| One-sided paired t-test p (reference) | 0.203 (t = 0.836) |

A crude seasonal proxy (dropping surges whose calendar month repeats for the same subject in another year) leaves 57 rows, not 61. It is not the rule behind the thesis figure and is not used above.

## Discrepancy with the thesis draft

`context/07_results.md` states a median of 1.05x, 56% beating placebo, a one-sided Wilcoxon p of about 0.050 and a sign test p of about 0.22. The saved table gives 1.04x, 48% beating placebo, p = 0.30 (Wilcoxon) and p = 0.66 (sign). These figures cannot be reproduced from `subject_surges.csv`. Either the thesis figures came from a different run or a seasonal filter that is not in the code, or they are wrong. This needs to be resolved before any p-value is reported.

## Recommendation

The one-sided Wilcoxon signed-rank test on the per-surge log ratios (log of this-year over placebo) is the natural primary test for paired ratios, and the sign test is the robust check. Report the Wilcoxon result from the table that the code actually produces, not the earlier draft values.

Suggested thesis sentence (use only after the table is confirmed): "Across 89 surges in 56 subjects, the lift at the surge was not larger than at placebo dates (median ratio 0.98; one-sided Wilcoxon signed-rank test on log ratios, p = 0.30; sign test p = 0.66)."

Note: `data/reports/*.md` is copied to the public repository by `jobs/sync_github.sh`. The student ID above is in the header as the user's rule requires; remove it before the next sync if this file should not be public.
