import pandas as pd, numpy as np, sys
f=sys.argv[1]; r=pd.read_csv(f)
print(f, 'rows',len(r), 'folds', r.groupby(['rep','fold']).ngroups)
t=r.groupby(['model','stage']).spearman.mean().unstack().round(3)
t['n']=r[r.stage=='v0'].groupby('model').size()
print(t.sort_values('v0',ascending=False).to_string())
rng=np.random.RandomState(0)
out=[]
for mdl,g in r[r.model!='Median floor'].groupby('model'):
    p=g.pivot_table(index=['rep','fold'],columns='stage',values='spearman')
    for a,b in [('v0','v1'),('v1','v2')]:
        d=(p[b]-p[a]).values
        bs=[rng.choice(d,len(d)).mean() for _ in range(2000)]
        out.append(dict(model=mdl,step=f'{a}->{b}',mean_gain=round(d.mean(),4),share_pos=round((d>0).mean(),2),ci_lo=round(np.percentile(bs,2.5),4),ci_hi=round(np.percentile(bs,97.5),4)))
o=pd.DataFrame(out); print(o.pivot(index='model',columns='step',values='mean_gain').to_string())
print(o.to_string())
