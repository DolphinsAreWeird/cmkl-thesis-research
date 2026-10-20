# 20c. Test C (themes), CORRECTED RERUN: 20_test_c.py with corrections A1 and C1 of addendum e
# (prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json).  The original run and its files stay on file.
#   A1: in the weekly series of the book and author articles that are candidates, the weeks before an article's first week with at
#       least one view (views > 0) are missing, not zero (they are dropped before the monthly means are made, so the months before the
#       article's first view have no value and x(t) is missing for the first month with views).  The concept-term series are not
#       article series and are unchanged.
#   C1: for test year Y the candidate book and author articles come only from works whose first Seattle loan is before 1 January of Y
#       (first month with loans > 0 in data/db/study2r/counts_work.parquet, all formats; month index < Y * 12), so the candidate
#       list is built per test year.  The whole-period look-ahead version (Wsel_insample, for C2 only) keeps the full pool of the
#       theme's works, because it is the version that deliberately uses everything.
# Nothing else changed (rows, selection rule, ridge, scoring, seed).  Output: data/db/wiki_led/test_c_preds_c.parquet,
# test_c_selection_c.json, data/reports/wiki_led_test_c_c.json.   Full run: bash jobs/bg.sh wl_test_c_c main_study/wiki_led/20c_test_c.py
#
# Original header of 20_test_c.py:
# 20. Test C (themes): Wikipedia-only forecasts of the change in a theme's borrowing, with the library choosing the articles
# walk-forward. Settings: prereg/addenda_wiki_led/2026-10-20_a_test_c_themes.json (read-only; SHA-256 in prereg/README.md).
# Rows scored: the benchmark's main rows (Seattle print and ebook, middle and narrow themes, horizon 1, all 52 pipelines present:
# 36,081 rows, 510 series). Training targets come from the demand panel (data/db/study3/demand_panel.parquet) for every month
# before the test year, so that the 2019 models have earlier months to learn from.
# Clarification: selection and fitting are done per series (a theme in one format), because the theme's change differs by format.
import sys, os, json, time, pathlib, hashlib, csv, resource
import numpy as np, pandas as pd
from scipy.stats import spearmanr, rankdata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
ROOT = D.parent
ADD = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_a_test_c_themes.json'
SHA = '35c917cbce539ef75580d793fbe161b72ba4ecaf59a24e59889cb56b71b648bb'
assert hashlib.sha256(ADD.read_bytes()).hexdigest() == SHA, 'addendum changed'
ADD_E = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-20_e_corrections_robustness.json'
assert hashlib.sha256(ADD_E.read_bytes()).hexdigest() == '36f3605286b51b8123d791c1d59a7dc89356ec3bb66bfba6b9667327d31b3e52', 'addendum e changed'
os.nice(5)                                                               # machine rule: nice, one heavy job at a time
OUT = D / 'db' / 'wiki_led'
REP = D / 'reports'
B = D / 'db' / 'benchmark'
SEED = 20261020
K = 10
EPS = 1e-12
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def peak_mb():                                                           # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


# ---------------------------------------------------------------- main rows (as in the benchmark and the progress page)
pipes = [r[''] for r in csv.DictReader(open(B / 'stage2_results' / 'A2_table.csv'))]
wd = pd.read_parquet(B / 'wide2.parquet')
s = wd[(wd.group == 'seattle') & (wd.format.isin(['print', 'ebook'])) & (wd.h == 1)].dropna(subset=['y_true'] + pipes).copy()
s = s[s.groupby(['format', 'level', 'node_id']).origin_mi.transform('size') >= 12]
assert len(s) == 36081 and s.groupby(['format', 'level', 'node_id']).ngroups == 510
REFS = [c for c in ['seasonal_naive', 'revert6', 'chronos2', 'chronos2_cur', 'median_all'] if c in s.columns]
s = s[['format', 'level', 'node_id', 'origin_mi', 'y_true', 'y_t', 'naive'] + REFS].reset_index(drop=True)
s['c'] = s.y_true - s.y_t
log('main rows', len(s), 'refs', REFS)

# ---------------------------------------------------------------- training targets from the demand panel
P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['level', 'node_id', 'format', 'mi', 'month_ok', 'log_share'])
P = P[P.format.isin(['print', 'ebook']) & P.level.isin(['middle', 'narrow'])]
P.loc[~P.month_ok, 'log_share'] = np.nan
Y = P.pivot_table(index=['format', 'level', 'node_id'], columns='mi', values='log_share')
MI = np.array(Y.columns)
CY = Y.shift(-1, axis=1) - Y                                             # c(t) = y(t+1) - y(t), indexed by origin t
log('panel series', Y.shape)

# ---------------------------------------------------------------- candidate monthly changes x(t)
def monthly(df, key, a1=False):
    df = df[[key, 'week', 'share'] + (['views'] if a1 else [])].copy()
    df['week'] = pd.to_datetime(df['week'])
    if a1:                                                               # A1 (addendum e): weeks before the first week with views > 0 are missing
        fv = df.loc[df.views > 0].groupby(key).week.min()
        df = df[df.week >= df[key].map(fv)]                              # an article with no view at all has no weeks left
    e = df['week'] + pd.Timedelta(days=6)
    df['mi'] = e.dt.year * 12 + e.dt.month - 1
    m = df.groupby([key, 'mi']).share.mean().unstack('mi')
    v = np.log(m.clip(lower=EPS))
    return v.diff(axis=1)                                                # x(t) = value(t) - value(t-1)


WV = pd.read_parquet(D / 'db' / 'interest' / 'wiki' / 'weekly_value.parquet', columns=['value', 'node_id', 'week', 'share', 'source'])
WV = WV[WV.source == 'wikipedia']
val_node = WV[['value', 'node_id']].drop_duplicates()
XV = monthly(WV, 'value')
works = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
XB = monthly(pd.read_parquet(D / 'db' / 'study2r' / 'weekly_book.parquet', columns=['article', 'week', 'views', 'share']), 'article', a1=True)
XA = monthly(pd.read_parquet(D / 'db' / 'study2r' / 'weekly_author.parquet', columns=['article', 'week', 'views', 'share']), 'article', a1=True)
XALL = pd.concat([XV.set_axis(['v:' + str(i) for i in XV.index]), XB.set_axis(['b:' + str(i) for i in XB.index]),
                  XA.set_axis(['a:' + str(i) for i in XA.index])]).reindex(columns=MI)
log('candidate series', XALL.shape)
WT = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'work_theme.parquet', columns=['work_id', 'node_id', 'strength'])
WT = WT[(WT.strength >= 0.25) & WT.work_id.isin(works.work_id)].merge(works[['work_id', 'article', 'author_article']], on='work_id')
# C1: first month with loans > 0 of each work (all formats), month index year * 12 + month - 1 (as in 10_test_a.py)
CW = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
LM = CW.groupby(['work_id', 'mi']).y.sum()
FIRST = LM[LM > 0].reset_index().groupby('work_id').mi.min()
del CW, LM
WT['first_mi'] = WT.work_id.map(FIRST)
assert WT.first_mi.notna().all(), 'a work of the candidate pool has no loan'
log('works in the candidate pool', WT.work_id.nunique(), '| first loan month range', int(WT.first_mi.min()), int(WT.first_mi.max()))


def candidate_parts(level, node):
    if level == 'narrow':
        vals = val_node[val_node.node_id == node].value
    else:
        vals = val_node[(val_node.node_id == node) | val_node.node_id.str.startswith(node + '.')].value
    return ['v:' + v for v in vals], WT[WT.node_id == node]


def candidates(level, node, first_before=None):
    """All candidates of a theme; with first_before (a month index) only articles of works whose first loan is before that month (C1)."""
    v, wt = candidate_parts(level, node)
    if first_before is not None:
        wt = wt[wt.first_mi < first_before]
    c = v + ['b:' + a for a in wt.article.dropna().unique()] + ['a:' + a for a in wt.author_article.dropna().unique()]
    return [x for x in dict.fromkeys(c) if x in XALL.index]


def spearman_cols(X, y):
    """Spearman of each column of X (months x cands, NaN allowed) with y, on months where both exist; returns rho, n."""
    rho, n = np.full(X.shape[1], np.nan), np.zeros(X.shape[1], int)
    for j in range(X.shape[1]):
        ok = ~np.isnan(X[:, j]) & ~np.isnan(y)
        n[j] = ok.sum()
        if n[j] >= 24 and np.nanstd(X[ok, j]) > 0:
            rho[j] = spearmanr(X[ok, j], y[ok]).statistic
    return rho, n


def fit_predict(Xtr, ytr, Xte, w):
    mu, sd = np.nanmean(Xtr, 0), np.nanstd(Xtr, 0)
    sd[sd == 0] = 1
    Ztr, Zte = np.nan_to_num((Xtr - mu) / sd), np.nan_to_num((Xte - mu) / sd)
    ok = ~np.isnan(ytr)
    Ztr, yt = Ztr[ok], ytr[ok]
    ym, zc = yt.mean(), Ztr.mean(0)
    Zc = Ztr - zc
    A = Zc.T @ Zc + 1.0 * np.eye(Zc.shape[1])                            # ridge, alpha 1.0, intercept by centring
    beta = np.linalg.solve(A, Zc.T @ (yt - ym))
    pred = ym + (Zte - zc) @ beta
    index = Zte @ w / max(w.sum(), EPS)
    return pred, index


s['Wsel_ridge'] = 0.0
s['Wsel_index'] = 0.0
s['Wsel_insample'] = 0.0
s['n_selected'] = 0
sel_log = []
groups = list(s.groupby(['format', 'level', 'node_id']))
for gi, ((fmt, lev, node), g) in enumerate(groups):
    cand = candidates(lev, node)                                         # the full pool of the theme (used only by the look-ahead version)
    if (fmt, lev, node) not in CY.index or not cand:
        continue
    cy = CY.loc[(fmt, lev, node)].values
    X = XALL.loc[cand].values.T                                          # months x candidates
    cpos = {c: i for i, c in enumerate(cand)}
    years = sorted(set(((g.origin_mi + 1) // 12).astype(int)))
    for Yr in years:
        cand_y = candidates(lev, node, first_before=Yr * 12)             # C1: only works first lent before 1 January of Yr
        cols = [cpos[c] for c in cand_y]
        tr = (MI + 1) < Yr * 12
        te_rows = g.index[((g.origin_mi + 1) // 12) == Yr]
        if not cols:
            continue
        rho, n = spearman_cols(X[tr][:, cols], cy[tr])
        loc = [j for j in np.argsort(-np.nan_to_num(rho, nan=-9)) if rho[j] > 0][:K]
        order = [cols[j] for j in loc]                                   # columns of X
        if not order:
            continue
        te_mi = s.loc[te_rows, 'origin_mi'].values
        te_idx = np.searchsorted(MI, te_mi)
        pred, index = fit_predict(X[tr][:, order], cy[tr], X[te_idx][:, order], rho[loc])
        s.loc[te_rows, 'Wsel_ridge'] = pred
        s.loc[te_rows, 'Wsel_index'] = index
        s.loc[te_rows, 'n_selected'] = len(order)
        sel_log.append(dict(format=fmt, level=lev, node_id=node, year=Yr, n_cand=len(cand_y), n_cand_full_pool=len(cand), selected=[cand[j] for j in order],
                            rho=[round(float(rho[j]), 3) for j in loc]))
    # whole-period selection and fit (look-ahead, for C2 only)
    allm = (MI >= MI.min()) & (MI <= s.origin_mi.max())
    rho, n = spearman_cols(X[allm], cy[allm])
    order = [j for j in np.argsort(-np.nan_to_num(rho, nan=-9)) if rho[j] > 0][:K]
    if order:
        idx = np.searchsorted(MI, g.origin_mi.values)
        pred, _ = fit_predict(X[allm][:, order], cy[allm], X[idx][:, order], rho[order])
        s.loc[g.index, 'Wsel_insample'] = pred
    if gi % 50 == 0:
        log('series', gi, '/', len(groups), node, fmt, 'candidates', len(cand))
s.to_parquet(OUT / 'test_c_preds_c.parquet', index=False)
pd.DataFrame(sel_log).to_json(OUT / 'test_c_selection_c.json', orient='records')

# C1 check: every selected article comes from a work first lent before 1 January of the test year (the original run: 0.8% of the selected
# book articles and 7.9% of the selected author articles did not); and A1 check: no selected article series has a value before its first view
SL = pd.DataFrame(sel_log)
wt_all = WT[['node_id', 'article', 'author_article', 'first_mi']]
c1_bad = {'b': 0, 'a': 0}
c1_n = {'b': 0, 'a': 0}
for r_ in SL.itertuples():
    w_ = wt_all[wt_all.node_id == r_.node_id]
    for c in r_.selected:
        if c[:2] in ('b:', 'a:'):
            kind = c[0]
            col = 'article' if kind == 'b' else 'author_article'
            fm = w_.loc[w_[col] == c[2:], 'first_mi']
            c1_n[kind] += 1
            c1_bad[kind] += int(not (fm.min() < r_.year * 12))
log('C1 check: selected articles not from a work first lent before 1 January of the test year', c1_bad, 'of', c1_n)

# ---------------------------------------------------------------- scoring: rank correlation within origin x format x level groups
FC = {'N0': None, 'Wsel_ridge': s.Wsel_ridge, 'Wsel_index': s.Wsel_index, 'Wsel_insample': s.Wsel_insample}
for r in REFS:
    FC[r] = s[r] - s.y_t
grp = s.groupby(['origin_mi', 'format', 'level'])
keys = [k for k, g in grp if len(g) >= 10]
months = np.sort(s.origin_mi.unique())
mpos = {m: i for i, m in enumerate(months)}
rng = np.random.default_rng(SEED)
nb = int(np.ceil(len(months) / 3))
BD = np.array([np.concatenate([np.arange(a, a + 3) % len(months) for a in rng.choice(len(months), nb)])[:len(months)] for _ in range(2000)])
res = {'rank': {}, 'avgrelmae': {}}
for name, f in FC.items():
    vals = []
    for k in keys:
        g = grp.get_group(k)
        if name == 'N0':
            vals.append((k[0], 0.0)); continue
        x = f.loc[g.index]
        vals.append((k[0], spearmanr(x, g.c).statistic if x.nunique() > 1 else 0.0))
    v = pd.DataFrame(vals, columns=['m', 'r'])
    per_m = v.groupby('m').r.agg(['sum', 'count']).reindex(months).fillna(0)
    S_, C_ = per_m['sum'].values, per_m['count'].values
    boots = np.array([S_[b].sum() / C_[b].sum() for b in BD])
    res['rank'][name] = dict(mean=float(v.r.mean()), lo=float(np.percentile(boots, 2.5)), hi=float(np.percentile(boots, 97.5)), groups=len(v))
    log('rank', name, round(v.r.mean(), 4), (round(np.percentile(boots, 2.5), 4), round(np.percentile(boots, 97.5), 4)))
for name in ['Wsel_ridge']:
    lvl = s.y_t + s[name]
    rat = []
    for k, g in s.groupby(['format', 'level', 'node_id']):
        rat.append((lvl[g.index] - g.y_true).abs().mean() / (g.naive - g.y_true).abs().mean())
    res['avgrelmae'][name] = float(np.exp(np.log(rat).mean()))
res['coverage'] = dict(series=len(groups), rows_with_selection=float((s.n_selected > 0).mean()))
res['c1_check'] = dict(selected_book_articles=c1_n['b'], not_first_lent_before_test_year_book=c1_bad['b'],
                       selected_author_articles=c1_n['a'], not_first_lent_before_test_year_author=c1_bad['a'])
res['decisions'] = dict(C1_primary=res['rank']['Wsel_ridge']['lo'] > 0,
                        C2_lookahead=res['rank']['Wsel_insample']['mean'] - res['rank']['Wsel_ridge']['mean'])
res['runtime_s'] = round(time.time() - T0)
res['peak_rss_mb'] = round(peak_mb())
res['correction'] = 'A1 (weeks before the first week with views dropped from the article series) and C1 (candidates per test year from works first lent before 1 January of that year)'
(REP / 'wiki_led_test_c_c.json').write_text(json.dumps(res, indent=1, default=float))
log('done', res['decisions'])
