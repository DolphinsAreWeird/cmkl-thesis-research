# 99. Hand checks by the author (prereg/DEVIATIONS.md, "Checks asked for by an outside review of the draft (19 November 2026)", part B).
#   --draw   draws the two samples and writes what the labelling page shows (no answer of the rule, the AI sorter or the judge is in it):
#            1. links between works and articles, made by rule: 80 book-article and 60 author-article links of the main set (links that are
#               a feature in at least one scored row of l_books_in_time/preds.parquet) and 60 author links of new books whose author was
#               matched before the first loan (Test B, matched_pre = 1 in robustness_b_preds.parquet), plus 20 planted wrong links (8, 6,
#               6: a further drawn work paired with the article of another further drawn work of the same kind), in a shuffled order;
#            2. 100 of the 400 pages the judge labelled (75 of its random part, 25 of its hard cases), with the text the judge saw.
#            Short descriptions and first sentences of the linked articles come from the Wikipedia action API (20 titles a request,
#            one request a second, generic user agent).
#   --score  reads Khant's answers (answers_links.csv: item, answer in right/wrong/unsure; answers_pages.csv: id, codes as
#            "code,code" or "none") and writes data/reports/hand_check.md and .json:
#            1. share of the 200 real links marked wrong, exact 95% interval (Clopper-Pearson), overall and by kind; "unsure" and blank
#               counted apart and left out of the share; planted links marked wrong;
#            2. precision and recall of the AI sorter (all pairs; confidence 2 or 3) and of the judge against Khant's answers, narrow and
#               middle level, as in testF/26_G1_validation.py (a page the method sends nowhere lowers recall, never precision), 95%
#               intervals from 2,000 page draws; pages left blank are left out and counted.
# Seed 20261119 for every draw. Outputs: data/db/wiki_led/hand_check/ (items, key, answers) and data/reports/hand_check.{md,json}.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/99_hand_check.py --draw     (then, with the answers in place, --score)
import sys, json, time, pathlib, argparse, urllib.error, urllib.parse, urllib.request
import numpy as np, pandas as pd
from scipy.stats import beta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D                                         # noqa: E402

D = pathlib.Path(D)
WL = D / 'db' / 'wiki_led'
OUT = WL / 'hand_check'
REP = D / 'reports'
ROOT = D.parent
GUIDE = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-21_g_theme_guide.tsv'
SEED, NB = 20261119, 2000
UA = 'thesis-hand-check/1.0 (research script; low volume)'
N_REAL = {'book': 80, 'author_main': 60, 'author_new': 60}
N_PLANT = {'book': 8, 'author_main': 6, 'author_new': 6}
QUESTION = {'book': 'Is this article about this book?', 'author_main': "Is this article about the book's author?",
            'author_new': "Is this article about the book's author?"}


def summaries(titles):
    """Short description and first sentence of English Wikipedia articles, 20 titles a request (action API, redirects followed)."""
    out, titles = {}, list(titles)
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'formatversion': 2, 'redirects': 1, 'prop': 'description|extracts',
                                    'exintro': 1, 'explaintext': 1, 'exsentences': 1, 'exlimit': 20, 'titles': '|'.join(chunk)})
        for attempt in range(4):
            try:
                req = urllib.request.Request('https://en.wikipedia.org/w/api.php?' + q, headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    j = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                print('  retry', attempt, e.code, e.headers.get('retry-after'), e.read()[:200], len(q), flush=True); time.sleep(5 * 2 ** attempt)
            except Exception as e:
                print('  retry', attempt, type(e).__name__, flush=True); time.sleep(5 * 2 ** attempt)
        else:
            raise SystemExit('Wikipedia API not reached')
        norm = {x['from']: x['to'] for x in j['query'].get('normalized', [])}
        redir = {x['from']: x['to'] for x in j['query'].get('redirects', [])}
        pages = {pg['title']: pg for pg in j['query']['pages']}
        for t in chunk:
            final = redir.get(norm.get(t, t), norm.get(t, t))
            pg = pages.get(final, {})
            out[t] = dict(shown_title=final, description=pg.get('description', ''),
                          first_sentence=(pg.get('extract') or ('(no article found)' if pg.get('missing') else ''))[:400],
                          url='https://en.wikipedia.org/wiki/' + urllib.parse.quote(final.replace(' ', '_')))
        print('  summaries', min(i + 20, len(titles)), 'of', len(titles), flush=True)
        time.sleep(1)
    return out


def draw():
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    W = pd.read_parquet(D / 'db' / 'taxonomy_v3' / 'spl_works.parquet', columns=['work_id', 'title', 'creator'])
    M = pd.read_parquet(WL / 'l_books_in_time' / 'matches.parquet')
    P = pd.read_parquet(WL / 'l_books_in_time' / 'preds.parquet', columns=['work_id', 'has_book_page', 'has_author_page'])
    used_b = set(P.loc[P.has_book_page == 1, 'work_id']); used_a = set(P.loc[P.has_author_page == 1, 'work_id'])
    pools = {'book': M[M.work_id.isin(used_b) & M.book_article.notna()][['work_id', 'book_article']].rename(columns={'book_article': 'article'}),
             'author_main': M[M.work_id.isin(used_a) & M.author_article.notna()][['work_id', 'author_article']].rename(columns={'author_article': 'article'})}
    RB = pd.read_parquet(WL / 'robustness_b_preds.parquet', columns=['work_id', 'matched_pre'])
    TB = pd.read_parquet(WL / 'test_b_rows.parquet', columns=['work_id', 'enwiki_title'])
    nb = TB[TB.work_id.isin(set(RB.loc[RB.matched_pre == 1, 'work_id'])) & TB.enwiki_title.notna()]
    pools['author_new'] = nb.rename(columns={'enwiki_title': 'article'})[['work_id', 'article']]
    items = []
    for kind, pool in pools.items():
        pool = pool.drop_duplicates('work_id').sort_values('work_id').reset_index(drop=True)
        pick = rng.permutation(len(pool))[:N_REAL[kind] + 2 * N_PLANT[kind]]
        real = pool.iloc[pick[:N_REAL[kind]]]
        a_ = pool.iloc[pick[N_REAL[kind]:N_REAL[kind] + N_PLANT[kind]]].reset_index(drop=True)
        b_ = pool.iloc[pick[N_REAL[kind] + N_PLANT[kind]:]].reset_index(drop=True)
        for r in real.itertuples():
            items.append(dict(kind=kind, planted=False, work_id=int(r.work_id), article=r.article, true_article=r.article))
        for i in range(N_PLANT[kind]):
            items.append(dict(kind=kind, planted=True, work_id=int(a_.work_id[i]), article=b_.article[i], true_article=a_.article[i]))
        print(kind, 'pool', len(pool), 'real', len(real), 'planted', N_PLANT[kind], flush=True)
    K = pd.DataFrame(items).merge(W, on='work_id', how='left')
    assert K.title.notna().all(), 'a drawn work has no title'
    K = K.iloc[rng.permutation(len(K))].reset_index(drop=True)
    K['item'] = [f'L{i + 1:03d}' for i in range(len(K))]
    S = summaries(K.article.unique())
    K['shown_title'] = K.article.map(lambda t: S[t]['shown_title']); K['description'] = K.article.map(lambda t: S[t]['description'])
    K['first_sentence'] = K.article.map(lambda t: S[t]['first_sentence']); K['url'] = K.article.map(lambda t: S[t]['url'])
    K.to_csv(OUT / 'links_key.csv', index=False)                       # holds kind and planted: never shown on the page
    show = [dict(item=r.item, question=QUESTION[r.kind], work_title=r.title, creator=r.creator, article=r.shown_title,
                 description=r.description, first_sentence=r.first_sentence, url=r.url) for r in K.itertuples()]
    (OUT / 'links_items.json').write_text(json.dumps(show, ensure_ascii=False, indent=1))
    # pages
    J = pd.read_csv(WL / 'testF' / 'judge_set_info.csv')
    T = pd.read_csv(WL / 'testF' / 'judge_pages.tsv', sep='\t', dtype=str, keep_default_na=False)
    pick = []
    for part, n in (('random', 75), ('hard case', 25)):
        ids = J[J.part == part].sort_values('position').id.to_numpy()
        pick += list(ids[rng.permutation(len(ids))[:n]])
    pick = [pick[i] for i in rng.permutation(len(pick))]
    T = T.set_index('id').loc[pick].reset_index()
    pages = [dict(id=r.id, title=r.title, description=r.description, first_sentence=r.first_sentence) for r in T.itertuples()]
    (OUT / 'pages_items.json').write_text(json.dumps(pages, ensure_ascii=False, indent=1))
    G = pd.read_csv(GUIDE, sep='\t', dtype=str)
    (OUT / 'theme_guide.json').write_text(json.dumps(G.to_dict(orient='records'), ensure_ascii=False))
    print('links', len(K), '| pages', len(pages), '| articles summarized', len(S), flush=True)


def cp(k, n):
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def prf(mp, hp, pages, rng_idx):
    """Precision of method pairs mp against Khant's pairs hp and recall of hp by mp, with page-bootstrap intervals (as 26_G1_validation)."""
    pid = {p: i for i, p in enumerate(pages)}
    mp, hp = mp[mp.id.isin(pid)], hp[hp.id.isin(pid)]
    hs, ms = set(zip(hp.id, hp.node)), set(zip(mp.id, mp.node))
    n = len(pages)
    m_n = np.bincount(mp.id.map(pid).to_numpy(), minlength=n).astype(float)
    m_h = np.bincount(mp.id.map(pid).to_numpy(), weights=np.array([(i, c) in hs for i, c in zip(mp.id, mp.node)], float), minlength=n)
    h_n = np.bincount(hp.id.map(pid).to_numpy(), minlength=n).astype(float)
    h_h = np.bincount(hp.id.map(pid).to_numpy(), weights=np.array([(i, c) in ms for i, c in zip(hp.id, hp.node)], float), minlength=n)
    bp = [m_h[ix].sum() / m_n[ix].sum() for ix in rng_idx if m_n[ix].sum()]
    br = [h_h[ix].sum() / h_n[ix].sum() for ix in rng_idx if h_n[ix].sum()]
    return dict(pages=n, method_pairs=int(m_n.sum()), khant_pairs=int(h_n.sum()), precision=float(m_h.sum() / m_n.sum()),
                precision_lo=float(np.percentile(bp, 2.5)), precision_hi=float(np.percentile(bp, 97.5)), recall=float(h_h.sum() / h_n.sum()),
                recall_lo=float(np.percentile(br, 2.5)), recall_hi=float(np.percentile(br, 97.5)))


def score():
    rng = np.random.default_rng(SEED)
    res, L = {}, ['# Hand checks by the author', '', 'Record: prereg/DEVIATIONS.md, 19 November 2026, part B. Labelled by the author alone.', '']
    # links
    K = pd.read_csv(OUT / 'links_key.csv')
    A = pd.read_csv(OUT / 'answers_links.csv', dtype=str).fillna('')
    K = K.merge(A[['item', 'answer']], on='item', how='left').fillna({'answer': ''})
    real = K[~K.planted]
    rows = []
    for kind, g in [('all', real)] + list(real.groupby('kind')):
        dec = g[g.answer.isin(['right', 'wrong'])]
        k, n = int((dec.answer == 'wrong').sum()), len(dec)
        lo, hi = cp(k, n) if n else (np.nan, np.nan)
        rows.append(dict(kind=kind, links=len(g), wrong=k, right=n - k, unsure=int((g.answer == 'unsure').sum()),
                         blank=int((g.answer == '').sum()), share_wrong=k / n if n else np.nan, lo=lo, hi=hi))
    pl = K[K.planted]
    res['links'] = dict(by_kind=rows, planted=len(pl), planted_marked_wrong=int((pl.answer == 'wrong').sum()),
                        planted_unsure=int((pl.answer == 'unsure').sum()))
    L += ['## Links between works and articles (made by rule)', '', '| Links | Checked | Wrong | Not sure | Blank | Share wrong (95% interval) |',
          '| --- | --- | --- | --- | --- | --- |']
    L += [f"| {r['kind']} | {r['links']} | {r['wrong']} | {r['unsure']} | {r['blank']} | {r['share_wrong']:.3f} ({r['lo']:.3f} to {r['hi']:.3f}) |" for r in rows]
    L += ['', f"Planted wrong links marked wrong: {res['links']['planted_marked_wrong']} of {len(pl)} (not sure: {res['links']['planted_unsure']}).", '']
    # pages
    H = pd.read_csv(OUT / 'answers_pages.csv', dtype=str).fillna('')
    H = H[H.codes.str.strip() != '']
    guide = set(pd.read_csv(GUIDE, sep='\t', dtype=str).code)
    hp = pd.DataFrame([(i, c.strip()) for i, cs in zip(H.id, H.codes) if cs.strip() != 'none' for c in cs.split(',') if c.strip() in guide],
                      columns=['id', 'node']).drop_duplicates()
    info = pd.read_csv(WL / 'testF' / 'judge_set_info.csv')
    t2id = dict(zip(info.title, info.id))
    AS = pd.read_parquet(WL / 'testF' / 'assign_pages.parquet', columns=['title', 'code', 'conf'])
    AS = AS[AS.title.isin(t2id)].assign(id=lambda x: x.title.map(t2id))
    J = pd.read_parquet(WL / 'testF' / 'judge_answers.parquet', columns=['id', 'codes'])
    jp = pd.DataFrame([(i, c) for i, cs in zip(J.id, J.codes) for c in cs], columns=['id', 'node'])
    methods = {'AI sorter (all pairs)': AS[['id', 'code']].rename(columns={'code': 'node'}).drop_duplicates(),
               'AI sorter (confidence 2 or 3)': AS[AS.conf >= 2][['id', 'code']].rename(columns={'code': 'node'}).drop_duplicates(),
               'judge': jp}
    pages = sorted(H.id)
    idx = rng.integers(0, len(pages), size=(NB, len(pages)))
    mid = lambda x: x.assign(node=x.node.str.split('.').str[:2].str.join('.')).drop_duplicates()
    out = []
    for m, mp in methods.items():
        for level in ('narrow', 'middle'):
            a_, b_ = (mp, hp) if level == 'narrow' else (mid(mp), mid(hp))
            out.append(dict(method=m, level=level, **prf(a_, b_, pages, idx)))
    res['pages'] = dict(answered=len(pages), blank=100 - len(pages), none=int((H.codes.str.strip() == 'none').sum()), scores=out)
    L += ['## Sorting of pages into themes, blind', '', f"Pages answered {len(pages)} of 100; marked as fitting no theme {res['pages']['none']}.", '',
          '| Against the author | Level | Precision (95% interval) | Recall (95% interval) |', '| --- | --- | --- | --- |']
    L += [f"| {r['method']} | {r['level']} | {r['precision']:.3f} ({r['precision_lo']:.3f} to {r['precision_hi']:.3f}) | "
          f"{r['recall']:.3f} ({r['recall_lo']:.3f} to {r['recall_hi']:.3f}) |" for r in out]
    (REP / 'hand_check.json').write_text(json.dumps(res, indent=1, default=float))
    (REP / 'hand_check.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--draw', action='store_true'); ap.add_argument('--score', action='store_true')
    a = ap.parse_args()
    draw() if a.draw else score() if a.score else ap.error('--draw or --score')
