# Shared look of the thesis figures (16 Oct 2026). Colours are the categorical slots checked earlier with the dataviz validator (light mode) plus gray for context.
# Usage in a figure script:  from _thesis_style import *;  setup();  fig, ax = plt.subplots(...);  clean(ax);  save(fig, 'fig_name', STAMP)
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _settings as ST

DB = ST.DB
ROOT = ST.ROOT
RES = DB / 'benchmark' / 'stage2_results'
FIGS = ROOT / 'paper' / 'figures'
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8a85', '#e4e3df', '#ffffff'
BLUE, ORANGE, AQUA, GRAY, RED = '#2a78d6', '#eb6834', '#1baf7a', '#9a9993', '#e34948'
PALE_BLUE, PALE_GRAY = '#dce8f8', '#f3f3f1'
STAMP = '2026-10-16_0800'


def setup():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'text.color': INK,
                         'xtick.color': INK2, 'ytick.color': INK2, 'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE})


def clean(ax, grid='x'):
    """Thin, recessive axes: no top/right/left spines, light grid on one axis, no tick marks."""
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(axis='both', colors=INK2, labelsize=8, length=0)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURFACE)
    ax.grid(False)
    if grid in ('x', 'both'):
        ax.grid(axis='x', color=GRID, lw=0.8)
    if grid in ('y', 'both'):
        ax.grid(axis='y', color=GRID, lw=0.8)


def dot(ax, x, y, lo=None, hi=None, color=BLUE, filled=True, ms=6.2):
    """Point with a 95% interval drawn as a line; open circle when filled is False."""
    if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi):
        ax.plot([lo, hi], [y, y], color=color, lw=1.6, solid_capstyle='round', zorder=2)
    ax.plot([x], [y], marker='o', ms=ms, mfc=color if filled else SURFACE, mec=color, mew=1.6, zorder=3, ls='none')


def save(fig, name, stamp=STAMP, dpi=200):
    FIGS.mkdir(parents=True, exist_ok=True)
    p = FIGS / f'{name}_{stamp}.png'
    fig.savefig(p, dpi=dpi, facecolor=SURFACE)
    plt.close(fig)
    print('wrote', p)
    return p
