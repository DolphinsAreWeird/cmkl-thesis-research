# Match each recording's book to an English Wikipedia article and pull monthly page views (Jul 2015 - Jun 2025).
import pandas as pd, requests, json, time, urllib.parse, unicodedata, re, os
from concurrent.futures import ThreadPoolExecutor
from config import D, UA; H={"User-Agent":UA}
m=pd.read_pickle(f'{D}/interim/recordings_joined.pkl')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))]
pairs=sorted(set(zip(m.title.str.strip(),m.author)))
out=f'{D}/raw/wiki_book_match.json'; mp=json.load(open(out)) if os.path.exists(out) else {}
def norm(x): return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()).strip()
STOP={'the','a','an','of','and','in','to','vol','volume','version','book'}
def key(t,a): return t+' || '+a
def find(p):
    t,a=p
    words=[w for w in norm(t).split() if w not in STOP]
    if not words: return key(t,a),None
    for k in range(3):
        try:
            r=requests.get("https://en.wikipedia.org/w/api.php",params={"action":"query","list":"search","srsearch":f'{t} {a.split()[-1]}',"srlimit":5,"format":"json"},headers=H,timeout=20).json()
            for h in r['query']['search']:
                ht=norm(re.sub(r'\(.*?\)','',h['title']))
                snip=norm(re.sub(r'<.*?>','',h.get('snippet','')))
                if all(w in ht.split() for w in words) and (norm(a.split()[-1]) in snip or '(' in h['title'] or len(words)>=2):
                    return key(t,a),h['title']
            return key(t,a),None
        except Exception: time.sleep(1)
    return key(t,a),None
todo=[p for p in pairs if key(*p) not in mp]
print('pairs',len(pairs),'todo',len(todo),flush=True)
for i in range(0,len(todo),400):
    with ThreadPoolExecutor(10) as ex: mp.update(dict(ex.map(find,todo[i:i+400])))
    json.dump(mp,open(out,'w')); print('search',min(i+400,len(todo)),flush=True)
pvf=f'{D}/raw/wiki_book_pageviews_monthly.json'; pvs=json.load(open(pvf)) if os.path.exists(pvf) else {}
titles=sorted(set(v for v in mp.values() if v)-set(pvs))
def pv(title):
    art=urllib.parse.quote(title.replace(' ','_'),safe='')
    url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{art}/monthly/2015070100/2025063000"
    for k in range(3):
        try:
            r=requests.get(url,headers=H,timeout=20)
            if r.status_code==404: return title,{}
            if r.status_code==200: return title,{x['timestamp'][:6]:x['views'] for x in r.json()['items']}
        except Exception: pass
        time.sleep(1)
    return title,None
for i in range(0,len(titles),400):
    with ThreadPoolExecutor(10) as ex: pvs.update(dict(ex.map(pv,titles[i:i+400])))
    json.dump(pvs,open(pvf,'w')); print('pv',min(i+400,len(titles)),'of',len(titles),flush=True)
print('DONE',flush=True)
