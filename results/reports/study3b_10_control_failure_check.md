# Study 3b positive controls: check after the #MeToo control failed (14 October 2026)

The fixed rule (Study 3 record, kept in Study 3b): if a control fails, check data and mappings for errors only, log any fix, and do not tune settings on other categories. No setting was changed.

## Result being checked
#MeToo, Sexual violence and domestic violence (narrow, B12.M01.N02), month 0 = October 2017, joint Seattle count model:
- **Months 0 to +2:** tau = +0.274 (about +31%), placebo-category p = 0.061 (146 placebos).
- **Months 0 to +5:** tau = +0.348 (about +42%), p = 0.041.

COVID-19 (p = 0.017) and George Floyd / BLM (p = 0.009) passed.

## Checks
1. **Data:** the 2017 checkout months are complete and match the SPL API in all three formats. No closure or missing month falls in the fit or effect window.
2. **Mapping:** the category is the v3 node after the logged fix that moved general violence out (addendum f). Nothing was changed after this run.
3. **Pre-period:** observed demand was already 36% to 56% above the fitted expectation in July, August and September 2017 (months -3 to -1; tau_pre = +0.23). The fit window ends at month -7, so the rise began before the event month fixed in the record.

## Conclusion
No data or mapping error was found, so nothing is fixed. The control is reported as failed at the primary window, with:
- its effect size;
- the secondary-window result;
- the earlier rise.

Steps 11 to 14 run with `--accept-failed-controls`.
