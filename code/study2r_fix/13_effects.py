"""Study 2R step 13: borrowing effects of every tested shift. Needs the controls section in the report (step 12). Sets:
  book      shifts_book.parquet (calibrated rule: floor 300, ratio 4.0), final classes, quality OK; print + ebook joint (primary)
  audio     the same shifts, audiobook model (secondary)
  book15    shifts_book_ratio1_5.parquet (record's sensitivity, addendum c)
  author    shifts_author.parquet (secondary): a work of the author, the author's article shift
Output data/db/study2r/effects_<set>.parquet. Statistics are in 14_inference.py."""
from _pipe2r import *
import argparse
ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=2); ap.add_argument('--sets', default='book,audio,book15,author'); args = ap.parse_args()
assert '<!-- begin controls -->' in (REP / 'study2r_fix_results.md').read_text(), 'run 12_controls.py first'
t0 = time.time()
W = works_table()
SB = pd.read_parquet(OUT / 'shifts_book.parquet'); SB15 = pd.read_parquet(OUT / 'shifts_book_ratio1_5.parquet'); SA = pd.read_parquet(OUT / 'shifts_author.parquet')
C = Ca = tabs = tabsa = None


def world(fm, name):
    C = load_counts(fm)
    return C, build_ztables(C, name, month_range(C), args.workers)


for st in args.sets.split(','):
    if st in ('book', 'book15', 'author'):
        if C is None:
            C, tabs = world(('print', 'ebook'), 'pe')
        CC, tt = C, tabs
    else:
        if Ca is None:
            Ca, tabsa = world(('audiobook',), 'au')
        CC, tt = Ca, tabsa
    if st in ('book', 'audio'):
        tests, X = book_tests(SB, W, CC), screens(CC, W, 'book', SB)
        kind = 'book'
    elif st == 'book15':
        tests, X = book_tests(SB15, W, CC), screens(CC, W, 'book', SB15)
        kind = 'book'
    else:
        tests, X = author_tests(SA, W, CC), screens(CC, W, 'author', SB, SA)
        kind = 'author'
    pool = pool_mask(CC, W, kind); art = art_codes(CC, W)
    log(st, 'tests', len(tests), 'works', tests.work_id.nunique(), 'pool works', int(pool.sum()))
    R = run_tests(CC, tt, tests, pool, art, X)
    R['set'] = st
    R.to_parquet(OUT / f'effects_{st}.parquet', index=False)
    ok = R[(R.skip == '')]
    log(st, 'tested', len(ok), 'skipped', R.skip.value_counts().to_dict(), 'too sparse', int(ok.too_sparse.sum()), 'mean placebos', ok.n_placebos.mean(), int(time.time() - t0), 's')
