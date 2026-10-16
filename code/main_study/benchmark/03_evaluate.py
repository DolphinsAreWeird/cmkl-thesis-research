# Method benchmark, stage 1: score every pipeline with the evaluation fixed in prereg/benchmark_settings_2026-10-15.json.
# Stage 2 (python 03_evaluate.py --stage2): the same evaluation extended by prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (block at the end).
# Inputs: Study 4 forecasts, Study 4b change forecasts (as levels), LightGBM and Chronos forecasts; combinations built here.
# Outputs: data/reports/benchmark_stage1.md, data/db/benchmark/{wide.parquet, series_scores.parquet, summary.csv}.
import sys, pathlib, time, warnings
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
from scipy import stats
import _settings as ST

DB = ST.DB
OUT = DB / 'benchmark'
REP = ST.DATA / 'reports' / 'benchmark_stage1.md'
K = ['group', 'format', 'level', 'node_id', 'origin_mi', 'h']
SEED = 20261015
NBOOT = 2000
SINGLES_ALL = ['naive', 'seasonal_naive', 'ridge_D', 'ridge_DW', 'catboost_D', 'catboost_DW', 'lightgbm_D', 'lightgbm_DW', 'chronos']
FS = {'-': '', 'D': '_D', 'D+W': '_DW', 'D+W+G': '_DWG', 'D+W+G+T': '_DWGT', 'D+W+S': '_DWS'}


# ---------------- assemble ----------------
def load():
    s4 = pd.read_parquet(DB / 'study4' / 'forecasts.parquet')
    s4['pipe'] = s4.model + s4.fset.map(FS)
    base = s4[s4.model == 'naive'][K + ['tmonth', 'y_true', 'y_t']]
    parts = [s4[K + ['pipe', 'y_hat']]]
    for f, nm in (('lightgbm_forecasts.parquet', None), ('chronos_forecasts.parquet', None)):
        p = OUT / f
        if p.exists():
            d = pd.read_parquet(p)
            d['pipe'] = d.model + d.fset.map(FS)
            parts.append(d[K + ['pipe', 'y_hat']])
        else:
            print(f'missing {p}', flush=True)
    b = pd.read_parquet(DB / 'study4b' / 'forecasts.parquet')
    b = b[(b.part == 'A') & (b.model != 'zero') & b.h.isin([1, 2])].copy()
    b['group'] = 'seattle'
    b['pipe'] = b.model.map({'ridge': 'ridgechg', 'catboost': 'catchg'}) + b.fset.map(FS)
    b['y_hat'] = b.ls_t + b.pred
    parts.append(b[K + ['pipe', 'y_hat']])
    long = pd.concat(parts, ignore_index=True)
    wide = long.pivot_table(index=K, columns='pipe', values='y_hat', aggfunc='first')
    wide = base.set_index(K).join(wide, how='left').reset_index()
    # sanity: 4b level forecasts and Study 4 share the same y(t)
    chk = b.merge(base, on=K)
    assert np.allclose(chk.ls_t, chk.y_t, atol=1e-9), '4b ls_t differs from Study 4 y_t'
    return wide


def add_combinations(w):
    def mean_of(cols):
        return w[cols].mean(axis=1, skipna=False) if all(c in w for c in cols) else np.nan
    w['avg_ridge_cat_D'] = mean_of(['ridge_D', 'catboost_D'])
    w['avg_ridge_cat_DW'] = mean_of(['ridge_DW', 'catboost_DW'])
    w['avg_three_DW'] = mean_of(['ridge_DW', 'catboost_DW', 'lightgbm_DW'])
    w['avg_naive_ridge_D'] = mean_of(['naive', 'ridge_D'])
    singles = [c for c in SINGLES_ALL if c in w]
    w['median_all'] = w[singles].median(axis=1, skipna=True)
    # inverse-MAE weights from the 12 previous test origins whose target month is on or before the origin
    err = w[K[:4] + ['origin_mi', 'h']].copy()
    for c in singles:
        err[c] = (w[c] - w.y_true).abs()
    cell = ['group', 'format', 'level', 'h']
    om = err.groupby(cell + ['origin_mi'])[singles].mean().reset_index()
    wts = []
    for key, g in om.groupby(cell):
        h = key[3]
        g = g.sort_values('origin_mi')
        o = g.origin_mi.to_numpy(); M = g[singles].to_numpy()
        for i, t in enumerate(o):
            prev = np.where(o + h <= t)[0][-12:]
            if len(prev) < 12:
                wv = np.ones(len(singles))
            else:
                m = np.nanmean(M[prev], axis=0)
                wv = np.where(np.isfinite(m) & (m > 0), 1.0 / m, np.nan)
            wts.append((*key, t, *wv))
    W = pd.DataFrame(wts, columns=cell + ['origin_mi'] + [f'w_{c}' for c in singles])
    ww = w[cell + ['origin_mi']].merge(W, on=cell + ['origin_mi'], how='left')
    num = np.zeros(len(w)); den = np.zeros(len(w))
    for c in singles:
        f = w[c].to_numpy(float); a = ww[f'w_{c}'].to_numpy(float)
        ok = np.isfinite(f) & np.isfinite(a)
        num[ok] += a[ok] * f[ok]; den[ok] += a[ok]
    w['invmae_all'] = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
    return w


def add_segments(w):
    f4b = pd.read_parquet(DB / 'study4b' / 'features.parquet', columns=['format', 'level', 'node_id', 'origin_mi', 'h', 's_sustained', 'split_qok_shift8'])
    f4b['group'] = 'seattle'
    w = w.merge(f4b, on=K, how='left')
    seg = np.where(w.s_sustained == 1, 'after_lasting_rise', np.where(w.split_qok_shift8 == 1, 'after_short_rise', 'quiet'))
    w['segment'] = np.where(w.s_sustained.isna(), None, seg)
    w['surge'] = (w.y_true - w.y_t) >= np.log(1.3)
    return w


# ---------------- scoring ----------------
def series_scores(d, pipes, min_months=12):
    """Per series MAE of every pipeline on the months all pipelines scored; relative MAE to naive."""
    d = d.dropna(subset=pipes + ['y_true'])
    ser = ['group', 'format', 'level', 'node_id']
    n = d.groupby(ser).size()
    keep = n[n >= min_months].index
    d = d.set_index(ser).loc[keep].reset_index()
    E = d[ser].copy()
    for p in pipes:
        E[p] = (d[p] - d.y_true).abs()
    S = E.groupby(ser)[pipes].mean()
    S['months'] = d.groupby(ser).size()
    return S, d


def avg_rel(S, pipes, seed=SEED, nboot=NBOOT):
    """AvgRelMAE (geometric mean of MAE / MAE_naive) with a category bootstrap; median; share < 1; mean rank."""
    lr = np.log(S[pipes].div(S['naive'], axis=0))
    nodes = S.index.get_level_values('node_id')
    G = lr.groupby(nodes)
    sums, cnt = G.sum(), G.size()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(cnt), size=(nboot, len(cnt)))
    bs = sums.to_numpy()[idx].sum(axis=1) / cnt.to_numpy()[idx].sum(axis=1)[:, None]
    lo, hi = np.exp(np.quantile(bs, [0.025, 0.975], axis=0))
    ranks = S[pipes].rank(axis=1, method='average')
    out = pd.DataFrame({'AvgRelMAE': np.exp(lr.mean()), 'ci_lo': lo, 'ci_hi': hi,
                        'median_rel': np.exp(lr.median()), 'share_beats_naive': (lr < 0).mean(),
                        'mean_rank': ranks.mean()}, index=pipes)
    return out


def friedman_nemenyi(S, pipes):
    X = S[pipes].to_numpy()
    st, p = stats.friedmanchisquare(*[X[:, j] for j in range(X.shape[1])])
    k, N = len(pipes), len(X)
    q = stats.studentized_range.ppf(0.95, k, 100000) / np.sqrt(2)
    cd = q * np.sqrt(k * (k + 1) / (6 * N))
    return dict(friedman_stat=float(st), friedman_p=float(p), nemenyi_cd=float(cd), series=N, k=k)


def mcs(d, pipes):
    from arch.bootstrap import MCS
    L = pd.DataFrame({p: (d[p] - d.y_true).abs() for p in pipes}).groupby(d.origin_mi.to_numpy()).mean()
    m = MCS(L, size=0.10, reps=NBOOT, block_size=3, method='R', bootstrap='stationary', seed=SEED)
    m.compute()
    pv = m.pvalues['Pvalue'] if 'Pvalue' in m.pvalues else m.pvalues.iloc[:, 0]
    return set(m.included), pv.reindex(pipes)


def comparison(w, name, mask, pipes, with_mcs=True):
    pipes = [p for p in pipes if p in w and w.loc[mask, p].notna().any()]
    S, d = series_scores(w[mask], pipes)
    T = avg_rel(S, pipes)
    fr = friedman_nemenyi(S, pipes)
    if with_mcs:
        inc, pv = mcs(d, pipes)
        T['in_MCS'] = [p in inc for p in pipes]
        T['MCS_p'] = pv.values
    T = T.sort_values('AvgRelMAE')
    T.insert(0, 'comparison', name)
    meta = dict(name=name, rows=len(d), months=int(d.origin_mi.nunique()), **fr)
    return T, meta, S


PIPES_MAIN = ['naive', 'seasonal_naive', 'ridge_D', 'ridge_DW', 'catboost_D', 'catboost_DW', 'lightgbm_D', 'lightgbm_DW',
              'chronos', 'ridgechg_D', 'ridgechg_DW', 'ridgechg_DWS', 'catchg_D', 'catchg_DW', 'catchg_DWS',
              'avg_ridge_cat_D', 'avg_ridge_cat_DW', 'avg_three_DW', 'avg_naive_ridge_D', 'median_all', 'invmae_all']
PIPES_NEWS = ['naive', 'ridge_D', 'ridge_DW', 'ridge_DWG', 'ridge_DWGT', 'catboost_D', 'catboost_DW', 'catboost_DWG', 'catboost_DWGT']


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    w = add_segments(add_combinations(load()))
    w.to_parquet(OUT / 'wide.parquet', index=False)
    sea = w.group == 'seattle'
    pe = sea & w.format.isin(['print', 'ebook'])
    gd_end = ST.mi_from_ym('2021-05')
    comps = [
        ('A. Print and ebook, horizon 1 (main)', pe & (w.h == 1), PIPES_MAIN),
        ('B. Print and ebook, horizon 2', pe & (w.h == 2), PIPES_MAIN),
        ('C. Seattle audiobooks, horizon 1', sea & (w.format == 'audiobook') & (w.h == 1), PIPES_MAIN),
        ('D. LibriVox, horizon 1', (w.group == 'librivox') & (w.h == 1), [p for p in PIPES_MAIN if 'chg' not in p]),
        ('E. Print and ebook, horizon 1, news window 2019-01 to 2021-05', pe & (w.h == 1) & (w.origin_mi <= gd_end), PIPES_NEWS),
    ]
    tabs, metas, scores = [], [], {}
    for name, mask, pipes in comps:
        T, meta, S = comparison(w, name, mask, pipes)
        tabs.append(T); metas.append(meta); scores[name] = S
        print(f'{time.strftime("%H:%M:%S")} {name}: {meta["series"]} series, {meta["months"]} months', flush=True)
    # by level (main comparison), descriptive
    lev = []
    for L in ('narrow', 'middle'):
        T, meta, _ = comparison(w, f'A by level: {L}', pe & (w.h == 1) & (w.level == L), PIPES_MAIN, with_mcs=False)
        lev.append(T); metas.append(meta)
    # when: segments (horizons 1 and 2), per series within segment, at least 1 month; >= 20 series to report
    seg = []
    for h in (1, 2):
        for sname, smask in (('quiet', w.segment == 'quiet'), ('after short rise', w.segment == 'after_short_rise'),
                             ('after lasting rise', w.segment == 'after_lasting_rise'), ('surge (outcome-defined)', w.surge)):
            m = pe & (w.h == h) & smask
            pipes = [p for p in PIPES_MAIN if p in w]
            Sg, d = series_scores(w[m], pipes, min_months=1)
            if len(Sg) < 20:
                seg.append(pd.DataFrame({'comparison': f'h{h} {sname}', 'series': [len(Sg)], 'note': ['fewer than 20 series']}))
                continue
            T = avg_rel(Sg, pipes).sort_values('AvgRelMAE')
            T.insert(0, 'comparison', f'h{h} {sname}'); T['series'] = len(Sg); T['rows'] = len(d)
            seg.append(T)
    # representation (organizing) effect holding the model fixed: paired geometric mean of MAE(rep) / MAE(D)
    rep = []
    for cname, mask, pairs in (
            ('A', pe & (w.h == 1), [('ridge_D', 'ridge_DW'), ('catboost_D', 'catboost_DW'), ('lightgbm_D', 'lightgbm_DW'),
                                    ('ridgechg_D', 'ridgechg_DW'), ('ridgechg_D', 'ridgechg_DWS'), ('catchg_D', 'catchg_DW'), ('catchg_D', 'catchg_DWS')]),
            ('E', pe & (w.h == 1) & (w.origin_mi <= gd_end), [('ridge_D', 'ridge_DW'), ('ridge_D', 'ridge_DWG'), ('ridge_D', 'ridge_DWGT'),
                                                               ('catboost_D', 'catboost_DW'), ('catboost_D', 'catboost_DWG'), ('catboost_D', 'catboost_DWGT')])):
        for a, b in pairs:
            if a not in w or b not in w:
                continue
            S, _ = series_scores(w[mask], ['naive', a, b])
            S2 = pd.DataFrame({'naive': S[a], 'x': S[b]})          # ratio of b to a, paired by series
            T = avg_rel(S2, ['x'])
            rep.append(dict(comparison=cname, base=a, with_behavior=b, ratio=T.AvgRelMAE.iloc[0], ci_lo=T.ci_lo.iloc[0],
                            ci_hi=T.ci_hi.iloc[0], share_better=T.share_beats_naive.iloc[0], series=len(S)))
    rep = pd.DataFrame(rep)
    allt = pd.concat(tabs + lev, keys=None)
    allt.to_csv(OUT / 'summary.csv')
    pd.concat(seg).to_csv(OUT / 'segments.csv')
    rep.to_csv(OUT / 'representation.csv', index=False)
    pd.DataFrame(metas).to_csv(OUT / 'meta.csv', index=False)
    for k, S in scores.items():
        S.assign(comparison=k).to_parquet(OUT / f'series_scores_{k[0]}.parquet')
    write_report(tabs, lev, seg, rep, pd.DataFrame(metas), time.time() - t0)


def fmt(T, cols=('AvgRelMAE', 'ci_lo', 'ci_hi', 'median_rel', 'share_beats_naive', 'mean_rank', 'in_MCS')):
    cols = [c for c in cols if c in T]
    h = '| pipeline | ' + ' | '.join(cols) + ' |\n|' + ' --- |' * (len(cols) + 1) + '\n'
    for p, r in T.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            vals.append(('yes' if v else 'no') if isinstance(v, (bool, np.bool_)) else (f'{v:.3f}' if isinstance(v, (float, np.floating)) else str(v)))
        h += f'| {p} | ' + ' | '.join(vals) + ' |\n'
    return h


def write_report(tabs, lev, seg, rep, metas, sec):
    L = ['# Method benchmark, stage 1', '',
         f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/benchmark_settings_2026-10-15.json. Code: code/main_study/benchmark/.',
         'AvgRelMAE is the geometric mean over series of MAE(pipeline) / MAE(naive); below 1 beats the forecast that repeats last month. '
         '95% interval from 2,000 bootstrap resamples of categories. Mean rank: 1 = best within a series. in_MCS: in the 90% model confidence set.', '']
    L.append('## Comparisons'); L.append('')
    L.append(metas.to_csv(index=False, sep='|').replace('|', ' | ')); L.append('')
    for T in tabs + lev:
        L.append(f'### {T.comparison.iloc[0]}'); L.append(''); L.append(fmt(T)); L.append('')
    L.append('## Behavior representation, model held fixed (paired ratio of MAE with behavior features to MAE without)'); L.append('')
    L.append(rep.round(3).to_csv(index=False, sep='|').replace('|', ' | ')); L.append('')
    L.append('## When: segments (print and ebook)'); L.append('')
    for T in seg:
        L.append(f'### {T.comparison.iloc[0]}'); L.append('')
        L.append(fmt(T, ('AvgRelMAE', 'ci_lo', 'ci_hi', 'median_rel', 'share_beats_naive', 'series')) if 'AvgRelMAE' in T else T.to_csv(index=False))
        L.append('')
    L.append(f'Run time {sec/60:.1f} min.')
    REP.write_text('\n'.join(L))
    print(f'wrote {REP}', flush=True)


# ======================================================================================================================================
# Stage 2 (addendum b: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json)
# Scores every pipeline of data/db/benchmark/wide2.parquet with the record's primary metric (AvgRelMAE, 90% model confidence set) and the secondary
# metrics of the addendum: volume-weighted relative MAE, relative RMSE, the cross-theme Spearman of forecast and actual change (the rise task, with its own
# confidence set), surge average precision, plain-number descriptives and the paired comparisons for the organizing question.
#   .venv/bin/python 03_evaluate.py --stage2 [--only A2,B2,C2,D2,E2,S1,A2_no_seasonal] [--nboot N] [--nboot-ap N]      (run under jobs/heavy_lock.sh)
# Stage 1 (python 03_evaluate.py) is unchanged.
# ======================================================================================================================================
import json, argparse, hashlib

ADDENDUM = ST.PREREG / 'addenda_benchmark' / '2026-10-15_b_stage2_metrics_tasks_pipelines.json'
ADDENDUM_SHA = '9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22'
LN13 = float(np.log(1.3))        # surge: actual change >= ln 1.3 (4b definition)
DIR_MIN = 0.10                   # direction accuracy: |actual change| > 0.10 (Study 4 definition)
MIN_GROUP = 10                   # Spearman: at least 10 series in an origin month x format x level group
RES = OUT / 'stage2_results'
REP2 = ST.DATA / 'reports' / 'benchmark_stage2.md'


def block_draws(T, nboot, seed, block=3):
    """Moving-block bootstrap over T months: overlapping blocks of `block` consecutive months, not wrapped, until T months are drawn (as Study 4b)."""
    b = min(block, T)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(nboot, nb))
    return (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(nboot, -1)[:, :T]


def ap_matrix(S, y):
    """Average precision of each column of S against the 0/1 vector y; rows ranked by descending score, ties in input order (the 4b function)."""
    npos = y.sum()
    if npos == 0:
        return np.full(S.shape[1], np.nan)
    o = np.argsort(-S, axis=0, kind='stable')
    yy = y[o]
    tp = np.cumsum(yy, axis=0)
    return ((tp / np.arange(1, len(y) + 1)[:, None]) * yy).sum(axis=0) / npos


def mcs_losses(L, seed=SEED):
    """Model confidence set of the record (size 0.10, stationary bootstrap block 3, range statistic) on a months x pipelines loss frame.
    Pipelines whose loss series are identical (for example a forecast change that is a multiple of another's has the same rank correlation) cannot be told
    apart by the test statistic, which needs a positive variance of the differences: the first of each such group is run and the others take its result."""
    from arch.bootstrap import MCS
    cols = list(L.columns)
    rep, keep = {}, []
    for c in cols:
        for k in keep:
            if np.nanmax(np.abs(L[c].to_numpy() - L[k].to_numpy())) < 1e-10:
                rep[c] = k
                break
        else:
            keep.append(c); rep[c] = c
    m = MCS(L[keep], size=0.10, reps=NBOOT, block_size=3, method='R', bootstrap='stationary', seed=seed)
    m.compute()
    pv = m.pvalues['Pvalue'] if 'Pvalue' in m.pvalues else m.pvalues.iloc[:, 0]
    inc = set(m.included)
    return {c for c in cols if rep[c] in inc}, pd.Series({c: pv.get(rep[c], np.nan) for c in cols})


class Cmp:
    """One comparison: the rows common to all its pipelines, per-series statistics and the month structure; light=True skips the month bootstrap
    and the confidence sets (segments)."""

    def __init__(self, w, mask, pipes, name, min_months=12, nboot=NBOOT, nboot_ap=None, seed=SEED, light=False):
        have = [p for p in pipes if p in w.columns and w.loc[mask, p].notna().mean() > 0.9]
        self.dropped = [p for p in pipes if p not in have]
        d = w[mask].dropna(subset=have + ['y_true', 'y_t'])
        ser = ['group', 'format', 'level', 'node_id']
        n = d.groupby(ser).size()
        d = d.set_index(ser).loc[n[n >= min_months].index].reset_index().reset_index(drop=True)
        self.name, self.pipes, self.d, self.light = name, have, d, light
        self.nboot, self.nboot_ap, self.seed = nboot, (nboot_ap or nboot), seed
        self.ok = len(d) > 0 and 'naive' in have
        if not self.ok:
            return
        y, yt = d.y_true.to_numpy(float), d.y_t.to_numpy(float)
        self.act = y - yt
        self.F = np.column_stack([d[p].to_numpy(float) for p in have])
        self.fc = self.F - yt[:, None]
        self.err = np.abs(self.F - y[:, None])
        sid = d.groupby(ser, sort=False).ngroup().to_numpy()
        ns = int(sid.max()) + 1
        self.keys = d[ser].drop_duplicates().reset_index(drop=True)
        cnt = np.bincount(sid, minlength=ns).astype(float)
        P = len(have)
        self.mae = np.column_stack([np.bincount(sid, weights=self.err[:, j], minlength=ns) / cnt for j in range(P)])
        self.rmse = np.column_stack([np.sqrt(np.bincount(sid, weights=self.err[:, j] ** 2, minlength=ns) / cnt) for j in range(P)])
        self.wts = np.bincount(sid, weights=np.exp(y), minlength=ns) / cnt            # the series' mean borrowing share over its scored months
        self.months = np.array(sorted(d.origin_mi.unique()))
        self.mpos = np.searchsorted(self.months, d.origin_mi.to_numpy())
        self.rows_of_month = [np.where(self.mpos == k)[0] for k in range(len(self.months))]
        _, self.node_code = np.unique(self.keys.node_id.to_numpy(), return_inverse=True)
        self.nn = int(self.node_code.max()) + 1
        self.node_idx = np.random.default_rng(seed).integers(0, self.nn, size=(nboot, self.nn))
        self.D = None if light else block_draws(len(self.months), nboot, seed)
        self.R = self.Rb = self.APd = self.ap_pt = None
        self.series_n, self.rows_n, self.months_n = ns, len(d), len(self.months)

    # ---------------- level task ----------------
    def node_boot(self, logvals, weights=None):
        """exp of the (weighted) mean over series of logvals (series x k), with the 95% interval from resampling categories (nodes)."""
        w = np.ones(len(logvals)) if weights is None else weights
        num = np.zeros((self.nn, logvals.shape[1])); den = np.zeros(self.nn)
        np.add.at(num, self.node_code, logvals * w[:, None]); np.add.at(den, self.node_code, w)
        pt = np.exp(num.sum(axis=0) / den.sum())
        bs = np.empty((self.nboot, logvals.shape[1]))
        for i in range(0, self.nboot, 250):
            ix = self.node_idx[i:i + 250]
            bs[i:i + 250] = num[ix].sum(axis=1) / den[ix].sum(axis=1)[:, None]
        lo, hi = np.exp(np.quantile(bs, [0.025, 0.975], axis=0))
        return pt, lo, hi

    def level_table(self, with_mcs=True):
        i0 = self.pipes.index('naive')
        lr = np.log(self.mae / self.mae[:, [i0]])
        T = pd.DataFrame(index=self.pipes)
        T['AvgRelMAE'], T['ci_lo'], T['ci_hi'] = self.node_boot(lr)
        T['median_rel'] = np.exp(np.median(lr, axis=0))
        T['share_beats_naive'] = (lr < 0).mean(axis=0)
        T['mean_rank'] = stats.rankdata(self.mae, axis=1).mean(axis=0)
        T['VW_AvgRelMAE'], T['vw_lo'], T['vw_hi'] = self.node_boot(lr, self.wts)
        lq = np.log(self.rmse / self.rmse[:, [i0]])
        T['AvgRelRMSE'], T['rmse_lo'], T['rmse_hi'] = self.node_boot(lq)
        if with_mcs and not self.light:
            L = pd.DataFrame({p: (self.d[p] - self.d.y_true).abs() for p in self.pipes}).groupby(self.d.origin_mi.to_numpy()).mean()
            inc, pv = mcs_losses(L)
            T['in_MCS_level'] = [p in inc for p in self.pipes]
            T['MCS_p_level'] = pv.values
        return T

    def friedman(self):
        return friedman_nemenyi(pd.DataFrame(self.mae, columns=self.pipes), self.pipes)

    # ---------------- rise task ----------------
    def rho_months(self):
        """Month x pipeline matrix: mean over the (format, level) groups of the month of the cross-theme Spearman between forecast change and actual change."""
        G = self.d.groupby(['origin_mi', 'format', 'level']).indices
        by = {}
        for (m, f, l), idx in G.items():
            if len(idx) < MIN_GROUP:
                continue
            a = stats.rankdata(self.act[idx]); a = a - a.mean()
            Fm = stats.rankdata(self.fc[idx], axis=0); Fm = Fm - Fm.mean(axis=0)
            den = np.sqrt((a ** 2).sum() * (Fm ** 2).sum(axis=0))
            r = np.full(Fm.shape[1], np.nan); ok = den > 1e-12
            r[ok] = (Fm[:, ok] * a[:, None]).sum(axis=0) / den[ok]
            by.setdefault(m, []).append(r)
        R = np.full((len(self.months), len(self.pipes)), np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            for m, lst in by.items():
                R[np.searchsorted(self.months, m)] = np.nanmean(np.vstack(lst), axis=0)
        self.R = R
        return R

    def rise_table(self, with_mcs=True):
        R = self.rho_months() if self.R is None else self.R
        T = pd.DataFrame(index=self.pipes)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            T['rho'] = np.nanmean(R, axis=0)
            T['rho_share_months_pos'] = np.nanmean(np.where(np.isnan(R), np.nan, R > 0), axis=0)
            if not self.light:
                self.Rb = R[self.D]                                                            # nboot x months x pipelines
                bs = np.nanmean(self.Rb, axis=1)
                T['rho_lo'], T['rho_hi'] = np.nanquantile(bs, [0.025, 0.975], axis=0)
        T.loc[np.isnan(R).all(axis=0), :] = np.nan
        if with_mcs and not self.light:
            good = [j for j in range(len(self.pipes)) if np.isfinite(R[:, j]).sum() >= 0.8 * len(self.months)]
            L = pd.DataFrame(1.0 - R[:, good], columns=[self.pipes[j] for j in good]).dropna(axis=0)
            inc, pv = mcs_losses(L)
            T['in_MCS_rise'] = [(p in inc) if p in L.columns else np.nan for p in self.pipes]
            T['MCS_p_rise'] = [pv.get(p, np.nan) for p in self.pipes]
            T.attrs['rise_months'] = len(L)
        return T

    # ---------------- surge task ----------------
    def surge_table(self, boot=True):
        Y = (self.act >= LN13).astype(float)
        P = len(self.pipes)
        const = np.array([np.nanstd(self.fc[:, j]) < 1e-12 for j in range(P)])
        cols = [j for j in range(P) if not const[j]]
        pt = np.full(P, np.nan)
        if Y.sum() > 0 and cols:
            pt[cols] = ap_matrix(self.fc[:, cols], Y)
        self.ap_pt, self.base_rate = pt, float(Y.mean())
        T = pd.DataFrame(index=self.pipes)
        T['AP'] = pt
        T['AP_lift'] = pt / self.base_rate if self.base_rate > 0 else np.nan
        if boot and not self.light and Y.sum() > 0:
            nb = self.nboot_ap
            D = self.D[:nb]
            APd = np.full((nb, P), np.nan)
            for b in range(nb):
                ri = np.concatenate([self.rows_of_month[k] for k in D[b]])
                APd[b, cols] = ap_matrix(self.fc[np.ix_(ri, cols)], Y[ri])
            self.APd = APd
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                T['AP_lo'], T['AP_hi'] = np.nanquantile(APd, [0.025, 0.975], axis=0)
                best = int(np.nanargmax(pt))
                dd = APd[:, [best]] - APd
                lo90, hi90 = np.nanquantile(dd, [0.05, 0.95], axis=0)
            T['AP_tied_with_best'] = [(bool(l <= 0 <= h) if np.isfinite(l) else np.nan) for l, h in zip(lo90, hi90)]
            T.attrs['best_ap'] = self.pipes[best]
        return T

    # ---------------- plain numbers ----------------
    def plain_table(self):
        P = len(self.pipes)
        Y = self.act >= LN13
        const = np.array([np.nanstd(self.fc[:, j]) < 1e-12 for j in range(P)])
        T = pd.DataFrame(index=self.pipes)
        T['mae_pct'] = self.err.mean(axis=0) * 100
        big = np.abs(self.act) > DIR_MIN
        T['direction_acc'] = (np.sign(self.fc[big]) == np.sign(self.act[big])[:, None]).mean(axis=0)
        hits, flagged = np.zeros(P), 0
        for idx in self.d.groupby(['origin_mi', 'format', 'level']).indices.values():
            if len(idx) < MIN_GROUP:
                continue
            k = int(np.ceil(0.05 * len(idx)))
            order = np.argsort(-self.fc[idx], axis=0, kind='stable')[:k]
            hits += Y[idx][order].sum(axis=0); flagged += k
        T['precision_top5pct'] = hits / max(flagged, 1)
        T.loc[const, ['direction_acc', 'precision_top5pct']] = np.nan
        T.attrs['move_rows'] = int(big.sum()); T.attrs['surge_base_rate'] = float(Y.mean())
        return T

    # ---------------- paired comparisons (model held fixed) ----------------
    def pair(self, a, b):
        ia, ib = self.pipes.index(a), self.pipes.index(b)
        lr = np.log(self.mae[:, [ib]] / self.mae[:, [ia]])
        pt, lo, hi = self.node_boot(lr)
        out = dict(base=a, other=b, mae_ratio=float(pt[0]), mae_lo=float(lo[0]), mae_hi=float(hi[0]), share_series_better=float((lr < 0).mean()), series=self.series_n)
        if self.R is not None and self.Rb is not None:
            d = self.R[:, ib] - self.R[:, ia]
            out['rho_diff'] = float(np.nanmean(d)) if np.isfinite(d).any() else np.nan
            if np.isfinite(d).any():
                bs = np.nanmean(self.Rb[:, :, ib] - self.Rb[:, :, ia], axis=1)
                out['rho_diff_lo'], out['rho_diff_hi'] = [float(x) for x in np.nanquantile(bs, [0.025, 0.975])]
        if self.APd is not None and self.ap_pt is not None and np.isfinite(self.ap_pt[ia]) and np.isfinite(self.ap_pt[ib]):
            dd = self.APd[:, ib] - self.APd[:, ia]
            out['ap_diff'] = float(self.ap_pt[ib] - self.ap_pt[ia])
            out['ap_diff_lo'], out['ap_diff_hi'] = [float(x) for x in np.nanquantile(dd, [0.025, 0.975])]
        return out

    def meta(self):
        return dict(name=self.name, rows=self.rows_n, series=self.series_n, months=self.months_n, pipelines=len(self.pipes), dropped=';'.join(self.dropped),
                    surge_base_rate=float((self.act >= LN13).mean()))


def full_table(c, boot_ap=True, with_mcs=True):
    T = c.level_table(with_mcs=with_mcs)
    for part in (c.rise_table(with_mcs=with_mcs), c.surge_table(boot=boot_ap), c.plain_table()):
        T = T.join(part)
    return T


def segment_tables(w, h, pipes, nboot):
    rows = []
    pe = (w.group == 'seattle') & w.format.isin(['print', 'ebook']) & (w.h == h)
    for sname, smask in (('quiet', w.segment == 'quiet'), ('after short rise', w.segment == 'after_short_rise'),
                         ('after lasting rise', w.segment == 'after_lasting_rise'), ('surge months (outcome-defined)', w.surge)):
        c = Cmp(w, pe & smask, pipes, f'h{h} {sname}', min_months=1, nboot=nboot, light=True)
        if not c.ok or c.series_n < 20:
            rows.append(pd.DataFrame({'segment': [f'h{h} {sname}'], 'note': [f'fewer than 20 series ({c.series_n if c.ok else 0})']}))
            continue
        T = c.level_table(with_mcs=False)
        if 'surge' not in sname:
            T = T.join(c.rise_table(with_mcs=False)).join(c.surge_table(boot=False))
        T.insert(0, 'segment', f'h{h} {sname}'); T['series'] = c.series_n; T['rows'] = c.rows_n
        rows.append(T)
    return rows


def organizing_pairs(pipes):
    P = []
    for m in ('ridgechg', 'lgbmchg', 'catchg'):
        for fs in ('DVcur', 'DW', 'DWS', 'DVtop', 'DVnli', 'DVbk', 'DVcurdw', 'DVdem'):
            P.append((f'{m}_D', f'{m}_{fs}', 'behavior against no behavior'))
        for fs in ('DVtop', 'DVnli', 'DVbk', 'DVcurdw', 'DVdem'):
            P.append((f'{m}_DVcur', f'{m}_{fs}', 'routing or representation against curated volume'))
    for v in ('chronos2_cur', 'chronos2_curdw', 'chronos2_bk', 'chronos2_nli', 'chronos2_top'):
        P.append(('chronos2', v, 'behavior against no behavior'))
    for v in ('chronos2_curdw', 'chronos2_bk', 'chronos2_nli', 'chronos2_top'):
        P.append(('chronos2_cur', v, 'routing or representation against curated volume'))
    P.append(('median_s2_demand', 'median_s2_behavior', 'combination: behavior against no behavior'))
    return [(a, b, k) for a, b, k in P if a in pipes and b in pipes]


def roster():
    A = json.loads(ADDENDUM.read_text())
    r = A['roster_A2']
    return list(r['stage1_21']), list(r['stage1_21']) + list(r['stage2_new']), A


def run_stage2(only=None, nboot=NBOOT, nboot_ap=None):
    got = hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()
    if got != ADDENDUM_SHA:
        raise SystemExit(f'stage-2 addendum changed ({got}); nothing is scored')
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    w = pd.read_parquet(OUT / 'wide2.parquet')
    stage1, ROSTER, _ = roster()
    extra = [c for c in w.columns if c.endswith('_DVdem')]
    ROSTER = ROSTER + [c for c in extra if c not in ROSTER]
    lib = [p for p in ROSTER if 'chg' not in p and p in ('naive', 'seasonal_naive', 'ridge_D', 'ridge_DW', 'catboost_D', 'catboost_DW', 'lightgbm_D', 'lightgbm_DW', 'chronos',
                                                            'chronos2', 'chronos2_cur', 'avg_ridge_cat_D', 'avg_ridge_cat_DW', 'avg_three_DW', 'avg_naive_ridge_D', 'median_all',
                                                            'invmae_all', 'revert6')]
    sea = w.group == 'seattle'
    pe = sea & w.format.isin(['print', 'ebook'])
    specs = {
        'A2': (pe & (w.h == 1), ROSTER), 'A2_no_seasonal': (pe & (w.h == 1), [p for p in ROSTER if p != 'seasonal_naive']),
        'B2': (pe & (w.h == 2), ROSTER), 'C2': (pe & (w.h == 3), ROSTER),
        'D2_h1': (sea & (w.format == 'audiobook') & (w.h == 1), ROSTER), 'D2_h2': (sea & (w.format == 'audiobook') & (w.h == 2), ROSTER),
        'D2_h3': (sea & (w.format == 'audiobook') & (w.h == 3), ROSTER),
        'E2_h1': ((w.group == 'librivox') & (w.h == 1), lib), 'E2_h2': ((w.group == 'librivox') & (w.h == 2), lib),
        'S1_h1': (pe & (w.h == 1), stage1), 'S1_h2': (pe & (w.h == 2), stage1),
    }
    want = [k for k in specs if only is None or k.split('_')[0] in only or k in only]
    metas, tables, pairs_all, fried = [], {}, [], {}
    for k in want:
        mask, pipes = specs[k]
        c = Cmp(w, mask, pipes, k, nboot=nboot, nboot_ap=nboot_ap)
        if not c.ok:
            print(f'{k}: no common rows or no naive column, skipped', flush=True); continue
        print(f'{time.strftime("%H:%M:%S")} {k}: {c.rows_n} rows, {c.series_n} series, {c.months_n} months, {len(c.pipes)} pipelines'
              + (f' (not available: {c.dropped})' if c.dropped else ''), flush=True)
        T = full_table(c, boot_ap=not k.startswith('A2_no'), with_mcs=True)
        T.to_csv(RES / f'{k}_table.csv')
        tables[k] = T
        if k == 'A2':                                              # H2: the leaders by format and level, descriptive (point estimates and node intervals)
            def isT(v):
                return isinstance(v, (bool, np.bool_)) and bool(v)
            lead = [p for p in T.index if p == 'naive' or isT(T.loc[p, 'in_MCS_level']) or isT(T.loc[p, 'in_MCS_rise'])]
            rows = []
            for fmt in ('print', 'ebook'):
                for lev in ('narrow', 'middle'):
                    c2 = Cmp(w, pe & (w.format == fmt) & (w.level == lev) & (w.h == 1), lead, f'A2 {fmt} {lev}', nboot=nboot, light=True)
                    if c2.ok:
                        t2 = c2.level_table(with_mcs=False).join(c2.rise_table(with_mcs=False))
                        t2.insert(0, 'format', fmt); t2.insert(1, 'level', lev); t2['series'] = c2.series_n; rows.append(t2)
            if rows:
                pd.concat(rows).to_csv(RES / 'H2_table.csv')
            yr = []                                                  # H3: the leaders by calendar year of the origin (stability over time), descriptive
            for y in range(2019, 2027):
                lo, hi = ST.mi_from_ym(f'{y}-01'), ST.mi_from_ym(f'{y}-12')
                c3 = Cmp(w, pe & (w.h == 1) & (w.origin_mi >= lo) & (w.origin_mi <= hi), lead, f'A2 {y}', min_months=3, nboot=nboot, light=True)
                if c3.ok:
                    t3 = c3.level_table(with_mcs=False).join(c3.rise_table(with_mcs=False))
                    t3.insert(0, 'year', y); t3['series'] = c3.series_n; t3['months'] = c3.months_n; yr.append(t3)
            if yr:
                pd.concat(yr).to_csv(RES / 'H3_by_year.csv')
        m = c.meta(); m.update(c.friedman()); m['rise_months_mcs'] = T.attrs.get('rise_months', np.nan); m['best_ap'] = T.attrs.get('best_ap', ''); metas.append(m)
        if k in ('A2', 'B2', 'C2', 'D2_h1', 'S1_h1'):
            pr = [dict(comparison=k, kind=kind, **c.pair(a, b)) for a, b, kind in organizing_pairs(c.pipes)]
            if pr:
                pd.DataFrame(pr).to_csv(RES / f'{k}_pairs.csv', index=False); pairs_all += pr
        print(f'{time.strftime("%H:%M:%S")} {k} done ({(time.time() - t0) / 60:.1f} min)', flush=True)
    pd.DataFrame(metas).to_csv(RES / 'meta.csv', index=False)
    if only is None or 'A2' in only or 'G2' in only:
        seg = []
        for h in (1, 2, 3):
            pipes = [p for p in ROSTER if p in w.columns]
            seg += segment_tables(w, h, pipes, nboot)
        pd.concat(seg).to_csv(RES / 'segments.csv')
        print(f'{time.strftime("%H:%M:%S")} segments done ({(time.time() - t0) / 60:.1f} min)', flush=True)
    print(f'{time.strftime("%H:%M:%S")} stage-2 scoring finished: {(time.time() - t0) / 60:.1f} min; results in {RES}', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage2', action='store_true')
    ap.add_argument('--only', default=None)
    ap.add_argument('--nboot', type=int, default=NBOOT)
    ap.add_argument('--nboot-ap', type=int, default=None)
    a = ap.parse_args()
    if a.stage2:
        run_stage2(set(a.only.split(',')) if a.only else None, a.nboot, a.nboot_ap)
    else:
        main()
