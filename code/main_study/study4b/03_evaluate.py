# Step 03 (Study 4b): evaluation. Part A (change forecasts: skill, DM, bootstrap, helps rule), Part B (surges: average precision,
# recall in the top 10, Brier, bootstrap of the AP difference), showcases, and a reference to Study 4's level forecasts.
# Reads data/db/study4b/forecasts.parquet and features.parquet; writes data/reports/study4b_evaluation.md and study4b_*.csv.
#   .venv/bin/python 03_evaluate.py [--forecasts F] [--features F] [--reports-dir D] [--study4-forecasts F]
import sys, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _settings as ST
import _b_eval as EV
from _b_eval import md_table

CB = lambda fs: f'catboost|{fs}'
RG = lambda fs: f'ridge|{fs}'
CLF = lambda fs: f'catboost_clf|{fs}'
LOG = lambda fs: f'logistic|{fs}'
A_PAIRS = [('catboost', CB('D'), CB('D+W')), ('catboost', CB('D'), CB('D+W+S')), ('catboost', CB('D+W'), CB('D+W+S')),
           ('ridge', RG('D'), RG('D+W')), ('ridge', RG('D'), RG('D+W+S')), ('ridge', RG('D+W'), RG('D+W+S'))]
B_PAIRS = [('catboost_clf', CLF('D'), CLF('D+W')), ('catboost_clf', CLF('D'), CLF('D+W+S')), ('catboost_clf', CLF('D+W'), CLF('D+W+S')),
           ('logistic', LOG('D'), LOG('D+W')), ('logistic', LOG('D'), LOG('D+W+S')), ('logistic', LOG('D+W'), LOG('D+W+S'))]


def verdict_lines(t, kind, what):
    L = []
    for _, r in t[t.scope.str.startswith(EV.POOLED)].iterrows():
        if kind == 'A':
            L.append(f'- {r.comparison}, print and ebook pooled, {r.level} level: **{"interest helps" if r.helps else "does not help"}** '
                     f'(skill {r.skill:.3f}, interval {r.ci_lo:.3f} to {r.ci_hi:.3f}, DM p {r.dm_p:.3f}).')
        else:
            L.append(f'- {r.model_class}: {r.comparison}, print and ebook pooled, {r.level} level: **{"interest helps" if r.helps else "does not help"}** '
                     f'(AP {r.ap_base:.4f} to {r.ap_new:.4f}, difference {r.ap_diff:+.4f}, interval {r.ci_lo:+.4f} to {r.ci_hi:+.4f}, {r.surges} surges).')
    return L


def showcases(Wa, Wb, F, nodes, B):
    rows = []
    for case in B.showcases:
        hit = nodes[(nodes.label.str.lower() == case['label'].lower()) & nodes.level.isin(B.levels)]
        for _, nd in hit.iterrows():
            for fmt in case['formats']:
                mi = ST.mi_from_ym(case['origin'])
                base = dict(category=nd.label, level=nd.level, node_id=nd.node_id, format=fmt, origin=case['origin'], target_month=case['target'])
                a = Wa[(Wa.node_id == nd.node_id) & (Wa.format == fmt) & (Wa.origin_mi == mi) & (Wa.h == B.h_surge)]
                if a.empty:
                    rows.append({**base, 'note': 'not forecast at this origin (below the size rule, or a month missing)'})
                    continue
                a = a.iloc[0]
                grp_a = Wa[(Wa.format == fmt) & (Wa.level == nd.level) & (Wa.origin_mi == mi) & (Wa.h == B.h_surge)]
                f = F[(F.node_id == nd.node_id) & (F.format == fmt) & (F.origin_mi == mi) & (F.h == B.h_surge)].iloc[0]
                row = {**base, 'actual_change': a.target, 'surge': float(a.target >= B.surge_change),
                       'rank_actual_change': int((grp_a.target > a.target).sum() + 1), 'n_in_group': len(grp_a),
                       'w_ratio': f.w_ratio, 'w_shift8': f.w_shift8, 's_sustained': f.s_sustained, 's_resp': f.s_resp, 'zero': 0.0}
                for m in [RG('D'), RG('D+W'), RG('D+W+S'), CB('D'), CB('D+W'), CB('D+W+S')]:
                    row['chg ' + m] = a.get(m, np.nan)
                b = Wb[(Wb.node_id == nd.node_id) & (Wb.format == fmt) & (Wb.origin_mi == mi)]
                grp_b = Wb[(Wb.format == fmt) & (Wb.level == nd.level) & (Wb.origin_mi == mi)]
                if len(b):
                    b = b.iloc[0]
                    for m in [CLF('D'), CLF('D+W'), CLF('D+W+S'), LOG('D'), LOG('D+W'), LOG('D+W+S')]:
                        row['p ' + m] = b.get(m, np.nan)
                        row['rank ' + m] = int((grp_b[m] > b[m]).sum() + 1) if np.isfinite(b.get(m, np.nan)) else np.nan
                row['note'] = ''
                rows.append(row)
    return pd.DataFrame(rows)


def study4_reference(Wa, path, B):
    """Study 4 level forecasts (CatBoost D, and the naive) against 4b zero change and 4b CatBoost D on the same rows."""
    p = pathlib.Path(path)
    if not p.exists():
        return pd.DataFrame()
    f4 = pd.read_parquet(p)
    f4 = f4[(f4.group == 'seattle') & (f4.model == 'catboost') & (f4.fset == 'D') & f4.h.isin([1, 2])]
    f4 = f4.assign(err_study4_catboost_D=(f4.y_hat - f4.y_true).abs())[['format', 'node_id', 'origin_mi', 'h', 'err_study4_catboost_D']]
    m = Wa.merge(f4, on=['format', 'node_id', 'origin_mi', 'h']).dropna(subset=['err_zero', 'err_' + CB('D'), 'err_study4_catboost_D'])
    rows = []
    for h in (1, 2):
        for lab, s in EV.strata(m[m.h == h], B):
            rows.append(dict(h=h, **lab, n=len(s), mae_zero=s.err_zero.mean(), mae_study4_catboost_D_level=s.err_study4_catboost_D.mean(),
                             mae_4b_catboost_D_change=s['err_' + CB('D')].mean()))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--forecasts', default=str(ST.OUT / 'forecasts.parquet'))
    ap.add_argument('--features', default=str(ST.OUT / 'features.parquet'))
    ap.add_argument('--reports-dir', default=str(ST.REPORTS))
    ap.add_argument('--nodes', default=str(ST.DB / 'study3' / 'nodes.parquet'))
    ap.add_argument('--study4-forecasts', default=str(ST.S4_FORECASTS))
    a = ap.parse_args()
    B = ST.settings()
    rep = pathlib.Path(a.reports_dir); rep.mkdir(parents=True, exist_ok=True)
    Fc = pd.read_parquet(a.forecasts)
    F = pd.read_parquet(a.features)
    nodes = pd.read_parquet(a.nodes)
    Wa, ma = EV.wide_a(Fc)
    Wb, mb = EV.wide_b(Fc, B)
    csv = lambda df, name: df.to_csv(rep / f'study4b_{name}.csv', index=False)
    L = ['# Study 4b: forecasting the change in category demand and catching rare surges', '',
         f'Made {time.strftime("%Y-%m-%d %H:%M")}. 4b record SHA-256 `{B.sha256}`; Study 4 record `{B.sha256_study4}`. Forecast rows: {len(Fc):,} '
         f'from {Fc.origin.nunique()} origins ({Fc.origin.min()} to {Fc.origin.max()}). Seattle formats; print and ebook are primary, audiobook secondary. '
         'The target is the change in log share, d(t+h) - d(t); skill = 1 - MAE(new) / MAE(base), so a positive skill means the new model has the smaller error '
         '(the error of the level forecast equals the error of the change forecast). '
         f'DM is one-sided with Newey-West lag {B.dm_lag}; the bootstrap uses moving blocks of {B.boot_block} months, {B.boot_n:,} resamples, seed {B.boot_seed}, '
         f'{B.ci_level:.0%} percentile intervals. Interest helps if skill > 0, the interval is above zero and DM p < {B.helps_alpha}. '
         'Study 4b is a second, informed test (see the record), not a replication.', '']

    # ---------------- Part A ----------------
    tabs = []
    for h in B.horizons:
        for cls, base, new in A_PAIRS:
            if base in Wa and new in Wa:
                tabs.append(EV.compare_a(Wa, base, new, h, B, label=f'{cls} {new.split("|")[1]} vs {base.split("|")[1]}'))
    t_int = pd.concat(tabs, ignore_index=True)
    csv(t_int, 'a_interest_comparison')
    tz = []
    for h in B.horizons:
        for m in ma:
            if m != 'zero':
                tz.append(EV.compare_a(Wa, 'zero', m, h, B, label=f'{m} vs zero change'))
    t_zero = pd.concat(tz, ignore_index=True)
    csv(t_zero, 'a_vs_zero')
    t_mae = EV.mae_table(Wa, [m for m in ['zero'] + [RG(f) for f in B.feature_sets] + [CB(f) for f in B.feature_sets] if m in Wa], B)
    csv(t_mae, 'a_mae')
    prim = t_int[(t_int.h == B.h_primary)]
    L += [f'## Part A. Change forecasts, primary horizon {B.h_primary}', '',
          f'Test origins {B.test_start} to {Wa.origin.max()}. Main rule: CatBoost D+W (or D+W+S) against CatBoost D, print and ebook pooled at each level.', '', '### Verdicts', '']
    for lab in ('catboost D+W vs D', 'catboost D+W+S vs D'):
        L += verdict_lines(prim[prim.comparison == lab], 'A', lab)
    L += ['', 'Same comparisons per format (not the pooled verdict):', '']
    for lab in ('catboost D+W vs D', 'catboost D+W+S vs D'):
        for _, r in prim[(prim.comparison == lab) & prim.scope.str.startswith('format')].iterrows():
            L.append(f'- {lab}, {r.format}, {r.level}: {"helps" if r.helps else "does not help"} (skill {r.skill:.3f}, interval {r.ci_lo:.3f} to {r.ci_hi:.3f}, DM p {r.dm_p:.3f}).')
    L += ['', f'### Interest comparisons at horizon {B.h_primary}', '', md_table(prim, int_cols=('n', 'months')), '',
          '### Interest comparisons at horizons 1 and 3 (secondary), print and ebook pooled', '',
          md_table(t_int[(t_int.h != B.h_primary) & t_int.scope.str.startswith(EV.POOLED)], int_cols=('n', 'months')), '',
          '(All strata and horizons: `study4b_a_interest_comparison.csv`.)', '',
          '### Each model against zero change (print and ebook pooled)', '',
          md_table(t_zero[t_zero.scope.str.startswith(EV.POOLED)], int_cols=('n', 'months')), '',
          '(All strata: `study4b_a_vs_zero.csv`.)', '',
          '### MAE of every model on the same rows (change in log share)', '', md_table(t_mae, 4, int_cols=('n',)), '']

    # ---------------- Part B ----------------
    sm = [m for m in [CLF(f) for f in B.feature_sets] + [LOG(f) for f in B.feature_sets] if m in Wb]
    t_s = EV.surge_table(Wb, sm, B)
    csv(t_s, 'b_surge_metrics')
    t_ap = EV.ap_diff_table(Wb, [p for p in B_PAIRS if p[1] in Wb and p[2] in Wb], B)
    csv(t_ap, 'b_ap_difference')
    L += [f'## Part B. Surges at horizon {B.h_surge}', '',
          f'A surge is a change of log share of at least log({B.surge_ratio}) = {B.surge_change:.4f} at horizon {B.h_surge}. Average precision (AP) is primary; '
          f'a model with no skill has AP equal to the base rate. Recall: the share of surges that fall among the {B.top_k} highest-scored category-formats in their origin and format '
          f'(random ranking gives the "random" column). Brier: mean squared error of the probability; the last column is the Brier score of always forecasting the test base rate. '
          'Rows with no surge in a stratum are omitted from the bootstrap table.', '', '### Metrics', '', md_table(t_s, 4, int_cols=('n', 'surges', 'origins_with_surge')), '',
          '### AP difference with block bootstrap', '']
    for cls, base, new in B_PAIRS[:2] + B_PAIRS[3:5]:
        L += verdict_lines(t_ap[(t_ap.comparison == f'{new} vs {base}')], 'B', '')
    L += ['', md_table(t_ap, 4, int_cols=('surges',)), '']

    # ---------------- showcases and reference ----------------
    t_sh = showcases(Wa, Wb, F, nodes, B)
    csv(t_sh, 'showcases')
    L += ['## Showcases', '', 'Two cases named in the record (chosen knowing their Study 3 outcome; they are illustrations, not tests). Changes are in log share; '
          '"rank" is the position among the eligible category-formats of the same level, format and origin (1 = highest score). `s_resp` is the earlier-shift responsiveness.', '',
          md_table(t_sh, 3), '']
    t_ref = study4_reference(Wa, a.study4_forecasts, B)
    csv(t_ref, 'ref_study4_level')
    L += ['## Reference: Study 4 level forecasts on the same rows', '',
          'Study 4 forecast the level; its error against the zero-change forecast (the same as its naive) and against the 4b CatBoost D change model, on the rows both cover (horizons 1 and 2).', '',
          md_table(t_ref, 4, int_cols=('n',)), '']
    (rep / 'study4b_evaluation.md').write_text('\n'.join(L))
    print(f'wrote {rep / "study4b_evaluation.md"}')


if __name__ == '__main__':
    main()
