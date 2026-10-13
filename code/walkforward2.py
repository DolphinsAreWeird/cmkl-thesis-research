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
m=m.sort_values('rel_m').reset_index(drop=True)
def prior(key):
    mean=np.full(len(m),np.nan); cnt=np.zeros(len(m))
    for k,g in m.groupby(key):
        ends=g.label_end.values; rel=g.rel_m.values; ys=g.y.values
        for idx,r in zip(g.index,rel):
            ok=ends<r
            if ok.any(): mean[idx]=ys[ok].mean(); cnt[idx]=ok.sum()
    return mean,cnt
for key,name in [('narrator_id','narr'),('author','auth'),('bookgroup','book')]:
    a,c=prior(key); m[f'{name}_prior']=a; m[f'{name}_prior_n']=np.log1p(c); m[f'{name}_has_prior']=(c>0).astype(int)
HIST=[c for c in m.columns if c.endswith(('_prior','_prior_n','_has_prior'))]
EARLY=None
if len(sys.argv)>2 and sys.argv[2]=='early':
    # after-launch scenario: month 1 listening is known, predict months 2..N+1
    def m1(r): return np.log1p(V[r.identifier].get((r.rel_m+1).strftime('%Y%m'),0))
    def rest(r):
        if r.rel_m+N+1>last: return np.nan
        return np.log1p(sum(V[r.identifier].get((r.rel_m+k).strftime('%Y%m'),0) for k in range(2,N+2)))
    m['month1']=m.apply(m1,axis=1); m['y']=m.apply(rest,axis=1); m=m.dropna(subset=['y']).reset_index(drop=True); m['label_end']=m.rel_m+N+1
    EARLY=['month1']
EMB=E[m.emb_row.values]
W=grp['META']+grp['VOL']+grp['TREND']
STAGES={'S0 metadata':(grp['META'],False),'S2 +wiki':(W,False),'S3 +goodreads':(W+grp['GOODREADS'],False),'S4 +text':(W+grp['GOODREADS'],True),'S5 +history':(W+grp['GOODREADS']+HIST,True)}
if EARLY: STAGES={'S5 +history':STAGES['S5 +history'],'S6 +month 1':(W+grp['GOODREADS']+HIST+EARLY,True)}
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
    preds={('S0 metadata','Median floor'):fl} if not EARLY else {}
    for st,(cols,text) in STAGES.items():
        a,b=X(cols,tr,text,pca),X(cols,te,text,pca)
        sc=StandardScaler().fit(a)
        preds[(st,'Ridge')]=Ridge(10).fit(sc.transform(a),y[tr]).predict(sc.transform(b))
        preds[(st,'LightGBM')]=lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=0,verbose=-1).fit(a,y[tr]).predict(b)
        if __import__('os').environ.get('CAT')!='1': continue
        ca=pd.DataFrame(a); cb=pd.DataFrame(b); ca['narr']=m.narrator_id.values[tr].astype(str); cb['narr']=m.narrator_id.values[te].astype(str); ca['g1']=m.genre1.values[tr]; cb['g1']=m.genre1.values[te]
        preds[(st,'CatBoost')]=CatBoostRegressor(iterations=400,depth=6,learning_rate=0.05,verbose=0,random_seed=0,cat_features=['narr','g1']).fit(ca,y[tr]).predict(cb)
    k=max(1,int(0.1*len(te)))
    for (st,mdl),p in preds.items():
        order=np.argsort(-p)[:k]
        rows.append(dict(quarter=str(q),n_test=len(te),n_train=len(tr),stage=st,model=mdl,spearman=spearmanr(p,y[te]).correlation,
            auc_top20=roc_auc_score(top,p),hit_rate_top10=(y[te][order]>=np.quantile(y[te],0.9)).mean()))
    pd.DataFrame(rows).to_csv(f'{D}/reports/walkforward_first{N}m'+('_early' if EARLY else '')+'.csv',index=False); print(q,len(tr),len(te),flush=True)
print('DONE',flush=True)
