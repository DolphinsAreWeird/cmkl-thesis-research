# Daily top 1,000 English Wikipedia pages, 2016 to 2026 (one call per day), for weekly themes.
import requests, json, time, os, pandas as pd
from config import D, UA; H={"User-Agent":UA}
f=f'{D}/raw/wiki_top_daily.json'; out=json.load(open(f)) if os.path.exists(f) else {}; last_saved=len(out)
def save():   # write then rename, so a crash mid-write never destroys the collected file
    with open(f+'.part','w') as h: json.dump(out,h)
    os.replace(f+'.part',f)
for d in pd.date_range('2016-01-01','2026-09-30',freq='D'):
    k=d.strftime('%Y%m%d')
    if k in out: continue
    for t in range(6):
        try:
            r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{d.year}/{d.month:02d}/{d.day:02d}",headers=H,timeout=30)
            if r.status_code==200: out[k]=[(a['article'],a['views']) for a in r.json()['items'][0]['articles'][:500]]; break
            if r.status_code==404: break
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(5)
    if len(out)%100==0 and len(out)!=last_saved: save(); last_saved=len(out); print(len(out),flush=True)
    time.sleep(0.8)
save(); print('DONE',len(out),flush=True)
