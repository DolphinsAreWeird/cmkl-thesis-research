# n21. Addendum n, part 2 (AZ, Amazon reviews), step 2: match the 43,298 main-set works to Amazon items (ISBN route, else title and
# author route) and write a check file of 50 random matched works for an independent check by someone else (not judged here).
# DATA ONLY: no model, nothing related to loans.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_2_amazon_reviews.matching (read-only; SHA-256 checked).
#
# Choices the record leaves open (also in data/db/wiki_led/n_more_signals/notes_amazon.md, with the time they were decided, before
# this script was run):
#   B1 ISBN form: isbn13() of code/study2r/common.py, copied unchanged: characters other than digits and X dropped; 9 digits + digit/X
#      -> 978 + the 9 digits + recomputed check digit; 13 digits starting 978 or 979 -> check digit recomputed; anything else dropped.
#      Applied to Seattle, Wikidata and both Amazon fields (an Amazon 'ISBN 10' field holding 13 digits is used as an ISBN-13).
#   B2 Seattle ISBNs: the isbn field of every record of the work (spl_record_work, any format) split on commas, semicolons and spaces
#      (as d3_nyt.py).  Seattle ISBNs exist only on ebook and audiobook records.
#   B3 Wikidata ISBNs: every wd_isbn row of the work's book_item (routes 'edition' and 'direct').
#   B4 ISBN route: an Amazon item matches when one of its ISBNs is in the work's set; no title or author check (the record has none
#      for this route); every such item is kept.
#   B5 Title route only for works with no ISBN-route item.  One title key on both sides, from the full title (Seattle spl_works.title,
#      Amazon title): text before the first ':' or '('; norm() of common.py (accents removed, lower case, '&' -> 'and', other
#      characters that are not letters or digits -> space); strip_art() (leading the / a / an); spaces removed.  spl_works.title_main is
#      not used.  An empty key never matches.
#   B6 Family name from spl_works.creator: the text before the first comma when there is one; else, after removing parentheses and a
#      trailing jr / sr / ii / iii / iv, the last word.  Normalized with norm(); every word of it (usually one) must be a word of the
#      normalized Amazon author name.  Works without a creator or family name, and Amazon items without an author name, get no title
#      match.
#   B7 An Amazon item may match several works (counted); a work sums all its matched items (also items without ratings).
#   B8 Check file: 50 works drawn by numpy default_rng(20261125).choice from the sorted matched work_ids, without replacement; one row
#      per work, sorted by work_id; the Amazon item shown is the work's matched item with the most ratings (ties: lowest parent_asin),
#      plus the number of matched items and up to three other matched items (title / author); empty columns 'correct' and 'note'.
#
# Inputs: data/db/wiki_led/l_books_in_time/matches.parquet, data/db/taxonomy_v3/spl_records.parquet, spl_record_work.parquet,
#   spl_works.parquet, data/db/study2r/wd_isbn.parquet, data/db/wiki_led/n_more_signals/amazon/meta_items.parquet and
#   ratings_item_month.parquet (from n20).
# Outputs (data/db/wiki_led/n_more_signals/): amazon_matches.parquet (work_id, parent_asin, route), amazon_match_check_50.tsv,
#   amazon_match_summary.json.
# Run from handoff/:  nice -n 10 bash jobs/bg.sh n21_amazon -I main_study/wiki_led/n_more_signals/n21_amazon_match.py
import sys, os, re, json, time, hashlib, pathlib, resource, unicodedata
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow.compute as pc

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
DB = ROOT / 'data' / 'db'
L = DB / 'wiki_led' / 'l_books_in_time'
TAXO = DB / 'taxonomy_v3'
OUT = DB / 'wiki_led' / 'n_more_signals'
AZ = OUT / 'amazon'
SEED = 20261125
T0 = time.time()
try:
    os.nice(5)
except OSError:
    pass


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB',
          *a, flush=True)


# ---------------------------------------------------------------- helpers copied unchanged from code/study2r/common.py (B1, B5, B6)
def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('&', ' and ')
    s = re.sub(r'[\W_]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def strip_art(s):
    return re.sub(r'^(the|a|an) ', '', s)


def isbn13(s):
    """canonical ISBN-13 (digits only) from an ISBN-10 or ISBN-13 with any hyphens; None if invalid"""
    s = re.sub(r'[^0-9Xx]', '', s or '').upper()
    if len(s) == 10 and re.fullmatch(r'\d{9}[\dX]', s):
        b = '978' + s[:9]
    elif len(s) == 13 and re.fullmatch(r'97[89]\d{10}', s):
        b = s[:12]
    else:
        return None
    ck = (10 - sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(b)) % 10) % 10
    return b + str(ck)


# ---------------------------------------------------------------- this record's keys
def title_key(t):                                               # B5
    t = re.split(r'[:(]', t if isinstance(t, str) else '', maxsplit=1)[0]
    return strip_art(norm(t)).replace(' ', '')


SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv'}


def family_words(c):                                            # B6
    c = c if isinstance(c, str) else ''
    if ',' in c:
        w = norm(re.sub(r'\([^)]*\)', ' ', c.split(',', 1)[0])).split()
    else:
        w = norm(re.sub(r'\([^)]*\)', ' ', c)).split()
        while w and w[-1] in SUFFIX:
            w = w[:-1]
        w = w[-1:]
    w = [x for x in w if not x.isdigit()]
    return tuple(w)


def main():
    assert sys.flags.isolated, 'run with python -I'
    # ------------------------------------------------------------ Seattle side
    W = pd.read_parquet(L / 'matches.parquet', columns=['work_id', 'book_item'])
    assert len(W) == 43298 and W.work_id.is_unique
    works = set(W.work_id)
    SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator'])
    SW = SW[SW.work_id.isin(works)].reset_index(drop=True)
    assert len(SW) == 43298
    RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    RW = RW[RW.work_id.isin(works)]
    R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'isbn'])
    R = R.merge(RW, on='record_id')
    tok = R.assign(t=R.isbn.fillna('').map(lambda s: [x for x in re.split(r'[,; ]+', s) if x])).explode('t').dropna(subset=['t'])
    tok['i13'] = tok.t.map(isbn13)
    S_isbn = tok.dropna(subset=['i13'])[['work_id', 'i13']].drop_duplicates().assign(src='seattle')
    X = pd.read_parquet(DB / 'study2r' / 'wd_isbn.parquet', columns=['item', 'isbn13'])
    X['i13'] = X.isbn13.map(isbn13)
    X = W.dropna(subset=['book_item']).merge(X.dropna(subset=['i13']), left_on='book_item', right_on='item')
    W_isbn = X[['work_id', 'i13']].drop_duplicates().assign(src='wikidata')
    WI = pd.concat([S_isbn, W_isbn], ignore_index=True)
    log('Seattle records of main-set works', len(R), 'ISBN tokens', len(tok), 'valid', tok.i13.notna().sum(),
        '| works with Seattle ISBNs', S_isbn.work_id.nunique(), 'with Wikidata ISBNs', W_isbn.work_id.nunique(),
        'with either', WI.work_id.nunique())

    # ------------------------------------------------------------ Amazon side
    M = pq.read_table(AZ / 'meta_items.parquet', columns=['parent_asin', 'isbn10', 'isbn13']).to_pandas()
    n_amazon = len(M)
    log('Amazon items', n_amazon)
    AI = pd.concat([pd.DataFrame({'parent_asin': M.parent_asin, 'i13': M.isbn10.map(isbn13)}),
                    pd.DataFrame({'parent_asin': M.parent_asin, 'i13': M.isbn13.map(isbn13)})])
    del M
    AI = AI.dropna(subset=['i13']).drop_duplicates()
    n_items_isbn = AI.parent_asin.nunique()
    log('Amazon items with a valid ISBN', n_items_isbn, 'ISBN pairs', len(AI))

    # ------------------------------------------------------------ (a) ISBN route (B4)
    P = WI.merge(AI, on='i13')
    src = P.groupby(['work_id', 'parent_asin']).src.agg(lambda s: '+'.join(sorted(set(s)))).reset_index()
    isbn_of = P.groupby(['work_id', 'parent_asin']).i13.first().to_dict()
    A = src.assign(route='isbn')
    works_isbn = set(A.work_id)
    wsrc = P.groupby('work_id').src.agg(lambda s: '+'.join(sorted(set(s))))
    log('ISBN route: pairs', len(A), 'works', len(works_isbn), 'by source', wsrc.value_counts().to_dict())

    # ------------------------------------------------------------ (b) title and author route (B5, B6)
    SW['key'] = SW.title.map(title_key)
    SW['fam'] = SW.creator.map(family_words)
    cand_w = SW[~SW.work_id.isin(works_isbn) & (SW.key != '') & (SW.fam.map(len) > 0)]
    keys = set(cand_w.key)
    M = pq.read_table(AZ / 'meta_items.parquet', columns=['parent_asin', 'title', 'author']).to_pandas()
    M['key'] = M.title.map(title_key)
    MM = M[M.key.isin(keys) & (M.author.fillna('') != '')][['parent_asin', 'key', 'author']].copy()
    MM['aw'] = MM.author.map(lambda a: frozenset(norm(a).split()))
    C = cand_w[['work_id', 'key', 'fam']].merge(MM[['parent_asin', 'key', 'aw']], on='key')
    ok = np.array([set(f) <= aw for f, aw in zip(C.fam, C.aw)], dtype=bool)
    B = C[ok][['work_id', 'parent_asin']].assign(route='title_author')
    log('title route: works tried', len(cand_w), 'Amazon items with a matching key and an author', len(MM), 'key pairs', len(C),
        'family name agrees', len(B), 'works', B.work_id.nunique())
    n_no_creator = int((SW.fam.map(len) == 0).sum())
    n_no_key = int((SW.key == '').sum())

    # ------------------------------------------------------------ match table (B7)
    T = pd.concat([A[['work_id', 'parent_asin', 'route']], B], ignore_index=True)
    Mi = M[M.parent_asin.isin(set(T.parent_asin))].set_index('parent_asin')[['title', 'author']]
    del M, MM, C
    assert not T.duplicated(['work_id', 'parent_asin']).any()
    assert not (T[T.route == 'title_author'].work_id.isin(works_isbn)).any()
    T = T.sort_values(['work_id', 'parent_asin']).reset_index(drop=True)
    T['work_id'] = T.work_id.astype(np.int64)
    T['parent_asin'] = T.parent_asin.astype('string')
    T['route'] = T.route.astype('string')
    tmp = OUT / 'amazon_matches.tmp'
    T.to_parquet(tmp, index=False)
    os.replace(tmp, OUT / 'amazon_matches.parquet')

    # ratings per matched item (for the check file and the counts)
    RT = pq.read_table(AZ / 'ratings_item_month.parquet', columns=['parent_asin', 'n'],
                       filters=[('parent_asin', 'in', list(set(T.parent_asin)))]).to_pandas()
    nrat = RT.groupby('parent_asin').n.sum()
    T['nrat'] = T.parent_asin.map(nrat).fillna(0).astype(np.int64)
    per_item = T.groupby('parent_asin').work_id.nunique()
    wk = T.groupby('work_id').agg(route=('route', 'first'), items=('parent_asin', 'size'), nrat=('nrat', 'sum'))
    summ = dict(
        main_set_works=43298,
        works_with_seattle_isbn=int(S_isbn.work_id.nunique()), works_with_wikidata_isbn=int(W_isbn.work_id.nunique()),
        works_with_any_isbn=int(WI.work_id.nunique()),
        amazon_items=int(n_amazon), amazon_items_with_valid_isbn=int(n_items_isbn),
        works_matched=int(len(wk)), works_matched_by_route=wk.route.value_counts().to_dict(),
        works_matched_isbn_by_source=wsrc.value_counts().to_dict(),
        works_no_family_name=n_no_creator, works_empty_title_key=n_no_key,
        pairs=int(len(T)), pairs_by_route=T.route.value_counts().to_dict(), items_matched=int(T.parent_asin.nunique()),
        items_matched_to_more_than_one_work=int((per_item > 1).sum()),
        items_matched_without_ratings=int((T.drop_duplicates('parent_asin').nrat == 0).sum()),
        works_matched_without_ratings=int((wk.nrat == 0).sum()),
        items_per_matched_work_median=float(wk['items'].median()), items_per_matched_work_max=int(wk['items'].max()),
        ratings_per_matched_work_median=float(wk.nrat.median()),
        finished=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    log(summ)

    # ------------------------------------------------------------ check file (B8)
    rng = np.random.default_rng(SEED)
    ids = np.sort(wk.index.to_numpy())
    pick = np.sort(rng.choice(ids, 50, replace=False))
    SWi = SW.set_index('work_id')

    def cell(x):
        return re.sub(r'[\t\r\n]+', ' ', '' if x is None or (isinstance(x, float) and np.isnan(x)) else str(x)).strip()
    out = []
    for i, w in enumerate(pick, 1):
        g = T[T.work_id == w].sort_values(['nrat', 'parent_asin'], ascending=[False, True])
        top = g.iloc[0]
        others = [f'{cell(Mi.at[a, "title"])} / {cell(Mi.at[a, "author"])}' for a in g.parent_asin.iloc[1:4]]
        out.append(dict(n=i, work_id=int(w), route=top.route, seattle_title=cell(SWi.at[w, 'title']), seattle_creator=cell(SWi.at[w, 'creator']),
                        amazon_title=cell(Mi.at[top.parent_asin, 'title']), amazon_author=cell(Mi.at[top.parent_asin, 'author']),
                        amazon_parent_asin=top.parent_asin, matched_isbn13=isbn_of.get((w, top.parent_asin), ''),
                        n_matched_items=len(g), other_matched_items=' | '.join(others), correct='', note=''))
    CK = pd.DataFrame(out)
    CK.to_csv(OUT / 'amazon_match_check_50.tsv', sep='\t', index=False)
    summ['check_file'] = dict(path='data/db/wiki_led/n_more_signals/amazon_match_check_50.tsv', seed=SEED, n=50,
                              by_route=CK.route.value_counts().to_dict())
    (OUT / 'amazon_match_summary.json').write_text(json.dumps(summ, indent=1, default=int))
    log('done; check file by route', CK.route.value_counts().to_dict())


if __name__ == '__main__':
    main()
