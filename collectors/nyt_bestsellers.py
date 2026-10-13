"""Collect New York Times bestseller lists (all lists, weekly) from June 2008 to today.
Resumes where it stopped. Respects the NYT limits: 5 requests a minute, 500 a day.
Usage:  python nyt_bestsellers.py            (reads NYT_API_KEY from the .env file next to this script)
Output: data/nyt/YYYY-MM-DD.json, one file per week."""
import json, os, time, datetime, pathlib, requests
HERE=pathlib.Path(__file__).parent
def load_env():
    f=HERE/'.env'
    if f.exists():
        for line in f.read_text().splitlines():
            if '=' in line and not line.startswith('#'): k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip())
load_env(); KEY=os.environ.get('NYT_API_KEY')
OUT=HERE/'data'/'nyt'; OUT.mkdir(parents=True,exist_ok=True)
def sundays(start=datetime.date(2008,6,8)):
    d=start
    while d<=datetime.date.today(): yield d; d+=datetime.timedelta(days=7)
LOG=OUT/'_calls.json'   # time of every call in the last 24 hours, so two runs close together never pass the daily limit
def recent():
    t=json.loads(LOG.read_text()) if LOG.exists() else []
    return [x for x in t if x>time.time()-86400]
def main(max_calls=480):
    if not KEY: raise SystemExit('Put NYT_API_KEY=... in the .env file first.')
    stamps=recent(); calls=len(stamps)
    for d in sundays():
        f=OUT/f'{d}.json'
        if f.exists(): continue
        if calls>=max_calls: print('Daily budget used (480 calls in the last 24 hours); run again tomorrow.'); return
        for attempt in range(5):
            r=requests.get('https://api.nytimes.com/svc/books/v3/lists/overview.json',params={'published_date':str(d),'api-key':KEY},timeout=60)
            calls+=1; stamps.append(time.time()); LOG.write_text(json.dumps(stamps))
            if r.status_code==200:
                res=r.json().get('results',{})
                keep=[dict(list=l.get('list_name'),books=[dict(rank=b.get('rank'),weeks_on_list=b.get('weeks_on_list'),title=b.get('title'),author=b.get('author'),
                      isbn13=b.get('primary_isbn13'),publisher=b.get('publisher'),description=b.get('description')) for b in (l.get('books') or [])]) for l in (res.get('lists') or [])]   # 2008 weeks return no lists: saved empty
                f.write_text(json.dumps(dict(requested=str(d),published=res.get('published_date'),lists=keep)))
                print('saved',d,flush=True); break
            if r.status_code==429: time.sleep(60); continue
            print('error',r.status_code,d); time.sleep(15)
        time.sleep(12.5)   # 5 requests a minute
    print('All weeks collected up to today.')
if __name__=='__main__': main()
