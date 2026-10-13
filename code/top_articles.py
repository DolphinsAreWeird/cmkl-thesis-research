# Society-wide attention: Wikipedia's 1,000 most-viewed English articles for every month, 2016 to 2026 (one call per month).
import requests, json, time, os, pandas as pd
from config import D, UA; H={"User-Agent":UA}
f=f'{D}/raw/wiki_top_monthly.json'; out=json.load(open(f)) if os.path.exists(f) else {}
for p in pd.period_range('2016-01','2026-09',freq='M'):
    k=p.strftime('%Y%m')
    if k in out: continue
    for t in range(6):
        try:
            r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{p.year}/{p.month:02d}/all-days",headers=H,timeout=30)
            if r.status_code==200:
                out[k]=[(a['article'],a['views']) for a in r.json()['items'][0]['articles']]; break
            if r.status_code==404: break
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(5)
    json.dump(out,open(f,'w')); time.sleep(1)
print('months',len(out),flush=True)
