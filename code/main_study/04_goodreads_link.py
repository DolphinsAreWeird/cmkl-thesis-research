# 04. Goodreads (UCSD Book Graph, modern books with >= 1,000 ratings, collected 2017): one row per Goodreads
# work (editions merged; shelf counts = maximum over editions, as in context/05), then a link to SPL works.
# Link tiers: A = same main title and same normalized creator; B = same main title and same creator surname;
# C = same main title, Goodreads author name unknown (the local author file covers only some authors), and the
# title is distinctive (>= 3 words or >= 15 letters) and unique on both sides. Tier C precision is estimated by
# applying the same rule to works whose author IS known and checking the surname.
# Output: goodreads_works.parquet, spl_goodreads_link.parquet, profile/goodreads_link_summary.json
import json, collections, numpy as np, pandas as pd
from _common import OUT, RAW, D, title_parts, norm_creator, creator_match_key, save_json

names = json.load(open(f'{D}/raw/goodreads_authors_matched.json'))
gen = json.load(open(f'{RAW}/goodreads_genres.json'))
eds = []
for l in open(f'{RAW}/goodreads_books_meta.jsonl'):
    b = json.loads(l)
    eds.append(b)
E = pd.DataFrame(eds)
E['work_id'] = E.work_id.fillna(E.book_id).astype(str)
works = []
for wid, g in E.groupby('work_id'):
    g = g.sort_values(['ratings', 'book_id'], ascending=[False, True], kind='mergesort')
    top = g.iloc[0]
    sh = collections.Counter()
    for shelves in g.shelves:
        for s, c in shelves:
            sh[s] = max(sh[s], int(c))
    gg = collections.Counter()
    for bid in g.book_id:
        for k, v in gen.get(bid, {}).items():
            gg[k] = max(gg[k], int(v))
    a1 = top.authors[0] if top.authors else None
    years = [int(y) for y in g.year if str(y).isdigit()]
    desc = max(g.description, key=lambda x: len(x or ''))
    works.append(dict(gr_work_id=wid, gr_book_id=top.book_id, gr_title=top.title, author_id=a1, author_name=names.get(a1),
                      year_min=min(years) if years else None, ratings=int(g.ratings.max()), n_editions=len(g),
                      shelves=sorted(sh.items(), key=lambda x: -x[1]), gr_genres=dict(gg), description=desc))
G = pd.DataFrame(works)
tp = [title_parts(t) for t in G.gr_title]
G['title_main'] = [x[0] for x in tp]; G['title_sub'] = [x[1] for x in tp]
G['creator_key'] = G.author_name.map(lambda x: norm_creator(x) if isinstance(x, str) and x.strip() else '')
G['creator_key'] = G.creator_key.map(creator_match_key)
G['surname'] = G.creator_key.str.split().str[-1].fillna('')
G['shelf_counts'] = G.shelves.map(lambda x: [int(c) for s, c in x])
G['shelves'] = G.shelves.map(lambda x: [s for s, c in x])
G['gr_genres'] = G.gr_genres.map(json.dumps)
G.to_parquet(f'{OUT}/goodreads_works.parquet', index=False)
print('goodreads works', len(G), 'with author name', G.author_name.notna().sum(), flush=True)

W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'work_key', 'title', 'creator', 'title_main', 'creator_key', 'checkouts_total',
                                                          'first_ym', 'pub_year_min'])
W['spl_sub'] = [title_parts(t)[1] for t in W.title]
W['creator_key'] = W.creator_key.map(creator_match_key)
W['surname'] = W.creator_key.str.split().str[-1].fillna('')
links = []
# Tier A and B
ga = G[G.creator_key != ''].copy()
A = W.merge(ga[['gr_work_id', 'title_main', 'creator_key', 'ratings']], on=['title_main', 'creator_key'])
A['tier'] = 'A'
B = W.merge(ga[['gr_work_id', 'title_main', 'surname', 'ratings']], on=['title_main', 'surname'])
B = B[~B.work_id.isin(A.work_id)]; B['tier'] = 'B'
AB = pd.concat([A, B]).sort_values(['ratings', 'gr_work_id'], ascending=[False, True], kind='mergesort').drop_duplicates('work_id')   # one Goodreads work per SPL work


def distinctive(t):
    return len(t.split()) >= 3 or len(t.replace(' ', '')) >= 15


gr_title_n = G.groupby('title_main').gr_work_id.nunique()
spl_title_n = W.groupby('title_main').work_id.nunique()
uniq = set(gr_title_n[gr_title_n == 1].index) & set(spl_title_n[spl_title_n == 1].index)
uniq = {t for t in uniq if t and distinctive(t)}
gc = G[(G.creator_key == '') & G.title_main.isin(uniq)]
C = W[~W.work_id.isin(AB.work_id)].merge(gc[['gr_work_id', 'title_main', 'ratings', 'title_sub']], on='title_main')
C['tier'] = 'C'


def title_only_ok(df):
    """Extra checks for links made on the title alone (tiers C and D):
    - the Goodreads subtitle must be empty or share at least half of its words with the SPL subtitle
      (rejects 'Harry Potter and the Chamber of Secrets: Sheet Music for Flute', 'The Hunger Games: Official Movie Companion');
    - the SPL work must not be both published and first borrowed after 2017, because the Goodreads data ends in 2017
      (rejects the 2022 'Sea of Tranquility' linked to a 2012 book with the same title)."""
    def sub_ok(a, b):
        if not a:
            return True
        ta, tb = set(a.split()), set(b.split())
        return len(ta & tb) / max(1, len(ta)) >= 0.5
    ok_sub = [sub_ok(g, s) for g, s in zip(df.title_sub, df.spl_sub)]
    late = (df.first_ym > 201712) & (df.pub_year_min.fillna(9999) > 2017)
    return np.array(ok_sub) & ~late.values


C = C[title_only_ok(C)]
# precision check of the tier C rule on works whose Goodreads author is known
gk = G[(G.creator_key != '') & G.title_main.isin(uniq)]
chk = W.merge(gk[['gr_work_id', 'title_main', 'surname']], on='title_main', suffixes=('', '_gr'))
chk = chk[chk.surname != '']
prec = float((chk.surname == chk.surname_gr).mean()) if len(chk) else None
# Tier D: short titles (not distinctive) that are unique on both sides, only for widely read Goodreads works
uniq_short = (set(gr_title_n[gr_title_n == 1].index) & set(spl_title_n[spl_title_n == 1].index)) - uniq - {''}
POP = 20000
gd = G[(G.creator_key == '') & G.title_main.isin(uniq_short) & (G.ratings >= POP)]
Dd = W[~W.work_id.isin(AB.work_id) & ~W.work_id.isin(C.work_id)].merge(gd[['gr_work_id', 'title_main', 'ratings', 'title_sub']], on='title_main')
Dd['tier'] = 'D'
Dd = Dd[title_only_ok(Dd)]
gk2 = G[(G.creator_key != '') & G.title_main.isin(uniq_short) & (G.ratings >= POP)]
chk2 = W.merge(gk2[['gr_work_id', 'title_main', 'surname']], on='title_main', suffixes=('', '_gr'))
chk2 = chk2[chk2.surname != '']
prec2 = float((chk2.surname == chk2.surname_gr).mean()) if len(chk2) else None
L = pd.concat([AB, C, Dd])[['work_id', 'gr_work_id', 'tier']]
L.to_parquet(f'{OUT}/spl_goodreads_link.parquet', index=False)
Wl = W.merge(L, on='work_id', how='left')
summ = dict(goodreads_works=len(G), goodreads_works_with_author_name=int(G.author_name.notna().sum()),
            spl_works=len(W), linked=int(Wl.tier.notna().sum()), by_tier=Wl.tier.value_counts().to_dict(),
            share_works_linked=float(Wl.tier.notna().mean()),
            share_checkouts_linked=float(Wl[Wl.tier.notna()].checkouts_total.sum() / W.checkouts_total.sum()),
            tier_c_rule_check=dict(n_checked=int(len(chk)), surname_agrees=prec),
            tier_d_rule_check=dict(n_checked=int(len(chk2)), surname_agrees=prec2, min_ratings=POP),
            goodreads_works_used=int(L.gr_work_id.nunique()))
save_json(summ, f'{OUT}/profile/goodreads_link_summary.json')
print(summ)
s = Wl[Wl.tier == 'D'].sample(min(15, int((Wl.tier == 'D').sum())), random_state=0).merge(G[['gr_work_id', 'gr_title', 'year_min']], on='gr_work_id')
print(s[['title', 'creator', 'gr_title', 'year_min']].to_string())
