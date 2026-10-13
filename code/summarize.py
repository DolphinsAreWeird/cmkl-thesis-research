import pandas as pd, numpy as np, json, os
from config import D; rng=np.random.RandomState(0); lines=[]
for lab in ['y_view','y_fav']:
    f=f'{D}/reports/results_{lab}.csv'
    if not os.path.exists(f): continue
    r=pd.read_csv(f); lines.append(f'===== {lab}: {r.groupby(["rep","fold"]).ngroups} test folds')
    lines.append(r.groupby(['model','stage']).spearman.mean().unstack().round(3).to_string())
    stg=sorted(r.stage.unique()); res=[]
    for mdl,g in r[r.model!='Median floor'].groupby('model'):
        p=g.pivot_table(index=['rep','fold'],columns='stage',values='spearman')
        for a,b in zip(stg[:-1],stg[1:]):
            d=(p[b]-p[a]).values; bs=[rng.choice(d,len(d)).mean() for _ in range(2000)]
            res.append(dict(model=mdl,step=f'{a[:2]}->{b[:2]}',gain=d.mean(),share_better=(d>0).mean(),ci_lo=np.percentile(bs,2.5),ci_hi=np.percentile(bs,97.5)))
    o=pd.DataFrame(res); o.to_csv(f'{D}/reports/gains_{lab}.csv',index=False)
    lines.append(o.pivot(index='model',columns='step',values='gain').round(4).to_string())
    lines.append('models with CI above zero per step: '+str(o.assign(sig=o.ci_lo>0).groupby('step').sig.sum().to_dict()))
if os.path.exists(f'{D}/reports/shapley_sources.json'): lines.append('Shapley (y_view, LightGBM): '+json.dumps(json.load(open(f'{D}/reports/shapley_sources.json'))['shapley']))
open(f'{D}/reports/summary.txt','w').write('\n'.join(lines)); print('\n'.join(lines))
