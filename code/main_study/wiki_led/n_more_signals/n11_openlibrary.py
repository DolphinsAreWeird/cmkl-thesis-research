#!/usr/bin/env python3
"""n11. Addendum n, part 1, signal OL (reading intent): Open Library reading-log entries of the main set's works, mapped through the
Open Library work id (P648) on each work's matched Wikidata book item, and the features OL_* (at origin t) and OLl_* (the same at
t-12) on the rows of addendum l.  DATA ONLY: no model is fitted, no loan is read or related to anything.

Record: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_1_signals_in_hand.OL_reading_intent, common.time_rule,
common.placebo_dates (read-only; SHA-256 checked below).  Parse and feature rules: addendum k's K1 (code/main_study/wiki_led/dirs/
k1_intent.py, choices K1 to K7; its strict line pattern, shelf names and feature function copied below).
Run from handoff/code (the dump is untrusted data: run with -I):
    nice -n 10 ../.venv/bin/python -I main_study/wiki_led/n_more_signals/n11_openlibrary.py --stage map|parse|features|all
Inputs (read only): data/db/wiki_led/l_books_in_time/matches.parquet and rows.parquet; Wikidata wbgetentities through the Http cache
(data/interim/wiki_led_cache/http; the requests of addendum m's m01, so they come from the cache); the dump
data/raw/openlibrary_dump/ol_dump_reading-log_2026-09-30.txt.gz; data/db/wiki_led/dirs/k1_intent/parse_info.json (its SHA-256);
data/collectors/openlibrary/mapping.parquet (only for a descriptive comparison with addendum k's mapping).
Outputs: data/db/wiki_led/n_more_signals/: feat_OL.parquet, ol_summary.json, ol_map_main.parquet, ol_entries_main.parquet,
ol_dump_month_totals.parquet, ol_parse_info.json.

CHOICES THE RECORD LEAVES OPEN (written 25 Nov 2026 16:52 +07:00, 09:52 UTC, before any step of this script ran;
also in data/db/wiki_led/n_more_signals/notes_nyt_ol.md)
  O1. Items and requests: the sorted unique book_item values of matches.parquet, wbgetentities in batches of 10 with exactly m01's
      parameters (action=wbgetentities, ids, props='claims|labels', languages='en', format='json', maxlag=5) through Http({'wd': 0.34}),
      so identical requests are read from the cache; any request not cached goes to the network at most 3 a second.
  O2. P648 statements: best rank (the preferred statements if the item has any, else the normal ones; deprecated never), with a string
      value matching ^OL[1-9][0-9]{0,9}W$ (an Open Library work).  Edition (OL...M) or author (OL...A) ids and other values are counted
      and not used (no search, as the record says).
  O3. An item with several Open Library works: the entries of all of them are summed (each dump line is filed under one work key, so
      no entry is counted twice).  Several main-set works with the same item each get the item's full counts (as K4).
  O4. Works with no book item, or whose item has no usable P648: unmapped, every OL feature missing (K4: unknown, not 0).  A mapped
      work with no entry in a month gets 0 for that month.  Dump keys are matched as they are (no redirect table; K4).
  O5. Dump (K1 to K3): k1's strict line pattern (RX) and shelf names copied unchanged; any other line is counted as malformed and
      skipped; nothing from the file is executed or used as a path; only counts are printed.  The file's SHA-256 must equal the one
      k1 recorded (data/db/wiki_led/dirs/k1_intent/parse_info.json), else the script stops.  Stopped Reading is counted and left out
      (K2).  An entry's month is the calendar month of its date (K3).
  O6. Data months 2017-01 to 2026-09 (record; K6).  The dump's first entry is in 2017-10 (k1's parse), so months 2017-01 to 2017-09
      are 0 for every mapped work, as in k1.  A feature is missing when a month it needs lies outside 2017-01 to 2026-09 (K6).
  O7. Features at origin t (K5, entries dated in month t or earlier as stated):  OL_wtr, OL_cur, OL_read = entries dated in month t on
      Want to Read, Currently Reading, Already Read;  OL_all = their sum;  OL_wtr_r = log((OL_wtr(t) + 1) / (median of OL_wtr over
      t-6 .. t-1 + 1)) (the record adds the log, which K5's ratio did not have);  OL_all3 = OL_all summed over t-2 .. t.  Raw counts
      otherwise (K5; not divided by Open Library's activity, which grew several-fold over these years).
  O8. OLl_* (common.placebo_dates): the same six values of the same work at origin t-12 (k1's function with the months moved 12
      earlier); missing where a needed month is before 2017-01 (monthly counts from origin 2018-01, OLl_all3 from 2018-03,
      OLl_wtr_r from 2018-07).
  O9. Rows: rows.parquet with mi <= 2026-07 (2026*12+6), in its order (asserted); float32; the same values for every format of a work.
  O10. Descriptive only: for main-set works that are Test A works and have both a usable P648 work and addendum k's mapping (quality
      high or medium), the share whose k mapping is among the P648 works.
"""
import sys, re, json, time, gzip, pathlib, hashlib, argparse
from collections import Counter
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                      # wiki_led: _common (Http); _common adds code/ for config
from _common import Http, maxlag_check, D as DATA_DIR    # noqa: E402

D = pathlib.Path(DATA_DIR)
ROOT = D.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
LB = D / 'db' / 'wiki_led' / 'l_books_in_time'
OUT = D / 'db' / 'wiki_led' / 'n_more_signals'
OUT.mkdir(parents=True, exist_ok=True)
DUMP = D / 'raw' / 'openlibrary_dump' / 'ol_dump_reading-log_2026-09-30.txt.gz'
K1INFO = D / 'db' / 'wiki_led' / 'dirs' / 'k1_intent' / 'parse_info.json'
KMAP = D / 'collectors' / 'openlibrary' / 'mapping.parquet'
WD_API = 'https://www.wikidata.org/w/api.php'
MI_MAX = 2026 * 12 + 6
SCORE0 = 2019 * 12
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


# k1_intent.py, copied unchanged (K1, K2, K6)
AV0, AV1 = mi_of('2017-01'), mi_of('2026-09')
SHELVES = {b'Want to Read': 'wtr', b'Currently Reading': 'cur', b'Already Read': 'read', b'Stopped Reading': 'stop'}
RX = re.compile(rb'/works/OL([1-9][0-9]{0,9})W\t(?:/books/OL[1-9][0-9]{0,9}M|\\N)\t(Want to Read|Currently Reading|Already Read|Stopped Reading)'
                rb'\t((?:19|20)[0-9]{2})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])')
OLW = re.compile(r'^OL([1-9][0-9]{0,9})W$')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ====================================================================== stage map (P648 from the cached claims)
def stage_map():
    H = Http({'wd': 0.34})
    M = pd.read_parquet(LB / 'matches.parquet', columns=['work_id', 'book_item'])
    ids = sorted(M.book_item.dropna().unique())
    ENT = {}
    for i in range(0, len(ids), 10):                           # O1: m01's requests
        batch = ids[i:i + 10]
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(batch), props='claims|labels', languages='en',
                                            format='json', maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        ents = json.loads(text).get('entities', {})
        for q in batch:
            e = ents.get(q) or {}
            ENT[q] = e if 'missing' not in e else {}
    log(f'items {len(ids):,}: network {H.n_net}, cache {H.n_cache}, back-offs {H.n_backoff}')
    cnt = Counter()
    rows = []
    for q in ids:
        ss = [s for s in (ENT.get(q) or {}).get('claims', {}).get('P648', []) if s.get('rank') != 'deprecated']
        cnt['items_with_p648_any'] += bool((ENT.get(q) or {}).get('claims', {}).get('P648'))
        pref = [s for s in ss if s.get('rank') == 'preferred']
        best = pref if pref else ss                                 # O2: best rank
        cnt['statements_not_best_rank'] += len(ss) - len(best)
        vals = []
        for s in best:
            try:
                v = s['mainsnak']['datavalue']['value']
            except (KeyError, TypeError):
                cnt['statements_without_value'] += 1
                continue
            m = OLW.fullmatch(v) if isinstance(v, str) else None
            if m is None:
                cnt['values_not_a_work_id' + ('_edition' if isinstance(v, str) and v.endswith('M') else
                                              '_author' if isinstance(v, str) and v.endswith('A') else '_other')] += 1
                continue
            vals.append(int(m.group(1)))
        vals = sorted(set(vals))
        rows.append((q, vals, len(vals)))
    I = pd.DataFrame(rows, columns=['book_item', 'ol_nums', 'n_ol'])
    I['ol_nums'] = I.ol_nums.map(lambda v: np.asarray(v, dtype=np.int64))
    I.to_parquet(OUT / 'ol_map_main.parquet', index=False)
    W = M.merge(I, on='book_item', how='left')
    W['n_ol'] = W.n_ol.fillna(0).astype(int)
    info = dict(works=len(M), works_with_item=int(M.book_item.notna().sum()), items=len(ids),
                items_with_a_p648_statement=int(cnt['items_with_p648_any']), items_mapped=int((I.n_ol > 0).sum()),
                items_with_several_ol_works=int((I.n_ol > 1).sum()), works_mapped=int((W.n_ol > 0).sum()),
                ol_works=len(set(v for vs in I.ol_nums for v in vs)), p648_counts={k: int(v) for k, v in cnt.items()},
                wikidata_requests=dict(network=H.n_net, cache=H.n_cache, backoffs=H.n_backoff))
    # O10: comparison with addendum k's mapping (descriptive)
    K = pd.read_parquet(KMAP, columns=['work_id', 'in_test_a', 'ol_work', 'quality'])
    K = K[K.in_test_a & K.quality.isin(['high', 'medium']) & K.ol_work.notna()]
    K['k_num'] = K.ol_work.str.extract(r'^OL([1-9][0-9]*)W$', expand=False).astype(float)
    C = W[W.n_ol > 0].merge(K[['work_id', 'k_num']].dropna(), on='work_id')
    info['compare_k_mapping'] = dict(works_with_both=len(C),
                                     k_work_among_p648=int(sum(int(k) in set(v) for k, v in zip(C.k_num, C.ol_nums))))
    (OUT / 'ol_map_info.json').write_text(json.dumps(info, indent=1))
    log('map', info)


def work_map():
    M = pd.read_parquet(LB / 'matches.parquet', columns=['work_id', 'book_item'])
    I = pd.read_parquet(OUT / 'ol_map_main.parquet')
    W = M.merge(I, on='book_item', how='left')
    W['ol_nums'] = W.ol_nums.map(lambda v: [int(x) for x in v] if v is not None and not (isinstance(v, float)) else [])
    return W


# ====================================================================== stage parse (untrusted dump -> counts, k1's rules)
def stage_parse():
    size = DUMP.stat().st_size
    h = sha256(DUMP)
    h_k1 = json.loads(K1INFO.read_text())['sha256']
    log('dump', size, 'bytes; SHA-256 equals k1\'s:', h == h_k1)
    assert h == h_k1, 'the dump differs from the file k1 parsed'
    W = work_map()
    want = set(v for vs in W.ol_nums for v in vs)
    tot = Counter()                                   # (mi, shelf) -> entries, whole dump
    mine = Counter()                                  # (ol_num, mi, shelf) -> entries, mapped works
    n = bad = before = after = 0
    with gzip.open(DUMP, 'rb') as fh:
        for line in fh:
            n += 1
            m = RX.fullmatch(line.rstrip(b'\n'))
            if m is None:
                bad += 1
                continue
            ol = int(m.group(1))
            sh = SHELVES[m.group(2)]
            y, mo = int(m.group(3)), int(m.group(4))
            mi = y * 12 + mo - 1
            tot[(mi, sh)] += 1
            if mi < AV0:
                before += 1
            elif mi > AV1:
                after += 1
            if ol in want:
                mine[(ol, mi, sh)] += 1
            if n % 2_000_000 == 0:
                log('lines', n)
    T = pd.DataFrame([(k[0], k[1], v) for k, v in tot.items()], columns=['mi', 'shelf', 'n']).sort_values(['mi', 'shelf'])
    T.to_parquet(OUT / 'ol_dump_month_totals.parquet', index=False)
    E = pd.DataFrame([(k[0], k[1], k[2], v) for k, v in mine.items()], columns=['ol_num', 'mi', 'shelf', 'n']).sort_values(['ol_num', 'mi', 'shelf'])
    E.to_parquet(OUT / 'ol_entries_main.parquet', index=False)
    info = dict(file=str(DUMP.relative_to(ROOT)), bytes=size, sha256=h, same_as_k1=(h == h_k1), lines=n, malformed=bad,
                entries_before_2017_01=before, entries_after_2026_09=after,
                rows_by_shelf={s: int(T[T.shelf == s].n.sum()) for s in ['wtr', 'cur', 'read', 'stop']},
                wanted_ol_works=len(want), wanted_ol_works_with_entries=int(E.ol_num.nunique()), wanted_entries=int(E.n.sum()),
                wanted_entries_stop_shelf=int(E[E.shelf == 'stop'].n.sum()),
                first_month=ym(int(T.mi.min())), last_month=ym(int(T.mi.max())), parsed=time.strftime('%Y-%m-%d %H:%M %z'))
    (OUT / 'ol_parse_info.json').write_text(json.dumps(info, indent=1))
    log('parse done', info)


# ====================================================================== stage features
def ol_features(mi, oi, CNT, shift):
    """k1's i_features() (K5 to K7), copied; data months mi + shift - k; oi = row of the work in CNT (-1 = unmapped).  Changed as the
    record says: the want-to-read ratio is logged (O7).  shift = 0 gives OL_*, shift = -12 gives OLl_* (O8)."""
    t = mi + shift

    def get(s, k):
        m = t - k
        ok = (m >= AV0) & (m <= AV1) & (oi >= 0)
        v = np.full(len(t), np.nan, np.float64)
        v[ok] = CNT[s][oi[ok], m[ok] - AV0]
        return v
    w0, c0, r0 = get('wtr', 0), get('cur', 0), get('read', 0)
    a = lambda k: get('wtr', k) + get('cur', k) + get('read', k)
    med6 = np.median(np.vstack([get('wtr', k) for k in range(1, 7)]), axis=0)          # NaN when any of the 6 months is missing
    out = {'wtr': w0, 'cur': c0, 'read': r0, 'all': w0 + c0 + r0, 'wtr_r': np.log((w0 + 1) / (med6 + 1)), 'all3': a(0) + a(1) + a(2)}
    return {k: v.astype(np.float32) for k, v in out.items()}


def stage_features():
    R = pd.read_parquet(LB / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R = R[R.mi <= MI_MAX].reset_index(drop=True)
    assert len(R) == 1773531, len(R)
    W = work_map()
    mapped = W[W.ol_nums.map(len) > 0].reset_index(drop=True)
    E = pd.read_parquet(OUT / 'ol_entries_main.parquet')
    E = E[(E.mi >= AV0) & (E.mi <= AV1) & E.shelf.isin(['wtr', 'cur', 'read'])]
    ols = np.sort(E.ol_num.unique())
    nmo = AV1 - AV0 + 1
    OLC = {}
    for s in ('wtr', 'cur', 'read'):                                   # Open Library works x months
        x = E[E.shelf == s]
        A = np.zeros((len(ols), nmo), np.float64)
        np.add.at(A, (np.searchsorted(ols, x.ol_num.to_numpy()), x.mi.to_numpy() - AV0), x.n.to_numpy())
        OLC[s] = A
    CNT = {s: np.zeros((len(mapped), nmo), np.float64) for s in OLC}  # mapped works x months, summed over the item's OL works (O3)
    for i, vs in enumerate(mapped.ol_nums):
        p = np.searchsorted(ols, vs)
        p = p[(p < len(ols)) & (ols[np.minimum(p, len(ols) - 1)] == np.asarray(vs))]
        for s in OLC:
            if len(p):
                CNT[s][i] = OLC[s][p].sum(axis=0)
    pos = pd.Series(np.arange(len(mapped)), index=mapped.work_id.to_numpy())
    oi = pos.reindex(R.work_id.to_numpy()).fillna(-1).to_numpy().astype(np.int64)
    mi = R.mi.to_numpy().astype(np.int64)
    F = R[['work_id', 'format', 'mi']].copy()
    for k, v in ol_features(mi, oi, CNT, 0).items():
        F['OL_' + k] = v
    for k, v in ol_features(mi, oi, CNT, -12).items():
        F['OLl_' + k] = v
    # checks
    R0 = pd.read_parquet(LB / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R0 = R0[R0.mi <= MI_MAX].reset_index(drop=True)
    assert (R0.work_id.to_numpy() == F.work_id.to_numpy()).all() and (R0.mi.to_numpy() == F.mi.to_numpy()).all() and \
        (R0.format.astype(str).to_numpy() == F.format.astype(str).to_numpy()).all(), 'row order differs from rows.parquet'
    cols = [c for c in F.columns if c.startswith('OL')]
    assert all(F[c].dtype == np.float32 for c in cols)
    g = F.groupby(['work_id', 'mi'])[cols]
    assert ((g.max() == g.min()) | (g.max().isna() & g.min().isna())).all().all() and (g.count().eq(g.size(), axis=0) | g.count().eq(0)).all().all(), 'formats differ'
    S = F.drop_duplicates(['work_id', 'mi']).set_index(['work_id', 'mi'])
    L = S[[c for c in cols if c.startswith('OL_')]].copy()
    L.index = pd.MultiIndex.from_arrays([L.index.get_level_values(0), L.index.get_level_values(1) + 12])
    J = S[[c for c in cols if c.startswith('OLl_')]].join(L, how='inner')
    for k in ['wtr', 'cur', 'read', 'all', 'wtr_r', 'all3']:
        a, b = J['OLl_' + k].to_numpy(), J['OL_' + k].to_numpy()
        assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)]), k
    assert F.loc[oi < 0, cols].isna().all().all(), 'unmapped works must be missing'
    F.to_parquet(OUT / 'feat_OL.parquet', index=False)
    log('feat_OL written', F.shape, 'lag check on', len(J), 'work-months')
    # summary
    mp = json.loads((OUT / 'ol_map_info.json').read_text())
    pa = json.loads((OUT / 'ol_parse_info.json').read_text())
    tot = sum(CNT[s] for s in CNT)
    sc = F[F.mi >= SCORE0]
    yrs = {}
    for y in range(2017, 2027):
        c0, c1 = mi_of(f'{y}-01') - AV0, min(mi_of(f'{y}-12'), AV1) - AV0 + 1
        e = tot[:, c0:c1].sum(1)
        yrs[y] = dict(mapped_works_with_entries=int((e > 0).sum()), entries=int(e.sum()))
    summ = dict(record=str(REC.relative_to(ROOT)), built=time.strftime('%Y-%m-%d %H:%M %z'),
                works_main_set=mp['works'], works_with_book_item=mp['works_with_item'], items=mp['items'],
                items_with_a_p648_statement=mp['items_with_a_p648_statement'], items_mapped=mp['items_mapped'],
                items_with_several_ol_works=mp['items_with_several_ol_works'], works_mapped=mp['works_mapped'],
                ol_works=mp['ol_works'], p648_counts=mp['p648_counts'], wikidata_requests=mp['wikidata_requests'],
                compare_k_mapping=mp['compare_k_mapping'],
                dump=dict(sha256_equals_k1=pa['same_as_k1'], lines=pa['lines'], malformed=pa['malformed'], first_month=pa['first_month'],
                          last_month=pa['last_month'], ol_works_with_entries=pa['wanted_ol_works_with_entries'],
                          entries_of_mapped_works_all_shelves=pa['wanted_entries'], of_them_stopped_reading=pa['wanted_entries_stop_shelf']),
                mapped_works_with_any_entry_2017_01_to_2026_09=int((tot.sum(1) > 0).sum()), by_year=yrs,
                rows=len(F), scored_rows=len(sc),
                scored_rows_with_OL_all=float(sc.OL_all.notna().mean()), scored_rows_OL_all_pos=float((sc.OL_all > 0).mean()),
                scored_rows_with_OL_wtr_r=float(sc.OL_wtr_r.notna().mean()), scored_rows_with_OLl_all=float(sc.OLl_all.notna().mean()),
                scored_rows_OLl_all_pos=float((sc.OLl_all > 0).mean()),
                missing_by_column_all_rows={c: int(F[c].isna().sum()) for c in cols})
    (OUT / 'ol_summary.json').write_text(json.dumps(summ, indent=1))
    log('summary', summ)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['map', 'parse', 'features', 'all'])
    a = ap.parse_args()
    if a.stage in ('map', 'all'):
        stage_map()
    if a.stage in ('parse', 'all'):
        stage_parse()
    if a.stage in ('features', 'all'):
        stage_features()
    log('done')
