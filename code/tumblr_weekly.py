# Tumblr tag activity per week, estimated from the time span of the 20 most recent posts before each week's end
# (posts per day = 20 / span). One call per tag per week; stays under Tumblr's 1,000 calls per hour.
import requests, time, json, os, pandas as pd
from config import D, key; K=key('TUMBLR_CONSUMER_KEY')
cases=[('wuthering heights','2026-02-13'),('the odyssey','2026-07-17'),('frankenstein','2025-10-17'),('nosferatu','2024-12-25'),('little women','2019-12-25'),
       ('persuasion','2022-07-15'),('dracula','2023-08-11'),('the little mermaid','2023-05-26'),('emma','2020-02-21'),('pinocchio','2022-12-09'),
       ('pride and prejudice','2022-06-03'),('the secret garden','2020-08-07'),('black beauty','2020-11-27'),('the count of monte cristo','2024-06-28')]
f=f'{D}/raw/tumblr_weekly.json'; out=json.load(open(f)) if os.path.exists(f) else {}
def rate(tag,end):
    ts=int(pd.Timestamp(end).timestamp())
    for k in range(5):
        try:
            r=requests.get("https://api.tumblr.com/v2/tagged",params=dict(tag=tag,api_key=K,before=ts),timeout=30)
            if r.status_code==429: time.sleep(60); continue
            posts=r.json().get('response',[])
            if not posts: return 0.0
            t=[p['timestamp'] for p in posts]; return len(t)/max((ts-min(t))/86400,1/24)
        except Exception: time.sleep(5)
    return None
for tag,rel in cases:
    key=f'{tag}|{rel}'; done=out.get(key,{})
    for w in pd.date_range(pd.Timestamp(rel)-pd.Timedelta(weeks=26),pd.Timestamp(rel)+pd.Timedelta(weeks=12),freq='7D'):
        k=w.strftime('%Y-%m-%d')
        if k in done or w>pd.Timestamp('2026-10-10'): continue
        v=rate(tag,w)
        if v is not None: done[k]=v
        time.sleep(3.7)
    out[key]=done; json.dump(out,open(f,'w')); print(tag,len(done),'weeks',flush=True)
print('DONE',flush=True)
