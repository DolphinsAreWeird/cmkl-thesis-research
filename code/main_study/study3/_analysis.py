# Glue between the panel and the methods: wide matrices per level and format, the donor rules, one full test of a
# category at a month 0 (event study, synthetic control, placebo categories, placebo years), and power draws.
# Used by 10_positive_controls.py, 11_power.py and 12_shift_effects.py.
import json
import numpy as np, pandas as pd
import _methods as M
from _build import ym_of, mi_from_ym


class Context:
    """Everything the tests need, held as small wide matrices (months x categories) per (level, format)."""

    def __init__(self, panel, nodes, overlap, shifts, S):
        self.S = S
        self.Y, self.ok = {}, {}
        for (level, fmt), g in panel.groupby(['level', 'format'], sort=True):
            Y = g.pivot(index='mi', columns='node_id', values='log_share').sort_index()
            full = np.arange(int(Y.index.min()), int(Y.index.max()) + 1)
            self.Y[(level, fmt)] = Y.reindex(full)
            self.ok[(level, fmt)] = g.pivot(index='mi', columns='node_id', values='size_ok').reindex(full).fillna(False).astype(bool)
        nd = nodes.set_index('node_id')
        self.parent = nd.parent.to_dict()
        self.broad = nd.broad_id.to_dict()
        self.label = nd.label.to_dict()
        self.ov = {}
        for (level, fmt), g in overlap.groupby(['level', 'format']):
            self.ov[(level, fmt)] = {a: dict(zip(h.node_b, h.share_of_a)) for a, h in g.groupby('node_a')}
        self.has_shifts = shifts is not None
        self.shift_m0 = {}
        if shifts is not None:
            for n, h in shifts.groupby('node_id'):
                self.shift_m0[n] = np.sort(h.m0.to_numpy())

    def keys(self, levels):
        return [k for k in sorted(self.Y) if k[0] in levels]

    def size_ok(self, level, fmt, node, m0):
        ok = self.ok.get((level, fmt))
        if ok is None or node not in ok.columns or m0 not in ok.index:
            return False
        return bool(ok.at[m0, node])

    def shifted_near(self, node, m0, win):
        """True if the category has any shift start (any source, any class) in months win[0]..win[1] around m0.
        NOT IN RECORD: shifts from both sources and of every class (seasonal included) count."""
        m = self.shift_m0.get(node)
        if m is None:
            return False
        return bool(np.any((m >= m0 + win[0]) & (m <= m0 + win[1])))

    def donors(self, level, fmt, treated, m0):
        """Record: same level, no shift start in months -6..+6, not sharing a parent node, sharing <= 10% of the
        treated category's works. NOT IN RECORD: a donor must also pass the minimum-size rule for that window and
        format. Without a shifts table the shift rule cannot be applied (the caller reports this)."""
        S = self.S
        Y = self.Y[(level, fmt)]
        ov = self.ov.get((level, fmt), {}).get(treated, {})
        out = []
        for n in Y.columns:
            if n == treated or not self.size_ok(level, fmt, n, m0):
                continue
            if self.parent.get(n) is not None and self.parent.get(n) == self.parent.get(treated):
                continue
            if ov.get(n, 0.0) > S.donor_max_overlap:
                continue
            if self.has_shifts and self.shifted_near(n, m0, S.donor_no_shift):
                continue
            out.append(n)
        return out

    def last_month(self, level, fmt):
        return int(self.Y[(level, fmt)].index.max())


def _clean(d):
    """Drop private keys and turn arrays and dicts into storable values."""
    out = {}
    for k, v in d.items():
        if k.startswith('_'):
            continue
        if isinstance(v, dict):
            out[k] = json.dumps({str(a): (None if (isinstance(b, float) and np.isnan(b)) else b) for a, b in v.items()})
        elif isinstance(v, (list, np.ndarray)):
            out[k] = json.dumps([None if (isinstance(x, float) and np.isnan(x)) else (int(x) if isinstance(x, np.integer) else x) for x in list(v)])
        else:
            out[k] = v
    return out


def placebo_years(ctx, level, fmt, node, m0, real):
    """Same category, same calendar months, every other year from the record's first placebo year that has data,
    passes the size rule and has no shift of the category in months -6..+6 around the placebo month 0.
    NOT IN RECORD: 'no shift in that window' uses the donor rule's window (-6..+6); the placebo window must pass the
    minimum-size rule; placebo years are compared on the primary window only. Returns the share of placebo effects
    >= the real effect for both methods."""
    S = ctx.S
    Y = ctx.Y[(level, fmt)]
    y0, cal = divmod(m0, 12)
    es_e, sc_e, years = [], [], []
    for yr in range(S.placebo_year_from, ctx.last_month(level, fmt) // 12 + 1):
        m = yr * 12 + cal
        if yr == y0 or m + S.window_primary[0] > Y.index.max() or m + S.sc_fit[0] < Y.index.min():
            continue
        if ctx.has_shifts and ctx.shifted_near(node, m, S.donor_no_shift):
            continue
        if not ctx.size_ok(level, fmt, node, m):
            continue
        es = M.event_study(Y[node], m, S)
        sc = M.sc_effect_only(Y, node, ctx.donors(level, fmt, node, m), m, S)
        es_e.append(es.get('es_effect_p', np.nan) if es['es_ok'] else np.nan)
        sc_e.append(sc['p'] if sc else np.nan)
        years.append(yr)
    sh_es, n_es = M.share_at_least(es_e, real.get('es_effect_p', np.nan))
    sh_sc, n_sc = M.share_at_least(sc_e, real.get('sc_effect_p', np.nan))
    return dict(py_years=years, py_es_effects=es_e, py_sc_effects=sc_e,
                py_es_share_ge=sh_es, py_es_n=n_es, py_sc_share_ge=sh_sc, py_sc_n=n_sc)


def test_unit(ctx, level, fmt, node, m0, placebo_years_on=True):
    """Full test of one category, format and month 0. Returns one flat record (storable)."""
    S = ctx.S
    rec = dict(level=level, format=fmt, node_id=node, label=ctx.label.get(node), broad_id=ctx.broad.get(node),
               m0=int(m0), month0=ym_of(m0), shift_rule_applied=ctx.has_shifts)
    Y = ctx.Y.get((level, fmt))
    if Y is None or node not in Y.columns:
        rec['skip'] = 'no data'
        return rec
    if not ctx.size_ok(level, fmt, node, m0):
        rec['skip'] = 'below minimum size'
        return rec
    es = M.event_study(Y[node], m0, S)
    pool = ctx.donors(level, fmt, node, m0)
    sc = M.sc_test(Y, node, pool, m0, S)
    rec.update(_clean(es)); rec.update(_clean(sc))
    rec['skip'] = '' if sc['sc_ok'] else sc.get('sc_reason', 'synthetic control failed')
    # NOT IN RECORD: placebo categories for the event study are the donors used by the synthetic control, each given
    # the same model at the same month 0 (the synthetic control's own placebo categories are its rank p-value).
    if es['es_ok'] and sc['sc_ok']:
        used = sc['_prep']['donors']
        d_es = [M.event_study(Y[d], m0, S) for d in used]
        for tag in ('p', 's'):
            vals = [x.get(f'es_effect_{tag}', np.nan) if x['es_ok'] else np.nan for x in d_es]
            rec[f'pc_es_share_ge_{tag}'], rec[f'pc_es_n_{tag}'] = M.share_at_least(vals, es.get(f'es_effect_{tag}', np.nan))
    if sc['sc_ok']:
        rec['lag_peak'] = M.peak_lag(sc['sc_gaps'], S.carry_lag)
    if placebo_years_on and (es['es_ok'] or sc['sc_ok']):
        rec.update(_clean(placebo_years(ctx, level, fmt, node, m0, {**es, **sc})))
    return rec


# ---------------- power ----------------
def power_candidates(ctx, level, fmt):
    """(category, month 0) pairs that can serve as placebo units: month 0 from the study start (and late enough for
    the fit window) to the last month with a full primary window, size rule passed, and no shift of the category in
    months -6..+6."""
    S = ctx.S
    Y = ctx.Y[(level, fmt)]
    lo = max(mi_from_ym(S.study_start), int(Y.index.min()) - S.sc_fit[0])
    hi = int(Y.index.max()) - S.window_primary[1]
    out = []
    for m0 in range(lo, hi + 1):
        for n in Y.columns:
            if not ctx.size_ok(level, fmt, n, m0):
                continue
            if ctx.has_shifts and ctx.shifted_near(n, m0, S.donor_no_shift):
                continue
            out.append((n, m0))
    return out


def power_draw(ctx, level, fmt, node, m0, lifts):
    """One placebo draw: the donor placebos are computed once (they do not depend on the treated series, which is
    never in their pools), then the synthetic control is rerun on the treated series with each injected lift."""
    S = ctx.S
    Y = ctx.Y[(level, fmt)]
    pool = ctx.donors(level, fmt, node, m0)
    base = M.sc_test(Y, node, pool, m0, S)
    out = []
    if not base['sc_ok']:
        return [dict(level=level, format=fmt, node_id=node, m0=m0, lift=l, p=np.nan, effect=np.nan,
                     n_donors=base['sc_n_donors'], reason=base.get('sc_reason')) for l in lifts]
    pl = base['_placebos']
    for lift in lifts:
        Yl = Y.copy()
        Yl[node] = M.inject_lift(Y[node], m0, S.power_window, lift)
        r = M.sc_test(Yl, node, pool, m0, S, placebos=pl)
        out.append(dict(level=level, format=fmt, node_id=node, m0=m0, lift=lift, p=r.get('sc_p_p', np.nan),
                        effect=r.get('sc_effect_p', np.nan), n_donors=r['sc_n_donors'], reason=''))
    return out


# ---------------- parallel runs ----------------
def _chunk_run(fn, ctx, items):
    return [fn(ctx, *it) for it in items]


def run_parallel(fn, ctx, items, workers):
    """fn(ctx, *item) for every item, in chunks so the context is sent to each worker only a few times.
    Results come back in the order of `items`."""
    from joblib import Parallel, delayed
    items = list(items)
    if workers <= 1 or len(items) < 8:
        return _chunk_run(fn, ctx, items)
    k = max(1, len(items) // (workers * 4))
    chunks = [items[i:i + k] for i in range(0, len(items), k)]
    res = Parallel(n_jobs=workers)(delayed(_chunk_run)(fn, ctx, c) for c in chunks)
    return [r for c in res for r in c]
