# Test F: AI matchmaking of Wikipedia pages and books into the same themes, results

Written 2026-10-21 20:31 from the outputs of code/main_study/wiki_led/testF/ (steps 20 to 27). Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (fixed 21 Oct 2026, 01:55, before any sorting).

## 1. The sorting

- Pages: 87,577 in the key; with at least one theme 84,818 (96.8%), none 2,759, still invalid after the re-ask (dropped) 0, waiting for the re-ask 0, not sorted yet 0. Theme pairs 168,587 (confidence 3, 2, 1: 60,752, 56,948, 50,887).
- Books: 20,000 in the key; with at least one theme 19,968 (99.8%), none 32, still invalid after the re-ask (dropped) 0, waiting for the re-ask 0, not sorted yet 0. Theme pairs 55,619 (confidence 3, 2, 1: 20,162, 25,741, 9,716).
- Coverage check (pages sorted, share given a theme): universe 96.9%, one-day sample 96.3%. The one-day sample is never used in G2 to G4.

## 2. Two independent sorting passes

- Pages (1,000 in both passes): same first theme 91.1% (same middle theme 92.7%), at least one shared theme 100.0%, agreement on none or some 99.2% (kappa 0.85); both none 24, only the first none 6, only the second none 2.
- Books (500 in both passes): same first theme 87.2% (same middle theme 88.6%), at least one shared theme 100.0%, agreement on none or some 100.0% (kappa 1.00); both none 1, only the first none 0, only the second none 0.

## 3. Check G1: agreement with an independent judge

- 400 judged pages scored (0 example pages left out); every method could route 400 of them; the judge gave no theme to 0 and marked 114 titles as misleading.
- Precision is the share of a method's page-theme pairs the judge also gives; recall the share of the judge's pairs the method gives; the last column is the share of misleading-title pages the method sends to a theme the judge does not give (lower is better).

| method | level | pages | method_pairs | judge_pairs | precision | recall | misleading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AI sorter (all pairs) | narrow | 400 | 828 | 863 | 0.849 [0.826, 0.871] | 0.815 [0.792, 0.837] | 0.368 [0.284, 0.458] |
| AI sorter (all pairs) | middle | 400 | 759 | 777 | 0.867 [0.844, 0.889] | 0.847 [0.824, 0.870] | 0.316 [0.236, 0.398] |
| AI sorter (confidence 2 or 3) | narrow | 400 | 588 | 863 | 0.951 [0.934, 0.966] | 0.648 [0.622, 0.673] | 0.105 [0.053, 0.163] |
| AI sorter (confidence 2 or 3) | middle | 400 | 552 | 777 | 0.958 [0.941, 0.973] | 0.681 [0.653, 0.709] | 0.096 [0.047, 0.151] |
| zero-shot routing (p >= 0.50) | narrow | 400 | 145 | 863 | 0.717 [0.643, 0.789] | 0.121 [0.096, 0.145] | 0.123 [0.065, 0.184] |
| zero-shot routing (p >= 0.50) | middle | 400 | 142 | 777 | 0.768 [0.693, 0.841] | 0.140 [0.113, 0.167] | 0.114 [0.059, 0.174] |
| embedding routing (cos >= 0.70) | narrow | 400 | 45 | 863 | 0.711 [0.574, 0.837] | 0.037 [0.025, 0.050] | 0.105 [0.052, 0.165] |
| embedding routing (cos >= 0.70) | middle | 400 | 48 | 777 | 0.708 [0.577, 0.829] | 0.044 [0.030, 0.059] | 0.114 [0.060, 0.173] |

Scores by part of the judged set (hard cases, random part, sources of hard cases) are in g1_scores.csv and data/reports/testF_26_G1.md.

## 4. The theme attention series

- S1 (views on top-500 days, all confidences): 81,928 pages, 163,089 page-theme pairs; 11 days without a top-500 list make 39 weeks partial (with the weeks before 2016).
- S2 (full daily views, confidence 2 or 3): 78,620 pages with such a theme, 40,000 selected (cap of 40,000 applied: yes); stored 40,000, missing 0; built: yes (complete).

## 5. Check G2: borrowing after rises of the AI theme series (S2)

- Rises found: 2,944, of which labelled 2,933 (by class {'fading': 2165, 'intermediate': 254, 'sustained': 514}); quality flags {'clean': 2819, 'one_day': 76, 'desktop_only': 41, 'one_day,desktop_only': 8}. Desktop flag applied (2,944 rises checked, 0 without desktop data, 49 flagged); donor screen new+gdelt; bootstrap 2000 resamples.
- Effect = mean difference in the log share of borrowing in months 0 to 2 (the month of the rise and the two after), against the theme's own trend (event study) and against a synthetic control of other themes; pooled over rises and formats with intervals from a bootstrap clustered by theme. A log effect of 0.088 is about 9.2% more borrowing.

**Decision (fixed): panel a, rises of 4 weeks or more, interval above 0.**

- narrow level, synthetic control: 0.015 [-0.005, 0.036] (+1.5%), 570 tests in 127 themes; interval above 0: no.
- narrow level, own trend: -0.006 [-0.032, 0.018] (-0.6%), 570 tests in 127 themes; interval above 0: no.
- middle level, synthetic control: 0.026 [-0.009, 0.066] (+2.6%), 223 tests in 50 themes; interval above 0: no.
- middle level, own trend: 0.009 [-0.035, 0.052] (+0.9%), 223 tests in 50 themes; interval above 0: no.
- both levels pooled, synthetic control: 0.018 [0.001, 0.035] (+1.8%), 793 tests in 177 themes; interval above 0: yes.
- both levels pooled, own trend: -0.002 [-0.025, 0.019] (-0.2%), 793 tests in 177 themes; interval above 0: no.

Pooled effects (all formats; sc = synthetic control, es = own trend; Chapter 6 = the stored result of the hand-checked concept pages):

| panel | level | rises | tests | categories | synthetic control | own trend |
| --- | --- | --- | --- | --- | --- | --- |
| a | both levels | 4 weeks or more | 793 | 177 | 0.018 [0.001, 0.035] | -0.002 [-0.025, 0.019] |
| b | both levels | 4 weeks or more | 640 | 161 | 0.037 [0.017, 0.061] | 0.038 [0.011, 0.067] |
| c | both levels | 4 weeks or more | 432 | 122 | 0.027 [0.002, 0.053] | 0.011 [-0.021, 0.047] |
| a | middle | 4 weeks or more | 223 | 50 | 0.026 [-0.009, 0.066] | 0.009 [-0.035, 0.052] |
| b | middle | 4 weeks or more | 188 | 48 | 0.059 [0.023, 0.100] | 0.076 [0.029, 0.130] |
| c | middle | 4 weeks or more | 153 | 40 | 0.034 [-0.014, 0.088] | 0.013 [-0.046, 0.072] |
| chapter6_concept_pages | middle | 4 weeks or more | 56 | 13 | 0.105 [0.018, 0.227] | 0.115 [0.053, 0.193] |
| a | narrow | 4 weeks or more | 570 | 127 | 0.015 [-0.005, 0.036] | -0.006 [-0.032, 0.018] |
| b | narrow | 4 weeks or more | 452 | 113 | 0.028 [0.003, 0.056] | 0.021 [-0.013, 0.056] |
| c | narrow | 4 weeks or more | 279 | 82 | 0.023 [-0.006, 0.055] | 0.010 [-0.032, 0.054] |
| chapter6_concept_pages | narrow | 4 weeks or more | 121 | 37 | 0.088 [0.029, 0.156] | 0.078 [0.021, 0.142] |
| a | both levels | 1 or 2 weeks | 3813 | 278 | 0.004 [-0.003, 0.010] | -0.009 [-0.018, -0.001] |
| b | both levels | 1 or 2 weeks | 2955 | 260 | -0.008 [-0.017, 0.001] | -0.038 [-0.052, -0.025] |
| c | both levels | 1 or 2 weeks | 2125 | 207 | -0.002 [-0.012, 0.007] | -0.033 [-0.049, -0.017] |
| a | middle | 1 or 2 weeks | 1278 | 84 | 0.005 [-0.005, 0.015] | 0.001 [-0.011, 0.013] |
| b | middle | 1 or 2 weeks | 1012 | 82 | -0.013 [-0.024, -0.002] | -0.024 [-0.044, -0.006] |
| c | middle | 1 or 2 weeks | 848 | 75 | -0.003 [-0.017, 0.010] | -0.011 [-0.035, 0.009] |
| chapter6_concept_pages | middle | 1 or 2 weeks | 406 | 55 | 0.026 [0.004, 0.049] | 0.001 [-0.027, 0.024] |
| a | narrow | 1 or 2 weeks | 2535 | 194 | 0.003 [-0.005, 0.011] | -0.014 [-0.025, -0.003] |
| b | narrow | 1 or 2 weeks | 1943 | 178 | -0.005 [-0.017, 0.007] | -0.046 [-0.065, -0.029] |
| c | narrow | 1 or 2 weeks | 1277 | 132 | -0.002 [-0.015, 0.011] | -0.047 [-0.069, -0.028] |
| chapter6_concept_pages | narrow | 1 or 2 weeks | 650 | 123 | 0.019 [0.002, 0.037] | -0.022 [-0.046, 0.001] |

Panels: a = all Seattle works with librarian headings (the Chapter 6 panel, plus LibriVox); b = the 20,000 AI-sorted works; c = the same 20,000 works with librarian headings.
- panel a: 2,559 rises tested in 10,236 rise-by-format tests (5,386 with a synthetic control); single tests with one-sided p < 0.05: 161; Benjamini-Hochberg q < 0.10: 0.
- panel b: 2,559 rises tested in 7,677 rise-by-format tests (4,158 with a synthetic control); single tests with one-sided p < 0.05: 118; Benjamini-Hochberg q < 0.10: 0.
- panel c: 2,559 rises tested in 7,677 rise-by-format tests (2,945 with a synthetic control); single tests with one-sided p < 0.05: 77; Benjamini-Hochberg q < 0.10: 0.
- A robustness run with the flagged rises included exists (g2_S2_pooled_with_flagged.csv).

## 6. Check G3: forecasts with the AI theme series

- Main rows of the benchmark: 36,081 forecasts of printed books and ebooks one month ahead (510 theme series, 88 months).

**Decision (fixed): Chronos-2 + S2 against Chronos-2 alone, interval of the paired difference below 0.** MAE ratio 0.9979 [0.9958, 0.9999], a change of -0.21%; interval below 1 (difference below 0): yes.

| pipeline | AvgRelMAE | share_beats_naive | rank correlation |
| --- | --- | --- | --- |
| naive | 1.0000 [1.0000, 1.0000] | 0.000 | n/a [n/a, n/a] |
| chronos2 | 0.9200 [0.9001, 0.9375] | 0.618 | 0.3079 [0.2744, 0.3396] |
| chronos2_cur | 0.9143 [0.8948, 0.9315] | 0.629 | 0.3190 [0.2829, 0.3522] |
| chronos2_nli | 0.9182 [0.8984, 0.9356] | 0.633 | 0.3162 [0.2807, 0.3486] |
| chronos2_ais2 | 0.9181 [0.8984, 0.9357] | 0.622 | 0.3172 [0.2836, 0.3490] |
| chronos2_ais1 | 0.9180 [0.8981, 0.9353] | 0.618 | 0.3167 [0.2806, 0.3503] |

AvgRelMAE below 1 beats repeating last month; the rank correlation is between the forecast change and the actual change within month, format and level. Paired comparisons (ratio of MAE, other over base, by series):

- chronos2_ais2 against chronos2: 0.9979 [0.9958, 0.9999] (-0.21%); better in 53% of series; rank correlation +0.0093 [+0.0041, +0.0151].
- chronos2_ais1 against chronos2: 0.9978 [0.9959, 0.9998] (-0.22%); better in 55% of series; rank correlation +0.0089 [+0.0032, +0.0146].
- chronos2_ais2 against chronos2_cur: 1.0042 [1.0020, 1.0062] (+0.42%); better in 44% of series; rank correlation -0.0018 [-0.0064, +0.0032].
- chronos2_ais2 against chronos2_nli: 0.9999 [0.9981, 1.0018] (-0.01%); better in 53% of series; rank correlation +0.0010 [-0.0030, +0.0051].
- chronos2_ais1 against chronos2_cur: 1.0040 [1.0019, 1.0060] (+0.40%); better in 40% of series; rank correlation -0.0023 [-0.0066, +0.0019].
- chronos2_ais1 against chronos2_nli: 0.9998 [0.9982, 1.0015] (-0.02%); better in 50% of series; rank correlation +0.0006 [-0.0026, +0.0038].
- chronos2_ais2 against chronos2_ais1: 1.0001 [0.9988, 1.0015] (+0.01%); better in 51% of series; rank correlation +0.0004 [-0.0025, +0.0036].
- chronos2_cur against chronos2: 0.9938 [0.9916, 0.9959] (-0.62%); better in 62% of series; rank correlation +0.0112 [+0.0041, +0.0185].
- chronos2_nli against chronos2: 0.9980 [0.9960, 1.0001] (-0.20%); better in 53% of series; rank correlation +0.0083 [+0.0027, +0.0142].

Wikipedia-only ranking with no fitting (the monthly change of a theme's series against the next month's change in borrowing, the Test C measure):

- S2 (AI pages): rank correlation 0.0085 [-0.0073, 0.0231] over 308 groups; rows with a value 100%.
- S1 (AI pages, top-500 days): rank correlation 0.0041 [-0.0104, 0.0189] over 308 groups; rows with a value 81%.
- concept pages: rank correlation 0.0260 [0.0085, 0.0424] over 308 groups; rows with a value 100%.
- zero-shot routing: rank correlation 0.0016 [-0.0123, 0.0157] over 308 groups; rows with a value 57%.
- embedding routing: rank correlation 0.0149 [0.0014, 0.0284] over 308 groups; rows with a value 22%.
- S2 (AI pages) minus concept pages: -0.0175 [-0.0371, +0.0032].
- S2 (AI pages) minus zero-shot routing: +0.0069 [-0.0102, +0.0244].
- S2 (AI pages) minus embedding routing: -0.0063 [-0.0253, +0.0123].
- S2 (AI pages) minus S1 (AI pages, top-500 days): +0.0045 [-0.0071, +0.0153].

Chronos-2 run time on this Mac: chronos2_ais1: 36,081 tasks in 455 s (full run about 7.6 min); chronos2_ais2: 36,081 tasks in 436 s (full run about 7.3 min).

## 7. Check G4: does it help when the same AI sorted the books too?

- G2, panel b, both levels, rises of 4 weeks or more: synthetic control 0.037 [0.017, 0.061], own trend 0.038 [0.011, 0.067] (640 tests).
- G2, panel c, both levels, rises of 4 weeks or more: synthetic control 0.027 [0.002, 0.053], own trend 0.011 [-0.021, 0.047] (432 tests).
- G2, panel b, middle, rises of 4 weeks or more: synthetic control 0.059 [0.023, 0.100], own trend 0.076 [0.029, 0.130] (188 tests).
- G2, panel c, middle, rises of 4 weeks or more: synthetic control 0.034 [-0.014, 0.088], own trend 0.013 [-0.046, 0.072] (153 tests).
- G2, panel b, narrow, rises of 4 weeks or more: synthetic control 0.028 [0.003, 0.056], own trend 0.021 [-0.013, 0.056] (452 tests).
- G2, panel c, narrow, rises of 4 weeks or more: synthetic control 0.023 [-0.006, 0.055], own trend 0.010 [-0.032, 0.054] (279 tests).
- G2, panel b minus panel c on the same rises and formats (positive: the AI-sorted books show the larger rise after a theme's rise):
  - narrow, rises of 4 weeks or more: synthetic control -0.000 [-0.019, 0.020], own trend 0.008 [-0.027, 0.040] (262 tests in 76 themes)
  - narrow, rises of 1 or 2 weeks: synthetic control 0.001 [-0.010, 0.012], own trend 0.007 [-0.006, 0.021] (1185 tests in 126 themes)
  - middle, rises of 4 weeks or more: synthetic control 0.018 [-0.009, 0.045], own trend 0.056 [0.018, 0.100] (152 tests in 40 themes)
  - middle, rises of 1 or 2 weeks: synthetic control -0.011 [-0.023, -0.001], own trend -0.015 [-0.033, 0.001] (833 tests in 75 themes)
  - both levels, rises of 4 weeks or more: synthetic control 0.007 [-0.009, 0.023], own trend 0.026 [-0.001, 0.052] (414 tests in 116 themes)
  - both levels, rises of 1 or 2 weeks: synthetic control -0.004 [-0.012, 0.003], own trend -0.002 [-0.013, 0.008] (2018 tests in 201 themes)
- Wikipedia-only ranking on 36,081 rows that all three panels share:
  - S2 (AI pages), panel a: 0.0085 [-0.0073, 0.0231]
  - S2 (AI pages), panel b: 0.0008 [-0.0163, 0.0177]
  - S2 (AI pages), panel c: 0.0054 [-0.0073, 0.0180]
  - S1 (AI pages, top-500 days), panel a: 0.0041 [-0.0104, 0.0189]
  - S1 (AI pages, top-500 days), panel b: 0.0049 [-0.0103, 0.0203]
  - S1 (AI pages, top-500 days), panel c: 0.0063 [-0.0062, 0.0183]
  - S2 (AI pages): panel b minus panel c: -0.0046 [-0.0188, +0.0093]
  - S2 (AI pages): panel b minus panel a: -0.0077 [-0.0212, +0.0062]
  - S2 (AI pages): panel c minus panel a: -0.0032 [-0.0126, +0.0072]
  - S1 (AI pages, top-500 days): panel b minus panel c: -0.0014 [-0.0129, +0.0102]
  - S1 (AI pages, top-500 days): panel b minus panel a: +0.0009 [-0.0117, +0.0138]
  - S1 (AI pages, top-500 days): panel c minus panel a: +0.0022 [-0.0063, +0.0112]

## 8. Choices the addendum did not fix (written into the code before any result)

- Step 20: A line with any code outside the guide (or a malformed token) is invalid as a whole and is re-asked; an item without an answer line is re-asked too; after the one re-ask a still invalid line is dropped. Codes are read case-insensitively; spaces for tabs are accepted; a repeated code keeps its first confidence; more than 3 codes keep the first 3. The second pass has no re-ask; judge codes outside the guide are dropped.
- Step 21: S1 has no data before 2016-01-01 and a week with a missing top-500 day is a partial week for S1; S2 uses only page-theme pairs of confidence 2 or 3; ties at the 40,000-page cut go by top-500 views, then title; the monthly series follow the benchmark rule (monthly_log).
- Step 22: Gap 0.34 s over 4 threads (at most 2.94 requests a second, under the limit of 3); a day missing from an answer is 0 views; the downloader also refuses while a job named with view, text or download runs.
- Step 23: A work's middle weight in panel b is the sum of its narrow weights; months with no loan of the 20,000 works are not usable; works without a theme stay in the denominator.
- Step 24: The weekly weighted views are the volume for the minimum-volume rule; the driver page is the page with the largest weighted rise; title_confusion is not applied; donors and placebo years are screened with the new series' rises and the stored GDELT rises; a row pooling both levels is added.
- Step 25: Rows without a value of the monthly change get 0 in the no-fitting ranking (as in Test C); G4 uses the main rows' keys where all three panels have the change.
- Step 26: Scores at the narrow level (routing pairs on narrow nodes) and the middle level; AI pairs of all confidences and of confidence 2 or 3; methods compared on the pages every method could route; page-bootstrap intervals.
- Step 27: First-theme agreement and overlap among items both passes put in a theme; none agreement with Cohen's kappa over all items.

## 9. Files

- Test F folder: /Users/mac/Documents/CMKL University/Thesis – Audiobook Performance Prediction/handoff/data/db/wiki_led/testF
- step reports: testF_20_parse.md, testF_21_series.md, testF_23_panels.md, testF_24_G2_S2_shifts.md, testF_24_G2_S2.md, testF_25_G3.md, testF_26_G1.md, testF_27_reliability.md (in /Users/mac/Documents/CMKL University/Thesis – Audiobook Performance Prediction/handoff/data/reports)
