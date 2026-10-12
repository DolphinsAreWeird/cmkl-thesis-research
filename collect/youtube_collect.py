"""Collect public YouTube data about books, published before each audiobook's release.

Usage:
    export YOUTUBE_API_KEY=...
    python youtube_collect.py books.csv youtube_data.json

books.csv columns: identifier, title, author, release_date (YYYY-MM-DD)

Commenter names and channel identities are never stored.
"""
import json
import os
import re
import sys
import time
import unicodedata

import pandas as pd
import requests

API = "https://www.googleapis.com/youtube/v3"
STOP = {"the", "a", "an", "of", "and", "in", "to", "version", "vol", "volume", "book"}
KEY = os.environ.get("YOUTUBE_API_KEY")


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def title_words(title):
    title = re.sub(r"\(.*?\)", "", title)
    return [w for w in norm(title).split() if w not in STOP]


def call(endpoint, params):
    params = dict(params, key=KEY)
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    if r.status_code == 403 and "quota" in r.text.lower():
        raise RuntimeError("Daily quota reached. Run again after the quota resets.")
    r.raise_for_status()
    return r.json()


def collect_book(title, author, release_date, top_n_comments=3):
    before = f"{release_date}T00:00:00Z"
    words = title_words(title)
    query = f'"{title}" {author.split()[-1]}'

    # 1. Videos published before release (100 quota units)
    search = call("search", {"part": "snippet", "q": query, "type": "video",
                             "maxResults": 50, "publishedBefore": before})
    ids = [item["id"]["videoId"] for item in search.get("items", [])]

    # 2. Public statistics (1 unit), keeping only videos whose title contains the book title
    videos = []
    if ids:
        stats = call("videos", {"part": "statistics,snippet", "id": ",".join(ids)})
        for item in stats.get("items", []):
            if not words or not all(w in norm(item["snippet"]["title"]).split() for w in words):
                continue
            s = item.get("statistics", {})
            videos.append({
                "id": item["id"],
                "published": item["snippet"]["publishedAt"],
                "title": item["snippet"]["title"],
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
            })

    # 3. Comments posted before release on the most-viewed kept videos (1 unit each)
    comments = []
    for v in sorted(videos, key=lambda x: -x["views"])[:top_n_comments]:
        try:
            threads = call("commentThreads", {"part": "snippet", "videoId": v["id"],
                                              "maxResults": 100, "order": "time",
                                              "textFormat": "plainText"})
        except requests.HTTPError:
            continue  # comments disabled
        for item in threads.get("items", []):
            c = item["snippet"]["topLevelComment"]["snippet"]
            if c["publishedAt"] < before:
                # author name and channel ID are deliberately not stored
                comments.append({"video": v["id"], "published": c["publishedAt"],
                                 "likes": c.get("likeCount", 0), "text": c["textDisplay"][:500]})

    return {"query": query, "before": before, "videos_raw": len(ids),
            "videos": videos, "pre_release_comments": comments}


def main(books_csv, out_json):
    if not KEY:
        sys.exit("Set the YOUTUBE_API_KEY environment variable first.")
    books = pd.read_csv(books_csv)
    data = json.load(open(out_json)) if os.path.exists(out_json) else {}
    for _, b in books.iterrows():
        if b.identifier in data:
            continue
        try:
            data[b.identifier] = collect_book(b.title, b.author, b.release_date)
        except RuntimeError as e:
            print(e)
            break
        json.dump(data, open(out_json, "w"))
        time.sleep(0.3)
    print(f"Saved {len(data)} books to {out_json}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
