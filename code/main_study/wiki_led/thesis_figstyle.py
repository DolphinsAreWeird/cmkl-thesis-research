"""Shared look of the thesis figures (scripts 94 and 95), set on 14 Nov 2026.

Every figure is drawn at its printed width (6.2 in, the width build_docx.py gives images), with constrained layout and no tight
cropping, so the type is the same true size in every figure: 8 pt, ticks 7.5 pt, panel titles 8.5 pt. Font Helvetica Neue (Arial if
missing). Colours: categorical slots 1 to 4 of the dataviz reference palette, checked with its validator on white (all checks pass;
aqua and yellow sit below 3:1 contrast, so every series also has its own marker shape and a legend or direct label). Each model keeps
its colour and marker in every figure. Gridlines are solid hairlines; only the axis that carries a scale is drawn.
POSTER_FIGS=1 switches to the poster sizes and SVG output in paper/poster/figs/ (paper/poster/build_poster.py inlines them)."""
import os, pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = pathlib.Path(__file__).resolve()
FIG = HERE.parents[3] / 'paper' / 'figures'
POSTER_DIR = HERE.parents[3] / 'paper' / 'poster' / 'figs'
POSTER = os.environ.get('POSTER_FIGS') == '1'

W = 6.2                                        # printed width in inches
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#898781', '#e1e0d9'
BLUE, ORANGE, AQUA, YELLOW, GRAY = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#898781'
LIGHT = '#d9d8d2'                              # neutral fill for context (training years, other months)

ENT = {                                        # entity -> (label, colour, marker)
    'rand': ('Random pick', GRAY, '|'),
    'wiki': ('Wikipedia alone', BLUE, 'o'),
    'pers': ('Persistence rule', YELLOW, '^'),
    'lib': ('Library model', ORANGE, 's'),
    'both': ('Library and Wikipedia', AQUA, 'D'),
}

_names = {f.name for f in font_manager.fontManager.ttflist}
FONT = 'Helvetica Neue' if 'Helvetica Neue' in _names else 'Arial'
BASE = 11 if POSTER else 8
plt.rcParams.update({
    'font.family': FONT, 'font.size': BASE, 'axes.titlesize': BASE + 0.5, 'axes.labelsize': BASE,
    'xtick.labelsize': BASE - 0.5, 'ytick.labelsize': BASE, 'legend.fontsize': BASE - 0.5,
    'text.color': INK, 'axes.labelcolor': INK, 'axes.edgecolor': MUTED, 'axes.linewidth': 0.6,
    'xtick.color': INK2, 'ytick.color': INK, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
    'axes.grid': False, 'grid.color': GRID, 'grid.linewidth': 0.6, 'grid.linestyle': '-',
    'legend.frameon': False, 'legend.handletextpad': 0.4, 'legend.columnspacing': 1.4, 'legend.borderaxespad': 0.2,
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.facecolor': 'white',
    'figure.constrained_layout.use': True, 'figure.constrained_layout.h_pad': 0.04, 'figure.constrained_layout.w_pad': 0.04,
    'savefig.dpi': 300, 'svg.fonttype': 'path', 'pdf.fonttype': 42,
    'axes.titlelocation': 'left', 'axes.titleweight': 'bold', 'axes.titlepad': 6,
})


def figure(h, w=None, **kw):
    """A figure at the printed width (poster: the width given, in inches)."""
    return plt.subplots(figsize=(w or W, h), **kw)


def save(fig, name, stamp):
    if POSTER:
        POSTER_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(POSTER_DIR / f'{name}.svg')
        out = POSTER_DIR / f'{name}.svg'
    else:
        out = FIG / f'{name}_{stamp}.png'
        fig.savefig(out)
    plt.close(fig)
    return out


def rows_axis(ax, labels, top_pad=0.6):
    """Horizontal rows read top to bottom; a hairline grid along x only."""
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_ylim(len(labels) - 0.5, -top_pad)
    ax.tick_params(axis='y', length=0, pad=4)
    ax.grid(axis='x')
    ax.set_axisbelow(True)


def point(ax, est, lo, hi, y, ent, size=None, ring=0):
    """An estimate with its 95% interval: interval 1.4 pt in the series colour, marker on top (a white ring only where markers overlap,
    since a ring cuts short intervals into dashes)."""
    _, col, mk = ENT[ent]
    size = size or (7 if POSTER else 5.2)
    if lo is not None and hi is not None:
        ax.plot([lo, hi], [y, y], color=col, linewidth=1.4, solid_capstyle='round', zorder=2)
    if mk == '|':
        ax.plot([est], [y], marker='|', color=col, markersize=size + 2, markeredgewidth=1.8, linestyle='none', zorder=3)
    else:
        ax.plot([est], [y], marker=mk, color=col, markersize=size * (0.9 if mk == 'D' else 1), markeredgecolor='white',
                markeredgewidth=ring, linestyle='none', zorder=3)


def legend(ax, ents, ncol=None, loc='lower left', anchor=(0, 1.0)):
    hs = []
    for e in ents:
        lab, col, mk = ENT[e]
        if mk == '|':
            hs.append(plt.Line2D([], [], marker='|', color=col, linestyle='none', markersize=7, markeredgewidth=1.8))
        else:
            hs.append(plt.Line2D([], [], marker=mk, color=col, linestyle='none', markersize=5.5, markeredgecolor='white', markeredgewidth=0.7))
    return ax.legend(hs, [ENT[e][0] for e in ents], loc=loc, bbox_to_anchor=anchor, ncol=ncol or len(ents))


def row_labels(ax, items, pad=6):
    """Row labels in the left gutter. Each item is a string, (label, note) for a second line in secondary ink, or ('#', heading)
    for a bold group heading. Rows run 0, 1, 2 ... from the top; set the y limits with rows_axis first."""
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([''] * len(items))
    kw = dict(xycoords=('axes fraction', 'data'), textcoords='offset points', ha='right', annotation_clip=False)
    two = (BASE + 0.5) * 0.5
    for i, it in enumerate(items):
        if isinstance(it, tuple) and it[0] == '#':
            ax.annotate(it[1], xy=(0, i), xytext=(-pad, 0), va='center', fontweight='bold', color=INK, **kw)
        elif isinstance(it, tuple) and it[1]:
            ax.annotate(it[0], xy=(0, i), xytext=(-pad, two), va='center', color=INK, **kw)
            ax.annotate(it[1], xy=(0, i), xytext=(-pad, -two), va='center', color=INK2, fontsize=BASE - 0.5, **kw)
        else:
            ax.annotate(it[0] if isinstance(it, tuple) else it, xy=(0, i), xytext=(-pad, 0), va='center', color=INK, **kw)


def value_label(ax, x, y, text, dx=5):
    ax.annotate(text, (x, y), xytext=(dx, 0), textcoords='offset points', va='center', ha='left', color=INK2, fontsize=BASE - 0.5)
