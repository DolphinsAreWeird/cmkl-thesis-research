# Test the adaptation-calendar method against the attention-shape model.
import pandas as pd, numpy as np, json, requests, time, lightgbm as lgb, urllib.parse
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from config import D, UA; H={"User-Agent":UA}
A=pd.read_csv(f'{D}/raw/wikidata_adaptations.csv'); A=A[A.type!='literary work']; A['date']=pd.to_datetime(A.date)
T={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly_to2026.json'))['items']}
weeks=pd.date_range('2017-01-02','2026-08-24',freq='W-MON')
def wk(d): 
    s=pd.Series({pd.Timestamp(k[:8]):v for k,v in d.items()},dtype=float)
    return s.resample('W-MON',label='left',closed='left').sum().reindex(weeks).fillna(0)/np.array([T[w.strftime('%Y%m')] for w in weeks])*1e9
adv={}
for a in A.ad_art.unique():
    r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/20160701/20260831",headers=H,timeout=30)
    if r.status_code==200: adv[a]=wk({x['timestamp']:x['views'] for x in r.json()['items']})
    time.sleep(0.9)
print('adaptation series',len(adv))
def ad_feats(book_art):
    sub=A[A.book_art==book_art]; n=len(weeks)
    wto=np.full(n,np.nan); wsince=np.full(n,np.nan); adlev=np.full(n,np.nan); adr=np.full(n,np.nan)
    if sub.empty: return wto,wsince,adlev,adr
    ad_sum=sum(adv[a].values for a in sub.ad_art if a in adv) if any(a in adv for a in sub.ad_art) else np.zeros(n)
    for t,w in enumerate(weeks):
        fut=[(d-w).days/7 for d in sub.date if 0<=(d-w).days/7<=52]; past=[(w-d).days/7 for d in sub.date if 0<(w-d).days/7<=52]
        if fut: wto[t]=min(fut)
        if past: wsince[t]=min(past)
        adlev[t]=np.log1p(ad_sum[t]); base=np.median(ad_sum[max(0,t-26):t]) if t>0 else 0
        adr[t]=np.log((ad_sum[t]+1)/(base+1))
    return wto,wsince,adlev,adr
S=json.load(open(f'{D}/interim/weekly_scope.json')); M=pd.DataFrame(S['map'])
P=pd.read_pickle(f'{D}/interim/weekly_lift_panel.pkl')
bg2art=M.drop_duplicates('bookgroup').set_index('bookgroup').art
widx={w:i for i,w in enumerate(weeks)}
for c in ['wto','wsince','adlev','adr']: P[c]=np.nan
for bg,g in P.groupby('bg'):
    art=bg2art.get(bg)
    if art not in set(A.book_art): continue
    f=ad_feats(art); ix=[widx[w] for w in g.week]
    for c,v in zip(['wto','wsince','adlev','adr'],f): P.loc[g.index,c]=v[ix]
SHAPE=['r0','r1','r4','rmax8','n15','tau','slope','level','cal']; ADAPT=SHAPE+['wto','wsince','adlev','adr']
for name,fs in [('shape',SHAPE),('shape+adaptation',ADAPT)]:
    P['q_'+name]=np.nan
    for f in range(5):
        m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=100,verbose=-1,random_state=0).fit(P.loc[P.f!=f,fs],P.loc[P.f!=f,'y'])
        P.loc[P.f==f,'q_'+name]=m.predict(P.loc[P.f==f,fs])
big=(P.y>np.log(1.5)).astype(int); near=P.wto.notna()|P.wsince.notna(); hot=P.r0>np.log(2)
res={}
for name in ['shape','shape+adaptation']:
    p=P['q_'+name]
    res[name]={'auc_all':round(roc_auc_score(big,p),3),'auc_hot':round(roc_auc_score(big[hot],p[hot]),3),
               'auc_near_adaptation':round(roc_auc_score(big[near],p[near]),3) if big[near].nunique()>1 else None,'spearman_near':round(spearmanr(p[near],P.y[near]).correlation,3)}
res['book_weeks_near_adaptation']=int(near.sum()); res['books_with_adaptation']=int(P[near].bg.nunique())
print(json.dumps(res,indent=1)); json.dump(res,open(f'{D}/reports/adaptation_test.json','w'),indent=1)
# event study around adaptation release dates (listening vs own trend), books in panel
ev=[]
for bg,g in P[near].groupby('bg'):
    pass
# final model on all rows for the case studies
mdl={n:lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=100,verbose=-1,random_state=0).fit(P[fs],P.y) for n,fs in [('shape',SHAPE),('shape+adaptation',ADAPT)]}
import pickle; pickle.dump((mdl,adv),open(f'{D}/interim/adapt_models.pkl','wb'))
