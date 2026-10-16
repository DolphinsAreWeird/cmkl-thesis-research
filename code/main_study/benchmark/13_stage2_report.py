# Method benchmark, stage 2: writes data/reports/benchmark_stage2.md from the result tables of 03_evaluate.py --stage2 (data/db/benchmark/stage2_results/).
# Tables only (numbers as computed); the reading of the results is written separately in the benchmark document.
#   ../../../.venv/bin/python 13_stage2_report.py
import sys, time, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import _settings as ST

RES = ST.DB / 'benchmark' / 'stage2_results'
REP = ST.DATA / 'reports' / 'benchmark_stage2.md'
ADD = json.loads((ST.PREREG / 'addenda_benchmark' / '2026-10-15_b_stage2_metrics_tasks_pipelines.json').read_text())


def f(x, d=3):
    if isinstance(x, (bool, np.bool_)):
        return 'yes' if x else 'no'
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ''
    if isinstance(x, (float, np.floating)):
        return f'{x:.{d}f}'
    return str(x)


def md(df, cols, heads=None, d=3, index_name='pipeline'):
    heads = heads or cols
    L = ['| ' + index_name + ' | ' + ' | '.join(heads) + ' |', '|' + ' --- |' * (len(cols) + 1)]
    for p, r in df.iterrows():
        L.append(f'| {p} | ' + ' | '.join(f(r[c], d) if c in r else '' for c in cols) + ' |')
    return '\n'.join(L) + '\n'


def ci(T, c, lo, hi, d=3):
    return T.apply(lambda r: f'{r[c]:.{d}f} ({r[lo]:.{d}f} to {r[hi]:.{d}f})' if pd.notna(r[c]) and pd.notna(r.get(lo)) else f(r[c], d), axis=1)


def sections_for(name, title, T, top=None):
    out = [f'### {title}', '']
    t = T.copy()
    # level task
    L = t.sort_values('AvgRelMAE')
    if top:
        L = L.head(top)
    L = L.assign(AvgRelMAE_ci=ci(L, 'AvgRelMAE', 'ci_lo', 'ci_hi'), VW_ci=ci(L, 'VW_AvgRelMAE', 'vw_lo', 'vw_hi'), RMSE_ci=ci(L, 'AvgRelRMSE', 'rmse_lo', 'rmse_hi'))
    out += ['**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)', '',
            md(L, ['AvgRelMAE_ci', 'median_rel', 'share_beats_naive', 'mean_rank', 'in_MCS_level', 'VW_ci', 'RMSE_ci'],
               ['AvgRelMAE (95%)', 'median ratio', 'share of series better than naive', 'mean rank', 'in confidence set', 'volume-weighted (95%)', 'relative RMSE (95%)'])]
    R = t.dropna(subset=['rho']).sort_values('rho', ascending=False)
    if top:
        R = R.head(top)
    R = R.assign(rho_ci=ci(R, 'rho', 'rho_lo', 'rho_hi'))
    out += ['**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)', '',
            md(R, ['rho_ci', 'rho_share_months_pos', 'in_MCS_rise'], ['Spearman (95%)', 'share of months above 0', 'in confidence set'])]
    S = t.dropna(subset=['AP']).sort_values('AP', ascending=False)
    if top:
        S = S.head(top)
    S = S.assign(AP_ci=ci(S, 'AP', 'AP_lo', 'AP_hi'))
    out += ['**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)', '',
            md(S, ['AP_ci', 'AP_lift', 'AP_tied_with_best'], ['average precision (95%)', 'lift', 'not distinguishable from the best'])]
    P = t.sort_values('mae_pct')
    if top:
        P = P.head(top)
    out += ['**Plain numbers** (pooled over all scored forecasts)', '',
            md(P, ['mae_pct', 'direction_acc', 'precision_top5pct'], ['mean absolute error (%)', 'direction right for moves above 10%', 'flagged top 5% that surge'])]
    return out


def main():
    meta = pd.read_csv(RES / 'meta.csv')
    L = ['# Method benchmark, stage 2', '',
         f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (SHA-256 9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22) '
         'and benchmark_settings_2026-10-15.json. Code: code/main_study/benchmark/ (03_evaluate.py --stage2). Result tables: data/db/benchmark/stage2_results/.',
         'AvgRelMAE is the geometric mean over series of MAE(pipeline) / MAE(repeat last month); intervals resample categories (2,000 draws); the confidence sets use the record settings; '
         'the Spearman and surge intervals resample months in blocks of 3.', '',
         '## Comparisons', '', meta.round(3).to_csv(index=False, sep='|').replace('|', ' | '), '']
    for k, title in (('A2', 'A2. Print and ebook, horizon 1 (main comparison)'), ('B2', 'B2. Print and ebook, horizon 2'), ('C2', 'C2. Print and ebook, horizon 3'),
                     ('A2_no_seasonal', 'A2 without the seasonal repeat (sensitivity, level task only)'), ('D2_h1', 'D2. Seattle audiobooks, horizon 1'),
                     ('D2_h2', 'D2. Seattle audiobooks, horizon 2'), ('D2_h3', 'D2. Seattle audiobooks, horizon 3'),
                     ('E2_h1', 'E2. LibriVox, horizon 1'), ('E2_h2', 'E2. LibriVox, horizon 2'),
                     ('S1_h1', 'Stage-1 roster alone, horizon 1, with the new metrics'), ('S1_h2', 'Stage-1 roster alone, horizon 2, with the new metrics')):
        p = RES / f'{k}_table.csv'
        if not p.exists():
            continue
        T = pd.read_csv(p, index_col=0)
        L += sections_for(k, title, T) if not k.startswith('A2_no') else [f'### {title}', '', md(T.sort_values('AvgRelMAE').assign(c=lambda d: ci(d, 'AvgRelMAE', 'ci_lo', 'ci_hi')), ['c', 'in_MCS_level', 'mean_rank'],
                                                                                                    ['AvgRelMAE (95%)', 'in confidence set', 'mean rank'])]
        pp = RES / f'{k}_pairs.csv'
        if pp.exists():
            P = pd.read_csv(pp)
            P['pair'] = P.base + ' -> ' + P.other
            P = P.set_index('pair')
            P['mae'] = P.apply(lambda r: f'{r.mae_ratio:.3f} ({r.mae_lo:.3f} to {r.mae_hi:.3f})', axis=1)
            P['rho'] = P.apply(lambda r: f'{r.rho_diff:+.3f} ({r.rho_diff_lo:+.3f} to {r.rho_diff_hi:+.3f})' if 'rho_diff' in r and pd.notna(r.get('rho_diff')) else '', axis=1)
            P['ap'] = P.apply(lambda r: f'{r.ap_diff:+.3f} ({r.ap_diff_lo:+.3f} to {r.ap_diff_hi:+.3f})' if 'ap_diff' in r and pd.notna(r.get('ap_diff')) else '', axis=1)
            L += [f'**Paired comparisons, model held fixed ({k})**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision', '',
                  md(P, ['kind', 'mae', 'share_series_better', 'rho', 'ap'], ['question', 'MAE ratio (95%)', 'share of series better', 'Spearman difference (95%)', 'surge AP difference (95%)'], index_name='pair')]
    sp = RES / 'segments.csv'
    if sp.exists():
        S = pd.read_csv(sp, index_col=0)
        L += ['## When: segments (print and ebook; segments with fewer than 20 series are not reported)', '']
        for seg, g in S.groupby('segment', sort=False):
            if 'AvgRelMAE' not in g:
                L += [f'### {seg}', '', g.dropna(axis=1, how='all').to_csv(index=False), '']
                continue
            g = g.dropna(subset=['AvgRelMAE']).sort_values('AvgRelMAE')
            if len(g) == 0:
                continue
            g = g.assign(c=ci(g, 'AvgRelMAE', 'ci_lo', 'ci_hi'))
            cols = ['c', 'VW_AvgRelMAE', 'AvgRelRMSE'] + [c for c in ('rho', 'AP') if c in g]
            L += [f'### {seg} ({int(g.series.iloc[0])} series, {int(g.rows.iloc[0])} forecasts)', '', md(g, cols, ['AvgRelMAE (95%)', 'volume-weighted', 'relative RMSE'] + [c for c in ('Spearman', 'surge AP') if c in g]), '']
    hp = RES / 'H2_table.csv'
    if hp.exists():
        Hh = pd.read_csv(hp, index_col=0)
        L += ['## By format and level (leaders of A2, horizon 1; node intervals)', '']
        for (fm, lv), g in Hh.groupby(['format', 'level'], sort=False):
            g = g.sort_values('AvgRelMAE').assign(c=ci(g.sort_values('AvgRelMAE'), 'AvgRelMAE', 'ci_lo', 'ci_hi'))
            L += [f'### {fm}, {lv} themes ({int(g.series.iloc[0])} series)', '', md(g, ['c', 'VW_AvgRelMAE', 'rho'], ['AvgRelMAE (95%)', 'volume-weighted', 'Spearman']), '']
    yp = RES / 'H3_by_year.csv'
    if yp.exists():
        Y = pd.read_csv(yp, index_col=0)
        piv = Y.reset_index(names='pipeline').pivot(index='pipeline', columns='year', values='AvgRelMAE')
        L += ['## By calendar year of the forecast origin (leaders of A2, horizon 1, AvgRelMAE)', '', md(piv.sort_values(piv.columns[0]), list(piv.columns), [str(c) for c in piv.columns]), '']
    for extra, head in (('benchmark_stage2_routing_coverage.md', 'Routing coverage (counts only)'), ('benchmark_stage2_nli_routing.md', 'Context-reading routing (outcome-free checks)'), ('benchmark_stage2_learned_categories.md', 'Categories learned from book text (structure)'), ('benchmark_stage2_learned.md', 'Categories learned from book text against subject-heading themes (scores)')):
        ep = ST.DATA / 'reports' / extra
        if ep.exists():
            L += [f'## {head}', '', f'See data/reports/{extra}.', '']
    REP.write_text('\n'.join(L) + '\n')
    print(f'wrote {REP}')


if __name__ == '__main__':
    main()
