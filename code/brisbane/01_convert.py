# 01. Brisbane 2015-2022: raw CSV (downloaded from the Brisbane City Council open-data portal, CC BY 4.0) -> one parquet per year with the
# same columns as the 2023-2025 files (title, author, call_number, age, checkout_library, date); the raw CSV is deleted after conversion.
# The CSV is untrusted data: run with `python -I`. Writes data/raw/brisbane/library-checkouts-YYYY.parquet and data/reports/brisbane_download_profile.md
import sys, pathlib, os
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[2]
RAWDL = ROOT / 'data' / 'raw' / 'brisbane_dl'
OUT = ROOT / 'data' / 'raw' / 'brisbane'
SRC = {'library-checkouts-branch-date-2015-2019.csv': 'https://data.brisbane.qld.gov.au/explore/dataset/library-checkouts-branch-date-2015-2019 (also data.qld.gov.au, CC-BY-4.0)',
       'library-checkouts-2020-2022.csv': 'https://data.brisbane.qld.gov.au/explore/dataset/library-checkouts-2020-2022 (also data.qld.gov.au, CC-BY-4.0)'}
COLS = ['title', 'author', 'call_number', 'age', 'checkout_library', 'date']
lines = ['# Brisbane library checkouts 2015-2022: download and conversion log', '']
import pyarrow as pa, pyarrow.parquet as pq
writers, counts, dmin, dmax, days, baddate = {}, {}, {}, {}, {}, {}
SCHEMA = pa.schema([(c, pa.string()) for c in COLS])
for name, url in SRC.items():
    f = RAWDL / name
    n = 0
    for ch in pd.read_csv(f, dtype=str, chunksize=200_000, usecols=COLS, encoding='utf-8-sig', keep_default_na=False):
        ch = ch[COLS]
        for c in COLS:
            ch[c] = ch[c].replace('', None)
        yr = ch['date'].str[:4]
        for y, g in ch.groupby(yr):
            if not y.isdigit():
                lines.append(f'- WARNING: {len(g):,} rows with a bad year value {y!r}, left out')
                continue
            if y not in writers:
                writers[y] = pq.ParquetWriter(OUT / f'library-checkouts-{y}.parquet', SCHEMA)
                counts[y], days[y], baddate[y] = 0, set(), 0
            writers[y].write_table(pa.Table.from_pandas(g, schema=SCHEMA, preserve_index=False))
            counts[y] += len(g)
            dt = pd.to_datetime(g['date'], errors='coerce', utc=True)
            days[y] |= set(dt.dt.date.dropna().unique()); baddate[y] += int(dt.isna().sum())
        n += len(ch)
    lines.append(f'- {name}: {f.stat().st_size / 1e6:.1f} MB CSV, {n:,} rows; source {url}')
for w in writers.values():
    w.close()
for y in sorted(writers):
    p = OUT / f'library-checkouts-{y}.parquet'
    lines.append(f'- {p.name}: {counts[y]:,} loans, {len(days[y])} distinct days sampled, {min(days[y])} to {max(days[y])}, {p.stat().st_size / 1e6:.1f} MB, unparsable dates {baddate[y]}')
for name in SRC:
    (RAWDL / name).unlink()
for y in (2023, 2024, 2025):
    p = OUT / f'library-checkouts-{y}.parquet'
    d = pd.read_parquet(p, columns=['date'])
    dt = pd.to_datetime(d['date'], errors='coerce', utc=True)
    lines.append(f'- {p.name} (already in the project): {len(d):,} loans, {dt.dt.date.nunique()} distinct days, {dt.min().date()} to {dt.max().date()}, {p.stat().st_size / 1e6:.1f} MB')
(ROOT / 'data' / 'reports' / 'brisbane_download_profile.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
