# 13. Which shifts carry over (record, which_shifts_carry_over): OLS of the shift-level synthetic-control effect
# (log lift, months 0..+2) on log(size), duration class (reference: fading), broad category fixed effects, format,
# and modern (Seattle) vs classic (LibriVox), with a bootstrap clustered by category. All shifts are reported.
# The lag (month of the peak gap within 0..+6) is summarised by duration class.
# NOT IN RECORD: the model is fitted separately for each interest source and each tested level (a middle category
# contains its narrow ones, so pooling levels would count the same checkouts twice); only main-analysis
# (non-seasonal) shifts enter the model.
# Needs: the shift-effects report. Output: data/db/study3/carryover_coefs.csv, carryover_lags.csv,
# data/reports/study3_13_carryover.md
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _files as IO
import _methods as M


def model_data(R):
    d = R[(R.analysis == 'main') & R.sc_ok].copy()
    d['classic'] = d.format == 'librivox'
    return d.dropna(subset=['sc_effect_p', 'size'])


def fit_all(d, n_boot, extra=()):
    out = []
    for (src, level), g in d.groupby(['source', 'level']):
        tab, n, ncl = M.carry_fit(g, S, outcome='sc_effect_p', extra=extra, n_boot=n_boot)
        tab.insert(0, 'level', level); tab.insert(0, 'source', src)
        tab['n_tests'], tab['n_categories'] = n, ncl
        out.append(tab)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def lags(d):
    g = d.dropna(subset=['lag_peak']).groupby(['source', 'level', 'duration_class'])
    return g.lag_peak.agg(['size', 'mean', 'median']).reset_index().rename(columns={'size': 'tests'})


def main():
    ap = IO.parser('Study 3 carry-over model')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    args, P, meta, warn = IO.start('13', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    R = IO.read_parquet(P.out('shift_effects.parquet'))
    d = model_data(R)
    C = fit_all(d, n_boot)
    Lg = lags(d)
    IO.save_csv(C, P.out('carryover_coefs.csv'))
    IO.save_csv(Lg, P.out('carryover_lags.csv'))
    L = [f'- tests in the model: {len(d)} (main analysis, synthetic control estimated); classic (LibriVox) tests: {int(d.classic.sum())}',
         f'- bootstrap clustered by category: {n_boot} resamples (record {S.boot_n}), seed {S.boot_seed}; 95% percentile intervals',
         f'- outcome: synthetic-control effect, months {S.carry_window[0]} to +{S.carry_window[1]}; reference duration class: {S.carry_ref_class}']
    L += [f'- WARNING: {w}' for w in warn] + ['', '## Coefficients']
    L += IO.md_table(C) if len(C) else ['(no tests)']
    L += ['', f'## Lag of the peak gap (months {S.carry_lag[0]} to +{S.carry_lag[1]})'] + (IO.md_table(Lg) if len(Lg) else ['(none)'])
    path = IO.write_report(P, '13', 'Study 3 carry-over model', L, S, meta)
    print('\n'.join(L))
    print('report:', path)


if __name__ == '__main__':
    main()
