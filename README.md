# CMKL Thesis Research

**[Privacy Policy](PRIVACY.md)** · **[Terms of Service](TERMS.md)** · Uses YouTube API Services under the [YouTube Terms of Service](https://www.youtube.com/t/terms)

Code, fixed analysis settings and result reports for an undergraduate honors thesis at CMKL University (Bangkok, Thailand), supervised by Dr. Fawad Asadi.

## What the thesis asks

When public interest in a topic rises, do more people read and listen to books on that topic? When does the rise carry over, and when does it fade without effect? And can public interest help forecast next month's demand for whole categories of books?

Interest comes from public, historical sources: Wikipedia page views (since 2015) and GDELT news themes and tone (since 2017). Demand comes from Seattle Public Library checkouts by format (audiobook, ebook, print) and from LibriVox listening for public-domain audiobooks. Book categories are built from the books' own subject headings and descriptions, not from the news.

## The studies

| Study | Question | Status |
| --- | --- | --- |
| 1 | Can information available before release predict which LibriVox recordings are listened to most? | Done |
| 2 | Does attention to a single book or its adaptation move its listening? | Done |
| 3 | When does a rise in interest in a theme carry over into borrowing of books on that theme? | First results in `results/reports/study3_*` |
| 4 | Do public-interest signals improve one-month-ahead forecasts of category demand? | Running |

## Fixed settings (pre-registration)

The thresholds, windows, controls, models and metrics for Studies 3 and 4 were fixed and dated on 13 October 2026, before any category's demand was compared with its interest and before any forecast was scored. They are in [`prereg/`](prereg/):

- `study3_settings_2026-10-13.json` and `forecast_settings_2026-10-13.json` are the records. Their SHA-256 fingerprints are in `prereg/README.md`, and the analysis code refuses to run if a record changes.
- `DEVIATIONS.md` lists every later clarification or change, with its date, its reason and whether any outcome data had been seen. The machine-readable versions are in `prereg/addenda/` and `prereg/addenda_forecast/`.

## Method benchmark and final test (15 to 17 October 2026)

The thesis compares 52 forecasting pipelines for monthly demand by book category (Seattle Public Library borrowing) and asks which ways of organizing online behavior into categories built from books, and which models, predict demand best, how accurately, and when. The settings were fixed before any score: `prereg/benchmark_settings_2026-10-15.json` and the addenda in `prereg/addenda_benchmark/`, with their fingerprints in `prereg/README.md`. The code is in `code/main_study/benchmark/` (its README lists the scripts) and the result reports are `results/reports/benchmark_*.md`.

A final test uses library months released after the settings were fixed. The forecasts of seven pipelines, of the simple forecast that repeats last month and of one reference pipeline, for September to November 2026, made from data to August 2026, are in `prereg/final_test/` with their SHA-256 in `prereg/README.md`. The commit time of the merge that added them is the date of their publication, before the library had released those months. `prereg/addenda_benchmark/2026-10-17_c_final_test_forecasts.json` fixes what was forecast and how, and `2026-10-17_d_final_test_scoring.json` fixes how the new months are built and scored, the metrics and the timing, before any of those months is downloaded. They are scored once, not before 5 December 2026; the scoring code refuses to run earlier.

## Repository layout

| Folder | Contents |
| --- | --- |
| `code/` | Collection and analysis scripts. `code/main_study/` holds the category build, the interest timelines, Study 3 (`study3/`) and Study 4 (`study4/`), each with its own README and simulation tests |
| `collectors/` | Scheduled collectors: New York Times best-seller lists, a daily Bluesky sample (post time, language and text only; account identifiers, handles, links and mentions are removed on arrival, and the text is never published), and weekly GDELT updates |
| `jobs/` | Helpers that run long jobs in the background and the macOS launchd schedules |
| `prereg/` | Fixed settings, the final-test forecasts (made before their months were released) and the deviations log |
| `results/reports/` | Markdown and CSV reports written by the analysis code |
| `collect/` | The YouTube collector described below |

## Data

Raw data is not included. Some sources do not allow redistribution, some text comes from people, and the files are large (about 16 GB). Every source is public and the scripts download it again:

| Source | Access |
| --- | --- |
| Seattle Public Library checkouts | data.seattle.gov (Socrata API) |
| Wikipedia page views | Wikimedia REST API and pageview dumps |
| GDELT Global Knowledge Graph | Google BigQuery |
| LibriVox and Internet Archive views | Their public APIs |
| Goodreads and Amazon reviews | UCSD research datasets (counts only are kept) |
| New York Times best-seller lists | NYT Books API |

No usernames, account IDs, handles or other personal identifiers are stored.

## Reproducing

Python 3.12. Install the pinned versions with `pip install -r requirements.lock` (or `requirements.txt` for the latest). Keys go in a local `.env` file (see `collectors/.env.example`) and are never committed. Each folder's README gives the run order.

## How the YouTube collection works

For each book, `collect/youtube_collect.py`:

1. Searches for videos about the book that were published **before** the audiobook's release date (`publishedBefore`), so nothing after release is used.
2. Keeps a video only if its title contains the book's title. Raw search results are mostly unrelated, so this step removes noise.
3. Reads public statistics for the kept videos (views, likes, comments).
4. Reads public comments on the most-viewed kept videos and keeps only those posted before the release date.
5. Stores comment text, dates and like counts. Commenter names and channel identities are never stored.

These records are turned into aggregate measures (for example, how many videos and comments existed, and whether activity was rising) and compared with listening figures in statistical models.

```
pip install -r requirements.txt
export YOUTUBE_API_KEY=your_key_here
python collect/youtube_collect.py books.csv youtube_data.json
```

`books.csv` needs the columns `identifier`, `title`, `author`, `release_date` (YYYY-MM-DD). The API key is read from an environment variable and is never stored in this repository.

## Data and use

This is non-commercial academic research. The project only reads public data, has no users, does not display YouTube content and does not redistribute data. See `PRIVACY.md`.

Contact: kwai@cmkl.ac.th
