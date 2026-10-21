#!/usr/bin/env python3
"""Test F data, step 4: the 20,000 books and their text.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (books).  Data only: the checkout totals are read once to choose the
books (as the addendum says; this uses loans of the whole period, a disclosed look-ahead) and are not written to any Test F file.
Nothing is sorted and no loan series is built.
Inputs (data/db/taxonomy_v3/): spl_works.parquet, work_headings.parquet with headings.parquet, work_terms.parquet,
spl_goodreads_link.parquet with goodreads_works.parquet.
Books: the 20,000 works with the most checkouts_total; ties at the cut-off are broken by the lower work_id.
Text per book:
  title      spl_works.title
  author     spl_works.creator (as stored; empty for some works)
  headings   up to 10 librarian subject headings of the work, largest share first (ties: lower heading_id), joined by ' ; '
  tags       up to 10 digital subject tags (work_terms), largest share first (ties: alphabetical), joined by ' ; '
  description the first 300 characters of the linked Goodreads description (spl_goodreads_link, tiers A and B), after decoding HTML
             entities, removing tags and making it one line; empty without a link or a description
Every field: one line, control characters (tabs, newlines) turned into spaces, runs of spaces made one.
Ids: the 20,000 work_ids sorted ascending, put in a fixed random order with numpy default_rng(20261021).permutation, get b00001 to b20000.
Output: data/db/wiki_led/testF/books.parquet (id, work_id, title, author, headings, tags, description and counts), books_summary.json.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/04_books.py
"""
import sys, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_common as F

N_BOOKS, N_HEAD, N_TAG, DESC_CUT = 20000, 10, 10, 300
TAXO = F.D / 'db' / 'taxonomy_v3'


def main():
    t0 = time.time()
    W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'checkouts_total'])
    W = W.sort_values(['checkouts_total', 'work_id'], ascending=[False, True], kind='stable')
    top = W.head(N_BOOKS)
    cut = int(top.checkouts_total.iloc[-1])
    n_above, n_at = int((W.checkouts_total > cut).sum()), int((W.checkouts_total == cut).sum())
    F.log(f'{len(W):,} works; cut-off {cut} checkouts: {n_above:,} works above it, {n_at} at it, {N_BOOKS - n_above} of those taken (lowest work_id)')
    assert cut == 955 and top.work_id.is_unique
    B = top[['work_id', 'title', 'creator']].copy()
    del W, top
    ids = set(B.work_id)

    H = pd.read_parquet(TAXO / 'headings.parquet', columns=['heading_id', 'heading']).set_index('heading_id').heading
    wh = pd.read_parquet(TAXO / 'work_headings.parquet')
    wh = wh[wh.work_id.isin(ids)].sort_values(['work_id', 'share', 'heading_id'], ascending=[True, False, True], kind='stable')
    n_head = wh.groupby('work_id').size()
    wh = wh.groupby('work_id').head(N_HEAD)
    wh['txt'] = [F.clean(x) for x in wh.heading_id.map(H)]
    assert (wh.txt != '').all()
    heads = wh.groupby('work_id').txt.agg(' ; '.join)

    wt = pd.read_parquet(TAXO / 'work_terms.parquet')
    wt = wt[wt.work_id.isin(ids)].sort_values(['work_id', 'share', 'term'], ascending=[True, False, True], kind='stable')
    n_tag = wt.groupby('work_id').size()
    wt = wt.groupby('work_id').head(N_TAG)
    wt['txt'] = [F.clean(x) for x in wt.term]
    assert (wt.txt != '').all()
    tags = wt.groupby('work_id').txt.agg(' ; '.join)

    L = pd.read_parquet(TAXO / 'spl_goodreads_link.parquet')
    assert L.work_id.is_unique
    L = L[L.work_id.isin(ids)]
    G = pd.read_parquet(TAXO / 'goodreads_works.parquet', columns=['gr_work_id', 'description'])
    assert G.gr_work_id.is_unique
    L = L.merge(G, on='gr_work_id', how='left').set_index('work_id')

    B = B.set_index('work_id')
    B['title_out'] = [F.clean(x) for x in B.title]
    B['author'] = [F.clean(x) for x in B.creator]
    B['headings'] = heads.reindex(B.index).fillna('')
    B['tags'] = tags.reindex(B.index).fillna('')
    B['n_headings_all'] = n_head.reindex(B.index).fillna(0).astype(int)
    B['n_tags_all'] = n_tag.reindex(B.index).fillna(0).astype(int)
    B['gr_tier'] = L.tier.reindex(B.index).fillna('')
    full = L.description.reindex(B.index)
    B['description'] = [F.clean_html(x, DESC_CUT) for x in full]
    B['description_cut'] = [len(F.clean_html(x)) > DESC_CUT for x in full]
    B = B.reset_index()

    order = np.sort(B.work_id.to_numpy())
    perm = np.random.default_rng(F.SEED_ORDER).permutation(len(order))
    idmap = {int(w): 'b%05d' % (k + 1) for k, w in enumerate(order[perm])}
    B.insert(0, 'id', B.work_id.map(idmap))
    B = B.sort_values('id').reset_index(drop=True)
    B = B[['id', 'work_id', 'title_out', 'author', 'headings', 'tags', 'description', 'n_headings_all', 'n_tags_all', 'gr_tier',
           'description_cut']].rename(columns={'title_out': 'title'})
    assert B.id.is_unique and len(B) == N_BOOKS and (B.title != '').all()
    B.to_parquet(F.OUT / 'books.parquet', index=False)

    summ = dict(books=len(B), cutoff_checkouts=cut, works_above_cutoff=n_above, works_at_cutoff=n_at, taken_at_cutoff=N_BOOKS - n_above,
                with_author=int((B.author != '').sum()), with_headings=int((B.headings != '').sum()), with_tags=int((B.tags != '').sum()),
                with_goodreads_link=int((B.gr_tier != '').sum()), goodreads_tier=B.gr_tier[B.gr_tier != ''].value_counts().to_dict(),
                with_description=int((B.description != '').sum()), description_cut_at_300=int(B.description_cut.sum()),
                with_no_headings_tags_or_description=int(((B.headings == '') & (B.tags == '') & (B.description == '')).sum()),
                headings_shown_median=float(np.median([0 if h == '' else h.count(' ; ') + 1 for h in B.headings])),
                tags_shown_median=float(np.median([0 if h == '' else h.count(' ; ') + 1 for h in B.tags])),
                seconds=round(time.time() - t0, 1))
    json.dump(summ, open(F.OUT / 'books_summary.json', 'w'), indent=1)
    F.log(f'wrote books.parquet: {summ}')


if __name__ == '__main__':
    main()
