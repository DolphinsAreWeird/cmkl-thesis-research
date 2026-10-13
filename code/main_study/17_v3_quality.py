# 17. (v3) Quality checks for checkpoint 2: coverage by fiction / nonfiction and format, in works and checkouts, with and
# without the title-word backup; v2 comparison on digital works; themes per work; node sizes by number of works (no
# per-category checkout totals, following the fixed settings in prereg/: only the control categories' demand is viewed);
# 10 random works for a spot check; heading parse summary.
# Output: data/db/taxonomy_v3/quality/*.csv and quality_summary.json
import os
os.environ['TAXO'] = 'v3'
import json, numpy as np, pandas as pd
from _common import OUT, OUT_V2, save_json

Q = f'{OUT}/quality'; os.makedirs(Q, exist_ok=True)
W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'creator', 'formats', 'checkouts_audiobook', 'checkouts_ebook', 'checkouts_book',
                                                          'checkouts_total', 'n_terms', 'n_headings'])
W = W.merge(pd.read_parquet(f'{OUT}/work_form_label.parquet'), on='work_id')
WT = pd.read_parquet(f'{OUT}/work_theme.parquet'); TB = pd.read_parquet(f'{OUT}/work_theme_title_backup.parquet')
EV = pd.read_parquet(f'{OUT}/work_theme_value.parquet')
N = pd.read_parquet(f'{OUT}/theme_nodes.parquet'); lab = dict(zip(N.node_id, N.label))
S = {}
main_any = set(WT.work_id); main_nar = set(WT[WT.level == 3].work_id)
tb_any = set(TB.work_id); tb_nar = set(TB[TB.level == 3].work_id)
rows = []
groups = {'all works': W.work_id.notna(), 'fiction': W.form_label == 'fiction', 'nonfiction': W.form_label == 'nonfiction',
          'form unknown or mixed': W.form_label.isin(['unknown', 'mixed'])}
for fmt in ['audiobook', 'ebook', 'book', 'digital (audiobook + ebook)']:
    co = W[['checkouts_audiobook', 'checkouts_ebook']].sum(1) if fmt.startswith('digital') else W[f'checkouts_{fmt}']
    inf = co > 0
    for gname, gm in groups.items():
        d = W[inf & gm]; c = co[inf & gm]
        for meas, ws in [('any theme', main_any), ('narrow theme', main_nar), ('any theme incl. title words', main_any | tb_any),
                         ('narrow theme incl. title words', main_nar | tb_nar)]:
            m = d.work_id.isin(ws)
            rows.append(dict(format=fmt, group=gname, measure=meas, works=int(len(d)), share_works=round(float(m.mean()) if len(d) else np.nan, 4),
                             share_checkouts=round(float(c[m.values].sum() / max(1, c.sum())), 4)))
COV = pd.DataFrame(rows); COV.to_csv(f'{Q}/coverage.csv', index=False)
# by source (all works with any checkouts)
src = []
for s in ['spl', 'lcsh', 'gr']:
    ws = set(EV[(EV.source == s) & EV.node_id.notna()].work_id)
    m = W.work_id.isin(ws)
    src.append(dict(source=s, works=int(m.sum()), share_works=round(float(m.mean()), 4), share_checkouts=round(float(W[m].checkouts_total.sum() / W.checkouts_total.sum()), 4)))
pd.DataFrame(src).to_csv(f'{Q}/coverage_by_source.csv', index=False)
# v2 comparison: digital works only
v2 = json.load(open(f'{OUT_V2}/quality/quality_summary.json'))['coverage_all']
dg = W[W.checkouts_audiobook + W.checkouts_ebook > 0]; dco = dg.checkouts_audiobook + dg.checkouts_ebook
S['digital_v3'] = {k: dict(share_works=round(float(dg.work_id.isin(ws).mean()), 4), share_checkouts=round(float(dco[dg.work_id.isin(ws).values].sum() / dco.sum()), 4))
                   for k, ws in [('any theme', main_any), ('narrow theme', main_nar), ('any theme incl. title words', main_any | tb_any), ('narrow theme incl. title words', main_nar | tb_nar)]}
S['digital_v2'] = {'any theme': v2['any theme (any level)'], 'narrow theme': v2['narrow level'], 'narrow theme without title words': v2['narrow theme without title words']}
S['works'] = dict(total=len(W), digital=int(len(dg)), print_only=int((W.formats == 'BOOK').sum()), with_headings=int((W.n_headings > 0).sum()),
                  digital_with_headings=int((dg.n_headings > 0).sum()), digital_checkout_share_with_headings=round(float(dco[(dg.n_headings > 0).values].sum() / dco.sum()), 4))
S['form_labels'] = W.form_label.value_counts().to_dict()
S['coverage_by_source'] = src

# themes per work, node sizes by works
k = WT.groupby(['work_id', 'level']).size().unstack(fill_value=0)
S['themes_per_work_among_covered'] = {f'level_{l}': k[k[l] > 0][l].describe(percentiles=[.5, .9]).round(2).to_dict() for l in [1, 2, 3]}
size = WT.groupby('node_id').agg(works=('work_id', 'size'), works_top=('rank_in_level', lambda r: int((r == 1).sum())),
                                 works_lcsh=('s_lcsh', lambda s: int((s > 0).sum()))).reset_index()
size = N[['node_id', 'level', 'label', 'added_in', 'n_values_v3']].merge(size, on='node_id', how='left').fillna({'works': 0, 'works_top': 0, 'works_lcsh': 0})
size.to_csv(f'{Q}/node_sizes_by_works.csv', index=False)
S['narrow_nodes_by_works'] = pd.cut(size[size.level == 3].works, [-1, 0, 9, 29, 99, 999, 1e9], labels=['0', '1-9', '10-29', '30-99', '100-999', '1000+']).value_counts().sort_index().to_dict()

# 10 random works for a spot check (works with checkouts in a digital format and at least one theme)
pool = W[(W.checkouts_audiobook + W.checkouts_ebook > 0) & W.work_id.isin(main_any)]
smp = pool.sample(10, random_state=20261013)
HP = pd.read_parquet(f'{OUT}/headings_parsed.parquet', columns=['heading_id', 'heading'])
WH = pd.read_parquet(f'{OUT}/work_headings.parquet')
WTm = pd.read_parquet(f'{OUT}/work_terms.parquet')
rr = []
for r in smp.itertuples():
    t = WT[WT.work_id == r.work_id].sort_values(['level', 'strength'], ascending=[True, False])
    def fmt(l, n=3):
        x = t[t.level == l]
        return ' ; '.join(f'{lab[a]} ({s:.2f})' for a, s in zip(x.node_id.head(n), x.strength.head(n)))
    heads = WH[WH.work_id == r.work_id].sort_values('share', ascending=False).merge(HP, on='heading_id').heading.head(5).tolist()
    terms = WTm[WTm.work_id == r.work_id].term.tolist()
    rr.append(dict(work_id=r.work_id, title=r.title, creator=r.creator, formats=r.formats, form=r.form_label, spl_terms=', '.join(terms),
                   print_headings=' | '.join(heads), sources=t.sources.iloc[0], broad=fmt(1), middle=fmt(2), narrow=fmt(3), judge_ok='', judge_note=''))
pd.DataFrame(rr).to_csv(f'{Q}/random_10_works_for_review.csv', index=False)

# unplaced values (on 3 or more works, no node): works and checkouts that carry one, and those whose only theme evidence
# is unplaced (no theme in the main assignment)
LOG = pd.read_csv(f'{OUT}/profile/placement_log.csv', usecols=['theme', 'method'], low_memory=False)
unpl = set(LOG[LOG.method == 'unplaced'].theme)
w_un = set(EV[EV.theme.isin(unpl)].work_id)
ur = []
for fmt in ['audiobook', 'ebook', 'book', 'digital (audiobook + ebook)', 'all formats']:
    co = (W[['checkouts_audiobook', 'checkouts_ebook']].sum(1) if fmt.startswith('digital') else
          W.checkouts_total if fmt == 'all formats' else W[f'checkouts_{fmt}'])
    d = W[co > 0]; c = co[co > 0]
    for meas, ws in [('carries an unplaced value', w_un), ('only unplaced values (no theme)', w_un - main_any)]:
        m = d.work_id.isin(ws)
        ur.append(dict(format=fmt, measure=meas, works=int(m.sum()), share_works=round(float(m.mean()), 4),
                       share_checkouts=round(float(c[m.values].sum() / c.sum()), 4)))
UR = pd.DataFrame(ur); UR.to_csv(f'{Q}/unplaced_share.csv', index=False)
S['unplaced_values'] = dict(values=len(unpl), share=ur)
save_json(S, f'{Q}/quality_summary.json')
pd.set_option('display.width', 250)
print(COV[COV.group.isin(['all works', 'fiction', 'nonfiction'])].pivot_table(index=['format', 'group'], columns='measure', values=['share_works', 'share_checkouts']).round(3).to_string())
print(json.dumps({k: S[k] for k in ['digital_v3', 'digital_v2', 'works', 'form_labels', 'narrow_nodes_by_works']}, indent=0, default=str))
print(pd.DataFrame(src).to_string(index=False))
