# 05. Brisbane replication, step 5: power by injected lifts as in Study 3b (record, secondary): observed weighted loans of placebo themes are multiplied by
# (1 + L) in months 0 to +2 (L = 0.2, 0.5, 1.0; plus 0 as a calibration check), the count test is rerun, detection = one-sided placebo-category rank p < 0.05;
# 200 draws per lift and size band (quartiles of expected loans in the window), seed 20261015; minimum detectable lift = smallest lift detected in >= 80% of draws.
# The fit months end at month -7, so the lifted z is z + log(1 + L) / sqrt(phi / sum mu) (Study 3b shortcut, tested there against a refit).
# Output data/db/brisbane/power_draws.parquet, power_summary.csv; report data/reports/brisbane_05_power.md. Run with `python -I`.
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _bris as B

B3, S, INF, M, IO = B.B3, B.S, B.INF, B.M, B.IO


def main():
    t0 = time.time()
    world, shifts = B.make_world()
    rng = np.random.default_rng(S.power_seed)
    lifts = (0.0,) + tuple(S.power_lifts)
    all_draws, rows, lines, edges_rows = [], [], [], []
    for level in B.LEVELS:
        lo = B3.mi_from_ym(B.MONTH0_FROM)
        hi = min(world.last_month('seattle', level) - S.window_primary[1], B3.mi_from_ym(B.MONTH0_TO))
        tabs = {m: world.ztable('seattle', level, m) for m in range(lo, hi + 1)}
        ids, ms, sm = INF.power_candidates(world, 'seattle', level, lo, hi, tabs)
        if len(ids) == 0:
            lines += [f'### {level}: no placebo units', '']; continue
        edges = M.size_bands(sm, S.power_bands)
        band = M.band_of(sm, edges)
        edges_rows.append(dict(level=level, units=len(ids), **{f'edge_{k}': float(e) for k, e in enumerate(edges)}))
        draws = []
        for b in range(S.power_bands):
            cand = np.flatnonzero(band == b)
            if len(cand) == 0:
                continue
            pick = rng.choice(cand, size=S.power_draws, replace=len(cand) < S.power_draws)
            draws += [(int(ids[k]), int(ms[k]), b) for k in pick]
        D = INF.power_draws(world, 'seattle', level, draws, tabs, lifts)
        all_draws.append(D)
        for b, g in D.groupby('band'):
            tab, mde = M.power_summary(g, S)
            tab.insert(0, 'band', b); tab.insert(0, 'level', level)
            tab['mde'] = mde; tab['median_sum_mu'] = float(g.summu_p.median()); tab['median_placebos'] = float(g.n_placebos.median())
            rows.append(tab)
            lines += [f'### {level}, size band {b + 1} of {S.power_bands} (expected loans {edges[b]:.1f} to {edges[b + 1]:.1f}): minimum detectable lift {mde if mde == mde else "none of the sizes"}', '']
            lines += IO.md_table(tab[['lift', 'draws', 'detected', 'rate']], floatfmt='{:.3f}') + ['']
    D = pd.concat(all_draws, ignore_index=True)
    D['month0'] = [B3.ym_of(m) for m in D.m0]
    IO.save_parquet(D, B.DB / 'power_draws.parquet')
    T = pd.concat(rows, ignore_index=True)
    T.to_csv(B.DB / 'power_summary.csv', index=False)
    # all bands together: detection by lift per level
    agg = []
    for level, g in D.groupby('level'):
        t, mde = M.power_summary(g, S)
        t.insert(0, 'level', level); t['mde_all_bands'] = mde
        agg.append(t)
    A = pd.concat(agg)
    head = [f'# Brisbane replication: power by injected lifts', '', f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}; Brisbane record SHA-256 `{B.SHA}`',
            f'- {S.power_draws} draws per lift and size band, lifts {list(S.power_lifts)} (+0 as a calibration check), seed {S.power_seed}; month 0 {B.MONTH0_FROM} to {B.MONTH0_TO}; detection one-sided rank p < {S.power_alpha}; MDE = smallest lift detected in >= {S.power_rate:.0%} of draws',
            '- size band edges (expected weighted loans in months 0 to +2, quartiles of all placebo units per level):', *IO.md_table(pd.DataFrame(edges_rows), floatfmt='{:.1f}'), '',
            '## Detection by lift, all size bands together (an average over small and large themes)'] + IO.md_table(A, floatfmt='{:.3f}') + ['', '## By size band', ''] + lines + [f'run time {time.time() - t0:.0f}s']
    (B.REP / 'brisbane_05_power.md').write_text('\n'.join(head) + '\n')
    print('\n'.join(head))


if __name__ == '__main__':
    main()
