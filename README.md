# CMKL Thesis Research

Code for an undergraduate honors thesis at CMKL University (Bangkok, Thailand), supervised by Dr. Fawad Asadi.

## What the thesis asks

Can public attention to a book before its audiobook is released predict how much that audiobook is listened to? And do patterns found on English titles carry over to Thai titles?

Listening outcomes come from public figures for public-domain audiobooks on LibriVox. Attention comes from public sources: Wikipedia page views and edits, YouTube videos and comments, and (if access is granted) Reddit discussion and Google Trends.

## What this repository contains

| File | Purpose |
|---|---|
| `collect/youtube_collect.py` | Reads public YouTube data about each book, published before its audiobook's release |
| `PRIVACY.md` | How data is collected, stored and deleted |
| `requirements.txt` | Python packages needed |

## How the YouTube collection works

For each book, the script:

1. Searches for videos about the book that were published **before** the audiobook's release date (`publishedBefore`), so nothing after release is used.
2. Keeps a video only if its title contains the book's title. Raw search results are mostly unrelated, so this step removes noise.
3. Reads public statistics for the kept videos (views, likes, comments).
4. Reads public comments on the most-viewed kept videos and keeps only those posted before the release date.
5. Stores comment text, dates and like counts. Commenter names and channel identities are never stored.

These records are later turned into aggregate measures (for example, how many videos and comments existed, and whether activity was rising) and compared with listening figures in statistical models.

## Running it

```
pip install -r requirements.txt
export YOUTUBE_API_KEY=your_key_here
python collect/youtube_collect.py books.csv youtube_data.json
```

`books.csv` needs the columns `identifier`, `title`, `author`, `release_date` (YYYY-MM-DD). The API key is read from an environment variable and is never stored in this repository.

## Data and use

This is non-commercial academic research. The project only reads public data, has no users, does not display YouTube content and does not redistribute data. See `PRIVACY.md`.

Contact: kwai@cmkl.ac.th
