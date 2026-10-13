import pandas as pd, numpy as np, json, ast, warnings, time, sys
warnings.filterwarnings('ignore')
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge, PoissonRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import ndcg_score, mean_squared_error
from scipy.stats import spearmanr
import lightgbm as lgb
from catboost import CatBoostRegressor

m=pd.read_pickle('base2.pkl')
E=np.load('emb.npy')
amap=json.load(open('author_wiki.json')); pvs=json.load(open('author_pv.json'))
m['emb_idx']=np.arange(len(m))
# sample: single named author, released >= Jul 2016 (12 months of page-view history before release)
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&(m.publicdate>='2016-07-01')].copy()
def prerel(row):
    t=amap.get(row.author); s=pvs.get(t) if t else None
    if not s: return np.nan
    rel=row.publicdate; months=pd.period_range(rel-pd.DateOffset(months=12),rel-pd.DateOffset(months=1),freq='M')
    v=[s.get(p.strftime('%Y%m')) for p in months]; v=[x for x in v if x is not None]
    return np.mean(v) if v else np.nan
m['wiki_pre']=m.apply(prerel,axis=1)
m['has_wiki']=m.wiki_pre.notna().astype(int)
m['log_wiki']=np.log1p(m.wiki_pre.fillna(0))
m['y']=np.log(m.views/m.days_since_published)
m['rate']=m.views/m.days_since_published
# metadata
def hrs(s):
    try: h,mi,se=[int(x) for x in str(s).split(':')]; return h+mi/60+se/3600
    except: return np.nan
m['log_hours']=np.log1p(m.totaltime.map(hrs).fillna(1))
m['log_sections']=np.log1p(m.num_sections)
m['log_age']=np.log(m.days_since_published)
m['narr_count']=np.log1p(m.groupby('narrator_id').narrator_id.transform('count'))
gc=m.genre_categories.map(lambda s: ast.literal_eval(s) if isinstance(s,str) else [])
top=pd.Series([g for l in gc for g in l]).value_counts().index[:20]
for g in top: m['g_'+g]=gc.map(lambda l: int(g in l))
m['genre1']=gc.map(lambda l: l[0] if l else 'None')
G=['g_'+g for g in top]
V0=['log_hours','log_sections','log_age','narr_count']+G
V1=V0+['log_wiki','has_wiki']
m=m.reset_index(drop=True)
print('sample',len(m),'with wiki',m.has_wiki.sum(), file=sys.stderr)
EMB=E[m.emb_idx.values]

def feats(stage,tr,te):
    cols=V0 if stage=='v0' else V1
    Xtr=m.loc[tr,cols].values.astype(float); Xte=m.loc[te,cols].values.astype(float)
    if stage=='v2':
        p=PCA(32,random_state=0).fit(EMB[tr]); Xtr=np.hstack([Xtr,p.transform(EMB[tr])]); Xte=np.hstack([Xte,p.transform(EMB[te])])
    return Xtr,Xte

def fit_predict(name,stage,tr,te,seed):
    Xtr,Xte=feats(stage,tr,te); ytr=m.y.values[tr]
    if name=='Median floor':
        med=m.loc[tr].groupby('genre1').y.median(); gm=np.median(ytr)
        return m.loc[te,'genre1'].map(med).fillna(gm).values
    if name in('Ridge','k-NN','Count model','Neural net'):
        sc=StandardScaler().fit(Xtr); Xtr,Xte=sc.transform(Xtr),sc.transform(Xte)
    if name=='Ridge': return Ridge(alpha=10).fit(Xtr,ytr).predict(Xte)
    if name=='Count model':
        r=PoissonRegressor(alpha=1e-3,max_iter=500).fit(Xtr,m.rate.values[tr],sample_weight=m.days_since_published.values[tr]/1000)
        return np.log(np.clip(r.predict(Xte),1e-3,None))
    if name=='k-NN': return KNeighborsRegressor(25,weights='distance').fit(Xtr,ytr).predict(Xte)
    if name=='Random forest': return RandomForestRegressor(200,min_samples_leaf=5,n_jobs=-1,random_state=seed).fit(Xtr,ytr).predict(Xte)
    if name=='LightGBM': return lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=seed,verbose=-1).fit(Xtr,ytr).predict(Xte)
    if name=='CatBoost':
        ctr=pd.DataFrame(Xtr); cte=pd.DataFrame(Xte)
        ctr['narr']=m.narrator_id.values[tr].astype(str); cte['narr']=m.narrator_id.values[te].astype(str)
        ctr['g1']=m.genre1.values[tr]; cte['g1']=m.genre1.values[te]
        cb=CatBoostRegressor(iterations=400,depth=6,learning_rate=0.05,verbose=0,random_seed=seed,cat_features=['narr','g1'],thread_count=-1)
        return cb.fit(ctr,ytr).predict(cte)
    if name=='LambdaMART':
        rel=pd.qcut(ytr,10,labels=False,duplicates='drop').astype(int)
        rng=np.random.RandomState(seed); order=rng.permutation(len(tr)); gs=100
        groups=[min(gs,len(tr)-i) for i in range(0,len(tr),gs)]
        rk=lgb.LGBMRanker(n_estimators=400,learning_rate=0.05,num_leaves=31,min_child_samples=20,random_state=seed,verbose=-1)
        rk.fit(Xtr[order],rel[order],group=groups); return rk.predict(Xte)
    if name=='Neural net': return MLPRegressor(hidden_layer_sizes=(64,32),alpha=1e-3,early_stopping=True,max_iter=400,random_state=seed).fit(Xtr,ytr).predict(Xte)

MODELS=['Median floor','Ridge','Count model','k-NN','Random forest','LightGBM','CatBoost','LambdaMART','Neural net']
STAGES=['v0','v1','v2']
rows=[]; t0=time.time()
for rep in range(int(__import__('os').environ.get('REPS','1'))):
    gkf=GroupKFold(n_splits=5,shuffle=True,random_state=rep)
    for fold,(tr,te) in enumerate(gkf.split(m,groups=m.bookgroup)):
        yte=m.y.values[te]; rte=m.rate.values[te]
        for st in STAGES:
            for name in MODELS:
                if name=='Median floor' and st!='v0': continue
                p=fit_predict(name,st,tr,te,rep*10+fold)
                rows.append(dict(rep=rep,fold=fold,stage=st,model=name,
                    spearman=spearmanr(p,yte).correlation,
                    ndcg100=ndcg_score([rte],[p],k=100),
                    rmse=np.nan if name=='LambdaMART' else mean_squared_error(yte,p)**0.5))
        pd.DataFrame(rows).to_csv('results.csv',index=False)
        print(f'rep {rep} fold {fold} done {round(time.time()-t0)}s',file=sys.stderr,flush=True)
res=pd.DataFrame(rows); res.to_csv('results.csv',index=False)
m.drop(columns=['emb_idx']).to_pickle('sample.pkl')
print('done',round(time.time()-t0),file=sys.stderr)
