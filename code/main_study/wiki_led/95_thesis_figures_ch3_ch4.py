# 95. Figures 3.1 (data over time) and 4.1 (design) of the rewritten thesis (paper/Thesis_Draft_2026-11-06_1118.md).
# Dates are those stated in Chapter 3: Seattle loans April 2005 to August 2026; Wikipedia user views July 2015 to September 2026;
# New York Times lists June 2008 to October 2026; LibriVox views January 2017 to August 2026; months scored January 2019 to July 2026
# (predicted months to August 2026); months left out 2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08; forecasts fixed in advance for
# September to November 2026. Same palette and type as 94_thesis_figures_ch5.py. Output: paper/figures/fig3_1_*, fig4_1_* (300 dpi).
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/95_thesis_figures_ch3_ch4.py
import sys, pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR                             # noqa: E402

FIG = pathlib.Path(DATA_DIR).parent / 'paper' / 'figures'
STAMP = '2026-11-06'
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE, AQUA, GRAY = '#2a78d6', '#eb6834', '#1baf7a', '#8a8985'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': INK2, 'xtick.color': INK2, 'ytick.color': INK,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
                     'savefig.dpi': 300, 'savefig.bbox': 'tight'})


def ym(y, m):
    return y + (m - 1) / 12


# Figure 3.1: the years each source covers
rows = [
    ('Seattle library loans', ym(2005, 4), ym(2026, 9), BLUE),
    ('New York Times bestseller lists', ym(2008, 6), ym(2026, 11), BLUE),
    ('Wikipedia page views', ym(2015, 7), ym(2026, 10), BLUE),
    ('LibriVox listening', ym(2017, 1), ym(2027, 0) - 4 / 12, BLUE),
    ('Months scored (backtest)', ym(2019, 1), ym(2026, 9), AQUA),
]
fig, ax = plt.subplots(figsize=(6.3, 2.6))
for i, (lab, a, b, col) in enumerate(rows):
    ax.add_patch(Rectangle((a, i - 0.28), b - a, 0.56, color=col, linewidth=0))
for a, b in ((ym(2020, 4), ym(2020, 10)), (ym(2024, 5), ym(2024, 8)), (ym(2025, 8), ym(2025, 9))):
    for i in (0, 4):                                        # only library months are left out
        ax.add_patch(Rectangle((a, i - 0.28), b - a, 0.56, facecolor='white', edgecolor=GRAY, hatch='////', linewidth=0, zorder=4))
ax.add_patch(Rectangle((ym(2026, 9), 4 - 0.28), 3 / 12, 0.56, facecolor='white', edgecolor=ORANGE, linewidth=1.5, zorder=5))
ax.annotate('forecasts fixed\nin advance', (ym(2026, 12), 4), xytext=(6, 0), textcoords='offset points', va='center', fontsize=8, color=INK)
ax.annotate('months left out', (ym(2020, 6), -0.3), xytext=(ym(2016, 6), -0.72), ha='center', va='center', fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle='-', color=INK2, linewidth=0.8))
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows])
ax.set_ylim(len(rows) - 0.4, -1.0)
ax.tick_params(axis='y', length=0)
ax.set_xlim(2005, 2028.6)
ax.set_xticks(range(2005, 2028, 3))
ax.grid(axis='x', color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
fig.savefig(FIG / f'fig3_1_data_over_time_{STAMP}.png')
plt.close(fig)

# Figure 4.1: the design
fig, ax = plt.subplots(figsize=(7.2, 3.9))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis('off')


def box(x, y, w, h, text, edge=INK2, bold=False, size=7.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.2', facecolor='white', edgecolor=edge, linewidth=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size, color=INK, fontweight='bold' if bold else 'normal',
            linespacing=1.3)


def arrow(x0, y0, x1, y1, col=INK2):
    ax.annotate('', (x1, y1), (x0, y0), arrowprops=dict(arrowstyle='-|>', color=col, linewidth=1.1, shrinkA=0, shrinkB=0))


ax.text(50, 59.5, 'Each test year from 2019 to 2026: fit on earlier years only, then predict that year', ha='center', fontsize=8, color=INK2)
box(1, 37, 24, 13, 'Wikipedia page views\n(book, author, theme\nand linked pages)', edge=BLUE)
box(1, 12, 24, 13, 'Library loans\n(each work\'s history,\ncalendar month)', edge=ORANGE)
models = [(48, 'Wikipedia alone', BLUE, True), (37, 'Library and Wikipedia', AQUA, True), (26, 'Library record', ORANGE, True),
          (15, 'Persistence rule', '#eda100', False), (4, 'No information', GRAY, False)]
for y, lab, col, bold in models:
    box(31, y, 27, 6.5, lab, edge=col, bold=bold)
arrow(25, 46, 31, 51.2, BLUE)
arrow(25, 41, 31, 40.2, BLUE)
arrow(25, 22, 31, 40.2, ORANGE)
arrow(25, 19, 31, 29.2, ORANGE)
arrow(25, 16, 31, 18.2, ORANGE)
box(64, 24, 18, 19, 'Forecasts\n(next month;\nnew books\' first\nsix months;\n3 to 12 months)')
for y, *_ in models:
    arrow(58, y + 3.2, 64, 33.5)
box(85, 24, 14.5, 19, 'Scores\n(rank\ncorrelation,\ntop-20\nhit rate,\nsurges,\nloan error)', size=7.2)
arrow(82, 33.5, 85, 33.5)
box(64, 5, 35.5, 9, 'Actual loans in the\npredicted months, never an input', edge=GRAY, size=7.2)
arrow(92.5, 14, 92.5, 24)
fig.savefig(FIG / f'fig4_1_design_{STAMP}.png')
plt.close(fig)
print('written to', FIG)
