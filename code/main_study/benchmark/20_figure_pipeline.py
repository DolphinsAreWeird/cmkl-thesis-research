# Thesis figure: the five stages every forecast passes through and the alternatives compared at each (drawn from the settings records; no results).
# Output: paper/figures/fig1_pipeline_benchmark_<stamp>.png
# Text size: the smallest text is 12.5 pt on an 11-inch canvas, which is 7.4 pt when the figure is shown 6.5 inches wide (the width of a thesis page).
#   ../../../.venv/bin/python 20_figure_pipeline.py [--stamp YYYY-MM-DD_HHMM]
import sys, time, pathlib, argparse, textwrap
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import _settings as ST

FIGS = ST.ROOT / 'paper' / 'figures'
SURFACE, INK, MUTED, HEAD, EDGE, BODY = '#ffffff', '#1d2430', '#5b6575', '#2a6fdb', '#c9d3e3', '#f3f6fb'

STAGES = [
    ('1', 'Categories\nfrom books', ['Themes from library subject headings (86 middle, 242 narrow)', 'Themes learned from catalogue descriptions (86 and 242 clusters)']),
    ('2', 'Routing\nbehavior\ninto themes', ['Hand-checked concept pages', 'Top 500 pages, matched by embedding', 'Top 500 pages, read in context', "Books' and authors' own articles", 'Articles weighted by past demand']),
    ('3', 'Representing\nthe signal', ['Volume and change', 'News volume and tone', 'State of a lasting rise', 'Duration-weighted interest']),
    ('4', 'Predicting', ['Repeat last month, seasonal repeat, mean of 6 months', 'Ridge, LightGBM, CatBoost, on the level or the change', 'Chronos-Bolt and Chronos-2, with or without interest', 'Averages and medians of models']),
    ('5', 'Judging', ["Task 1: the level of next month's borrowing", 'Task 2: which themes will rise', 'Error ratio, rank correlation, 90% confidence set', 'Final test on later months']),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stamp', default=time.strftime('%Y-%m-%d_%H%M'))
    a = ap.parse_args()
    W, Hh = 11.0, 7.3
    fig = plt.figure(figsize=(W, Hh), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, Hh); ax.axis('off')
    ax.text(0.25, Hh - 0.4, 'Five stages, and the alternatives compared at each', fontsize=16.5, fontweight='bold', color=INK, va='center', ha='left')
    w, gap, x0, ytop, h_head, h_body = 1.98, 0.18, 0.25, Hh - 0.8, 0.95, 4.45
    for i, (num, name, items) in enumerate(STAGES):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, ytop - h_head - h_body), w, h_body + h_head, boxstyle='round,pad=0,rounding_size=0.1', fc=BODY, ec=EDGE, lw=1.4))
        ax.add_patch(FancyBboxPatch((x, ytop - h_head), w, h_head, boxstyle='round,pad=0,rounding_size=0.1', fc=HEAD, ec=HEAD, lw=1.4))
        ax.add_patch(plt.Rectangle((x, ytop - h_head), w, 0.16, fc=HEAD, ec=HEAD, lw=0))   # square the header's lower corners
        ax.text(x + 0.14, ytop - h_head / 2, num, fontsize=22, fontweight='bold', color='white', va='center', ha='left')
        ax.text(x + 0.5, ytop - h_head / 2, name, fontsize=13.5, fontweight='bold', color='white', va='center', ha='left', linespacing=1.15)
        y = ytop - h_head - 0.28
        for it in items:
            lines = textwrap.wrap(it, 16)
            ax.text(x + 0.12, y, '•', fontsize=14, color=HEAD, va='top', ha='left')
            ax.text(x + 0.3, y, '\n'.join(lines), fontsize=12.5, color=INK, va='top', ha='left', linespacing=1.2)
            y -= 0.232 * len(lines) + 0.17
        if i < len(STAGES) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.01, ytop - h_head / 2), (x + w + gap - 0.01, ytop - h_head / 2), arrowstyle='-|>', mutation_scale=14, color=MUTED, lw=1.6))
    foot = ytop - h_head - h_body - 0.22
    for k, t in enumerate(['Demand: monthly borrowing by theme and format (Seattle Public Library; printed books and ebooks first,\nthen audiobooks) and listening on LibriVox.',
                           'Behavior: weekly Wikipedia page views and news coverage, routed into the same themes.']):
        ax.text(0.25, foot - (0.0 if k == 0 else 0.56), t, fontsize=12.5, color=MUTED, va='top', ha='left', linespacing=1.25)
    p = FIGS / f'fig1_pipeline_benchmark_{a.stamp}.png'
    fig.savefig(p, dpi=200, facecolor=SURFACE)
    print('wrote', p)


if __name__ == '__main__':
    main()
