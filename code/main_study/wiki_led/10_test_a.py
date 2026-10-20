# 10. Test A (existing books): can Wikipedia alone predict which books' borrowing rises next month?
# Settings: prereg/wiki_led_settings_2026-10-20.json, section test_A_existing_books (read-only; SHA-256 in prereg/README.md).
# Units: the 7,747 Seattle works with their own English Wikipedia article (data/db/study2r/works.parquet).
# Wikipedia features come from data/db/study2r/weekly_book.parquet and weekly_author.parquet; loans from counts_work.parquet;
# library-wide monthly totals by format from data/db/study3/demand_panel.parquet (total_checkouts, the totals of spl_rows_*).
# Clarifications of the record (not changes; also written to the report):
#   (1) "normal" in r4, r1 and rmax is the median of the 26 weeks before the last 4 weeks; for nrise8, run and dw each week is
#       compared with the median of the 26 weeks before that week (the thesis rule for rising weeks); a median needs >= 13 weeks.
#   (2) excluded months are missing, not zero: M6 and the 12-month mean skip them (the benchmark treats such months as missing
#       rather than low demand); a row whose M6 window has no available month is dropped.
# Output: data/db/wiki_led/test_a_rows.parquet, test_a_preds.parquet, data/reports/wiki_led_test_a.md (+ .json)
#   python 10_test_a.py            (from code/, with ../.venv/bin/python)
import sys, json, time, pathlib, hashlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr, rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
REC = ROOT / 'prereg' / 'wiki_led_settings_2026-10-20.json'
SHA = '88d895c38c128753aaaabf3294c85969c066db8b0852089ae6e47609958c145b'
OUT = D / 'db' / 'wiki_led'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
SEED = 20261020
T0 = time.time()
assert hashlib.sha256(REC.read_bytes()).hexdigest() == SHA, 'settings record changed'
S = json.loads(REC.read_text())['test_A_existing_books']


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def mi_of(ym):  # 'YYYY-MM' -> month index year*12 + month-1
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


ORIG0, ORIG1 = mi_of('2016-03'), mi_of('2026-07')
SCORE0 = mi_of('2019-01')
EPS = 1e-12

# ---------------------------------------------------------------- excluded months (benchmark rule on library-wide totals)
# the panel's month_ok is the benchmark's implementation of the rule (months with no library total at all are also not ok)
P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok'])
P = P.drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
assert {mi_of('2020-05'), mi_of('2024-06')} <= EXCL, 'closure months not flagged'
log('excluded months:', sorted(f'{m // 12}-{m % 12 + 1:02d}' for m in EXCL))

# ---------------------------------------------------------------- loans panel
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
L = C.groupby(['work_id', 'mi']).y.sum()
first = L[L > 0].reset_index().groupby('work_id').mi.min()
MI = np.arange(mi_of('2005-04'), mi_of('2026-08') + 1)
LW = L.unstack('mi').reindex(columns=MI).fillna(0).astype(np.float32)   # works x months
LW = LW.reindex(W.work_id).fillna(0)
for w, m0 in first.items():                                             # months before the first loan: not in the collection
    LW.loc[w, LW.columns < m0] = np.nan
log('loans panel', LW.shape)
ex_mask = np.isin(MI, sorted(EXCL))

# ---------------------------------------------------------------- Wikipedia features per article and origin month
ORIGINS = np.arange(ORIG0, ORIG1 + 1)
ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']


def article_features(g):
    g = g.set_index('week').sort_index()
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    v = g['valid'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    normal = s.shift(4).rolling(26, min_periods=13).median()              # 26 weeks before the last 4
    nrm_w = s.shift(1).rolling(26, min_periods=13).median()               # 26 weeks before each week
    ratio_w = (s + EPS) / (nrm_w + EPS)
    up = (ratio_w >= 1.5) & nrm_w.notna() & s.notna()
    upv = up.values.astype(int)
    runlen = np.zeros(len(upv), int)
    for i in range(len(upv)):
        runlen[i] = (runlen[i - 1] + 1 if i else 1) if upv[i] else 0
    contrib = pd.Series(np.where(upv == 1, np.log(ratio_w.values) * np.minimum(runlen, 4) / 4, 0.0), index=grid)
    lr = np.log((s + EPS) / (normal + EPS))
    f = pd.DataFrame({
        'lvl4': np.log(m4.clip(lower=EPS)),
        'r4': np.log((m4 + EPS) / (normal + EPS)),
        'r1': lr,
        'rmax': np.log((s + EPS) / (normal + EPS)).rolling(4, min_periods=1).max(),
        'nrise8': up.astype(int).rolling(8, min_periods=1).sum(),
        'run': pd.Series(runlen, index=grid),
        'dw': contrib.rolling(8, min_periods=1).sum(),
        'chg': np.log((m4 + EPS) / (s.shift(4).rolling(4, min_periods=1).mean() + EPS)),
        'valid4': v.rolling(4, min_periods=1).mean(),
    }, index=grid)
    f.loc[normal.isna(), ['r4', 'r1', 'rmax']] = np.nan
    wend = (grid + pd.Timedelta(days=6)).values
    idx = np.searchsorted(wend, ENDS, side='right') - 1                     # last week ending on or before the month end
    ok = idx >= 0
    out = f.iloc[idx[ok]].copy()
    out['mi'] = ORIGINS[ok]
    # a week more than 2 weeks before the month end means the article had no data that month: features missing
    stale = (ENDS[ok] - wend[idx[ok]]) > np.timedelta64(13, 'D')
    out.loc[stale, FEATS] = np.nan
    return out.reset_index(drop=True)


def features_for(path, names):
    X = pd.read_parquet(path, columns=['article', 'week', 'share', 'valid'])
    X = X[X.article.isin(names)]
    X['week'] = pd.to_datetime(X['week'])
    parts = []
    for i, (a, g) in enumerate(X.groupby('article', sort=False)):
        h = article_features(g)
        h.insert(0, 'article', a)
        parts.append(h)
        if i % 2000 == 0:
            log('  features', path.name, i)
    return pd.concat(parts, ignore_index=True)


cache = OUT / 'test_a_wiki_features.parquet'
if cache.exists():
    WF = pd.read_parquet(cache)
else:
    fb = features_for(D / 'db' / 'study2r' / 'weekly_book.parquet', set(W.article.dropna()))
    fa = features_for(D / 'db' / 'study2r' / 'weekly_author.parquet', set(W.author_article.dropna()))
    fb['kind'], fa['kind'] = 'book', 'author'
    WF = pd.concat([fb, fa], ignore_index=True)
    WF.to_parquet(cache, index=False)
log('wiki features', WF.shape)
FB = WF[WF.kind == 'book'].drop(columns='kind').rename(columns={c: 'b_' + c for c in FEATS})
FA = WF[WF.kind == 'author'].drop(columns='kind').rename(columns={c: 'a_' + c for c in FEATS})

# ---------------------------------------------------------------- rows
rows = []
A = LW.values
for k, m in enumerate(ORIGINS):
    if m in EXCL or (m + 1) in EXCL:
        continue
    j = np.searchsorted(MI, m)
    win = A[:, j - 11:j + 1]
    present = np.nansum(win, axis=1) > 0
    w6 = A[:, j - 5:j + 1].copy()
    w6[:, ex_mask[j - 5:j + 1]] = np.nan
    w12 = A[:, j - 11:j + 1].copy()
    w12[:, ex_mask[j - 11:j + 1]] = np.nan
    with np.errstate(all='ignore'):
        M6 = np.nanmedian(w6, axis=1)
        m12 = np.nanmean(w12, axis=1)
    Lt, Lt1, Lnext = A[:, j], A[:, j - 1], A[:, j + 1]
    keep = present & ~np.isnan(M6) & ~np.isnan(Lnext) & ~np.isnan(Lt)
    if not keep.any():
        continue
    r = pd.DataFrame({
        'work_id': W.work_id.values[keep], 'mi': m,
        'L_t': Lt[keep], 'L_next': Lnext[keep], 'M6': M6[keep],
        'h_lt': np.log1p(Lt[keep]), 'h_lt1': np.log1p(np.nan_to_num(Lt1[keep])), 'h_m6': np.log1p(M6[keep]),
        'h_m12': np.log1p(m12[keep]), 'h_lyago': np.log1p(np.nan_to_num(A[keep, j - 11])),
        'h_age': m - first.reindex(W.work_id.values[keep]).values,
    })
    rows.append(r)
R = pd.concat(rows, ignore_index=True)
R['D'] = np.log1p(R.L_next) - np.log1p(R.M6)
R['Sg'] = ((R.D >= np.log(2)) & (R.L_next - R.M6 >= 5)).astype(int)
R['Y'] = np.log1p(R.L_next)
R = R.merge(W[['work_id', 'article', 'author_article']], on='work_id', how='left')
R = R.merge(FB, on=['article', 'mi'], how='left')
R = R.merge(FA.rename(columns={'article': 'author_article'}), on=['author_article', 'mi'], how='left')
R['year'] = (R.mi + 1) // 12                                             # year of the target month
R['test_year'] = R['year']
R.to_parquet(OUT / 'test_a_rows.parquet', index=False)
log('rows', R.shape, 'scored rows', (R.mi >= SCORE0).sum(), 'surge rate scored', R.loc[R.mi >= SCORE0, 'Sg'].mean().round(4))

WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)


def ridge_fit_predict(tr, te, cols, target):
    def prep(x, sc=None):
        z = x[cols].copy()
        miss = z.isna().astype(float).add_suffix('_na')
        z = pd.concat([z.fillna(0), miss], axis=1)
        return z
    ztr, zte = prep(tr), prep(te)
    sc = StandardScaler().fit(ztr)
    m = Ridge(alpha=1.0).fit(sc.transform(ztr), tr[target])
    return m.predict(sc.transform(zte))


def lgb_fit_predict(tr, te, cols, target):
    m = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr[target])
    return m.predict(te[cols])


# ---------------------------------------------------------------- walk-forward by year
preds = []
for Y in range(2019, 2027):
    te = R[(R.year == Y) & (R.mi >= SCORE0)]
    if te.empty:
        continue
    tr = R[(R.mi + 1) < Y * 12]                                         # outcome month before 1 January of Y
    p = te[['work_id', 'mi', 'year', 'D', 'Sg', 'Y', 'L_t', 'M6']].copy()
    p['N0_D'] = tr.D.mean(); p['N0_Y'] = tr.Y.mean()
    p['Wrule_D'] = te.b_dw.fillna(0).values + te.a_dw.fillna(0).values
    p['Hnaive_D'] = (te.h_lt - te.h_m6).values; p['Hnaive_Y'] = te.h_lt.values
    for tgt in ['D', 'Y']:
        p[f'Wridge_{tgt}'] = ridge_fit_predict(tr, te, WCOLS, tgt)
        p[f'Wlgbm_{tgt}'] = lgb_fit_predict(tr, te, WCOLS, tgt)
        p[f'Hlgbm_{tgt}'] = lgb_fit_predict(tr, te, HCOLS, tgt)
        p[f'HWlgbm_{tgt}'] = lgb_fit_predict(tr, te, HCOLS + WCOLS, tgt)
    preds.append(p)
    log('year', Y, 'train', len(tr), 'test', len(te))
PR = pd.concat(preds, ignore_index=True)
PR.to_parquet(OUT / 'test_a_preds.parquet', index=False)

# ---------------------------------------------------------------- scoring
MODELS_D = ['Wrule_D', 'Wridge_D', 'Wlgbm_D', 'Hnaive_D', 'Hlgbm_D', 'HWlgbm_D']
MODELS_Y = ['N0_Y', 'Wridge_Y', 'Wlgbm_Y', 'Hnaive_Y', 'Hlgbm_Y', 'HWlgbm_Y']
months = np.sort(PR.mi.unique())
rng = np.random.default_rng(SEED)
NB = 2000


def per_month_spearman(col, tgt):
    out = []
    for m in months:
        g = PR[PR.mi == m]
        out.append(spearmanr(g[col], g[tgt]).statistic if g[col].nunique() > 1 else 0.0)
    return np.array(out)


def block_draws(n, block=3):
    starts = np.arange(n)
    k = int(np.ceil(n / block))
    draws = []
    for _ in range(NB):
        s = rng.choice(starts, k)
        idx = np.concatenate([np.arange(a, a + block) % n for a in s])[:n]
        draws.append(idx)
    return np.array(draws)


BD = block_draws(len(months))


def ci_mean(x):
    b = x[BD].mean(axis=1)
    return float(x.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


# book-resampling interval: weighted Pearson of within-month ranks with bootstrap weights per book (ranks from the full month)
books = np.sort(PR.work_id.unique())
bidx = {b: i for i, b in enumerate(books)}
PR['_bi'] = PR.work_id.map(bidx).values
WB = rng.poisson(1.0, size=(400, len(books))).astype(float)            # Poisson bootstrap weights, 400 draws (approximation)


def book_ci(col, tgt):
    vals = np.zeros(400)
    for m in months:
        g = PR[PR.mi == m]
        rx, ry, bi = rankdata(g[col]), rankdata(g[tgt]), g._bi.values
        w = WB[:, bi]
        sw = w.sum(1, keepdims=True)
        mx, my = (w * rx).sum(1, keepdims=True) / sw, (w * ry).sum(1, keepdims=True) / sw
        cov = (w * (rx - mx) * (ry - my)).sum(1)
        vx, vy = (w * (rx - mx) ** 2).sum(1), (w * (ry - my) ** 2).sum(1)
        vals += cov / np.sqrt(vx * vy)
    vals /= len(months)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


res = {'change_rank': {}, 'surge_ap': {}, 'level': {}, 'paired': {}}
SP = {}
for c in MODELS_D:
    SP[c] = per_month_spearman(c, 'D')
    m, lo, hi = ci_mean(SP[c])
    blo, bhi = book_ci(c, 'D')
    res['change_rank'][c] = dict(mean=m, lo=lo, hi=hi, book_lo=blo, book_hi=bhi, months_above_0=float((SP[c] > 0).mean()))
    log('change rank', c, round(m, 4), (round(lo, 4), round(hi, 4)))
d = SP['HWlgbm_D'] - SP['Hlgbm_D']
res['paired']['HW_minus_H_change_rank'] = dict(zip(['mean', 'lo', 'hi'], ci_mean(d)))
d2 = SP['Wlgbm_D'] - SP['Wrule_D']
res['paired']['Wlgbm_minus_Wrule_change_rank'] = dict(zip(['mean', 'lo', 'hi'], ci_mean(d2)))

base = PR.Sg.mean()
mpos = {m: np.where(PR.mi.values == m)[0] for m in months}
for c in MODELS_D:
    ap = average_precision_score(PR.Sg, PR[c])
    b = []
    for t in range(NB):                                                # month-block draws for AP
        ix = np.concatenate([mpos[months[i]] for i in BD[t]])
        b.append(average_precision_score(PR.Sg.values[ix], PR[c].values[ix]) / PR.Sg.values[ix].mean())
    res['surge_ap'][c] = dict(ap=float(ap), base=float(base), ratio=float(ap / base),
                              ratio_lo=float(np.percentile(b, 2.5)), ratio_hi=float(np.percentile(b, 97.5)))
    log('surge AP', c, round(ap, 4), 'base', round(base, 4))

for c in MODELS_Y:
    sp = per_month_spearman(c, 'Y') if not c.startswith('N0') else np.zeros(len(months))
    mae = float((PR[c] - PR.Y).abs().mean())
    m, lo, hi = ci_mean(sp)
    res['level'][c] = dict(spearman=m, lo=lo, hi=hi, mae=mae)
    log('level', c, round(m, 4), 'MAE', round(mae, 4))

res['n'] = dict(rows=int(len(PR)), months=int(len(months)), books=int(PR.work_id.nunique()), surge_rate=float(base),
                rows_with_book_features=float(PR.merge(R[['work_id', 'mi', 'b_lvl4']], on=['work_id', 'mi']).b_lvl4.notna().mean()))
res['decisions'] = {
    'A1_primary_W_alone_predicts_rises': res['change_rank']['Wlgbm_D']['lo'] > 0,
    'A2_W_adds_to_history': res['paired']['HW_minus_H_change_rank']['lo'] > 0,
    'A3_W_flags_surges': res['surge_ap']['Wlgbm_D']['ratio_lo'] > 1,
}
res['excluded_months'] = sorted(f'{m // 12}-{m % 12 + 1:02d}' for m in EXCL)
res['runtime_s'] = round(time.time() - T0)
(REP / 'wiki_led_test_a.json').write_text(json.dumps(res, indent=1, default=float))
log('decisions', res['decisions'])
