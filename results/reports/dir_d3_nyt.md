# D3: New York Times best-seller lists as a second target (addendum i)

1. Of the 7,747 Seattle books of Test A, 2,892 (37.3%) were on a New York Times best-seller list at least once between June 2008 and October 2026. They are mostly books published after 2008 and among the most borrowed; a hand check of 50 random matches found 50 right.
2. Among those books, Wikipedia alone ranks which ones come onto a list next month far better than chance (AUC 0.818, where 0.5 is chance; 17.8% of its monthly top 20 are listed next month, against 0.7% of all), but the library history ranks them better (AUC 0.856, top 20 26.0%); much of the skill of both is spotting new releases that are about to be listed.
3. Both together are best (AUC 0.877, top 20 30.4%): Wikipedia adds a little to the library history (+0.021 AUC, +4.4 points in the top 20, both intervals above zero); for books in the library three years or more, Wikipedia alone does as well as the library history (AUC 0.794 and 0.791) and the gain of the two together is largest (+0.042).
4. Borrowing and the lists move mostly in the same month: Seattle loans jump in the month a book enters a list (correlation 0.097), keep rising a little in the month after (0.032) and rise less in the month before (0.012).
5. For books already in the library, loans (against their own earlier level) after the first list week are about 1.7 to 1.9 times those of similar books in months 0 to 2 and still 1.6 times after a year, having started to rise one to three months before; new bestsellers are borrowed from their first month and peak a median 3 months after their first list week.

Direction D3 of prereg/addenda_wiki_led/2026-10-22_i_directions.json. Code: code/main_study/wiki_led/dirs/d3_nyt.py (its header lists every setting the record left open, with the time it was written). Data: data/db/wiki_led/dirs/d3_nyt/. Descriptive; every interval is a 95% interval. Run 22 Oct 2026.

## 1. Data and matching

- **Lists.** 958 weekly overview files of the official Books API (2008-06-15 to 2026-10-18; the 2008-06-08 file is empty), 298,479 list entries after dropping 117 stale second copies of a list (files of 2008 to 2011 repeat some lists; the copy that repeats unchanged in other weeks is dropped). The "Children's & Young Adult Series" lists (9,560 entries) are left out because their entries are series, not books. 22,943 distinct books (title and author). A week belongs to the month of its published date; the list reflects sales of a week that ended about two weeks earlier.
- **ISBNs.** The collector kept only each entry's primary ISBN-13 (99.2% of entries have one), not the other ISBNs the API lists. Seattle records carry ISBNs only for ebooks and audiobooks, none for print, so the Wikidata edition ISBNs of each work's matched item were added. An ISBN hit needs the titles to agree.
- **Routes** (distinct NYT title, author and ISBN combinations): Seattle ISBN 1,248, Wikidata ISBN 919, title and author family name 3,385, ambiguous and dropped 3, no match 26,093. An entry counts for every Test A work of the matched book whose title agrees (Test A has 544 works that share 224 articles).
- **Match rate.** 2,892 of 7,747 Test A works (37.3%) have at least one NYT week; 2,788 of 22,943 distinct NYT books (12.2%) reach a Test A work (most NYT books have no Wikipedia article of their own or fewer than 500 Seattle loans, so they are not in Test A).
- **Hand check.** 50 random matched pairs (NYT book and Seattle work), read on both sides: 50 of 50 right (exact interval 92.9% to 100.0%) on the fourth sheet, drawn after the last change to the rules. Earlier sheets: 49, 47 and 48 of 50; their errors (an entry also given to another book that shares an author page as its article; a Dirk Cussler novel matched through the author page "Clive Cussler"; graphic versions; another book of a series, such as SKIPPYJON JONES: SNOW WHAT on Skippyjon Jones) led to the rules in the header, choices 6 to 7c. Sheets: hand_check_50*.csv.
- **Missed matches.** In 400 random unmatched Test A works, NYT entries by an author with the same family name and a similar title were listed: 6 entries for 5 works, all other books (for example IF YOU GIVE A DOG A DONUT against If you give a mouse a cookie, BEYOND THE ICE LIMIT against The Ice Limit). No missed match was found this way; matches lost to unusual author strings are not covered by this check.

## 2. Which books match

| Test A works | works | matched |
|---|---:|---:|
| earliest Seattle edition up to 2000 | 1,383 | 5.4% |
| earliest Seattle edition 2001 to 2008 | 1,750 | 22.2% |
| earliest Seattle edition 2009 to 2016 | 2,396 | 56.6% |
| earliest Seattle edition 2017 to 2026 | 2,218 | 48.4% |
| Seattle loans 2016 to 2026, lowest quarter | 1,938 | 21.4% |
| Seattle loans 2016 to 2026, second | 1,940 | 26.9% |
| Seattle loans 2016 to 2026, third | 1,933 | 36.8% |
| Seattle loans 2016 to 2026, highest quarter | 1,936 | 64.3% |
| Seattle subjects: fiction | 4,493 | 34.3% |
| Seattle subjects: not fiction | 3,068 | 42.7% |
| all | 7,747 | 37.3% |

Matched works by the list family they appear on most: fiction 52.8%, nonfiction 31.3%, children and young adult 14.6%, graphic 1.3%. Median first NYT year of a matched work 2015; median first Seattle loan 2015 (unmatched 2008). On the NYT side the share that reaches a Test A work grows with time on the lists: 1 week 5.8%, 2 to 4 weeks 6.8%, 5 to 12 weeks 12.3%, 13 to 52 weeks 29.3%, over 52 weeks 60.9%. So the matched set is mostly recent bestsellers that Seattle lent a lot; classics and older books are rarely on these lists (the lists start in 2008).

## 3. (a) Which books come onto a list next month

Rows: Test A's rows (origin months 2019-01 to 2026-07, features at the end of month t) of books with no NYT week in month t; the target is at least one NYT week in month t+1. Main population, as the record says, the matched works (194,692 rows, 2,882 works, 78 months, 1,283 appearances, base rate 0.68% per month). This population is chosen with hindsight (books listed at some time in 2008 to 2026); the same test on all 7,747 works (549,923 rows, base rate 0.24%) is the check. Of the appearances, 421 are first appearances (never listed since June 2008) and 862 returns; 50.0% had been listed in the 12 months before.

Models: "refit" = Test A's LightGBM regressor and settings, unchanged, trained on the new target walk-forward by year (W: Wikipedia features, H: library history, HW: both). "Test A" = Test A's stored scores for its own targets (change D and level Y), not trained on the NYT target. NYT-past = weeks on any list in the 12 months before (a reference added here). Placebo = Test A's stored placebo scores (each book scored with the pages of a donor book of similar traffic).

| model | AUC, mean of months (interval) | AUC first appearances | AUC returns | top-20 share (interval) | top 20 / base rate | all works: AUC | all works: top 20 |
|---|---|---:|---:|---|---:|---:|---:|
| W refit | 0.818 (0.800 to 0.837) | 0.933 | 0.760 | 17.8% (15.8% to 20.0%) | 26 | 0.821 | 12.8% |
| H refit | 0.856 (0.843 to 0.869) | 0.944 | 0.810 | 26.0% (22.6% to 29.5%) | 38 | 0.885 | 19.6% |
| HW refit | 0.877 (0.862 to 0.892) | 0.977 | 0.825 | 30.4% (26.7% to 34.3%) | 45 | 0.898 | 24.7% |
| W, Test A change | 0.730 (0.708 to 0.753) | 0.886 | 0.653 | 13.4% (11.3% to 15.6%) | 20 | 0.717 | 7.6% |
| H, Test A change | 0.589 (0.566 to 0.612) | 0.900 | 0.451 | 7.9% (5.8% to 10.1%) | 12 | 0.587 | 3.4% |
| HW, Test A change | 0.627 (0.603 to 0.649) | 0.924 | 0.494 | 13.3% (10.8% to 15.8%) | 20 | 0.620 | 4.9% |
| W, Test A level | 0.823 (0.808 to 0.840) | 0.895 | 0.787 | 9.5% (7.6% to 11.6%) | 14 | 0.838 | 5.8% |
| H, Test A level | 0.838 (0.827 to 0.850) | 0.829 | 0.836 | 10.6% (9.0% to 12.4%) | 16 | 0.890 | 9.9% |
| HW, Test A level | 0.849 (0.838 to 0.860) | 0.851 | 0.842 | 11.3% (9.8% to 13.1%) | 17 | 0.898 | 10.2% |
| W ridge, Test A change | 0.740 (0.721 to 0.760) | 0.876 | 0.672 | 8.7% (6.9% to 10.8%) | 13 | 0.738 | 4.4% |
| Wikipedia rule, Test A | 0.638 (0.616 to 0.658) | 0.721 | 0.601 | 4.3% (3.0% to 5.6%) | 6 | 0.643 | 2.1% |
| naive library rule, Test A | 0.551 (0.530 to 0.575) | 0.590 | 0.545 | 2.2% (1.3% to 3.3%) | 3 | 0.538 | 1.2% |
| NYT-past rule | 0.612 (0.577 to 0.650) | 0.010 | 0.895 | 13.4% (11.4% to 15.4%) | 20 | 0.760 | 13.4% |
| placebo W, change | 0.580 (0.555 to 0.607) | 0.551 | 0.588 | 1.3% (0.7% to 1.9%) | 2 | 0.591 | 0.4% |
| placebo W, level | 0.615 (0.588 to 0.643) | 0.581 | 0.626 | 1.5% (1.0% to 2.1%) | 2 | 0.634 | 0.5% |
| placebo HW, change | 0.588 (0.565 to 0.611) | 0.904 | 0.448 | 9.6% (7.6% to 11.7%) | 14 | 0.586 | 3.2% |
| placebo HW, level | 0.839 (0.828 to 0.851) | 0.831 | 0.837 | 10.5% (9.0% to 12.2%) | 16 | 0.891 | 9.9% |
| chance | 0.500 | 0.500 | 0.500 | 0.68% | 1 | 0.500 | 0.24% |

AUC first appearances and returns: share of (listed, not listed) pairs of the same month ranked right, with only that kind of appearance as the listed side. The NYT-past rule scores 0 for every book never listed, so it ranks first appearances below the rest.

Paired differences on the same months (matched works; all works in brackets):

| difference | AUC (interval) | top-20 share, points (interval) |
|---|---|---|
| HW refit minus H refit | +0.021 (+0.004 to +0.038) [+0.013] | +4.4 (+3.1 to +5.8) [+5.1] |
| W refit minus H refit | -0.038 (-0.060 to -0.015) [-0.064] | -8.1 (-10.8 to -5.6) [-6.8] |
| Test A change: HW minus H | +0.037 (+0.027 to +0.048) [+0.032] | +5.4 (+4.2 to +6.6) [+1.5] |
| Test A level: HW minus H | +0.011 (+0.009 to +0.013) [+0.009] | +0.7 (+0.1 to +1.3) [+0.3] |
| HW refit minus NYT-past | +0.265 (+0.221 to +0.307) [+0.139] | +17.0 (+12.6 to +21.7) [+11.3] |
| W minus its placebo, change | +0.150 (+0.117 to +0.182) [+0.126] | +12.1 (+10.3 to +14.2) [+7.2] |
| W minus its placebo, level | +0.208 (+0.189 to +0.230) [+0.204] | +7.9 (+6.1 to +10.1) [+5.3] |

By the book's age in Seattle at month t (pair-weighted AUC within months, interval by month blocks; added after the first scoring):

| age in Seattle | rows | appearances (first) | W refit | H refit | HW refit | HW minus H | NYT-past |
|---|---:|---:|---|---|---|---|---|
| under 12 months | 6,157 | 494 (335) | 0.783 (0.760 to 0.807) | 0.852 (0.819 to 0.884) | 0.879 (0.848 to 0.908) | +0.028 (+0.012 to +0.044) | 0.280 (0.238 to 0.319) |
| 12 to 35 months | 18,787 | 287 (23) | 0.670 (0.633 to 0.708) | 0.746 (0.709 to 0.779) | 0.760 (0.728 to 0.792) | +0.013 (-0.020 to +0.050) | 0.778 (0.742 to 0.816) |
| 36 months or more | 169,748 | 502 (63) | 0.794 (0.765 to 0.823) | 0.791 (0.771 to 0.811) | 0.834 (0.808 to 0.857) | +0.042 (+0.009 to +0.074) | 0.787 (0.743 to 0.827) |

Reading. Refitted on the sales target, Wikipedia alone ranks next month's list appearances well above chance but below the library history, and Wikipedia adds a small amount to the library history. Test A's stored Wikipedia scores beat their placebo (the pages of a similar book by another author) by 0.15 (change) and 0.21 (level) in AUC, so the ranking comes from the book's own pages and not only from their traffic level; the refits were not given a placebo. Much of the ranking for all three models is the recognition of new books: a book that has just reached the library and just got a Wikipedia page is often a new release about to be listed (the refits rank first appearances with AUC above 0.9). Returns to a list (paperback editions, film tie-ins, books listed again) are harder; among books in the library three years or more, Wikipedia alone matches the library history and the two together do best, while for books in the library one to three years the NYT-past rule (a recent bestseller coming back, often as a paperback) is at least as good. Test A's own scores, trained to rank next month's borrowing change, rank list appearances much less well than the refits (the library change model is close to chance for returns), so the sales target needs its own fit; Test A's level scores (next month's loans) do better, because books borrowed a lot are the ones that sell.

## 4. (b) Lead and lag

Matched works, monthly change in Seattle loans (log of 1 + loans, all formats; excluded months and months before the first loan left out) against NYT presence (0/1) or the list entry month (listed in a month, not in the month before), both demeaned within the work and pooled over works. k > 0: the list k months after the loan change (borrowing first); k < 0: the list k months before (list first). Intervals: bootstrap over works.

| k | presence 2008 to 2026 | entry 2008 to 2026 | presence 2016 to 2026 | entry 2016 to 2026 |
|---:|---|---|---|---|
| -3 | -0.020 (-0.022 to -0.018) | -0.006 (-0.008 to -0.004) | -0.015 (-0.017 to -0.013) | -0.004 (-0.006 to -0.001) |
| -2 | -0.011 (-0.013 to -0.010) | 0.003 (0.000 to 0.005) | -0.012 (-0.014 to -0.010) | -0.002 (-0.005 to 0.001) |
| -1 | 0.011 (0.008 to 0.013) | 0.032 (0.029 to 0.035) | 0.003 (0.001 to 0.006) | 0.019 (0.015 to 0.022) |
| +0 | 0.062 (0.058 to 0.065) | 0.097 (0.092 to 0.103) | 0.048 (0.044 to 0.053) | 0.082 (0.075 to 0.088) |
| +1 | 0.055 (0.052 to 0.058) | 0.012 (0.009 to 0.015) | 0.043 (0.039 to 0.047) | 0.015 (0.011 to 0.019) |
| +2 | 0.042 (0.039 to 0.046) | -0.000 (-0.003 to 0.002) | 0.034 (0.030 to 0.037) | -0.000 (-0.003 to 0.002) |
| +3 | 0.031 (0.028 to 0.034) | 0.001 (-0.001 to 0.004) | 0.025 (0.022 to 0.029) | 0.002 (-0.001 to 0.004) |

Rows: 357,648 work-months of 2,890 works (entry, k = 0). Reading: the loan change goes with the entry month itself; the entry is followed by a further rise in the next month (k = -1) more than it is preceded by one (k = +1). Presence (a state that lasts for months) correlates with loan changes in the same and later months and negatively with changes 2 and 3 months after the book was listed, when loans fall back. Correlations are small because most months of most books have neither an entry nor a large change.

## 5. (c) Seattle loans around the first NYT week

Event: the month of a matched work's first NYT week, 2009-01 to 2026-08 (2,679 of 2,892 matched works; earlier first weeks are left out because lists before June 2008 were not collected). 478 of them were in the Seattle library at least 6 months before (established books); the other 2,201 are new books (section 5.3). Controls: works of the same month and loan decile with no NYT week in the window. Two baselines: "own" (choices 15 and 16: M6 over months -6 to -1, so months -3 to -1 are inside the baseline) and "D2" (D2's baseline, months -9 to -4, added after the first results, so months -3 to -1 show any rise before the event). Placebo: every event moved 24 months earlier. Excess D = log(1 + loans) minus log(1 + M6), event minus the mean of its controls (exp(D) - 1 is the extra share of loans). Rose and surged: Test A's rules.

### 5.1 own baseline: 477 events (fiction 242, nonfiction 132, children and young adult 89, graphic 14), median 409 controls each; placebo 296 events

| month | excess D (interval) | loans times similar books | excess rose | excess surged | placebo excess D (interval) | placebo excess rose |
|---:|---|---:|---|---|---|---:|
| -3 | -0.013 (-0.038 to 0.012) | 0.99 | -0.8% (-2.2% to 0.9%) | -0.2% (-0.4% to 0.3%) | 0.031 (0.003 to 0.058) | 0.5% |
| -2 | 0.078 (0.048 to 0.108) | 1.08 | 5.4% (2.8% to 8.1%) | 2.5% (1.0% to 4.0%) | 0.008 (-0.023 to 0.040) | 0.6% |
| -1 | 0.282 (0.232 to 0.335) | 1.33 | 18.2% (14.5% to 22.2%) | 11.8% (8.8% to 14.8%) | 0.040 (0.002 to 0.077) | 0.0% |
| +0 | 0.535 (0.463 to 0.612) | 1.71 | 36.8% (32.2% to 41.2%) | 25.0% (21.2% to 29.2%) | 0.062 (0.019 to 0.105) | 3.8% |
| +1 | 0.646 (0.568 to 0.728) | 1.91 | 41.0% (36.7% to 45.6%) | 32.3% (28.0% to 36.4%) | 0.051 (0.005 to 0.098) | 3.6% |
| +2 | 0.667 (0.585 to 0.753) | 1.95 | 39.9% (35.6% to 44.4%) | 33.8% (29.6% to 38.1%) | 0.049 (-0.001 to 0.100) | 2.3% |
| +3 | 0.632 (0.546 to 0.715) | 1.88 | 38.1% (33.7% to 42.6%) | 32.6% (28.5% to 37.2%) | 0.063 (0.015 to 0.113) | 5.4% |
| +4 | 0.646 (0.560 to 0.735) | 1.91 | 38.5% (34.0% to 42.9%) | 34.4% (30.1% to 38.9%) | 0.052 (-0.003 to 0.103) | 4.3% |
| +5 | 0.657 (0.576 to 0.740) | 1.93 | 39.1% (34.6% to 43.4%) | 33.4% (29.0% to 37.8%) | 0.060 (0.006 to 0.115) | 5.7% |
| +6 | 0.624 (0.540 to 0.712) | 1.87 | 36.7% (32.4% to 41.2%) | 32.0% (27.4% to 36.2%) | 0.090 (0.033 to 0.143) | 7.6% |
| +7 | 0.601 (0.516 to 0.684) | 1.82 | 37.1% (32.8% to 41.7%) | 30.6% (26.4% to 34.9%) | 0.071 (0.018 to 0.122) | 4.2% |
| +8 | 0.606 (0.522 to 0.688) | 1.83 | 33.9% (29.2% to 38.5%) | 30.5% (26.4% to 34.9%) | 0.092 (0.035 to 0.147) | 7.4% |
| +9 | 0.566 (0.484 to 0.643) | 1.76 | 34.3% (29.9% to 38.7%) | 28.9% (24.7% to 33.1%) | 0.079 (0.021 to 0.136) | 5.7% |
| +10 | 0.527 (0.441 to 0.607) | 1.69 | 31.5% (27.0% to 35.8%) | 27.1% (23.1% to 31.3%) | 0.130 (0.071 to 0.187) | 9.0% |
| +11 | 0.524 (0.443 to 0.603) | 1.69 | 32.1% (27.5% to 36.6%) | 26.6% (22.4% to 31.2%) | 0.157 (0.095 to 0.219) | 11.3% |
| +12 | 0.491 (0.408 to 0.573) | 1.63 | 30.0% (25.8% to 34.4%) | 25.7% (21.7% to 29.9%) | 0.181 (0.116 to 0.249) | 11.7% |

Excess D by the family of the first list (months 0, 2, 6, 12): children and young adult 0.39, 0.45, 0.55, 0.54; fiction 0.60, 0.78, 0.72, 0.56; nonfiction 0.54, 0.65, 0.53, 0.35.

### 5.2 D2 baseline: 457 events (fiction 229, nonfiction 129, children and young adult 86, graphic 13), median 419 controls each; placebo 292 events

| month | excess D (interval) | loans times similar books | excess rose | excess surged | placebo excess D (interval) | placebo excess rose |
|---:|---|---:|---|---|---|---:|
| -3 | 0.136 (0.097 to 0.177) | 1.15 | 10.7% (7.2% to 14.0%) | 6.8% (4.4% to 9.6%) | 0.073 (0.032 to 0.117) | 2.1% |
| -2 | 0.227 (0.182 to 0.273) | 1.25 | 15.1% (11.4% to 19.2%) | 9.6% (6.8% to 12.7%) | 0.050 (0.001 to 0.098) | 3.9% |
| -1 | 0.410 (0.348 to 0.471) | 1.51 | 26.8% (22.6% to 31.2%) | 17.6% (13.9% to 21.3%) | 0.080 (0.027 to 0.134) | 4.1% |
| +0 | 0.638 (0.560 to 0.721) | 1.89 | 38.1% (33.5% to 42.5%) | 30.0% (25.6% to 34.3%) | 0.099 (0.049 to 0.153) | 6.4% |
| +1 | 0.743 (0.655 to 0.827) | 2.10 | 42.9% (38.4% to 47.2%) | 36.7% (32.3% to 41.3%) | 0.088 (0.034 to 0.142) | 5.0% |
| +2 | 0.760 (0.677 to 0.850) | 2.14 | 41.4% (37.0% to 45.9%) | 35.7% (31.1% to 40.2%) | 0.085 (0.027 to 0.145) | 6.8% |
| +3 | 0.726 (0.638 to 0.815) | 2.07 | 40.9% (36.6% to 45.5%) | 35.5% (31.1% to 39.7%) | 0.093 (0.037 to 0.147) | 7.0% |
| +4 | 0.743 (0.651 to 0.838) | 2.10 | 42.0% (37.6% to 46.5%) | 36.4% (32.1% to 40.7%) | 0.080 (0.019 to 0.136) | 4.4% |
| +5 | 0.748 (0.658 to 0.843) | 2.11 | 43.1% (38.7% to 47.4%) | 36.2% (31.6% to 40.8%) | 0.090 (0.029 to 0.152) | 7.0% |
| +6 | 0.716 (0.627 to 0.811) | 2.05 | 39.9% (35.5% to 44.0%) | 34.2% (29.7% to 38.7%) | 0.122 (0.062 to 0.179) | 9.5% |
| +7 | 0.693 (0.601 to 0.785) | 2.00 | 37.9% (33.2% to 42.5%) | 32.9% (28.6% to 37.3%) | 0.104 (0.053 to 0.162) | 6.6% |
| +8 | 0.697 (0.609 to 0.787) | 2.01 | 38.4% (33.8% to 43.0%) | 33.4% (29.1% to 37.9%) | 0.122 (0.057 to 0.183) | 7.8% |
| +9 | 0.654 (0.570 to 0.744) | 1.92 | 36.7% (32.1% to 41.4%) | 31.9% (27.6% to 36.3%) | 0.107 (0.047 to 0.172) | 9.1% |
| +10 | 0.625 (0.538 to 0.717) | 1.87 | 34.7% (30.4% to 39.3%) | 30.3% (26.1% to 34.9%) | 0.163 (0.097 to 0.227) | 10.5% |
| +11 | 0.615 (0.529 to 0.706) | 1.85 | 36.2% (31.7% to 40.3%) | 28.9% (24.7% to 33.2%) | 0.189 (0.120 to 0.256) | 11.5% |
| +12 | 0.587 (0.498 to 0.680) | 1.80 | 33.2% (28.5% to 37.7%) | 28.9% (24.5% to 33.3%) | 0.211 (0.136 to 0.288) | 13.0% |

Excess D by the family of the first list (months 0, 2, 6, 12): children and young adult 0.53, 0.57, 0.63, 0.61; fiction 0.69, 0.87, 0.81, 0.66; nonfiction 0.66, 0.75, 0.65, 0.47.

### 5.3 New books

For the 2,201 matched books that reached Seattle less than 6 months before their first NYT week, the first Seattle loan came in the month before the first list week for 52.6%, in the same month for 41.5% and later for 6.0% (a list week reflects sales of about two weeks earlier, so a book released late in a month is often listed early in the next). Their peak month of loans in the first 24 months came a median 3 months after the first list week (quartiles 1 and 7); 43.5% peaked in months 0 to 2 and 0.3% before the first list week. Library borrowing of a new bestseller starts with its release and the list, and peaks later, as holds queues are worked through.

Reading. For established books the first list week comes with a large and lasting rise in Seattle loans: about 1.7 to 1.9 times similar books in months 0 to 2, and 1.6 times a year later. With D2's earlier baseline, loans were already higher in months -3 to -1 (0.14, 0.23 and 0.41): borrowing starts rising before the first list week, partly because the list reports sales two weeks late and partly because the books that become bestsellers were gaining readers already. The placebo is not zero (about 0.10 at month 0 and 0.21 at month 12 with D2's baseline): books that later become bestsellers drift up against controls matched on level only, so part of the later months' excess is this drift, but the rise at the list week is many times the placebo.

## 6. Limits

- The NYT lists are a ranking of sales, not sales counts; a book off the list may still sell well. Presence is coarse (a month with one week counts as listed).
- Only the primary ISBN of each entry was saved; Seattle has no print ISBNs; most matches use title and author (hand check 50 of 50 right on the last sheet, recall checked only for similar titles).
- The main population of (a) is chosen with hindsight (books listed at some time); the all-works version is the check and gives the same order of models.
- Test A rows exist only for books already lent in Seattle, so new releases listed in their first month are mostly outside (a); they are described in 5.3.
- Weeks of monthly topic lists repeat inside a month; only presence (not weeks) is used in the tests.
- A list published early in month t+1 reports sales of the last days of month t, so part of the target of (a) is close to a same-month signal; no input of (a) uses anything after month t.
- The event controls are matched on loan level, not trend (the placebo shows the drift). Wikidata and Seattle mapping errors of Test A (some works carry an author page as their article) are inherited.

## 7. Settings and changes

All open settings are in the header of d3_nyt.py with their times; the change to the record (primary ISBN only, Wikidata ISBNs added), the tightening of the matching rules after the hand checks (before any test result) and the descriptive additions after the first results (age split and placebo in (a), D2 baseline and placebo in (c)) are logged in prereg/DEVIATIONS.md under addendum i. Nothing was tuned; no direction or model was chosen from these results.

Files in data/db/wiki_led/dirs/d3_nyt/: nyt_entries.parquet (all entries), nyt_key_matches.parquet and nyt_entries_matched.parquet (matching), nyt_monthly.parquet (work by month: weeks, best rank, lists, families), works_match_info.parquet, hand_check_50*.csv, recall_probe.csv, a_rows.parquet, a_refit_preds.parquet, a_results.json, b_results.json, c_events_own.parquet, c_events_d2.parquet, c_results.json, a_run.log.
