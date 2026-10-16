"""Study 2R step 14: single-book tests (BH), pooled tau by duration class and size tercile with equivalence verdicts, the confirmatory
duration tests of addendum a (H1, H2, size coefficient, Hansen threshold), for the main set, the audiobook model, the ratio 1.5
sensitivity and the author-article shifts. Reads data/db/study2r/effects_<set>.parquet (step 13). Writes data/reports/study2r_*.csv and the
sections 'main', 'confirmatory', 'secondary' of data/reports/study2r_results.md."""
from _pipe2r import *
import argparse
ap = argparse.ArgumentParser(); ap.add_argument('--sets', default='book,audio,book15,author'); args = ap.parse_args()
t0 = time.time()
assert '<!-- begin controls -->' in (REP / 'study2r_results.md').read_text()
TITLE = {'book': 'Main: calibrated rule (floor 300, ratio 4.0), print and ebook', 'audio': 'Secondary: same shifts, audiobook',
         'book15': 'Sensitivity (addendum c): ratio 1.5, print and ebook', 'author': 'Secondary: author-article shifts, print and ebook'}
pc = lambda x: 100 * (np.exp(x) - 1)


def frame(R):
    """Tests that enter the pooled analysis: usable fit and window, not too sparse (sum mu >= 5), finite tau (sum Y > 0)."""
    ok = R[R.skip == ''].copy()
    ex = dict(tested=len(ok), too_sparse=int(ok.too_sparse.sum()), y_zero=int((~ok.too_sparse & ~np.isfinite(ok.tau_p)).sum()))
    A = ok[~ok.too_sparse & np.isfinite(ok.tau_p)].copy()
    A['dur'] = A.whole_duration.astype(float)
    A['log2dur'] = np.log2(A.dur); A['log2peak'] = np.log2(A.whole_peak)
    A['tercile'] = pd.qcut(A.whole_peak, 3, labels=['small', 'middle', 'large']).astype(str)
    return A, ex, R


def verdict(lo, hi, n_works):
    if hi < LOG110:
        return 'no meaningful effect (upper bound below +10%)' if n_works >= FEAS_WORKS else f'inconclusive (upper bound below +10% but only {n_works} works, fewer than {FEAS_WORKS})'
    if lo > 0:
        return 'positive: interval above 0; cannot rule out +10%'
    return 'inconclusive: cannot rule out +10%'


def pooled(A, label_rows):
    rows = []
    for grp, col, val in label_rows:
        g = A if col is None else A[A[col] == val]
        if len(g) < 2:
            continue
        r = dict(group=grp, tests=len(g), works=g.work_id.nunique(), articles=g.article.nunique())
        b = M.cluster_boot_mean(g.tau_p.to_numpy(), g.work_id.to_numpy(), N_BOOT, SEED)
        ba = M.cluster_boot_mean(g.tau_p.to_numpy(), g.article.to_numpy(), N_BOOT, SEED)
        bs = M.cluster_boot_mean(g.tau_s.replace([np.inf, -np.inf], np.nan).to_numpy(), g.work_id.to_numpy(), N_BOOT, SEED)
        r.update(tau=b['mean'], lo=b['low'], hi=b['high'], lift_pct=pc(b['mean']), lift_lo=pc(b['low']), lift_hi=pc(b['high']),
                 largest_lift_ruled_out_pct=pc(b['high']), lo_article=ba['low'], hi_article=ba['high'],
                 tau_s=bs['mean'], lo_s=bs.get('low', np.nan), hi_s=bs.get('high', np.nan), share_p_lt_05=float((g.p_p < ALPHA).mean()),
                 median_summu=float(g.summu_p.median()), verdict=verdict(b['low'], b['high'], g.work_id.nunique()))
        rows.append(r)
    return pd.DataFrame(rows)


def confirmatory(A, cl):
    out = {}
    X1 = np.column_stack([np.ones(len(A)), A.log2dur])
    est, B = boot_ols(X1, A.tau_p, A[cl])
    lo, hi = pct(B[:, 1]); p1 = float((1 + (B[:, 1] <= 0).sum()) / (N_BOOT + 1))
    out['H1'] = dict(slope=float(est[1]), ci_low=lo, ci_high=hi, p_one_sided=p1, verdict='supported (p < 0.05, slope > 0)' if est[1] > 0 and p1 < ALPHA else 'not supported')
    lowm, highm = (A.dur <= 2), (A.dur >= 6)
    if lowm.sum() >= 2 and highm.sum() >= 2:
        d, Bd = boot_diff(A.tau_p, highm, lowm, A[cl])
        dl, dh = pct(Bd)
        out['H2'] = dict(diff=d, ci_low=dl, ci_high=dh, n_low=int(lowm.sum()), n_high=int(highm.sum()), mean_low=float(A.tau_p[lowm].mean()), mean_high=float(A.tau_p[highm].mean()),
                         verdict='supported (95% interval above 0)' if dl > 0 else 'not supported')
    X2 = np.column_stack([np.ones(len(A)), A.log2dur, A.log2peak])
    est2, B2 = boot_ols(X2, A.tau_p, A[cl])
    out['size'] = dict(coef_log2_peak=float(est2[2]), ci_low=pct(B2[:, 2])[0], ci_high=pct(B2[:, 2])[1], coef_log2_dur=float(est2[1]),
                       dur_ci_low=pct(B2[:, 1])[0], dur_ci_high=pct(B2[:, 1])[1], corr_log2dur_log2peak=float(np.corrcoef(A.log2dur, A.log2peak)[0, 1]))
    out['hansen'] = hansen(A.dur.to_numpy(), A.tau_p.to_numpy(), A[cl].to_numpy())
    return out


allsec = {}
for st in args.sets.split(','):
    R = pd.read_parquet(OUT / f'effects_{st}.parquet')
    A, ex, R = frame(R)
    L = [f'### {TITLE[st]}', '',
         f'Tests: {len(R)} work-shift rows, {ex["tested"]} with a usable fit and window; {ex["too_sparse"]} too sparse (expected checkouts over months 0 to +2 below 5; out of BH and pooled means); '
         f'{ex["y_zero"]} with no checkouts in the window (tau = -infinity; out of the pooled means); {len(A)} tests in the pooled analysis, {A.work_id.nunique()} works, {A.article.nunique()} articles. '
         f'Mean placebo works per test {R[R.skip == ""].n_placebos.mean():.0f}.', '']
    # single tests and BH
    fam = R[(R.skip == '') & ~R.too_sparse & R.p_p.notna()].copy()
    fam['bh_q'] = M.bh_q(fam.p_p.to_numpy(float))
    fam['detected_bh'] = fam.bh_q < BH_Q
    fam = fam.merge(A[['work_id', 'm0']].assign(in_pooled=True), on=['work_id', 'm0'], how='left')
    save = fam[['set', 'work_id', 'article', 'start_week', 'm0', 'label', 'whole_duration', 'whole_peak', 'summu_p', 'sumy_p', 'tau_p', 'z_p', 'n_placebos', 'p_p', 'tau_s', 'p_s', 'bh_q', 'detected_bh']]
    save.to_csv(REP / f'study2r_single_tests_{st}.csv', index=False)
    L += [f'Single-book tests (one-sided rank p among placebo works, months 0 to +2): {len(fam)} tests; p < 0.05 in {int((fam.p_p < ALPHA).sum())} ({100 * (fam.p_p < ALPHA).mean():.1f}%, 5% expected with no effect); '
          f'p < 0.01 in {int((fam.p_p < 0.01).sum())} ({100 * (fam.p_p < 0.01).mean():.1f}%); Benjamini-Hochberg q < 0.10: {int(fam.detected_bh.sum())} ({100 * fam.detected_bh.mean():.1f}%) in {fam[fam.detected_bh].work_id.nunique()} works. '
          f'Months 0 to +5: p < 0.05 in {100 * (fam.p_s < ALPHA).mean():.1f}%. Placebo years: mean share of placebo-year z at or above the treated z {fam.py_share_ge.mean():.3f} (0.5 expected with no effect) over {int(fam.py_share_ge.notna().sum())} tests.', '']
    # pooled
    rows = [('all shifts', None, None)] + [(f'class: {c}', 'label', c) for c in CLASSES] + [(f'whole duration: {b}', 'duration_bin', b) for b in ['1-2 weeks', '3 weeks', '4-5 weeks', '6+ weeks']] \
        + [(f'size tercile: {c}', 'tercile', c) for c in ['small', 'middle', 'large']]
    P = pooled(A, rows)
    P.insert(0, 'set', st)
    P.to_csv(REP / f'study2r_pooled_{st}.csv', index=False)
    edges = A.whole_peak.quantile([0, 1 / 3, 2 / 3, 1]).round(1).tolist()
    L += ['Pooled mean tau = log(sum Y / sum mu) over months 0 to +2, 95% interval from a bootstrap clustered by work (2,000 resamples, seed 20261013). Lift = exp(tau) - 1. '
          'The largest lift ruled out is the lift at the upper 95% bound. Verdict by addendum a and b (no meaningful effect needs an upper bound below +10% and at least 299 works).', '',
          f'Size terciles are of whole peak ratio: cut points {edges[1]} and {edges[2]} (range {edges[0]} to {edges[3]}).', '']
    Pt = P.assign(mean_tau=P.tau, interval=[f'{a:.3f} to {b:.3f}' for a, b in zip(P.lo, P.hi)], lift=P.lift_pct.round(1),
                  lift_interval=[f'{a:.1f}% to {b:.1f}%' for a, b in zip(P.lift_lo, P.lift_hi)], largest_lift_ruled_out=P.largest_lift_ruled_out_pct.round(1),
                  interval_by_article=[f'{a:.3f} to {b:.3f}' for a, b in zip(P.lo_article, P.hi_article)], p05=(100 * P.share_p_lt_05).round(1))
    L += md_table(Pt[['group', 'tests', 'works', 'mean_tau', 'interval', 'lift', 'lift_interval', 'largest_lift_ruled_out', 'p05', 'interval_by_article', 'verdict']])
    L += ['', 'p05 = share of tests with one-sided p < 0.05 (%). largest_lift_ruled_out in %. interval_by_article = the same bootstrap clustered by article (works of one article together), as a check.', '']
    dg = []
    for grp, col, val in rows:
        g = A if col is None else A[A[col] == val]
        g = g[g.plc_tau_median.notna()]
        if len(g) > 5:
            b = M.cluster_boot_mean((g.tau_p - g.plc_tau_median).to_numpy(), g.work_id.to_numpy(), N_BOOT, SEED)
            bm = M.cluster_boot_mean((g.tau_p - g.plc_tau_mean).to_numpy(), g.work_id.to_numpy(), N_BOOT, SEED)
            dg.append(dict(group=grp, tests=len(g), mean_tau=g.tau_p.mean(), placebo_median_tau=g.plc_tau_median.mean(), adjusted=b['mean'], lo=b['low'], hi=b['high'],
                           placebo_mean_tau=g.plc_tau_mean.mean(), adjusted_vs_placebo_mean=bm['mean'], lo_m=bm['low'], hi_m=bm['high']))
    DG = pd.DataFrame(dg); DG.insert(0, 'set', st); DG.to_csv(REP / f'study2r_placebo_adjusted_{st}.csv', index=False)
    L += ['Diagnostic, not in the record and not used for any verdict: mean tau of the treated work minus the median tau of its matched placebo works in the same months (the placebo works show what the model forecasts leave over in the same calendar months; interval from the work-clustered bootstrap).', '']
    L += md_table(DG.drop(columns='set').assign(interval=[f'{a:.3f} to {b:.3f}' for a, b in zip(DG.lo, DG.hi)], interval_vs_mean=[f'{a:.3f} to {b:.3f}' for a, b in zip(DG.lo_m, DG.hi_m)]).drop(columns=['lo', 'hi', 'lo_m', 'hi_m']))
    L += ['']
    ps = pooled(A.assign(x=1), [('months 0 to +5 (all shifts)', None, None)])
    L += [f'Secondary window (months 0 to +5), all shifts: mean tau {ps.tau_s[0]:.3f} (95% interval {ps.lo_s[0]:.3f} to {ps.hi_s[0]:.3f}).']
    fmt = []
    for f in (C_FMT := [c[len('tau_p_'):] for c in A.columns if c.startswith('tau_p_')]):
        v = A[f'tau_p_{f}'].replace([np.inf, -np.inf], np.nan).dropna()
        if len(v) > 5:
            b = M.cluster_boot_mean(v.to_numpy(), A.loc[v.index, 'work_id'].to_numpy(), N_BOOT, SEED)
            fmt.append(f'{f} alone (joint fit): mean tau {b["mean"]:.3f} ({b["low"]:.3f} to {b["high"]:.3f}), {len(v)} tests')
    if fmt:
        L += ['Per format, from the joint fit (descriptive): ' + '; '.join(fmt) + '.']
    L += ['']
    # confirmatory
    C = {cl: confirmatory(A, cl) for cl in ('work_id', 'article')}
    c = C['work_id']
    L += ['**Confirmatory duration tests (addendum a)** (work-clustered bootstrap, 2,000, seed 20261013):', '']
    L += [f'- H1, slope of tau on log2 whole duration in weeks: {c["H1"]["slope"]:.3f} per doubling (95% interval {c["H1"]["ci_low"]:.3f} to {c["H1"]["ci_high"]:.3f}), one-sided p = {c["H1"]["p_one_sided"]:.4f}: **{c["H1"]["verdict"]}**. '
          f'Clustered by article: interval {C["article"]["H1"]["ci_low"]:.3f} to {C["article"]["H1"]["ci_high"]:.3f}, p = {C["article"]["H1"]["p_one_sided"]:.4f}.']
    if 'H2' in c:
        h = c['H2']
        L += [f'- H2, 6+ weeks minus 1 to 2 weeks: {h["diff"]:.3f} (95% interval {h["ci_low"]:.3f} to {h["ci_high"]:.3f}); mean tau {h["mean_high"]:.3f} ({h["n_high"]} tests) against {h["mean_low"]:.3f} ({h["n_low"]} tests): **{h["verdict"]}**. '
              f'Clustered by article: {C["article"]["H2"]["ci_low"]:.3f} to {C["article"]["H2"]["ci_high"]:.3f}.']
    s = c['size']
    L += [f'- Coefficient of log2 peak size given log2 duration (not tested): {s["coef_log2_peak"]:.3f} (95% interval {s["ci_low"]:.3f} to {s["ci_high"]:.3f}); log2 duration coefficient in the same model {s["coef_log2_dur"]:.3f} ({s["dur_ci_low"]:.3f} to {s["dur_ci_high"]:.3f}); correlation of log2 duration and log2 peak {s["corr_log2dur_log2peak"]:.2f}.']
    h = c['hansen']
    if np.isfinite(h['gamma']):
        L += [f'- Hansen threshold regression of tau on whole duration (candidates 2 to 10 weeks, mean shift): threshold {h["gamma"]} weeks (shifts of {h["gamma"]} weeks or less: mean tau {h["mean_low"]:.3f}, {h["n_low"]} tests; longer: {h["mean_high"]:.3f}, {h["n_high"]} tests; difference {h["diff"]:.3f}, '
              f'95% interval at the re-estimated threshold {h["diff_ci_low"]:.3f} to {h["diff_ci_high"]:.3f}); bootstrap interval of the threshold {h["gamma_ci_low"]:.0f} to {h["gamma_ci_high"]:.0f} weeks (percentiles over resamples; share of resamples by threshold {h["boot_gamma_dist"]}); '
              f'likelihood-ratio set {h["lr_set"]}; the step explains {100 * h["ssr_reduction"]:.2f}% of the variance of tau. Article-clustered threshold interval {C["article"]["hansen"].get("gamma_ci_low", np.nan):.0f} to {C["article"]["hansen"].get("gamma_ci_high", np.nan):.0f}.']
    L += ['']
    pd.DataFrame([dict(set=st, cluster=cl, test='H1 slope per log2 week', est=C[cl]['H1']['slope'], lo=C[cl]['H1']['ci_low'], hi=C[cl]['H1']['ci_high'], p_one_sided=C[cl]['H1']['p_one_sided'])
                  for cl in C] + [dict(set=st, cluster=cl, test='H2 6+ minus 1-2 weeks', est=C[cl]['H2']['diff'], lo=C[cl]['H2']['ci_low'], hi=C[cl]['H2']['ci_high']) for cl in C if 'H2' in C[cl]]
                 + [dict(set=st, cluster=cl, test='log2 peak size given log2 duration', est=C[cl]['size']['coef_log2_peak'], lo=C[cl]['size']['ci_low'], hi=C[cl]['size']['ci_high']) for cl in C]
                 + [dict(set=st, cluster=cl, test='Hansen threshold (weeks)', est=C[cl]['hansen']['gamma'], lo=C[cl]['hansen'].get('gamma_ci_low'), hi=C[cl]['hansen'].get('gamma_ci_high')) for cl in C]
                 ).to_csv(REP / f'study2r_confirmatory_{st}.csv', index=False)
    allsec[st] = L
    log(st, 'done', int(time.time() - t0), 's')

if 'book' in allsec:
    put_section('main', ['## Main analysis and confirmatory duration tests', '', f'Built {time.strftime("%Y-%m-%d %H:%M")} by code/study2r/13_effects.py and 14_inference.py.', ''] + allsec['book'])
sec = [x for k in ('audio', 'book15', 'author') if k in allsec for x in allsec[k]]
if sec:
    put_section('secondary', ['## Secondary analyses and sensitivities', ''] + sec)
