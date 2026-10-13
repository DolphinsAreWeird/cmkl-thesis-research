# Walk-forward test with configurable label window and a wider model set.
# usage: python walkforward3.py START N MODE   (label = log views in months START..START+N-1 after release month)
#   MODE=robust : Ridge + LightGBM on all pre-release features only
#   MODE=full   : stages S0/S4/S5, models Ridge, LightGBM, CatBoost, LightGBM classifier, logistic, ensemble
#   MODE=early  : month 1 known; stages S5/S6, full model set (START must be >=2)
import pandas as pd, numpy as np, json, sys, os, warnings
warnings.filterwarnings('ignore')
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr, rankdata
import lightgbm as lgb
from catboost import CatBoostRegressor
from config import D; S,N,MODE=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet')
GR=pd.read_parquet(f'{D}/processed/features_goodreads.parquet'); grp=json.load(open(f'{D}/processed/feature_groups.json'))
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
m=L.merge(F,on='identifier').merge(GR,on='identifier',how='left')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&m.identifier.isin(V)&m.publicdate.notna()].copy()
m['rel_m']=m.publicdate.dt.tz_localize(None).dt.to_period('M'); last=pd.Period('2026-08','M')
# review fix 4: narrator catalogue size counted only from recordings released before this one (point in time)
allrec=L[['identifier','narrator_id','publicdate']].dropna().sort_values('publicdate')
allrec['narr_pit']=np.log1p(allrec.groupby('narrator_id').cumcount())
m=m.merge(allrec[['identifier','narr_pit']],on='identifier',how='left'); m['narr_count']=m.narr_pit.fillna(0)
def lab(r):
    if r.rel_m<pd.Period('2017-01','M') or r.rel_m+S+N-1>last: return np.nan
    return np.log1p(sum(V[r.identifier].get((r.rel_m+k).strftime('%Y%m'),0) for k in range(S,S+N)))
m['y']=m.apply(lab,axis=1); m=m.dropna(subset=['y']); m['label_end']=m.rel_m+S+N-1
m['month1']=m.apply(lambda r: np.log1p(V[r.identifier].get((r.rel_m+1).strftime('%Y%m'),0)),axis=1)
m=m.sort_values('rel_m').reset_index(drop=True)
for key,name in [('narrator_id','narr'),('author','auth'),('bookgroup','book')]:
    mean=np.full(len(m),np.nan); cnt=np.zeros(len(m))
    for k,g in m.groupby(key):
        e=g.label_end.values; ys=g.y.values
        for idx,r in zip(g.index,g.rel_m.values):
            ok=e<r
            if ok.any(): mean[idx]=ys[ok].mean(); cnt[idx]=ok.sum()
    m[f'{name}_prior']=mean; m[f'{name}_prior_n']=np.log1p(cnt); m[f'{name}_has_prior']=(cnt>0).astype(int)
HIST=[c for c in m.columns if c.endswith(('_prior','_prior_n','_has_prior'))]
EMB=E[m.emb_row.values]; W=grp['META']+grp['VOL']+grp['TREND']; G=grp['GOODREADS']
ALLST={'S0 metadata':(grp['META'],False),'S4 +social+text':(W+G,True),'S5 +history':(W+G+HIST,True),'S6 +month 1':(W+G+HIST+['month1'],True)}
if MODE=='robust': STAGES={k:ALLST[k] for k in ['S5 +history']}; MODELS=['Ridge','LightGBM']
elif MODE=='full': STAGES={k:ALLST[k] for k in ['S0 metadata','S4 +social+text','S5 +history']}; MODELS=['Ridge','LightGBM','CatBoost','LightGBM classifier','Logistic','Ensemble']
else: STAGES={k:ALLST[k] for k in ['S5 +history','S6 +month 1']}; MODELS=['Ridge','LightGBM','CatBoost','LightGBM classifier','Logistic','Ensemble']
rows=[]; out=f'{D}/reports/wf3fix_{MODE}_m{S}to{S+N-1}.csv'
for q in pd.period_range('2020Q1',(last-(S+N-1)).asfreq('Q'),freq='Q'):
    qs=q.asfreq('M','start'); te=m.index[(m.rel_m>=qs)&(m.rel_m<=q.asfreq('M','end'))]; tr=m.index[m.label_end<qs]
    if len(te)<30 or len(tr)<300: continue
    y=m.y.values; top=(y[te]>=np.quantile(y[te],0.8)).astype(int); ytr_top=(y[tr]>=np.quantile(y[tr],0.8)).astype(int)
    pca=PCA(32,random_state=0).fit(EMB[tr]); k=max(1,int(0.1*len(te)))
    for st,(cols,text) in STAGES.items():
        a=m.loc[tr,cols].fillna(0).values.astype(float); b=m.loc[te,cols].fillna(0).values.astype(float)
        if text: a=np.hstack([a,pca.transform(EMB[tr])]); b=np.hstack([b,pca.transform(EMB[te])])
        sc=StandardScaler().fit(a); P={}
        P['Ridge']=Ridge(10).fit(sc.transform(a),y[tr]).predict(sc.transform(b))
        P['LightGBM']=lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=0,verbose=-1).fit(a,y[tr]).predict(b)
        if MODE!='robust':
            ca=pd.DataFrame(a); cb=pd.DataFrame(b)
            if st in ('S5 +history','S6 +month 1'):   # review fix 5: narrator identity only where narrator history is allowed
                ca['narr']=m.narrator_id.values[tr].astype(str); cb['narr']=m.narrator_id.values[te].astype(str)
            ca['g1']=m.genre1.values[tr]; cb['g1']=m.genre1.values[te]
            P['CatBoost']=CatBoostRegressor(iterations=400,depth=6,learning_rate=0.05,verbose=0,random_seed=0,cat_features=[c for c in ['narr','g1'] if c in ca.columns]).fit(ca,y[tr]).predict(cb)
            P['LightGBM classifier']=lgb.LGBMClassifier(n_estimators=400,learning_rate=0.03,num_leaves=15,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=0,verbose=-1).fit(a,ytr_top).predict_proba(b)[:,1]
            P['Logistic']=LogisticRegression(C=0.3,max_iter=2000).fit(sc.transform(a),ytr_top).predict_proba(sc.transform(b))[:,1]
            P['Ensemble']=np.mean([rankdata(P[x]) for x in ['Ridge','LightGBM','CatBoost','LightGBM classifier','Logistic']],axis=0)
        for mdl,p in P.items():
            o=np.argsort(-p)[:k]; base_rate=(y[te]>=np.quantile(y[te],0.9)).mean()
            rows.append(dict(quarter=str(q),n_test=len(te),stage=st,model=mdl,spearman=spearmanr(p,y[te]).correlation,auc_top20=roc_auc_score(top,p),hit_rate_top10=(y[te][o]>=np.quantile(y[te],0.9)).mean(),hit_base=base_rate))
    pd.DataFrame(rows).to_csv(out,index=False); print(MODE,S,N,q,flush=True)
print('DONE',out,flush=True)
