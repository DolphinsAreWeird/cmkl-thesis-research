# Wider adaptation test: all LibriVox books linked to a Wikipedia book article, monthly listening.
import pandas as pd, numpy as np, json, requests, time, urllib.parse
from scipy.stats import spearmanr
from config import D, UA; H={"User-Agent":UA,"Accept":"application/sparql-results+json"}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); V=json.load(open(f'{D}/raw/ia_views_monthly.json'))
b=lk[lk.wiki_book.notna()].copy(); b['art']=b.wiki_book.str.replace(' ','_')
arts=sorted(set(b.art)|{'Wuthering_Heights','Frankenstein','Odyssey'})
def q(s):
    for k in range(6):
        r=requests.post("https://query.wikidata.org/sparql",data={"query":s},headers=H,timeout=90)
        if r.status_code==200: return r.json()['results']['bindings']
        time.sleep(int(r.headers.get('retry-after',10))+2)
    return []
rows=[]
for i in range(0,len(arts),60):
    vals=" ".join('<https://en.wikipedia.org/wiki/'+urllib.parse.quote(a,safe="(),_'!")+'>' for a in arts[i:i+60])
    for x in q(f'''SELECT ?bookArt ?adArt (MIN(?date) AS ?d) WHERE {{ VALUES ?bookArt {{ {vals} }} ?bookArt schema:about ?book. ?ad wdt:P144 ?book. ?ad wdt:P577 ?date.
       ?ad wdt:P31/wdt:P279* ?t. VALUES ?t {{ wd:Q11424 wd:Q5398426 wd:Q1259759 wd:Q506240 }}
       ?adArt schema:about ?ad; schema:isPartOf <https://en.wikipedia.org/>. }} GROUP BY ?bookArt ?adArt HAVING (MIN(?date) >= "2017-07-01"^^xsd:dateTime)'''):
        rows.append(dict(book_art=urllib.parse.unquote(x['bookArt']['value'].split('/wiki/')[-1]),ad_art=urllib.parse.unquote(x['adArt']['value'].split('/wiki/')[-1]),date=x['d']['value'][:10]))
    time.sleep(1)
A=pd.DataFrame(rows).drop_duplicates(); A['date']=pd.to_datetime(A.date); A=A[A.date<='2026-06-30']
print('adaptations',len(A),'books',A.book_art.nunique(),flush=True)
def peak(a,d):
    s=(d-pd.Timedelta(days=120)).strftime('%Y%m%d'); e=(d+pd.Timedelta(days=60)).strftime('%Y%m%d')
    for k in range(5):
        r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/{s}/{e}",headers={"User-Agent":H["User-Agent"]},timeout=30)
        if r.status_code==200:
            v=pd.Series({pd.Timestamp(x['timestamp'][:8]):x['views'] for x in r.json()['items']}); return float(v.resample('W').sum().max()) if len(v) else 0.0
        if r.status_code==404: return 0.0
        time.sleep(int(r.headers.get('retry-after',5))+1)
    return np.nan
A['ad_peak']=[ (time.sleep(0.9) or peak(a,d)) for a,d in zip(A.ad_art,A.date)]
months=pd.period_range('2017-01','2026-09',freq='M')
res=[]
for _,a in A.iterrows():
    ids=b[b.art==a.book_art].identifier.tolist()
    if not ids:
        pat={'Wuthering_Heights':'Wuthering','Frankenstein':'Frankenstein','Odyssey':'Odyssey'}.get(a.book_art)
        L=pd.read_parquet(f'{D}/processed/labels.parquet'); ids=L[L.title.str.contains(pat,case=False,na=False)].identifier.tolist() if pat else []
    if not ids: continue
    rel=lk.set_index('identifier').publicdate.reindex(ids).dropna()
    m0=a.date.to_period('M')
    if any(abs((r.tz_localize(None).to_period('M')-m0).n)<=8 for r in rel): continue
    ser=pd.Series({p:sum(V.get(i,{}).get(p.strftime('%Y%m'),0) for i in ids) for p in months})
    if m0-12<months[0] or m0+2>pd.Period('2026-09','M'): continue
    base=ser[m0-12:m0-7].median()
    if base<20: continue
    res.append(dict(book=a.book_art,adaptation=a.ad_art,date=a.date.date(),ad_peak=a.ad_peak,lift=ser[m0:m0+2].mean()/base,lead=ser[m0-3:m0-1].mean()/base))
R=pd.DataFrame(res).sort_values('ad_peak',ascending=False); R.to_csv(f'{D}/reports/adaptation_wide.csv',index=False)
print('usable adaptations',len(R)); print('Spearman(adaptation peak, lift):',round(spearmanr(R.ad_peak,R.lift).correlation,2))
for th in [50000,100000,200000]:
    g=R.ad_peak>=th; print(f'>={th:,}/week: n={g.sum()} median lift {R[g].lift.median():.2f}x (lead months -3..-2: {R[g].lead.median():.2f}x), share>=1.3x {(R[g].lift>=1.3).mean():.0%} | others n={(~g).sum()} median {R[~g].lift.median():.2f}x share {(R[~g].lift>=1.3).mean():.0%}')
print(R.head(15).round(2).to_string(index=False))
