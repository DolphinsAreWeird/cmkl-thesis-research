# Stream the UCSD Goodreads Book Graph (academic use; collected 2017) without saving the big files.
# Step 1: books whose normalized title matches a LibriVox title. Step 2: authors. Step 3: dated reviews for matched books.
import json, gzip, re, unicodedata, subprocess, sys, pandas as pd, collections
from config import D; U='https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/'
def norm(x):
    x=unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()
    x=re.sub(r'\(.*?\)|\[.*?\]','',x); x=re.sub(r'\b(vol(ume)?|version|book|part)\s*[0-9ivx]+\b','',x)
    x=re.sub(r'[^a-z0-9 ]',' ',x); x=re.sub(r'^(the|a|an) ','',x.strip()); return re.sub(r'\s+',' ',x).strip()
def stream(name):
    p=subprocess.Popen(['curl','-s',U+name],stdout=subprocess.PIPE)
    with gzip.open(p.stdout,'rt') as f:
        for line in f: yield line
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
titles=set(lk.title.map(norm))-{''}
step=sys.argv[1]
if step=='books':
    keep=[]; n=0
    for line in stream('goodreads_books.json.gz'):
        n+=1
        b=json.loads(line)
        if norm(b.get('title_without_series') or b.get('title','')) in titles:
            shelves={s['name']:int(s['count']) for s in b.get('popular_shelves',[])[:40]}
            keep.append(dict(book_id=b['book_id'],work_id=b.get('work_id'),title=b.get('title_without_series') or b['title'],
                authors=[a['author_id'] for a in b.get('authors',[])],ratings_count=int(b.get('ratings_count') or 0),
                text_reviews_count=int(b.get('text_reviews_count') or 0),to_read=shelves.get('to-read',0),
                language=b.get('language_code',''),pub_year=b.get('publication_year','')))
        if n%200000==0: print('books scanned',n,'kept',len(keep),flush=True)
    json.dump(keep,open(f'{D}/raw/goodreads_books_matched.json','w')); print('DONE books',n,len(keep),flush=True)
if step=='authors':
    need=set(a for b in json.load(open(f'{D}/raw/goodreads_books_matched.json')) for a in b['authors'])
    names={}
    for line in stream('goodreads_book_authors.json.gz'):
        a=json.loads(line)
        if a['author_id'] in need: names[a['author_id']]=a['name']
    json.dump(names,open(f'{D}/raw/goodreads_authors_matched.json','w')); print('DONE authors',len(names),flush=True)
if step=='reviews':
    ids=set(json.load(open(f'{D}/interim/goodreads_linked_book_ids.json')))
    monthly=collections.defaultdict(lambda: collections.Counter()); n=0
    for line in stream('goodreads_reviews_dedup.json.gz'):
        n+=1
        if '"book_id": "' in line:
            bid=line.split('"book_id": "',1)[1].split('"',1)[0]
            if bid in ids:
                r=json.loads(line); d=r.get('date_added','')   # e.g. 'Fri Aug 25 13:55:02 -0700 2017'
                try: ym=pd.to_datetime(d,format='%a %b %d %H:%M:%S %z %Y').strftime('%Y%m')
                except Exception: continue
                monthly[bid][ym]+=1
        if n%2000000==0: print('reviews scanned',n,'books with reviews',len(monthly),flush=True)
    json.dump({k:dict(v) for k,v in monthly.items()},open(f'{D}/raw/goodreads_reviews_monthly.json','w')); print('DONE reviews',n,len(monthly),flush=True)
