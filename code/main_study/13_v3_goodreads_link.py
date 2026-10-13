# 13. (v3) Goodreads to SPL links using the full UCSD author file (data/raw/modern/goodreads_extra/goodreads_book_authors.json.gz),
# so links can require the same author for almost every Goodreads work. Goodreads works come from the v2 table (read
# only). Tiers: A = same main title and same author (first + last name); B = same main title and same surname;
# C/D = title only, as in v2, now only for the few Goodreads works whose author is still unknown.
# Output: data/db/taxonomy_v3/goodreads_works.parquet, spl_goodreads_link.parquet, profile/goodreads_link_summary.json
import os
os.environ['TAXO'] = 'v3'
import gzip, json, numpy as np, pandas as pd
from _common import OUT, OUT_V2, RAW, title_parts, norm_creator, creator_match_key, save_json

os.makedirs(f'{OUT}/profile', exist_ok=True)
G = pd.read_parquet(f'{OUT_V2}/goodreads_works.parquet')
need = set(G.author_id.dropna())
names = {}
with gzip.open(f'{RAW}/goodreads_extra/goodreads_book_authors.json.gz', 'rt') as f:
    for line in f:
        a = json.loads(line)
        if a['author_id'] in need:
            names[a['author_id']] = a['name']
G['author_name'] = G.author_id.map(names)
G['creator_key'] = G.author_name.map(lambda x: creator_match_key(norm_creator(x)) if isinstance(x, str) and x.strip() else '')
G['surname'] = G.creator_key.str.split().str[-1].fillna('')
G.to_parquet(f'{OUT}/goodreads_works.parquet', index=False)
print('goodreads works', len(G), 'with author name', int(G.author_name.notna().sum()), flush=True)

W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'creator', 'title_main', 'creator_key', 'checkouts_total',
                                                          'first_ym', 'pub_year_min', 'formats'])
W['creator_key'] = W.creator_key.map(creator_match_key)
W['surname'] = W.creator_key.str.split().str[-1].fillna('')
W['spl_sub'] = [title_parts(t)[1] for t in W.title]
ga = G[G.creator_key != '']
A = W.merge(ga[['gr_work_id', 'title_main', 'creator_key', 'ratings']], on=['title_main', 'creator_key']); A['tier'] = 'A'
B = W.merge(ga[['gr_work_id', 'title_main', 'surname', 'ratings']], on=['title_main', 'surname'])
B = B[~B.work_id.isin(A.work_id) & (B.surname != '')]; B['tier'] = 'B'
AB = pd.concat([A, B]).sort_values(['ratings', 'gr_work_id'], ascending=[False, True], kind='mergesort').drop_duplicates('work_id')


def distinctive(t):
    return len(t.split()) >= 3 or len(t.replace(' ', '')) >= 15


def title_only_ok(df):
    def sub_ok(a, b):
        if not a:
            return True
        ta, tb = set(a.split()), set(b.split())
        return len(ta & tb) / max(1, len(ta)) >= 0.5
    ok_sub = np.array([sub_ok(g, s) for g, s in zip(df.title_sub, df.spl_sub)], dtype=bool)
    late = ((df.first_ym > 201712) & (df.pub_year_min.fillna(9999) > 2017)).values
    return ok_sub & ~late


tp = [title_parts(t) for t in G.gr_title]
G['title_sub'] = [x[1] for x in tp]
gr_title_n = G.groupby('title_main').gr_work_id.nunique()
spl_title_n = W.groupby('title_main').work_id.nunique()
uniq_all = set(gr_title_n[gr_title_n == 1].index) & set(spl_title_n[spl_title_n == 1].index) - {''}
uniq = {t for t in uniq_all if distinctive(t)}
gc = G[(G.creator_key == '') & G.title_main.isin(uniq)]
C = W[~W.work_id.isin(AB.work_id)].merge(gc[['gr_work_id', 'title_main', 'ratings', 'title_sub']], on='title_main'); C['tier'] = 'C'
C = C[title_only_ok(C)]
gd = G[(G.creator_key == '') & G.title_main.isin(uniq_all - uniq) & (G.ratings >= 20000)]
Dd = W[~W.work_id.isin(AB.work_id) & ~W.work_id.isin(C.work_id)].merge(gd[['gr_work_id', 'title_main', 'ratings', 'title_sub']], on='title_main'); Dd['tier'] = 'D'
Dd = Dd[title_only_ok(Dd)]
L = pd.concat([AB, C, Dd])[['work_id', 'gr_work_id', 'tier']]
L.to_parquet(f'{OUT}/spl_goodreads_link.parquet', index=False)
Wl = W.merge(L, on='work_id', how='left')
dig = Wl.formats.str.contains('AUDIOBOOK|EBOOK')
v2 = json.load(open(f'{OUT_V2}/profile/goodreads_link_summary.json'))
summ = dict(goodreads_works=len(G), goodreads_works_with_author_name=int(G.author_name.notna().sum()), spl_works=len(W),
            linked=int(Wl.tier.notna().sum()), by_tier=Wl.tier.value_counts().to_dict(),
            share_works_linked=float(Wl.tier.notna().mean()), share_checkouts_linked=float(Wl[Wl.tier.notna()].checkouts_total.sum() / W.checkouts_total.sum()),
            digital_works=int(dig.sum()), digital_works_linked=int((dig & Wl.tier.notna()).sum()),
            goodreads_works_used=int(L.gr_work_id.nunique()), v2_linked=v2['linked'], v2_by_tier=v2['by_tier'])
save_json(summ, f'{OUT}/profile/goodreads_link_summary.json')
print(summ)
