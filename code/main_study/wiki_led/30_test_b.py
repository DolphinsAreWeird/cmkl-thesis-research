# 30. Test B (new books): can Wikipedia alone (the author's page before release) predict a new book's first 6 months of loans?
# Settings: prereg/wiki_led_settings_2026-10-20.json, section test_B_new_books (read-only; SHA-256 in prereg/README.md).
# Rows: data/db/wiki_led/test_b_rows.parquet (built by 01_population, 01b_loans_library, 02_author_match, 03_author_views, 04_rows).
# Output: data/db/wiki_led/test_b_preds.parquet, data/reports/wiki_led_test_b.json, wiki_led_test_b_accuracy.csv
import sys, json, time, pathlib, hashlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr, rankdata
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
REC = ROOT / 'prereg' / 'wiki_led_settings_2026-10-20.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '88d895c38c128753aaaabf3294c85969c066db8b0852089ae6e47609958c145b'
OUT, REP = D / 'db' / 'wiki_led', D / 'reports'
SEED = 20261020
NB = 2000
T0 = time.time()
# Corrections B1 to B4 of the code audit (prereg/DEVIATIONS.md, logged before any Test B score): time-safe matched and
# writer_type, no first-month format flags in the library model (kept only in a labelled check), works whose month before
# first_ym is an excluded month left out of the main scoring, bootstrap clusters merged across creator keys sharing an article.
WCOLS = ['matched_pre', 'v6', 'v12', 'trend', 'vmax', 'writer_type_pre']
LCOLS = ['n_prior_works', 'ln_prior_loans', 'month']
LCOLS_FMT = ['fmt_print', 'fmt_ebook', 'fmt_audiobook'] + LCOLS                 # labelled check only (month-0 information)
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def ym_add(ym, k):
    i = (ym // 100) * 12 + ym % 100 - 1 + k
    return (i // 12) * 100 + i % 12 + 1


R = pd.read_parquet(OUT / 'test_b_rows.parquet')
R['fm'] = (R.first_ym // 100) * 12 + R.first_ym % 100 - 1
R['year'] = R.first_ym // 100
# B1: an author counts as matched only if the article had a view in a month before the book's first month
V = pd.read_parquet(OUT / 'author_monthly_views.parquet')
first_view = V[V.views > 0].groupby('enwiki_title').ym.min()
fv = R.enwiki_title.map(first_view)
R['matched_pre'] = ((R.matched == 1) & fv.notna() & (fv < R.first_ym)).astype(int)
R['writer_type_pre'] = (R.writer_type * R.matched_pre).astype(int)
# B3: excluded months (any format fails month_ok in the demand panel), as YYYYMM
PM = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['ym', 'month_ok']).drop_duplicates()
EXCL = {int(s.replace('-', '')) for s in PM.loc[~PM.month_ok, 'ym'].unique()}
R['shifted'] = R.first_ym.map(lambda y: ym_add(y, -1) in EXCL).astype(int)
R['flag_wide'] = R.first_ym.map(lambda y: any(ym_add(y, k) in EXCL for k in range(-1, 6))).astype(int)
# B4: clusters = connected groups of creator_key and enwiki_title
parent = {}


def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for ck, t in R.loc[R.matched == 1, ['creator_key', 'enwiki_title']].drop_duplicates().itertuples(index=False):
    a, b = find('k:' + ck), find('t:' + str(t))
    if a != b:
        parent[a] = b
R['cluster'] = R.creator_key.map(lambda k: find('k:' + k))
log('rows', len(R), 'matched (Oct 2026)', R.matched.mean().round(3), 'matched before release', R.matched_pre.mean().round(3),
    'shifted first month (left out)', int(R.shifted.sum()), 'clusters', R.cluster.nunique(), 'creator keys', R.creator_key.nunique())
R = R[R.shifted == 0].copy()

preds = []
for Y in range(2019, 2027):
    te = R[R.year == Y]
    tr = R[R.fm + 5 < Y * 12]
    if te.empty:
        continue
    p = te[['work_id', 'cluster', 'year', 'Y6', 'loans6', 'matched_pre', 'writer_type_pre', 'flag_wide']].copy()
    p['N0'] = tr.Y6.mean()
    sc = StandardScaler().fit(tr[WCOLS])
    p['W_ridge'] = Ridge(alpha=1.0).fit(sc.transform(tr[WCOLS]), tr.Y6).predict(sc.transform(te[WCOLS]))
    for name, cols in (('W_lgbm', WCOLS), ('L_lgbm', LCOLS), ('LW_lgbm', LCOLS + WCOLS),
                       ('Lfmt_check', LCOLS_FMT), ('LWfmt_check', LCOLS_FMT + WCOLS)):
        p[name] = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr.Y6).predict(te[cols])
    preds.append(p)
    log('year', Y, 'train', len(tr), 'test', len(te))
P = pd.concat(preds, ignore_index=True).rename(columns={'cluster': 'creator_key'})   # bootstrap below resamples 'creator_key'
P.to_parquet(OUT / 'test_b_preds.parquet', index=False)
MODELS = ['N0', 'W_ridge', 'W_lgbm', 'L_lgbm', 'LW_lgbm', 'Lfmt_check', 'LWfmt_check']

# ---------------------------------------------------------------- scores with author-cluster bootstrap
years = sorted(P.year.unique())


def year_spearman(df, c):
    out = []
    for y in years:
        g = df[df.year == y]
        out.append(spearmanr(g[c], g.Y6).statistic if g[c].nunique() > 1 else 0.0)
    return float(np.mean(out))


def top10(df, c):
    hits = []
    for y in years:
        g = df[df.year == y]
        a = g.Y6 >= g.Y6.quantile(0.9)
        pr = g[c] >= g[c].quantile(0.9) if g[c].nunique() > 1 else pd.Series(False, index=g.index)
        hits.append((a & pr).sum() / max(pr.sum(), 1))
    return float(np.mean(hits))


def scores(df, label):
    rng = np.random.default_rng(SEED)
    keys = df.creator_key.values
    uk, inv = np.unique(keys, return_inverse=True)
    rows_of = pd.Series(np.arange(len(df))).groupby(inv).apply(np.array).values
    yr = df.year.values
    base = {c: year_spearman(df, c) for c in MODELS}
    draws = {c: [] for c in MODELS}
    diff_lw_l = []
    for b in range(NB):
        pick = rng.integers(0, len(uk), len(uk))
        idx = np.concatenate(rows_of[pick])
        sub_y = df.Y6.values[idx]
        vals = {}
        for c in MODELS:
            if c == 'N0':
                vals[c] = 0.0; continue
            x = df[c].values[idx]
            v = []
            for y in years:
                m = yr[idx] == y
                if m.sum() > 10:
                    v.append(np.corrcoef(rankdata(x[m]), rankdata(sub_y[m]))[0, 1])
            vals[c] = float(np.mean(v))
        for c in MODELS:
            draws[c].append(vals[c])
        diff_lw_l.append(vals['LW_lgbm'] - vals['L_lgbm'])
        if b % 500 == 0:
            log('  bootstrap', label, b)
    out = {}
    act = np.expm1(df.Y6)
    for c in MODELS:
        pr = np.expm1(df[c]).clip(lower=0)
        e = (pr - act).abs()
        out[c] = dict(spearman=base[c], lo=float(np.percentile(draws[c], 2.5)), hi=float(np.percentile(draws[c], 97.5)),
                      pooled_spearman=float(spearmanr(df[c], df.Y6).statistic) if c != 'N0' else 0.0,
                      mae_log=float((df[c] - df.Y6).abs().mean()), mae_loans=float(e.mean()), median_err_loans=float(e.median()),
                      wape=float(e.sum() / act.sum()), within_25pct=float(((e <= 0.25 * act) & (act >= 4)).sum() / (act >= 4).sum()),
                      r2_log=float(1 - ((df[c] - df.Y6) ** 2).sum() / ((df.Y6 - df.Y6.mean()) ** 2).sum()),
                      top10_precision=top10(df, c))
    out['LW_minus_L'] = dict(mean=base['LW_lgbm'] - base['L_lgbm'], lo=float(np.percentile(diff_lw_l, 2.5)),
                             hi=float(np.percentile(diff_lw_l, 97.5)))
    out['n'] = dict(rows=len(df), authors=len(uk), mean_loans6=float(act.mean()), median_loans6=float(act.median()))
    return out


res = {'all': scores(P, 'all')}
res['matched'] = scores(P[P.matched_pre == 1].reset_index(drop=True), 'matched')
res['writer_type'] = scores(P[P.writer_type_pre == 1].reset_index(drop=True), 'writer_type')
res['no_flagged_months'] = scores(P[P.flag_wide == 0].reset_index(drop=True), 'no_flagged_months')
res['decisions'] = dict(B1_primary=res['all']['W_lgbm']['lo'] > 0, B2=res['all']['LW_minus_L']['lo'] > 0,
                        B3_matched_B1=res['matched']['W_lgbm']['lo'] > 0, B3_matched_B2=res['matched']['LW_minus_L']['lo'] > 0,
                        B3_writer_B1=res['writer_type']['W_lgbm']['lo'] > 0, B3_writer_B2=res['writer_type']['LW_minus_L']['lo'] > 0)
res['runtime_s'] = round(time.time() - T0)
(REP / 'wiki_led_test_b.json').write_text(json.dumps(res, indent=1))
pd.DataFrame({k: v for k, v in res['all'].items() if k in MODELS}).T.to_csv(REP / 'wiki_led_test_b_accuracy.csv')
for k in ['all', 'matched', 'writer_type']:
    log(k, {c: round(res[k][c]['spearman'], 3) for c in MODELS}, 'LW-L', round(res[k]['LW_minus_L']['mean'], 4),
        (round(res[k]['LW_minus_L']['lo'], 4), round(res[k]['LW_minus_L']['hi'], 4)))
log('decisions', res['decisions'])
