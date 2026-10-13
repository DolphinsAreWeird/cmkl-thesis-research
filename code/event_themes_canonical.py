# Finer society themes (from attention items only), books mapped onto them, and an event-based test:
# when a theme rises strongly in a month, do its books gain listeners over the next 3 months, compared with random books that month?
import pandas as pd, numpy as np, json, urllib.parse
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from config import D; O=f'{D}/db'
items=pd.read_parquet(f'{O}/items.parquet'); obs=pd.read_parquet(f'{O}/observations.parquet'); AE=np.load(f'{D}/interim/top_article_emb.npy')
L=pd.read_parquet(f'{O}/listening.parquet'); B=json.load(open(f'{D}/interim/book_themes.json')); books=B['books']; BE=np.load(f'{D}/interim/book_emb_by_group.npy')
title=pd.read_parquet(f'{O}/books.parquet').set_index('book_id').title
# keep only topics a book could be about: drop people, sport, films, TV, music and games (by their Wikipedia description)
import re
PEOPLE_MEDIA=re.compile(r'\b(born|actor|actress|singer|rapper|musician|footballer|player|athlete|wrestler|golfer|racing driver|comedian|youtuber|model|politician|businessman|businesswoman|film|television|tv series|season|episode|album|song|single|band|video game|game|tournament|championship|league|season|sports|olympic|award|cup|club|team|streamer|influencer|personality)\b',re.I)
keep=~items.text.str.split(':',n=1).str[1].fillna('').str.contains(PEOPLE_MEDIA)
print('topic items kept:',int(keep.sum()),'of',len(items),flush=True)
items=items[keep].reset_index(drop=True); AE=AE[keep.values]
K=200; km=MiniBatchKMeans(K,random_state=0,batch_size=4096,n_init=3).fit(AE); C=km.cluster_centers_/np.linalg.norm(km.cluster_centers_,axis=1,keepdims=True)
tf=TfidfVectorizer(stop_words='english',token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',min_df=2).fit(items.text); Xt=tf.transform(items.text); voc=np.array(tf.get_feature_names_out())
labels=[', '.join(voc[np.argsort(-np.asarray(Xt[km.labels_==k].mean(0)).ravel())[:4]]) for k in range(K)]
# book-to-theme: cosine to the theme centre, keep strong links only (top 2% of all book-theme pairs)
S=BE@C.T; cut=np.quantile(S,0.999); Wb=np.where(S>=cut,S-cut,0)
n_books=(Wb>0).sum(0); print('themes with at least 5 linked books:',int((n_books>=3).sum()),'of',K,flush=True)
# theme momentum: share of the month's top-page attention held by the theme, vs its median over the previous 12 months
ix=pd.Series(range(len(items)),index=items.item_id).reindex(obs.item_id); obs=obs[ix.notna().values].copy(); obs['theme']=km.labels_[ix.dropna().astype(int).values]
lev=obs.groupby(['period','theme']).share.sum().unstack(fill_value=0).sort_index()
per=list(lev.index); LV=lev.reindex(columns=range(K),fill_value=0).values+1e-6
MOM=np.full_like(LV,np.nan)
for i in range(12,len(per)): MOM[i]=np.log(LV[i]/np.median(LV[i-12:i],axis=0))
# listening, market-adjusted change over the next 3 months vs the previous 12; launches excluded
Lw=L.pivot(index='book_id',columns='period',values='listens').reindex(books); lper=list(Lw.columns); LL=np.log1p(Lw.values); MK=np.median(LL,axis=0)
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
relm={str(k):[x.tz_localize(None).to_period('M') for x in v.publicdate.dropna()] for k,v in lk.groupby('bookgroup')}
rng=np.random.RandomState(0); ev=[]
for i,p in enumerate(per):
    if i<12 or p not in lper: continue
    j=lper.index(p)
    if j<12 or j+3>=len(lper): continue
    P=pd.Period(p,'M'); base=np.median(LL[:,j-12:j],axis=1); y=(LL[:,j+1:j+4].mean(1)-base)-(MK[j+1:j+4].mean()-np.median(MK[j-12:j]))
    ok=(np.expm1(base)>=5)&np.array([not any(-8<=(P-r).n<=3 for r in relm.get(b,[])) for b in books])
    for k in np.where((MOM[i]>=np.log(3))&(n_books>=3))[0]:
        bsk=np.where((Wb[:,k]>0)&ok)[0]
        if len(bsk)<3: continue
        bsk=bsk[np.argsort(-Wb[bsk,k])][:5]; obs_y=y[bsk].mean()
        pool=np.where(ok)[0]; null=np.array([y[rng.choice(pool,len(bsk),replace=False)].mean() for _ in range(300)])
        ev.append(dict(month=p,theme=k,label=labels[k],momentum=round(float(np.exp(MOM[i,k])),1),n_books=len(bsk),
                       excess=float(np.exp(obs_y-np.median(null))),pct=float((null<obs_y).mean()),books=[title.get(books[b],'') for b in bsk[:4]],
                       pages=[urllib.parse.unquote(items.item_id.values[q][5:]).replace('_',' ') for q in np.where(km.labels_==k)[0][np.argsort(-AE[km.labels_==k]@C[k])][:3]]))
E=pd.DataFrame(ev); E.to_csv(f'{D}/reports/theme_events_canonical.csv',index=False)
print('theme-month events (theme at least 3x its normal, 5+ linked books):',len(E),'| distinct themes',E.theme.nunique())
print('median excess listening vs random books:',round(E.excess.median(),3),'| share of events beating random median:',round((E.pct>0.5).mean(),2),'| share in top 10% of random draws:',round((E.pct>0.9).mean(),2),'(chance 0.10)')
for lo,hi in [(3,5),(5,10),(10,1e9)]:
    s=E[(E.momentum>=lo)&(E.momentum<hi)]; print(f'momentum {lo}-{hi}x: n={len(s)} median excess {s.excess.median():.3f} share>random {(s.pct>0.5).mean():.2f} top10% {(s.pct>0.9).mean():.2f}')
print(E.sort_values('excess',ascending=False).head(12)[['month','label','momentum','excess','pct','books','pages']].to_string(index=False))
json.dump(dict(labels=labels),open(f'{D}/db/fine_theme_labels.json','w'))
np.save(f'{D}/db/fine_theme_centroids.npy',C)
