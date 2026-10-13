# Daily Wikipedia views (book articles) and daily LibriVox listening for books with a book-level article, 2017-01 to 2026-08.
import pandas as pd, json, requests, time, os, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from config import D, UA; H={"User-Agent":UA}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); PV=json.load(open(f'{D}/raw/wiki_pageviews_monthly.json'))
b=lk[(lk.n_authors==1)&lk.wiki_book.notna()].copy(); b['art']=b.wiki_book.str.replace(' ','_')
b=b[b.art.isin(PV)]
arts=sorted(b.art.unique()); recs=sorted(b.identifier.unique())
json.dump({'arts':arts,'map':b[['identifier','bookgroup','art','title','author']].to_dict('records')},open(f'{D}/interim/weekly_scope.json','w'))
print('articles',len(arts),'recordings',len(recs),flush=True)
fw=f'{D}/raw/wiki_book_daily.json'; W=json.load(open(fw)) if os.path.exists(fw) else {}
fl=f'{D}/raw/ia_views_daily_books.json'; Lr=json.load(open(fl)) if os.path.exists(fl) else {}
def ia(i):
    for k in range(5):
        try:
            j=requests.get(f"https://be-api.us.archive.org/views/v1/long/{i}",headers=H,timeout=30).json()
            return i,dict(zip(j['days'],j['ids'][i]['detail']['non_robot']['per_day']))
        except Exception: time.sleep(3)
    return i,None
todo=[r for r in recs if r not in Lr]
for s in range(0,len(todo),150):
    with ThreadPoolExecutor(3) as ex:
        for i,v in ex.map(ia,todo[s:s+150]):
            if v: Lr[i]={k[:10]:x for k,x in v.items() if x}
    json.dump(Lr,open(fl,'w')); print('ia',len(Lr),flush=True)
for n,a in enumerate([a for a in arts if a not in W]):
    url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/20160701/20260831"
    for k in range(8):
        try:
            r=requests.get(url,headers=H,timeout=30)
            if r.status_code==200: W[a]={x['timestamp'][:8]:x['views'] for x in r.json()['items']}; break
            if r.status_code==404: W[a]={}; break
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(3)
    time.sleep(0.9)
    if n%50==49: json.dump(W,open(fw,'w')); print('wiki',len(W),flush=True)
json.dump(W,open(fw,'w')); print('DONE',len(W),len(Lr),flush=True)
