# Amazon Reviews 2023, Books reviews, streamed from the dataset authors' Hugging Face copy (McAuley-Lab/Amazon-Reviews-2023)
# instead of the slow UCSD server. Same output as modern_books.py: monthly review counts per parent_asin, only for books
# kept in amazon_books_meta.jsonl. No review text or reviewer ID is kept. Resumes by byte offset if the connection drops.
import sys, os, json, time, collections, pathlib, requests
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA
D = os.path.join(D, 'raw', 'modern') if not os.path.exists(os.path.join(D, 'amazon_books_meta.jsonl')) else D
URL = 'https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/review_categories/Books.jsonl'
aids = {json.loads(l)['asin'] for l in open(os.path.join(D, 'amazon_books_meta.jsonl'))}
print('books kept from meta:', len(aids), flush=True)
mon = collections.defaultdict(collections.Counter); off = 0; n = 0; t0 = time.time(); tries = 0
while True:
    try:
        with requests.get(URL, headers={'User-Agent': UA, 'Range': f'bytes={off}-'}, stream=True, timeout=120) as r:
            r.raise_for_status(); buf = b''
            for chunk in r.iter_content(1 << 22):
                buf += chunk; lines = buf.split(b'\n'); buf = lines.pop()
                for b in lines:
                    off += len(b) + 1; n += 1
                    line = b.decode('utf-8', 'replace')
                    try:
                        pa = line.split('"parent_asin": "', 1)[1].split('"', 1)[0]
                        if pa in aids:
                            ts = int(line.split('"timestamp": ', 1)[1].split(',', 1)[0].split('}', 1)[0])
                            mon[pa][time.strftime('%Y%m', time.gmtime(ts / 1000))] += 1
                    except Exception: pass
                    if n % 3000000 == 0: print('amazon reviews', n, len(mon), f'{off/1e9:.1f} GB', f'{off/1e6/(time.time()-t0):.1f} MB/s', flush=True)
            if buf.strip():
                off += len(buf); n += 1
        break
    except Exception as e:
        tries += 1; print('connection error, resuming at byte', off, repr(e)[:120], flush=True)
        if tries > 20: raise
        time.sleep(10)
tmp = os.path.join(D, 'amazon_reviews_monthly.json.part')
with open(tmp, 'w') as f: json.dump({k: dict(v) for k, v in mon.items()}, f)
os.replace(tmp, os.path.join(D, 'amazon_reviews_monthly.json'))
print('amazon reviews done', n, len(mon), f'{(time.time()-t0)/60:.0f} min', flush=True)
