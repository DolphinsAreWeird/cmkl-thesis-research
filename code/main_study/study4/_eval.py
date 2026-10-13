# Evaluation helpers for 03_evaluate.py: wide forecast table, strata, comparison and secondary-metric tables.
import numpy as np, pandas as pd
import _models as M

KEY = ['group', 'format', 'level', 'node_id', 'origin_mi', 'origin', 'h', 'tmonth', 'y_true', 'y_t']
CB_D, CB_DW = 'catboost|D', 'catboost|D+W'


def wide_forecasts(Fc, F):
    """One row per scored category-format-origin-horizon, one column per model|fset with the forecast, and
    err_<model|fset> with its absolute error. Only rows with an observed target and an observed month t are in the table."""
    Fc = Fc[np.isfinite(Fc.y_true) & np.isfinite(Fc.y_t)].copy()
    Fc['m'] = Fc.model + '|' + Fc.fset.where(Fc.fset != '-', '')
    Fc['m'] = Fc.m.str.rstrip('|')
    W = Fc.pivot(index=KEY, columns='m', values='y_hat').reset_index()
    W.columns.name = None
    models = [c for c in W.columns if c not in KEY]
    extra = F[['group', 'format', 'node_id', 'origin_mi', 'h', 'split_qok_shift8', 'w_ratio', 'w_shift8', 'w_lab_sustained',
               'w_lab_intermediate', 'w_lab_fading']]
    W = W.merge(extra, on=['group', 'format', 'node_id', 'origin_mi', 'h'], how='left')
    for m in models:
        W['err_' + m] = (W[m] - W['y_true']).abs()
    W['act_change'] = W.y_true - W.y_t
    return W, models


def strata(df):
    """(label, subset) pairs: format x level, all formats pooled at each level (the verdict rows), and everything pooled."""
    out = []
    for (f, l), d in df.groupby(['format', 'level'], sort=True):
        out.append((dict(scope='format x level', format=f, level=l), d))
    for l, d in df.groupby('level', sort=True):
        out.append((dict(scope='formats pooled', format='all', level=l), d))
    out.append((dict(scope='all pooled', format='all', level='all'), df))
    return out


def comparison_table(df, base, new, S):
    """Skill of `new` against `base` for every stratum, with bootstrap interval, DM p and the helps verdict."""
    rows = []
    for lab, d in strata(df):
        r = M.compare_models(d.origin_mi.to_numpy(), d['err_' + base].to_numpy(), d['err_' + new].to_numpy(), S)
        r.update(lab)
        r['helps'] = M.helps(r, S) if r['n'] else False
        rows.append(r)
    cols = ['scope', 'format', 'level', 'n', 'months', 'mae_base', 'mae_new', 'skill', 'ci_lo', 'ci_hi', 'dm_stat', 'dm_p', 'helps']
    return pd.DataFrame(rows)[cols]


def _group_cols(lab):
    return ['origin_mi', 'format'] + (['level'] if lab['level'] != 'all' else [])


def secondary_table(df, models, S):
    """MASE (against the seasonal naive), Spearman, top-10% hit rate and direction accuracy per model and stratum."""
    rows = []
    df = df.reset_index(drop=True)
    for lab, d in strata(df):
        d = d.reset_index(drop=True)
        for m in models:
            fc_change = d[m] - d.y_t
            row = dict(lab)
            row.update(model=m, n=int(d[m].notna().sum()),
                       mase=M.mase(d.y_true, d[m], d['seasonal_naive']) if 'seasonal_naive' in d else np.nan,
                       spearman=M.spearman_within(d, fc_change, d.act_change, _group_cols(lab)),
                       top_hit=M.top_hit_rate(d, fc_change, d.act_change, _group_cols(lab), S.top_share),
                       direction=M.direction_accuracy(fc_change, d.act_change, S.direction_min))
            rows.append(row)
    return pd.DataFrame(rows)


def baseline_table(df, models):
    """MAE of every model on the rows where all listed models have a forecast (so the numbers are comparable)."""
    d = df.dropna(subset=models)
    rows = []
    for lab, s in strata(d):
        row = dict(lab); row['n'] = len(s)
        for m in models:
            row['mae ' + m] = float(s['err_' + m].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def conditional_table(df, base, new, S):
    """Skill separately for category-months with a quality-ok interest shift that started in the 8 weeks before the
    origin (split_qok_shift8 = 1) and for all other category-months."""
    rows = []
    for name, d in (('shift months', df[df.split_qok_shift8 == 1]), ('other months', df[df.split_qok_shift8 != 1])):
        if len(d) == 0:
            continue
        t = comparison_table(d, base, new, S)
        t.insert(0, 'split', name)
        rows.append(t)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def md_table(df, floats=3, int_cols=()):
    if df is None or len(df) == 0:
        return '_(no rows)_'
    cols = list(df.columns)
    out = ['| ' + ' | '.join(str(c).replace('|', '/') for c in cols) + ' |', '| ' + ' | '.join('---' for _ in cols) + ' |']
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (bool, np.bool_)):
                cells.append('yes' if v else 'no')
            elif isinstance(v, (int, np.integer)) or c in int_cols and pd.notna(v):
                cells.append(f'{int(v):,}')
            elif isinstance(v, (float, np.floating)):
                cells.append('' if not np.isfinite(v) else f'{v:.{floats}f}')
            else:
                cells.append(str(v).replace('|', '/'))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out)
