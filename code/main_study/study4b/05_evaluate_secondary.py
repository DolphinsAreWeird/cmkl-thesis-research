# Step 05 (Study 4b): evaluation of the two secondary surge definitions (addendum 2026-10-14_a_secondary_surges.json), reported beside
# the primary log(1.3) surge, never instead of it. Same metrics, strata, bootstrap and helps rule as Part B of 03_evaluate.py.
# Reads data/db/study4b/forecasts_surge_{base98,pct20}.parquet and the primary tables in data/reports/study4b_b_*.csv.
#   .venv/bin/python 05_evaluate_secondary.py [--reports-dir D]
import sys, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _settings as ST
import _b_eval as EV
import _b_surge2 as SG
from _b_eval import md_table

CLF = lambda fs: f'catboost_clf|{fs}'
LOG = lambda fs: f'logistic|{fs}'
B_PAIRS = [('catboost_clf', CLF('D'), CLF('D+W')), ('catboost_clf', CLF('D'), CLF('D+W+S')), ('catboost_clf', CLF('D+W'), CLF('D+W+S')),
           ('logistic', LOG('D'), LOG('D+W')), ('logistic', LOG('D'), LOG('D+W+S')), ('logistic', LOG('D+W'), LOG('D+W+S'))]
NAMES = {'base98': 'base-rate surge (top 2% of changes within format and level, cut-off from training rows only)',
         'pct20': '20% surge (change >= log 1.2 = 0.1823)'}


def wide_secondary(Fc):
    d = Fc[np.isfinite(Fc.target)].copy()
    d['m'] = d.model + '|' + d.fset
    key = EV.KEY + ['thr']
    W = d.pivot(index=key, columns='m', values='pred').reset_index()
    W.columns.name = None
    W['surge'] = (W.target >= W.thr).astype(float)
    return W, [c for c in W.columns if c not in key + ['surge']]


def showcases(W, models, nodes, B):
    rows = []
    for case in B.showcases:
        hit = nodes[(nodes.label.str.lower() == case['label'].lower()) & nodes.level.isin(B.levels)]
        for _, nd in hit.iterrows():
            for fmt in case['formats']:
                mi = ST.mi_from_ym(case['origin'])
                base = dict(category=nd.label, level=nd.level, node_id=nd.node_id, format=fmt, origin=case['origin'], target_month=case['target'])
                b = W[(W.node_id == nd.node_id) & (W.format == fmt) & (W.origin_mi == mi)]
                if b.empty:
                    rows.append({**base, 'note': 'not forecast at this origin'})
                    continue
                b = b.iloc[0]
                grp = W[(W.format == fmt) & (W.level == nd.level) & (W.origin_mi == mi)]
                row = {**base, 'actual_change': b.target, 'cutoff': b.thr, 'surge': b.surge, 'n_in_group': len(grp)}
                for m in models:
                    row['p ' + m] = b[m]
                    row['rank ' + m] = int((grp[m] > b[m]).sum() + 1)
                row['note'] = ''
                rows.append(row)
    return pd.DataFrame(rows)


def verdicts(t):
    L = []
    for cls, base, new in B_PAIRS[:2] + B_PAIRS[3:5]:
        for _, r in t[(t.comparison == f'{new} vs {base}') & t.scope.str.startswith(EV.POOLED)].iterrows():
            L.append(f'- {cls}: {new} vs {base}, print and ebook pooled, {r.level} level: **{"interest helps" if r.helps else "does not help"}** '
                     f'(AP {r.ap_base:.4f} to {r.ap_new:.4f}, difference {r.ap_diff:+.4f}, interval {r.ci_lo:+.4f} to {r.ci_hi:+.4f}, {r.surges} surges).')
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reports-dir', default=str(ST.REPORTS))
    ap.add_argument('--db-dir', default=str(ST.OUT))
    ap.add_argument('--nodes', default=str(ST.DB / 'study3' / 'nodes.parquet'))
    a = ap.parse_args()
    B = ST.settings()
    rep = pathlib.Path(a.reports_dir)
    nodes = pd.read_parquet(a.nodes)
    prim_ap = pd.read_csv(rep / 'study4b_b_ap_difference.csv')
    prim_m = pd.read_csv(rep / 'study4b_b_surge_metrics.csv')
    L = ['# Study 4b: secondary surge definitions (Part B, horizon 2)', '',
         f'Made {time.strftime("%Y-%m-%d %H:%M")}. Addendum `prereg/addenda_4b/2026-10-14_a_secondary_surges.json`. Two extra surge definitions, each with its own classifiers '
         'and average precision (AP), reported beside the primary log(1.3) surge and never instead of it. Models (CatBoost classifier, logistic regression), feature sets (D, D+W, D+W+S), '
         'horizon 2, walk-forward retraining at every origin, strata, 2,000-draw block bootstrap (blocks of 3 months, seed 20261013) and the helps rule (interval above zero) are the same as for the primary surge. '
         'In the base-rate surge the cut-off (98th percentile of the 2-month change in log share within the same format and level) is computed on the training rows of each origin only and then applied to '
         'that origin\'s training labels and test rows, so the label of a test row never uses the test month or later months; the share of surges in the test rows therefore differs a little from 2%. '
         'The primary evaluation was read before this step was built; no setting was changed after it.', '']
    summary = []
    for d in SG.DEFS:
        Fc = pd.read_parquet(pathlib.Path(a.db_dir) / f'forecasts_surge_{d}.parquet')
        W, models = wide_secondary(Fc)
        models = [m for m in [CLF(f) for f in B.feature_sets] + [LOG(f) for f in B.feature_sets] if m in W]
        t_s = EV.surge_table(W, models, B)
        t_ap = EV.ap_diff_table(W, [p for p in B_PAIRS if p[1] in W and p[2] in W], B)
        t_sh = showcases(W, models, nodes, B)
        t_s.to_csv(rep / f'study4b_secondary_{d}_metrics.csv', index=False)
        t_ap.to_csv(rep / f'study4b_secondary_{d}_ap_difference.csv', index=False)
        t_sh.to_csv(rep / f'study4b_secondary_{d}_showcases.csv', index=False)
        cut = Fc.groupby(['format']).thr.agg(['min', 'median', 'max']).round(4).reset_index() if d == 'base98' else None
        L += [f'## {NAMES[d]}', '', f'Forecast rows {len(Fc):,} from {Fc.origin.nunique()} origins ({Fc.origin.min()} to {Fc.origin.max()}).', '']
        if cut is not None:
            L += ['Cut-offs applied to test rows (change in log share; range over origins):', '', md_table(cut, 4), '']
        L += ['### Metrics', '', md_table(t_s, 4, int_cols=('n', 'surges', 'origins_with_surge')), '', '### AP difference with block bootstrap', '']
        L += verdicts(t_ap) + ['', md_table(t_ap, 4, int_cols=('surges',)), '', '### Showcases (illustrations, not tests)', '', md_table(t_sh, 3), '']
        t_ap = t_ap.assign(definition=d)
        summary.append(t_ap)
    pa = prim_ap.assign(definition='primary (log 1.3)')
    S = pd.concat([pa] + summary, ignore_index=True)
    S = S[S.scope.str.startswith(EV.POOLED)]
    key = S[S.comparison.isin([f'{n} vs {b}' for _, b, n in B_PAIRS[:2] + B_PAIRS[3:5]])]
    S.to_csv(rep / 'study4b_secondary_summary_all.csv', index=False)
    key = key[['definition', 'level', 'model_class', 'comparison', 'surges', 'ap_base', 'ap_new', 'ap_diff', 'ci_lo', 'ci_hi', 'helps']]
    key.to_csv(rep / 'study4b_secondary_summary.csv', index=False)
    bm = pd.concat([prim_m.assign(definition='primary (log 1.3)')] +
                   [pd.read_csv(rep / f'study4b_secondary_{d}_metrics.csv').assign(definition=d) for d in SG.DEFS], ignore_index=True)
    bm = bm[bm.scope.str.startswith(EV.POOLED)][['definition', 'level', 'model', 'surges', 'base_rate', 'ap', 'ap_over_base', 'recall_top', 'recall_random']]
    L2 = ['## Side by side: primary and secondary definitions (print and ebook pooled)', '',
          'AP difference for the interest comparisons (D+W and D+W+S against D):', '', md_table(key.sort_values(['level', 'model_class', 'comparison', 'definition']), 4, int_cols=('surges',)), '',
          'AP and recall in the top 10 of every model:', '', md_table(bm.sort_values(['level', 'model', 'definition']), 4, int_cols=('surges',)), '']
    L = L[:4] + L2 + L[4:]
    (rep / 'study4b_secondary_surges.md').write_text('\n'.join(L))
    print(f'wrote {rep / "study4b_secondary_surges.md"}')


if __name__ == '__main__':
    main()
