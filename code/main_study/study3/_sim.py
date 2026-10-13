# Simulated worlds for testing the Study 3 methods and scripts without touching real demand.
# A world has the same tables as a real build: nodes, demand panel (same columns), donor overlap, interest shifts and
# weekly GDELT tone, plus the true injected effects. Log shares follow
#   level + trend + loading x common format factor + seasonal pattern + AR(1) noise (+ injected effects),
# with the record's digital missing months removed and print ending early, as in the real data.
import numpy as np, pandas as pd
from _build import mi_from_ym, ym_of, size_columns
from _files import save_parquet, save_json

TOTAL = 150_000          # checkouts per format-month in the simulated library


def sim_nodes(S, n_broad=8, n_mid=4, n_narrow=3):
    rows = []
    for b in range(1, n_broad + 1):
        bid = f'B{b:02d}'
        rows.append((bid, 'broad', None, f'Broad {b}', bid))
        for m in range(1, n_mid + 1):
            mid = f'{bid}.M{m:02d}'
            rows.append((mid, 'middle', bid, f'Middle {b}.{m}', bid))
            for n in range(1, n_narrow + 1):
                rows.append((f'{mid}.N{n:02d}', 'narrow', mid, f'Narrow {b}.{m}.{n}', bid))
    N = pd.DataFrame(rows, columns=['node_id', 'level', 'parent', 'label', 'broad_id'])
    for k, c in enumerate(S.controls):            # control labels on narrow nodes in different broad groups
        nid = f'B{k + 1:02d}.M01.N01'
        N.loc[N.node_id == nid, 'label'] = c['label']
    return N


def control_nodes(N, S):
    return {c['name']: N[(N.label == c['label']) & (N.level == c['level'])].node_id.iloc[0] for c in S.controls}


def sim_shifts(rng, N, S, grid_end, null):
    """Random shifts on 40% of narrow and middle nodes, plus one at each control month for the control nodes."""
    rows = []
    lo, hi = mi_from_ym(S.study_start) + 5, grid_end - 8
    cands = N[N.level.isin(S.levels_tested)].node_id.tolist()
    ctrl = control_nodes(N, S)
    for n in rng.choice(cands, size=int(0.4 * len(cands)), replace=False):
        for _ in range(rng.integers(1, 3)):
            rows.append((n, int(rng.integers(lo, hi))))
    for c in S.controls:
        rows.append((ctrl[c['name']], mi_from_ym(c['shift_month'])))
    out = []
    for n, m0 in rows:
        y, m = divmod(m0, 12)
        first = pd.Timestamp(year=y, month=m + 1, day=1)
        monday = first + pd.Timedelta(days=(7 - first.weekday()) % 7) + pd.Timedelta(weeks=int(rng.integers(0, 3)))
        dur = int(rng.integers(1, 9))
        cls = 'sustained' if dur >= S.sustained_min else ('intermediate' if dur == S.intermediate_eq else 'fading')
        size = float(1.5 + rng.lognormal(0.0, 0.6))
        out.append(dict(source=str(rng.choice([S.primary_source, S.secondary_source])), node_id=n,
                        level=N.set_index('node_id').level[n], start_week=monday, duration_class=cls, duration_count=dur,
                        size=size, large=size >= S.large_ratio, seasonal=bool(rng.random() < 0.1)))
    X = pd.DataFrame(out).drop_duplicates(['source', 'node_id', 'start_week']).reset_index(drop=True)
    X['m0'] = (X.start_week.dt.year * 12 + X.start_week.dt.month - 1).astype(np.int64)
    X['true_effect'] = 0.0 if null else true_effect(X, S)
    ctrl_rows = X.node_id.isin(ctrl.values())
    lost = rng.choice(np.flatnonzero(~ctrl_rows.to_numpy()), size=3, replace=False)   # no real-time label possible
    X.loc[lost, 'duration_class'] = 'interrupted'
    X.loc[lost, 'true_effect'] = 0.0
    return X


def true_effect(X, S):
    """Known effect of a shift on log share in months 0..+2 (half of it in months 3..5): rises with log(size) for
    sustained shifts, half for intermediate, none for fading or seasonal shifts."""
    base = 0.08 + 0.18 * np.log(X['size'])
    mult = X.duration_class.map({'sustained': 1.0, 'intermediate': 0.5, 'fading': 0.0})
    return np.where(X.seasonal, 0.0, base * mult)


def _unit_series(rng, grid, F, noise):
    t = (grid - grid[0]) / 120.0
    lvl = rng.uniform(np.log(0.003), np.log(0.03))
    trend = rng.normal(0.0, 0.15)
    load = rng.uniform(0.6, 1.4)
    amp = rng.uniform(0.0, 0.12); ph = rng.uniform(0, 2 * np.pi)
    seas = amp * np.sin(2 * np.pi * (grid % 12) / 12 + ph)
    e = np.zeros(len(grid))
    eps = rng.normal(0.0, noise, len(grid))
    for i in range(1, len(grid)):
        e[i] = 0.3 * e[i - 1] + eps[i]
    return lvl + trend * t + load * F + seas + e


def sim_world(S, seed=0, start='2012-01', end='2026-08', print_end='2020-07', null=False, noise=0.05,
              n_broad=8, n_mid=4, n_narrow=3, librivox=True, control_lift=0.35):
    rng = np.random.default_rng(seed)
    N = sim_nodes(S, n_broad, n_mid, n_narrow)
    g0, g1 = mi_from_ym(start), mi_from_ym(end)
    grid = np.arange(g0, g1 + 1)
    shifts = sim_shifts(rng, N, S, g1, null)
    ctrl = control_nodes(N, S)
    small = set(N[N.level == 'narrow'].node_id.iloc[-3:])         # three narrow nodes fail the size rule
    formats = list(S.seattle_formats) + (['librivox'] if librivox else [])
    parts = []
    for fmt in formats:
        F = np.cumsum(rng.normal(0.0, 0.02, len(grid)))
        fgrid = grid
        if fmt == 'print':
            fgrid = grid[grid <= mi_from_ym(print_end)]
        if fmt == 'librivox':
            fgrid = grid[grid >= mi_from_ym(S.study_start)]
        Ff = F[np.isin(grid, fgrid)]
        missing = set(mi_from_ym(list(S.missing_months))) if fmt in S.digital_formats else set()
        for _, nd in N.iterrows():
            y = _unit_series(rng, fgrid, Ff, noise)
            for _, sh in shifts[shifts.node_id == nd.node_id].iterrows():
                rel = fgrid - sh.m0
                y = y + sh.true_effect * ((rel >= 0) & (rel <= 2)) + 0.5 * sh.true_effect * ((rel >= 3) & (rel <= 5))
            for c in S.controls:
                if nd.node_id == ctrl[c['name']] and fmt in S.digital_formats and not null:
                    rel = fgrid - mi_from_ym(c['shift_month'])
                    y = y + control_lift * ((rel >= 0) & (rel <= 5))
            ok = ~np.isin(fgrid, list(missing))
            w = np.where(ok, np.exp(y) * TOTAL, np.nan)
            nw = 8 if nd.node_id in small else int(rng.integers(40, 200))
            parts.append(pd.DataFrame({'level': nd.level, 'node_id': nd.node_id, 'parent': nd.parent, 'broad_id': nd.broad_id,
                                       'label': nd.label, 'format': fmt, 'mi': fgrid, 'month_ok': ok,
                                       'weighted_checkouts': w, 'total_checkouts': np.where(ok, float(TOTAL), np.nan),
                                       'n_works_month': np.where(ok, nw // 2, 0), 'n_works_24m': nw}))
    P = pd.concat(parts, ignore_index=True)
    P['share'] = P.weighted_checkouts / P.total_checkouts
    P['log_share'] = np.log(P.share)
    P['ym'] = [ym_of(m) for m in P.mi]
    P = pd.concat([size_columns(g, S) for _, g in P.groupby('format')], ignore_index=True)
    cols = ['level', 'node_id', 'parent', 'broad_id', 'label', 'format', 'ym', 'mi', 'month_ok', 'weighted_checkouts',
            'total_checkouts', 'share', 'log_share', 'n_works_month', 'n_works_24m', 'median_weighted_24m',
            'months_avail_24m', 'size_ok']
    P = P[cols]
    return dict(panel=P[P.format != 'librivox'].reset_index(drop=True), librivox=P[P.format == 'librivox'].reset_index(drop=True),
                nodes=N, overlap=sim_overlap(rng, N, formats), shifts=shifts,
                tone=sim_tone(rng, N, shifts, S, end), controls=ctrl)


def sim_overlap(rng, N, formats):
    rows = []
    for level, g in N.groupby('level'):
        ids = g.node_id.tolist()
        for a in ids:
            for b in ids:
                if a != b and rng.random() < 0.05:
                    s = float(rng.uniform(0.0, 0.3))
                    for f in formats:
                        rows.append((level, f, a, b, 100, int(100 * s), s))
    return pd.DataFrame(rows, columns=['level', 'format', 'node_a', 'node_b', 'n_works_a', 'n_shared', 'share_of_a'])


def sim_tone(rng, N, shifts, S, end):
    """Weekly GDELT-like tone per node; in the first weeks of a shift the tone drops in proportion to its effect."""
    weeks = pd.date_range('2015-06-01', pd.Timestamp(end + '-28'), freq='7D')
    rows = []
    for _, nd in N.iterrows():
        base = -1.5 + rng.normal(0, 0.3)
        e = rng.normal(0, 0.25, len(weeks))
        tone = base + e
        for _, sh in shifts[shifts.node_id == nd.node_id].iterrows():
            k = (weeks >= sh.start_week) & (weeks < sh.start_week + pd.Timedelta(weeks=S.tone_weeks))
            tone[k] -= 2.0 * sh.true_effect
        pos = 2.0 + 0.5 * e; neg = pos - tone
        rows.append(pd.DataFrame({'node_id': nd.node_id, 'level': nd.level, 'week': weeks, 'tone': tone,
                                  'tone_pos': pos, 'tone_neg': neg, 'mentions': 1000}))
    return pd.concat(rows, ignore_index=True)


def write_world(P, W, S):
    """Write a simulated world where the real files would be, inside the --sim folder."""
    P.interest.mkdir(parents=True, exist_ok=True)
    save_parquet(W['panel'], P.panel)
    if len(W['librivox']):
        save_parquet(W['librivox'], P.panel_librivox)
    save_parquet(W['nodes'], P.nodes)
    save_parquet(W['overlap'], P.overlap)
    sh = W['shifts'].drop(columns=['m0'])
    # the interest side's own layout (label, dur_rt, integer levels), so the adapter's mapping is exercised
    lv = {'broad': 1, 'middle': 2, 'narrow': 3}
    real = sh.drop(columns=['true_effect']).rename(columns={'duration_class': 'label', 'duration_count': 'dur_rt'})
    real['level'] = real.level.map(lv)
    save_parquet(real, P.interest / 'shifts.parquet')
    save_parquet(sh, P.db / 'sim_truth_shifts.parquet')
    (P.interest / 'gdelt').mkdir(parents=True, exist_ok=True)
    tone = W['tone'].rename(columns={'tone_pos': 'positive', 'tone_neg': 'negative'}).assign(source='gdelt', partial_week=False)
    tone['level'] = tone.level.map(lv)
    save_parquet(tone, P.interest / 'gdelt' / 'weekly_node.parquet')
    save_json(W['controls'], P.db / 'sim_truth_controls.json')
