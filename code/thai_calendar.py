# Step 4: Thai adaptation calendar from Wikidata, with Thai Wikipedia attention on the film/series page.
import pandas as pd, requests, time, urllib.parse, json
from config import D, UA; H={"User-Agent":UA,"Accept":"application/sparql-results+json"}
s='''SELECT ?work ?workLabel ?authorLabel ?ad ?adLabel ?typeLabel (MIN(?date) AS ?d) ?thAd ?thWork WHERE {
  ?ad wdt:P144 ?work. ?ad wdt:P577 ?date. ?ad wdt:P31 ?type. VALUES ?type { wd:Q11424 wd:Q5398426 wd:Q1259759 wd:Q506240 wd:Q21191270 }
  { ?work wdt:P407 wd:Q9217 } UNION { ?work wdt:P50 ?au. ?au wdt:P27 wd:Q869 } UNION { ?work wdt:P364 wd:Q9217 }
  OPTIONAL { ?work wdt:P50 ?author. }
  OPTIONAL { ?thAd schema:about ?ad; schema:isPartOf <https://th.wikipedia.org/>. }
  OPTIONAL { ?thWork schema:about ?work; schema:isPartOf <https://th.wikipedia.org/>. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "th,en". } }
GROUP BY ?work ?workLabel ?authorLabel ?ad ?adLabel ?typeLabel ?thAd ?thWork'''
for k in range(5):
    r=requests.post("https://query.wikidata.org/sparql",data={"query":s},headers=H,timeout=120)
    if r.status_code==200: break
    time.sleep(15)
B=r.json()['results']['bindings']
rows=[dict(work=b['workLabel']['value'],author=b.get('authorLabel',{}).get('value',''),adaptation=b['adLabel']['value'],type=b['typeLabel']['value'],date=b['d']['value'][:10],
           th_ad=urllib.parse.unquote(b['thAd']['value'].split('/wiki/')[-1]) if 'thAd' in b else '',th_work=urllib.parse.unquote(b['thWork']['value'].split('/wiki/')[-1]) if 'thWork' in b else '') for b in B]
T=pd.DataFrame(rows).drop_duplicates(); T['date']=pd.to_datetime(T.date,errors='coerce'); T=T.sort_values('date')
print('Thai-literature adaptations in Wikidata:',len(T),'| since 2017:',(T.date>='2017-01-01').sum(),'| with a Thai Wikipedia page:',(T.th_ad!='').sum())
def pv(a,d):
    if not a or pd.isna(d): return None
    s=(d-pd.Timedelta(days=120)).strftime('%Y%m%d'); e=(d+pd.Timedelta(days=60)).strftime('%Y%m%d')
    if s<'20150701': return None
    r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/th.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/{s}/{e}",headers={"User-Agent":H["User-Agent"]},timeout=30)
    if r.status_code!=200: return None
    v=pd.Series({pd.Timestamp(x['timestamp'][:8]):x['views'] for x in r.json()['items']}); time.sleep(0.9); return float(v.resample('W').sum().max()) if len(v) else 0.0
R=T[T.date>='2017-01-01'].copy(); R['th_peak_weekly_views']=[pv(a,d) for a,d in zip(R.th_ad,R.date)]
R.to_csv(f'{D}/reports/thai_adaptation_calendar.csv',index=False)
print(R.sort_values('th_peak_weekly_views',ascending=False)[['work','author','adaptation','type','date','th_peak_weekly_views']].head(20).to_string(index=False))
