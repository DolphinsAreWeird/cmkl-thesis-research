# Structured entity linking via Wikidata SPARQL: authors -> enwiki article, and their works -> enwiki article.
import pandas as pd, requests, json, time, re, unicodedata, os
from config import D, UA
H={"User-Agent":UA,"Accept":"application/sparql-results+json"}
EP="https://query.wikidata.org/sparql"
def q(sparql):
    for k in range(6):
        r=requests.post(EP,data={"query":sparql},headers=H,timeout=90)
        if r.status_code==200: return r.json()['results']['bindings']
        time.sleep(int(r.headers.get('retry-after',10))+2)
    raise RuntimeError(r.status_code)
m=pd.read_pickle(f'{D}/interim/recordings_joined.pkl')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&(m.author.notna())]
authors=sorted(set(m.author))
esc=lambda s: s.replace('\\','\\\\').replace('"','\\"')
amap={}
for i in range(0,len(authors),80):
    vals=" ".join(f'"{esc(a)}"@en' for a in authors[i:i+80])
    res=q(f'''SELECT ?name ?p ?article (COUNT(?sl) AS ?n) WHERE {{ VALUES ?name {{ {vals} }} ?p rdfs:label|skos:altLabel ?name; wdt:P31 wd:Q5.
      ?article schema:about ?p; schema:isPartOf <https://en.wikipedia.org/>. ?p wikibase:sitelinks ?sl }} GROUP BY ?name ?p ?article''')
    for b in res:
        nm=b['name']['value']; n=int(b['n']['value'])
        if nm not in amap or n>amap[nm][2]: amap[nm]=(b['p']['value'].split('/')[-1], b['article']['value'].split('/wiki/')[-1], n)
    print('authors',i+80,len(amap),flush=True); time.sleep(1)
json.dump(amap,open(f'{D}/raw/wikidata_author_match.json','w'))
qids=sorted(set(v[0] for v in amap.values()))
works=[]
for i in range(0,len(qids),40):
    vals=" ".join('wd:'+x for x in qids[i:i+40])
    res=q(f'''SELECT ?a ?w ?label ?article WHERE {{ VALUES ?a {{ {vals} }} ?w wdt:P50 ?a. ?w rdfs:label ?label FILTER(LANG(?label)="en").
      ?article schema:about ?w; schema:isPartOf <https://en.wikipedia.org/>. }}''')
    for b in res: works.append((b['a']['value'].split('/')[-1],b['label']['value'],b['article']['value'].split('/wiki/')[-1]))
    print('works',i+40,len(works),flush=True); time.sleep(1)
json.dump(works,open(f'{D}/raw/wikidata_author_works.json','w'))
print('DONE',flush=True)
