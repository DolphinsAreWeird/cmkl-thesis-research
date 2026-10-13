# Study 2: event study of attention bursts, spillover, and hidden-book monthly forecasts.
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
import lightgbm as lgb
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from config import D
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); PV=json.load(open(f'{D}/raw/wiki_pageviews_monthly.json'))
T={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly_to2026.json'))['items']}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); L=pd.read_parquet(f'{D}/processed/labels.parquet')
lk=lk.merge(L[['identifier','genre1']],on='identifier',how='left')
lm=[p.strftime('%Y%m') for p in pd.period_range('2017-01','2026-08',freq='M')]
am=[p.strftime('%Y%m') for p in pd.period_range('2015-07','2025-06',freq='M')]
# ---- book-level series: listening summed over a book's recordings; attention = book article, else author article
books=[]
for bg,g in lk[lk.n_authors==1].groupby('bookgroup'):
    art=g.wiki_book.dropna().iloc[0] if g.wiki_book.notna().any() else None; src='book'
    if not art or art.replace(' ','_') not in PV: art=g.wiki_author.dropna().iloc[0] if g.wiki_author.notna().any() else None; src='author'
    if not art or art.replace(' ','_') not in PV or not PV[art.replace(' ','_')]: continue
    s=PV[art.replace(' ','_')]; a=np.array([s.get(k,0)/T[k]*1e6 for k in am])
    lis=np.array([sum(V.get(i,{}).get(k,0) for i in g.identifier) for k in lm],float)
    rel=g.publicdate.min()
    books.append(dict(bg=bg,author=g.author.iloc[0],title=g.title.iloc[0],genre=g.genre1.iloc[0],src=src,art=art,att=a,lis=lis,rels=list(g.publicdate.dropna())))
print('books with attention + listening',len(books),'| book-level attention',sum(b['src']=='book' for b in books))
# market index: median listening across all books per month (log)
M=np.median(np.log1p(np.array([b['lis'] for b in books])),axis=0)
# ---- burst detection on attention
PVraw=lambda art,ym: PV[art.replace(' ','_')].get(ym,0)
li=lambda ym: lm.index(ym) if ym in lm else None
events=[]
for b in books:
    a=b['att']
    for t in range(12,len(am)):
        base=np.median(a[t-12:t])
        if base>0 and a[t]>=2.5*base and a[t]==a[max(0,t-2):t+3].max():
            ym=am[t]; j=li(ym)
            if j is None or j<6 or j+6>=len(lm): continue
            win=pd.Period(ym,'M')
            if any(abs((pd.Period(r.strftime('%Y-%m'),'M')-win).n)<=8 for r in b['rels']): continue   # skip new-recording launches
            if j<12 or b['lis'][j-12:j-1].mean()<20: continue
            y=np.log1p(b['lis']); kk=np.arange(-12,-1); co=np.polyfit(kk,y[j-12:j-1],1)   # book's own pre-burst trend
            resp=[y[j+k]-np.polyval(co,k) for k in range(-6,7)]
            rawv=PVraw(b['art'],ym)
            events.append(dict(bg=b['bg'],title=b['title'],author=b['author'],src=b['src'],month=ym,ratio=a[t]/base,raw=rawv,resp=resp))
E=pd.DataFrame(events); print('bursts',len(E),'books',E.bg.nunique())
R=np.array(E.resp.tolist()); rng=np.random.RandomState(0)
bs=np.array([R[rng.randint(0,len(R),len(R))].mean(0) for _ in range(2000)])
es=pd.DataFrame({'k':range(-6,7),'mean_excess_pct':(np.exp(R.mean(0))-1)*100,'lo':(np.exp(np.percentile(bs,2.5,0))-1)*100,'hi':(np.exp(np.percentile(bs,97.5,0))-1)*100})
groups={'book article, >=3x, >=20k views':(E.src=='book')&(E.ratio>=3)&(E.raw>=20000),'book article':E.src=='book','author article':E.src=='author'}
for lab,sub in groups.items():
    es[lab]=(np.exp(R[sub.values].mean(0))-1)*100; print(lab,'n=',int(sub.sum()))
strong=R[groups['book article, >=3x, >=20k views'].values]
bs2=np.array([strong[rng.randint(0,len(strong),len(strong))].mean(0) for _ in range(2000)])
es['strong_lo']=(np.exp(np.percentile(bs2,2.5,0))-1)*100; es['strong_hi']=(np.exp(np.percentile(bs2,97.5,0))-1)*100
es.to_csv(f'{D}/reports/study2_event_response_detrended.csv',index=False); print(es.round(1).to_string(index=False))

E.to_pickle(f'{D}/interim/study2_events_detrended.pkl')
print(E[(E.src=='book')&(E.ratio>=3)&(E.raw>=20000)].sort_values('ratio',ascending=False).head(8)[['title','month','ratio','raw']].to_string())
