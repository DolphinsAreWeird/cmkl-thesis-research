# Study 4b evaluation helpers: wide tables, strata, comparisons (Part A), surge metrics and AP-difference bootstrap (Part B).
import numpy as np, pandas as pd
import _s4
import _b_models as BM

M4 = _s4.models
md_table = _s4.evalm.md_table
KEY = ['format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth', 'ls_t', 'target']
FORMAT_ORDER = ['print', 'ebook', 'audiobook']
POOLED = 'print+ebook pooled'


def _wide(Fc, part):
    d = Fc[Fc.part == part].copy()
    d['m'] = (d.model + '|' + d.fset.where(d.fset != '-', '')).str.rstrip('|')
    W = d.pivot(index=KEY, columns='m', values='pred').reset_index()
    W.columns.name = None
    return W, [c for c in W.columns if c not in KEY]


def wide_a(Fc):
    """One row per scored category-format-origin-horizon; one column per model|fset with the forecast change and err_<m> with
    its absolute error against the realised change."""
    W, models = _wide(Fc[np.isfinite(Fc.target)], 'A')
    for m in models:
        W['err_' + m] = (W[m] - W['target']).abs()
    return W, models


def wide_b(Fc, B):
    W, models = _wide(Fc[np.isfinite(Fc.target)], 'B')
    W['surge'] = (W.target >= B.surge_change).astype(float)
    return W, models


def strata(df, B):
    """format x level for every format (print, ebook primary; audiobook secondary) and print+ebook pooled at each level
    (the primary verdict rows)."""
    out = []
    for f in FORMAT_ORDER:
        for l in B.levels:
            d = df[(df.format == f) & (df.level == l)]
            if len(d):
                out.append((dict(scope='format x level' + (' (secondary)' if f in B.formats_secondary else ''), format=f, level=l), d))
    for l in B.levels:
        d = df[df.format.isin(B.formats_primary) & (df.level == l)]
        if len(d):
            out.append((dict(scope=POOLED + ' (primary)', format='print+ebook', level=l), d))
    return out


# ---------------- Part A ----------------
COLS_A = ['h', 'comparison', 'scope', 'format', 'level', 'n', 'months', 'mae_base', 'mae_new', 'skill', 'ci_lo', 'ci_hi', 'dm_stat', 'dm_p', 'helps']


def compare_a(W, base, new, h, B, label=None):
    d = W[(W.h == h)].dropna(subset=[base, new])
    rows = []
    for lab, s in strata(d, B):
        r = M4.compare_models(s.origin_mi.to_numpy(), s['err_' + base].to_numpy(), s['err_' + new].to_numpy(), B)
        r.update(lab)
        r['helps'] = M4.helps(r, B) if r['n'] else False
        r['h'] = h
        r['comparison'] = label or f'{new} vs {base}'
        rows.append(r)
    return pd.DataFrame(rows)[COLS_A] if rows else pd.DataFrame(columns=COLS_A)


def mae_table(W, models, B):
    """MAE (log-share change) of every model on the rows where all listed models have a forecast."""
    rows = []
    for h in B.horizons:
        d = W[W.h == h].dropna(subset=models)
        for lab, s in strata(d, B):
            row = dict(h=h, **lab, n=len(s))
            for m in models:
                row['mae ' + m] = float(s['err_' + m].mean())
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------- Part B ----------------
def surge_table(Wb, models, B):
    rows = []
    for lab, s in strata(Wb, B):
        s = s.reset_index(drop=True)
        base = float(s.surge.mean())
        for m in models:
            ok = s[[m, 'surge']].dropna()
            rec, rnd, npos, ng = BM.top_k_recall(s, m, B.top_k, ['origin_mi', 'format'])
            ap = BM.average_precision(s.surge, s[m])
            rows.append(dict(**lab, model=m, n=int(len(ok)), surges=int(s.surge.sum()), base_rate=base, ap=ap,
                             ap_over_base=ap / base if base > 0 else np.nan, recall_top=rec, recall_random=rnd,
                             origins_with_surge=ng, brier=BM.brier(s.surge, s[m]), brier_base_rate=base * (1 - base)))
    return pd.DataFrame(rows)


def ap_diff_table(Wb, pairs, B):
    """AP(new) - AP(base) with the block-bootstrap interval; helps if the interval is above zero."""
    rows = []
    for lab, s in strata(Wb, B):
        s = s.reset_index(drop=True)
        if s.surge.sum() == 0:
            continue
        for cls, base, new in pairs:
            d = s.dropna(subset=[base, new])
            lo, hi, _ = BM.ap_diff_bootstrap(d.origin_mi.to_numpy(), d.surge.to_numpy(), d[base].to_numpy(), d[new].to_numpy(),
                                             B.boot_block, B.boot_n, B.boot_seed, B.ci_level)
            a0, a1 = BM.average_precision(d.surge, d[base]), BM.average_precision(d.surge, d[new])
            rows.append(dict(**lab, comparison=f'{new} vs {base}', model_class=cls, surges=int(d.surge.sum()), ap_base=a0, ap_new=a1,
                             ap_diff=a1 - a0, ci_lo=lo, ci_hi=hi, helps=bool(np.isfinite(lo) and lo > 0)))
    return pd.DataFrame(rows)
