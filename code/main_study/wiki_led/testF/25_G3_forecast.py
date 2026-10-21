#!/usr/bin/env python3
"""Test F, step 25, check G3 (and the ranking part of G4): Chronos-2 with the AI theme series as input, and a Wikipedia-only ranking.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (tests.G3_forecasting, tests.G4_books_side).
Rows: the benchmark's main rows (data/db/benchmark/wide2.parquet: Seattle, print and ebook, horizon 1, every one of the 52 pipelines
present, series with at least 12 such months: 36,081 forecasts, 510 series), rebuilt as in paper/progress_map/prep_stages.py.
Phase chronos: the benchmark's Chronos-2 runner (benchmark/09_chronos2.py: same model and revision, context = the series' monthly log share
up to the origin, past covariates only, median forecast, 3 threads) with two new variants, chronos2_ais2 (covariate ais2_wlog, the S2
monthly series of step 21) and chronos2_ais1 (ais1_wlog, S1). Only the main rows' series and origins are forecast. The variants' parts and
forecasts go to <Test F folder>/chronos2_out/, never into the benchmark's folders.
Phase evaluate: the benchmark's scoring class (benchmark/03_evaluate.py, Cmp: AvgRelMAE with the category bootstrap, 2,000 draws, seed
20261015; the rank correlation of forecast and actual change within month x format x level groups of at least 10, with the moving-block
bootstrap of months; paired differences with the same draws) on naive, chronos2, chronos2_cur (concept pages), chronos2_nli (zero-shot
routing) and the two new variants. Decision: Chronos-2 + S2 against Chronos-2 alone, paired ratio of MAE with its interval below 1
(the difference below 0).
Wikipedia-only ranking (no fitting): for each row, the theme's monthly log change of the series at the origin (x(t) = m(t) - m(t-1)),
ranked against the actual change of borrowing c(t) = y(t+1) - y(t) within origin x format x level groups of at least 10 rows: the Test C
measure of code/main_study/wiki_led/20c_test_c.py (Spearman per group, mean over groups, 2,000 draws of 3-month blocks, seed 20261020; a
row without a value of x gets 0, as there). Shown for S2, S1 and, for comparison, the stored concept-page, zero-shot and embedding series
(benchmark/stage2/monthly_cov.parquet: cur_wlog, nli_wlog, top_wlog); paired differences with the same draws.
G4: the same ranking on panels a, b and c (23_panels.py) for the main rows' keys where all three panels have the change, so that b and c
differ only in who sorted the books.
In a mock world the borrowing history and targets are shuffled across themes and months before use (_testf_analysis.shuffle_history),
the stored forecasts are left as they are (so they forecast nothing real), and --mock-fill fills a variant that was not run with Chronos-2
plus noise.
Outputs: chronos2_out/chronos2_<variant>_forecasts.parquet, g3_chronos_timing.json, g3_level_rise.csv, g3_pairs.csv, g3_wikionly.csv,
g4_wikionly.csv, g3_summary.json; report testF_25_G3.md.
Run from handoff/ (the Chronos phase is heavy; about 6 minutes per variant on this Mac, measured in the mock test):
  bash jobs/bg.sh testF_g3 main_study/benchmark/_locked.py ../wiki_led/testF/25_G3_forecast.py --phase chronos
  then from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/25_G3_forecast.py --phase evaluate
"""
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, json, shutil, pathlib, argparse, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import _testf_analysis as T

BENCH = T.MAIN / 'benchmark'
WIDE2 = T.D / 'db' / 'benchmark' / 'wide2.parquet'
A2 = T.D / 'db' / 'benchmark' / 'stage2_results' / 'A2_table.csv'
MCOV = T.D / 'db' / 'benchmark' / 'stage2' / 'monthly_cov.parquet'
NEW = {'chronos2_ais2': 'ais2_wlog', 'chronos2_ais1': 'ais1_wlog'}
NEW_H = {'chronos2_aic2': 'aic2_wlog'}                          # addendum h (concept pages); scored by 29_H_concept.py, not by phase evaluate
SEED_C = 20261020                                               # the Test C measure's seed (20c_test_c.py)
NB = 2000


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main_rows():
    """The 36,081 main rows of the benchmark (as paper/progress_map/prep_stages.py)."""
    import csv
    pipes = [r[''] for r in csv.DictReader(open(A2))]
    wd = pd.read_parquet(WIDE2)
    s = wd[(wd.group == 'seattle') & (wd.format.isin(['print', 'ebook'])) & (wd.h == 1)].dropna(subset=['y_true'] + pipes).copy()
    s = s[s.groupby(['format', 'level', 'node_id']).origin_mi.transform('size') >= 12]
    assert len(s) == 36081 and s.groupby(['format', 'level', 'node_id']).ngroups == 510, 'the main rows are not the benchmark main rows'
    keep = ['group', 'format', 'level', 'node_id', 'origin_mi', 'h', 'y_true', 'y_t', 'naive', 'chronos2', 'chronos2_cur', 'chronos2_nli']
    return s[keep].reset_index(drop=True)


def covariates(P, s2_ok):
    M = pd.read_parquet(P / 'series_monthly.parquet')
    covs = {}
    for v, c in {**NEW, **NEW_H}.items():
        if c in M:
            covs[c] = {n: g.set_index('mi')[c] for n, g in M[['node_id', 'mi', c]].dropna(subset=[c]).groupby('node_id')}
    return covs


# ---------------------------------------------------------------- phase chronos
def phase_chronos(P, a):
    import torch
    CH = load_module('bm09', BENCH / '09_chronos2.py')
    C = CH.C
    C.check_addendum()
    base = C.base_rows()                                          # read before C.OUT is redirected (it caches in the benchmark folder)
    hist = C.history()
    if P.mock:
        hist = T.shuffle_history(hist, P.mock_seed + 11)
    keys = main_rows()[['group', 'format', 'level', 'node_id', 'origin_mi', 'h']]
    bm = base.merge(keys, on=C.K, how='inner')
    assert len(bm) == 36081, f'{len(bm)} base rows match the main rows'
    covs = covariates(P, True)
    out = P / 'chronos2_out'
    out.mkdir(exist_ok=True)
    C.OUT = out                                                   # parts and forecasts of the new variants go to the Test F folder
    for v, c in {**NEW, **NEW_H}.items():
        CH.VARIANTS[v] = [c]
    torch.set_num_threads(3)
    torch.manual_seed(C.SEED)
    CH.patch_loader()
    from chronos import Chronos2Pipeline
    pipe = Chronos2Pipeline.from_pretrained(CH.MODEL, device_map='cpu', dtype=torch.float32, revision=CH.REVISION)
    timing = json.loads((P / 'g3_chronos_timing.json').read_text()) if (P / 'g3_chronos_timing.json').exists() else {}
    for v in a.variants.split(','):
        v = v if v.startswith('chronos2_') else f'chronos2_{v}'
        cov = {**NEW, **NEW_H}[v]
        if cov not in covs:
            raise SystemExit(f'{v}: the covariate {cov} is not in series_monthly.parquet (run 21_series.py)')
        if a.limit:
            shutil.rmtree(out / 'chronos2_parts_test' / v, ignore_errors=True)
        t0 = time.time()
        CH.run_variant(v, pipe, bm, hist, covs, a.limit)
        el = time.time() - t0
        n = a.limit or 36081
        timing[v + ('_limited' if a.limit else '')] = dict(tasks=n, seconds=round(el, 1), tasks_per_s=round(n / el, 1),
                                                          full_run_estimate_min=round(36081 / (n / el) / 60, 1), mock=P.mock, when=time.strftime('%Y-%m-%d %H:%M'))
        T.log(f'{v}: {n:,} tasks in {el:.0f}s ({n / el:.0f} a second); full run about {36081 / (n / el) / 60:.1f} min')
    T.write_json(timing, P / 'g3_chronos_timing.json')


# ---------------------------------------------------------------- the Test C measure (20c_test_c.py, scoring block)
def block_draws_c(n_months, seed=SEED_C, nboot=NB):
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n_months / 3))
    return np.array([np.concatenate([np.arange(a_, a_ + 3) % n_months for a_ in rng.choice(n_months, nb)])[:n_months] for _ in range(nboot)])


def test_c_scores(s, xcols, ccol='c'):
    """Spearman within origin x format x level groups (>= 10 rows; 0 when x is constant), mean over groups, month-block intervals, and
    the per-draw values for paired differences."""
    grp = s.groupby(['origin_mi', 'format', 'level'])
    keys = [k for k, g in grp if len(g) >= 10]
    months = np.sort(s.origin_mi.unique())
    BD = block_draws_c(len(months))
    out, draws = {}, {}
    for x in xcols:
        vals = []
        for k in keys:
            g = grp.get_group(k)
            xv = g[x]
            vals.append((k[0], spearmanr(xv, g[ccol]).statistic if xv.nunique() > 1 else 0.0))
        v = pd.DataFrame(vals, columns=['m', 'r'])
        per_m = v.groupby('m').r.agg(['sum', 'count']).reindex(months).fillna(0)
        S_, C_ = per_m['sum'].to_numpy(), per_m['count'].to_numpy()
        boots = np.array([S_[b].sum() / C_[b].sum() for b in BD])
        draws[x] = boots
        out[x] = dict(rho=float(v.r.mean()), lo=float(np.percentile(boots, 2.5)), hi=float(np.percentile(boots, 97.5)), groups=len(v),
                      rows_with_value=float((s[x] != 0).mean()))
    return out, draws


def paired(draws, pt, a_, b_):
    d = draws[b_] - draws[a_]
    return dict(base=a_, other=b_, diff=pt[b_]['rho'] - pt[a_]['rho'], lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)))


def changes(M, col):
    """Monthly log change x(t) = m(t) - m(t-1) of a node series, long (node_id, origin_mi, x)."""
    W = M.pivot_table(index='mi', columns='node_id', values=col)
    W = W.reindex(np.arange(int(W.index.min()), int(W.index.max()) + 1))
    X = W.diff().stack(future_stack=True).rename('x').reset_index()
    X.columns = ['origin_mi', 'node_id', 'x']
    return X.dropna()


def attach_x(s, X, name):
    s = s.merge(X.rename(columns={'x': name}), on=['node_id', 'origin_mi'], how='left')
    s[name] = s[name].fillna(0.0)
    return s


def panel_changes(P, name, mock_seed):
    if name == 'a':
        p = pd.read_parquet(T.D / 'db' / 'study3' / 'demand_panel.parquet', columns=['level', 'node_id', 'format', 'mi', 'month_ok', 'log_share', 'weighted_checkouts', 'share'])
        if mock_seed is not None:
            p = T.shuffle_panel(p, mock_seed + 3)
    else:
        p = pd.read_parquet(P / f'panel_{name}.parquet', columns=['level', 'node_id', 'format', 'mi', 'month_ok', 'log_share'])
    p = p[p.format.isin(['print', 'ebook']) & p.level.isin(['middle', 'narrow'])].copy()
    p.loc[~p.month_ok.astype(bool), 'log_share'] = np.nan
    Y = p.pivot_table(index=['format', 'level', 'node_id'], columns='mi', values='log_share')
    Y = Y.reindex(columns=np.arange(int(Y.columns.min()), int(Y.columns.max()) + 1))
    CY = (Y.shift(-1, axis=1) - Y).stack(future_stack=True).rename(f'c_{name}').reset_index()
    CY.columns = ['format', 'level', 'node_id', 'origin_mi', f'c_{name}']
    return CY.dropna()


# ---------------------------------------------------------------- phase evaluate
def phase_evaluate(P, a):
    t0 = time.time()
    T.mock_only(P, a.mock_fill, '--mock-fill')
    EV = load_module('bm03', BENCH / '03_evaluate.py')
    s = main_rows()
    if P.mock:                                                    # targets from the shuffled history (the same shuffle as phase chronos)
        C = load_module('bm_s2c', BENCH / '_stage2_common.py')
        H = T.shuffle_history(C.history(), P.mock_seed + 11)
        key = list(zip(s.group, s.format, s.level, s.node_id))
        s['y_t'] = [H[k].get(o, np.nan) for k, o in zip(key, s.origin_mi)]
        s['y_true'] = [H[k].get(o + 1, np.nan) for k, o in zip(key, s.origin_mi)]
        s['naive'] = s.y_t
    for v in NEW:
        f = P / 'chronos2_out' / f'{v}_forecasts.parquet'
        if f.exists():
            F = pd.read_parquet(f)
            F = F[F.h == 1][['group', 'format', 'level', 'node_id', 'origin_mi', 'y_hat']].rename(columns={'y_hat': v})
            s = s.merge(F, on=['group', 'format', 'level', 'node_id', 'origin_mi'], how='left')
        else:
            s[v] = np.nan
        if s[v].isna().any():
            if P.mock and a.mock_fill:
                rng = np.random.default_rng(P.mock_seed + (21 if v.endswith('2') else 22))
                fill = s.chronos2 + rng.normal(0, 0.02, len(s))
                s[v] = s[v].fillna(fill)
            else:
                raise SystemExit(f'{v}: {int(s[v].isna().sum()):,} of {len(s):,} main rows have no forecast (run --phase chronos)')
    pipes = ['naive', 'chronos2', 'chronos2_cur', 'chronos2_nli', 'chronos2_ais2', 'chronos2_ais1']
    c = EV.Cmp(s, pd.Series(True, index=s.index), pipes, 'G3', nboot=EV.NBOOT)
    if c.dropped or (not P.mock and c.rows_n != 36081):
        raise SystemExit(f'the scoring class dropped pipelines or rows: {c.dropped}, {c.rows_n} rows')
    LT = c.level_table(with_mcs=False).join(c.rise_table(with_mcs=False))
    LT.index.name = 'pipeline'
    LT.to_csv(P / 'g3_level_rise.csv')
    pairs = [('chronos2', 'chronos2_ais2'), ('chronos2', 'chronos2_ais1'), ('chronos2_cur', 'chronos2_ais2'), ('chronos2_nli', 'chronos2_ais2'),
             ('chronos2_cur', 'chronos2_ais1'), ('chronos2_nli', 'chronos2_ais1'), ('chronos2_ais1', 'chronos2_ais2'), ('chronos2', 'chronos2_cur'),
             ('chronos2', 'chronos2_nli')]
    PR = pd.DataFrame([c.pair(x, y) for x, y in pairs])
    PR.to_csv(P / 'g3_pairs.csv', index=False)
    dec = PR[(PR.base == 'chronos2') & (PR.other == 'chronos2_ais2')].iloc[0]
    # Wikipedia-only ranking on the main rows
    s['c'] = s.y_true - s.y_t
    M = pd.read_parquet(P / 'series_monthly.parquet')
    MC = pd.read_parquet(MCOV)
    xs = {}
    for name, (frame, col) in {'S2 (AI pages)': (M, 'ais2_wlog'), 'S1 (AI pages, top-500 days)': (M, 'ais1_wlog'),
                               'concept pages': (MC, 'cur_wlog'), 'zero-shot routing': (MC, 'nli_wlog'), 'embedding routing': (MC, 'top_wlog')}.items():
        if col in frame:
            xn = 'x_' + col
            s = attach_x(s, changes(frame, col), xn)
            xs[name] = xn
    W3, D3 = test_c_scores(s, list(xs.values()))
    WO = pd.DataFrame([dict(series=k, **W3[v]) for k, v in xs.items()])
    WO.to_csv(P / 'g3_wikionly.csv', index=False)
    wpairs = [paired(D3, W3, xs[b_], xs[a_]) | dict(base=b_, other=a_) for a_, b_ in
              (('S2 (AI pages)', 'concept pages'), ('S2 (AI pages)', 'zero-shot routing'), ('S2 (AI pages)', 'embedding routing'),
               ('S2 (AI pages)', 'S1 (AI pages, top-500 days)')) if a_ in xs and b_ in xs]
    # G4: panels a, b, c on common keys
    ck = s[['format', 'level', 'node_id', 'origin_mi'] + [v for v in xs.values() if 'ais' in v]].copy()
    for nm in ('a', 'b', 'c'):
        ck = ck.merge(panel_changes(P, nm, P.mock_seed if P.mock else None), on=['format', 'level', 'node_id', 'origin_mi'], how='inner')
    g4, g4p = [], []
    for xname, xcol in ((k, v) for k, v in xs.items() if 'ais' in v):
        res = {}
        for nm in ('a', 'b', 'c'):
            sc, dr = test_c_scores(ck.assign(c=ck[f'c_{nm}']), [xcol])
            res[nm] = (sc[xcol], dr[xcol])
            g4.append(dict(series=xname, panel=nm, rows=len(ck), **sc[xcol]))
        for x_, y_ in (('c', 'b'), ('a', 'b'), ('a', 'c')):
            d = res[y_][1] - res[x_][1]
            g4p.append(dict(series=xname, base=f'panel {x_}', other=f'panel {y_}', diff=res[y_][0]['rho'] - res[x_][0]['rho'],
                            lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5))))
    G4 = pd.DataFrame(g4)
    G4.to_csv(P / 'g4_wikionly.csv', index=False)
    summ = dict(mock=P.mock, mock_fill=bool(a.mock_fill), rows=c.rows_n, series=c.series_n, months=c.months_n, nboot=EV.NBOOT,
                decision_G3=dict(base='chronos2', other='chronos2_ais2', mae_ratio=float(dec.mae_ratio), lo=float(dec.mae_lo), hi=float(dec.mae_hi),
                                 interval_below_1=bool(dec.mae_hi < 1)),
                wikionly_pairs=wpairs, g4_pairs=g4p, g4_rows=len(ck), seconds=round(time.time() - t0), peak_gb=round(T.peak_gb(), 2))
    timing = P / 'g3_chronos_timing.json'
    summ['chronos_timing'] = json.loads(timing.read_text()) if timing.exists() else None
    T.write_json(summ, P / 'g3_summary.json')
    write_report(P, LT, PR, WO, wpairs, G4, g4p, summ)
    T.log(f'evaluate done in {summ["seconds"]}s; peak memory {summ["peak_gb"]} GB')


def write_report(P, LT, PR, WO, wpairs, G4, g4p, summ):
    d = summ['decision_G3']
    L = [f'# Test F, check G3: forecasts with the AI theme series ({P.tag()})', '',
         f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; main rows {summ["rows"]:,} ({summ["series"]} series, {summ["months"]} months); bootstrap {summ["nboot"]} draws']
    if P.mock:
        L += ['', '**MOCK WORLD: borrowing shuffled across themes and months' + (', new forecasts filled with noise' if summ['mock_fill'] else '') +
              '; these numbers mean nothing about real borrowing.**']
    L += ['', '## Decision', f'- Chronos-2 + S2 against Chronos-2 alone: MAE ratio {d["mae_ratio"]:.4f} [{d["lo"]:.4f}, {d["hi"]:.4f}] '
          f'({100 * (d["mae_ratio"] - 1):+.2f}%); interval below 1: {"yes" if d["interval_below_1"] else "no"}', '',
          '## Accuracy and rank correlation (AvgRelMAE against naive with the category bootstrap; rho of forecast and actual change)', '']
    L += T.md_table(LT.reset_index()[['pipeline', 'AvgRelMAE', 'ci_lo', 'ci_hi', 'share_beats_naive', 'rho', 'rho_lo', 'rho_hi']], '{:.4f}')
    L += ['', '## Paired comparisons (MAE ratio other / base by series; rho difference)', '']
    L += T.md_table(PR[[c for c in ['base', 'other', 'mae_ratio', 'mae_lo', 'mae_hi', 'share_series_better', 'rho_diff', 'rho_diff_lo', 'rho_diff_hi'] if c in PR]], '{:.4f}')
    L += ['', '## Wikipedia-only ranking, no fitting (the Test C measure)', ''] + T.md_table(WO, '{:.4f}')
    L += ['', 'Paired differences (other minus base):'] + [f'- {p["other"]} minus {p["base"]}: {p["diff"]:+.4f} [{p["lo"]:+.4f}, {p["hi"]:+.4f}]' for p in wpairs]
    L += ['', f'## G4: the same ranking on panels a, b, c ({summ["g4_rows"]:,} common rows)', ''] + T.md_table(G4, '{:.4f}')
    L += ['', 'Paired differences:'] + [f'- {p["series"]}: {p["other"]} minus {p["base"]}: {p["diff"]:+.4f} [{p["lo"]:+.4f}, {p["hi"]:+.4f}]' for p in g4p]
    if summ.get('chronos_timing'):
        L += ['', '## Chronos-2 run time on this Mac', ''] + [f'- {k}: {v}' for k, v in summ['chronos_timing'].items()]
    T.write_text('\n'.join(L) + '\n', P.report('testF_25_G3.md'))


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--phase', choices=['chronos', 'evaluate', 'all'], default='all')
    ap.add_argument('--variants', default='ais2,ais1')
    ap.add_argument('--limit', type=int, default=None, help='first N tasks only (timing); no forecast file is written')
    ap.add_argument('--mock-fill', action='store_true')
    a = ap.parse_args()
    P = T.Paths(a.root)
    T.be_nice(10)
    T.log(f'{P.tag()}; phase {a.phase}')
    if a.phase in ('chronos', 'all'):
        phase_chronos(P, a)
    if a.phase in ('evaluate', 'all'):
        phase_evaluate(P, a)
    T.log(f'peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
