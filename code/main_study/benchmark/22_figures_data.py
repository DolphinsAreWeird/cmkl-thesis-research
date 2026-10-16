# Thesis figures built from existing project data (16 Oct 2026). One script, one switch per figure; it writes only the PNGs and the figure_values CSVs.
#   --rank   fig_rank_accuracy         how well forecasts rank themes (benchmark forecasts, printed books and ebooks, one month ahead)
#   --rise   fig_lasting_rise_example  what a short rise and a lasting rise in Wikipedia interest look like (interest tables, fixed rule)
#   --tree   fig_theme_hierarchy       how library subject headings become themes (taxonomy tables)
#   ../../../.venv/bin/python 22_figures_data.py --rank --rise --tree [--stamp YYYY-MM-DD_HHMM]
# Output: paper/figures/NAME_<stamp>.png (200 dpi, 11 inches wide) and data/db/benchmark/stage2_results/figure_values_NAME.csv (the numbers plotted).
# Text size: the smallest text is 13.5 pt at the 11-inch design width, which is 8 pt when the figure is shown 6.5 inches wide.
# Sample of --rank: the sample of the main results table (comparison A2 of 03_evaluate.py --stage2: printed books and ebooks, one month ahead, rows where all
# 52 pipelines of the roster have a forecast, series with at least 12 forecast months); it is checked against data/db/benchmark/stage2_results/meta.csv.
import sys, json, hashlib, argparse
from _thesis_style import *
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.text import Text
from scipy import stats
import pyarrow.parquet as pq

FS = 13.5                      # smallest text size (pt) at the 11-inch design width
FS_TITLE, FS_MAIN = 14.5, 17.0
HEAD, EDGE, BODY, LINE = '#2a6fdb', '#c9d3e3', '#f3f6fb', '#aeb3ba'     # the card colours of 20_figure_pipeline.py and a thin grey connector
NAME1, NAME2, NAME3 = 'fig_rank_accuracy', 'fig_lasting_rise_example', 'fig_theme_hierarchy'
MINUS = '−'


# ======================================================================================================================================
# helpers
# ======================================================================================================================================
def fonts():
    setup()
    plt.rcParams.update({'font.size': FS, 'axes.labelsize': FS, 'xtick.labelsize': FS, 'ytick.labelsize': FS, 'axes.titlesize': FS})


def new_fig(W, H):
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=SURFACE)
    fig.canvas.draw()
    return fig


def axes_in(fig, left, bottom, width, height):
    W, H = fig.get_size_inches()
    return fig.add_axes([left / W, bottom / H, width / W, height / H])


def put(fig, x, y, s, **kw):
    """Text at a position in inches from the lower left corner of the figure."""
    W, H = fig.get_size_inches()
    return fig.text(x / W, y / H, s, **kw)


def measure(fig, s, size, weight='normal'):
    t = fig.text(0, 0, s, fontsize=size, fontweight=weight)
    w = t.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi
    t.remove()
    return w


def wrap(fig, s, max_w, size, weight='normal'):
    lines, cur = [], ''
    for word in s.split(' '):
        trial = (cur + ' ' + word).strip()
        if not cur or measure(fig, trial, size, weight) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def audit(fig, name, min_pt=FS):
    """Smallest text, text outside the canvas and overlapping text (all in the saved figure)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = []
    for t in fig.findobj(Text):
        s = t.get_text().strip()
        if not s or not t.get_visible():
            continue
        bb = t.get_window_extent(r)
        if bb.width < 1 or bb.height < 1:
            continue
        items.append((t, bb, s))
    Wp, Hp = fig.get_size_inches() * fig.dpi
    small = sorted({round(t.get_fontsize(), 2) for t, _, _ in items})
    if small[0] < min_pt - 1e-6:
        print(f'[{name}] WARNING: text smaller than {min_pt} pt')
    print(f'[{name}] text sizes used (pt): {small}; smallest {small[0]} = {small[0] * 6.5 / fig.get_size_inches()[0]:.1f} pt at 6.5 inches wide')
    for t, bb, s in items:
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > Wp + 1 or bb.y1 > Hp + 1:
            print(f'[{name}] text outside the canvas: {s[:40]!r} {bb.bounds}')
    n = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ix = min(a.x1, b.x1) - max(a.x0, b.x0)
            iy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ix > 3 and iy > 3:
                n += 1
                print(f'[{name}] overlapping text: {items[i][2][:35]!r} / {items[j][2][:35]!r} ({ix:.0f} x {iy:.0f} px)')
    print(f'[{name}] overlapping text pairs: {n}')


def write_values(name, df):
    p = RES / f'figure_values_{name}.csv'
    df.to_csv(p, index=False)
    print('wrote', p)


# ======================================================================================================================================
# figure 1: how well forecasts rank themes
# ======================================================================================================================================
WIDE2 = DB / 'benchmark' / 'wide2.parquet'
ADDENDUM = ST.PREREG / 'addenda_benchmark' / '2026-10-15_b_stage2_metrics_tasks_pipelines.json'
ADDENDUM_SHA = '9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22'
SEED, NBOOT, MIN_GROUP, MIN_MONTHS = 20261015, 2000, 10, 12
LN13 = float(np.log(1.3))                    # a rise of 30% or more in the share (the surge definition of the benchmark)
SER = ['group', 'format', 'level', 'node_id']
P1 = ['chronos2_cur', 'catchg_D', 'revert6']
LAB1 = {'chronos2_cur': 'Chronos-2 + concept pages', 'catchg_D': 'CatBoost on the change', 'revert6': 'Mean of the last six months'}
COL1 = {'chronos2_cur': BLUE, 'catchg_D': ORANGE, 'revert6': GRAY}
DODGE = {'chronos2_cur': -0.13, 'catchg_D': 0.0, 'revert6': 0.13}


def main_sample():
    """The rows of comparison A2 of the main results table, selected as in 03_evaluate.py (Cmp.__init__), and a check against meta.csv."""
    got = hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()
    if got != ADDENDUM_SHA:
        raise SystemExit(f'stage-2 addendum changed ({got}); nothing is drawn')
    roster = json.loads(ADDENDUM.read_text())['roster_A2']
    names = pq.ParquetFile(WIDE2).schema_arrow.names
    pipes = list(roster['stage1_21']) + list(roster['stage2_new'])
    pipes += [c for c in names if c.endswith('_DVdem') and c not in pipes]
    w = pd.read_parquet(WIDE2, columns=SER + ['origin_mi', 'h', 'tmonth', 'y_true', 'y_t'] + [p for p in pipes if p in names])
    pe = (w.group == 'seattle') & w.format.isin(['print', 'ebook']) & (w.h == 1)
    have = [p for p in pipes if p in w.columns and w.loc[pe, p].notna().mean() > 0.9]
    d = w[pe].dropna(subset=have + ['y_true', 'y_t'])
    n = d.groupby(SER).size()
    d = d.set_index(SER).loc[n[n >= MIN_MONTHS].index].reset_index().reset_index(drop=True)
    series, months = d.groupby(SER).ngroups, d.origin_mi.nunique()
    meta = pd.read_csv(RES / 'meta.csv').set_index('name').loc['A2']
    print(f'sample: {len(d):,} forecasts, {series} series, {months} months, {len(have)} pipelines with a forecast on every row '
          f'(main table meta.csv: {int(meta.rows):,}, {int(meta.series)}, {int(meta.months)}, {int(meta.pipelines)})')
    if not (len(d) == int(meta.rows) == 36081 and series == int(meta.series) == 510 and months == int(meta.months) == 88 and len(have) == int(meta.pipelines)):
        raise SystemExit('the sample of the main results table was not reproduced; nothing is drawn')
    return d


def block_draws(T, nboot, seed, block=3):
    """Moving-block bootstrap over T months (blocks of 3 consecutive months), the function of 03_evaluate.py."""
    b = min(block, T)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(nboot, nb))
    return (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(nboot, -1)[:, :T]


def rank_numbers(d):
    """Per pipeline: mean actual change (%) of each fifth of themes ranked by forecast change, rank correlation and precision of the top 5%, with 95% intervals."""
    months = np.array(sorted(d.origin_mi.unique()))
    T = len(months)
    # cell = origin month x format x level; with h = 1 one origin month is one target month (the column tmonth of wide2 holds only the calendar month '01' to '12')
    G = d.groupby(['origin_mi', 'format', 'level']).indices
    yt = d.y_t.to_numpy(float)
    act = d.y_true.to_numpy(float) - yt
    D = block_draws(T, NBOOT, SEED)
    out = {}
    for p in P1:
        fc = d[p].to_numpy(float) - yt
        F, Rm, hits, flagged = np.full((T, 5), np.nan), np.full(T, np.nan), np.zeros(T), np.zeros(T)
        af, ar, sizes = {}, {}, []
        for (m, f, l), idx in G.items():
            if len(idx) < MIN_GROUP:
                continue
            a, x = act[idx], fc[idx]
            fifth = (((stats.rankdata(x, method='ordinal') - 1) * 5) // len(idx)).astype(int)      # five equal groups, lowest forecast change first
            v = (np.exp(a) - 1) * 100                                               # percent change of the theme's share
            af.setdefault(m, []).append([v[fifth == k].mean() for k in range(5)])
            sizes.append(np.bincount(fifth, minlength=5))
            ra, rx = stats.rankdata(a), stats.rankdata(x)
            ra, rx = ra - ra.mean(), rx - rx.mean()
            den = np.sqrt((ra ** 2).sum() * (rx ** 2).sum())
            ar.setdefault(m, []).append((rx * ra).sum() / den if den > 1e-12 else np.nan)
            k = int(np.ceil(0.05 * len(idx)))
            o = np.argsort(-x, kind='stable')[:k]
            mi = int(np.searchsorted(months, m))
            hits[mi] += (a[o] >= LN13).sum()
            flagged[mi] += k
        for m, lst in af.items():
            F[np.searchsorted(months, m)] = np.mean(lst, axis=0)
        for m, lst in ar.items():
            Rm[np.searchsorted(months, m)] = np.nanmean(lst)
        bs = np.nanmean(F[D], axis=1)
        fl, fh = np.nanquantile(bs, [0.025, 0.975], axis=0)
        rl, rh = np.nanquantile(np.nanmean(Rm[D], axis=1), [0.025, 0.975])
        pl, ph = np.quantile(hits[D].sum(1) / flagged[D].sum(1), [0.025, 0.975])
        out[p] = dict(mean=np.nanmean(F, axis=0), lo=fl, hi=fh, months=int(np.isfinite(F[:, 0]).sum()), cells=len(sizes), per_fifth=np.mean(sizes, axis=0),
                      rho=float(np.nanmean(Rm)), rho_lo=float(rl), rho_hi=float(rh), prec=float(hits.sum() / flagged.sum()), prec_lo=float(pl), prec_hi=float(ph),
                      hits=int(hits.sum()), flagged=int(flagged.sum()))
    return out, float((act >= LN13).mean())


def spread_labels(y, h, lo, hi, pad=0.12):
    """Move labels (centres y, heights h, data units, top to bottom) apart, keeping their order and staying inside [lo, hi]."""
    order = np.argsort(-np.asarray(y))
    out = np.array(y, float)
    for k in range(1, len(order)):
        a, b = order[k - 1], order[k]
        out[b] = min(out[b], out[a] - (h[a] + h[b]) / 2 - pad)
    for k in range(len(order) - 2, -1, -1):                 # if the lowest was pushed out of the axes, push the others up
        a, b = order[k], order[k + 1]
        if out[b] - h[b] / 2 < lo:
            out[b] = lo + h[b] / 2
        out[a] = max(out[a], out[b] + (h[a] + h[b]) / 2 + pad)
    return out


def fig_rank_accuracy(stamp):
    fonts()
    d = main_sample()
    R, base = rank_numbers(d)
    tab = pd.read_csv(RES / 'A2_table.csv', index_col=0)
    meta = pd.read_csv(RES / 'meta.csv').set_index('name').loc['A2']
    print(f'surge base rate: {base:.5f} (meta.csv {float(meta.surge_base_rate):.5f})')
    assert abs(base - float(meta.surge_base_rate)) < 1e-12
    print('sanity check, mean cross-theme Spearman of forecast change and actual change (ours | main table A2 | value given in the brief):')
    given = {'chronos2_cur': 0.319, 'catchg_D': 0.267, 'revert6': 0.140}
    for p in P1:
        print(f'  {p:13s} {R[p]["rho"]:.4f} [{R[p]["rho_lo"]:.4f}, {R[p]["rho_hi"]:.4f}] | {tab.loc[p, "rho"]:.4f} [{tab.loc[p, "rho_lo"]:.4f}, {tab.loc[p, "rho_hi"]:.4f}] | {given[p]}')
        assert abs(R[p]['rho'] - tab.loc[p, 'rho']) < 1e-9
    print('precision of the top 5% (ours | table A2): ' + '; '.join(f'{p} {R[p]["prec"]:.5f} | {tab.loc[p, "precision_top5pct"]:.5f}' for p in P1))
    for p in P1:
        assert abs(R[p]['prec'] - tab.loc[p, 'precision_top5pct']) < 1e-9
    for p in P1:
        print(f'  {p:13s} fifths {np.round(R[p]["mean"], 2)}  95% low {np.round(R[p]["lo"], 2)}  high {np.round(R[p]["hi"], 2)}  '
              f'(months {R[p]["months"]}, cells {R[p]["cells"]}, themes per fifth {np.round(R[p]["per_fifth"], 1)})')

    W, H = 11.0, 5.55
    fig = new_fig(W, H)
    put(fig, 0.25, H - 0.33, 'Themes forecast to rise most did rise most', fontsize=FS_MAIN, fontweight='bold', color=INK, va='center', ha='left')
    top = H - 0.66                                            # top of the panel titles
    ax_top, ax_bot = 4.2, 1.1                                 # axes top and bottom, inches from the bottom of the figure
    ah = ax_top - ax_bot
    # ---------------- left panel: average actual change by fifth of forecast change
    LEFT, LW_ = 0.95, 5.55
    aL = axes_in(fig, LEFT, ax_bot, LW_, ah)
    X0, X1, Y0, Y1 = 0.55, 5.45, -4.6, 5.0
    lab_w = 1.75
    aL.set_xlim(X0, X1 + lab_w * (X1 - X0) / (LW_ - lab_w))
    aL.set_ylim(Y0, Y1)
    clean(aL, 'none')
    aL.tick_params(axis='both', labelsize=FS)
    aL.spines['bottom'].set_bounds(X0, X1)
    yt = [-4, -2, 0, 2, 4]
    aL.set_yticks(yt)
    aL.set_yticklabels([MINUS + f'{abs(v)}%' if v < 0 else ('0%' if v == 0 else f'+{v}%') for v in yt])
    aL.hlines([v for v in yt if v != 0], X0, X1, color=GRID, lw=0.9, zorder=0)
    aL.hlines(0, X0, X1, color=INK2, lw=1.3, zorder=1)
    aL.set_xticks(range(1, 6))
    aL.set_xticklabels(['Lowest\nfifth', '2nd', '3rd', '4th', 'Highest\nfifth'])
    put(fig, LEFT + (LW_ - lab_w) / 2, 0.3, 'Themes ranked by forecast change, in fifths', fontsize=FS, color=INK2, va='center', ha='center')
    xs = np.arange(1, 6)
    for p in P1:
        c, m, lo, hi = COL1[p], R[p]['mean'], R[p]['lo'], R[p]['hi']
        x = xs + DODGE[p]
        aL.plot(x, m, color=c, lw=2.3, zorder=3, solid_capstyle='round')
        aL.vlines(x, lo, hi, color=c, lw=2.3, zorder=2)
        aL.plot(x, m, 'o', ms=8.5, mfc=c, mec=SURFACE, mew=1.3, zorder=4, ls='none')
    # direct labels at the right end of each line
    ppu = ah / (Y1 - Y0)                                      # inches per y unit
    names = {p: wrap(fig, LAB1[p], lab_w - 0.3, FS) for p in P1}
    hts = [len(names[p]) * FS * 1.22 / 72 / ppu for p in P1]
    yend = [R[p]['mean'][-1] for p in P1]
    yl = spread_labels(yend, hts, Y0 + 0.2, Y1 - 0.1)
    for p, y0, y1 in zip(P1, yend, yl):
        xe = 5 + DODGE[p] + 0.16
        aL.plot([xe, X1 + 0.12], [y0, y1], color=COL1[p], lw=1.4, zorder=2, solid_capstyle='round')
        aL.text(X1 + 0.17, y1, '\n'.join(names[p]), fontsize=FS, color=INK, va='center', ha='left', linespacing=1.15)
    put(fig, LEFT, top, "Average actual change in the theme's\nshare the next month", fontsize=FS_TITLE, fontweight='bold', color=INK, va='top', ha='left', linespacing=1.2)
    # ---------------- right panel: precision of the top 5% flagged
    RX0, RX1, catw = 7.05, 10.8, 1.8
    aR = axes_in(fig, RX0 + catw, ax_bot, RX1 - RX0 - catw, ah)
    aR.set_xlim(0, 8.6)
    aR.set_ylim(-1.05, 2.55)
    clean(aR, 'x')
    aR.tick_params(axis='both', labelsize=FS)
    aR.grid(axis='x', color=GRID, lw=0.9)
    ypos = {p: yy for p, yy in zip(P1, (2.0, 1.0, 0.0))}
    pr = {p: tab.loc[p, 'precision_top5pct'] * 100 for p in P1}
    for p in P1:
        y = ypos[p]
        aR.barh(y, pr[p], height=0.52, color=COL1[p], zorder=2)
        lo, hi = R[p]['prec_lo'] * 100, R[p]['prec_hi'] * 100
        aR.plot([lo, hi], [y, y], color=INK, lw=1.7, zorder=3, solid_capstyle='butt')
        aR.plot([lo, lo], [y - 0.09, y + 0.09], color=INK, lw=1.7, zorder=3)
        aR.plot([hi, hi], [y - 0.09, y + 0.09], color=INK, lw=1.7, zorder=3)
        aR.text(hi + 0.32, y, f'{pr[p]:.1f}%' if pr[p] >= 1 else f'{pr[p]:.2f}%', fontsize=FS, color=INK, va='center', ha='left')
    aR.set_yticks([ypos[p] for p in P1])
    aR.set_yticklabels(['\n'.join(wrap(fig, LAB1[p], catw - 0.2, FS)) for p in P1], linespacing=1.15, color=INK)
    aR.tick_params(axis='y', pad=6)
    aR.set_xticks([0, 2, 4, 6, 8])
    aR.set_xticklabels(['0%', '2%', '4%', '6%', '8%'])
    aR.vlines(base * 100, -0.8, 2.45, color=INK, lw=1.7, ls=(0, (1.2, 2.2)), zorder=4)
    aR.text(base * 100 + 0.25, -0.62, 'Among all\nforecasts: 0.65%', fontsize=FS, color=INK, va='center', ha='left', linespacing=1.15)
    tr = wrap(fig, 'The 5% of themes flagged as most likely to rise', RX1 - RX0, FS_TITLE, 'bold')
    put(fig, RX0, top, '\n'.join(tr), fontsize=FS_TITLE, fontweight='bold', color=INK, va='top', ha='left', linespacing=1.2)
    put(fig, (RX0 + RX1) / 2 + 0.2, 0.42, 'Share that rose by 30%\nor more in the month', fontsize=FS, color=INK2, va='center', ha='center', linespacing=1.2)
    audit(fig, NAME1)
    save(fig, NAME1, stamp)

    rows = []
    for p in P1:
        for k in range(5):
            rows.append(dict(panel='left: average actual change of the theme share by fifth of forecast change (%)', pipeline=p, label=LAB1[p], x=k + 1,
                             x_label=['lowest fifth', '2nd', '3rd', '4th', 'highest fifth'][k], value=R[p]['mean'][k], ci_lo=R[p]['lo'][k], ci_hi=R[p]['hi'][k],
                             note=f'mean over {R[p]["months"]} months of the cell averages; 95% interval: moving-block bootstrap over months (blocks of 3, {NBOOT} draws, seed {SEED})'))
    for p in P1:
        rows.append(dict(panel='right: share of the 5% flagged themes that rose by 30% or more (%)', pipeline=p, label=LAB1[p], x=np.nan, x_label='top 5% flagged',
                         value=pr[p], ci_lo=R[p]['prec_lo'] * 100, ci_hi=R[p]['prec_hi'] * 100,
                         note=f'bar = precision_top5pct of A2_table.csv; {R[p]["hits"]} of {R[p]["flagged"]} flagged forecasts; interval: same bootstrap'))
    rows.append(dict(panel='right: share of the 5% flagged themes that rose by 30% or more (%)', pipeline='all forecasts', label='base rate', x=np.nan,
                     x_label='dotted line', value=base * 100, ci_lo=np.nan, ci_hi=np.nan, note='share of all 36,081 forecasts with a rise of 30% or more (meta.csv, surge_base_rate)'))
    for p in P1:
        rows.append(dict(panel='check: mean cross-theme Spearman of forecast change and actual change', pipeline=p, label=LAB1[p], x=np.nan, x_label='this script',
                         value=R[p]['rho'], ci_lo=R[p]['rho_lo'], ci_hi=R[p]['rho_hi'], note=f'A2_table.csv: {tab.loc[p, "rho"]:.4f} [{tab.loc[p, "rho_lo"]:.4f}, {tab.loc[p, "rho_hi"]:.4f}]'))
    write_values(NAME1, pd.DataFrame(rows))


# ======================================================================================================================================
# figure 2: a short rise and a lasting rise in weekly Wikipedia interest
# ======================================================================================================================================
INT = DB / 'interest'
# the two rises shown: (key, theme node, start week, label in the table); both are rises of the middle theme "Race, racism and diversity"
EXAMPLES = [('short', 'B05.M02', '2022-01-31', 'fading'), ('lasting', 'B05.M02', '2020-05-25', 'sustained')]
ROW_TITLE = {'short': 'A short rise', 'lasting': 'A lasting rise'}


def rise_windows():
    sh = pd.read_parquet(INT / 'shifts.parquet')
    sw = pd.read_parquet(INT / 'shift_weekly.parquet')
    nodes = pd.read_parquet(DB / 'taxonomy_v3' / 'theme_nodes.parquet', columns=['node_id', 'level', 'label']).set_index('node_id')
    th = json.loads((ST.PREREG / 'study3_settings_2026-10-13.json').read_text())['shift_definitions']
    out = []
    for key, nid, start, label in EXAMPLES:
        start = pd.Timestamp(start)
        row = sh[(sh.source == 'wikipedia') & (sh.node_id == nid) & (sh.start_week == start)]
        assert len(row) == 1, (nid, start)
        row = row.iloc[0]
        assert row.label == label and row.level == 2 and bool(row.quality_ok) and bool(row.main_set), (key, row.label, row.quality_ok)
        g = sw[(sw.source == 'wikipedia') & (sw.node_id == nid)].sort_values('week').reset_index(drop=True)
        i = int(g.index[g.week == start][0])
        win = g.iloc[i - 16:i + 17].copy()
        assert len(win) == 33 and (win.week.diff().dropna() == pd.Timedelta(days=7)).all() and win.usable.all() and win.ratio.notna().all()
        # independent re-derivation of the rule from the weekly shares: normal level = median of the previous 26 weeks, ratio, run of weeks at or above 1.5
        normal = g.share.shift(1).rolling(26, min_periods=26).median()
        assert np.allclose(normal.iloc[i - 16:i + 17].to_numpy(), win.normal.to_numpy(), rtol=1e-9)
        ratio = g.share / normal
        assert np.allclose(ratio.iloc[i - 16:i + 17].to_numpy(), win.ratio.to_numpy(), rtol=1e-9)
        run = 0
        while ratio.iloc[i + run] >= 1.5:
            run += 1
        assert run == int(row.whole_duration), (run, row.whole_duration)
        cls = 'sustained' if run >= 4 else ('fading' if run <= 2 else 'intermediate')
        assert cls == label
        others = sh[(sh.source == 'wikipedia') & (sh.node_id == nid) & (sh.start_week >= win.week.min()) & (sh.start_week <= win.week.max()) & (sh.start_week != start)]
        assert len(others) == 0
        win['offset'] = np.arange(-16, 17)
        out.append(dict(key=key, node_id=nid, theme=nodes.loc[nid, 'label'], start=start, label=label, run=run, row=row, win=win,
                        above=int((win.ratio >= 1.5).sum()), peak=float(win.ratio.max()), peak_offset=int(win.offset[win.ratio.idxmax()])))
    print('rule from prereg/study3_settings:', th['normal_level'], '|', th['shift_start'], '|', th['sustained'], '|', th['fading'])
    return out


def fig_lasting_rise_example(stamp):
    fonts()
    ex = rise_windows()
    for e in ex:
        r = e['row']
        print(f"[{e['key']}] {e['theme']} ({e['node_id']}, level {r.level}) start week {e['start'].date()}, label {r.label} (label week {r.label_week.date()}), "
              f"weeks at or above 1.5 from the start: {e['run']}, weeks at or above 1.5 in the 33-week window: {e['above']}, peak {e['peak']:.2f} at week {e['peak_offset']:+d}, "
              f"ratio at start {r.ratio_start:.2f}, normal level {r.normal_start:.6f} of Wikipedia views ({r.volume_normal_start:,.0f} views a week), "
              f"quality_flag {r.quality_flag!r}, title_check {r.title_check}, seasonal {r.seasonal}, main_set {r.main_set}, driver page {r.wiki_driver}")
    W, H = 11.0, 6.0
    fig = new_fig(W, H)
    put(fig, 0.25, H - 0.33, 'One rule separates short rises from lasting rises in Wikipedia interest', fontsize=FS_MAIN, fontweight='bold', color=INK, va='center', ha='left')
    ah, left, aw = 1.65, 1.0, 9.8
    tops = [H - 1.05, H - 1.05 - ah - 0.85]
    YMAX = 5.6
    assert max(e['peak'] for e in ex) < YMAX - 0.7, 'the common y scale is too small for these rises'
    for e, top in zip(ex, tops):
        ax = axes_in(fig, left, top - ah, aw, ah)
        win = e['win']
        ax.set_xlim(-16.8, 16.8)
        ax.set_ylim(0, YMAX)
        clean(ax, 'y')
        ax.tick_params(axis='both', labelsize=FS)
        ax.set_yticks([0, 1, 2, 3, 4, 5])
        ax.set_xticks([-16, -12, -8, -4, 0, 4, 8, 12, 16])
        ax.set_xticklabels([MINUS + '16', MINUS + '12', MINUS + '8', MINUS + '4', '0', '4', '8', '12', '16'])
        ax.grid(axis='y', color=GRID, lw=0.9)
        # weeks at or above 1.5 times normal, shaded
        run = e['run']
        ax.axvspan(-0.5, run - 0.5, color=PALE_BLUE, zorder=0, lw=0)
        ax.axhline(1.5, color=INK2, lw=1.5, ls=(0, (5, 3)), zorder=2)
        ax.axvline(0, color=ORANGE, lw=2.0, ls=(0, (1.5, 1.8)), zorder=2)
        ax.plot(win.offset, win.ratio, color=BLUE, lw=2.4, zorder=4, solid_capstyle='round')
        hi = win.ratio >= 1.5
        ax.plot(win.offset[hi], win.ratio[hi], 'o', ms=7.5, mfc=BLUE, mec=SURFACE, mew=1.0, zorder=5, ls='none')
        ax.plot(win.offset[~hi], win.ratio[~hi], 'o', ms=6.2, mfc=SURFACE, mec=BLUE, mew=1.6, zorder=5, ls='none')
        ax.text(-16.5, 1.62, '1.5 times normal', fontsize=FS, color=INK2, va='bottom', ha='left', zorder=3, bbox=dict(fc=SURFACE, ec='none', pad=1.5))
        sd = e['start']
        ax.text(-0.9, 4.0, f'Start: week of {sd.day} {sd:%B %Y}', fontsize=FS, color=INK, va='center', ha='right')
        # bracket over the shaded weeks and what it means
        ytop = 5.0 if e['key'] == 'lasting' else 3.3
        ax.plot([-0.5, run - 0.5], [ytop, ytop], color=INK, lw=1.6, zorder=6, solid_capstyle='butt')
        ax.plot([-0.5, -0.5], [ytop - 0.14, ytop + 0.14], color=INK, lw=1.6, zorder=6)
        ax.plot([run - 0.5, run - 0.5], [ytop - 0.14, ytop + 0.14], color=INK, lw=1.6, zorder=6)
        word = 'week' if run == 1 else 'weeks'
        txt = (f'Stays at or above 1.5\nfor {run} {word}' if e['key'] == 'lasting' else f'Falls back below 1.5\nafter {run} {word}')
        ax.text(run - 0.5 + 0.7, ytop, txt, fontsize=FS, color=INK, va='center', ha='left', linespacing=1.15)
        ax.set_ylabel('Interest,\ntimes normal', fontsize=FS, color=INK2, labelpad=8, linespacing=1.15)
        put(fig, left, top + 0.3, ROW_TITLE[e['key']], fontsize=FS_TITLE, fontweight='bold', color=INK, va='center', ha='left')
        wt = measure(fig, ROW_TITLE[e['key']], FS_TITLE, 'bold')
        put(fig, left + wt + 0.25, top + 0.3, e['theme'], fontsize=FS, color=INK2, va='center', ha='left')
    axb = fig.axes[-1]
    axb.set_xlabel('Weeks from the start of the rise', fontsize=FS, color=INK2, labelpad=6)
    audit(fig, NAME2)
    save(fig, NAME2, stamp)
    rows = []
    for e in ex:
        r = e['row']
        for _, x in e['win'].iterrows():
            rows.append(dict(panel=ROW_TITLE[e['key']], theme=e['theme'], node_id=e['node_id'], start_week=e['start'].date(), label_in_table=r.label,
                             label_week=r.label_week.date(), weeks_at_or_above_1_5_from_start=e['run'], peak_interest_over_normal=e['peak'], quality_flag=r.quality_flag,
                             title_check=r.title_check, driver_page=r.wiki_driver, week_from_start=int(x.offset), week_beginning=x.week.date(),
                             share_of_en_wikipedia_views=x.share, weekly_views=x.volume, normal_level_share=x.normal, interest_over_normal=x.ratio,
                             at_or_above_1_5=bool(x.ratio >= 1.5)))
    write_values(NAME2, pd.DataFrame(rows))


# ======================================================================================================================================
# figure 3: from the subject headings of the books to themes
# ======================================================================================================================================
TAX = DB / 'taxonomy_v3'
BRANCH = 'B05.M02'                                   # middle theme "Race, racism and diversity"; its broad theme is B05
HEADINGS_PER_NARROW = 3
SKIP_HEADING_STARTS = ('Colors ',)                   # children's colour books that the automatic placement put under multicultural / diversity


def tree_data():
    nodes = pd.read_parquet(TAX / 'theme_nodes.parquet', columns=['node_id', 'level', 'parent', 'label', 'label_source'])
    mid = nodes[nodes.node_id == BRANCH].iloc[0]
    broad = nodes[nodes.node_id == mid.parent].iloc[0]
    narrow = nodes[(nodes.parent == BRANCH)].sort_values('node_id')
    assert mid.level == 2 and broad.level == 1 and (narrow.level == 3).all()
    n_mid = int((nodes.parent == broad.node_id).sum())
    print(f'branch: broad {broad.node_id} "{broad.label}" > middle {mid.node_id} "{mid.label}" > narrow '
          + ', '.join(f'{r.node_id} "{r.label}" ({r.label_source})' for r in narrow.itertuples()))
    print('levels in the table:', nodes.groupby('level').size().to_dict(), '| middle themes of this broad theme:', n_mid, '| narrow themes of this middle theme:', len(narrow))
    # heading -> theme value -> narrow node (the chain of 14_v3_headings.py and 15_v3_hierarchy.py), then the most frequent headings of each narrow theme
    target = set(narrow.node_id)
    vn = pd.read_parquet(TAX / 'theme_value_node.parquet', columns=['theme', 'node_id'])
    val2node = {t: n for t, n in zip(vn.theme, vn.node_id) if n in target}
    hp = pd.read_parquet(TAX / 'headings_parsed.parquet', columns=['heading_id', 'heading', 'n_works', 'components_json'])
    rows = []
    for hid, h, nw, cj in zip(hp.heading_id, hp.heading, hp.n_works, hp.components_json):
        for f, v in json.loads(cj):
            if f in ('theme', 'core_theme') and v in val2node:
                rows.append((hid, h, int(nw), v, val2node[v]))
    HV = pd.DataFrame(rows, columns=['heading_id', 'heading', 'n_works', 'theme_value', 'node_id']).drop_duplicates(['heading_id', 'node_id'])
    wh = pd.read_parquet(TAX / 'work_headings.parquet', columns=['work_id', 'heading_id'])
    wt = pd.read_parquet(TAX / 'work_theme.parquet', columns=['work_id', 'node_id', 'level', 'strength'])
    wt = wt[wt.level == 3]
    picked, info = [], {}
    for r in narrow.itertuples():
        g = HV[HV.node_id == r.node_id].sort_values(['n_works', 'heading'], ascending=[False, True]).reset_index(drop=True)
        g['rank_in_theme'] = np.arange(1, len(g) + 1)
        skipped = g[g.heading.str.startswith(SKIP_HEADING_STARTS)]
        g2 = g[~g.heading.str.startswith(SKIP_HEADING_STARTS)].head(HEADINGS_PER_NARROW).copy()
        works_node = wt[wt.node_id == r.node_id]
        g2['share_of_its_works_with_this_theme'] = [float(np.isin(wh[wh.heading_id == hid].work_id.unique(), works_node.work_id.to_numpy()).mean()) for hid in g2.heading_id]
        info[r.node_id] = dict(n_headings=int(g.heading_id.nunique()), n_works=int(works_node.work_id.nunique()),
                               skipped=[(x.heading, x.n_works, x.rank_in_theme) for x in skipped[skipped.rank_in_theme < g2.rank_in_theme.max()].itertuples()])
        if info[r.node_id]['skipped']:
            print(f'  {r.node_id}: skipped (not about this theme, placed there by the automatic rule): ' + '; '.join(f'{h!r} ({n} works, rank {k})' for h, n, k in info[r.node_id]['skipped']))
        print(f'  {r.node_id} "{r.label}": {info[r.node_id]["n_headings"]:,} headings and {info[r.node_id]["n_works"]:,} works reach it; shown: ' + '; '.join(
            f'{x.heading!r} ({x.n_works:,} works, rank {x.rank_in_theme} among its headings, value "{x.theme_value}", {x.share_of_its_works_with_this_theme:.0%} of its works carry the narrow theme)' for x in g2.itertuples()))
        picked.append(g2.assign(narrow_label=r.label))
    return broad, mid, narrow, pd.concat(picked, ignore_index=True), info, n_mid


def card(ax, x, y, w, h, header, lines_h):
    """A column card in the style of 20_figure_pipeline.py: pale body, blue header, square lower corners of the header."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.12', fc=BODY, ec=EDGE, lw=1.4, zorder=1))
    ax.add_patch(FancyBboxPatch((x, y + h - lines_h), w, lines_h, boxstyle='round,pad=0,rounding_size=0.12', fc=HEAD, ec=HEAD, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, y + h - lines_h), w, 0.18, fc=HEAD, ec=HEAD, lw=0, zorder=2))
    ax.text(x + w / 2, y + h - lines_h / 2, header, fontsize=FS_TITLE - 1, fontweight='bold', color='white', va='center', ha='center', linespacing=1.15, zorder=3)


def node_box(ax, cx, cy, w, h, text, bold, fc, ec, size=FS):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle='round,pad=0,rounding_size=0.08', fc=fc, ec=ec, lw=1.4, zorder=4))
    ax.text(cx, cy, text, fontsize=size + (0.5 if bold else 0), fontweight='bold' if bold else 'normal', color=INK, va='center', ha='center', linespacing=1.15, zorder=5)


def connect(ax, sources, target, xmid):
    """Thin grey bracket connector: from each source (right edge midpoint) to one target (left edge midpoint) through a vertical trunk at xmid."""
    (tx, ty) = target
    ys = [s[1] for s in sources]
    for sx, sy in sources:
        ax.plot([sx, xmid], [sy, sy], color=LINE, lw=1.5, zorder=3, solid_capstyle='round')
    if len(ys) > 1:
        ax.plot([xmid, xmid], [min(ys), max(ys)], color=LINE, lw=1.5, zorder=3, solid_capstyle='round')
    ax.add_patch(FancyArrowPatch((xmid, ty), (tx, ty), arrowstyle='-|>', mutation_scale=16, color=LINE, lw=1.5, shrinkA=0, shrinkB=0, zorder=3))


def fig_theme_hierarchy(stamp):
    fonts()
    broad, mid, narrow, heads, info, n_mid = tree_data()
    W, H = 11.0, 6.1
    fig = new_fig(W, H)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')
    ax.text(0.25, H - 0.33, "From the books' subject headings to themes", fontsize=FS_MAIN, fontweight='bold', color=INK, va='center', ha='left')
    top, bottom, hh = H - 0.72, 1.0, 0.95
    widths = [3.25, 2.25, 2.1, 2.15]
    gap = (W - 0.25 * 2 - sum(widths)) / 3
    xs = [0.25]
    for w_ in widths[:-1]:
        xs.append(xs[-1] + w_ + gap)
    heads_hdr = ['Subject headings\nof the books\n(examples)', 'Narrow themes\n(242 in all)', 'Middle theme\n(86 in all)', 'Broad theme\n(19 in all)']
    for x, w_, t in zip(xs, widths, heads_hdr):
        card(ax, x, bottom, w_, top - bottom, t, hh)
    body_top, body_bot = top - hh, bottom
    # column A: three headings per narrow theme
    n_narrow = len(narrow)
    bh, bgap, ggap = 0.40, 0.09, 0.30
    group_h = HEADINGS_PER_NARROW * bh + (HEADINGS_PER_NARROW - 1) * bgap
    total = n_narrow * group_h + (n_narrow - 1) * ggap
    assert total <= body_top - body_bot - 0.2, 'the headings do not fit in the column: lower HEADINGS_PER_NARROW or the box height'
    y = (body_top + body_bot) / 2 + total / 2
    centers_h, group_c = [], []
    for r in narrow.itertuples():
        g = heads[heads.node_id == r.node_id]
        ys = []
        for k, x_ in enumerate(g.itertuples()):
            cy = y - bh / 2
            node_box(ax, xs[0] + widths[0] / 2, cy, widths[0] - 0.24, bh, x_.heading, False, SURFACE, EDGE)
            ys.append(cy)
            y -= bh + bgap
        y += bgap
        group_c.append(np.mean(ys))
        centers_h.append(ys)
        y -= ggap
    # column B: narrow themes
    nw_, nh_ = widths[1] - 0.24, 0.8
    for r, cy, ys in zip(narrow.itertuples(), group_c, centers_h):
        lab = r.label[:1].upper() + r.label[1:]
        node_box(ax, xs[1] + widths[1] / 2, cy, nw_, nh_, '\n'.join(wrap(fig, lab, nw_ - 0.1, FS + 0.5, 'bold')), True, PALE_BLUE, HEAD)
        connect(ax, [(xs[0] + widths[0] - 0.12, yy) for yy in ys], (xs[1] + 0.12, cy), xs[0] + widths[0] + gap / 2)
    # column C: middle theme, column D: broad theme
    cy_mid = float(np.mean(group_c))
    mw = widths[2] - 0.24
    node_box(ax, xs[2] + widths[2] / 2, cy_mid, mw, 0.8, '\n'.join(wrap(fig, mid.label, mw - 0.1, FS + 0.5, 'bold')), True, PALE_BLUE, HEAD)
    connect(ax, [(xs[1] + widths[1] - 0.12, cy) for cy in group_c], (xs[2] + 0.12, cy_mid), xs[1] + widths[1] + gap / 2)
    bw = widths[3] - 0.24
    node_box(ax, xs[3] + widths[3] / 2, cy_mid, bw, 0.8, '\n'.join(wrap(fig, broad.label, bw - 0.1, FS + 0.5, 'bold')), True, PALE_BLUE, HEAD)
    connect(ax, [(xs[2] + widths[2] - 0.12, cy_mid)], (xs[3] + 0.12, cy_mid), xs[2] + widths[2] + gap / 2)
    note = "A work can carry several themes, each with a strength; a theme's demand is the strength-weighted sum of its works' borrowing, as a share of all borrowing in the format."
    nl = wrap(fig, note, W - 0.5, FS)
    ax.text(0.25, bottom - 0.2, '\n'.join(nl), fontsize=FS, color=INK2, va='top', ha='left', linespacing=1.25)
    audit(fig, NAME3)
    save(fig, NAME3, stamp)
    rows = [dict(level='broad theme (19 in all)', node_id=broad.node_id, label=broad.label, parent_node_id='', n_works=pd.NA, note=f'has {n_mid} middle themes'),
            dict(level='middle theme (86 in all)', node_id=mid.node_id, label=mid.label, parent_node_id=mid.parent, n_works=pd.NA,
                 note=f'has {len(narrow)} narrow themes, all shown')]
    for r in narrow.itertuples():
        sk = info[r.node_id]['skipped']
        rows.append(dict(level='narrow theme (242 in all)', node_id=r.node_id, label=r.label, parent_node_id=r.parent, n_works=info[r.node_id]['n_works'],
                         note=f'label source: {r.label_source}' + (' (drawn with a capital first letter)' if r.label[0].islower() else '')
                              + f'; {info[r.node_id]["n_headings"]:,} distinct headings reach it; n_works = works carrying this narrow theme'
                              + ('' if not sk else '; headings skipped as not about this theme (placed there by the automatic embedding rule): '
                                 + ', '.join(f'{h} ({n} works, rank {k})' for h, n, k in sk))))
    for x_ in heads.itertuples():
        rows.append(dict(level='subject heading', node_id=x_.node_id, label=x_.heading, parent_node_id=x_.node_id, n_works=x_.n_works,
                         note=f'theme value "{x_.theme_value}"; rank {x_.rank_in_theme} by number of works among all headings of this narrow theme; '
                              f'{x_.share_of_its_works_with_this_theme:.0%} of the works with this heading carry the narrow theme'))
    df = pd.DataFrame(rows)
    df['n_works'] = df['n_works'].astype('Int64')
    write_values(NAME3, df)


# ======================================================================================================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--rank', action='store_true')
    ap.add_argument('--rise', action='store_true')
    ap.add_argument('--tree', action='store_true')
    ap.add_argument('--stamp', default=STAMP)
    a = ap.parse_args()
    if not (a.rank or a.rise or a.tree):
        raise SystemExit('give at least one of --rank --rise --tree')
    if a.rank:
        fig_rank_accuracy(a.stamp)
    if a.rise:
        fig_lasting_rise_example(a.stamp)
    if a.tree:
        fig_theme_hierarchy(a.stamp)
