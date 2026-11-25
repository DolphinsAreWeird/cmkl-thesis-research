# More online signals for single books, better models, and results by kind of book

Made by `code/main_study/wiki_led/n_more_signals/n50_score.py` and `n60_report.py` on 2026-11-26 01:24 (+07:00). Settings fixed in advance in `prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json` (made public on GitHub, pull request 35, at 09:38 UTC on 25 November 2026, before any step ran). Choices and fixes made later are logged with times in `prereg/DEVIATIONS.md`, section "Addendum n".

## The question

The single-book models predict which books will rise in loans next month at the Seattle Public Library. Until now they used the library's loan history and two Wikipedia pages: the book's own article and its author's. Theme pages added almost nothing (the previous report). This report asks three things, on the same books and months as the thesis's main table:

1. **Other online signals.** Do any of these add to the library model with the own and author pages: New York Times bestseller lists; the Wikipedia pages of the book's film and TV versions; Wikipedia pages linked to the book in Wikidata (subjects, places, characters, periods); Open Library reading logs; Amazon reviews?
2. **Better use of the pages already in the model.** Does the gain come from the book's own page or the author's? Do models fitted separately for each kind of book do better than one model for all? Does a pretrained Transformer (Chronos-2) forecast better than the boosted trees, and does it help as an extra input?
3. **For which kinds of book** does each signal help (the 14 families of the previous report: series, film or TV version, popularity, fiction, audience, format, age, author's earlier books, own article, award, translated, classic, genre, theme)?

## How to read the numbers

- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; 0 is chance, 1 is perfect), averaged over the 78 months from February 2019 to August 2026. Models only ever learn from earlier years.
- **Gain**: the score with the added signal minus the score without it, on the same rows. 0.001 is small; the own and author pages together add about 0.005.
- **Five seeds**: every boosted-tree model was fitted five times with different random seeds; a value is the mean of the five. "±" is their standard deviation, then the smallest and largest, and how many were above 0. The Transformer has no random part, so it has one run.
- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months, with the five-seed mean recomputed in each redraw.
- **Placebos**: for each new signal, the same model given the same book's signal with its dates moved 12 months later. For the own and author pages, the same model given another book's (or author's) article with similar traffic. A real signal should beat its placebo.

## In short

- **Bestseller lists** passed the rule fixed in advance. Added to the library model with the own and author pages, they changed the score by +0.0009 (+0.0006 to +0.0012) (five seeds ± 0.0000; +0.0008 to +0.0009; 5 of 5 above 0); real dates minus dates moved 12 months: +0.0006 (+0.0004 to +0.0010).
- **Film and TV pages** did not pass the rule fixed in advance. Added to the library model with the own and author pages, they changed the score by -0.0001 (-0.0002 to +0.0001) (five seeds ± 0.0002; -0.0004 to +0.0002; 2 of 5 above 0); real dates minus dates moved 12 months: -0.0001 (-0.0002 to -0.0000). Reason: the gain was not clearly above zero after the correction for testing five signals; the same signal with its dates moved 12 months did about as well, so the gain cannot be told apart from what the signal says about the book in general.
- **Linked pages** did not pass the rule fixed in advance. Added to the library model with the own and author pages, they changed the score by +0.0000 (-0.0002 to +0.0002) (five seeds ± 0.0002; -0.0002 to +0.0002; 2 of 5 above 0); real dates minus dates moved 12 months: +0.0000 (-0.0001 to +0.0001). Reason: the gain was not clearly above zero after the correction for testing five signals; the same signal with its dates moved 12 months did about as well, so the gain cannot be told apart from what the signal says about the book in general.
- **Reading logs** did not pass the rule fixed in advance. Added to the library model with the own and author pages, they changed the score by +0.0001 (-0.0001 to +0.0003) (five seeds ± 0.0002; -0.0002 to +0.0003; 4 of 5 above 0); real dates minus dates moved 12 months: -0.0000 (-0.0002 to +0.0001). Reason: the gain was not clearly above zero after the correction for testing five signals; the same signal with its dates moved 12 months did about as well, so the gain cannot be told apart from what the signal says about the book in general.
- **Amazon reviews** passed the rule fixed in advance. Added to the library model with the own and author pages, they changed the score by +0.0032 (+0.0026 to +0.0039) (five seeds ± 0.0005; +0.0023 to +0.0037; 5 of 5 above 0); real dates minus dates moved 12 months: +0.0018 (+0.0012 to +0.0025). Scored only up to April 2023, the last month with full review counts.
- **All four signals in hand together** (no pass rule): +0.0007 (+0.0004 to +0.0011); against the same four with dates moved 12 months: +0.0007 (+0.0005 to +0.0009).
- **Book page or author page?** Both carry part of the gain. The book's own page alone added +0.0025 (+0.0020 to +0.0031) to the library model and the author's page alone +0.0033 (+0.0025 to +0.0041); together +0.0049 (+0.0040 to +0.0058). Each beat another article of similar traffic (book +0.0016 (+0.0012 to +0.0021), author +0.0031 (+0.0025 to +0.0038)), so both passed by the rule fixed in advance (book: passed; author: passed). The author's page adds +0.0023 (+0.0018 to +0.0028) beyond the book's page, and the book's page +0.0015 (+0.0012 to +0.0019) beyond the author's. The author page reaches more books (about three in five scored rows have one, against one in five for a book page), which is much of why its whole-set gain is larger.
- **One model per kind of book** (no pass rule): of 24 group comparisons, 5 were better and 8 worse than one model for all books after the correction. Better: print (library model, +0.0032); print (library + own pages, +0.0036); high popularity third (library model, +0.0023); high popularity third (library + own pages, +0.0017); low popularity third (library model, +0.0039). Worse: fiction (library + own pages, -0.0007); other (mixed or unknown) (library model, -0.0274); other (mixed or unknown) (library + own pages, -0.0362); audiobook (library model, -0.0063); audiobook (library + own pages, -0.0083); author article only (library + own pages, -0.0015); book article (library + own pages, -0.0027); neither (library + own pages, -0.0011). Separate models mostly shrank the own-page gain rather than raising it.
- **Pretrained Transformer (Chronos-2, no training on these data)** (no pass rule): the Transformer on loan history alone scored 0.307 (0.295 to 0.319) against 0.347 (0.340 to 0.355) for the boosted-tree library model (-0.0402 (-0.0475 to -0.0337)); with the own and author pages as extra inputs it scored 0.310 (0.298 to 0.322) against 0.352 (0.344 to 0.360) (-0.0420 (-0.0488 to -0.0360)); the pages changed the Transformer's score by +0.0031 (+0.0024 to +0.0037); given to the boosted trees as two extra inputs, its forecasts changed the score by +0.0091 (+0.0071 to +0.0110).
- **By kind of book, bestseller lists**: 53 of 53 groups were large enough to judge; a gain was found in 34 and a difference from the other books in 7 after correcting for the number of groups.
- **By kind of book, film and tv pages**: 53 of 53 groups were large enough to judge; a gain was found in 0 and a difference from the other books in 0 after correcting for the number of groups.
- **By kind of book, linked pages**: 53 of 53 groups were large enough to judge; a gain was found in 0 and a difference from the other books in 0 after correcting for the number of groups.
- **By kind of book, reading logs**: 53 of 53 groups were large enough to judge; a gain was found in 11 and a difference from the other books in 4 after correcting for the number of groups.
- **By kind of book, all four in hand**: 53 of 53 groups were large enough to judge; a gain was found in 22 and a difference from the other books in 9 after correcting for the number of groups.
- **By kind of book, amazon reviews**: 53 of 53 groups were large enough to judge; a gain was found in 28 and a difference from the other books in 7 after correcting for the number of groups.

## Rules fixed in advance

**New signals.** A signal passes only if both hold: (1) its gain over the library model with the own and author pages has a one-sided p that passes Holm's correction over the five signals, with an estimate above zero; (2) it beats the same signal with its dates moved 12 months (95% interval above zero). A signal that could not be built counts as not passing and keeps its place in the correction.

| Signal | (1) Gain over library + own pages | One-sided p | Passes Holm | (2) Real minus moved dates | Passed |
| --- | --- | --- | --- | --- | --- |
| Bestseller lists | +0.0009 (+0.0006 to +0.0012) | 0.0005 | yes | +0.0006 (+0.0004 to +0.0010) | **yes** |
| Film and TV pages | -0.0001 (-0.0002 to +0.0001) | 0.7591 | no | -0.0001 (-0.0002 to -0.0000) | **no** |
| Linked pages | +0.0000 (-0.0002 to +0.0002) | 0.4668 | no | +0.0000 (-0.0001 to +0.0001) | **no** |
| Reading logs | +0.0001 (-0.0001 to +0.0003) | 0.0645 | no | -0.0000 (-0.0002 to +0.0001) | **no** |
| Amazon reviews | +0.0032 (+0.0026 to +0.0039) | 0.0005 | yes | +0.0018 (+0.0012 to +0.0025) | **yes** |

**Book page against author page.** A page passes if its gain over the library model passes Holm's correction over the two pages (one-sided, 0.05, estimate above zero) and it beats another article of similar traffic (95% interval above zero).

| Page | Gain over library model | One-sided p | Passes Holm | Real minus another article | Passed |
| --- | --- | --- | --- | --- | --- |
| Book's own page | +0.0025 (+0.0020 to +0.0031) | 0.0005 | yes | +0.0016 (+0.0012 to +0.0021) | **yes** |
| Author's page | +0.0033 (+0.0025 to +0.0041) | 0.0005 | yes | +0.0031 (+0.0025 to +0.0038) | **yes** |

The models per kind of book and the Transformer had no pass rule: they are reported with intervals only.

## New York Times bestseller lists

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + own pages + bestseller lists | 0.353 (0.345 to 0.361) | 0.0001 | 0.360 (0.345 to 0.377) |
| Bestseller lists alone (with the format) | 0.030 (0.027 to 0.034) | 0.0002 | 0.031 (0.025 to 0.035) |
| Library + own pages + bestseller lists, dates moved 12 months (placebo) | 0.352 (0.345 to 0.360) | 0.0003 | 0.360 (0.345 to 0.377) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | +0.0009 (+0.0006 to +0.0012) | ± 0.0000; +0.0008 to +0.0009; 5 of 5 above 0 | +0.0005 (+0.0001 to +0.0009) | +0.0009 (+0.0006 to +0.0014) | +0.0003 (+0.0000 to +0.0007) | +0.0013 (+0.0008 to +0.0018) |
| Real minus dates moved 12 months | +0.0006 (+0.0004 to +0.0010) | ± 0.0002; +0.0004 to +0.0010; 5 of 5 above 0 | +0.0002 (+0.0000 to +0.0005) | +0.0007 (+0.0003 to +0.0011) | +0.0002 (-0.0001 to +0.0005) | +0.0011 (+0.0006 to +0.0017) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.835 (0.811 to 0.858) | -0.0017 (-0.0044 to +0.0012) |
| Early warning | 0.408 (0.375 to 0.443) | 0.399 (0.365 to 0.435) | -0.0087 (-0.0131 to -0.0045) |

## Wikipedia pages of the book's film and TV versions

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + own pages + film and tv pages | 0.352 (0.345 to 0.360) | 0.0002 | 0.360 (0.344 to 0.376) |
| Film and TV pages alone (with the format) | 0.032 (0.029 to 0.035) | 0.0002 | 0.034 (0.029 to 0.038) |
| Library + own pages + film and tv pages, dates moved 12 months (placebo) | 0.352 (0.345 to 0.360) | 0.0002 | 0.360 (0.344 to 0.376) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | -0.0001 (-0.0002 to +0.0001) | ± 0.0002; -0.0004 to +0.0002; 2 of 5 above 0 | -0.0001 (-0.0004 to +0.0001) | -0.0003 (-0.0006 to -0.0000) | -0.0001 (-0.0003 to +0.0002) | +0.0001 (-0.0001 to +0.0004) |
| Real minus dates moved 12 months | -0.0001 (-0.0002 to -0.0000) | ± 0.0002; -0.0002 to +0.0002; 2 of 5 above 0 | -0.0001 (-0.0002 to +0.0001) | -0.0001 (-0.0004 to +0.0001) | -0.0001 (-0.0002 to +0.0000) | -0.0001 (-0.0002 to +0.0001) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.835 (0.811 to 0.858) | -0.0019 (-0.0047 to +0.0010) |
| Early warning | 0.408 (0.375 to 0.443) | 0.406 (0.375 to 0.440) | -0.0018 (-0.0053 to +0.0018) |

## Wikipedia pages linked to the book in Wikidata (its subjects, places, characters and periods)

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + own pages + linked pages | 0.352 (0.344 to 0.360) | 0.0002 | 0.360 (0.344 to 0.377) |
| Linked pages alone (with the format) | 0.038 (0.034 to 0.041) | 0.0002 | 0.038 (0.032 to 0.044) |
| Library + own pages + linked pages, dates moved 12 months (placebo) | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | +0.0000 (-0.0002 to +0.0002) | ± 0.0002; -0.0002 to +0.0002; 2 of 5 above 0 | +0.0001 (-0.0001 to +0.0005) | -0.0001 (-0.0004 to +0.0002) | -0.0000 (-0.0003 to +0.0002) | +0.0001 (-0.0001 to +0.0005) |
| Real minus dates moved 12 months | +0.0000 (-0.0001 to +0.0001) | ± 0.0001; -0.0001 to +0.0001; 3 of 5 above 0 | +0.0001 (-0.0001 to +0.0003) | -0.0001 (-0.0002 to +0.0001) | +0.0000 (-0.0001 to +0.0002) | +0.0001 (-0.0001 to +0.0003) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.837 (0.813 to 0.859) | -0.0003 (-0.0028 to +0.0024) |
| Early warning | 0.408 (0.375 to 0.443) | 0.403 (0.371 to 0.439) | -0.0042 (-0.0081 to -0.0002) |

## Open Library reading logs (want to read, reading, read)

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + own pages + reading logs | 0.352 (0.345 to 0.360) | 0.0001 | 0.360 (0.345 to 0.377) |
| Reading logs alone (with the format) | 0.050 (0.045 to 0.054) | 0.0001 | 0.052 (0.045 to 0.057) |
| Library + own pages + reading logs, dates moved 12 months (placebo) | 0.352 (0.345 to 0.360) | 0.0001 | 0.360 (0.345 to 0.377) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | +0.0001 (-0.0001 to +0.0003) | ± 0.0002; -0.0002 to +0.0003; 4 of 5 above 0 | +0.0003 (+0.0000 to +0.0005) | +0.0000 (-0.0004 to +0.0003) | -0.0000 (-0.0003 to +0.0002) | +0.0005 (+0.0002 to +0.0007) |
| Real minus dates moved 12 months | -0.0000 (-0.0002 to +0.0001) | ± 0.0002; -0.0003 to +0.0001; 2 of 5 above 0 | +0.0001 (-0.0001 to +0.0002) | -0.0002 (-0.0005 to +0.0000) | -0.0001 (-0.0003 to +0.0001) | +0.0002 (+0.0000 to +0.0004) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.836 (0.812 to 0.858) | -0.0015 (-0.0042 to +0.0012) |
| Early warning | 0.408 (0.375 to 0.443) | 0.403 (0.371 to 0.438) | -0.0047 (-0.0087 to -0.0009) |

## Amazon reviews (Amazon Reviews 2023)

Scored on the rows whose origin month is on or before April 2023, the last month with full review counts; the library and own-page models are rescored on the same rows.

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model (loan history and calendar month) | 0.343 (0.334 to 0.353) | 0.0002 | no rows |
| Library + own and author pages | 0.348 (0.339 to 0.358) | 0.0002 | no rows |
| Library + own pages + amazon reviews | 0.351 (0.342 to 0.362) | 0.0004 | no rows |
| Amazon reviews alone (with the format) | 0.100 (0.089 to 0.109) | 0.0003 | no rows |
| Library + own pages + amazon reviews, dates moved 12 months (placebo) | 0.350 (0.340 to 0.360) | 0.0001 | no rows |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | +0.0032 (+0.0026 to +0.0039) | ± 0.0005; +0.0023 to +0.0037; 5 of 5 above 0 | no rows | +0.0038 (+0.0030 to +0.0046) | +0.0020 (+0.0012 to +0.0030) | +0.0037 (+0.0025 to +0.0053) |
| Real minus dates moved 12 months | +0.0018 (+0.0012 to +0.0025) | ± 0.0004; +0.0013 to +0.0023; 5 of 5 above 0 | no rows | +0.0023 (+0.0015 to +0.0031) | +0.0009 (+0.0001 to +0.0018) | +0.0022 (+0.0009 to +0.0037) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.814 (0.781 to 0.843) | 0.803 (0.768 to 0.834) | -0.0113 (-0.0190 to -0.0052) |
| Early warning | 0.380 (0.341 to 0.420) | 0.361 (0.325 to 0.399) | -0.0193 (-0.0269 to -0.0116) |

## The four signals in hand together (lists, film and TV pages, linked pages, reading logs)

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library + own and author pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + own pages + all four in hand | 0.353 (0.345 to 0.361) | 0.0003 | 0.360 (0.345 to 0.377) |
| ... all four, dates moved 12 months (placebo) | 0.352 (0.344 to 0.360) | 0.0002 | 0.360 (0.345 to 0.376) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Gain over library + own pages | +0.0007 (+0.0004 to +0.0011) | ± 0.0002; +0.0003 to +0.0008; 5 of 5 above 0 | +0.0004 (+0.0001 to +0.0009) | +0.0004 (+0.0000 to +0.0007) | +0.0001 (-0.0001 to +0.0004) | +0.0016 (+0.0009 to +0.0024) |
| Real minus dates moved 12 months | +0.0007 (+0.0005 to +0.0009) | ± 0.0003; +0.0003 to +0.0011; 5 of 5 above 0 | +0.0004 (+0.0002 to +0.0007) | +0.0004 (+0.0002 to +0.0007) | +0.0002 (+0.0000 to +0.0005) | +0.0014 (+0.0009 to +0.0020) |

Monthly top-20 lists (share of the 20 books with the highest predicted change whose loans rose by half or more next month; the early-warning list keeps only books that had not already risen):

| List | Library + own pages | With the signal | Gain |
| --- | --- | --- | --- |
| All books | 0.837 (0.813 to 0.859) | 0.834 (0.808 to 0.857) | -0.0030 (-0.0067 to +0.0006) |
| Early warning | 0.408 (0.375 to 0.443) | 0.399 (0.367 to 0.434) | -0.0088 (-0.0142 to -0.0034) |

## The book's own page against the author's page

Book articles: 3,892; author articles: 10,356; every one got a placebo article. Share of scored rows with a book-page value 20.8%, with an author-page value 61.2% (the placebo has the same missing pattern).

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 |
| --- | --- | --- | --- |
| Library model | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) |
| Library + both pages | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) |
| Library + book's own page | 0.350 (0.342 to 0.358) | 0.0001 | 0.358 (0.343 to 0.374) |
| Library + author's page | 0.351 (0.343 to 0.359) | 0.0002 | 0.359 (0.343 to 0.375) |
| Library + another book's page of similar traffic (placebo) | 0.348 (0.340 to 0.356) | 0.0002 | 0.357 (0.342 to 0.373) |
| Library + another author's page of similar traffic (placebo) | 0.347 (0.340 to 0.356) | 0.0001 | 0.357 (0.341 to 0.373) |

| Comparison | 2019 to 2026 | Five seeds | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Book page added to the library model | +0.0025 (+0.0020 to +0.0031) | ± 0.0002; +0.0024 to +0.0028; 5 of 5 above 0 | +0.0021 (+0.0013 to +0.0029) | +0.0016 (+0.0010 to +0.0021) | +0.0030 (+0.0022 to +0.0038) | +0.0031 (+0.0022 to +0.0042) |
| Author page added to the library model | +0.0033 (+0.0025 to +0.0041) | ± 0.0003; +0.0029 to +0.0036; 5 of 5 above 0 | +0.0025 (+0.0016 to +0.0036) | +0.0029 (+0.0022 to +0.0037) | +0.0031 (+0.0021 to +0.0042) | +0.0039 (+0.0026 to +0.0051) |
| Book page: real minus another book's page | +0.0016 (+0.0012 to +0.0021) | ± 0.0002; +0.0014 to +0.0020; 5 of 5 above 0 | +0.0012 (+0.0008 to +0.0016) | +0.0014 (+0.0009 to +0.0019) | +0.0017 (+0.0013 to +0.0022) | +0.0018 (+0.0011 to +0.0025) |
| Author page: real minus another author's page | +0.0031 (+0.0025 to +0.0038) | ± 0.0002; +0.0030 to +0.0033; 5 of 5 above 0 | +0.0021 (+0.0016 to +0.0026) | +0.0020 (+0.0014 to +0.0029) | +0.0033 (+0.0026 to +0.0040) | +0.0041 (+0.0031 to +0.0051) |
| Author page beyond the book page | +0.0023 (+0.0018 to +0.0028) | ± 0.0002; +0.0022 to +0.0026; 5 of 5 above 0 | +0.0017 (+0.0010 to +0.0025) | +0.0023 (+0.0015 to +0.0032) | +0.0019 (+0.0013 to +0.0026) | +0.0027 (+0.0019 to +0.0036) |
| Book page beyond the author page | +0.0015 (+0.0012 to +0.0019) | ± 0.0002; +0.0014 to +0.0018; 5 of 5 above 0 | +0.0013 (+0.0008 to +0.0019) | +0.0009 (+0.0005 to +0.0013) | +0.0017 (+0.0013 to +0.0022) | +0.0020 (+0.0014 to +0.0027) |
| Both pages added to the library model (published result) | +0.0049 (+0.0040 to +0.0058) | ± 0.0002; +0.0046 to +0.0051; 5 of 5 above 0 | +0.0038 (+0.0029 to +0.0049) | +0.0038 (+0.0029 to +0.0049) | +0.0049 (+0.0039 to +0.0060) | +0.0059 (+0.0044 to +0.0075) |

By which article the book has (marks as in "Results by kind of book" below):

| Group | Rows | Score (library) | Book page | Author page |
| --- | --- | --- | --- | --- |
| book article | 265,942 | 0.326 | +0.0135 (+0.0118 to +0.0153) **found** **differs** | +0.0083 (+0.0066 to +0.0101) **found** **differs** |
| author article only | 516,918 | 0.354 | -0.0001 (-0.0005 to +0.0003) **differs** | +0.0030 (+0.0017 to +0.0043) **found** |
| neither | 475,947 | 0.347 | +0.0002 (-0.0002 to +0.0008) **differs** | +0.0013 (+0.0003 to +0.0023) **found** **differs** |

Books with neither article have no page values, so any gain there comes from the model learning how books without articles behave.

## One model per kind of book

For four families, the library model and the library + own pages model were fitted separately within each group (training on that group's earlier rows only) and compared with the single model fitted on all books, on the group's own rows. Every group-year had at least 1,000 training rows. Marked **bold** where the Benjamini-Hochberg adjusted p is below 0.05 (within each comparison over all groups).

| Family | Group | Rows | Library: separate minus single | Library + own pages: separate minus single | Own-page gain, single model | Own-page gain, separate models | Difference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fiction or nonfiction | fiction | 827,393 | -0.0002 (-0.0007 to +0.0002) | **-0.0007 (-0.0011 to -0.0002)** | +0.0055 | +0.0050 | **-0.0004 (-0.0007 to -0.0001)** |
| Fiction or nonfiction | nonfiction | 412,596 | -0.0005 (-0.0013 to +0.0003) | -0.0001 (-0.0011 to +0.0009) | +0.0033 | +0.0037 | +0.0004 (-0.0001 to +0.0011) |
| Fiction or nonfiction | other (mixed or unknown) | 18,818 | **-0.0274 (-0.0383 to -0.0165)** | **-0.0362 (-0.0463 to -0.0267)** | +0.0127 | +0.0038 | -0.0089 (-0.0177 to -0.0007) |
| Format | audiobook | 340,064 | **-0.0063 (-0.0093 to -0.0036)** | **-0.0083 (-0.0120 to -0.0049)** | +0.0059 | +0.0039 | **-0.0020 (-0.0031 to -0.0009)** |
| Format | ebook | 446,291 | -0.0005 (-0.0018 to +0.0006) | -0.0011 (-0.0025 to +0.0001) | +0.0049 | +0.0043 | -0.0006 (-0.0011 to -0.0000) |
| Format | print | 472,452 | **+0.0032 (+0.0022 to +0.0042)** | **+0.0036 (+0.0027 to +0.0046)** | +0.0038 | +0.0042 | +0.0004 (-0.0003 to +0.0011) |
| Own Wikipedia article | author article only | 516,918 | -0.0007 (-0.0016 to +0.0004) | **-0.0015 (-0.0022 to -0.0007)** | +0.0038 | +0.0030 | **-0.0008 (-0.0014 to -0.0002)** |
| Own Wikipedia article | book article | 265,942 | +0.0011 (-0.0007 to +0.0030) | **-0.0027 (-0.0047 to -0.0007)** | +0.0146 | +0.0109 | **-0.0038 (-0.0053 to -0.0024)** |
| Own Wikipedia article | neither | 475,947 | +0.0000 (-0.0013 to +0.0014) | **-0.0011 (-0.0021 to -0.0003)** | +0.0012 | +0.0000 | **-0.0012 (-0.0022 to -0.0002)** |
| Popularity in the year before | high | 556,811 | **+0.0023 (+0.0011 to +0.0034)** | **+0.0017 (+0.0005 to +0.0029)** | +0.0044 | +0.0039 | **-0.0006 (-0.0010 to -0.0001)** |
| Popularity in the year before | low | 259,396 | **+0.0039 (+0.0015 to +0.0062)** | +0.0017 (-0.0007 to +0.0040) | +0.0053 | +0.0031 | **-0.0022 (-0.0035 to -0.0007)** |
| Popularity in the year before | middle | 442,600 | -0.0009 (-0.0033 to +0.0011) | -0.0012 (-0.0033 to +0.0008) | +0.0048 | +0.0045 | -0.0003 (-0.0007 to +0.0003) |

## A pretrained Transformer (Chronos-2)

Chronos-2 (amazon/chronos-2, the version of the theme benchmark) was used as released, with no training on these data, on the computer's processor. For each book, format and month it saw up to 60 months of log loans and forecast the next month; its predicted change is the median forecast minus the log of the last six months' average, as for the other models. The version with pages also saw the monthly view share of the book's own and author's articles. It has no random part, so the "± across seeds" column is empty for it.

| Model | Score 2019 to 2026 (95% interval) | ± across seeds | Score 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- | --- |
| Library model (boosted trees) | 0.347 (0.340 to 0.355) | 0.0002 | 0.356 (0.340 to 0.373) | 0.333 | 0.348 | 0.361 |
| Library + own and author pages (boosted trees) | 0.352 (0.344 to 0.360) | 0.0001 | 0.360 (0.344 to 0.376) | 0.336 | 0.353 | 0.367 |
| Transformer, loan history only | 0.307 (0.295 to 0.319) |  | 0.318 (0.304 to 0.333) | 0.283 | 0.311 | 0.327 |
| Transformer, loan history + own and author page views | 0.310 (0.298 to 0.322) |  | 0.322 (0.307 to 0.337) | 0.288 | 0.314 | 0.329 |
| Boosted trees: library + own pages + the two Transformer forecasts | 0.361 (0.353 to 0.370) | 0.0001 | 0.372 (0.356 to 0.387) | 0.346 | 0.361 | 0.377 |

| Comparison | 2019 to 2026 | 2024 to 2026 | Print | Ebook | Audiobook |
| --- | --- | --- | --- | --- | --- |
| Transformer minus library model | -0.0402 (-0.0475 to -0.0337) | -0.0377 (-0.0447 to -0.0311) | -0.0497 (-0.0648 to -0.0358) | -0.0368 (-0.0410 to -0.0324) | -0.0342 (-0.0398 to -0.0290) |
| Transformer with pages minus library + own pages | -0.0420 (-0.0488 to -0.0360) | -0.0380 (-0.0451 to -0.0318) | -0.0485 (-0.0628 to -0.0353) | -0.0392 (-0.0433 to -0.0353) | -0.0384 (-0.0435 to -0.0338) |
| What the pages add to the Transformer | +0.0031 (+0.0024 to +0.0037) | +0.0035 (+0.0026 to +0.0045) | +0.0051 (+0.0043 to +0.0059) | +0.0025 (+0.0016 to +0.0032) | +0.0017 (+0.0003 to +0.0030) |
| Transformer forecasts added to the boosted trees | +0.0091 (+0.0071 to +0.0110) | +0.0116 (+0.0093 to +0.0142) | +0.0095 (+0.0059 to +0.0130) | +0.0075 (+0.0055 to +0.0095) | +0.0102 (+0.0085 to +0.0122) |

| List | Library model (boosted trees) | Library + own and author pages (boosted trees) | Transformer, loan history only | Transformer, loan history + own and author page views | Boosted trees: library + own pages + the two Transformer forecasts |
| --- | --- | --- | --- | --- | --- |
| Top 20, all books | 0.830 | 0.837 | 0.785 | 0.793 | 0.852 |
| Top 20, early warning | 0.421 | 0.408 | 0.416 | 0.434 | 0.476 |

## Results by kind of book

Every group of every family fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books are ranked against each other. "Score" is the library + own pages model's score in that group; each cell is the gain from adding the signal, a five-seed mean with its 95% interval. Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that signal; **differs** = the gain differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged. Groups from Wikidata (series, film or TV, award, translated, classic) cover only books matched to a Wikidata book item. Amazon reviews are scored on fewer months (see above), so their rows differ from the "Rows" column.

### Series (asked for by Khant)

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in a series, known at the time | 120,125 | 78 | 0.306 | +0.0009 (+0.0002 to +0.0016) **found** | +0.0001 (-0.0008 to +0.0009) | -0.0005 (-0.0012 to +0.0001) | +0.0002 (-0.0008 to +0.0010) | +0.0002 (-0.0010 to +0.0012) | +0.0013 (+0.0004 to +0.0021) **found** |
| no series link known at the time | 165,706 | 78 | 0.369 | +0.0007 (+0.0003 to +0.0012) **found** | +0.0002 (-0.0003 to +0.0006) | +0.0000 (-0.0004 to +0.0005) | +0.0013 (+0.0007 to +0.0019) **found** | +0.0008 (-0.0005 to +0.0022) | +0.0016 (+0.0008 to +0.0024) **found** |

### Film or TV adaptation (asked for by Khant)

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| film or TV version already out | 55,662 | 78 | 0.327 | +0.0013 (+0.0004 to +0.0022) **found** | +0.0006 (-0.0011 to +0.0024) | +0.0003 (-0.0005 to +0.0011) | -0.0001 (-0.0014 to +0.0012) | +0.0003 (-0.0012 to +0.0017) | +0.0017 (-0.0001 to +0.0037) |
| no film or TV version out yet | 230,169 | 78 | 0.349 | +0.0008 (+0.0003 to +0.0013) **found** | -0.0002 (-0.0006 to +0.0002) | -0.0003 (-0.0007 to +0.0002) | +0.0011 (+0.0006 to +0.0016) **found** | +0.0006 (-0.0005 to +0.0017) | +0.0011 (+0.0006 to +0.0017) **found** |

### Popularity in the year before (asked for by Khant)

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low | 260,656 | 77 | 0.367 | +0.0017 (+0.0008 to +0.0028) **found** | -0.0003 (-0.0011 to +0.0001) | -0.0003 (-0.0009 to +0.0002) | +0.0009 (+0.0001 to +0.0022) **found** | +0.0099 (+0.0038 to +0.0211) **found** | +0.0024 (+0.0012 to +0.0042) **found** **differs** |
| middle | 442,985 | 78 | 0.331 | +0.0003 (+0.0001 to +0.0007) **found** **differs** | +0.0000 (-0.0002 to +0.0003) | +0.0001 (-0.0001 to +0.0003) | +0.0001 (-0.0001 to +0.0003) | +0.0028 (+0.0018 to +0.0041) **found** | +0.0004 (+0.0001 to +0.0008) **found** |
| high | 555,166 | 78 | 0.348 | +0.0006 (+0.0002 to +0.0011) **found** | -0.0000 (-0.0004 to +0.0003) | -0.0001 (-0.0004 to +0.0002) | -0.0001 (-0.0004 to +0.0002) | +0.0025 (+0.0014 to +0.0035) **found** | +0.0002 (-0.0002 to +0.0006) **differs** |

### Fiction or nonfiction

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fiction | 827,393 | 78 | 0.348 | +0.0008 (+0.0005 to +0.0011) **found** | -0.0001 (-0.0004 to +0.0001) | -0.0000 (-0.0002 to +0.0002) | +0.0001 (-0.0001 to +0.0003) | +0.0044 (+0.0036 to +0.0053) **found** **differs** | +0.0006 (+0.0003 to +0.0010) **found** |
| nonfiction | 412,596 | 78 | 0.358 | +0.0010 (+0.0007 to +0.0014) **found** | +0.0000 (-0.0002 to +0.0003) | +0.0000 (-0.0002 to +0.0003) | +0.0003 (+0.0001 to +0.0005) | +0.0006 (-0.0004 to +0.0016) **differs** | +0.0008 (+0.0004 to +0.0013) **found** |
| other (mixed or unknown) | 18,818 | 78 | 0.338 | +0.0007 (-0.0008 to +0.0023) | +0.0001 (-0.0015 to +0.0017) | -0.0002 (-0.0019 to +0.0014) | -0.0006 (-0.0021 to +0.0008) | +0.0042 (+0.0013 to +0.0073) **found** | +0.0018 (-0.0006 to +0.0040) |

### Audience

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adult | 839,677 | 78 | 0.375 | +0.0009 (+0.0006 to +0.0013) **found** | +0.0001 (-0.0001 to +0.0003) | +0.0001 (-0.0001 to +0.0003) | +0.0004 (+0.0002 to +0.0006) **found** **differs** | +0.0029 (+0.0022 to +0.0037) **found** | +0.0010 (+0.0006 to +0.0015) **found** **differs** |
| children | 360,814 | 78 | 0.288 | +0.0004 (+0.0000 to +0.0008) | -0.0002 (-0.0007 to +0.0003) | +0.0000 (-0.0004 to +0.0004) | -0.0003 (-0.0007 to +0.0002) | +0.0037 (+0.0021 to +0.0058) **found** | +0.0002 (-0.0003 to +0.0006) |
| young adult | 58,316 | 78 | 0.326 | +0.0006 (-0.0003 to +0.0016) | +0.0003 (-0.0007 to +0.0016) | -0.0004 (-0.0010 to +0.0002) | -0.0002 (-0.0010 to +0.0006) | +0.0027 (+0.0004 to +0.0049) **found** | +0.0001 (-0.0010 to +0.0012) |

### Format

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| audiobook | 340,064 | 78 | 0.367 | +0.0013 (+0.0008 to +0.0018) **found** **differs** | +0.0001 (-0.0001 to +0.0004) | +0.0001 (-0.0001 to +0.0005) | +0.0005 (+0.0002 to +0.0007) **found** | +0.0037 (+0.0025 to +0.0053) **found** | +0.0016 (+0.0009 to +0.0024) **found** **differs** |
| ebook | 446,291 | 78 | 0.353 | +0.0003 (+0.0000 to +0.0007) **found** **differs** | -0.0001 (-0.0003 to +0.0002) | -0.0000 (-0.0003 to +0.0002) | -0.0000 (-0.0003 to +0.0002) | +0.0020 (+0.0012 to +0.0030) **found** | +0.0001 (-0.0001 to +0.0004) **differs** |
| print | 472,452 | 78 | 0.336 | +0.0009 (+0.0006 to +0.0014) **found** | -0.0003 (-0.0006 to -0.0000) | -0.0001 (-0.0004 to +0.0002) | +0.0000 (-0.0004 to +0.0003) | +0.0038 (+0.0030 to +0.0046) **found** | +0.0004 (+0.0000 to +0.0007) |

### Time since first Seattle loan

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| under 1 year | 199,907 | 78 | 0.421 | +0.0027 (+0.0019 to +0.0035) **found** **differs** | -0.0001 (-0.0004 to +0.0001) | +0.0001 (-0.0003 to +0.0007) | +0.0009 (+0.0005 to +0.0014) **found** **differs** | +0.0101 (+0.0084 to +0.0122) **found** **differs** | +0.0030 (+0.0020 to +0.0040) **found** **differs** |
| 1 to 5 years | 548,026 | 78 | 0.333 | +0.0004 (+0.0002 to +0.0007) **found** **differs** | +0.0000 (-0.0002 to +0.0003) | -0.0001 (-0.0003 to +0.0002) | +0.0001 (-0.0001 to +0.0003) | +0.0029 (+0.0019 to +0.0040) **found** | +0.0002 (-0.0001 to +0.0005) **differs** |
| 5 years or more | 510,874 | 78 | 0.316 | +0.0005 (+0.0001 to +0.0009) **found** | -0.0002 (-0.0005 to +0.0002) | +0.0000 (-0.0003 to +0.0004) | -0.0003 (-0.0007 to +0.0000) **differs** | +0.0001 (-0.0010 to +0.0011) **differs** | +0.0001 (-0.0003 to +0.0004) **differs** |

### Author's earlier Seattle books

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no | 360,676 | 78 | 0.356 | +0.0007 (+0.0003 to +0.0010) **found** | -0.0003 (-0.0006 to +0.0000) | -0.0001 (-0.0004 to +0.0002) | +0.0000 (-0.0003 to +0.0004) | +0.0016 (+0.0009 to +0.0023) **found** **differs** | +0.0003 (-0.0000 to +0.0007) |
| unknown | 7,372 | 78 | 0.330 | -0.0011 (-0.0037 to +0.0013) | -0.0008 (-0.0041 to +0.0018) | -0.0011 (-0.0037 to +0.0014) | +0.0001 (-0.0022 to +0.0022) | +0.0102 (-0.0046 to +0.0276) | -0.0004 (-0.0045 to +0.0031) |
| yes | 890,709 | 78 | 0.351 | +0.0009 (+0.0006 to +0.0013) **found** | +0.0000 (-0.0002 to +0.0003) | +0.0000 (-0.0002 to +0.0003) | +0.0002 (-0.0000 to +0.0004) | +0.0039 (+0.0031 to +0.0048) **found** **differs** | +0.0008 (+0.0004 to +0.0013) **found** |

### Own Wikipedia article

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| author article only | 516,918 | 78 | 0.357 | +0.0009 (+0.0006 to +0.0012) **found** | -0.0002 (-0.0004 to +0.0000) | +0.0001 (-0.0001 to +0.0004) | +0.0002 (+0.0000 to +0.0004) | +0.0035 (+0.0027 to +0.0044) **found** | +0.0008 (+0.0005 to +0.0011) **found** |
| book article | 265,942 | 78 | 0.341 | +0.0010 (+0.0005 to +0.0014) **found** | +0.0001 (-0.0004 to +0.0006) | -0.0003 (-0.0006 to +0.0001) | +0.0003 (-0.0002 to +0.0009) | +0.0004 (-0.0006 to +0.0013) **differs** | +0.0012 (+0.0006 to +0.0018) **found** |
| neither | 475,947 | 78 | 0.348 | +0.0009 (+0.0005 to +0.0013) **found** | -0.0001 (-0.0003 to +0.0001) | +0.0000 (-0.0002 to +0.0003) | +0.0003 (+0.0001 to +0.0006) **found** | +0.0047 (+0.0035 to +0.0061) **found** | +0.0007 (+0.0003 to +0.0012) **found** |

### Award

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| award won by then | 34,142 | 78 | 0.325 | +0.0016 (-0.0001 to +0.0032) | +0.0004 (-0.0009 to +0.0017) | -0.0000 (-0.0012 to +0.0012) | -0.0001 (-0.0018 to +0.0016) | +0.0012 (-0.0013 to +0.0038) | +0.0018 (+0.0001 to +0.0036) |
| no award known by then | 251,689 | 78 | 0.347 | +0.0008 (+0.0004 to +0.0012) **found** | +0.0000 (-0.0005 to +0.0005) | -0.0001 (-0.0005 to +0.0003) | +0.0010 (+0.0004 to +0.0015) **found** | +0.0005 (-0.0005 to +0.0015) | +0.0015 (+0.0008 to +0.0021) **found** |

### Translated

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| translated | 17,953 | 78 | 0.328 | +0.0010 (-0.0007 to +0.0029) | -0.0029 (-0.0050 to -0.0007) | -0.0004 (-0.0020 to +0.0012) | -0.0001 (-0.0024 to +0.0022) | -0.0000 (-0.0043 to +0.0048) | -0.0009 (-0.0032 to +0.0013) |
| written in English | 254,007 | 78 | 0.344 | +0.0009 (+0.0005 to +0.0013) **found** | +0.0003 (-0.0003 to +0.0008) | -0.0002 (-0.0006 to +0.0002) | +0.0008 (+0.0003 to +0.0014) **found** | +0.0005 (-0.0005 to +0.0016) | +0.0017 (+0.0010 to +0.0023) **found** |

### Public-domain classic

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1930 or later | 242,178 | 78 | 0.335 | +0.0010 (+0.0005 to +0.0014) **found** | +0.0002 (-0.0004 to +0.0007) | -0.0002 (-0.0006 to +0.0002) | +0.0008 (+0.0003 to +0.0014) **found** | +0.0003 (-0.0008 to +0.0014) | +0.0016 (+0.0009 to +0.0023) **found** |
| first published before 1930 | 13,333 | 78 | 0.344 | +0.0022 (+0.0002 to +0.0044) | -0.0016 (-0.0055 to +0.0016) | +0.0019 (-0.0009 to +0.0047) | -0.0003 (-0.0029 to +0.0022) | -0.0023 (-0.0076 to +0.0040) | +0.0010 (-0.0027 to +0.0046) |

### Genre (broad theme)

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 Magic, myth and the supernatural | 117,139 | 78 | 0.312 | +0.0012 (+0.0006 to +0.0019) **found** | -0.0002 (-0.0007 to +0.0004) | -0.0004 (-0.0009 to +0.0001) | +0.0000 (-0.0006 to +0.0006) | +0.0041 (+0.0022 to +0.0062) **found** | +0.0005 (-0.0003 to +0.0012) |
| B02 Gender, sexuality and relationships | 106,306 | 78 | 0.377 | +0.0012 (+0.0005 to +0.0021) **found** | +0.0003 (-0.0002 to +0.0007) | +0.0001 (-0.0003 to +0.0005) | +0.0009 (+0.0003 to +0.0014) **found** | +0.0028 (+0.0009 to +0.0049) **found** | +0.0015 (+0.0007 to +0.0024) **found** |
| B03 Religion and spirituality | 29,838 | 78 | 0.343 | +0.0002 (-0.0008 to +0.0011) | -0.0006 (-0.0018 to +0.0005) | -0.0007 (-0.0023 to +0.0005) | -0.0008 (-0.0020 to +0.0002) | +0.0019 (-0.0022 to +0.0074) | +0.0003 (-0.0011 to +0.0017) |
| B04 Science, technology and learning | 64,777 | 78 | 0.327 | +0.0001 (-0.0010 to +0.0011) | -0.0001 (-0.0008 to +0.0005) | +0.0001 (-0.0006 to +0.0008) | +0.0002 (-0.0003 to +0.0008) | +0.0034 (+0.0012 to +0.0053) **found** | +0.0003 (-0.0006 to +0.0012) |
| B05 Race, ethnicity and migration | 49,860 | 78 | 0.383 | +0.0004 (-0.0005 to +0.0012) | -0.0002 (-0.0012 to +0.0007) | +0.0003 (-0.0002 to +0.0010) | +0.0008 (+0.0001 to +0.0015) | +0.0041 (+0.0009 to +0.0073) **found** | +0.0007 (-0.0003 to +0.0016) |
| B06 Arts, media and entertainment | 70,364 | 78 | 0.365 | +0.0007 (+0.0001 to +0.0012) **found** | -0.0005 (-0.0011 to +0.0000) | +0.0001 (-0.0003 to +0.0005) | -0.0001 (-0.0005 to +0.0004) | +0.0039 (+0.0020 to +0.0062) **found** | +0.0002 (-0.0007 to +0.0009) |
| B07 Childhood, family and growing up | 113,354 | 78 | 0.358 | +0.0002 (-0.0004 to +0.0008) **differs** | -0.0006 (-0.0010 to -0.0003) | -0.0004 (-0.0010 to +0.0001) | -0.0006 (-0.0010 to -0.0002) **differs** | +0.0031 (+0.0015 to +0.0046) **found** | -0.0002 (-0.0008 to +0.0004) **differs** |
| B08 War, conflict and history | 74,991 | 78 | 0.362 | +0.0014 (+0.0008 to +0.0021) **found** | +0.0001 (-0.0006 to +0.0007) | +0.0002 (-0.0004 to +0.0009) | +0.0003 (-0.0004 to +0.0010) | +0.0023 (-0.0001 to +0.0051) | +0.0011 (+0.0004 to +0.0019) **found** |
| B09 Nature, places and the environment | 96,529 | 78 | 0.361 | +0.0002 (-0.0004 to +0.0008) | -0.0005 (-0.0011 to +0.0001) | -0.0001 (-0.0007 to +0.0006) | +0.0003 (-0.0004 to +0.0009) | +0.0042 (+0.0022 to +0.0063) **found** | -0.0001 (-0.0011 to +0.0008) |
| B10 Work, business and money | 34,342 | 78 | 0.331 | +0.0008 (-0.0001 to +0.0017) | -0.0004 (-0.0010 to +0.0001) | -0.0007 (-0.0015 to +0.0001) | -0.0006 (-0.0015 to +0.0003) | +0.0023 (-0.0014 to +0.0058) | +0.0008 (-0.0004 to +0.0019) |
| B11 Food, home and holidays | 51,305 | 78 | 0.401 | +0.0004 (-0.0004 to +0.0011) | +0.0001 (-0.0006 to +0.0010) | +0.0001 (-0.0006 to +0.0008) | -0.0006 (-0.0015 to +0.0001) | +0.0014 (-0.0013 to +0.0043) | +0.0012 (-0.0001 to +0.0025) |
| B12 Violence, trauma, death and grief | 47,097 | 78 | 0.377 | +0.0011 (-0.0000 to +0.0023) | +0.0002 (-0.0004 to +0.0010) | +0.0001 (-0.0005 to +0.0007) | +0.0005 (-0.0001 to +0.0012) | +0.0063 (+0.0035 to +0.0091) **found** | +0.0013 (+0.0001 to +0.0026) |
| B13 Politics, society and justice | 34,610 | 78 | 0.404 | +0.0022 (+0.0013 to +0.0031) **found** **differs** | +0.0006 (-0.0002 to +0.0014) | +0.0003 (-0.0004 to +0.0011) | +0.0004 (-0.0004 to +0.0012) | +0.0026 (-0.0011 to +0.0063) | +0.0018 (+0.0008 to +0.0029) **found** |
| B14 Mind, self and philosophy | 72,637 | 78 | 0.334 | +0.0008 (+0.0002 to +0.0014) **found** | -0.0006 (-0.0010 to -0.0003) | +0.0001 (-0.0004 to +0.0006) | -0.0001 (-0.0006 to +0.0004) | +0.0010 (-0.0010 to +0.0031) | -0.0002 (-0.0009 to +0.0004) |
| B15 Health, illness and addiction | 28,119 | 78 | 0.326 | +0.0016 (-0.0001 to +0.0030) | +0.0007 (-0.0005 to +0.0019) | -0.0000 (-0.0013 to +0.0012) | +0.0003 (-0.0009 to +0.0013) | -0.0009 (-0.0067 to +0.0045) | +0.0015 (+0.0001 to +0.0027) |
| B16 Animals | 73,393 | 78 | 0.304 | +0.0018 (+0.0005 to +0.0032) **found** | -0.0001 (-0.0010 to +0.0008) | -0.0001 (-0.0009 to +0.0008) | +0.0003 (-0.0007 to +0.0012) | +0.0019 (-0.0023 to +0.0056) | +0.0013 (-0.0004 to +0.0030) |
| B17 Sports, games and fitness | 18,180 | 78 | 0.319 | +0.0014 (-0.0001 to +0.0031) | +0.0004 (-0.0006 to +0.0015) | +0.0005 (-0.0006 to +0.0016) | +0.0005 (-0.0007 to +0.0016) | +0.0068 (+0.0004 to +0.0160) | +0.0011 (-0.0005 to +0.0028) |
| B18 Space and the universe | 14,185 | 78 | 0.299 | -0.0001 (-0.0018 to +0.0016) | +0.0008 (-0.0016 to +0.0033) | -0.0010 (-0.0029 to +0.0006) | -0.0000 (-0.0027 to +0.0024) | +0.0023 (-0.0027 to +0.0067) | -0.0005 (-0.0028 to +0.0017) |
| B19 Crime, police and law | 51,005 | 78 | 0.354 | +0.0002 (-0.0007 to +0.0011) | +0.0006 (-0.0001 to +0.0012) | +0.0004 (-0.0002 to +0.0010) | +0.0005 (-0.0001 to +0.0011) | +0.0024 (+0.0002 to +0.0046) | +0.0005 (-0.0007 to +0.0017) |
| no theme | 110,776 | 78 | 0.339 | +0.0012 (+0.0005 to +0.0018) **found** | +0.0003 (-0.0003 to +0.0010) | +0.0004 (-0.0002 to +0.0009) | +0.0001 (-0.0005 to +0.0006) | +0.0038 (+0.0019 to +0.0061) **found** | +0.0009 (+0.0001 to +0.0017) |

### Has a theme

| Group | Rows | Months | Score | Bestseller lists | Film and TV pages | Linked pages | Reading logs | Amazon reviews | All four in hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no | 162,732 | 78 | 0.349 | +0.0012 (+0.0007 to +0.0017) **found** | +0.0001 (-0.0004 to +0.0006) | +0.0000 (-0.0004 to +0.0004) | +0.0001 (-0.0003 to +0.0005) | +0.0049 (+0.0028 to +0.0072) **found** | +0.0009 (+0.0004 to +0.0015) **found** |
| yes | 1,096,075 | 78 | 0.353 | +0.0008 (+0.0005 to +0.0012) **found** | -0.0001 (-0.0003 to +0.0001) | +0.0000 (-0.0002 to +0.0002) | +0.0002 (-0.0000 to +0.0004) | +0.0029 (+0.0024 to +0.0036) **found** | +0.0007 (+0.0004 to +0.0010) **found** |

### Groups that stand out after correction

- Bestseller lists, Series (asked for by Khant): in a series, known at the time: gain +0.0009 (+0.0002 to +0.0016), adjusted p 0.034.
- All four in hand, Series (asked for by Khant): in a series, known at the time: gain +0.0013 (+0.0004 to +0.0021), adjusted p 0.010.
- Bestseller lists, Series (asked for by Khant): no series link known at the time: gain +0.0007 (+0.0003 to +0.0012), adjusted p 0.012.
- Reading logs, Series (asked for by Khant): no series link known at the time: gain +0.0013 (+0.0007 to +0.0019), adjusted p 0.009.
- All four in hand, Series (asked for by Khant): no series link known at the time: gain +0.0016 (+0.0008 to +0.0024), adjusted p 0.006.
- Bestseller lists, Film or TV adaptation (asked for by Khant): film or TV version already out: gain +0.0013 (+0.0004 to +0.0022), adjusted p 0.004.
- Bestseller lists, Film or TV adaptation (asked for by Khant): no film or TV version out yet: gain +0.0008 (+0.0003 to +0.0013), adjusted p 0.004.
- Reading logs, Film or TV adaptation (asked for by Khant): no film or TV version out yet: gain +0.0011 (+0.0006 to +0.0016), adjusted p 0.009.
- All four in hand, Film or TV adaptation (asked for by Khant): no film or TV version out yet: gain +0.0011 (+0.0006 to +0.0017), adjusted p 0.003.
- Bestseller lists, Popularity in the year before (asked for by Khant): high: gain +0.0006 (+0.0002 to +0.0011), adjusted p 0.006.
- All four in hand, Popularity in the year before (asked for by Khant): high: smaller than in the other books by -0.0009 (-0.0015 to -0.0004), adjusted p 0.008.
- Bestseller lists, Popularity in the year before (asked for by Khant): low: gain +0.0017 (+0.0008 to +0.0028), adjusted p 0.002.
- Reading logs, Popularity in the year before (asked for by Khant): low: gain +0.0009 (+0.0001 to +0.0022), adjusted p 0.024.
- All four in hand, Popularity in the year before (asked for by Khant): low: gain +0.0024 (+0.0012 to +0.0042), adjusted p 0.003; larger than in the other books by +0.0020 (+0.0009 to +0.0036), adjusted p 0.008.
- Bestseller lists, Popularity in the year before (asked for by Khant): middle: gain +0.0003 (+0.0001 to +0.0007), adjusted p 0.008; smaller than in the other books by -0.0007 (-0.0010 to -0.0004), adjusted p 0.021.
- All four in hand, Popularity in the year before (asked for by Khant): middle: gain +0.0004 (+0.0001 to +0.0008), adjusted p 0.024.
- Bestseller lists, Fiction or nonfiction: fiction: gain +0.0008 (+0.0005 to +0.0011), adjusted p 0.002.
- All four in hand, Fiction or nonfiction: fiction: gain +0.0006 (+0.0003 to +0.0010), adjusted p 0.003.
- Bestseller lists, Fiction or nonfiction: nonfiction: gain +0.0010 (+0.0007 to +0.0014), adjusted p 0.002.
- All four in hand, Fiction or nonfiction: nonfiction: gain +0.0008 (+0.0004 to +0.0013), adjusted p 0.003.
- Bestseller lists, Audience: adult: gain +0.0009 (+0.0006 to +0.0013), adjusted p 0.002.
- Reading logs, Audience: adult: gain +0.0004 (+0.0002 to +0.0006), adjusted p 0.009; larger than in the other books by +0.0007 (+0.0003 to +0.0011), adjusted p 0.013.
- All four in hand, Audience: adult: gain +0.0010 (+0.0006 to +0.0015), adjusted p 0.003; larger than in the other books by +0.0009 (+0.0003 to +0.0016), adjusted p 0.020.
- Bestseller lists, Format: audiobook: gain +0.0013 (+0.0008 to +0.0018), adjusted p 0.002; larger than in the other books by +0.0007 (+0.0003 to +0.0011), adjusted p 0.030.
- Reading logs, Format: audiobook: gain +0.0005 (+0.0002 to +0.0007), adjusted p 0.021.
- All four in hand, Format: audiobook: gain +0.0016 (+0.0009 to +0.0024), adjusted p 0.003; larger than in the other books by +0.0014 (+0.0007 to +0.0021), adjusted p 0.008.
- Bestseller lists, Format: ebook: gain +0.0003 (+0.0000 to +0.0007), adjusted p 0.050; smaller than in the other books by -0.0008 (-0.0012 to -0.0003), adjusted p 0.021.
- All four in hand, Format: ebook: smaller than in the other books by -0.0009 (-0.0013 to -0.0005), adjusted p 0.008.
- Bestseller lists, Format: print: gain +0.0009 (+0.0006 to +0.0014), adjusted p 0.002.
- Bestseller lists, Time since first Seattle loan: 1 to 5 years: gain +0.0004 (+0.0002 to +0.0007), adjusted p 0.002; smaller than in the other books by -0.0007 (-0.0012 to -0.0003), adjusted p 0.021.
- All four in hand, Time since first Seattle loan: 1 to 5 years: smaller than in the other books by -0.0008 (-0.0015 to -0.0002), adjusted p 0.041.
- Bestseller lists, Time since first Seattle loan: 5 years or more: gain +0.0005 (+0.0001 to +0.0009), adjusted p 0.018.
- Reading logs, Time since first Seattle loan: 5 years or more: smaller than in the other books by -0.0007 (-0.0011 to -0.0004), adjusted p 0.013.
- All four in hand, Time since first Seattle loan: 5 years or more: smaller than in the other books by -0.0009 (-0.0013 to -0.0005), adjusted p 0.008.
- Bestseller lists, Time since first Seattle loan: under 1 year: gain +0.0027 (+0.0019 to +0.0035), adjusted p 0.002; larger than in the other books by +0.0022 (+0.0014 to +0.0030), adjusted p 0.021.
- Reading logs, Time since first Seattle loan: under 1 year: gain +0.0009 (+0.0005 to +0.0014), adjusted p 0.009; larger than in the other books by +0.0010 (+0.0005 to +0.0016), adjusted p 0.013.
- All four in hand, Time since first Seattle loan: under 1 year: gain +0.0030 (+0.0020 to +0.0040), adjusted p 0.003; larger than in the other books by +0.0028 (+0.0018 to +0.0037), adjusted p 0.008.
- Bestseller lists, Author's earlier Seattle books: no: gain +0.0007 (+0.0003 to +0.0010), adjusted p 0.002.
- Bestseller lists, Author's earlier Seattle books: yes: gain +0.0009 (+0.0006 to +0.0013), adjusted p 0.002.
- All four in hand, Author's earlier Seattle books: yes: gain +0.0008 (+0.0004 to +0.0013), adjusted p 0.003.
- Bestseller lists, Own Wikipedia article: author article only: gain +0.0009 (+0.0006 to +0.0012), adjusted p 0.002.
- All four in hand, Own Wikipedia article: author article only: gain +0.0008 (+0.0005 to +0.0011), adjusted p 0.003.
- Bestseller lists, Own Wikipedia article: book article: gain +0.0010 (+0.0005 to +0.0014), adjusted p 0.002.
- All four in hand, Own Wikipedia article: book article: gain +0.0012 (+0.0006 to +0.0018), adjusted p 0.003.
- Bestseller lists, Own Wikipedia article: neither: gain +0.0009 (+0.0005 to +0.0013), adjusted p 0.002.
- Reading logs, Own Wikipedia article: neither: gain +0.0003 (+0.0001 to +0.0006), adjusted p 0.044.
- All four in hand, Own Wikipedia article: neither: gain +0.0007 (+0.0003 to +0.0012), adjusted p 0.003.
- Bestseller lists, Award: no award known by then: gain +0.0008 (+0.0004 to +0.0012), adjusted p 0.002.
- Reading logs, Award: no award known by then: gain +0.0010 (+0.0004 to +0.0015), adjusted p 0.009.
- All four in hand, Award: no award known by then: gain +0.0015 (+0.0008 to +0.0021), adjusted p 0.003.
- Bestseller lists, Translated: written in English: gain +0.0009 (+0.0005 to +0.0013), adjusted p 0.002.
- Reading logs, Translated: written in English: gain +0.0008 (+0.0003 to +0.0014), adjusted p 0.015.
- All four in hand, Translated: written in English: gain +0.0017 (+0.0010 to +0.0023), adjusted p 0.003.
- Bestseller lists, Public-domain classic: 1930 or later: gain +0.0010 (+0.0005 to +0.0014), adjusted p 0.002.
- Reading logs, Public-domain classic: 1930 or later: gain +0.0008 (+0.0003 to +0.0014), adjusted p 0.018.
- All four in hand, Public-domain classic: 1930 or later: gain +0.0016 (+0.0009 to +0.0023), adjusted p 0.003.
- Bestseller lists, Genre (broad theme): B01 Magic, myth and the supernatural: gain +0.0012 (+0.0006 to +0.0019), adjusted p 0.002.
- Bestseller lists, Genre (broad theme): B02 Gender, sexuality and relationships: gain +0.0012 (+0.0005 to +0.0021), adjusted p 0.002.
- Reading logs, Genre (broad theme): B02 Gender, sexuality and relationships: gain +0.0009 (+0.0003 to +0.0014), adjusted p 0.009.
- All four in hand, Genre (broad theme): B02 Gender, sexuality and relationships: gain +0.0015 (+0.0007 to +0.0024), adjusted p 0.003.
- Bestseller lists, Genre (broad theme): B06 Arts, media and entertainment: gain +0.0007 (+0.0001 to +0.0012), adjusted p 0.015.
- Bestseller lists, Genre (broad theme): B07 Childhood, family and growing up: smaller than in the other books by -0.0008 (-0.0012 to -0.0003), adjusted p 0.021.
- Reading logs, Genre (broad theme): B07 Childhood, family and growing up: smaller than in the other books by -0.0008 (-0.0012 to -0.0004), adjusted p 0.013.
- All four in hand, Genre (broad theme): B07 Childhood, family and growing up: smaller than in the other books by -0.0010 (-0.0015 to -0.0005), adjusted p 0.008.
- Bestseller lists, Genre (broad theme): B08 War, conflict and history: gain +0.0014 (+0.0008 to +0.0021), adjusted p 0.002.
- All four in hand, Genre (broad theme): B08 War, conflict and history: gain +0.0011 (+0.0004 to +0.0019), adjusted p 0.006.
- Bestseller lists, Genre (broad theme): B13 Politics, society and justice: gain +0.0022 (+0.0013 to +0.0031), adjusted p 0.002; larger than in the other books by +0.0014 (+0.0006 to +0.0023), adjusted p 0.026.
- All four in hand, Genre (broad theme): B13 Politics, society and justice: gain +0.0018 (+0.0008 to +0.0029), adjusted p 0.010.
- Bestseller lists, Genre (broad theme): B14 Mind, self and philosophy: gain +0.0008 (+0.0002 to +0.0014), adjusted p 0.011.
- Bestseller lists, Genre (broad theme): B16 Animals: gain +0.0018 (+0.0005 to +0.0032), adjusted p 0.011.
- Bestseller lists, Genre (broad theme): no theme: gain +0.0012 (+0.0005 to +0.0018), adjusted p 0.002.
- Bestseller lists, Has a theme: no: gain +0.0012 (+0.0007 to +0.0017), adjusted p 0.002.
- All four in hand, Has a theme: no: gain +0.0009 (+0.0004 to +0.0015), adjusted p 0.003.
- Bestseller lists, Has a theme: yes: gain +0.0008 (+0.0005 to +0.0012), adjusted p 0.002.
- All four in hand, Has a theme: yes: gain +0.0007 (+0.0004 to +0.0010), adjusted p 0.003.
- Amazon reviews, Popularity in the year before (asked for by Khant): high: gain +0.0025 (+0.0014 to +0.0035), adjusted p 0.002.
- Amazon reviews, Popularity in the year before (asked for by Khant): low: gain +0.0099 (+0.0038 to +0.0211), adjusted p 0.002.
- Amazon reviews, Popularity in the year before (asked for by Khant): middle: gain +0.0028 (+0.0018 to +0.0041), adjusted p 0.002.
- Amazon reviews, Fiction or nonfiction: fiction: gain +0.0044 (+0.0036 to +0.0053), adjusted p 0.002; larger than in the other books by +0.0037 (+0.0023 to +0.0052), adjusted p 0.008.
- Amazon reviews, Fiction or nonfiction: nonfiction: smaller than in the other books by -0.0037 (-0.0052 to -0.0022), adjusted p 0.008.
- Amazon reviews, Fiction or nonfiction: other (mixed or unknown): gain +0.0042 (+0.0013 to +0.0073), adjusted p 0.006.
- Amazon reviews, Audience: adult: gain +0.0029 (+0.0022 to +0.0037), adjusted p 0.002.
- Amazon reviews, Audience: children: gain +0.0037 (+0.0021 to +0.0058), adjusted p 0.002.
- Amazon reviews, Audience: young adult: gain +0.0027 (+0.0004 to +0.0049), adjusted p 0.044.
- Amazon reviews, Format: audiobook: gain +0.0037 (+0.0025 to +0.0053), adjusted p 0.002.
- Amazon reviews, Format: ebook: gain +0.0020 (+0.0012 to +0.0030), adjusted p 0.002.
- Amazon reviews, Format: print: gain +0.0038 (+0.0030 to +0.0046), adjusted p 0.002.
- Amazon reviews, Time since first Seattle loan: 1 to 5 years: gain +0.0029 (+0.0019 to +0.0040), adjusted p 0.002.
- Amazon reviews, Time since first Seattle loan: 5 years or more: smaller than in the other books by -0.0048 (-0.0069 to -0.0032), adjusted p 0.008.
- Amazon reviews, Time since first Seattle loan: under 1 year: gain +0.0101 (+0.0084 to +0.0122), adjusted p 0.002; larger than in the other books by +0.0085 (+0.0065 to +0.0105), adjusted p 0.008.
- Amazon reviews, Author's earlier Seattle books: no: gain +0.0016 (+0.0009 to +0.0023), adjusted p 0.002; smaller than in the other books by -0.0023 (-0.0033 to -0.0012), adjusted p 0.008.
- Amazon reviews, Author's earlier Seattle books: yes: gain +0.0039 (+0.0031 to +0.0048), adjusted p 0.002; larger than in the other books by +0.0022 (+0.0011 to +0.0033), adjusted p 0.008.
- Amazon reviews, Own Wikipedia article: author article only: gain +0.0035 (+0.0027 to +0.0044), adjusted p 0.002.
- Amazon reviews, Own Wikipedia article: book article: smaller than in the other books by -0.0036 (-0.0046 to -0.0026), adjusted p 0.008.
- Amazon reviews, Own Wikipedia article: neither: gain +0.0047 (+0.0035 to +0.0061), adjusted p 0.002.
- Amazon reviews, Genre (broad theme): B01 Magic, myth and the supernatural: gain +0.0041 (+0.0022 to +0.0062), adjusted p 0.006.
- Amazon reviews, Genre (broad theme): B02 Gender, sexuality and relationships: gain +0.0028 (+0.0009 to +0.0049), adjusted p 0.014.
- Amazon reviews, Genre (broad theme): B04 Science, technology and learning: gain +0.0034 (+0.0012 to +0.0053), adjusted p 0.005.
- Amazon reviews, Genre (broad theme): B05 Race, ethnicity and migration: gain +0.0041 (+0.0009 to +0.0073), adjusted p 0.029.
- Amazon reviews, Genre (broad theme): B06 Arts, media and entertainment: gain +0.0039 (+0.0020 to +0.0062), adjusted p 0.002.
- Amazon reviews, Genre (broad theme): B07 Childhood, family and growing up: gain +0.0031 (+0.0015 to +0.0046), adjusted p 0.002.
- Amazon reviews, Genre (broad theme): B09 Nature, places and the environment: gain +0.0042 (+0.0022 to +0.0063), adjusted p 0.002.
- Amazon reviews, Genre (broad theme): B12 Violence, trauma, death and grief: gain +0.0063 (+0.0035 to +0.0091), adjusted p 0.002.
- Amazon reviews, Genre (broad theme): no theme: gain +0.0038 (+0.0019 to +0.0061), adjusted p 0.002.
- Amazon reviews, Has a theme: no: gain +0.0049 (+0.0028 to +0.0072), adjusted p 0.002.
- Amazon reviews, Has a theme: yes: gain +0.0029 (+0.0024 to +0.0036), adjusted p 0.002.

## Data behind the test

- **Bestseller lists**: 3,830 of 43,298 main-set works matched to New York Times list entries (74,526 entries; ISBN or title and author, the rules of the earlier list test unchanged, which they reproduce exactly). 19.8% of the 1,258,807 scored rows belong to a matched work (unmatched works get 0 and a flag); 0.76% of scored rows were on a list in their month. An independent check of 50 random matches found 48 right, 2 wrong and 0 unsure (the rule allowed up to 5 wrong).
- **Film and TV pages**: 4.0% of 1,258,807 scored rows have a value (546 works with at least one film or TV article with views).
- **Linked pages**: 9.2% of 1,258,807 scored rows have a value (1,447 works, 1,688 pages).
- **Reading logs**: 2,735 works mapped to Open Library through Wikidata; 17.2% of 1,258,807 scored rows have a value. The dump keeps only entries still on a shelf in September 2026.
- **Amazon reviews**: 25,891 works matched; last usable month April 2023; 80.5% of 673,926 scored rows (up to that month) have a review history. An independent check of 50 random matches found 48 right, 2 wrong and 0 unsure (the rule allowed up to 5 wrong). Both wrong ones have titles that start with a series name and a colon (for example "Pete the Cat: ..."), so every book of that series by the same author was summed into one work.
- Checks: the stored library and own-page scores of the main table are reproduced exactly; the refitted library + own pages model equals the stored predictions; the copied page-feature code reproduces the stored features.

## Limits

- Film and TV pages, linked pages and reading logs exist only for books matched to a Wikidata book item, mostly well-known books; which books have one uses Wikidata as of October 2026.
- Bestseller lists cover only the top of the market; most books never appear on one.
- Amazon reviews come from one retailer and end in 2023, so they are scored on fewer months than the other signals. Matching by title and author merges books of a series whose titles share the text before a colon, and a few non-book Amazon items carry a book's ISBN.
- The Transformer was used as released, without tuning or training on library data; a trained deep model might do differently. It was pretrained (released in 2025) on public time series that may cover some of the test years; it never saw these library series, but it may carry general patterns of those years. Its gain as an extra input had no pass rule and no placebo, so it is a lead to confirm, not a result.
- Bestseller lists and Amazon reviews raised the score over all books, but Amazon reviews lowered the share of risers in both monthly top-20 lists and bestseller lists lowered it in the early-warning list. They improve the ranking as a whole more than its very top.
- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.

