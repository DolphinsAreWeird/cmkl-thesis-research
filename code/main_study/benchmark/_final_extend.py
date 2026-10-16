# Extension of the frozen taxonomy tables with the checkout rows of months released after the freeze (machinery of the final test, part 2).
# The history is not rebuilt: records, works and theme strengths of the taxonomy v3 build stay as they are. New rows are matched to the stored
# records by the record key of 10_v3_spl_rows.py (digital: title, creator, subjects, publisher, publication year, ISBN; print: title, creator, subjects).
# A row whose record is new gets a new record; the new records are grouped into works by the same work-key rule (_common.assign_work_keys) and a new
# record whose key equals the key of a stored work joins that work (and so keeps its stored theme strengths). A work that first appears after the
# freeze gets theme strengths by the rules of 16_v3_assign.py from its own records only: OverDrive subject terms of its digital records (source spl) and
# print subject headings of its print records (source lcsh), through the stored phrase, heading and value-to-node tables; headings and terms that the
# stored tables do not know give no evidence; there is no Goodreads evidence for a new work. The functions pubyear, creator_from_title, fix_cp850 and
# rollup are taken from the build scripts' own source (ast), not copied.
# Output: a 'world' folder with the layout of Study 3's simulated worlds (taxonomy/ holds the extended tables), which study3's panel builder reads.
import os
os.environ.setdefault('TAXO', 'v3')
import sys, re, ast, json, time, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
MAIN = HERE.parent
ROOT = HERE.parents[2]
DB = ROOT / 'data' / 'db'
V3, V2 = DB / 'taxonomy_v3', DB / 'taxonomy_v2'
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

FILE_OF = {'AUDIOBOOK': 'audiobook', 'EBOOK': 'ebook', 'BOOK': 'book'}
DIGITAL = ('AUDIOBOOK', 'EBOOK')
SEP = '\x1f'
RAW_COLS = ['checkoutyear', 'checkoutmonth', 'checkouts', 'title', 'creator', 'subjects', 'publisher', 'publicationyear', 'isbn']


def _extract(path, names, ns):
    """Define the named top-level functions of a script in ns, from the script's own source."""
    tree = ast.parse(pathlib.Path(path).read_text())
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            exec(compile(ast.Module([n], []), str(path), 'exec'), ns)
    missing = [x for x in names if x not in ns]
    if missing:
        raise SystemExit(f'{missing} not found in {path}')
    return ns


def load_common():
    spec = importlib.util.spec_from_file_location('spl_common', MAIN / '_common.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build_namespace(level):
    ns = {'re': re, 'np': np, 'pd': pd, 'level': level}
    _extract(MAIN / '10_v3_spl_rows.py', {'pubyear', 'creator_from_title'}, ns)
    _extract(MAIN / '11_v3_work_table.py', {'fix_cp850'}, ns)
    _extract(MAIN / '16_v3_assign.py', {'rollup'}, ns)
    return ns


# ---------------- record keys ----------------
def key_strings(fmt, title, creator, subjects, publisher, pubyear_s, isbn):
    """The record key of 10_v3_spl_rows.py as one string per row (format first, so that the same fields in two formats are two records)."""
    f = lambda s: pd.Series(s).fillna('').astype(str).reset_index(drop=True)
    parts = [f(title), f(creator), f(subjects)]
    if fmt in DIGITAL:
        parts += [f(publisher), f(pubyear_s), f(isbn)]
    out = fmt + SEP + parts[0]
    for p in parts[1:]:
        out = out + SEP + p
    return out


def hash_keys(keys):
    return pd.util.hash_array(keys.to_numpy(dtype=object)).astype(np.uint64)


def frozen_key_table(cache=None):
    """Sorted 64-bit hashes of the stored records' keys with their record ids (computed once and cached)."""
    cache = pathlib.Path(cache) if cache else None
    if cache and cache.exists():
        z = np.load(cache)
        return z['hash'], z['record_id']
    pf = pq.ParquetFile(V3 / 'spl_records.parquet')
    cols = ['record_id', 'format', 'title', 'creator', 'creator_from_title', 'subjects', 'publisher', 'publicationyear', 'isbn']
    hs, ids = [], []
    for b in pf.iter_batches(batch_size=200_000, columns=cols):
        d = b.to_pandas()
        for fmt, g in d.groupby(d['format'].astype(str)):
            raw_creator = g.creator.where(~g.creator_from_title.astype(bool), '') if fmt == 'BOOK' else g.creator
            k = key_strings(fmt, g.title, raw_creator, g.subjects, g.publisher, g.publicationyear, g.isbn)
            hs.append(hash_keys(k)); ids.append(g.record_id.to_numpy(np.int64))
    h = np.concatenate(hs); i = np.concatenate(ids)
    o = np.argsort(h, kind='stable')
    h, i = h[o], i[o]
    if len(np.unique(h)) != len(h):
        dup = int(len(h) - len(np.unique(h)))
        print(f'warning: {dup} stored records share a 64-bit key hash with another record (kept: the first)', flush=True)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, hash=h, record_id=i)
    return h, i


def lookup(sorted_hash, sorted_ids, h):
    pos = np.searchsorted(sorted_hash, h)
    pos_c = np.minimum(pos, len(sorted_hash) - 1)
    found = sorted_hash[pos_c] == h
    return np.where(found, sorted_ids[pos_c], -1)


# ---------------- evidence of new works ----------------
def load_lookup_tables(restrict_before_ym=None):
    """Phrase, value-to-node, node and heading tables. Dry run only: restrict_before_ym (a month as yyyymm) removes the print headings and the OverDrive terms
    that occur only on works first seen from that month on, so that new works meet vocabulary the stored tables do not know, as in the real case."""
    P = pd.read_parquet(V2 / 'phrases.parquet', columns=['source', 'raw', 'components_json'])
    comp = {(s, r): [tuple(x) for x in json.loads(c)] for s, r, c in zip(P.source, P.raw, P.components_json)}
    VN = pd.read_parquet(V3 / 'theme_value_node.parquet')
    N = pd.read_parquet(V3 / 'theme_nodes.parquet')
    H = pd.read_parquet(V3 / 'headings.parquet', columns=['heading', 'heading_id'])
    head_id = dict(zip(H.heading, H.heading_id))
    if restrict_before_ym is not None:
        fy = pd.read_parquet(V3 / 'spl_works.parquet', columns=['work_id', 'first_ym'])
        old_work = set(fy.work_id[fy.first_ym < restrict_before_ym].tolist())
        wh = pd.read_parquet(V3 / 'work_headings.parquet', columns=['work_id', 'heading_id'])
        seen_h = set(wh.heading_id[wh.work_id.isin(old_work)].tolist())
        head_id = {h: i for h, i in head_id.items() if i in seen_h}
        wt = pd.read_parquet(V3 / 'work_terms.parquet', columns=['work_id', 'term'])
        seen_t = set(wt.term[wt.work_id.isin(old_work)].tolist())
        comp = {k: v for k, v in comp.items() if not (k[0] == 'spl' and k[1] not in seen_t)}
    return comp, dict(zip(VN.theme, VN.node_id)), dict(zip(N.node_id, N.level)), head_id


def heading_themes(ids):
    """heading_id -> [(theme value, weight)] for the headings in ids, as 16_v3_assign.py reads headings_parsed (core theme 1.0, other theme 0.5)."""
    want = set(int(i) for i in ids)
    HP = pd.read_parquet(V3 / 'headings_parsed.parquet', columns=['heading_id', 'components_json'])
    HP = HP[HP.heading_id.isin(want)]
    out = {}
    for hid, cj in zip(HP.heading_id, HP.components_json):
        th = []
        for f, v in json.loads(cj):
            if f == 'core_theme':
                th.append((v, 1.0))
            elif f == 'theme':
                th.append((v, 0.5))
        if th:
            out[int(hid)] = th
    return out


def new_work_strengths(NR, ns, tabs):
    """Theme strengths of the new works. NR: the new records with work_id, format, subjects and their checkouts in the new months.
    Returns a table in the layout of work_theme.parquet."""
    comp, v2node, level, head_id = tabs
    ev = []
    d = NR[(NR.format != 'BOOK') & (NR.subjects != '')][['work_id', 'subjects', 'checkouts']].copy()
    d['term'] = d.subjects.str.split(', ')
    d = d.explode('term')
    d['term'] = d.term.str.strip()
    d = d[d.term != '']
    wt = d.groupby(['work_id', 'term'], as_index=False).checkouts.sum()
    dig = NR[NR.format != 'BOOK'].groupby('work_id').checkouts.sum()
    wt['share'] = (wt.checkouts / wt.work_id.map(dig)).fillna(0).clip(upper=1.0).round(4)
    for wid, t, s in zip(wt.work_id, wt.term, wt.share):
        cs = comp.get(('spl', t), [])
        th = [v for f, v in cs if f == 'theme']
        for v in th:
            ev.append((wid, 'spl', v, float(s) / len(th)))
    p = NR[(NR.format == 'BOOK') & (NR.subjects != '')][['work_id', 'subjects', 'checkouts']].copy()
    p['heading'] = p.subjects.str.split(', ')
    p = p.explode('heading')
    p['heading'] = p.heading.str.strip()
    p = p[p.heading != '']
    uh = pd.Series(p.heading.unique())
    fixed = dict(zip(uh, uh.map(ns['fix_cp850'])))
    p['heading'] = p.heading.map(fixed)
    p['heading_id'] = p.heading.map(head_id)
    n_unknown = int(p.heading_id.isna().sum())
    p = p[p.heading_id.notna()]
    p['heading_id'] = p.heading_id.astype(int)
    wh = p.groupby(['work_id', 'heading_id'], as_index=False).checkouts.sum()
    prt = NR[NR.format == 'BOOK'].groupby('work_id').checkouts.sum()
    wh['share'] = (wh.checkouts / wh.work_id.map(prt)).fillna(0).clip(upper=1.0).round(4)
    hth = heading_themes(wh.heading_id.unique())
    for wid, hid, s in zip(wh.work_id, wh.heading_id, wh.share):
        for v, w in hth.get(int(hid), ()):
            ev.append((wid, 'lcsh', v, float(s) * w))
    if not ev:
        return pd.DataFrame(columns=['work_id', 'node_id', 'level', 'strength', 's_spl', 's_lcsh', 's_gr', 'sources', 'rank_in_level']), dict(unknown_headings=n_unknown)
    EV = pd.DataFrame(ev, columns=['work_id', 'source', 'theme', 'weight'])
    EV = EV.groupby(['work_id', 'source', 'theme'], as_index=False).weight.sum()
    EV['node_id'] = EV.theme.map(v2node)
    E = EV[EV.node_id.notna()].copy()
    E['share'] = E.weight / E.groupby(['work_id', 'source']).weight.transform('sum')
    ns['level'] = level
    out = ns['rollup'](E, ['spl', 'lcsh', 'gr'])
    out['work_id'] = out.work_id.astype(np.int64)
    return out, dict(unknown_headings=n_unknown, evidence_rows=len(EV))


# ---------------- the extension ----------------
def read_stored_rows(fmt, before_mi=None):
    t = pq.read_table(V3 / f'spl_rows_{FILE_OF[fmt]}.parquet').to_pandas()
    if before_mi is not None:
        mi = t.year.astype(np.int64) * 12 + t.month.astype(np.int64) - 1
        t = t[mi < before_mi]
    return t


def extend(new_raw, world, before_mi=None, hash_cache=None, log=print, restrict_vocab=False):
    """new_raw: {format name: DataFrame with the raw API columns (RAW_COLS; missing fields empty)} for months after the freeze.
    before_mi: dry run only. Treat everything first seen at month index >= before_mi as new: the stored rows, records, works and strengths from that
    month on are left out of the frozen set (the rows of those months are then expected in new_raw).
    Writes world/taxonomy/*.parquet (extended tables) and returns a report dict (counts only)."""
    t0 = time.time()
    world = pathlib.Path(world)
    tx = world / 'taxonomy'
    tx.mkdir(parents=True, exist_ok=True)
    CM = load_common()
    ns = build_namespace(None)
    tabs = load_lookup_tables(restrict_before_ym=(before_mi // 12) * 100 + before_mi % 12 + 1 if (restrict_vocab and before_mi is not None) else None)
    # frozen record keys
    sh, sid = frozen_key_table(hash_cache)
    log(f'{time.strftime("%H:%M:%S")} stored record keys: {len(sh):,}')
    # frozen rows, record -> work, works
    rows_old = {f: read_stored_rows(f, before_mi) for f in FILE_OF}
    rw = pd.read_parquet(V3 / 'spl_record_work.parquet')
    works_cols = ['work_id', 'work_key', 'checkouts_audiobook', 'checkouts_ebook', 'checkouts_book']
    W = pd.read_parquet(V3 / 'spl_works.parquet', columns=works_cols)
    max_rec = int(max(sid.max(), rw.record_id.max()))          # new ids start above every stored id, also those left out of a dry-run freeze
    max_work = int(W.work_id.max())
    if before_mi is not None:
        keep_rec = set()
        for f, t in rows_old.items():
            keep_rec.update(np.unique(t.record_id.to_numpy()).tolist())
        keep_rec = np.fromiter(keep_rec, dtype=np.int64)
        rw = rw[rw.record_id.isin(keep_rec)]
        fm = np.isin(sid, keep_rec)
        sh, sid = sh[fm], sid[fm]                              # a record seen only from the freeze month on is new again
        # frozen works: those with a frozen record; their stored checkouts are recomputed from the frozen rows
        W = W[W.work_id.isin(rw.work_id.unique())].copy()
        wm = rw.set_index('record_id').work_id
        for f, c in (('AUDIOBOOK', 'checkouts_audiobook'), ('EBOOK', 'checkouts_ebook'), ('BOOK', 'checkouts_book')):
            t = rows_old[f]
            s_ = t.groupby('record_id').checkouts.sum()
            wc = s_.groupby(wm.reindex(s_.index).to_numpy()).sum()
            W[c] = W.work_id.map(wc).fillna(0).astype(np.int64)
    WT = pd.read_parquet(V3 / 'work_theme.parquet')
    if before_mi is not None:
        WT = WT[WT.work_id.isin(W.work_id)]
    key_to_work = dict(zip(W.work_key, W.work_id))
    log(f'{time.strftime("%H:%M:%S")} frozen: {sum(len(t) for t in rows_old.values()):,} rows, {len(rw):,} records, {len(W):,} works, {WT.work_id.nunique():,} works with a theme')
    # new rows -> records
    new_rows, new_recs, rep = {}, [], {}
    next_rec = max_rec + 1
    for fmt, raw in new_raw.items():
        r = raw.copy()
        for c in RAW_COLS:
            if c not in r.columns:
                r[c] = ''
        r = r.reset_index(drop=True)
        keys = key_strings(fmt, r.title, r.creator, r.subjects, r.publisher, r.publicationyear, r.isbn)
        h = hash_keys(keys)
        rec = lookup(sh, sid, h)
        known = rec >= 0
        # new keys (unique per format)
        newk = pd.DataFrame({'h': h[~known], 'i': np.where(~known)[0]}).drop_duplicates('h')
        newk['record_id'] = np.arange(next_rec, next_rec + len(newk), dtype=np.int64)
        next_rec += len(newk)
        m = pd.Series(newk.record_id.values, index=newk.h.values)
        rec = np.where(known, rec, m.reindex(h).to_numpy(np.int64, na_value=-1))
        assert (rec >= 0).all()
        rows = pd.DataFrame({'record_id': rec.astype(np.int32), 'year': r.checkoutyear.astype(int).astype(np.int16),
                             'month': r.checkoutmonth.astype(int).astype(np.int8), 'checkouts': r.checkouts.astype(float).astype(int).astype(np.int32)})
        new_rows[fmt] = rows
        nr = r.iloc[newk.i.values].copy()
        nr['record_id'] = newk.record_id.values
        nr['format'] = fmt
        new_recs.append(nr)
        rep[fmt] = dict(rows=len(rows), checkouts=int(rows.checkouts.sum()), rows_on_known_records=int(known.sum()),
                        checkouts_on_known_records=int(rows.checkouts.to_numpy()[known].sum()), new_records=len(newk))
    NR = pd.concat(new_recs, ignore_index=True) if new_recs else pd.DataFrame()
    # attributes of the new records (as write_part in 10_v3_spl_rows.py)
    if len(NR):
        is_book = NR.format == 'BOOK'
        raw_c = NR.creator.fillna('')
        NR['creator_from_title'] = is_book & (raw_c == '')
        NR['creator'] = np.where(is_book & (raw_c == ''), NR.title.map(ns['creator_from_title']), raw_c)
        NR['subjects'] = NR.subjects.fillna('')
        NR['pub_year'] = NR.publicationyear.map(ns['pubyear'])
        tp = [CM.title_parts(t) for t in NR.title]
        NR['title_main'] = [x[0] for x in tp]
        NR['title_sub'] = [x[1] for x in tp]
        NR['creator_key'] = NR.creator.map(CM.norm_creator)
        NR['creator_match'] = NR.creator_key.map(CM.creator_match_key)
        NR['work_key'] = CM.assign_work_keys(NR.title_main, NR.title_sub, NR.creator_match)
        wid = NR.work_key.map(key_to_work)
        joined = wid.notna()
        nk = pd.Series(NR.work_key[~joined].unique())
        new_ids = pd.Series(np.arange(max_work + 1, max_work + 1 + len(nk), dtype=np.int64), index=nk.values)
        wid = wid.where(joined, NR.work_key.map(new_ids))
        NR['work_id'] = wid.astype(np.int64)
        NR['joined_stored_work'] = joined.to_numpy()
    else:
        NR['work_id'] = []
    # checkouts of the new records in the new months
    rec_co = pd.concat([t.groupby('record_id').checkouts.sum() for t in new_rows.values()]) if new_rows else pd.Series(dtype=np.int64)
    rec_co = rec_co.groupby(level=0).sum()
    NR['checkouts'] = NR.record_id.map(rec_co).fillna(0).astype(np.int64)
    new_work_mask = ~NR.joined_stored_work if len(NR) else pd.Series(dtype=bool)
    NW = NR[new_work_mask] if len(NR) else NR
    strengths, ev_info = new_work_strengths(NW, ns, tabs) if len(NW) else (pd.DataFrame(columns=WT.columns), {})
    log(f'{time.strftime("%H:%M:%S")} new records {len(NR):,}, of which on stored works {int(NR.joined_stored_work.sum()) if len(NR) else 0:,}; new works {NW.work_id.nunique() if len(NW) else 0:,}; '
        f'new works with a theme {strengths.work_id.nunique():,}')
    # record_work and work tables
    rw_new = pd.DataFrame({'record_id': NR.record_id.astype(np.int64), 'work_id': NR.work_id.astype(np.int32)}) if len(NR) else pd.DataFrame(columns=['record_id', 'work_id'])
    rw_all = pd.concat([rw, rw_new], ignore_index=True)
    all_rows_new = pd.concat([t.assign(fmt=f) for f, t in new_rows.items()], ignore_index=True)
    wmap = rw_all.drop_duplicates('record_id').set_index('record_id').work_id
    all_rows_new['work_id'] = wmap.reindex(all_rows_new.record_id.to_numpy().astype(np.int64)).to_numpy()
    add = all_rows_new.groupby(['work_id', 'fmt']).checkouts.sum().unstack(fill_value=0)
    colname = {'AUDIOBOOK': 'checkouts_audiobook', 'EBOOK': 'checkouts_ebook', 'BOOK': 'checkouts_book'}
    Wn = W.set_index('work_id')
    new_ids = np.setdiff1d(add.index.to_numpy(), Wn.index.to_numpy())
    if len(new_ids):
        Wn = pd.concat([Wn, pd.DataFrame(0, index=pd.Index(new_ids, name='work_id'), columns=Wn.columns).assign(work_key='')])
    for f, c in colname.items():
        if f in add.columns:
            Wn[c] = Wn[c] + add[f].reindex(Wn.index).fillna(0).astype(np.int64)
    if len(NR):
        keymap = NR.drop_duplicates('work_id').set_index('work_id').work_key
        Wn.loc[Wn.index.isin(keymap.index) & (Wn.work_key == ''), 'work_key'] = keymap.reindex(Wn.index[Wn.index.isin(keymap.index) & (Wn.work_key == '')]).values
    Wn = Wn.reset_index()
    WT_all = pd.concat([WT, strengths[WT.columns]], ignore_index=True)
    # write
    for f, old in rows_old.items():
        new = new_rows.get(f)
        t = pd.concat([old, new], ignore_index=True) if new is not None else old
        pq.write_table(pa.Table.from_pandas(t.astype({'record_id': np.int32, 'year': np.int16, 'month': np.int8, 'checkouts': np.int32}), preserve_index=False), tx / f'spl_rows_{FILE_OF[f]}.parquet')
    rw_all.to_parquet(tx / 'spl_record_work.parquet', index=False)
    Wn.to_parquet(tx / 'spl_works.parquet', index=False)
    WT_all.to_parquet(tx / 'work_theme.parquet', index=False)
    for name in ('theme_nodes.parquet', 'work_theme_title_backup.parquet'):
        link = tx / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(V3 / name)
    if len(NR):
        NR[['record_id', 'format', 'work_id', 'work_key', 'joined_stored_work']].to_parquet(world / 'new_records.parquet', index=False)
    rep['new_works'] = int(NW.work_id.nunique()) if len(NW) else 0
    rep['new_works_with_theme'] = int(strengths.work_id.nunique())
    rep['new_records_joined_to_stored_works'] = int(NR.joined_stored_work.sum()) if len(NR) else 0
    rep.update(ev_info)
    rep['seconds'] = round(time.time() - t0)
    return rep
