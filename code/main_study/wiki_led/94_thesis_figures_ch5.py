# 94. Figures 5.1 to 5.4 of the rewritten thesis (Chapter 5, draft of 5 Nov 2026: paper/drafts/Thesis_Chapters_3-5_2026-11-05_2009.md).
# Values are read from the result files where they hold them (books chosen in time: data/reports/wiki_led_l_backtest.json; well-known books:
# wiki_led_test_a_c.json, corrected rerun; new books: wiki_led_test_b.json); the rest are typed in below with the report each comes from.
# Colours: categorical slots 1 to 4 of the dataviz reference palette (validated, light mode), entity-fixed across figures, with a marker shape
# per model as a second cue; gray for the random pick. Output: paper/figures/fig5_*_2026-11-05.png (300 dpi).
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/94_thesis_figures_ch5.py
import sys, json, pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
REP = DATA / 'reports'
FIG = DATA.parent / 'paper' / 'figures'
STAMP = '2026-11-05'

INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
STYLE = {                                                   # entity -> (label, colour, marker)
    'rand': ('Random pick', '#8a8985', '|'),
    'wiki': ('Wikipedia alone', '#2a78d6', 'o'),
    'pers': ('Persistence rule', '#eda100', '^'),
    'lib': ('Library record', '#eb6834', 's'),
    'both': ('Library and Wikipedia', '#1baf7a', 'D'),
}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
                     'xtick.color': INK2, 'ytick.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'legend.frameon': False, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})

L = json.load(open(REP / 'wiki_led_l_backtest.json'))
P = L['by_period']['2019-2026']
A = json.load(open(REP / 'wiki_led_test_a_c.json'))
B = json.load(open(REP / 'wiki_led_test_b.json'))


def ci(est, lo=None, hi=None):
    return (est, lo, hi)


def from_l(model, fmt='all', key='rank'):
    v = P[fmt][model][key]
    return ci(v['est'], v['lo'], v['hi'])


def from_a(model):
    v = A['change_rank'][model]
    return ci(v['mean'], v['lo'], v['hi'])


def from_b(model, part='all'):
    v = B[part][model]
    return ci(v.get('spearman', v.get('mean')), v['lo'], v['hi'])


def axes_rows(ax, labels):
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_ylim(len(labels) - 0.5, -0.6)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def point(ax, x, y, ent, size=7):
    est, lo, hi = x
    _, col, mk = STYLE[ent]
    if lo is not None:
        ax.plot([lo, hi], [y, y], color=col, linewidth=2, solid_capstyle='round', zorder=2)
    line_marker = mk == '|'                                  # drawn by its edge only, so the edge carries the colour
    ax.plot([est], [y], marker=mk, color=col, markersize=size, markeredgecolor=col if line_marker else 'white',
            markeredgewidth=2.5 if line_marker else 1.2, linestyle='none', zorder=3)


def legend(ax, ents, ncol):
    hs = [plt.Line2D([], [], marker=STYLE[e][2], color=STYLE[e][1], linestyle='none', markersize=7,
                     markeredgecolor=STYLE[e][1] if STYLE[e][2] == '|' else 'white', markeredgewidth=2.5 if STYLE[e][2] == '|' else 1.0)
          for e in ents]
    ax.legend(hs, [STYLE[e][0] for e in ents], loc='lower left', bbox_to_anchor=(0, 1.0), ncol=ncol, handletextpad=0.3, columnspacing=1.2)


# Figure 5.1: Wikipedia alone, the library record and both
rows51 = [
    ('Existing books, main set\n(next month\'s change in loans)', {'wiki': from_l('W14'), 'lib': from_l('HM'), 'both': from_l('HMW14')}),
    ('Existing books, well-known\n(next month\'s change in loans)', {'wiki': from_a('Wlgbm_D'), 'lib': from_a('Hlgbm_D'), 'both': from_a('HWlgbm_D')}),
    ('New books\n(loans in the first six months)', {'wiki': from_b('W_lgbm'), 'lib': from_b('L_lgbm'), 'both': from_b('LW_lgbm')}),
    # Wikipedia_Led_Results_2026-10-22_1512.md, Test B table: new books with no earlier Seattle book by the author (45,303)
    ('New books, no earlier book\nby the author', {'wiki': ci(0.090), 'lib': ci(0.045), 'both': ci(0.101)}),
    # same document, Test E: LibriVox rows with stored Wikipedia views (20.5%)
    ('LibriVox recordings\n(next month\'s change in listening)', {'wiki': ci(0.052), 'lib': ci(0.364), 'both': ci(0.359)}),
]
fig, ax = plt.subplots(figsize=(6.3, 3.6))
axes_rows(ax, [r[0] for r in rows51])
for i, (_, vals) in enumerate(rows51):
    for off, ent in zip((-0.2, 0, 0.2), ('wiki', 'lib', 'both')):
        point(ax, vals[ent], i + off, ent)
ax.axvline(0, color=INK2, linewidth=0.8)
ax.set_xlim(-0.01, 0.46)
ax.set_xlabel('Rank correlation with the actual outcome (0 is chance)')
legend(ax, ['wiki', 'lib', 'both'], 3)
fig.savefig(FIG / f'fig5_1_alone_library_both_{STAMP}.png')
plt.close(fig)

# Figure 5.2: borrowing after lasting rises, by page set (synthetic control, months 0 to 2, log share)
rows52 = [
    # Thesis_Draft_2026-10-17_0411.md, Table B3 (Wikipedia, lasting rises)
    ('Hand-checked concept pages,\nnarrow themes', ci(0.088, 0.029, 0.156)),
    ('Hand-checked concept pages,\nmiddle themes', ci(0.105, 0.018, 0.227)),
    # data/reports/testF_results.md and testF_h_concept_results.md, panel a (narrow and middle pooled)
    ('Pages sorted by the AI model,\nall kinds', ci(0.018, 0.0005, 0.035)),
    ('Pages sorted by the AI model,\nconcepts only', ci(0.028, 0.001, 0.055)),
]
fig, ax = plt.subplots(figsize=(6.3, 2.6))
axes_rows(ax, [r[0] for r in rows52])
for i, (_, v) in enumerate(rows52):
    point(ax, v, i, 'wiki')
    ax.annotate(f'+{v[0]:.3f}', (v[2], i), xytext=(6, 0), textcoords='offset points', va='center', color=INK, fontsize=8.5)
ax.axvline(0, color=INK2, linewidth=0.8)
ax.set_xlim(-0.02, 0.27)
ax.set_xlabel('Change in the theme\'s share of borrowing, months 0 to 2 (log scale; 0.10 is about +10.5%)')
fig.savefig(FIG / f'fig5_2_page_sets_{STAMP}.png')
plt.close(fig)

# Figure 5.3: gain from adding Wikipedia to the library record
gain_l = L['decisions']['L2a']
rows53 = [
    ('Existing books, main set', ci(gain_l['est'], gain_l['lo'], gain_l['hi'])),
    # wiki_led_l_backtest.md, rows with an article feature: HMW14 0.3548 minus HM 0.3482
    ('Existing books, main set,\nrows with an article', ci(P['all']['_rows_with_page']['HMW14']['est'] - P['all']['_rows_with_page']['HM']['est'])
     if isinstance(P['all'].get('_rows_with_page'), dict) and 'HMW14' in P['all']['_rows_with_page'] else ci(0.3548 - 0.3482)),
    ('Existing books, well-known', ci(A['paired']['HW_minus_H_change_rank']['mean'], A['paired']['HW_minus_H_change_rank']['lo'],
                                      A['paired']['HW_minus_H_change_rank']['hi'])),
    # data/reports/dir_d1_horizons_books.md: average of the next 3, 6 and 12 months, well-known books
    ('Well-known, next 3 months', ci(0.011)),
    ('Well-known, next 6 months', ci(0.011)),
    ('Well-known, next 12 months', ci(0.010)),
    ('New books, all', from_b('LW_minus_L')),
    ('New books, author\'s article\nviewed before the first loan', from_b('LW_minus_L', 'matched')),
    # Wikipedia_Led_Results_2026-10-22_1512.md, Test B table
    ('New books, author has an\nearlier Seattle book', ci(0.020)),
    ('New books, no earlier\nbook by the author', ci(0.056)),
]
fig, ax = plt.subplots(figsize=(6.3, 4.4))
axes_rows(ax, [r[0] for r in rows53])
for i, (_, v) in enumerate(rows53):
    point(ax, v, i, 'both')
    ax.annotate(f'+{v[0]:.3f}', (v[2] if v[2] is not None else v[0], i), xytext=(6, 0), textcoords='offset points', va='center', color=INK, fontsize=8.5)
for y in (2.5, 5.5):
    ax.axhline(y, color=GRID, linewidth=0.8)
ax.axvline(0, color=INK2, linewidth=0.8)
ax.set_xlim(-0.002, 0.068)
ax.set_xlabel('Gain in rank correlation from adding Wikipedia to the library record')
fig.savefig(FIG / f'fig5_3_gain_by_situation_{STAMP}.png')
plt.close(fig)

# Figure 5.4: share of each month's top 20 that rose, by format (main set, 2019 to 2026)
fmts = [('print', 'Print'), ('ebook', 'Ebook'), ('audiobook', 'Audiobook'), ('all', 'All formats')]
fig, ax = plt.subplots(figsize=(6.3, 3.4))
axes_rows(ax, [f[1] for f in fmts])
for i, (f, _) in enumerate(fmts):
    base = P[f]['_base_rose']
    base = base['est'] if isinstance(base, dict) else base
    point(ax, ci(base), i, 'rand', size=11)
    # small vertical offsets so the library and the library-and-Wikipedia marks, often within a point of each other, stay visible
    for ent, model, off in (('wiki', 'W14', 0), ('pers', 'naive', -0.22), ('lib', 'HM', 0), ('both', 'HMW14', 0.22)):
        point(ax, ci(P[f][model]['top20']['est']), i + off, ent)
ax.axvline(0.9, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)))
ax.annotate('90% target', (0.9, -0.55), xytext=(3, 0), textcoords='offset points', color=INK2, fontsize=8, va='center')
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_xlabel('Share of each month\'s top 20 that rose next month')
legend(ax, ['rand', 'wiki', 'pers', 'lib', 'both'], 5)
fig.savefig(FIG / f'fig5_4_top20_by_format_{STAMP}.png')
plt.close(fig)

for name, rows in (('5.1', rows51), ('5.2', rows52), ('5.3', rows53)):
    print('Figure', name)
    for lab, v in rows:
        print('  ', lab.replace('\n', ' '), {k: tuple(round(x, 4) if x is not None else None for x in t) for k, t in v.items()} if isinstance(v, dict)
              else tuple(round(x, 4) if x is not None else None for x in v))
print('Figure 5.4', {f: {m: round(P[f][m]['top20']['est'], 3) for m in ('W14', 'naive', 'HM', 'HMW14')} for f, _ in fmts})
print('written to', FIG)
