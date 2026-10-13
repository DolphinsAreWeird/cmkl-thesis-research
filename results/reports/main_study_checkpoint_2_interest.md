# Main study, checkpoint 2: interest timelines from GDELT and Wikipedia

Khant Phyo Wai (student ID 01323050), CMKL University, honors thesis
Prepared 13 October 2026; updated the same evening with the decisions on the first version's open questions. Status: checkpoint for Khant's review. This step covers the interest side only. No Seattle, LibriVox, Goodreads, Amazon or NYT data were read or joined, and nothing here compares interest with demand.

## Summary

- **What exists now.** Every node of the approved taxonomy has a weekly interest series from English Wikipedia (concept pages, July 2015 to September 2026) and, where news covers it, from GDELT news themes (January 2017 to June 2021), with GDELT tone. The interest side stays on the approved v2 value list, with one v3 change: the value "violence" moved to the new narrow node B12.M01.N04 "Violence and violent crime". Shift labels follow the fixed record `prereg/study3_settings_2026-10-13.json` (the code checks its SHA-256) and addendum d (the start rule).
- **Coverage.** Wikipedia gives a usable series (at least 80% of weeks above the minimum volume) for 239 of 242 narrow, all 86 middle and all 19 broad nodes. GDELT gives one for 102 narrow, 61 middle and 18 broad nodes. 180 nodes are usable in both (101 narrow, 61 middle, 18 broad).
- **Final shifts.** Main set (narrow and middle levels, not seasonal, completed): 833 Wikipedia and 371 GDELT shifts. Of these, 687 and 371 are quality_ok (no quality flag), which is the tested set. Large (size 3 or more): 105 and 39, of which 58 and 39 are quality_ok. Seven Wikipedia shifts are title confusion (a TV series, film, company or person with the same name as the page). One GDELT code was dropped as figurative: `TAX_DISEASE_AMNESIA`.
- **Positive controls (interest side).**
  - COVID-19 and George Floyd / Black Lives Matter appear in both sources as sustained shifts that start in the expected week (epidemics: 20 January 2020 in GDELT, 27 January 2020 in Wikipedia; race and racism: 25 May 2020 in both). None of them carries a quality flag.
  - #MeToo is a sustained shift in GDELT from 9 October 2017. In Wikipedia it is a one-week rise ("fading", 1.8 times normal). Readers went to the "Sexual harassment" page, which is not one of the category's pages; by decision the pages stay as they are and this is reported.
  - The September 2019 climate strikes appear as short ("fading") shifts for the climate change value in both sources (about 2 times normal). At node level Wikipedia shows a short shift and GDELT none, because weather codes make up 45% of the GDELT node; by decision the node stays as it is (its label covers weather) and the value series is reported descriptively. Climate is not one of the fixed positive controls.
- **GDELT durations.** On the final shifts (main set, quality_ok, July 2017 to June 2021) the median shift lasts 1 week in GDELT and 1 week in Wikipedia; the ratio is 1.0 (ratio of means 1.05), so the GDELT thresholds stay at 4 / 3 / 2 weeks. Section 10 has the entry for `prereg/DEVIATIONS.md`.
- **Agreement between sources.** For nodes usable in both (July 2017 to June 2021), 31 of 143 (22%) quality_ok Wikipedia shifts in the main set have a GDELT shift in the same node within two weeks (7 of 13 of the large ones). The two sources rise together for large public events and mostly move on their own otherwise.
- **Still open** (section 13): 11 GDELT main-set shifts are driven by repeated pages from a single website (a feed artefact, found while checking for figurative use); they are flagged in a separate column but not yet excluded.

## 1. What was built

| Step | Script (`code/main_study/interest/`) | Output (`data/db/interest/`) |
|---|---|---|
| GDELT codes to readable text, family rules, similarity to every theme value | `01_gdelt_codes.py`, `_gdelt_rules.py` | `gdelt/codes.parquet`, `gdelt/code_value_cos.npy` |
| GDELT mapping with hand verdicts and the figurative-use verdicts, review sheet | `02_gdelt_map.py`, `_gdelt_review.py` | `gdelt/code_map.parquet`, `gdelt/review_gdelt_mappings.csv` |
| GDELT weekly volume and tone per value and node | `03_gdelt_series.py` | `gdelt/weekly_node.parquet`, `gdelt/weekly_value.parquet`, `gdelt/weekly_total.parquet` |
| Wikidata candidates for every theme value | `04_wiki_candidates.py` | `wiki/candidates.parquet` (API answers cached in `wiki/_*.json`) |
| Hand-chosen concept pages, resolved through the MediaWiki API, and their redirects | `05_wiki_articles.py`, `_wiki_choices.py` | `wiki/articles.parquet`, `wiki/articles_review.csv`, `wiki/redirects.parquet` |
| Daily views (pages, redirects with traffic, site total) | `06_wiki_pageviews.py` | `wiki/pv_daily/` (915 files), `wiki/total_daily.parquet`, `wiki/redirect_screen.parquet` |
| Wikipedia weekly interest per value and node | `07_wiki_series.py` | `wiki/weekly_node.parquet`, `wiki/weekly_value.parquet`, `wiki/article_daily_summary.csv` |
| Shift labels, seasonal flags, coverage | `08_shift_labels.py`, `_shifts.py` | `shifts.parquet`, `shift_weekly.parquet`, `coverage.csv` |
| Automatic quality flags for Wikipedia shifts (one day, desktop only) | `09_wiki_spike_check.py` | `wiki/shift_quality.parquet` |
| Driver code of every GDELT main-set shift and the evidence for the figurative-use check | `10_gdelt_drivers.py`, `_gdelt_url_samples.py` (run once, not in `run_all.sh`) | `gdelt/driver_codes.csv`, `gdelt/driver_evidence.csv`, `gdelt/figurative_url_samples.csv` |
| Title-confusion check, `quality_flag` and `quality_ok` in `shifts.parquet`, GDELT duration scaling | `11_quality_flags.py`, `_title_confusion.py` | `shifts.parquet`, `wiki/review_title_confusion.csv`, `gdelt_duration_scaling.json` |
| Controls, largest shifts, agreement between sources | `12_controls.py` | `controls_summary.csv`, `controls_weekly.csv`, `top_shifts_by_year.csv`, `shared_shifts.csv`, `checkpoint_tables.md` |

Shared helpers are in `_ci.py` (paths, taxonomy loading with the v3 move, embeddings, polite API calls, and the reader for the fixed settings). `run_all.sh` reruns everything; section 14 has run times.

**`shifts.parquet` columns added by this update:** `quality_flag` ('' when clean, otherwise one or more of 'one_day', 'desktop_only', 'title_confusion', comma separated), `quality_ok` (True when `quality_flag` is ''), `title_check` (the hand verdict for checked shifts), `wiki_driver` and `gdelt_driver` (the page or code that drove the rise), `gdelt_feed_artifact` (descriptive, see section 3.6), and `strict_start` (the strict reading of the start rule, kept as the robustness column). GDELT shifts get no automatic flag, so their `quality_flag` is ''.

## 2. Settings

All shift settings are read from `prereg/study3_settings_2026-10-13.json`. `_ci.settings()` checks the file's SHA-256 against `prereg/README.md` (eeeb6c80...), parses every number from the record's text and stops if the wording changes. The values used: normal level = median of the previous 26 weeks (current week excluded); ratio = share / normal; rising = ratio >= 1.5 and an 8-week Mann-Kendall test (current week included, Hamed-Rao variance) with tau > 0 and one-sided p < 0.10; start = first rising week after at least 8 consecutive weeks below 1.5; sustained >= 4 weeks (labelled in week 4), intermediate = 3, fading <= 2; size = peak ratio up to the labelling week; large = size >= 3.0; seasonal = a start within +/-2 ISO weeks of the same calendar week in at least half of the other years with data (kept out of the main set); minimum normal volume 1,000 views (Wikipedia) and 100 mentions (GDELT) per week; ISO weeks from Monday; narrow and middle levels tested, broad descriptive only. The labelling code was written after the record was fixed, so the labels never used other values.

- **Start rule (addendum d, confirmed).** The "armed" reading: once 8 weeks below 1.5 have passed, the next rising week starts a shift, even if a few elevated but not yet rising weeks come first; the arming is lost on a missing week or when a shift ends. The reason: an 8-week Mann-Kendall test does not reach p < 0.10 in the first or second week of a sudden jump; it does in the third (one-sided p = 0.067 for flat weeks followed by three high weeks). The strict reading is kept as the column `strict_start`. 87% of Wikipedia starts and 76% of GDELT starts meet it. All control starts do too, except Wikipedia COVID-19, whose first elevated week (20 January 2020, 5 times normal) was not yet rising.
- **Normal level.** All 26 previous weeks must be full weeks. The minimum volume is applied to the median raw volume (views or mentions) of the same 26 weeks. A week failing either is "not usable": it gets no ratio and breaks the quiet run.
- **Rising test.** Computed only when all 8 weeks are full weeks. One-sided p = 1 - Phi(z), with z from the Hamed-Rao test in `pymannkendall`.
- **Seasonal flag.** "Other years with data" are ISO years in which at least 3 of the 5 weeks around the same calendar week are usable. Calendar weeks are compared on a 52-week circle.
- **Shifts that end early.** Fading and intermediate are labelled in the week the ratio drops back below 1.5; size is the peak before that week. A shift still running at the end of the data is "censored", and one that hits a missing week is "interrupted". Both are kept out of the main set.
- **Limitation (decision 6).** Because of the rising test, sudden events start one or two weeks after the jump (Wikipedia COVID-19: jump in the week of 20 January, start a week later), and spikes shorter than three weeks never become shifts. This is intended: Study 2 covered short spikes, and this study is about shifts that pass the trend test.

## 3. GDELT themes to categories

### 3.1 Codes and readable text

The weekly GDELT file has 14,257 theme codes (codes with at least 50 mentions in a week; `TAX_WORLDLANGUAGES` was already excluded by the query). Each code was turned into text by removing its family prefix (`WB_1234_`, `TAX_FNCACT_`, `TAX_DISEASE_`, `EPU_POLICY_`, `CRISISLEX_T03_`, `UNGP_`, `SOC_`, `ECON_`, `USPEC_`, `NATURAL_DISASTER_` and others), lowercasing, turning underscores into spaces, splitting glued words with a word list (`CLIMATECHANGE` becomes "climate change"; disease names are never split), and spelling out a few acronyms (MSM, WMD, ICT, NGO, PPP). About 40 codes got a hand-written text where the stripped text meant nothing. The template is the taxonomy's own ("books about <text>"), with the same model (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, fastembed) and the same centred embedding space; the code checks that it reproduces `theme_value_embeddings.npy`.

### 3.2 Codes that are actors or entities, not topics

| Family rule | Codes excluded | Reason |
|---|---|---|
| Job titles and roles (`TAX_FNCACT_`) | 2,923 | a person by role (president, police, children, victim) |
| Species names (`TAX_WORLD...`, pests, plant diseases) | 2,839 | names matched as words, very noisy (bear market, Fox News, navy SEAL) |
| Ethnic and national groups (`TAX_ETHNICITY_`) | 942 | actor mentions (Russian, American, Black) |
| Named militant or political groups (`TAX_TERROR_`) | 758 | organisation names |
| Named parties (`TAX_POLITICAL_`) | 503 | organisation names |
| Religious groups, denominations, places of worship (`TAX_RELIGION_`) | 350 | members and buildings (Muslims, church, mosque) |
| Named aid and development organisations | 282 | organisation names |
| Currencies | 200 | names |
| Weapons | 130 | object names |
| Military ranks | 64 | titles |
| Place types (`SOC_POINTSOFINTEREST_`) | 60 | type of place mentioned (school, hospital) |
| Food commodities | 34 | commodity names, mostly market news |
| Named trade agreements | 28 | names |
| Cartels, one technical tag | 7 | names; `CRISISLEX_CRISISLEXREC` has no topic |

Together these are 9,120 codes and 28.1% of all mentions. Codes inside these families that name a topic were whitelisted: 17 belief systems (`TAX_RELIGION_ISLAM`, `_CHRISTIANITY`, `_BUDDHISM`, `_OCCULT`, `_WITCHCRAFT` and others), four generic free-trade codes, and three roles named after a control theme (epidemiologist, virologist, climatologist).

### 3.3 Similarity rule

Each remaining code (5,137) goes to its single most similar theme value when the cosine is at least 0.70. A code is never split across values, so it is counted once per node. I chose 0.70 after reading 45 examples in each band from 0.45 to 1.0: above 0.80 almost all were right, between 0.70 and 0.80 most were right, and below 0.65 most were wrong. 802 codes passed the threshold; every high-volume code and every code near a control category was then checked by hand.

### 3.4 Hand check

The review sheet `gdelt/review_gdelt_mappings.csv` has 1,090 rows, each with a verdict and a note. It covers: all candidate codes for the four control categories (found by similarity and by keyword search over all 14,257 codes); the 100 highest-volume automatically mapped codes; the two largest codes of every narrow and middle node, repeated until no unchecked code was left; every driver code of a GDELT main-set shift (section 3.6); and every other code with a hand verdict or a group rule. Group decisions are written as rules with reasons in `_gdelt_review.py`.

| Set (each code counted in its first set) | Rows | Correct | Kept, borderline | Added by hand (to any node) | Moved to another value | Dropped (wrong, general flag, not a topic, figurative) | Checked, correctly left out |
|---|---|---|---|---|---|---|---|
| Control-category candidates | 716 | 95 | 12 | 189 | 30 | 5 | 385 |
| 100 highest-volume automatically mapped codes | 93 | 66 | 4 | 0 | 4 | 19 | 0 |
| Largest codes per narrow and middle node | 127 | 97 | 22 | 1 | 7 | 0 | 0 |
| Driver codes of GDELT main-set shifts (figurative check) | 9 | 6 | 1 | 1 | 0 | 1 | 0 |
| Other codes with a hand verdict or group rule | 145 | 5 | 0 | 87 | 18 | 30 | 5 |
| All | 1090 | 269 | 39 | 278 | 59 | 55 | 390 |

Of the 100 highest-volume automatic mappings, 73 were kept (68 correct, 5 borderline); 15 were very general word flags, 8 went to a better value, 2 were not topics and 2 were wrong. What the check found:

- **General word flags** (dropped): `USPEC_POLITICS_GENERAL1` (485 million mentions), `GENERAL_GOVERNMENT`, `GENERAL_HEALTH`, `MEDICAL`, `EPU_POLICY_*`, `EPU_ECONOMY*`, `LEGISLATION`, `MANMADE_DISASTER_IMPLIED`, `CRISISLEX_T03_DEAD`, `LEADER`. They fire on one common word in a large share of all news; kept, they would make up most of a node's volume and hide topical change (decision 5 agreed).
- **Wrong by word form**: `LEADER` matched the self-help value leadership; `WB_621_HEALTH_NUTRITION_AND_POPULATION` matched nutrition; `KILL` matched murder; `WB_1350_PHARMACEUTICALS` matched recreational drugs; `HUMAN_RIGHTS_ABUSES_WATERBOARDING` matched surfing; `TAX_DISEASE_BLACK_DEATH` matched Black life.
- **Armed-conflict violence.** `WB_2432_FRAGILITY_CONFLICT_AND_VIOLENCE` (250 million mentions), `WB_2433_CONFLICT_AND_VIOLENCE` and `WB_2462_POLITICAL_VIOLENCE_AND_WAR` matched the value violence; they go to war. Revolutionary violence goes to revolution and violent unrest to activism.
- **The v3 move, rechecked (decision 8).** With "violence" in its own node "Violence and violent crime", `WB_930_VIOLENCE_PREVENTION` stays on it, and `UNGP_CRIME_VIOLENCE` ("crime violence", 94 million mentions) and `WB_741_URBAN_CRIME_AND_VIOLENCE` move from crime to violence: the new node names exactly this, and their cosine to crime and to violence is nearly equal. Armed-conflict codes stay with war and police brutality with police. The recheck also found that two "violent storm" codes had been blocked from the disaster rule by an earlier verdict; they now go to disasters.
- **Epidemics.** The model places "pandemic" nearest weather (cosine 0.48) and "coronavirus" at only 0.51; epidemic terms and named epidemic diseases of people (89 codes) were mapped by a hand rule. Vaccination went to public health, general infection codes to disease.
- **Climate and weather.** Natural disaster events (148 codes) went to disasters, World Bank climate policy codes (27) to climate change; `CRISISLEX_O01_WEATHER` (39 million mentions) stays on weather, so 45% of the GDELT climate node's mentions are weather.
- **Borderline choices** kept with notes: `HARASSMENT` on sexual violence; Islamophobia codes on Islam; police brutality on police; hate speech and hate crime left out of racism.

Result: 1,037 codes are mapped (27.0% of all mentions). Codes reach 112 narrow, 64 middle and 18 broad nodes.

### 3.5 Weekly GDELT series

For each value and node: volume share = mentions of its codes / all mentions of all 14,257 codes that week; tone, positive and negative = mention-weighted means of the codes' weekly averages. A node counts the codes of its own values and of all values below it. The first week (26 December 2016, one day) and the last (28 June 2021, three days) are partial and flagged, and treated as missing. GDELT keeps a code-week only with 50 or more mentions, and an article with two codes of the same node counts twice, so shares are shares of mentions, not of articles.

### 3.6 Figurative-use check (decision 5)

For each GDELT shift at the tested levels in the main set, `10_gdelt_drivers.py` finds the code that contributed most to the rise (largest rise in mentions over the first weeks against its median week in the 26 weeks before). The 123 distinct driver codes each got a verdict with a reason (`_gdelt_review.FIGURATIVE`, also in the review sheet, columns `figurative_check` and `figurative_note`):

- For 20 codes whose word is often used figuratively in news (witchcraft, amnesia, blindness, deafness, gambling, icy, earthquake, suicide, cancer...) or whose rises looked odd, I sampled up to 40 article URLs on the middle day of each of the code's two highest-volume weeks and of every shift week it drove (89 code-days; GDELT URLs usually contain the headline words). The source is GDELT GKG 2.0 in BigQuery, the project's sandbox, the same route as `code/gdelt_weekly.py`; the samples scanned 50 GB of October's free quota (a free dry run checked the cost first). The samples are in `gdelt/figurative_url_samples.csv`.
- For the other 103 codes the verdict rests on the meaning of the code and on its highest-volume weeks: World Bank topic codes are assigned from many terms, so figurative use does not apply; for the rest the top weeks match news on the topic.

Result: **one code is figurative and dropped: `TAX_DISEASE_AMNESIA`.** Its rises are political figures of speech ("Dems accuse GOP official of amnesia on Trump vulgarity", January 2018; "the people's republic of amnesia", June 2019; "don't forget the GOP tried to overturn the election", May 2021), with no medical amnesia in the samples. After the drop, the rerun found 122 driver codes, all with verdicts.

Two findings go beyond the rule:

- **`TAX_RELIGION_WITCHCRAFT` is not driven by "witch hunt".** None of its six sampled days contains the phrase. Its shift weeks are witchcraft and exorcism news and witch TV series (Charmed, American Horror Story), so it stays (literal). Its largest rise, in May 2018, is mostly repeated pages from one website (unitaangola.org, 32 of 40 URLs).
- **Single-website feed artefacts.** One site (bjhmoh.cn, template pages such as "index.php?r=archives/guide/body") supplies 23 to 38 of 40 sampled URLs on most shift weeks of `WB_1447_GERIATRICS` and `WB_1532_TEACHER_TRAINING`, and 13 to 34 of 40 for `TAX_DISEASE_DEAFNESS`. This is not figurative use, so these codes stay under the rule. Instead, `shifts.parquet` has a descriptive column `gdelt_feed_artifact`: True when the URL sample of the driver code on the shift's start week has at least half of its URLs from one site. It is True for 11 GDELT main-set shifts, False for 64, and empty for the 296 whose driver was not sampled. It is not part of `quality_ok` (see section 13).

| Node | Level | Start | Label | Size | Driver code | Most common site in the URL sample (start week) |
|---|---|---|---|---|---|---|
| deaf / blindness (B15.M05.N02) | narrow | 2018-08-13 | fading | 1.8 | `TAX_DISEASE_DEAFNESS` | bjhmoh.cn (30 of 40) |
| Magic, witches and fantasy creatures (B01.M02) | middle | 2018-05-07 | sustained | 3.4 | `TAX_RELIGION_WITCHCRAFT` | unitaangola.org (32 of 40) |
| fairies / witches (B01.M02.N02) | narrow | 2018-05-07 | sustained | 6.0 | `TAX_RELIGION_WITCHCRAFT` | unitaangola.org (32 of 40) |
| School, adolescence and coming of age (B07.M02) | middle | 2017-12-25 | sustained | 5.6 | `WB_1447_GERIATRICS` | bjhmoh.cn (37 of 40) |
| coming of age / aging (B07.M02.N01) | narrow | 2018-01-08 | sustained | 11.8 | `WB_1447_GERIATRICS` | bjhmoh.cn (34 of 40) |
| coming of age / aging (B07.M02.N01) | narrow | 2019-02-04 | fading | 1.8 | `WB_1447_GERIATRICS` | bjhmoh.cn (38 of 40) |
| School, adolescence and coming of age (B07.M02) | middle | 2019-04-01 | fading | 1.6 | `WB_1447_GERIATRICS` | bjhmoh.cn (36 of 40) |
| teaching / homeschooling (B04.M05.N01) | narrow | 2017-12-25 | fading | 1.5 | `WB_1532_TEACHER_TRAINING` | bjhmoh.cn (24 of 40) |
| teaching / homeschooling (B04.M05.N01) | narrow | 2018-08-13 | fading | 1.7 | `WB_1532_TEACHER_TRAINING` | bjhmoh.cn (23 of 40) |
| teaching / homeschooling (B04.M05.N01) | narrow | 2019-04-01 | sustained | 2.3 | `WB_1532_TEACHER_TRAINING` | bjhmoh.cn (29 of 40) |
| teaching / homeschooling (B04.M05.N01) | narrow | 2019-09-09 | fading | 2.1 | `WB_1532_TEACHER_TRAINING` | bjhmoh.cn (23 of 40) |

## 4. Wikipedia concept pages to categories

### 4.1 Page choice

For each of the 614 theme values, `04_wiki_candidates.py` searched Wikidata through the official API (`wbsearchentities`) with the value and with its gloss, read each candidate's English Wikipedia sitelink and description, and read its "instance of" classes from the Wikidata query service. Candidates that are people, books, films, albums, TV series, journals, organisations, names, lists or disambiguation pages were marked unsuitable; the first suitable candidate became the automatic pick (580 values had one).

I checked all 614 values by hand, beyond the controls and the top 100. The automatic pick was often the wrong kind of page ("vampires" gave the 1915 film Les Vampires, "orphans" the Chicago Cubs, "pets" positron emission tomography, "dragons" the Wales football team; "nature", "sociology" and "nutrition" gave journals). The hand choices are in `_wiki_choices.py`, with notes. Related pages were added only where the value's own gloss names them or the main page is ambiguous (18 values, 20 extra pages), for example Epidemic and Pandemic for "plague", Rape and Sexual assault for "sexual violence", Global warming for "climate change", Climate for "weather". Event and movement pages (COVID-19 pandemic, Black Lives Matter, Me Too movement) were not used. By decision, "Sexual harassment" was not added after the #MeToo result (decision 2). `05_wiki_articles.py` resolved every title with the MediaWiki API; two first choices were disambiguation pages and were replaced.

| Values | Checked | Automatic pick kept | Automatic pick replaced | Of which had no automatic pick |
|---|---|---|---|---|
| All | 614 | 411 | 203 | 34 |
| 100 with the most works | 100 | 57 | 43 | 12 |
| Control categories | 12 | 10 | 2 | 1 |

"Most works" is the taxonomy's own support count (number of works carrying the value); it is a catalogue count, not a demand measure. The result is 634 value-page pairs and 624 distinct pages. The value "violence" keeps its page (Violence), which now counts in the node B12.M01.N04.

**Shared pages (decision 7: acceptable as they are).** A page used by more than one value is counted once in any node that contains both:

- Disease: disease, illness
- Family: family, family and relationships, family life
- Health: health, health and fitness
- Mother: motherhood, mothers and daughters
- Outdoor recreation: outdoor recreation, outdoors
- Religion: religion, religion and spirituality
- Sales: marketing and sales, sales
- Sport: sports, sports and recreation

### 4.2 Page views, redirects and title moves

`06_wiki_pageviews.py` fetched daily views from the official Wikimedia REST API (per-article, all-access, agent=user, 1 July 2015 to 30 September 2026) and the daily total of English Wikipedia user views (aggregate endpoint), at about one request per second with the project User-Agent. There were no failed or empty answers.

The pageviews API does not follow redirects, and after a page move the old title keeps the earlier history (the earlier finding that moved titles showed zero views). The 624 pages have 18,079 redirects. They were screened in batches of 50 with the MediaWiki API (views in the last 60 days, and the `{{R from move}}` / `{{R from merge}}` categories); 1,924 were moved or merged titles or carried real recent traffic; their monthly history was fetched, and the 291 that carried at least 1% of their page's total views, or at least 10% of it in some month with 1,000 views or more, were fetched daily and added to their page. Redirects left out carry 1.7% of the last 60 days of views. This repairs the title moves ("LGBT" to "LGBTQ people", "Global warming" to "Climate change", "RMS Titanic" to "Titanic" and others); all 624 page series have views on every day of the period.

The site total agrees with the monthly totals already in the project to within 0.1% in every month. During the COVID-19 lockdown (30 March to 3 May 2020) all English Wikipedia traffic was 15% to 20% above its usual level, which lowers shares in those weeks.

### 4.3 Weekly Wikipedia series

Weekly interest of a value or node = weekly views of its pages (each page once, with kept redirects) / total English Wikipedia user views that week. The first week (29 June 2015) and the last (28 September 2026) are partial and flagged. Each node-week also stores the share of the week's views that came on its busiest day.

## 5. Shift labels and quality flags

| Source | Level | Fading | Intermediate | Sustained | Interrupted or censored | Seasonal (any label) | Main set | Main set, quality_ok | Large in main set | Large, quality_ok |
|---|---|---|---|---|---|---|---|---|---|---|
| Wikipedia | Narrow | 561 | 62 | 112 | 10 | 108 | 628 | 523 | 85 | 46 |
| Wikipedia | Middle | 197 | 10 | 33 | 3 | 36 | 205 | 164 | 20 | 12 |
| Wikipedia | Broad (descriptive) | 36 | 3 | 13 | 1 | 27 | 0 | 0 | 0 | 0 |
| GDELT | Narrow | 224 | 8 | 43 | 3 | 32 | 245 | 245 | 29 | 29 |
| GDELT | Middle | 113 | 5 | 18 | 2 | 12 | 126 | 126 | 10 | 10 |
| GDELT | Broad (descriptive) | 24 | 3 | 7 | 0 | 4 | 0 | 0 | 0 | 0 |

The main set is narrow and middle levels, not seasonal, and not censored or interrupted. Seasonal shifts are mostly holidays and anniversaries (Christmas and other holidays, the 11 September and JFK anniversaries, remembrance days for the world wars, the Titanic anniversary, World AIDS Day, Mother's Day, Pride month, the International Day of Yoga) and sports seasons.

**Quality flags (decision 4).** `one_day` and `desktop_only` come from `09_wiki_spike_check.py` as they were, not tuned: for each Wikipedia shift at the tested levels, one day carried at least half of a week's views of the node, or the rise of the page that drove it came at least 90% from desktop views while that page's usual desktop share is at least 25 points lower (automated traffic is mostly desktop). In the Wikipedia main set: 687 have no flag, 89 are desktop_only, 35 one_day, 15 both one_day and desktop_only, and 7 title_confusion (833 in all). Study 3 leaves shifts with `quality_ok` False out of the tested set; they still count in the donor and placebo-year screens, and all shifts are kept for a robustness run.

**Title-confusion check.** I checked every large Wikipedia shift in the main set (105) and the 50 largest other Wikipedia main-set shifts by size (155 in all). For each, `11_quality_flags.py` lists the page or pages carrying the rise (with kept redirects), the peak day, and any same-named page (a TV series, film, game, song or person) in the English Wikipedia daily top-500 list on the peak day and the days around it (`data/raw/wiki_top_daily.json`). I marked `title_confusion` where such a page clearly drove the rise. Every verdict has a one-line reason in `wiki/review_title_confusion.csv` (verdicts in `_title_confusion.py`). Seven shifts are title confusion:

| Node | Level | Start | Size | Reason |
|---|---|---|---|---|
| robin hood (B08.M04.N05) | narrow | 2018-11-05 | 3.2 | the film Robin Hood (2018) opened on 21 Nov; Robin_Hood_(2018_film) had 35,506 views that day, the legend page peaked the next day |
| utopia (B04.M09.N02) | narrow | 2020-09-21 | 2.8 | the TV series Utopia (2020) started on 25 Sep (41,869 views that day); the concept page peaked on 26 Sep |
| robin hood (B08.M04.N05) | narrow | 2021-01-25 | 2.5 | the trading app Robinhood during the GameStop events: Robinhood_(company) had 244,717 views on 28 Jan, the Robin Hood page 19,163 (usual 3,273); a company rather than a series, same mechanism |
| birds / insects (B16.M02.N02) | narrow | 2024-10-28 | 3.2 | the TV series The Penguin (finale late Oct): The_Penguin_(TV_series) 59,549 views on 29 Oct, the Penguin page peaked on 30 Oct |
| amish (B05.M03.N03) | narrow | 2024-11-04 | 3.4 | the person Amish Shah (US House candidate) on election night: Amish_Shah 25,797 views on 6 Nov, the same day the Amish page peaked |
| School, adolescence and coming of age (B07.M02) | middle | 2025-03-10 | 3.6 | the TV series Adolescence (Netflix, March 2025), as in the narrow node |
| adolescence / runaways (B07.M02.N05) | narrow | 2025-03-10 | 13.5 | the TV series Adolescence (Netflix, March 2025): Adolescence_(TV_series) 275,339 views on 29 Mar, the concept page peaked on 30 Mar |

The Robinhood case is a company (a trading app) rather than a series or a person; the mechanism is the same, so I marked it. Not marked: rises where a series or film drew readers to a page with a different title (Mindhunter and the Ted Bundy series to "Serial killer", The Queen's Gambit to "Chess", the film The Odyssey to "Trojan War"). These are theme interest driven by an adaptation, not confusion. A few unflagged spikes have no clear cause (Pet in May 2022, Superhero in March 2025), and two look automated rather than confused: "Information" and "Communication" have identical daily views on 30 April 2026. These are noted in the review file but not flagged, since they are not title confusion.

## 6. Coverage

A node has a usable series when at least 80% of its weeks pass the minimum volume (weeks counted from January 2016 for Wikipedia and from July 2017 for GDELT).

| Level | Nodes | Wikipedia usable | GDELT with any code | GDELT usable | Usable in both |
|---|---|---|---|---|---|
| Broad | 19 | 19 | 18 | 18 | 18 |
| Middle | 86 | 86 | 64 | 61 | 61 |
| Narrow | 242 | 239 | 112 | 102 | 101 |

The 130 narrow nodes without GDELT codes are themes that the GDELT theme list does not cover with topical codes: fiction and fantasy, arts and crafts, sports, science and mathematics, philosophy and self-help, and some history (the world wars, the Cold War). The new node B12.M01.N04 "Violence and violent crime" is usable in both sources. All four control nodes are usable in both sources in every week.

## 7. Positive controls (interest side)

| Control | Series | Source | Shift starts in expected window | Start | Label (week) | Size | Whole-course peak | Weeks >= 1.5 | Max ratio in window | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Epidemics and plagues, COVID-19 | node B15.M04.N05 | Wikipedia | yes | 2020-01-27 | sustained (2020-02-17) | 7.65 | 56.92 | 14 | 56.92 | none |
| Epidemics and plagues, COVID-19 | node B15.M04.N05 | GDELT | yes | 2020-01-20 | sustained (2020-02-10) | 14.13 | 27.22 | 17 | 27.22 | none |
| Epidemics and plagues, COVID-19 | value: plague | Wikipedia | yes | 2020-01-27 | sustained (2020-02-17) | 9.85 | 76.23 | 14 | 76.23 |  |
| Epidemics and plagues, COVID-19 | value: plague | GDELT | yes | 2020-01-20 | sustained (2020-02-10) | 12.96 | 31.27 | 18 | 31.27 |  |
| Race and racism, George Floyd and BLM | node B05.M02.N02 | Wikipedia | yes | 2020-05-25 | sustained (2020-06-15) | 5.28 | 5.28 | 8 | 5.28 | none |
| Race and racism, George Floyd and BLM | node B05.M02.N02 | GDELT | yes | 2020-05-25 | sustained (2020-06-15) | 14.04 | 14.04 | 12 | 14.04 | none |
| Race and racism, George Floyd and BLM | value: racism | Wikipedia | yes | 2020-05-25 | sustained (2020-06-15) | 6.69 | 6.69 | 8 | 6.69 |  |
| Race and racism, George Floyd and BLM | value: racism | GDELT | yes | 2020-05-25 | sustained (2020-06-15) | 14.58 | 14.58 | 12 | 14.58 |  |
| Sexual and domestic violence, #MeToo | node B12.M01.N02 | Wikipedia | yes | 2017-10-16 | fading (2017-10-23) | 1.77 | 1.77 | 1 | 1.77 | none |
| Sexual and domestic violence, #MeToo | node B12.M01.N02 | GDELT | yes | 2017-10-09 | sustained (2017-10-30) | 2.09 | 2.48 | 10 | 2.34 | none |
| Sexual and domestic violence, #MeToo | value: sexual violence | Wikipedia | no |  |  |  |  |  | 1.84 |  |
| Sexual and domestic violence, #MeToo | value: sexual violence | GDELT | yes | 2017-10-16 | sustained (2017-11-06) | 2.41 | 2.56 | 10 | 2.48 |  |
| Climate change and weather, climate strikes | node B09.M07.N02 | Wikipedia | yes | 2019-09-23 | fading (2019-09-30) | 1.85 | 1.85 | 1 | 1.85 | none |
| Climate change and weather, climate strikes | node B09.M07.N02 | GDELT | no |  |  |  |  |  | 1.58 |  |
| Climate change and weather, climate strikes | value: climate change | Wikipedia | yes | 2019-09-23 | fading (2019-09-30) | 1.98 | 1.98 | 1 | 1.98 |  |
| Climate change and weather, climate strikes | value: climate change | GDELT | yes | 2019-09-16 | fading (2019-09-30) | 2.3 | 2.3 | 2 | 2.3 |  |

"Shift starts in expected window" means a shift (any label) starts in the weeks around the event, or one is already running then. Size is the peak ratio up to the labelling week; whole-course peak and weeks at 1.5 or more are descriptive. The value rows are descriptive.

**Epidemics and plagues, COVID-19** (node B15.M04.N05, Epidemics and plagues; expected around March 2020). Ratio = share / median of the previous 26 weeks.

| Week | W node | G node | W plague | G plague | Events (W node / G node) | G tone |
| --- | --- | --- | --- | --- | --- | --- |
| 2020-01-06 | 1.01 | 1.25 | 1.08 | 1.27 | - / - | -0.45 |
| 2020-01-13 | 1.00 | 1.40 | 1.01 | 1.44 | - / - | -0.52 |
| 2020-01-20 | 5.01 | 7.07* | 6.31 | 6.95* | - / start | -1.02 |
| 2020-01-27 | 7.65* | 13.22* | 9.85* | 12.45* | start / - | -0.36 |
| 2020-02-03 | 5.41* | 14.13* | 6.91* | 12.96* | - / - | -0.10 |
| 2020-02-10 | 3.23* | 12.96* | 3.99* | 11.64* | - / sustained (size 14.1) | 0.26 |
| 2020-02-17 | 3.30 | 11.67* | 4.12 | 10.39* | sustained (size 7.7) / - | 0.37 |
| 2020-02-24 | 14.56* | 15.37* | 19.38* | 14.77* | - / - | 0.06 |
| 2020-03-02 | 9.82* | 16.19* | 12.86* | 16.26* | - / - | 0.24 |
| 2020-03-09 | 56.92* | 22.16* | 76.23* | 24.26* | - / - | 0.15 |
| 2020-03-16 | 33.25* | 27.22* | 43.27* | 31.27* | - / - | 0.39 |
| 2020-03-23 | 20.78* | 26.90* | 26.42* | 30.83* | - / - | 0.38 |
| 2020-03-30 | 11.65* | 25.10* | 13.65* | 29.09* | - / - | 0.40 |
| 2020-04-06 | 7.80 | 22.96* | 8.99 | 26.87* | - / - | 0.46 |
| 2020-04-13 | 4.76 | 19.73 | 5.38 | 22.98 | - / - | 0.51 |
| 2020-04-20 | 2.31 | 5.58 | 2.42 | 6.74 | - / - | 0.60 |
| 2020-04-27 | 1.56 | 2.44 | 1.57 | 3.18 | - / - | 0.71 |
| 2020-05-04 | 1.14 | 1.72 | 1.12 | 2.33 | - / - | 0.64 |
| 2020-05-11 | 0.92 | 1.56 | 0.90 | 2.04 | - / - | 0.59 |
| 2020-05-18 | 0.76 | 1.40 | 0.74 | 1.83 | - / - | 0.79 |
| 2020-05-25 | 0.67 | 1.12 | 0.65 | 1.46 | - / - | 0.71 |

`*` = rising week (ratio >= 1.5 and 8-week Mann-Kendall tau > 0, one-sided p < 0.10). G tone = GDELT tone of the node minus its median of the previous 26 weeks (negative = more negative coverage).


**Race and racism, George Floyd and BLM** (node B05.M02.N02, Race and racism; expected late May to June 2020). Ratio = share / median of the previous 26 weeks.

| Week | W node | G node | W racism | G racism | Events (W node / G node) | G tone |
| --- | --- | --- | --- | --- | --- | --- |
| 2020-04-27 | 0.88 | 0.60 | 0.77 | 0.59 | - / - | -0.46 |
| 2020-05-04 | 0.96 | 0.67 | 0.87 | 0.66 | - / - | -0.63 |
| 2020-05-11 | 0.94 | 0.79 | 0.86 | 0.78 | - / - | -0.91 |
| 2020-05-18 | 0.94 | 0.97 | 0.86 | 0.97 | - / - | -0.13 |
| 2020-05-25 | 2.09* | 2.70* | 2.51* | 2.78* | start / start | -1.28 |
| 2020-06-01 | 5.28* | 13.14* | 6.69* | 13.68* | - / - | -0.67 |
| 2020-06-08 | 4.48* | 14.04* | 4.90* | 14.58* | - / - | -0.21 |
| 2020-06-15 | 2.89* | 9.54* | 3.14* | 9.85* | sustained (size 5.3) / sustained (size 14.0) | 0.24 |
| 2020-06-22 | 2.37 | 7.61* | 2.66 | 7.82* | - / - | 0.72 |
| 2020-06-29 | 1.97 | 4.61 | 2.12 | 4.77 | - / - | 0.69 |
| 2020-07-06 | 1.71 | 2.98 | 1.77 | 3.11 | - / - | 0.71 |
| 2020-07-13 | 1.54 | 2.56 | 1.57 | 2.67 | - / - | 0.79 |
| 2020-07-20 | 1.40 | 2.42 | 1.37 | 2.53 | - / - | 0.31 |
| 2020-07-27 | 1.26 | 1.91 | 1.15 | 1.99 | - / - | 0.70 |
| 2020-08-03 | 1.19 | 1.58 | 1.02 | 1.64 | - / - | 0.83 |

`*` = rising week (ratio >= 1.5 and 8-week Mann-Kendall tau > 0, one-sided p < 0.10). G tone = GDELT tone of the node minus its median of the previous 26 weeks (negative = more negative coverage).


**Sexual and domestic violence, #MeToo** (node B12.M01.N02, Sexual violence and domestic violence; expected October 2017). Ratio = share / median of the previous 26 weeks.

| Week | W node | G node | W sexual violence | G sexual violence | Events (W node / G node) | G tone |
| --- | --- | --- | --- | --- | --- | --- |
| 2017-08-28 | 1.03 | 0.92 | 1.04 | 0.94 | - / - | -0.08 |
| 2017-09-04 | 1.01 | 0.95 | 1.00 | 0.96 | - / - | -0.33 |
| 2017-09-11 | 1.07 | 0.87 | 1.03 | 0.89 | - / - | -0.01 |
| 2017-09-18 | 1.02 | 1.06 | 0.94 | 1.06 | - / - | 0.24 |
| 2017-09-25 | 1.00 | 1.00 | 0.95 | 0.97 | - / - | 0.02 |
| 2017-10-02 | 1.03 | 1.12 | 0.96 | 1.11 | - / - | 0.31 |
| 2017-10-09 | 1.24 | 1.91* | 1.19 | 2.10 | - / start | 0.48 |
| 2017-10-16 | 1.77* | 1.99* | 1.84 | 2.15* | start / - | 0.32 |
| 2017-10-23 | 1.29 | 1.82* | 1.23 | 1.94* | fading (size 1.8) / - | 0.20 |
| 2017-10-30 | 1.29 | 2.09* | 1.22 | 2.36* | - / sustained (size 2.1) | 0.37 |
| 2017-11-06 | 1.32 | 2.30* | 1.23 | 2.41* | - / - | 0.15 |
| 2017-11-13 | 1.30 | 2.34* | 1.23 | 2.48* | - / - | 0.40 |
| 2017-11-20 | 1.24 | 2.48* | 1.14 | 2.56* | - / - | 0.18 |
| 2017-11-27 | 1.43 | 2.20* | 1.24 | 2.38* | - / - | 0.22 |
| 2017-12-04 | 1.21 | 2.05* | 1.15 | 2.28* | - / - | 0.61 |

`*` = rising week (ratio >= 1.5 and 8-week Mann-Kendall tau > 0, one-sided p < 0.10). G tone = GDELT tone of the node minus its median of the previous 26 weeks (negative = more negative coverage).


**Climate change and weather, climate strikes** (node B09.M07.N02, Climate change and weather; expected September 2019). Ratio = share / median of the previous 26 weeks.

| Week | W node | G node | W climate change | G climate change | Events (W node / G node) | G tone |
| --- | --- | --- | --- | --- | --- | --- |
| 2019-07-29 | 0.98 | 1.05 | 1.01 | 1.06 | - / - | -0.09 |
| 2019-08-05 | 0.85 | 1.19 | 0.86 | 1.05 | - / - | -0.38 |
| 2019-08-12 | 0.88 | 1.14 | 0.88 | 1.06 | - / - | -0.18 |
| 2019-08-19 | 1.04 | 1.24 | 1.06 | 1.47 | - / - | -0.30 |
| 2019-08-26 | 1.00 | 1.19 | 1.00 | 1.26 | - / - | -0.62 |
| 2019-09-02 | 1.02 | 1.13 | 1.03 | 1.05 | - / - | -0.60 |
| 2019-09-09 | 1.05 | 1.04 | 1.06 | 1.18 | - / - | -0.21 |
| 2019-09-16 | 1.33 | 1.46 | 1.38 | 2.00* | - / - | -0.16 |
| 2019-09-23 | 1.85* | 1.58 | 1.98* | 2.30* | start / - | 0.18 |
| 2019-09-30 | 1.39 | 0.97 | 1.45 | 1.18 | fading (size 1.8) / - | 0.25 |
| 2019-10-07 | 1.29 | 1.12 | 1.33 | 1.33 | - / - | -0.21 |
| 2019-10-14 | 1.21 | 0.91 | 1.24 | 1.06 | - / - | -0.02 |
| 2019-10-21 | 1.05 | 0.94 | 1.07 | 1.08 | - / - | 0.13 |
| 2019-10-28 | 1.00 | 0.91 | 1.01 | 1.07 | - / - | 0.22 |
| 2019-11-04 | 1.04 | 0.93 | 1.04 | 1.09 | - / - | 0.49 |

`*` = rising week (ratio >= 1.5 and 8-week Mann-Kendall tau > 0, one-sided p < 0.10). G tone = GDELT tone of the node minus its median of the previous 26 weeks (negative = more negative coverage).

What the tables show:

- **COVID-19.** Both sources pass. GDELT starts on 20 January 2020, Wikipedia a week later, after a jump to 5 times normal that did not yet pass the rising test. Wikipedia peaked at 57 times normal in the week of 9 March, GDELT at 27 times a week later; the ratio stayed at 1.5 or more for 14 weeks in Wikipedia and 17 in GDELT.
- **George Floyd and Black Lives Matter.** Both sources pass. Both start in the week of 25 May 2020 and are labelled sustained in week 4 (15 June). GDELT rose more (14 times normal) than Wikipedia (5 times).
- **#MeToo.** GDELT passes: a sustained shift from 9 October 2017, about 2 times normal for 10 weeks. Wikipedia rose to 1.8 times normal in the week of 16 October and fell back the next week, so it is labelled fading, and the value "sexual violence" alone did not form a shift. Readers went to the "Sexual harassment" page instead: 9.0 times its normal level that week and 2.5 to 3.3 times through early December (a check outside the pipeline, two API requests). That page is not in the category, while the GDELT side includes `HARASSMENT`. By decision the category's pages stay as they are; on the demand side this control fails the minimum-size rule and is not tested (addendum f), so nothing is changed after seeing it. With "violence" moved to its own node (v3), the Wikipedia node peak is 1.77 times normal instead of 1.71; the label is unchanged.
- **Climate strikes (descriptive).** The climate change value shows a short shift in both sources: GDELT from 16 September 2019 (2.3 times normal) and Wikipedia from 23 September (2.0 times), both fading. At node level Wikipedia shows a short shift and GDELT none (peak 1.6 times, not rising), because weather codes make up 45% of the GDELT node. By decision the node stays as it is: its approved label covers weather, and climate is not one of the fixed positive controls.

GDELT tone dropped in the first week of the George Floyd protests (-1.3, from -0.1 the week before) and of the COVID-19 news (-1.0, from -0.5), and was slightly positive in the weeks after both and during #MeToo (0.2 to 0.5). Tone is not used for any label.

## 8. Largest shifts per source and year

The tables list the 10 largest main-set shifts per source and year. Wikipedia rows show the page that drove the rise and the final `quality_flag`; GDELT rows show the driver code and the feed-artefact check where the code was sampled. Of the 110 Wikipedia rows, 53 carry a quality flag. Flags are common among the largest rises: 47 of the 105 large Wikipedia main-set shifts are flagged (19 desktop_only, 16 one_day, 7 both, 5 title_confusion), against 146 of all 833 main-set shifts.

Many unflagged Wikipedia rows match known events: the 2016 US election (presidents, fascism), Charlottesville in August 2017 (fascism), the First World War centenary in November 2018, COVID-19, George Floyd (race and racism, and the American Civil War through the statue debate), the Israel-Gaza fighting of May 2021 and October 2023 (Jewish life), the invasion of Ukraine in February 2022 (Cold War, Second World War), the death of Elizabeth II (monarchy) and the death of Pope Francis and the conclave in 2025 (Catholic Church). The Trojan War rises of December 2025 and July 2026 most likely follow the trailer and release of the film The Odyssey. Most GDELT rows also follow news events (racism codes in July 2019 and March 2021, antisemitism, Islamophobia in October 2020, aviation incidents); the witchcraft and geriatrics rows are discussed in section 3.6.

**GDELT, 2017** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| School, adolescence and coming of age (B07.M02) | middle | 2017-12-25 | sustained | 5.6 | 6.3 | 14 | `WB_1447_GERIATRICS` | yes |
| The Holocaust, Nazism and genocide (B08.M03) | middle | 2017-11-20 | fading | 3.4 | 3.4 | 1 | `WB_2509_GENOCIDE` |  |
| wildlife / zoology (B16.M02.N04) | narrow | 2017-12-11 | fading | 3.2 | 3.2 | 1 | `WB_605_WILDLIFE_RESOURCES` |  |
| seasons / winter (B09.M07.N01) | narrow | 2017-11-06 | sustained | 3.0 | 26.2 | 20 | `NATURAL_DISASTER_ICY` | no |
| Magic, witches and fantasy creatures (B01.M02) | middle | 2017-10-30 | fading | 2.8 | 2.8 | 2 | `TAX_RELIGION_WITCHCRAFT` | no |
| information (B04.M10.N03) | narrow | 2017-11-13 | sustained | 2.7 | 2.7 | 8 | `WB_655_INFORMATION_MANAGEMENT` |  |
| holocaust / genocide (B08.M03.N01) | narrow | 2017-09-04 | sustained | 2.7 | 2.7 | 4 | `WB_2508_ETHNIC_CLEANSING` |  |
| management / consulting (B10.M02.N01) | narrow | 2017-12-18 | fading | 2.5 | 2.5 | 2 | `WB_730_MANAGEMENT_INFORMATION_SYSTEMS` |  |
| Christianity and the Bible (B03.M01) | middle | 2017-12-18 | fading | 2.4 | 2.4 | 2 | `TAX_RELIGION_CHRISTIANITY` |  |
| christianity / latter day saints (B03.M01.N01) | narrow | 2017-12-11 | sustained | 2.2 | 2.2 | 4 | `TAX_RELIGION_CHRISTIANITY` |  |

**GDELT, 2018** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| coming of age / aging (B07.M02.N01) | narrow | 2018-01-08 | sustained | 11.8 | 11.8 | 12 | `WB_1447_GERIATRICS` | yes |
| fairies / witches (B01.M02.N02) | narrow | 2018-05-07 | sustained | 6.0 | 6.0 | 6 | `TAX_RELIGION_WITCHCRAFT` | yes |
| Archaeology, geology and natural history (B09.M06) | middle | 2018-04-30 | sustained | 5.7 | 5.7 | 6 | `WB_2286_GEOLOGICAL_SURVEY` |  |
| archaeology / geology (B09.M06.N01) | narrow | 2018-04-30 | sustained | 5.7 | 5.7 | 6 | `WB_2286_GEOLOGICAL_SURVEY` |  |
| aviation (B08.M05.N03) | narrow | 2018-04-16 | fading | 4.6 | 4.6 | 1 | `AVIATION_INCIDENT` |  |
| Wild animals (B16.M02) | middle | 2018-02-12 | fading | 3.9 | 3.9 | 1 | `WB_605_WILDLIFE_RESOURCES` |  |
| Philosophy and belief (B14.M03) | middle | 2018-09-24 | fading | 3.6 | 3.6 | 1 | `TAX_RELIGION_ATHEISM` | no |
| atheism / skepticism (B14.M03.N02) | narrow | 2018-09-24 | fading | 3.6 | 3.6 | 1 | `TAX_RELIGION_ATHEISM` | no |
| Magic, witches and fantasy creatures (B01.M02) | middle | 2018-05-07 | sustained | 3.4 | 3.4 | 6 | `TAX_RELIGION_WITCHCRAFT` | yes |
| money / wealth (B10.M03.N02) | narrow | 2018-07-30 | sustained | 3.4 | 3.4 | 4 | `WB_345_SOVEREIGN_WEALTH_FUNDS` |  |

**GDELT, 2019** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aviation (B08.M05.N03) | narrow | 2019-12-30 | sustained | 14.3 | 14.3 | 6 | `AVIATION_INCIDENT` |  |
| aviation (B08.M05.N03) | narrow | 2019-02-18 | sustained | 9.1 | 9.1 | 7 | `AVIATION_INCIDENT` |  |
| great depression / financial crisis (B10.M03.N05) | narrow | 2019-08-05 | fading | 5.5 | 5.5 | 2 | `EPU_CATS_SOVEREIGN_DEBT_CURRENCY_CRISES` |  |
| hiv aids (B15.M04.N04) | narrow | 2019-03-04 | fading | 4.3 | 4.3 | 1 | `TAX_DISEASE_HIV` |  |
| holocaust / genocide (B08.M03.N01) | narrow | 2019-04-01 | fading | 4.0 | 4.0 | 2 | `WB_2509_GENOCIDE` |  |
| Race and racism (B05.M02.N02) | narrow | 2019-07-15 | sustained | 3.9 | 3.9 | 5 | `DISCRIMINATION_RACE_RACIST` |  |
| multicultural / diversity (B05.M02.N01) | narrow | 2019-10-07 | intermediate | 3.8 | 3.8 | 3 | `WB_933_ETHNIC_RELIGIOUS_AND_OTHER_MINORITIES` |  |
| autism (B07.M01.N03) | narrow | 2019-02-25 | sustained | 3.6 | 7.5 | 7 | `TAX_DISEASE_AUTISM` |  |
| jewish life / judaism (B03.M03.N01) | narrow | 2019-02-11 | fading | 3.4 | 3.4 | 2 | `REL_ANTISEMITISM` |  |
| Jewish life and history (B03.M03) | middle | 2019-02-11 | fading | 3.4 | 3.4 | 2 | `REL_ANTISEMITISM` |  |

**GDELT, 2020** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Epidemics and plagues (B15.M04.N05) | narrow | 2020-01-20 | sustained | 14.1 | 27.2 | 17 | `WB_2167_PANDEMICS` |  |
| Race and racism (B05.M02.N02) | narrow | 2020-05-25 | sustained | 14.0 | 14.0 | 12 | `DISCRIMINATION_RACE_RACISM` |  |
| Race, racism and diversity (B05.M02) | middle | 2020-05-25 | sustained | 11.1 | 11.1 | 10 | `DISCRIMINATION_RACE_RACISM` |  |
| police / forensic science (B19.M01.N02) | narrow | 2020-05-25 | sustained | 6.0 | 6.0 | 10 | `WB_2082_LAW_ENFORCEMENT` |  |
| theology / church (B03.M01.N02) | narrow | 2020-09-21 | sustained | 5.1 | 5.1 | 7 | `TAX_RELIGION_CATHOLICISM` |  |
| islamic theology / islam (B03.M02.N02) | narrow | 2020-10-19 | sustained | 4.3 | 4.3 | 4 | `DISCRIMINATION_RELIGION_ISLAMOPHOBIA` |  |
| political philosophy / activism (B13.M01.N02) | narrow | 2020-05-25 | sustained | 4.2 | 4.2 | 6 | `PROTEST` |  |
| Islam, Buddhism, Hinduism and other religions (B03.M02) | middle | 2020-10-19 | intermediate | 4.1 | 4.1 | 3 | `TAX_RELIGION_ISLAM` |  |
| aviation (B08.M05.N03) | narrow | 2020-05-18 | fading | 3.5 | 3.5 | 1 | `MANMADE_DISASTER_PLANE_CRASH` |  |
| social justice / justice (B13.M03.N01) | narrow | 2020-05-25 | sustained | 3.5 | 3.5 | 5 | `JUSTICE` |  |

**GDELT, 2021** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver code | Feed artefact (URL sample) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aviation (B08.M05.N03) | narrow | 2021-01-04 | fading | 3.1 | 3.1 | 2 | `AVIATION_INCIDENT` |  |
| feminism / gender (B02.M02.N01) | narrow | 2021-03-01 | fading | 2.8 | 2.8 | 2 | `WB_615_GENDER` |  |
| Feminism and gender (B02.M02) | middle | 2021-03-01 | fading | 2.8 | 2.8 | 2 | `WB_615_GENDER` |  |
| Race and racism (B05.M02.N02) | narrow | 2021-03-08 | sustained | 2.8 | 2.8 | 4 | `DISCRIMINATION_RACE_RACISM` |  |
| Childhood, parenting and adoption (B07.M01) | middle | 2021-03-29 | fading | 2.8 | 2.8 | 1 | `TAX_DISEASE_AUTISM` |  |
| fairies / witches (B01.M02.N02) | narrow | 2021-03-01 | fading | 2.7 | 2.7 | 2 | `TAX_RELIGION_WITCHCRAFT` | no |
| jewish life / judaism (B03.M03.N01) | narrow | 2021-05-17 | sustained | 2.6 | 2.6 | 5 | `REL_ANTISEMITISM` |  |
| Jewish life and history (B03.M03) | middle | 2021-05-17 | sustained | 2.6 | 2.6 | 5 | `REL_ANTISEMITISM` |  |
| bullying (B07.M02.N03) | narrow | 2021-03-01 | fading | 2.6 | 2.6 | 1 | `BULLYING` | no |
| Race, racism and diversity (B05.M02) | middle | 2021-03-08 | sustained | 2.5 | 2.5 | 4 | `DISCRIMINATION_RACE_RACISM` |  |

**Wikipedia, 2016** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Artificial intelligence and robots (B04.M08) | middle | 2016-04-04 | fading | 7.6 | 7.6 | 1 | Virtual reality | one_day, desktop_only |
| mountaineering / mountains (B09.M01.N04) | narrow | 2016-03-28 | fading | 6.6 | 6.6 | 2 | Mountain | desktop_only |
| fitness / exercise (B17.M03.N01) | narrow | 2016-06-13 | sustained | 5.1 | 5.1 | 4 | Physical fitness |  |
| marriage / arranged marriage (B02.M03.N01) | narrow | 2016-07-25 | intermediate | 4.4 | 4.4 | 3 | Dating | desktop_only |
| Government and political ideas (B13.M01) | middle | 2016-11-07 | fading | 4.3 | 4.3 | 2 | President of the United States |  |
| Marriage, dating and infidelity (B02.M03) | middle | 2016-07-25 | intermediate | 3.5 | 3.5 | 3 | Dating | desktop_only |
| wolves / bears (B16.M02.N01) | narrow | 2016-04-18 | fading | 3.2 | 3.2 | 1 | Rabbit | one_day |
| nazis / fascism (B08.M03.N02) | narrow | 2016-11-07 | sustained | 3.1 | 3.1 | 5 | Fascism |  |
| corruption (B19.M01.N05) | narrow | 2016-10-31 | fading | 2.6 | 2.6 | 1 | Corruption |  |
| Travel, exploration and mountains (B09.M01) | middle | 2016-03-28 | fading | 2.5 | 2.5 | 2 | Mountain | desktop_only |

**Wikipedia, 2017** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| film / acting (B06.M04.N01) | narrow | 2017-07-24 | fading | 13.6 | 13.6 | 2 | Film | desktop_only |
| nazis / fascism (B08.M03.N02) | narrow | 2017-08-14 | intermediate | 5.9 | 5.9 | 3 | Fascism |  |
| Film, television and stage (B06.M04) | middle | 2017-07-24 | fading | 5.5 | 5.5 | 2 | Film | desktop_only |
| exploration / polar exploration (B09.M01.N02) | narrow | 2017-07-17 | fading | 5.4 | 5.4 | 1 | Polar exploration |  |
| self harm (B12.M04.N03) | narrow | 2017-07-31 | sustained | 4.7 | 4.7 | 7 | Self-harm |  |
| asian american (B05.M04.N03) | narrow | 2017-11-20 | fading | 4.4 | 4.4 | 1 | Asian Americans | desktop_only |
| ghosts / haunted houses (B01.M04.N01) | narrow | 2017-01-30 | fading | 3.8 | 3.8 | 1 | Haunted house | one_day |
| murder / serial killers (B12.M02.N01) | narrow | 2017-05-15 | fading | 3.6 | 3.6 | 1 | Serial killer | one_day |
| vietnam war / peace (B08.M01.N03) | narrow | 2017-05-01 | fading | 3.6 | 3.6 | 1 | Vietnam War | one_day |
| mathematics (B04.M03.N01) | narrow | 2017-07-31 | fading | 3.4 | 3.4 | 1 | Mathematics | one_day, desktop_only |

**Wikipedia, 2018** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| computers / computer science (B04.M02.N01) | narrow | 2018-11-12 | sustained | 7.0 | 7.0 | 5 | Computer science | desktop_only |
| political philosophy / activism (B13.M01.N02) | narrow | 2018-10-22 | sustained | 5.8 | 5.8 | 4 | Nationalism |  |
| gardening / botany (B09.M04.N01) | narrow | 2018-10-15 | fading | 4.8 | 4.8 | 1 | Botany | one_day, desktop_only |
| hockey / figure skating (B17.M02.N03) | narrow | 2018-01-15 | sustained | 3.9 | 7.3 | 7 | Figure skating |  |
| world war ii / world war i (B08.M01.N01) | narrow | 2018-11-05 | fading | 3.5 | 3.5 | 2 | World War I |  |
| Computers, software and the internet (B04.M02) | middle | 2018-11-26 | fading | 3.3 | 3.3 | 2 | Computer science | desktop_only |
| robin hood (B08.M04.N05) | narrow | 2018-11-05 | sustained | 3.2 | 3.2 | 5 | Robin Hood | title_confusion |
| marriage / arranged marriage (B02.M03.N01) | narrow | 2018-01-22 | intermediate | 2.4 | 2.4 | 3 | Dating | desktop_only |
| outdoor recreation / outdoors (B09.M03.N03) | narrow | 2018-11-19 | intermediate | 2.4 | 2.4 | 3 | Outdoor recreation |  |
| fitness / exercise (B17.M03.N01) | narrow | 2018-06-25 | fading | 2.4 | 2.4 | 2 | Physical fitness |  |

**Wikipedia, 2019** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| productivity (B10.M04.N02) | narrow | 2019-02-04 | intermediate | 31.4 | 31.4 | 3 | Productivity | one_day, desktop_only |
| seasons / winter (B09.M07.N01) | narrow | 2019-12-16 | fading | 10.6 | 10.6 | 2 | Winter | one_day |
| men / masculinity (B02.M02.N02) | narrow | 2019-11-04 | intermediate | 8.0 | 8.0 | 3 | Man |  |
| elephants (B16.M02.N06) | narrow | 2019-09-16 | fading | 3.9 | 3.9 | 1 | Elephant | one_day |
| Christianity and the Bible (B03.M01) | middle | 2019-03-11 | sustained | 3.8 | 8.1 | 10 | Bible | desktop_only |
| Entrepreneurship and productivity (B10.M04) | middle | 2019-02-04 | fading | 3.5 | 3.5 | 1 | Productivity | desktop_only |
| prison / criminology (B19.M01.N03) | narrow | 2019-04-29 | fading | 3.3 | 3.3 | 2 | Prison | desktop_only |
| journaling (B06.M02.N02) | narrow | 2019-10-07 | fading | 3.2 | 3.2 | 1 | Diary | one_day |
| writing / writers (B06.M02.N01) | narrow | 2019-11-11 | fading | 2.8 | 2.8 | 1 | Writing |  |
| murder / serial killers (B12.M02.N01) | narrow | 2019-01-21 | sustained | 2.7 | 2.7 | 4 | Serial killer |  |

**Wikipedia, 2020** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| running (B17.M03.N04) | narrow | 2020-05-04 | sustained | 10.2 | 10.2 | 4 | Running |  |
| Visual arts, design and crafts (B06.M01) | middle | 2020-04-27 | fading | 9.9 | 9.9 | 1 | Art | one_day |
| Epidemics and plagues (B15.M04.N05) | narrow | 2020-01-27 | sustained | 7.7 | 56.9 | 14 | Pandemic |  |
| happiness / positive psychology (B14.M01.N02) | narrow | 2020-02-24 | fading | 5.5 | 5.5 | 1 | Happiness | one_day, desktop_only |
| circus (B06.M06.N04) | narrow | 2020-10-26 | fading | 5.4 | 5.4 | 1 | Circus | one_day |
| great depression / financial crisis (B10.M03.N05) | narrow | 2020-03-09 | sustained | 5.3 | 5.3 | 11 | Great Depression |  |
| nazis / fascism (B08.M03.N02) | narrow | 2020-05-25 | sustained | 5.3 | 5.3 | 10 | Fascism | one_day |
| Race and racism (B05.M02.N02) | narrow | 2020-05-25 | sustained | 5.3 | 5.3 | 8 | Racism |  |
| civil war / american civil war (B08.M02.N01) | narrow | 2020-05-25 | sustained | 4.6 | 4.6 | 7 | American Civil War |  |
| Race, racism and diversity (B05.M02) | middle | 2020-05-25 | sustained | 4.5 | 4.5 | 7 | Racism |  |

**Wikipedia, 2021** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internet (B04.M02.N03) | narrow | 2021-08-02 | sustained | 6.6 | 7.7 | 11 | Internet | desktop_only |
| jewish life / judaism (B03.M03.N01) | narrow | 2021-05-10 | intermediate | 4.2 | 4.2 | 3 | Jews |  |
| Jewish life and history (B03.M03) | middle | 2021-05-10 | intermediate | 4.2 | 4.2 | 3 | Jews |  |
| holocaust / genocide (B08.M03.N01) | narrow | 2021-04-19 | fading | 4.1 | 4.1 | 2 | The Holocaust |  |
| space / mars (B18.M01.N02) | narrow | 2021-02-15 | intermediate | 3.1 | 3.1 | 3 | Mars |  |
| seasons / winter (B09.M07.N01) | narrow | 2021-09-20 | intermediate | 2.9 | 2.9 | 3 | Winter | desktop_only |
| communication (B13.M04.N02) | narrow | 2021-09-06 | intermediate | 2.8 | 2.8 | 3 | Communication |  |
| asian american (B05.M04.N03) | narrow | 2021-01-18 | fading | 2.8 | 2.8 | 1 | Asian Americans |  |
| Computers, software and the internet (B04.M02) | middle | 2021-08-02 | sustained | 2.7 | 3.2 | 11 | Internet | desktop_only |
| happiness / positive psychology (B14.M01.N02) | narrow | 2021-09-20 | fading | 2.7 | 2.7 | 1 | Happiness | one_day, desktop_only |

**Wikipedia, 2022** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hockey / figure skating (B17.M02.N03) | narrow | 2022-01-31 | sustained | 6.5 | 6.5 | 4 | Figure skating |  |
| cold war / russian revolution (B13.M02.N02) | narrow | 2022-02-21 | sustained | 5.5 | 5.5 | 5 | Cold War |  |
| monarchy (B08.M04.N02) | narrow | 2022-09-05 | intermediate | 5.4 | 5.4 | 3 | Monarchy |  |
| Jewish life and history (B03.M03) | middle | 2022-10-24 | intermediate | 3.7 | 3.7 | 3 | Antisemitism |  |
| jewish life / judaism (B03.M03.N01) | narrow | 2022-10-24 | intermediate | 3.7 | 3.7 | 3 | Antisemitism |  |
| happiness / positive psychology (B14.M01.N02) | narrow | 2022-09-12 | fading | 3.5 | 3.5 | 1 | Happiness | desktop_only |
| pets / dogs (B16.M01.N01) | narrow | 2022-05-02 | fading | 3.4 | 3.4 | 2 | Pet |  |
| Pets and farm animals (B16.M01) | middle | 2022-05-02 | fading | 3.2 | 3.2 | 2 | Pet |  |
| world war ii / world war i (B08.M01.N01) | narrow | 2022-02-21 | sustained | 3.2 | 3.2 | 4 | World War II |  |
| football / soccer (B17.M02.N01) | narrow | 2022-11-28 | sustained | 3.2 | 3.2 | 4 | Association football |  |

**Wikipedia, 2023** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orphans / adoption (B07.M01.N02) | narrow | 2023-11-20 | fading | 10.0 | 10.0 | 1 | Orphan | one_day, desktop_only |
| jewish life / judaism (B03.M03.N01) | narrow | 2023-10-02 | sustained | 7.3 | 7.3 | 11 | Jews |  |
| Jewish life and history (B03.M03) | middle | 2023-10-02 | sustained | 7.3 | 7.3 | 11 | Jews |  |
| cybersecurity / intelligence agencies (B19.M02.N01) | narrow | 2023-10-09 | fading | 4.7 | 4.7 | 1 | Computer security | one_day |
| fear (B12.M04.N02) | narrow | 2023-10-16 | fading | 4.6 | 4.6 | 1 | Fear | desktop_only |
| aliens / ufos (B18.M01.N01) | narrow | 2023-02-06 | fading | 3.6 | 3.6 | 2 | Unidentified flying object |  |
| space / mars (B18.M01.N02) | narrow | 2023-11-27 | fading | 3.5 | 3.5 | 1 | Mars | one_day, desktop_only |
| celebrity / popular culture (B06.M05.N01) | narrow | 2023-09-11 | sustained | 3.1 | 3.1 | 4 | Popular culture |  |
| Celebrity and popular culture (B06.M05) | middle | 2023-09-11 | intermediate | 2.7 | 2.7 | 3 | Popular culture |  |
| Spies, hackers and conspiracies (B19.M02) | middle | 2023-10-09 | fading | 2.6 | 2.6 | 1 | Computer security | one_day |

**Wikipedia, 2024** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropology (B05.M03.N01) | narrow | 2024-12-23 | fading | 450.9 | 450.9 | 1 | Anthropology | one_day |
| nazis / fascism (B08.M03.N02) | narrow | 2024-10-21 | sustained | 8.1 | 8.1 | 4 | Fascism |  |
| Government and political ideas (B13.M01) | middle | 2024-11-04 | fading | 4.5 | 4.5 | 2 | President of the United States |  |
| The Holocaust, Nazism and genocide (B08.M03) | middle | 2024-10-14 | sustained | 4.1 | 4.1 | 5 | Fascism |  |
| media / social media (B13.M04.N01) | narrow | 2024-03-04 | sustained | 3.4 | 3.4 | 6 | Social media |  |
| amish (B05.M03.N03) | narrow | 2024-11-04 | fading | 3.4 | 3.4 | 1 | Amish | title_confusion |
| presidents / jfk assassination (B13.M01.N01) | narrow | 2024-07-08 | intermediate | 3.3 | 3.3 | 3 | Assassination of John F. Kennedy | one_day |
| birds / insects (B16.M02.N02) | narrow | 2024-10-28 | fading | 3.3 | 3.3 | 1 | Penguin | title_confusion |
| mathematics (B04.M03.N01) | narrow | 2024-07-08 | fading | 3.1 | 3.1 | 1 | Mathematics | one_day |
| disability / disability sports (B15.M05.N01) | narrow | 2024-08-26 | fading | 2.6 | 2.6 | 2 | Parasports |  |

**Wikipedia, 2025** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adolescence / runaways (B07.M02.N05) | narrow | 2025-03-10 | sustained | 13.5 | 13.5 | 8 | Adolescence | title_confusion |
| presidents / jfk assassination (B13.M01.N01) | narrow | 2025-01-20 | fading | 6.9 | 6.9 | 2 | President of the United States |  |
| Government and political ideas (B13.M01) | middle | 2025-01-20 | fading | 3.8 | 3.8 | 1 | President of the United States |  |
| theology / church (B03.M01.N02) | narrow | 2025-04-28 | intermediate | 3.8 | 3.8 | 3 | Catholic Church |  |
| School, adolescence and coming of age (B07.M02) | middle | 2025-03-10 | sustained | 3.6 | 3.6 | 4 | Adolescence | title_confusion |
| farm animals / animal rights (B16.M01.N02) | narrow | 2025-09-29 | fading | 3.4 | 3.4 | 2 | Ethology |  |
| nazis / fascism (B08.M03.N02) | narrow | 2025-09-15 | intermediate | 3.4 | 3.4 | 3 | Fascism |  |
| vampires / superheroes (B01.M01.N01) | narrow | 2025-03-24 | fading | 3.4 | 3.4 | 1 | Superhero |  |
| aviation (B08.M05.N03) | narrow | 2025-12-01 | sustained | 3.3 | 3.3 | 5 | Aviation | desktop_only |
| greek mythology / classical studies (B01.M03.N02) | narrow | 2025-12-22 | fading | 3.2 | 3.2 | 1 | Trojan War |  |

**Wikipedia, 2026** (non-seasonal shifts at narrow and middle levels, by size)

| Node | Level | Start | Label | Size | Whole-course peak | Weeks >= 1.5 | Driver page | quality_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| photography (B06.M01.N03) | narrow | 2026-08-24 | sustained | 11.9 | 14.0 | 5 | Photography |  |
| running (B17.M03.N04) | narrow | 2026-08-24 | sustained | 8.8 | 10.3 | 5 | Running | desktop_only |
| Myths and legends (B01.M03) | middle | 2026-07-20 | sustained | 7.8 | 7.8 | 6 | Trojan War |  |
| communication (B13.M04.N02) | narrow | 2026-04-27 | sustained | 5.8 | 5.8 | 4 | Communication |  |
| photography (B06.M01.N03) | narrow | 2026-06-01 | sustained | 5.3 | 5.3 | 4 | Photography | desktop_only |
| suicide / death and dying (B12.M03.N02) | narrow | 2026-04-27 | fading | 5.3 | 5.3 | 1 | Suicide | one_day |
| information (B04.M10.N03) | narrow | 2026-04-27 | sustained | 5.1 | 5.1 | 4 | Information |  |
| beauty / aesthetics (B06.M06.N02) | narrow | 2026-02-02 | fading | 3.9 | 3.9 | 1 | Aesthetics | one_day |
| running (B17.M03.N04) | narrow | 2026-06-08 | fading | 3.6 | 3.6 | 2 | Running | desktop_only |
| road trips / hiking (B09.M01.N03) | narrow | 2026-08-24 | sustained | 3.5 | 3.5 | 5 | Hiking | desktop_only |

## 9. Shifts found in both sources

| Shift set | Shifts in | Also in | Tolerance (weeks) | Shifts | Matched | Share |
| --- | --- | --- | --- | --- | --- | --- |
| main set | Wikipedia | GDELT | +/-2 | 177 | 31 | 0.17 |
| main set | GDELT | Wikipedia | +/-2 | 370 | 31 | 0.08 |
| main set | Wikipedia (large only) | GDELT | +/-2 | 21 | 7 | 0.33 |
| main set | GDELT (large only) | Wikipedia | +/-2 | 39 | 7 | 0.18 |
| main set | Wikipedia | GDELT | +/-4 | 177 | 43 | 0.24 |
| main set | GDELT | Wikipedia | +/-4 | 370 | 43 | 0.12 |
| main set | Wikipedia (large only) | GDELT | +/-4 | 21 | 8 | 0.38 |
| main set | GDELT (large only) | Wikipedia | +/-4 | 39 | 9 | 0.23 |
| main set, quality_ok | Wikipedia | GDELT | +/-2 | 143 | 31 | 0.22 |
| main set, quality_ok | GDELT | Wikipedia | +/-2 | 370 | 31 | 0.08 |
| main set, quality_ok | Wikipedia (large only) | GDELT | +/-2 | 13 | 7 | 0.54 |
| main set, quality_ok | GDELT (large only) | Wikipedia | +/-2 | 39 | 7 | 0.18 |
| main set, quality_ok | Wikipedia | GDELT | +/-4 | 143 | 43 | 0.30 |
| main set, quality_ok | GDELT | Wikipedia | +/-4 | 370 | 43 | 0.12 |
| main set, quality_ok | Wikipedia (large only) | GDELT | +/-4 | 13 | 8 | 0.61 |
| main set, quality_ok | GDELT (large only) | Wikipedia | +/-4 | 39 | 9 | 0.23 |

The comparison uses main-set shifts that start between July 2017 and June 2021 at nodes usable in both sources (180 nodes). A match is a shift in the same node in the other source whose start is within two (or four) weeks. Wikipedia has fewer shifts than GDELT in these years, so the shares are not symmetric. Leaving out flagged Wikipedia shifts raises the matched share, which suggests the flags remove mostly spurious rises. The sources agree for the large public events (COVID-19, George Floyd) and mostly disagree on small rises.

## 10. GDELT durations (proposed addendum to the fixed record)

The record says the Wikipedia duration thresholds are scaled for GDELT by the ratio of median shift durations, computed from interest data only, rounded, with a minimum of 2 weeks. Recomputed on 13 October 2026 on the final shifts (main set and quality_ok), with no demand data read (`gdelt_duration_scaling.json`):

| Shifts used | GDELT n | GDELT median (mean) | Wikipedia n | Wikipedia median (mean) | Ratio of medians | Ratio of means |
|---|---|---|---|---|---|---|
| Final (proposed): main set and quality_ok, both sources July 2017 to June 2021 | 371 | 1 (2.23) | 308 | 1 (2.12) | 1.00 | 1.05 |
| Final, Wikipedia all years (GDELT as above) | 371 | 1 (2.23) | 687 | 1 (1.95) | 1.00 | 1.14 |
| Earlier definition: all completed non-seasonal shifts at tested levels, July 2017 to June 2021 | 372 | 1 (2.23) | 383 | 1 (2.13) | 1.00 | 1.05 |

Ratio of medians (GDELT / Wikipedia, same years) = 1.0. Scaled GDELT thresholds: sustained >= 4 weeks (labelled in week 4), intermediate = 3 weeks, fading <= 2 weeks, the same as Wikipedia. Suggested entry for `prereg/DEVIATIONS.md`:

> 2026-10-13 | GDELT duration thresholds computed as the record requires, on the final shifts (main set, quality_ok, narrow and middle levels, July 2017 to June 2021): median shift duration 1 week in GDELT (n = 371) and 1 week in Wikipedia (n = 308), ratio 1.0 (ratio of means 1.05). Scaled thresholds: sustained >= 4 weeks (labelled in week 4), intermediate 3, fading <= 2, identical to Wikipedia. | Required by the record | No demand data seen

Durations are whole weeks and most shifts last one week, so the median is a coarse measure; it cannot show a difference smaller than a week.

## 11. Problems found

1. **Word-form matches in the embedding.** The sentence model often matches by word form rather than meaning ("pandemic" near weather, "waterboarding" near surfing). Every high-volume code was checked; small codes in nodes that were not checked may still be wrong, but their volume is small.
2. **Very general GDELT flags.** They fire on one common word in a large share of news and were dropped; this removes 39% of the mentions that the threshold had mapped.
3. **Taxonomy values that are too general for news.** "water" (with swimming), "food" and "cooking" (home cooking) and "leadership" (self-help) attract large news codes with a different meaning; they were handled code by code. "violence" now has its own node (v3).
4. **Figurative and other senses in GDELT.** One driver code is figurative (amnesia) and was dropped. Translated news also brings other senses of a word (Italian "occultare", to hide, in `TAX_RELIGION_OCCULT`; Italian "tormenta", torments, in two tiny off-season blizzard weeks); these were small and the codes stay.
5. **Single-website feed artefacts in GDELT.** See section 3.6 and question 1 in section 13.
6. **Automated traffic and title confusion in Wikipedia.** Handled by `quality_flag` (section 5). Some automated spikes are not caught by the two automatic flags (Information and Communication on 30 April 2026).
7. **Sudden shocks start late; short spikes are not shifts** (section 2, intended).
8. **GDELT history is short.** GDELT labels start in July 2017 (the first 26 weeks are the first normal level); #MeToo is just inside the labelled period. GDELT from July 2021 arrives after 2 November 2026; rerunning `run_all.sh` then extends every GDELT series, and new driver codes will need figurative verdicts (`10_gdelt_drivers.py` lists them).
9. **Lockdown traffic** lowers Wikipedia shares in April 2020.
10. **The v3 value table on disk still lists "violence" under the sexual and domestic violence node** (`data/db/taxonomy_v3/theme_value_node.parquet`, written 19:44), although the node table has B12.M01.N04 and addendum f records the move. The interest code applies the move itself (`_ci.V3_MOVES`); the v3 build may want to update its value table.
11. **File sync.** A duplicate cache file ("_entity_cache 2.json") appeared earlier, probably from cloud sync; `data/` has since been moved to `data.nosync/`, which should stop this.

## 12. Decisions, and why

Decisions taken on 13 October on the first version's open questions (interest data only):

| # | Decision | Applied |
|---|---|---|
| 1 | Start rule: the armed reading (addendum d); keep `strict_start` as the robustness column | yes |
| 2 | #MeToo: keep the category's pages; report the Wikipedia rise as short and that readers went to "Sexual harassment" | yes (sections 4.1, 7) |
| 3 | Climate: leave the GDELT node as it is; value series descriptive | yes (section 7) |
| 4 | `quality_flag` / `quality_ok` in `shifts.parquet`; step 09 flags as they are; hand check for title confusion | yes (section 5) |
| 5 | Drop the very general flags; drop driver codes whose rises are figurative | yes (sections 3.4, 3.6) |
| 6 | Spikes shorter than three weeks: intended, reported as a limitation | yes (section 2) |
| 7 | Shared pages acceptable; listed | yes (section 4.1) |
| 8 | Interest side stays on the v2 values; apply only the move of "violence" to B12.M01.N04 and recheck its GDELT codes | yes (sections 3.4, 4.1) |

My implementation choices within these decisions:

| Choice | Why |
|---|---|
| Title confusion judged on the page carrying the rise and same-named pages in the daily top-500 list around the peak day | Objective, checkable evidence for each verdict; covers series, films, games, songs and people |
| A company with the page's name (Robinhood, January 2021) counted as title confusion | Same mechanism as a series or person: readers who wanted something else |
| Adaptation-driven rises (a series about serial killers, a film about the Odyssey) not counted | The page title differs; readers were looking for the theme |
| Figurative check by URL samples for words with common figurative use, by meaning and top weeks for the rest | The weekly counts cannot show how a word was used; URLs carry the headline; cost kept to 50 GB of free quota |
| Feed artefacts recorded in a separate column, not in `quality_ok` | The decision covered figurative use only; dropping or flagging these shifts is left to you |
| `UNGP_CRIME_VIOLENCE` and `WB_741_URBAN_CRIME_AND_VIOLENCE` moved to the new violence node | The new node's label names them; the recheck was limited to the moved value |
| GDELT duration scaling on the final shifts (main set and quality_ok); other definitions reported alongside | "Final shifts" is the tested set; all definitions give 1.0 |

Earlier choices (unchanged): one value per GDELT code at cosine >= 0.70 then hand verdicts; family rules for actors and entities; natural disasters to disasters; HARASSMENT on sexual violence; one concept page per Wikipedia value with related pages only where the gloss names them; the redirect screen; usable series at 80% usable weeks; agreement window +/-2 weeks (also +/-4).

## 13. Open questions

1. **GDELT feed artefacts.** 11 GDELT main-set shifts are driven by codes whose URL sample on the start week is mostly one website (table in section 3.6), including the largest GDELT shift of the coming of age / aging node (11.8 times normal, January 2018) and the fairies / witches shift of May 2018 (6.0 times). Options: add 'feed_artifact' to `quality_flag` for these shifts (they would leave the tested set like the Wikipedia flags); drop the three codes whose shift weeks are mostly from one site (`WB_1447_GERIATRICS`, `WB_1532_TEACHER_TRAINING`, `TAX_DISEASE_DEAFNESS`; witchcraft would stay, since only its May 2018 rise is from one site); or leave them as recorded. Only the 20 sampled codes were checked; sampling the drivers of all 371 GDELT main-set shifts would cost about 150 GB of BigQuery quota, more than this month has left.
2. **Unflagged automated spikes in Wikipedia.** Information and Communication on 30 April 2026 have identical daily views, which looks automated, but neither automatic flag catches it. Leave as is (flags not tuned), or flag by hand?

## 14. Files, rerunning and run times

Code: `code/main_study/interest/` (`run_all.sh` runs 01 to 12 in order; `SKIP_API=1` rebuilds from cached API answers only; `_gdelt_url_samples.py` is a one-off helper that uses BigQuery and is not in `run_all.sh`). Data: `data/db/interest/` (GDELT under `gdelt/`, Wikipedia under `wiki/`). Logs: `data/reports/interest_wiki_cand.log`, `interest_wiki_pv.log`, `interest_spike.log`, `interest_run_all_final.log`. Review sheets: `data/db/interest/gdelt/review_gdelt_mappings.csv` (GDELT, with the figurative verdicts), `data/db/interest/gdelt/driver_evidence.csv` (evidence for the figurative check), `data/db/interest/wiki/articles_review.csv` (Wikipedia pages, all 614 values) and `data/db/interest/wiki/review_title_confusion.csv` (title confusion, 155 shifts).

| Step | Wall time on this Mac |
|---|---|
| 04 Wikidata candidates (879 searches, 6,081 entities) | 23 min |
| 06 page views (624 pages, 18,703 titles screened, 1,924 monthly, 291 redirect daily) | 73 min |
| 09 quality check (866 desktop requests) | 15 min |
| URL samples for the figurative check (89 code-days, 50 GB scanned) | 4 min |
| Whole pipeline from cached API answers (`SKIP_API=1 ./run_all.sh`) | 73 s |
