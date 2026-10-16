# Wikipedia talk-page edits as an interest source: weekly series and rises

Interest side only. No borrowing data were read for this report. Fixed settings: `prereg/conversation_sources_settings_2026-10-14.json`. Code: `code/conversation/01` to `05`. Choices the record does not make are in `prereg/DEVIATIONS.md` (Conversation sources).

## 1. What was collected

- Source: Wikimedia REST API, `metrics/edits/per-page/en.wikipedia/Talk:<title>/<editor type>/daily`, no key, User-Agent with kwai@cmkl.ac.th, at most 4 requests a second, cached under `data/interim/talk_edits_cache/`. Counts only; the API returns no editor names and none are stored.
- Editor types: the API has no single "everything except bots" value, so registered users and anonymous editors were fetched apart and added (human edits); the two bot types (group bots, named bots) were fetched too, only to report their share.
- Articles: all 624 English Wikipedia concept articles of `articles.parquet` (canonical titles; 614 theme values), one talk page each.
- Period fetched: 1 Jan 2015 to 30 Sep 2026 (2015 is the start-up period for the 52-week normaliser). Rises are looked for from the first week with a full 26-week normal level, January 2016, to the last full week, 21 Sep 2026.
- Talk pages with at least one human edit since 2016: 624 of 624 (100.0%); with at least 50 edits since 2016: 454.
- Human talk edits in total: 241,763; bot edits: 26,955 (10.0% of all edits to these pages), dropped.

Series by level. A week is usable when the 26-week normal level exists and its median raw volume reaches 20 human talk edits a week.

| level | nodes_with_articles | nodes_with_a_usable_week | nodes_usable_80pct_of_weeks | median_usable_share | median_weekly_human_edits | nodes_with_a_rise |
| --- | --- | --- | --- | --- | --- | --- |
| narrow | 242 | 6 | 0 | 0 | 0 | 3 |
| middle | 86 | 9 | 0 | 0 | 1 | 5 |
| broad | 19 | 13 | 2 | 0.0411 | 10 | 9 |

For comparison, Wikipedia page views: narrow 239 usable of 242, middle 86 usable of 86, broad 19 usable of 19 nodes.

## 2. Normalisation

The Wikimedia `edits/aggregate` endpoint returns totals by editor type and by page type, but the page types are only all, content and non-content. There is no talk-namespace total (non-content mixes in user, project, file and other pages), so the record's first choice, division by all English Wikipedia talk-page edits that week, is not available. **Used: the record's fallback, the theme's own trailing 52-week mean** (mean of the same series over the previous 52 full weeks, at least 26 of them, current week left out). Share = human talk edits this week / that mean. The rule then runs on this share as it runs on page-view shares.

Consequence to keep in mind: the denominator is the series' own history, so a series that has been rising for months is damped, and the share has no meaning across themes (every series is near 1 in quiet weeks). It is a ratio to the own recent past, which is what the rise rule needs.

## 3. Noise benchmark (interest data only)

Same method as `code/parameter_audit/calibrate_interest.py`: each series is rebuilt from its own quiet-week deviations in 8-week blocks, so it keeps ordinary variation but holds no real event; the unchanged rule is run on real and rebuilt series. Noise share = rises per 100 series-years in rebuilt series / rises per 100 series-years in real series.

| level | real_series | real_series_years | real_shifts | real_per100y | noise_shifts | noise_per100y | noise_share_all | real_sustained | noise_sustained | noise_share_sustained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narrow | 5 | 4.4 | 2 | 45.8 | 39 | 86.5 | 1.89 | 1 | 4 | 0.388 |
| middle | 6 | 13.9 | 14 | 101 | 80 | 88.7 | 0.882 | 1 | 13 | 2.01 |

Wikipedia page views, same benchmark (parameter audit): narrow all 0.71, sustained 0.25; middle all 0.73, sustained 0.29.

Grid (ratio, Mann-Kendall alpha, quiet weeks) for talk edits:

| setting | value | level | real_shifts | noise_shifts | noise_share_all | real_sustained | noise_sustained | noise_share_sustained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ratio | 1.2 | narrow | 3 | 23 | 0.743 | 1 | 2 | 0.194 |
| ratio | 1.2 | middle | 12 | 49 | 0.63 | 2 | 11 | 0.849 |
| ratio | 1.3 | narrow | 3 | 24 | 0.776 | 1 | 2 | 0.194 |
| ratio | 1.3 | middle | 13 | 57 | 0.677 | 1 | 11 | 1.7 |
| ratio | 1.5 | narrow | 2 | 39 | 1.89 | 1 | 4 | 0.388 |
| ratio | 1.5 | middle | 14 | 80 | 0.882 | 1 | 13 | 2.01 |
| ratio | 2 | narrow | 3 | 55 | 1.78 | 0 | 3 |  |
| ratio | 2 | middle | 11 | 105 | 1.47 | 0 | 5 |  |
| ratio | 2.5 | narrow | 4 | 57 | 1.38 | 0 | 1 |  |
| ratio | 2.5 | middle | 8 | 111 | 2.14 | 0 | 3 |  |
| ratio | 3 | narrow | 4 | 56 | 1.36 | 0 | 1 |  |
| ratio | 3 | middle | 9 | 92 | 1.58 | 0 | 2 |  |
| mk_alpha | 0.05 | narrow | 2 | 28 | 1.36 | 1 | 2 | 0.194 |
| mk_alpha | 0.05 | middle | 11 | 70 | 0.982 | 0 | 10 |  |
| mk_alpha | 0.2 | narrow | 2 | 42 | 2.04 | 1 | 4 | 0.388 |
| mk_alpha | 0.2 | middle | 15 | 89 | 0.916 | 1 | 12 | 1.85 |
| mk_alpha | 1 | narrow | 2 | 44 | 2.13 | 1 | 2 | 0.194 |
| mk_alpha | 1 | middle | 16 | 92 | 0.887 | 1 | 10 | 1.54 |
| quiet_weeks | 4 | narrow | 4 | 82 | 1.99 | 1 | 9 | 0.872 |
| quiet_weeks | 4 | middle | 17 | 168 | 1.53 | 1 | 23 | 3.55 |
| quiet_weeks | 12 | narrow | 2 | 8 | 0.388 | 1 | 0 | 0 |
| quiet_weeks | 12 | middle | 6 | 25 | 0.643 | 0 | 4 |  |

Share of usable weeks at or above each ratio to normal:

| level | weeks | series | share_ge_1.2 | share_ge_1.3 | share_ge_1.5 | share_ge_2.0 | share_ge_3.0 | p90 | p95 | p97.5 | p99 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle | 726 | 6 | 0.303 | 0.264 | 0.212 | 0.124 | 0.0634 | 2.28 | 3.39 | 4.04 | 6.32 |
| narrow | 228 | 5 | 0.281 | 0.268 | 0.206 | 0.11 | 0.0526 | 2.05 | 3 | 5.25 | 6.79 |

## 4. Rises (Study 3 rule unchanged, minimum 20 talk edits a week)

Counts of shift starts by duration class. `main set` = narrow and middle nodes, not seasonal, not censored or interrupted (the set Study 3b tests). Classes: sustained 4 weeks or more, intermediate 3, fading 2 or fewer.

| level | all_starts | sustained | intermediate | fading | censored | interrupted | seasonal | main_set_sustained | main_set_intermediate | main_set_fading | large (size>=3) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narrow | 5 | 2 | 0 | 3 | 0 | 0 | 0 | 2 | 0 | 3 | 3 |
| middle | 16 | 2 | 0 | 14 | 0 | 0 | 0 | 2 | 0 | 14 | 7 |
| broad | 50 | 1 | 4 | 44 | 0 | 1 | 0 | 0 | 0 | 0 | 12 |

Main-set rises by start year: 2016 2, 2017 3, 2018 2, 2019 1, 2020 2, 2021 1, 2022 2, 2024 3, 2025 5.

Main-set rises with a start in 2016-01 to 2026-03 (the window for month 0 in the record): 21.

Sensitivity, not part of the record and not used downstream: the same rule with a lower minimum normal level (counts of all starts by class, narrow and middle nodes, not seasonal).

| minimum | level | sustained | intermediate | fading |
| --- | --- | --- | --- | --- |
| 20 | narrow | 2 | 0 | 3 |
| 20 | middle | 2 | 0 | 14 |
| 10 | narrow | 4 | 1 | 12 |
| 10 | middle | 8 | 2 | 27 |
| 5 | narrow | 9 | 5 | 33 |
| 5 | middle | 13 | 9 | 69 |

## 5. Positive controls

Events: COVID-19 declared a pandemic 11 Mar 2020; George Floyd died 25 May 2020; #MeToo hashtag went viral 15 Oct 2017. A control rise is the first rise whose start week lies from 2 weeks before to 8 weeks after the event. Series: the control node and the control theme values (value series labelled with the same rule and the same minimum).

| control | series | median_weekly_edits_around_event | peak_weekly_edits_event_window | first_rise_at_minimum_5 (not in record) | first_rise_start | class | size | wikipedia_node_rise_start |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COVID-19 (Mar 2020) | node B15.M04.N05 Epidemics and plagues | 1 | 27 | no rise (or normal volume below 5) |  | series has no usable week |  |  |
| COVID-19 (Mar 2020) | value plague | 1 | 27 | no rise (or normal volume below 5) |  | no usable week (volume below 20 or no normal level) |  |  |
| COVID-19 (Mar 2020) | value epidemiology | 0 | 2 | no rise (or normal volume below 5) |  | no usable week (volume below 20 or no normal level) |  |  |
| George Floyd (Jun 2020) | node B05.M02.N02 Race and racism | 3 | 69 | no rise (or normal volume below 5) |  | series has no usable week |  | 2020-05-25 |
| George Floyd (Jun 2020) | value racism | 0 | 30 | no rise (or normal volume below 5) |  | no usable week (volume below 20 or no normal level) |  |  |
| #MeToo (Oct 2017) | node B12.M01.N02 Sexual violence and domestic violence | 2 | 9 | no rise (or normal volume below 5) |  | series has no usable week |  | 2017-10-16 |
| #MeToo (Oct 2017) | value sexual violence | 0 | 3 | no rise (or normal volume below 5) |  | no usable week (volume below 20 or no normal level) |  |  |

With the record's minimum of 20 edits a week none of the three control series has a usable week, so none can be tested; the column "first_rise_at_minimum_5" is a descriptive look at the same rule with a lower minimum and is not part of the record.

## 6. Agreement with Wikipedia page-view rises

For each talk-edit rise (sustained, intermediate or fading; censored and interrupted left out) in a node that also has a Wikipedia series: is there a Wikipedia rise start in the same node within 2 weeks (either direction, any class)? "Chance" is the share of usable talk weeks in the same node that lie within 2 weeks of some Wikipedia start, averaged over the talk rises: the agreement expected if the two sets of start dates were unrelated. Lead-lag is the median of (talk start minus the nearest Wikipedia start) in weeks over matched rises; positive means talk edits rose later. The reverse column is the share of Wikipedia rises, in weeks where the talk series is usable, that have a talk rise within 2 weeks.

| group | talk_rises | with_wikipedia_rise_within_2_weeks | share | chance | median_lag_weeks |
| --- | --- | --- | --- | --- | --- |
| all levels | 64 | 7 | 0.109 | 0.0581 | 2 |
| narrow | 5 | 2 | 0.4 | 0.115 | 1.5 |
| middle | 16 | 3 | 0.188 | 0.0689 | 2 |
| broad | 43 | 2 | 0.0465 | 0.0475 | 1 |
| main set | 21 | 5 | 0.238 | 0.0798 | 2 |
| sustained | 5 | 0 | 0 | 0.106 |  |
| intermediate | 3 | 0 | 0 | 0.0526 |  |
| fading | 56 | 7 | 0.125 | 0.0541 | 2 |

| level | wikipedia_rises_in_usable_talk_weeks | with_talk_rise_within_2_weeks | share |
| --- | --- | --- | --- |
| narrow | 8 | 2 | 0.25 |
| middle | 12 | 3 | 0.25 |
| broad | 18 | 2 | 0.111 |

Talk rises in nodes with a Wikipedia series: 64 of 70.
