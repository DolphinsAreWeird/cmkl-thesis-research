# D3 of addendum i (prereg/addenda_wiki_led/2026-10-22_i_directions.json, section D3_sales_target): do the signals of Test A predict
# book SALES (New York Times best-seller lists), not only Seattle borrowing, and do Seattle borrowing and the lists lead or follow each other?
# Run from code/:  ../.venv/bin/python main_study/wiki_led/dirs/d3_nyt.py --stage prep|a|a_score|b|c|report|all
#   (stage a refits LightGBM: run it through  bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/dirs/d3_nyt.py --stage a)
# Inputs (read only): data/collectors/nyt/YYYY-MM-DD.json (Books API overview, saved by collectors/nyt_bestsellers.py; no API call here),
#   data/db/study2r/works.parquet and counts_work.parquet (Test A's 7,747 works and loans), data/db/taxonomy_v3/spl_records.parquet and
#   spl_record_work.parquet (Seattle records and their ISBNs), data/db/study2r_fix/group_members.parquet (other Seattle works of the same
#   book), data/db/study2r/wd_isbn.parquet (Wikidata edition ISBNs of the matched items), data/db/wiki_led/test_a_rows_c.parquet and
#   test_a_preds_c.parquet (Test A, corrected), data/db/study3/demand_panel.parquet (excluded months).
# Outputs: data/db/wiki_led/dirs/d3_nyt/ (entries, matches, monthly table, predictions, tables, results JSON, hand-check sheet) and
#   data/reports/dir_d3_nyt.md.
#
# SETTINGS AND CHOICES NOT FIXED BY THE RECORD (written 22 Oct 2026 03:20 to 03:31 +07, before any D3 test result was computed)
#  Data
#   1. The collector kept only each book's primary_isbn13; the other ISBNs the API lists ("isbns") were not saved, so the ISBN route
#      uses the primary ISBN-13 only (a limit of the saved data; logged in prereg/DEVIATIONS.md under addendum i).
#   2. Files from 2008 to 2011 repeat some lists: the second copy is a stale list (the same every week). Only the first copy of each
#      list name in a file is kept; the script checks that the dropped copies are identical across files.
#   3. The week's date is the list's published date; a week belongs to the calendar month of that date. Coverage: 2008-06-15 to
#      2026-10-18 (the 2008-06-08 file is empty).
#   4. "Children's & Young Adult Series" lists are left out of matching and presence: their entries are series, not single books.
#   5. List families: children and young adult (Children, Young Adult, Middle Grade, Picture), graphic (Graphic, Manga), fiction
#      (name contains Fiction but not Nonfiction, and Mass Market), nonfiction (all others: Nonfiction, Advice, Business and the
#      monthly topic lists).
#  Matching (an NYT entry to one of Test A's works)
#   6. ISBN route: the entry's ISBN-13 equals an ISBN of a Seattle record of the work or of another Seattle work grouped to the same book
#      (study2r_fix group members). Seattle ISBNs exist only on ebook and audiobook records (none on print records), so a second ISBN
#      route adds the Wikidata edition ISBNs of the work's matched item (route isbn_wikidata). An ISBN hit is kept only when the titles
#      agree (equal, one equal to the other's main title, or one contained word for word in the other, as in 'TOM CLANCY: OATH OF
#      OFFICE' and 'Oath of Office'). This is stricter than the Study 2R rule (reject only when title and author both disagree): a look
#      at the ISBN hits whose titles disagree, before any test result, showed mostly other books of the same series (box sets and
#      omnibus ISBNs, such as THE HUNGER GAMES on Catching Fire), so the author alone is not enough here.
#   7. Title route: the normalised full NYT title (or without a leading article) equals a title key of the work (Seattle title, main
#      title before a colon, Wikipedia article title without the parenthesis), or the full Seattle or article title equals a key of the
#      NYT title; and a family name of the Seattle creator (or the last word of the author's article title) is a word of the NYT
#      author. Matching is to the book (Wikipedia article): candidates are collapsed to articles, exact full-title matches are
#      preferred over main-title matches, and a tie between two articles is dropped as ambiguous. Test A has 544 works that share 224
#      articles (other editions or formats of one book, and some author pages); a matched entry counts for every Test A work of its
#      article whose title agrees with the entry (and, on the title route, whose author agrees).
#   8. Hand check: 50 matched (work, NYT book) pairs drawn at random (seed 20261022) are judged by reading both sides; the share right
#      is reported with an exact (Clopper-Pearson) interval.
#   7b. (added 03:26, after the second hand check, before any test result) The Wikipedia article title is not used as a title key
#      when it looks like a person page (equal to the author article, or containing the creator's family name while the Seattle title
#      does not): a Clive Cussler novel by Dirk Cussler had matched every Seattle work that carries the article 'Clive Cussler'. A
#      title pair is also not a match when one title carries a word for another form of the book that the other lacks (graphic,
#      young readers, young people, adapted, workbook, summary, study guide, box set, boxed set, omnibus, trilogy, coloring book):
#      Sapiens and The Lightning Thief had also been given to their graphic versions.  A third hand-check sample (seed 20261024),
#      drawn after these fixes, was judged next (see 7c); the earlier sheets are kept.
#   7c. (added 03:27, after the third hand check, before any test result) When only the part of the NYT title before a colon equals
#      the Seattle title ('SKIPPYJON JONES: SNOW WHAT' and 'Skippyjon Jones'; 'UGLIES: SHAY'S STORY' and 'Uglies'), the pair is
#      another book of the series: it is no longer a title-route match (it stays acceptable on the ISBN route, as containment).
#      Third sheet: 48 of 50 right, both errors of this kind. A fourth sample (seed 20261025), drawn after this fix, gives the
#      reported share right.
#  Monthly table
#   9. For each matched work and month: weeks on any list (distinct weeks), best rank, number of lists, and presence by family.
#      Presence in month t = at least one week on any (non-series) list.
#  (a) Prediction of a list appearance in month t+1
#  10. Rows: Test A's corrected rows (origin t, features at the end of t) of works with no NYT week in month t. Primary population:
#      the matched works, as the record says (a selection on ever being listed in 2008 to 2026, known only afterwards); check: all 7,747
#      works (unmatched works count as never listed). Target: at least one NYT week in month t+1.
#  11. Scores: Test A's stored predictions where they exist (target months 2019-02 to 2026-08): W, H and HW LightGBM of the change
#      target (Wlgbm_D, Hlgbm_D, HWlgbm_D) and of the level target (_Y), the naive history rule and the Wikipedia rule. Refit: Test A's
#      LightGBM regressor with Test A's settings and seed, unchanged (squared loss on the 0/1 target), with W, H and HW columns,
#      walk-forward by the target year as in Test A (train on rows whose outcome month is before 1 January of the test year), test
#      years 2019 to 2026; once on the matched works (primary) and once on all works. Nothing is tuned.
#  12. Reference rules added (not in the record): chance; the NYT-past rule (weeks on any list in months t-12 to t-1, ties by the
#      number of weeks on any list before t-12), to show how much of an appearance next month is a book that was listed recently.
#  13. Measures: AUC within each month (months with at least one appearance), averaged over months; the pair-weighted within-month
#      AUC (share of appearing and not-appearing pairs of the same month ordered right, ties half), also for first appearances and
#      returns separately; pooled AUC over all rows; top-20 share (the 20 highest scores of the month, ties broken by work_id; missing
#      scores last) against the month's base rate; 95% intervals by the month-block bootstrap of Test A (blocks of 3 months, 2,000
#      draws, seed 20261020; for the AUC over the months with an appearance); paired differences HW minus H on the same months. Scored
#      rows: origin months 2019-01 to 2026-07 (Test A's scored period).
#  13b. (added 03:34, after the first scoring of (a)) The pair-weighted within-month AUC is also split by the book's age in Seattle at
#      t (months since its first loan: under 12, 12 to 35, 36 or more), to see how much of the ranking is the recognition of new books.
#  13c. (added 03:35, after the first scoring of (a)) Placebo: Test A's stored placebo scores (11c_placebo_a.py: each book scored with
#      the Wikipedia pages of a donor book of similar traffic and another author; pW and pHW, change and level targets) are scored on
#      the NYT target in the same way. If W's ranking came from the book's own pages, the real scores should beat their placebo.
#  (b) Lead and lag
#  14. Matched works, months 2008-07 to 2026-08. Loan change dL_t = log(1 + loans t) - log(1 + loans t-1), all formats (as Test A),
#      missing before the first loan and when t or t-1 is an excluded month. Presence N (0/1). For k = -3..3, the within-work
#      correlation of dL_t and N_{t+k} (both demeaned within work over the rows where both exist, pooled over works); k > 0 means the
#      list k months later (borrowing changes first), k < 0 the list k months earlier (list first). Intervals: bootstrap over works
#      (2,000 draws). Added: the same with the list entry month (present in t+k, absent in t+k-1) in place of presence, and the
#      period 2016 to 2026.
#  (c) Loans around the first NYT week (event study as D2)
#  15. Event: the month of a matched work's first NYT week in the data; first weeks before 2009-01 are left out (the lists before June
#      2008 were not collected, so the first week seen may not be the first). Established books: first Seattle loan at least 6 months
#      before the event month; M6 = median loans of months e-6 to e-1 (excluded months skipped). New books (first loan later) are
#      described separately (month of first loan and of peak loans relative to the event).
#  16. Controls: works of the 7,747 with no NYT week in months e-12 to e+12, first loan at least 6 months before e, in the same decile
#      of log(1 + M6) at origin e-1 (deciles over all such works that month). For months k = -3..12: D_k = log(1 + loans e+k) -
#      log(1 + M6); rose = D_k >= ln 1.5; surged = D_k >= ln 2 and loans - M6 >= 5 (Test A's rules). Excess = event value minus the
#      mean of its controls; averaged over events; 95% intervals by bootstrap over events (2,000 draws). By list family of the first
#      week as well.
#  17. (added 03:33, after the first results of (b) and (c) had been seen) For comparison with D2, the event study is also run with D2's
#      baseline (header C2 and C3 of d2_events.py: M6 over months e-9 to e-4, at least 3 available months, a loan in the 12 months to
#      e-4, controls without an NYT week from e-9 to e+12), so that months -3 to -1 lie outside the baseline. Both versions also get a
#      placebo with every event moved 24 months earlier (D2's C6; the fake window ends 12 months before the real first week).
#      Version 'own' (choices 15 and 16) stays the one fixed here; the D2 version is the cleaner check of the months before the event.
import sys, os, json, time, pathlib, hashlib, re, argparse, math
import numpy as np, pandas as pd

CODE = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(CODE)); sys.path.insert(0, str(CODE / 'study2r'))
from config import D  # noqa: E402
from common import norm, strip_art, title_keys, parse_creators, isbn13  # noqa: E402

D = pathlib.Path(D)
ROOT = D.parent
ADD_I = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_i_directions.json'
assert hashlib.sha256(ADD_I.read_bytes()).hexdigest() == '5659fbc6e63f5c477603564971dd9e4cb82bfcda57d1e9f1ae03915460ddb58e', 'addendum i changed'
NYT = D / 'collectors' / 'nyt'
OUT = D / 'db' / 'wiki_led' / 'dirs' / 'd3_nyt'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
SEED_A = 20261020          # Test A's seed (LightGBM, month-block bootstrap)
SEED = 20261022            # this direction's seed (hand-check sample, other bootstraps)
NB = 2000
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def family(name):
    n = name.replace('’', "'")
    if any(w in n for w in ("Children", 'Young Adult', 'Middle Grade', 'Picture')):
        return 'children_ya'
    if 'Graphic' in n or 'Manga' in n:
        return 'graphic'
    if ('Fiction' in n and 'Nonfiction' not in n) or n == 'Mass Market':
        return 'fiction'
    return 'nonfiction'


def is_series(name):
    return 'Series' in name


# ============================================================================================ stage prep
def stage_prep():
    # ---------------------------------------------------------------- 1. NYT entries
    rows, dropped, n_dup_lists = [], 0, 0
    files = sorted(NYT.glob('2*.json'))
    docs = [(f, json.loads(f.read_text())) for f in files]
    sig_files = {}                                             # content signature of a list copy -> files it appears in
    for f, d in docs:
        for l in d['lists']:
            sig_files.setdefault((l['list'], json.dumps(l['books'], sort_keys=True)), set()).add(f.name)
    for f, d in docs:
        pub = d.get('published') or d.get('requested')
        names = [l['list'] for l in d['lists']]
        keep = []
        for name in dict.fromkeys(names):
            copies = [l for l in d['lists'] if l['list'] == name]
            if len(copies) > 1:                                # choice 2: a stale copy repeats unchanged in other files
                n_dup_lists += 1
                fresh = [l for l in copies if len(sig_files[(name, json.dumps(l['books'], sort_keys=True))]) == 1]
                chosen = fresh[0] if fresh else copies[0]
                dropped += len(copies) - 1
                copies = [chosen]
            keep.append(copies[0])
        for l in keep:
            name = l['list']
            for b in l['books']:
                rows.append((pub, name, b.get('rank'), b.get('weeks_on_list'), b.get('isbn13'), b.get('title') or '',
                             b.get('author') or '', b.get('publisher') or '', b.get('description') or ''))
    E = pd.DataFrame(rows, columns=['week', 'list', 'rank', 'weeks_on_list', 'isbn13', 'title', 'author', 'publisher', 'description'])
    E['week'] = pd.to_datetime(E.week)
    E['mi'] = E.week.dt.year * 12 + E.week.dt.month - 1
    E['family'] = E.list.map(family)
    E['series'] = E.list.map(is_series)
    E['isbn13'] = E.isbn13.map(lambda s: isbn13(s) if isinstance(s, str) and s else None)
    info = dict(files=len(files), files_with_lists=int(E.week.nunique()), first_week=str(E.week.min().date()),
                last_week=str(E.week.max().date()), entries=len(E), dropped_stale_list_copies=dropped, lists_with_two_copies=n_dup_lists, series_entries=int(E.series.sum()),
                entries_with_isbn13=float(E.isbn13.notna().mean()),
                distinct_books_title_author=int(E[~E.series].assign(k=E.title.map(norm) + '|' + E.author.map(norm)).k.nunique()))
    log('NYT entries', info)
    E.to_parquet(OUT / 'nyt_entries.parquet', index=False)

    # ---------------------------------------------------------------- 2. Seattle side: works, ISBNs, title keys, family names
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
    TAXO = D / 'db' / 'taxonomy_v3'
    SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title_main', 'pub_year_min', 'first_ym'])
    G = pd.read_parquet(D / 'db' / 'study2r_fix' / 'group_members.parquet', columns=['work_id', 'group_id'])
    # a Seattle work's records count for itself (if it is a Test A work) and for the Test A work of its study2r_fix group
    MAP = pd.concat([pd.DataFrame({'src': W.work_id, 'group': W.work_id}),
                     G[G.group_id.isin(W.work_id)].rename(columns={'work_id': 'src', 'group_id': 'group'})]).drop_duplicates()
    RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    RW = RW[RW.work_id.isin(MAP.src)]
    R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'format', 'isbn', 'subjects'])
    R = R.merge(RW, on='record_id').merge(MAP, left_on='work_id', right_on='src')
    tok = R.assign(t=R.isbn.fillna('').map(lambda s: [x for x in re.split(r'[,; ]+', s) if x])).explode('t').dropna(subset=['t'])
    tok['i13'] = tok.t.map(isbn13)
    tok = tok[tok.i13.notna()]
    seattle_isbn = tok.groupby('i13').group.apply(set).to_dict()
    log('Seattle ISBNs', len(seattle_isbn), 'works with one', tok.group.nunique(), 'by format', tok.groupby('format').group.nunique().to_dict())
    # Wikidata edition ISBNs of the matched item
    X = pd.read_parquet(D / 'db' / 'study2r' / 'wd_isbn.parquet', columns=['item', 'isbn13'])
    X = X.merge(W[['work_id', 'item']], on='item')
    wd_isbn = X.groupby('isbn13').work_id.apply(set).to_dict()
    log('Wikidata ISBNs', len(wd_isbn), 'works with one', X.work_id.nunique())
    # fiction / juvenile from the Seattle subjects of the digital records (for describing which books match)
    sub = R[R.format.isin(['EBOOK', 'AUDIOBOOK']) & R.subjects.notna()].groupby('group').subjects.apply(lambda s: ' , '.join(s))
    W = W.merge(SW, on='work_id', how='left')
    W['fiction'] = W.work_id.map(lambda w: (lambda s: (', fiction' in (', ' + s.lower()) or s.lower().startswith('fiction')) and 'nonfiction' not in s.lower())(sub.get(w, ''))
                                 if w in sub.index else None)
    W['juvenile'] = W.work_id.map(lambda w: ('juvenile' in sub.get(w, '').lower() or 'young adult' in sub.get(w, '').lower()) if w in sub.index else None)
    W['first_loan_year'] = W.first_ym.astype(str).str[:4].astype(float) if W.first_ym.notna().any() else np.nan

    def art_clean(a):
        return re.sub(r'\s*\([^)]*\)\s*$', '', a or '')
    MARKERS = ('graphic', 'young readers', 'young people', 'adapted', 'workbook', 'summary', 'study guide', 'box set', 'boxed set',
               'omnibus', 'trilogy', 'coloring book', 'colouring book')

    def markers(t):
        n = f' {norm(t)} '
        return frozenset(m for m in MARKERS if f' {m} ' in n)
    full_keys, all_keys, fams, mark, n_author_like = {}, {}, {}, {}, 0
    for r in W.itertuples():
        fm = set(parse_creators(r.creator))
        if isinstance(r.author_article, str) and r.author_article:
            aa = norm(art_clean(r.author_article)).split()
            if aa:
                fm.add(aa[-1])
        fams[r.work_id] = {f for f in fm if f}
        a_n, t_n = norm(art_clean(r.article)), norm(r.title)
        author_like = (a_n == norm(art_clean(r.author_article if isinstance(r.author_article, str) else ''))) or \
            (bool(fams[r.work_id] & set(a_n.split())) and a_n not in t_n and strip_art(a_n) not in t_n)
        n_author_like += author_like
        arts = () if author_like else (art_clean(r.article),)
        fk = set()
        for t in (r.title,) + arts:
            n = norm(re.sub(r'\s*\([^)]*\)\s*', ' ', t or ''))
            if n:
                fk |= {n, strip_art(n)}
        full_keys[r.work_id] = fk
        all_keys[r.work_id] = title_keys(r.title, r.title_main, *arts) | fk
        mark[r.work_id] = markers(r.title)
    log('works whose article looks like a person page (article not used as a title key):', n_author_like)
    idx_all = {}
    for w, ks in all_keys.items():
        for k in ks:
            idx_all.setdefault(k, set()).add(w)

    # ---------------------------------------------------------------- 3. match each distinct NYT book key (title, author, isbn)
    # Matching is at the level of the book (the Wikipedia article): Test A has 544 works that share 224 articles (other editions or
    # formats of the same book), and an entry matched to a book is given to every Test A work of that book.
    art_of = dict(zip(W.work_id, W.article))
    works_of = W.groupby('article').work_id.apply(lambda s: sorted(s)).to_dict()

    def contains(a, b):                                         # whole-word containment of normalised strings
        return bool(a) and bool(b) and f' {a} ' in f' {b} '
    B = E[~E.series][['isbn13', 'title', 'author']].drop_duplicates().reset_index(drop=True)
    out = []
    n_rej = 0
    for r in B.itertuples():
        nt = norm(r.title)
        n_full = {nt, strip_art(nt)} - {''}
        n_keys = title_keys(r.title) | n_full
        nt_np = norm(re.sub(r'\s*\([^)]*\)\s*', ' ', r.title))           # NYT title without a parenthesis, not split at a colon
        n_keys_safe = n_full | ({nt_np, strip_art(nt_np)} - {''})
        awords = set(norm(r.author).split())
        pick, route, tier, ncand, wlist = None, 'none', None, 0, []

        n_mark = markers(r.title)

        def t_agree(w):   # 1 exact full title, 2 full title equals a main title, 3 one title contains the other (ISBN route only), 0 none
            if mark[w] != n_mark:                            # choice 7b: another form of the book (graphic, young readers ...)
                return 0
            if n_full & full_keys[w]:
                return 1
            if (n_full & all_keys[w]) or (full_keys[w] & n_keys_safe):
                return 2
            if full_keys[w] & n_keys:                        # choice 7c: only the part of the NYT title before a colon agrees
                return 3
            if any(contains(k, nt) for k in all_keys[w] if len(k) >= 4) or any(contains(nt, k) for k in full_keys[w]):
                return 3
            return 0

        def a_agree(w):
            return bool(fams[w] & awords)

        def resolve(ws):  # candidate works -> one book (article), best title tier first
            tiers = {}
            for w in ws:
                t = t_agree(w)
                a_ = art_of[w]
                tiers[a_] = min(tiers.get(a_, 9), t)
            best = min(tiers.values())
            top = [a_ for a_, t in tiers.items() if t == best]
            return (top[0], best, len(tiers)) if len(top) == 1 else (None, best, len(tiers))
        for rname, table in (('isbn_seattle', seattle_isbn), ('isbn_wikidata', wd_isbn)):
            if pick is not None or route.startswith('ambiguous') or not isinstance(r.isbn13, str):
                continue
            hits = sorted(table.get(r.isbn13, ()))
            hits_ok = [w for w in hits if t_agree(w) > 0]        # choice 6 (tightened, see header): title must agree
            n_rej += len(hits) - len(hits_ok)
            if hits_ok:
                art, tier, ncand = resolve(hits_ok)
                if art is not None:                          # the works of that book whose title agrees (not only the ISBN hits)
                    pick, route = art, rname
                    wlist = [w for w in works_of[art] if t_agree(w) > 0]
                else:
                    route = 'ambiguous_isbn'
        if pick is None and not route.startswith('ambiguous') and awords:
            cand = set()
            for k in n_keys:
                cand |= idx_all.get(k, set())
            cand = [w for w in cand if a_agree(w) and t_agree(w) in (1, 2)]
            if cand:
                art, tier, ncand = resolve(cand)
                if art is not None:
                    pick, route = art, 'title_author'
                    wlist = sorted(w for w in cand if art_of[w] == art)
                else:
                    route = 'ambiguous_title'
        out.append((r.isbn13, r.title, r.author, pick, route, tier if pick is not None else None, ncand, wlist))
    M = pd.DataFrame(out, columns=['isbn13', 'title', 'author', 'article', 'route', 'title_tier', 'n_candidates', 'works'])
    log('NYT book keys', len(M), 'routes', M.route.value_counts().to_dict(), 'ISBN hits rejected (title disagrees)', n_rej)
    M.to_parquet(OUT / 'nyt_key_matches.parquet', index=False)
    M = M.explode('works').rename(columns={'works': 'work_id'})

    EM = E[~E.series].merge(M[['isbn13', 'title', 'author', 'work_id', 'route', 'title_tier']], on=['isbn13', 'title', 'author'], how='left')
    EM = EM[EM.work_id.notna()].copy()
    EM['work_id'] = EM.work_id.astype(int)
    EM.to_parquet(OUT / 'nyt_entries_matched.parquet', index=False)

    # ---------------------------------------------------------------- 4. monthly table
    g = EM.groupby(['work_id', 'mi'])
    T = pd.DataFrame({'weeks': g.week.nunique(), 'best_rank': g['rank'].min(), 'n_lists': g.list.nunique(),
                      'n_entries': g.size()}).reset_index()
    for fam in ('fiction', 'nonfiction', 'children_ya', 'graphic'):
        T['on_' + fam] = T.set_index(['work_id', 'mi']).index.isin(EM[EM.family == fam].set_index(['work_id', 'mi']).index).astype('int8')
    T['on_audio'] = T.set_index(['work_id', 'mi']).index.isin(EM[EM.list.str.startswith('Audio')].set_index(['work_id', 'mi']).index).astype('int8')
    T.to_parquet(OUT / 'nyt_monthly.parquet', index=False)
    log('monthly table', T.shape, 'works', T.work_id.nunique())

    # ---------------------------------------------------------------- 5. match description
    matched = set(T.work_id)
    W['matched'] = W.work_id.isin(matched)
    firstw = EM.groupby('work_id').week.min()
    W['first_nyt_year'] = W.work_id.map(firstw).dt.year
    route_w = EM.sort_values('week').groupby('work_id').route.agg(lambda s: s.value_counts().index[0])
    fam_w = EM.groupby('work_id').family.agg(lambda s: s.value_counts().index[0])
    W['main_route'] = W.work_id.map(route_w)
    W['main_family'] = W.work_id.map(fam_w)
    W.drop(columns=['title_main']).to_parquet(OUT / 'works_match_info.parquet', index=False)
    # NYT side: share of distinct NYT books (title + author, non-series) that reach a Test A work
    NB_ = E[~E.series].assign(k=E.title.map(norm) + '|' + E.author.map(norm))
    NB_ = NB_.merge(M[['isbn13', 'title', 'author', 'work_id']], on=['isbn13', 'title', 'author'], how='left')
    nb = NB_.groupby('k').agg(first=('week', 'min'), fam=('family', lambda s: s.value_counts().index[0]),
                              matched=('work_id', lambda s: s.notna().any()), weeks=('week', 'nunique'))
    nb['year'] = nb['first'].dt.year
    nb.reset_index().to_parquet(OUT / 'nyt_books_side.parquet', index=False)
    # recall probe: 400 random unmatched works; NYT entries by an author with the same family name and a similar title (Jaccard of
    # title words >= 0.5) are listed for reading (written to recall_probe.csv)
    EN = E[~E.series].copy()
    EN['aw'] = EN.author.map(lambda a: set(norm(a).split()))
    EN['tw'] = EN.title.map(lambda t: set(strip_art(norm(t)).split()))
    EN = EN.drop_duplicates(['title', 'author'])
    U = W[~W.matched].sample(400, random_state=SEED)
    probe = []
    for r in U.itertuples():
        fam = fams[r.work_id]
        st_ = set(strip_art(norm(re.split(r'\s*:\s*', r.title)[0])).split())
        if not fam or not st_:
            continue
        c = EN[EN.aw.map(lambda w: bool(w & fam))]
        if c.empty:
            continue
        j = c.tw.map(lambda t: len(t & st_) / len(t | st_))
        c = c[j >= 0.5]
        for b in c.itertuples():
            probe.append(dict(work_id=r.work_id, seattle_title=r.title, creator=r.creator, nyt_title=b.title, nyt_author=b.author))
    pd.DataFrame(probe).to_csv(OUT / 'recall_probe.csv', index=False)
    info.update(nyt_books=len(nb), nyt_books_matched=int(nb.matched.sum()), works=len(W), works_matched=int(W.matched.sum()),
                isbn_rejected=n_rej, key_routes=M.route.value_counts().to_dict(), recall_probe_unmatched_sample=400,
                recall_probe_candidates=len(probe), recall_probe_works=len({x['work_id'] for x in probe}))
    (OUT / 'prep_info.json').write_text(json.dumps(info, indent=1, default=str))

    # ---------------------------------------------------------------- 6. hand-check sheet (50 random matched pairs)
    EM['article'] = EM.work_id.map(art_of)
    P = EM.groupby(['article', 'title', 'author']).agg(route=('route', 'first'), tier=('title_tier', 'first'), first_week=('week', 'min'),
                                                      lists=('list', lambda s: '; '.join(sorted(set(s))[:3])),
                                                      description=('description', 'first'), publisher=('publisher', 'first')).reset_index()
    rep = W.sort_values('checkouts_2016_2026', ascending=False).drop_duplicates('article')
    rs = np.random.RandomState(SEED)
    S = P.iloc[np.sort(rs.choice(len(P), 50, replace=False))].merge(
        rep[['article', 'title', 'creator', 'author_article', 'first_ym']].rename(columns={'title': 'seattle_title'}), on='article')
    S['correct'] = ''
    S['note'] = ''
    f = OUT / 'hand_check_50.csv'
    if not f.exists():
        S.to_csv(f, index=False)
    # second sheet, drawn after the fix of 03:25 (first sheet: 49 of 50 right; the wrong one came from giving an entry to every
    # work of a shared author article); judged the same way
    rs2 = np.random.RandomState(SEED + 1)
    wk = EM.groupby(['article', 'title', 'author']).work_id.agg(lambda s: sorted(set(s))).rename('works').reset_index()
    S2 = P.iloc[np.sort(rs2.choice(len(P), 50, replace=False))].merge(wk, on=['article', 'title', 'author'])
    wt = W.set_index('work_id')
    S2['seattle_title'] = S2.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'title']) for w in ws))
    S2['creator'] = S2.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'creator']) for w in ws))
    S2['first_ym'] = S2.works.map(lambda ws: min(wt.loc[w, 'first_ym'] for w in ws))
    S2['correct'] = ''
    S2['note'] = ''
    f2 = OUT / 'hand_check_50_b.csv'
    if not f2.exists():
        S2.to_csv(f2, index=False)
    rs3 = np.random.RandomState(SEED + 2)
    S3 = P.iloc[np.sort(rs3.choice(len(P), 50, replace=False))].merge(wk, on=['article', 'title', 'author'])
    S3['seattle_title'] = S3.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'title']) for w in ws))
    S3['creator'] = S3.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'creator']) for w in ws))
    S3['first_ym'] = S3.works.map(lambda ws: min(wt.loc[w, 'first_ym'] for w in ws))
    S3['correct'] = ''
    S3['note'] = ''
    f3 = OUT / 'hand_check_50_c.csv'
    if not f3.exists():
        S3.to_csv(f3, index=False)
    rs4 = np.random.RandomState(SEED + 3)
    S4 = P.iloc[np.sort(rs4.choice(len(P), 50, replace=False))].merge(wk, on=['article', 'title', 'author'])
    S4['seattle_title'] = S4.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'title']) for w in ws))
    S4['creator'] = S4.works.map(lambda ws: ' || '.join(str(wt.loc[w, 'creator']) for w in ws))
    S4['first_ym'] = S4.works.map(lambda ws: min(wt.loc[w, 'first_ym'] for w in ws))
    S4['correct'] = ''
    S4['note'] = ''
    f4 = OUT / 'hand_check_50_d.csv'
    if not f4.exists():
        S4.to_csv(f4, index=False)
    log('hand-check sheet', f)


# ============================================================================================ shared loaders
def excluded_months():
    P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
    return {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}         # Test A's rule


def loans_panel():
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
    C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
    L = C.groupby(['work_id', 'mi']).y.sum()
    first = L[L > 0].reset_index().groupby('work_id').mi.min()
    MI = np.arange(mi_of('2005-04'), mi_of('2026-08') + 1)
    LW = L.unstack('mi').reindex(columns=MI).fillna(0).astype(np.float64).reindex(W.work_id).fillna(0)
    A = LW.values.copy()
    fm = first.reindex(W.work_id).values
    for i, m0 in enumerate(fm):
        if np.isnan(m0):
            A[i, :] = np.nan
        else:
            A[i, MI < m0] = np.nan
    return W.work_id.values, MI, A, first



def presence_matrix(work_ids):
    """works x months (2008-06 .. 2026-10) of NYT weeks (0 when not listed); months outside the coverage are not in the matrix"""
    T = pd.read_parquet(OUT / 'nyt_monthly.parquet')
    NM = np.arange(NYT0, NYT1 + 1)
    P = T.pivot_table(index='work_id', columns='mi', values='weeks', aggfunc='sum').reindex(index=work_ids, columns=NM).fillna(0)
    return NM, P.values


NYT0, NYT1 = mi_of('2008-06'), mi_of('2026-10')
SCORE0 = mi_of('2019-01')
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED_A, n_jobs=4, verbose=-1)          # Test A's settings, unchanged


def block_draws(n, rng, block=3):
    k = int(np.ceil(n / block))
    out = np.empty((NB, n), dtype=int)
    for b in range(NB):
        s0 = rng.choice(np.arange(n), k)
        out[b] = np.concatenate([np.arange(a, a + block) % n for a in s0])[:n]
    return out


# ============================================================================================ stage a
def stage_a():
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    R = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_rows_c.parquet',
                        columns=['work_id', 'mi', 'year', 'L_t', 'M6', 'D', 'Y'] + HCOLS + WCOLS)
    works = np.sort(R.work_id.unique())
    NM, PW = presence_matrix(works)
    wi = {w: i for i, w in enumerate(works)}
    ri = R.work_id.map(wi).values
    col = lambda m: m - NYT0
    R['on_t'] = PW[ri, col(R.mi.values)] > 0
    R['E'] = (PW[ri, col(R.mi.values + 1)] > 0).astype('int8')
    cum = np.concatenate([np.zeros((len(works), 1)), np.cumsum(PW, axis=1)], axis=1)    # cum[:, j] = weeks in months before NM[j]
    j = col(R.mi.values)
    R['nyt_w12'] = cum[ri, j] - cum[ri, np.maximum(j - 12, 0)]                          # weeks in months t-12 .. t-1
    R['nyt_before12'] = cum[ri, np.maximum(j - 12, 0)]
    R['nyt_ever_before'] = cum[ri, j] > 0
    R['NYTpast'] = R.nyt_w12 + R.nyt_before12 / 1e4
    T = pd.read_parquet(OUT / 'nyt_monthly.parquet')
    matched = set(T.work_id)
    R['matched'] = R.work_id.isin(matched)
    R = R[(~R.on_t) & (R.mi + 1 <= NYT1)].copy()
    log('rows not listed in month t', len(R), 'matched works rows', int(R.matched.sum()), 'appearances next month', int(R.E.sum()))
    PR = pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_preds_c.parquet',
                         columns=['work_id', 'mi', 'Wrule_D', 'Hnaive_D', 'Wridge_D', 'Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D', 'Wlgbm_Y', 'Hlgbm_Y', 'HWlgbm_Y'])
    R = R.merge(PR, on=['work_id', 'mi'], how='left')
    # refits on the new target (Test A's models and settings, nothing tuned)
    preds = []
    for pop in ('matched', 'all'):
        Rp = R[R.matched] if pop == 'matched' else R
        for Y in range(2019, 2027):
            te = Rp[(Rp.year == Y) & (Rp.mi >= SCORE0)]
            if te.empty:
                continue
            tr = Rp[(Rp.mi + 1) < Y * 12]
            p = te[['work_id', 'mi']].copy()
            p['pop'] = pop
            for name, cols in (('W', WCOLS), ('H', HCOLS), ('HW', HCOLS + WCOLS)):
                m = lgb.LGBMRegressor(**LGB).fit(tr[cols], tr['E'])
                p[f'{name}fit_E'] = m.predict(te[cols])
            preds.append(p)
            log('refit', pop, Y, 'train', len(tr), 'positives', int(tr.E.sum()), 'test', len(te), 'positives', int(te.E.sum()))
    F = pd.concat(preds, ignore_index=True)
    F.to_parquet(OUT / 'a_refit_preds.parquet', index=False)
    keep = ['work_id', 'mi', 'year', 'E', 'matched', 'nyt_ever_before', 'nyt_w12', 'NYTpast', 'L_t', 'M6',
            'Wrule_D', 'Hnaive_D', 'Wridge_D', 'Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D', 'Wlgbm_Y', 'Hlgbm_Y', 'HWlgbm_Y']
    R[keep].to_parquet(OUT / 'a_rows.parquet', index=False)
    log('stage a written')


def auc_pairs(y, s):
    """concordant share of (positive, negative) pairs (ties count 1/2), and the number of pairs"""
    from scipy.stats import rankdata
    y = np.asarray(y).astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan, 0
    r = rankdata(s)
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0), n1 * n0


def score_a():
    R = pd.read_parquet(OUT / 'a_rows.parquet')
    R = R.merge(pd.read_parquet(D / 'db' / 'wiki_led' / 'test_a_rows_c.parquet', columns=['work_id', 'mi', 'h_age']), on=['work_id', 'mi'])
    F = pd.read_parquet(OUT / 'a_refit_preds.parquet')
    PL = pd.read_parquet(D / 'db' / 'wiki_led' / 'placebo_a_preds_c.parquet', columns=['work_id', 'mi', 'pW_D', 'pW_Y', 'pHW_D', 'pHW_Y'])
    R = R.merge(PL, on=['work_id', 'mi'], how='left')
    res = {}
    for pop in ('matched', 'all'):
        X = R[R.mi >= SCORE0] if pop == 'all' else R[(R.mi >= SCORE0) & R.matched]
        X = X.merge(F[F['pop'] == pop].drop(columns='pop'), on=['work_id', 'mi'], how='left')
        X['first'] = X.E.astype(bool) & ~X.nyt_ever_before
        X['ret'] = X.E.astype(bool) & X.nyt_ever_before
        rng = np.random.default_rng(SEED_A)
        months = np.sort(X.mi.unique())
        groups = {m: g for m, g in X.groupby('mi')}
        models = ['Wfit_E', 'Hfit_E', 'HWfit_E', 'Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D', 'Wlgbm_Y', 'Hlgbm_Y', 'HWlgbm_Y', 'Wridge_D', 'Wrule_D',
                  'Hnaive_D', 'NYTpast', 'pW_D', 'pW_Y', 'pHW_D', 'pHW_Y']
        out = dict(n_rows=int(len(X)), n_months=int(len(months)), n_works=int(X.work_id.nunique()), n_appear=int(X.E.sum()),
                   n_first=int(X['first'].sum()), n_return=int(X['ret'].sum()), base_rate=float(X.E.mean()),
                   months_with_appearance=int(sum(groups[m].E.sum() > 0 for m in months)), models={})
        mpos = np.array([groups[m].E.sum() > 0 for m in months])
        BD_all = block_draws(len(months), rng)
        base_m = np.array([groups[m].E.mean() for m in months])
        out['base_rate_month_mean'] = float(base_m.mean())
        per = {}
        for c in models:
            if X[c].isna().any():
                log('  missing scores', pop, c, int(X[c].isna().sum()))
            auc_m, top_m, conc, pairs = [], [], {'all': [0.0, 0], 'first': [0.0, 0], 'ret': [0.0, 0]}, None
            for m in months:
                g = groups[m]
                s_ = g[c].fillna(g[c].min() - 1).values
                a, _ = auc_pairs(g.E.values, s_)
                auc_m.append(a)
                o = np.lexsort((g.work_id.values, -s_))[:20]
                top_m.append(g.E.values[o].mean())
                for kind in ('all', 'first', 'ret'):
                    yk = g.E.values.astype(bool) if kind == 'all' else g[kind].values
                    keep = yk | ~g.E.values.astype(bool)
                    a2, n2 = auc_pairs(yk[keep], s_[keep])
                    if n2:
                        conc[kind][0] += a2 * n2
                        conc[kind][1] += n2
            auc_m, top_m = np.array(auc_m), np.array(top_m)
            per[c] = (auc_m, top_m)
            am = auc_m[mpos]
            BDm = block_draws(len(am), np.random.default_rng(SEED_A))
            bt = top_m[BD_all].mean(1)
            ba = am[BDm].mean(1)
            from sklearn.metrics import roc_auc_score
            out['models'][c] = dict(
                auc_month_mean=float(am.mean()), auc_lo=float(np.percentile(ba, 2.5)), auc_hi=float(np.percentile(ba, 97.5)),
                auc_pooled=float(roc_auc_score(X.E, X[c].fillna(X[c].min() - 1))),
                auc_within_pairs=float(conc['all'][0] / conc['all'][1]),
                auc_within_pairs_first=float(conc['first'][0] / conc['first'][1]) if conc['first'][1] else None,
                auc_within_pairs_return=float(conc['ret'][0] / conc['ret'][1]) if conc['ret'][1] else None,
                top20=float(top_m.mean()), top20_lo=float(np.percentile(bt, 2.5)), top20_hi=float(np.percentile(bt, 97.5)),
                top20_ratio=float(top_m.mean() / base_m.mean()))
            log(pop, c, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out['models'][c].items()})
        # paired differences on the same months
        pairs_ = [('HWfit_E', 'Hfit_E'), ('Wfit_E', 'Hfit_E'), ('HWlgbm_D', 'Hlgbm_D'), ('HWlgbm_Y', 'Hlgbm_Y'), ('HWfit_E', 'NYTpast'),
                  ('Hfit_E', 'NYTpast'), ('Wlgbm_D', 'pW_D'), ('Wlgbm_Y', 'pW_Y'), ('HWlgbm_D', 'pHW_D'), ('HWlgbm_Y', 'pHW_Y')]
        out['paired'] = {}
        for a_, b_ in pairs_:
            da = (per[a_][0] - per[b_][0])[mpos]
            dt = per[a_][1] - per[b_][1]
            BDm = block_draws(len(da), np.random.default_rng(SEED_A))
            ba, bt = da[BDm].mean(1), dt[BD_all].mean(1)
            out['paired'][f'{a_}_minus_{b_}'] = dict(auc=float(da.mean()), auc_lo=float(np.percentile(ba, 2.5)), auc_hi=float(np.percentile(ba, 97.5)),
                                                    top20=float(dt.mean()), top20_lo=float(np.percentile(bt, 2.5)), top20_hi=float(np.percentile(bt, 97.5)))
        # added after the first scoring (03:34): pair-weighted within-month AUC by the book's age in Seattle at t (months since its
        # first loan, h_age), each group against its own negatives, to see how much of the skill is the recognition of new books
        out['by_age'] = {}
        for lab, lo_, hi_ in (('lt12', 0, 11), ('12to35', 12, 35), ('ge36', 36, 10 ** 6)):
            Xg = X[(X.h_age >= lo_) & (X.h_age <= hi_)]
            d_ = dict(rows=int(len(Xg)), appear=int(Xg.E.sum()), first=int(Xg['first'].sum()))
            mg = [g for m, g in Xg.groupby('mi')]
            BDg = block_draws(len(mg), np.random.default_rng(SEED_A))
            nd = {}
            for c in models:
                nums, dens = np.zeros(len(mg)), np.zeros(len(mg))
                for q, g in enumerate(mg):
                    a2, n2 = auc_pairs(g.E.values, g[c].fillna(g[c].min() - 1).values)
                    if n2:
                        nums[q], dens[q] = a2 * n2, n2
                nd[c] = (nums, dens)
                bs = nums[BDg].sum(1) / dens[BDg].sum(1)
                d_[c] = float(nums.sum() / dens.sum()) if dens.sum() else None
                d_[c + '_lo'], d_[c + '_hi'] = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
            for a_, b_ in (('HWfit_E', 'Hfit_E'), ('Wfit_E', 'Hfit_E')):
                diff = nd[a_][0].sum() / nd[a_][1].sum() - nd[b_][0].sum() / nd[b_][1].sum()
                bs = nd[a_][0][BDg].sum(1) / nd[a_][1][BDg].sum(1) - nd[b_][0][BDg].sum(1) / nd[b_][1][BDg].sum(1)
                d_[f'{a_}_minus_{b_}'] = [float(diff), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            out['by_age'][lab] = d_
        # who appears: share of appearances that were listed in the 12 months before, and by origin year
        app = X[X.E == 1]
        out['appear_listed_last12'] = float((app.nyt_w12 > 0).mean())
        out['appear_listed_ever_before'] = float(app.nyt_ever_before.mean())
        out['by_year'] = {int(y): dict(rows=int(len(g)), appear=int(g.E.sum())) for y, g in X.groupby('year')}
        res[pop] = out
    return res


# ============================================================================================ stage b
def stage_b():
    works, MI, A, first = loans_panel()
    T = pd.read_parquet(OUT / 'nyt_monthly.parquet')
    matched = np.isin(works, T.work_id.unique())
    works, A = works[matched], A[matched]
    EXCL = excluded_months()
    ex = np.isin(MI, sorted(EXCL))
    A = A.copy()
    A[:, ex] = np.nan
    dL = np.full_like(A, np.nan)
    dL[:, 1:] = np.log1p(A[:, 1:]) - np.log1p(A[:, :-1])
    NM, PW = presence_matrix(works)
    # align presence to the loans month grid; NaN outside the NYT coverage
    N = np.full(A.shape, np.nan)
    jj = np.searchsorted(MI, NM)
    ok = (jj < len(MI)) & (MI[np.minimum(jj, len(MI) - 1)] == NM)
    N[:, jj[ok]] = (PW[:, ok] > 0).astype(float)
    # beyond the loans grid (2026-09, 2026-10) presence is still known: extend the grid for the leads
    ext = NM[NM > MI[-1]]
    Next = (PW[:, np.isin(NM, ext)] > 0).astype(float)
    Nfull = np.concatenate([N, Next], axis=1)
    Ent = np.full(Nfull.shape, np.nan)
    Ent[:, 1:] = np.where(np.isnan(Nfull[:, 1:]) | np.isnan(Nfull[:, :-1]), np.nan, ((Nfull[:, 1:] == 1) & (Nfull[:, :-1] == 0)).astype(float))
    t_ok = (MI >= mi_of('2008-07'))
    rng = np.random.default_rng(SEED)
    Cw = rng.multinomial(len(works), np.ones(len(works)) / len(works), size=NB).astype(float)   # bootstrap over works
    res = {}
    for label, t0 in (('2008_2026', mi_of('2008-07')), ('2016_2026', mi_of('2016-01'))):
        for sig_name, S_ in (('presence', Nfull), ('entry', Ent)):
            rows = {}
            for k in range(-3, 4):
                cols = np.where((MI >= t0) & t_ok)[0]
                tk = cols + k
                okc = (tk >= 0) & (tk < S_.shape[1])
                cols, tk = cols[okc], tk[okc]
                x = dL[:, cols]
                y = S_[:, tk]
                m = ~np.isnan(x) & ~np.isnan(y)
                n = m.sum(1)
                xs = np.where(m, x, 0.0); ys = np.where(m, y, 0.0)
                with np.errstate(invalid='ignore', divide='ignore'):
                    xm = xs.sum(1) / n; ym = ys.sum(1) / n
                xd = np.where(m, x - xm[:, None], 0.0); yd = np.where(m, y - ym[:, None], 0.0)
                sxy, sxx, syy = (xd * yd).sum(1), (xd ** 2).sum(1), (yd ** 2).sum(1)
                good = n >= 3
                sxy, sxx, syy = sxy * good, sxx * good, syy * good
                r = sxy.sum() / np.sqrt(sxx.sum() * syy.sum())
                rb = (Cw @ sxy) / np.sqrt((Cw @ sxx) * (Cw @ syy))
                rows[k] = dict(r=float(r), lo=float(np.percentile(rb, 2.5)), hi=float(np.percentile(rb, 97.5)), n_rows=int(m[good].sum()),
                               n_works=int(good.sum()))
            res[f'{sig_name}_{label}'] = rows
            log('lead/lag', sig_name, label, {k: round(v['r'], 4) for k, v in rows.items()})
    (OUT / 'b_results.json').write_text(json.dumps(res, indent=1))
    return res


# ============================================================================================ stage c
def stage_c():
    works, MI, A, first = loans_panel()
    EXCL = excluded_months()
    ex = np.isin(MI, sorted(EXCL))
    A = A.copy()
    A[:, ex] = np.nan
    NM, PW = presence_matrix(works)
    cumP = np.concatenate([np.zeros((len(works), 1)), np.cumsum(PW, axis=1)], axis=1)
    EM = pd.read_parquet(OUT / 'nyt_entries_matched.parquet')
    fw = EM.groupby('work_id').agg(first_week=('week', 'min'))
    ff = EM.merge(fw, on='work_id')
    fw['family'] = ff[ff.week == ff.first_week].groupby('work_id').family.agg(lambda s: s.value_counts().index[0])
    fw['e'] = fw.first_week.dt.year * 12 + fw.first_week.dt.month - 1
    wi = {w: i for i, w in enumerate(works)}
    fw['i'] = fw.index.map(wi)
    fw['first_loan'] = first.reindex(fw.index).values
    n_all = len(fw)
    fl_all = first.reindex(works).values
    K = np.arange(-3, 13)

    def nyt_weeks(m0, m1):                       # NYT weeks of every work in months m0..m1 (inside the coverage)
        a0, a1 = max(m0, NYT0) - NYT0, min(m1, NYT1) - NYT0 + 1
        return cumP[:, a1] - cumP[:, a0] if a1 > a0 else np.zeros(len(works))

    def run(ev, base):
        """ev: events with columns e, i, family (index work_id). base 'own' (choice 15-16) or 'd2' (D2's C2-C3)."""
        rows = []
        for e in sorted(ev.e.unique()):
            j = int(np.searchsorted(MI, e))
            if base == 'own':
                w6 = A[:, j - 6:j]
                with np.errstate(all='ignore'):
                    M6 = np.nanmedian(w6, axis=1)
                elig = (fl_all <= e - 6) & ~np.isnan(M6)
                ctrl_free = nyt_weeks(e - 12, e + 12) == 0
            else:
                t0 = j - 4
                w6 = A[:, t0 - 5:t0 + 1]
                with np.errstate(all='ignore'):
                    M6 = np.nanmedian(w6, axis=1)
                    present = np.nansum(A[:, t0 - 11:t0 + 1], axis=1) > 0
                elig = present & (np.isfinite(w6).sum(1) >= 3)
                ctrl_free = nyt_weeks(e - 9, e + 12) == 0
            lm = np.log1p(M6)
            dec = np.full(len(works), -1)
            rk = pd.Series(lm[elig]).rank(pct=True, method='average').values
            dec[elig] = np.minimum((rk * 10 - 1e-9).astype(int), 9)
            ctrl_ok = elig & ctrl_free
            Lk = np.full((len(works), len(K)), np.nan)
            for q, k in enumerate(K):
                if 0 <= j + k < len(MI):
                    Lk[:, q] = A[:, j + k]
            with np.errstate(all='ignore'):
                Dk = (np.log1p(Lk.astype(np.float32)) - np.log1p(M6.astype(np.float32))[:, None]).astype(np.float64)
            rose = np.where(np.isnan(Dk), np.nan, (Dk >= np.log(1.5)).astype(float))
            surg = np.where(np.isnan(Dk), np.nan, ((Dk >= np.log(2)) & (Lk - M6[:, None] >= 5)).astype(float))
            for r in ev[ev.e == e].itertuples():
                i = r.i
                if not elig[i]:
                    continue
                cm = ctrl_ok & (dec == dec[i])
                cm[i] = False
                if cm.sum() == 0:
                    continue
                row = dict(work_id=r.Index, e=e, family=r.family, M6=M6[i], decile=int(dec[i]), n_controls=int(cm.sum()))
                with np.errstate(all='ignore'):
                    for q, k in enumerate(K):
                        row[f'D_{k}'] = Dk[i, q]; row[f'cD_{k}'] = np.nanmean(Dk[cm, q]) if np.isfinite(Dk[cm, q]).any() else np.nan
                        row[f'rose_{k}'] = rose[i, q]; row[f'crose_{k}'] = np.nanmean(rose[cm, q]) if np.isfinite(rose[cm, q]).any() else np.nan
                        row[f'surg_{k}'] = surg[i, q]; row[f'csurg_{k}'] = np.nanmean(surg[cm, q]) if np.isfinite(surg[cm, q]).any() else np.nan
                rows.append(row)
        return pd.DataFrame(rows)

    def summarize(ev):
        rng = np.random.default_rng(SEED)
        res = {}
        for k in K:
            r_ = {}
            for nm in ('D', 'rose', 'surg'):
                x = (ev[f'{nm}_{k}'] - ev[f'c{nm}_{k}']).values
                x = x[~np.isnan(x)]
                if len(x) < 10:
                    continue
                b = x[rng.integers(0, len(x), size=(NB, len(x)))].mean(1)
                r_[nm] = dict(event=float(np.nanmean(ev[f'{nm}_{k}'])), control=float(np.nanmean(ev[f'c{nm}_{k}'])), excess=float(x.mean()),
                              lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)), n=int(len(x)))
            res[int(k)] = r_
        return res

    ev = fw[(fw.e >= mi_of('2009-01')) & (fw.e <= MI[-1])]
    log('events (first NYT week 2009-01 .. 2026-08)', len(ev), 'of', n_all, 'matched works')
    res = dict(n_matched_works=int(n_all), n_events_2009_2026=int(len(ev)))
    for base in ('own', 'd2'):
        EV = run(ev, base)
        EV.to_parquet(OUT / f'c_events_{base}.parquet', index=False)
        # placebo (added): every event moved 24 months earlier; the fake window ends 12 months before the real first week
        pl = ev.assign(e=ev.e - 24)
        pl = pl[pl.e >= mi_of('2006-07')]
        PL = run(pl, base)
        res[base] = dict(n_with_controls=int(len(EV)), median_controls=float(EV.n_controls.median()),
                         n_by_family=EV.family.value_counts().to_dict(), all=summarize(EV),
                         by_family={f: summarize(g) for f, g in EV.groupby('family') if len(g) >= 30},
                         placebo=dict(n=int(len(PL)), all=summarize(PL)))
        log('event study', base, len(EV), {k: round(res[base]['all'][k]['D']['excess'], 3) for k in (-3, -1, 0, 1, 2, 3, 6, 12)},
            'placebo', len(PL), {k: round(res[base]['placebo']['all'][k]['D']['excess'], 3) for k in (-1, 0, 1, 2, 6)})
    est = ev[ev.first_loan <= ev.e - 6]
    new = ev[~(ev.first_loan <= ev.e - 6)]
    res['n_established_own'] = int(len(est)); res['n_new_own'] = int(len(new))
    # new books: first Seattle loan and peak month relative to the first NYT week
    rel_first, rel_peak = [], []
    for r in new.itertuples():
        if np.isnan(r.first_loan):
            continue
        rel_first.append(r.first_loan - r.e)
        j0 = int(np.searchsorted(MI, int(r.first_loan)))
        seg = A[r.i, j0:j0 + 24]
        if np.isfinite(seg).sum() >= 12:
            rel_peak.append(int(r.first_loan + np.nanargmax(seg) - r.e))
    rf, rp = np.array(rel_first), np.array(rel_peak)
    res['new_books'] = dict(n=int(len(rf)), first_loan_rel_quartiles=[float(x) for x in np.percentile(rf, [25, 50, 75])],
                            share_first_loan_before=float((rf < 0).mean()), share_same_month=float((rf == 0).mean()),
                            share_after=float((rf > 0).mean()), n_peak=int(len(rp)),
                            peak_rel_quartiles=[float(x) for x in np.percentile(rp, [25, 50, 75])],
                            share_peak_m0_to_m2=float(((rp >= 0) & (rp <= 2)).mean()), share_peak_before=float((rp < 0).mean()))
    (OUT / 'c_results.json').write_text(json.dumps(res, indent=1, default=float))
    return res


# ============================================================================================ report
def stage_report():
    from scipy.stats import beta
    info = json.loads((OUT / 'prep_info.json').read_text())
    A_ = json.loads((OUT / 'a_results.json').read_text())
    B_ = json.loads((OUT / 'b_results.json').read_text())
    C_ = json.loads((OUT / 'c_results.json').read_text())
    W = pd.read_parquet(OUT / 'works_match_info.parquet')
    NBk = pd.read_parquet(OUT / 'nyt_books_side.parquet')
    KM = pd.read_parquet(OUT / 'nyt_key_matches.parquet')
    sheets = {}
    for tag, f in (('1', 'hand_check_50.csv'), ('2', 'hand_check_50_b.csv'), ('3', 'hand_check_50_c.csv'), ('4', 'hand_check_50_d.csv')):
        h = pd.read_csv(OUT / f, dtype={'correct': str})
        sheets[tag] = (int((h.correct == 'yes').sum()), int(h.correct.isin(['yes', 'no']).sum()))
    ok, n = sheets['4']
    cp_lo = beta.ppf(0.025, ok, n - ok + 1) if ok > 0 else 0.0
    cp_hi = beta.ppf(0.975, ok + 1, n - ok) if ok < n else 1.0
    pr = pd.read_csv(OUT / 'recall_probe.csv')
    L = []
    w = L.append
    pc = lambda x, d=1: f'{100 * x:.{d}f}%'
    f3 = lambda x: f'{x:.3f}'
    ci = lambda v, a, b, f=f3: f'{f(v)} ({f(a)} to {f(b)})'
    nm = int(W.matched.sum())
    am, aa = A_['matched'], A_['all']
    M_ = am['models']
    c_own, c_d2 = C_['own'], C_['d2']
    ex = lambda b, k, v='D': b['all'][str(k)][v]
    ent = B_['entry_2008_2026']
    # ---------------------------------------------------------------- the five lines
    w('# D3: New York Times best-seller lists as a second target (addendum i)\n')
    w(f'1. Of the 7,747 Seattle books of Test A, {nm:,} ({pc(nm / len(W))}) were on a New York Times best-seller list at least once between June 2008 '
      f'and October 2026. They are mostly books published after 2008 and among the most borrowed; a hand check of 50 random matches found {ok} right.')
    w(f'2. Among those books, Wikipedia alone ranks which ones come onto a list next month far better than chance (AUC {f3(M_["Wfit_E"]["auc_month_mean"])}, '
      f'where 0.5 is chance; {pc(M_["Wfit_E"]["top20"])} of its monthly top 20 are listed next month, against {pc(am["base_rate_month_mean"])} of all), '
      f'but the library history ranks them better (AUC {f3(M_["Hfit_E"]["auc_month_mean"])}, top 20 {pc(M_["Hfit_E"]["top20"])}); '
      f'much of the skill of both is spotting new releases that are about to be listed.')
    d = am['paired']['HWfit_E_minus_Hfit_E']
    g36 = am['by_age']['ge36']
    w(f'3. Both together are best (AUC {f3(M_["HWfit_E"]["auc_month_mean"])}, top 20 {pc(M_["HWfit_E"]["top20"])}): Wikipedia adds a little to the library history '
      f'({d["auc"]:+.3f} AUC, {100 * d["top20"]:+.1f} points in the top 20, both intervals above zero); for books in the library three years or more, '
      f'Wikipedia alone does as well as the library history (AUC {f3(g36["Wfit_E"])} and {f3(g36["Hfit_E"])}) and the gain of the two together is largest '
      f'({g36["HWfit_E_minus_Hfit_E"][0]:+.3f}).')
    w(f'4. Borrowing and the lists move mostly in the same month: Seattle loans jump in the month a book enters a list (correlation {f3(ent["0"]["r"])}), '
      f'keep rising a little in the month after ({f3(ent["-1"]["r"])}) and rise less in the month before ({f3(ent["1"]["r"])}).')
    w(f'5. For books already in the library, loans (against their own earlier level) after the first list week are about {math.exp(ex(c_own, 0)["excess"]):.1f} to '
      f'{math.exp(ex(c_own, 2)["excess"]):.1f} times those of similar books in months 0 to 2 and still {math.exp(ex(c_own, 12)["excess"]):.1f} times after a year, '
      f'having started to rise one to three months before; new bestsellers are borrowed from their first month and peak a median '
      f'{C_["new_books"]["peak_rel_quartiles"][1]:.0f} months after their first list week.\n')
    w(f'Direction D3 of prereg/addenda_wiki_led/2026-10-22_i_directions.json. Code: code/main_study/wiki_led/dirs/d3_nyt.py (its header lists every '
      f'setting the record left open, with the time it was written). Data: data/db/wiki_led/dirs/d3_nyt/. Descriptive; every interval is a 95% interval. '
      f'Run 22 Oct 2026.\n')
    # ---------------------------------------------------------------- 1 data and matching
    w('## 1. Data and matching\n')
    w(f'- **Lists.** {info["files_with_lists"]} weekly overview files of the official Books API ({info["first_week"]} to {info["last_week"]}; the 2008-06-08 file is empty), '
      f'{info["entries"]:,} list entries after dropping {info["dropped_stale_list_copies"]} stale second copies of a list (files of 2008 to 2011 repeat some lists; the copy that '
      f'repeats unchanged in other weeks is dropped). The "Children\'s & Young Adult Series" lists ({info["series_entries"]:,} entries) are left out because their entries '
      f'are series, not books. {info["distinct_books_title_author"]:,} distinct books (title and author). A week belongs to the month of its published date; the list '
      f'reflects sales of a week that ended about two weeks earlier.')
    w(f'- **ISBNs.** The collector kept only each entry\'s primary ISBN-13 ({pc(info["entries_with_isbn13"])} of entries have one), not the other ISBNs the API lists. '
      f'Seattle records carry ISBNs only for ebooks and audiobooks, none for print, so the Wikidata edition ISBNs of each work\'s matched item were added. '
      f'An ISBN hit needs the titles to agree.')
    km = KM.route.value_counts()
    w(f'- **Routes** (distinct NYT title, author and ISBN combinations): Seattle ISBN {km.get("isbn_seattle", 0):,}, Wikidata ISBN {km.get("isbn_wikidata", 0):,}, '
      f'title and author family name {km.get("title_author", 0):,}, ambiguous and dropped {km.get("ambiguous_title", 0) + km.get("ambiguous_isbn", 0):,}, '
      f'no match {km.get("none", 0):,}. An entry counts for every Test A work of the matched book whose title agrees (Test A has 544 works that share 224 articles).')
    w(f'- **Match rate.** {nm:,} of 7,747 Test A works ({pc(nm / len(W))}) have at least one NYT week; {int(NBk.matched.sum()):,} of {len(NBk):,} distinct NYT books '
      f'({pc(NBk.matched.mean())}) reach a Test A work (most NYT books have no Wikipedia article of their own or fewer than 500 Seattle loans, so they are not in Test A).')
    w(f'- **Hand check.** 50 random matched pairs (NYT book and Seattle work), read on both sides: {ok} of {n} right (exact interval {pc(cp_lo)} to {pc(cp_hi)}) on the '
      f'fourth sheet, drawn after the last change to the rules. Earlier sheets: {sheets["1"][0]}, {sheets["2"][0]} and {sheets["3"][0]} of 50; their errors (an entry '
      f'also given to another book that shares an author page as its article; a Dirk Cussler novel matched through the author page "Clive Cussler"; graphic versions; '
      f'another book of a series, such as SKIPPYJON JONES: SNOW WHAT on Skippyjon Jones) led to the rules in the header, choices 6 to 7c. Sheets: hand_check_50*.csv.')
    w(f'- **Missed matches.** In 400 random unmatched Test A works, NYT entries by an author with the same family name and a similar title were listed: '
      f'{info["recall_probe_candidates"]} entries for {info["recall_probe_works"]} works, all other books (for example IF YOU GIVE A DOG A DONUT against If you give a mouse '
      f'a cookie, BEYOND THE ICE LIMIT against The Ice Limit). No missed match was found this way; matches lost to unusual author strings are not covered by this check.\n')
    # ---------------------------------------------------------------- 2 which books match
    w('## 2. Which books match\n')
    W['fy'] = W.first_ym.astype(str).str[:4].astype(int)
    W['pub_bin'] = pd.cut(W.pub_year_min, [0, 2000, 2008, 2016, 2027], labels=['up to 2000', '2001 to 2008', '2009 to 2016', '2017 to 2026'])
    W['ck_q'] = pd.qcut(W.checkouts_2016_2026, 4, labels=['lowest quarter', 'second', 'third', 'highest quarter'])
    w('| Test A works | works | matched |')
    w('|---|---:|---:|')
    for lab, g in W.groupby('pub_bin', observed=True):
        w(f'| earliest Seattle edition {lab} | {len(g):,} | {pc(g.matched.mean())} |')
    for lab, g in W.groupby('ck_q', observed=True):
        w(f'| Seattle loans 2016 to 2026, {lab} | {len(g):,} | {pc(g.matched.mean())} |')
    for lab, g in W.groupby(W.fiction.map({True: 'fiction', False: 'not fiction'})):
        w(f'| Seattle subjects: {lab} | {len(g):,} | {pc(g.matched.mean())} |')
    w(f'| all | {len(W):,} | {pc(W.matched.mean())} |\n')
    fam = W[W.matched].main_family.value_counts(normalize=True)
    w(f'Matched works by the list family they appear on most: fiction {pc(fam.get("fiction", 0))}, nonfiction {pc(fam.get("nonfiction", 0))}, children and young adult '
      f'{pc(fam.get("children_ya", 0))}, graphic {pc(fam.get("graphic", 0))}. Median first NYT year of a matched work {int(W[W.matched].first_nyt_year.median())}; '
      f'median first Seattle loan {int(W[W.matched].fy.median())} (unmatched {int(W[~W.matched].fy.median())}). On the NYT side the share that reaches a Test A work '
      f'grows with time on the lists: ' + ', '.join(f'{lab} {pc(g.matched.mean())}' for lab, g in NBk.groupby(pd.cut(NBk.weeks, [0, 1, 4, 12, 52, 5000],
      labels=['1 week', '2 to 4 weeks', '5 to 12 weeks', '13 to 52 weeks', 'over 52 weeks']), observed=True)) + '. So the matched set is mostly recent bestsellers '
      'that Seattle lent a lot; classics and older books are rarely on these lists (the lists start in 2008).\n')
    # ---------------------------------------------------------------- 3 prediction
    w('## 3. (a) Which books come onto a list next month\n')
    w(f'Rows: Test A\'s rows (origin months 2019-01 to 2026-07, features at the end of month t) of books with no NYT week in month t; the target is at least one NYT week '
      f'in month t+1. Main population, as the record says, the matched works ({am["n_rows"]:,} rows, {am["n_works"]:,} works, {am["n_months"]} months, {am["n_appear"]:,} '
      f'appearances, base rate {pc(am["base_rate_month_mean"], 2)} per month). This population is chosen with hindsight (books listed at some time in 2008 to 2026); '
      f'the same test on all 7,747 works ({aa["n_rows"]:,} rows, base rate {pc(aa["base_rate_month_mean"], 2)}) is the check. Of the appearances, {am["n_first"]} are '
      f'first appearances (never listed since June 2008) and {am["n_return"]} returns; {pc(am["appear_listed_last12"])} had been listed in the 12 months before.\n')
    w('Models: "refit" = Test A\'s LightGBM regressor and settings, unchanged, trained on the new target walk-forward by year (W: Wikipedia features, H: library history, '
      'HW: both). "Test A" = Test A\'s stored scores for its own targets (change D and level Y), not trained on the NYT target. NYT-past = weeks on any list in the 12 '
      'months before (a reference added here). Placebo = Test A\'s stored placebo scores (each book scored with the pages of a donor book of similar traffic).\n')
    w('| model | AUC, mean of months (interval) | AUC first appearances | AUC returns | top-20 share (interval) | top 20 / base rate | all works: AUC | all works: top 20 |')
    w('|---|---|---:|---:|---|---:|---:|---:|')
    names = [('Wfit_E', 'W refit'), ('Hfit_E', 'H refit'), ('HWfit_E', 'HW refit'), ('Wlgbm_D', 'W, Test A change'), ('Hlgbm_D', 'H, Test A change'),
             ('HWlgbm_D', 'HW, Test A change'), ('Wlgbm_Y', 'W, Test A level'), ('Hlgbm_Y', 'H, Test A level'), ('HWlgbm_Y', 'HW, Test A level'),
             ('Wridge_D', 'W ridge, Test A change'), ('Wrule_D', 'Wikipedia rule, Test A'), ('Hnaive_D', 'naive library rule, Test A'), ('NYTpast', 'NYT-past rule'),
             ('pW_D', 'placebo W, change'), ('pW_Y', 'placebo W, level'), ('pHW_D', 'placebo HW, change'), ('pHW_Y', 'placebo HW, level')]
    for c, lab in names:
        v, va = M_[c], aa['models'][c]
        fa = v['auc_within_pairs_first']
        w(f'| {lab} | {ci(v["auc_month_mean"], v["auc_lo"], v["auc_hi"])} | {f3(fa) if fa is not None else "-"} | {f3(v["auc_within_pairs_return"])} | '
          f'{pc(v["top20"])} ({pc(v["top20_lo"])} to {pc(v["top20_hi"])}) | {v["top20_ratio"]:.0f} | {f3(va["auc_month_mean"])} | {pc(va["top20"])} |')
    w(f'| chance | 0.500 | 0.500 | 0.500 | {pc(am["base_rate_month_mean"], 2)} | 1 | 0.500 | {pc(aa["base_rate_month_mean"], 2)} |\n')
    w('AUC first appearances and returns: share of (listed, not listed) pairs of the same month ranked right, with only that kind of appearance as the listed side. '
      'The NYT-past rule scores 0 for every book never listed, so it ranks first appearances below the rest.\n')
    w('Paired differences on the same months (matched works; all works in brackets):\n')
    w('| difference | AUC (interval) | top-20 share, points (interval) |')
    w('|---|---|---|')
    for k_, lab in (('HWfit_E_minus_Hfit_E', 'HW refit minus H refit'), ('Wfit_E_minus_Hfit_E', 'W refit minus H refit'),
                    ('HWlgbm_D_minus_Hlgbm_D', 'Test A change: HW minus H'), ('HWlgbm_Y_minus_Hlgbm_Y', 'Test A level: HW minus H'),
                    ('HWfit_E_minus_NYTpast', 'HW refit minus NYT-past'), ('Wlgbm_D_minus_pW_D', 'W minus its placebo, change'),
                    ('Wlgbm_Y_minus_pW_Y', 'W minus its placebo, level')):
        v, va = am['paired'][k_], aa['paired'][k_]
        w(f'| {lab} | {v["auc"]:+.3f} ({v["auc_lo"]:+.3f} to {v["auc_hi"]:+.3f}) [{va["auc"]:+.3f}] | {100 * v["top20"]:+.1f} ({100 * v["top20_lo"]:+.1f} to '
          f'{100 * v["top20_hi"]:+.1f}) [{100 * va["top20"]:+.1f}] |')
    w('')
    w('By the book\'s age in Seattle at month t (pair-weighted AUC within months, interval by month blocks; added after the first scoring):\n')
    w('| age in Seattle | rows | appearances (first) | W refit | H refit | HW refit | HW minus H | NYT-past |')
    w('|---|---:|---:|---|---|---|---|---|')
    for g, lab in (('lt12', 'under 12 months'), ('12to35', '12 to 35 months'), ('ge36', '36 months or more')):
        v = am['by_age'][g]
        dd = v['HWfit_E_minus_Hfit_E']
        w(f'| {lab} | {v["rows"]:,} | {v["appear"]} ({v["first"]}) | {ci(v["Wfit_E"], v["Wfit_E_lo"], v["Wfit_E_hi"])} | {ci(v["Hfit_E"], v["Hfit_E_lo"], v["Hfit_E_hi"])} | '
          f'{ci(v["HWfit_E"], v["HWfit_E_lo"], v["HWfit_E_hi"])} | {dd[0]:+.3f} ({dd[1]:+.3f} to {dd[2]:+.3f}) | {ci(v["NYTpast"], v["NYTpast_lo"], v["NYTpast_hi"])} |')
    w('')
    w('Reading. Refitted on the sales target, Wikipedia alone ranks next month\'s list appearances well above chance but below the library history, and '
      'Wikipedia adds a small amount to the library history. Test A\'s stored Wikipedia scores beat their placebo (the pages of a similar book by another author) '
      f'by {am["paired"]["Wlgbm_D_minus_pW_D"]["auc"]:.2f} (change) and {am["paired"]["Wlgbm_Y_minus_pW_Y"]["auc"]:.2f} (level) in AUC, so the ranking comes from '
      'the book\'s own pages and not only from their traffic level; the refits were not given a placebo. Much of the ranking for all three models is the recognition of new books: a book '
      'that has just reached the library and just got a Wikipedia page is often a new release about to be listed (the refits rank first appearances with AUC above '
      '0.9). '
      'Returns to a list (paperback editions, film tie-ins, books listed again) are harder; among books in the library three years or more, Wikipedia alone matches '
      'the library history and the two together do best, while for books in the library one to three years the NYT-past rule (a recent bestseller coming back, often '
      'as a paperback) is at least as good. Test A\'s own scores, trained to rank next month\'s borrowing change, rank list appearances much less well than the refits '
      '(the library change model is close to chance for returns), so the sales target needs its own fit; Test A\'s level scores (next month\'s loans) do better, '
      'because books borrowed a lot are the ones that sell.\n')
    # ---------------------------------------------------------------- 4 lead lag
    w('## 4. (b) Lead and lag\n')
    w(f'Matched works, monthly change in Seattle loans (log of 1 + loans, all formats; excluded months and months before the first loan left out) against NYT presence '
      f'(0/1) or the list entry month (listed in a month, not in the month before), both demeaned within the work and pooled over works. k > 0: the list k months '
      f'after the loan change (borrowing first); k < 0: the list k months before (list first). Intervals: bootstrap over works.\n')
    w('| k | presence 2008 to 2026 | entry 2008 to 2026 | presence 2016 to 2026 | entry 2016 to 2026 |')
    w('|---:|---|---|---|---|')
    for k in range(-3, 4):
        cells = []
        for key in ('presence_2008_2026', 'entry_2008_2026', 'presence_2016_2026', 'entry_2016_2026'):
            v = B_[key][str(k)]
            cells.append(ci(v['r'], v['lo'], v['hi']))
        w(f'| {k:+d} | ' + ' | '.join(cells) + ' |')
    v0 = B_['entry_2008_2026']['0']
    w(f'\nRows: {v0["n_rows"]:,} work-months of {v0["n_works"]:,} works (entry, k = 0). Reading: the loan change goes with the entry month itself; the entry is '
      f'followed by a further rise in the next month (k = -1) more than it is preceded by one (k = +1). Presence (a state that lasts for months) correlates with '
      f'loan changes in the same and later months and negatively with changes 2 and 3 months after the book was listed, when loans fall back. Correlations are small '
      f'because most months of most books have neither an entry nor a large change.\n')
    # ---------------------------------------------------------------- 5 event study
    w('## 5. (c) Seattle loans around the first NYT week\n')
    w(f'Event: the month of a matched work\'s first NYT week, 2009-01 to 2026-08 ({C_["n_events_2009_2026"]:,} of {C_["n_matched_works"]:,} matched works; earlier '
      f'first weeks are left out because lists before June 2008 were not collected). {C_["n_established_own"]} of them were in the Seattle library at least 6 months '
      f'before (established books); the other {C_["n_new_own"]:,} are new books (section 5.3). Controls: works of the same month and loan decile with no NYT week in the '
      f'window. Two baselines: "own" (choices 15 and 16: M6 over months -6 to -1, so months -3 to -1 are inside the baseline) and "D2" (D2\'s baseline, months -9 to -4, '
      f'added after the first results, so months -3 to -1 show any rise before the event). Placebo: every event moved 24 months earlier. Excess D = log(1 + loans) '
      f'minus log(1 + M6), event minus the mean of its controls (exp(D) - 1 is the extra share of loans). Rose and surged: Test A\'s rules.\n')
    for b, lab in (('own', 'own baseline'), ('d2', 'D2 baseline')):
        cb = C_[b]
        w(f'### 5.{1 if b == "own" else 2} {lab}: {cb["n_with_controls"]} events (fiction {cb["n_by_family"].get("fiction", 0)}, nonfiction '
          f'{cb["n_by_family"].get("nonfiction", 0)}, children and young adult {cb["n_by_family"].get("children_ya", 0)}, graphic {cb["n_by_family"].get("graphic", 0)}), '
          f'median {cb["median_controls"]:.0f} controls each; placebo {cb["placebo"]["n"]} events\n')
        w('| month | excess D (interval) | loans times similar books | excess rose | excess surged | placebo excess D (interval) | placebo excess rose |')
        w('|---:|---|---:|---|---|---|---:|')
        for k in range(-3, 13):
            v = cb['all'][str(k)]
            pv = cb['placebo']['all'].get(str(k), {})
            if 'D' not in v:
                continue
            pD = pv.get('D')
            w(f'| {k:+d} | {ci(v["D"]["excess"], v["D"]["lo"], v["D"]["hi"])} | {math.exp(v["D"]["excess"]):.2f} | '
              f'{pc(v["rose"]["excess"])} ({pc(v["rose"]["lo"])} to {pc(v["rose"]["hi"])}) | {pc(v["surg"]["excess"])} ({pc(v["surg"]["lo"])} to {pc(v["surg"]["hi"])}) | '
              f'{ci(pD["excess"], pD["lo"], pD["hi"]) if pD else "-"} | {pc(pv["rose"]["excess"]) if pv.get("rose") else "-"} |')
        w('')
        fams = cb['by_family']
        fname = {'fiction': 'fiction', 'nonfiction': 'nonfiction', 'children_ya': 'children and young adult', 'graphic': 'graphic'}
        w('Excess D by the family of the first list (months 0, 2, 6, 12): ' + '; '.join(
            f'{fname[f]} ' + ', '.join(f'{fams[f][str(k)]["D"]["excess"]:.2f}' for k in (0, 2, 6, 12) if 'D' in fams[f][str(k)]) for f in fams) + '.\n')
    nb_ = C_['new_books']
    w('### 5.3 New books\n')
    w(f'For the {nb_["n"]:,} matched books that reached Seattle less than 6 months before their first NYT week, the first Seattle loan came in the month before the first '
      f'list week for {pc(nb_["share_first_loan_before"])}, in the same month for {pc(nb_["share_same_month"])} and later for {pc(nb_["share_after"])} (a list week '
      f'reflects sales of about two weeks earlier, so a book released late in a month is often listed early in the next). Their peak month of loans in the first 24 '
      f'months came a median {nb_["peak_rel_quartiles"][1]:.0f} months after the first list week (quartiles {nb_["peak_rel_quartiles"][0]:.0f} and '
      f'{nb_["peak_rel_quartiles"][2]:.0f}); {pc(nb_["share_peak_m0_to_m2"])} peaked in months 0 to 2 and {pc(nb_["share_peak_before"])} before the first list week. '
      f'Library borrowing of a new bestseller starts with its release and the list, and peaks later, as holds queues are worked through.\n')
    w('Reading. For established books the first list week comes with a large and lasting rise in Seattle loans: about '
      f'{math.exp(ex(c_own, 0)["excess"]):.1f} to {math.exp(ex(c_own, 2)["excess"]):.1f} times similar books in months 0 to 2, and '
      f'{math.exp(ex(c_own, 12)["excess"]):.1f} times a year later. With D2\'s earlier baseline, loans were already higher in months -3 to -1 '
      f'({ex(c_d2, -3)["excess"]:.2f}, {ex(c_d2, -2)["excess"]:.2f} and {ex(c_d2, -1)["excess"]:.2f}): borrowing starts rising before the first list week, partly '
      f'because the list reports sales two weeks late and partly because the books that become bestsellers were gaining readers already. The placebo is not zero '
      f'(about {cb["placebo"]["all"]["0"]["D"]["excess"]:.2f} at month 0 and {cb["placebo"]["all"]["12"]["D"]["excess"]:.2f} at month 12 with D2\'s baseline): '
      f'books that later become bestsellers drift up against controls matched on level only, so part of the later months\' excess is this drift, but the rise at the '
      f'list week is many times the placebo.\n')
    # ---------------------------------------------------------------- 6 limits
    w('## 6. Limits\n')
    w('- The NYT lists are a ranking of sales, not sales counts; a book off the list may still sell well. Presence is coarse (a month with one week counts as listed).')
    w('- Only the primary ISBN of each entry was saved; Seattle has no print ISBNs; most matches use title and author (hand check 50 of 50 right on the last sheet, '
      'recall checked only for similar titles).')
    w('- The main population of (a) is chosen with hindsight (books listed at some time); the all-works version is the check and gives the same order of models.')
    w('- Test A rows exist only for books already lent in Seattle, so new releases listed in their first month are mostly outside (a); they are described in 5.3.')
    w('- Weeks of monthly topic lists repeat inside a month; only presence (not weeks) is used in the tests.')
    w('- A list published early in month t+1 reports sales of the last days of month t, so part of the target of (a) is close to a same-month signal; '
      'no input of (a) uses anything after month t.')
    w('- The event controls are matched on loan level, not trend (the placebo shows the drift). Wikidata and Seattle mapping errors of Test A (some works carry an '
      'author page as their article) are inherited.\n')
    w('## 7. Settings and changes\n')
    w('All open settings are in the header of d3_nyt.py with their times; the change to the record (primary ISBN only, Wikidata ISBNs added), the tightening of the '
      'matching rules after the hand checks (before any test result) and the descriptive additions after the first results (age split and placebo in (a), '
      'D2 baseline and placebo in (c)) are logged in prereg/DEVIATIONS.md under addendum i. Nothing was tuned; no direction or model was chosen from these results.\n')
    w('Files in data/db/wiki_led/dirs/d3_nyt/: nyt_entries.parquet (all entries), nyt_key_matches.parquet and nyt_entries_matched.parquet (matching), '
      'nyt_monthly.parquet (work by month: weeks, best rank, lists, families), works_match_info.parquet, hand_check_50*.csv, recall_probe.csv, a_rows.parquet, '
      'a_refit_preds.parquet, a_results.json, b_results.json, c_events_own.parquet, c_events_d2.parquet, c_results.json, a_run.log.')
    (REP / 'dir_d3_nyt.md').write_text('\n'.join(L) + '\n')
    log('report written', REP / 'dir_d3_nyt.md')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='prep')
    st = ap.parse_args().stage
    if st in ('prep', 'all'):
        stage_prep()
    if st in ('a', 'all'):
        stage_a()
    if st in ('a_score', 'a', 'all'):
        r = score_a()
        (OUT / 'a_results.json').write_text(json.dumps(r, indent=1, default=float))
    if st in ('b', 'all'):
        stage_b()
    if st in ('c', 'all'):
        stage_c()
    if st in ('report', 'all'):
        stage_report()
