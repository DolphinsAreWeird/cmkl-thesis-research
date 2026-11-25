# m02. Addendum m, step 3: theme series and the book-level theme features (A_theme_pages).  DATA ONLY: no loans are related to
# anything (theme borrowing K uses the stored theme panel, as a feature); the report has counts.
# Settings: prereg/addenda_wiki_led/2026-11-25_m_theme_pages_single_books.json (read-only; SHA-256 checked).
#
# Arm C, hand-reviewed concept pages: data/db/interest/wiki/weekly_node.parquet, levels 3 and 2; valid week = 7 days, not partial, views > 0.
# Arm A, AI-sorted pages (S2): daily views of the 40,000 S2 pages (store data/interim/testF_views/), pairs of confidence 2 or 3 with the
#   assignment weights, middle = sum of its narrow pairs (testF/21_series.py's node_tables).  Time-safe admission: a page counts in the
#   series used at origin t once it has 2 different days in the daily top 500 (namespace rule) on or before the last day of t; once
#   admitted, its whole past is in the series.  Series for each admission version; features at origin t from the version of t.
# Series features: article_features() of l_books_in_time/l02_views.py copied unchanged (7 kept features used: lvl4, r4, r1, run, dw, chg,
#   valid4), for origins 2015-07 to 2026-08 (earlier origins only serve the 12-month moved placebo).
# Book features (per work and origin, per level n = narrow, m = middle): strength-weighted mean of the 7 features over the work's themes
#   at that level whose r4 is present (each feature over the themes where it is present too), max_r4, lasting (any run >= 4).
# Placebo 1 (donor): same level, different broad theme, closest median log weekly share over valid weeks 2016-01-04..2018-12-30 (arm A:
#   version of origin 2018-12), each donor at most 3 times, themes in an order drawn with seed 20261125.
# Placebo 2 (lag): the row's features at origin t-12.
# Theme borrowing K (secondary): per level, strength-weighted mean over the work's themes, in the row's format, of
#   k_r = ls(t) - median(ls(t-5..t)) and k_c = mean(ls(t-2..t)) - mean(ls(t-5..t-3)), ls = log share, months with month_ok false left out.
# Outputs (row order of l_books_in_time/rows.parquet restricted to origins up to 2026-07): data/db/wiki_led/m_theme_pages/feat_C.parquet,
#   feat_A.parquet, feat_K.parquet, node_features_C.parquet, node_features_A.parquet, donors.csv; report data/reports/theme_pages_m02_features.md
#   Run from code/:  bash ../jobs/bg.sh m02_features main_study/wiki_led/m_theme_pages/m02_theme_features.py
import sys, os, json, time, hashlib, pathlib, resource, warnings
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'testF'))
import _testf_analysis as T                                    # noqa: E402  (Test F helpers; checks addendum g's fingerprints)

DATA = T.D
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_m_theme_pages_single_books.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'df8a4fd95bb46cec3488ba062b0033156e2ded4d00678cf899471cc201663d7f', 'addendum m changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
OUT = DATA / 'db' / 'wiki_led' / 'm_theme_pages'
OUT.mkdir(parents=True, exist_ok=True)
REP = DATA / 'reports'
TAXO = DATA / 'db' / 'taxonomy_v3'
os.nice(5)
T0 = time.time()
warnings.simplefilter('ignore', RuntimeWarning)


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def month_end(mi):
    y, m = divmod(mi, 12)
    return pd.Timestamp(year=y, month=m + 1, day=1) + pd.offsets.MonthEnd(0)


# ---------------------------------------------------------------- article_features() copied unchanged from l02_views.py (origins wider)
ORIGINS = np.arange(mi_of('2015-07'), mi_of('2026-08') + 1)
ENDS = np.array([month_end(m) for m in ORIGINS], dtype='datetime64[ns]')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
EPS = 1e-12


def article_features(g):
    g = g.set_index('week').sort_index()
    seen = (g['views'] > 0).to_numpy()
    if not seen.any():
        return None
    g = g.iloc[int(seen.argmax()):]
    grid = pd.date_range(g.index.min(), g.index.max(), freq='7D')
    s = g['share'].reindex(grid).astype(float)
    v = g['valid'].reindex(grid).astype(float)
    m4 = s.rolling(4, min_periods=1).mean()
    normal = s.shift(4).rolling(26, min_periods=13).median()
    nrm_w = s.shift(1).rolling(26, min_periods=13).median()
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
    idx = np.searchsorted(wend, ENDS, side='right') - 1
    ok = idx >= 0
    out = f.iloc[idx[ok]].copy()
    out['mi'] = ORIGINS[ok]
    stale = (ENDS[ok] - wend[idx[ok]]) > np.timedelta64(13, 'D')
    out.loc[stale, FEATS] = np.nan
    return out.reset_index(drop=True)


F7 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']

# check of the copy: stored book-article features of addendum l are reproduced (40 articles, origins 2016-03 to 2026-08)
WB = pd.read_parquet(L / 'weekly_book.parquet')
WFs = pd.read_parquet(L / 'wiki_features.parquet')
WFs = WFs[WFs.kind == 'book']
chk_titles = sorted(WFs.article.unique())[::max(1, WFs.article.nunique() // 40)][:40]
worst = 0.0
for t in chk_titles:
    g = WB[WB.article == t][['week', 'views', 'share', 'valid']].copy()
    g['week'] = pd.to_datetime(g.week)
    mine = article_features(g)
    ref = WFs[WFs.article == t]
    cm = ref.merge(mine, on='mi', suffixes=('_ref', ''))
    for c in FEATS:
        d = np.nanmax(np.abs(cm[c].to_numpy(float) - cm[c + '_ref'].to_numpy(float))) if len(cm) else 0.0
        both_nan = (cm[c].isna() == cm[c + '_ref'].isna()).all()
        assert both_nan, f'missing pattern differs for {t} {c}'
        worst = max(worst, 0.0 if np.isnan(d) else d)
assert worst < 1e-6, f'copied article_features does not reproduce addendum l ({worst})'
log('check: article_features copy reproduces addendum l on', len(chk_titles), 'articles, largest difference', worst)
del WB, WFs

TW = T.weekly_totals()[['week', 'total_views', 'days_covered', 'partial_week']].reset_index(drop=True)
TW['week'] = pd.to_datetime(TW.week)
NW = len(TW)
TOTV = TW.total_views.to_numpy(float)
FULLWK = ((TW.days_covered == 7) & ~TW.partial_week).to_numpy()


def feats_from_series(views):
    """views: weekly views (NW) of one theme -> DataFrame mi + FEATS, or None."""
    g = pd.DataFrame({'week': TW.week, 'views': views, 'share': views / TOTV, 'valid': FULLWK & (views > 0)})
    return article_features(g)


NODES = T.load_nodes()
broad_of = lambda n: n.split('.')[0]
PRE = (TW.week >= '2016-01-04') & (TW.week <= '2018-12-30')


def pre_level(views):
    sh = views / TOTV
    ok = PRE.to_numpy() & FULLWK & (views > 0)
    return float(np.median(np.log(sh[ok]))) if ok.any() else np.nan


# ---------------------------------------------------------------- arm C series
WN = pd.read_parquet(DATA / 'db' / 'interest' / 'wiki' / 'weekly_node.parquet')
WN = WN[WN.level.isin([2, 3])]
WN['week'] = pd.to_datetime(WN.week)
nfC, preC = [], {}
for nid, g in WN.groupby('node_id'):
    v = g.set_index('week').views.reindex(TW.week).fillna(0.0).to_numpy(float)
    preC[nid] = pre_level(v)
    f = feats_from_series(v)
    if f is not None:
        f.insert(0, 'node_id', nid)
        nfC.append(f)
NFC = pd.concat(nfC, ignore_index=True)
NFC.to_parquet(OUT / 'node_features_C.parquet', index=False)
log('arm C: themes with features', NFC.node_id.nunique())
del WN

# ---------------------------------------------------------------- arm A series (time-safe admission)
P = T.Paths()
A = T.read_assign(P, 'pages')
S2P = pd.read_parquet(P / 's2_pages.parquet')
use = set(S2P[S2P.selected & S2P.stored].title)
pairs = A[(A.set == 'universe') & (A.conf >= T.S2_MIN_CONF) & A.title.isin(use)][['title', 'code', 'weight']]
par = T.parent_map()
allp = pd.concat([pairs.assign(node_id=pairs.code), pairs.assign(node_id=pairs.code.map(par))], ignore_index=True)
nodesA = sorted(allp.node_id.unique())
npos = {n: j for j, n in enumerate(nodesA)}
log('arm A: pages', len(use), '| page-theme pairs (narrow)', len(pairs), '| themes', len(nodesA))
TL, top_days = T.top_long(sorted(use))
TL = TL.drop_duplicates(['title', 'date']).sort_values(['title', 'date'])
second = TL.groupby('title').date.nth(1)                              # the second different day in the top 500
second = pd.Series(second.values, index=TL.loc[second.index, 'title'].values)
adm_mi = (second.dt.year * 12 + second.dt.month - 1).reindex(sorted(use))
n_never = int(adm_mi.isna().sum())
adm_mi = adm_mi.fillna(10 ** 6)                                       # never twice in the top 500: never admitted
log('arm A: pages with 2 top-500 days by 2026-09-30', len(use) - n_never, 'of', len(use))
AM0, AM1 = int(ORIGINS[0]), int(ORIGINS[-1])
adm_idx = adm_mi.clip(lower=AM0).astype(int) - AM0                   # pages admitted before 2015-07 count from the first origin
NA = AM1 - AM0 + 2                                                    # last slot: admitted after 2026-08 (never used for features)
adm_idx = adm_idx.clip(upper=NA - 1)
dwk = ((T.DAYS - pd.Timestamp('2015-06-29')).days // 7).to_numpy()   # day -> week index of TW (weeks start Monday 2015-06-29)
assert (TW.week.iloc[0] == pd.Timestamp('2015-06-29')) and dwk.max() < NW
acc = np.zeros((len(nodesA), NA, NW), np.float64)
idx = T.store_index(P)
idx = idx[idx.title.isin(use)]
for fi, (f, g) in enumerate(idx.groupby('file')):
    with np.load(P.views / f, allow_pickle=False) as z:
        Vb = z['views'][g.row.to_numpy()].astype(np.float64)
    Wk = np.zeros((len(g), NW))
    np.add.at(Wk.T, dwk, Vb.T)                                         # daily -> weekly sums per page
    tl = g.title.to_numpy()
    tpos = {t: i for i, t in enumerate(tl)}
    pb = allp[allp.title.isin(tpos)]
    pi_ = pb.title.map(tpos).to_numpy()
    ai_ = adm_idx.reindex(pb.title).to_numpy()
    assert not np.isnan(ai_.astype(float)).any(), 'page without admission month'
    np.add.at(acc, (pb.node_id.map(npos).to_numpy(), ai_.astype(int)), Wk[pi_] * pb.weight.to_numpy()[:, None])
    if fi % 20 == 0:
        log('  arm A store files', fi + 1)
# check: all pages together reproduce Test F's stored S2 weekly series
S2W = pd.read_parquet(P / 'series_weekly_S2.parquet')
S2W['week'] = pd.to_datetime(S2W.week)
tot = acc.sum(axis=1)
ref = S2W.pivot_table(index='node_id', columns='week', values='views').reindex(index=nodesA, columns=TW.week).fillna(0.0).to_numpy()
rel = np.abs(tot - ref).max() / max(ref.max(), 1)
log('check: all S2 pages reproduce series_weekly_S2, largest relative difference', rel)
assert rel < 1e-6, 'arm A series do not reproduce Test F'
nfA, preA, nversions = [], {}, 0
pre_slot = mi_of('2018-12') - AM0
for nid in nodesA:
    j = npos[nid]
    cum = np.cumsum(acc[j], axis=0)                                   # series of the pages admitted by each origin
    preA[nid] = pre_level(cum[pre_slot])
    slots = [s for s in range(NA - 1) if acc[j, s].any()]
    for k, s in enumerate(slots):
        s_end = slots[k + 1] - 1 if k + 1 < len(slots) else NA - 2
        f = feats_from_series(cum[s])
        nversions += 1
        if f is None:
            continue
        f = f[(f.mi >= AM0 + s) & (f.mi <= AM0 + s_end)]
        f.insert(0, 'node_id', nid)
        nfA.append(f)
NFA = pd.concat(nfA, ignore_index=True)
NFA.to_parquet(OUT / 'node_features_A.parquet', index=False)
adm_by_year = {int(k): int(v) for k, v in (adm_mi[adm_mi < 10 ** 6] // 12).value_counts().sort_index().items()}
log('arm A: themes with features', NFA.node_id.nunique(), '| series versions', nversions)
del acc, S2W, ref, TL

# ---------------------------------------------------------------- donors (placebo 1)
rng = np.random.default_rng(20261125)


def donors(pre):
    out = {}
    for lv in (2, 3):
        nodes = sorted(n for n, v in pre.items() if T.level_of(n) == lv and np.isfinite(v))
        order = [nodes[i] for i in rng.permutation(len(nodes))]
        used = {n: 0 for n in nodes}
        for n in order:
            cands = sorted((abs(pre[c] - pre[n]), c) for c in nodes if broad_of(c) != broad_of(n) and used[c] < 3)
            if cands:
                out[n] = cands[0][1]
                used[cands[0][1]] += 1
    return out


DON = {'C': donors(preC), 'A': donors(preA)}
pd.DataFrame([(a, n, d, preC.get(n) if a == 'C' else preA.get(n), preC.get(d) if a == 'C' else preA.get(d)) for a in DON for n, d in DON[a].items()],
             columns=['arm', 'node_id', 'donor', 'pre_level', 'donor_pre_level']).to_csv(OUT / 'donors.csv', index=False)
log('donors: C', len(DON['C']), 'A', len(DON['A']))

# ---------------------------------------------------------------- rows and the work-theme pairs
R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi'])
R = R[R.mi <= mi_of('2026-07')].reset_index(drop=True)
R['format'] = R.format.astype(str)
works = np.sort(R.work_id.unique())
wpos = {w: i for i, w in enumerate(works)}
WT = pd.read_parquet(TAXO / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'strength'])
WT = WT[WT.work_id.isin(wpos) & WT.level.isin([2, 3])]
log('rows', len(R), '| works', len(works), '| work-theme pairs (levels 2, 3)', len(WT))
NO = len(ORIGINS)
ri_w = R.work_id.map(wpos).to_numpy()
ri_o = (R.mi - AM0).to_numpy()
assert ri_o.min() >= 0


def book_features(NF, arm, donor_map=None):
    """-> dict column -> float32 array aligned with R (real) and the same at t-12 (lag)."""
    cols_real, cols_lag = {}, {}
    for lv, tag in ((3, 'n'), (2, 'm')):
        pr = WT[WT.level == lv]
        nid = pr.node_id.map(donor_map) if donor_map is not None else pr.node_id
        keep = nid.notna()
        pr, nid = pr[keep], nid[keep]
        nodes = sorted(set(nid) & set(NF.node_id))
        npos_ = {n: i for i, n in enumerate(nodes)}
        X = np.full((len(nodes), NO, len(F7)), np.nan, np.float32)
        nf = NF[NF.node_id.isin(npos_)]
        X[nf.node_id.map(npos_).to_numpy(), (nf.mi - AM0).to_numpy()] = nf[F7].to_numpy(np.float32)
        inn = nid.isin(npos_).to_numpy()
        pw = pr.work_id.map(wpos).to_numpy()[inn]
        pn = nid[inn].map(npos_).to_numpy()
        ps = pr.strength.to_numpy(np.float64)[inn]
        Wf = np.full((len(works), NO, len(F7) + 2), np.nan, np.float32)
        for o in range(NO):
            V = X[pn, o, :].astype(np.float64)                           # pairs x 7
            has = ~np.isnan(V[:, 1])                                       # r4 present
            if not has.any():
                continue
            num = np.zeros((len(works), len(F7))); den = np.zeros((len(works), len(F7)))
            for k in range(len(F7)):
                ok = has & ~np.isnan(V[:, k])
                num[:, k] = np.bincount(pw[ok], weights=ps[ok] * V[ok, k], minlength=len(works))
                den[:, k] = np.bincount(pw[ok], weights=ps[ok], minlength=len(works))
            with np.errstate(invalid='ignore', divide='ignore'):
                Wf[:, o, :len(F7)] = np.where(den > 0, num / den, np.nan)
            mx = np.full(len(works), -np.inf)
            np.maximum.at(mx, pw[has], V[has, 1])
            lst = np.zeros(len(works))
            np.maximum.at(lst, pw[has], (V[has, 3] >= 4).astype(float))
            anyw = np.bincount(pw[has], minlength=len(works)) > 0
            Wf[:, o, len(F7)] = np.where(anyw, mx, np.nan)
            Wf[:, o, len(F7) + 1] = np.where(anyw, lst, np.nan)
        names = [f'{arm}_{tag}_{c}' for c in F7] + [f'{arm}_{tag}_maxr4', f'{arm}_{tag}_lasting']
        real = Wf[ri_w, ri_o, :]
        lo = ri_o - 12
        lag = np.full_like(real, np.nan)
        okl = lo >= 0
        lag[okl] = Wf[ri_w[okl], lo[okl], :]
        for k, c in enumerate(names):
            cols_real[c] = real[:, k]
            cols_lag[c] = lag[:, k]
        del Wf, X
    return cols_real, cols_lag


summ = dict(check_article_features_max_diff=worst, check_arm_A_vs_testF_rel=float(rel), admitted_by_year=adm_by_year, coverage={})
sc = (R.mi >= mi_of('2019-01')).to_numpy()
for arm, NF in (('C', NFC), ('A', NFA)):
    real, lag = book_features(NF, arm)
    don, _ = book_features(NF, arm, DON[arm])
    out = pd.DataFrame({'work_id': R.work_id, 'format': R.format, 'mi': R.mi})
    for c in real:
        out[c] = real[c]
    for c in real:
        out[c.replace(f'{arm}_', f'{arm}d_', 1)] = don[c]
    for c in real:
        out[c.replace(f'{arm}_', f'{arm}l_', 1)] = lag[c]
    out.to_parquet(OUT / f'feat_{arm}.parquet', index=False)
    summ['coverage'][arm] = {f'{k}_{lv}': float(np.mean(~np.isnan(d[f'{arm}_{lv}_r4'][sc]))) for k, d in (('real', real), ('donor', don), ('lag', lag))
                             for lv in ('n', 'm')}
    log('arm', arm, 'book features written; share of scored rows with a feature', summ['coverage'][arm])
    del real, lag, don, out

# ---------------------------------------------------------------- theme borrowing K
DP = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['level', 'node_id', 'format', 'mi', 'month_ok', 'log_share'])
DP = DP[DP.level.isin(['narrow', 'middle'])]
DP['format'] = DP.format.map({'book': 'print', 'print': 'print', 'ebook': 'ebook', 'audiobook': 'audiobook'})
assert DP.format.notna().all()
DP.loc[~DP.month_ok | ~np.isfinite(DP.log_share), 'log_share'] = np.nan
Kcols = {}
for lvname, lv, tag in (('narrow', 3, 'n'), ('middle', 2, 'm')):
    kr = np.full(len(R), np.nan); kc = np.full(len(R), np.nan)
    for fmt in ('print', 'ebook', 'audiobook'):
        Pv = DP[(DP.level == lvname) & (DP.format == fmt)].pivot_table(index='mi', columns='node_id', values='log_share', dropna=False)
        Pv = Pv.reindex(np.arange(Pv.index.min(), mi_of('2026-08') + 1))
        med6 = Pv.rolling(6, min_periods=1).median()
        a_r = (Pv - med6)
        a_c = Pv.rolling(3, min_periods=1).mean() - Pv.shift(3).rolling(3, min_periods=1).mean()
        pr = WT[WT.level == lv]
        pr = pr[pr.node_id.isin(Pv.columns)]
        cpos = {n: i for i, n in enumerate(Pv.columns)}
        rsel = np.flatnonzero((R.format == fmt).to_numpy())
        for name, Amat, tgt in (('k_r', a_r, kr), ('k_c', a_c, kc)):
            M_ = Amat.to_numpy()
            mpos = {m: i for i, m in enumerate(Amat.index)}
            # per row: weighted mean over the work's themes; done per origin month with bincount over pairs
            pw = pr.work_id.map(wpos).to_numpy(); pn = pr.node_id.map(cpos).to_numpy(); ps = pr.strength.to_numpy(float)
            rw_ = ri_w[rsel]; rm_ = R.mi.to_numpy()[rsel]
            for m in np.unique(rm_):
                if m not in mpos:
                    continue
                v = M_[mpos[m], pn]
                ok = np.isfinite(v)
                num = np.bincount(pw[ok], weights=ps[ok] * v[ok], minlength=len(works))
                den = np.bincount(pw[ok], weights=ps[ok], minlength=len(works))
                sel = rsel[rm_ == m]
                with np.errstate(invalid='ignore', divide='ignore'):
                    tgt[sel] = np.where(den[ri_w[sel]] > 0, num[ri_w[sel]] / den[ri_w[sel]], np.nan)
    Kcols[f'K_{tag}_r'] = kr.astype(np.float32); Kcols[f'K_{tag}_c'] = kc.astype(np.float32)
KO = pd.DataFrame({'work_id': R.work_id, 'format': R.format, 'mi': R.mi, **Kcols})
KO.to_parquet(OUT / 'feat_K.parquet', index=False)
summ['coverage']['K'] = {c: float(np.mean(~np.isnan(KO[c].to_numpy()[sc]))) for c in Kcols}
log('K written', summ['coverage']['K'])

summ['runtime_s'] = round(time.time() - T0)
summ['peak_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30, 2)
summ['themes_with_features'] = dict(C=int(NFC.node_id.nunique()), A=int(NFA.node_id.nunique()))
summ['donors'] = {a: len(v) for a, v in DON.items()}
(OUT / 'features_summary.json').write_text(json.dumps(summ, indent=1, default=str))
Lr = ['# Addendum m, step 3: theme series and book-level theme features (counts only)', '',
      f'Made by `code/main_study/wiki_led/m_theme_pages/m02_theme_features.py` on {time.strftime("%Y-%m-%d %H:%M")} (+07:00). Data only.', '',
      f'- Check: the copied article_features() gives addendum l\'s stored book-article features on 40 articles (largest difference {worst:.1e}).',
      f'- Check: all 40,000 S2 pages together give Test F\'s stored weekly series (largest relative difference {rel:.1e}).',
      f'- Themes with features: hand-reviewed pages {summ["themes_with_features"]["C"]}, AI-sorted pages {summ["themes_with_features"]["A"]}; donor themes found: {summ["donors"]}.',
      f'- AI-sorted pages admitted (second top-500 day), by year: {adm_by_year}.',
      '- Share of scored rows (origins 2019-01 to 2026-07) with a theme feature (r4 present):']
for arm, d in summ['coverage'].items():
    Lr.append(f'  - {arm}: ' + ', '.join(f'{k} {v:.3f}' for k, v in d.items()))
Lr.append(f'- Run time {summ["runtime_s"]} s, peak memory {summ["peak_gb"]} GB.')
(REP / 'theme_pages_m02_features.md').write_text('\n'.join(Lr) + '\n')
log('done')
