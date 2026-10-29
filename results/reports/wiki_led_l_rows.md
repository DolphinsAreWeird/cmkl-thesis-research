# Addendum l, step 2: rows of the frame "books chosen in time"

Made by `code/main_study/wiki_led/l_books_in_time/l03_rows.py` on 2026-10-30 02:58 (local time, UTC+06:30). Data only: counts, no model and no relation between a feature and an outcome.

- Works: 43,298 (Test D's 25% sample without the placeholder works); works with at least one row: 43,298.
- Rows: 1,793,653; backtest origins 2016-03 to 2026-07: 1,773,531, of which scored (origins from 2019-01): 1,258,807; origin 2026-08 (frozen forecasts only): 20,122. By format: {'print': 795398, 'ebook': 580360, 'audiobook': 417895}.
- Scored rows with a book-article feature: 265,942 of 1,258,807 (21.1%); with an author-article feature: 775,542 of 1,258,807 (61.6%); with either: 782,860 of 1,258,807 (62.2%).
- Rows at origin 2026-08 with either: 12,290 of 20,122 (61.1%).
- Check: on origins to 2026-07 the rows and the values of L_t, L_next, M6, h_lt, h_lt1, h_m6, h_m12, h_lyago, h_age, D, Sg, Y, loans12 equal Test D's stored rows for these works (rows only here 0, only in Test D 0, largest difference 0.0).
- Run time 6 s.
