# Wikipedia clickstream (CC0, monthly, English): keep only clicks into or out of the project's topic pages.
# Months: the 18 months with the most quality-ok Wikipedia shifts (sustained or large) since 2018-01, plus 6 quiet months
# (no such shift) drawn with seed 20261013. One month is downloaded at a time, reduced, then the raw file is deleted.
import sys, os, gzip, pathlib, requests, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA
DB = pathlib.Path(D) / 'db'; out = DB / 'clickstream'; out.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(D) / 'raw' / '_download'; tmp.mkdir(parents=True, exist_ok=True)
pages = pd.read_parquet(DB / 'interest' / 'wiki' / 'articles.parquet')
topic = set(pages['canonical'].dropna().astype(str).str.replace(' ', '_'))
s = pd.read_parquet(DB / 'interest' / 'shifts.parquet'); s['start_week'] = pd.to_datetime(s.start_week)
s = s[(s.source == 'wikipedia') & s.quality_ok.astype(bool) & (s.start_week >= '2018-01-01') & s.label.isin(['sustained', 'intermediate', 'fading'])]
s = s[(s.label == 'sustained') | (s['size'] >= 3)]
by = s.groupby(s.start_week.dt.to_period('M')).size().sort_values(ascending=False)
last = pd.Period('2026-09', 'M'); allm = pd.period_range('2018-01', last, freq='M')
busy = list(by.index[:18]); quiet_pool = [m for m in allm if m not in set(by.index)]
rng = np.random.default_rng(20261013); quiet = list(rng.choice(np.array(quiet_pool, dtype=object), size=min(6, len(quiet_pool)), replace=False))
months = sorted(set(busy) | set(quiet))
pd.DataFrame({'month': [str(m) for m in months], 'kind': ['busy' if m in busy else 'quiet' for m in months]}).to_csv(out / 'months.csv', index=False)
print('months', [str(m) for m in months], flush=True)
for m in months:
    dst = out / f'clickstream_{m}.parquet'
    if dst.exists(): continue
    url = f'https://dumps.wikimedia.org/other/clickstream/{m}/clickstream-enwiki-{m}.tsv.gz'
    f = tmp / url.rsplit('/', 1)[1]
    with requests.get(url, headers={'User-Agent': UA}, stream=True, timeout=120) as g:
        if g.status_code != 200: print(m, 'HTTP', g.status_code, flush=True); continue
        with open(str(f) + '.part', 'wb') as w:
            for chunk in g.iter_content(1 << 20): w.write(chunk)
    os.replace(str(f) + '.part', f)
    rows = []
    with gzip.open(f, 'rt', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            p = line.rstrip('\n').split('\t')
            if len(p) != 4: continue
            if p[0] in topic or p[1] in topic: rows.append((p[0], p[1], p[2], int(p[3])))
    pd.DataFrame(rows, columns=['prev', 'curr', 'type', 'n']).to_parquet(dst, index=False)
    f.unlink(); print(m, 'kept rows', len(rows), flush=True)
print('DONE', flush=True)
