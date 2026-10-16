# 11. Power by injected lifts (record, power): the observed Y of placebo categories is multiplied by (1 + L) in months 0..+2
# after random placebo start months, and the count event study is rerun; detection = one-sided placebo-category rank p < 0.05;
# the minimum detectable effect is the smallest lift detected in at least 80% of draws, per level and size band.
# Size bands are the quartiles of sum mu (the expected weighted checkouts over the primary window), computed per level over all
# placebo units (category x month 0 with a feasible fit and no interest shift in months -6..+6, month 0 from the study start).
# 200 draws per size and band, seed 20261013, lifts 0.10 0.20 0.30 0.50 1.00.
# The fit months end at month -7, so a lift in months 0..+2 changes only sum Y: mu and phi stay as fitted, and the lifted z is
# z + log(1 + L) / sqrt(phi / sum mu), ranked among the other placebo categories of that month (same exclusions as a test).
# NOT IN RECORD: (1) the same draws are used for every lift (common random numbers) and are drawn without replacement within a
# band (with replacement if a band has fewer units); (2) placebo units are drawn uniformly among the units of a band;
# (3) a lift of 0 is also run as a calibration check of the false-positive rate; it is not part of the minimum detectable
# effect; (4) Seattle joint model only (LibriVox is not part of the power run).
# Needs: the controls report (PASS, or --accept-failed-controls). Output: data/db/study3b/power_draws.parquet, power_summary.csv,
# report study3b_11_power.md. The z tables are cached in data/db/study3b/ztables/ and reused by step 12.
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

B3 = _s3.build


def controls_ok(P, accept):
    status = IO.report_field(P.report('10'), 'controls status')
    if status != 'PASS' and not accept:
        raise SystemExit('Step 11 refuses to run: the positive-controls report says the controls did not all pass '
                         f'(status {status}). Check data and mappings first (record), then rerun 10, or pass --accept-failed-controls.')
    return status


def main():
    ap = IO.parser('Study 3b power by injected lifts')
    ap.add_argument('--accept-failed-controls', action='store_true')
    ap.add_argument('--draws', type=int, default=None, help='simulation runs only: draws per lift size and band')
    args, P, meta, warn = IO.start('11', ap)
    cstatus = controls_ok(P, args.accept_failed_controls)
    n = IO.sim_only(args, 'draws', S.power_draws)
    shifts = INF.load_shifts(P, S)
    world = INF.World(P, S, shifts)
    spec = dict(sim=args.sim)
    workers = IO.workers_of(args)
    rng = np.random.default_rng(S.power_seed)
    lifts = (0.0,) + tuple(S.power_lifts)
    t0 = time.time()
    all_draws, rows, lines, edges_rows = [], [], [], []
    for level in S.levels_tested:
        lo = B3.mi_from_ym(S.study_start)
        hi = world.last_month('seattle', level) - S.window_primary[1]
        INF.run_tasks(spec, [('seattle', 'z', level, m, []) for m in range(lo, hi + 1)], workers)
        tabs = {m: world.ztable('seattle', level, m) for m in range(lo, hi + 1)}
        ids, ms, sm = INF.power_candidates(world, 'seattle', level, lo, hi, tabs)
        if len(ids) == 0:
            lines += [f'### {level}: no placebo units', '']
            continue
        edges = M.size_bands(sm, S.power_bands)
        band = M.band_of(sm, edges)
        edges_rows.append(dict(level=level, units=len(ids), **{f'edge_{k}': float(e) for k, e in enumerate(edges)}))
        draws = []
        for b in range(S.power_bands):
            cand = np.flatnonzero(band == b)
            if len(cand) == 0:
                continue
            pick = rng.choice(cand, size=n, replace=len(cand) < n)
            draws += [(int(ids[k]), int(ms[k]), b) for k in pick]
        D = INF.power_draws(world, 'seattle', level, draws, tabs, lifts)
        all_draws.append(D)
        for b, g in D.groupby('band'):
            tab, mde = M.power_summary(g, S)
            tab.insert(0, 'band', b); tab.insert(0, 'level', level)
            tab['mde'] = mde
            tab['median_sum_mu'] = float(g.summu_p.median())
            tab['median_placebos'] = float(g.n_placebos.median())
            rows.append(tab)
            lines += [f'### {level}, size band {b + 1} of {S.power_bands} (sum mu {edges[b]:.1f} to {edges[b + 1]:.1f}): minimum detectable lift '
                      f'{mde if mde == mde else "none of the sizes"}', ''] + IO.md_table(tab[['lift', 'draws', 'detected', 'rate', 'median_placebos']]) + ['']
    D = pd.concat(all_draws, ignore_index=True) if all_draws else pd.DataFrame()
    D['month0'] = [B3.ym_of(m) for m in D.m0] if len(D) else []
    IO.save_parquet(D, P.out('power_draws.parquet'))
    T = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    IO.save_csv(T, P.out('power_summary.csv'))
    head = [f'- draws per lift size and band: {n} (record {S.power_draws}); lifts {list(S.power_lifts)} (plus 0 as a calibration check); seed {S.power_seed}; '
            f'detection: one-sided rank p < {S.power_alpha}; MDE: smallest lift detected in >= {S.power_rate:.0%} of draws',
            f'- positive-controls status when run: {cstatus}', f'- size band edges (sum mu, quartiles per level): ',
            *IO.md_table(pd.DataFrame(edges_rows)), f'- run time {time.time() - t0:.0f}s with {workers} workers'] + [f'- WARNING: {w}' for w in warn] + ['']
    path = IO.write_report(P, '11', 'Study 3b power by injected lifts', head + lines, S, meta)
    print('\n'.join(head + lines))
    print('report:', path)


if __name__ == '__main__':
    main()
