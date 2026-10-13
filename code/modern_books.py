# Modern books with performance over time, streamed from the source (nothing large saved to disk).
#  A) Goodreads (UCSD): books with >= 1,000 ratings, full metadata, genres, top shelves; monthly review counts to 2017.
#  B) Amazon Reviews 2023: Books with >= 500 ratings, full metadata and category path; monthly review counts to 2023.
import json, gzip, subprocess, collections, os, time, pandas as pd
from config import D as DATA; D=DATA+'/raw/modern'
import requests
from config import UA
def stream(url):
    # Download with resume (a dropped connection no longer restarts a multi-GB pass), read the local copy, delete it after.
    os.makedirs(f'{D}/_download',exist_ok=True); f=f"{D}/_download/{url.rsplit('/',1)[1]}"
    total=int(requests.head(url,headers={'User-Agent':UA},allow_redirects=True,timeout=60).headers['Content-Length'])
    while (have:=os.path.getsize(f) if os.path.exists(f) else 0)<total:
        try:
            with requests.get(url,headers={'User-Agent':UA,'Range':f'bytes={have}-'},stream=True,timeout=120) as r:
                r.raise_for_status()
                if have and r.status_code!=206: raise SystemExit('server ignored the resume request')
                with open(f,'ab') as out:
                    for chunk in r.iter_content(1<<20): out.write(chunk)
        except requests.RequestException as e: print('download retry:',str(e)[:80],flush=True); time.sleep(30)
        print('downloaded',url.rsplit('/',1)[1],round(os.path.getsize(f)/1e9,2),'of',round(total/1e9,2),'GB',flush=True)
    with gzip.open(f,'rt',encoding='utf-8',errors='ignore') as g:
        for line in g: yield line
    os.remove(f)
def save_json(obj,path):   # write then rename, so a crash never leaves a half file that looks finished
    with open(path+'.part','w') as out: json.dump(obj,out)
    os.replace(path+'.part',path)
G='https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/'
if not os.path.exists(f'{D}/goodreads_books_meta.jsonl'):
    keep={}; n=0
    with open(f'{D}/goodreads_books_meta.jsonl','w') as out:
        for line in stream(G+'goodreads_books.json.gz'):
            n+=1; b=json.loads(line)
            if int(b.get('ratings_count') or 0)>=1000 and (b.get('language_code') or 'eng').startswith('en'):
                rec=dict(book_id=b['book_id'],work_id=b.get('work_id'),title=b.get('title_without_series') or b.get('title'),authors=[a['author_id'] for a in b.get('authors',[])],
                         year=b.get('publication_year'),pages=b.get('num_pages'),publisher=b.get('publisher'),format=b.get('format'),description=(b.get('description') or '')[:2000],
                         ratings=int(b.get('ratings_count') or 0),avg=b.get('average_rating'),series=b.get('series'),shelves=[(s['name'],int(s['count'])) for s in b.get('popular_shelves',[])[:25]])
                out.write(json.dumps(rec)+'\n'); keep[b['book_id']]=1
            if n%500000==0: print('goodreads books',n,len(keep),flush=True)
    print('goodreads modern kept',len(keep),flush=True)
ids={json.loads(l)['book_id'] for l in open(f'{D}/goodreads_books_meta.jsonl')}
if not os.path.exists(f'{D}/goodreads_genres.json'):
    gen={}
    for line in stream(G+'goodreads_book_genres_initial.json.gz'):
        r=json.loads(line)
        if r['book_id'] in ids: gen[r['book_id']]=r['genres']
    save_json(gen,f'{D}/goodreads_genres.json'); print('genres',len(gen),flush=True)
if not os.path.exists(f'{D}/goodreads_reviews_monthly.json'):
    mon=collections.defaultdict(collections.Counter); n=0
    for line in stream(G+'goodreads_reviews_dedup.json.gz'):
        n+=1
        bid=line.split('"book_id": "',1)[1].split('"',1)[0] if '"book_id": "' in line else None
        if bid in ids:
            d=line.split('"date_added": "',1)[1].split('"',1)[0] if '"date_added": "' in line else ''
            try: ym=time.strftime('%Y%m',time.strptime(d,'%a %b %d %H:%M:%S %z %Y'))
            except Exception: continue
            mon[bid][ym]+=1
        if n%3000000==0: print('goodreads reviews',n,len(mon),flush=True)
    save_json({k:dict(v) for k,v in mon.items()},f'{D}/goodreads_reviews_monthly.json'); print('goodreads reviews done',len(mon),flush=True)
A='https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/'
if not os.path.exists(f'{D}/amazon_books_meta.jsonl'):
    n=k=0
    with open(f'{D}/amazon_books_meta.jsonl.part','w') as out:
        for line in stream(A+'meta_categories/meta_Books.jsonl.gz'):
            n+=1; m=json.loads(line)
            if (m.get('rating_number') or 0)>=500:
                det=m.get('details') or {}
                rec=dict(asin=m.get('parent_asin'),title=m.get('title'),author=(m.get('author') or {}).get('name') if isinstance(m.get('author'),dict) else m.get('store'),
                         categories=m.get('categories'),ratings=m.get('rating_number'),avg=m.get('average_rating'),price=m.get('price'),
                         publisher=det.get('Publisher'),date=det.get('Publication date') or det.get('Publisher'),language=det.get('Language'),pages=det.get('Print length') or det.get('Paperback') or det.get('Hardcover'),
                         description=' '.join(m.get('description') or [])[:2000],features=' '.join(m.get('features') or [])[:1000])
                out.write(json.dumps(rec)+'\n'); k+=1
            if n%500000==0: print('amazon meta',n,k,flush=True)
    os.replace(f'{D}/amazon_books_meta.jsonl.part',f'{D}/amazon_books_meta.jsonl'); print('amazon modern kept',k,flush=True)
aids={json.loads(l)['asin'] for l in open(f'{D}/amazon_books_meta.jsonl')}
if not os.path.exists(f'{D}/amazon_reviews_monthly.json'):
    mon=collections.defaultdict(collections.Counter); n=0
    for line in stream(A+'review_categories/Books.jsonl.gz'):
        n+=1
        try:
            pa=line.split('"parent_asin": "',1)[1].split('"',1)[0]
            if pa in aids:
                ts=int(line.split('"timestamp": ',1)[1].split(',',1)[0].split('}',1)[0]); mon[pa][time.strftime('%Y%m',time.gmtime(ts/1000))]+=1
        except Exception: pass
        if n%3000000==0: print('amazon reviews',n,len(mon),flush=True)
    save_json({k:dict(v) for k,v in mon.items()},f'{D}/amazon_reviews_monthly.json'); print('amazon reviews done',len(mon),flush=True)
print('ALLDONE',flush=True)
