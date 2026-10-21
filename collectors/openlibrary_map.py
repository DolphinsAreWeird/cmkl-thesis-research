"""Open Library work IDs for the study's books (one-time, cached; addendum i, D4_intent_collection).
Books: the Test A works (data/db/study2r/works.parquet, 7,747, each with a Wikidata item) and the 20,000 Test F books
(data/db/wiki_led/testF/books.parquet). Both use the Seattle library work_id of data/db/taxonomy_v3/spl_works.parquet.
Order of sources:
  1. Wikidata P648 (Open Library ID) of the book's item; if the item has none, P648 of its edition items (P747, or items
     with P629 = the book). SPARQL endpoint, 200 items a query, 2 s between queries. Edition IDs (OL...M) are turned into
     work IDs with /books/OL...M.json; every work ID is checked to be a live work (merged works followed to the target).
  2. Books still without a work: the Open Library search API (search.json), by the book's ISBNs (Seattle records, and
     Wikidata ISBNs for Test A items), 25 books a request, and by title and author (one request a book; if that finds
     nothing, one free-text query of main title and author surname). Open Library has duplicate works for many books;
     among the candidates that pass the title and author check the one with the most reading-log entries is kept.
Match quality: high / medium / low (rules in decide()); 'none' when nothing passed.
At most 1 Open Library request a second (1.05 s gap), project user agent with a contact address. Resumes from its caches.
Run once from the project (it reads data/db):  jobs/bg.sh ol_map ../collectors/openlibrary_map.py [--then-snapshot]
Output (OUT = ~/thesis-collectors/data/openlibrary, seen in the project as data/collectors/openlibrary):
  mapping.parquet and mapping.csv (one row per study book), mapping_summary.json, map_work/ (caches)."""
import sys, json, re, time, argparse, hashlib, subprocess, pathlib, datetime as dt
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import ol_common as C

ROOT = C.HERE.parent
D = ROOT / 'data'
WORK = C.OUT / 'map_work'


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def jl_load(f):
    out = []
    for x in (f.read_text().splitlines() if f.exists() else []):
        try:
            out.append(json.loads(x))
        except ValueError:                      # a line cut off when a run was stopped; that book is searched again
            pass
    return out


def jl_add(f, rec):
    with open(f, 'a') as fh:
        fh.write(json.dumps(rec) + '\n')


# ---------------------------------------------------------------- 0. input list
def build_input():
    f = WORK / 'input.parquet'
    if f.exists():
        return pd.read_parquet(f)
    A = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'item'])
    Fb = pd.read_parquet(D / 'db' / 'wiki_led' / 'testF' / 'books.parquet', columns=['id', 'work_id'])
    assert len(A) == 7747 and len(Fb) == 20000 and A.work_id.is_unique and Fb.work_id.is_unique
    ids = sorted(set(A.work_id) | set(Fb.work_id))
    W = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'spl_works.parquet', columns=['work_id', 'title', 'creator'])
    B = pd.DataFrame({'work_id': ids}).merge(W, on='work_id', how='left')
    B['in_test_a'] = B.work_id.isin(A.work_id)
    B['in_test_f'] = B.work_id.isin(Fb.work_id)
    B = B.merge(Fb.rename(columns={'id': 'testf_id'}), on='work_id', how='left').merge(
        A.rename(columns={'item': 'wikidata_item'}), on='work_id', how='left')
    # ISBNs: Seattle records of the work (ebook and audiobook records carry them), then Wikidata ISBN-13s of the item
    rw = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'spl_record_work.parquet')
    rw = rw[rw.work_id.isin(ids)]
    R = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'spl_records.parquet', columns=['record_id', 'isbn']).set_index('record_id')
    x = rw.join(R, on='record_id')
    isb = {}
    for k, s in zip(x.work_id, x.isbn.fillna('')):
        for i in re.split(r'[,; ]+', s):
            i = re.sub(r'[^0-9Xx]', '', i).upper()
            if len(i) in (10, 13):
                isb.setdefault(k, []).append(i)
    wd = pd.read_parquet(D / 'db' / 'study2r' / 'wd_isbn.parquet', columns=['item', 'isbn13']).dropna()
    wdi = wd.groupby('item').isbn13.agg(lambda s: sorted(set(s)))
    out = []
    for k, it in zip(B.work_id, B.wikidata_item):
        own = sorted(set(isb.get(k, [])))
        extra = [i for i in (wdi.get(it, []) if isinstance(it, str) else []) if i not in own]
        out.append((own + extra)[:20])
    B['isbns'] = out
    B.to_parquet(f, index=False)
    log(f'input: {len(B):,} study books ({B.in_test_a.sum():,} Test A, {B.in_test_f.sum():,} Test F, {(B.in_test_a & B.in_test_f).sum():,} in both); '
        f'{B.wikidata_item.notna().sum():,} with a Wikidata item, {(B.isbns.map(len) > 0).sum():,} with ISBNs')
    return B


# ---------------------------------------------------------------- 1. Wikidata P648
SPARQL = """SELECT ?item ?ol ?src WHERE {
  VALUES ?item { %s }
  { ?item wdt:P648 ?ol . BIND("item" AS ?src) }
  UNION { ?item wdt:P747 ?ed . ?ed wdt:P648 ?ol . BIND("edition_item" AS ?src) }
  UNION { ?ed wdt:P629 ?item . ?ed wdt:P648 ?ol . BIND("edition_item" AS ?src) }
}"""


def wikidata(items):
    f = WORK / 'wikidata_p648.jsonl'
    done = {q for r in jl_load(f) for q in r['items']}
    todo = sorted(set(items) - done)
    if todo:
        cli = C.Client(gap=2.0, log=log)
        cli.s.headers['Accept'] = 'application/sparql-results+json'
        for i in range(0, len(todo), 200):
            part = todo[i:i + 200]
            j = cli.get(C.WDQS, data={'query': SPARQL % ' '.join(f'wd:{q}' for q in part), 'format': 'json'}, timeout=120)
            if j is None:
                raise SystemExit('Wikidata query failed after retries; rerun to resume')
            rows = [dict(item=b['item']['value'].rsplit('/', 1)[-1], ol=b['ol']['value'].strip(), src=b['src']['value'])
                    for b in j['results']['bindings']]
            jl_add(f, dict(items=part, rows=rows))
            log(f'wikidata: {i + len(part):,} of {len(todo):,} items queried')
    rows = [x for r in jl_load(f) for x in r['rows']]
    return pd.DataFrame(rows, columns=['item', 'ol', 'src']).drop_duplicates()


# ---------------------------------------------------------------- 2. edition -> work, and live-work check
def resolve(P, cli):
    """Turn P648 values into live work keys. Returns {p648 value: dict(status, work, title, ...)}."""
    f = WORK / 'ol_resolve.jsonl'
    cache = {r['id']: r for r in jl_load(f)}
    # per item only the first tier that has values: work IDs on the item, edition IDs on the item (up to 5),
    # work IDs on edition items, edition IDs on edition items (up to 5)
    vals = set()
    for _, g in P.groupby('item'):
        for src, suf in (('item', 'W'), ('item', 'M'), ('edition_item', 'W'), ('edition_item', 'M')):
            v = sorted(x for x in g[g.src == src].ol if re.fullmatch(rf'OL\d+{suf}', x))
            if v:
                vals.update(v if suf == 'W' else v[:5]); break
    vals = sorted(vals)
    ed = [v for v in vals if v.endswith('M') and v not in cache]
    for n, m in enumerate(ed, 1):
        j = cli.get(f'{C.OL}/books/{m}.json')
        if j is None:
            raise SystemExit('Open Library failing; rerun to resume')
        ws = [w.get('key', '').rsplit('/', 1)[-1] for w in (j.get('works') or [])]
        rec = dict(id=m, kind='edition', work_raw=ws[0] if ws else None, error=j.get('error'))
        cache[m] = rec; jl_add(f, rec)
        if n % 200 == 0:
            log(f'editions: {n:,} of {len(ed):,} resolved')
    raw = sorted({v for v in vals if v.endswith('W')} | {cache[v]['work_raw'] for v in vals if v.endswith('M') and cache[v].get('work_raw')})
    chk_f = WORK / 'ol_check.json'
    chk = json.loads(chk_f.read_text()) if chk_f.exists() else {}
    need = [k for k in raw if k not in chk]
    if need:
        log(f'checking {len(need):,} work keys from Wikidata')
        chk.update(C.check_keys(cli, need, log=log))
        chk_f.write_text(json.dumps(chk))
    res = {}
    for v in vals:
        w = v if v.endswith('W') else cache[v].get('work_raw')
        info = chk.get(w) if w else None
        res[v] = dict(info, raw=w) if info else dict(status='gone', work=None, raw=w)
    return res


# ---------------------------------------------------------------- 3. search API
FIELDS = 'key,title,subtitle,author_name,edition_count,readinglog_count'


def slim(d, extra=()):
    r = dict(key=d['key'].rsplit('/', 1)[-1], title=d.get('title', ''), subtitle=d.get('subtitle', ''), authors=d.get('author_name', [])[:6],
             edition_count=d.get('edition_count', 0), readinglog_count=d.get('readinglog_count', 0))
    r.update({k: d[k] for k in extra if k in d})
    return r


def isbn_search(B, cli):
    f = WORK / 'isbn_search.jsonl'
    done = {w for r in jl_load(f) for w in r['work_ids']}
    todo = B[(B.isbns.map(len) > 0) & ~B.work_id.isin(done)]
    rows, batches, cur = list(zip(todo.work_id, todo.isbns)), [], []
    for w, I in rows:                                   # batches of at most 25 books and 120 ISBNs (keeps the URL short)
        if cur and (len(cur) == 25 or sum(len(x) for _, x in cur) + len(I) > 120):
            batches.append(cur); cur = []
        cur.append((w, I))
    if cur:
        batches.append(cur)
    n = 0
    for bi, part in enumerate(batches):
        n += len(part)
        q = 'isbn:(' + ' OR '.join(sorted({x for _, I in part for x in I})) + ')'
        j = cli.get(f'{C.OL}/search.json', params=dict(q=q, fields=FIELDS + ',isbn', limit=500))
        if j is None:
            raise SystemExit('Open Library failing; rerun to resume')
        hits = {}
        for d in j.get('docs', []):
            got = set(d.get('isbn', []))
            for w, I in part:
                if got & set(I):
                    hits.setdefault(str(w), []).append(slim(d))
        jl_add(f, dict(work_ids=[int(w) for w, _ in part], hits=hits, n_found=j.get('numFound')))
        if bi % 40 == 39:
            log(f'isbn search: {n:,} of {len(rows):,} books ({bi + 1} of {len(batches)} requests)')
    out = {}
    for r in jl_load(f):
        for w, h in r['hits'].items():
            out.setdefault(int(w), []).extend(h)
    return out


def ta_search(B, cli):
    f = WORK / 'ta_search.jsonl'
    cache = {r['work_id']: r for r in jl_load(f)}
    todo = B[~B.work_id.isin(cache)]
    t0 = time.time()
    for n, (w, t, c) in enumerate(zip(todo.work_id, todo.title, todo.creator), 1):
        full, last = C.author_parts(c)
        main = C.title_main(t) or str(t)
        p = dict(title=main, fields=FIELDS, limit=10)
        if full:
            p['author'] = full
        j = cli.get(f'{C.OL}/search.json', params=p)
        if j is None:
            if cli.fail_run >= 10:
                raise SystemExit('Open Library failing for 10 books in a row; rerun to resume')
            continue
        docs, how = [slim(d) for d in j.get('docs', [])], 'title_author' if full else 'title'
        if not docs:
            j = cli.get(f'{C.OL}/search.json', params=dict(q=f'{main} {last}'.strip(), fields=FIELDS, limit=10))
            docs, how = ([slim(d) for d in j.get('docs', [])] if j else []), 'free_text'
        rec = dict(work_id=int(w), how=how, docs=docs)
        cache[int(w)] = rec; jl_add(f, rec)
        if n % 500 == 0:
            el = time.time() - t0
            log(f'title/author search: {n:,} of {len(todo):,} books ({el / n:.2f} s a book, about {(len(todo) - n) * el / n / 3600:.1f} h left)')
    return cache


def alt_names(need, hits, ta, cli):
    """Open Library's alternative names of the authors (pen names, other spellings: M. C. Beaton is filed under Marion
    Chesney, Dostoevsky under Dostoyevsky) for candidates whose title agrees but whose author does not; 100 works a request."""
    f = WORK / 'alt_names.json'
    alt = json.loads(f.read_text()) if f.exists() else {}
    want = set()
    for b in need.itertuples():
        for d in hits.get(b.work_id, []) + (ta.get(b.work_id) or {}).get('docs', []):
            if d['key'] not in alt and C.author_agree(b.creator, d['authors']) is not True and C.title_sim(b.title, d['title'], d.get('subtitle', '')) >= 0.85:
                want.add(d['key'])
    want = sorted(want)
    log(f'alternative author names: {len(want):,} candidate works to look up')
    for i in range(0, len(want), 100):
        part = want[i:i + 100]
        j = cli.get(f'{C.OL}/search.json', params=dict(q='key:(' + ' OR '.join(f'/works/{k}' for k in part) + ')', fields='key,author_alternative_name', limit=200))
        if j is None:
            continue
        got = {d['key'].rsplit('/', 1)[-1]: d.get('author_alternative_name', []) for d in j.get('docs', [])}
        for k in part:
            names = list(dict.fromkeys(C.norm(x) for x in got.get(k, [])))
            alt[k] = [x for x in names if x][:300]
        f.write_text(json.dumps(alt))
    return alt


# ---------------------------------------------------------------- 4. decision
def decide(b, wd_rows, res, isb_hits, ta, alt=None):
    """One Open Library work per study book, with its source and a quality flag.
    Wikidata: P648 of the item ('item') preferred over P648 of edition items; among several live works the one with the
    most reading-log entries. high = title agrees (similarity >= 0.85) or author agrees; medium = neither (often a
    translated title; the Wikidata link is kept and flagged).
    Search candidates (ISBN and title/author routes) fall in tiers; the best tier present wins, and within it the work
    with the most reading-log entries (ties: found by both routes, then more editions):
      A  title similarity >= 0.85 and author agrees               high if found by ISBN or similarity >= 0.95, else medium
      B  found by ISBN and author agrees (title differs)          medium (alternative titles, e.g. US and UK)
      C  similarity >= 0.85 and no usable author on one side      low
      D  found by ISBN, similarity >= 0.85, author differs        low (pen names not in Open Library, or a wrong ISBN)
    Anything else is not used. Author agreement also uses Open Library's alternative author names (alt)."""
    alt = alt or {}
    base = dict(ol_work=None, source='none', source_detail='', quality='none', ol_title='', ol_authors='', title_sim=None,
                author_agree=None, n_candidates=0, note='')
    if wd_rows:
        cands = []
        for r in wd_rows:
            x = res.get(r['ol'])
            if x and x.get('work') and x['status'] in ('ok', 'redirect', 'unknown'):
                cands.append((r['src'] == 'item', x.get('readinglog_count') or 0, x.get('edition_count') or 0, r, x))
        works = {c[4]['work'] for c in cands}
        if cands:
            cands.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True)
            _, _, _, r, x = cands[0]
            ts = C.title_sim(b.title, x.get('title', ''), x.get('subtitle', ''))
            aa = C.author_agree(b.creator, x.get('authors', []), alt.get(x['work'])) if x.get('authors') else None
            note = []
            if len(works) > 1:
                note.append(f'{len(works)} works in Wikidata')
            if x['status'] == 'redirect':
                note.append(f"P648 {x.get('raw')} redirects")
            if x['status'] == 'unknown':
                note.append('work not checked (request failed)')
            if r['ol'].endswith('M'):
                note.append(f"edition {r['ol']}")
            return dict(base, ol_work=x['work'], source='wikidata_P648', source_detail=r['src'] if r['ol'].endswith('W') else r['src'] + '_edition_id',
                        quality='high' if (ts >= 0.85 or aa) else 'medium', ol_title=x.get('title', ''), ol_authors='; '.join(x.get('authors', [])),
                        title_sim=ts, author_agree=aa, n_candidates=len(works), note='; '.join(note))
    cand = {}
    for d in isb_hits:
        cand.setdefault(d['key'], dict(d, by=set()))['by'].add('isbn')
    for d in (ta or {}).get('docs', []):
        cand.setdefault(d['key'], dict(d, by=set()))['by'].add('title_author')
    ok = []
    for k, d in cand.items():
        ts = C.title_sim(b.title, d['title'], d.get('subtitle', ''))
        aa = C.author_agree(b.creator, d['authors'], alt.get(k))
        isbn = 'isbn' in d['by']
        if ts >= 0.85 and aa is True:
            tier, q = 'A', 'high' if (isbn or ts >= 0.95) else 'medium'
        elif isbn and aa is True:
            tier, q = 'B', 'medium'
        elif ts >= 0.85 and aa is None:
            tier, q = 'C', 'low'
        elif isbn and ts >= 0.85 and aa is False:
            tier, q = 'D', 'low'
        else:
            continue
        ok.append((tier, -(d.get('readinglog_count') or 0), -len(d['by']), -(d.get('edition_count') or 0), k, d, ts, aa, q))
    if not ok:
        return dict(base, n_candidates=len(cand), note=f"{len(cand)} candidates, none passed" if cand else ('no search result' if ta else 'not searched'))
    ok.sort(key=lambda c: c[:4])
    tier, _, _, _, k, d, ts, aa, q = ok[0]
    by = sorted(d['by'])
    detail = '+'.join(by) if by != ['title_author'] else (ta.get('how', 'title_author') if ta else 'title_author')
    same = sum(c[0] == tier for c in ok)
    return dict(base, ol_work=k, source='ol_search', source_detail=detail, quality=q, ol_title=d['title'], ol_authors='; '.join(d['authors']),
                title_sim=ts, author_agree=aa, n_candidates=len(ok), note=f'tier {tier}' + (f'; {same} works in this tier' if same > 1 else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='test on the first N books (writes to OL_OUT if set)')
    ap.add_argument('--then-snapshot', action='store_true', help='start the weekly snapshot job (launchd) when done')
    a = ap.parse_args()
    lock = C.take_lock()
    if lock is None:
        raise SystemExit('another Open Library job is running')
    WORK.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    log(f'output folder {C.OUT}; user agent: {C.user_agent()}')
    B = build_input()
    if a.limit:
        B = B.head(a.limit)
    P = wikidata(sorted(B.wikidata_item.dropna().unique()))
    log(f'wikidata: {P.item.nunique():,} of {B.wikidata_item.nunique():,} items have a P648 value (own or via an edition item); '
        f'{P.ol.str.fullmatch(r"OL[0-9]+W").sum():,} work and {P.ol.str.fullmatch(r"OL[0-9]+M").sum():,} edition values')
    cli = C.Client(gap=1.05, log=log)
    res = resolve(P, cli)
    by_item = {q: g.to_dict('records') for q, g in P.groupby('item')}
    first = [decide(b, by_item.get(b.wikidata_item, []), res, [], None) for b in B.itertuples()]
    need = B[[r['ol_work'] is None for r in first]]
    log(f'after Wikidata: {len(B) - len(need):,} of {len(B):,} books have a work; searching for {len(need):,}')
    hits = isbn_search(need, cli)
    log(f'isbn search: {len(hits):,} of {(need.isbns.map(len) > 0).sum():,} books with ISBNs got a result')
    ta = ta_search(need, cli)
    alt = alt_names(need, hits, ta, cli)
    rows = []
    for b, r0 in zip(B.itertuples(), first):
        r = r0 if r0['ol_work'] else decide(b, [], res, hits.get(b.work_id, []), ta.get(b.work_id), alt)
        rows.append(dict(work_id=b.work_id, testf_id=b.testf_id if isinstance(b.testf_id, str) else '', in_test_a=b.in_test_a, in_test_f=b.in_test_f,
                         wikidata_item=b.wikidata_item if isinstance(b.wikidata_item, str) else '', title=b.title, author=b.creator,
                         n_isbn=len(b.isbns), **r))
    M = pd.DataFrame(rows)
    M.to_parquet(C.OUT / 'mapping.parquet', index=False)
    M.to_csv(C.OUT / 'mapping.csv', index=False)

    def cov(s):
        return dict(books=int(len(s)), with_work=int(s.ol_work.notna().sum()), share=round(float(s.ol_work.notna().mean()), 4) if len(s) else 0,
                    by_source=s[s.ol_work.notna()].source.value_counts().to_dict(), by_quality=s.quality.value_counts().to_dict())
    unsearched = int((~need.work_id.isin(ta)).sum())
    if unsearched:
        log(f'{unsearched} books could not be searched (requests failed); rerun to finish them')
    summ = dict(made=dt.datetime.now().isoformat(timespec='seconds'), complete=not a.limit and not unsearched, limit=a.limit, unsearched=unsearched,
                test_a=cov(M[M.in_test_a]), test_f=cov(M[M.in_test_f]), all=cov(M),
                unique_works=int(M.ol_work.nunique()), source_detail=M.source_detail.value_counts().to_dict(),
                open_library_requests=cli.n, hours=round((time.time() - t0) / 3600, 2),
                sha256_mapping_csv=hashlib.sha256((C.OUT / 'mapping.csv').read_bytes()).hexdigest())
    (C.OUT / 'mapping_summary.json').write_text(json.dumps(summ, indent=1))
    log('Test A:', summ['test_a']); log('Test F:', summ['test_f']); log('unique works:', summ['unique_works'])
    lock.close()
    if a.then_snapshot and not a.limit:
        r = subprocess.run(['launchctl', 'kickstart', f'gui/{subprocess.check_output(["id", "-u"]).decode().strip()}/com.khant.thesis.openlibrary'])
        if r.returncode == 0:
            log('started the weekly snapshot job (launchd com.khant.thesis.openlibrary)')
        else:                                                       # run the deployed copy directly instead
            dst = pathlib.Path.home() / 'thesis-collectors'
            log(f'launchctl kickstart failed (code {r.returncode}); running the snapshot directly')
            with open(dst / 'logs' / 'openlibrary.log', 'a') as fh:
                subprocess.run([str(dst / '.venv' / 'bin' / 'python'), '-u', str(dst / 'openlibrary_reading_log.py')], cwd=dst, stdout=fh, stderr=fh)


if __name__ == '__main__':
    main()
