# Shared test helpers: simulated worlds (Study 4's builder, through _s4) turned into Study 4b feature tables.
import sys, pathlib, copy
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _settings as ST, _s4, _b_features as BF, _b_run as BR, _b_models as BM, _b_eval as EV

B = ST.settings()
MI = ST.mi_from_ym
sim = _s4.load_sim()


def fast_settings(iterations=120, horizons=None):
    """The record's settings with fewer CatBoost trees (tests only: the worlds have a few hundred rows) and optionally fewer horizons."""
    b = copy.copy(B)
    b.s4 = copy.copy(B.s4)
    b.cb_iterations = b.s4.cb_iterations = iterations
    if horizons:
        b.horizons = tuple(horizons)
    return b


def empty_effects():
    return pd.DataFrame(dict(source=pd.Series(dtype=str), analysis=pd.Series(dtype=str), sc_ok=pd.Series(dtype=bool),
                             sc_effect_p=pd.Series(dtype=float), node_id=pd.Series(dtype=str), format=pd.Series(dtype=str),
                             m0=pd.Series(dtype='int64')))


def add_effect(eff, node, fmt, m0, effect, source='wikipedia', analysis='main', sc_ok=True):
    row = pd.DataFrame([dict(source=source, analysis=analysis, sc_ok=sc_ok, sc_effect_p=effect, node_id=node, format=fmt, m0=int(m0))])
    return pd.concat([eff, row], ignore_index=True)


def features(world, effects=None, b=None):
    """Study 4b table (horizons 1, 2, 3) for a simulated world."""
    b = b or B
    S4h = copy.copy(b.s4)
    S4h.horizons = (1, 2, 3)
    F = sim.build(world, S4h)
    return BF.add_s_and_targets(F, world['shifts'], effects if effects is not None else empty_effects(), b)


def world(beta=1.0, seed=0, **kw):
    kw.setdefault('formats', ('print', 'ebook'))
    return sim.make_world(beta=beta, seed=seed, **kw)


def run_origins(F, b, first, last, parts=('A', 'B')):
    out = [BR.forecast_origin(F, m, b, 1, parts=parts) for m in range(MI(first), MI(last) + 1)]
    return pd.concat([o for o in out if len(o)], ignore_index=True)
