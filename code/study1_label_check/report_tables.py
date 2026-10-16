# Builds the tables for data/reports/study1_label_check.md from the saved CSVs (no model fitting). Run from code/.
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import D
R = f'{D}/reports'; P = f'{R}/study1_label_check'
q = pd.read_csv(f'{P}_quarters.csv'); t = pd.read_csv(f'{P}_titles.csv'); old = pd.read_csv(f'{R}/wf3fix_full_m2to7.csv')
old = old[old.model.isin(['Ridge', 'CatBoost'])].assign(label='old run (log of summed views, months 2-7)')
MET = ['auc_top20', 'spearman', 'hit_rate_top10']
def md(df, nd=3):
    df = df.reset_index() if df.index.name or isinstance(df.index, pd.MultiIndex) else df
    h = '| ' + ' | '.join(map(str, df.columns)) + ' |\n|' + '---|' * len(df.columns) + '\n'
    return h + '\n'.join('| ' + ' | '.join(f'{v:.{nd}f}' if isinstance(v, float) else str(v) for v in r) + ' |' for r in df.values)
out = {}
a = pd.concat([q, old]); a['stage'] = pd.Categorical(a.stage, ['S0 metadata', 'S4 +social+text', 'S5 +history'], ordered=True)
out['means'] = md(a.groupby(['label', 'model', 'stage'], observed=True)[MET + ['hit_base']].mean().assign(quarters=a.groupby(['label', 'model', 'stage'], observed=True).quarter.nunique()))
# label correlations
c = pd.read_csv(f'{P}_label_corr_by_quarter.csv'); cm = c.groupby('label')[['L0', 'L2', 'L3', 'L4']].mean()
out['corr_q'] = md(cm)
pool = t[['L0', 'L2', 'L3', 'L4']].corr(method='spearman'); out['corr_pool'] = md(pool)
# top-20% overlap between labels (per quarter, share of one label's top-20% titles also in the other's)
ov = []
for qq, g in t.groupby('quarter'):
    top = {k: set(g.identifier[g[k] >= g[k].quantile(0.8)]) for k in ['L0', 'L2', 'L3', 'L4']}
    for x in top:
        for y in top:
            if x < y: ov.append(dict(pair=f'{x} vs {y}', share=len(top[x] & top[y]) / len(top[x])))
out['overlap'] = md(pd.DataFrame(ov).groupby('pair').share.mean().to_frame('share of top 20% in common'))
# source gains
g = a.pivot_table(index=['label', 'model', 'quarter'], columns='stage', values=MET[:2], observed=True)
rows = []
for (lab, mdl), d in g.groupby(level=[0, 1]):
    for met in MET[:2]:
        for name, hi, lo in [('S4 - S0 (social + text)', 'S4 +social+text', 'S0 metadata'), ('S5 - S4 (history)', 'S5 +history', 'S4 +social+text'), ('S5 - S0 (all)', 'S5 +history', 'S0 metadata')]:
            x = d[(met, hi)] - d[(met, lo)]
            rows.append(dict(label=lab, model=mdl, metric=met, step=name, mean_gain=x.mean(), quarters_positive=f'{int((x > 0).sum())}/{len(x)}'))
G = pd.DataFrame(rows); out['gains'] = md(G.pivot_table(index=['model', 'step', 'metric'], columns='label', values='mean_gain', sort=False))
out['gains_pos'] = md(G.pivot_table(index=['model', 'step', 'metric'], columns='label', values='quarters_positive', aggfunc='first', sort=False))
# launch strength
t['tier'] = pd.qcut(t.L4, 4, labels=['Q1 lowest L4', 'Q2', 'Q3', 'Q4 highest L4'])
def desc(by):
    d = t.groupby(by, observed=True).launch_strength.agg(n='size', mean='mean', median='median', p10=lambda x: x.quantile(.1), p90=lambda x: x.quantile(.9), share_above_0=lambda x: (x > 0).mean())
    return md(d)
out['launch_tier'] = desc('tier'); out['launch_year'] = desc('year')
out['launch_corr'] = f"{t.launch_strength.corr(t.L4, method='spearman'):.3f}"
out['zero_share'] = md(t.groupby('tier', observed=True).agg(median_views_m1_12=('views_m1_12', 'median'), share_under_100_views=('views_m1_12', lambda x: (x < 100).mean()), mean_slope_beta=('beta4', 'mean')))
p = pd.read_csv(f'{P}_l4_params.csv'); out['params'] = md(p[['quarter', 'n_train', 'theta', 'sigma_beta']].iloc[[0, 4, 9, 14, 19]])
out['n_test'] = f"{t.shape[0]} test titles over {t.quarter.nunique()} quarters"
for k, v in out.items(): print(f'## {k}\n{v}\n')
base = os.path.dirname(os.path.abspath(__file__))
out['interpretation'] = open(f'{base}/interpretation.txt').read().strip(); out['notinrecord'] = open(f'{base}/notinrecord.txt').read().strip()
tpl = open(f'{base}/report_template.md').read()
for k, v in out.items(): tpl = tpl.replace('{{' + k + '}}', str(v))
open(f'{R}/study1_label_check.md', 'w').write(tpl); print('written report')
