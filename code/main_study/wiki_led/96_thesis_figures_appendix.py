# 96. Figures D.1, D.2, E.1 and E.2 of the thesis appendices, redrawn on 14 Nov 2026 in the shared style (thesis_figstyle.py) from the
# numbers the 16 Oct figures plotted, so no value changes:
#   D.1 leading pipelines on three measures    data/db/benchmark/stage2_results/A2_table.csv (as benchmark/21_figures_tables.py, fig_board)
#   D.2 when the gain is larger or smaller      A2, B2, C2, D2_h1, E2_h1, H2_table.csv and segments.csv (as 21_figures_tables.py, fig_when)
#   E.1 a short and a lasting rise              figure_values_fig_lasting_rise_example.csv (written by benchmark/22_figures_data.py --rise)
#   E.2 effect by how long the rise lasted      figure_values_fig_effect_by_duration.csv (written by benchmark/24_figure_duration.py)
# The 16 Oct figures carried a title inside the image; the thesis captions say the same, so the titles are left out here.
# Output: paper/figures/figD1_pipelines, figD2_when_gain, figE1_rise_example, figE2_effect_by_duration _2026-11-14.png (300 dpi).
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/96_thesis_figures_appendix.py
import sys, pathlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D as DATA_DIR                             # noqa: E402
import thesis_figstyle as S                                  # noqa: E402
from thesis_figstyle import plt                              # noqa: E402
from matplotlib.lines import Line2D                          # noqa: E402

RES = pathlib.Path(DATA_DIR) / 'db' / 'benchmark' / 'stage2_results'
STAMP = '2026-11-14'
MS = 5.0


def table(name):
    return pd.read_csv(RES / name, index_col=0)


def dot(ax, x, y, lo, hi, col, filled=True):
    if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi):
        ax.plot([lo, hi], [y, y], color=col, linewidth=1.3, solid_capstyle='round', zorder=2)
    ax.plot([x], [y], marker='o', markersize=MS, markerfacecolor=col if filled else 'white', markeredgecolor=col,
            markeredgewidth=1.0 if filled else 1.2, linestyle='none', zorder=3)


def ref(ax, x, dotted=False):
    ax.axvline(x, color=S.INK2, linewidth=0.7, linestyle=(0, (1, 1.5)) if dotted else '-', zorder=1)


# ---------------------------------------------------------------- D.1 leading pipelines on three measures
BOARD = [('chronos2_cur', 'Chronos-2 + concept pages', 'pre'), ('chronos2_bk', 'Chronos-2 + book and author articles', 'pre'),
         ('chronos2_curdw', 'Chronos-2 + duration-weighted\nconcept pages', 'pre'), ('chronos2', 'Chronos-2, no interest', 'pre'),
         ('median_s2_all', 'Median of all 40 models', 'comb'), ('chronos', 'Chronos-Bolt', 'pre'),
         ('catchg_D', 'CatBoost on the change', 'chg'), ('lgbmchg_D', 'LightGBM on the change', 'chg'), ('ridgechg_D', 'Ridge on the change', 'chg'),
         ('catboost_D', 'CatBoost, level', 'other'), ('naive', 'Repeat last month', 'other'), ('revert6', 'Mean of last 6 months', 'other')]
COLF = {'pre': S.BLUE, 'chg': S.ORANGE, 'comb': S.AQUA, 'other': S.GRAY}
T = table('A2_table.csv')
fig, axs = S.figure(3.75, ncols=3, sharey=True, gridspec_kw={'width_ratios': [1.05, 1, 1]})
for a in axs:
    S.rows_axis(a, [''] * len(BOARD), top_pad=0.6)
axs[0].set_yticklabels([lab for _, lab, _ in BOARD], fontsize=S.BASE - 0.5, linespacing=1.0)
for k, (p, lab, fam) in enumerate(BOARD):
    r, c = T.loc[p], COLF[fam]
    if r.AvgRelMAE > 1.07:
        axs[0].annotate(f'{r.AvgRelMAE:.2f}, off scale', (1.058, k), ha='right', va='center', fontsize=S.BASE - 0.5, color=S.INK2)
    else:
        dot(axs[0], r.AvgRelMAE, k, r.ci_lo, r.ci_hi, c, bool(r.in_MCS_level) if pd.notna(r.in_MCS_level) else False)
    if pd.notna(r.rho):
        dot(axs[1], r.rho, k, r.rho_lo, r.rho_hi, c, bool(r.in_MCS_rise) if pd.notna(r.in_MCS_rise) else False)
    if pd.notna(r.AP):
        dot(axs[2], r.AP, k, r.AP_lo, r.AP_hi, c, bool(r.AP_tied_with_best) if pd.notna(r.AP_tied_with_best) else False)
ref(axs[0], 1)
axs[0].set_xlim(0.89, 1.06); axs[0].set_xticks([0.90, 0.95, 1.00, 1.05]); axs[0].set_xticklabels(['0.90', '0.95', '1.00', '1.05'])
axs[0].set_xlabel('Error relative to repeating\nlast month (below 1 is better)')
axs[0].set_title("Level of next month", fontsize=S.BASE + 0.5)
ref(axs[1], 0)
axs[1].set_xlim(-0.01, 0.38); axs[1].set_xticks([0, 0.1, 0.2, 0.3])
axs[1].set_xlabel('Rank correlation with\nthe actual change')
axs[1].set_title('Which themes will rise', fontsize=S.BASE + 0.5)
ref(axs[2], 0.0065, dotted=True)
axs[2].annotate('chance', (0.0065, len(BOARD) - 0.45), xytext=(3, 0), textcoords='offset points', fontsize=S.BASE - 1, color=S.INK2, va='center')
axs[2].set_xlim(-0.01, 0.38); axs[2].set_xticks([0, 0.1, 0.2, 0.3])
axs[2].set_xlabel('Average precision, rises\nof 30% or more')
axs[2].set_title('Rare surges', fontsize=S.BASE + 0.5)
for a in axs:
    a.spines['bottom'].set_visible(True)
hs = [Line2D([], [], marker='o', linestyle='none', markersize=MS, markerfacecolor=COLF[k], markeredgecolor=COLF[k], label=lab) for k, lab in
      (('pre', 'Pretrained forecaster'), ('chg', 'Trained on the change'), ('comb', 'Combination of models'), ('other', 'Level model or reference'))]
hs += [Line2D([], [], marker='o', linestyle='none', markersize=MS, markerfacecolor=S.INK2, markeredgecolor=S.INK2, label='Filled: in the set'),
       Line2D([], [], marker='o', linestyle='none', markersize=MS, markerfacecolor='white', markeredgecolor=S.INK2, markeredgewidth=1.2, label='Open: not in the set')]
fig.legend(handles=hs, loc='outside lower center', ncol=3)
S.save(fig, 'figD1_pipelines', STAMP)

# ---------------------------------------------------------------- D.2 when the gain over repeating last month is larger or smaller
fig = plt.figure(figsize=(S.W, 4.9))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.95], width_ratios=[1.0, 1.0])
axA, axB, axC = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
tabs = {1: table('A2_table.csv'), 2: table('B2_table.csv'), 3: table('C2_table.csv')}
names = [('chronos2_cur', 'Chronos-2 + concept pages', S.BLUE, '-'), ('chronos2', 'Chronos-2, no interest', S.BLUE, (0, (4, 2))),
         ('chronos', 'Chronos-Bolt', S.BLUE, (0, (1, 1.4))), ('median_s2_all', 'Median of all 40 models', S.AQUA, '-'),
         ('catchg_D', 'CatBoost on the change', S.ORANGE, '-')]
ends = []
for p, lab, c, ls in names:
    v = [tabs[h].loc[p, 'AvgRelMAE'] for h in (1, 2, 3)]
    axA.plot([1, 2, 3], v, color=c, linewidth=1.3, linestyle=ls, marker='o', markersize=3.6, markerfacecolor=c, markeredgecolor='white',
             markeredgewidth=0.5, label=lab)
    ends.append((v[-1], lab, c))
placed = []                                                 # direct labels at the line ends, spread to at least 0.012 apart
for v, lab, c in sorted(ends):
    yl = v if not placed else max(v, placed[-1] + 0.012)
    placed.append(yl)
    axA.plot([3.04, 3.16], [v, yl], color=S.MUTED, linewidth=0.5)
    axA.annotate(lab, (3.18, yl), va='center', ha='left', fontsize=S.BASE - 1, color=S.INK)
axA.axhline(1, color=S.INK2, linewidth=0.7)
axA.annotate('repeating last month', (1, 1), xytext=(0, 2), textcoords='offset points', fontsize=S.BASE - 1, color=S.INK2, va='bottom')
axA.set_xticks([1, 2, 3]); axA.set_xlim(0.85, 4.75)
axA.set_ylim(0.84, 1.02); axA.set_yticks([0.85, 0.90, 0.95, 1.00]); axA.set_yticklabels(['0.85', '0.90', '0.95', '1.00'])
axA.grid(axis='y'); axA.set_axisbelow(True)
axA.spines['left'].set_visible(False); axA.spines['bottom'].set_visible(True)
axA.tick_params(axis='y', length=0)
axA.set_xlabel('Months ahead')
axA.set_title('A  Forecast horizon', fontsize=S.BASE + 0.5)
axA.spines['bottom'].set_bounds(0.85, 3.15)
H = pd.read_csv(RES / 'H2_table.csv')
H = H[H.iloc[:, 0] == 'chronos2_cur']
D2, E2 = table('D2_h1_table.csv'), table('E2_h1_table.csv')
rowsb = [('LibriVox listening', E2.loc['chronos2_cur', 'AvgRelMAE'], E2.loc['chronos2_cur', 'ci_lo'], E2.loc['chronos2_cur', 'ci_hi'], None)]
for fmt, lvl, lab in (('print', 'middle', 'Printed, middle themes'), ('print', 'narrow', 'Printed, narrow themes'),
                      ('ebook', 'middle', 'Ebooks, middle themes'), ('ebook', 'narrow', 'Ebooks, narrow themes')):
    r = H[(H.format == fmt) & (H.level == lvl)].iloc[0]
    rowsb.append((lab, r.AvgRelMAE, r.ci_lo, r.ci_hi, None))
rowsb.append(('Seattle audiobooks', D2.loc['chronos2_cur', 'AvgRelMAE'], D2.loc['chronos2_cur', 'ci_lo'], D2.loc['chronos2_cur', 'ci_hi'],
              (D2.loc['median_s2_all', 'AvgRelMAE'], D2.loc['median_s2_all', 'ci_lo'], D2.loc['median_s2_all', 'ci_hi'])))
S.rows_axis(axB, [r[0] for r in rowsb], top_pad=0.6)
axB.tick_params(axis='y', labelsize=S.BASE - 0.5)
for i, (lab, v, lo, hi, extra) in enumerate(rowsb):
    dot(axB, v, i - (0.17 if extra else 0), lo, hi, S.BLUE)
    if extra:
        dot(axB, extra[0], i + 0.17, extra[1], extra[2], S.AQUA)
ref(axB, 1)
axB.set_xlim(0.78, 1.04); axB.set_xticks([0.80, 0.90, 1.00]); axB.set_xticklabels(['0.80', '0.90', '1.00'])
axB.spines['bottom'].set_visible(True)
axB.set_xlabel('Error relative to repeating last month')
axB.set_title('B  Library and format', fontsize=S.BASE + 0.5)
SG = pd.read_csv(RES / 'segments.csv', index_col=0)
segs = [('h1 quiet', 'Quiet months'), ('h1 after short rise', 'After a short rise'), ('h1 after lasting rise', 'After a lasting rise'),
        ('h1 surge months (outcome-defined)', 'Surge months*')]
labs = []
for i, (sg, lab) in enumerate(segs):
    for p, c, dy in (('chronos2_cur', S.BLUE, -0.17), ('median_s2_all', S.AQUA, 0.17)):
        r = SG[(SG.index == p) & (SG.segment == sg)].iloc[0]
        dot(axC, r.AvgRelMAE, i + dy, r.ci_lo, r.ci_hi, c)
    n = SG[(SG.index == 'naive') & (SG.segment == sg)].iloc[0].rows
    labs.append((lab, f'{int(n):,} forecasts'))
S.rows_axis(axC, [''] * len(segs), top_pad=0.6)
S.row_labels(axC, labs)
ref(axC, 1)
axC.set_xlim(0.5, 1.25); axC.set_xticks([0.6, 0.8, 1.0, 1.2]); axC.set_xticklabels(['0.6', '0.8', '1.0', '1.2'])
axC.spines['bottom'].set_visible(True)
axC.set_xlabel('Error relative to repeating last month (below 1 is better)')
axC.set_title('C  Kind of month', fontsize=S.BASE + 0.5)
axC.legend([Line2D([], [], marker='o', linestyle='none', markersize=MS, color=S.BLUE),
            Line2D([], [], marker='o', linestyle='none', markersize=MS, color=S.AQUA)],
           ['Chronos-2 + concept pages', 'Median of all 40 models'], loc='lower right', ncol=1)
S.save(fig, 'figD2_when_gain', STAMP)

# ---------------------------------------------------------------- E.1 a short and a lasting rise in Wikipedia interest
V = pd.read_csv(RES / 'figure_values_fig_lasting_rise_example.csv')
fig, axs = S.figure(3.2, nrows=2, sharex=True)
for ax, (panel, g) in zip(axs, sorted(V.groupby('panel'), key=lambda kv: kv[1].weeks_at_or_above_1_5_from_start.iloc[0])):
    g = g.sort_values('week_from_start')
    run = int(g.weeks_at_or_above_1_5_from_start.iloc[0])
    start = pd.Timestamp(g.start_week.iloc[0])
    ax.axvspan(-0.5, run - 0.5, color='#e3edfa', linewidth=0, zorder=0)
    ax.axhline(1.5, color=S.INK2, linewidth=0.8, linestyle=(0, (4, 2)), zorder=2)
    ax.axvline(0, color=S.INK2, linewidth=0.7, zorder=2)
    ax.plot(g.week_from_start, g.interest_over_normal, color=S.BLUE, linewidth=1.3, zorder=4)
    hi = g.interest_over_normal >= 1.5
    ax.plot(g.week_from_start[hi], g.interest_over_normal[hi], 'o', markersize=3.8, markerfacecolor=S.BLUE, markeredgecolor='white',
            markeredgewidth=0.5, zorder=5, linestyle='none')
    ax.plot(g.week_from_start[~hi], g.interest_over_normal[~hi], 'o', markersize=3.2, markerfacecolor='white', markeredgecolor=S.BLUE,
            markeredgewidth=0.9, zorder=5, linestyle='none')
    ax.set_ylim(0, 5.6); ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.set_xlim(-16.8, 16.8)
    ax.grid(axis='y'); ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0)
    ax.annotate('1.5 times normal', (-16.5, 1.5), xytext=(0, 2), textcoords='offset points', fontsize=S.BASE - 1, color=S.INK2, va='bottom')
    word = 'week' if run == 1 else 'weeks'
    what = f'stays at or above 1.5 for {run} {word}' if run >= 4 else f'falls back below 1.5 after {run} {word}'
    ax.annotate(f'Starts in the week of {start.day} {start:%B %Y};\n{what}', (run - 0.5, 4.6), xytext=(6, 0), textcoords='offset points',
                fontsize=S.BASE - 0.5, color=S.INK, va='center', ha='left')
    ax.set_title(('B  Lasting rise' if run >= 4 else 'A  Short rise'), fontsize=S.BASE + 0.5)
    ax.set_ylabel('Interest, times normal', fontsize=S.BASE - 0.5, color=S.INK2)
axs[1].set_xticks(range(-16, 17, 4))
axs[1].set_xticklabels([f'−{abs(x)}' if x < 0 else str(x) for x in range(-16, 17, 4)])
axs[1].spines['bottom'].set_visible(True)
axs[1].set_xlabel('Weeks from the start of the rise')
S.save(fig, 'figE1_rise_example', STAMP)

# ---------------------------------------------------------------- E.2 effect on borrowing by how long the rise lasted
E = pd.read_csv(RES / 'figure_values_fig_effect_by_duration.csv')
LABS = ['1 to 2', '3', '4 to 5', '6 to 8', '9 or more']
fig, ax = S.figure(2.7)
cols = {'narrow': (S.BLUE, 'o', -0.13, 'Narrow themes'), 'middle': (S.ORANGE, 's', 0.13, 'Middle themes')}
for lv, (c, mk, dx, lab) in cols.items():
    d = E[E.level == lv].set_index('weeks').loc[LABS]
    for k, (_, r) in enumerate(d.iterrows()):
        ax.plot([k + dx, k + dx], [r.lo, r.hi], color=c, linewidth=1.3, solid_capstyle='round', zorder=2)
        ax.plot([k + dx], [r['mean']], marker=mk, markersize=MS, color=c, markeredgecolor='white', markeredgewidth=0, linestyle='none', zorder=3)
ax.axhline(0, color=S.INK2, linewidth=0.7)
ax.axvline(1.5, color=S.INK2, linewidth=0.7, linestyle=(0, (4, 2)))
ax.annotate('Lasting rise: 4 weeks or more', (1.5, 0.44), xytext=(5, 0), textcoords='offset points', fontsize=S.BASE - 0.5, color=S.INK2, va='top')
cnt = {(r.level, r.weeks): int(r.tests) for r in E.itertuples()}
ax.set_xticks(range(len(LABS)))
ax.set_xticklabels([f'{l}\n{cnt[("narrow", l)]} | {cnt[("middle", l)]}' for l in LABS])
ax.tick_params(axis='x', length=0)
ax.set_xlabel('Weeks the rise stayed at 1.5 times normal or more (tests for narrow | middle themes)')
ax.set_ylabel('Effect on borrowing, months 0 to 2\n(log share)', fontsize=S.BASE - 0.5, color=S.INK2)
ax.set_xlim(-0.55, len(LABS) - 0.45)
ax.set_ylim(-0.2, 0.46)
ax.grid(axis='y'); ax.set_axisbelow(True)
ax.tick_params(axis='y', length=0)
ax.legend([Line2D([], [], marker=cols[k][1], linestyle='none', markersize=MS, color=cols[k][0]) for k in cols], [cols[k][3] for k in cols],
          loc='upper left')
S.save(fig, 'figE2_effect_by_duration', STAMP)
print('written to', S.FIG)
