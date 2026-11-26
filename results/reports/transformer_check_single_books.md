# A fair check of the Transformer lead for single books

Made by `code/main_study/wiki_led/o_transformer_check/o04_score.py` and `o05_report.py` on 2026-11-26 15:04 +0700. Settings fixed in advance in `prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json` (made public on GitHub, pull request 37, at 05:11 UTC on 26 November 2026, before any step ran). Choices made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum o".

## The question

In the previous report, the boosted-tree model with the library history and the own and author pages got better by +0.0091 when it was also given the forecasts of a pretrained Transformer (Chronos-2) as two extra inputs, the biggest gain found so far. Nothing was fixed in advance for it, and two doubts remained:

1. **Did the Transformer remember the test years?** It was trained before its release on 20 October 2025 on public time series that may cover the same years. So the gain is checked again on the 10 months after its release (November 2025 to August 2026), which it cannot have seen.
2. **Is it the Transformer, or just a longer look at the loans?** The Transformer reads up to 60 months of each book's loans; the trees' own history inputs reach back about a year. So the trees are also given the same 60 months in plain form (the last 24 months one by one, averages over 24, 36 and 60 months, trends over 12 and 36 months, spread, months with no loans, and three textbook forecasts: exponential smoothing, same month last year, and a 12-month straight line). The Transformer's forecasts must still add something on top.

Both must pass for the lead to count as confirmed on past data. A third, blind check uses September 2026, a month nobody has seen yet.

## How to read the numbers

- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; 0 is chance, 1 is perfect), averaged over the months. Models only ever learn from earlier years.
- **Gain**: the score of one model minus another's on the same rows. 0.001 is small; the own and author pages together add about 0.005.
- **Five seeds**: every boosted-tree model was fitted five times; a value is the mean, "±" their spread. The Transformer itself has no random part.
- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months. For the 10 months after the release, the blocks are drawn within those 10 months only.

## In short

- **Months the Transformer cannot have seen** (passed): on November 2025 to August 2026, its forecasts added +0.0111 (+0.0095 to +0.0126) (± 0.0002; +0.0110 to +0.0114; 5 of 5 above 0), against +0.0091 (+0.0071 to +0.0110) over all months.
- **More than a longer look at the loans** (passed): on top of the plain 60 months, its forecasts added +0.0040 (+0.0032 to +0.0048) (± 0.0003; +0.0037 to +0.0044; 5 of 5 above 0). The plain 60 months alone added +0.0128 (+0.0098 to +0.0156) (no rule); both together +0.0168 (+0.0141 to +0.0193).
- **Verdict**: the lead is **confirmed on past data**: both checks passed by the rule fixed in advance.
- **Transformer forecasts or plain 60 months** (no rule), each added alone to library + own pages: Transformer minus plain -0.0038 (-0.0065 to -0.0007); below 0 means the plain 60 months did better.
- **Which forecast carries it** (no rule): the forecast without pages alone added +0.0081 (+0.0060 to +0.0100), the one with pages alone +0.0089 (+0.0069 to +0.0108).
- **Placebo** (no rule): the real forecasts against the same forecasts made 12 months earlier: +0.0075 (+0.0053 to +0.0099).
- **2024 to 2026**: Transformer forecasts +0.0116 (+0.0093 to +0.0142); on top of the plain 60 months +0.0041 (+0.0031 to +0.0050).
- **Monthly top-20 lists** (no rule): share of the 20 books with the highest predicted change whose loans rose by half or more: 0.837 for library + own pages, 0.852 with the Transformer forecasts, 0.855 with the plain 60 months and the forecasts; early-warning lists 0.408, 0.476 and 0.486.
- **By kind of book** (no rule): the Transformer forecasts' gain was found in 47 of 53 groups and differed from the other books in 16; on top of the plain 60 months it was found in 49 of 53 and differed in 11, after correcting for the number of groups.
- **Blind month**: forecasts for September 2026 are frozen and public (20,122 rows, made 2026-11-26 07:56 UTC); they are scored once, when the library releases September and it is downloaded.

## Rules fixed in advance

Holm's correction over the two checks at one-sided 0.05; a check passes if Holm rejects it, its estimate is above 0 and its 95% interval is above 0.

| Check | Gain (95% interval) | One-sided p | Passes Holm | Passed |
| --- | --- | --- | --- | --- |
| Transformer forecasts added, months after its release (Nov 2025 to Aug 2026) | +0.0111 (+0.0095 to +0.0126) | 0.0005 | yes | **yes** |
| Transformer forecasts added on top of the plain 60 months, 2019 to 2026 | +0.0040 (+0.0032 to +0.0048) | 0.0005 | yes | **yes** |

## All months, February 2019 to August 2026

| Model | Score (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) | 0.333 | 0.348 | 0.361 |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) | 0.336 | 0.353 | 0.367 |
| Library + own pages + the two Transformer forecasts | 0.361 (0.353 to 0.370) | 0.0001 | 0.372 (0.356 to 0.387) | 0.346 | 0.361 | 0.377 |
| Library + own pages + the same 60 months in plain form | 0.365 (0.357 to 0.373) | 0.0002 | 0.379 (0.363 to 0.395) | 0.347 | 0.367 | 0.381 |
| Library + own pages + plain 60 months + the two Transformer forecasts | 0.369 (0.361 to 0.378) | 0.0002 | 0.383 (0.368 to 0.399) | 0.352 | 0.370 | 0.385 |
| Library + own pages + the Transformer forecast without pages | 0.360 (0.352 to 0.369) | 0.0001 | 0.371 (0.355 to 0.386) | 0.345 | 0.360 | 0.377 |
| Library + own pages + the Transformer forecast with pages | 0.361 (0.353 to 0.370) | 0.0001 | 0.372 (0.356 to 0.387) | 0.346 | 0.361 | 0.377 |
| Library + own pages + the two Transformer forecasts made 12 months earlier (placebo) | 0.354 (0.346 to 0.362) | 0.0002 | 0.362 (0.346 to 0.378) | 0.338 | 0.355 | 0.368 |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Transformer forecasts added to library + own pages | +0.0091 (+0.0071 to +0.0110) | ± 0.0002; +0.0088 to +0.0093; 5 of 5 above 0 | +0.0116 (+0.0093 to +0.0142) | +0.0095 (+0.0059 to +0.0130) | +0.0075 (+0.0055 to +0.0095) | +0.0102 (+0.0085 to +0.0122) |
| Plain 60 months added to library + own pages | +0.0128 (+0.0098 to +0.0156) | ± 0.0002; +0.0125 to +0.0131; 5 of 5 above 0 | +0.0191 (+0.0169 to +0.0209) | +0.0107 (+0.0041 to +0.0163) | +0.0139 (+0.0115 to +0.0162) | +0.0138 (+0.0109 to +0.0165) |
| Transformer forecasts added on top of the plain 60 months | +0.0040 (+0.0032 to +0.0048) | ± 0.0003; +0.0037 to +0.0044; 5 of 5 above 0 | +0.0041 (+0.0031 to +0.0050) | +0.0046 (+0.0032 to +0.0063) | +0.0033 (+0.0025 to +0.0041) | +0.0040 (+0.0031 to +0.0048) |
| Plain 60 months and Transformer forecasts together | +0.0168 (+0.0141 to +0.0193) | ± 0.0003; +0.0164 to +0.0171; 5 of 5 above 0 | +0.0231 (+0.0204 to +0.0253) | +0.0153 (+0.0099 to +0.0201) | +0.0172 (+0.0144 to +0.0198) | +0.0178 (+0.0152 to +0.0203) |
| Transformer forecasts against the plain 60 months (each added to library + own pages) | -0.0038 (-0.0065 to -0.0007) | ± 0.0001; -0.0038 to -0.0036; 0 of 5 above 0 | -0.0074 (-0.0093 to -0.0054) | -0.0012 (-0.0068 to +0.0055) | -0.0065 (-0.0081 to -0.0048) | -0.0036 (-0.0063 to -0.0009) |
| Only the forecast without pages | +0.0081 (+0.0060 to +0.0100) | ± 0.0001; +0.0079 to +0.0082; 5 of 5 above 0 | +0.0106 (+0.0084 to +0.0131) | +0.0082 (+0.0047 to +0.0117) | +0.0064 (+0.0044 to +0.0084) | +0.0096 (+0.0079 to +0.0115) |
| Only the forecast with pages | +0.0089 (+0.0069 to +0.0108) | ± 0.0001; +0.0087 to +0.0091; 5 of 5 above 0 | +0.0116 (+0.0093 to +0.0141) | +0.0096 (+0.0061 to +0.0131) | +0.0073 (+0.0054 to +0.0093) | +0.0098 (+0.0079 to +0.0117) |
| Transformer forecasts against the same forecasts made 12 months earlier | +0.0075 (+0.0053 to +0.0099) | ± 0.0002; +0.0072 to +0.0077; 5 of 5 above 0 | +0.0097 (+0.0065 to +0.0132) | +0.0079 (+0.0039 to +0.0118) | +0.0061 (+0.0038 to +0.0083) | +0.0087 (+0.0065 to +0.0111) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | + Transformer forecasts | + plain 60 months | + plain 60 months + forecasts |
| --- | --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.852 (0.830 to 0.873) | 0.845 (0.823 to 0.867) | 0.855 (0.833 to 0.876) |
| Early warning | 0.408 (0.375 to 0.443) | 0.476 (0.440 to 0.512) | 0.464 (0.424 to 0.505) | 0.486 (0.445 to 0.528) |

| List comparison | All books | Early warning |
| --- | --- | --- |
| Transformer forecasts added to library + own pages | +0.0150 (+0.0039 to +0.0265) | +0.0688 (+0.0488 to +0.0898) |
| Plain 60 months added to library + own pages | +0.0079 (-0.0027 to +0.0190) | +0.0568 (+0.0305 to +0.0845) |
| Transformer forecasts added on top of the plain 60 months | +0.0099 (+0.0047 to +0.0153) | +0.0221 (+0.0136 to +0.0294) |

## The 10 months after the Transformer's release (2025-11 to 2026-08)

185,459 scored rows. Intervals from redraws of 3-month blocks within these months only.

| Model | Score (95% interval) |
| --- | --- |
| Library model (loan history and calendar month) | 0.350 (0.332 to 0.370) |
| Library + own and author pages | 0.353 (0.336 to 0.372) |
| Library + own pages + the two Transformer forecasts | 0.364 (0.345 to 0.385) |
| Library + own pages + the same 60 months in plain form | 0.371 (0.353 to 0.390) |
| Library + own pages + plain 60 months + the two Transformer forecasts | 0.375 (0.357 to 0.395) |

| Comparison | Gain (95% interval) | Five seeds | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- |
| Transformer forecasts added to library + own pages | +0.0111 (+0.0095 to +0.0126) | ± 0.0002; +0.0110 to +0.0114; 5 of 5 above 0 | +0.0137 (+0.0099 to +0.0171) | +0.0098 (+0.0065 to +0.0125) | +0.0100 (+0.0080 to +0.0124) |
| Plain 60 months added to library + own pages | +0.0178 (+0.0158 to +0.0200) | ± 0.0003; +0.0174 to +0.0181; 5 of 5 above 0 |  |  |  |
| Transformer forecasts added on top of the plain 60 months | +0.0041 (+0.0036 to +0.0046) | ± 0.0003; +0.0036 to +0.0044; 5 of 5 above 0 | +0.0047 (+0.0034 to +0.0059) | +0.0040 (+0.0032 to +0.0047) | +0.0037 (+0.0028 to +0.0046) |
| Only the forecast without pages | +0.0101 (+0.0086 to +0.0114) | ± 0.0001; +0.0099 to +0.0103; 5 of 5 above 0 |  |  |  |
| Only the forecast with pages | +0.0111 (+0.0096 to +0.0126) | ± 0.0004; +0.0108 to +0.0117; 5 of 5 above 0 |  |  |  |
| Transformer forecasts against the same forecasts made 12 months earlier | +0.0094 (+0.0072 to +0.0118) | ± 0.0003; +0.0091 to +0.0098; 5 of 5 above 0 |  |  |  |

## Results by kind of book

Every group of the 14 families fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books are ranked against each other. "Score" is the library + own pages model's score in that group. Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged.

### Series (asked for by Khant)

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| in a series, known at the time | 120,125 | 78 | 0.306 | +0.0202 (+0.0171 to +0.0234) **found** **differs** | +0.0069 (+0.0055 to +0.0084) **found** |
| no series link known at the time | 165,706 | 78 | 0.369 | +0.0111 (+0.0087 to +0.0136) **found** **differs** | +0.0053 (+0.0042 to +0.0064) **found** |

### Film or TV adaptation (asked for by Khant)

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| film or TV version already out | 55,662 | 78 | 0.327 | +0.0231 (+0.0196 to +0.0265) **found** **differs** | +0.0099 (+0.0073 to +0.0125) **found** **differs** |
| no film or TV version out yet | 230,169 | 78 | 0.349 | +0.0125 (+0.0101 to +0.0150) **found** **differs** | +0.0049 (+0.0039 to +0.0058) **found** **differs** |

### Popularity in the year before (asked for by Khant)

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| low | 260,656 | 77 | 0.367 | +0.0097 (+0.0067 to +0.0127) **found** | +0.0048 (+0.0026 to +0.0079) **found** |
| middle | 442,985 | 78 | 0.331 | +0.0083 (+0.0061 to +0.0103) **found** | +0.0025 (+0.0017 to +0.0033) **found** **differs** |
| high | 555,166 | 78 | 0.348 | +0.0111 (+0.0088 to +0.0135) **found** **differs** | +0.0054 (+0.0045 to +0.0064) **found** **differs** |

### Fiction or nonfiction

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| fiction | 827,393 | 78 | 0.348 | +0.0096 (+0.0073 to +0.0117) **found** | +0.0037 (+0.0027 to +0.0048) **found** |
| nonfiction | 412,596 | 78 | 0.358 | +0.0077 (+0.0058 to +0.0096) **found** | +0.0045 (+0.0037 to +0.0054) **found** |
| other (mixed or unknown) | 18,818 | 78 | 0.338 | +0.0167 (+0.0112 to +0.0227) **found** **differs** | +0.0048 (+0.0012 to +0.0082) **found** |

### Audience

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| adult | 839,677 | 78 | 0.375 | +0.0070 (+0.0056 to +0.0084) **found** **differs** | +0.0038 (+0.0030 to +0.0047) **found** |
| children | 360,814 | 78 | 0.288 | +0.0137 (+0.0105 to +0.0170) **found** **differs** | +0.0046 (+0.0033 to +0.0060) **found** |
| young adult | 58,316 | 78 | 0.326 | +0.0043 (-0.0002 to +0.0090) | +0.0030 (+0.0011 to +0.0047) **found** |

### Format

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| audiobook | 340,064 | 78 | 0.367 | +0.0102 (+0.0085 to +0.0122) **found** | +0.0040 (+0.0031 to +0.0048) **found** |
| ebook | 446,291 | 78 | 0.353 | +0.0075 (+0.0055 to +0.0095) **found** **differs** | +0.0033 (+0.0025 to +0.0041) **found** |
| print | 472,452 | 78 | 0.336 | +0.0095 (+0.0059 to +0.0130) **found** | +0.0046 (+0.0032 to +0.0063) **found** |

### Time since first Seattle loan

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| under 1 year | 199,907 | 78 | 0.421 | +0.0056 (+0.0028 to +0.0087) **found** | +0.0028 (+0.0005 to +0.0044) **found** |
| 1 to 5 years | 548,026 | 78 | 0.333 | +0.0027 (-0.0004 to +0.0054) **differs** | +0.0027 (+0.0018 to +0.0035) **found** **differs** |
| 5 years or more | 510,874 | 78 | 0.316 | +0.0192 (+0.0170 to +0.0218) **found** **differs** | +0.0065 (+0.0053 to +0.0076) **found** **differs** |

### Author's earlier Seattle books

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| no | 360,676 | 78 | 0.356 | +0.0097 (+0.0076 to +0.0117) **found** | +0.0043 (+0.0033 to +0.0055) **found** |
| unknown | 7,372 | 78 | 0.330 | +0.0028 (-0.0103 to +0.0156) | +0.0011 (-0.0052 to +0.0073) |
| yes | 890,709 | 78 | 0.351 | +0.0089 (+0.0067 to +0.0109) **found** | +0.0038 (+0.0030 to +0.0047) **found** |

### Own Wikipedia article

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| author article only | 516,918 | 78 | 0.357 | +0.0078 (+0.0057 to +0.0098) **found** | +0.0039 (+0.0028 to +0.0051) **found** |
| book article | 265,942 | 78 | 0.341 | +0.0146 (+0.0120 to +0.0171) **found** **differs** | +0.0059 (+0.0048 to +0.0069) **found** **differs** |
| neither | 475,947 | 78 | 0.348 | +0.0063 (+0.0027 to +0.0091) **found** **differs** | +0.0030 (+0.0020 to +0.0039) **found** **differs** |

### Award

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| award won by then | 34,142 | 78 | 0.325 | +0.0196 (+0.0137 to +0.0251) **found** | +0.0072 (+0.0045 to +0.0099) **found** |
| no award known by then | 251,689 | 78 | 0.347 | +0.0140 (+0.0118 to +0.0163) **found** | +0.0058 (+0.0046 to +0.0068) **found** |

### Translated

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| translated | 17,953 | 78 | 0.328 | +0.0120 (+0.0045 to +0.0202) **found** | +0.0053 (+0.0012 to +0.0092) **found** |
| written in English | 254,007 | 78 | 0.344 | +0.0147 (+0.0122 to +0.0171) **found** | +0.0057 (+0.0046 to +0.0068) **found** |

### Public-domain classic

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| 1930 or later | 242,178 | 78 | 0.335 | +0.0158 (+0.0129 to +0.0185) **found** | +0.0060 (+0.0049 to +0.0071) **found** **differs** |
| first published before 1930 | 13,333 | 78 | 0.344 | +0.0211 (+0.0125 to +0.0306) **found** | +0.0124 (+0.0078 to +0.0179) **found** **differs** |

### Genre (broad theme)

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| B01 Magic, myth and the supernatural | 117,139 | 78 | 0.312 | +0.0111 (+0.0089 to +0.0133) **found** | +0.0046 (+0.0033 to +0.0060) **found** |
| B02 Gender, sexuality and relationships | 106,306 | 78 | 0.377 | +0.0058 (+0.0029 to +0.0088) **found** | +0.0023 (+0.0004 to +0.0041) **found** |
| B03 Religion and spirituality | 29,838 | 78 | 0.343 | +0.0074 (+0.0034 to +0.0116) **found** | +0.0037 (+0.0004 to +0.0067) **found** |
| B04 Science, technology and learning | 64,777 | 78 | 0.327 | +0.0095 (+0.0060 to +0.0132) **found** | +0.0035 (+0.0018 to +0.0052) **found** |
| B05 Race, ethnicity and migration | 49,860 | 78 | 0.383 | +0.0049 (+0.0008 to +0.0091) **found** **differs** | +0.0034 (+0.0013 to +0.0055) **found** |
| B06 Arts, media and entertainment | 70,364 | 78 | 0.365 | +0.0070 (+0.0034 to +0.0106) **found** | +0.0037 (+0.0014 to +0.0064) **found** |
| B07 Childhood, family and growing up | 113,354 | 78 | 0.358 | +0.0054 (+0.0006 to +0.0094) **found** **differs** | +0.0029 (+0.0015 to +0.0042) **found** |
| B08 War, conflict and history | 74,991 | 78 | 0.362 | +0.0088 (+0.0054 to +0.0124) **found** | +0.0038 (+0.0023 to +0.0053) **found** |
| B09 Nature, places and the environment | 96,529 | 78 | 0.361 | +0.0111 (+0.0064 to +0.0151) **found** | +0.0073 (+0.0052 to +0.0094) **found** **differs** |
| B10 Work, business and money | 34,342 | 78 | 0.331 | +0.0089 (+0.0050 to +0.0131) **found** | +0.0046 (+0.0019 to +0.0077) **found** |
| B11 Food, home and holidays | 51,305 | 78 | 0.401 | +0.0160 (+0.0098 to +0.0224) **found** **differs** | +0.0052 (+0.0022 to +0.0083) **found** |
| B12 Violence, trauma, death and grief | 47,097 | 78 | 0.377 | +0.0063 (+0.0025 to +0.0101) **found** | +0.0035 (+0.0015 to +0.0055) **found** |
| B13 Politics, society and justice | 34,610 | 78 | 0.404 | +0.0075 (+0.0032 to +0.0118) **found** | +0.0041 (+0.0019 to +0.0064) **found** |
| B14 Mind, self and philosophy | 72,637 | 78 | 0.334 | +0.0099 (+0.0067 to +0.0130) **found** | +0.0048 (+0.0032 to +0.0063) **found** |
| B15 Health, illness and addiction | 28,119 | 78 | 0.326 | +0.0039 (-0.0004 to +0.0082) | +0.0020 (-0.0005 to +0.0048) |
| B16 Animals | 73,393 | 78 | 0.304 | +0.0098 (+0.0051 to +0.0145) **found** | +0.0021 (-0.0003 to +0.0048) |
| B17 Sports, games and fitness | 18,180 | 78 | 0.319 | +0.0081 (-0.0009 to +0.0182) | +0.0044 (+0.0006 to +0.0086) **found** |
| B18 Space and the universe | 14,185 | 78 | 0.299 | +0.0037 (-0.0057 to +0.0125) | +0.0017 (-0.0024 to +0.0059) |
| B19 Crime, police and law | 51,005 | 78 | 0.354 | +0.0109 (+0.0069 to +0.0146) **found** | +0.0022 (+0.0005 to +0.0039) **found** |
| no theme | 110,776 | 78 | 0.339 | +0.0104 (+0.0068 to +0.0142) **found** | +0.0044 (+0.0026 to +0.0063) **found** |

### Has a theme

| Group | Rows | Months | Score | Transformer forecasts added | Added on top of the plain 60 months |
| --- | --- | --- | --- | --- | --- |
| no | 162,732 | 78 | 0.349 | +0.0087 (+0.0056 to +0.0120) **found** | +0.0043 (+0.0030 to +0.0057) **found** |
| yes | 1,096,075 | 78 | 0.353 | +0.0091 (+0.0071 to +0.0110) **found** | +0.0039 (+0.0030 to +0.0048) **found** |

## Data and checks

- The plain 60 months come from the same monthly loan series the Transformer reads. Checks: the last month equals the stored history input on every row (100%); the same-month-last-year forecast equals the stored one wherever both exist; the smoothing forecast matched an independent calculation on sampled books.
- A refit of the library + own pages model reproduces the stored predictions exactly, and the previous report's +0.0091 is reproduced.
- The forecasts made 12 months earlier are missing for 46% of rows (no row a year before), so that placebo mostly speaks for books with a longer record.
- Blind month: 20,122 rows at origin August 2026, frozen 2026-11-26 07:56 UTC; file `prereg/blind_o/forecasts_origin_2026-08.csv`, SHA-256 5d2f1b3e1333d182... in `prereg/README.md`. Check: the library + own pages forecast of the first seed equals the one frozen for the earlier blind test.

## Limits

- The unseen-months check has 10 months only. Its interval redraws blocks within those 10 months, so it shows the month-to-month variation inside them only, and it can look narrower than the interval over all months.
- The 10 months were not blind: they sit inside the 2024 to 2026 window, whose gain was seen before the rules were fixed. That check answers the worry about pretraining, not whether the gain holds on new data; the blind month does that.
- The plain 60 months are one fair way to give the trees the same loans, not every possible way; a model built to read long histories might do better.
- The Transformer was used as released, without tuning or training on library data.
- The blind month is one month: it adds to the backtest, it does not replace it.
- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.

