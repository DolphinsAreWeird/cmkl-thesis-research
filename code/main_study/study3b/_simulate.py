# Simulated worlds for testing the Study 3b methods and scripts without touching real demand.
#  sim_counts: a Counts object (the dense data of one level) with known truth, for the method tests.
#  write_world: files with the layout of a real run (counts, month status, categories, shifts, tone) for the script chain.
# Counts follow Poisson (or negative binomial) draws around  exposure x exp(level + trend + month-of-year effect)  with the
# record's digital missing months removed, as in the real data.
import numpy as np, pandas as pd
import _s3
from _methods import Counts
import _paths as IO

B3 = _s3.build
FORMATS = ('audiobook', 'ebook', 'print')


def sim_counts(seed, sizes, T=120, mi0=2012 * 12, effects=(), overdisp=0.0, trend_sd=0.004, season_sd=0.15, missing=(), formats=FORMATS,
               exposure=(80_000, 140_000), ids=None):
    """sizes: mean monthly count per format of each category (length K). effects: (category index, m0, lift) multiplying the
    mean in months m0..m0+2. missing: month indices (usable False in every format). Returns Counts and the truth dict."""
    rng = np.random.default_rng(seed)
    K = len(sizes)
    sizes = np.asarray(sizes, dtype=float)
    N = {f: rng.integers(*exposure, size=T).astype(float) for f in formats}
    ok = {f: np.ones(T, bool) for f in formats}
    for m in missing:
        for f in formats:
            ok[f][m - mi0] = False
    t = np.arange(T)
    trend = rng.normal(0, trend_sd, K)
    season = rng.normal(0, season_sd, (K, 12))
    fmt_off = {f: rng.normal(0, 0.5, K) for f in formats}
    cal = (mi0 + t) % 12
    Y = {}
    for f in formats:
        rate = sizes[:, None] / N[f].mean() * np.exp(fmt_off[f][:, None] + trend[:, None] * (t[None] - T / 2) + season[:, cal])
        lam = rate * N[f][None]
        for (c, m0, lift) in effects:
            lam[c, m0 - mi0:m0 - mi0 + 3] *= 1 + lift
        if overdisp > 0:
            lam = lam * rng.gamma(1 / overdisp, overdisp, size=lam.shape)
        y = rng.poisson(lam).astype(float)
        y[:, ~ok[f]] = np.nan
        Y[f] = y
        N[f] = np.where(ok[f], N[f], np.nan)
    ids = np.arange(K) if ids is None else np.asarray(ids)
    return Counts(mi0, ids, Y, N, ok), dict(sizes=sizes, effects=list(effects))


# ---------------- a world with the layout of a real run ----------------
def _monday_in(rng, m0):
    y, m = divmod(m0, 12)
    first = pd.Timestamp(year=y, month=m + 1, day=1)
    return first + pd.Timedelta(days=(7 - first.weekday()) % 7) + pd.Timedelta(weeks=int(rng.integers(0, 3)))


def _shift_rows(rng, S, level_code, ids, grid_end, share=0.4, effect_ids=(), effect_months=None, null=False):
    """Interest-side shift rows (layout of interest/shifts.parquet, only the columns the adapter needs plus a few) and the
    list of true effects (category, m0, lift)."""
    rows, eff = [], []
    lo, hi = B3.mi_from_ym(S.study_start) + 6, grid_end - 8
    picks = [(n, int(rng.integers(lo, hi))) for n in rng.choice(ids, size=int(share * len(ids)), replace=False) for _ in range(int(rng.integers(1, 3)))]
    picks += [(n, m) for n, m in (effect_months or [])]
    for n, m0 in picks:
        dur = int(rng.integers(1, 9))
        cls = 'sustained' if dur >= S.sustained_min else ('intermediate' if dur == S.intermediate_eq else 'fading')
        size = float(1.5 + rng.lognormal(0.0, 0.6))
        lift = 0.0 if null else (0.8 if (n in effect_ids or rng.random() < 0.3) else 0.0)
        rows.append(dict(source=str(rng.choice(['wikipedia', 'gdelt'])), level=level_code, node_id=n, start_week=_monday_in(rng, m0), label=cls,
                         dur_rt=dur, whole_duration=dur + int(rng.integers(0, 3)), size=size, large=size >= S.large_ratio,
                         seasonal=bool(rng.random() < 0.1), quality_flag='', quality_ok=bool(rng.random() > 0.15)))
        if lift:
            eff.append((n, m0, lift))
    X = pd.DataFrame(rows).drop_duplicates(['source', 'node_id', 'start_week']).reset_index(drop=True)
    X['id'] = np.arange(len(X))
    return X, eff


def write_world(P, S, seed=0, null=False, n_broad=4, n_mid=3, n_narrow=3, n_values=90, T=120, mi0=2012 * 12):
    """Write a simulated world in the layout of a real run into P (a Paths with sim set): counts_seattle, counts_librivox,
    month_status, categories, panel_meta, shifts_value, interest/shifts.parquet, interest/gdelt tone files. Returns the meta."""
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(1, n_broad + 1):
        for m in range(1, n_mid + 1):
            mid = f'B{b:02d}.M{m:02d}'
            rows.append(('middle', mid, f'B{b:02d}', f'B{b:02d}', f'Middle {b}.{m}'))
            for n in range(1, n_narrow + 1):
                rows.append(('narrow', f'{mid}.N{n:02d}', mid, f'B{b:02d}', f'Narrow {b}.{m}.{n}'))
    cats = pd.DataFrame(rows, columns=['level', 'node_id', 'parent', 'broad_id', 'label'])
    ctrl = {}
    for k, c in enumerate(S.controls):                      # controls on narrow nodes of different broad groups, large enough to be tested
        nid = f'B{k + 1:02d}.M01.N01'
        cats.loc[cats.node_id == nid, 'label'] = c['label']
        ctrl[c['name']] = nid
    narrow_ids = cats[cats.level == 'narrow'].node_id.tolist()
    vals = [(f'value {i:03d}', narrow_ids[i % len(narrow_ids)]) for i in range(n_values)]
    vcats = pd.DataFrame({'level': 'value', 'node_id': [v for v, _ in vals], 'parent': [p for _, p in vals],
                          'broad_id': [p.split('.')[0] for _, p in vals], 'label': [v for v, _ in vals]})
    cats = pd.concat([cats, vcats], ignore_index=True)
    grid_end = mi0 + T - 1
    missing = tuple(B3.mi_from_ym(m) for m in S.missing_months)
    status = []
    for f in S.seattle_formats:
        for mi in range(mi0, grid_end + 1):
            ok = not (f in S.digital_formats and mi in missing)
            status.append(dict(format=f, mi=mi, month_ok=ok, total_checkouts=float(rng.integers(80_000, 140_000)) if ok else np.nan,
                               n_rows=1000, reason='' if ok else 'missing in record'))
    lv0 = B3.mi_from_ym('2017-01')
    for mi in range(lv0, grid_end + 1):
        status.append(dict(format='librivox', mi=mi, month_ok=True, total_checkouts=float(rng.integers(3_000_000, 4_000_000)), n_rows=100, reason=''))
    status = pd.DataFrame(status)
    # shifts and true effects (the controls get a clear lift)
    eff_ids = set(ctrl.values())
    ctrl_months = [(ctrl[c['name']], B3.mi_from_ym(c['shift_month'])) for c in S.controls]
    X3, eff3 = _shift_rows(rng, S, 3, narrow_ids, grid_end, effect_ids=eff_ids, effect_months=ctrl_months, null=null)
    X2, eff2 = _shift_rows(rng, S, 2, cats[cats.level == 'middle'].node_id.tolist(), grid_end, null=null)
    Xv, effv = _shift_rows(rng, S, 4, [v for v, _ in vals], grid_end, null=null)
    # counts: category sizes spread from very small to large; effects applied to all formats
    tables = {}
    for level, ids, eff in (('narrow', narrow_ids, eff3), ('middle', cats[cats.level == 'middle'].node_id.tolist(), eff2), ('value', [v for v, _ in vals], effv)):
        idx = {n: i for i, n in enumerate(ids)}
        sizes = 10 ** rng.uniform(-0.3, 2.8 if level != 'value' else 2.3, len(ids))
        if level == 'narrow':
            for n in ctrl.values():
                sizes[idx[n]] = 120.0
        C, _ = sim_counts(int(rng.integers(1 << 30)), sizes, T=T, mi0=mi0, effects=[(idx[n], m0, l) for n, m0, l in eff if m0 + 3 <= grid_end],
                          overdisp=0.03, missing=missing_digital(S, missing), ids=ids)
        tables[level] = C
    long = []
    for level, C in tables.items():
        for f in S.seattle_formats:
            y = np.nan_to_num(C.Y[f])
            if f in S.digital_formats:
                pass
            r, c = np.nonzero(y > 0)
            long.append(pd.DataFrame({'level': level, 'node_id': C.ids[r], 'format': f, 'mi': c + mi0, 'y': y[r, c]}))
    long = pd.concat(long, ignore_index=True)
    # month_ok of the sim: digital missing months have no stored rows; mark them in status (done above)
    lvl = []
    for level, ids in (('narrow', narrow_ids), ('middle', cats[cats.level == 'middle'].node_id.tolist()), ('value', [v for v, _ in vals][:30])):
        sizes = 10 ** rng.uniform(0.3, 2.5, len(ids))
        Cl, _ = sim_counts(int(rng.integers(1 << 30)), sizes, T=grid_end - lv0 + 1, mi0=lv0, formats=('librivox',), overdisp=0.1, ids=ids, exposure=(3_000_000, 4_000_000))
        y = np.nan_to_num(Cl.Y['librivox'])
        r, c = np.nonzero(y > 0)
        lvl.append(pd.DataFrame({'level': level, 'node_id': Cl.ids[r], 'format': 'librivox', 'mi': c + lv0, 'y': y[r, c]}))
    lvl = pd.concat(lvl, ignore_index=True)
    IO.save_parquet(long, P.counts); IO.save_parquet(lvl, P.counts_librivox); IO.save_parquet(status, P.months)
    IO.save_parquet(cats, P.categories)
    # interest side
    (P.interest / 'gdelt').mkdir(parents=True, exist_ok=True)
    keep = ['id', 'start_week', 'label', 'size', 'dur_rt', 'whole_duration', 'source', 'level', 'node_id', 'seasonal', 'large', 'quality_ok', 'quality_flag']
    IO.save_parquet(pd.concat([X3, X2], ignore_index=True)[keep], P.interest / 'shifts.parquet')
    IO.save_parquet(Xv[keep], P.shifts_value)
    tone_weeks = pd.date_range('2016-12-26', '2022-12-26', freq='7D')
    nt, vt = [], []
    for level, code, ids in ((3, 3, narrow_ids), (2, 2, cats[cats.level == 'middle'].node_id.tolist()), (4, 4, [v for v, _ in vals])):
        for n in ids:
            base = rng.normal(-1.5, 0.5)
            pos = np.abs(rng.normal(3.0, 0.4, len(tone_weeks))); neg = np.abs(rng.normal(4.5, 0.5, len(tone_weeks)))
            tone = pos - neg + base * 0.0
            d = pd.DataFrame({'week': tone_weeks, 'tone': tone, 'positive': pos, 'negative': neg, 'mentions': 500.0, 'partial_week': False})
            d.loc[0, 'partial_week'] = True
            (vt if level == 4 else nt).append(d.assign(level=code, node_id=n, value=n))
    nt = pd.concat(nt, ignore_index=True).drop(columns='value'); vt = pd.concat(vt, ignore_index=True).drop(columns='level')
    IO.save_parquet(nt, P.interest / 'gdelt' / 'weekly_node.parquet')
    IO.save_parquet(vt, P.interest / 'gdelt' / 'weekly_value.parquet')
    meta = dict(build_id=IO.build_id(['sim', seed, null]), taxonomy='simulated', settings_sha256=S.sha256, formats=list(S.seattle_formats),
                simulated=True, inputs={}, controls=ctrl, effects=dict(narrow=eff3, middle=eff2, value=effv))
    IO.save_json({k: v for k, v in meta.items() if k != 'effects'}, P.meta)
    return meta


def missing_digital(S, missing):
    """Months that are unusable in the digital formats only; the sim Counts mark them unusable in every format, which is
    close enough for the chain test (the real data have them only for audiobook and ebook)."""
    return ()
