# 94. Figures 5.1 to 5.4 of the thesis (Chapter 5; paper/Thesis_Draft_2026-11-06_2020.md and later).
# Values are read from the result files where they hold them (books chosen in time: data/reports/wiki_led_l_backtest.json; well-known books:
# wiki_led_test_a_c.json, corrected rerun; new books: wiki_led_test_b.json); the rest are typed in below with the report each comes from.
# Look: thesis_figstyle.py (printed width 6.2 in, Helvetica Neue 8 pt, entity colours and marker shapes fixed across figures).
# 14 Nov 2026: redrawn in the shared style (same values as the 5 Nov figures); Figure 5.4 (share of the top 20 that rose, all works
# and works not yet risen) added in place of Table 5.3. Output: paper/figures/fig5_1 to fig5_4 *_2026-11-14.png (300 dpi).
# POSTER_FIGS=1 writes the poster versions of 5.1 to 5.3 (one-line labels, larger type, SVG) to paper/poster/figs/.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/94_thesis_figures_ch5.py
import sys, json, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR                             # noqa: E402
import thesis_figstyle as S                                  # noqa: E402
from thesis_figstyle import plt                              # noqa: E402

REP = pathlib.Path(DATA_DIR) / 'reports'
STAMP = '2026-11-14'
POSTER = S.POSTER
PW = 6.3                                                     # poster figure width (in); text about 19 pt at A1

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


def labels(items):
    """Thesis: (label, note) two-line labels; poster: the one-line short form (third element)."""
    if POSTER:
        return [('#', it[1]) if it[0] == '#' else it[2] for it in items]
    return [it if it[0] == '#' else (it[0], it[1]) for it in items]


# Figure 5.1: Wikipedia alone, the library record and both
rows51 = [
    (('Existing books, main set', "next month's change in loans", 'Existing books, main set'),
     {'wiki': from_l('W14'), 'lib': from_l('HM'), 'both': from_l('HMW14')}),
    (('Existing books, well-known*', "next month's change in loans", 'Existing books, well-known*'),
     {'wiki': from_a('Wlgbm_D'), 'lib': from_a('Hlgbm_D'), 'both': from_a('HWlgbm_D')}),
    (('New books', 'loans in the first six months', 'New books (first six months)'),
     {'wiki': from_b('W_lgbm'), 'lib': from_b('L_lgbm'), 'both': from_b('LW_lgbm')}),
    # Wikipedia_Led_Results_2026-10-22_1512.md, Test B table: new books with no earlier Seattle book by the author (45,303)
    (('New books, no earlier book by the author', 'loans in the first six months', 'New books, no earlier book by author'),
     {'wiki': ci(0.090), 'lib': ci(0.045), 'both': ci(0.101)}),
    # same document, Test E: LibriVox rows with stored Wikipedia views (20.5%)
    (('LibriVox recordings', "next month's change in listening", 'LibriVox listening'),
     {'wiki': ci(0.052), 'lib': ci(0.364), 'both': ci(0.359)}),
]
fig, ax = S.figure(1.95 if POSTER else 3.05, PW if POSTER else None)
S.rows_axis(ax, [''] * len(rows51), top_pad=0.55)
S.row_labels(ax, labels([r[0] for r in rows51]))
for i, (_, vals) in enumerate(rows51):
    for off, ent in zip((-0.22, 0, 0.22), ('wiki', 'lib', 'both')):
        S.point(ax, *vals[ent], i + off, ent)
ax.axvline(0, color=S.MUTED, linewidth=0.6, zorder=1)
ax.set_xlim(-0.01, 0.42)
ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4])
ax.set_xlabel('Rank correlation with the actual outcome' + ('' if POSTER else ' (0 is chance)'))
if POSTER:                                                   # the poster figure is narrower than its legend: put the legend across the figure
    leg = S.legend(ax, ['wiki', 'lib', 'both'])
    fig.legend(leg.legend_handles, [h.get_text() for h in leg.get_texts()], loc='outside upper center', ncol=3)
    leg.remove()
else:
    S.legend(ax, ['wiki', 'lib', 'both'])
S.save(fig, 'fig5_1_alone_library_both', STAMP)

# Figure 5.2: borrowing after lasting rises, by page set (synthetic control, months 0 to 2, log share)
rows52 = [
    # Thesis_Draft_2026-10-17_0411.md, Table B3 (Wikipedia, lasting rises)
    (('Hand-reviewed concept pages', 'narrow themes', 'Concept pages, narrow themes'), ci(0.088, 0.029, 0.156)),
    (('Hand-reviewed concept pages', 'middle themes', 'Concept pages, middle themes'), ci(0.105, 0.018, 0.227)),
    # data/reports/testF_results.md and testF_h_concept_results.md, panel a (narrow and middle pooled)
    (('Pages sorted by the AI model', 'all kinds', 'AI-sorted pages, all kinds'), ci(0.018, 0.0005, 0.035)),
    (('Pages sorted by the AI model', 'concepts only', 'AI-sorted pages, concepts only'), ci(0.028, 0.001, 0.055)),
]
fig, ax = S.figure(1.85 if POSTER else 2.1, PW if POSTER else None)
S.rows_axis(ax, [''] * len(rows52), top_pad=0.5)
S.row_labels(ax, labels([r[0] for r in rows52]))
for i, (_, v) in enumerate(rows52):
    S.point(ax, *v, i, 'wiki')
    S.value_label(ax, v[2], i, f'+{v[0]:.3f}')
ax.axvline(0, color=S.MUTED, linewidth=0.6, zorder=1)
ax.set_xlim(-0.01, 0.27)
ax.set_xlabel("Change in the theme's share of borrowing, months 0 to 2\n(log scale; 0.10 is about +10.5%)")
S.save(fig, 'fig5_2_page_sets', STAMP)

# Figure 5.3: gain from adding Wikipedia to the library record
gain_l = L['decisions']['L2a']
rwp = P['all'].get('_rows_with_page')
rows53 = [
    ('#', 'Existing books'),
    (('Main set', 'all works', 'Main set, all works'), ci(gain_l['est'], gain_l['lo'], gain_l['hi'])),
    # wiki_led_l_backtest.md, rows with an article feature: HMW14 0.3548 minus HM 0.3482
    (('Main set', 'rows with an article', 'Main set, books with an article'),
     ci(rwp['HMW14']['est'] - rwp['HM']['est']) if isinstance(rwp, dict) and 'HMW14' in rwp else ci(0.3548 - 0.3482)),
    (('Well-known books*', 'next month', 'Well-known books, next month*'),
     ci(A['paired']['HW_minus_H_change_rank']['mean'], A['paired']['HW_minus_H_change_rank']['lo'], A['paired']['HW_minus_H_change_rank']['hi'])),
    # data/reports/dir_d1_horizons_books.md: average of the next 3, 6 and 12 months, well-known books
    (('Well-known books*', 'next 3 months', 'Well-known, next 3 months*'), ci(0.011)),
    (('Well-known books*', 'next 6 months', 'Well-known, next 6 months*'), ci(0.011)),
    (('Well-known books*', 'next 12 months', 'Well-known, next 12 months*'), ci(0.010)),
    ('#', 'New books'),
    (('All new books', 'loans in the first six months', 'All new books'), from_b('LW_minus_L')),
    (("Author's article viewed", 'before the first loan', "Author's page had earlier views"), from_b('LW_minus_L', 'matched')),
    # Wikipedia_Led_Results_2026-10-22_1512.md, Test B table
    (('Author has an earlier', 'Seattle book', 'Earlier book by the author'), ci(0.020)),
    (('No earlier book', 'by the author', 'No earlier book by the author'), ci(0.056)),
]
if POSTER:                                                   # the short labels name the group, so the headings are left out
    rows53 = [r for r in rows53 if r[0] != '#']
fig, ax = S.figure(2.2 if POSTER else 4.0, PW if POSTER else None)
S.rows_axis(ax, [''] * len(rows53), top_pad=0.5)
S.row_labels(ax, labels([r if r[0] == '#' else r[0] for r in rows53]))
for i, r in enumerate(rows53):
    if r[0] == '#':
        continue
    v = r[1]
    S.point(ax, *v, i, 'both')
    S.value_label(ax, v[2] if v[2] is not None else v[0], i, f'+{v[0]:.3f}')
ax.axvline(0, color=S.MUTED, linewidth=0.6, zorder=1)
ax.set_xlim(-0.002, 0.068)
ax.set_xlabel('Gain in rank correlation from adding Wikipedia' if POSTER else 'Gain in rank correlation from adding Wikipedia to the library model')
S.save(fig, 'fig5_3_gain_by_situation', STAMP)

# Figure 5.4 (thesis only): share of each month's top 20 that rose, all formats, 2019 to 2026 (Table A.1 gives the same numbers by format)
if not POSTER:
    allf = P['all']
    order = [('rand', None), ('wiki', 'W14'), ('pers', 'naive'), ('lib', 'HM'), ('both', 'HMW14')]
    fig, axs = S.figure(2.05, sharey=True, ncols=2)
    for k, (ax, key, title) in enumerate(zip(axs, ('top20', 'early_top20'),
                                              ('A  All works', 'B  Works not yet risen'))):
        S.rows_axis(ax, [''] * len(order), top_pad=0.6)
        if k == 0:
            S.row_labels(ax, [S.ENT[e][0] for e, _ in order])
        for i, (ent, m) in enumerate(order):
            if m is None:
                if key == 'top20':                         # random pick: the base rate of rising (no interval)
                    v = (allf['_base_rose'], None, None)
                else:
                    S.value_label(ax, 0, i, 'base rate not computed', dx=2)
                    continue
            else:
                d = allf[m][key]
                v = (d['est'], d['lo'], d['hi'])
            ax.barh(i, v[0], height=0.52, color=S.ENT[ent][1], linewidth=0, zorder=2)
            if v[1] is not None:
                ax.plot([v[1], v[2]], [i, i], color=S.INK, linewidth=0.8, solid_capstyle='butt', zorder=3)
            if v[0] > 0.3:                                 # long bar: value inside at its start, clear of the target line
                ax.annotate(f'{100 * v[0]:.1f}%', (0, i), xytext=(4, 0), textcoords='offset points', va='center', ha='left',
                            fontsize=S.BASE - 0.5, color=S.INK if ent == 'pers' else 'white', fontweight='bold', zorder=4)
            else:
                S.value_label(ax, v[2] if v[2] is not None else v[0], i, f'{100 * v[0]:.1f}%', dx=4)
        ax.set_xlim(0, 1.0)
        ax.set_xticks([0, 0.25, 0.5, 0.75])
        ax.set_xticklabels(['0', '25%', '50%', '75%'])
        ax.spines['left'].set_visible(True)
        ax.spines['left'].set_color(S.MUTED)
        ax.set_title(title, fontsize=S.BASE + 0.5)
        if key == 'top20':
            ax.axvline(0.9, color=S.INK2, linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
            ax.annotate('90% target', (0.9, -0.55), xytext=(0, 1), textcoords='offset points', ha='center', va='bottom',
                        fontsize=S.BASE - 0.5, color=S.INK2, annotation_clip=False)
    fig.supxlabel("Share of each month's top 20 that rose the next month (95% interval)", fontsize=S.BASE)
    S.save(fig, 'fig5_4_top20', STAMP)

for name, rows in (('5.1', rows51), ('5.2', rows52), ('5.3', [r for r in rows53 if r[0] != '#'])):
    print('Figure', name)
    for lab, v in rows:
        print('  ', lab[0], lab[1], {k: tuple(round(x, 4) if x is not None else None for x in t) for k, t in v.items()} if isinstance(v, dict)
              else tuple(round(x, 4) if x is not None else None for x in v))
print('written to', S.POSTER_DIR if POSTER else S.FIG)
