# 11. Placebo check of Test A: each book gets the Wikipedia pages (book and author) of a different book with similar traffic.
# Settings: prereg/addenda_wiki_led/2026-10-20_b_placebo_test_a.json (read-only; SHA-256 in prereg/README.md).
# Clarifications: "different author" = a different author_article, or a different creator when either book has no author
# article; a book with no book-article level at all is matched on its author-article level; matching value = median lvl4
# over origins 2016-03 to 2018-12, else over the book's first 12 origins with a value.
# Output: data/db/wiki_led/placebo_a_preds.parquet, data/reports/wiki_led_placebo_a.json
import sys, json, time, pathlib, hashlib, importlib.util
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_b_placebo_test_a.json'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == '9589a400807417bb7f8c3e381ab0c0bebba6e55af5c14aeee5026809887aad27'
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
T0 = time.time()
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)
SCORE0 = 2019 * 12


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


R = pd.read_parquet(OUT / 'test_a_rows.parquet')
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
WF = pd.read_parquet(OUT / 'test_a_wiki_features.parquet')

# ---------------------------------------------------------------- donors
def match_value(col):
    x = R[['work_id', 'mi', col]].dropna()
    early = x[(x.mi >= 2016 * 12 + 2) & (x.mi <= 2018 * 12 + 11)].groupby('work_id')[col].median()
    first12 = x.sort_values('mi').groupby('work_id').head(12).groupby('work_id')[col].median()
    return early.combine_first(first12)


vb, va = match_value('b_lvl4'), match_value('a_lvl4')
info = W.set_index('work_id')[['article', 'author_article', 'creator']]
info['akey'] = info.author_article.fillna('creator:' + info.creator.astype(str))
donor = {}
for kind, v in (('book', vb), ('author', va)):
    pool = v.sort_values()
    keys, vals = pool.index.values, pool.values
    for b in info.index:
        if b in donor or (kind == 'author' and b in vb.index):
            continue
        if b not in v.index:
            continue
        i = np.searchsorted(vals, v[b])
        best, bd = None, np.inf
        for j in range(max(0, i - 50), min(len(vals), i + 50)):
            d = keys[j]
            if d == b or info.akey[d] == info.akey[b]:
                continue
            dist = abs(vals[j] - v[b])
            if dist < bd or (dist == bd and d < best):
                best, bd = d, dist
        if best is not None:
            donor[b] = best
log('donors', len(donor), 'of', len(info))

# ---------------------------------------------------------------- swap the Wikipedia features
FB = WF[WF.kind == 'book'].drop(columns='kind').rename(columns={c: 'b_' + c for c in FEATS})
FA = WF[WF.kind == 'author'].drop(columns='kind').rename(columns={c: 'a_' + c for c in FEATS})
P = R.drop(columns=WCOLS).copy()
P['donor'] = P.work_id.map(donor)
P['d_article'] = P.donor.map(info.article)
P['d_author'] = P.donor.map(info.author_article)
P = P.merge(FB.rename(columns={'article': 'd_article'}), on=['d_article', 'mi'], how='left')
P = P.merge(FA.rename(columns={'article': 'd_author'}), on=['d_author', 'mi'], how='left')
nod = P.donor.isna()
P.loc[nod, WCOLS] = R.loc[nod.values, WCOLS].values                   # books without a donor keep their own (counted)
log('rows', len(P), 'without donor', int(nod.sum()))


def walk(df, cols, tgt):
    out = []
    for Y in range(2019, 2027):
        te = df[(df.year == Y) & (df.mi >= SCORE0)]
        if te.empty:
            continue
        tr = df[(df.mi + 1) < Y * 12]
        m = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr[tgt])
        out.append(pd.Series(m.predict(te[cols]), index=te.index))
    return pd.concat(out)


pr = P[(P.mi >= SCORE0)][['work_id', 'mi', 'D', 'Sg', 'Y', 'L_t']].copy()
for name, cols in (('pW', WCOLS), ('pHW', HCOLS + WCOLS)):
    for tgt in ('D', 'Y'):
        pr[f'{name}_{tgt}'] = walk(P, cols, tgt)
        log('fitted', name, tgt)
real = pd.read_parquet(OUT / 'test_a_preds.parquet')
pr = pr.merge(real[['work_id', 'mi', 'Wlgbm_D', 'HWlgbm_D', 'Hlgbm_D', 'Wlgbm_Y', 'HWlgbm_Y']], on=['work_id', 'mi'], how='inner')
pr.to_parquet(OUT / 'placebo_a_preds.parquet', index=False)

months = np.sort(pr.mi.unique())
rng = np.random.default_rng(SEED)
n, k = len(months), int(np.ceil(len(months) / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % n for a in rng.choice(n, k)])[:n] for _ in range(2000)])
g = {m: pr[pr.mi == m] for m in months}
sp = lambda c: np.array([spearmanr(g[m][c], g[m].D).statistic for m in months])
res = {}
S = {c: sp(c) for c in ['Wlgbm_D', 'pW_D', 'HWlgbm_D', 'pHW_D', 'Hlgbm_D']}
for c, v in S.items():
    b = v[BD].mean(1)
    res[c] = dict(change_rank=float(v.mean()), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)),
                  surge_ap_ratio=float(average_precision_score(pr.Sg, pr[c]) / pr.Sg.mean()))
for a, b_ in (('Wlgbm_D', 'pW_D'), ('HWlgbm_D', 'pHW_D'), ('pHW_D', 'Hlgbm_D')):
    d = S[a] - S[b_]
    bb = d[BD].mean(1)
    res[f'{a}_minus_{b_}'] = dict(mean=float(d.mean()), lo=float(np.percentile(bb, 2.5)), hi=float(np.percentile(bb, 97.5)))
act = np.expm1(pr.Y)
for c in ['Wlgbm_Y', 'pW_Y']:
    e = (np.expm1(pr[c]).clip(lower=0) - act).abs()
    res[c] = dict(mae_loans=float(e.mean()), wape=float(e.sum() / act.sum()),
                  level_rank=float(np.mean([spearmanr(g[m][c], g[m].Y).statistic for m in months])))
res['donors'] = len(donor)
res['rows_without_donor'] = int(nod.sum())
(REP / 'wiki_led_placebo_a.json').write_text(json.dumps(res, indent=1))
for k_, v in res.items():
    log(k_, v)
