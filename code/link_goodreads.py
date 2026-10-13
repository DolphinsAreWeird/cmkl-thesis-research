import json, pandas as pd, numpy as np, re, unicodedata
def norm(x):
    x=unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()
    x=re.sub(r'\(.*?\)|\[.*?\]','',x); x=re.sub(r'\b(vol(ume)?|version|book|part)\s*[0-9ivx]+\b','',x)
    x=re.sub(r'[^a-z0-9 ]',' ',x); x=re.sub(r'^(the|a|an) ','',x.strip()); return re.sub(r'\s+',' ',x).strip()
from config import D
B=pd.DataFrame(json.load(open(f'{D}/raw/goodreads_books_matched.json'))); A=json.load(open(f'{D}/raw/goodreads_authors_matched.json'))
B['nt']=B.title.map(norm); B['alast']=B.authors.map(lambda l: {norm(A.get(a,'')).split()[-1] for a in l if norm(A.get(a,''))})
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl')
idx=B.groupby('nt').groups
rows=[]; ids=set()
for _,r in lk[lk.n_authors==1].iterrows():
    t=norm(r.title); last=norm(str(r.author)).split()[-1] if norm(str(r.author)) else ''
    if t not in idx or not last: continue
    c=B.loc[idx[t]]; c=c[c.alast.map(lambda s: last in s)]
    if c.empty: continue
    w=c.groupby('work_id').agg(ratings=('ratings_count','sum'),reviews=('text_reviews_count','sum'),to_read=('to_read','max'),ids=('book_id',list)).sort_values('ratings',ascending=False).iloc[0]
    rows.append(dict(identifier=r.identifier,gr_work=w.name,gr_ratings=int(w.ratings),gr_text_reviews=int(w.reviews),gr_to_read=int(w.to_read),gr_book_ids=w.ids)); ids|=set(w.ids)
G=pd.DataFrame(rows); G.to_pickle(f'{D}/interim/goodreads_linked.pkl'); json.dump(sorted(ids),open(f'{D}/interim/goodreads_linked_book_ids.json','w'))
print('recordings linked to Goodreads',len(G),'of',(lk.n_authors==1).sum(),'| editions',len(ids))
print(G.sort_values('gr_ratings',ascending=False).head(5)[['identifier','gr_ratings','gr_to_read']].to_string())
