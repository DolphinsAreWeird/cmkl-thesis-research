# 13. Which shifts carry over (record, all_shifts.carry_over): the Study 3 carry-over regression with tau from the count model as the
# outcome: OLS of tau (months 0..+2, joint Seattle model) on log(size), duration class (reference: fading) and broad category fixed
# effects, with a bootstrap clustered by category (2,000 resamples, seed 20261013). There is no format term because the model is joint
# across the Seattle formats.
# NOT IN RECORD: (1) fitted separately for each interest source and each tested level (as Study 3); main-analysis (non-seasonal)
# shifts only; (2) tests that are too sparse (sum mu < 5) or have sum Y = 0 (tau undefined) are left out of the main model; a second
# model includes the too-sparse tests with sum Y > 0; (3) Study 3's lag of the peak gap is not repeated (the count model gives no
# monthly gap series; the monthly observed and expected counts of a test can be read from the event study).
# Needs: the shift-effects report. Output: data/db/study3b/carryover_coefs.csv, report study3b_13_carryover.md
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from _settings import SETTINGS as S
import _paths as IO
import _methods as M


def model_data(R, include_sparse):
    d = R[(R.analysis == 'main') & (R.skip == '')].replace([np.inf, -np.inf], np.nan)
    if not include_sparse:
        d = d[~d.too_sparse.fillna(False).astype(bool)]
    return d.dropna(subset=['tau_p', 'size'])


def fit_all(d, n_boot, include_sparse, extra=()):
    out = []
    for (src, level), g in d.groupby(['source', 'level']):
        if g.node_id.nunique() < 3:
            continue
        tab, n, ncl = M.carry_fit(g, S, outcome='tau_p', extra=extra, n_boot=n_boot)
        tab.insert(0, 'level', level); tab.insert(0, 'source', src)
        tab['n_tests'], tab['n_categories'], tab['include_sparse'] = n, ncl, include_sparse
        out.append(tab)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    ap = IO.parser('Study 3b carry-over model')
    ap.add_argument('--boot', type=int, default=None, help='simulation runs only: bootstrap resamples')
    args, P, meta, warn = IO.start('13', ap)
    n_boot = IO.sim_only(args, 'boot', S.boot_n)
    R = IO.read_parquet(P.out('shift_effects.parquet'))
    C0 = fit_all(model_data(R, False), n_boot, False)
    C1 = fit_all(model_data(R, True), n_boot, True)
    C = pd.concat([C0, C1], ignore_index=True)
    IO.save_csv(C, P.out('carryover_coefs.csv'))
    d = model_data(R, False)
    L = [f'- tests in the main model: {len(d)} (main analysis, non-sparse, sum Y > 0); by level: {d.groupby("level").size().to_dict()}',
         f'- bootstrap clustered by category: {n_boot} resamples (record {S.boot_n}), seed {S.boot_seed}; 95% percentile intervals',
         f'- outcome: tau (log of observed over expected weighted checkouts), months {S.carry_window[0]} to +{S.carry_window[1]}; reference duration class: {S.carry_ref_class}']
    L += [f'- WARNING: {w}' for w in warn] + ['', '## Coefficients (too-sparse tests left out)']
    L += IO.md_table(C0) if len(C0) else ['(no model could be fitted)']
    L += ['', '## Coefficients including too-sparse tests with sum Y > 0 (sensitivity)']
    L += IO.md_table(C1) if len(C1) else ['(no model could be fitted)']
    path = IO.write_report(P, '13', 'Study 3b carry-over model', L, S, meta)
    print('\n'.join(L))
    print('report:', path)


if __name__ == '__main__':
    main()
