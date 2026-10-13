# Positive controls: check after the COVID-19 control failed (13 October 2026)

The record says: if a control fails, check data and mappings for errors only, log any fix, and do not tune thresholds on other categories. This is that check. No setting was changed.

## Result being checked
COVID-19, Epidemics and plagues (narrow, B15.M04.N05), month 0 = March 2020, passes in no Seattle format:
- **ebook:** synthetic-control effect +0.27 log share over months 0 to +2 (about +31%), rank p = 0.115 (60 donors); months 0 to +5: +0.30, p = 0.098;
- **audiobook:** below the minimum size;
- **print:** not estimable, because April to September 2020 are closure months and a window needs at least 2 available months.

LibriVox shows +1.75 (p = 0.036). Under the pass rule fixed before the run (addendum c, item 14), LibriVox is shown but does not decide.

## Checks
1. **Ebook data, January to June 2020.** Rows and checkouts equal the SPL API in every month. No ebook month is flagged as closure or missing (`study3_panel_build.md`).
2. **Category contents.**
   - The node was built and hand-checked in taxonomy v3 before the run: 2,133 works in the main assignment.
   - Its contents were not changed after the record, apart from the logged rename rule, which did not touch this node.
   - The GDELT word-form errors ("pandemic" near weather) were on the interest side and do not enter demand.
3. **Month 0.** It is fixed in the record (March 2020). The interest shift itself starts in late January 2020 (Wikipedia week of 27 January, GDELT week of 20 January). The pre-period gaps in January and February are flat or negative, so no early rise was missed by the fixed month.
4. **Donor pool.** 60 ebook donors remained after the shift screen. The real effect ranks about 7th of 61. Several donors moved strongly in spring 2020, as the whole mix of borrowing changed when the library closed. The record anticipated this ("the change in the mix of categories lasts longer").

No data or mapping error was found, so nothing is fixed. The control is reported as failed, with the effect size and p-value above.

## Consequence
- The record does not stop the study when a control fails. Its rule is "no other result is read until they are reported". They are now reported.
- Step 11 (power) runs with `--accept-failed-controls`, as the code requires.
- The thesis reports both outcomes:
  - the design recovered the George Floyd shift (audiobook +1.51, p = 0.027; ebook +1.04, p = 0.017);
  - it did not recover a +0.27 COVID-19 ebook effect at p < 0.05.
- The power step shows which effect sizes the design can detect.
