# 00. Reference counts from the official SPL open-data API (data.seattle.gov, no key), used only to check
# how complete the local files are. A handful of small aggregate queries; nothing is written to data/raw.
# Output: data/db/taxonomy_v2/spl_api_counts.parquet, spl_book_subject_sample.json
import requests, time, pandas as pd
from _common import OUT, UA, save_json, snapshot

U = 'https://data.seattle.gov/resource/tmmm-ytt6.json'
H = {'User-Agent': UA}


def get(params):
    for k in range(5):
        try:
            r = requests.get(U, params=params, headers=H, timeout=180)
            if r.status_code == 200:
                return r.json()
            print('status', r.status_code, r.text[:200], flush=True)
        except Exception as e:
            print('retry', str(e)[:100], flush=True)
        time.sleep(15)
    raise SystemExit('API failed')


snap = snapshot()          # freeze the ebook line count at the same moment
print('snapshot', snap, flush=True)
rows = []
for mt in ['AUDIOBOOK', 'EBOOK', 'BOOK']:
    j = get({'$select': 'checkoutyear,checkoutmonth,count(*) AS n_rows,sum(checkouts) AS checkouts',
             '$where': f"materialtype='{mt}'", '$group': 'checkoutyear,checkoutmonth', '$limit': 5000})
    for x in j:
        rows.append(dict(materialtype=mt, year=int(x['checkoutyear']), month=int(x['checkoutmonth']),
                         n_rows=int(x['n_rows']), checkouts=int(float(x['checkouts']))))
    print(mt, len(j), 'months', flush=True)
    time.sleep(2)
a = pd.DataFrame(rows).sort_values(['materialtype', 'year', 'month'])
a['api_queried'] = time.strftime('%Y-%m-%d %H:%M')
a.to_parquet(f'{OUT}/spl_api_counts.parquet', index=False)
print(a.groupby('materialtype')[['n_rows', 'checkouts']].sum(), flush=True)

# checkout types behind the digital rows (not in the local files), by material type
ct = get({'$select': 'materialtype,checkouttype,usageclass,count(*) AS n_rows,sum(checkouts) AS checkouts',
          '$where': "materialtype in('AUDIOBOOK','EBOOK','BOOK')", '$group': 'materialtype,checkouttype,usageclass', '$limit': 100})
pd.DataFrame(ct).to_csv(f'{OUT}/spl_api_checkouttype.csv', index=False)
print(pd.DataFrame(ct), flush=True)
time.sleep(2)

# a small sample of print-book rows, to see how their subject headings are written (for later use)
smp = get({'$select': 'checkoutyear,checkoutmonth,title,creator,subjects', '$where': "materialtype='BOOK' AND checkoutyear=2019 AND checkoutmonth=6",
           '$order': 'checkouts DESC', '$limit': 40})
save_json(smp, f'{OUT}/spl_book_subject_sample.json')
for x in smp[:12]:
    print(x.get('title', '')[:60], '|', x.get('subjects', '')[:160])
