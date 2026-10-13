# Seattle Public Library: monthly checkouts by title (official open data, no key). Audiobooks and ebooks first, then print books.
import requests, json, time, os, pandas as pd
from config import D as DATA, UA; D=DATA+'/raw/modern'; U='https://data.seattle.gov/resource/tmmm-ytt6.json'
for mt in ['AUDIOBOOK','EBOOK','BOOK']:
    f=f'{D}/seattle_{mt.lower()}.jsonl'
    if os.path.exists(f) and os.path.getsize(f):   # drop a half-written last line left by a killed run
        with open(f,'rb+') as h:
            h.seek(-1,2)
            if h.read(1)!=b'\n':
                h.seek(0); buf=h.read(); h.truncate(buf.rfind(b'\n')+1)
    done=sum(1 for _ in open(f)) if os.path.exists(f) else 0
    off=done
    with open(f,'a') as out:
        while True:
            rows=None
            for k in range(6):
                try:
                    r=requests.get(U,params={'$select':'checkoutyear,checkoutmonth,checkouts,title,creator,subjects,publisher,publicationyear,isbn,usageclass','$where':f"materialtype='{mt}'",'$order':':id','$limit':50000,'$offset':off},headers={'User-Agent':UA},timeout=120)
                    if r.status_code==200: rows=r.json(); break
                except Exception: pass
                time.sleep(10)
            if rows is None: raise SystemExit(f'{mt}: 6 failed requests at offset {off}; rerun later (it resumes)')
            if not rows: break
            for x in rows: out.write(json.dumps(x)+'\n')
            off+=len(rows); print(mt,off,flush=True); time.sleep(1)
    print(mt,'DONE',off,flush=True)
print('ALLDONE',flush=True)
