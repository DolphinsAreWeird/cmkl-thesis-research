# Conversation sources, borrowing test: shared set-up. Loads the Study 3b machinery (count panel, joint quasi-Poisson event study,
# placebo-category rank) unchanged and adds the rises of the two conversation sources. Record:
# prereg/conversation_sources_settings_2026-10-14.json; choices it does not make: prereg/DEVIATIONS.md (Conversation sources,
# rows dated 2026-10-15 "written before the positive controls were run").
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY3B = HERE.parent / 'main_study' / 'study3b'
sys.path.insert(0, str(STUDY3B))
import json, numpy as np, pandas as pd
import _s3
from _settings import SETTINGS as S
import _paths as IO
import _inference as INF
import _methods as M

B3, INT3 = _s3.build, _s3.interest
REC = json.loads((ROOT / 'prereg' / 'conversation_sources_settings_2026-10-14.json').read_text())   # read only
BOOT_SEED = 20261014
BOOT_N = 2000
REPORT = ROOT / 'data' / 'reports' / 'conversation_sources_results.md'
OUTDIR = ROOT / 'data' / 'db' / 'conversation'
OUTDIR.mkdir(parents=True, exist_ok=True)
SOURCES = {'tweetskb': dict(file=ROOT / 'data/db/interest/tweetskb/shifts.parquet', last_m0='2020-09', title='TweetsKB'),
           'talk_edits': dict(file=ROOT / 'data/db/interest/talk_edits/shifts.parquet', last_m0='2026-03', title='Wikipedia talk edits')}
FIRST_M0 = '2016-01'
LEVELS = ('narrow', 'middle')


def conv_shifts(src):
    """Normalised rises of one conversation source (all levels, all classes), through the Study 3 adapter."""
    X = INT3.normalise_shifts(pd.read_parquet(SOURCES[src]['file']), S)
    if 'near_break' not in X:
        X['near_break'] = False
    X['near_break'] = X.near_break.fillna(False).astype(bool)
    return X


def tested_set(X, src):
    lo, hi = B3.mi_from_ym(FIRST_M0), B3.mi_from_ym(SOURCES[src]['last_m0'])
    return X[X.level.isin(LEVELS) & X.labelled & ~X.seasonal & ~X.near_break & (X.m0 >= lo) & (X.m0 <= hi)].copy()


def make_world(sources=('tweetskb', 'talk_edits')):
    """World of the 3b panel with the placebo screen = Study 3b screen + the starts of the given conversation source(s)."""
    P = IO.Paths()
    meta = IO.load_meta(P)
    base = INF.load_shifts(P, S)
    extra = []
    for s in sources:
        X = conv_shifts(s)
        extra.append(X[X.level.isin(LEVELS)])
    allsh = pd.concat([base] + extra, ignore_index=True)
    world = INF.World(P, S, allsh)
    world.zdir = OUTDIR / 'ztables'
    return P, meta, world
