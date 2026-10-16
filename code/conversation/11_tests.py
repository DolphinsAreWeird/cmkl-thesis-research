# Conversation sources, step 11: H1 and H2 per source, narrow and middle. Refuses to run unless the positive-control section
# is already in the report (step 10). Study 3b count model and placebo ranking per rise; pooled tau by duration class; bootstrap
# clustered by theme (2,000 resamples, seed 20261014). Appends section 2 to data/reports/conversation_sources_results.md.
# Run: bash jobs/heavy_lock.sh nice -n 10 .venv/bin/python code/conversation/11_tests.py
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import conv_common as C
from conv_common import S, B3, INF, IO, M

MIN_RISES = 5


def fmt(x, d=3):
    return '' if x is None or (isinstance(x, float) and not np.isfinite(x)) else f'{x:.{d}f}'


def contributing(R):
    ok = R[(R.skip == '') & ~R.too_sparse.fillna(False).astype(bool)].replace([np.inf, -np.inf], np.nan)
    return ok[ok.tau_p.notna()]


def boot_diff(sus, fad, n, seed):
    """Mean tau of sustained minus mean tau of fading, resampling themes. sus, fad: DataFrames with node_id, tau_p."""
    nodes = np.array(sorted(set(sus.node_id) | set(fad.node_id)))
    G = len(nodes)
    idx = {k: i for i, k in enumerate(nodes)}

    def agg(d):
        c = d.node_id.map(idx).to_numpy()
        return np.bincount(c, weights=d.tau_p.to_numpy(float), minlength=G), np.bincount(c, minlength=G).astype(float)

    ss, ns = agg(sus); sf, nf = agg(fad)
    out = dict(diff=float(sus.tau_p.mean() - fad.tau_p.mean()), clusters=G)
    if G < 2:
        return out | dict(low=np.nan, high=np.nan, dropped=n, n_valid=0)
    pick = np.random.default_rng(seed).integers(0, G, size=(n, G))
    a, b = ns[pick].sum(1), nf[pick].sum(1)
    ok = (a > 0) & (b > 0)
    d = ss[pick].sum(1)[ok] / a[ok] - sf[pick].sum(1)[ok] / b[ok]
    out['n_valid'], out['dropped'] = int(ok.sum()), int((~ok).sum())
    out['low'], out['high'] = M.percentile_ci(d, 0.95) if len(d) > 1 else (np.nan, np.nan)
    return out


def verdict(n, low, label='above 0'):
    if n < MIN_RISES:
        return 'too few rises, no verdict'
    return 'interval above 0: SUPPORTED' if (low is not None and np.isfinite(low) and low > 0) else 'interval does not exclude 0: NOT SUPPORTED'


def main():
    t0 = time.time()
    if not C.REPORT.exists() or '## 1. Positive controls' not in C.REPORT.read_text():
        raise SystemExit('refuses to run: the positive-control section (step 10) is not in the report yet')
    P, meta, world = C.make_world()
    allres = []
    for src in C.SOURCES:
        X = C.conv_shifts(src)
        T = C.tested_set(X, src)
        units = T.groupby(['level', 'm0']).node_id.apply(lambda x: sorted(set(x))).reset_index()
        recs = []
        for u in units.itertuples():
            tab = world.ztable('seattle', u.level, int(u.m0))
            for n in u.node_id:
                if n in world.C[('seattle', u.level)].index:
                    recs.append(INF.test_unit(world, 'seattle', u.level, n, int(u.m0), tab))
                else:
                    recs.append(dict(level=u.level, node_id=n, m0=int(u.m0), skip='no counts'))
        Tt = pd.DataFrame(recs).drop(columns=['broad_id', 'label', 'parent', 'month0'], errors='ignore')
        R = T[['shift_id', 'source', 'level', 'node_id', 'start_week', 'm0', 'duration_class', 'size']].merge(Tt, on=['level', 'node_id', 'm0'], how='left')
        for c in ('too_sparse', 'y_zero'):
            R[c] = R[c].fillna(False).astype(bool) if c in R else False
        R['source'] = src
        allres.append(R)
        print(src, len(T), 'rises tested set;', int((R.skip == '').sum()), 'tests ok', flush=True)
    R = pd.concat(allres, ignore_index=True)
    R.drop(columns=[c for c in R if c.startswith('py_years')]).to_parquet(C.OUTDIR / 'shift_effects.parquet')

    L = ['', '## 2. Tested rises', '',
         'Narrow and middle levels, sustained, intermediate or fading, not seasonal, not within 2 weeks of a TweetsKB linker break, month 0 from 2016-01 to 2020-09 (TweetsKB) or 2026-03 (talk edits). '
         '"Pooled" = tested, at least 5 expected checkouts in months 0 to +2 (not too sparse) and tau defined. The verdict rule: a class with fewer than 5 pooled rises gets no verdict.', '']
    cnt = []
    for (s, lv, cl), g in R.groupby(['source', 'level', 'duration_class']):
        ok = g[g.skip == '']
        cnt.append(dict(source=s, level=lv, duration_class=cl, rises_in_set=len(g), themes=g.node_id.nunique(), tested=len(ok), too_sparse=int(ok.too_sparse.sum()),
                        not_tested=int((g.skip != '').sum()), pooled=len(contributing(g)), share_p_below_0_05=fmt(float((ok.p_cat_p < S.alpha).mean()), 2) if len(ok) else ''))
    L += IO.md_table(pd.DataFrame(cnt)) + ['']

    L += ['## 3. Pooled tau by class (log lift of borrowing in months 0 to +2 over the model expectation; mean over rises)', '']
    rows = []
    for (s, lv, cl), g in R.groupby(['source', 'level', 'duration_class']):
        c = contributing(g)
        b = M.cluster_boot_mean(c.tau_p.to_numpy(), c.node_id.to_numpy(), C.BOOT_N, C.BOOT_SEED) if len(c) else dict(mean=np.nan, low=np.nan, high=np.nan, clusters=0)
        rows.append(dict(source=s, level=lv, duration_class=cl, pooled_rises=len(c), themes=b.get('clusters', 0), mean_tau=fmt(b['mean']), ci_low=fmt(b.get('low')), ci_high=fmt(b.get('high')),
                         **{f'tau_{f}': fmt(c[f'tau_p_{f}'].replace([np.inf, -np.inf], np.nan).mean()) for f in S.seattle_formats},
                         tau_months0_5=fmt(c.tau_s.replace([np.inf, -np.inf], np.nan).mean()),
                         note='' if len(c) >= MIN_RISES else 'descriptive only (fewer than 5 rises)'))
    PT = pd.DataFrame(rows)
    L += IO.md_table(PT) + ['', 'Per-format columns and months 0 to +5 are secondary and descriptive. Intervals for classes with fewer than 5 rises are not to be read.', '']

    L += ['## 4. H1 and H2', '',
          'H1: pooled tau of sustained rises minus pooled tau of fading rises, 95% percentile interval from 2,000 resamples of themes, seed 20261014; supported if the lower limit is above 0. '
          'H2: pooled tau of sustained rises, same interval method, supported if the lower limit is above 0. A class with fewer than 5 pooled rises gets no verdict.', '']
    hrows = []
    for (s, lv), g in R.groupby(['source', 'level']):
        c = contributing(g)
        sus, fad = c[c.duration_class == 'sustained'], c[c.duration_class == 'fading']
        if len(sus) and len(fad):
            h1 = boot_diff(sus, fad, C.BOOT_N, C.BOOT_SEED)
        else:
            h1 = dict(diff=np.nan, low=np.nan, high=np.nan, dropped=0, n_valid=0, clusters=0)
        h2 = C.M.cluster_boot_mean(sus.tau_p.to_numpy(), sus.node_id.to_numpy(), C.BOOT_N, C.BOOT_SEED) if len(sus) else dict(mean=np.nan, low=np.nan, high=np.nan)
        hrows.append(dict(source=s, level=lv, sustained=len(sus), fading=len(fad),
                          H1_diff=fmt(h1['diff']), H1_low=fmt(h1.get('low')), H1_high=fmt(h1.get('high')), H1_resamples_dropped=h1.get('dropped'),
                          H1_verdict=verdict(min(len(sus), len(fad)), h1.get('low')),
                          H2_mean=fmt(h2['mean']), H2_low=fmt(h2.get('low')), H2_high=fmt(h2.get('high')), H2_verdict=verdict(len(sus), h2.get('low'))))
    H = pd.DataFrame(hrows)
    H.to_csv(C.OUTDIR / 'hypotheses.csv', index=False)
    L += IO.md_table(H) + ['']

    L += ['## 5. Sensitivity: tests with fewer than 5 expected checkouts included (descriptive)', '']
    srows = []
    for (s, lv, cl), g in R.groupby(['source', 'level', 'duration_class']):
        ok = g[g.skip == ''].replace([np.inf, -np.inf], np.nan)
        ok = ok[ok.tau_p.notna()]
        srows.append(dict(source=s, level=lv, duration_class=cl, rises=len(ok), mean_tau=fmt(ok.tau_p.mean()) if len(ok) else ''))
    L += IO.md_table(pd.DataFrame(srows)) + ['', f'Run time {time.time() - t0:.0f} s.', '', '<!-- AGREEMENT -->']
    txt = C.REPORT.read_text().split('<!-- TESTS -->')[0]
    C.REPORT.write_text(txt + '<!-- TESTS -->' + '\n'.join(L) + '\n')
    print(H.to_string())


if __name__ == '__main__':
    main()
