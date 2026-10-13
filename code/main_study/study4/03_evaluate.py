# Step 03: evaluation of the forecasts. Main comparison (CatBoost D+W against CatBoost D), helps-rule verdicts, secondary
# metrics, conditional split, horizon 2, GDELT and tone comparisons, LibriVox, showcases.
# Reads data/db/study4/forecasts.parquet and features.parquet; writes data/reports/study4_03_evaluation.md and CSVs.
#   .venv/bin/python 03_evaluate.py [--forecasts F] [--features F] [--reports-dir D]
import sys, time, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _settings as ST
import _eval as EV
from _eval import CB_D, CB_DW, md_table


def showcase_tables(W, F, nodes, S):
    rows = []
    for case in S.showcases:
        hit = nodes[nodes.label.str.lower() == case['label'].lower()]
        if hit.empty:
            hit = nodes[nodes.label.str.lower().str.contains(case['label'].lower(), regex=False)]
        for _, nd in hit.iterrows():
            if nd.level not in S.levels:
                continue
            for fmt in case['formats']:
                for o in case['origins']:
                    mi = ST.mi_from_ym(o)
                    d = W[(W.node_id == nd.node_id) & (W.format == fmt) & (W.origin_mi == mi) & (W.h == 1)]
                    base = dict(category=nd.label, level=nd.level, node_id=nd.node_id, format=fmt, origin=o, target=ST.ym_of(mi + 1))
                    if d.empty:
                        rows.append({**base, 'note': 'not forecast at this origin (below the size rule, or a month missing)'})
                        continue
                    r = d.iloc[0]
                    rows.append({**base, 'last_log_share': r.y_t, 'naive': r['naive'], 'catboost_D': r[CB_D], 'catboost_D+W': r[CB_DW],
                                 'ridge_D': r.get('ridge|D', np.nan), 'ridge_D+W': r.get('ridge|D+W', np.nan), 'actual': r.y_true,
                                 'interest_ratio_to_normal': r.w_ratio, 'shift_in_last_8_weeks': r.w_shift8,
                                 'abs_err_D': r['err_' + CB_D], 'abs_err_D+W': r['err_' + CB_DW], 'note': ''})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--forecasts', default=str(ST.OUT / 'forecasts.parquet'))
    ap.add_argument('--features', default=str(ST.OUT / 'features.parquet'))
    ap.add_argument('--reports-dir', default=str(ST.REPORTS))
    ap.add_argument('--nodes', default=str(ST.DB / 'study3' / 'nodes.parquet'))
    a = ap.parse_args()
    S = ST.settings()
    rep = pathlib.Path(a.reports_dir); rep.mkdir(parents=True, exist_ok=True)
    Fc = pd.read_parquet(a.forecasts)
    F = pd.read_parquet(a.features)
    nodes = pd.read_parquet(a.nodes)
    W, models = EV.wide_forecasts(Fc, F)
    csv = lambda df, name: df.to_csv(rep / f'study4_03_{name}.csv', index=False)
    L = ['# Study 4, step 03: evaluation', '',
         f'Made {time.strftime("%Y-%m-%d %H:%M")}. Record SHA-256 `{S.sha256}`. Forecasts: {len(Fc):,} rows from '
         f'{Fc.origin.nunique()} origins ({Fc.origin.min()} to {Fc.origin.max()}). Skill = 1 - MAE(new) / MAE(base); '
         'a positive skill means the new model has the smaller error. Errors are on the log-share scale. '
         'Only category-format-months with an observed target month and an observed month t are scored.', '']
    need = [CB_D, CB_DW]
    miss = [m for m in need if m not in models]
    if miss:
        raise SystemExit(f'forecasts lack {miss}: run 02_forecast.py first')
    sea = W[W.group == 'seattle']
    main1 = sea[sea.h == 1].dropna(subset=need)

    # ---- main comparison
    t_main = EV.comparison_table(main1, CB_D, CB_DW, S)
    csv(t_main, 'main_comparison')
    L += ['## 1. Main comparison: CatBoost D+W against CatBoost D, horizon 1 (Seattle)', '',
          f'Test origins {main1.origin.min()} to {main1.origin.max()}. Bootstrap: moving blocks of {S.boot_block} months, '
          f'{S.boot_n:,} resamples, seed {S.boot_seed}, {S.ci_level:.0%} percentile interval. DM: one-sided, Newey-West lag {S.dm_lag}.', '',
          md_table(t_main, int_cols=('n', 'months')), '']
    base_models = [m for m in ['naive', 'seasonal_naive', 'ridge|D', 'ridge|D+W', CB_D, CB_DW] if m in models]
    t_base = EV.baseline_table(main1, base_models)
    csv(t_base, 'baselines')
    L += ['### MAE of every model on the same rows', '', md_table(t_base, 4, int_cols=('n',)), '']

    # ---- helps rule
    L += ['## 2. Helps-rule verdicts (horizon 1)', '',
          f'Interest helps if skill > 0, the {S.ci_level:.0%} bootstrap interval is above zero and DM p < {S.helps_alpha}. '
          'The overall verdict uses all formats pooled at each level.', '']
    pooled = t_main[t_main.scope == 'formats pooled']
    for _, r in pooled.iterrows():
        L.append(f'- Overall, {r.level} level: **{"interest helps" if r.helps else "interest does not help"}** '
                 f'(skill {r.skill:.3f}, interval {r.ci_lo:.3f} to {r.ci_hi:.3f}, DM p {r.dm_p:.3f}).')
    for _, r in t_main[t_main.scope == 'format x level'].iterrows():
        L.append(f'- {r.format}, {r.level}: {"helps" if r.helps else "does not help"} (skill {r.skill:.3f}, DM p {r.dm_p:.3f}).')
    L.append('')

    # ---- secondary
    sec_models = [m for m in ['ridge|D', 'ridge|D+W', CB_D, CB_DW] if m in models]
    t_sec = EV.secondary_table(main1, sec_models, S)
    csv(t_sec, 'secondary')
    L += ['## 3. Secondary metrics (horizon 1)', '',
          'MASE: MAE divided by the seasonal naive MAE (below 1 beats it). Spearman: across categories within each month and '
          f'format, forecast change against actual change, averaged over months (groups of fewer than {EV.M.MIN_GROUP} categories skipped). '
          f'Top-10% hit rate: base rate {S.top_share:.0%}. Direction accuracy: category-months with |actual change| > {S.direction_min}.', '',
          md_table(t_sec), '']

    # ---- conditional
    t_cond = EV.conditional_table(main1, CB_D, CB_DW, S)
    csv(t_cond, 'conditional')
    L += ['## 4. Conditional split: shift months and other months (horizon 1)', '',
          f'"Shift months": a quality-ok Wikipedia interest shift started in the {S.cond_shift_weeks} weeks before the origin. '
          'The quality flag only splits the scoring; it is never a feature.', '', md_table(t_cond, int_cols=('n', 'months')), '']

    # ---- horizon 2
    main2 = sea[sea.h == 2].dropna(subset=need)
    t_h2 = EV.comparison_table(main2, CB_D, CB_DW, S) if len(main2) else pd.DataFrame()
    csv(t_h2, 'horizon2')
    L += ['## 5. Horizon 2 (target month t+2, same information)', '', md_table(t_h2, int_cols=('n', 'months')), '']

    # ---- GDELT and tone
    g_models = ['catboost|D+W+G', 'catboost|D+W+G+T']
    L += ['## 6. GDELT and tone, over the shorter period', '']
    if all(m in models for m in g_models):
        gd = sea[sea.h == 1].dropna(subset=[CB_D, CB_DW] + g_models)
        L += [f'Origins {gd.origin.min()} to {gd.origin.max()} ({len(gd):,} rows). Only categories GDELT covers have GDELT features; '
              'the others carry missing values in the G and T sets.', '']
        pairs = [('D+W against D (same period)', CB_D, CB_DW), ('D+W+G against D+W (adds GDELT volume)', CB_DW, 'catboost|D+W+G'),
                 ('D+W+G+T against D+W+G (adds tone)', 'catboost|D+W+G', 'catboost|D+W+G+T'),
                 ('D+W+G+T against D+W (GDELT volume and tone)', CB_DW, 'catboost|D+W+G+T')]
        gt = []
        for name, b, n in pairs:
            t = EV.comparison_table(gd, b, n, S)
            t.insert(0, 'comparison', name)
            gt.append(t)
        t_g = pd.concat(gt, ignore_index=True)
        csv(t_g, 'gdelt_tone')
        L += [md_table(t_g, int_cols=('n', 'months')), '',
              'Rows restricted to categories with GDELT series:', '']
        cov = gd[gd.node_id.isin(set(F[F.g_ratio.notna()].node_id))]
        gt2 = []
        for name, b, n in pairs[1:3]:
            t = EV.comparison_table(cov, b, n, S)
            t.insert(0, 'comparison', name)
            gt2.append(t)
        t_g2 = pd.concat(gt2, ignore_index=True)
        csv(t_g2, 'gdelt_tone_covered')
        L += [md_table(t_g2, int_cols=('n', 'months')), '']
    else:
        L += ['_(no D+W+G forecasts in the file)_', '']

    # ---- LibriVox
    lib = W[(W.group == 'librivox') & (W.h == 1)]
    L += ['## 7. LibriVox (secondary series, reported separately)', '']
    if len(lib) and CB_D in lib and CB_DW in lib:
        lib = lib.dropna(subset=need)
        t_lib = EV.comparison_table(lib, CB_D, CB_DW, S)
        csv(t_lib, 'librivox')
        L += [md_table(t_lib, int_cols=('n', 'months')), '']
    else:
        L += ['_(no LibriVox forecasts)_', '']

    # ---- showcases
    t_show = showcase_tables(sea, F, nodes, S)
    csv(t_show, 'showcases')
    L += ['## 8. Showcase cases (examples chosen knowing their Study 3 outcome; not tests)', '',
          'Log shares; the target month is the month after the origin. "interest ratio" is the last week against its 26-week median.', '',
          md_table(t_show, 3), '']
    (rep / 'study4_03_evaluation.md').write_text('\n'.join(L))
    print(f'wrote {rep / "study4_03_evaluation.md"}')


if __name__ == '__main__':
    main()
