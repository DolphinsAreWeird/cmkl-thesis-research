"""Study 2R control check, mapping fix (15 Oct 2026; data and mapping only, no setting tuned).
Problem found: a book was represented by ONE Seattle work (the largest), while the same book sits in several Seattle works
(other editions, film tie-in editions, other creator spellings, part editions, other formats) and many editions fall below the 500-checkout
floor and were never matched. Fix, the same for every book: the unit is now the Wikipedia article. Its checkouts are the sum, in every
format and month, of ALL Seattle works (any size) that the record's two matching rules (ISBN; title + author family name) attach to the same
Wikidata item, plus works whose title is the book's title plus a plain edition marker (', Part One', 'with 2nd Epilogue', 'movie tie-in',
'unabridged' ...). The article list is unchanged (articles with at least one originally matched work of >= 500 checkouts).
Added works (not previously matched) must equal the book's full title (no split at a colon) once a plain edition marker is removed, and also need the given name of their creator to agree with the Wikidata author (so a prequel by Brian
Herbert is not added to a book by Frank Herbert).
Outputs in data/db/study2r_fix/: works.parquet (one row per article; work_id = the largest originally matched work), group_members.parquet,
counts_work.parquet (summed over the members), shifts_*.parquet with work_ids = the group id, and links to the unchanged inputs."""
import sys, pathlib, re, json, time, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'study2r'))
import numpy as np, pandas as pd, pyarrow.dataset as ds
from common import norm, strip_art, title_keys, parse_creators, isbn13, TAXO, D, log
OLD = D / 'db' / 'study2r'; FIX = D / 'db' / 'study2r_fix'; FIX.mkdir(exist_ok=True)

M = pd.read_parquet(OLD / 'book_matches.parquet')
A = pd.read_parquet(OLD / 'articles.parquet')
M['article_c'] = M.article.map(dict(zip(A.requested, A.canonical)))
BA = pd.read_parquet(OLD / 'book_author_articles.parquet')
item_author_art = dict(zip(BA.item, BA.author_article))
items = sorted(set(M.item))
I = pd.read_parquet(OLD / 'wd_items.parquet'); I = I[I.item.isin(items)]
art = dict(zip(I.item, I.article)); cls = dict(zip(I.item, I.cls))
L = pd.read_parquet(OLD / 'wd_labels.parquet').set_index('item').text.to_dict()
AU = pd.read_parquet(OLD / 'wd_authors.parquet'); AU = AU[AU.item.isin(items)]
auth_words = {}
for r in AU.itertuples():
    if r.author_label:
        auth_words.setdefault(r.item, set()).update(norm(r.author_label).split())
X = pd.read_parquet(OLD / 'wd_isbn.parquet'); X = X[X.item.isin(items)]
isbn_items = X.groupby('isbn13').item.apply(set).to_dict()
GOOD = {'Q7725634', 'Q571', 'Q725377', 'Q2831984', 'Q20540385', 'Q1517777', 'Q12765855', 'Q193495', 'Q83790', 'Q8261'}
cls_rank = {i: (0 if set(c.split(',')) & GOOD else 1) for i, c in cls.items()}
def strict_keys(*titles):
    """normalised full titles only (parenthesis removed, leading article optional); NO split at a colon, so a series title does not match a book with a subtitle"""
    v = set()
    for t in titles:
        if t:
            n = norm(re.sub(r'\s*\([^)]*\)\s*', ' ', t))
            if n:
                v.add(n); v.add(strip_art(n))
    return {x for x in v if x}


keys_of = {i: strict_keys(L.get(i), art[i]) for i in items}
index = {}
for i, ks in keys_of.items():
    for k in ks:
        index.setdefault(k, []).append(i)

# plain edition markers that may follow the book's title (after a comma, colon, dash or in parentheses) or end it
NUM = r'(?:one|two|three|four|five|six|seven|eight|nine|ten|i|ii|iii|iv|v|vi|\d+)'
SUF = re.compile(r'^(?P<k>.+?)(?:\s+(?:part|book|volume|vol)\s+' + NUM + r'|\s+(?:movie|film|tv|television|netflix|hbo)\s+tie\s*in(?:\s+edition)?|\s+(?:un)?abridged(?:\s+edition)?'
                 r'|\s+(?:special|anniversary|deluxe|collector s|illustrated|reissue|large print|paperback|hardcover|new|revised|expanded)\s+edition'
                 r'|\s+a\s+novel|\s+with\s+(?:a\s+|the\s+|\d+\w*\s+)?(?:new\s+|2nd\s+|second\s+|bonus\s+)?(?:epilogue|introduction|foreword|afterword|extra\s+epilogue|epilogues))+$')


def variants(title, main):
    v = set(strict_keys(title))
    for raw in (title,):
        if not raw:
            continue
        n = norm(re.sub(r'\s*\([^)]*\)\s*', ' ', raw))
        m = SUF.match(n)
        if m:
            k = m.group('k'); v.add(k); v.add(strip_art(k))
        # a series label before a colon, with the book title after it: no rule (too risky)
    return {x for x in v if x}


def fam_ok(item, fams):
    w = auth_words.get(item)
    return None if not w else any(f in w for f in fams)


def given_ok(item, creator):
    """every name token (2+ letters) of at least one creator string is a word of the Wikidata author label"""
    w = auth_words.get(item)
    if not w:
        return True
    for part in (creator or '').split(';'):
        for seg in part.split('/'):
            toks = [t for t in norm(seg).split() if len(t) >= 2 and not re.fullmatch(r'\d+', t)]
            if toks and all(t in w for t in toks):
                return True
    return False


WK = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main', 'checkouts_total'])
RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'isbn'])
R = R[R.isbn.notna() & (R.isbn.str.len() >= 10)].merge(RW, on='record_id')
R['isbn13'] = R.isbn.map(isbn13)
R = R[R.isbn13.isin(isbn_items.keys())].drop_duplicates(['work_id', 'isbn13'])
isbn_hits = {}
for r in R.itertuples():
    for i in isbn_items[r.isbn13]:
        isbn_hits.setdefault(r.work_id, {}).setdefault(i, 0); isbn_hits[r.work_id][i] += 1
log('Seattle works', len(WK), 'with an ISBN hit on a matched item', len(isbn_hits))

orig = dict(zip(M.work_id, M.item))
rows = []
for r in WK.itertuples():
    if r.work_id in orig:
        continue
    fams = parse_creators(r.creator)
    tk = variants(r.title, r.title_main)
    pick = None
    hits = isbn_hits.get(r.work_id)
    if hits:
        for i in sorted(hits, key=lambda i: (-hits[i], cls_rank[i], int(i[1:]))):
            ta = bool(keys_of[i] & tk); aa = fam_ok(i, fams)
            if (ta or aa) and given_ok(i, r.creator):
                pick = (i, 'isbn'); break
    if pick is None and fams:
        cand = []
        for k in tk:
            for i in index.get(k, ()):
                if i not in cand and fam_ok(i, fams) and given_ok(i, r.creator):
                    cand.append(i)
        if cand:
            ex = norm(r.title_main or r.title)
            cand.sort(key=lambda i: (cls_rank[i], 0 if norm(L.get(i, '')) in (ex, strip_art(ex)) else 1, int(i[1:])))
            pick = (cand[0], 'title_author_or_edition_marker')
    if pick:
        rows.append(dict(work_id=r.work_id, item=pick[0], how=pick[1]))
E = pd.DataFrame(rows)
E['article'] = E.item.map(art)
log('extra Seattle works attached to a matched item:', len(E), E.how.value_counts().to_dict())

G = pd.concat([M[['work_id', 'item']].assign(how='original', article=M.article_c),
               E.assign(how=E.how)[['work_id', 'item', 'how']].assign(article=E.item.map(lambda i: dict(zip(A.requested, A.canonical)).get(art[i], art[i])))], ignore_index=True)
G = G.merge(WK[['work_id', 'title', 'creator', 'checkouts_total']], on='work_id', how='left')
# group id = the largest originally matched work of the article
big = M.sort_values('checkouts_2016_2026', ascending=False).drop_duplicates('article_c').set_index('article_c').work_id
G['group_id'] = G.article.map(big).astype('int64')
G.to_parquet(FIX / 'group_members.parquet', index=False)
cnt = G.groupby('group_id').agg(n_works=('work_id', 'size'), n_added=('how', lambda s: int((s != 'original').sum())), total=('checkouts_total', 'sum'))
log('groups', len(cnt), 'groups with extra works', int((cnt.n_added > 0).sum()), 'groups with >1 originally matched works', int((G[G.how == 'original'].groupby('group_id').size() > 1).sum()))

W = pd.DataFrame(dict(work_id=big.values, article=big.index)).merge(M[['work_id', 'title', 'creator', 'item']], on='work_id')
W['author_article'] = W.item.map(item_author_art)
W = W.merge(cnt.reset_index().rename(columns={'group_id': 'work_id'}), on='work_id')
W[['work_id', 'title', 'creator', 'item', 'article', 'author_article', 'n_works', 'n_added']].to_parquet(FIX / 'works.parquet', index=False)

# counts: every record of every member work, summed by group
RG = RW[RW.work_id.isin(set(G.work_id))].merge(G[['work_id', 'group_id']], on='work_id')
rids = list(RG.record_id.astype('int64').unique())
parts = []
for f, fmt in (('book', 'print'), ('ebook', 'ebook'), ('audiobook', 'audiobook')):
    t = ds.dataset(TAXO / f'spl_rows_{f}.parquet').to_table(filter=ds.field('record_id').isin(rids), columns=['record_id', 'year', 'month', 'checkouts']).to_pandas()
    t['mi'] = t.year.astype(np.int64) * 12 + t.month.astype(np.int64) - 1
    t = t.merge(RG[['record_id', 'group_id']], on='record_id').groupby(['group_id', 'mi'], as_index=False).checkouts.sum()
    t['format'] = fmt; parts.append(t.rename(columns={'group_id': 'work_id', 'checkouts': 'y'}))
Y = pd.concat(parts, ignore_index=True); Y = Y[Y.y > 0]
Y['work_id'] = Y.work_id.astype(np.int64); Y['mi'] = Y.mi.astype(np.int64)
Y.to_parquet(FIX / 'counts_work.parquet', index=False)
log('counts', len(Y), 'rows; groups with rows', Y.work_id.nunique())

# shifts: one group per article
gid = dict(zip(W.article, W.work_id))
for f in ('shifts_book', 'shifts_book_ratio1_5', 'shifts_author'):
    S = pd.read_parquet(OLD / f'{f}.parquet')
    if 'work_ids' in S:
        S['work_ids'] = S.article.map(lambda a: str(gid[a]) if a in gid else '')
    S.to_parquet(FIX / f'{f}.parquet', index=False)
for f in ('kept_articles', 'weekly_author', 'weekly_book', 'articles', 'calibration', 'feasibility'):
    p = OLD / (f + ('.json' if f in ('calibration', 'feasibility') else '.parquet'))
    q = FIX / p.name
    if not q.exists():
        os.symlink(p, q)
log('done')
