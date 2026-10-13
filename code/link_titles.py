import pandas as pd, json, re, unicodedata, urllib.parse
from config import D
m=pd.read_pickle(f'{D}/interim/recordings_joined.pkl')
amap=json.load(open(f'{D}/raw/wikidata_author_match.json')); works=json.load(open(f'{D}/raw/wikidata_author_works.json'))
def norm(x):
    x=unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()
    x=re.sub(r'\(.*?\)|\[.*?\]','',x); x=re.sub(r'\b(vol(ume)?|version|book|part)\s*[0-9ivx]+\b','',x)
    x=re.sub(r'[^a-z0-9 ]',' ',x); x=re.sub(r'^(the|a|an) ','',x.strip()); return re.sub(r'\s+',' ',x).strip()
W={}
for q,label,art in works: W.setdefault(q,{})[norm(label)]=art
def link(r):
    a=amap.get(r.author) if isinstance(r.author,str) and r.n_authors==1 else None
    if not a: return pd.Series([None,None])
    t=norm(str(r.title)); cand=W.get(a[0],{})
    art=cand.get(t)
    if not art and len(t.split())>=2:
        for lab,ar in cand.items():
            if len(lab.split())>=2 and (t.startswith(lab+' ') or lab.startswith(t+' ')): art=ar; break
    return pd.Series([urllib.parse.unquote(a[1]), urllib.parse.unquote(art) if art else None])
m[['wiki_author','wiki_book']]=m.apply(link,axis=1)
m.to_pickle(f'{D}/interim/recordings_linked.pkl')
s=m[(m.n_authors==1)]
print('recordings',len(m),'single-author',len(s),'author linked',s.wiki_author.notna().sum(),'book linked',s.wiki_book.notna().sum())
arts=sorted(set(m.wiki_author.dropna())|set(m.wiki_book.dropna())); json.dump(arts,open(f'{D}/interim/wiki_articles_needed.json','w')); print('articles to fetch',len(arts))
print(m.loc[m.wiki_book.notna(),['title','author','wiki_book']].sample(8,random_state=1).to_string())
