#!/usr/bin/env python3
"""Test B (new books), step 4: match each first-author display name to an English Wikipedia article about a human.

Settings: prereg/wiki_led_settings_2026-10-20.json, test_B_new_books.author_matching.  The rule, exactly:
  titles tried in order: the plain name, then 'Name (writer)', 'Name (author)', 'Name (novelist)'; the next title is tried only when
  the earlier one is missing, is a disambiguation page, or its Wikidata item is not a human (P31 = Q5).  Redirects are followed.
  The first title whose Wikidata item is a human is accepted.  writer_type = P106 (occupation) intersects the writer set below.
Nothing is checked by hand.  Data only: no model, no outcome.

Run from handoff/code (a long download, so detached):
    bash ../jobs/bg.sh wiki_led_match main_study/wiki_led/02_author_match.py
Options: --test N  uses only the first N names (sorted) and writes *_test files.
Every HTTP response is cached under data/interim/wiki_led_cache/, so a rerun costs nothing.
Action API (Wikipedia) and Wikidata: sequential, at most 5 requests per second, maxlag=5, back-off on 429/503/maxlag.
"""
import sys, re, json, time
import pandas as pd
from _common import OUT, Http, log, maxlag_check, T0

WP_API = 'https://en.wikipedia.org/w/api.php'
WD_API = 'https://www.wikidata.org/w/api.php'
H = Http({'wp': 0.21, 'wd': 0.21})
WRITER = {'Q36180', 'Q6625963', 'Q49757', 'Q482980', 'Q1930187', 'Q28389', 'Q11774202', 'Q4853732', 'Q15980158', 'Q214917',
          'Q201788', 'Q864380', 'Q18814623', 'Q715301'}
SUFFIXES = [('plain', ''), ('writer', ' (writer)'), ('author', ' (author)'), ('novelist', ' (novelist)')]
BAD = re.compile(r'[#<>\[\]|{}\n\r\t]')
TEST = int(sys.argv[sys.argv.index('--test') + 1]) if '--test' in sys.argv else 0
SUF = '_test' if TEST else ''


def chunks(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def wp_resolve(titles):
    """titles -> {input title: dict(status, title, qid)} via prop=pageprops&redirects=1 in batches of 50."""
    res = {}
    todo = sorted(set(titles))
    nb = (len(todo) + 49) // 50
    for bi, batch in enumerate(chunks(todo)):
        st, text = H.get('wp', WP_API, dict(action='query', prop='pageprops', redirects=1, titles='|'.join(batch), format='json',
                                            formatversion=2, maxlag=5), check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Action API status {st}')
        q = json.loads(text).get('query', {})
        norm = {d['from']: d['to'] for d in q.get('normalized', [])}
        redir = {d['from']: d['to'] for d in q.get('redirects', [])}
        pages = {}
        for p in q.get('pages', []):
            pages[p['title']] = p
        for t in batch:
            cur = norm.get(t, t)
            for _ in range(10):
                if cur in redir:
                    cur = redir[cur]
                else:
                    break
            p = pages.get(cur)
            if p is None:
                res[t] = dict(status='invalid', title=None, qid=None)
            elif p.get('invalid'):
                res[t] = dict(status='invalid', title=None, qid=None)
            elif p.get('missing'):
                res[t] = dict(status='missing', title=None, qid=None)
            elif p.get('ns', 0) != 0:
                res[t] = dict(status='nonmain', title=p['title'], qid=None)
            else:
                pp = p.get('pageprops', {})
                if 'disambiguation' in pp:
                    res[t] = dict(status='disambiguation', title=p['title'], qid=pp.get('wikibase_item'))
                elif not pp.get('wikibase_item'):
                    res[t] = dict(status='no_item', title=p['title'], qid=None)
                else:
                    res[t] = dict(status='page', title=p['title'], qid=pp['wikibase_item'])
        if (bi + 1) % 100 == 0 or bi + 1 == nb:
            log(f'  Wikipedia batches {bi + 1}/{nb}; network {H.n_net}, cache {H.n_cache}, backoffs {H.n_backoff}')
    return res


def claim_ids(claims, prop):
    out = []
    for stmt in claims.get(prop, []):
        if stmt.get('rank') == 'deprecated':
            continue
        ms = stmt.get('mainsnak', {})
        if ms.get('snaktype') == 'value':
            v = ms.get('datavalue', {}).get('value')
            if isinstance(v, dict) and v.get('id'):
                out.append(v['id'])
    return out


ENT = {}      # qid -> dict(is_human, p31, occupations)


def wd_fetch(qids):
    todo = sorted(q for q in set(qids) if q and q not in ENT)
    nb = (len(todo) + 49) // 50
    for bi, batch in enumerate(chunks(todo)):
        st, text = H.get('wd', WD_API, dict(action='wbgetentities', ids='|'.join(batch), props='claims', format='json', maxlag=5),
                         check=maxlag_check)
        if st != 200:
            raise RuntimeError(f'Wikidata status {st}')
        ents = json.loads(text).get('entities', {})
        for q in batch:
            e = ents.get(q)
            if e is None or 'missing' in e:
                ENT[q] = dict(is_human=False, p31=[], occupations=[], missing=True)
                continue
            cl = e.get('claims', {})
            p31 = claim_ids(cl, 'P31')
            ENT[q] = dict(is_human='Q5' in p31, p31=p31, occupations=claim_ids(cl, 'P106'), missing=False)
        if (bi + 1) % 50 == 0 or bi + 1 == nb:
            log(f'  Wikidata batches {bi + 1}/{nb}; network {H.n_net}, cache {H.n_cache}, backoffs {H.n_backoff}')


def main():
    pop = pd.read_parquet(OUT / 'test_b_population.parquet', columns=['work_id', 'display_name', 'creator_key'])
    g = pop.groupby('display_name').agg(creator_keys=('creator_key', lambda s: sorted(set(s))), n_works=('work_id', 'size')).reset_index()
    g = g.sort_values('display_name').reset_index(drop=True)
    if TEST:
        g = g.iloc[:: max(1, len(g) // TEST)].head(TEST).reset_index(drop=True)
    names = g.display_name.tolist()
    log(f'distinct first-author display names: {len(names)}')
    state = {n: dict(accepted=None, tried=[], plain_status=None) for n in names}
    invalid = [n for n in names if BAD.search(n) or len(n.encode()) > 250]
    for n in invalid:
        state[n]['plain_status'] = 'invalid_title'
    log(f'names that cannot be a page title (never queried): {len(invalid)}')
    invalid_set = set(invalid)
    pending = [n for n in names if n not in invalid_set]
    stage_counts = {}
    for sname, suf in SUFFIXES:
        if not pending:
            break
        titles = {n: n + suf for n in pending}
        log(f'stage {sname}: {len(titles)} titles')
        res = wp_resolve(list(titles.values()))
        cand = {n: res[t] for n, t in titles.items()}
        wd_fetch([r['qid'] for r in cand.values() if r['status'] == 'page'])
        nxt = []
        acc = 0
        for n in pending:
            r = cand[n]
            state[n]['tried'].append(titles[n])
            if r['status'] == 'page':
                human = ENT[r['qid']]['is_human']
                status = 'human' if human else 'not_human'
            else:
                human = False
                status = r['status']
            if sname == 'plain':
                state[n]['plain_status'] = status
            if human:
                state[n]['accepted'] = dict(title_tried=titles[n], enwiki_title=r['title'], qid=r['qid'], method=sname)
                acc += 1
            else:
                nxt.append(n)
        stage_counts[sname] = dict(queried=len(pending), accepted=acc)
        log(f'stage {sname}: accepted {acc} of {len(pending)}')
        pending = nxt
    rows = []
    for _, r in g.iterrows():
        s = state[r.display_name]
        a = s['accepted']
        if a:
            occ = ENT[a['qid']]['occupations']
            rows.append(dict(display_name=r.display_name, creator_keys=r.creator_keys, n_works=int(r.n_works), title_tried=a['title_tried'],
                             enwiki_title=a['enwiki_title'], qid=a['qid'], is_human=True, occupations=sorted(set(occ)),
                             writer_type=bool(WRITER & set(occ)), method=a['method'], plain_status=s['plain_status']))
        else:
            rows.append(dict(display_name=r.display_name, creator_keys=r.creator_keys, n_works=int(r.n_works),
                             title_tried=(s['tried'][-1] if s['tried'] else None), enwiki_title=None, qid=None, is_human=False,
                             occupations=[], writer_type=False, method='none', plain_status=s['plain_status']))
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / f'author_match{SUF}.parquet', index=False)
    pd.DataFrame([dict(qid=q, **{k: v for k, v in d.items()}) for q, d in ENT.items()]).assign(
        p31=lambda x: x.p31.map(list), occupations=lambda x: x.occupations.map(list)).to_parquet(OUT / f'wikidata_items{SUF}.parquet', index=False)
    summ = dict(names=len(names), matched_human=int(df.is_human.sum()), writer_type=int(df.writer_type.sum()),
                by_method=df.method.value_counts().to_dict(), plain_status=df.plain_status.value_counts().to_dict(),
                stage_counts=stage_counts, wikidata_items=len(ENT), network_requests=H.n_net, cache_hits=H.n_cache, backoffs=H.n_backoff,
                runtime_s=round(time.time() - T0))
    (OUT / f'author_match_summary{SUF}.json').write_text(json.dumps(summ, indent=1))
    log(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
