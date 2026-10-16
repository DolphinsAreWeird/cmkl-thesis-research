# Shared set-up of the Brisbane replication (record: prereg/brisbane_replication_settings_2026-10-15.json, SHA-256 in prereg/README.md).
# Reuses the Study 3b modules (count model, inference, panel helpers) from code/main_study/study3b/ unchanged. Settings are the checked Study 3b
# settings object (which also checks the Study 3 record and addenda) with the Brisbane record's changes applied on a copy. Run with `python -I`.
import sys, json, re, copy, hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
CODE = ROOT / 'code'
S3B = CODE / 'main_study' / 'study3b'
for p in (str(S3B), str(CODE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np, pandas as pd
import _s3, _paths as IO, _inference as INF, _methods as M, _panel as PN
from _settings import SETTINGS as S0

RECORD = ROOT / 'prereg' / 'brisbane_replication_settings_2026-10-15.json'
README = ROOT / 'prereg' / 'README.md'
DB = ROOT / 'data' / 'db' / 'brisbane'
REP = ROOT / 'data' / 'reports'
RAW = ROOT / 'data' / 'raw' / 'brisbane'
B3, I3 = _s3.build, _s3.inputs
FORMAT = 'all'                      # a single pooled series (record: formats pooled)
LEVELS = ('narrow', 'middle')       # record: narrow and middle levels
MONTH0_FROM, MONTH0_TO = '2016-01', '2025-06'     # record: month 0 from 2016-01 to 2025-06
CLOSURE = (0.5, 12, 6)              # record: below half of the median of the previous 12 months, at least 6 needed
MIN_DAYS = 2                        # record: a month is usable only with at least 2 sampled days
BOOT_SEED = 20261015                # record: 2,000 resamples, seed 20261015
LIFTS = (0.2, 0.5, 1.0)             # record: +20%, +50%, +100%; 200 draws


def record_ok():
    got = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    m = re.search(r'brisbane_replication_settings_2026-10-15\.json` SHA-256: ([0-9a-f]{64})', README.read_text())
    if not m or m.group(1) != got:
        raise SystemExit(f'Brisbane record hash {got} does not match prereg/README.md; nothing runs.')
    return got


SHA = record_ok()
REC = json.loads(RECORD.read_text())
S = copy.copy(S0)
S.levels_tested = LEVELS
S.seattle_formats = (FORMAT,)
S.power_lifts = LIFTS
S.study_start = MONTH0_FROM          # record: month 0 from 2016-01 (also the first month 0 of the power units)
S.boot_seed = BOOT_SEED
S.power_seed = BOOT_SEED
S.sha256 = 'brisbane:' + SHA + ':' + S0.sha256       # keys the z-table cache
assert S.boot_n == 2000 and S.power_draws == 200 and S.es_fit_len == 24 and S.es_fit_end == -7 and S.window_primary == (0, 2)


class BPaths:
    """What INF.World and the 3b helpers read from a Paths object, pointed at data/db/brisbane/ (taxonomy and interest are the real ones, read only)."""
    sim = False

    def __init__(self):
        DB.mkdir(parents=True, exist_ok=True)
        self.db, self.rep = DB, REP
        self.interest = ROOT / 'data' / 'db' / 'interest'
        self.study3 = ROOT / 'data' / 'db' / 'study3'
        self.taxo_v3 = ROOT / 'data' / 'db' / 'taxonomy_v3'
        self.taxo_v2 = ROOT / 'data' / 'db' / 'taxonomy_v2'
        self.librivox_listening = ROOT / 'data' / 'db' / 'listening.parquet'
        self.meta = DB / 'panel_meta.json'
        self.counts = DB / 'counts_brisbane.parquet'
        self.counts_librivox = DB / 'none_librivox.parquet'      # never exists: no LibriVox in this study
        self.months = DB / 'month_status.parquet'
        self.categories = DB / 'categories.parquet'
        self.shifts_value = DB / 'none_value.parquet'


def load_shifts(P):
    """Study 3 interest shifts (narrow and middle), through the Study 3 adapter (Mondays, classes, quality flags, m0)."""
    f3 = P.interest / INT3().SHIFTS_FILE
    X = INT3().normalise_shifts(pd.read_parquet(f3), S)
    return X[X.level.isin(LEVELS)].reset_index(drop=True)


def INT3():
    return _s3.interest


def make_world(P=None):
    P = P or BPaths()
    shifts = load_shifts(P)
    w = INF.World(P, S, shifts)
    import json as _j
    INF._WORLD[_j.dumps({'sim': None}, sort_keys=True)] = w         # run_tasks(workers=1) then reuses this world (no worker processes)
    return w, shifts


def ztables_all(world, level, lo, hi):
    return {m: world.ztable('seattle', level, m) for m in range(lo, hi + 1)}
