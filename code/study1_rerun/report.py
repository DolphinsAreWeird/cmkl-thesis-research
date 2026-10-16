"""Build data/reports/study1_reruns_*.csv from the old and new outputs."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, numpy as np
from config import D
R=f'{D}/reports'
# 1 launch window
rows=[]
for s,n in [(1,3),(2,3),(1,6),(2,6),(1,12),(2,12),(3,6)]:
    e=s+n-1; row=dict(first_month=s,months=n,window=f'{s}-{e}',includes_month1=int(s==1))
    for tag,f in [('old',f'wf3_robust_m{s}to{e}.csv'),('new',f'wf3fix_robust_m{s}to{e}.csv')]:
        d=pd.read_csv(f'{R}/{f}'); d=d[d.model=='Ridge']
        row[f'{tag}_auc_ridge']=d.auc_top20.mean(); row[f'{tag}_quarters']=d.quarter.nunique()
        l=pd.read_csv(f'{R}/{f}'); l=l[l.model=='LightGBM']; row[f'{tag}_auc_lgbm']=l.auc_top20.mean()
    rows.append(row)
w=pd.DataFrame(rows).round(3); w.to_csv(f'{R}/study1_reruns_1_launch_window.csv',index=False); print(w.to_string())
# 2 after launch
o=pd.read_csv(f'{R}/wf3_early_m2to7.csv'); n=pd.read_csv(f'{R}/wf3fix_early_m2to7.csv')
def agg(d): return d.groupby(['stage','model'])[['auc_top20','hit_rate_top10','spearman']].mean()
a=agg(o).join(agg(n),lsuffix='_old',rsuffix='_new').round(3); a['quarters_old']=o.quarter.nunique(); a['quarters_new']=n.quarter.nunique()
a.to_csv(f'{R}/study1_reruns_2_after_launch.csv'); print(a.to_string())
# 3 experiment 1
out=[]
for lab in ['y_view','y_fav']:
    for tag,f in [('old',f'results2_{lab}.csv'),('new',f'results3fix_{lab}.csv')]:
        r=pd.read_csv(f'{R}/{f}'); g=r.groupby(['model','stage']).spearman.mean().reset_index(); g['label']=lab; g['run']=tag; g['folds']=r.groupby(['rep','fold']).ngroups; out.append(g)
mean=pd.concat(out); mean.round(4).to_csv(f'{R}/study1_reruns_3_exp1_spearman.csv',index=False)
rng=np.random.RandomState(0); res=[]
for lab in ['y_view','y_fav']:
    for tag,f in [('old',f'results2_{lab}.csv'),('new',f'results3fix_{lab}.csv')]:
        r=pd.read_csv(f'{R}/{f}'); stg=sorted(r.stage.unique())
        for mdl,g in r[r.model!='Median floor'].groupby('model'):
            p=g.pivot_table(index=['rep','fold'],columns='stage',values='spearman')
            for x,y in zip(stg[:-1],stg[1:]):
                d=(p[y]-p[x]).values; bs=[rng.choice(d,len(d)).mean() for _ in range(2000)]
                res.append(dict(label=lab,run=tag,model=mdl,step=f'{x[:2]}->{y[:2]}',gain=d.mean(),ci_lo=np.percentile(bs,2.5),ci_hi=np.percentile(bs,97.5)))
G=pd.DataFrame(res); G.round(4).to_csv(f'{R}/study1_reruns_3_exp1_gains.csv',index=False)
G['sig']=G.ci_lo>0; print(G.groupby(['label','run','step']).agg(mean_gain=('gain','mean'),n_sig=('sig','sum'),n_pos=('gain',lambda x:(x>0).sum())).round(4).to_string())
so=json.load(open(f'{R}/shapley_sources.json'))['shapley']; sn=json.load(open(f'{R}/shapley3fix_sources.json'))['shapley']
S=pd.DataFrame({'old':so,'new':sn}).round(4); S.to_csv(f'{R}/study1_reruns_3_shapley.csv'); print(S)
