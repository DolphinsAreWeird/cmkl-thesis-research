# Readers for the real inputs of the demand panel (Seattle checkouts, taxonomy, SPL API counts, LibriVox).
# Files are reloaded on every call: the taxonomy job may still be rewriting them. Used by 01 and by 10 (backup).
import os
import numpy as np, pandas as pd
import _files as IO
import _build as B


def choose_source(P):
    """Taxonomy v3 when its work_theme exists; otherwise the v2 themes carried onto v3 works (development only)."""
    v3 = P.taxo_v3
    nodes = v3 / 'theme_nodes.parquet' if (v3 / 'theme_nodes.parquet').exists() else P.taxo_v2 / 'theme_nodes.parquet'
    if (v3 / 'work_theme.parquet').exists():
        return dict(taxonomy='v3', development=False, nodes=nodes)
    return dict(taxonomy='v2 themes carried onto v3 works by work key', development=True, nodes=nodes)


def input_files(P, S, src):
    fs = [src['nodes'], P.taxo_v3 / 'spl_record_work.parquet', P.taxo_v3 / 'spl_works.parquet',
          P.taxo_v2 / 'spl_api_counts.parquet']
    fs += [P.taxo_v3 / f'spl_rows_{IO.SEATTLE_FILE[f]}.parquet' for f in S.seattle_formats]
    if src['development']:
        fs += [P.taxo_v2 / 'work_theme.parquet', P.taxo_v2 / 'spl_works.parquet']
    else:
        fs += [P.taxo_v3 / 'work_theme.parquet', P.taxo_v3 / 'work_theme_title_backup.parquet']
    lv = P.taxo_v3 / 'librivox_work_theme.parquet'
    if lv.exists():
        fs += [lv, P.librivox_listening]
    return [str(f) for f in fs if os.path.exists(f)]


def mtimes(files):
    return {f: os.path.getmtime(f) for f in files if os.path.exists(f)}


def changed_since(recorded):
    """Input files whose modification time differs from the one recorded at build time."""
    return [f for f, t in recorded.items() if not os.path.exists(f) or abs(os.path.getmtime(f) - t) > 1e-6]


def load_nodes(src):
    return B.node_table(IO.read_parquet(src['nodes']))


def load_work_theme(P, src, include_title=False):
    """Main assignment keyed by v3 work ids; include_title=True gives the flagged title-word backup strengths.
    Returns (table, how strength was obtained, info dict)."""
    if not src['development']:
        WT = IO.read_parquet(P.taxo_v3 / 'work_theme.parquet')
        if include_title:
            TB = IO.read_parquet(P.taxo_v3 / 'work_theme_title_backup.parquet')
            return B.with_title_backup(WT, TB), 'main sources plus title words (flagged backup)', {}
        W, how = B.main_strength(WT)
        return W, how, {}
    WT = IO.read_parquet(P.taxo_v2 / 'work_theme.parquet')
    k2 = IO.read_parquet(P.taxo_v2 / 'spl_works.parquet', columns=['work_id', 'work_key'])
    k3 = IO.read_parquet(P.taxo_v3 / 'spl_works.parquet', columns=['work_id', 'work_key'])
    m = k2.merge(k3, on='work_key', suffixes=('_v2', '_v3')).drop_duplicates('work_id_v2')
    mp = dict(zip(m.work_id_v2.astype(np.int64), m.work_id_v3.astype(np.int64)))
    n_before = WT.work_id.nunique()
    WT['work_id'] = WT.work_id.astype(np.int64).map(mp)
    WT = WT[WT.work_id.notna()].copy()
    W, how = B.main_strength(WT, include_title)
    return W, how, {'v2 works with themes': n_before, 'carried onto v3 works': int(WT.work_id.nunique())}


def api_counts(P):
    """SPL API rows and checkouts per format and month (an independent count of what the download should hold)."""
    f = P.taxo_v2 / 'spl_api_counts.parquet'
    if not f.exists():
        return {}
    A = IO.read_parquet(f)
    A['mi'] = B.mi_of(A.year, A.month)
    name = {'AUDIOBOOK': 'audiobook', 'EBOOK': 'ebook', 'BOOK': 'print'}
    return {name[t]: g.set_index('mi')[['n_rows', 'checkouts']] for t, g in A.groupby('materialtype') if t in name}


def load_record_work(P):
    return IO.read_parquet(P.taxo_v3 / 'spl_record_work.parquet')


def format_month_data(P, S, fmt, rw, api):
    """Work x month checkouts, month totals and month status for one Seattle format."""
    rows = IO.read_parquet(P.taxo_v3 / f'spl_rows_{IO.SEATTLE_FILE[fmt]}.parquet', columns=['record_id', 'year', 'month', 'checkouts'])
    wm, totals = B.work_month(rows, rw)
    miss = S.missing_months if fmt in S.digital_formats else ()
    st = B.month_status(totals, miss, api.get(fmt), closure=(S.closure_frac, S.closure_lookback, S.closure_min))
    raw = dict(raw_rows=len(rows), raw_checkouts=int(rows.checkouts.sum()),
               unmapped_records=int((~rows.record_id.astype(np.int64).isin(rw.record_id.astype(np.int64))).sum()))
    return wm, totals, st, raw


def librivox_inputs(P):
    """LibriVox views as rows of a 'format' (book ids as works), or None when the taxonomy mapping is missing."""
    f = P.taxo_v3 / 'librivox_work_theme.parquet'
    if not f.exists():
        return None
    L = IO.read_parquet(P.librivox_listening)
    WT = IO.read_parquet(f).rename(columns={'book_id': 'work_id'})
    uniq = pd.Index(pd.concat([L.book_id, WT.work_id]).astype(str).unique())
    code = pd.Series(np.arange(len(uniq)), index=uniq)
    rows = pd.DataFrame({'record_id': code.reindex(L.book_id.astype(str)).to_numpy(), 'year': L.period.str[:4].astype(int),
                         'month': L.period.str[5:7].astype(int), 'checkouts': L.listens.astype(np.int64)})
    rw = pd.DataFrame({'record_id': np.arange(len(uniq)), 'work_id': np.arange(len(uniq))})
    WT['work_id'] = code.reindex(WT.work_id.astype(str)).to_numpy()
    return rows, rw, WT
