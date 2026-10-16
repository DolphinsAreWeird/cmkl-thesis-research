"""Study 2R step 12: POSITIVE CONTROLS, run before anything else on real data. Event per addendum c (first shift at ratio 1.5 within 8 weeks of the
release date, else the release month); outcome per the record (joint print + ebook count event study, tau over months 0 to +2, 200 matched placebo works,
one-sided rank p). Pass rule of the record: pooled tau > 0 with a bootstrap interval above zero across the controls AND at least 4 of 7 with p < 0.05.
Writes data/db/study2r/controls.csv and the section 'controls' of data/reports/study2r_results.md."""
from _pipe2r import *
import argparse
ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=2); args = ap.parse_args()
t0 = time.time()
REL = {"The Queen's Gambit": ('2020-10-23', 47460), 'The Duke and I': ('2020-12-25', 40237), 'Dune': ('2021-10-22', 13343),
       'Where the Crawdads Sing': ('2022-07-15', 36910), 'American Prometheus': ('2023-07-21', 5121),
       'Killers of the Flower Moon': ('2023-10-20', 30993), 'Shogun': ('2024-02-27', 547)}
W = works_table()
SB15 = pd.read_parquet(OUT / 'shifts_book_ratio1_5.parquet')
rows = []
for name, (rel, wid) in REL.items():
    art = W.set_index('work_id').article[wid]
    r = pd.Timestamp(rel)
    s = SB15[(SB15.article == art) & (SB15.start_week >= r - pd.Timedelta(days=56)) & (SB15.start_week <= r + pd.Timedelta(days=56))].sort_values('start_week')
    if len(s):
        f = s.iloc[0]
        rows.append(dict(control=name, work_id=wid, article=art, release=rel, source='first ratio 1.5 shift', start_week=f.start_week, m0=int(mi_of([f.start_week])[0]),
                         shift_class=f.label, shift_size=f['size'], shift_whole_duration=int(f.whole_duration), n_shifts_in_window=len(s)))
    else:
        rows.append(dict(control=name, work_id=wid, article=art, release=rel, source='release month (no shift)', start_week=pd.NaT, m0=int(r.year * 12 + r.month - 1),
                         shift_class='', shift_size=np.nan, shift_whole_duration=0, n_shifts_in_window=0))
CT = pd.DataFrame(rows)
log(CT[['control', 'source', 'start_week', 'shift_class']].to_string())

C = load_counts(('print', 'ebook'))
tabs = build_ztables(C, 'pe', month_range(C), args.workers)
log('z tables print+ebook', len(tabs), int(time.time() - t0), 's')
X = screens(C, W, 'book', SB15)
pool = pool_mask(C, W, 'book'); art = art_codes(C, W)
R = run_tests(C, tabs, CT, pool, art, X)
R['lift_pct'] = 100 * (np.exp(R.tau_p) - 1)
R['p_below_05'] = R.p_p < ALPHA
ok = R[(R.skip == '') & np.isfinite(R.tau_p)]
b = M.cluster_boot_mean(ok.tau_p.to_numpy(), ok.work_id.to_numpy(), N_BOOT, SEED)
n_sig = int((ok.p_p < ALPHA).sum())
passed = bool(b['mean'] > 0 and b['low'] > 0 and n_sig >= 4)
# secondary: audiobook model (descriptive)
Ca = load_counts(('audiobook',))
tabsa = build_ztables(Ca, 'au', month_range(Ca), args.workers)
Xa = screens(Ca, W, 'book', SB15); poola = pool_mask(Ca, W, 'book'); arta = art_codes(Ca, W)
Ra = run_tests(Ca, tabsa, CT, poola, arta, Xa)
R = R.merge(Ra[['work_id', 'tau_p', 'p_p', 'n_placebos', 'summu_p']].rename(columns=lambda c: c if c == 'work_id' else c + '_audio'), on='work_id', how='left')
R.to_csv(OUT / 'controls.csv', index=False)
R.to_csv(REP / 'study2r_controls.csv', index=False)

L = ['## Positive controls (run first, before any main analysis)', '',
     f'Built {time.strftime("%Y-%m-%d %H:%M")} by code/study2r/12_controls.py. Event per addendum c: month 0 = month of the first ratio 1.5 shift within 8 weeks of the release date, else the release month. '
     'Outcome: joint print and ebook count event study of the largest matched Seattle work, tau = log(sum Y / sum mu) over months 0 to +2, z, one-sided rank p among 200 matched placebo works.', '',
     f'**Result: {"PASS" if passed else "FAIL"}.** Pooled mean tau = {b["mean"]:.3f} (95% bootstrap interval {b["low"]:.3f} to {b["high"]:.3f}; lift {100 * (np.exp(b["mean"]) - 1):.1f}%, interval {100 * (np.exp(b["low"]) - 1):.1f}% to {100 * (np.exp(b["high"]) - 1):.1f}%); '
     f'{n_sig} of {len(ok)} tests with one-sided p < 0.05 (rule: pooled interval above zero and at least 4 of 7).', '']
T = R.assign(month0=[ym(m) for m in R.m0], lift=lambda d: d.lift_pct.round(1))
cols = ['control', 'month0', 'source', 'skip', 'formats' if 'formats' in R else 'pf', 'summu_p', 'sumy_p', 'tau_p', 'lift', 'z_p', 'n_placebos', 'plc_tau_median', 'p_p', 'tau_s', 'p_s', 'tau_p_print', 'tau_p_ebook', 'py_n', 'py_share_ge', 'tau_p_audio', 'p_p_audio']
cols = [c for c in cols if c in T.columns]
L += md_table(T[cols])
L += ['', 'Columns: summu_p = expected checkouts over months 0 to +2, sumy_p = observed; tau_p, p_p = months 0 to +2 (record primary); tau_s, p_s = months 0 to +5; tau_p_print and tau_p_ebook = the same from the joint fit, per format (descriptive); plc_tau_median = median tau of the 200 placebo works in the same months (diagnostic); py_n and py_share_ge = placebo years and their share with z at or above the treated z (descriptive); tau_p_audio, p_p_audio = separate audiobook model (secondary, descriptive).']
put_section('controls', L)
log('controls', 'PASS' if passed else 'FAIL', f'pooled tau {b["mean"]:.3f} [{b["low"]:.3f}, {b["high"]:.3f}]', f'{n_sig}/7 p<.05', int(time.time() - t0), 's')
print('\n'.join(L))
