# TweetsKB conversation series: interest side

Written by `code/conversation/04_tweetskb_shifts.py`. Settings: `prereg/conversation_sources_settings_2026-10-14.json` (not edited). Implementation choices the record does not make are in `prereg/DEVIATIONS.md` (Conversation sources section). No borrowing data were read or linked. Counts only: no tweet text, tweet IDs or user fields were requested or stored.

## What the endpoint holds (read this first)

The public 5% endpoint contains tweets only from 2015-01-05 to 2020-12-21: its earliest tweet is 2015-01-01 and its latest 2020-12-31 (checked with a count by year and a min/max query). It has no tweets for February 2013 to December 2014 or for January 2021 to June 2023, so the record's period (February 2013 to June 2023) cannot be built from the endpoint. Within 2015 to 2020, 19 weeks have fewer than 7 days of sample data (outages in 2017 and 2018) and are treated as missing. Two of the three linker breaks (January 2021, September 2022) fall outside the data, so they cannot be checked; only April 2018 can. Series for 2013 to 2014 and 2021 to 2023 would need the monthly files (Zenodo parts 1 to 3, GESIS parts 10 to 12), which are large downloads that need Khant's permission and were not made. Everything below covers 2015 to 2020 only.

## What was built

- Entities: 624 English Wikipedia concept articles mapped to theme values (the articles of `data/db/interest/wiki/articles.parquet`), with 291 redirect titles that the Wikipedia series also adds to an article. 636 DBpedia IRIs of 915 exist in TweetsKB; 590 of 624 articles have at least one IRI there. The 34 articles with none (mostly very general or disambiguated titles) have no TweetsKB series.
- Source: the public TweetsKB SPARQL endpoint (5% sample), graph `http://data.gesis.org/tweetskb`, one query every 3 seconds, User-Agent with kwai@cmkl.ac.th, every answer cached in `data/interim/tweetskb_cache/`.
- Weekly series: ISO weeks starting Monday, weeks of the sample only (see above). For a node: distinct tweets that mention any of its articles (each tweet once per node), divided by all tweets in the sample that week. Tone: mean positive and mean negative score of those tweets (0 to 1).
- Nodes: 242 narrow, 86 middle, 19 broad. Files: `data/db/interest/tweetskb/weekly_node.parquet`, `weekly_article.parquet`, `shifts.parquet`.
- Partial weeks (fewer than 7 days of sample data): 250 of 544; they count as missing.

## Coverage per year

Sample tweets are the denominator. The column on tweets in broad nodes is an upper bound for the tweets that mention at least one mapped article (a tweet in two broad nodes counts twice). "Usable series" = nodes whose weeks are usable (26 full weeks behind them and a normal level of at least 100 tweets a week) in at least 80% of the year's weeks.

| year | weeks | full weeks | sample tweets | median weekly sample tweets | articles with tweets | article tweet mentions | tweets in broad nodes sum | share tweets in broad nodes sum | narrow usable series | narrow median weekly tweets | narrow series | middle usable series | middle median weekly tweets | middle series | broad usable series | broad median weekly tweets | broad series |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2013 | 48 | 0 | 0.000 |  |  | 0.000 | 0.000 |  | 0 | 0.000 | 242 | 0 | 0.000 | 86 | 0 | 0.000 | 19 |
| 2014 | 52 | 0 | 0.000 |  |  | 0.000 | 0.000 |  | 0 | 0.000 | 242 | 0 | 0.000 | 86 | 0 | 0.000 | 19 |
| 2015 | 53 | 52 | 17,487,084 | 336,202 | 545.000 | 414,705 | 409,764 | 0.023 | 0 | 8.000 | 242 | 0 | 36.000 | 86 | 0 | 340.000 | 19 |
| 2016 | 52 | 52 | 14,825,552 | 291,316 | 551.000 | 402,374 | 397,355 | 0.027 | 13 | 7.500 | 242 | 28 | 38.750 | 86 | 18 | 365.500 | 19 |
| 2017 | 52 | 47 | 11,889,022 | 249,783 | 548.000 | 380,542 | 375,653 | 0.032 | 13 | 7.000 | 242 | 24 | 32.750 | 86 | 18 | 327.000 | 19 |
| 2018 | 52 | 39 | 8,207,494 | 215,784 | 449.000 | 290,202 | 285,157 | 0.035 | 0 | 4.000 | 242 | 0 | 34.500 | 86 | 0 | 292.000 | 19 |
| 2019 | 52 | 52 | 11,768,294 | 230,858 | 448.000 | 401,327 | 393,861 | 0.033 | 17 | 5.250 | 242 | 20 | 39.250 | 86 | 18 | 327.500 | 19 |
| 2020 | 53 | 52 | 15,244,161 | 301,127 | 453.000 | 475,043 | 465,284 | 0.031 | 14 | 5.500 | 242 | 18 | 52.000 | 86 | 18 | 374.000 | 19 |
| 2021 | 52 | 0 | 0.000 |  |  | 0.000 | 0.000 |  | 0 | 0.000 | 242 | 0 | 0.000 | 86 | 0 | 0.000 | 19 |
| 2022 | 52 | 0 | 0.000 |  |  | 0.000 | 0.000 |  | 0 | 0.000 | 242 | 0 | 0.000 | 86 | 0 | 0.000 | 19 |
| 2023 | 26 | 0 | 0.000 |  |  | 0.000 | 0.000 |  | 0 | 0.000 | 242 | 0 | 0.000 | 86 | 0 | 0.000 | 19 |


## The linker breaks and 2021 to 2023

Coverage of 2021 to June 2023: none. The endpoint has no tweet after 2020-12-31, so there are no 2021 to 2023 series and the January 2021 and September 2022 breaks cannot be checked.

April 2018: the sample has no tweets from 2017-11-29 to 2018-03-31 and restarts on 2018-04-01, the first day of Part 7 (new linker dump). A before-and-after comparison at the break is therefore possible only across the gap. The table compares the median share in the 8 full weeks before the gap (weeks of 2017-10-02 to 2017-11-20) with the 8 full weeks from 2018-04-02, for series with at least 30 tweets a week in both windows. The placebo columns give the same statistic for pairs of 8-week windows 18 weeks apart (the same distance) that lie on one side of the gap, every 4th week: the 5th and 95th percentile of the median log2 jump across series, and the share of series that changed by a factor of 1.5 either way. A seasonal difference (October to November against April) and the gap itself are not separated from a linker effect.

| level | series | median_log2_jump | share_changed_1_5x | share_up_1_5x | share_down_1_5x | placebo_pairs | placebo_median_log2_jump_p5 | placebo_median_log2_jump_p95 | placebo_share_changed_median | placebo_share_changed_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narrow | 33 | 0.263 | 0.394 | 0.273 | 0.121 | 56 | -0.166 | 0.137 | 0.100 | 0.199 |
| middle | 40 | 0.018 | 0.500 | 0.275 | 0.225 | 56 | -0.137 | 0.134 | 0.067 | 0.193 |
| broad | 18 | 0.191 | 0.556 | 0.278 | 0.278 | 56 | -0.123 | 0.133 | 0.053 | 0.158 |

Share of sample tweets in the broad nodes (sum), after over before, with the placebo range:

| comparison | tweets_in_broad_nodes_share_after_over_before | placebo_p5 | placebo_p95 | placebo_pairs |
| --- | --- | --- | --- | --- |
| April 2018 (across the gap) | 1.020 | 0.868 | 1.176 | 56.000 |
| January 2021 |  |  |  |  |
| September 2022 |  |  |  |  |

A median jump outside the placebo range, or a changed-share above the placebo 95th percentile, would point to a level shift at the break. Rises that start within 2 weeks of a break week are flagged and left out of every count below (0 of 156 starts).


## Noise benchmark (parameter-audit method, interest data only)

Each narrow and middle series is rebuilt 20 times from its own quiet-week deviations from normal (circular blocks of 8 weeks, seed 20261014), so it keeps ordinary week-to-week variation and holds no real event. The unchanged rule is run on the real and the rebuilt series. Noise share = rises found per 100 series-years in the rebuilt series divided by rises per 100 series-years in the real series. The base row is the record's rule (ratio 1.5); the other rows change only the ratio, for context.

| setting | value | level | real_series | real_series_years | real_shifts | real_shifts_not_near_break | real_sustained | noise_series_years | noise_shifts | noise_sustained | noise_share_all | noise_share_sustained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base (record) |  | narrow | 242 | 79.300 | 41 | 41 | 6 | 5,162 | 2938 | 180 | 1.101 | 0.461 |
| base (record) |  | middle | 86 | 119.200 | 72 | 72 | 9 | 7,148 | 3484 | 263 | 0.807 | 0.488 |
| ratio | 1.200 | narrow | 242 | 79.300 | 70 | 70 | 9 | 5,162 | 6698 | 766 | 1.470 | 1.308 |
| ratio | 1.200 | middle | 86 | 119.200 | 117 | 117 | 15 | 7,148 | 8878 | 855 | 1.266 | 0.951 |
| ratio | 1.300 | narrow | 242 | 79.300 | 55 | 55 | 8 | 5,162 | 5196 | 456 | 1.452 | 0.876 |
| ratio | 1.300 | middle | 86 | 119.200 | 88 | 87 | 16 | 7,148 | 6481 | 571 | 1.229 | 0.595 |
| ratio | 2.000 | narrow | 242 | 79.300 | 17 | 17 | 3 | 5,162 | 1239 | 19 | 1.120 | 0.097 |
| ratio | 2.000 | middle | 86 | 119.200 | 34 | 34 | 3 | 7,148 | 1619 | 104 | 0.794 | 0.578 |
| ratio | 2.500 | narrow | 242 | 79.300 | 11 | 11 | 2 | 5,162 | 683 | 4 | 0.954 | 0.031 |
| ratio | 2.500 | middle | 86 | 119.200 | 21 | 21 | 2 | 7,148 | 920 | 88 | 0.731 | 0.734 |
| ratio | 3.000 | narrow | 242 | 79.300 | 8 | 8 | 2 | 5,162 | 356 | 2 | 0.684 | 0.015 |
| ratio | 3.000 | middle | 86 | 119.200 | 13 | 13 | 1 | 7,148 | 556 | 67 | 0.714 | 1.118 |


## Rises by duration class

The Study 3 rule is unchanged: sustained = at least 4 weeks at ratio 1.5 or more, intermediate = 3, fading = 2 or fewer. Censored = still running when data end, interrupted = data became unusable. Starts within 2 weeks of a break are excluded.

All starts (data 2015 to 2020):

| level_name | sustained | intermediate | fading | censored | interrupted | all |
| --- | --- | --- | --- | --- | --- | --- |
| broad | 6 | 2 | 35 | 0 | 0 | 43 |
| middle | 9 | 4 | 59 | 0 | 0 | 72 |
| narrow | 6 | 4 | 31 | 0 | 0 | 41 |

Starts in the outcome period (week of 4 January 2016 to week of 27 March 2023):

| level_name | sustained | intermediate | fading | censored | interrupted | all |
| --- | --- | --- | --- | --- | --- | --- |
| broad | 6 | 2 | 33 | 0 | 0 | 41 |
| middle | 9 | 4 | 50 | 0 | 0 | 63 |
| narrow | 6 | 4 | 28 | 0 | 0 | 38 |

Main set (narrow and middle, not seasonal, completed, outside the break windows, outcome period): | level_name | sustained | intermediate | fading | censored | interrupted | all |
| --- | --- | --- | --- | --- | --- | --- |
| middle | 8 | 3 | 48 | 0 | 0 | 59 |
| narrow | 6 | 4 | 28 | 0 | 0 | 38 |

Seasonal rises (all starts, outside breaks) by level: {'broad': 4, 'middle': 4, 'narrow': 0}.


## Control themes

For each event, the first rise that starts within 8 weeks (before or after) of the event date, in the control theme's narrow node and in its middle and broad parents. Event dates: COVID-19 declared a pandemic 2020-03-11, George Floyd's death 2020-05-25, #MeToo hashtag 2017-10-15. Size = peak ratio to the 26-week normal up to the labelling week.

| control | event_date | node_id | level | node_label | rise_found | start_week | weeks_from_event | duration_class | size | whole_peak | weeks_ge_1_5 | near_break | seasonal | n_rises_in_window | max_ratio_in_window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COVID-19, March 2020 | 2020-03-11 | B15.M04.N05 | narrow | Epidemics and plagues | False |  |  |  |  |  |  |  |  | 0 |  |
| COVID-19, March 2020 | 2020-03-11 | B15.M04 | middle | Disease, epidemics and public health | False |  |  |  |  |  |  |  |  | 0 |  |
| COVID-19, March 2020 | 2020-03-11 | B15 | broad | Health, illness and addiction | True | 2020-03-09 | 0.00 | sustained | 1.96 | 1.96 | 4.00 | False | False | 1 | 1.96 |
| George Floyd, June 2020 | 2020-05-25 | B05.M02.N02 | narrow | Race and racism | True | 2020-05-25 | 0.00 | sustained | 7.26 | 7.26 | 10.00 | False | False | 1 | 7.26 |
| George Floyd, June 2020 | 2020-05-25 | B05.M02 | middle | Race, racism and diversity | True | 2020-05-25 | 0.00 | sustained | 7.22 | 7.22 | 10.00 | False | False | 1 | 7.22 |
| George Floyd, June 2020 | 2020-05-25 | B05 | broad | Race, ethnicity and migration | True | 2020-05-25 | 0.00 | sustained | 6.82 | 6.82 | 8.00 | False | False | 1 | 6.82 |
| #MeToo, October 2017 | 2017-10-15 | B12.M01.N02 | narrow | Sexual violence and domestic violence | False |  |  |  |  |  |  |  |  | 0 |  |
| #MeToo, October 2017 | 2017-10-15 | B12.M01 | middle | Abuse, sexual violence and revenge | True | 2017-10-16 | 0.00 | fading | 1.63 | 1.63 | 1.00 | False | False | 1 | 2.22 |
| #MeToo, October 2017 | 2017-10-15 | B12 | broad | Violence, trauma, death and grief | True | 2017-11-06 | 3.00 | fading | 1.72 | 1.72 | 2.00 | False | False | 1 | 1.78 |


Run time of this step: 1.8 minutes.
