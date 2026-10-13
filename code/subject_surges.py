# Scalable theme test. 1) Book-relevant concept pages = subjects (Wikidata P921) used for literary works.
# 2) Long-tail monthly page views for each. 3) Automatic surges, labelled sudden or sustained using only earlier months.
# 4) Matched difference-in-differences for the books closest to each subject, with placebo years.
import pandas as pd, numpy as np, json, requests, time, urllib.parse, os
from config import D, UA; O=f'{D}/db'; H={"User-Agent":UA}
fs=f'{D}/raw/wikidata_book_subjects.json'
if not os.path.exists(fs):
    q='''SELECT ?s ?art (COUNT(DISTINCT ?w) AS ?n) WHERE { ?w wdt:P31 wd:Q7725634; wdt:P921 ?s. ?art schema:about ?s; schema:isPartOf <https://en.wikipedia.org/>. }
         GROUP BY ?s ?art HAVING (COUNT(DISTINCT ?w) >= 15) ORDER BY DESC(?n) LIMIT 1500'''
    for k in range(4):
        r=requests.post("https://query.wikidata.org/sparql",data={"query":q},headers={**H,"Accept":"application/sparql-results+json"},timeout=120)
        if r.status_code==200: break
        time.sleep(20)
    S=[dict(qid=b['s']['value'].split('/')[-1],art=urllib.parse.unquote(b['art']['value'].split('/wiki/')[-1]),n=int(b['n']['value'])) for b in r.json()['results']['bindings']]
    json.dump(S,open(fs,'w')); print('subjects',len(S),flush=True)
S=pd.DataFrame(json.load(open(fs)))
SKIPWORDS=('List_of','English_language','French_language','German_language','Novel','Poetry','Literature','Fiction','Book')
S=S[~S.art.str.startswith(SKIPWORDS)].reset_index(drop=True); print('subjects kept',len(S),flush=True)
# descriptions + embeddings
fd=f'{D}/raw/subject_desc.json'; desc=json.load(open(fd)) if os.path.exists(fd) else {}
todo=[a for a in S.art if a not in desc]
for i in range(0,len(todo),50):
    ch=todo[i:i+50]
    try:
        j=requests.get("https://en.wikipedia.org/w/api.php",params=dict(action='query',prop='description',titles='|'.join(c.replace('_',' ') for c in ch),format='json',redirects=1),headers=H,timeout=30).json()['query']
        got={p.get('title','').replace(' ','_'):p.get('description','') for p in j['pages'].values()}
        for c in ch: desc[c]=got.get(c,'')
    except Exception: pass
    time.sleep(1)
json.dump(desc,open(fd,'w'))
from fastembed import TextEmbedding
m=TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
SE=np.array(list(m.embed([a.replace('_',' ')+(': '+desc.get(a,'') if desc.get(a) else '') for a in S.art]))); SE/=np.linalg.norm(SE,axis=1,keepdims=True)
# monthly long-tail views
fv=f'{D}/raw/subject_views_monthly.json'; V=json.load(open(fv)) if os.path.exists(fv) else {}
for n,a in enumerate([a for a in S.art if a not in V]):
    for k in range(6):
        try:
            r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/monthly/2016010100/2026083100",headers=H,timeout=30)
            if r.status_code==200: V[a]={x['timestamp'][:6]:x['views'] for x in r.json()['items']}; break
            if r.status_code==404: V[a]={}; break
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(5)
    if n%100==99: json.dump(V,open(fv,'w')); print('views',len(V),flush=True)
    time.sleep(0.9)
json.dump(V,open(fv,'w')); print('views done',len(V),flush=True)
# books
B=json.load(open(f'{D}/interim/book_themes.json')); books=np.array(B['books']); BE=np.load(f'{D}/interim/book_emb_by_group.npy')
L=pd.read_parquet(f'{O}/listening.parquet'); Lw=L.pivot(index='book_id',columns='period',values='listens').reindex(books)
lper=[pd.Period(p,'M') for p in Lw.columns]; LL=np.log1p(Lw.values.astype(float))
lab=pd.read_parquet(f'{D}/processed/labels.parquet'); lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
g1=lk.merge(lab[['identifier','genre1']],on='identifier').groupby('bookgroup').genre1.agg(lambda s:s.mode().iloc[0]); g1.index=g1.index.astype(str); genre=g1.reindex(books).fillna('None').values
title=lk.groupby('bookgroup').title.first(); title.index=title.index.astype(str)
rel={str(k):[x.tz_localize(None).to_period('M') for x in v.publicdate.dropna()] for k,v in lk.groupby('bookgroup')}
launch=np.array([[any(-12<=(p-r).n<=3 for r in rel.get(b,[])) for p in lper] for b in books])   # a new recording released 3 months before to 12 months after p
SIM=BE@SE.T; cut=np.quantile(SIM,0.995)
def did(bk,j,rng,nc=10):
    pre=slice(j-12,j-2); post=slice(j,j+3)
    ok=(~launch[:,j])&(np.expm1(np.median(LL[:,pre],axis=1))>=5)
    lvl=np.median(LL[:,pre],axis=1); sl=np.polyfit(np.arange(10),LL[:,pre].T,1)[0]; chg=LL[:,post].mean(1)-LL[:,pre].mean(1)
    bs=[b for b in bk if ok[b]]; pool=np.where(ok&~np.isin(np.arange(len(books)),bk))[0]; eff=[]
    for b in bs:
        c=pool[genre[pool]==genre[b]]
        if len(c)<nc: c=pool
        d=((lvl[c]-lvl[b])/0.8)**2+((sl[c]-sl[b])/0.05)**2; eff.append(chg[b]-chg[c[np.argsort(d)[:nc]]].mean())
    return np.array(eff)
months=pd.period_range('2016-01','2026-08',freq='M'); rng=np.random.RandomState(0); rows=[]
for si,a in enumerate(S.art):
    v=pd.Series(V.get(a,{})); 
    if v.empty: continue
    v.index=pd.PeriodIndex([pd.Period(f'{k[:4]}-{k[4:]}','M') for k in v.index]); v=v.reindex(months).fillna(0).values
    bk=np.where(SIM[:,si]>=cut)[0]; bk=bk[np.argsort(-SIM[bk,si])][:10]
    if len(bk)<3: continue
    last=-99
    for i in range(12,len(months)):
        base=np.median(v[i-12:i])
        if base<3000 or v[i]<3*base or i-last<12: continue         # surge: at least 3x its own median, on a page with real traffic
        p=months[i]
        if p not in lper: continue
        j=lper.index(p)
        if j<12 or j+3>=len(lper): continue
        last=i; r=v[i-3:i]/base; kind='sustained' if (r>=1.5).sum()>=2 else 'sudden'
        e=did(bk,j,rng)
        if len(e)<3: continue
        pl=[]
        for s in (-24,-12,12,24):
            jj=j+s
            if 12<=jj and jj+3<len(lper):
                ee=did(bk,jj,rng)
                if len(ee)>=3: pl.append(ee.mean())
        rows.append(dict(subject=a.replace('_',' '),month=str(p),surge=round(v[i]/base,1),kind=kind,n_books=len(e),effect=float(e.mean()),placebo=float(np.mean(pl)) if pl else np.nan,
                         books=[title.get(books[b],'') for b in bk[:3]]))
R=pd.DataFrame(rows); R.to_csv(f'{D}/reports/subject_surges.csv',index=False)
print('surges tested',len(R),'subjects',R.subject.nunique(),flush=True)
def summ(x): return dict(n=len(x),median_effect=round(float(np.exp(x.effect.median())),3),share_positive=round(float((x.effect>0).mean()),2),share_beating_placebo=round(float((x.effect>x.placebo).mean()),2),median_placebo=round(float(np.exp(x.placebo.median())),3))
out=dict(all=summ(R),sudden=summ(R[R.kind=='sudden']),sustained=summ(R[R.kind=='sustained']),big_surges_10x=summ(R[R.surge>=10]))
print(json.dumps(out,indent=1),flush=True); json.dump(out,open(f'{D}/reports/subject_surges_summary.json','w'),indent=1)
print(R.sort_values('effect',ascending=False).head(12).to_string(index=False),flush=True)
print('ALLDONE',flush=True)
