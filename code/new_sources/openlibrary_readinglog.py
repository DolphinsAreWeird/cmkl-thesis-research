# Open Library reading-log dump (CC0): download once, then profile it (structure only).
# Source: https://openlibrary.org/developers/dumps  ->  archive.org item ol_dump_YYYY-MM-DD
import sys, os, gzip, collections, requests, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from config import D, UA
URL = 'https://openlibrary.org/data/ol_dump_reading-log_latest.txt.gz'
out_dir = pathlib.Path(D) / 'raw' / 'openlibrary'; out_dir.mkdir(parents=True, exist_ok=True)
r = requests.head(URL, headers={'User-Agent': UA}, allow_redirects=True, timeout=60)
name = r.url.rsplit('/', 1)[1]; f = out_dir / name
import time
total = int(r.headers.get('Content-Length', 0))
tries = 0
while not f.exists():
    part = pathlib.Path(str(f) + '.part'); have = part.stat().st_size if part.exists() else 0
    try:
        with requests.get(r.url, headers={'User-Agent': UA, 'Range': f'bytes={have}-'}, stream=True, timeout=120) as g, open(part, 'ab') as w:
            g.raise_for_status()
            for chunk in g.iter_content(1 << 20): w.write(chunk)
        if total == 0 or part.stat().st_size >= total: os.replace(part, f)
    except Exception as e:
        tries += 1; print('download interrupted at', part.stat().st_size if part.exists() else 0, 'bytes; retry', tries, flush=True)
        if tries > 20: raise
        time.sleep(10)
print('file', f, round(f.stat().st_size / 1e6, 1), 'MB', flush=True)
shelves = collections.Counter(); years = collections.Counter(); n = 0; bad = 0; works = set(); sample = []
with gzip.open(f, 'rt', encoding='utf-8', errors='replace') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t'); n += 1
        if len(p) < 4: bad += 1; continue
        work, ed, shelf, date = p[0], p[1], p[2], p[3]
        shelves[shelf] += 1; years[(date[:4], shelf)] += 1; works.add(work)
        if n <= 3: sample.append(p[:4])
rep = pathlib.Path(D) / 'reports' / 'openlibrary_readinglog_profile.md'
L = ['# Open Library reading-log dump: profile', '', f'- file: {name} ({round(f.stat().st_size/1e6,1)} MB, CC0)', f'- rows: {n:,}; malformed: {bad:,}; distinct works: {len(works):,}',
     '- columns: work key, edition key (optional), shelf, date', f'- shelves: {dict(shelves)}', '', '| year | shelf | rows |', '| --- | --- | --- |']
L += [f'| {y} | {s} | {c:,} |' for (y, s), c in sorted(years.items())]
L += ['', 'Sample rows (keys only, no user data):'] + [f'- {s}' for s in sample]
rep.write_text('\n'.join(L) + '\n'); print('\n'.join(L[:8]))
