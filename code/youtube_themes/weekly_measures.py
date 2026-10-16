"""Weekly YouTube measures per theme, from the raw theme-month JSON records.

Usage (from inside code/):
    ../.venv/bin/python youtube_themes/weekly_measures.py <out_dir> [themes.csv]

<out_dir> is the folder the collector writes to (records/, progress.json). For each raw record
this writes a small table <out_dir>/measures/<theme>_<month>.csv (weeks only, no text), then
joins all of them into <out_dir>/weekly_measures.csv. Once a record has its table, the raw
record can be purged by the collector (--purge).

Per theme and week (weeks start on Monday):
  videos          videos published that week (kept after the relevance check)
  views           views of those videos at collection (or refresh) time
  comments        comments posted that week, among the collected ones
  matched         comments whose text is close in meaning to the theme
  match_share     matched / comments
  mean_tone       average tone of all comments, from -1 (negative) to +1 (positive)
  mean_tone_matched  the same for matched comments only

Everything runs on this computer. Comment text is never sent anywhere.
Matching: the same local sentence-embedding model used elsewhere in the project (fastembed,
paraphrase-multilingual-MiniLM-L12-v2); cosine similarity to the theme text >= MATCH_THRESHOLD.
Tone: VADER if installed, otherwise the same embedding model scored against positive and
negative anchor sentences (a rough fallback; say so in the methods if it is used).
"""
import csv
import datetime as dt
import json
import os
import sys

import numpy as np

MATCH_THRESHOLD = 0.35  # cosine similarity; fix and date it before the real run (see DEVIATIONS.md rules)
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
POS = ["I love this, it is wonderful and inspiring.", "Great, thank you, this made me happy."]
NEG = ["I hate this, it is terrible and upsetting.", "This is awful, it made me angry and sad."]
COLS = ["week", "videos", "views", "comments", "matched", "tone_sum", "tone_matched_sum"]


class LocalModels:
    """Embedding and tone, both local. Loaded only when first needed."""

    def __init__(self):
        self._emb = None
        self._vader = None
        self._vader_tried = False
        self._anchors = None

    def embed(self, texts):
        if self._emb is None:
            from fastembed import TextEmbedding
            self._emb = TextEmbedding(MODEL)
        v = np.array(list(self._emb.embed(list(texts), batch_size=64)), dtype=float)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)

    def tone(self, texts):
        if not self._vader_tried:
            self._vader_tried = True
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self._vader = SentimentIntensityAnalyzer()
            except ImportError:
                self._vader = None
        if self._vader is not None:
            return np.array([self._vader.polarity_scores(t)["compound"] for t in texts])
        if self._anchors is None:
            self._anchors = (self.embed(POS).mean(0), self.embed(NEG).mean(0))
        e = self.embed(texts)
        return np.clip((e @ self._anchors[0] - e @ self._anchors[1]) * 4, -1, 1)


def week_start(iso):
    d = dt.datetime.strptime(iso[:10], "%Y-%m-%d").date()
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def measures_for_record(record, theme_text, models, threshold=MATCH_THRESHOLD):
    """Return {week: row} for one theme-month record."""
    weeks = {}

    def row(w):
        return weeks.setdefault(w, {"week": w, "videos": 0, "views": 0, "comments": 0,
                                    "matched": 0, "tone_sum": 0.0, "tone_matched_sum": 0.0})
    for v in record["videos"]:
        r = row(week_start(v["published"]))
        r["videos"] += 1
        r["views"] += v["views"]
    texts = [c["text"] for c in record["comments"] if c.get("text")]
    comments = [c for c in record["comments"] if c.get("text")]
    if texts:
        sims = models.embed(texts) @ models.embed([theme_text])[0]
        tone = models.tone(texts)
        for c, s, t in zip(comments, sims, tone):
            r = row(week_start(c["published"]))
            r["comments"] += 1
            r["tone_sum"] += float(t)
            if s >= threshold:
                r["matched"] += 1
                r["tone_matched_sum"] += float(t)
    return weeks


def write_measure(path, weeks):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for k in sorted(weeks):
            w.writerow(weeks[k])


def theme_text(theme):
    return f"{theme['label']}. {theme['search_terms'].replace(';', ',')}"


def build(out, themes_csv, models=None):
    models = models or LocalModels()
    themes = {}
    with open(themes_csv, newline="", encoding="utf-8") as f:
        for t in csv.DictReader(f):
            themes[t["theme_id"]] = t
    rec_dir, mdir = os.path.join(out, "records"), os.path.join(out, "measures")
    for name in sorted(os.listdir(rec_dir)) if os.path.isdir(rec_dir) else []:
        if not name.endswith(".json"):
            continue
        rp, mp = os.path.join(rec_dir, name), os.path.join(mdir, name[:-5] + ".csv")
        if os.path.exists(mp) and os.path.getmtime(mp) >= os.path.getmtime(rp):
            continue  # already up to date
        rec = json.load(open(rp, encoding="utf-8"))
        if rec["theme"] not in themes:
            continue
        write_measure(mp, measures_for_record(rec, theme_text(themes[rec["theme"]]), models))
    return join(out)


def join(out):
    """Add up the per-record tables into one weekly table per theme."""
    mdir = os.path.join(out, "measures")
    agg = {}
    for name in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        theme = name.rsplit("_", 1)[0]
        with open(os.path.join(mdir, name), newline="") as f:
            for r in csv.DictReader(f):
                a = agg.setdefault((theme, r["week"]), dict.fromkeys(COLS[1:], 0.0))
                for k in COLS[1:]:
                    a[k] += float(r[k])
    path = os.path.join(out, "weekly_measures.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["theme_id", "week", "videos", "views", "comments", "matched",
                    "match_share", "mean_tone", "mean_tone_matched"])
        for (theme, week) in sorted(agg):
            a = agg[(theme, week)]
            n, m = a["comments"], a["matched"]
            w.writerow([theme, week, int(a["videos"]), int(a["views"]), int(n), int(m),
                        round(m / n, 4) if n else "", round(a["tone_sum"] / n, 4) if n else "",
                        round(a["tone_matched_sum"] / m, 4) if m else ""])
    return path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = sys.argv[1]
    print("wrote", build(out, sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "themes.csv")))
