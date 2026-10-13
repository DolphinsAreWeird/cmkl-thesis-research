# 19. (v3) Write every number table used in checkpoint 2 to data/reports/main_study_checkpoint_2_tables.md, straight from the
# saved v3 outputs, so a rerun on the full print file refreshes the tables in one step. Section names are short codes
# that the report refers to (FILES, COV ..., SIZE ..., MINSIZE, UNPLACED, LIBRIVOX, RANDOM ...).
import os
os.environ['TAXO'] = 'v3'
import json, numpy as np, pandas as pd
from _common import OUT, REP
B = OUT
OUTF = f'{REP}/main_study_checkpoint_2_tables.md'
o = []
def md(df):
    cols = list(df.columns); s = '| ' + ' | '.join(map(str, cols)) + ' |\n|' + '|'.join(['---'] * len(cols)) + '|\n'
    for r in df.itertuples(index=False):
        s += '| ' + ' | '.join('' if (isinstance(x, float) and np.isnan(x)) else str(x) for x in r) + ' |\n'
    return s
n = lambda x: f'{int(round(x)):,}'
P = json.load(open(f'{B}/profile/v3_profile.json'))
rows = []
for f in ['audiobook', 'ebook', 'book']:
    x = P[f]; rows.append([f, n(x['rows']), n(x['api_rows']), f"{x['share_of_api_rows']*100:.1f}", n(x['checkouts']), f"{x['first_month']} to {x['last_month']}", x['months'], x['months_complete'], x['complete_through']])
o.append('## FILES\n' + md(pd.DataFrame(rows, columns=['Format', 'Rows read', 'API rows', '% of API', 'Checkouts', 'Months', 'Months present', 'Complete months', 'Complete through'])))
o.append('## PROFILEJSON\n```\n' + json.dumps({k: P[k] for k in ['book_records', 'headings', 'works']}, indent=1) + '\n```\n')
Y = pd.read_csv(f'{B}/profile/v3_by_year_format.csv'); y = Y[Y.format == 'book'].copy()
o.append('## BOOKYEAR\n' + md(y.assign(rows=y.rows.map(n), checkouts=y.checkouts.map(n), subj=(y.share_rows_with_subjects * 100).round(1), cre=(y.share_rows_creator_missing * 100).round(1))[['year', 'rows', 'checkouts', 'months', 'subj', 'cre']]))
G = json.load(open(f'{B}/profile/goodreads_link_summary.json')); o.append('## LINK\n```\n' + json.dumps(G, indent=1) + '\n```\n')
C = pd.read_parquet(f'{B}/lcsh_cores.parquet')
o.append('## CORES\n' + md(C.groupby('kind').agg(cores=('core', 'size'), works=('n_works', 'sum')).reset_index()))
t = C[C.kind == 'topic']
o.append('## CORESRC\n' + md(t.groupby('value_source').agg(cores=('core', 'size'), works=('n_works', 'sum')).reset_index()))
L = pd.read_csv(f'{B}/profile/placement_log.csv', low_memory=False)
o.append('## PLACE\n' + md(L.groupby('method').agg(values=('theme', 'size'), works=('n_works', 'sum')).reset_index()))
o.append('## PLACELEVEL\n' + md(L[L.node_id.notna()].groupby('level').agg(values=('theme', 'size')).reset_index()))
cal = json.load(open(f'{B}/profile/placement_calibration.json')); o.append('## CAL\n' + json.dumps({k: cal[k] for k in ['loo_accuracy_narrow', 'hand_judged_bands', 'tau_narrow']}))
hand = L[L.method == 'hand'].sort_values('n_works', ascending=False).head(40)
o.append('## HANDTOP\n' + md(hand[['theme', 'n_works', 'node_label', 'reason']]))
emb = L[L.method == 'embedding: narrow'].sort_values('n_works', ascending=False).head(30)
o.append('## EMBTOP\n' + md(emb[['theme', 'n_works', 'node_label', 'sim']]))
un = L[L.method == 'unplaced'].sort_values('n_works', ascending=False).head(30)
o.append('## UNPLTOP\n' + '; '.join(f'{a} ({b})' for a, b in zip(un.theme, un.n_works)))
o.append('## NEWNODES\n' + md(pd.read_csv(f'{B}/profile/new_nodes.csv')))
COV = pd.read_csv(f'{B}/quality/coverage.csv')
for fmt in ['audiobook', 'ebook', 'book', 'digital (audiobook + ebook)']:
    rows = []
    for g in ['all works', 'fiction', 'nonfiction', 'form unknown or mixed']:
        r = [g]
        x = COV[(COV.format == fmt) & (COV.group == g)]
        if x.empty: continue
        r.append(n(x.works.iloc[0]))
        for meas in ['any theme', 'narrow theme', 'any theme incl. title words', 'narrow theme incl. title words']:
            z = x[x.measure == meas].iloc[0]; r.append(f'{z.share_works*100:.1f} / {z.share_checkouts*100:.1f}')
        rows.append(r)
    o.append(f'## COV {fmt}\n' + md(pd.DataFrame(rows, columns=['Group', 'Works', 'Any theme', 'Narrow theme', 'Any theme incl. title words', 'Narrow theme incl. title words'])))
QS = json.load(open(f'{B}/quality/quality_summary.json')); o.append('## QS\n```\n' + json.dumps(QS, indent=1, default=str) + '\n```\n')
SRC = pd.read_csv(f'{B}/quality/coverage_by_source.csv'); o.append('## SRC\n' + md(SRC))
D = pd.read_csv(f'{B}/quality/control_definitions.csv'); o.append('## CTRLDEF\n' + md(D))
MS = pd.read_csv(f'{B}/quality/control_min_size.csv')    # pass or fail only (the medians stay in the CSV, not shown)
o.append('## MINSIZE\n' + md(MS[['category', 'variant', 'format', 'shift_month', 'works_with_checkouts_in_format', 'months_available', 'passes_min_size']]))
# works with checkouts per year (no checkout counts: the control series are not viewed again after checkpoint 2)
SZ = pd.read_csv(f'{B}/quality/control_sizes_by_year.csv')
for cat in SZ.category.unique():
    z = SZ[(SZ.category == cat) & (SZ.variant == 'main') & (SZ.year >= 2014)]
    w = z.pivot_table(index='year', columns='format', values='works', fill_value=0)
    o.append(f'## SIZE {cat}\n' + md(w.reindex(columns=['audiobook', 'ebook', 'book']).fillna(0).astype(int).reset_index()))
UR = pd.read_csv(f'{B}/quality/unplaced_share.csv'); o.append('## UNPLACED\n' + md(UR))
G = pd.read_parquet(f'{B}/work_genre.parquet')
o.append('## GENRE\n' + md(pd.DataFrame([dict(works_with_genre=G.work_id.nunique(), from_spl_or_goodreads=int(G[(G.s_spl > 0) | (G.s_gr > 0)].work_id.nunique()),
                                                print_only_from_print_genre_parts=int(G[G.s_lcsh > 0].work_id.nunique()))])))
if os.path.exists(f'{B}/quality/librivox_coverage.csv'):
    o.append('## LIBRIVOX\n' + md(pd.read_csv(f'{B}/quality/librivox_coverage.csv')) + md(pd.read_csv(f'{B}/quality/librivox_top_nodes.csv').head(25)))
R = pd.read_csv(f'{B}/quality/random_10_works_for_review.csv')
o.append('## RANDOM\n' + md(R[['title', 'creator', 'formats', 'form', 'spl_terms', 'print_headings', 'sources', 'broad', 'narrow']].fillna('')))
NS = pd.read_csv(f'{B}/quality/node_sizes_by_works.csv')
o.append('## NODESIZE\n' + md(NS[NS.level == 3].sort_values('works', ascending=False).head(10)[['node_id', 'label', 'works', 'works_lcsh']]) + md(NS[NS.level == 3].sort_values('works').head(10)[['node_id', 'label', 'works', 'works_lcsh']]))
snap = json.load(open(f'{B}/spl_snapshot.json'))
head = ('# Checkpoint 2 number tables (generated by code/main_study/19_v3_report_tables.py)\n\nPrint snapshot: '
        + f"{snap['BOOK']['lines']:,} lines taken {snap['BOOK']['taken']}.\n\n")
open(OUTF, 'w').write(head + '\n'.join(o)); print('written', OUTF)
