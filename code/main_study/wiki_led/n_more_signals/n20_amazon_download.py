# n20. Addendum n, part 2 (AZ, Amazon reviews), step 1: stream the two Amazon Reviews 2023 files and reduce them while streaming.
# DATA ONLY: no model, nothing related to loans.  Nothing raw is written to disk and user ids are never stored, written or printed.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_2_amazon_reviews (read-only; SHA-256 checked).
# The content is untrusted data: run with python -I from code/ (away from the data folder); nothing from the files is executed or
# printed (the log holds counts only).
#
# Choices the record leaves open (also in data/db/wiki_led/n_more_signals/notes_amazon.md, decided 2026-11-25 16:45 +07:00 before
# this script was run):
#   A1 Client: urllib, generic user agent 'research-data-client/1.0'; a HEAD first; size and ETag must equal those seen when the record
#      was fixed (602,182,123 and 4,942,125,770 bytes) or the script stops.  Compressed bytes go straight into a zlib decompressor.
#   A2 Resume: on a network error the stream reopens at the compressed byte reached (Range + If-Range: ETag; a changed file answers 200
#      and the script stops), keeping the decompressor state (back-off up to 60 s; amended 2026-11-25 19:08 +07:00, before any meta
#      output: at most 200 failures in a row, the count reset after each received chunk, socket timeout 60 s, because the Mac sleeps
#      and changes networks; first rule was 40 retries in all).  Amended again 2026-11-25 19:13 +07:00, before any meta output: the
#      file is fetched as consecutive 8 MiB byte ranges, at most 3 at a time, handed to the one decompressor strictly in order; each
#      range must answer 206 with the exact Content-Range (If-Range: ETag) and full length, and is retried on its own (200 failures in a
#      row at most), because one connection gave about 0.2 MB/s on the current network.  A gzip stream cannot be
#      re-entered from a new process, so after a crash the meta file is streamed again from byte 0 and the lines already reduced
#      (checkpoint after each part of 250,000 lines) are skipped without parsing.  The ratings file has no cross-process checkpoint;
#      a finished output of either file is not redone.
#   A3 Decompression gives at most 8 MB per step; a line longer than 64 MB is skipped and counted.
#   A4 Ratings rows: header must be 'user_id,parent_asin,rating,timestamp'; kept when exactly 4 comma fields, parent_asin of 10
#      characters 0-9/A-Z, rating 1..5 (integer or '.0'), integer millisecond time stamp 1995-07-01 .. 2025-01-31 UTC.  Others counted
#      and dropped.  The user id field is dropped on each line.  No deduplication (would need the user id).
#   A5 Month = UTC calendar month of the time stamp, mi = year * 12 + month - 1.  Output per (parent_asin, mi): n and rsum; monthly
#      totals over all kept rows.
#   A6 Meta lines: json.loads inside a guard; not an object or bad parent_asin -> dropped and counted.  Kept: parent_asin, title (string
#      else ''), author name (author.name when author is an object and name a string, else ''), control characters removed, white
#      space collapsed, cut to 500 (title) / 200 (author) characters.
#   A7 ISBNs from details only, keys 'ISBN 10' / 'ISBN 13' (any case; space, hyphen or nothing before the number), string values reduced
#      to digits, X and hyphens, cut to 20 characters, kept as given (normalized in n21).  The parent_asin is not used as an ISBN, nor
#      'Page numbers source ISBN'.
#   A8 Publication date (kept, unused): details['Publication date']; else the text in the last parentheses of details['Publisher'] if it
#      holds a four-digit year; else the text after the last dash of subtitle if it holds one; cut to 40 characters; pub_year = first
#      four-digit year 1400-2025 in it.
#   A9 A parent_asin on two meta lines keeps its first line (counted).  Intermediate meta parts are deleted after the final file.
#
# Outputs (data/db/wiki_led/n_more_signals/amazon/): ratings_item_month.parquet (parent_asin, mi, n, rsum),
#   ratings_month_totals.parquet (mi, n, rsum), meta_items.parquet (parent_asin, title, author, isbn10, isbn13, pub_date, pub_year),
#   download_summary.json.
# Run from handoff/:  nice -n 10 bash jobs/bg.sh n20_amazon -I main_study/wiki_led/n_more_signals/n20_amazon_download.py [ratings|meta|all]
import sys, os, io, re, json, time, zlib, hashlib, pathlib, resource, socket, threading, concurrent.futures, http.client, urllib.request, \
    urllib.error, unicodedata
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]                                          # handoff/
assert (ROOT / 'prereg').is_dir() and (ROOT / 'code').is_dir(), ROOT
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
OUT = ROOT / 'data' / 'db' / 'wiki_led' / 'n_more_signals' / 'amazon'
OUT.mkdir(parents=True, exist_ok=True)
PARTS = OUT / '_parts_meta'
BASE = 'https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/'
FILES = {
    'ratings': dict(url=BASE + 'benchmark/0core/rating_only/Books.csv.gz', size=602182123, etag='"23e491eb-62bd8a1487136"'),
    'meta': dict(url=BASE + 'raw/meta_categories/meta_Books.jsonl.gz', size=4942125770, etag='"12692daca-62bda188a2719"'),
}
UA = 'research-data-client/1.0'
MAX_FAILS = 200                          # A2 (amended 2026-11-25 19:08 +07:00): failures in a row (now per range)
BLK = 8 << 20                            # A2 (amended 2026-11-25 19:13 +07:00): byte ranges of 8 MiB
NCONN = 3                                # A2 (amended 2026-11-25 19:13 +07:00): at most 3 ranges fetched at once
OUT_STEP = 8 << 20                       # A3
MAXLINE = 64 << 20                       # A3
META_PART = 250_000                      # A2
RAT_CHUNK = 2_000_000
TS_LO = int(pd.Timestamp('1995-07-01', tz='UTC').value // 10 ** 6)     # A4, ms
TS_HI = int(pd.Timestamp('2025-02-01', tz='UTC').value // 10 ** 6)     # exclusive: up to 2025-01-31
T0 = time.time()
try:
    os.nice(5)
except OSError:
    pass


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB',
          *a, flush=True)


def atomic_json(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, default=int))
    os.replace(tmp, path)


def atomic_parquet(df, path):
    tmp = path.with_suffix('.tmp')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


# ---------------------------------------------------------------- A1, A2, A3: resumable gzip stream (decompressed bytes, in memory)
class FileChanged(Exception):
    pass


class GzStream(io.RawIOBase):
    """Compressed file fetched as consecutive byte ranges of BLK bytes over NCONN connections (A2, amended 19:13), handed to one zlib
    decompressor strictly in order; each range is retried on its own; nothing is written to disk."""
    def __init__(self, name):
        f = FILES[name]
        self.name, self.url, self.size, self.etag = name, f['url'], f['size'], f['etag']
        self.pos = 0                 # compressed bytes handed to the decompressor
        self.d = zlib.decompressobj(31)
        self.pending = b''           # compressed bytes not yet fed (bounded output)
        self.buf = b''
        self.bpos = 0
        self.eof = False
        self.retries = 0             # all retries
        self.out_bytes = 0
        self.members = 0
        self.fed = False
        self.lock = threading.Lock()
        self.nblocks = -(-self.size // BLK)
        self.pool = concurrent.futures.ThreadPoolExecutor(NCONN)
        self.futs = {}
        self.next_req = 0
        self.next_get = 0
        self._head()

    def _head(self):
        r = urllib.request.urlopen(urllib.request.Request(self.url, method='HEAD', headers={'User-Agent': UA}), timeout=120)
        size, etag = int(r.headers.get('Content-Length', -1)), r.headers.get('ETag')
        r.close()
        assert size == self.size and etag == self.etag, f'{self.name}: file on the server differs from the one seen when the record was fixed'

    def _fetch(self, k):
        a = k * BLK
        b = min(self.size, a + BLK) - 1
        h = {'User-Agent': UA, 'Accept-Encoding': 'identity', 'Range': f'bytes={a}-{b}', 'If-Range': self.etag}
        fails = 0
        while True:
            try:
                r = urllib.request.urlopen(urllib.request.Request(self.url, headers=h), timeout=60)
                try:
                    if r.status != 206 or r.headers.get('Content-Range', '') != f'bytes {a}-{b}/{self.size}' \
                            or r.headers.get('ETag') not in (None, self.etag):
                        raise FileChanged(f'{self.name}: range {a}-{b} answered {r.status}; the file may have changed')
                    data = r.read()
                finally:
                    r.close()
                if len(data) != b - a + 1:
                    raise ConnectionError('short range')
                return data
            except (socket.timeout, TimeoutError, ConnectionError, http.client.HTTPException, urllib.error.URLError, OSError) as e:
                fails += 1
                with self.lock:
                    self.retries += 1
                if fails > MAX_FAILS:
                    raise
                wait = min(60, 2 ** min(fails, 6))
                log(f'{self.name}: network error ({type(e).__name__}) in range {k} of {self.nblocks}; retry {fails} of this range in {wait}s')
                time.sleep(wait)

    def _read_net(self):
        while self.next_req < self.nblocks and self.next_req < self.next_get + NCONN + 1:
            self.futs[self.next_req] = self.pool.submit(self._fetch, self.next_req)
            self.next_req += 1
        if self.next_get >= self.nblocks:
            self.pool.shutdown(wait=False)
            return b''
        data = self.futs.pop(self.next_get).result()
        self.next_get += 1
        return data

    def _fill(self):
        while self.bpos >= len(self.buf) and not self.eof:
            if not self.pending:
                if self.pos >= self.size:                       # all compressed bytes received
                    tail = b''
                    if self.fed:
                        tail = self.d.flush()
                        assert self.d.eof, f'{self.name}: gzip stream incomplete'
                    self.buf, self.bpos, self.eof = tail, 0, True
                    self.out_bytes += len(tail)
                    return
                chunk = self._read_net()
                self.pos += len(chunk)
                self.pending = chunk
            if not self.fed:
                self.fed = True
                self.members += 1
            out = self.d.decompress(self.pending, OUT_STEP)
            self.pending = self.d.unconsumed_tail
            if self.d.eof:                                      # member finished; the rest (if any) starts the next member
                self.pending = self.d.unused_data + self.pending
                self.d = zlib.decompressobj(31)
                self.fed = False
            self.buf, self.bpos = out, 0
            self.out_bytes += len(out)

    def readable(self):
        return True

    def readinto(self, b):
        self._fill()
        n = min(len(b), len(self.buf) - self.bpos)
        if n <= 0:
            return 0
        b[:n] = self.buf[self.bpos:self.bpos + n]
        self.bpos += n
        return n


def lines(stream, stats):
    """yield complete lines (bytes, without the newline); lines longer than MAXLINE are skipped and counted (A3)"""
    br = io.BufferedReader(stream, buffer_size=4 << 20)
    while True:
        ln = br.readline(MAXLINE)
        if not ln:
            return
        if not ln.endswith(b'\n') and len(ln) >= MAXLINE:
            stats['too_long'] += 1
            while True:                                         # skip the rest of the line
                more = br.readline(MAXLINE)
                if not more or more.endswith(b'\n'):
                    break
            continue
        yield ln.rstrip(b'\r\n')


# ---------------------------------------------------------------- ratings (A4, A5)
ASIN_RE = re.compile(rb'[0-9A-Z]{10}')
RATING = {b'1': 1, b'2': 2, b'3': 3, b'4': 4, b'5': 5, b'1.0': 1, b'2.0': 2, b'3.0': 3, b'4.0': 4, b'5.0': 5}
TS_RE = re.compile(rb'[0-9]{1,15}')


def do_ratings():
    out_im, out_tot = OUT / 'ratings_item_month.parquet', OUT / 'ratings_month_totals.parquet'
    js = OUT / 'ratings_summary.json'
    if out_im.exists() and out_tot.exists() and js.exists():
        log('ratings: output exists, skipped')
        return json.loads(js.read_text())
    s = GzStream('ratings')
    st = dict(lines=0, kept=0, bad_fields=0, bad_asin=0, bad_rating=0, bad_ts=0, ts_out_of_window=0, too_long=0, empty=0)
    asins, mis, rts = [], [], []           # per-chunk numpy arrays (no user ids)
    badr = {}                              # rejected rating values (first 8 characters), at most 20 kinds
    a_buf, r_buf, t_buf = [], [], []

    def flush():
        if not a_buf:
            return
        ts = np.array(t_buf, dtype=np.int64)
        ok = (ts >= TS_LO) & (ts < TS_HI)
        st['ts_out_of_window'] += int((~ok).sum())
        a = np.array(a_buf, dtype='S10')[ok]
        r = np.array(r_buf, dtype=np.int8)[ok]
        m = (ts[ok].astype('datetime64[ms]').astype('datetime64[M]').astype(np.int64) + 1970 * 12).astype(np.int32)
        asins.append(a); rts.append(r); mis.append(m)
        st['kept'] += int(ok.sum())
        a_buf.clear(); r_buf.clear(); t_buf.clear()

    it = lines(s, st)
    header = next(it)
    assert header == b'user_id,parent_asin,rating,timestamp', 'ratings header differs'
    for ln in it:
        st['lines'] += 1
        if not ln:
            st['empty'] += 1
            continue
        f = ln.split(b',')
        if len(f) != 4:
            st['bad_fields'] += 1
            continue
        # f[0] is the user id: never kept
        if not ASIN_RE.fullmatch(f[1]):
            st['bad_asin'] += 1
            continue
        rv = RATING.get(f[2])
        if rv is None:
            st['bad_rating'] += 1
            k = f[2][:8].decode('ascii', 'replace')
            if k in badr or len(badr) < 20:
                badr[k] = badr.get(k, 0) + 1
            continue
        if not TS_RE.fullmatch(f[3]):
            st['bad_ts'] += 1
            continue
        a_buf.append(f[1]); r_buf.append(rv); t_buf.append(int(f[3]))
        if len(a_buf) >= RAT_CHUNK:
            flush()
            log(f'ratings: {st["lines"]:,} lines, {s.pos / s.size:6.1%} of the file, retries {s.retries}')
    flush()
    del it
    log('ratings stream done', st, 'compressed', s.pos, 'decompressed', s.out_bytes, 'members', s.members)
    A = np.concatenate(asins); M = np.concatenate(mis); R = np.concatenate(rts)
    del asins, mis, rts
    ua, inv = np.unique(A, return_inverse=True)
    del A
    m0 = int(M.min())
    key = inv.astype(np.int64) * 4096 + (M - m0)
    del inv
    uk, kinv = np.unique(key, return_inverse=True)
    n = np.bincount(kinv).astype(np.int32)
    rs = np.bincount(kinv, weights=R.astype(np.float64)).astype(np.int64)
    del kinv, key
    assert rs.max() < 2 ** 31
    tot = pd.DataFrame({'mi': M, 'r': R.astype(np.int64)}).groupby('mi').r.agg(['size', 'sum']).reset_index()
    tot.columns = ['mi', 'n', 'rsum']
    del M, R
    im = pd.DataFrame({'parent_asin': pd.array(ua[uk // 4096].astype(str), dtype='string'), 'mi': (uk % 4096 + m0).astype(np.int32),
                       'n': n, 'rsum': rs.astype(np.int32)})
    atomic_parquet(im, out_im)
    atomic_parquet(tot.astype({'mi': np.int32, 'n': np.int64, 'rsum': np.int64}), out_tot)
    summ = dict(**st, bad_rating_values=badr, items=int(len(ua)), item_months=int(len(im)), first_mi=int(tot.mi.min()), last_mi=int(tot.mi.max()),
                compressed_bytes=s.pos, decompressed_bytes=s.out_bytes, gzip_members=s.members, retries=s.retries,
                url=s.url, etag=s.etag, finished=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    atomic_json(js, summ)
    log('ratings written', len(im), 'item-months,', len(ua), 'items')
    return summ


# ---------------------------------------------------------------- meta (A6 to A9)
CTRL = re.compile(r'[\x00-\x1f\x7f-\x9f​-‏  ﻿]')
WS = re.compile(r'\s+')
YEAR = re.compile(r'(?<!\d)(1[4-9]\d\d|20[0-2]\d)(?!\d)')
ISBN_KEY = re.compile(r'isbn[ \-]?(10|13)')
ISBN_KEEP = re.compile(r'[^0-9Xx\-]')
ASIN_S = re.compile(r'[0-9A-Z]{10}')


def clean(x, n):
    if not isinstance(x, str):
        return ''
    x = CTRL.sub(' ', x)
    x = unicodedata.normalize('NFC', x)
    return WS.sub(' ', x).strip()[:n]


def pub_date_of(det, subtitle):
    v = det.get('Publication date')
    if isinstance(v, str) and v.strip():
        return clean(v, 40)
    v = det.get('Publisher')
    if isinstance(v, str):
        m = re.findall(r'\(([^()]*)\)', v[:2000])
        if m and YEAR.search(m[-1]):
            return clean(m[-1], 40)
    if isinstance(subtitle, str):
        sub = subtitle[:2000]
        for dash in ('–', '—', ' - '):
            if dash in sub:
                t = sub.rsplit(dash, 1)[1]
                if YEAR.search(t):
                    return clean(t, 40)
                break
    return ''


def reduce_meta(ln, st):
    try:
        o = json.loads(ln)
    except (ValueError, RecursionError):
        st['bad_json'] += 1
        return None
    if not isinstance(o, dict):
        st['not_object'] += 1
        return None
    pa_ = o.get('parent_asin')
    if not isinstance(pa_, str) or not ASIN_S.fullmatch(pa_):
        st['bad_asin'] += 1
        return None
    au = o.get('author')
    name = clean(au.get('name'), 200) if isinstance(au, dict) else ''
    det = o.get('details')
    det = det if isinstance(det, dict) else {}
    i10 = i13 = ''
    for k, v in det.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        m = ISBN_KEY.fullmatch(k.strip().lower())
        if m:
            val = ISBN_KEEP.sub('', v)[:20]
            if m.group(1) == '10' and not i10:
                i10 = val
            elif m.group(1) == '13' and not i13:
                i13 = val
    pd_ = pub_date_of(det, o.get('subtitle'))
    y = YEAR.search(pd_)
    return (pa_, clean(o.get('title'), 500), name, i10, i13, pd_, int(y.group(1)) if y else -1)


META_COLS = ['parent_asin', 'title', 'author', 'isbn10', 'isbn13', 'pub_date', 'pub_year']


def do_meta():
    out = OUT / 'meta_items.parquet'
    js = OUT / 'meta_summary.json'
    if out.exists() and js.exists():
        log('meta: output exists, skipped')
        return json.loads(js.read_text())
    PARTS.mkdir(exist_ok=True)
    ck = PARTS / 'checkpoint.json'
    cp = json.loads(ck.read_text()) if ck.exists() else dict(lines_done=0, parts=0, stats={})
    st = dict(lines=0, kept=0, empty=0, bad_json=0, not_object=0, bad_asin=0, too_long=0)
    for k, v in cp['stats'].items():
        st[k] = v
    skip = cp['lines_done']
    if skip:
        log(f'meta: resuming, {skip:,} lines already reduced in {cp["parts"]} parts (streaming again from byte 0, not parsing them)')
    s = GzStream('meta')
    rows = []
    seen = 0
    part = cp['parts']
    ls = dict(too_long=0)                                       # counted over the whole stream (restarts from byte 0)

    def write_part():
        nonlocal part, rows
        df = pd.DataFrame(rows, columns=META_COLS).astype({'pub_year': np.int16})
        atomic_parquet(df, PARTS / f'part_{part:05d}.parquet')
        part += 1
        rows = []
        st['too_long'] = ls['too_long']
        atomic_json(ck, dict(lines_done=seen, parts=part, stats=st))

    for ln in lines(s, ls):
        seen += 1
        if seen <= skip:
            if seen % 1_000_000 == 0:
                log(f'meta: skipping, {seen:,} lines, {s.pos / s.size:6.1%}')
            continue
        st['lines'] += 1
        if not ln.strip():
            st['empty'] += 1
        else:
            r = reduce_meta(ln, st)
            if r is not None:
                rows.append(r)
                st['kept'] += 1
        if seen % META_PART == 0:
            write_part()
            log(f'meta: {seen:,} lines, kept {st["kept"]:,}, {s.pos / s.size:6.1%} of the file ({s.pos:,} bytes), retries {s.retries}')
    write_part()
    log('meta stream done', st, 'compressed', s.pos, 'decompressed', s.out_bytes, 'members', s.members)
    st['too_long'] = ls['too_long']
    files = sorted(PARTS.glob('part_*.parquet'))
    assert len(files) == part
    schema = pa.schema([(c, pa.string()) for c in META_COLS[:-1]] + [('pub_year', pa.int16())])
    T = pa.concat_tables([pq.read_table(f).select(META_COLS).cast(schema) for f in files])
    assert T.num_rows == st['kept'], (T.num_rows, st['kept'])
    first = ~pd.Series(T['parent_asin'].to_numpy(zero_copy_only=False)).duplicated(keep='first').to_numpy()
    dup = int((~first).sum())
    T = T.filter(pa.array(first))
    tmp = out.with_suffix('.tmp')
    pq.write_table(T, tmp)
    os.replace(tmp, out)

    def nonempty(c):
        return int(pc.sum(pc.not_equal(T[c], '')).as_py() or 0)
    summ = dict(**st, duplicate_parent_asin=dup, items=int(T.num_rows), with_isbn10=nonempty('isbn10'), with_isbn13=nonempty('isbn13'),
                with_author=nonempty('author'), with_pub_date=nonempty('pub_date'),
                compressed_bytes=s.pos, decompressed_bytes=s.out_bytes, gzip_members=s.members, retries=s.retries,
                url=s.url, etag=s.etag, finished=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    atomic_json(js, summ)
    for f in files:
        f.unlink()
    ck.unlink()
    PARTS.rmdir()
    log('meta written', T.num_rows, 'items; duplicates dropped', dup)
    return summ


if __name__ == '__main__':
    assert sys.flags.isolated, 'run with python -I'
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    res = {}
    if what in ('ratings', 'all'):
        res['ratings'] = do_ratings()
    if what in ('meta', 'all'):
        res['meta'] = do_meta()
    if what == 'all':
        atomic_json(OUT / 'download_summary.json', res)
    log('done')
