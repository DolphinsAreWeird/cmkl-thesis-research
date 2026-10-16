# 02. Brisbane replication, step 2: match Brisbane titles to Seattle works, inherit theme profiles, build the monthly theme count panel.
# Record: each Brisbane title is matched to a Seattle work by normalised title and author family name (exact match after normalisation, same
# rule for every title) and inherits that work's taxonomy-v3 theme profile; unmatched titles are left out; the match rate by year is reported.
# Demand of a theme in a month = sum of matched loans weighted by theme strength; exposure = all loans of the month; formats pooled.
# Closure: a month whose total loans are below half of the median of the previous 12 months (at least 6 needed) is missing; a month needs >= 2 sampled days.
# Only structure (loans, days, match rates, theme counts) is printed. No theme demand series is shown here.
# NOT IN RECORD choices are marked below and listed in prereg/DEVIATIONS.md (Brisbane replication section).
# Reads untrusted data (downloaded files): run with `python -I`. Output data/db/brisbane/, report data/reports/brisbane_02_panel.md
import sys, pathlib, time, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _bris as B
sys.path.insert(0, str(B.CODE / 'main_study'))
import importlib.util
_spec = importlib.util.spec_from_file_location('spl_common', str(B.CODE / 'main_study' / '_common.py'))
# _common.py writes TAXO folders on import (TAXO env var is ignored under -I, default v2 folder exists); load it only for its normalisation functions
C = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(C)

CORE_SHARE = 0.01
TITLE_MIN = 0.9
TZ = 'Australia/Brisbane'          # NOT IN RECORD: months and sampled days are read in local time (the 2020-2025 files carry UTC timestamps; 2015-2019 carry dates)


def log(*a):
    print(*a, flush=True)


def family(creator_key):
    """NOT IN RECORD: author family name = last word of the normalised creator key (the Seattle normalisation, 'Last, First' flipped)."""
    t = str(creator_key or '').split()
    return t[-1] if t else ''


def keys_for(pairs):
    """pairs: DataFrame title, author (unique). Returns (title_key, family) using the Seattle normalisation (code/main_study/_common.py)."""
    tk = [C.title_parts(t)[0] if isinstance(t, str) else '' for t in pairs.title]
    fam = [family(C.norm_creator(a)) if isinstance(a, str) else '' for a in pairs.author]
    return tk, fam


def seattle_index():
    W = pd.read_parquet(B.ROOT / 'data/db/taxonomy_v3/spl_works.parquet', columns=['work_id', 'title_main', 'creator_key', 'checkouts_total'])
    W['fam'] = W.creator_key.map(family)
    W = W[(W.fam != '') & (W.title_main.astype(str).str.len() >= 2) & ~W.creator_key.isin(C.GENERIC_CREATORS)]
    # NOT IN RECORD: when several Seattle works share one (title, family name) key, the work with the most Seattle checkouts is taken (ties: lowest work_id)
    W = W.sort_values(['title_main', 'fam', 'checkouts_total', 'work_id'], ascending=[True, True, False, True])
    n_keys = W.groupby(['title_main', 'fam']).size()
    amb = int((n_keys > 1).sum())
    W = W.drop_duplicates(['title_main', 'fam'])
    return W[['title_main', 'fam', 'work_id']].rename(columns={'title_main': 'tk'}), amb, len(n_keys)


def main():
    t0 = time.time()
    P = B.BPaths()
    IOP = B.IO.Paths(None)                                  # real Study 3b paths, used only to READ the taxonomy
    src = B.I3.choose_source(IOP)
    N = B.I3.load_nodes(src)
    WT, how, _ = B.I3.load_work_theme(IOP, src)
    SW, amb, nkeys = seattle_index()
    log(f'Seattle match index: {len(SW):,} keys ({amb:,} keys had more than one work)')
    themed = set(WT[WT.level.isin(B.LEVELS)].work_id.unique())
    rows, pw, mon = [], [], []
    for f in sorted(B.RAW.glob('library-checkouts-*.parquet')):
        y = int(f.stem.split('-')[-1])
        d = pd.read_parquet(f, columns=['title', 'author', 'date'])
        dt = pd.to_datetime(d['date'], errors='coerce', utc=True).dt.tz_convert(TZ)
        d['mi'] = (dt.dt.year * 12 + dt.dt.month - 1)
        d['day'] = dt.dt.date
        d = d[d.mi.notna()].reset_index(drop=True)
        d['mi'] = d.mi.astype(np.int64)
        ck = d.title.fillna('') + '\x1f' + d.author.fillna('')
        codes, uniq = pd.factorize(ck)
        u = pd.Series(uniq).str.split('\x1f', n=1, expand=True)
        u.columns = ['title', 'author']
        u['tk'], u['fam'] = keys_for(u)
        u = u.merge(SW, on=['tk', 'fam'], how='left')            # keeps the order of u (many-to-one on SW's unique keys)
        wid = u.work_id.to_numpy()
        d['work_id'] = wid[codes]
        dd = d.groupby(['mi', 'day']).size().rename('n').reset_index()
        dd['core'] = dd.n >= CORE_SHARE * dd.groupby('mi').n.transform('sum')       # NOT IN RECORD: a sampled day holds >= 1% of its month's loans (stray dates with a handful of loans do not count)
        mm = dd.groupby('mi').agg(total_checkouts=('n', 'sum'), dates=('day', 'size'), days=('core', 'sum'))
        mm['titled'] = d.title.notna().groupby(d.mi).sum().reindex(mm.index)
        mon.append(mm.reset_index())
        rows_core = int(dd.core.sum())
        pw.append(d[d.work_id.notna()].groupby(['work_id', 'mi']).size().rename('checkouts').reset_index())
        matched = int(d.work_id.notna().sum())
        themed_n = int(d.work_id.isin(themed).sum())
        rows.append(dict(year=y, loans=len(d), dates_with_loans=int(d.day.nunique()), sampled_days=rows_core, loans_with_author=int(d.author.notna().sum()), matched_loans=matched,
                         match_rate=matched / len(d), loans_with_theme_profile=themed_n, theme_rate=themed_n / len(d),
                         unique_title_author_pairs=len(u), matched_pairs=int(u.work_id.notna().sum())))
        log(f'{y}: loans {len(d):,}, sampled days {rows[-1]["sampled_days"]} (dates with loans {rows[-1]["dates_with_loans"]}), matched {matched / len(d):.3f}, with theme profile {themed_n / len(d):.3f}, {time.time() - t0:.0f}s')
        del d, u, ck
    Y = pd.DataFrame(rows)
    mon = pd.concat(mon, ignore_index=True).groupby('mi', as_index=False).sum()
    wm = pd.concat(pw, ignore_index=True).groupby(['work_id', 'mi'], as_index=False).checkouts.sum()
    wm['work_id'] = wm.work_id.astype(np.int64)
    # ---- month status: >= 2 sampled days, then the closure rule on the months that qualify
    mon = mon.set_index('mi')
    enough = mon[mon.days >= B.MIN_DAYS]
    totals = pd.DataFrame({'total_checkouts': enough.total_checkouts, 'n_rows': enough.total_checkouts})
    st = B3.month_status(totals, closure=B.CLOSURE)
    st['days'] = mon.days.reindex(st.index)
    few = st.days.notna() & (st.days < B.MIN_DAYS)
    st.loc[few, 'reason'] = 'fewer than 2 sampled days'
    st.loc[few, 'total_checkouts'] = mon.total_checkouts.reindex(st.index[few])
    # NOT IN RECORD (added after the first control table showed a month with no matched loans): a month in which fewer than 90% of the loans have a title is
    # missing, because titles cannot be matched there (the source files hold no titles at all in 2020-07, 2022-10 and 2023-08, 41% in 2017-08, 71% in 2017-03).
    st['title_share'] = (mon.titled / mon.total_checkouts).reindex(st.index)
    notitle = st.title_share.notna() & (st.title_share < TITLE_MIN) & (st.reason == '')
    st.loc[notitle, 'reason'] = 'source file has too few titles (under 90% of loans)'
    st['month_ok'] = st.reason == ''
    grid0, T = int(st.index.min()), len(st)
    okm = set(st[st.month_ok].index.tolist())
    # ---- theme counts: sum of matched loans x theme strength; sparse long table
    longs, checks = [], {}
    wm_ok = wm[wm.mi.isin(okm)]
    for level in B.LEVELS:
        wtl = WT[WT.level == level]
        ids = sorted(wtl.node_id.unique())
        D = B.PN.node_dense(wm, wtl, ids, grid0, T, okm)
        expect = wm_ok.merge(wtl.groupby('work_id').strength.sum().rename('s').reset_index(), on='work_id').eval('checkouts * s').sum()
        checks[level] = dict(identity=bool(np.isclose(D.sum(), expect, rtol=1e-9)), coverage=float(expect / max(1, int(st.loc[sorted(okm), 'total_checkouts'].sum()))))
        longs.append(B.PN.sparse_rows(level, ids, D, B.FORMAT, grid0))
        del D
    long = pd.concat(longs, ignore_index=True)
    stt = st.reset_index()[['mi', 'month_ok', 'total_checkouts', 'n_rows', 'reason', 'days', 'title_share']]
    stt.insert(0, 'format', B.FORMAT)
    cats = N[N.level.isin(B.LEVELS)][['node_id', 'level', 'parent', 'broad_id', 'label']]
    present = pd.concat([pd.DataFrame({'level': lv, 'node_id': sorted(set(long[long.level == lv].node_id))}) for lv in B.LEVELS])
    cats = cats.merge(present, on=['level', 'node_id'], how='inner').drop_duplicates(['level', 'node_id'])
    B.IO.save_parquet(long, P.counts); B.IO.save_parquet(stt, P.months); B.IO.save_parquet(cats, P.categories)
    Y.to_csv(B.DB / 'match_by_year.csv', index=False)
    meta = dict(build_id=B.IO.build_id([len(long), B.S.sha256]), taxonomy='v3', formats=[B.FORMAT], librivox=False, created=time.strftime('%Y-%m-%d %H:%M:%S'),
                months=[B3.ym_of(st.index.min()), B3.ym_of(st.index.max())])
    B.IO.save_json(meta, P.meta)
    # ---- report (structure only)
    bad = st[~st.month_ok]
    L = ['# Brisbane replication, step 2: match and panel (structure only)', '', f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}; Brisbane record SHA-256 `{B.SHA}`',
         f'- Seattle match index: {len(SW):,} works keyed by (normalised main title, author family name); {amb:,} keys had more than one Seattle work (the work with the most Seattle checkouts is taken)',
         f'- theme strength: {how}; only works with a narrow or middle theme profile ({len(themed):,}) add to theme counts',
         f'- months {B3.ym_of(st.index.min())} to {B3.ym_of(st.index.max())}: {len(st)}; usable {int(st.month_ok.sum())}; unusable {len(bad)}', '', '## Match rate by year (loans)']
    L += B.IO.md_table(Y.assign(match_rate=Y.match_rate.round(4), theme_rate=Y.theme_rate.round(4)))
    L += ['', f'Overall: {int(Y.matched_loans.sum()):,} of {int(Y.loans.sum()):,} loans matched ({100 * Y.matched_loans.sum() / Y.loans.sum():.1f}%), '
          f'{100 * Y.loans_with_theme_profile.sum() / Y.loans.sum():.1f}% carry a narrow or middle theme profile.', '', '## Unusable months']
    L += B.IO.md_table(bad.reset_index().assign(month=lambda x: [B3.ym_of(m) for m in x.mi])[['month', 'days', 'total_checkouts', 'title_share', 'reason', 'closure_ratio']].round(3)) if len(bad) else ['none']
    L += ['', '## Sampled days per usable month']
    L += B.IO.md_table(st[st.month_ok].groupby('days').size().rename('months').reset_index())
    L += ['', '## Identities', *[f'- {lv}: weighted-sum identity {c["identity"]}; share of usable-month loans carrying a {lv} theme (weighted) {100 * c["coverage"]:.1f}%' for lv, c in checks.items()]]
    L += ['', f'## Categories with counts', *[f'- {lv}: {int((cats.level == lv).sum())}' for lv in B.LEVELS]]
    (B.REP / 'brisbane_02_panel.md').write_text('\n'.join(L) + '\n')
    log('\n'.join(L))
    log(f'done in {time.time() - t0:.0f}s')


B3 = B.B3

if __name__ == '__main__':
    main()
