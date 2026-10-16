"""Theme-level YouTube collector (YouTube Data API v3, public data, API key only).

For each theme and calendar month it finds videos published in that month, checks they
are about the theme, and reads comments on the 10 most-viewed ones. One JSON record per
theme and month goes to <out>/records/. See the design document (14 October 2026).

Usage:
    export YOUTUBE_API_KEY=...            # the key is read only from this variable
    python youtube_themes.py themes.csv 2016-01 2026-09 out/             # collect (resumes)
    python youtube_themes.py themes.csv 2016-01 2026-09 out/ --dry-run   # plan, no API calls
    python youtube_themes.py themes.csv 2016-01 2026-09 out/ --refresh   # 30 days later
    python youtube_themes.py themes.csv 2016-01 2026-09 out/ --purge     # weekly, deletes old raw

themes.csv columns: theme_id, label, search_terms (terms separated by ';').

Privacy: only video IDs, dates, counts and the first 500 characters of comment text are
kept. Author names, channel IDs, profile images and user IDs are never written.
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import sys
import time

API = "https://www.googleapis.com/youtube/v3"
UNITS = {"search": 100, "videos": 1, "commentThreads": 1, "comments": 1}
TOP_VIDEOS, MAX_PAGES, MIN_INTERVAL = 10, 5, 0.5  # at most 2 calls per second
REFRESH_AFTER_DAYS, PURGE_AFTER_DAYS = 30, 90
DEFAULT_DAILY_UNITS = 100000
STOP = {"the", "a", "an", "of", "and", "in", "to", "for", "on", "with", "or", "is", "are",
        "how", "what", "why", "from", "about", "this", "that", "your", "you", "our", "their"}


class QuotaExceeded(Exception):
    """The daily quota is used up (or our own daily budget is)."""


class CommentsUnavailable(Exception):
    """Comments are turned off for this video (or the video is gone)."""


# ---------------------------------------------------------------- API client

class Client:
    """Thin API wrapper: key from the environment, at most 2 calls a second, unit counting."""

    def __init__(self, key=None, sleep=time.sleep, clock=time.monotonic, budget=None):
        self.key = key if key is not None else os.environ.get("YOUTUBE_API_KEY")
        if not self.key:
            sys.exit("Set the YOUTUBE_API_KEY environment variable first.")
        self.sleep, self.clock, self.budget = sleep, clock, budget
        self.last = None
        self.units = 0

    def get(self, endpoint, params):
        import requests  # imported here so tests and dry runs need no network library
        cost = UNITS[endpoint]
        if self.budget is not None and self.units + cost > self.budget:
            raise QuotaExceeded("daily unit budget for this run reached")
        for attempt in range(4):
            if self.last is not None:
                wait = MIN_INTERVAL - (self.clock() - self.last)
                if wait > 0:
                    self.sleep(wait)
            self.last = self.clock()
            try:
                # key goes in a header, so it can never appear in a URL or an error message
                r = requests.get(f"{API}/{endpoint}", params=params, timeout=30,
                                 headers={"x-goog-api-key": self.key})
            except requests.RequestException as e:
                if attempt == 3:
                    raise RuntimeError(f"network error on {endpoint}: {type(e).__name__}")
                self.sleep(5 * (attempt + 1))
                continue
            self.units += cost
            if r.status_code == 200:
                return r.json()
            reason = error_reason(r)
            if reason in ("quotaExceeded", "dailyLimitExceeded"):
                raise QuotaExceeded(reason)
            if reason in ("commentsDisabled", "videoNotFound", "forbidden") and endpoint == "commentThreads":
                raise CommentsUnavailable(reason)
            if reason == "rateLimitExceeded" or r.status_code >= 500:
                self.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"{endpoint} failed: HTTP {r.status_code} {reason}")
        raise RuntimeError(f"{endpoint} failed after retries")


def error_reason(r):
    try:
        return r.json()["error"]["errors"][0]["reason"]
    except Exception:
        return "unknown"


# ---------------------------------------------------------------- helpers

def months(start, end):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def month_bounds(month):
    y, m = map(int, month.split("-"))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-01T00:00:00Z", f"{ny:04d}-{nm:02d}-01T00:00:00Z"


def read_themes(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["terms"] = [t.strip() for t in r["search_terms"].split(";") if t.strip()]
    return rows


def search_query(terms):
    """Any of the terms (YouTube treats | as OR); multi-word terms are quoted."""
    return " | ".join(f'"{t}"' if " " in t else t for t in terms)


def stem(w):
    return w[:-1] if len(w) > 4 and w.endswith("s") else w


def content_words(text):
    return {stem(w) for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3 and w not in STOP}


def is_relevant(title, description, terms):
    """Title or description shares at least one content word with the theme terms."""
    theme_words = content_words(" ".join(terms))
    return bool(theme_words & content_words(f"{title} {description}"))


MENTION = re.compile(r"@[\w.\-]+")


def clean_text(text):
    """First 500 characters, with @mentions of other people replaced."""
    return MENTION.sub("@user", text or "")[:500]


def keep_video(item):
    s = item.get("statistics", {})
    return {"id": item["id"], "published": item["snippet"]["publishedAt"],
            "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0))}


def keep_comment(video_id, thread):
    """Whitelist of fields. The author name, channel ID and profile image are never read."""
    c = thread["snippet"]["topLevelComment"]
    sn = c["snippet"]
    return {"id": c["id"], "video": video_id, "published": sn["publishedAt"],
            "likes": int(sn.get("likeCount", 0)), "text": clean_text(sn.get("textDisplay"))}


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def read_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def rec_path(out, theme, month):
    return os.path.join(out, "records", f"{theme}_{month}.json")


def ledger_path(out):
    return os.path.join(out, "progress.json")


# ---------------------------------------------------------------- collection

def fetch_comments(client, video_id, max_pages=MAX_PAGES):
    comments, token = [], None
    for _ in range(max_pages):
        params = {"part": "snippet", "videoId": video_id, "maxResults": 100,
                  "order": "time", "textFormat": "plainText"}
        if token:
            params["pageToken"] = token
        try:
            page = client.get("commentThreads", params)
        except CommentsUnavailable:
            break
        comments += [keep_comment(video_id, t) for t in page.get("items", [])]
        token = page.get("nextPageToken")
        if not token:
            break
    return comments


def collect_one(client, theme, month):
    after, before = month_bounds(month)
    search = client.get("search", {
        "part": "snippet", "type": "video", "q": search_query(theme["terms"]),
        "publishedAfter": after, "publishedBefore": before, "relevanceLanguage": "en",
        "order": "relevance", "maxResults": 50})
    ids = [i["id"]["videoId"] for i in search.get("items", []) if i.get("id", {}).get("videoId")]
    videos = []
    if ids:
        stats = client.get("videos", {"part": "statistics,snippet", "id": ",".join(ids)})
        for item in stats.get("items", []):
            sn = item["snippet"]
            if is_relevant(sn.get("title", ""), sn.get("description", ""), theme["terms"]):
                videos.append(keep_video(item))  # title and description are not stored
    videos.sort(key=lambda v: -v["views"])
    comments = []
    for v in videos[:TOP_VIDEOS]:
        comments += fetch_comments(client, v["id"])
    return {"theme": theme["theme_id"], "month": month, "collected_at": now_iso(),
            "refreshed_at": None, "videos_found": len(ids), "videos": videos,
            "comments": comments}


def run_collect(client, themes, start, end, out):
    ledger = read_json(ledger_path(out), {})
    done = 0
    try:
        for theme in themes:
            for month in months(start, end):
                key = f"{theme['theme_id']}_{month}"
                if key in ledger:
                    continue
                record = collect_one(client, theme, month)
                write_json(rec_path(out, theme["theme_id"], month), record)
                ledger[key] = {"collected_at": record["collected_at"], "refreshed_at": None, "purged": False}
                write_json(ledger_path(out), ledger)  # saved after every theme-month
                done += 1
    except QuotaExceeded as e:
        print(f"Stopped: quota reached ({e}). Run again later to continue.")
        return done, True
    print(f"Collected {done} theme-months, {client.units} units used.")
    return done, False


# ---------------------------------------------------------------- refresh

def refresh_record(client, record):
    """Re-request stored videos and comments; delete items no longer available."""
    ids = [v["id"] for v in record["videos"]]
    alive = {}
    for i in range(0, len(ids), 50):
        got = client.get("videos", {"part": "statistics,snippet", "id": ",".join(ids[i:i + 50])})
        for item in got.get("items", []):
            alive[item["id"]] = keep_video(item)
    record["videos"] = [alive[v["id"]] for v in record["videos"] if v["id"] in alive]
    kept_comments = []
    for vid in {c["video"] for c in record["comments"]}:
        if vid not in alive:
            continue  # video gone: its comments go too
        stored = [c for c in record["comments"] if c["video"] == vid]
        oldest = min(c["published"] for c in stored)
        seen, token, covered = {}, None, False
        for _ in range(MAX_PAGES + 5):
            params = {"part": "snippet", "videoId": vid, "maxResults": 100,
                      "order": "time", "textFormat": "plainText"}
            if token:
                params["pageToken"] = token
            try:
                page = client.get("commentThreads", params)
            except CommentsUnavailable:
                seen, covered = {}, True  # comments now off: all stored ones are removed
                break
            for t in page.get("items", []):
                c = keep_comment(vid, t)
                seen[c["id"]] = c
            token = page.get("nextPageToken")
            last = min((c["published"] for c in seen.values()), default=None)
            if not token or (last is not None and last <= oldest):
                covered = True
                break
        for c in stored:
            if c["id"] in seen:
                kept_comments.append(seen[c["id"]])
            elif not covered:
                kept_comments.append(c)  # page walk did not reach it: keep, cannot tell
    record["comments"] = kept_comments
    record["refreshed_at"] = now_iso()
    return record


def run_refresh(client, out, now=None):
    ledger = read_json(ledger_path(out), {})
    now = now or dt.datetime.now(dt.timezone.utc)
    done = 0
    try:
        for key, info in sorted(ledger.items()):
            if info.get("refreshed_at") or info.get("purged"):
                continue
            if now - parse_iso(info["collected_at"]) < dt.timedelta(days=REFRESH_AFTER_DAYS):
                continue
            path = os.path.join(out, "records", f"{key}.json")
            record = read_json(path)
            if record is None:
                continue
            record = refresh_record(client, record)
            write_json(path, record)
            info["refreshed_at"] = record["refreshed_at"]
            write_json(ledger_path(out), ledger)
            done += 1
    except QuotaExceeded as e:
        print(f"Stopped: quota reached ({e}). Run --refresh again later to continue.")
        return done, True
    print(f"Refreshed {done} theme-months, {client.units} units used.")
    return done, False


# ---------------------------------------------------------------- purge

def run_purge(out, now=None):
    """Delete raw records older than 90 days, but only once weekly measures for them exist."""
    ledger = read_json(ledger_path(out), {})
    now = now or dt.datetime.now(dt.timezone.utc)
    removed = skipped = 0
    for key, info in ledger.items():
        path = os.path.join(out, "records", f"{key}.json")
        if info.get("purged") or not os.path.exists(path):
            continue
        if now - parse_iso(info["collected_at"]) < dt.timedelta(days=PURGE_AFTER_DAYS):
            continue
        measure = os.path.join(out, "measures", f"{key}.csv")
        # measures must exist and be newer than the raw record (so they include any refresh)
        if not os.path.exists(measure) or os.path.getmtime(measure) < os.path.getmtime(path):
            skipped += 1
            continue
        os.remove(path)
        info["purged"] = True
        removed += 1
    write_json(ledger_path(out), ledger)
    print(f"Purged {removed} raw records; {skipped} kept because weekly measures are not ready.")
    return removed, skipped


# ---------------------------------------------------------------- dry run

def plan(themes, start, end, out):
    """Planned calls and worst-case quota units for collection (resume-aware)."""
    ledger = read_json(ledger_path(out), {}) if out else {}
    todo = sum(1 for t in themes for m in months(start, end) if f"{t['theme_id']}_{m}" not in ledger)
    pages = TOP_VIDEOS * MAX_PAGES
    calls = {"search": todo, "videos": todo, "commentThreads (at most)": todo * pages}
    units = {"search": todo * UNITS["search"], "videos": todo, "commentThreads (at most)": todo * pages}
    total = sum(units.values())
    # Refresh: statistics again plus comment pages again (same size as collection, per design)
    refresh_units = todo + todo * pages
    return {"theme_months": todo, "calls": calls, "units": units, "total_units": total,
            "refresh_units_at_most": refresh_units,
            "days_at_daily_budget": math.ceil(total / DEFAULT_DAILY_UNITS)}


def print_plan(p):
    print(f"Theme-months still to collect: {p['theme_months']:,}")
    for k in p["calls"]:
        print(f"  {k:26s} {p['calls'][k]:>10,} calls  {p['units'][k]:>10,} units")
    print(f"Total collection units (worst case): {p['total_units']:,}")
    print(f"Refresh 30 days later, at most:      {p['refresh_units_at_most']:,} units")
    print(f"Days at {DEFAULT_DAILY_UNITS:,} units a day:       about {p['days_at_daily_budget']}")
    print("No API calls were made.")


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("themes_csv")
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("out")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print planned calls and units, call nothing")
    mode.add_argument("--refresh", action="store_true", help="re-request stored items 30 days after collection")
    mode.add_argument("--purge", action="store_true", help="delete raw records older than 90 days once weekly measures exist")
    ap.add_argument("--max-units", type=int, default=DEFAULT_DAILY_UNITS, help="stop after this many units in one run")
    a = ap.parse_args(argv)
    themes = read_themes(a.themes_csv)
    if a.dry_run:
        print_plan(plan(themes, a.start, a.end, a.out))
    elif a.purge:
        run_purge(a.out)
    else:
        client = Client(budget=a.max_units)
        if a.refresh:
            run_refresh(client, a.out)
        else:
            run_collect(client, themes, a.start, a.end, a.out)


if __name__ == "__main__":
    main()
