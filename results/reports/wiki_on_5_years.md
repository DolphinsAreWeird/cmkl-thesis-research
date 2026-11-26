# Do the Wikipedia pages still help once the model has 5 years of loans?

Made by `code/main_study/wiki_led/q_wiki_on_5_years/q03_score.py` and `q04_report.py` on 2026-11-26 15:39 +0700. Settings fixed in advance in `prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json` (made public on GitHub, pull request 39, at 08:16 UTC on 26 November 2026, before any step ran). Choices made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum q".

## The question

The previous check found that giving the boosted-tree model 5 years of each book's loans (in plain form: monthly values, averages, trends and simple forecasts) raised the score more than anything else so far. Before making that the main model, one question matters for the thesis: the Wikipedia gain was measured on top of a loan history that reaches back only about a year. Some of what the pages carry, such as which books stay read for years, may also be in older loans. So: **with 5 years of loans in the model, do the book's and author's Wikipedia pages still add to the score?** This is checked on all books and on books that have a page (their own or their author's), the sample of the thesis.

## How to read the numbers

- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; 0 is chance, 1 is perfect), averaged over the months, February 2019 to August 2026. Models only ever learn from earlier years.
- **Gain**: the score of one model minus another's on the same rows.
- **Five seeds**: every model was fitted five times; a value is the mean, "±" their spread.
- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months.

## In short

- **All books** (passed): with 5 years of loans, the pages add +0.0046 (+0.0039 to +0.0055) (± 0.0004; +0.0040 to +0.0050; 5 of 5 above 0), against +0.0049 (+0.0040 to +0.0058) with about 1 year of loans. So the Wikipedia pages still help books in general once the model has 5 years of loans.
- **Books with a page** (passed): +0.0065 (+0.0054 to +0.0077) (± 0.0004; +0.0058 to +0.0070; 5 of 5 above 0), against +0.0069 (+0.0056 to +0.0082) with about 1 year. So the Wikipedia pages still help books with a page once the model has 5 years of loans.
- **How much of the Wikipedia gain is left** (no rule): 95% (85% to 106%) for all books, 94% (85% to 104%) for books with a page. Difference of the two gains: -0.0002 (-0.0008 to +0.0003) and -0.0004 (-0.0011 to +0.0003).
- **What 5 years of loans add** (no rule): +0.0131 (+0.0100 to +0.0158) without Wikipedia, +0.0128 (+0.0098 to +0.0156) with it (all books).
- **Best model**: library + 5 years of loans + own and author pages, 0.365 (0.357 to 0.373) on all books and 0.368 (0.359 to 0.376) on books with a page.
- **Books with their own article** (no rule): pages add +0.0132 (+0.0112 to +0.0152) with 5 years of loans, +0.0146 (+0.0123 to +0.0170) with about 1 year.
- **Books with an author article only** (no rule): pages add +0.0034 (+0.0026 to +0.0044) with 5 years of loans, +0.0038 (+0.0027 to +0.0049) with about 1 year.
- **Blind month**: forecasts for September 2026 are frozen and public (20,122 rows, made 2026-11-26 08:27 UTC); they are scored once, when the library releases September and it is downloaded.

## Rules fixed in advance

Holm's correction over the two checks at one-sided 0.05; a check passes if Holm rejects it, its estimate is above 0 and its 95% interval is above 0.

| Check | Gain (95% interval) | One-sided p | Passes Holm | Passed |
| --- | --- | --- | --- | --- |
| Wikipedia pages added on top of 5 years of loans, all books | +0.0046 (+0.0039 to +0.0055) | 0.0005 | yes | **yes** |
| The same, books with a page (ranked among themselves) | +0.0065 (+0.0054 to +0.0077) | 0.0005 | yes | **yes** |

## All books (1,258,807 scored rows)

| Model | Score (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Library, about 1 year of loans (no Wikipedia) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) | 0.333 | 0.348 | 0.361 |
| Library, about 1 year of loans + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) | 0.336 | 0.353 | 0.367 |
| Library + 5 years of loans (no Wikipedia) | 0.360 (0.352 to 0.369) | 0.0004 | 0.375 (0.360 to 0.391) | 0.344 | 0.362 | 0.375 |
| Library + 5 years of loans + own and author pages | 0.365 (0.357 to 0.373) | 0.0002 | 0.379 (0.363 to 0.395) | 0.347 | 0.367 | 0.381 |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Wikipedia pages added, with 5 years of loans | +0.0046 (+0.0039 to +0.0055) | ± 0.0004; +0.0040 to +0.0050; 5 of 5 above 0 | +0.0037 (+0.0029 to +0.0046) | +0.0033 (+0.0022 to +0.0048) | +0.0047 (+0.0038 to +0.0055) | +0.0059 (+0.0048 to +0.0070) |
| Wikipedia pages added, with about 1 year of loans | +0.0049 (+0.0040 to +0.0058) | ± 0.0002; +0.0046 to +0.0051; 5 of 5 above 0 | +0.0038 (+0.0029 to +0.0049) | +0.0038 (+0.0029 to +0.0049) | +0.0049 (+0.0039 to +0.0060) | +0.0059 (+0.0044 to +0.0075) |
| 5 years of loans added, without Wikipedia | +0.0131 (+0.0100 to +0.0158) | ± 0.0005; +0.0126 to +0.0137; 5 of 5 above 0 | +0.0192 (+0.0170 to +0.0210) | +0.0113 (+0.0043 to +0.0169) | +0.0141 (+0.0116 to +0.0165) | +0.0138 (+0.0108 to +0.0166) |
| 5 years of loans added, with Wikipedia | +0.0128 (+0.0098 to +0.0156) | ± 0.0002; +0.0125 to +0.0131; 5 of 5 above 0 | +0.0191 (+0.0169 to +0.0209) | +0.0107 (+0.0041 to +0.0163) | +0.0139 (+0.0115 to +0.0162) | +0.0138 (+0.0109 to +0.0165) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library, about 1 year of loans (no Wikipedia) | Library, about 1 year of loans + own and author pages | Library + 5 years of loans (no Wikipedia) | Library + 5 years of loans + own and author pages |
| --- | --- | --- | --- | --- |
| All | 0.830 (0.806 to 0.852) | 0.837 (0.813 to 0.859) | 0.839 (0.814 to 0.862) | 0.845 (0.823 to 0.867) |
| Early warning | 0.421 (0.388 to 0.456) | 0.408 (0.375 to 0.443) | 0.476 (0.437 to 0.514) | 0.464 (0.424 to 0.505) |

| List comparison | All | Early warning |
| --- | --- | --- |
| Wikipedia pages added, with 5 years of loans | +0.0063 (+0.0020 to +0.0107) | -0.0112 (-0.0207 to -0.0020) |
| Wikipedia pages added, with about 1 year of loans | +0.0075 (+0.0035 to +0.0119) | -0.0139 (-0.0246 to -0.0043) |

## Books with a page (own or author) (782,860 scored rows)

| Model | Score (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Library, about 1 year of loans (no Wikipedia) | 0.348 (0.340 to 0.356) | 0.0003 | 0.358 (0.343 to 0.374) | 0.345 | 0.348 | 0.351 |
| Library, about 1 year of loans + own and author pages | 0.355 (0.347 to 0.363) | 0.0001 | 0.363 (0.349 to 0.378) | 0.350 | 0.355 | 0.359 |
| Library + 5 years of loans (no Wikipedia) | 0.361 (0.353 to 0.369) | 0.0004 | 0.377 (0.363 to 0.392) | 0.355 | 0.362 | 0.366 |
| Library + 5 years of loans + own and author pages | 0.368 (0.359 to 0.376) | 0.0002 | 0.382 (0.368 to 0.397) | 0.361 | 0.369 | 0.373 |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Wikipedia pages added, with 5 years of loans | +0.0065 (+0.0054 to +0.0077) | ± 0.0004; +0.0058 to +0.0070; 5 of 5 above 0 | +0.0049 (+0.0037 to +0.0061) | +0.0055 (+0.0038 to +0.0077) | +0.0068 (+0.0057 to +0.0080) | +0.0072 (+0.0059 to +0.0085) |
| Wikipedia pages added, with about 1 year of loans | +0.0069 (+0.0056 to +0.0082) | ± 0.0003; +0.0066 to +0.0073; 5 of 5 above 0 | +0.0048 (+0.0035 to +0.0061) | +0.0056 (+0.0038 to +0.0075) | +0.0074 (+0.0060 to +0.0090) | +0.0077 (+0.0059 to +0.0097) |
| 5 years of loans added, without Wikipedia | +0.0131 (+0.0100 to +0.0160) | ± 0.0005; +0.0126 to +0.0139; 5 of 5 above 0 | +0.0194 (+0.0169 to +0.0217) | +0.0102 (+0.0040 to +0.0154) | +0.0146 (+0.0116 to +0.0172) | +0.0144 (+0.0105 to +0.0179) |
| 5 years of loans added, with Wikipedia | +0.0127 (+0.0097 to +0.0155) | ± 0.0003; +0.0122 to +0.0130; 5 of 5 above 0 | +0.0195 (+0.0172 to +0.0217) | +0.0101 (+0.0043 to +0.0151) | +0.0140 (+0.0112 to +0.0165) | +0.0139 (+0.0101 to +0.0172) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library, about 1 year of loans (no Wikipedia) | Library, about 1 year of loans + own and author pages | Library + 5 years of loans (no Wikipedia) | Library + 5 years of loans + own and author pages |
| --- | --- | --- | --- | --- |
| All | 0.789 (0.761 to 0.814) | 0.796 (0.768 to 0.822) | 0.794 (0.765 to 0.821) | 0.800 (0.773 to 0.825) |
| Early warning | 0.402 (0.371 to 0.436) | 0.382 (0.352 to 0.415) | 0.445 (0.409 to 0.479) | 0.435 (0.397 to 0.468) |

| List comparison | All | Early warning |
| --- | --- | --- |
| Wikipedia pages added, with 5 years of loans | +0.0060 (+0.0005 to +0.0117) | -0.0099 (-0.0208 to +0.0007) |
| Wikipedia pages added, with about 1 year of loans | +0.0075 (+0.0026 to +0.0119) | -0.0204 (-0.0345 to -0.0085) |

## By kind of page

| Books | Rows | Pages added, 5 years of loans | Pages added, about 1 year | Share left |
| --- | --- | --- | --- | --- |
| Books with their own article | 265,942 | +0.0132 (+0.0112 to +0.0152) | +0.0146 (+0.0123 to +0.0170) | 90% (83% to 98%) |
| Books with an author article only | 516,918 | +0.0034 (+0.0026 to +0.0044) | +0.0038 (+0.0027 to +0.0049) | 91% (77% to 109%) |
| Books with no page | 475,947 | +0.0009 (+0.0003 to +0.0016) | +0.0012 (+0.0002 to +0.0022) | 80% (26% to 235%) |

Books with no page have no page values; a "gain" there comes from the model using the missing pattern, not from page traffic.

## Results by kind of book (all books)

Every group of the 14 families fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books are ranked against each other. "Score" is the score of library + 5 years of loans (no Wikipedia) in that group. Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged.

### Series (asked for by Khant)

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| in a series, known at the time | 120,125 | 78 | 0.316 | +0.0091 (+0.0065 to +0.0118) **found** **differs** | +0.0106 (+0.0076 to +0.0139) **found** |
| no series link known at the time | 165,706 | 78 | 0.367 | +0.0145 (+0.0122 to +0.0168) **found** **differs** | +0.0151 (+0.0125 to +0.0174) **found** |

### Film or TV adaptation (asked for by Khant)

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| film or TV version already out | 55,662 | 78 | 0.332 | +0.0139 (+0.0105 to +0.0175) **found** | +0.0167 (+0.0122 to +0.0217) **found** |
| no film or TV version out yet | 230,169 | 78 | 0.351 | +0.0123 (+0.0104 to +0.0143) **found** | +0.0131 (+0.0108 to +0.0154) **found** |

### Popularity in the year before (asked for by Khant)

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| low | 260,656 | 77 | 0.378 | +0.0044 (+0.0023 to +0.0061) **found** | +0.0053 (+0.0026 to +0.0074) **found** |
| middle | 442,985 | 78 | 0.341 | +0.0041 (+0.0033 to +0.0048) **found** | +0.0048 (+0.0038 to +0.0059) **found** |
| high | 555,166 | 78 | 0.358 | +0.0045 (+0.0036 to +0.0055) **found** | +0.0044 (+0.0031 to +0.0056) **found** |

### Fiction or nonfiction

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| fiction | 827,393 | 78 | 0.357 | +0.0053 (+0.0044 to +0.0062) **found** **differs** | +0.0055 (+0.0044 to +0.0065) **found** **differs** |
| nonfiction | 412,596 | 78 | 0.365 | +0.0031 (+0.0022 to +0.0040) **found** **differs** | +0.0033 (+0.0025 to +0.0041) **found** **differs** |
| other (mixed or unknown) | 18,818 | 78 | 0.353 | +0.0075 (+0.0036 to +0.0114) **found** | +0.0127 (+0.0070 to +0.0182) **found** **differs** |

### Audience

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| adult | 839,677 | 78 | 0.378 | +0.0063 (+0.0052 to +0.0075) **found** **differs** | +0.0063 (+0.0053 to +0.0072) **found** **differs** |
| children | 360,814 | 78 | 0.309 | +0.0008 (-0.0002 to +0.0017) **differs** | +0.0018 (+0.0002 to +0.0035) **found** **differs** |
| young adult | 58,316 | 78 | 0.325 | +0.0074 (+0.0045 to +0.0103) **found** | +0.0065 (+0.0034 to +0.0099) **found** |

### Format

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| audiobook | 340,064 | 78 | 0.375 | +0.0059 (+0.0048 to +0.0070) **found** **differs** | +0.0059 (+0.0044 to +0.0075) **found** |
| ebook | 446,291 | 78 | 0.362 | +0.0047 (+0.0038 to +0.0055) **found** | +0.0049 (+0.0039 to +0.0060) **found** |
| print | 472,452 | 78 | 0.344 | +0.0033 (+0.0022 to +0.0048) **found** **differs** | +0.0038 (+0.0029 to +0.0049) **found** **differs** |

### Time since first Seattle loan

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| under 1 year | 199,907 | 78 | 0.429 | +0.0052 (+0.0041 to +0.0065) **found** | +0.0042 (+0.0030 to +0.0054) **found** |
| 1 to 5 years | 548,026 | 78 | 0.340 | +0.0033 (+0.0025 to +0.0043) **found** **differs** | +0.0038 (+0.0029 to +0.0047) **found** **differs** |
| 5 years or more | 510,874 | 78 | 0.329 | +0.0053 (+0.0044 to +0.0061) **found** **differs** | +0.0060 (+0.0045 to +0.0075) **found** **differs** |

### Author's earlier Seattle books

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| no | 360,676 | 78 | 0.366 | +0.0040 (+0.0030 to +0.0051) **found** | +0.0047 (+0.0034 to +0.0060) **found** |
| unknown | 7,372 | 78 | 0.340 | +0.0020 (-0.0010 to +0.0054) | -0.0001 (-0.0026 to +0.0023) **differs** |
| yes | 890,709 | 78 | 0.358 | +0.0049 (+0.0041 to +0.0058) **found** | +0.0049 (+0.0040 to +0.0058) **found** |

### Own Wikipedia article

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| author article only | 516,918 | 78 | 0.366 | +0.0034 (+0.0026 to +0.0044) **found** **differs** | +0.0038 (+0.0027 to +0.0049) **found** |
| book article | 265,942 | 78 | 0.342 | +0.0132 (+0.0112 to +0.0152) **found** **differs** | +0.0146 (+0.0123 to +0.0170) **found** **differs** |
| neither | 475,947 | 78 | 0.360 | +0.0009 (+0.0003 to +0.0016) **found** **differs** | +0.0012 (+0.0002 to +0.0022) **found** **differs** |

### Award

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| award won by then | 34,142 | 78 | 0.325 | +0.0169 (+0.0133 to +0.0204) **found** **differs** | +0.0210 (+0.0163 to +0.0257) **found** **differs** |
| no award known by then | 251,689 | 78 | 0.351 | +0.0120 (+0.0098 to +0.0140) **found** **differs** | +0.0125 (+0.0101 to +0.0149) **found** **differs** |

### Translated

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| translated | 17,953 | 78 | 0.326 | +0.0136 (+0.0077 to +0.0195) **found** | +0.0165 (+0.0090 to +0.0245) **found** |
| written in English | 254,007 | 78 | 0.348 | +0.0122 (+0.0102 to +0.0141) **found** | +0.0132 (+0.0110 to +0.0154) **found** |

### Public-domain classic

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| 1930 or later | 242,178 | 78 | 0.339 | +0.0126 (+0.0105 to +0.0147) **found** | +0.0140 (+0.0115 to +0.0165) **found** |
| first published before 1930 | 13,333 | 78 | 0.347 | +0.0067 (+0.0009 to +0.0123) **found** | +0.0086 (+0.0019 to +0.0152) **found** |

### Genre (broad theme)

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| B01 Magic, myth and the supernatural | 117,139 | 78 | 0.322 | +0.0044 (+0.0028 to +0.0059) **found** | +0.0051 (+0.0033 to +0.0070) **found** |
| B02 Gender, sexuality and relationships | 106,306 | 78 | 0.381 | +0.0064 (+0.0047 to +0.0082) **found** **differs** | +0.0055 (+0.0038 to +0.0072) **found** |
| B03 Religion and spirituality | 29,838 | 78 | 0.349 | +0.0044 (+0.0018 to +0.0073) **found** | +0.0068 (+0.0034 to +0.0106) **found** |
| B04 Science, technology and learning | 64,777 | 78 | 0.334 | +0.0054 (+0.0026 to +0.0086) **found** | +0.0060 (+0.0033 to +0.0089) **found** |
| B05 Race, ethnicity and migration | 49,860 | 78 | 0.386 | +0.0072 (+0.0050 to +0.0095) **found** **differs** | +0.0065 (+0.0043 to +0.0089) **found** |
| B06 Arts, media and entertainment | 70,364 | 78 | 0.373 | +0.0047 (+0.0028 to +0.0065) **found** | +0.0061 (+0.0042 to +0.0081) **found** |
| B07 Childhood, family and growing up | 113,354 | 78 | 0.366 | +0.0044 (+0.0029 to +0.0060) **found** | +0.0050 (+0.0032 to +0.0065) **found** |
| B08 War, conflict and history | 74,991 | 78 | 0.365 | +0.0071 (+0.0047 to +0.0095) **found** **differs** | +0.0076 (+0.0053 to +0.0097) **found** **differs** |
| B09 Nature, places and the environment | 96,529 | 78 | 0.364 | +0.0051 (+0.0033 to +0.0069) **found** | +0.0063 (+0.0041 to +0.0085) **found** |
| B10 Work, business and money | 34,342 | 78 | 0.338 | +0.0022 (-0.0005 to +0.0047) | +0.0038 (+0.0006 to +0.0071) **found** |
| B11 Food, home and holidays | 51,305 | 78 | 0.419 | +0.0020 (+0.0002 to +0.0037) **found** **differs** | +0.0043 (+0.0017 to +0.0068) **found** |
| B12 Violence, trauma, death and grief | 47,097 | 78 | 0.381 | +0.0059 (+0.0040 to +0.0079) **found** | +0.0048 (+0.0026 to +0.0069) **found** |
| B13 Politics, society and justice | 34,610 | 78 | 0.407 | +0.0068 (+0.0041 to +0.0100) **found** | +0.0068 (+0.0035 to +0.0105) **found** |
| B14 Mind, self and philosophy | 72,637 | 78 | 0.344 | +0.0035 (+0.0017 to +0.0054) **found** | +0.0035 (+0.0015 to +0.0057) **found** |
| B15 Health, illness and addiction | 28,119 | 78 | 0.335 | +0.0064 (+0.0030 to +0.0099) **found** | +0.0065 (+0.0022 to +0.0109) **found** |
| B16 Animals | 73,393 | 78 | 0.320 | +0.0021 (+0.0002 to +0.0040) **found** **differs** | +0.0034 (+0.0004 to +0.0067) **found** |
| B17 Sports, games and fitness | 18,180 | 78 | 0.333 | -0.0009 (-0.0044 to +0.0026) **differs** | -0.0045 (-0.0089 to -0.0002) **differs** |
| B18 Space and the universe | 14,185 | 78 | 0.302 | +0.0069 (+0.0012 to +0.0126) **found** | +0.0079 (+0.0021 to +0.0135) **found** |
| B19 Crime, police and law | 51,005 | 78 | 0.359 | +0.0072 (+0.0051 to +0.0094) **found** **differs** | +0.0078 (+0.0047 to +0.0111) **found** |
| no theme | 110,776 | 78 | 0.348 | +0.0044 (+0.0028 to +0.0062) **found** | +0.0045 (+0.0027 to +0.0065) **found** |

### Has a theme

| Group | Rows | Months | Score | Pages added, 5 years of loans | Pages added, about 1 year |
| --- | --- | --- | --- | --- | --- |
| no | 162,732 | 78 | 0.356 | +0.0045 (+0.0035 to +0.0058) **found** | +0.0048 (+0.0033 to +0.0064) **found** |
| yes | 1,096,075 | 78 | 0.361 | +0.0046 (+0.0038 to +0.0055) **found** | +0.0048 (+0.0039 to +0.0057) **found** |

## Data and checks

- The 5 years of loans are addendum o's 35 plain features, built from the same monthly loan series; a refit of the library model reproduces its stored predictions exactly, and addendum o's +0.0128 for the 5 years is reproduced.
- Books with a page: the row has the book's own article or the author's article (as in the page-books scores of 26 November).
- Blind month: 20,122 rows at origin August 2026, frozen 2026-11-26 08:27 UTC; file `prereg/blind_q/forecasts_origin_2026-08.csv`, SHA-256 c518491861ce531c... in `prereg/README.md`; the library + 5 years + pages forecasts of the same rows are in `prereg/blind_o/`. Check: the library model's first-seed forecast equals the one frozen for the earlier blind test.

## Limits

- The 5 years are one fair plain way to give the model older loans, not every way; a longer or different history could shrink the Wikipedia gain further.
- The question was asked after addendum o's results were seen; the rules were fixed before this model was fitted.
- New books have no loan history and are not in these rows; their test is separate.
- The blind month is one month: it adds to the backtest, it does not replace it.
- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.
