import pandas as pd, requests, json, time, urllib.parse, unicodedata
from concurrent.futures import ThreadPoolExecutor
H={"User-Agent":"CMKL-thesis-research/0.1 (student project; contact via CMKL University)"}
m=pd.read_pickle('base2.pkl')
authors=sorted(set(m.loc[m.n_authors==1,'author'].dropna()))
skip={'Various','Unknown','Anonymous',''}
authors=[a for a in authors if a not in skip]
def norm(s): return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
def find(a):
    for t in range(3):
        try:
            r=requests.get("https://en.wikipedia.org/w/api.php",params={"action":"query","list":"search","srsearch":a,"srlimit":3,"format":"json"},headers=H,timeout=30).json()
            last=norm(a.split()[-1])
            for h in r['query']['search']:
                if last in norm(h['title']): return a,h['title']
            return a,None
        except Exception: time.sleep(2)
    return a,None
t=time.time()
with ThreadPoolExecutor(8) as ex: res=list(ex.map(find,authors))
print("search done",flush=True)
amap=dict(res); json.dump(amap,open('author_wiki.json','w'))
print('authors',len(authors),'matched',sum(v is not None for v in amap.values()),round(time.time()-t),'s')
def pv(title):
    art=urllib.parse.quote(title.replace(' ','_'),safe='')
    url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/monthly/2015070100/2025063000"
    for t in range(3):
        try:
            r=requests.get(url,headers=H,timeout=30)
            if r.status_code==404: return title,{}
            if r.status_code==200: return title,{i['timestamp'][:6]:i['views'] for i in r.json()['items']}
        except Exception: pass
        time.sleep(2)
    return title,None
titles=sorted(set(v for v in amap.values() if v))
t=time.time()
with ThreadPoolExecutor(8) as ex: pvs=dict(ex.map(pv,titles))
json.dump(pvs,open('author_pv.json','w'))
print('pageview series',sum(v is not None for v in pvs.values()),'of',len(titles),round(time.time()-t),'s')
