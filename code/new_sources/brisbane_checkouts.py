# Brisbane City Council library checkouts (CC BY 4.0): single-day loan snapshots, 2023-2025.
# Keeps title, author, call number, item type, age group, branch and timestamp. No personal data exists in the source.
import sys, io, requests, pathlib, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA
out = pathlib.Path(D) / 'raw' / 'brisbane'; out.mkdir(parents=True, exist_ok=True)
lines = ['# Brisbane library checkouts: download log', '']
for yr in (2023, 2024, 2025):
    ds = f'library-checkouts-{yr}'
    url = f'https://data.brisbane.qld.gov.au/api/explore/v2.1/catalog/datasets/{ds}/exports/csv?delimiter=%2C'
    r = requests.get(url, headers={'User-Agent': UA}, timeout=600)
    if r.status_code != 200:
        lines.append(f'- {ds}: HTTP {r.status_code}, skipped'); print(ds, r.status_code, flush=True); continue
    df = pd.read_csv(io.BytesIO(r.content), dtype=str)
    keep = [c for c in ['title', 'author', 'call_number', 'item_type', 'age', 'checkout_library', 'date'] if c in df.columns]
    df = df[keep]; df.to_parquet(out / f'{ds}.parquet', index=False)
    d = pd.to_datetime(df['date'], errors='coerce', utc=True)
    lines.append(f'- {ds}: {len(r.content)/1e6:.1f} MB transferred, {len(df):,} loans, {d.dt.date.nunique()} distinct days, {d.min()} to {d.max()}; kept columns {keep}')
    print(lines[-1], flush=True)
(pathlib.Path(D) / 'reports' / 'brisbane_checkouts_profile.md').write_text('\n'.join(lines) + '\n')
