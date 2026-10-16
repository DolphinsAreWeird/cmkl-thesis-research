"""Build themes.csv for the YouTube theme collector from taxonomy version 3.

One row per middle-level theme (86 of them): theme_id, label, search_terms.
Search terms are the node's anchor term plus the most frequent subject-heading
terms of the books placed under that theme. Plain English, 2 to 4 terms.
Also writes a short review sheet (themes_review.md) for Khant to check by eye.

Run from inside code/:  ../.venv/bin/python youtube_themes/make_themes_csv.py
Only reads local files. No network.
"""
import pathlib
import re
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import config  # noqa: E402  (shared data folder)

TAX = pathlib.Path(config.D) / "db" / "taxonomy_v3"
# Terms that are too broad to search on their own
TOO_BROAD = {
    "history", "society", "family", "business", "science", "life", "fiction", "general",
    "social aspects", "psychology", "sociology", "people", "world", "human", "men", "culture",
    "nonfiction", "interpersonal relations", "social life and customs", "biography",
}
# Heading fragments that are cataloguing leftovers or mean something else on YouTube
BAD_TERMS = {
    "romans", "romanies", "mythological", "french language", "russian language", "lego toys",
    "palestinian arabs", "treasure troves", "forgotten realms imaginary place", "future the",
    "social problem", "germans", "russians", "sleepovers", "night", "play", "choice", "goal",
    "selling", "contests", "popularity", "secrets", "secrecy", "sex", "men", "young men",
    "lesbian", "trivia and", "wit and", "chaotic behavior in systems",
}
FUNCTION_WORDS = {"the", "and", "in", "of", "a", "an", "into", "to", "for", "on", "with"}
MAX_TERMS, MIN_TERMS, POOL = 4, 2, 25


def words(term):
    return set(re.findall(r"[a-z]+", term.lower()))


def acceptable(term):
    if not re.fullmatch(r"[a-z][a-z' \-]{2,38}", term):
        return False
    if len(term.split()) > 4 or term in TOO_BROAD or term in BAD_TERMS:
        return False
    if term.split()[-1] in FUNCTION_WORDS:
        return False
    return True


def pick_terms(anchor, ranked, label):
    chosen = []
    candidates = ([anchor] if isinstance(anchor, str) else []) + list(ranked)
    for t in candidates:
        t = t.strip().lower()
        if not acceptable(t) or t in chosen:
            continue
        w = words(t)
        # skip a term whose words are already covered by (or cover) a chosen term
        if any(w <= words(c) or words(c) <= w for c in chosen):
            continue
        chosen.append(t)
        if len(chosen) == MAX_TERMS:
            break
    return chosen


def main():
    nodes = pd.read_parquet(TAX / "theme_nodes.parquet")
    mid = nodes[nodes.level == 2].sort_values("node_id")
    wtv = pd.read_parquet(TAX / "work_theme_value.parquet", columns=["work_id", "theme", "node_id"])
    wtv = wtv[wtv.node_id.str.count(r"\.") == 2].copy()  # works placed on a level-3 node
    wtv["mid"] = wtv.node_id.str.rsplit(".", n=1).str[0]
    freq = wtv.groupby(["mid", "theme"]).work_id.nunique().reset_index(name="n")
    rows, review = [], []
    for _, r in mid.iterrows():
        f = freq[freq.mid == r.node_id].sort_values("n", ascending=False).head(POOL)
        terms = pick_terms(r.anchor, f.theme.tolist(), r.label)
        rows.append({"theme_id": r.node_id, "label": r.label, "search_terms": "; ".join(terms)})
        review.append((r.node_id, r.label, terms, f.head(8).theme.tolist()))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "themes.csv", index=False)
    short = out[out.search_terms.str.count(";") + 1 < MIN_TERMS]
    lines = [
        "# Search terms review sheet (86 themes)", "",
        "For Khant. Each theme has 2 to 4 search terms taken from the books' subject headings. "
        "The collector searches YouTube for any of the terms (OR), so each term should find videos "
        "about the theme on its own. Please check for terms that are too broad, too narrow or "
        "mean something else on YouTube. Edit `themes.csv` directly (separate terms with `; `).", "",
        "| Theme | Label | Search terms | Next most frequent headings (not used) |", "|---|---|---|---|",
    ]
    for tid, label, terms, top in review:
        rest = [t for t in top if t not in terms][:4]
        lines.append(f"| {tid} | {label} | {'; '.join(terms)} | {'; '.join(rest)} |")
    if len(short):
        lines += ["", f"Themes with fewer than {MIN_TERMS} terms (need a hand-added term): "
                  + ", ".join(short.theme_id)]
    (HERE / "themes_review.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {len(out)} themes; {len(short)} with fewer than {MIN_TERMS} terms")


if __name__ == "__main__":
    main()
