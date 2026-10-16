# Thesis figure: mean effect on borrowing (months 0 to 2) by how long a rise in Wikipedia interest lasted, narrow and middle themes, all formats pooled.
# Same effects and the same pooling as the pooled table of Study 3 (study3/12_shift_effects.py: main analysis, synthetic-control effect of the primary window,
# 95% percentile intervals from a bootstrap that resamples whole categories, 2,000 draws, seed 20261013); here the effects are grouped by the whole length
# of the rise in weeks (weeks at or above 1.5 times normal) instead of the three duration classes. Exploratory and descriptive.
# Output: paper/figures/fig_effect_by_duration_<stamp>.png and data/db/benchmark/stage2_results/figure_values_fig_effect_by_duration.csv
#   ../../../.venv/bin/python 24_figure_duration.py [--stamp YYYY-MM-DD_HHMM]
import sys, time, argparse
from _thesis_style import *

BINS = [0, 2, 3, 5, 8, 1000]
LABS = ['1 to 2', '3', '4 to 5', '6 to 8', '9 or more']
N_BOOT, SEED = 2000, 20261013
FS, FS_P, FS_T = 13.5, 15.0, 16.5
LW, MS = 2.4, 9.5


def cluster_boot_mean(v, cluster, n, seed):
    """Resample whole clusters with replacement n times (same procedure as study3/_methods.cluster_bootstrap); mean of the effect in each resample."""
    rng = np.random.default_rng(seed)
    idx = v.reset_index(drop=True).groupby(cluster, sort=True).indices
    groups = [idx[k] for k in sorted(idx)]
    x = v.reset_index(drop=True).sc_effect_p.to_numpy(float)
    out = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        out[i] = x[np.concatenate([groups[j] for j in pick])].mean()
    return out


def values():
    R = pd.read_parquet(DB / 'study3' / 'shift_effects.parquet')
    S = pd.read_parquet(DB / 'interest' / 'shifts.parquet')[['source', 'node_id', 'start_week', 'whole_duration']].drop_duplicates(['source', 'node_id', 'start_week'])
    R = R.merge(S, on=['source', 'node_id', 'start_week'], how='left')
    ok = R[(R.source == 'wikipedia') & (R.analysis == 'main') & (R.sc_ok == True) & R.sc_effect_p.notna()].copy()   # noqa: E712
    ok['bin'] = pd.cut(ok.whole_duration, bins=BINS, labels=LABS)
    rows = []
    for (lv, b), g in ok.groupby(['level', 'bin'], observed=True):
        bs = cluster_boot_mean(g, 'node_id', N_BOOT, SEED)
        rows.append(dict(level=lv, weeks=b, tests=len(g), themes=g.node_id.nunique(), mean=g.sc_effect_p.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stamp', default=time.strftime('%Y-%m-%d_%H%M'))
    a = ap.parse_args()
    setup()
    plt.rcParams.update({'font.size': FS})
    V = values()
    V.to_csv(RES / 'figure_values_fig_effect_by_duration.csv', index=False)
    print(V.round(3).to_string())
    fig, ax = plt.subplots(figsize=(11, 6.2))
    cols = {'narrow': (BLUE, -0.13, 'narrow themes'), 'middle': (ORANGE, 0.13, 'middle themes')}
    for lv, (c, dx, lab) in cols.items():
        d = V[V.level == lv].set_index('weeks').loc[LABS]
        for k, (b, r) in enumerate(d.iterrows()):
            x = k + dx
            ax.plot([x, x], [r.lo, r.hi], color=c, lw=LW, solid_capstyle='round', zorder=2)
            ax.plot([x], [r['mean']], marker='o', ms=MS, mfc=c, mec=c, zorder=3, ls='none')
    ax.axhline(0, color=INK2, lw=1.2)
    ax.axvline(1.5, color=INK2, lw=1.2, ls=(0, (3, 2)))
    ax.text(1.58, 0.42, 'lasting rise:\n4 weeks or more', fontsize=FS, color=INK2, va='top', ha='left', linespacing=1.15)
    ax.set_xticks(range(len(LABS)))
    ax.set_xticklabels([f'{l}\n{int(V[(V.weeks == l) & (V.level == "narrow")].tests.iloc[0])} | {int(V[(V.weeks == l) & (V.level == "middle")].tests.iloc[0])}' for l in LABS], fontsize=FS)
    ax.set_xlabel('Weeks the rise stayed at 1.5 times normal or more\n(tests for narrow | middle themes below)', fontsize=FS)
    ax.set_ylabel('Mean effect on borrowing,\nmonths 0 to 2 (log share)', fontsize=FS)
    ax.set_xlim(-0.55, len(LABS) - 0.45)
    ax.set_ylim(-0.2, 0.46)
    clean(ax, 'y')
    ax.tick_params(axis='both', colors=INK2, labelsize=FS, length=0)
    h = [Line2D([0], [0], marker='o', ls='none', ms=MS, mfc=c, mec=c, label=lab) for c, _, lab in cols.values()]
    ax.legend(handles=h, loc='upper left', frameon=False, fontsize=FS, labelcolor=INK2)
    fig.suptitle('Borrowing after a rise in Wikipedia interest, by how long the rise lasted', fontsize=FS_T, x=0.012, ha='left', fontweight='bold', color=INK)
    fig.subplots_adjust(left=0.13, right=0.985, top=0.9, bottom=0.2)
    p = FIGS / f'fig_effect_by_duration_{a.stamp}.png'
    fig.savefig(p, dpi=200, facecolor=SURFACE)
    print('wrote', p)


if __name__ == '__main__':
    main()
