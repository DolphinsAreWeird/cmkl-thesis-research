# Figure for the benchmark: AvgRelMAE with 95% intervals for the main comparison (print and ebook, horizon 1),
# pipelines in the 90% model confidence set drawn filled, the others hollow. Writes paper/figures/fig4_benchmark_<stamp>.{png,svg}.
import sys, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import _settings as ST

NAMES = {'naive': 'Repeat last month', 'seasonal_naive': 'Seasonal repeat', 'ridge_D': 'Ridge, borrowing only',
         'ridge_DW': 'Ridge + Wikipedia', 'catboost_D': 'CatBoost, borrowing only', 'catboost_DW': 'CatBoost + Wikipedia',
         'lightgbm_D': 'LightGBM, borrowing only', 'lightgbm_DW': 'LightGBM + Wikipedia', 'chronos': 'Chronos (pretrained)',
         'ridgechg_D': 'Ridge on change, borrowing only', 'ridgechg_DW': 'Ridge on change + Wikipedia',
         'ridgechg_DWS': 'Ridge on change + Wikipedia + lasting rises', 'catchg_D': 'CatBoost on change, borrowing only',
         'catchg_DW': 'CatBoost on change + Wikipedia', 'catchg_DWS': 'CatBoost on change + Wikipedia + lasting rises',
         'avg_ridge_cat_D': 'Average: ridge + CatBoost', 'avg_ridge_cat_DW': 'Average: ridge + CatBoost, + Wikipedia',
         'avg_three_DW': 'Average: ridge + CatBoost + LightGBM, + Wikipedia', 'avg_naive_ridge_D': 'Average: repeat + ridge',
         'median_all': 'Median of all single models', 'invmae_all': 'Weighted average by recent accuracy'}
INK, MUTED, ACCENT, GRID = '#1f2328', '#6b7280', '#2b6cb0', '#e5e7eb'


def main():
    T = pd.read_csv(ST.DB / 'benchmark' / 'summary.csv', index_col=0)
    T = T[T.comparison.str.startswith('A. ') & (T.index != 'seasonal_naive')].sort_values('AvgRelMAE', ascending=False)   # seasonal repeat (about 2.1) is off the scale; given in the caption
    fig, ax = plt.subplots(figsize=(7.2, 0.32 * len(T) + 1.2), dpi=200)
    y = range(len(T))
    for i, (p, r) in enumerate(T.iterrows()):
        inc = bool(r.in_MCS)
        ax.plot([r.ci_lo, r.ci_hi], [i, i], color=ACCENT if inc else MUTED, lw=2, solid_capstyle='round')
        ax.plot(r.AvgRelMAE, i, 'o', ms=7, mfc=ACCENT if inc else 'white', mec=ACCENT if inc else MUTED, mew=1.6)
    ax.axvline(1.0, color=INK, lw=1, ls=(0, (3, 3)))
    ax.set_yticks(list(y)); ax.set_yticklabels([NAMES.get(p, p) for p in T.index], fontsize=8, color=INK)
    ax.set_xlabel('Error relative to "repeat last month"\n(geometric mean over themes and formats; below 1 is better)', fontsize=8, color=INK)
    ax.tick_params(axis='x', labelsize=8, colors=INK); ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.plot([], [], 'o', mfc=ACCENT, mec=ACCENT, label='In the 90% model confidence set (tied best)')
    ax.plot([], [], 'o', mfc='white', mec=MUTED, label='Outside the set')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.11), ncol=2, fontsize=7.5, frameon=False)
    fig.tight_layout()
    stamp = time.strftime('%Y-%m-%d_%H%M')
    out = ST.ROOT / 'paper' / 'figures' / f'fig4_benchmark_{stamp}'
    fig.savefig(str(out) + '.png'); fig.savefig(str(out) + '.svg')
    print(out)


if __name__ == '__main__':
    main()
