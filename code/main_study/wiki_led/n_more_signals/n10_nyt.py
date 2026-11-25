# n10. Addendum n, part 1, signal N (bestseller lists): New York Times list weeks matched to the main set's works, and the features
# N_* (at origin t) and Nl_* (the same at t-12) on the rows of addendum l.  DATA ONLY: no model is fitted, no loan is read or related
# to anything.  Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_1_signals_in_hand.N_bestseller_lists,
# common.time_rule and common.placebo_dates (read-only; SHA-256 checked below).
# Run from code/:  nice -n 10 ../.venv/bin/python main_study/wiki_led/n_more_signals/n10_nyt.py --stage reproduce|match|features|check|all
# Inputs (read only): data/db/wiki_led/dirs/d3_nyt/nyt_entries.parquet (D3's stored entries), nyt_key_matches.parquet and
#   nyt_entries_matched.parquet (D3's matches, for the checks); data/db/wiki_led/l_books_in_time/matches.parquet (main set) and
#   rows.parquet; data/db/taxonomy_v3/spl_works.parquet, spl_record_work.parquet, spl_records.parquet; data/db/study2r/works.parquet,
#   wd_isbn.parquet; data/db/study2r_fix/group_members.parquet.
# Outputs: data/db/wiki_led/n_more_signals/: feat_N.parquet, nyt_summary.json, nyt_key_matches_main.parquet,
#   nyt_entries_matched_main.parquet, nyt_monthly_main.parquet, nyt_overlap_d3_check.parquet, nyt_check_50.tsv.
#
# THE MATCHING RULES ARE D3's (code/main_study/wiki_led/dirs/d3_nyt.py, header choices 1 to 7c, stage_prep sections 2 and 3).  The
# function match_keys() below is a copy of that code, unchanged except that the work table, the two ISBN tables and the book key are
# passed in.  Choices the record leaves open (written 25 Nov 2026 16:44 to 16:47 +07:00, 09:44 to 09:47 UTC, before any step of this
# script ran; also in data/db/wiki_led/n_more_signals/notes_nyt_ol.md):
#  N1. Entries: D3's stored nyt_entries.parquet (June 2008 to October 2026), not re-read from the collector files; non-series lists
#      only (D3 choice 4); the distinct (ISBN-13, title, author) keys are matched, as in D3.
#  N2. Code check ('reproduce' stage, run first): match_keys() on D3's own inputs (Test A's 7,747 works with their Test A articles and
#      author articles, Seattle ISBNs of the works and their study2r_fix group members, Wikidata ISBNs of the Test A items) must give
#      D3's nyt_key_matches.parquet exactly (every key: book, route, title tier, number of candidates, works); the script stops if not.
#  N3. Main-set work table: Seattle title, main title and creator from taxonomy_v3 spl_works (for the 7,747 Test A works these equal
#      Test A's); the Wikipedia article is the main set's book_article (l01) and the author article l01's author_article (route A or B).
#      D3 always had an article; here 39,233 of 43,298 works have none.  Such a work gets no article title key, the 'author-like
#      article' test (7b) is not applied to it, and in the collapse step it is its own book (key '#w<work_id>'), so a tie between two
#      article-less works, or between one and an article, is a tie between two books and is dropped as ambiguous (D3 choice 7).
#      Where the main set's article differs from Test A's (48 of the 1,943 Test A works in the main set: Test A followed the
#      sitelink's redirect, for example to a series page), the main set's article is used, so the main set is matched on one rule.
#  N4. Seattle ISBN route (D3 choice 6): ISBNs of the work's own Seattle records (all formats, D3's tokenizer and isbn13()).  D3 also
#      used the records of "another Seattle work grouped to the same book" (study2r_fix group members).  That grouping exists only for
#      Test A's books; the main set has no regrouping of its own (addendum l counts each work's own records), and its equivalent, other
#      main-set works with the same book article, is already covered by D3's collapse step (an ISBN hit on one work of a book gives the
#      entry to every work of that book whose title agrees).  So the group members' records are used for the main-set works that are
#      Test A works (D3's rule where its grouping exists; count in the summary) and no new grouping is built for the others.  The
#      number of works and entries that match only through a group member's ISBN is counted in nyt_summary.json.
#  N5. Wikidata ISBN route (D3 choice 6): the edition ISBNs (study2r/wd_isbn.parquet) of the work's l01 book_item; title check as D3.
#  N6. Self-check on the main set (asked for): for the main-set works that are Test A works, the matched entries (week, list, title,
#      author, ISBN) are compared with D3's nyt_entries_matched.parquet, work by work; every difference is kept in
#      nyt_overlap_d3_check.parquet with its cause (new main-set candidate tie, other article, group-member ISBN, other) and counted.
#  N7. Independent check sheet: 50 matched main-set works drawn with numpy RandomState(20261125).choice over the sorted work_ids of
#      matched works, without replacement; one row per work with the Seattle title and creator and every distinct (list title, list
#      author, route) of its matched entries, plus context (book article, first and last list week, lists, publisher, a short
#      description); verdict columns left empty for the checker.  Not judged here.
#  N8. Weeks in a month (D3 choice 9): distinct list weeks (published dates) in the calendar month on any non-series list; a book on
#      two lists in one week counts one week.
#  N9. Features at origin t (time rule: weeks published on or before the last day of month t):
#      N_on = 1 if weeks(t) >= 1;  N_enter = 1 if weeks(t) >= 1 and weeks(t-1) = 0;  N_weeks = weeks(t);
#      N_weeks3 = weeks(t-2) + weeks(t-1) + weeks(t);  N_ever = log(1 + weeks in months before t), "before t" read as months before
#      month t (from 2008-06, the first collected week), so month t is not in it;  N_matched = 1 if the work has at least one matched
#      list week published on or before the last day of month t.  The record's "matched-book flag" is dated this way because a flag
#      for "ever matched in 2008 to 2026" would use lists published after t (the time rule); it equals N_ever > 0 or N_on = 1.
#      Unmatched works: 0 everywhere (record).
#  N10. Nl_* (common.placebo_dates): the same six values of the same work at origin t-12 (Nl_on, Nl_enter, Nl_weeks, Nl_weeks3,
#      Nl_ever, Nl_matched).  Every origin of the rows (2016-03 on) has t-12 inside the collected weeks.
#  N11. Rows: rows.parquet with mi <= 2026-07 (2026*12+6), in its order; float32; the same values for every format of a work.
#  Added after the first match run (16:48 +07:00), record-only, no match changed (the code check N2 still passes): match_keys() also
#      returns the works of the tied books of an ambiguous key (tied_works), and the overlap causes name a differing author article.
import sys, json, time, pathlib, hashlib, re, argparse
import numpy as np, pandas as pd

CODE = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(CODE)); sys.path.insert(0, str(CODE / 'study2r'))
from config import D  # noqa: E402
from common import norm, strip_art, title_keys, parse_creators, isbn13  # noqa: E402

D = pathlib.Path(D)
ROOT = D.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
D3OUT = D / 'db' / 'wiki_led' / 'dirs' / 'd3_nyt'
LB = D / 'db' / 'wiki_led' / 'l_books_in_time'
TAXO = D / 'db' / 'taxonomy_v3'
OUT = D / 'db' / 'wiki_led' / 'n_more_signals'
OUT.mkdir(parents=True, exist_ok=True)
SEED_CHECK = 20261125
MI_MAX = 2026 * 12 + 6
SCORE0 = 2019 * 12
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:7.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


NYT0, NYT1 = mi_of('2008-06'), mi_of('2026-10')


# ============================================================================================ inputs
def entries():
    E = pd.read_parquet(D3OUT / 'nyt_entries.parquet')
    return E


def seattle_isbn_map(MAP):
    """MAP: columns src (a Seattle work whose records are read) and group (the work the ISBN counts for); D3 stage_prep section 2"""
    RW = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    RW = RW[RW.work_id.isin(MAP.src)]
    R = pd.read_parquet(TAXO / 'spl_records.parquet', columns=['record_id', 'format', 'isbn'])
    R = R.merge(RW, on='record_id').merge(MAP, left_on='work_id', right_on='src')
    tok = R.assign(t=R.isbn.fillna('').map(lambda s: [x for x in re.split(r'[,; ]+', s) if x])).explode('t').dropna(subset=['t'])
    tok['i13'] = tok.t.map(isbn13)
    tok = tok[tok.i13.notna()]
    return tok.groupby('i13').group.apply(set).to_dict(), tok


def wd_isbn_map(W):
    X = pd.read_parquet(D / 'db' / 'study2r' / 'wd_isbn.parquet', columns=['item', 'isbn13'])
    X = X.merge(W[['work_id', 'item']].dropna(subset=['item']), on='item')
    return X.groupby('isbn13').work_id.apply(set).to_dict()


def test_a_inputs():
    """D3's own inputs (stage_prep section 2)"""
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet')
    SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title_main'])
    G = pd.read_parquet(D / 'db' / 'study2r_fix' / 'group_members.parquet', columns=['work_id', 'group_id'])
    MAP = pd.concat([pd.DataFrame({'src': W.work_id, 'group': W.work_id}),
                     G[G.group_id.isin(W.work_id)].rename(columns={'work_id': 'src', 'group_id': 'group'})]).drop_duplicates()
    s_isbn, _ = seattle_isbn_map(MAP)
    w_isbn = wd_isbn_map(W)
    W = W.merge(SW, on='work_id', how='left')
    W['book'] = W.article
    return W[['work_id', 'title', 'title_main', 'creator', 'article', 'author_article', 'book', 'item']], s_isbn, w_isbn


def main_inputs():
    """main-set work table and ISBN tables (choices N3 to N5)"""
    M = pd.read_parquet(LB / 'matches.parquet', columns=['work_id', 'book_item', 'book_article', 'author_article'])
    SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main', 'pub_year_min', 'first_ym'])
    W = M.merge(SW, on='work_id', how='left').rename(columns={'book_article': 'article', 'book_item': 'item'})
    assert len(W) == 43298 and W.title.notna().all()
    W['book'] = np.where(W.article.notna(), W.article, '#w' + W.work_id.astype(str))
    TA = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id'])
    G = pd.read_parquet(D / 'db' / 'study2r_fix' / 'group_members.parquet', columns=['work_id', 'group_id'])
    in_main_ta = set(W.work_id) & set(TA.work_id)
    MAP = pd.concat([pd.DataFrame({'src': W.work_id, 'group': W.work_id}),
                     G[G.group_id.isin(in_main_ta)].rename(columns={'work_id': 'src', 'group_id': 'group'})]).drop_duplicates()
    s_isbn, tok = seattle_isbn_map(MAP)
    s_isbn_own, _ = seattle_isbn_map(pd.DataFrame({'src': W.work_id, 'group': W.work_id}))
    w_isbn = wd_isbn_map(W)
    info = dict(works=len(W), works_with_article=int(W.article.notna().sum()), works_with_item=int(W.item.notna().sum()),
                test_a_works_in_main=len(in_main_ta), group_member_works_used=int((MAP.src != MAP.group).sum()),
                seattle_isbns=len(s_isbn), works_with_seattle_isbn=int(tok.group.nunique()),
                seattle_isbn_works_by_format=tok.groupby('format', observed=True).group.nunique().to_dict(),
                wikidata_isbns=len(w_isbn), works_with_wikidata_isbn=len(set().union(*w_isbn.values())) if w_isbn else 0)
    return W, s_isbn, w_isbn, s_isbn_own, info


# ============================================================================================ D3's matching (copied, parametrised)
def match_keys(E, W, seattle_isbn, wd_isbn):
    """D3 stage_prep section 2 (title keys, family names, markers) and section 3 (match each distinct NYT key), unchanged; W needs
    work_id, title, title_main, creator, article (may be missing, choice N3), author_article, book (the collapse key)"""
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
        if isinstance(r.article, str) and r.article:
            a_n, t_n = norm(art_clean(r.article)), norm(r.title)
            author_like = (a_n == norm(art_clean(r.author_article if isinstance(r.author_article, str) else ''))) or \
                (bool(fams[r.work_id] & set(a_n.split())) and a_n not in t_n and strip_art(a_n) not in t_n)
            n_author_like += author_like
            arts = () if author_like else (art_clean(r.article),)
        else:                                                   # choice N3: no article, no article key
            arts = ()
        fk = set()
        for t in (r.title,) + arts:
            n = norm(re.sub(r'\s*\([^)]*\)\s*', ' ', t or ''))
            if n:
                fk |= {n, strip_art(n)}
        full_keys[r.work_id] = fk
        all_keys[r.work_id] = title_keys(r.title, r.title_main if isinstance(r.title_main, str) else None, *arts) | fk
        mark[r.work_id] = markers(r.title)
    idx_all = {}
    for w, ks in all_keys.items():
        for k in ks:
            idx_all.setdefault(k, set()).add(w)

    art_of = dict(zip(W.work_id, W.book))
    works_of = W.groupby('book').work_id.apply(lambda s: sorted(s)).to_dict()

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
        tied = []

        n_mark = markers(r.title)

        def t_agree(w):   # 1 exact full title, 2 full title equals a main title, 3 one title contains the other (ISBN route only), 0 none
            if mark[w] != n_mark:                            # D3 choice 7b: another form of the book (graphic, young readers ...)
                return 0
            if n_full & full_keys[w]:
                return 1
            if (n_full & all_keys[w]) or (full_keys[w] & n_keys_safe):
                return 2
            if full_keys[w] & n_keys:                        # D3 choice 7c: only the part of the NYT title before a colon agrees
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
            tied[:] = top if len(top) > 1 else []               # added (record only): the tied books of an ambiguous key
            return (top[0], best, len(tiers)) if len(top) == 1 else (None, best, len(tiers))
        for rname, table in (('isbn_seattle', seattle_isbn), ('isbn_wikidata', wd_isbn)):
            if pick is not None or route.startswith('ambiguous') or not isinstance(r.isbn13, str):
                continue
            hits = sorted(table.get(r.isbn13, ()))
            hits_ok = [w for w in hits if t_agree(w) > 0]        # D3 choice 6 (tightened): title must agree
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
        tied_works = sorted(w for b in tied for w in works_of[b]) if route.startswith('ambiguous') else []
        out.append((r.isbn13, r.title, r.author, pick, route, tier if pick is not None else None, ncand, wlist, tied_works))
    M = pd.DataFrame(out, columns=['isbn13', 'title', 'author', 'article', 'route', 'title_tier', 'n_candidates', 'works', 'tied_works'])
    return M, n_rej, n_author_like


def entries_matched(E, M):
    X = M.explode('works').rename(columns={'works': 'work_id'})
    EM = E[~E.series].merge(X[['isbn13', 'title', 'author', 'work_id', 'route', 'title_tier']], on=['isbn13', 'title', 'author'], how='left')
    EM = EM[EM.work_id.notna()].copy()
    EM['work_id'] = EM.work_id.astype(int)
    return EM


def norm_keys(M):
    K = M.copy()
    K['isbn13'] = K.isbn13.astype(object).where(K.isbn13.notna(), None)
    K['works'] = K.works.map(lambda w: tuple(int(x) for x in w))
    K['title_tier'] = K.title_tier.astype(float)
    return K.sort_values(['isbn13', 'title', 'author'], na_position='first').reset_index(drop=True)


# ============================================================================================ stages
def stage_reproduce():
    E = entries()
    W, s_isbn, w_isbn = test_a_inputs()
    M, n_rej, n_al = match_keys(E, W, s_isbn, w_isbn)
    A = norm_keys(M)
    B = norm_keys(pd.read_parquet(D3OUT / 'nyt_key_matches.parquet'))
    assert len(A) == len(B), (len(A), len(B))
    same = {}
    for c in ['isbn13', 'title', 'author', 'article', 'route', 'n_candidates', 'works']:
        a, b = A[c].astype(object), B[c].astype(object)
        same[c] = bool(((a == b) | (a.isna() & b.isna())).all())
    same['title_tier'] = bool(np.allclose(A.title_tier.fillna(-1), B.title_tier.fillna(-1)))
    info = dict(keys=len(A), equal_by_column=same, all_equal=all(same.values()), isbn_rejected=n_rej, author_like_articles=n_al,
                routes=A.route.value_counts().to_dict(), checked=time.strftime('%Y-%m-%d %H:%M %z'))
    (OUT / 'nyt_reproduce_d3.json').write_text(json.dumps(info, indent=1))
    log('reproduce D3 on its own inputs:', info)
    assert info['all_equal'], 'match_keys() does not reproduce D3 on its own inputs'


def stage_match():
    E = entries()
    W, s_isbn, w_isbn, s_isbn_own, info = main_inputs()
    log('main-set inputs', info)
    M, n_rej, n_al = match_keys(E, W, s_isbn, w_isbn)
    log('NYT keys', len(M), 'routes', M.route.value_counts().to_dict(), 'ISBN hits rejected', n_rej, 'author-like articles', n_al)
    M.to_parquet(OUT / 'nyt_key_matches_main.parquet', index=False)
    EM = entries_matched(E, M)
    EM.to_parquet(OUT / 'nyt_entries_matched_main.parquet', index=False)
    g = EM.groupby(['work_id', 'mi'])
    T = pd.DataFrame({'weeks': g.week.nunique(), 'n_lists': g.list.nunique(), 'n_entries': g.size()}).reset_index()
    T.to_parquet(OUT / 'nyt_monthly_main.parquet', index=False)
    # the same without the group members' ISBNs (choice N4: how much depends on them)
    M2, _, _ = match_keys(E, W, s_isbn_own, w_isbn)
    EM2 = entries_matched(E, M2)
    k = ['work_id', 'week', 'list', 'title', 'author']
    only_grp = EM.merge(EM2[k].drop_duplicates(), on=k, how='left', indicator=True)
    only_grp = only_grp[only_grp._merge == 'left_only']
    lost = set(EM.work_id) - set(EM2.work_id)
    info.update(nyt_keys=len(M), key_routes=M.route.value_counts().to_dict(), isbn_rejected=n_rej, author_like_articles=n_al,
                entries_matched=len(EM), works_matched=int(EM.work_id.nunique()),
                group_member_isbn=dict(entries_only_with_them=len(only_grp), works_with_such_entries=int(only_grp.work_id.nunique()),
                                       works_matched_only_with_them=len(lost),
                                       entries_without_them_not_in_main=int(len(EM2.merge(EM[k].drop_duplicates(), on=k, how='left', indicator=True).query('_merge == "left_only"')))))
    # works by route: a work counts under every route that gave it an entry; main route = most frequent route of its entries (D3)
    wr = EM.groupby('work_id').route.agg(lambda s: s.value_counts().index[0])
    info['works_by_main_route'] = wr.value_counts().to_dict()
    info['works_by_any_route'] = {r: int(EM[EM.route == r].work_id.nunique()) for r in sorted(EM.route.unique())}
    info['works_with_article_matched'] = int(EM[EM.work_id.isin(W.loc[W.article.notna(), 'work_id'])].work_id.nunique())
    info['works_without_article_matched'] = int(EM[EM.work_id.isin(W.loc[W.article.isna(), 'work_id'])].work_id.nunique())
    amb = M[M.route.str.startswith('ambiguous')]
    info['ambiguous_keys'] = len(amb)
    tw = set(w for ws in amb.tied_works for w in ws)
    amb_e = E[~E.series].merge(amb[['isbn13', 'title', 'author']], on=['isbn13', 'title', 'author'])
    info['ambiguous_detail'] = dict(list_weeks_of_ambiguous_keys=int(amb_e.groupby(['title', 'author']).week.nunique().sum()),
                                    works_in_tied_books=len(tw), of_them_otherwise_unmatched=len(tw - set(EM.work_id)),
                                    tied_books_all_without_article=int(sum(all(str(b).startswith('#w') for b in
                                                                               {W.set_index('work_id').book.get(w) for w in ws}) for ws in amb.tied_works)))
    (OUT / 'nyt_match_info.json').write_text(json.dumps(info, indent=1, default=str))
    log('match written', {k_: v for k_, v in info.items() if k_ not in ('seattle_isbn_works_by_format',)})
    overlap_check(E, W, M, EM)


def overlap_check(E, W, M, EM):
    """choice N6: main-set works that are Test A works, their matched entries against D3's"""
    TA = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'article', 'author_article'])
    ov = sorted(set(W.work_id) & set(TA.work_id))
    D3E = pd.read_parquet(D3OUT / 'nyt_entries_matched.parquet')
    k = ['work_id', 'week', 'list', 'title', 'author']
    a = D3E[D3E.work_id.isin(ov)][k + ['route']].drop_duplicates(k)
    b = EM[EM.work_id.isin(ov)][k + ['route']].drop_duplicates(k)
    X = a.merge(b, on=k, how='outer', suffixes=('_d3', '_main'), indicator=True)
    X['side'] = X._merge.map({'left_only': 'only_d3', 'right_only': 'only_main', 'both': 'both'}).astype(str)
    X = X.drop(columns='_merge')
    # causes for the differences, key by key
    MK = M.set_index(['title', 'author']).sort_index()
    DK = pd.read_parquet(D3OUT / 'nyt_key_matches.parquet').set_index(['title', 'author']).sort_index()
    art_ta = dict(zip(TA.work_id, TA.article))
    art_main = dict(zip(W.work_id, W.article))
    au_ta = dict(zip(TA.work_id, TA.author_article))
    au_main = dict(zip(W.work_id, W.author_article))

    def why(w):
        x = []
        if art_ta.get(w) != art_main.get(w):
            x.append('article differs from Test A')
        a, b = au_ta.get(w), au_main.get(w)
        if not (a == b or (not isinstance(a, str) and not isinstance(b, str))):
            x.append('author article differs from Test A')
        return f' ({"; ".join(x)})' if x else ''

    def cause(r):
        if r.side == 'both':
            return ''
        mk = MK.loc[[(r.title, r.author)]] if (r.title, r.author) in MK.index else None
        dk = DK.loc[[(r.title, r.author)]] if (r.title, r.author) in DK.index else None
        routes_main = set(mk.route) if mk is not None else set()
        tag = why(r.work_id)
        if r.side == 'only_d3':
            if any(x.startswith('ambiguous') for x in routes_main):
                return 'main: ambiguous tie with another main-set book'
            if mk is not None and any(len(w) and r.work_id not in set(w) for w in mk.works):
                return 'main: key given to another main-set book' + tag
            return 'main: not matched' + tag
        else:
            if dk is not None and any(x.startswith('ambiguous') for x in dk.route):
                return 'd3: ambiguous tie among Test A books'
            if dk is not None and any(len(w) and r.work_id not in set(w) for w in dk.works):
                return 'd3: key given to another Test A book' + tag
            return 'd3: not matched' + tag
    X['cause'] = [cause(r) for r in X.itertuples()]
    X.to_parquet(OUT / 'nyt_overlap_d3_check.parquet', index=False)
    wa, wb = set(a.work_id), set(b.work_id)
    res = dict(test_a_works_in_main=len(ov), works_matched_d3=len(wa), works_matched_main=len(wb), works_both=len(wa & wb),
               works_only_d3=len(wa - wb), works_only_main=len(wb - wa),
               entries_d3=len(a), entries_main=len(b), entries_both=int((X.side == 'both').sum()),
               entries_only_d3=int((X.side == 'only_d3').sum()), entries_only_main=int((X.side == 'only_main').sum()),
               works_with_identical_entries=int(sum(1 for w in (wa | wb) if not (X[(X.work_id == w)].side != 'both').any())),
               differing_works=sorted(int(w) for w in set(X[X.side != 'both'].work_id)),
               causes_entries=X[X.side != 'both'].groupby(['side', 'cause']).size().rename('n').reset_index().to_dict('records'),
               causes_works=X[X.side != 'both'].drop_duplicates(['work_id', 'side', 'cause']).groupby(['side', 'cause']).size().rename('n').reset_index().to_dict('records'))
    (OUT / 'nyt_overlap_d3_check.json').write_text(json.dumps(res, indent=1, default=str))
    log('overlap with D3:', {k_: v for k_, v in res.items() if k_ != 'differing_works'})


def weeks_matrix(work_ids):
    T = pd.read_parquet(OUT / 'nyt_monthly_main.parquet')
    NM = np.arange(NYT0, NYT1 + 1)
    P = T.pivot_table(index='work_id', columns='mi', values='weeks', aggfunc='sum').reindex(index=work_ids, columns=NM).fillna(0)
    return NM, P.to_numpy(np.float64)


def n_feats(PW, cum, ri, t):
    """the six N features at origins t (array of month indices) for work rows ri (choice N9)"""
    j = t - NYT0
    assert (j >= 2).all() and (j < PW.shape[1]).all()
    w0, w1, w2 = PW[ri, j], PW[ri, j - 1], PW[ri, j - 2]
    before = cum[ri, j]                      # weeks in months before t (cum[:, j] = sum of columns < j)
    through = cum[ri, j + 1]                 # weeks in months up to and including t
    return {'on': (w0 > 0).astype(np.float32), 'enter': ((w0 > 0) & (w1 == 0)).astype(np.float32), 'weeks': w0.astype(np.float32),
            'weeks3': (w0 + w1 + w2).astype(np.float32), 'ever': np.log1p(before).astype(np.float32),
            'matched': (through > 0).astype(np.float32)}


def stage_features():
    R = pd.read_parquet(LB / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R = R[R.mi <= MI_MAX].reset_index(drop=True)
    assert len(R) == 1773531, len(R)
    works = np.sort(pd.read_parquet(LB / 'matches.parquet', columns=['work_id']).work_id.to_numpy())
    assert set(R.work_id.unique()) <= set(works)
    NM, PW = weeks_matrix(works)
    cum = np.concatenate([np.zeros((len(works), 1)), np.cumsum(PW, axis=1)], axis=1)
    ri = np.searchsorted(works, R.work_id.to_numpy())
    t = R.mi.to_numpy().astype(np.int64)
    F = R[['work_id', 'format', 'mi']].copy()
    for k, v in n_feats(PW, cum, ri, t).items():
        F['N_' + k] = v
    for k, v in n_feats(PW, cum, ri, t - 12).items():
        F['Nl_' + k] = v
    # checks: row order, one value per work and origin across formats, lag equals the value 12 months earlier where both exist
    R0 = pd.read_parquet(LB / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R0 = R0[R0.mi <= MI_MAX].reset_index(drop=True)
    assert (R0.work_id.to_numpy() == F.work_id.to_numpy()).all() and (R0.mi.to_numpy() == F.mi.to_numpy()).all() and \
        (R0.format.astype(str).to_numpy() == F.format.astype(str).to_numpy()).all(), 'row order differs from rows.parquet'
    cols = [c for c in F.columns if c.startswith('N')]
    assert F.groupby(['work_id', 'mi'])[cols].nunique().max().max() == 1, 'formats of a work differ'
    S = F.drop_duplicates(['work_id', 'mi']).set_index(['work_id', 'mi'])
    L = S[[c for c in cols if c.startswith('N_')]].copy()
    L.index = pd.MultiIndex.from_arrays([L.index.get_level_values(0), L.index.get_level_values(1) + 12])
    J = S[[c for c in cols if c.startswith('Nl_')]].join(L, how='inner')
    for k in ['on', 'enter', 'weeks', 'weeks3', 'ever', 'matched']:
        assert np.array_equal(J['Nl_' + k].to_numpy(), J['N_' + k].to_numpy()), k
    assert all(F[c].dtype == np.float32 for c in cols) and not F[cols].isna().any().any()
    F.to_parquet(OUT / 'feat_N.parquet', index=False)
    log('feat_N written', F.shape, 'lag check on', len(J), 'work-months')
    # summary
    info = json.loads((OUT / 'nyt_match_info.json').read_text())
    ovl = json.loads((OUT / 'nyt_overlap_d3_check.json').read_text())
    rep = json.loads((OUT / 'nyt_reproduce_d3.json').read_text())
    sc = F[F.mi >= SCORE0]
    everm = set(pd.read_parquet(OUT / 'nyt_monthly_main.parquet').work_id)
    T = pd.read_parquet(OUT / 'nyt_monthly_main.parquet')
    E = entries()
    wk_per_month = E[~E.series].groupby('mi').week.nunique()
    summ = dict(
        record=str(REC.relative_to(ROOT)), built=time.strftime('%Y-%m-%d %H:%M %z'),
        reproduce_d3_on_its_inputs=dict(all_equal=rep['all_equal'], keys=rep['keys']),
        works_main_set=info['works'], works_with_book_article=info['works_with_article'], works_with_book_item=info['works_with_item'],
        nyt_keys=info['nyt_keys'], key_routes=info['key_routes'], isbn_hits_rejected_title=info['isbn_rejected'],
        ambiguous_keys=info['ambiguous_keys'], ambiguous_detail=info['ambiguous_detail'],
        works_matched=info['works_matched'], works_matched_by_main_route=info['works_by_main_route'],
        works_matched_by_any_route=info['works_by_any_route'],
        works_matched_with_article=info['works_with_article_matched'], works_matched_without_article=info['works_without_article_matched'],
        entries_matched=info['entries_matched'], group_member_isbn=info['group_member_isbn'],
        overlap_with_d3={k_: v for k_, v in ovl.items() if k_ != 'differing_works'},
        rows=len(F), scored_rows=len(sc),
        scored_rows_of_ever_matched_works=float(sc.work_id.isin(everm).mean()),
        scored_rows_N_matched=float((sc.N_matched > 0).mean()), scored_rows_N_on=float((sc.N_on > 0).mean()),
        scored_rows_N_enter=float((sc.N_enter > 0).mean()), scored_rows_Nl_matched=float((sc.Nl_matched > 0).mean()),
        works_in_scored_rows_with_N_on=int(sc.loc[sc.N_on > 0, 'work_id'].nunique()),
        list_weeks_per_month_2015_2026=dict(min=int(wk_per_month[(wk_per_month.index >= mi_of('2015-01')) & (wk_per_month.index <= MI_MAX)].min()),
                                            max=int(wk_per_month[(wk_per_month.index >= mi_of('2015-01')) & (wk_per_month.index <= MI_MAX)].max())),
        months_with_no_list_week_2015_2026=[ym(m) for m in range(mi_of('2015-01'), MI_MAX + 1) if m not in wk_per_month.index],
        monthly_rows=len(T))
    (OUT / 'nyt_summary.json').write_text(json.dumps(summ, indent=1, default=str))
    log('summary', summ)


def stage_check():
    """choice N7: 50 random matched works for an independent checker (not judged here)"""
    EM = pd.read_parquet(OUT / 'nyt_entries_matched_main.parquet')
    W = pd.read_parquet(LB / 'matches.parquet', columns=['work_id', 'book_article'])
    SW = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'pub_year_min', 'first_ym', 'formats'])
    W = W.merge(SW, on='work_id', how='left').set_index('work_id')
    ids = np.sort(EM.work_id.unique())
    rs = np.random.RandomState(SEED_CHECK)
    pick = np.sort(rs.choice(ids, 50, replace=False))
    rows = []
    for i, w in enumerate(pick, 1):
        x = EM[EM.work_id == w]
        k = x.groupby(['title', 'author', 'route']).agg(first=('week', 'min'), last=('week', 'max'), weeks=('week', 'nunique'),
                                                        lists=('list', lambda s: '; '.join(sorted(set(s))[:3])),
                                                        publisher=('publisher', 'first'), description=('description', 'first')).reset_index()
        k = k.sort_values('first')
        r = W.loc[w]
        rows.append(dict(n=i, work_id=int(w), seattle_title=r.title, seattle_creator=r.creator,
                         seattle_pub_year_min=r.pub_year_min, seattle_first_loan_month=r.first_ym, seattle_formats=r.formats,
                         book_article=r.book_article if isinstance(r.book_article, str) else '',
                         list_title=' || '.join(k.title), list_author=' || '.join(k.author), route=' || '.join(k.route),
                         n_list_keys=len(k), first_week=str(k['first'].min().date()), last_week=str(k['last'].max().date()),
                         list_weeks=int(x.week.nunique()), lists=' || '.join(k.lists), publisher=' || '.join(k.publisher.fillna('')),
                         description=' || '.join(d[:200] for d in k.description.fillna('')),
                         correct='', note=''))
    S = pd.DataFrame(rows)
    for c in S.columns:
        if S[c].dtype == object or str(S[c].dtype).startswith('str'):
            S[c] = S[c].astype(str).str.replace('\t', ' ').str.replace('\n', ' ')
    f = OUT / 'nyt_check_50.tsv'
    S.to_csv(f, sep='\t', index=False)
    log('check sheet', f, 'routes of the sample', S.route.str.split(' \\|\\| ').explode().value_counts().to_dict())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['reproduce', 'match', 'features', 'check', 'all'])
    a = ap.parse_args()
    if a.stage in ('reproduce', 'all'):
        stage_reproduce()
    if a.stage in ('match', 'all'):
        stage_match()
    if a.stage in ('features', 'all'):
        stage_features()
    if a.stage in ('check', 'all'):
        stage_check()
    log('done')
