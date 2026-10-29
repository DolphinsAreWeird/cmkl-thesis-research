# l01. Addendum l (books chosen in time), step 1: match every sampled work to its English Wikipedia book article and to an author
# article.  Settings: prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json, L1_books_chosen_in_time (read-only; SHA-256 checked).
# DATA ONLY: no loan is read except the eligibility already stored in Test D's rows; no model, no outcome.
#
# Works: the work_ids of data/db/wiki_led/test_d_rows_c.parquet whose md5(str(work_id)) starts with 0, 1, 2 or 3 (Test D's 25% sample),
#   without the works of data/db/taxonomy_v3/quality/placeholder_works.csv.
# Book articles: the rules of code/study2r/02_match_books.py, copied unchanged (ISBN route, then title and author family name, the same
#   tie-breaks, the same control overrides), on the stored bulk Wikidata tables of 14 Oct 2026 (data/db/study2r/wd_*.parquet), with no
#   loan threshold.  Check: for sampled works that are Test A works, the article must equal Test A's.
# Author articles (choice logged in DEVIATIONS before any result): route A, the author article that
#   data/db/study2r/book_author_articles.parquet gives for the matched book item (Test A's route; it covers Test A's items); route B for
#   every other work, the first author parsed from the creator (parse_author of 01_population.py) and matched by Test B's rules
#   (02_author_match.py: the name, then (writer), (author), (novelist); accepted when the Wikidata item is a human), through Test B's
#   functions and HTTP cache (data/interim/wiki_led_cache/), at most 5 requests a second.
# Outputs: data/db/wiki_led/l_books_in_time/matches.parquet, match_summary.json; report data/reports/wiki_led_l_matches.md
#   Run from code/:  bash ../jobs/bg.sh wl_l01 main_study/wiki_led/l_books_in_time/l01_match.py
import sys, json, time, hashlib, pathlib, importlib
from collections import Counter
import pandas as pd, pyarrow.parquet as pq

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                       # wiki_led: _common, 01_population, 02_author_match
sys.path.insert(0, str(HERE.parents[2] / 'study2r'))        # code/study2r: common (text helpers)
import common as C2                                         # noqa: E402
from _common import log                                     # noqa: E402
POP = importlib.import_module('01_population')
AM = importlib.import_module('02_author_match')

D = C2.D
ROOT = D.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
OUT = D / 'db' / 'wiki_led' / 'l_books_in_time'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
TAXO = D / 'db' / 'taxonomy_v3'
S2 = D / 'db' / 'study2r'
T0 = time.time()

# ---------------------------------------------------------------- sampled works
wid = pq.read_table(D / 'db' / 'wiki_led' / 'test_d_rows_c.parquet', columns=['work_id']).to_pandas().work_id.unique()
samp = {int(w) for w in wid if hashlib.md5(str(w).encode()).hexdigest()[0] in '0123'}
ph = set(pd.read_csv(TAXO / 'quality' / 'placeholder_works.csv').work_id)
n_ph = len(samp & ph)
samp -= ph
W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main', 'creator_key'])
E_ = W[W.work_id.isin(samp)].copy()
log('sampled works', len(E_), '| placeholder works left out', n_ph)

# ---------------------------------------------------------------- ISBNs (as 02_match_books.py)
RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'isbn'])
R = R[R.isbn.notna() & (R.isbn.str.len() >= 10)]
R = R.merge(RW[['record_id', 'work_id']], on='record_id')
R = R[R.work_id.isin(E_.work_id)]
R['isbn13'] = R.isbn.map(C2.isbn13)
R = R[R.isbn13.notna()].drop_duplicates(['work_id', 'isbn13'])
isbns = R.groupby('work_id').isbn13.apply(list).to_dict()
log('sampled works with at least one valid ISBN:', len(isbns))
del R

# ---------------------------------------------------------------- Wikidata tables and the matching loop (copied from 02_match_books.py)
OVERRIDES = {}
if (S2 / 'control_overrides.json').exists():
    OVERRIDES = {int(k): tuple(v) for k, v in json.load(open(S2 / 'control_overrides.json')).items()}
I = pd.read_parquet(S2 / 'wd_items.parquet')
L = pd.read_parquet(S2 / 'wd_labels.parquet').set_index('item').text.to_dict()
AU = pd.read_parquet(S2 / 'wd_authors.parquet')
auth_words = {}
for r in AU.itertuples():
    if r.author_label:
        auth_words.setdefault(r.item, set()).update(C2.norm(r.author_label).split())
X = pd.read_parquet(S2 / 'wd_isbn.parquet')
isbn_items = X.groupby('isbn13').item.apply(set).to_dict()
art = dict(zip(I.item, I.article)); cls = dict(zip(I.item, I.cls))
GOOD = {'Q7725634', 'Q571', 'Q725377', 'Q2831984', 'Q20540385', 'Q1517777', 'Q12765855', 'Q193495', 'Q83790', 'Q8261'}
cls_rank = {i: (0 if set(c.split(',')) & GOOD else 1) for i, c in cls.items()}
keys_of = {i: C2.title_keys(L.get(i), art[i]) for i in art}
index = {}
for i, ks in keys_of.items():
    for k in ks:
        index.setdefault(k, []).append(i)
log('Wikidata items', len(I), '| distinct ISBNs', len(isbn_items))


def author_ok(item, fams):
    w = auth_words.get(item)
    return None if not w else any(f in w for f in fams)


rows, rej = [], 0
for n, r in enumerate(E_.itertuples()):
    fams = C2.parse_creators(r.creator)
    tk = C2.title_keys(r.title, r.title_main)
    pick = None
    hits = Counter()
    for b in isbns.get(r.work_id, []):
        for i in isbn_items.get(b, ()):
            hits[i] += 1
    if hits:
        order = sorted(hits, key=lambda i: (-hits[i], cls_rank[i], int(i[1:])))
        for i in order:
            ta = bool(keys_of[i] & tk); aa = author_ok(i, fams)
            if not ta and aa is False:
                rej += 1; continue
            pick = (i, 'isbn'); break
    if pick is None and fams:
        cand = []
        for k in tk:
            for i in index.get(k, ()):
                if i not in cand and author_ok(i, fams):
                    cand.append(i)
        if cand:
            exact = C2.norm(r.title_main or r.title)
            cand.sort(key=lambda i: (cls_rank[i], 0 if C2.norm(L.get(i, '')) in (exact, C2.strip_art(exact)) else 1, int(i[1:])))
            pick = (cand[0], 'title_author')
    if r.work_id in OVERRIDES:
        pick = (OVERRIDES[r.work_id][0], 'manual_control_fix')
    rows.append(dict(work_id=r.work_id, creator=r.creator, creator_key=r.creator_key, book_item=pick[0] if pick else None,
                     book_article=art.get(pick[0]) if pick else None, book_method=pick[1] if pick else 'none'))
    if n % 10000 == 0:
        log('  matched', n, 'of', len(E_))
M = pd.DataFrame(rows)
log('book articles:', int(M.book_article.notna().sum()), 'works,', M.book_article.nunique(), 'articles | ISBN hits rejected', rej)

# ---------------------------------------------------------------- check against Test A's matching output (requested titles; works.parquet
# holds the canonical title after redirects, which step l02 resolves the same way)
TA = pd.read_parquet(S2 / 'book_matches.parquet', columns=['work_id', 'article'])
chk = M.merge(TA, on='work_id', how='inner')
same = int((chk.book_article == chk.article).sum())
log('check: sampled Test A works', len(chk), '| same article as Test A', same)
assert same == len(chk), 'the copied matcher does not reproduce Test A'

# ---------------------------------------------------------------- author articles
BAA = pd.read_parquet(S2 / 'book_author_articles.parquet').drop_duplicates('item').set_index('item').author_article.to_dict()
M['author_article'] = M.book_item.map(BAA)
M['author_route'] = M.author_article.notna().map({True: 'A_book_item', False: None})
need = M.author_article.isna()
parsed = M.loc[need, 'creator'].map(POP.parse_author)
M.loc[need, 'display_name'] = parsed.map(lambda t: (t[0] or '').strip() or None)
names = sorted(set(M.loc[need, 'display_name'].dropna()))
log('route B: distinct first-author names to match', len(names))
state = {n: None for n in names}
pending = [n for n in names if not (AM.BAD.search(n) or len(n.encode()) > 250)]
for sname, suf in AM.SUFFIXES:
    if not pending:
        break
    titles = {n: n + suf for n in pending}
    res = AM.wp_resolve(list(titles.values()))
    AM.wd_fetch([res[t]['qid'] for t in titles.values() if res[t]['status'] == 'page'])
    nxt = []
    for n in pending:
        x = res[titles[n]]
        if x['status'] == 'page' and AM.ENT[x['qid']]['is_human']:
            state[n] = dict(title=x['title'], qid=x['qid'], method=sname)
        else:
            nxt.append(n)
    log(f'  stage {sname}: accepted {len(pending) - len(nxt)} of {len(pending)}')
    pending = nxt
acc = M.display_name.map(lambda n: state.get(n) if isinstance(n, str) else None)
M.loc[need, 'author_article'] = acc[need].map(lambda a: a['title'] if a else None)
M.loc[need & M.author_article.notna(), 'author_route'] = 'B_name'
M['author_method'] = acc.map(lambda a: a['method'] if a else None)
M.to_parquet(OUT / 'matches.parquet', index=False)

summ = dict(sampled_works=len(M), placeholder_works_left_out=n_ph, with_isbn=len(isbns),
            book_matched_works=int(M.book_article.notna().sum()), book_articles=int(M.book_article.nunique()),
            book_method=M.book_method.value_counts().to_dict(), isbn_hits_rejected=rej,
            test_a_works_in_sample=len(chk), test_a_same_article=same,
            author_matched_works=int(M.author_article.notna().sum()), author_articles=int(M.author_article.nunique()),
            author_route=M.author_route.value_counts().to_dict(), route_b_names=len(names),
            either_article_works=int((M.book_article.notna() | M.author_article.notna()).sum()),
            network_requests=AM.H.n_net, cache_hits=AM.H.n_cache, runtime_s=round(time.time() - T0))
(OUT / 'match_summary.json').write_text(json.dumps(summ, indent=1))
pc = lambda k: f'{k:,} ({100 * k / len(M):.1f}%)'
Lr = ['# Addendum l, step 1: Wikipedia articles of the sampled works', '',
      f'Made by `code/main_study/wiki_led/l_books_in_time/l01_match.py` on {time.strftime("%Y-%m-%d %H:%M")} (local time, UTC+06:30). '
      'Data only: no loan, model or outcome.', '',
      f'- Sampled works (Test D\'s 25% sample, placeholder works left out: {n_ph}): {len(M):,}',
      f'- With a book article: {pc(summ["book_matched_works"])}, {summ["book_articles"]:,} distinct articles; by method {summ["book_method"]}; '
      f'ISBN hits rejected because title and author both disagreed: {rej:,}',
      f'- Check against Test A: {same:,} of the {len(chk):,} sampled Test A works get the same article (must be all).',
      f'- With an author article: {pc(summ["author_matched_works"])}, {summ["author_articles"]:,} distinct articles; route {summ["author_route"]}',
      f'- With either: {pc(summ["either_article_works"])}',
      f'- Route B names: {len(names):,}; network requests {AM.H.n_net:,}, cache hits {AM.H.n_cache:,}; run time {summ["runtime_s"]} s.']
(REP / 'wiki_led_l_matches.md').write_text('\n'.join(Lr) + '\n')
log(json.dumps(summ))
