# 11. Injected-lift power (record, power): multiplicative lifts are injected into the demand of placebo categories
# for months 0..+2 after randomly drawn placebo start months, and the synthetic control is rerun; a draw is detected
# when the one-sided rank p < 0.05; the minimum detectable effect is the smallest lift detected in >= 80% of draws.
# Run for every tested level and format. Placebo units: (category, month 0) with month 0 from the study start, the
# size rule passed, and no interest shift of the category in months -6..+6.
# NOT IN RECORD: the same randomly drawn placebo units are used for every lift size (common random numbers), drawn
# without replacement; donor placebos are computed once per draw because the treated unit is never in their pools.
# Needs: the positive-controls report. Output: data/db/study3/power_draws.parquet, power_summary.csv,
# data/reports/study3_11_power.md
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _analysis as A
import _methods as M
from _interest import shifts_for_step


def controls_ok(P, accept):
    status = IO.report_field(P.report('10'), 'controls status')
    if status != 'PASS' and not accept:
        raise SystemExit('Step 11 refuses to run: the positive-controls report says the controls did not all pass '
                         f'(status {status}). Check data and mappings first (record), then rerun 10, or pass '
                         '--accept-failed-controls to go on and report it.')
    return status


def draw_units(ctx, rng, n):
    """Placebo units per (level, format), in a fixed order so the seed gives the same draws every run."""
    plan = []
    for key in ctx.keys(S.levels_tested):
        cand = A.power_candidates(ctx, *key)
        if not cand:
            continue
        idx = rng.choice(len(cand), size=n, replace=len(cand) < n)
        plan += [(key, cand[i]) for i in idx]
    return plan


def main():
    ap = IO.parser('Study 3 injected-lift power')
    ap.add_argument('--without-shifts', action='store_true', help='run without the shift screen (flagged)')
    ap.add_argument('--accept-failed-controls', action='store_true')
    ap.add_argument('--draws', type=int, default=None, help='simulation runs only: draws per lift size')
    args, P, meta, warn = IO.start('11', ap)
    cstatus = controls_ok(P, args.accept_failed_controls)
    n = IO.sim_only(args, 'draws', S.power_draws)
    panel, nodes, overlap = IO.load_panels(P), IO.read_parquet(P.nodes), IO.read_parquet(P.overlap)
    shifts, shift_note = shifts_for_step(P, S, args.without_shifts, '11')
    ctx = A.Context(panel, nodes, overlap, shifts, S)
    rng = np.random.default_rng(S.power_seed)
    plan = draw_units(ctx, rng, n)
    t0 = time.time()
    res = A.run_parallel(A.power_draw, ctx, [(key[0], key[1], unit[0], unit[1], S.power_lifts) for key, unit in plan], args.workers)
    D = pd.DataFrame([r for rs in res for r in rs])
    D['month0'] = [f'{m // 12:04d}-{m % 12 + 1:02d}' for m in D.m0]
    IO.save_parquet(D, P.out('power_draws.parquet'))
    rows, lines = [], []
    for (level, fmt), g in D.groupby(['level', 'format']):
        tab, mde = M.power_summary(g.to_dict('records'), S)
        tab.insert(0, 'format', fmt); tab.insert(0, 'level', level)
        tab['mde'] = mde
        tab['median_donors'] = float(g.n_donors.median())
        tab['failed_draws'] = int(g[g.lift == S.power_lifts[0]].p.isna().sum())
        rows.append(tab)
        lines += [f'### {level}, {fmt}: minimum detectable lift {mde if mde == mde else "none of the sizes"}', '']
        lines += IO.md_table(tab[['lift', 'true_log_lift', 'draws', 'detected', 'rate', 'mean_effect']]) + ['']
    T = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    IO.save_csv(T, P.out('power_summary.csv'))
    head = [f'- draws per lift size: {n} (record {S.power_draws}); lifts {list(S.power_lifts)}; seed {S.power_seed}; '
            f'detection: one-sided p < {S.power_alpha}; MDE: smallest lift detected in >= {S.power_rate:.0%} of draws',
            f'- positive-controls status when run: {cstatus}', f'- shift screen: {shift_note}',
            f'- run time {time.time() - t0:.0f}s with {args.workers} workers'] + [f'- WARNING: {w}' for w in warn] + ['']
    path = IO.write_report(P, '11', 'Study 3 injected-lift power', head + lines, S, meta)
    print('\n'.join(head + lines))
    print('report:', path)


if __name__ == '__main__':
    main()
