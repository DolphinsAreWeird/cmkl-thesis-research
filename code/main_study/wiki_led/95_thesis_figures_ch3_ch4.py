# 95. Figures 3.1, 3.2 and 4.1 of the thesis (paper/Thesis_Draft_2026-11-06_2020.md and later). Look: thesis_figstyle.py.
# 3.1 The years each source covers. Dates as stated in Chapter 3: Seattle loans April 2005 to August 2026; Wikipedia user views July 2015
#     to September 2026; New York Times lists June 2008 to October 2026; LibriVox views January 2017 to August 2026; months scored January
#     2019 to July 2026 (predicted months to August 2026); months left out 2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08; forecasts fixed
#     in advance for September to November 2026.
# 3.2 (added 14 Nov 2026) Two well-known books with screen adaptations: monthly Seattle loans (all formats) and the share of English
#     Wikipedia views of the book's article over the last four weeks of each month, from data/db/wiki_led/test_a_rows_c.parquet
#     (L_t and b_lvl4 = log mean share of the last 4 weeks; corrected rerun; for American Prometheus the larger of its two works). Release
#     months: Oppenheimer (film of American Prometheus), 21 July 2023; Station Eleven (HBO Max series), 16 December 2021 (Wikidata). Chosen
#     on 14 Nov from 17 adapted books for clean periods (no left-out months beside the release) and opposite responses: views rose about
#     45-fold and 32-fold, loans about 33-fold and 1.2-fold. An illustration of the two series, not a result.
# 4.1 (redrawn 14 Nov 2026, replaces the box-and-arrow diagram) A: what one forecast made at the end of month t uses and predicts
#     (Sections 3.2, 4.1, 4.2); B: the walk-forward split (Section 4.5): training rows are forecasts whose target month ended before the test
#     year (from March 2016, the first row of the main set), test rows are the forecasts made in that year, and forecasts from or for a
#     month left out are not made (t in March to September 2020, April to July 2024, July to August 2025); 78 scored months in all.
# 3.3 (redrawn 14 Nov 2026 from the 16 Oct figure's saved values) From subject headings to narrow, middle and broad themes, one branch.
# Output: paper/figures/fig3_1_*, fig3_2_*, fig3_3_*, fig4_1_* _2026-11-14.png (300 dpi).
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/95_thesis_figures_ch3_ch4.py
import sys, pathlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR                             # noqa: E402
import thesis_figstyle as S                                  # noqa: E402
from thesis_figstyle import plt                              # noqa: E402
from matplotlib.patches import Rectangle, Patch              # noqa: E402

DATA = pathlib.Path(DATA_DIR)
STAMP = '2026-11-14'
LEFT_OUT = ((2020, 4, 2020, 9), (2024, 5, 2024, 7), (2025, 8, 2025, 8))     # library months left out (inclusive)
BLUE_T, ORANGE_T = '#bcd4f2', '#f7c9b4'                      # light tints of the Wikipedia and library colours


def ym(y, m):
    return y + (m - 1) / 12


# ---------------------------------------------------------------- Figure 3.1: the years each source covers
rows = [
    ('Seattle library loans', ym(2005, 4), ym(2026, 9), S.BLUE),
    ('New York Times bestseller lists', ym(2008, 6), ym(2026, 11), S.BLUE),
    ('Wikipedia page views', ym(2015, 7), ym(2026, 10), S.BLUE),
    ('LibriVox listening', ym(2017, 1), ym(2026, 9), S.BLUE),
    ('Months scored in the backtest', ym(2019, 1), ym(2026, 8), S.AQUA),
]
fig, ax = S.figure(1.95)
S.rows_axis(ax, [''] * len(rows), top_pad=0.55)
S.row_labels(ax, [r[0] for r in rows])
h = 0.46
for i, (_, a, b, col) in enumerate(rows):
    ax.add_patch(Rectangle((a, i - h / 2), b - a, h, color=col, linewidth=0, zorder=2))
for y0, m0, y1, m1 in LEFT_OUT:
    for i in (0, 4):                                        # only library months are left out
        ax.add_patch(Rectangle((ym(y0, m0), i - h / 2 - 0.04), ym(y1, m1 + 1) - ym(y0, m0), h + 0.08, facecolor='white',
                               edgecolor=S.MUTED, hatch='//////', linewidth=0, zorder=3))
ax.add_patch(Rectangle((ym(2026, 9), 4 - h / 2), 3 / 12, h, facecolor='white', edgecolor=S.ORANGE, linewidth=1.1, zorder=4))
ax.set_xlim(2005, 2027.2)
ax.set_xticks(range(2005, 2027, 3))
ax.spines['bottom'].set_visible(True)
plt.rcParams['hatch.linewidth'] = 0.5
ax.legend([Patch(facecolor='white', edgecolor=S.MUTED, hatch='//////', linewidth=0),
           Patch(facecolor='white', edgecolor=S.ORANGE, linewidth=1.1)],
          ['Library months left out', 'Forecasts fixed in advance (September to November 2026)'],
          loc='lower left', bbox_to_anchor=(0, 1.0), ncol=2, handlelength=1.6)
S.save(fig, 'fig3_1_data_over_time', STAMP)

# ---------------------------------------------------------------- Figure 3.2: two books, their loans and their article's views
rows_a = pd.read_parquet(DATA / 'db' / 'wiki_led' / 'test_a_rows_c.parquet', columns=['work_id', 'mi', 'L_t', 'article', 'b_lvl4'])
books = [('American Prometheus', 'American Prometheus', (2023, 7), 'Film Oppenheimer\nJuly 2023'),
         ('Station Eleven', 'Station Eleven', (2021, 12), 'TV series\nDecember 2021')]
x0, x1 = ym(2018, 1), ym(2026, 8)
fig, axs = S.figure(3.0, nrows=2, ncols=2, sharex=True, gridspec_kw={'height_ratios': [1, 1]})
for c, (art, title, (ry, rm), rel) in enumerate(books):
    s = rows_a[rows_a.article == art]
    main = s.groupby('work_id').L_t.sum().idxmax()          # the work with most loans (American Prometheus has two records' works)
    s = s[s.work_id == main].sort_values('mi')
    print(art, 'work', main, 'months', len(s))
    full = pd.DataFrame({'mi': np.arange(int(s.mi.min()), int(s.mi.max()) + 1)}).merge(s, on='mi', how='left')   # gaps stay NaN
    x = full.mi // 12 + (full.mi % 12) / 12 + 1 / 24          # month centres
    share = np.exp(full.b_lvl4) * 1e6
    for r, (ax, y, col, lab) in enumerate(((axs[0, c], share, S.BLUE, 'Article views per million\nEnglish Wikipedia views'),
                                           (axs[1, c], full.L_t, S.ORANGE, 'Seattle loans per month'))):
        keep = (x >= x0) & (x <= x1)
        ax.plot(x[keep], y[keep], color=col, linewidth=1.3, solid_joinstyle='round', zorder=3)
        ax.grid(axis='y')
        ax.set_axisbelow(True)
        ax.set_ylim(0, None)
        ax.axvline(ym(ry, rm) + 1 / 24, color=S.INK2, linewidth=0.7, zorder=2)
        for y0, m0, y1, m1 in LEFT_OUT:
            ax.axvspan(ym(y0, m0), ym(y1, m1 + 1), color='#f1f0ec', linewidth=0, zorder=1)
        if c == 0:
            ax.set_ylabel(lab, fontsize=S.BASE - 0.5, color=S.INK2)
        ax.tick_params(axis='y', length=0)
    top = axs[0, c]
    top.set_title(title, loc='left', fontsize=S.BASE + 0.5)
    top.annotate(rel, (ym(ry, rm) + 1 / 24, 1), xycoords=('data', 'axes fraction'), xytext=(-4, -2), textcoords='offset points',
                 va='top', ha='right', fontsize=S.BASE - 1, color=S.INK2)
    axs[1, c].set_xlim(x0, x1)
    axs[1, c].set_xticks(range(2018, 2027, 2))
    axs[1, c].spines['bottom'].set_visible(True)
S.save(fig, 'fig3_2_two_books', STAMP)

# ---------------------------------------------------------------- Figure 3.3: from subject headings to themes (one branch)
# Values written by benchmark/22_figures_data.py --tree (data/db/benchmark/stage2_results/figure_values_fig_theme_hierarchy.csv):
# the middle theme B05.M02 with both of its narrow themes and three of the most common headings of each.
TV = pd.read_csv(DATA / 'db' / 'benchmark' / 'stage2_results' / 'figure_values_fig_theme_hierarchy.csv')
broad = TV[TV.level.str.startswith('broad')].iloc[0]
middle = TV[TV.level.str.startswith('middle')].iloc[0]
narrows = TV[TV.level.str.startswith('narrow')].reset_index(drop=True)
heads = TV[TV.level == 'subject heading']
fig, ax = S.figure(2.6)
ax.set_xlim(-0.3, 100.6); ax.set_ylim(4, 62); ax.axis('off')
THEME_FILL, EDGE = '#e8f0fb', '#c9c8c1'


def tbox(x0, x1, yc, h, lines, fill='white', edge=EDGE, bold=False, sub=None):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x0, yc - h / 2), x1 - x0, h, boxstyle='round,pad=0,rounding_size=0.8', facecolor=fill, edgecolor=edge,
                                linewidth=0.7, zorder=2))
    if sub is None:
        ax.text((x0 + x1) / 2, yc, lines, ha='center', va='center', fontsize=S.BASE - 0.5, color=S.INK, fontweight='bold' if bold else 'normal',
                zorder=3, linespacing=1.15)
    else:
        ax.text((x0 + x1) / 2, yc + 1.4, lines, ha='center', va='center', fontsize=S.BASE - 0.5, color=S.INK, fontweight='bold' if bold else 'normal',
                zorder=3, linespacing=1.15)
        ax.text((x0 + x1) / 2, yc - (h / 2) + 1.9, sub, ha='center', va='center', fontsize=S.BASE - 1, color=S.INK2, zorder=3)


def line(xs, ys, arrow=False):
    ax.plot(xs, ys, color=S.MUTED, linewidth=0.8, solid_capstyle='butt', solid_joinstyle='miter', zorder=1)
    if arrow:
        ax.annotate('', (xs[-1], ys[-1]), (xs[-1] - 1.6, ys[-1]), arrowprops=dict(arrowstyle='-|>', color=S.MUTED, linewidth=0.8,
                                                                                    shrinkA=0, shrinkB=0, mutation_scale=7), zorder=1)


cols = [(0, 'Subject headings (examples)'), (37, 'Narrow themes (242 in all)'), (64, 'Middle theme (86)'), (84, 'Broad theme (19)')]
for x, lab in cols:
    ax.text(x, 60, lab, ha='left', va='center', fontsize=S.BASE - 0.5, color=S.INK2, fontweight='bold')
centers = {0: [50, 43, 36], 1: [22, 15, 8]}
ncent = [43, 15]
for k, nr in narrows.iterrows():
    hs = heads[heads.parent_node_id == nr.node_id].sort_values('n_works', ascending=False).head(3)
    ys = centers[k]
    for yc, (_, hrow) in zip(ys, hs.iterrows()):
        tbox(0, 31, yc, 5.2, '', fill='white')
        ax.text(1.2, yc, hrow.label, ha='left', va='center', fontsize=S.BASE - 0.5, color=S.INK, zorder=3)
        ax.text(29.8, yc, f'{int(hrow.n_works):,}', ha='right', va='center', fontsize=S.BASE - 1, color=S.INK2, zorder=3)
        line([31, 34], [yc, yc])
    line([34, 34], [ys[0], ys[-1]])
    line([34, 36.5], [ncent[k], ncent[k]], arrow=True)
    lab = nr.label[0].upper() + nr.label[1:]
    tbox(36.5, 58, ncent[k], 8.5, lab, fill=THEME_FILL, edge=S.BLUE, bold=True, sub=f'{int(nr.n_works):,} works')
    line([58, 60.5], [ncent[k], ncent[k]])
line([60.5, 60.5], [ncent[0], ncent[1]])
mid_y = 29
line([60.5, 64], [mid_y, mid_y], arrow=True)
tbox(64, 80.5, mid_y, 8.5, middle.label.replace(' and ', '\nand '), fill=THEME_FILL, edge=S.BLUE, bold=True)
line([80.5, 84], [mid_y, mid_y], arrow=True)
tbox(84, 100, mid_y, 8.5, broad.label.replace(' and ', '\nand '), fill=THEME_FILL, edge=S.BLUE, bold=True)
ax.text(29.8, 55.2, 'works', ha='right', va='center', fontsize=S.BASE - 1, color=S.INK2)
S.save(fig, 'fig3_3_theme_hierarchy', STAMP)

# ---------------------------------------------------------------- Figure 4.1: one forecast, and the walk-forward split
fig = plt.figure(figsize=(S.W, 3.9))
gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 2.0])
axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

# A. one forecast, made at the end of month t (x in months; month t spans -1..0, month t+1 spans 0..1)
wk = 1 / 4.345                                              # a week in months
lanes = ['Wikipedia views (weekly)', 'Library loans (monthly)', 'Predicted']
S.rows_axis(axA, [''] * 3, top_pad=1.05)
S.row_labels(axA, lanes)
axA.grid(False)
bh = 0.52


def bar(ax, a, b, y, fc, text=None, tc=S.INK, ec='none', bold=False):
    ax.add_patch(Rectangle((a, y - bh / 2), b - a, bh, facecolor=fc, edgecolor=ec, linewidth=0.8 if ec != 'none' else 0, zorder=2))
    if text:
        ax.text((a + b) / 2, y, text, ha='center', va='center', fontsize=S.BASE - 0.5, color=tc, zorder=3,
                fontweight='bold' if bold else 'normal')


bar(axA, -30 * wk, -4 * wk, 0, BLUE_T, '26-week normal (median)')
bar(axA, -4 * wk, 0, 0, S.BLUE)
axA.annotate('last 4 weeks', (0, 0 + bh / 2), xytext=(-3, -1.5), textcoords='offset points', ha='right', va='top',
             fontsize=S.BASE - 1, color=S.INK2)
for k in range(5, 0, -1):                                   # months t-5 .. t-1, then month t darker
    bar(axA, -k - 1 + 0.02, -k - 0.02, 1, ORANGE_T)
bar(axA, -1 + 0.02, -0.02, 1, S.ORANGE, 'L(t)', tc='white', bold=True)
axA.annotate('six-month median M6 (months t−5 to t)', (-3.5, 1 + bh / 2), xytext=(0, -1.5), textcoords='offset points',
             ha='center', va='top', fontsize=S.BASE - 1, color=S.INK2)
bar(axA, 0.02, 0.98, 2, S.INK2, 'L(t+1)', tc='white', bold=True)
axA.text(1.15, 2, 'change D = ln(1 + L(t+1)) − ln(1 + M6);\nscored against actual loans, never an input', ha='left', va='center',
         fontsize=S.BASE - 1, color=S.INK2)
axA.axvspan(0, 6.0, color='#f4f3ef', zorder=0, linewidth=0)
axA.axvline(0, color=S.INK, linewidth=0.9, zorder=4)
axA.annotate('Forecast made at the end of month t', (0, -0.72), xytext=(-4, 0), textcoords='offset points', ha='right', va='center',
             fontsize=S.BASE - 0.5, color=S.INK)
axA.annotate('Not yet known', (0, -0.72), xytext=(4, 0), textcoords='offset points', ha='left', va='center',
             fontsize=S.BASE - 0.5, color=S.INK2)
axA.set_xlim(-7.2, 6.0)
axA.set_xticks([-k - 0.5 for k in range(6, -1, -1)] + [0.5])
axA.set_xticklabels([f't−{k}' for k in range(6, 0, -1)] + ['t', 't+1'])
axA.tick_params(axis='x', length=0)
axA.spines['bottom'].set_visible(False)
axA.set_title('A  One forecast', fontsize=S.BASE + 0.5)

# B. walk-forward: each test year predicted by models fitted on earlier rows only (x = month the forecast is made)
years = list(range(2019, 2027))
S.rows_axis(axB, [''] * len(years), top_pad=0.6)
S.row_labels(axB, [str(y) for y in years])
gaps = [(ym(2020, 3), ym(2020, 10)), (ym(2024, 4), ym(2024, 8)), (ym(2025, 7), ym(2025, 9))]
first = ym(2016, 3)
hb = 0.5
for i, Y in enumerate(years):
    axB.add_patch(Rectangle((first, i - hb / 2), ym(Y - 1, 12) - first, hb, color=S.LIGHT, linewidth=0, zorder=2))
    end = ym(2026, 8) if Y == 2026 else Y + 1
    axB.add_patch(Rectangle((Y, i - hb / 2), end - Y, hb, color=S.AQUA, linewidth=0, zorder=2))
    for a, b in gaps:
        if a < end:
            axB.add_patch(Rectangle((a, i - hb / 2 - 0.05), min(b, end) - a, hb + 0.1, color='white', linewidth=0, zorder=3))
axB.annotate('Test year', xy=(0, -0.95), xycoords=('axes fraction', 'data'), xytext=(-6, 0), textcoords='offset points', ha='right',
             va='center', fontweight='bold', color=S.INK, annotation_clip=False)
axB.set_xlim(2016, 2027.2)
axB.set_xticks(range(2016, 2028, 1))
axB.set_xticklabels([str(y) if y % 2 == 0 else '' for y in range(2016, 2028)])
axB.spines['bottom'].set_visible(True)
axB.grid(axis='x')
axB.set_axisbelow(True)
axB.set_xlabel('Month the forecast is made')
axB.legend([Patch(color=S.LIGHT), Patch(color=S.AQUA), Patch(facecolor='white', edgecolor=S.MUTED, linewidth=0.6)],
           ['Training rows', 'Test rows, scored', 'Months left out'],
           loc='lower left', bbox_to_anchor=(0, 1.0), ncol=3, handlelength=1.4)
axB.set_title('B  Testing forward in time', fontsize=S.BASE + 0.5, pad=18)
S.save(fig, 'fig4_1_design', STAMP)

# months scored, as a check on panel B (78 in Section 4.5)
n = 0
for Y in years:
    for m in range(1, 13):
        t = ym(Y, m)
        if (Y == 2026 and m > 7) or any(a <= t + 1e-9 < b for a, b in gaps):
            continue
        n += 1
print('months scored in panel B:', n)
print('written to', S.FIG)
