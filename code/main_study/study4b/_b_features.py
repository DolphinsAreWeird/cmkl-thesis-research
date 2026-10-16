# Study 4b feature table: the Study 4 D and W features plus the S features (Study 3 knowledge known at the origin), the change
# target and the surge label. Pure functions; the settings object B comes from _settings.py.
import numpy as np, pandas as pd
import _s4

FE = _s4.features
S_NUM = ['s_sustained', 's_resp']
PART_NUM = {'D': FE.D_NUM, 'W': FE.W_NUM, 'S': S_NUM}
FSET_PARTS = {'D': ['D'], 'D+W': ['D', 'W'], 'D+W+S': ['D', 'W', 'S']}
CAT_COLS = list(FE.CAT_COLS)
# columns that are never features: the level and change targets, the surge label, scoring splits, keys, baseline ingredients
NON_FEATURES = list(FE.NON_FEATURES) + ['change', 'surge', 'tmonth_int']


def feature_columns(fset):
    num = [c for p in FSET_PARTS[fset] for c in PART_NUM[p]]
    return num, list(CAT_COLS)


# ---------------- S feature 1: a sustained Wikipedia shift started in the last 8 weeks ----------------
def sustained_flags(shifts, origins, B):
    """(node_id, origin_mi, s_sustained = 1) for every origin at which a Wikipedia shift that is quality_ok and labelled
    'sustained' started in the last B.sustained_weeks weeks up to the last included week L of the origin month, and whose
    labelling week is on or before L (the label is the real-time one, given in the shift's fourth week).
    NOT IN RECORD: quality_ok shifts only (as the brief for this build says), Wikipedia only, and the same window and week
    alignment as Study 4 (L = last Monday whose Sunday is on or before the last day of the origin month)."""
    sh = shifts[(shifts.source == 'wikipedia') & (shifts.label == 'sustained') & shifts.quality_ok.astype(bool)]
    mis = np.array(sorted(int(m) for m in origins))
    if len(sh) == 0 or len(mis) == 0:
        return pd.DataFrame({'node_id': pd.Series(dtype=object), 'origin_mi': pd.Series(dtype='int64'), 's_sustained': pd.Series(dtype=float)})
    Lw = np.array([np.datetime64(FE.last_week_monday(m), 'D') for m in mis])
    win = np.timedelta64(7 * (B.sustained_weeks - 1), 'D')
    rows = []
    for r in sh.itertuples():
        if pd.isna(r.label_week):
            continue
        start = np.datetime64(pd.Timestamp(r.start_week), 'D')
        lo, hi = np.searchsorted(Lw, start, side='left'), np.searchsorted(Lw, start + win, side='right')
        lab = np.datetime64(pd.Timestamp(r.label_week), 'D')
        for k in range(lo, hi):
            if lab <= Lw[k]:
                rows.append((r.node_id, int(mis[k])))
    X = pd.DataFrame(rows, columns=['node_id', 'origin_mi']).drop_duplicates()
    X['s_sustained'] = 1.0
    return X


# ---------------- S feature 2: category responsiveness ----------------
def prepare_effects(shift_effects, B):
    """Study 3 per-shift synthetic-control effects usable for responsiveness: Wikipedia shifts, main analysis (not the
    seasonal one), synthetic control fitted (sc_ok) with a primary-window effect (months 0 to +2, `sc_effect_p`). `avail_mi` =
    month 0 + 2: the effect is known only once that month is over, so a shift is used at origin t only if avail_mi <= t.
    NOT IN RECORD: Wikipedia and non-seasonal shifts only (Study 3's main analysis); all duration classes; the primary window
    effect sc_effect_p."""
    x = shift_effects[(shift_effects.source == 'wikipedia') & (shift_effects.analysis == 'main')]
    x = x[x.sc_ok.fillna(False).astype(bool) & x.sc_effect_p.notna()]
    return pd.DataFrame(dict(node_id=x.node_id.to_numpy(), format=x.format.to_numpy(), avail_mi=(x.m0 + B.effect_window[1]).to_numpy(),
                             effect=x.sc_effect_p.to_numpy(float)))


def responsiveness(keys, eff):
    """keys: DataFrame with node_id, format, origin_mi. Mean effect of the category's own earlier shifts in the same format
    whose avail_mi <= origin_mi; 0 when there are none.
    NOT IN RECORD: 'same level and format' is read as the category's own node (so its own level) and the row's own format;
    formats are not pooled (the outcome is format-specific)."""
    out = np.zeros(len(keys))
    if len(eff) == 0:
        return out
    book = {}
    for k, g in eff.groupby(['node_id', 'format']):
        g = g.sort_values('avail_mi')
        book[k] = (g.avail_mi.to_numpy(), np.cumsum(g.effect.to_numpy()))
    for k, idx in keys.reset_index(drop=True).groupby(['node_id', 'format']).indices.items():
        if k not in book:
            continue
        ends, cs = book[k]
        n = np.searchsorted(ends, keys.origin_mi.to_numpy()[idx], side='right')
        out[idx] = np.where(n > 0, cs[np.maximum(n - 1, 0)] / np.maximum(n, 1), 0.0)
    return out


# ---------------- table assembly ----------------
def add_s_and_targets(F, shifts, shift_effects, B):
    """Adds s_sustained, s_resp, the change target and the surge label (NaN where the target is missing)."""
    F = F.copy()
    flags = sustained_flags(shifts, F.origin_mi.unique(), B)
    F = F.merge(flags, on=['node_id', 'origin_mi'], how='left')
    F['s_sustained'] = F.s_sustained.fillna(0.0)
    F['s_resp'] = responsiveness(F[['node_id', 'format', 'origin_mi']], prepare_effects(shift_effects, B))
    F['change'] = F.y - F.ls_t
    F['surge'] = np.where(F.change.notna(), (F.change >= B.surge_change).astype(float), np.nan)
    return F


def check_inputs(F4, built, atol=1e-9):
    """The h = 1 and 2 rows rebuilt from the raw inputs must equal the Study 4 feature table (D, W, targets, keys)."""
    keys = ['group', 'format', 'node_id', 'origin_mi', 'h']
    cols = ['y', 'ls_t', 'ls_t1', 'ls_t2', 'ls_ly', 'mean6', 'dlog_total'] + FE.W_NUM + ['split_qok_shift8']
    b = built[built.h.isin((1, 2))]
    if len(b) != len(F4):
        raise SystemExit(f'rebuilt table has {len(b)} rows for h = 1, 2 but the Study 4 table has {len(F4)}')
    m = F4[keys + cols].merge(b[keys + cols], on=keys, suffixes=('_a', '_b'), validate='one_to_one')
    if len(m) != len(F4):
        raise SystemExit('rebuilt and Study 4 tables have different keys')
    for c in cols:
        if not np.allclose(m[c + '_a'].to_numpy(float), m[c + '_b'].to_numpy(float), atol=atol, equal_nan=True):
            raise SystemExit(f'rebuilt column {c} differs from the Study 4 feature table')
