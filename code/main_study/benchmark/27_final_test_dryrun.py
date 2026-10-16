# Dry run of the final-test data extension on months that are already known. The last months of the stored data are treated as 'released after the freeze':
# the stored rows, records, works and theme strengths from the freeze month on are left out, the rows of those months are rebuilt from the stored records as if
# they had just come from the API (raw fields), and the extension of _final_extend.py brings them in. The Study 3 panel builder then makes the panel of the extended
# world, which is compared with the stored panel. Origin = the month before the freeze: the stored forecasts of the final-test pipelines at that origin (horizons 1 to 3)
# are scored against targets from the extended world and against the stored targets, which is exactly the situation of the final test.
# All months used here are known; nothing in this script is evidence about the unseen months.
#   ../../../.venv/bin/python 27_final_test_dryrun.py --freeze 2026-06 --step all      (under the heavy-job lock)
import os
os.environ.setdefault('TAXO', 'v3')
import sys, json, time, pathlib, argparse, subprocess
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd, pyarrow.parquet as pq
import _final_extend as X

ROOT = X.ROOT
DB = X.DB
FT_DIR = DB / 'final_test'
STORED_PANEL = DB / 'study3' / 'demand_panel.parquet'
REPORT = ROOT / 'data' / 'reports' / 'benchmark_final_test_dryrun.md'
REPORT_VOCAB = ROOT / 'data' / 'reports' / 'benchmark_final_test_dryrun_unseen_vocab.md'
PIPES = ['naive', 'chronos', 'chronos2', 'chronos2_cur', 'chronos2_curdw', 'chronos2_bk', 'catchg_D', 'catchg_DW', 'catchg_DWS']


def say(m):
    print(f'{time.strftime("%H:%M:%S")} {m}', flush=True)


def mi_of(ym):
    y, m = ym.split('-')
    return int(y) * 12 + int(m) - 1


def raw_rows_since(before_mi):
    """The stored rows from month index before_mi on, as raw API rows (strings), rebuilt from the stored records."""
    out = {}
    for fmt, f in X.FILE_OF.items():
        t = pq.read_table(X.V3 / f'spl_rows_{f}.parquet').to_pandas()
        mi = t.year.astype(np.int64) * 12 + t.month.astype(np.int64) - 1
        t = t[mi >= before_mi].reset_index(drop=True)
        ids = np.unique(t.record_id.to_numpy()).astype(np.int64).tolist()
        R = pq.read_table(X.V3 / 'spl_records.parquet', columns=['record_id', 'title', 'creator', 'creator_from_title', 'subjects', 'publisher', 'publicationyear', 'isbn'],
                          filters=[('record_id', 'in', ids)]).to_pandas().set_index('record_id')
        R = R.loc[t.record_id.astype(np.int64)].reset_index(drop=True)
        creator = R.creator.where(~R.creator_from_title.astype(bool), '') if fmt == 'BOOK' else R.creator
        out[fmt] = pd.DataFrame({'checkoutyear': t.year.astype(str), 'checkoutmonth': t.month.astype(str), 'checkouts': t.checkouts.astype(str),
                                 'title': R.title, 'creator': creator, 'subjects': R.subjects, 'publisher': R.publisher if fmt != 'BOOK' else '',
                                 'publicationyear': R.publicationyear, 'isbn': R.isbn if fmt != 'BOOK' else ''})
        say(f'{fmt}: {len(out[fmt]):,} raw rows from {len(ids):,} records')
    return out


def step_extend(a):
    before = mi_of(a.freeze)
    world = pathlib.Path(a.world)
    new_raw = raw_rows_since(before)
    rep = X.extend(new_raw, world, before_mi=before, hash_cache=FT_DIR / 'record_keys.npz', log=say, restrict_vocab=a.unseen_vocab)
    link = world / 'taxonomy' / 'spl_api_counts.parquet'
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(X.V2 / 'spl_api_counts.parquet')
    (world / 'extend_report.json').write_text(json.dumps(rep, indent=1, default=str))
    say(f'extension done: {json.dumps(rep, default=str)}')


def step_panel(a):
    cmd = [sys.executable, '-u', str(HERE / '26_final_test_panel.py'), '--world', str(a.world)]
    r = subprocess.call(cmd)
    if r:
        raise SystemExit(f'panel build failed ({r})')


def compare(a):
    before = mi_of(a.freeze)
    world = pathlib.Path(a.world)
    old = pd.read_parquet(STORED_PANEL)
    new = pd.read_parquet(world / 'db' / 'demand_panel.parquet')
    key = ['format', 'level', 'node_id', 'mi']
    cols = ['log_share', 'share', 'weighted_checkouts', 'total_checkouts', 'month_ok', 'size_ok', 'n_works_month']
    m = old[key + cols].merge(new[key + cols], on=key, how='outer', suffixes=('_s', '_w'), indicator=True)
    L = ['# Final test, dry run of the data extension on known months', '',
         f'Written {time.strftime("%Y-%m-%d %H:%M")}. Code: code/main_study/benchmark/27_final_test_dryrun.py with _final_extend.py and 26_final_test_panel.py. '
         f'Freeze month {a.freeze}: stored rows, records, works and strengths from {a.freeze} on were left out and the rows of {a.freeze} to 2026-08 were brought in again as new rows. '
         'All months here are known; this is a test of the machinery, not evidence about unseen months.', '']
    L += ['## Months before the freeze: the rebuilt panel equals the stored panel', '']
    pre = m[m.mi < before]
    both = pre[pre._merge == 'both']
    d = (both.log_share_s - both.log_share_w).abs()
    L += [f'- rows compared {len(both):,}; rows only in one panel {int((pre._merge != "both").sum()):,}; log share: both missing {int((both.log_share_s.isna() & both.log_share_w.isna()).sum()):,}, '
          f'max abs difference {np.nanmax(d):.2e}; size_ok differs in {int((both.size_ok_s != both.size_ok_w).sum())} rows; month_ok differs in {int((both.month_ok_s != both.month_ok_w).sum())} rows.']
    post = m[m.mi >= before]
    pb = post[post._merge == 'both']
    L += ['', f'## Months from the freeze on: extended panel against stored panel (the stored panel used the full taxonomy)', '']
    L += [f'- rows compared {len(pb):,}; rows only in one panel {int((post._merge != "both").sum()):,}; month_ok differs in {int((pb.month_ok_s != pb.month_ok_w).sum())} rows']
    both_ok = pb[pb.log_share_s.notna() & pb.log_share_w.notna()]
    dd = both_ok.log_share_w - both_ok.log_share_s
    q = dd.abs().quantile([.5, .9, .99]).to_numpy()
    L += [f'- log share rows with a value in both: {len(both_ok):,}; difference (extended minus stored): mean {dd.mean():+.4f}, median abs {q[0]:.4f}, 90th percentile abs {q[1]:.4f}, 99th percentile abs {q[2]:.4f}, max abs {dd.abs().max():.4f}']
    L += ['', '| Format | Level | Months | Rows | Mean difference | Median abs | 90th pct abs | Share of rows with abs difference > 0.05 |', '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for (f, lv), g in both_ok.groupby(['format', 'level']):
        x = g.log_share_w - g.log_share_s
        L.append(f'| {f} | {lv} | {g.mi.nunique()} | {len(g):,} | {x.mean():+.4f} | {x.abs().median():.4f} | {x.abs().quantile(.9):.4f} | {(x.abs() > 0.05).mean():.3f} |')
    # total checkouts
    tt = pb.groupby(['format', 'mi']).agg(s=('total_checkouts_s', 'first'), w=('total_checkouts_w', 'first')).reset_index()
    L += ['', f'- format-month totals equal in {int((tt.s == tt.w).sum())} of {len(tt)} format-months']
    # scoring rehearsal
    L += score_rehearsal(a, new, before)
    rp = REPORT_VOCAB if a.unseen_vocab else REPORT
    rp.write_text('\n'.join(L) + '\n')
    say(f'wrote {rp}')


def score_rehearsal(a, new, before):
    """Stored forecasts of the final-test pipelines at the origin before the freeze, horizons 1 to 3, scored against stored and extended targets."""
    origin = before - 1
    w = pd.read_parquet(DB / 'benchmark' / 'wide2.parquet', columns=['group', 'format', 'level', 'node_id', 'origin_mi', 'h', 'y_t', 'y_true'] + [p for p in PIPES if p != 'naive'])
    w = w[(w.group == 'seattle') & (w.origin_mi == origin)].copy()
    w['naive'] = w.y_t
    w['mi'] = w.origin_mi + w.h
    tg = new[new.mi >= before].set_index(['format', 'level', 'node_id', 'mi']).log_share
    w['y_world'] = tg.reindex(pd.MultiIndex.from_frame(w[['format', 'level', 'node_id', 'mi']])).to_numpy()
    L = ['', f'## Scoring rehearsal: origin {pd.Timestamp(year=origin // 12, month=origin % 12 + 1, day=1):%Y-%m}, stored forecasts, targets from the stored panel and from the extended world', '']
    L += ['Print and ebook, narrow and middle themes; error = absolute error in log share; pooled ratio = sum of absolute errors of the pipeline / of naive over the rows both targets exist for; '
          'AvgRelMAE = geometric mean over series of the ratio of mean absolute errors (series with a naive error of 0 left out).', '']
    L += ['| Horizon | Rows | Pipeline | Pooled ratio, stored target | Pooled ratio, extended target | AvgRelMAE, stored target | AvgRelMAE, extended target | Mean abs error x100, stored | Mean abs error x100, extended |',
          '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for h in (1, 2, 3):
        g = w[(w.h == h) & w.format.isin(['print', 'ebook']) & w.y_true.notna() & w.y_world.notna() & w.naive.notna()]
        if len(g) == 0:
            continue
        for p in PIPES:
            gg = g[g[p].notna()] if p != 'naive' else g
            row = [h, len(gg), p]
            for tcol in ('y_true', 'y_world'):
                e = (gg[p] - gg[tcol]).abs(); en = (gg.naive - gg[tcol]).abs()
                row.append(f'{e.sum() / en.sum():.3f}')
            for tcol in ('y_true', 'y_world'):
                e = (gg[p] - gg[tcol]).abs(); en = (gg.naive - gg[tcol]).abs()
                s = pd.DataFrame({'sid': gg.format + '|' + gg.level + '|' + gg.node_id, 'e': e, 'en': en}).groupby('sid').mean()
                s = s[s.en > 0]
                row.append(f'{np.exp(np.log(s.e / s.en).mean()):.3f}' if len(s) else '')
            for tcol in ('y_true', 'y_world'):
                row.append(f'{(gg[p] - gg[tcol]).abs().mean() * 100:.2f}')
            L.append('| ' + ' | '.join(str(x) for x in row[:3]) + ' | ' + ' | '.join(row[3:]) + ' |')
    return L


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', default='2026-06')
    ap.add_argument('--world', default=None)
    ap.add_argument('--step', default='all', choices=['extend', 'panel', 'compare', 'all'])
    ap.add_argument('--unseen-vocab', action='store_true', help='drop headings and terms that occur only on works first seen from the freeze month on')
    a = ap.parse_args()
    a.world = a.world or str(FT_DIR / (f'dryrun_{a.freeze}' + ('_unseen_vocab' if a.unseen_vocab else '')))
    FT_DIR.mkdir(parents=True, exist_ok=True)
    if a.step in ('extend', 'all'):
        step_extend(a)
    if a.step in ('panel', 'all'):
        step_panel(a)
    if a.step in ('compare', 'all'):
        compare(a)
