# 05. Final concept articles per theme value, resolved through the official MediaWiki API, and their redirects.
# For every title in _wiki_choices.CHOICES: follow redirects to the canonical title, read the Wikidata item (pageprops
# wikibase_item), the short description and the disambiguation flag. Then list every redirect to each canonical page
# (prop=redirects, namespace 0), which 06 screens for traffic. The automatic Wikidata pick from 04 is kept next to the
# hand choice, so the review can show which picks were changed and why.
# Outputs: data/db/interest/wiki/articles.parquet, redirects.parquet, articles_review.csv
import json, os, pandas as pd
from _ci import WK, load_taxonomy, polite_get, save_json, save_parquet
import _wiki_choices as WC

API = 'https://en.wikipedia.org/w/api.php'
V, N = load_taxonomy()
missing_values = sorted(set(V.theme) - set(WC.CHOICES))
if missing_values:
    raise SystemExit(f'no article chosen for {len(missing_values)} values: {missing_values[:20]}')
rows = [dict(theme=t, role='main' if k == 0 else 'related', chosen=title) for t, titles in WC.CHOICES.items() if t in set(V.theme)
        for k, title in enumerate(titles)]
A = pd.DataFrame(rows)

fc = f'{WK}/_resolve_cache.json'
cache = json.load(open(fc)) if os.path.exists(fc) else {}
todo = sorted(set(A.chosen) - set(cache))
for i in range(0, len(todo), 50):
    b = todo[i:i + 50]
    r = polite_get(API, dict(action='query', titles='|'.join(b), redirects=1, prop='pageprops|description|info',
                             ppprop='wikibase_item|disambiguation', format='json', formatversion=2))
    q = r.json()['query']
    norm = {x['from']: x['to'] for x in q.get('normalized', [])}
    red = {x['from']: x['to'] for x in q.get('redirects', [])}
    pages = {p['title']: p for p in q['pages']}
    for t in b:
        t1 = norm.get(t, t); t2 = red.get(t1, t1)
        p = pages.get(t2, {})
        cache[t] = dict(canonical=None if p.get('missing') else t2, pageid=p.get('pageid'), redirected=t2 != t1,
                        qid=p.get('pageprops', {}).get('wikibase_item'), desc=p.get('description'),
                        disambiguation='disambiguation' in p.get('pageprops', {}), missing=bool(p.get('missing')))
    save_json(cache, fc)
for k in ['canonical', 'pageid', 'redirected', 'qid', 'desc', 'disambiguation', 'missing']:
    A[k] = A.chosen.map(lambda t: cache[t][k])

# automatic Wikidata pick (04) for comparison
C = pd.read_parquet(f'{WK}/candidates.parquet')
auto = C[C.auto_pick].drop_duplicates('theme').set_index('theme')
A['auto_pick'] = A.theme.map(auto.enwiki)
A['auto_qid'] = A.theme.map(auto.qid)
A['changed_from_auto'] = (A.role == 'main') & (A.canonical.fillna('') != A.auto_pick.fillna('')) & (A.qid.fillna('') != A.auto_qid.fillna(''))
A['note'] = A.theme.map(WC.NOTES)
A = A.merge(V[['theme', 'node_id', 'general', 'support']], on='theme', how='left')
save_parquet(A, f'{WK}/articles.parquet')

# redirects of every canonical page
fr = f'{WK}/_redirect_cache.json'
rcache = json.load(open(fr)) if os.path.exists(fr) else {}
targets = sorted(set(A.canonical.dropna()) - set(rcache))
for i in range(0, len(targets), 50):
    b = targets[i:i + 50]
    got = {t: [] for t in b}
    params = dict(action='query', titles='|'.join(b), prop='redirects', rdlimit='max', rdnamespace=0, rdprop='title|pageid',
                  format='json', formatversion=2)
    while True:
        r = polite_get(API, params).json()
        for p in r['query']['pages']:
            if p['title'] in got:
                got[p['title']].extend(x['title'] for x in p.get('redirects', []))
        if 'continue' not in r:
            break
        params.update(r['continue'])
    rcache.update(got); save_json(rcache, fr)
RD = pd.DataFrame([dict(canonical=t, redirect=x) for t in sorted(set(A.canonical.dropna())) for x in rcache.get(t, [])])
save_parquet(RD, f'{WK}/redirects.parquet')

label = dict(zip(N.node_id, N.label))
A['node_label'] = A.node_id.map(label)
# review sheet: every value was checked by hand; the control categories and the 100 values with most works are marked
CONTROL_NODES = {'B15.M04.N05', 'B05.M02.N02', 'B12.M01.N02', 'B09.M07.N02'}
rank = V.sort_values('support', ascending=False).reset_index(drop=True).reset_index().set_index('theme')['index'] + 1
A['importance_rank'] = A.theme.map(rank)
A['control_category'] = A.node_id.isin(CONTROL_NODES)
A['top100'] = A.importance_rank <= 100
A['verdict'] = ['related page added by hand' if r.role == 'related' else
                ('automatic pick replaced' if r.changed_from_auto else 'automatic pick kept') for r in A.itertuples()]
A['auto_pick_wrong_kind'] = A.changed_from_auto & A.auto_pick.notna()
A.sort_values(['importance_rank', 'role'], ascending=[True, True]).to_csv(f'{WK}/articles_review.csv', index=False)
m = A[A.role == 'main']
for nm, sub in [('all values', m), ('top 100 values', m[m.top100]), ('control-category values', m[m.control_category])]:
    print(f'{nm}: {len(sub)} | automatic pick kept {int((~sub.changed_from_auto).sum())} | replaced {int(sub.changed_from_auto.sum())} '
          f'(no automatic pick {int(sub.auto_pick.isna().sum())})')
print('values', A.theme.nunique(), 'titles', len(A), 'unique canonical', A.canonical.nunique())
print('missing', A[A.missing].chosen.tolist())
print('disambiguation', A[A.disambiguation].chosen.tolist())
print('main picks changed from the automatic Wikidata pick', int(A.changed_from_auto.sum()), 'of', int((A.role == 'main').sum()))
print('redirects', len(RD), 'per article median', RD.groupby('canonical').size().median(), 'max', RD.groupby('canonical').size().max())
shared = A.groupby('canonical').node_id.nunique()
print('articles shared by values in different nodes:', shared[shared > 1].to_dict())
