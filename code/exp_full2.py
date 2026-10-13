# Full comparison: 4 feature stages x 9 models x 2 labels, grouped 5-fold CV repeated 3 times, cohort-adjusted labels.
import pandas as pd, numpy as np, json, sys, os, time, warnings, itertools
warnings.filterwarnings('ignore')
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge, PoissonRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import ndcg_score
from scipy.stats import spearmanr
import lightgbm as lgb
from catboost import CatBoostRegressor
from config import D
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet')
grp=json.load(open(f'{D}/processed/feature_groups.json'))
E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
m=L.merge(F,on='identifier').merge(pd.read_parquet(f'{D}/processed/features_goodreads.parquet'),on='identifier',how='left')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&(m.publicdate>='2016-07-01')].reset_index(drop=True)
EMB=E[m.emb_row.values]
W=grp['META']+grp['VOL']+grp['TREND']
STAGES={'S0 metadata':grp['META'],'S1 +wiki volume':grp['META']+grp['VOL'],'S2 +wiki trend':W,'S3 +goodreads':W+grp['GOODREADS'],'S4 +text':W+grp['GOODREADS']}
MODELS=['Median floor','Ridge','Count model','k-NN','Random forest','LightGBM','CatBoost','LambdaMART','Neural net']
def mat(cols,idx): return m.loc[idx,cols].fillna(0).values.astype(float)
def fit_predict(name,cols,text,tr,te,y,seed):
    Xtr,Xte=mat(cols,tr),mat(cols,te)
    if text:
        p=PCA(32,random_state=0).fit(EMB[tr]); Xtr=np.hstack([Xtr,p.transform(EMB[tr])]); Xte=np.hstack([Xte,p.transform(EMB[te])])
    ytr=y[tr]
    if name=='Median floor':
        med=pd.Series(ytr).groupby(m.genre1.values[tr]).median()
        return pd.Series(m.genre1.values[te]).map(med).fillna(np.median(ytr)).values
    if name in('Ridge','k-NN','Count model','Neural net'):
        sc=StandardScaler().fit(Xtr); Xtr,Xte=sc.transform(Xtr),sc.transform(Xte)
    if name=='Ridge': return Ridge(alpha=10).fit(Xtr,ytr).predict(Xte)
    if name=='Count model': return np.log(np.clip(PoissonRegressor(alpha=1e-3,max_iter=500).fit(Xtr,np.exp(ytr)).predict(Xte),1e-3,None))
    if name=='k-NN': return KNeighborsRegressor(25,weights='distance').fit(Xtr,ytr).predict(Xte)
    if name=='Random forest': return RandomForestRegressor(200,min_samples_leaf=5,n_jobs=-1,random_state=seed).fit(Xtr,ytr).predict(Xte)
    if name=='LightGBM': return lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=seed,verbose=-1).fit(Xtr,ytr).predict(Xte)
    if name=='CatBoost':
        a=pd.DataFrame(Xtr); b=pd.DataFrame(Xte)
        a['narr']=m.narrator_id.values[tr].astype(str); b['narr']=m.narrator_id.values[te].astype(str)
        a['g1']=m.genre1.values[tr]; b['g1']=m.genre1.values[te]
        return CatBoostRegressor(iterations=400,depth=6,learning_rate=0.05,verbose=0,random_seed=seed,cat_features=['narr','g1']).fit(a,ytr).predict(b)
    if name=='LambdaMART':
        rel=pd.qcut(ytr,10,labels=False,duplicates='drop').astype(int)
        o=np.random.RandomState(seed).permutation(len(tr)); groups=[min(100,len(tr)-i) for i in range(0,len(tr),100)]
        return lgb.LGBMRanker(n_estimators=400,learning_rate=0.05,num_leaves=31,min_child_samples=20,random_state=seed,verbose=-1).fit(Xtr[o],rel[o],group=groups).predict(Xte)
    if name=='Neural net': return MLPRegressor(hidden_layer_sizes=(64,32),alpha=1e-3,early_stopping=True,max_iter=400,random_state=seed).fit(Xtr,ytr).predict(Xte)
label=sys.argv[1]; reps=int(sys.argv[2]); out=f'{D}/reports/results2_{label}.csv'
y=m[label].values; t0=time.time()
start=int(os.environ.get('START','0')); rows=pd.read_csv(out).query('rep<@start').to_dict('records') if start and os.path.exists(out) else []
print('sample',len(m),'author wiki',int(m.wa_has.sum()),'book wiki',int(m.wb_has.sum()),flush=True)
for rep in range(start,reps):
    for fold,(tr,te) in enumerate(GroupKFold(5,shuffle=True,random_state=rep).split(m,groups=m.bookgroup)):
        for st,cols in STAGES.items():
            for name in MODELS:
                if name=='Median floor' and not st.startswith('S0'): continue
                p=fit_predict(name,cols,st.startswith('S4'),tr,te,y,rep*10+fold)
                rows.append(dict(label=label,rep=rep,fold=fold,stage=st,model=name,spearman=spearmanr(p,y[te]).correlation,ndcg100=ndcg_score([np.exp(y[te])],[p],k=100)))
        pd.DataFrame(rows).to_csv(out,index=False); print(label,rep,fold,round(time.time()-t0),'s',flush=True)
print('DONE',flush=True)
