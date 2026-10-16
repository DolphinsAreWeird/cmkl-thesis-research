# Method benchmark, stage 2: figures from the result tables of 03_evaluate.py --stage2 (data/db/benchmark/stage2_results/).
#   fig A: every leading pipeline on the three questions (level error, which themes rise, rare surges), one row per pipeline, same order in the three panels
#   fig B: what organizing behavior changes (paired error change, model held fixed) and how the leaders change with the horizon
# Colours: three categorical slots of the reference palette (checked with the dataviz validator, light mode, all pairs) plus gray for context; filled marks = in the
# 90% confidence set (or not distinguishable from the best), open = not.
#   ../../../.venv/bin/python 16_figure_stage2.py [--table A2] [--stamp YYYY-MM-DD_HHMM]
import sys, pathlib, argparse, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import _settings as ST

RES = ST.DB / 'benchmark' / 'stage2_results'
FIGS = ST.ROOT / 'paper' / 'figures'
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8a85', '#e4e3df', '#ffffff'
BLUE, ORANGE, AQUA, GRAY, RED = '#2a78d6', '#eb6834', '#1baf7a', '#9a9993', '#e34948'

FSET = {'D': 'borrowing history only', 'DW': '+ Wikipedia (hand-checked pages)', 'DWS': '+ Wikipedia + lasting rises', 'DVcur': '+ Wikipedia volume', 'DVtop': '+ top pages (embedding)',
        'DVnli': '+ top pages (context-reading)', 'DVbk': '+ book and author articles', 'DVcurdw': '+ Wikipedia volume, duration-weighted', 'DVdem': '+ demand-aligned articles'}
MODEL = {'ridge': 'Ridge, level', 'catboost': 'CatBoost, level', 'lightgbm': 'LightGBM, level', 'ridgechg': 'Ridge on the change', 'lgbmchg': 'LightGBM on the change', 'catchg': 'CatBoost on the change'}
SPECIAL = {'naive': 'Repeat last month', 'seasonal_naive': 'Seasonal repeat', 'revert6': 'Mean of last 6 months', 'chronos': 'Chronos-Bolt (pretrained)', 'chronos2': 'Chronos-2 (pretrained)',
           'chronos2_cur': 'Chronos-2 + Wikipedia (hand-checked pages)', 'chronos2_curdw': 'Chronos-2 + Wikipedia, duration-weighted', 'chronos2_bk': 'Chronos-2 + book and author articles',
           'chronos2_top': 'Chronos-2 + top pages (embedding)', 'chronos2_nli': 'Chronos-2 + top pages (context-reading)', 'median_all': 'Median of 9 single models',
           'median_s2_all': 'Median of all learned models', 'median_s2_demand': 'Median, models without behavior', 'median_s2_behavior': 'Median, models with Wikipedia',
           'avg_ridge_cat_D': 'Mean of ridge and CatBoost', 'avg_ridge_cat_DW': 'Mean of ridge and CatBoost + Wikipedia', 'avg_three_DW': 'Mean of three models + Wikipedia',
           'avg_naive_ridge_D': 'Mean of repeat and ridge', 'invmae_all': 'Weighted by recent accuracy'}


def pretty(p):
    if p in SPECIAL:
        return SPECIAL[p]
    m, _, fs = p.partition('_')
    return (MODEL.get(m, m) + ('' if fs in ('D', '') else ' ' + FSET.get(fs, fs))).replace('  ', ' ') if m in MODEL else p


def family(p):
    if p.startswith('chronos'):
        return 'pre'
    if p.startswith(('ridgechg', 'lgbmchg', 'catchg')):
        return 'chg'
    if p.startswith(('median', 'avg_', 'invmae')):
        return 'comb'
    return 'other'


COL = {'pre': BLUE, 'chg': ORANGE, 'comb': AQUA, 'other': GRAY}
FAMNAME = {'pre': 'pretrained forecaster', 'chg': 'trained on the change', 'comb': 'combination of models', 'other': 'level models and references'}


def style(ax):
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(axis='both', colors=INK2, labelsize=8, length=0)
    ax.grid(axis='x', color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURFACE)


def dots(ax, y, x, lo, hi, filled, colors):
    for yi, xi, l, h, f, c in zip(y, x, lo, hi, filled, colors):
        if not np.isfinite(xi):
            continue
        if np.isfinite(l) and np.isfinite(h):
            ax.plot([l, h], [yi, yi], color=c, lw=1.6, solid_capstyle='round', zorder=2)
        ax.plot([xi], [yi], marker='o', ms=6.2, mfc=c if f else SURFACE, mec=c, mew=1.6, zorder=3, ls='none')


def select_rows(T):
    keep = []

    def add(p):
        if p in T.index and p not in keep:
            keep.append(p)
    for p in T.index[T.in_MCS_level.fillna(False).astype(bool) | T.in_MCS_rise.fillna(False).astype(bool)]:
        add(p)
    for p in ('chronos2_cur', 'chronos2_bk', 'chronos2_curdw', 'chronos2_nli', 'chronos2', 'chronos2_top', 'chronos'):
        add(p)
    for p in ('median_s2_all', 'median_s2_demand', 'median_s2_behavior', 'median_all'):
        add(p)
    for p in ('catchg_D', 'lgbmchg_D', 'ridgechg_D', 'lightgbm_D', 'ridge_D', 'catboost_D', 'revert6', 'naive'):
        add(p)
    return T.loc[keep].sort_values('AvgRelMAE')


XMAX = 1.07


def fig_a(T, name, title, nmax=26):
    keep = select_rows(T)
    n = len(keep)
    y = np.arange(n)[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(12.2, 0.30 * n + 2.0), sharey=True, facecolor=SURFACE)
    cols = [COL[family(p)] for p in keep.index]
    ax = axs[0]
    off = keep.AvgRelMAE > XMAX
    dots(ax, y[~off.to_numpy()], keep.AvgRelMAE[~off], keep.ci_lo[~off], keep.ci_hi[~off], keep.in_MCS_level.fillna(False).astype(bool)[~off], [c for c, o in zip(cols, off) if not o])
    for yi, v in zip(y[off.to_numpy()], keep.AvgRelMAE[off]):
        ax.annotate(f'{v:.2f} \u2192', (XMAX - 0.004, yi), ha='right', va='center', fontsize=7.8, color=INK2)
    ax.set_xlim(0.885, XMAX)
    ax.axvline(1, color=INK2, lw=0.9)
    ax.set_xlabel('Error relative to repeating last month\n(below 1 is better)', fontsize=8.5, color=INK2)
    ax.set_title('Level of next month\'s borrowing', fontsize=10, color=INK, loc='left', fontweight='bold')
    ax = axs[1]
    R = keep.dropna(subset=['rho'])
    dots(ax, y[[keep.index.get_loc(p) for p in R.index]], R.rho, R.rho_lo, R.rho_hi, R.in_MCS_rise.fillna(False).astype(bool), [COL[family(p)] for p in R.index])
    ax.axvline(0, color=INK2, lw=0.9)
    ax.set_xlabel('Rank correlation of forecast and\nactual change across themes', fontsize=8.5, color=INK2)
    ax.set_title('Which themes will rise', fontsize=10, color=INK, loc='left', fontweight='bold')
    ax = axs[2]
    S = keep.dropna(subset=['AP'])
    dots(ax, y[[keep.index.get_loc(p) for p in S.index]], S.AP, S.AP_lo, S.AP_hi, S.AP_tied_with_best.fillna(False).astype(bool), [COL[family(p)] for p in S.index])
    base = (S.AP / S.AP_lift).median() if len(S) else np.nan
    if np.isfinite(base):
        ax.axvline(base, color=INK2, lw=0.9, ls=(0, (1, 2)))
        ax.text(base, -0.55, '  chance', fontsize=7.5, color=INK2, va='center')
    ax.set_xlabel('Average precision of flagging themes\nabout to rise by 30% or more', fontsize=8.5, color=INK2)
    ax.set_title('Rare surges', fontsize=10, color=INK, loc='left', fontweight='bold')
    for a in axs:
        style(a)
    axs[0].set_yticks(y)
    axs[0].set_yticklabels([pretty(p) for p in keep.index], fontsize=8.3, color=INK)
    axs[0].set_ylim(-0.8, n - 0.2)
    axs[0].tick_params(axis='y', pad=4)
    # legend (always present for >= 2 series; identity not by colour alone: family also in the row label)
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=COL[k], mec=COL[k], label=FAMNAME[k]) for k in ('pre', 'chg', 'comb', 'other')]
    h += [Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=INK2, mec=INK2, label='filled: in the 90% confidence set (not distinguishable from the best)'),
          Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=SURFACE, mec=INK2, mew=1.5, label='open: not')]
    fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, fontsize=8, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(title, fontsize=11, color=INK, x=0.012, ha='left', fontweight='bold')
    fig.tight_layout(rect=(0, 0.07, 1, 0.96), w_pad=2.0)
    return fig


def fig_b(pairs, hz, title):
    fig, axs = plt.subplots(1, 2, figsize=(12.4, 6.3), gridspec_kw={'width_ratios': [1.45, 1]}, facecolor=SURFACE)
    ax = axs[0]
    P = pairs[pairs.kind == 'behavior against no behavior'].copy()
    P['model'] = P.base.str.split('_').str[0]
    order = [m for m in ('chronos2', 'catchg', 'lgbmchg', 'ridgechg') if m in set(P.model)]
    head = {'chronos2': 'Chronos-2', 'catchg': 'CatBoost on the change', 'lgbmchg': 'LightGBM on the change', 'ridgechg': 'Ridge on the change'}
    short = {'DVcur': 'Wikipedia volume (hand-checked pages)', 'DW': 'all ten Wikipedia features', 'DWS': 'with the lasting-rise state', 'DVcurdw': 'duration-weighted interest',
             'DVbk': 'book and author articles', 'DVnli': 'top pages read in context', 'DVtop': 'top pages by embedding', 'DVdem': 'articles weighted by past demand'}
    short2 = {'chronos2_cur': 'Wikipedia volume (hand-checked pages)', 'chronos2_curdw': 'duration-weighted interest', 'chronos2_bk': 'book and author articles',
              'chronos2_nli': 'top pages read in context', 'chronos2_top': 'top pages by embedding'}
    y, rows, labs, heads = 0.0, [], [], []
    for m in order:
        heads.append((y, head[m])); y -= 1.0
        for _, r in P[P.model == m].iterrows():
            rows.append((y, r)); labs.append((y, short2.get(r.other) if m == 'chronos2' else short.get(r.other.split('_', 1)[1], r.other))); y -= 1.0
        y -= 0.7
    for (yy, r) in rows:
        pt, lo, hi = (r.mae_ratio - 1) * 100, (r.mae_lo - 1) * 100, (r.mae_hi - 1) * 100
        sig = (lo > 0) or (hi < 0)
        c = (BLUE if pt < 0 else RED) if sig else GRAY
        ax.plot([lo, hi], [yy, yy], color=c, lw=1.6, solid_capstyle='round', zorder=2)
        ax.plot([pt], [yy], 'o', ms=6.2, mfc=c, mec=SURFACE, mew=1.2, zorder=3)
        ax.text(2.32, yy, f'{pt:+.1f}%', fontsize=7.8, va='center', ha='right', color=INK2)
    ax.axvline(0, color=INK2, lw=0.9)
    ax.set_yticks([yy for yy, _ in labs]); ax.set_yticklabels([l for _, l in labs], fontsize=8.2, color=INK)
    for yy, t in heads:
        ax.text(-0.012, yy, t, transform=ax.get_yaxis_transform(), ha='right', va='center', fontsize=8.8, color=INK, fontweight='bold')
    ax.set_xlim(-1.0, 2.38)
    ax.set_xlabel('Change in error when the behavior input is added, same model\n(negative = more accurate)', fontsize=8.5, color=INK2)
    ax.set_title('What organizing behavior changes', fontsize=10, color=INK, loc='left', fontweight='bold', pad=8)
    style(ax); ax.set_ylim(min(yy for yy, _ in labs) - 0.8, 0.8)
    ax.tick_params(axis='y', pad=2)
    ax = axs[1]
    names = {'chronos2_cur': 'Chronos-2 + Wikipedia', 'chronos2': 'Chronos-2, no interest', 'chronos': 'Chronos-Bolt', 'median_s2_all': 'Median of all learned models', 'catchg_D': 'CatBoost on the change'}
    colr = {'chronos2_cur': BLUE, 'chronos2': BLUE, 'chronos': BLUE, 'median_s2_all': AQUA, 'catchg_D': ORANGE}
    dash = {'chronos2_cur': '-', 'chronos2': (0, (5, 2)), 'chronos': (0, (1, 2)), 'median_s2_all': '-', 'catchg_D': '-'}
    ends = []
    for p in names:
        g = hz[hz.pipeline == p].sort_values('h')
        if len(g) < 3:
            continue
        ax.plot(g.h, (1 - g.AvgRelMAE) * 100, color=colr[p], lw=2, ls=dash[p], marker='o', ms=6, mfc=colr[p], mec=SURFACE, mew=1.2)
        ends.append([(1 - g.AvgRelMAE.iloc[-1]) * 100, p])
    ends.sort()
    lab_y = []
    for k, (v, p) in enumerate(ends):
        t = v if not lab_y else max(v, lab_y[-1] + 0.75)
        lab_y.append(t)
        ax.annotate(names[p], (3.0, v), xytext=(3.12, t), fontsize=8, va='center', color=INK2, arrowprops=dict(arrowstyle='-', color=GRID, lw=0.8, shrinkA=0, shrinkB=2))
    ax.axhline(0, color=INK2, lw=0.9)
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(['1 month', '2 months', '3 months'])
    ax.set_xlim(0.85, 4.35)
    ax.set_ylabel('Error below repeating last month (%)', fontsize=8.5, color=INK2)
    ax.set_title('Accuracy by forecast horizon', fontsize=10, color=INK, loc='left', fontweight='bold', pad=8)
    style(ax); ax.grid(axis='x', visible=False); ax.grid(axis='y', color=GRID, lw=0.8)
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=BLUE, mec=BLUE, label='left: more accurate (interval below zero)'),
         Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=RED, mec=RED, label='left: less accurate (interval above zero)'),
         Line2D([0], [0], marker='o', ls='none', ms=6.5, mfc=GRAY, mec=GRAY, label='left: not clearly different from zero'),
         Line2D([0], [0], color=BLUE, lw=2, label='right: pretrained forecaster'), Line2D([0], [0], color=AQUA, lw=2, label='right: combination of models'),
         Line2D([0], [0], color=ORANGE, lw=2, label='right: trained on the change')]
    fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, fontsize=8, labelcolor=INK2, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(title, fontsize=11, color=INK, x=0.012, ha='left', fontweight='bold')
    fig.tight_layout(rect=(0, 0.07, 1, 0.95), w_pad=3.0)
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--table', default='A2')
    ap.add_argument('--stamp', default=time.strftime('%Y-%m-%d_%H%M'))
    a = ap.parse_args()
    T = pd.read_csv(RES / f'{a.table}_table.csv', index_col=0)
    f1 = fig_a(T, a.table, 'Print and ebook borrowing, one month ahead: which pipelines predict best')
    p1 = FIGS / f'fig5_benchmark_stage2_{a.stamp}.png'
    f1.savefig(p1, dpi=200, facecolor=SURFACE); print('wrote', p1)
    pp = RES / f'{a.table}_pairs.csv'
    if pp.exists():
        pairs = pd.read_csv(pp)
        hz = []
        for k, h in (('A2', 1), ('B2', 2), ('C2', 3)):
            f = RES / f'{k}_table.csv'
            if f.exists():
                t = pd.read_csv(f, index_col=0)
                hz.append(t[['AvgRelMAE']].assign(h=h).reset_index(names='pipeline'))
        H = pd.concat(hz) if hz else pd.DataFrame()
        H = H.sort_values(['pipeline', 'h']) if len(H) else H
        if len(H):
            f2 = fig_b(pairs, H, 'Print and ebook borrowing: effect of organizing behavior, and accuracy by horizon')
            p2 = FIGS / f'fig6_benchmark_stage2_{a.stamp}.png'
            f2.savefig(p2, dpi=200, facecolor=SURFACE); print('wrote', p2)


if __name__ == '__main__':
    main()
