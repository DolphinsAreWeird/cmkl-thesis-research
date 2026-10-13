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
            pre=np.log1p(b['lis'][j-6:j-1]).mean()
            if b['lis'][j-6:j-1].mean()<20: continue
            resp=[(np.log1p(b['lis'][j+k])-pre)-(M[j+k]-M[j-6:j-1].mean()) for k in range(-6,7)]
            events.append(dict(bg=b['bg'],title=b['title'],author=b['author'],src=b['src'],month=ym,ratio=a[t]/base,resp=resp))
E=pd.DataFrame(events); print('bursts',len(E),'books',E.bg.nunique())
R=np.array(E.resp.tolist()); rng=np.random.RandomState(0)
bs=np.array([R[rng.randint(0,len(R),len(R))].mean(0) for _ in range(2000)])
es=pd.DataFrame({'k':range(-6,7),'mean_excess_pct':(np.exp(R.mean(0))-1)*100,'lo':(np.exp(np.percentile(bs,2.5,0))-1)*100,'hi':(np.exp(np.percentile(bs,97.5,0))-1)*100})
for lab,sub in [('big bursts (>=5x)',E.ratio>=5),('book article',E.src=='book')]:
    es[lab]=(np.exp(R[sub.values].mean(0))-1)*100
es.to_csv(f'{D}/reports/study2_event_response.csv',index=False); print(es.round(1).to_string(index=False))
# ---- spillover: other books by the same author
bya={}
for b in books: bya.setdefault(b['author'],[]).append(b)
sp=[]
for _,e in E.iterrows():
    j=li(e.month)
    for b in bya.get(e.author,[]):
        if b['bg']==e.bg or b['lis'][j-6:j-1].mean()<20: continue
        pre=np.log1p(b['lis'][j-6:j-1]).mean()
        sp.append([(np.log1p(b['lis'][j+k])-pre)-(M[j+k]-M[j-6:j-1].mean()) for k in range(-6,7)])
S=np.array(sp); sps=pd.DataFrame({'k':range(-6,7),'spill_pct':(np.exp(S.mean(0))-1)*100}) if len(S) else pd.DataFrame()
sps.to_csv(f'{D}/reports/study2_spillover.csv',index=False); print('spillover pairs',len(S)); print(sps.round(1).to_string(index=False))
# ---- hidden-book monthly forecast (panel, books split into folds; no own-listening inputs)
rows=[]
for b in books:
    a=b['att']
    for t in range(12,len(am)):
        j=li(am[t])
        if j is None or j+1>=len(lm): continue
        base=np.median(a[t-12:t]); rows.append(dict(bg=b['bg'],genre=b['genre'],src=int(b['src']=='book'),cal=int(am[t][4:]),
            att=np.log1p(a[t]),att_prev=np.log1p(a[t-1]),ratio=np.log1p(a[t])-np.log1p(base),base=np.log1p(base),
            market=M[j],y=np.log1p(b['lis'][j+1]),j=j))
P=pd.DataFrame(rows); P['genre']=P.genre.astype('category')
feats=['genre','src','cal','att','att_prev','ratio','base','market']
ub=P.bg.unique(); rng=np.random.RandomState(1); fold=dict(zip(ub,rng.randint(0,5,len(ub)))); P['fold']=P.bg.map(fold); P['pred']=np.nan
for f in range(5):
    tr,te=P.fold!=f,P.fold==f
    mdl=lgb.LGBMRegressor(n_estimators=400,learning_rate=0.05,num_leaves=31,min_child_samples=50,verbose=-1,random_state=0).fit(P.loc[tr,feats],P.loc[tr,'y'])
    P.loc[te,'pred']=mdl.predict(P.loc[te,feats])
lvl=P.groupby('bg')[['y','pred']].mean(); top=(lvl.y>=lvl.y.quantile(0.8)).astype(int)
within=P.groupby('bg').apply(lambda g: spearmanr(g.pred,g.y).correlation if g.y.std()>0 else np.nan).dropna()
P['dev_y']=P.y-P.groupby('bg').y.transform('mean'); P['dev_p']=P.pred-P.groupby('bg').pred.transform('mean')
res=dict(books=len(lvl),level_auc_top20=round(roc_auc_score(top,lvl.pred),3),level_spearman=round(spearmanr(lvl.pred,lvl.y).correlation,3),
         within_book_timing_spearman_median=round(within.median(),3),month_to_month_deviation_corr=round(np.corrcoef(P.dev_y,P.dev_p)[0,1],3))
json.dump(res,open(f'{D}/reports/study2_hidden_book.json','w'),indent=1); print(res)
P.to_pickle(f'{D}/interim/study2_panel.pkl'); E.to_pickle(f'{D}/interim/study2_events.pkl')
