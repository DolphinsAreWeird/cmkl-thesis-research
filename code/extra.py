import pandas as pd, numpy as np, warnings, itertools, sys
warnings.filterwarnings('ignore')
from sklearn.model_selection import GroupKFold
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import spearmanr
import lightgbm as lgb
from catboost import CatBoostRegressor
m=pd.read_pickle('sample_adj.pkl').reset_index(drop=True)
b=pd.read_pickle('base2.pkl'); b['emb_idx']=np.arange(len(b))
m=m.merge(b[['identifier','emb_idx']],on='identifier',how='left')
E=np.load('emb.npy')[m.emb_idx.values]
G=[c for c in m.columns if c.startswith('g_')]
M=['log_hours','log_sections','narr_count']+G; W=['log_wiki','has_wiki']
def X(cols,tr,te,text):
    a=m.loc[tr,cols].values.astype(float) if cols else np.zeros((len(tr),0)); c=m.loc[te,cols].values.astype(float) if cols else np.zeros((len(te),0))
    if text:
        p=PCA(32,random_state=0).fit(E[tr]); a=np.hstack([a,p.transform(E[tr])]); c=np.hstack([c,p.transform(E[te])])
    return a,c
def lgbm(seed): return lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=seed,verbose=-1)
task=sys.argv[1]
rows=[]
if task=='shapley':
    players=['M','W','T']
    for rep in range(3):
        for fold,(tr,te) in enumerate(GroupKFold(5,shuffle=True,random_state=rep).split(m,groups=m.bookgroup)):
            for k in range(1,4):
                for S in itertools.combinations(players,k):
                    cols=(M if 'M' in S else [])+(W if 'W' in S else [])
                    a,c=X(cols,tr,te,'T' in S)
                    p=lgbm(rep).fit(a,m.y.values[tr]).predict(c)
                    rows.append(dict(rep=rep,fold=fold,S=''.join(S),sp=spearmanr(p,m.y.values[te]).correlation))
            print('fold',rep,fold,flush=True)
    r=pd.DataFrame(rows); r.to_csv('shapley_runs.csv',index=False)
    v=r.groupby('S').sp.mean().to_dict(); v['']=0.0
    from math import factorial
    n=3; key=lambda S:''.join(p for p in players if p in S)
    for i in players:
        others=[p for p in players if p!=i]; phi=0
        for k in range(0,3):
            for S in itertools.combinations(others,k):
                w=factorial(len(S))*factorial(n-len(S)-1)/factorial(n)
                phi+=w*(v[key(set(S)|{i})]-v[key(S)])
        print('Shapley',i,round(phi,4))
    print({k:round(x,4) for k,x in v.items()})
if task=='wikisub':
    s=m[m.has_wiki==1].reset_index(drop=True); m=s
    for rep in range(3):
        for fold,(tr,te) in enumerate(GroupKFold(5,shuffle=True,random_state=rep).split(m,groups=m.bookgroup)):
            for st,cols in [('v0',M),('v1',M+['log_wiki'])]:
                a=m.loc[tr,cols].values.astype(float); c=m.loc[te,cols].values.astype(float); y=m.y.values[tr]
                sc=StandardScaler().fit(a)
                preds={'Ridge':Ridge(10).fit(sc.transform(a),y).predict(sc.transform(c)),
                       'Random forest':RandomForestRegressor(200,min_samples_leaf=5,random_state=rep).fit(a,y).predict(c),
                       'LightGBM':lgbm(rep).fit(a,y).predict(c)}
                for k,p in preds.items(): rows.append(dict(rep=rep,fold=fold,stage=st,model=k,sp=spearmanr(p,m.y.values[te]).correlation))
    r=pd.DataFrame(rows); r.to_csv('wikisub_runs.csv',index=False)
    print('n',len(m)); print(r.groupby(['model','stage']).sp.mean().unstack().round(4))
    d=r.pivot_table(index=['model','rep','fold'],columns='stage',values='sp'); d['gain']=d.v1-d.v0
    print(d.groupby('model').gain.agg(['mean',lambda x:(x>0).mean()]).round(4))
if task=='favorites':
    m['cohort']=m.publicdate.dt.year.astype(str)+'H'+((m.publicdate.dt.month>6)+1).astype(str)
    yf=np.log1p(m.favorites/m.days_since_published*365); yf=yf-m.assign(t=yf).groupby('cohort').t.transform('median')
    for rep in range(3):
        for fold,(tr,te) in enumerate(GroupKFold(5,shuffle=True,random_state=rep).split(m,groups=m.bookgroup)):
            for st,cols,text in [('v0',M,False),('v1',M+W,False),('v2',M+W,True)]:
                a,c=X(cols,tr,te,text); y=yf.values[tr]; sc=StandardScaler().fit(a)
                preds={'Ridge':Ridge(10).fit(sc.transform(a),y).predict(sc.transform(c)),
                       'Random forest':RandomForestRegressor(200,min_samples_leaf=5,random_state=rep).fit(a,y).predict(c),
                       'LightGBM':lgbm(rep).fit(a,y).predict(c)}
                for k,p in preds.items(): rows.append(dict(rep=rep,fold=fold,stage=st,model=k,sp=spearmanr(p,yf.values[te]).correlation))
        print('rep',rep,flush=True)
    r=pd.DataFrame(rows); r.to_csv('fav_runs.csv',index=False)
    print(r.groupby(['model','stage']).sp.mean().unstack().round(4))
    d=r.pivot_table(index=['model','rep','fold'],columns='stage',values='sp'); d['g1']=d.v1-d.v0; d['g2']=d.v2-d.v1
    print(d.groupby('model')[['g1','g2']].agg(['mean',lambda x:(x>0).mean()]).round(4))
