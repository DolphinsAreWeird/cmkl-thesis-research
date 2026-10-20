#!/usr/bin/env python3
"""73. Independent check of data/db/wiki_led/burst_features.parquet (data only).

Recomputes the features for random article-origin pairs from the daily files with plain pandas, written separately from 70_burst_features.py
(label-based slices on date indexes, Python loops, no shared helper), and compares them with the stored table.  The sample: 80 random books and
40 random authors at 8 random origins (always including 2026-08 and 2026-09), plus 60 pairs drawn from rows where top500 is above 0.  For top500 the
file wiki_top_daily.json is searched as text (title and day found by position), not decoded as JSON.
Writes data/db/wiki_led/burst_features_check.json.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/73_check_burst_features.py
"""
import re, json, bisect, hashlib, collections
import numpy as np, pandas as pd
from _common import D, OUT, log

S2R = D / 'db' / 'study2r'
EPS = 1e-12
LN15 = float(np.log(1.5))
DAYS = pd.date_range('2015-07-01', '2026-09-30', freq='D')
TOT = pd.read_parquet(D / 'db' / 'interest' / 'wiki' / 'total_daily.parquet').set_index('date').views.reindex(DAYS).astype(float)
fid = lambda t: hashlib.sha1(t.encode()).hexdigest()[:16]


def views(t):
    d = pd.read_parquet(S2R / 'pv_daily' / f'{fid(t)}.parquet', columns=['date', 'views'])
    return d.set_index('date').views.reindex(DAYS, fill_value=0).astype(float)


F = pd.read_parquet(OUT / 'burst_features.parquet').set_index(['kind', 'article', 'mi'])
W = pd.read_parquet(S2R / 'works.parquet')
RS = pd.read_parquet(S2R / 'redirect_screen.parquet')
RS = RS[RS['keep'] == True]          # noqa: E712
kept = RS.groupby('canonical').redirect.apply(list).to_dict()
b2a = W.dropna(subset=['author_article']).drop_duplicates('article').set_index('article').author_article.to_dict()
TA = pd.read_parquet(OUT / 'test_a_wiki_features.parquet', columns=['article', 'kind', 'mi', 'r4']).set_index(['kind', 'article', 'mi']).r4

# the top-500 file as text: positions of the day keys
txt = open(D / 'raw' / 'wiki_top_daily.json', encoding='ascii').read()
day_pos = [(m.start(), m.group(1)) for m in re.finditer(r'"(\d{8})": \[\[', txt)]
starts = [p for p, _ in day_pos]


def top_days(title):
    key = '["' + json.dumps(title.replace(' ', '_'))[1:-1] + '", '
    days = set()
    for m in re.finditer(re.escape(key), txt):
        days.add(day_pos[bisect.bisect_right(starts, m.start()) - 1][1])
    return {pd.Timestamp(d) for d in days}


listed = {pd.Timestamp(k) for _, k in day_pos}
rng = np.random.default_rng(7)
books = sorted(set(W.article))
authors = sorted(set(W.author_article.dropna()))
sb = [books[i] for i in rng.choice(len(books), 80, replace=False)]
sa = [authors[i] for i in rng.choice(len(authors), 40, replace=False)]
origins = rng.choice(np.arange(2016 * 12 + 2, 2026 * 12 + 9), 6, replace=False).tolist() + [2026 * 12 + 7, 2026 * 12 + 8]
pairs = [('book', a, o) for a in sb for o in origins] + [('author', a, o) for a in sa for o in origins]
hit = F.reset_index()
hit = hit[hit.top500 > 0]
for i in rng.choice(len(hit), 60, replace=False):
    r = hit.iloc[i]
    pairs.append((r.kind, r.article, int(r.mi)))
cache = {}


def series(kind, a):
    if (kind, a) not in cache:
        try:
            v = views(a)
            if kind == 'book':
                for r in kept.get(a, []):
                    v = v + views(r)
        except FileNotFoundError:
            v = None
        cache[(kind, a)] = v
    return cache[(kind, a)]


n_cmp = collections.Counter()
worst = collections.defaultdict(float)
mismatch = []
for kind, a, mi in pairs:
    v = series(kind, a)
    if v is None:
        continue
    y, m = divmod(mi, 12)
    e = pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)
    s = v / TOT
    vv, ss = v[:e], s[:e]
    last, lasts = vv.iloc[-28:], ss.iloc[-28:]
    nrm = ss.iloc[-210:-28].median()
    exp = {'hi28': int(((lasts + EPS) / (nrm + EPS) >= 1.5).sum()), 'nrm0': float(nrm == 0)}
    if last.sum() > 0:
        exp['pk28'] = last.max() / last.sum()
        pkd = last.index[np.where(last.values == last.max())[0].max()]
        exp['dpk'] = (e - pkd).days
        exp['pre7'] = np.log((ss[pkd - pd.Timedelta(days=7):pkd - pd.Timedelta(days=1)].mean() + EPS) / (nrm + EPS))
        if exp['dpk'] >= 2:
            exp['dec'] = np.log((ss[pkd + pd.Timedelta(days=1):pkd + pd.Timedelta(days=7)].mean() + EPS) / (ss[pkd] + EPS))
        exp['rec'] = np.log((lasts.max() + EPS) / (ss.iloc[:-28].max() + EPS))
    titles = [a] + (kept.get(a, []) if kind == 'book' else [])
    td = set().union(*[top_days(t) for t in titles])
    win = list(last.index)
    exp['top500'] = sum(d in td for d in win)
    exp['top500_lists'] = sum(d in listed for d in win)
    if kind == 'book':
        au = b2a.get(a)
        av = series('author', au) if (au is not None and au != a) else None
        if av is not None and last.nunique() > 1 and av[:e].iloc[-28:].nunique() > 1:
            exp['corr28'] = float(np.corrcoef(lasts.values, (av / TOT)[:e].iloc[-28:].values)[0, 1])
        br = TA.get(('book', a, mi), np.nan)
        ar = TA.get(('author', au, mi), np.nan) if au is not None else np.nan
        if mi <= 2026 * 12 + 6 and not (np.isnan(br) or np.isnan(ar)):
            exp['co'] = float(br >= LN15 and ar >= LN15)
    got = F.loc[(kind, a, mi)]
    for k in ['pk28', 'dpk', 'pre7', 'dec', 'rec', 'hi28', 'top500', 'top500_lists', 'nrm0'] + (['corr28', 'co'] if kind == 'book' else []):
        g, ev = got[k], exp.get(k, np.nan)
        if k == 'co' and mi > 2026 * 12 + 6:
            continue
        n_cmp[k] += 1
        if np.isnan(ev) != np.isnan(g):
            mismatch.append((kind, a, mi, k, None if np.isnan(ev) else float(ev), None if np.isnan(g) else float(g)))
        elif not np.isnan(ev):
            d = abs(float(ev) - float(g)) / (1 + abs(float(ev)))
            worst[k] = max(worst[k], d)
            if d > 1e-4:
                mismatch.append((kind, a, mi, k, float(ev), float(g)))
res = dict(pairs=len(pairs), values_compared=int(sum(n_cmp.values())), compared_by_feature=dict(n_cmp), mismatches=len(mismatch), mismatch_examples=mismatch[:10],
           worst_relative_difference={k: float(f'{v:.2e}') for k, v in worst.items()}, seed=7)
(OUT / 'burst_features_check.json').write_text(json.dumps(res, indent=1))
log(json.dumps({k: v for k, v in res.items() if k != 'compared_by_feature'}))
