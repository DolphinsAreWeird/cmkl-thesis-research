# 04. Brisbane replication, step 4: H1 and H2 on the Study 3 Wikipedia shifts (quality OK, non-seasonal, narrow and middle, month 0 2016-01 to 2025-06),
# Study 3b count model (months 0 to +2, 24 fit months ending at month -7, placebo-category rank on z), pooled tau by duration class with a bootstrap
# clustered by theme (2,000 resamples, seed 20261015), and the joint regression of tau on log2 whole duration and log2 whole peak size.
#   H1: pooled tau of sustained rises > 0 with its 95% bootstrap interval above 0.
#   H2: pooled tau of sustained rises minus pooled tau of fading rises > 0 with its 95% interval above 0.
# Choices the record does not make: see prereg/DEVIATIONS.md (Brisbane replication). Run with `python -I`.
# Output: data/db/brisbane/shift_effects.parquet, pooled_effects.csv, joint_regression.csv; report data/reports/brisbane_04_hypotheses.md
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _bris as B

B3, S, INF, M, IO = B.B3, B.S, B.INF, B.M, B.IO
COLS = ['shift_id', 'source', 'level', 'node_id', 'start_week', 'm0', 'duration_class', 'size', 'whole_duration', 'whole_peak', 'seasonal', 'quality_ok']


def plan(shifts, world):
    lo, hi = B3.mi_from_ym(B.MONTH0_FROM), B3.mi_from_ym(B.MONTH0_TO)
    s = shifts[(shifts.source == 'wikipedia') & shifts.labelled & shifts.quality_ok & ~shifts.seasonal & shifts.level.isin(B.LEVELS) & (shifts.m0 >= lo) & (shifts.m0 <= hi)]
    have = {lv: set(world.C[('seattle', lv)].ids) for lv in B.LEVELS}
    s = s[[n in have[lv] for lv, n in zip(s.level, s.node_id)]]
    units = s.groupby(['level', 'm0']).node_id.apply(lambda x: sorted(set(x))).reset_index()
    return s, [('seattle', 'unit', r.level, int(r.m0), list(r.node_id)) for r in units.itertuples()]


def boot_diff(R, a, b, n, seed):
    """Mean tau of class a minus mean tau of class b; themes resampled with replacement; both means recomputed on every resample."""
    g = R[R.duration_class.isin([a, b])]
    codes, uniq = pd.factorize(g.node_id, sort=True)
    G = len(uniq)
    sa = np.bincount(codes, weights=np.where(g.duration_class == a, g.tau_p, 0.0), minlength=G)
    ca = np.bincount(codes, weights=(g.duration_class == a).astype(float), minlength=G)
    sb = np.bincount(codes, weights=np.where(g.duration_class == b, g.tau_p, 0.0), minlength=G)
    cb = np.bincount(codes, weights=(g.duration_class == b).astype(float), minlength=G)
    est = sa.sum() / ca.sum() - sb.sum() / cb.sum()
    pick = np.random.default_rng(seed).integers(0, G, size=(n, G))
    with np.errstate(invalid='ignore', divide='ignore'):
        d = sa[pick].sum(1) / ca[pick].sum(1) - sb[pick].sum(1) / cb[pick].sum(1)
    d = d[np.isfinite(d)]
    lo, hi = M.percentile_ci(d, 0.95)
    return dict(diff=float(est), low=lo, high=hi, valid_resamples=len(d), share_le0=float((d <= 0).mean()), themes=G,
                n_a=int(ca.sum()), n_b=int(cb.sum()))


def ols_boot(d, n, seed):
    x = np.column_stack([np.ones(len(d)), d.ld.to_numpy(), d.lp.to_numpy()]); y = d.y.to_numpy()
    codes, uniq = pd.factorize(d.node_id); K = len(uniq)
    XtX = np.zeros((K, 3, 3)); Xty = np.zeros((K, 3))
    for k in range(K):
        m = codes == k
        XtX[k] = x[m].T @ x[m]; Xty[k] = x[m].T @ y[m]
    est = np.linalg.solve(XtX.sum(0), Xty.sum(0))
    rs = np.random.default_rng(seed); bs = np.full((n, 3), np.nan)
    for b in range(n):
        idx = rs.integers(0, K, K)
        try:
            bs[b] = np.linalg.solve(XtX[idx].sum(0), Xty[idx].sum(0))
        except np.linalg.LinAlgError:
            pass
    ok = np.isfinite(bs).all(1); bs = bs[ok]
    one = lambda col: float(np.linalg.lstsq(np.column_stack([np.ones(len(d)), d[col]]), y, rcond=None)[0][1])
    return dict(tests=len(d), themes=K, b_dur=est[1], dur_lo=np.percentile(bs[:, 1], 2.5), dur_hi=np.percentile(bs[:, 1], 97.5),
                b_peak=est[2], peak_lo=np.percentile(bs[:, 2], 2.5), peak_hi=np.percentile(bs[:, 2], 97.5), intercept=est[0],
                corr_ld_lp=float(np.corrcoef(d.ld, d.lp)[0, 1]), dur_alone=one('ld'), peak_alone=one('lp'), valid_resamples=int(ok.sum()))


def main():
    t0 = time.time()
    world, shifts = B.make_world()
    s, tasks = plan(shifts, world)
    res = INF.run_tasks({'sim': None}, tasks, 1)
    T = pd.DataFrame([r for t in res for r in t[3]])
    R = s.reindex(columns=COLS).merge(T.drop(columns=['broad_id', 'label'], errors='ignore'), on=['level', 'node_id', 'm0'], how='inner')
    R['broad_id'] = [world.cats[lv].broad_id.get(n) for lv, n in zip(R.level, R.node_id)]
    for c in ('too_sparse', 'y_zero'):
        R[c] = R[c].fillna(False).astype(bool) if c in R else False
    R['significant'] = R.p_cat_p < S.alpha
    IO.save_parquet(R.drop(columns=['py_years'], errors='ignore'), B.DB / 'shift_effects.parquet')
    tested = R[R.skip == '']
    main_ = tested[~tested.too_sparse & ~tested.y_zero].replace([np.inf, -np.inf], np.nan).dropna(subset=['tau_p'])
    L = ['# Brisbane replication: H1 and H2, joint regression', '', f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}; Brisbane record SHA-256 `{B.SHA}`',
         f'- shifts: Wikipedia, narrow and middle, labelled, quality OK, non-seasonal, month 0 {B.MONTH0_FROM} to {B.MONTH0_TO}: {len(s)} shifts with a theme in the Brisbane panel, in {len(tasks)} (level, month 0) units',
         f'- shift rows tested (feasible fit, usable window of at least {S.min_window_months} months): {len(tested)} of {len(R)}; skip reasons: {R[R.skip != ""].skip.value_counts().to_dict()}',
         f'- main set (not too sparse, i.e. at least {S.sparse_below:g} expected weighted loans in months 0 to +2, and loans above 0): {len(main_)} tests in {main_.node_id.nunique()} themes; too sparse: {int(tested.too_sparse.sum())}; zero loans in window: {int(tested.y_zero.sum())}',
         f'- bootstrap: {S.boot_n} resamples of themes, seed {S.boot_seed}, 95% percentile intervals', '']
    # ---------------- pooled tau by class
    rows = []
    for inc, d0 in (('main (not too sparse)', main_), ('including too sparse', tested[~tested.y_zero].replace([np.inf, -np.inf], np.nan).dropna(subset=['tau_p']))):
        for cls in ('sustained', 'intermediate', 'fading', 'all'):
            for lv in ('both', 'narrow', 'middle'):
                g = d0 if cls == 'all' else d0[d0.duration_class == cls]
                if lv != 'both':
                    g = g[g.level == lv]
                if len(g) == 0:
                    continue
                b = M.cluster_boot_mean(g.tau_p.to_numpy(), g.node_id.to_numpy(), S.boot_n, S.boot_seed)
                rows.append(dict(set=inc, duration_class=cls, level=lv, tests=len(g), themes=g.node_id.nunique(), tau_mean=b['mean'], ci_low=b.get('low'), ci_high=b.get('high'),
                                 lift_pct=100 * (np.exp(b['mean']) - 1), share_p_below_05=float((g.p_cat_p < S.alpha).mean()), median_expected_loans=float(g.summu_p.median())))
    P = pd.DataFrame(rows)
    P.to_csv(B.DB / 'pooled_effects.csv', index=False)
    h1 = P[(P.set.str.startswith('main')) & (P.duration_class == 'sustained') & (P.level == 'both')].iloc[0] if len(P[(P.set.str.startswith('main')) & (P.duration_class == 'sustained') & (P.level == 'both')]) else None
    d2 = boot_diff(main_, 'sustained', 'fading', S.boot_n, S.boot_seed) if (main_.duration_class == 'sustained').any() and (main_.duration_class == 'fading').any() else None
    d2s = boot_diff(tested[~tested.y_zero].replace([np.inf, -np.inf], np.nan).dropna(subset=['tau_p']), 'sustained', 'fading', S.boot_n, S.boot_seed)
    L += ['## Hypotheses (pooled mean tau over months 0 to +2; tau is the log of observed over expected weighted loans)', '']
    if h1 is not None:
        v1 = 'SUPPORTED' if (h1.tau_mean > 0 and h1.ci_low > 0) else 'NOT SUPPORTED'
        L += [f'- **H1 {v1}**: pooled tau of sustained rises = {h1.tau_mean:.3f} (95% interval {h1.ci_low:.3f} to {h1.ci_high:.3f}; about {h1.lift_pct:+.1f}% loans against the fitted trend), '
              f'{int(h1.tests)} tests in {int(h1.themes)} themes.']
    if d2 is not None:
        v2 = 'SUPPORTED' if (d2['diff'] > 0 and d2['low'] > 0) else 'NOT SUPPORTED'
        fad = P[(P.set.str.startswith('main')) & (P.duration_class == 'fading') & (P.level == 'both')].iloc[0]
        L += [f'- **H2 {v2}**: sustained minus fading = {d2["diff"]:.3f} (95% interval {d2["low"]:.3f} to {d2["high"]:.3f}; share of resamples at or below 0: {d2["share_le0"]:.3f}); '
              f'fading pooled tau = {fad.tau_mean:.3f} ({fad.ci_low:.3f} to {fad.ci_high:.3f}), {int(fad.tests)} tests in {int(fad.themes)} themes; {d2["themes"]} themes in the difference.']
    L += [f'- Sensitivity, including too-sparse tests: sustained minus fading = {d2s["diff"]:.3f} ({d2s["low"]:.3f} to {d2s["high"]:.3f}), {d2s["n_a"]} sustained and {d2s["n_b"]} fading tests.', '']
    L += ['## Pooled tau by duration class and level'] + IO.md_table(P, floatfmt='{:.3f}') + ['']
    # ---------------- by level difference
    for lv in B.LEVELS:
        g = main_[main_.level == lv]
        if (g.duration_class == 'sustained').any() and (g.duration_class == 'fading').any():
            dd = boot_diff(g, 'sustained', 'fading', S.boot_n, S.boot_seed)
            L += [f'- {lv} only: sustained minus fading = {dd["diff"]:.3f} ({dd["low"]:.3f} to {dd["high"]:.3f}), {dd["n_a"]} and {dd["n_b"]} tests, {dd["themes"]} themes.']
    # ---------------- detection
    L += ['', f'## Detection (placebo-category rank, one-sided p < {S.alpha}; about {100 * S.alpha:.0f}% expected under no effect)']
    for cls, g in main_.groupby('duration_class'):
        L.append(f'- {cls}: {int((g.p_cat_p < S.alpha).sum())} of {len(g)} ({100 * (g.p_cat_p < S.alpha).mean():.1f}%); median expected weighted loans in the window {g.summu_p.median():.1f}')
    # ---------------- joint regression
    d = main_.copy()
    d['dur'] = pd.to_numeric(d.whole_duration, errors='coerce'); d['peak'] = pd.to_numeric(d.whole_peak, errors='coerce')
    d = d[(d.dur >= 1) & (d.peak > 0)].copy()
    d['ld'], d['lp'], d['y'] = np.log2(d.dur), np.log2(d.peak), d.tau_p
    jr = []
    for name, g in (('Wikipedia, narrow and middle', d), ('narrow only', d[d.level == 'narrow']), ('middle only', d[d.level == 'middle'])):
        if g.node_id.nunique() >= 5:
            jr.append(dict(set=name, **ols_boot(g, S.boot_n, S.boot_seed)))
    J = pd.DataFrame(jr)
    J.to_csv(B.DB / 'joint_regression.csv', index=False)
    L += ['', '## Joint regression: tau on log2 whole duration (weeks) and log2 whole peak ratio (bootstrap clustered by theme)', '']
    L += IO.md_table(J.reindex(columns=['set', 'tests', 'themes', 'b_dur', 'dur_lo', 'dur_hi', 'b_peak', 'peak_lo', 'peak_hi', 'corr_ld_lp', 'dur_alone', 'peak_alone']), floatfmt='{:.3f}')
    L += ['', f'Seattle, same specification (exploratory, Study 3b tau, 625 tests): duration 0.021 (-0.013 to 0.053), size -0.008 (-0.055 to 0.043).', f'run time {time.time() - t0:.0f}s']
    (B.REP / 'brisbane_04_hypotheses.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
