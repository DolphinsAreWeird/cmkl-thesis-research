# Four directions to improve prediction (addendum i): comparison

Written 22 Oct 2026, 05:30 +07, for Khant Phyo Wai (student ID 01323050). Record: `prereg/addenda_wiki_led/2026-10-22_i_directions.json`, fixed at 03:13 and public on GitHub before any result. All four directions are exploratory and all are reported. Details and intervals are in the four reports named below.

## In five lines

1. The best new direction is the **event calendar**: a film or TV release, or the author's death, marks books whose borrowing jumps (about 35% of flagged books surge within three months, against about 6% of books in general), and the library model misses most of them.
2. **Sales lists** are the second: Wikipedia predicts which books join a New York Times list next month far above chance (AUC 0.82), close to the library history (0.86); the two together reach 0.88, and for books held three years or more Wikipedia alone does as well as the library history.
3. **Longer windows do not help Wikipedia**: for books it adds about +0.010 to the library model at 1, 3, 6 and 12 months alike, while the library model itself gets much better further ahead; for themes the link does not grow either.
4. The **hand-checked topic pages** keep their effect for about six months (about 10 to 11% more borrowing in months 0 to 5, about 5% in months 6 to 11); the AI-sorted theme series show no lasting effect.
5. **Intent signals** (Open Library "want to read" counts) are being collected weekly from now; there is no history to test yet.

## Direction by direction

| Direction | Fixed measure | Result | What it means |
| --- | --- | --- | --- |
| D1 books: 1, 3, 6, 12 months ahead | Spearman of predicted and actual change; library + Wikipedia minus library | Wikipedia alone 0.133, 0.158, 0.157, 0.160; library 0.350, 0.444, 0.481, 0.509; added value +0.009, +0.011, +0.011, +0.010 (no growth; changes from k = 1 all include 0) | Averages over longer windows are easier to rank for every model; Wikipedia does not see further ahead than the library does |
| D1 themes: ranking 3 to 12 months ahead | Wikipedia-only rank correlation per window | Hand-checked topic pages 0.026 (1 month) falling to -0.002 (12 months); AI series at or below 0 | No gain from longer windows |
| D1 themes: effect after lasting rises | Borrowing against a blend of other themes, months 0 to 2, 3 to 5, 6 to 11 | Hand-checked topic pages +0.093, +0.107, +0.048 (log; about +10%, +11%, +5%); AI topic pages +0.028, +0.012, +0.019; all AI pages +0.018, +0.016, +0.008 | Real topic attention keeps borrowing up for about half a year; the AI series' small effect does not last |
| D2 event calendar | Share of flagged books that rose or surged, against matched books and the base rate | Film or TV release: 45.9% rose against 10.4% for matched books (+35.5 points); author's death +32.3 points; dated awards +3.0. Release alert: 54.3% rose and 34.7% surged in the next three months, against 22.8% and 6.4% | A strong, practical alert for a small group of books: these events sit near only 4.8% of all big surges, and swapping them into the library model's top 20 did not raise its hit rate |
| D3 sales (NYT lists) | AUC for a list appearance next month among books not on a list | Wikipedia 0.818, library 0.856, both 0.877 (+0.021); books held 3 years or more: Wikipedia 0.794, library 0.791 | Wikipedia predicts sales lists better than it predicts borrowing changes; library and sales move mostly in the same month, and loans run about 1.7 to 1.9 times those of similar books after a book's first NYT week |
| D4 intent (Open Library) | Collection only | Weekly collector installed (launchd); mapping of the 7,747 and 20,000 books to Open Library works under way at 1 request a second | Testable once a few months of history exist |

## Honest limits

- Event dates come from Wikidata and may have been entered after the event, so the calendar is a little better than what was known at the time; keeping only adaptations whose article already had views gives the same picture. Big literary prizes cannot be tested: Wikidata dates 95% of award statements only to the year.
- The NYT matches cover 2,892 of the 7,747 works (mostly recent, heavily borrowed bestsellers), matched mostly by title and author, with a hand check of 50 of 50 right on the final sample.
- Several comparisons were added after first results (D2's not-yet-risen comparison, D3's split by time in the library and placebos); each is labelled in its report and in `prereg/DEVIATIONS.md`.
- One library (Seattle) and one sales source (NYT lists, which cover only the top of the market).

## What to try next

- Combine the library model with the event calendar and the NYT signal in one alert list, fixed in advance, and score it on the live months (the October lists are already frozen).
- For sales, add a daily sales-rank source across apps (paid, needs approval) and Google Trends once official access exists; Open Library intent becomes testable in a few months.

## Reports

`dir_d1_horizons_books.md`, `dir_d1_horizons_themes.md`, `dir_d2_events.md`, `dir_d3_nyt.md` (all in `data/reports/`); code in `code/main_study/wiki_led/dirs/`; the collector in `collectors/` (deployed to `~/thesis-collectors`).
