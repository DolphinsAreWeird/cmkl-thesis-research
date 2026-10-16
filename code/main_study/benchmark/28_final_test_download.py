# Final unseen test: download the months that the Seattle open data (Checkouts by Title, data.seattle.gov, resource tmmm-ytt6) release after August 2026.
# REFUSES TO RUN unless addendum d (targets, scoring and decisions of the final test) exists and has the SHA-256 printed in prereg/README.md: no month after 2026-08
# is to be downloaded before the scoring rules are fixed (addendum c).
# One JSON-lines file per material type and month in data/raw/modern/final_test/ (the same fields as code/seattle.py), the API's own row and checkout counts per
# month in data/db/final_test/new_months_api_counts.parquet. A month counts as released only when all three material types have rows and the downloaded row
# count equals the API's count asked again after the download.
#   ../../../.venv/bin/python 28_final_test_download.py --list                 (counts only: which months the API holds; reads no title or value)
#   ../../../.venv/bin/python 28_final_test_download.py --months 2026-09       (download)
import sys, os, re, json, time, pathlib, argparse, hashlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import requests, pandas as pd
from config import D, UA

URL = 'https://data.seattle.gov/resource/tmmm-ytt6.json'
H = {'User-Agent': UA}
TYPES = ['AUDIOBOOK', 'EBOOK', 'BOOK']
SELECT = 'checkoutyear,checkoutmonth,checkouts,title,creator,subjects,publisher,publicationyear,isbn,usageclass'
RAW = pathlib.Path(D) / 'raw' / 'modern' / 'final_test'
OUT = pathlib.Path(D) / 'db' / 'final_test'
PREREG = HERE.parents[2] / 'prereg'


def guard():
    cand = sorted((PREREG / 'addenda_benchmark').glob('*_d_final_test_*.json'))
    if not cand:
        raise SystemExit('addendum d (final test: targets, scoring, decisions) does not exist yet; no month after 2026-08 is downloaded before it is fixed')
    f = cand[-1]
    text = (PREREG / 'README.md').read_text()
    i = text.find(f.name)
    m = re.search(r'SHA-256:\s*([0-9a-f]{64})', text[i:i + 600]) if i >= 0 else None
    got = hashlib.sha256(f.read_bytes()).hexdigest()
    if not m or m.group(1) != got:
        raise SystemExit(f'{f.name} is not fingerprinted in prereg/README.md (or was changed): download refused')
    return f.name, got


def get(params, tries=6):
    for k in range(tries):
        try:
            r = requests.get(URL, params=params, headers=H, timeout=180)
            if r.status_code == 200:
                return r.json()
            print('status', r.status_code, r.text[:200], flush=True)
        except Exception as e:
            print('retry', str(e)[:100], flush=True)
        time.sleep(10 * (k + 1))
    raise SystemExit('API failed')


def api_counts(year=None, month=None):
    rows = []
    for mt in TYPES:
        where = f"materialtype='{mt}'" + (f" AND checkoutyear='{year}' AND checkoutmonth='{month}'" if year else " AND checkoutyear>='2026'")
        j = get({'$select': 'checkoutyear,checkoutmonth,count(*) AS n_rows,sum(checkouts) AS checkouts', '$where': where, '$group': 'checkoutyear,checkoutmonth', '$limit': 5000})
        for x in j:
            rows.append(dict(materialtype=mt, year=int(x['checkoutyear']), month=int(x['checkoutmonth']), n_rows=int(x['n_rows']), checkouts=int(float(x['checkouts']))))
        time.sleep(1)
    a = pd.DataFrame(rows)
    if len(a):
        a = a.sort_values(['materialtype', 'year', 'month']).reset_index(drop=True)
        a['api_queried'] = time.strftime('%Y-%m-%d %H:%M')
    return a


def download(year, month):
    got = {}
    for mt in TYPES:
        f = RAW / f'seattle_{mt.lower()}_{year}-{month:02d}.jsonl'
        if f.exists() and f.stat().st_size:
            got[mt] = sum(1 for _ in open(f))
            continue
        off, n = 0, 0
        tmp = f.with_suffix('.part')
        with open(tmp, 'w') as out:
            while True:
                rows = get({'$select': SELECT, '$where': f"materialtype='{mt}' AND checkoutyear='{year}' AND checkoutmonth='{month}'", '$order': ':id', '$limit': 50000, '$offset': off})
                if not rows:
                    break
                for x in rows:
                    out.write(json.dumps(x) + '\n')
                off += len(rows); n += len(rows)
                print(mt, year, month, n, flush=True)
                time.sleep(1)
        os.replace(tmp, f)
        got[mt] = n
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--months', default=None, help='YYYY-MM,YYYY-MM')
    a = ap.parse_args()
    if a.list:
        # counts only; this reads no title, subject or checkout value of any month. It is allowed before addendum d (data availability).
        c = api_counts()
        print(c[c.year * 12 + c.month >= 2026 * 12 + 7].to_string(index=False))
        return
    name, sha = guard()
    print('addendum d', name, sha, flush=True)
    RAW.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for ym in a.months.split(','):
        y, m = int(ym[:4]), int(ym[5:7])
        c = api_counts(y, m)
        if set(c.materialtype) != set(TYPES):
            print(f'{ym}: not released for all material types ({sorted(set(c.materialtype))}); skipped', flush=True)
            continue
        got = download(y, m)
        c2 = api_counts(y, m)
        ok = all(got[mt] == int(c2[c2.materialtype == mt].n_rows.iloc[0]) for mt in TYPES)
        print(f'{ym}: downloaded {got}; API rows {dict(zip(c2.materialtype, c2.n_rows))}; complete: {ok}', flush=True)
        c2['downloaded_rows'] = c2.materialtype.map(got)
        c2['complete'] = ok
        rows.append(c2)
    if rows:
        new = pd.concat(rows, ignore_index=True)
        f = OUT / 'new_months_api_counts.parquet'
        if f.exists():
            old = pd.read_parquet(f)
            new = pd.concat([old[~old.set_index(['materialtype', 'year', 'month']).index.isin(new.set_index(['materialtype', 'year', 'month']).index)], new], ignore_index=True)
        new.to_parquet(f, index=False)
        print('wrote', f, flush=True)


if __name__ == '__main__':
    main()
