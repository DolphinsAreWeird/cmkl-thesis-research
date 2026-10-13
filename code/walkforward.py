# Time-based evaluation: labels from listening in the first N months after release (Internet Archive daily views),
# models trained only on recordings whose label window had closed before each test quarter, tested quarter by quarter.
import pandas as pd, numpy as np, json, sys, warnings
warnings.filterwarnings('ignore')
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
import lightgbm as lgb
from catboost import CatBoostRegressor
from config import D; N=int(sys.argv[1]) if len(sys.argv)>1 else 6
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet')
GR=pd.read_parquet(f'{D}/processed/features_goodreads.parquet'); grp=json.load(open(f'{D}/processed/feature_groups.json'))
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
m=L.merge(F,on='identifier').merge(GR,on='identifier',how='left')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&m.identifier.isin(V)].copy()
m['rel_m']=m.publicdate.dt.tz_localize(None).dt.to_period('M')
last=pd.Period('2026-08','M')
def firstN(r):
    s=V[r.identifier]; months=[(r.rel_m+k).strftime('%Y%m') for k in range(1,N+1)]
    if r.rel_m<pd.Period('2017-01','M') or r.rel_m+N>last: return np.nan
    return np.log1p(sum(s.get(k,0) for k in months))
m['y']=m.apply(firstN,axis=1); m=m.dropna(subset=['y']).reset_index(drop=True)
m['label_end']=m.rel_m+N
EMB=E[m.emb_row.values]
W=grp['META']+grp['VOL']+grp['TREND']
STAGES={'S0 metadata':(grp['META'],False),'S2 +wiki':(W,False),'S3 +goodreads':(W+grp['GOODREADS'],False),'S4 +text':(W+grp['GOODREADS'],True)}
def X(cols,idx,text,pca):
    a=m.loc[idx,cols].fillna(0).values.astype(float)
    return np.hstack([a,pca.transform(EMB[idx])]) if text else a
rows=[]
quarters=pd.period_range('2020Q1',(last-N).asfreq('Q'),freq='Q')
for q in quarters:
    qs=q.asfreq('M','start'); te=m.index[(m.rel_m>=qs)&(m.rel_m<=q.asfreq('M','end'))]
    tr=m.index[m.label_end<qs]
    if len(te)<30 or len(tr)<300: continue
    y=m.y.values; top=(y[te]>=np.quantile(y[te],0.8)).astype(int)
    pca=PCA(32,random_state=0).fit(EMB[tr])
    med=m.loc[tr].groupby('genre1').y.median(); fl=m.loc[te,'genre1'].map(med).fillna(np.median(y[tr])).values
    preds={('S0 metadata','Median floor'):fl}
    for st,(cols,text) in STAGES.items():
        a,b=X(cols,tr,text,pca),X(cols,te,text,pca)
        sc=StandardScaler().fit(a)
        preds[(st,'Ridge')]=Ridge(10).fit(sc.transform(a),y[tr]).predict(sc.transform(b))
        preds[(st,'LightGBM')]=lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=0,verbose=-1).fit(a,y[tr]).predict(b)
        ca=pd.DataFrame(a); cb=pd.DataFrame(b); ca['narr']=m.narrator_id.values[tr].astype(str); cb['narr']=m.narrator_id.values[te].astype(str); ca['g1']=m.genre1.values[tr]; cb['g1']=m.genre1.values[te]
        preds[(st,'CatBoost')]=CatBoostRegressor(iterations=400,depth=6,learning_rate=0.05,verbose=0,random_seed=0,cat_features=['narr','g1']).fit(ca,y[tr]).predict(cb)
    k=max(1,int(0.1*len(te)))
    for (st,mdl),p in preds.items():
        order=np.argsort(-p)[:k]
        rows.append(dict(quarter=str(q),n_test=len(te),n_train=len(tr),stage=st,model=mdl,spearman=spearmanr(p,y[te]).correlation,
            auc_top20=roc_auc_score(top,p),hit_rate_top10=(y[te][order]>=np.quantile(y[te],0.9)).mean()))
    pd.DataFrame(rows).to_csv(f'{D}/reports/walkforward_first{N}m.csv',index=False); print(q,len(tr),len(te),flush=True)
print('DONE',flush=True)
