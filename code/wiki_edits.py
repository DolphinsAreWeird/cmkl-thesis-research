# Monthly edit counts per article (Wikimedia Analytics REST), a second attention signal (Mestyan et al., 2013 used edits).
import json, requests, time, urllib.parse, os, pandas as pd
from config import D, UA; H={"User-Agent":UA}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl')
s=lk[(lk.n_authors==1)&(~lk.author.isin(['Various','Unknown','Anonymous']))&(lk.publicdate>='2016-07-01')]
arts=sorted(set(s.wiki_author.dropna())|set(s.wiki_book.dropna()))
f=f'{D}/raw/wiki_edits_monthly.json'; ed=json.load(open(f)) if os.path.exists(f) else {}
todo=[a for a in arts if a not in ed]
def get(a):
    url=f"https://wikimedia.org/api/rest_v1/metrics/edits/per-page/en.wikipedia/{urllib.parse.quote(a,safe='')}/user/monthly/20150101/20250701"
    for k in range(8):
        try:
            r=requests.get(url,headers=H,timeout=20)
            if r.status_code==200:
                it=r.json()['items'][0]['results'] if r.json().get('items') else []
                return {x['timestamp'][:7].replace('-',''):x['edits'] for x in it}
            if r.status_code==404: return {}
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(3)
    return None
print('todo',len(todo),flush=True)
for i,a in enumerate(todo):
    v=get(a)
    if v is not None: ed[a]=v
    if i%100==99: json.dump(ed,open(f,'w')); print(i+1,len(ed),flush=True)
    time.sleep(0.9)
json.dump(ed,open(f,'w')); print('DONE',len(ed),flush=True)
