# Step 2: widen the adaptation calendar. Find works by any LibriVox author (via Wikidata author IDs) that have film/TV adaptations from mid-2017,
# then match the work's title to LibriVox recordings by that author. Measures lift with monthly listening, as before.
import pandas as pd, numpy as np, json, requests, time, re, unicodedata, urllib.parse
from config import D, UA; H={"User-Agent":UA,"Accept":"application/sparql-results+json"}
amap=json.load(open(f'{D}/raw/wikidata_author_match.json')); qids=sorted(set(v[0] for v in amap.values()))
def q(s):
    for k in range(6):
        r=requests.post("https://query.wikidata.org/sparql",data={"query":s},headers=H,timeout=90)
        if r.status_code==200: return r.json()['results']['bindings']
        time.sleep(int(r.headers.get('retry-after',10))+2)
    return []
rows=[]
for i in range(0,len(qids),80):
    vals=" ".join('wd:'+x for x in qids[i:i+80])
    for x in q(f'''SELECT ?a ?workLabel ?adArt (MIN(?date) AS ?d) WHERE {{ VALUES ?a {{ {vals} }} ?work wdt:P50 ?a. ?ad wdt:P144 ?work. ?ad wdt:P577 ?date.
        ?ad wdt:P31/wdt:P279* ?t. VALUES ?t {{ wd:Q11424 wd:Q5398426 wd:Q1259759 wd:Q506240 }}
        ?adArt schema:about ?ad; schema:isPartOf <https://en.wikipedia.org/>.
        ?work rdfs:label ?workLabel FILTER(LANG(?workLabel)="en") }} GROUP BY ?a ?workLabel ?adArt HAVING (MIN(?date) >= "2017-07-01"^^xsd:dateTime && MIN(?date) <= "2026-06-30"^^xsd:dateTime)'''):
        rows.append(dict(author_q=x['a']['value'].split('/')[-1],work=x['workLabel']['value'],ad_art=urllib.parse.unquote(x['adArt']['value'].split('/wiki/')[-1]),date=x['d']['value'][:10]))
    time.sleep(1)
A=pd.DataFrame(rows).drop_duplicates(); print('adaptations of works by LibriVox authors:',len(A),flush=True)
def norm(x):
    x=unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower(); x=re.sub(r'\(.*?\)','',x)
    x=re.sub(r'\b(vol(ume)?|version|book|part)\s*[0-9ivx]+\b','',x); x=re.sub(r'[^a-z0-9 ]',' ',x); x=re.sub(r'^(the|a|an) ','',x.strip()); return re.sub(r'\s+',' ',x).strip()
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
q2a={v[0]:k for k,v in amap.items()}
lk['nt']=lk.title.map(norm); A['nt']=A.work.map(norm); A['author']=A.author_q.map(q2a)
M=A.merge(lk[['identifier','author','nt','publicdate']],on=['author','nt'])
G=M.groupby(['work','author','ad_art','date']).agg(ids=('identifier',list),rels=('publicdate',list)).reset_index()
print('matched to LibriVox recordings:',len(G),'adaptations of',G.work.nunique(),'works',flush=True)
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); months=pd.period_range('2017-01','2026-09',freq='M')
def peak(a,d):
    s=(d-pd.Timedelta(days=120)).strftime('%Y%m%d'); e=(d-pd.Timedelta(days=7)).strftime('%Y%m%d')
    for k in range(5):
        r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/{s}/{e}",headers={"User-Agent":H["User-Agent"]},timeout=30)
        if r.status_code==200:
            v=pd.Series({pd.Timestamp(x['timestamp'][:8]):x['views'] for x in r.json()['items']}); return float(v.resample('W').sum().max()) if len(v) else 0.0
        if r.status_code==404: return 0.0
        time.sleep(int(r.headers.get('retry-after',5))+1)
    return np.nan
out=[]
for _,a in G.iterrows():
    d=pd.Timestamp(a.date); m0=d.to_period('M')
    if d.month==1 and d.day==1: continue
    if any(abs((r.tz_localize(None).to_period('M')-m0).n)<=8 for r in a.rels if pd.notna(r)): continue
    ser=pd.Series({p:sum(V.get(i,{}).get(p.strftime('%Y%m'),0) for i in a.ids) for p in months})
    if m0-12<months[0] or m0+2>months[-1]: continue
    base=ser[m0-12:m0-7].median()
    if base<20: continue
    time.sleep(0.9)
    out.append(dict(work=a.work,author=a.author,adaptation=a.ad_art,date=a.date,pre_peak=peak(a.ad_art,d),lift=ser[m0:m0+2].mean()/base))
W=pd.DataFrame(out).sort_values('pre_peak',ascending=False); W.to_csv(f'{D}/reports/adaptation_wider2.csv',index=False)
print('usable with exact dates and clean listening:',len(W)); print(W.head(25).round(2).to_string(index=False))
