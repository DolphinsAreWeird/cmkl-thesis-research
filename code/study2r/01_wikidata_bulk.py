"""Study 2R step 1a: bulk download from Wikidata (SPARQL) of every item that has an English Wikipedia article and is an
instance of a written-work class, plus the ISBNs stored on those items or on their editions (P629 edition of).
Slim queries only (item, article title, class), so each takes seconds. All answers are cached under
data/interim/study2r_cache/, so a rerun costs nothing. Output: data/db/study2r/wd_items.parquet, wd_isbn.parquet
Classes (direct instance of): literary work (covers novels), written work, book, graphic novel, comic book album,
non-fiction literary work, historical non-fiction work, philosophical work, monograph, textbook, version/edition.
Series classes (book series, novel series, manga series) and films are NOT accepted: their articles are not about one book.
"""
import pandas as pd
from common import *

CLASSES = {'Q7725634': 'literary work', 'Q47461344': 'written work', 'Q571': 'book', 'Q725377': 'graphic novel',
           'Q2831984': 'comic book album', 'Q20540385': 'non-fiction literary work', 'Q1517777': 'historical non-fiction work',
           'Q12765855': 'philosophical work', 'Q193495': 'monograph', 'Q83790': 'textbook', 'Q3331189': 'version, edition or translation',
           'Q8261': 'novel'}
EN = '<https://en.wikipedia.org/>'
rows = []
for c, lab in CLASSES.items():
    b = sparql(f'SELECT ?i ?n WHERE {{ ?i wdt:P31 wd:{c} . ?a schema:about ?i ; schema:isPartOf {EN} ; schema:name ?n }}')
    if b is None:
        raise SystemExit(f'class {c} failed; rerun (cached answers are kept)')
    log(lab, len(b))
    rows += [dict(item=qid(r['i']['value']), article=r['n']['value'], cls=c, cls_label=lab) for r in b]
I = pd.DataFrame(rows)
I = I.groupby(['item', 'article'], as_index=False).agg(cls=('cls', lambda s: ','.join(sorted(set(s)))))
I.to_parquet(OUT / 'wd_items.parquet', index=False)
log('items with an enwiki article in an accepted class:', len(I))

isb = []
for prop in ('P212', 'P957'):
    for form, q in (('edition', f'SELECT ?w ?v WHERE {{ ?e wdt:P629 ?w . ?e wdt:{prop} ?v . ?a schema:about ?w ; schema:isPartOf {EN} }}'),
                    ('direct', f'SELECT ?w ?v WHERE {{ ?w wdt:{prop} ?v . ?a schema:about ?w ; schema:isPartOf {EN} }}')):
        b = sparql(q)
        if b is None:
            raise SystemExit(f'ISBN query {prop} {form} failed; rerun')
        log('ISBN', prop, form, len(b))
        isb += [dict(item=qid(r['w']['value']), isbn_raw=r['v']['value'], route=form) for r in b]
X = pd.DataFrame(isb)
X['isbn13'] = X.isbn_raw.map(isbn13)
X = X[X.isbn13.notna()].drop_duplicates(['item', 'isbn13'])
X = X[X.item.isin(I.item)]
X.to_parquet(OUT / 'wd_isbn.parquet', index=False)
log('ISBN rows for accepted items:', len(X), 'distinct items', X.item.nunique(), 'seconds', int(time.time() - T0))

# ---- labels, descriptions and authors of the same items (bulk per class; slim queries)
lab, des, aut = [], [], []
for c in CLASSES:
    if c == 'Q8261':
        continue
    base = f'?i wdt:P31 wd:{c} . ?a schema:about ?i ; schema:isPartOf {EN} .'
    for name, q, sink in (
        ('label', f'SELECT ?i ?l WHERE {{ {base} ?i rdfs:label ?l FILTER(lang(?l)="en") }}', lab),
        ('description', f'SELECT ?i ?l WHERE {{ {base} ?i schema:description ?l FILTER(lang(?l)="en") }}', des),
        ('author item', f'SELECT ?i ?au WHERE {{ {base} ?i wdt:P50 ?au }}', aut),
        ('author string', f'SELECT ?i ?au ?l WHERE {{ {base} ?i wdt:P2093 ?l BIND("" AS ?au) }}', aut)):
        b = sparql(q)
        if b is None:
            raise SystemExit(f'{name} query for {c} failed; rerun (cached answers are kept)')
        log(c, name, len(b))
        for r in b:
            i = qid(r['i']['value'])
            if sink is aut:
                sink.append(dict(item=i, author_item=qid(r['au']['value']) if r['au']['value'] else '', author_label=r['l']['value'] if 'l' in r else ''))
            else:
                sink.append(dict(item=i, text=r['l']['value']))
pd.DataFrame(lab).drop_duplicates('item').to_parquet(OUT / 'wd_labels.parquet', index=False)
pd.DataFrame(des).drop_duplicates('item').to_parquet(OUT / 'wd_desc.parquet', index=False)
A = pd.DataFrame(aut).drop_duplicates()
# labels of the author items, in batches of 300 (VALUES)
need = sorted(set(A.author_item[A.author_item != '']))
labs = {}
for k in range(0, len(need), 300):
    vals = ' '.join('wd:' + x for x in need[k:k + 300])
    b = sparql(f'SELECT ?a ?l WHERE {{ VALUES ?a {{ {vals} }} ?a rdfs:label ?l FILTER(lang(?l) IN ("en","mul")) }}')
    if b is None:
        raise SystemExit('author label batch failed; rerun')
    for r in b:
        labs.setdefault(qid(r['a']['value']), r['l']['value'])
    if (k // 300) % 20 == 0:
        log('author labels', k, '/', len(need))
m = A.author_item != ''
A.loc[m, 'author_label'] = A.loc[m, 'author_item'].map(labs).fillna('')
A.to_parquet(OUT / 'wd_authors.parquet', index=False)
log('labels', len(lab), 'descriptions', len(des), 'author rows', len(aut), 'seconds', int(time.time() - T0))
