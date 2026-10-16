"""Study 2R step 1b-3: the book set. Seattle works with >= 500 checkouts over 2016-01..2026-08 (all formats) matched to an
English Wikipedia article about the book, using the bulk Wikidata tables from 01.
  1. ISBN route: every ISBN on any record of the work (ISBN-10 converted to ISBN-13, so hyphen variants do not matter
     because both sides are reduced to 13 digits). A hit is rejected only when title AND author both disagree with the
     Wikidata item (a wrong ISBN on a Seattle record or an omnibus); the rejection count is reported.
  2. Title + author route for works without an accepted ISBN hit: the normalised Seattle title (or its main title) equals
     the item's English label or article title (parenthesis and leading article removed), and the family name of a Seattle
     creator is a word in an author label of the item (P50 label or P2093 string).
  Tie-breaks among several items: class (literary work, book ... before written work, edition), exact label match, lowest QID.
Outputs: data/db/study2r/book_matches.parquet, data/reports/study2r_match_check.csv (random 100, seed 20261014),
data/reports/study2r_book_set.md (counts, method shares, positive controls).
"""
import numpy as np, pandas as pd, pyarrow.dataset as ds, pyarrow.compute as pc
from collections import Counter
from common import *

OVERRIDES = {}   # work_id -> (wikidata item, reason): filled only for failed positive controls with an unambiguous article
if (OUT / 'control_overrides.json').exists():
    OVERRIDES = {int(k): tuple(v) for k, v in json.load(open(OUT / 'control_overrides.json')).items()}

# ---------------------------------------------------------------- eligible works
W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main', 'checkouts_total'])
tot = {}
for f in ('book', 'ebook', 'audiobook'):
    d = ds.dataset(TAXO / f'spl_rows_{f}.parquet')
    for b in d.to_batches(columns=['record_id', 'year', 'month', 'checkouts'], filter=ds.field('year') >= 2016, batch_size=2_000_000):
        x = b.to_pandas()
        x = x[(x.year * 100 + x.month) <= 202608]
        for k, v in x.groupby('record_id').checkouts.sum().items():
            tot[k] = tot.get(k, 0) + int(v)
RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
RW['n'] = RW.record_id.map(tot).fillna(0)
wt = RW.groupby('work_id').n.sum()
W['checkouts_2016_2026'] = W.work_id.map(wt).fillna(0).astype(int)
E_ = W[W.checkouts_2016_2026 >= 500].copy()
log('eligible works (>= 500 checkouts 2016-01..2026-08):', len(E_), '| with checkouts_total >= 500:', int((W.checkouts_total >= 500).sum()))

# ---------------------------------------------------------------- ISBNs of the eligible works
R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'isbn'])
R = R[R.isbn.notna() & (R.isbn.str.len() >= 10)]
R = R.merge(RW[['record_id', 'work_id']], on='record_id')
R = R[R.work_id.isin(E_.work_id)]
R['isbn13'] = R.isbn.map(isbn13)
R = R[R.isbn13.notna()].drop_duplicates(['work_id', 'isbn13'])
isbns = R.groupby('work_id').isbn13.apply(list).to_dict()
log('eligible works with at least one valid ISBN:', len(isbns), f'({100 * len(isbns) / len(E_):.0f}%)')
del R

# ---------------------------------------------------------------- Wikidata tables
I = pd.read_parquet(OUT / 'wd_items.parquet')
L = pd.read_parquet(OUT / 'wd_labels.parquet').set_index('item').text.to_dict()
Dsc = pd.read_parquet(OUT / 'wd_desc.parquet').set_index('item').text.to_dict()
AU = pd.read_parquet(OUT / 'wd_authors.parquet')
auth_words = {}
for r in AU.itertuples():
    if r.author_label:
        auth_words.setdefault(r.item, set()).update(norm(r.author_label).split())
X = pd.read_parquet(OUT / 'wd_isbn.parquet')
isbn_items = X.groupby('isbn13').item.apply(set).to_dict()
art = dict(zip(I.item, I.article)); cls = dict(zip(I.item, I.cls))
GOOD = {'Q7725634', 'Q571', 'Q725377', 'Q2831984', 'Q20540385', 'Q1517777', 'Q12765855', 'Q193495', 'Q83790', 'Q8261'}
cls_rank = {i: (0 if set(c.split(',')) & GOOD else 1) for i, c in cls.items()}
keys_of = {i: title_keys(L.get(i), art[i]) for i in art}
index = {}
for i, ks in keys_of.items():
    for k in ks:
        index.setdefault(k, []).append(i)
log('Wikidata items', len(I), 'with labels', len(L), 'with author words', len(auth_words), 'distinct ISBNs', len(isbn_items))


def author_ok(item, fams):
    w = auth_words.get(item)
    return None if not w else any(f in w for f in fams)


rows = []
rej = 0
for r in E_.itertuples():
    fams = parse_creators(r.creator)
    tk = title_keys(r.title, r.title_main)
    rec = dict(work_id=r.work_id, title=r.title, creator=r.creator, checkouts_2016_2026=r.checkouts_2016_2026, item=None,
               method='none', n_isbn=len(isbns.get(r.work_id, [])), n_candidates=0, title_agree=None, author_agree=None)
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
            pick = (i, 'isbn', ta, aa, len(order)); break
    if pick is None and fams:
        cand = []
        for k in tk:
            for i in index.get(k, ()):
                if i not in cand and author_ok(i, fams):
                    cand.append(i)
        if cand:
            exact = norm(r.title_main or r.title)
            cand.sort(key=lambda i: (cls_rank[i], 0 if norm(L.get(i, '')) in (exact, strip_art(exact)) else 1, int(i[1:])))
            pick = (cand[0], 'title_author', True, True, len(cand))
    if r.work_id in OVERRIDES:
        i, why = OVERRIDES[r.work_id]
        pick = (i, 'manual_control_fix', None, None, 1)
    if pick:
        i, m, ta, aa, n = pick
        rec.update(item=i, method=m, n_candidates=n, title_agree=ta, author_agree=aa, article=art.get(i), label=L.get(i),
                   description=Dsc.get(i, ''), cls=cls.get(i))
    rows.append(rec)
M = pd.DataFrame(rows)
M = M[M.item.notna()].reset_index(drop=True)
M.to_parquet(OUT / 'book_matches.parquet', index=False)
log('matched works', len(M), 'of', len(E_), '| distinct articles', M.article.nunique(), '| ISBN hits rejected (title and author both disagree):', rej)

# ---------------------------------------------------------------- hand-check sheet
rs = np.random.RandomState(SEED)
S = M.iloc[np.sort(rs.choice(len(M), min(100, len(M)), replace=False))]
S = pd.DataFrame(dict(work_id=S.work_id, seattle_title=S.title, seattle_creator=S.creator, matched_article=S.article,
                      wikidata_description=S.description, method=S.method, wikidata_item=S.item,
                      checkouts_2016_2026=S.checkouts_2016_2026, correct_yes_no='', note=''))
S.to_csv(REP / 'study2r_match_check.csv', index=False)

# ---------------------------------------------------------------- positive controls
CTRL = [("The Queen's Gambit", 'queens gambit', 'tevis', 'The Queen\'s Gambit (novel)'), ('The Duke and I', 'duke and i', 'quinn', 'The Duke and I'),
        ('Dune', 'dune', 'herbert', 'Dune (novel)'), ('Where the Crawdads Sing', 'where the crawdads sing', 'owens', 'Where the Crawdads Sing'),
        ('American Prometheus', 'american prometheus', 'bird', 'American Prometheus'),
        ('Killers of the Flower Moon', 'killers of the flower moon', 'grann', 'Killers of the Flower Moon: The Osage Murders and the Birth of the FBI'),
        ('Shogun', 'shogun', 'clavell', 'Shōgun (novel)')]
cl = []
EL = E_.assign(tn=E_.title_main.map(norm), tt=E_.title.map(norm), fam=E_.creator.map(parse_creators))
for name, key, fam, expect in CTRL:
    c = EL[(EL.tn.map(lambda s: s == key or s == strip_art(key)) | EL.tt.map(lambda s: s.startswith(key))) & EL.fam.map(lambda f: fam in f)]
    for r in c.itertuples():
        m = M[M.work_id == r.work_id]
        cl.append(dict(control=name, work_id=r.work_id, seattle_title=r.title, creator=r.creator, checkouts=r.checkouts_2016_2026,
                       matched=len(m) > 0, article=m.article.iloc[0] if len(m) else '', method=m.method.iloc[0] if len(m) else '', expected_article=expect))
    if len(c) == 0:
        cl.append(dict(control=name, work_id=None, seattle_title='(no eligible Seattle work found)', creator='', checkouts=0, matched=False, article='', method='', expected_article=expect))
CT = pd.DataFrame(cl)
CT.to_csv(OUT / 'positive_control_matches.csv', index=False)

# ---------------------------------------------------------------- report
ms = M.method.value_counts()
pct = lambda k: f'{k:,} ({100 * k / len(M):.1f}%)'
L_ = ['# Study 2R: book set (matching of Seattle works to English Wikipedia book articles)', '',
      f'Built {time.strftime("%Y-%m-%d %H:%M")} by code/study2r/02_match_books.py (interest and matching only; no borrowing outcome around any event).', '',
      '## Counts', '',
      f'- Seattle works with at least 500 checkouts over 2016-01 to 2026-08 (all formats): {len(E_):,}',
      f'- of these, with at least one valid ISBN on some record: {len(isbns):,} ({100 * len(isbns) / len(E_):.0f}%)',
      f'- matched to an English Wikipedia article about the book: **{len(M):,} works** ({100 * len(M) / len(E_):.1f}% of eligible), **{M.article.nunique():,} distinct articles**',
      f'- works sharing an article with another work (e.g. several Seattle editions): {int(M.duplicated("article", keep=False).sum()):,}', '',
      '## Match method', '']
for k, v in ms.items():
    L_.append(f'- {k}: {pct(int(v))}')
isb = M[M.method == 'isbn']
L_ += ['', f'- ISBN hits rejected because title and author both disagreed with the Wikidata item: {rej:,}',
       f'- among accepted ISBN matches: title agrees {100 * isb.title_agree.astype(float).mean():.0f}%, author family name agrees {100 * (isb.author_agree == True).sum() / max(len(isb), 1):.0f}% '  # noqa: E712
       f'(author unknown on the item: {100 * isb.author_agree.isna().mean():.0f}%)',
       f'- title and author matches with more than one candidate item: {int(((M.method == "title_author") & (M.n_candidates > 1)).sum()):,}', '',
       '## Wikidata classes of the matched items', '']
for k, v in M.cls.value_counts().head(8).items():
    L_.append(f'- {k}: {v:,}')
L_ += ['', '## Positive controls', '', '| Control | Seattle work | Checkouts | Matched | Article | Method |', '|---|---|---|---|---|---|']
for r in CT.itertuples():
    L_.append(f'| {r.control} | {r.seattle_title} ({r.creator}) | {r.checkouts} | {"yes" if r.matched else "NO"} | {r.article} | {r.method} |')
L_ += ['', 'Hand-check sheet for Khant: data/reports/study2r_match_check.csv (random 100, seed 20261014; fill the column correct_yes_no).']
(REP / 'study2r_book_set.md').write_text('\n'.join(L_) + '\n')
log('done in', int(time.time() - T0), 's')
