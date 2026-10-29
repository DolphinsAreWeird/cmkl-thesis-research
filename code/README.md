# Code map

Run every script from inside `code/` with the project environment, for example `../.venv/bin/python main_study/benchmark/03_evaluate.py`. Paths and keys come from `config.py`, which almost every script imports; that is why the older scripts sit next to it in this folder and are not sorted into sub-folders. Long jobs are started with `../jobs/bg.sh NAME script.py args`.

The thesis code imports `config.py`, `features.py`, `seattle.py`, `positive_controls.py` and `gdelt_weekly.py` from this folder, so these five must stay where they are.

## The thesis (start here)

| Folder | Plain description | Thesis part |
| --- | --- | --- |
| `main_study/` (files `00` to `21`, `_common.py` and others) | Builds the book categories: Seattle Public Library borrowing by title, subject headings and Goodreads shelves, the three-level theme hierarchy, assignment of works to themes, quality checks; `21_v3_data_checks.py` (30 Oct 2026) checks the snapshot against the AIC-400 data wrangling checklist (placeholder records, key, ranges, duplicate lines; report `data/reports/seattle_data_checks.md`) | Data; categories |
| `main_study/interest/` | Builds the interest series: English Wikipedia page views routed to themes, GDELT news volume and tone, shift labels, quality flags | Data; routing |
| `main_study/benchmark/` | The method benchmark: 52 pipelines, scoring, the second-stage routings, Chronos-2, learned categories, figures and tables (scripts indexed in its README) | Pipelines; results |
| `main_study/study3/`, `main_study/study3b/` | Whether a rise in interest in a theme is followed by more borrowing: pooled tests, positive controls, power, duration, carry-over, small categories, sentiment direction | Lasting rises |
| `main_study/study4/`, `main_study/study4b/` | The first forecasting tests that led to the benchmark: next month's level, the change, and rare surges | Lasting rises (forecasts before the benchmark) |
| `main_study/wiki_led/` | Data for Test B (new books) of the Wikipedia-led tests fixed on 20 Oct 2026: population of new works, loans in the first six months, library-only features, first-author match to English Wikipedia and Wikidata, monthly author page views, one row per work, checks and a data report (`data/reports/wiki_led_test_b_data.md`). Data only, no model. `92_residuals_2019_2023.py` (30 Oct 2026): residuals of Test A's library-only model by calendar month, book age and Wikipedia rises, and correlations of the Wikipedia features, test years 2019 to 2023 only | Wikipedia-led tests |
| `main_study/wiki_led/testF/` | Data for Test F, AI matchmaking (addendum g, 21 Oct 2026): the pages of the daily top 500 on 2 days or more, their short description and first sentence from the Wikipedia Action API, the theme guide for the sorters, the 20,000 most-borrowed books with their text, chunk files for the AI sorters, the reliability and judge sets, and a data report (`data/reports/testF_data.md`). Scripts `01` to `06` run in order. Data only, nothing sorted | Wikipedia-led tests |
| `study2r/`, `study2r_fix/` | Single modern books: does a rise in attention to a book raise its own borrowing | Lasting rises (single books) |
| `conversation/` | Talk-page edits and the TweetsKB archive as conversation signals (tested, too thin) | Lasting rises |
| `brisbane/` | A replication check on Brisbane library data | Lasting rises |
| `parameter_audit/` | The register of every fixed setting and how it was calibrated | Appendix |
| `youtube_themes/` | Theme list and weekly measures for the planned YouTube comment study | Further work |

Each of `main_study/study3`, `study3b`, `study4`, `study4b`, `study2r`, `study1_label_check` and `study1_seattle` has its own `README.md` with ground rules and how to run it.

## Earlier work (September to 13 October 2026), kept because earlier reports came from it

These answered which new books will be read, the first question of the project. The settings of the later work are fixed in `../prereg/`.

| Files | What they do |
| --- | --- |
| `study1_label_check/`, `study1_rerun/`, `study1_seattle/` | Re-checks and reruns of the first question: label windows, Shapley feature groups, Seattle coverage |
| `features.py`, `gr_features.py`, `reports_data.py` | Label and feature tables for LibriVox recordings, including Wikipedia and Goodreads trend features computed only from months before release |
| `exp.py`, `exp_adj.py`, `exp_full.py`, `exp_full2.py`, `extra.py`, `shapley4.py`, `analyze.py`, `summarize.py`, `summarize2.py` | Model comparison on those tables (feature stages by models, grouped cross-validation) and its summaries |
| `walkforward.py`, `walkforward2.py`, `walkforward3.py`, `walkforward3_fix.py` | Time-ordered tests with a label window after release (each later file replaces the one before) |
| `study2.py`, `study2b.py`, `weekly_analysis.py`, `hidden_book_redo.py`, `librivox_bursts_redo_*.py` | Event studies of attention bursts, spillover and the hidden-book forecast on LibriVox listening |
| `adapt_*.py`, `adaptations.py`, `thai_calendar.py`, `case_fig.py` | Film and TV adaptations as attention events, a blind forecast, the Thai calendar, and the case figures |
| `pooled_print_ebook.py`, `category_test.py`, `subject_surges.py` | Pooled and theme-level tests of rises in interest |
| `taxonomy_v1.py`, `book_themes.py`, `theme_poc.py`, `theme_radar.py`, `event_themes*.py`, `build_db.py`, `eval_db.py`, `emb.py` | The first theme taxonomy, theme proofs of concept and the first theme database |
| `run_all.sh`, `run_rest.sh`, `run2.sh`, `run2b.sh`, `run_wf.sh`, `run_wf3.sh` | Chains that ran the scripts above in order (superseded by `../jobs/bg.sh`) |

## Data collection

| Files | Source |
| --- | --- |
| `seattle.py` | Seattle Public Library monthly checkouts by title (open data) |
| `wiki.py`, `wiki2.py`, `wiki_books.py`, `wiki_edits.py`, `pageviews.py`, `wikidata_match.py`, `link_titles.py`, `link_goodreads.py` | Wikipedia articles of books and authors through Wikidata, their page views and edits, and the links between recordings, articles and Goodreads |
| `top_articles.py`, `top_daily.py` | The most-viewed English Wikipedia pages by month and by day, 2016 to 2026 |
| `weekly_collect.py`, `ia_views.py` | Daily Wikipedia views and LibriVox listening (Internet Archive views) for books with their own article |
| `gdelt_weekly.py` | GDELT news themes and tone by week |
| `goodreads.py`, `modern_books.py`, `tumblr_weekly.py` | Goodreads Book Graph (streamed), modern books over time, Tumblr tag activity |
| `youtube_collect.py`, `youtube_sample.py`, `yt_comments.py`, `yt_trailers.py`, `yt_daily.sh` | YouTube data about books and adaptations (quota-limited, no author names stored) |
| `new_sources/` | Amazon reviews, Brisbane checkouts, Wikipedia clickstream, Open Library reading log |

The scheduled collectors (Bluesky, New York Times lists, GDELT updates) are in `../collectors/`.
