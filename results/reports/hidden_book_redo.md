# Hidden-book weekly model, redone with an own-listening baseline and a time-blocked split

Code: code/hidden_book_redo.py. Tables: hidden_book_redo_auc.csv, hidden_book_redo_by_year.csv, hidden_book_redo_attention_gain.csv. Old code and reports were not changed.

## What was tested
Same panel as the old weekly model (766 LibriVox books, 218,307 book-weeks, weeks near a book's release removed, books with a median of under 3 weekly listens removed). The question for each book-week: will listening over the next 4 weeks reach 1.5 times the book's own 26-week median? 8.2% of weeks say yes. "Hot" weeks are those where Wikipedia attention is at least 2 times the book's own 26-week median (5,019 weeks).

Three models, all gradient-boosted trees with the same settings as the old model:
- Attention only: the old model's inputs (this week's and recent attention, trend, level, calendar month). It does not use the book's own listening. This reproduces the old numbers (0.618 and 0.712).
- Own listening only: the book's listening in the last 1, 4 and 8 weeks compared with its own 26-week median, its own listening level, and the calendar month. No attention.
- Both.
Plus one rule with no fitting: the last 4 weeks of own listening relative to the 26-week median.

Two splits:
- A, book split: the old 5 folds by book, weeks from all years mixed.
- B, time-blocked walk-forward: for each year 2020 to 2026, train only on weeks that ended at least 5 weeks before 1 January of that year (the 4-week outcome window cannot reach into the test year), and test on that year. Test books are also held out of training (5 book folds inside each year). Test weeks: 186,650 (4,393 hot).

## Results: AUC for "next 4 weeks reach 1.5x normal"

| Model | A book split, all weeks | A, hot weeks | B walk-forward, all weeks | B, hot weeks |
|---|---|---|---|---|
| Attention only (old model) | 0.618 | 0.712 | 0.587 | 0.627 |
| Own listening only | 0.818 | 0.824 | 0.766 | 0.802 |
| Both | 0.820 | 0.832 | 0.769 | 0.803 |
| Rule: own 4-week ratio, no fitting | 0.727 | 0.775 | 0.711 | 0.770 |

## What attention adds over own listening (AUC of both minus own listening only, 95% interval from resampling books, 200 draws)

| Split | All weeks | Hot weeks |
|---|---|---|
| A book split | +0.002 [+0.001, +0.004] | +0.008 [-0.002, +0.018] |
| B walk-forward | +0.003 [+0.001, +0.005] | +0.000 [-0.009, +0.009] |

Own listening adds a lot to attention: +0.20 (A) and +0.18 (B) AUC over attention alone.

## Reading
1. The old result, AUC 0.62 overall and 0.71 in hot weeks, holds only against a weak comparison. A model that just knows the book's own recent listening reaches 0.82, and a one-line rule with no fitting reaches 0.73 overall and 0.78 in hot weeks, both better than the attention model.
2. Adding attention to own listening gives almost nothing: +0.002 to +0.003 AUC overall (statistically above zero because the sample is large, practically tiny), and no detectable gain in hot weeks (interval includes zero; point estimates +0.008 and +0.000).
3. The time-blocked split lowers every model. Attention only drops from 0.62 to 0.59 overall and from 0.71 to 0.63 in hot weeks, so the old hot-week figure was partly helped by mixing years. By year, attention-only AUC in hot weeks ranges from 0.47 (2026) to 0.70 (2024), and in all weeks it is 0.49 to 0.61. Own listening holds up (0.72 to 0.80 by year).
4. Statement the data support: attention carries a weak signal about a book's next month that is almost entirely already contained in the book's own recent listening. It is useful only for a book with no listening record, which is the real use of a hidden-book model.

## Cautions
- The outcome is measured against the same 26-week median that the own-listening inputs use, so own listening has a built-in advantage (a book that is already above its median tends to stay above it). This makes the own-listening baseline strong by construction, and it is the fair persistence benchmark, but the gap to attention should not be read as attention being useless for books without history.
- Only the weekly model was redone. The monthly model (level AUC 0.71, within-book Spearman 0.05) was not rerun here.
- One model setting (no tuning) and one random fold assignment; the bootstrap resamples books but not fold assignment.
- Walk-forward 2026 covers weeks only up to the data end (August 2026).
