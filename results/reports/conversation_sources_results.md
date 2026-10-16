# Conversation sources: borrowing test results

Khant Phyo Wai, CMKL University, ID 01323050. Second, informed analysis: it repeats the Study 3b design on two new interest sources; it is not an independent replication of the Wikipedia result. Settings: `prereg/conversation_sources_settings_2026-10-14.json` (read only). Code: `code/conversation/10` to `12`. Choices the record does not make: `prereg/DEVIATIONS.md`, Conversation sources, rows dated 2026-10-15.

## Summary (read this first)

- Positive controls: TweetsKB passes George Floyd (narrow Race and racism, tau 1.17, p 0.009) and has no narrow rise for COVID-19 or #MeToo, so those two cannot be tested. Talk edits have no narrow rise in any control window (the series fall below 20 edits a week), so no control can be tested for that source.
- TweetsKB, H2 (sustained rises above 0): supported at the narrow level (mean tau 0.229, 6 rises, interval 0.014 to 0.418) and the middle level (0.143, 8 rises, 0.011 to 0.278). H1 (sustained minus fading): supported at the middle level (0.150, 0.016 to 0.296), not at the narrow level (0.209, -0.020 to 0.415).
- These TweetsKB results rest on very few rises, and the largest effects come from the single George Floyd event; without it every H1 and H2 interval includes 0 (section 7).
- Talk edits: no verdict at either level (2 sustained rises narrow, 2 middle).
- Agreement with Wikipedia rises within 2 weeks: TweetsKB 21% of tested rises (chance 5%), 64% of sustained ones; talk edits 24% (chance 8%), 0 of 4 sustained.

## 1. Positive controls (written before any other result)

Rule (Study 3b): tau > 0 and one-sided placebo-category p < 0.05 in the joint Seattle model (print, ebook, audiobook), months 0 to +2. The control is the narrow node of the theme; month 0 is the month of the first rise that starts within 8 weeks before to 8 weeks after the event (talk edits: 2 weeks before to 8 weeks after, as on the interest side). The middle node is tested the same way but is descriptive only. A source with no rise in the narrow node cannot be tested for that event.

- TweetsKB: COVID-19: NO RISE, CONTROL NOT TESTABLE; George Floyd: PASS; #MeToo: NO RISE, CONTROL NOT TESTABLE
- Wikipedia talk edits: COVID-19: NO RISE, CONTROL NOT TESTABLE; George Floyd: NO RISE, CONTROL NOT TESTABLE; #MeToo: NO RISE, CONTROL NOT TESTABLE

| source | control | level | label | rise | month0 | tau_p | p_cat_p | n_placebos | summu_p | too_sparse | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tweetskb | COVID-19, March 2020 | narrow | Epidemics and plagues | none |  |  |  |  |  |  | NO RISE, CONTROL NOT TESTABLE |
| tweetskb | COVID-19, March 2020 | middle | Disease, epidemics and public health | none |  |  |  |  |  |  | no rise (descriptive) |
| tweetskb | George Floyd, June 2020 | narrow | Race and racism | 2020-05-25 sustained size 7.26 | 2020-05 | 1.166 | 0.009 | 105.000 | 4254.210 | False | PASS |
| tweetskb | George Floyd, June 2020 | middle | Race, racism and diversity | 2020-05-25 sustained size 7.22 | 2020-05 | 0.931 | 0.026 | 37.000 | 7050.987 | False | PASS (descriptive) |
| tweetskb | #MeToo, October 2017 | narrow | Sexual violence and domestic violence | none |  |  |  |  |  |  | NO RISE, CONTROL NOT TESTABLE |
| tweetskb | #MeToo, October 2017 | middle | Abuse, sexual violence and revenge | 2017-10-16 fading size 1.63 | 2017-10 | 0.153 | 0.059 | 50.000 | 6785.389 | False | FAIL (descriptive) |
| talk_edits | COVID-19, March 2020 | narrow | Epidemics and plagues | none |  |  |  |  |  |  | NO RISE, CONTROL NOT TESTABLE |
| talk_edits | COVID-19, March 2020 | middle | Disease, epidemics and public health | none |  |  |  |  |  |  | no rise (descriptive) |
| talk_edits | George Floyd, June 2020 | narrow | Race and racism | none |  |  |  |  |  |  | NO RISE, CONTROL NOT TESTABLE |
| talk_edits | George Floyd, June 2020 | middle | Race, racism and diversity | none |  |  |  |  |  |  | no rise (descriptive) |
| talk_edits | #MeToo, October 2017 | narrow | Sexual violence and domestic violence | none |  |  |  |  |  |  | NO RISE, CONTROL NOT TESTABLE |
| talk_edits | #MeToo, October 2017 | middle | Abuse, sexual violence and revenge | none |  |  |  |  |  |  | no rise (descriptive) |

Per-format tau of the tested controls (descriptive):

| source | control | level | tau_p_audiobook | tau_p_ebook | tau_p_print |
| --- | --- | --- | --- | --- | --- |
| tweetskb | George Floyd, June 2020 | narrow | 1.213 | 1.122 |  |
| tweetskb | George Floyd, June 2020 | middle | 1.016 | 0.844 |  |
| tweetskb | #MeToo, October 2017 | middle | 0.093 | 0.047 | 0.273 |

Run time 1 s. Panel build `20261014-001042-382abdb190c4`.

<!-- TESTS -->
## 2. Tested rises

Narrow and middle levels, sustained, intermediate or fading, not seasonal, not within 2 weeks of a TweetsKB linker break, month 0 from 2016-01 to 2020-09 (TweetsKB) or 2026-03 (talk edits). "Pooled" = tested, at least 5 expected checkouts in months 0 to +2 (not too sparse) and tau defined. The verdict rule: a class with fewer than 5 pooled rises gets no verdict.

| source | level | duration_class | rises_in_set | themes | tested | too_sparse | not_tested | pooled | share_p_below_0_05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| talk_edits | middle | fading | 14 | 5 | 14 | 0 | 0 | 14 | 0.07 |
| talk_edits | middle | sustained | 2 | 2 | 2 | 0 | 0 | 2 | 0.00 |
| talk_edits | narrow | fading | 3 | 3 | 3 | 0 | 0 | 3 | 0.00 |
| talk_edits | narrow | sustained | 2 | 2 | 2 | 0 | 0 | 2 | 0.00 |
| tweetskb | middle | fading | 46 | 19 | 46 | 0 | 0 | 46 | 0.04 |
| tweetskb | middle | intermediate | 2 | 2 | 2 | 0 | 0 | 2 | 0.00 |
| tweetskb | middle | sustained | 8 | 6 | 8 | 0 | 0 | 8 | 0.25 |
| tweetskb | narrow | fading | 26 | 16 | 26 | 0 | 0 | 26 | 0.04 |
| tweetskb | narrow | intermediate | 4 | 4 | 4 | 0 | 0 | 4 | 0.00 |
| tweetskb | narrow | sustained | 6 | 5 | 6 | 0 | 0 | 6 | 0.17 |

## 3. Pooled tau by class (log lift of borrowing in months 0 to +2 over the model expectation; mean over rises)

| source | level | duration_class | pooled_rises | themes | mean_tau | ci_low | ci_high | tau_audiobook | tau_ebook | tau_print | tau_months0_5 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| talk_edits | middle | fading | 14 | 5 | 0.019 | -0.000 | 0.065 | 0.065 | -0.000 | 0.015 | 0.014 |  |
| talk_edits | middle | sustained | 2 | 2 | 0.006 | -0.028 | 0.040 | -0.001 | -0.018 | 0.019 | -0.002 | descriptive only (fewer than 5 rises) |
| talk_edits | narrow | fading | 3 | 3 | -0.107 | -0.344 | 0.062 | -0.092 | -0.161 | -0.050 | -0.051 | descriptive only (fewer than 5 rises) |
| talk_edits | narrow | sustained | 2 | 2 | 0.038 | -0.084 | 0.159 | 0.052 | -0.038 | 0.096 | -0.027 | descriptive only (fewer than 5 rises) |
| tweetskb | middle | fading | 46 | 19 | -0.007 | -0.032 | 0.025 | -0.013 | -0.029 | 0.013 | -0.006 |  |
| tweetskb | middle | intermediate | 2 | 2 | -0.018 | -0.036 | 0.000 | -0.078 | 0.017 | -0.021 | -0.016 | descriptive only (fewer than 5 rises) |
| tweetskb | middle | sustained | 8 | 6 | 0.143 | 0.011 | 0.278 | 0.141 | 0.176 | -0.002 | 0.132 |  |
| tweetskb | narrow | fading | 26 | 16 | 0.020 | -0.034 | 0.080 | -0.029 | 0.042 | 0.008 | 0.002 |  |
| tweetskb | narrow | intermediate | 4 | 4 | -0.044 | -0.142 | 0.054 | -0.022 | -0.061 | -0.087 | -0.038 | descriptive only (fewer than 5 rises) |
| tweetskb | narrow | sustained | 6 | 5 | 0.229 | 0.014 | 0.418 | 0.280 | 0.277 | -0.084 | 0.209 |  |

Per-format columns and months 0 to +5 are secondary and descriptive. Intervals for classes with fewer than 5 rises are not to be read.

## 4. H1 and H2

H1: pooled tau of sustained rises minus pooled tau of fading rises, 95% percentile interval from 2,000 resamples of themes, seed 20261014; supported if the lower limit is above 0. H2: pooled tau of sustained rises, same interval method, supported if the lower limit is above 0. A class with fewer than 5 pooled rises gets no verdict.

| source | level | sustained | fading | H1_diff | H1_low | H1_high | H1_resamples_dropped | H1_verdict | H2_mean | H2_low | H2_high | H2_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| talk_edits | middle | 2 | 14 | -0.013 | -0.069 | 0.038 | 153 | too few rises, no verdict | 0.006 | -0.028 | 0.040 | too few rises, no verdict |
| talk_edits | narrow | 2 | 3 | 0.145 | -0.112 | 0.503 | 67 | too few rises, no verdict | 0.038 | -0.084 | 0.159 | too few rises, no verdict |
| tweetskb | middle | 8 | 46 | 0.150 | 0.016 | 0.296 | 0 | interval above 0: SUPPORTED | 0.143 | 0.011 | 0.278 | interval above 0: SUPPORTED |
| tweetskb | narrow | 6 | 26 | 0.209 | -0.020 | 0.415 | 8 | interval does not exclude 0: NOT SUPPORTED | 0.229 | 0.014 | 0.418 | interval above 0: SUPPORTED |

## 5. Sensitivity: tests with fewer than 5 expected checkouts included (descriptive)

| source | level | duration_class | rises | mean_tau |
| --- | --- | --- | --- | --- |
| talk_edits | middle | fading | 14 | 0.019 |
| talk_edits | middle | sustained | 2 | 0.006 |
| talk_edits | narrow | fading | 3 | -0.107 |
| talk_edits | narrow | sustained | 2 | 0.038 |
| tweetskb | middle | fading | 46 | -0.007 |
| tweetskb | middle | intermediate | 2 | -0.018 |
| tweetskb | middle | sustained | 8 | 0.143 |
| tweetskb | narrow | fading | 26 | 0.020 |
| tweetskb | narrow | intermediate | 4 | -0.044 |
| tweetskb | narrow | sustained | 6 | 0.229 |

Run time 6 s.

<!-- AGREEMENT -->
## 6. Secondary: agreement with Wikipedia page-view rises and lead-lag (interest data only)

A conversation rise (sustained, intermediate or fading, in a node that has a Wikipedia series) agrees when a Wikipedia rise of any class starts in the same node within 14 days. "Chance" is the share of the source's usable weeks in that node that lie within 14 days of some Wikipedia start. Lead-lag = conversation start minus nearest Wikipedia start in weeks, median over agreeing rises; positive means the conversation source rose later. "Tested set" is the set used for H1 and H2 (narrow and middle, not seasonal, not near a break, month 0 in the period). The talk-edit rows for all levels equal the talk-edit interest report.

| source | group | rises | matched_within_2_weeks | share | chance | median_lag_weeks |
| --- | --- | --- | --- | --- | --- | --- |
| tweetskb | all levels | 138 | 27 | 0.196 | 0.047 | 0.0 |
| tweetskb | narrow | 37 | 10 | 0.270 | 0.063 | -0.5 |
| tweetskb | middle | 66 | 8 | 0.121 | 0.031 | 0.0 |
| tweetskb | broad | 35 | 9 | 0.257 | 0.059 | 0.0 |
| tweetskb | tested set | 84 | 18 | 0.214 | 0.046 | 0.0 |
| tweetskb | tested set, sustained | 14 | 9 | 0.643 | 0.061 | 0.0 |
| tweetskb | tested set, fading | 64 | 6 | 0.094 | 0.042 | 0.0 |
| talk_edits | all levels | 64 | 7 | 0.109 | 0.058 | 2.0 |
| talk_edits | narrow | 5 | 2 | 0.400 | 0.115 | 1.5 |
| talk_edits | middle | 16 | 3 | 0.188 | 0.069 | 2.0 |
| talk_edits | broad | 43 | 2 | 0.047 | 0.048 | 1.0 |
| talk_edits | tested set | 21 | 5 | 0.238 | 0.080 | 2.0 |
| talk_edits | tested set, sustained | 4 | 0 | 0.000 | 0.084 |  |
| talk_edits | tested set, fading | 17 | 5 | 0.294 | 0.079 | 2.0 |

## 7. Check after the results were seen: TweetsKB without the George Floyd rise (descriptive, not part of the record)

The two largest TweetsKB sustained effects are the George Floyd rise of 25 May 2020 (narrow Race and racism and its middle parent). The same H1 and H2 computation is repeated without them.

| source | level | sustained | fading | H1_diff | H1_low | H1_high | H2_mean | H2_low | H2_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tweetskb | middle | 7 | 46 | 0.037 | -0.077 | 0.172 | 0.030 | -0.083 | 0.149 |
| tweetskb | narrow | 5 | 26 | 0.022 | -0.111 | 0.166 | 0.042 | -0.070 | 0.153 |

