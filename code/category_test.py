# Category-level test: does a rising theme lift TOTAL listening across its books (pooled), not single books?
import pandas as pd, numpy as np, json, re
from sklearn.cluster import MiniBatchKMeans
from scipy.stats import spearmanr
from config import D; O=f'{D}/db'
items=pd.read_parquet(f'{O}/items.parquet'); obs=pd.read_parquet(f'{O}/observations.parquet'); AE=np.load(f'{D}/interim/top_article_emb.npy')
L=pd.read_parquet(f'{O}/listening.parquet'); B=json.load(open(f'{D}/interim/book_themes.json')); books=B['books']; BE=np.load(f'{D}/interim/book_emb_by_group.npy')
PM=re.compile(r'\b(born|actor|actress|singer|rapper|musician|footballer|player|athlete|wrestler|golfer|racing driver|comedian|youtuber|model|politician|businessman|businesswoman|film|television|tv series|season|episode|album|song|single|band|video game|game|tournament|championship|league|sports|olympic|award|cup|club|team|streamer|influencer|personality)\b',re.I)
keep=~items.text.str.split(':',n=1).str[1].fillna('').str.contains(PM); items=items[keep].reset_index(drop=True); AE=AE[keep.values]
K=200; km=MiniBatchKMeans(K,random_state=0,batch_size=4096,n_init=3).fit(AE); C=km.cluster_centers_/np.linalg.norm(km.cluster_centers_,axis=1,keepdims=True)
S=BE@C.T; Wb=S>=np.quantile(S,0.995)
ix=pd.Series(range(len(items)),index=items.item_id).reindex(obs.item_id); obs=obs[ix.notna().values].copy(); obs['theme']=km.labels_[ix.dropna().astype(int).values]
lev=obs.groupby(['period','theme']).share.sum().unstack(fill_value=0).reindex(columns=range(K),fill_value=0).sort_index(); per=list(lev.index); LV=lev.values+1e-6
A=np.full_like(LV,np.nan)
for i in range(12,len(per)): A[i]=np.log(LV[i]/np.median(LV[i-12:i],axis=0))
Lw=L.pivot(index='book_id',columns='period',values='listens').reindex(books); lper=list(Lw.columns); X=Lw.values.astype(float)
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
rel={str(k):[x.tz_localize(None).to_period('M') for x in v.publicdate.dropna()] for k,v in lk.groupby('bookgroup')}
P=[pd.Period(p,'M') for p in lper]
launch=np.array([[any(-3<=(p-r).n<=8 for r in rel.get(b,[])) for p in P] for b in books])   # month p is within a launch window of this book
X=np.where(launch,np.nan,X)
tot=np.nansum(X,axis=0)
rows=[]
nb=Wb.sum(0)
for k in np.where(nb>=5)[0]:
    sub=X[Wb[:,k]]; share=np.log(np.nansum(sub,axis=0)+1)-np.log(tot)     # theme's share of all listening
    for i,p in enumerate(per):
        if p not in lper or np.isnan(A[i,k]): continue
        j=lper.index(p)
        if j<12 or j+3>=len(lper): continue
        rows.append(dict(theme=k,month=p,att=A[i,k],d1=share[j+1]-np.median(share[j-12:j]),d3=share[j+1:j+4].mean()-np.median(share[j-12:j]),d0=share[j]-np.median(share[j-12:j])))
R=pd.DataFrame(rows).dropna()
def stats(R,col):
    pooled=spearmanr(R.att,R[col]).correlation
    within=R.groupby('theme').apply(lambda g: spearmanr(g.att,g[col]).correlation if len(g)>12 else np.nan).dropna()
    hi=R.att>=np.log(3); diff=np.exp(R[col][hi].mean()-R[col][~hi].mean())
    return dict(pooled_spearman=round(float(pooled),3),mean_within_theme=round(float(within.mean()),3),share_themes_positive=round(float((within>0).mean()),2),
                theme_listening_when_attention_3x_vs_other_months=round(float(diff),3),n_hi=int(hi.sum()))
rng=np.random.RandomState(0); Rp=R.copy()
Rp['att']=R.groupby('theme').att.transform(lambda s: np.roll(s.values,rng.randint(12,36)))
out={'themes':int((nb>=5).sum()),'theme_months':len(R)}
for col,nm in [('d0','same month'),('d1','next month'),('d3','next 3 months')]:
    out[nm]=dict(real=stats(R,col),placebo=stats(Rp,col))
print(json.dumps(out,indent=1)); json.dump(out,open(f'{D}/reports/category_test.json','w'),indent=1); R.to_parquet(f'{O}/category_panel.parquet')
