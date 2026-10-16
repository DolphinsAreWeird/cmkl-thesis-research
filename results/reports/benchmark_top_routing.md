# Routing the daily top-500 Wikipedia pages into book themes (stage 2a)

Written 2026-10-15 04:03. Rule: prereg/addenda_benchmark/2026-10-15_a_top_pages_routing.json. No demand data read.

- Pool: 139,166 pages over 3,915 days (1,905,645 page-days in the top 500, after the namespace rule).
- Routed at cosine >= 0.7: 6,002 pages (4.3%); page-days routed: 105,412.
- Nodes with a series: 322 (broad 19, middle 85, narrow 218).
- Share of full weeks with any routed views, median over nodes: middle 17%, narrow 4%.

## Agreement with the hand-curated pages that appear in the pool

274 of 634 curated pages appear in the top-500 pool.

result | count
same node | 251
not routed | 18
other node | 5


## Most-viewed routed pages per broad theme (top 3, by total top-500 views)

- B01: List of Marvel Cinematic Universe films -> superheroes (0.74); Marvel Cinematic Universe -> superheroes (0.80); Batman v Superman: Dawn of Justice -> superheroes (0.71)
- B02: International Women's Day -> feminism (0.71); Pansexuality -> sexuality (0.71); Wedding anniversary -> weddings (0.74)
- B03: Bible -> bible (0.83); Jesus -> judaism (0.75); Muhammad -> islam (0.81)
- B04: Internet -> internet (0.71); Microsoft Windows -> computers (0.72); Index (statistics) -> statistics (0.76)
- B05: Critical race theory -> race relations (0.85); Black Lives Matter -> black life (0.81); South Africa -> apartheid (0.73)
- B06: List of highest-grossing films -> film (0.71); List of United States stand-up comedians -> comedians (0.86); List of stand-up comedians -> comedians (0.97)
- B07: Mother's Day -> motherhood (0.71); Asperger syndrome -> autism (0.81); Brothers (2009 film) -> brothers (0.85)
- B08: World War II -> world war ii (0.82); Adolf Hitler -> nazis (0.71); World War I -> world war i (0.86)
- B09: Earth -> earth sciences (0.72); Pirates of the Caribbean (film series) -> pirates (0.80); Ocean's 8 -> ocean (0.80)
- B10: International Workers' Day -> labor (0.71); Great Depression -> great depression (0.92); Google AdSense -> advertising (0.78)
- B11: Halloween -> halloween (0.88); Thanksgiving -> thanksgiving (0.87); Christmas -> christmas (0.75)
- B12: Deaths in 2024 -> death (0.78); Deaths in 2025 -> death (0.81); Deaths in 2023 -> death (0.81)
- B13: 2022 Russian invasion of Ukraine -> russian revolution (0.72); Vladimir Putin -> russian revolution (0.72); List of presidents of the United States -> presidents (0.95)
- B14: Friendship Day -> friendship (0.75); Kinds of Kindness -> kindness (0.75); Philosophy -> philosophy (0.77)
- B15: Pandemic -> epidemiology (0.77); List of epidemics -> epidemiology (0.83); Bubonic plague -> plague (0.81)
- B16: Cat -> cats (0.83); The Bear (TV series) -> bears (0.71); The Penguin (TV series) -> penguins (0.70)
- B17: Kobe Bryant -> basketball (0.75); FIFA World Cup -> soccer (0.72); Roger Federer -> tennis (0.76)
- B18: The Martian (film) -> mars (0.76); Mars Orbiter Mission -> mars (0.74); Opportunity (rover) -> mars (0.72)
- B19: Denial-of-service attack -> cybersecurity (0.73); Black Mafia Family -> mafia (0.73); Index of law articles -> law (0.72)


## Forecasts with each routing (four volume features, no shift states)

name | rows | months | friedman_stat | friedman_p | nemenyi_cd | series | k
R1. Print and ebook, horizon 1 | 39345 | 89 | 203.00447302208522 | 4.3512777161911755e-41 | 0.3984580078656457 | 511 | 7
R2. Seattle audiobooks, horizon 1 | 16013 | 86 | 18.819047619047524 | 0.00448040253171469 | 0.6004844290348117 | 225 | 7

### R1. Print and ebook, horizon 1

| pipeline | AvgRelMAE | ci_lo | ci_hi | median_rel | share_beats_naive | mean_rank | in_MCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| naive | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 3.166 | yes |
| lightgbm_D | 1.017 | 1.001 | 1.031 | 1.018 | 0.427 | 3.540 | yes |
| lightgbm_Wtop | 1.023 | 1.006 | 1.037 | 1.024 | 0.403 | 3.789 | yes |
| lightgbm_Wcur | 1.023 | 1.007 | 1.038 | 1.028 | 0.387 | 3.910 | yes |
| ridge_D | 1.076 | 1.061 | 1.091 | 1.045 | 0.319 | 4.364 | no |
| ridge_Wtop | 1.077 | 1.063 | 1.093 | 1.045 | 0.309 | 4.663 | no |
| ridge_Wcur | 1.078 | 1.063 | 1.093 | 1.048 | 0.321 | 4.568 | no |


### R2. Seattle audiobooks, horizon 1

| pipeline | AvgRelMAE | ci_lo | ci_hi | median_rel | share_beats_naive | mean_rank | in_MCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| naive | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 3.556 | yes |
| lightgbm_Wcur | 1.012 | 0.995 | 1.027 | 1.020 | 0.444 | 3.884 | yes |
| lightgbm_Wtop | 1.015 | 1.000 | 1.029 | 1.014 | 0.440 | 3.929 | yes |
| lightgbm_D | 1.017 | 1.003 | 1.030 | 1.016 | 0.418 | 4.129 | yes |
| ridge_D | 1.032 | 1.021 | 1.042 | 1.008 | 0.413 | 4.147 | yes |
| ridge_Wcur | 1.032 | 1.021 | 1.043 | 1.010 | 0.436 | 3.987 | yes |
| ridge_Wtop | 1.032 | 1.022 | 1.043 | 1.014 | 0.404 | 4.369 | yes |


### Paired ratios (print and ebook): geometric mean of MAE(other) / MAE(base)

base | other | ratio | ci_lo | ci_hi | share_other_better | series
ridge_D | ridge_Wcur | 1.002 | 1.0 | 1.004 | 0.466 | 511
ridge_D | ridge_Wtop | 1.001 | 1.0 | 1.002 | 0.38 | 511
ridge_Wcur | ridge_Wtop | 0.999 | 0.998 | 1.001 | 0.489 | 511
lightgbm_D | lightgbm_Wcur | 1.006 | 1.003 | 1.01 | 0.423 | 511
lightgbm_D | lightgbm_Wtop | 1.006 | 1.003 | 1.009 | 0.466 | 511
lightgbm_Wcur | lightgbm_Wtop | 0.999 | 0.996 | 1.003 | 0.491 | 511


Run time 6.7 min.
