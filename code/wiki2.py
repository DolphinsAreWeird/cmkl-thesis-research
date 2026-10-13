import pandas as pd, requests, json, time, urllib.parse, unicodedata, os
from concurrent.futures import ThreadPoolExecutor
from config import UA
H={"User-Agent":UA}
m=pd.read_pickle('base2.pkl')
s=m[(m.n_authors==1)&(m.publicdate>='2016-07-01')]
authors=sorted(set(s.author.dropna())-{'Various','Unknown','Anonymous',''})
amap=json.load(open('author_wiki.json')) if os.path.exists('author_wiki.json') else {}
todo=[a for a in authors if a not in amap]
def norm(x): return unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()
def find(a):
    for t in range(3):
        try:
            r=requests.get("https://en.wikipedia.org/w/api.php",params={"action":"query","list":"search","srsearch":a,"srlimit":3,"format":"json"},headers=H,timeout=20).json()
            last=norm(a.split()[-1])
            for h in r['query']['search']:
                if last in norm(h['title']): return a,h['title']
            return a,None
        except Exception: time.sleep(1)
    return a,None
print('authors',len(authors),'todo',len(todo),flush=True)
for i in range(0,len(todo),300):
    with ThreadPoolExecutor(10) as ex: amap.update(dict(ex.map(find,todo[i:i+300])))
    json.dump(amap,open('author_wiki.json','w')); print('search',i+300,flush=True)
pvs=json.load(open('author_pv.json')) if os.path.exists('author_pv.json') else {}
titles=sorted(set(v for v in amap.values() if v)-set(pvs))
def pv(title):
    art=urllib.parse.quote(title.replace(' ','_'),safe='')
    url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/monthly/2015070100/2025063000"
    for t in range(3):
        try:
            r=requests.get(url,headers=H,timeout=20)
            if r.status_code==404: return title,{}
            if r.status_code==200: return title,{x['timestamp'][:6]:x['views'] for x in r.json()['items']}
        except Exception: pass
        time.sleep(1)
    return title,None
for i in range(0,len(titles),300):
    with ThreadPoolExecutor(10) as ex: pvs.update(dict(ex.map(pv,titles[i:i+300])))
    json.dump(pvs,open('author_pv.json','w')); print('pv',i+300,'of',len(titles),flush=True)
print('DONE',flush=True)
