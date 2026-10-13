# Daily non-robot views per recording from the Internet Archive Views API (public), stored as monthly sums.
import json, requests, time, os, pandas as pd, collections
from config import D, UA; H={"User-Agent":UA}
L=pd.read_parquet(f'{D}/processed/labels.parquet')
ids=L.sort_values('publicdate',ascending=False).identifier.tolist()   # newest first: they have full post-release history
f=f'{D}/raw/ia_views_monthly.json'; out=json.load(open(f)) if os.path.exists(f) else {}
todo=[i for i in ids if i not in out]; print('todo',len(todo),flush=True)
from concurrent.futures import ThreadPoolExecutor
def one(i):
    for k in range(5):
        try:
            r=requests.get(f"https://be-api.us.archive.org/views/v1/long/{i}",headers=H,timeout=30)
            if r.status_code==200:
                j=r.json(); days=j['days']; d=j['ids'].get(i,{}).get('detail',{}).get('non_robot',{}).get('per_day',[])
                m=collections.Counter()
                for day,v in zip(days,d): m[day[:7].replace('-','')]+=v
                return i,dict(m)
            time.sleep(3)
        except Exception: time.sleep(3)
    return i,None
for b in range(0,len(todo),150):
    with ThreadPoolExecutor(3) as ex:
        for i,v in ex.map(one,todo[b:b+150]):
            if v is not None: out[i]=v
    json.dump(out,open(f,'w')); print(b+150,len(out),flush=True)
json.dump(out,open(f,'w')); print('DONE',len(out),flush=True)
