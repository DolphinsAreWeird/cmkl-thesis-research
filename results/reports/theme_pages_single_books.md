# Theme pages as inputs for single books, and results by kind of book

Made by `code/main_study/wiki_led/m_theme_pages/m04_score.py` and `m05_report.py` on 2026-11-25 16:03 (+07:00). Settings fixed in advance in `prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json` (made public on GitHub, pull request 33, at 05:38 UTC on 25 November 2026, before any step ran). Changes and choices made later are logged with times in `prereg/DEVIATIONS.md`.

## The question

Until now, the models for single books used the library's loan history and two Wikipedia pages: the book's own article and its author's. Here, pages about the book's themes are added: their traffic level, their rise against normal, how long a rise has lasted, and whether a lasting rise is under way. Two sets of theme pages are tested separately: 624 concept pages reviewed by hand, and about 40,000 pages sorted into the same themes by an AI model (each counted only from the month it had twice been among the 500 most-viewed pages). The question is whether they improve the ranking of which books will rise next month, on the same books and months as the thesis's main table, and for which kinds of books any page signal helps.

## How to read the numbers

- **Score**: each month and format, the books are ranked by predicted change in loans and compared with the actual change (rank correlation; 0 is chance, 1 is perfect), averaged over the 78 months from February 2019 to August 2026. Models only ever learn from earlier years.
- **Gain**: the score with the added pages minus the score without them, on the same rows.
- **Five seeds**: every model was fitted five times with different random seeds. A value is the mean of the five; "±" is their standard deviation, then the smallest and largest of the five, and how many were above 0.
- **95% interval** (in brackets): from 2,000 redraws of blocks of three consecutive months, with the five-seed mean recomputed in each redraw.
- **Placebos**: the same model given (a) the pages of another theme with similar traffic, or (b) the real theme pages with their dates moved 12 months later. If the signal is real and about the book's own themes at the right time, the real pages should beat both.

## In short

- **Hand-reviewed theme pages** did not pass the rule fixed in advance. Added to the library model with the book's own and author's pages, they changed the score by +0.0006 (+0.0001 to +0.0010) (five seeds ± 0.0002; +0.0002 to +0.0008; 5 of 5 above 0). Reason: the gain cannot be told apart from the theme's usual timing (the same pages with dates moved 12 months did as well).
- **AI-sorted theme pages** passed the rule fixed in advance. Added to the library model with the book's own and author's pages, they changed the score by +0.0008 (+0.0003 to +0.0013) (five seeds ± 0.0002; +0.0005 to +0.0011; 5 of 5 above 0).
- **The book's own and author's pages** (the existing test) added +0.0049 (+0.0040 to +0.0058) (five seeds ± 0.0002; +0.0046 to +0.0051; 5 of 5 above 0), as published.
- **The theme's own borrowing** (a library-side feature, no Wikipedia) added +0.0021 (+0.0017 to +0.0026). With it in the model, hand-reviewed theme pages added -0.0004 (-0.0007 to -0.0001) and AI-sorted ones +0.0001 (-0.0003 to +0.0005).
- **Where the theme-page gain comes from.** Split by whether the book has a narrow catalogue theme (a split fixed in advance): AI-sorted theme pages added +0.0003 (-0.0002 to +0.0009) for books with a theme and +0.0034 (+0.0026 to +0.0042) for books without one; hand-reviewed pages +0.0001 (-0.0004 to +0.0006) and +0.0029 (+0.0019 to +0.0038). Most rows of books without a narrow theme have no theme-page values at all, so their gain cannot come from page traffic: it comes from the model learning that books without a catalogue theme behave differently. The two placebos have the same missing values, so the real-minus-placebo differences in the table below are the cleaner measure of what the theme pages themselves carry.
- **By kind of book, own and author pages**: 53 of 53 groups were large enough to judge; a gain was found in 51 and a difference from the other books in 15 after correcting for the number of groups.
- **By kind of book, theme pages, hand-reviewed**: 53 of 53 groups were large enough to judge; a gain was found in 12 and a difference from the other books in 24 after correcting for the number of groups.
- **By kind of book, theme pages, AI-sorted**: 53 of 53 groups were large enough to judge; a gain was found in 14 and a difference from the other books in 26 after correcting for the number of groups.

## Rule fixed in advance

A set of theme pages passes only if all three hold: (1) its gain over the library model with the book's own and author's pages is above zero, with Holm's correction for testing two page sets; (2) it beats another theme's pages with similar traffic; (3) it beats its own pages with the dates moved 12 months. Conditions (2) and (3) need a 95% interval above zero.

| Theme pages | (1) Adds to library + own pages | One-sided p | (2) Beats another theme | (3) Beats moved dates | Passed |
| --- | --- | --- | --- | --- | --- |
| Hand-reviewed theme pages | yes: +0.0006 (+0.0001 to +0.0010) | 0.0065 | yes: +0.0013 (+0.0008 to +0.0017) | no: +0.0004 (-0.0000 to +0.0008) | **no** |
| AI-sorted theme pages | yes: +0.0008 (+0.0003 to +0.0013) | 0.0005 | yes: +0.0006 (+0.0004 to +0.0009) | yes: +0.0005 (+0.0004 to +0.0007) | **yes** |

## Scores of every model, main set, 2019 to 2026

1,258,807 book-format-months; target months February 2019 to August 2026.

| Model | Score, five-seed mean (95% interval) | ± across seeds |
| --- | --- | --- |
| Library model (loan history and calendar month) | 0.347 (0.340 to 0.355) | 0.0002 |
| Library + the book's own and author's pages | 0.352 (0.344 to 0.360) | 0.0001 |
| ... + hand-reviewed theme pages | 0.353 (0.345 to 0.361) | 0.0003 |
| ... + AI-sorted theme pages | 0.353 (0.345 to 0.361) | 0.0002 |
| Library + hand-reviewed theme pages (no own pages) | 0.348 (0.340 to 0.356) | 0.0002 |
| Library + AI-sorted theme pages (no own pages) | 0.348 (0.340 to 0.356) | 0.0003 |
| Hand-reviewed theme pages alone | 0.020 (0.017 to 0.023) | 0.0005 |
| AI-sorted theme pages alone | 0.027 (0.023 to 0.032) | 0.0006 |
| Another theme's hand-reviewed pages alone (placebo) | 0.013 (0.010 to 0.017) | 0.0003 |
| Another theme's AI-sorted pages alone (placebo) | 0.022 (0.019 to 0.025) | 0.0004 |
| Library + own pages + another theme's hand-reviewed pages (placebo) | 0.351 (0.344 to 0.360) | 0.0001 |
| Library + own pages + another theme's AI-sorted pages (placebo) | 0.352 (0.345 to 0.360) | 0.0001 |
| Library + own pages + hand-reviewed theme pages, dates moved 12 months (placebo) | 0.352 (0.345 to 0.360) | 0.0002 |
| Library + own pages + AI-sorted theme pages, dates moved 12 months (placebo) | 0.352 (0.345 to 0.360) | 0.0002 |
| Library + own pages + the theme's own borrowing | 0.354 (0.346 to 0.363) | 0.0001 |
| ... + theme borrowing + hand-reviewed theme pages | 0.354 (0.346 to 0.362) | 0.0001 |
| ... + theme borrowing + AI-sorted theme pages | 0.354 (0.347 to 0.363) | 0.0002 |

| Comparison | Gain, five-seed mean (95% interval) | Five seeds: ± SD; smallest to largest; above 0 |
| --- | --- | --- |
| Own and author pages, added to the library model | +0.0049 (+0.0040 to +0.0058) | ± 0.0002; +0.0046 to +0.0051; 5 of 5 above 0 |
| Hand-reviewed theme pages, added to library + own pages | +0.0006 (+0.0001 to +0.0010) | ± 0.0002; +0.0002 to +0.0008; 5 of 5 above 0 |
| AI-sorted theme pages, added to library + own pages | +0.0008 (+0.0003 to +0.0013) | ± 0.0002; +0.0005 to +0.0011; 5 of 5 above 0 |
| Hand-reviewed: real themes minus another theme with similar traffic | +0.0013 (+0.0008 to +0.0017) | ± 0.0003; +0.0008 to +0.0015; 5 of 5 above 0 |
| AI-sorted: real themes minus another theme with similar traffic | +0.0006 (+0.0004 to +0.0009) | ± 0.0001; +0.0005 to +0.0007; 5 of 5 above 0 |
| Hand-reviewed: real dates minus dates moved 12 months | +0.0004 (-0.0000 to +0.0008) | ± 0.0002; +0.0002 to +0.0006; 5 of 5 above 0 |
| AI-sorted: real dates minus dates moved 12 months | +0.0005 (+0.0004 to +0.0007) | ± 0.0001; +0.0005 to +0.0006; 5 of 5 above 0 |
| Hand-reviewed pages alone: real minus another theme | +0.0070 (+0.0032 to +0.0106) | ± 0.0006; +0.0061 to +0.0077; 5 of 5 above 0 |
| AI-sorted pages alone: real minus another theme | +0.0051 (+0.0023 to +0.0078) | ± 0.0009; +0.0044 to +0.0062; 5 of 5 above 0 |
| Hand-reviewed theme pages added to the library model (no own pages) | +0.0005 (-0.0000 to +0.0011) | ± 0.0003; +0.0001 to +0.0010; 5 of 5 above 0 |
| AI-sorted theme pages added to the library model (no own pages) | +0.0008 (+0.0002 to +0.0014) | ± 0.0004; +0.0003 to +0.0012; 5 of 5 above 0 |
| Hand-reviewed theme pages beyond the theme's own borrowing | -0.0004 (-0.0007 to -0.0001) | ± 0.0001; -0.0005 to -0.0003; 0 of 5 above 0 |
| AI-sorted theme pages beyond the theme's own borrowing | +0.0001 (-0.0003 to +0.0005) | ± 0.0001; +0.0001 to +0.0002; 5 of 5 above 0 |
| The theme's own borrowing, added to library + own pages | +0.0021 (+0.0017 to +0.0026) | ± 0.0001; +0.0020 to +0.0023; 5 of 5 above 0 |

## Scores of every model, main set, 2024 to 2026

The rows whose target month is in January 2024 to August 2026; the same draws of three-month blocks.

| Model | Score, five-seed mean (95% interval) | ± across seeds |
| --- | --- | --- |
| Library model (loan history and calendar month) | 0.356 (0.340 to 0.373) | 0.0002 |
| Library + the book's own and author's pages | 0.360 (0.344 to 0.376) | 0.0002 |
| ... + hand-reviewed theme pages | 0.361 (0.345 to 0.377) | 0.0003 |
| ... + AI-sorted theme pages | 0.361 (0.345 to 0.377) | 0.0003 |
| Library + hand-reviewed theme pages (no own pages) | 0.357 (0.341 to 0.374) | 0.0003 |
| Library + AI-sorted theme pages (no own pages) | 0.357 (0.341 to 0.374) | 0.0002 |
| Hand-reviewed theme pages alone | 0.022 (0.015 to 0.028) | 0.0009 |
| AI-sorted theme pages alone | 0.028 (0.023 to 0.033) | 0.0009 |
| Another theme's hand-reviewed pages alone (placebo) | 0.011 (0.007 to 0.016) | 0.0003 |
| Another theme's AI-sorted pages alone (placebo) | 0.024 (0.020 to 0.029) | 0.0003 |
| Library + own pages + another theme's hand-reviewed pages (placebo) | 0.359 (0.344 to 0.376) | 0.0001 |
| Library + own pages + another theme's AI-sorted pages (placebo) | 0.360 (0.345 to 0.377) | 0.0002 |
| Library + own pages + hand-reviewed theme pages, dates moved 12 months (placebo) | 0.361 (0.345 to 0.377) | 0.0003 |
| Library + own pages + AI-sorted theme pages, dates moved 12 months (placebo) | 0.360 (0.345 to 0.377) | 0.0003 |
| Library + own pages + the theme's own borrowing | 0.362 (0.346 to 0.379) | 0.0001 |
| ... + theme borrowing + hand-reviewed theme pages | 0.362 (0.346 to 0.378) | 0.0002 |
| ... + theme borrowing + AI-sorted theme pages | 0.362 (0.347 to 0.378) | 0.0003 |

| Comparison | Gain, five-seed mean (95% interval) | Five seeds: ± SD; smallest to largest; above 0 |
| --- | --- | --- |
| Own and author pages, added to the library model | +0.0038 (+0.0029 to +0.0049) | ± 0.0003; +0.0034 to +0.0042; 5 of 5 above 0 |
| Hand-reviewed theme pages, added to library + own pages | +0.0011 (+0.0004 to +0.0017) | ± 0.0004; +0.0005 to +0.0016; 5 of 5 above 0 |
| AI-sorted theme pages, added to library + own pages | +0.0007 (+0.0001 to +0.0014) | ± 0.0004; +0.0003 to +0.0014; 5 of 5 above 0 |
| Hand-reviewed: real themes minus another theme with similar traffic | +0.0016 (+0.0008 to +0.0022) | ± 0.0003; +0.0013 to +0.0018; 5 of 5 above 0 |
| AI-sorted: real themes minus another theme with similar traffic | +0.0008 (+0.0004 to +0.0013) | ± 0.0002; +0.0006 to +0.0011; 5 of 5 above 0 |
| Hand-reviewed: real dates minus dates moved 12 months | +0.0004 (-0.0003 to +0.0011) | ± 0.0003; +0.0000 to +0.0006; 5 of 5 above 0 |
| AI-sorted: real dates minus dates moved 12 months | +0.0004 (+0.0001 to +0.0007) | ± 0.0001; +0.0002 to +0.0005; 5 of 5 above 0 |
| Hand-reviewed pages alone: real minus another theme | +0.0107 (+0.0033 to +0.0169) | ± 0.0008; +0.0098 to +0.0120; 5 of 5 above 0 |
| AI-sorted pages alone: real minus another theme | +0.0042 (+0.0007 to +0.0079) | ± 0.0010; +0.0031 to +0.0057; 5 of 5 above 0 |
| Hand-reviewed theme pages added to the library model (no own pages) | +0.0012 (+0.0002 to +0.0022) | ± 0.0004; +0.0005 to +0.0017; 5 of 5 above 0 |
| AI-sorted theme pages added to the library model (no own pages) | +0.0011 (+0.0003 to +0.0019) | ± 0.0004; +0.0005 to +0.0017; 5 of 5 above 0 |
| Hand-reviewed theme pages beyond the theme's own borrowing | -0.0002 (-0.0007 to +0.0001) | ± 0.0002; -0.0004 to +0.0001; 1 of 5 above 0 |
| AI-sorted theme pages beyond the theme's own borrowing | +0.0000 (-0.0006 to +0.0006) | ± 0.0003; -0.0004 to +0.0003; 2 of 5 above 0 |
| The theme's own borrowing, added to library + own pages | +0.0021 (+0.0014 to +0.0028) | ± 0.0003; +0.0017 to +0.0024; 5 of 5 above 0 |

## By format, 2019 to 2026

| Format | Library | + own pages | + hand-reviewed theme pages | + AI-sorted theme pages |
| --- | --- | --- | --- | --- |
| print | 0.333 | 0.336 | 0.339 | 0.338 |
| ebook | 0.348 | 0.353 | 0.353 | 0.353 |
| audiobook | 0.361 | 0.367 | 0.367 | 0.367 |

| Comparison | print | ebook | audiobook |
| --- | --- | --- | --- |
| Own and author pages, added to the library model | +0.0038 (+0.0029 to +0.0049) | +0.0049 (+0.0039 to +0.0060) | +0.0059 (+0.0044 to +0.0075) |
| Hand-reviewed theme pages, added to library + own pages | +0.0024 (+0.0013 to +0.0034) | -0.0006 (-0.0011 to -0.0000) | -0.0002 (-0.0005 to +0.0003) |
| AI-sorted theme pages, added to library + own pages | +0.0020 (+0.0010 to +0.0030) | +0.0000 (-0.0004 to +0.0004) | +0.0004 (-0.0002 to +0.0010) |
| Hand-reviewed: real themes minus another theme with similar traffic | +0.0032 (+0.0023 to +0.0040) | +0.0001 (-0.0004 to +0.0006) | +0.0005 (-0.0000 to +0.0010) |
| AI-sorted: real themes minus another theme with similar traffic | +0.0016 (+0.0010 to +0.0023) | +0.0002 (-0.0001 to +0.0004) | +0.0001 (-0.0003 to +0.0004) |
| Hand-reviewed: real dates minus dates moved 12 months | +0.0007 (-0.0001 to +0.0016) | +0.0004 (-0.0001 to +0.0009) | +0.0001 (-0.0005 to +0.0006) |
| AI-sorted: real dates minus dates moved 12 months | +0.0007 (+0.0003 to +0.0011) | +0.0005 (+0.0003 to +0.0007) | +0.0003 (+0.0001 to +0.0006) |
| Hand-reviewed pages alone: real minus another theme | +0.0080 (+0.0021 to +0.0139) | +0.0063 (+0.0018 to +0.0106) | +0.0067 (+0.0014 to +0.0114) |
| AI-sorted pages alone: real minus another theme | +0.0079 (+0.0027 to +0.0132) | +0.0055 (+0.0019 to +0.0089) | +0.0020 (-0.0017 to +0.0059) |
| Hand-reviewed theme pages added to the library model (no own pages) | +0.0026 (+0.0014 to +0.0037) | -0.0008 (-0.0016 to +0.0000) | -0.0003 (-0.0009 to +0.0004) |
| AI-sorted theme pages added to the library model (no own pages) | +0.0023 (+0.0012 to +0.0036) | -0.0002 (-0.0008 to +0.0004) | +0.0002 (-0.0005 to +0.0010) |
| Hand-reviewed theme pages beyond the theme's own borrowing | +0.0000 (-0.0007 to +0.0008) | -0.0007 (-0.0010 to -0.0004) | -0.0004 (-0.0009 to -0.0001) |
| AI-sorted theme pages beyond the theme's own borrowing | +0.0006 (-0.0001 to +0.0014) | -0.0003 (-0.0006 to +0.0001) | +0.0001 (-0.0005 to +0.0007) |
| The theme's own borrowing, added to library + own pages | +0.0056 (+0.0044 to +0.0066) | +0.0009 (+0.0004 to +0.0014) | -0.0001 (-0.0006 to +0.0005) |

## By format, 2024 to 2026

| Format | Library | + own pages | + hand-reviewed theme pages | + AI-sorted theme pages |
| --- | --- | --- | --- | --- |
| print | 0.341 | 0.344 | 0.347 | 0.346 |
| ebook | 0.354 | 0.358 | 0.358 | 0.358 |
| audiobook | 0.373 | 0.378 | 0.378 | 0.378 |

| Comparison | print | ebook | audiobook |
| --- | --- | --- | --- |
| Own and author pages, added to the library model | +0.0031 (+0.0023 to +0.0038) | +0.0040 (+0.0022 to +0.0064) | +0.0044 (+0.0033 to +0.0056) |
| Hand-reviewed theme pages, added to library + own pages | +0.0034 (+0.0018 to +0.0048) | -0.0005 (-0.0014 to +0.0004) | +0.0002 (-0.0004 to +0.0008) |
| AI-sorted theme pages, added to library + own pages | +0.0022 (+0.0008 to +0.0038) | +0.0001 (-0.0005 to +0.0007) | -0.0001 (-0.0009 to +0.0007) |
| Hand-reviewed: real themes minus another theme with similar traffic | +0.0040 (+0.0021 to +0.0056) | -0.0000 (-0.0009 to +0.0007) | +0.0008 (+0.0005 to +0.0011) |
| AI-sorted: real themes minus another theme with similar traffic | +0.0019 (+0.0008 to +0.0030) | +0.0002 (-0.0001 to +0.0005) | +0.0003 (+0.0000 to +0.0007) |
| Hand-reviewed: real dates minus dates moved 12 months | +0.0013 (-0.0001 to +0.0026) | -0.0001 (-0.0010 to +0.0009) | -0.0001 (-0.0005 to +0.0003) |
| AI-sorted: real dates minus dates moved 12 months | +0.0006 (-0.0001 to +0.0013) | +0.0006 (+0.0002 to +0.0010) | +0.0001 (-0.0002 to +0.0004) |
| Hand-reviewed pages alone: real minus another theme | +0.0098 (-0.0047 to +0.0210) | +0.0090 (-0.0002 to +0.0164) | +0.0134 (+0.0054 to +0.0205) |
| AI-sorted pages alone: real minus another theme | +0.0076 (-0.0009 to +0.0168) | +0.0049 (-0.0002 to +0.0099) | +0.0002 (-0.0046 to +0.0052) |
| Hand-reviewed theme pages added to the library model (no own pages) | +0.0035 (+0.0017 to +0.0049) | -0.0005 (-0.0021 to +0.0010) | +0.0007 (-0.0002 to +0.0020) |
| AI-sorted theme pages added to the library model (no own pages) | +0.0024 (+0.0009 to +0.0039) | +0.0004 (-0.0004 to +0.0013) | +0.0004 (-0.0008 to +0.0019) |
| Hand-reviewed theme pages beyond the theme's own borrowing | +0.0003 (-0.0004 to +0.0009) | -0.0006 (-0.0010 to -0.0002) | -0.0004 (-0.0012 to +0.0003) |
| AI-sorted theme pages beyond the theme's own borrowing | +0.0007 (-0.0001 to +0.0015) | -0.0003 (-0.0010 to +0.0004) | -0.0004 (-0.0012 to +0.0003) |
| The theme's own borrowing, added to library + own pages | +0.0063 (+0.0046 to +0.0079) | +0.0007 (-0.0000 to +0.0015) | -0.0006 (-0.0017 to +0.0005) |

## Monthly top-20 lists

Each month and format, the 20 books with the highest predicted change; the share of them whose loans rose by half or more next month. The early-warning list keeps only books that had not already risen. Gains are in share points (0.010 is one percentage point).

| Period | Formats | List | Library | + own pages | + hand-reviewed theme pages | + AI-sorted theme pages | Own pages gain | Hand-reviewed gain | AI-sorted gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 to 2026 | all | all books | 0.830 | 0.837 | 0.847 | 0.839 | +0.0075 (+0.0035 to +0.0119) | +0.0104 (+0.0039 to +0.0179) | +0.0024 (-0.0020 to +0.0077) |
| 2019 to 2026 | all | early warning | 0.421 | 0.408 | 0.408 | 0.393 | -0.0139 (-0.0246 to -0.0043) | +0.0001 (-0.0144 to +0.0153) | -0.0147 (-0.0235 to -0.0059) |
| 2019 to 2026 | print | all books | 0.859 | 0.859 | 0.865 | 0.863 | -0.0001 (-0.0063 to +0.0069) | +0.0058 (-0.0036 to +0.0155) | +0.0035 (-0.0050 to +0.0127) |
| 2019 to 2026 | print | early warning | 0.495 | 0.497 | 0.503 | 0.487 | +0.0023 (-0.0100 to +0.0132) | +0.0056 (-0.0173 to +0.0286) | -0.0103 (-0.0219 to +0.0021) |
| 2019 to 2026 | ebook | all books | 0.809 | 0.823 | 0.837 | 0.823 | +0.0137 (+0.0046 to +0.0230) | +0.0138 (+0.0058 to +0.0242) | +0.0003 (-0.0059 to +0.0074) |
| 2019 to 2026 | ebook | early warning | 0.384 | 0.361 | 0.363 | 0.349 | -0.0228 (-0.0400 to -0.0074) | +0.0026 (-0.0156 to +0.0214) | -0.0117 (-0.0260 to +0.0019) |
| 2019 to 2026 | audiobook | all books | 0.820 | 0.829 | 0.841 | 0.833 | +0.0088 (+0.0029 to +0.0149) | +0.0115 (+0.0019 to +0.0233) | +0.0036 (-0.0022 to +0.0097) |
| 2019 to 2026 | audiobook | early warning | 0.386 | 0.364 | 0.356 | 0.342 | -0.0212 (-0.0367 to -0.0056) | -0.0079 (-0.0236 to +0.0076) | -0.0222 (-0.0387 to -0.0072) |
| 2024 to 2026 | all | all books | 0.859 | 0.861 | 0.870 | 0.864 | +0.0018 (-0.0032 to +0.0080) | +0.0091 (-0.0019 to +0.0210) | +0.0033 (-0.0046 to +0.0129) |
| 2024 to 2026 | all | early warning | 0.465 | 0.470 | 0.467 | 0.449 | +0.0042 (-0.0086 to +0.0154) | -0.0024 (-0.0265 to +0.0268) | -0.0209 (-0.0310 to -0.0114) |
| 2024 to 2026 | print | all books | 0.821 | 0.811 | 0.817 | 0.821 | -0.0100 (-0.0190 to +0.0012) | +0.0058 (-0.0181 to +0.0289) | +0.0100 (-0.0074 to +0.0304) |
| 2024 to 2026 | print | early warning | 0.530 | 0.547 | 0.568 | 0.547 | +0.0169 (+0.0067 to +0.0276) | +0.0219 (-0.0078 to +0.0538) | +0.0004 (-0.0129 to +0.0139) |
| 2024 to 2026 | ebook | all books | 0.874 | 0.880 | 0.897 | 0.882 | +0.0058 (-0.0021 to +0.0139) | +0.0169 (+0.0093 to +0.0257) | +0.0015 (-0.0050 to +0.0083) |
| 2024 to 2026 | ebook | early warning | 0.408 | 0.411 | 0.403 | 0.381 | +0.0035 (-0.0148 to +0.0218) | -0.0085 (-0.0408 to +0.0357) | -0.0300 (-0.0471 to -0.0114) |
| 2024 to 2026 | audiobook | all books | 0.882 | 0.892 | 0.896 | 0.890 | +0.0096 (+0.0050 to +0.0150) | +0.0046 (-0.0067 to +0.0196) | -0.0015 (-0.0093 to +0.0069) |
| 2024 to 2026 | audiobook | early warning | 0.459 | 0.451 | 0.430 | 0.418 | -0.0077 (-0.0340 to +0.0153) | -0.0208 (-0.0452 to +0.0057) | -0.0331 (-0.0593 to -0.0100) |

## Results by kind of book

Every group of every family fixed in advance is listed, whatever it shows. The models were fitted on all books; a group only restricts which books are ranked against each other. "Score" is the library model's score in that group. Each gain is a five-seed mean with its 95% interval. Marks: **found** = gain above zero after the Benjamini-Hochberg correction over all groups of that comparison; **differs** = the gain in this group differs from the gain in the other books of the same family after the same correction; *small* = fewer than 36 scored months or 1,000 rows, not judged. Groups defined from Wikidata (series, film or TV, award, translated, classic) cover only books matched to a Wikidata book item.

### Series (Khant)

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| in a series, known at the time | 120,125 | 78 | 0.295 | +0.0106 (+0.0076 to +0.0139) **found** | -0.0005 (-0.0015 to +0.0005) | -0.0007 (-0.0016 to +0.0003) |
| no series link known at the time | 165,706 | 78 | 0.354 | +0.0151 (+0.0125 to +0.0174) **found** | -0.0004 (-0.0010 to +0.0002) | -0.0002 (-0.0008 to +0.0004) |

### Film or TV adaptation (Khant)

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| film or TV version already out | 55,662 | 78 | 0.311 | +0.0167 (+0.0122 to +0.0217) **found** | +0.0019 (+0.0004 to +0.0033) **found** **differs** | +0.0001 (-0.0012 to +0.0014) |
| no film or TV version out yet | 230,169 | 78 | 0.336 | +0.0131 (+0.0108 to +0.0154) **found** | -0.0010 (-0.0018 to -0.0003) **differs** | -0.0006 (-0.0012 to +0.0001) |

### Popularity in the year before (Khant)

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| low | 260,656 | 77 | 0.362 | +0.0053 (+0.0026 to +0.0074) **found** | +0.0004 (-0.0004 to +0.0012) | +0.0006 (-0.0013 to +0.0019) |
| middle | 442,985 | 78 | 0.326 | +0.0048 (+0.0038 to +0.0059) **found** | +0.0019 (+0.0011 to +0.0027) **found** **differs** | +0.0013 (+0.0007 to +0.0020) **found** **differs** |
| high | 555,166 | 78 | 0.344 | +0.0044 (+0.0031 to +0.0056) **found** | -0.0005 (-0.0010 to -0.0001) **differs** | +0.0001 (-0.0005 to +0.0007) **differs** |

### Fiction or nonfiction

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| fiction | 827,393 | 78 | 0.343 | +0.0055 (+0.0044 to +0.0065) **found** **differs** | +0.0009 (+0.0003 to +0.0014) **found** **differs** | +0.0002 (-0.0003 to +0.0007) **differs** |
| nonfiction | 412,596 | 78 | 0.354 | +0.0033 (+0.0025 to +0.0041) **found** **differs** | -0.0002 (-0.0007 to +0.0002) **differs** | +0.0019 (+0.0012 to +0.0026) **found** **differs** |
| other (mixed or unknown) | 18,818 | 78 | 0.325 | +0.0127 (+0.0070 to +0.0182) **found** **differs** | +0.0026 (+0.0001 to +0.0052) | +0.0002 (-0.0019 to +0.0022) |

### Audience

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| adult | 839,677 | 78 | 0.369 | +0.0063 (+0.0053 to +0.0072) **found** **differs** | -0.0000 (-0.0004 to +0.0004) | +0.0008 (+0.0003 to +0.0014) **found** **differs** |
| children | 360,814 | 78 | 0.286 | +0.0018 (+0.0002 to +0.0035) **found** **differs** | +0.0007 (-0.0004 to +0.0017) | -0.0006 (-0.0015 to +0.0003) **differs** |
| young adult | 58,316 | 78 | 0.319 | +0.0065 (+0.0034 to +0.0099) **found** | -0.0001 (-0.0010 to +0.0008) | -0.0011 (-0.0021 to -0.0001) **differs** |

### Format

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| audiobook | 340,064 | 78 | 0.361 | +0.0059 (+0.0044 to +0.0075) **found** | -0.0002 (-0.0005 to +0.0003) **differs** | +0.0004 (-0.0002 to +0.0010) |
| ebook | 446,291 | 78 | 0.348 | +0.0049 (+0.0039 to +0.0060) **found** | -0.0006 (-0.0011 to -0.0000) **differs** | +0.0000 (-0.0004 to +0.0004) **differs** |
| print | 472,452 | 78 | 0.333 | +0.0038 (+0.0029 to +0.0049) **found** **differs** | +0.0024 (+0.0013 to +0.0034) **found** **differs** | +0.0020 (+0.0010 to +0.0030) **found** **differs** |

### Time since first Seattle loan

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| under 1 year | 199,907 | 78 | 0.417 | +0.0042 (+0.0030 to +0.0054) **found** | -0.0001 (-0.0010 to +0.0010) | +0.0025 (+0.0014 to +0.0037) **found** **differs** |
| 1 to 5 years | 548,026 | 78 | 0.330 | +0.0038 (+0.0029 to +0.0047) **found** **differs** | +0.0007 (+0.0002 to +0.0012) **found** | +0.0009 (+0.0003 to +0.0015) **found** |
| 5 years or more | 510,874 | 78 | 0.310 | +0.0060 (+0.0045 to +0.0075) **found** **differs** | +0.0007 (-0.0000 to +0.0013) | +0.0002 (-0.0004 to +0.0008) **differs** |

### Author's earlier Seattle books

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| no | 360,676 | 78 | 0.351 | +0.0047 (+0.0034 to +0.0060) **found** | +0.0002 (-0.0004 to +0.0008) | +0.0009 (+0.0004 to +0.0015) **found** |
| unknown | 7,372 | 78 | 0.330 | -0.0001 (-0.0026 to +0.0023) **differs** | +0.0126 (+0.0051 to +0.0222) **found** **differs** | +0.0080 (+0.0002 to +0.0172) |
| yes | 890,709 | 78 | 0.346 | +0.0049 (+0.0040 to +0.0058) **found** | +0.0007 (+0.0002 to +0.0012) **found** | +0.0007 (+0.0001 to +0.0012) |

### Own Wikipedia article

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| author article only | 516,918 | 78 | 0.354 | +0.0038 (+0.0027 to +0.0049) **found** | +0.0004 (-0.0001 to +0.0009) | +0.0010 (+0.0004 to +0.0016) **found** |
| book article | 265,942 | 78 | 0.326 | +0.0146 (+0.0123 to +0.0170) **found** **differs** | -0.0003 (-0.0010 to +0.0003) **differs** | -0.0003 (-0.0009 to +0.0004) **differs** |
| neither | 475,947 | 78 | 0.347 | +0.0012 (+0.0002 to +0.0022) **found** **differs** | +0.0013 (+0.0006 to +0.0019) **found** **differs** | +0.0016 (+0.0009 to +0.0026) **found** **differs** |

### Award

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| award won by then | 34,142 | 78 | 0.304 | +0.0210 (+0.0163 to +0.0257) **found** **differs** | -0.0001 (-0.0016 to +0.0013) | -0.0010 (-0.0027 to +0.0006) |
| no award known by then | 251,689 | 78 | 0.335 | +0.0125 (+0.0101 to +0.0149) **found** **differs** | -0.0005 (-0.0012 to +0.0001) | -0.0003 (-0.0008 to +0.0003) |

### Translated

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| translated | 17,953 | 78 | 0.312 | +0.0165 (+0.0090 to +0.0245) **found** | -0.0018 (-0.0031 to -0.0005) | -0.0004 (-0.0028 to +0.0021) |
| written in English | 254,007 | 78 | 0.331 | +0.0132 (+0.0110 to +0.0154) **found** | -0.0003 (-0.0010 to +0.0003) | -0.0005 (-0.0012 to +0.0001) |

### Public-domain classic

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| 1930 or later | 242,178 | 78 | 0.321 | +0.0140 (+0.0115 to +0.0165) **found** | -0.0007 (-0.0015 to +0.0001) **differs** | -0.0006 (-0.0013 to +0.0001) |
| first published before 1930 | 13,333 | 78 | 0.335 | +0.0086 (+0.0019 to +0.0152) **found** | +0.0052 (+0.0011 to +0.0096) **found** **differs** | +0.0015 (-0.0014 to +0.0046) |

### Genre (broad theme)

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| B01 Magic, myth and the supernatural | 117,139 | 78 | 0.307 | +0.0051 (+0.0033 to +0.0070) **found** | -0.0012 (-0.0020 to -0.0004) **differs** | -0.0018 (-0.0026 to -0.0011) **differs** |
| B02 Gender, sexuality and relationships | 106,306 | 78 | 0.371 | +0.0055 (+0.0038 to +0.0072) **found** | +0.0004 (-0.0005 to +0.0015) | -0.0010 (-0.0018 to -0.0003) **differs** |
| B03 Religion and spirituality | 29,838 | 78 | 0.336 | +0.0068 (+0.0034 to +0.0106) **found** | -0.0040 (-0.0071 to -0.0012) **differs** | -0.0008 (-0.0021 to +0.0006) |
| B04 Science, technology and learning | 64,777 | 78 | 0.321 | +0.0060 (+0.0033 to +0.0089) **found** | -0.0005 (-0.0018 to +0.0007) | -0.0010 (-0.0020 to -0.0001) **differs** |
| B05 Race, ethnicity and migration | 49,860 | 78 | 0.376 | +0.0065 (+0.0043 to +0.0089) **found** | -0.0012 (-0.0023 to -0.0002) **differs** | -0.0016 (-0.0027 to -0.0005) **differs** |
| B06 Arts, media and entertainment | 70,364 | 78 | 0.359 | +0.0061 (+0.0042 to +0.0081) **found** | +0.0001 (-0.0012 to +0.0013) | +0.0020 (+0.0006 to +0.0035) **found** |
| B07 Childhood, family and growing up | 113,354 | 78 | 0.353 | +0.0050 (+0.0032 to +0.0065) **found** | -0.0008 (-0.0016 to +0.0000) **differs** | -0.0014 (-0.0021 to -0.0006) **differs** |
| B08 War, conflict and history | 74,991 | 78 | 0.354 | +0.0076 (+0.0053 to +0.0097) **found** **differs** | +0.0000 (-0.0010 to +0.0010) | -0.0001 (-0.0010 to +0.0008) |
| B09 Nature, places and the environment | 96,529 | 78 | 0.355 | +0.0063 (+0.0041 to +0.0085) **found** | +0.0003 (-0.0009 to +0.0014) | +0.0010 (-0.0002 to +0.0024) |
| B10 Work, business and money | 34,342 | 78 | 0.327 | +0.0038 (+0.0006 to +0.0071) **found** | -0.0021 (-0.0038 to -0.0007) **differs** | -0.0006 (-0.0019 to +0.0008) |
| B11 Food, home and holidays | 51,305 | 78 | 0.396 | +0.0043 (+0.0017 to +0.0068) **found** | +0.0127 (+0.0083 to +0.0173) **found** **differs** | +0.0064 (+0.0031 to +0.0098) **found** **differs** |
| B12 Violence, trauma, death and grief | 47,097 | 78 | 0.373 | +0.0048 (+0.0026 to +0.0069) **found** | -0.0013 (-0.0021 to -0.0005) **differs** | -0.0005 (-0.0018 to +0.0007) |
| B13 Politics, society and justice | 34,610 | 78 | 0.397 | +0.0068 (+0.0035 to +0.0105) **found** | +0.0006 (-0.0007 to +0.0021) | +0.0035 (+0.0017 to +0.0054) **found** **differs** |
| B14 Mind, self and philosophy | 72,637 | 78 | 0.331 | +0.0035 (+0.0015 to +0.0057) **found** | -0.0006 (-0.0014 to +0.0002) **differs** | -0.0008 (-0.0017 to +0.0001) **differs** |
| B15 Health, illness and addiction | 28,119 | 78 | 0.320 | +0.0065 (+0.0022 to +0.0109) **found** | -0.0005 (-0.0020 to +0.0009) | +0.0000 (-0.0012 to +0.0012) |
| B16 Animals | 73,393 | 78 | 0.301 | +0.0034 (+0.0004 to +0.0067) **found** | -0.0002 (-0.0017 to +0.0014) | -0.0010 (-0.0019 to -0.0000) **differs** |
| B17 Sports, games and fitness | 18,180 | 78 | 0.324 | -0.0045 (-0.0089 to -0.0002) **differs** | -0.0019 (-0.0055 to +0.0009) | -0.0031 (-0.0058 to -0.0003) **differs** |
| B18 Space and the universe | 14,185 | 78 | 0.292 | +0.0079 (+0.0021 to +0.0135) **found** | -0.0005 (-0.0029 to +0.0016) | -0.0021 (-0.0043 to +0.0000) **differs** |
| B19 Crime, police and law | 51,005 | 78 | 0.346 | +0.0078 (+0.0047 to +0.0111) **found** | -0.0011 (-0.0028 to +0.0004) | +0.0002 (-0.0012 to +0.0016) |
| no theme | 110,776 | 78 | 0.335 | +0.0045 (+0.0027 to +0.0065) **found** | +0.0016 (+0.0003 to +0.0028) **found** | +0.0020 (+0.0009 to +0.0031) **found** |

### Has a theme

| Group | Rows | Months | Score (library) | Own and author pages | Theme pages, hand-reviewed | Theme pages, AI-sorted |
| --- | --- | --- | --- | --- | --- | --- |
| no | 162,732 | 78 | 0.344 | +0.0048 (+0.0033 to +0.0064) **found** | +0.0029 (+0.0019 to +0.0038) **found** **differs** | +0.0034 (+0.0026 to +0.0042) **found** **differs** |
| yes | 1,096,075 | 78 | 0.348 | +0.0048 (+0.0039 to +0.0057) **found** | +0.0001 (-0.0004 to +0.0006) **differs** | +0.0003 (-0.0002 to +0.0009) **differs** |

### Groups that stand out after correction

- Own and author pages, Series (Khant): in a series, known at the time: gain +0.0106 (+0.0076 to +0.0139), adjusted p 0.001.
- Own and author pages, Series (Khant): no series link known at the time: gain +0.0151 (+0.0125 to +0.0174), adjusted p 0.001.
- Own and author pages, Film or TV adaptation (Khant): film or TV version already out: gain +0.0167 (+0.0122 to +0.0217), adjusted p 0.001.
- Theme pages, hand-reviewed, Film or TV adaptation (Khant): film or TV version already out: gain +0.0019 (+0.0004 to +0.0033), adjusted p 0.047; larger than in the other books by +0.0029 (+0.0012 to +0.0046), adjusted p 0.004.
- Own and author pages, Film or TV adaptation (Khant): no film or TV version out yet: gain +0.0131 (+0.0108 to +0.0154), adjusted p 0.001.
- Theme pages, hand-reviewed, Film or TV adaptation (Khant): no film or TV version out yet: smaller than in the other books by -0.0029 (-0.0046 to -0.0012), adjusted p 0.004.
- Own and author pages, Popularity in the year before (Khant): high: gain +0.0044 (+0.0031 to +0.0056), adjusted p 0.001.
- Theme pages, hand-reviewed, Popularity in the year before (Khant): high: smaller than in the other books by -0.0020 (-0.0028 to -0.0012), adjusted p 0.004.
- Theme pages, AI-sorted, Popularity in the year before (Khant): high: smaller than in the other books by -0.0014 (-0.0020 to -0.0007), adjusted p 0.008.
- Own and author pages, Popularity in the year before (Khant): low: gain +0.0053 (+0.0026 to +0.0074), adjusted p 0.001.
- Own and author pages, Popularity in the year before (Khant): middle: gain +0.0048 (+0.0038 to +0.0059), adjusted p 0.001.
- Theme pages, hand-reviewed, Popularity in the year before (Khant): middle: gain +0.0019 (+0.0011 to +0.0027), adjusted p 0.009; larger than in the other books by +0.0021 (+0.0014 to +0.0028), adjusted p 0.004.
- Theme pages, AI-sorted, Popularity in the year before (Khant): middle: gain +0.0013 (+0.0007 to +0.0020), adjusted p 0.004; larger than in the other books by +0.0008 (+0.0002 to +0.0015), adjusted p 0.026.
- Own and author pages, Fiction or nonfiction: fiction: gain +0.0055 (+0.0044 to +0.0065), adjusted p 0.001; larger than in the other books by +0.0019 (+0.0009 to +0.0029), adjusted p 0.005.
- Theme pages, hand-reviewed, Fiction or nonfiction: fiction: gain +0.0009 (+0.0003 to +0.0014), adjusted p 0.018; larger than in the other books by +0.0010 (+0.0004 to +0.0016), adjusted p 0.011.
- Theme pages, AI-sorted, Fiction or nonfiction: fiction: smaller than in the other books by -0.0016 (-0.0025 to -0.0009), adjusted p 0.004.
- Own and author pages, Fiction or nonfiction: nonfiction: gain +0.0033 (+0.0025 to +0.0041), adjusted p 0.001; smaller than in the other books by -0.0023 (-0.0034 to -0.0014), adjusted p 0.005.
- Theme pages, hand-reviewed, Fiction or nonfiction: nonfiction: smaller than in the other books by -0.0012 (-0.0017 to -0.0006), adjusted p 0.004.
- Theme pages, AI-sorted, Fiction or nonfiction: nonfiction: gain +0.0019 (+0.0012 to +0.0026), adjusted p 0.004; larger than in the other books by +0.0017 (+0.0009 to +0.0026), adjusted p 0.004.
- Own and author pages, Fiction or nonfiction: other (mixed or unknown): gain +0.0127 (+0.0070 to +0.0182), adjusted p 0.001; larger than in the other books by +0.0079 (+0.0025 to +0.0133), adjusted p 0.023.
- Own and author pages, Audience: adult: gain +0.0063 (+0.0053 to +0.0072), adjusted p 0.001; larger than in the other books by +0.0034 (+0.0021 to +0.0047), adjusted p 0.005.
- Theme pages, AI-sorted, Audience: adult: gain +0.0008 (+0.0003 to +0.0014), adjusted p 0.004; larger than in the other books by +0.0015 (+0.0007 to +0.0024), adjusted p 0.006.
- Own and author pages, Audience: children: gain +0.0018 (+0.0002 to +0.0035), adjusted p 0.036; smaller than in the other books by -0.0045 (-0.0062 to -0.0030), adjusted p 0.005.
- Theme pages, AI-sorted, Audience: children: smaller than in the other books by -0.0013 (-0.0022 to -0.0004), adjusted p 0.008.
- Own and author pages, Audience: young adult: gain +0.0065 (+0.0034 to +0.0099), adjusted p 0.001.
- Theme pages, AI-sorted, Audience: young adult: smaller than in the other books by -0.0020 (-0.0031 to -0.0009), adjusted p 0.004.
- Own and author pages, Format: audiobook: gain +0.0059 (+0.0044 to +0.0075), adjusted p 0.001.
- Theme pages, hand-reviewed, Format: audiobook: smaller than in the other books by -0.0011 (-0.0017 to -0.0004), adjusted p 0.015.
- Own and author pages, Format: ebook: gain +0.0049 (+0.0039 to +0.0060), adjusted p 0.001.
- Theme pages, hand-reviewed, Format: ebook: smaller than in the other books by -0.0017 (-0.0024 to -0.0009), adjusted p 0.004.
- Theme pages, AI-sorted, Format: ebook: smaller than in the other books by -0.0012 (-0.0020 to -0.0003), adjusted p 0.016.
- Own and author pages, Format: print: gain +0.0038 (+0.0029 to +0.0049), adjusted p 0.001; smaller than in the other books by -0.0016 (-0.0026 to -0.0005), adjusted p 0.013.
- Theme pages, hand-reviewed, Format: print: gain +0.0024 (+0.0013 to +0.0034), adjusted p 0.009; larger than in the other books by +0.0028 (+0.0016 to +0.0039), adjusted p 0.004.
- Theme pages, AI-sorted, Format: print: gain +0.0020 (+0.0010 to +0.0030), adjusted p 0.004; larger than in the other books by +0.0018 (+0.0008 to +0.0028), adjusted p 0.004.
- Own and author pages, Time since first Seattle loan: 1 to 5 years: gain +0.0038 (+0.0029 to +0.0047), adjusted p 0.001; smaller than in the other books by -0.0016 (-0.0027 to -0.0005), adjusted p 0.023.
- Theme pages, hand-reviewed, Time since first Seattle loan: 1 to 5 years: gain +0.0007 (+0.0002 to +0.0012), adjusted p 0.039.
- Theme pages, AI-sorted, Time since first Seattle loan: 1 to 5 years: gain +0.0009 (+0.0003 to +0.0015), adjusted p 0.011.
- Own and author pages, Time since first Seattle loan: 5 years or more: gain +0.0060 (+0.0045 to +0.0075), adjusted p 0.001; larger than in the other books by +0.0023 (+0.0009 to +0.0035), adjusted p 0.013.
- Theme pages, AI-sorted, Time since first Seattle loan: 5 years or more: smaller than in the other books by -0.0009 (-0.0016 to -0.0003), adjusted p 0.018.
- Own and author pages, Time since first Seattle loan: under 1 year: gain +0.0042 (+0.0030 to +0.0054), adjusted p 0.001.
- Theme pages, AI-sorted, Time since first Seattle loan: under 1 year: gain +0.0025 (+0.0014 to +0.0037), adjusted p 0.004; larger than in the other books by +0.0019 (+0.0008 to +0.0031), adjusted p 0.006.
- Own and author pages, Author's earlier Seattle books: no: gain +0.0047 (+0.0034 to +0.0060), adjusted p 0.001.
- Theme pages, AI-sorted, Author's earlier Seattle books: no: gain +0.0009 (+0.0004 to +0.0015), adjusted p 0.013.
- Own and author pages, Author's earlier Seattle books: unknown: smaller than in the other books by -0.0050 (-0.0078 to -0.0024), adjusted p 0.005.
- Theme pages, hand-reviewed, Author's earlier Seattle books: unknown: gain +0.0126 (+0.0051 to +0.0222), adjusted p 0.009; larger than in the other books by +0.0121 (+0.0045 to +0.0218), adjusted p 0.006.
- Own and author pages, Author's earlier Seattle books: yes: gain +0.0049 (+0.0040 to +0.0058), adjusted p 0.001.
- Theme pages, hand-reviewed, Author's earlier Seattle books: yes: gain +0.0007 (+0.0002 to +0.0012), adjusted p 0.037.
- Own and author pages, Own Wikipedia article: author article only: gain +0.0038 (+0.0027 to +0.0049), adjusted p 0.001.
- Theme pages, AI-sorted, Own Wikipedia article: author article only: gain +0.0010 (+0.0004 to +0.0016), adjusted p 0.004.
- Own and author pages, Own Wikipedia article: book article: gain +0.0146 (+0.0123 to +0.0170), adjusted p 0.001; larger than in the other books by +0.0118 (+0.0095 to +0.0140), adjusted p 0.005.
- Theme pages, hand-reviewed, Own Wikipedia article: book article: smaller than in the other books by -0.0012 (-0.0021 to -0.0004), adjusted p 0.006.
- Theme pages, AI-sorted, Own Wikipedia article: book article: smaller than in the other books by -0.0015 (-0.0023 to -0.0007), adjusted p 0.004.
- Own and author pages, Own Wikipedia article: neither: gain +0.0012 (+0.0002 to +0.0022), adjusted p 0.021; smaller than in the other books by -0.0058 (-0.0074 to -0.0040), adjusted p 0.005.
- Theme pages, hand-reviewed, Own Wikipedia article: neither: gain +0.0013 (+0.0006 to +0.0019), adjusted p 0.009; larger than in the other books by +0.0012 (+0.0005 to +0.0019), adjusted p 0.004.
- Theme pages, AI-sorted, Own Wikipedia article: neither: gain +0.0016 (+0.0009 to +0.0026), adjusted p 0.004; larger than in the other books by +0.0011 (+0.0004 to +0.0020), adjusted p 0.004.
- Own and author pages, Award: award won by then: gain +0.0210 (+0.0163 to +0.0257), adjusted p 0.001; larger than in the other books by +0.0085 (+0.0036 to +0.0133), adjusted p 0.005.
- Own and author pages, Award: no award known by then: gain +0.0125 (+0.0101 to +0.0149), adjusted p 0.001; smaller than in the other books by -0.0085 (-0.0133 to -0.0036), adjusted p 0.005.
- Own and author pages, Translated: translated: gain +0.0165 (+0.0090 to +0.0245), adjusted p 0.001.
- Own and author pages, Translated: written in English: gain +0.0132 (+0.0110 to +0.0154), adjusted p 0.001.
- Own and author pages, Public-domain classic: 1930 or later: gain +0.0140 (+0.0115 to +0.0165), adjusted p 0.001.
- Theme pages, hand-reviewed, Public-domain classic: 1930 or later: smaller than in the other books by -0.0059 (-0.0109 to -0.0013), adjusted p 0.023.
- Own and author pages, Public-domain classic: first published before 1930: gain +0.0086 (+0.0019 to +0.0152), adjusted p 0.020.
- Theme pages, hand-reviewed, Public-domain classic: first published before 1930: gain +0.0052 (+0.0011 to +0.0096), adjusted p 0.040; larger than in the other books by +0.0059 (+0.0013 to +0.0109), adjusted p 0.023.
- Own and author pages, Genre (broad theme): B01 Magic, myth and the supernatural: gain +0.0051 (+0.0033 to +0.0070), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B01 Magic, myth and the supernatural: smaller than in the other books by -0.0018 (-0.0027 to -0.0010), adjusted p 0.004.
- Theme pages, AI-sorted, Genre (broad theme): B01 Magic, myth and the supernatural: smaller than in the other books by -0.0029 (-0.0038 to -0.0020), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B02 Gender, sexuality and relationships: gain +0.0055 (+0.0038 to +0.0072), adjusted p 0.001.
- Theme pages, AI-sorted, Genre (broad theme): B02 Gender, sexuality and relationships: smaller than in the other books by -0.0019 (-0.0026 to -0.0012), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B03 Religion and spirituality: gain +0.0068 (+0.0034 to +0.0106), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B03 Religion and spirituality: smaller than in the other books by -0.0047 (-0.0077 to -0.0019), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B04 Science, technology and learning: gain +0.0060 (+0.0033 to +0.0089), adjusted p 0.001.
- Theme pages, AI-sorted, Genre (broad theme): B04 Science, technology and learning: smaller than in the other books by -0.0019 (-0.0030 to -0.0008), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B05 Race, ethnicity and migration: gain +0.0065 (+0.0043 to +0.0089), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B05 Race, ethnicity and migration: smaller than in the other books by -0.0018 (-0.0031 to -0.0007), adjusted p 0.006.
- Theme pages, AI-sorted, Genre (broad theme): B05 Race, ethnicity and migration: smaller than in the other books by -0.0025 (-0.0036 to -0.0014), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B06 Arts, media and entertainment: gain +0.0061 (+0.0042 to +0.0081), adjusted p 0.001.
- Theme pages, AI-sorted, Genre (broad theme): B06 Arts, media and entertainment: gain +0.0020 (+0.0006 to +0.0035), adjusted p 0.022.
- Own and author pages, Genre (broad theme): B07 Childhood, family and growing up: gain +0.0050 (+0.0032 to +0.0065), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B07 Childhood, family and growing up: smaller than in the other books by -0.0014 (-0.0023 to -0.0007), adjusted p 0.006.
- Theme pages, AI-sorted, Genre (broad theme): B07 Childhood, family and growing up: smaller than in the other books by -0.0024 (-0.0031 to -0.0016), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B08 War, conflict and history: gain +0.0076 (+0.0053 to +0.0097), adjusted p 0.001; larger than in the other books by +0.0028 (+0.0009 to +0.0048), adjusted p 0.025.
- Own and author pages, Genre (broad theme): B09 Nature, places and the environment: gain +0.0063 (+0.0041 to +0.0085), adjusted p 0.001.
- Own and author pages, Genre (broad theme): B10 Work, business and money: gain +0.0038 (+0.0006 to +0.0071), adjusted p 0.018.
- Theme pages, hand-reviewed, Genre (broad theme): B10 Work, business and money: smaller than in the other books by -0.0027 (-0.0043 to -0.0013), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B11 Food, home and holidays: gain +0.0043 (+0.0017 to +0.0068), adjusted p 0.002.
- Theme pages, hand-reviewed, Genre (broad theme): B11 Food, home and holidays: gain +0.0127 (+0.0083 to +0.0173), adjusted p 0.009; larger than in the other books by +0.0130 (+0.0086 to +0.0175), adjusted p 0.004.
- Theme pages, AI-sorted, Genre (broad theme): B11 Food, home and holidays: gain +0.0064 (+0.0031 to +0.0098), adjusted p 0.004; larger than in the other books by +0.0060 (+0.0027 to +0.0095), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B12 Violence, trauma, death and grief: gain +0.0048 (+0.0026 to +0.0069), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B12 Violence, trauma, death and grief: smaller than in the other books by -0.0019 (-0.0028 to -0.0011), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B13 Politics, society and justice: gain +0.0068 (+0.0035 to +0.0105), adjusted p 0.001.
- Theme pages, AI-sorted, Genre (broad theme): B13 Politics, society and justice: gain +0.0035 (+0.0017 to +0.0054), adjusted p 0.004; larger than in the other books by +0.0029 (+0.0010 to +0.0048), adjusted p 0.013.
- Own and author pages, Genre (broad theme): B14 Mind, self and philosophy: gain +0.0035 (+0.0015 to +0.0057), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): B14 Mind, self and philosophy: smaller than in the other books by -0.0013 (-0.0021 to -0.0004), adjusted p 0.029.
- Theme pages, AI-sorted, Genre (broad theme): B14 Mind, self and philosophy: smaller than in the other books by -0.0016 (-0.0025 to -0.0006), adjusted p 0.004.
- Own and author pages, Genre (broad theme): B15 Health, illness and addiction: gain +0.0065 (+0.0022 to +0.0109), adjusted p 0.002.
- Own and author pages, Genre (broad theme): B16 Animals: gain +0.0034 (+0.0004 to +0.0067), adjusted p 0.028.
- Theme pages, AI-sorted, Genre (broad theme): B16 Animals: smaller than in the other books by -0.0017 (-0.0028 to -0.0007), adjusted p 0.008.
- Own and author pages, Genre (broad theme): B17 Sports, games and fitness: smaller than in the other books by -0.0095 (-0.0141 to -0.0049), adjusted p 0.005.
- Theme pages, AI-sorted, Genre (broad theme): B17 Sports, games and fitness: smaller than in the other books by -0.0040 (-0.0067 to -0.0012), adjusted p 0.016.
- Own and author pages, Genre (broad theme): B18 Space and the universe: gain +0.0079 (+0.0021 to +0.0135), adjusted p 0.009.
- Theme pages, AI-sorted, Genre (broad theme): B18 Space and the universe: smaller than in the other books by -0.0029 (-0.0051 to -0.0006), adjusted p 0.025.
- Own and author pages, Genre (broad theme): B19 Crime, police and law: gain +0.0078 (+0.0047 to +0.0111), adjusted p 0.001.
- Own and author pages, Genre (broad theme): no theme: gain +0.0045 (+0.0027 to +0.0065), adjusted p 0.001.
- Theme pages, hand-reviewed, Genre (broad theme): no theme: gain +0.0016 (+0.0003 to +0.0028), adjusted p 0.047.
- Theme pages, AI-sorted, Genre (broad theme): no theme: gain +0.0020 (+0.0009 to +0.0031), adjusted p 0.004.
- Own and author pages, Has a theme: no: gain +0.0048 (+0.0033 to +0.0064), adjusted p 0.001.
- Theme pages, hand-reviewed, Has a theme: no: gain +0.0029 (+0.0019 to +0.0038), adjusted p 0.009; larger than in the other books by +0.0027 (+0.0016 to +0.0039), adjusted p 0.004.
- Theme pages, AI-sorted, Has a theme: no: gain +0.0034 (+0.0026 to +0.0042), adjusted p 0.004; larger than in the other books by +0.0030 (+0.0020 to +0.0041), adjusted p 0.004.
- Own and author pages, Has a theme: yes: gain +0.0048 (+0.0039 to +0.0057), adjusted p 0.001.
- Theme pages, hand-reviewed, Has a theme: yes: smaller than in the other books by -0.0027 (-0.0039 to -0.0016), adjusted p 0.004.
- Theme pages, AI-sorted, Has a theme: yes: smaller than in the other books by -0.0030 (-0.0041 to -0.0020), adjusted p 0.004.

## Data behind the test

- Theme pages: 328 themes with hand-reviewed pages and 327 with AI-sorted pages had a weekly series. Share of scored rows whose book had a narrow-theme feature: 87.1% (hand-reviewed), 87.1% (AI-sorted); books with no catalogue theme have none.
- AI-sorted pages counted from the month of their second day in the daily top 500, by year: {'2016': 8861, '2017': 5253, '2018': 4166, '2019': 3732, '2020': 3483, '2021': 3019, '2022': 2690, '2023': 2468, '2024': 2503, '2025': 2455, '2026': 1370}.
- Wikidata book items: 4,065 of 43,298 main-set works; 1,198 follow an earlier book; 600 have a dated film or TV adaptation; 374 a dated award; 180 were first published before 1930.
- Checks: the copied feature code reproduces the stored features of the book articles exactly; all AI-sorted pages together reproduce the stored theme series; the library and own-page scores, their intervals and the five-seed gains of 20 November are reproduced exactly.

## Limits

- The 40,000 AI-sorted pages were picked by how often they were among the most viewed over the whole period; counting each page only from its second top-500 day removes most, not all, of this look-ahead.
- The hand-reviewed pages were chosen by meaning, not traffic, but by someone who knew the earlier theme results.
- Wikidata facts cover only books matched to a Wikidata book item, mostly well-known ones; which books have an item uses Wikidata as of October 2026.
- A group result describes the books of that group in this sample. It is not the effect of being that kind of book.
- Bestseller-list history was not used as a split: its matching was checked only for the well-known books.
- Popularity thirds are cut over every book-format with a scored month in that test year, so a book's third can depend slightly on which other books became eligible later in the same year (mostly new books with no loans the year before). No prediction uses the thirds.
- "Rows" in the group tables are scored rows (in format-months with at least 3 books of the group).

