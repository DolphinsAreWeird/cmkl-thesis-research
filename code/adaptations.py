# Wikidata: find films and TV series "based on" (P144) each book that has its own Wikipedia article, with release dates and article titles.
import json, requests, time, pandas as pd, urllib.parse
from config import D, UA; H={"User-Agent":UA,"Accept":"application/sparql-results+json"}
S=json.load(open(f'{D}/interim/weekly_scope.json')); arts=S['arts']
add=['Wuthering_Heights','Frankenstein']; arts=sorted(set(arts)|set(add))
def q(s):
    for k in range(6):
        r=requests.post("https://query.wikidata.org/sparql",data={"query":s},headers=H,timeout=90)
        if r.status_code==200: return r.json()['results']['bindings']
        time.sleep(int(r.headers.get('retry-after',10))+2)
    raise RuntimeError(r.status_code)
rows=[]
for i in range(0,len(arts),60):
    vals=" ".join('<https://en.wikipedia.org/wiki/'+urllib.parse.quote(a,safe="(),_'!")+'>' for a in arts[i:i+60])
    res=q(f'''SELECT ?bookArt ?ad ?adArt ?date ?typeLabel WHERE {{ VALUES ?bookArt {{ {vals} }}
      ?bookArt schema:about ?book. ?ad wdt:P144 ?book. ?ad wdt:P577 ?date. ?ad wdt:P31 ?type.
      ?adArt schema:about ?ad; schema:isPartOf <https://en.wikipedia.org/>.
      FILTER(?date >= "2016-01-01"^^xsd:dateTime)
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}''')
    for b in res:
        rows.append(dict(book_art=urllib.parse.unquote(b['bookArt']['value'].split('/wiki/')[-1]),ad_art=urllib.parse.unquote(b['adArt']['value'].split('/wiki/')[-1]),
                         date=b['date']['value'][:10],type=b['typeLabel']['value']))
    time.sleep(1)
A=pd.DataFrame(rows).sort_values('date').drop_duplicates(['book_art','ad_art'])
A.to_csv(f'{D}/raw/wikidata_adaptations.csv',index=False)
print('adaptations',len(A),'books with an adaptation',A.book_art.nunique()); print(A.type.value_counts().head(6).to_string())
print(A[A.book_art.isin(add)].to_string(index=False))
