# Thesis figures made from the result tables of the benchmark (data/db/benchmark/stage2_results/), 16 Oct 2026.
#   data      timeline of the data sources against the forecast months
#   board     scoreboard of the leading pipelines on three measures
#   organize  what each behavior input changes, per model (paired error change, matrix)
#   learned   themes built from subject headings against themes learned from catalogue descriptions
#   when      error by horizon, by library and format, and by kind of month
# Text size: the smallest text is 13.5 pt on an 11-inch canvas, which is 8 pt when a figure is shown 6.5 inches wide (the width of a thesis page).
#   ../../../.venv/bin/python 21_figures_tables.py [data board organize learned when] [--stamp YYYY-MM-DD_HHMM]
import sys
from _thesis_style import *
from matplotlib.patches import Rectangle, Patch
from matplotlib.gridspec import GridSpec

ST_STAMP = sys.argv[sys.argv.index('--stamp') + 1] if '--stamp' in sys.argv else STAMP
args = [a for a in sys.argv[1:] if not a.startswith('--') and a != ST_STAMP]
which = set(args) or {'data', 'board', 'organize', 'learned', 'when'}
setup()
FS, FS_P, FS_T = 13.5, 15.0, 16.5          # smallest text, panel titles, figure title
plt.rcParams.update({'font.size': FS})
LW, MS = 2.4, 9.5


def table(name):
    return pd.read_csv(RES / name, index_col=0)


def clean2(ax, grid='x'):
    clean(ax, grid)
    ax.tick_params(axis='both', colors=INK2, labelsize=FS, length=0)


def dot2(ax, x, y, lo=None, hi=None, color=BLUE, filled=True):
    if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi):
        ax.plot([lo, hi], [y, y], color=color, lw=LW, solid_capstyle='round', zorder=2)
    ax.plot([x], [y], marker='o', ms=MS, mfc=color if filled else SURFACE, mec=color, mew=2.0, zorder=3, ls='none')


def title(fig, text):
    fig.suptitle(text, fontsize=FS_T, x=0.012, ha='left', fontweight='bold', color=INK)


# ---------------------------------------------------------------------------------------------------------- data timeline
def fig_data():
    rows = [  # label, start, end, role, note
        ('Seattle library checkouts', 2005.0, 2026.6, 'out', 'main outcome (2016 on used)'),
        ('LibriVox listening', 2017.0, 2026.6, 'out2', 'audiobook outcome'),
        ('Wikipedia page views', 2015.5, 2026.75, 'beh', 'main behavior input'),
        ('GDELT news and tone', 2017.0, 2021.4, 'beh', 'second input'),
        ('Tweets, talk-page edits', 2015.0, 2020.9, 'thin', 'too thin to use'),
        ('Brisbane library loans', 2015.0, 2025.9, 'thin', 'too thin to use'),
    ]
    fill = {'out': BLUE, 'out2': BLUE, 'beh': AQUA, 'thin': '#d9d9d5'}
    edge = {'out': BLUE, 'out2': BLUE, 'beh': AQUA, 'thin': GRAY}
    fig, ax = plt.subplots(figsize=(11, 5.0))
    n = len(rows)
    ax.axvspan(2019.0, 2026.67, color=PALE_BLUE, zorder=0)
    ax.text(2022.8, n - 0.15, 'forecast months\n2019 to 2026', fontsize=FS, color=BLUE, va='bottom', ha='center', linespacing=1.15)
    ax.axvline(2026.67, color=INK2, lw=1.2, ls=(0, (3, 2)), zorder=1)
    ax.text(2026.95, n - 0.15, 'final test:\nSeptember\n2026 onward', fontsize=FS, color=INK2, va='bottom', ha='left', linespacing=1.15)
    for i, (lab, a_, b_, role, note) in enumerate(rows):
        y = n - 1 - i
        ax.add_patch(Rectangle((a_, y - 0.3), b_ - a_, 0.6, facecolor=fill[role], edgecolor=edge[role], lw=1.6, zorder=2))
        ax.text(2004.4, y, lab, ha='right', va='center', fontsize=FS, color=INK)
        if role in ('out', 'out2', 'beh') and (b_ - a_) > 8:
            ax.text(a_ + 0.3, y, note, ha='left', va='center', fontsize=FS, color=SURFACE, zorder=4)
        elif role == 'thin' and (b_ - a_) > 8:
            ax.text(a_ + 0.3, y, note, ha='left', va='center', fontsize=FS, color=INK, zorder=4)
        else:
            ax.text(b_ + 0.3, y, note, ha='left', va='center', fontsize=FS, color=INK2)
    ax.set_xlim(2005, 2031.8)
    ax.set_ylim(-0.6, n + 1.4)
    ax.set_xticks(range(2005, 2027, 4))
    ax.set_yticks([])
    clean2(ax, 'x')
    fig.subplots_adjust(left=0.30, right=0.99, top=0.9, bottom=0.2)
    title(fig, 'What data cover which years')
    h = [Patch(fc=BLUE, ec=BLUE, label='demand (what is forecast)'), Patch(fc=AQUA, ec=AQUA, label='behavior used as input'),
         Patch(fc='#d9d9d5', ec=GRAY, label='too thin to use')]
    fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, fontsize=FS, labelcolor=INK2, bbox_to_anchor=(0.55, 0.0), columnspacing=1.4, handlelength=1.4)
    return save(fig, 'fig_data_coverage', ST_STAMP)


# ---------------------------------------------------------------------------------------------------------- scoreboard
BOARD = [('chronos2_cur', 'Chronos-2 + concept pages', 'pre'), ('chronos2_bk', 'Chronos-2 + book and\nauthor articles', 'pre'), ('chronos2_curdw', 'Chronos-2 + duration-\nweighted concept pages', 'pre'),
         ('chronos2', 'Chronos-2, no interest', 'pre'), ('median_s2_all', 'Median of all\n40 models', 'comb'), ('chronos', 'Chronos-Bolt', 'pre'),
         ('catchg_D', 'CatBoost on the change', 'chg'), ('lgbmchg_D', 'LightGBM on the change', 'chg'), ('ridgechg_D', 'Ridge on the change', 'chg'),
         ('catboost_D', 'CatBoost, level', 'other'), ('naive', 'Repeat last month', 'other'), ('revert6', 'Mean of last 6 months', 'other')]
COLF = {'pre': BLUE, 'chg': ORANGE, 'comb': AQUA, 'other': GRAY}


def fig_board():
    T = table('A2_table.csv')
    n = len(BOARD)
    y = np.arange(n)[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(11, 8.0), sharey=True, gridspec_kw={'width_ratios': [1.05, 1, 1], 'wspace': 0.12})
    for k, (p, lab, fam) in enumerate(BOARD):
        r = T.loc[p]
        c = COLF[fam]
        if r.AvgRelMAE > 1.07:
            axs[0].annotate('1.31 →', (1.052, y[k]), ha='right', va='center', fontsize=FS, color=INK2)
        else:
            dot2(axs[0], r.AvgRelMAE, y[k], r.ci_lo, r.ci_hi, c, bool(r.in_MCS_level) if pd.notna(r.in_MCS_level) else False)
        if pd.notna(r.rho):
            dot2(axs[1], r.rho, y[k], r.rho_lo, r.rho_hi, c, bool(r.in_MCS_rise) if pd.notna(r.in_MCS_rise) else False)
        if pd.notna(r.AP):
            dot2(axs[2], r.AP, y[k], r.AP_lo, r.AP_hi, c, bool(r.AP_tied_with_best) if pd.notna(r.AP_tied_with_best) else False)
    axs[0].axvline(1, color=INK2, lw=1.2)
    axs[0].set_xlim(0.89, 1.06); axs[0].set_xticks([0.90, 0.95, 1.00, 1.05])
    axs[0].set_xlabel("Error relative to\nrepeating last month\n(below 1 is better)", fontsize=FS)
    axs[0].set_title("Level of next\nmonth's borrowing", fontsize=FS_P, loc='left', fontweight='bold')
    axs[1].axvline(0, color=INK2, lw=1.2)
    axs[1].set_xlim(0.0, 0.38); axs[1].set_xticks([0, 0.1, 0.2, 0.3])
    axs[1].set_xlabel("Rank correlation of\nforecast and actual\nchange across themes", fontsize=FS)
    axs[1].set_title("Which themes\nwill rise", fontsize=FS_P, loc='left', fontweight='bold')
    axs[2].axvline(0.0065, color=INK2, lw=1.2, ls=(0, (1, 2)))
    axs[2].text(0.014, -0.75, 'chance', fontsize=FS, color=INK2, va='center')
    axs[2].set_xlim(0.0, 0.38); axs[2].set_xticks([0, 0.1, 0.2, 0.3])
    axs[2].set_xlabel("Average precision of\nflagging themes about\nto rise by 30% or more", fontsize=FS)
    axs[2].set_title("Rare surges", fontsize=FS_P, loc='left', fontweight='bold')
    for a in axs:
        clean2(a, 'x')
    axs[0].set_yticks(y)
    axs[0].set_yticklabels([lab for _, lab, _ in BOARD], fontsize=FS, color=INK, linespacing=1.1)
    axs[0].set_ylim(-1.1, n - 0.4)
    h = [Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=COLF[k], mec=COLF[k], label=lab) for k, lab in
         (('pre', 'pretrained forecaster'), ('chg', 'trained on the change'), ('comb', 'combination of models'), ('other', 'level model or reference'))]
    h += [Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=INK2, mec=INK2, label='filled: in the 90% confidence set'),
          Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=SURFACE, mec=INK2, mew=2, label='open: not in the set')]
    fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, fontsize=FS, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0), columnspacing=1.6)
    title(fig, 'Printed books and ebooks, one month ahead: leading pipelines')
    fig.subplots_adjust(left=0.27, right=0.985, top=0.835, bottom=0.265)
    return save(fig, 'fig_pipeline_scoreboard', ST_STAMP)


# ---------------------------------------------------------------------------------------------------------- organizing matrix
def fig_organize():
    P = pd.read_csv(RES / 'A2_pairs.csv')
    P = P[P.kind == 'behavior against no behavior'].copy()
    P['model'] = P.base.str.split('_').str[0]
    cols = [('chronos2', 'Chronos-2\n(pretrained)'), ('catchg', 'CatBoost\non change'), ('lgbmchg', 'LightGBM\non change'), ('ridgechg', 'Ridge\non change')]
    rows = [('Representing the signal (concept pages)', None),
            ('Volume of the pages', 'DVcur'), ('All ten features', 'DW'), ('Ten features and lasting-rise state', 'DWS'), ('Duration-weighted volume', 'DVcurdw'),
            ('Routing behavior into themes (volume)', None),
            ("Books' and authors' articles", 'DVbk'), ('Top pages, read in context', 'DVnli'), ('Top pages, by embedding', 'DVtop'), ('Weighted by past demand', 'DVdem')]
    key = {'DVcur': 'chronos2_cur', 'DVcurdw': 'chronos2_curdw', 'DVbk': 'chronos2_bk', 'DVnli': 'chronos2_nli', 'DVtop': 'chronos2_top'}
    fig, ax = plt.subplots(figsize=(11, 7.2))
    nrow = len(rows)
    xl = 4.7
    ax.set_xlim(0, xl + 4 * 1.5)
    ax.set_ylim(-1.35, nrow + 0.15)
    ax.invert_yaxis()
    ax.axis('off')
    for j, (m, name) in enumerate(cols):
        ax.text(xl + j * 1.5 + 0.75, -0.2, name, ha='center', va='bottom', fontsize=FS, fontweight='bold', color=INK, linespacing=1.15)
    for i, (lab, code) in enumerate(rows):
        if code is None:
            ax.text(0.0, i + 0.62, lab, ha='left', va='center', fontsize=FS, fontweight='bold', color=INK2)
            ax.plot([0, xl + 6.0], [i + 1.0, i + 1.0], color=GRID, lw=1.0)
            continue
        ax.text(0.2, i + 0.5, lab, ha='left', va='center', fontsize=FS, color=INK)
        for j, (m, name) in enumerate(cols):
            other = key.get(code) if m == 'chronos2' else f'{m}_{code}'
            r = P[(P.model == m) & (P.other == other)]
            x = xl + j * 1.5
            if len(r) == 0:
                ax.add_patch(Rectangle((x + 0.05, i + 0.07), 1.4, 0.86, facecolor=PALE_GRAY, edgecolor=GRID, lw=0.8, hatch='////', zorder=1))
                ax.text(x + 0.75, i + 0.5, 'not run', ha='center', va='center', fontsize=FS, color=MUTED)
                continue
            r = r.iloc[0]
            pt, lo, hi = (r.mae_ratio - 1) * 100, (r.mae_lo - 1) * 100, (r.mae_hi - 1) * 100
            fc, tc = (BLUE, SURFACE) if hi < 0 else ((RED, SURFACE) if lo > 0 else ('#e9e9e6', INK))
            ax.add_patch(Rectangle((x + 0.05, i + 0.07), 1.4, 0.86, facecolor=fc, edgecolor=SURFACE, lw=0, zorder=2))
            ax.text(x + 0.75, i + 0.5, f'{pt:+.1f}%'.replace('-', '−'), ha='center', va='center', fontsize=FS + 1, color=tc, fontweight='bold', zorder=3)
    h = [Patch(fc=BLUE, label='more accurate'), Patch(fc='#e9e9e6', ec=GRID, label='no clear difference'), Patch(fc=RED, label='less accurate'), Patch(fc=PALE_GRAY, ec=GRID, hatch='////', label='not run')]
    fig.legend(handles=h, loc='lower center', ncol=4, frameon=False, fontsize=FS, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0), columnspacing=1.6, handlelength=1.4)
    title(fig, "Change in a model's error when a behavior input is added")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.075)
    return save(fig, 'fig_organizing_effects', ST_STAMP)


# ---------------------------------------------------------------------------------------------------------- built vs learned themes
def fig_learned():
    order = [('chronos2', 'Chronos-2'), ('chronos', 'Chronos-Bolt'), ('median_s2_demand', 'Median of models'), ('lgbmchg_D', 'LightGBM, change'), ('catchg_D', 'CatBoost, change'), ('ridgechg_D', 'Ridge, change')]
    fig, axs = plt.subplots(1, 2, figsize=(11, 6.0), sharey=True, gridspec_kw={'wspace': 0.1})
    for ax, level, ttl in zip(axs, ('middle', 'narrow'), ('Middle themes (86)', 'Narrow themes (242)')):
        A = table(f'learned_subject-heading_print_{level}.csv')
        B = table(f'learned_learned_print_{level}.csv')
        for k, (p, lab) in enumerate(order):
            y = len(order) - 1 - k
            for D, c, dy in ((A, BLUE, 0.16), (B, ORANGE, -0.16)):
                dot2(ax, D.loc[p, 'AvgRelMAE'], y + dy, D.loc[p, 'ci_lo'], D.loc[p, 'ci_hi'], c, True)
        ax.axvline(1, color=INK2, lw=1.2)
        ax.set_xlim(0.86, 1.04)
        ax.set_xticks([0.90, 0.95, 1.00])
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([lab for _, lab in order][::-1], fontsize=FS, color=INK)
        ax.set_ylim(-0.6, len(order) - 0.4)
        ax.set_title(ttl, fontsize=FS_P, loc='left', fontweight='bold')
        ax.set_xlabel('Error relative to repeating\nlast month (below 1 is better)', fontsize=FS)
        clean2(ax, 'x')
    h = [Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=BLUE, mec=BLUE, label='built from subject headings'),
         Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=ORANGE, mec=ORANGE, label='learned from catalogue descriptions')]
    fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, fontsize=FS, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0), columnspacing=2.0)
    title(fig, 'Printed books and ebooks, borrowing history only: two sets of themes')
    fig.subplots_adjust(left=0.2, right=0.985, top=0.87, bottom=0.25)
    return save(fig, 'fig_learned_vs_built', ST_STAMP)


# ---------------------------------------------------------------------------------------------------------- when
def fig_when():
    fig = plt.figure(figsize=(11, 8.6))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.92], width_ratios=[1.2, 1.0], hspace=0.62, wspace=0.78)
    axA, axB, axC = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])

    def sub(ax, txt, dy=1.02):
        ax.text(0, dy, txt, transform=ax.transAxes, fontsize=FS, color=MUTED, va='bottom', ha='left')
    # (A) horizon, printed books and ebooks
    tabs = {1: table('A2_table.csv'), 2: table('B2_table.csv'), 3: table('C2_table.csv')}
    names = {'chronos2_cur': ('Chronos-2 + concept pages', BLUE, '-'), 'chronos2': ('Chronos-2, no interest', BLUE, (0, (5, 2))), 'chronos': ('Chronos-Bolt', BLUE, (0, (1, 1.5))),
             'median_s2_all': ('Median of all 40', AQUA, '-'), 'catchg_D': ('CatBoost, change', ORANGE, '-')}
    ends = []
    for p, (lab, c, ls) in names.items():
        v = [tabs[h].loc[p, 'AvgRelMAE'] for h in (1, 2, 3)]
        axA.plot([1, 2, 3], v, color=c, lw=LW, ls=ls, marker='o', ms=MS - 2, mfc=c, mec=SURFACE, mew=1.2)
        ends.append((v[-1], lab))
    ends.sort()
    ly = []
    for v, lab in ends:
        t = v if not ly else max(v, ly[-1] + 0.024)
        ly.append(t)
        axA.annotate(lab, (3, v), xytext=(3.25, t), fontsize=FS, va='center', color=INK2, arrowprops=dict(arrowstyle='-', color=GRID, lw=1.0, shrinkA=0, shrinkB=12))
    axA.axhline(1, color=INK2, lw=1.2)
    axA.text(1.0, 1.006, 'repeating last month', fontsize=FS, color=INK2, va='bottom', ha='left')
    axA.set_xticks([1, 2, 3]); axA.set_xticklabels(['1', '2', '3'])
    axA.set_xlim(0.85, 5.9)
    axA.set_ylim(0.82, 1.04)
    axA.set_yticks([0.85, 0.90, 0.95, 1.00])
    axA.set_xlabel('Forecast horizon (months ahead)', fontsize=FS)
    axA.set_ylabel('Error relative to repeating\nlast month', fontsize=FS)
    axA.set_title('A. Forecast horizon', fontsize=FS_P, loc='left', fontweight='bold', pad=26)
    sub(axA, 'printed books and ebooks')
    clean2(axA, 'y')
    # (B) by library and format
    H = pd.read_csv(RES / 'H2_table.csv')
    H = H[H.iloc[:, 0] == 'chronos2_cur']
    D = table('D2_h1_table.csv'); E = table('E2_h1_table.csv')
    rowsb = [('LibriVox listening', E.loc['chronos2_cur', 'AvgRelMAE'], E.loc['chronos2_cur', 'ci_lo'], E.loc['chronos2_cur', 'ci_hi'], None)]
    for fmt, lvl, lab in (('print', 'middle', 'Printed, middle'), ('print', 'narrow', 'Printed, narrow'), ('ebook', 'middle', 'Ebooks, middle'), ('ebook', 'narrow', 'Ebooks, narrow')):
        r = H[(H.format == fmt) & (H.level == lvl)].iloc[0]
        rowsb.append((lab, r.AvgRelMAE, r.ci_lo, r.ci_hi, None))
    rowsb.append(('Seattle audiobooks', D.loc['chronos2_cur', 'AvgRelMAE'], D.loc['chronos2_cur', 'ci_lo'], D.loc['chronos2_cur', 'ci_hi'],
                  (D.loc['median_s2_all', 'AvgRelMAE'], D.loc['median_s2_all', 'ci_lo'], D.loc['median_s2_all', 'ci_hi'])))
    n = len(rowsb)
    for i, (lab, v, lo, hi, extra) in enumerate(rowsb):
        y = n - 1 - i
        dot2(axB, v, y + (0.16 if extra else 0), lo, hi, BLUE, True)
        if extra:
            dot2(axB, extra[0], y - 0.16, extra[1], extra[2], AQUA, True)
    axB.axvline(1, color=INK2, lw=1.2)
    axB.set_yticks(range(n)); axB.set_yticklabels([r[0] for r in rowsb][::-1], fontsize=FS, color=INK)
    axB.set_ylim(-0.6, n - 0.4)
    axB.set_xlim(0.78, 1.04); axB.set_xticks([0.80, 0.90, 1.00])
    axB.set_xlabel('Error relative to repeating\nlast month', fontsize=FS)
    axB.set_title('B. Library and format', fontsize=FS_P, loc='left', fontweight='bold', pad=26)
    sub(axB, 'one month ahead')
    clean2(axB, 'x')
    # (C) by kind of month
    S = pd.read_csv(RES / 'segments.csv', index_col=0)
    segs = [('h1 quiet', 'Quiet months'), ('h1 after short rise', 'After a short rise'), ('h1 after lasting rise', 'After a lasting rise'), ('h1 surge months (outcome-defined)', 'Surge months*')]
    ylabs = []
    for i, (sg, lab) in enumerate(segs):
        y = len(segs) - 1 - i
        for p, c, dy in (('chronos2_cur', BLUE, 0.16), ('median_s2_all', AQUA, -0.16)):
            r = S[(S.index == p) & (S.segment == sg)].iloc[0]
            dot2(axC, r.AvgRelMAE, y + dy, r.ci_lo, r.ci_hi, c, True)
        r = S[(S.index == 'naive') & (S.segment == sg)].iloc[0]
        ylabs.append(f'{lab}\n{int(r.rows):,} forecasts')
    axC.axvline(1, color=INK2, lw=1.2)
    axC.set_yticks(range(len(segs))); axC.set_yticklabels(ylabs[::-1], fontsize=FS, color=INK, linespacing=1.1)
    axC.set_ylim(-0.6, len(segs) - 0.4)
    axC.set_xlim(0.5, 1.25); axC.set_xticks([0.6, 0.8, 1.0, 1.2])
    axC.set_xlabel('Error relative to repeating last month (below 1 is better)', fontsize=FS)
    axC.set_title('C. Kind of month', fontsize=FS_P, loc='left', fontweight='bold', pad=26)
    sub(axC, 'printed books and ebooks, one month ahead; * months picked by the outcome')
    clean2(axC, 'x')
    h = [Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=BLUE, mec=BLUE, label='Chronos-2 + concept pages'),
         Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=AQUA, mec=AQUA, label='Median of all 40 models')]
    fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, fontsize=FS, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0), columnspacing=2.0)
    title(fig, 'When the gain over repeating last month is larger or smaller')
    fig.subplots_adjust(left=0.215, right=0.985, top=0.865, bottom=0.115)
    return save(fig, 'fig_when_gain', ST_STAMP)


for name, f in (('data', fig_data), ('board', fig_board), ('organize', fig_organize), ('learned', fig_learned), ('when', fig_when)):
    if name in which:
        f()
