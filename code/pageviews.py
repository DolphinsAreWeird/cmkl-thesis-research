import json, requests, time, urllib.parse, os
from concurrent.futures import ThreadPoolExecutor
from config import D, UA; H={"User-Agent":UA}
arts=json.load(open(f'{D}/interim/wiki_articles_needed_sample.json'))
f=f'{D}/raw/wiki_pageviews_monthly.json'; pv=json.load(open(f)) if os.path.exists(f) else {}
import pandas as pd
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl')
auth=set(lk.wiki_author.dropna())
todo=sorted([a for a in arts if a not in pv], key=lambda a: (a not in auth, a))
def get(a):
    url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/monthly/2015070100/2025063000"
    for k in range(8):
        try:
            r=requests.get(url,headers=H,timeout=20)
            if r.status_code==200: return a,{x['timestamp'][:6]:x['views'] for x in r.json()['items']}
            if r.status_code==404: return a,{}
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(3)
    return a,None
print('todo',len(todo),flush=True)
for i in range(0,len(todo),100):
    res={}
    for a in todo[i:i+100]:
        k,v=get(a); res[k]=v; time.sleep(0.9)
    pv.update({k:v for k,v in res.items() if v is not None}); json.dump(pv,open(f,'w'))
    print(i+100,'ok',len(pv),'failed',sum(v is None for v in res.values()),flush=True)
print('DONE',flush=True)
