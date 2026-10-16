# Final unseen test: scoring of the frozen forecasts (addendum d). Run once, on the scoring date.
# Real mode: refuses to run unless addendum d is fingerprinted in prereg/README.md, the frozen forecast files have the SHA-256 printed there, the extended panel exists
# (29_final_test_world.py), and the scoring date has come. Rehearsal mode (--rehearsal ORIGIN) scores the STORED forecasts of a known origin against the panel of a dry-run
# world with the same code: a test of this script on months that are known, never a result.
#   ../../../.venv/bin/python 30_final_test_score.py                       real
#   ../../../.venv/bin/python 30_final_test_score.py --rehearsal 2026-05 --world data/db/final_test/dryrun_2026-06
import os
import sys, re, json, time, pathlib, argparse, hashlib, datetime
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _final_score as SC

ROOT = HERE.parents[2]
DB = ROOT / 'data' / 'db'
PREREG = ROOT / 'prereg'
FT = PREREG / 'final_test'
PIPES = ['naive', 'chronos', 'chronos2', 'chronos2_cur', 'chronos2_curdw', 'chronos2_bk', 'catchg_D', 'catchg_DW', 'catchg_DWS']
LIST = [p for p in PIPES if p != 'chronos2']
PRIMARY = 'chronos2_cur'
SCORING_DATE = '2026-12-05'          # fixed in addendum d
MIN_ROWS_PRIMARY = 400


def say(m):
    print(f'{time.strftime("%H:%M:%S")} {m}', flush=True)


def sha256_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def readme_hash(name):
    t = (PREREG / 'README.md').read_text()
    i = t.find(name)
    m = re.search(r'SHA-256:\s*([0-9a-f]{64})', t[i:i + 600]) if i >= 0 else None
    return m.group(1) if m else None


def mi_of(ym):
    y, m = ym.split('-')
    return int(y) * 12 + int(m) - 1


def guard():
    cand = sorted((PREREG / 'addenda_benchmark').glob('*_d_final_test_*.json'))
    if not cand:
        raise SystemExit('addendum d does not exist')
    f = cand[-1]
    if readme_hash(f.name) != sha256_file(f):
        raise SystemExit(f'{f.name} is not fingerprinted in prereg/README.md or was changed')
    if datetime.date.today().isoformat() < SCORING_DATE:
        raise SystemExit(f'scoring is not allowed before {SCORING_DATE} (addendum d)')
    return f.name, sha256_file(f)


def load_frozen(origins):
    parts = []
    for o in origins:
        csv = FT / f'forecasts_origin_{o}.csv'
        meta = json.loads((FT / f'forecasts_origin_{o}_meta.json').read_text())
        got = sha256_file(csv)
        if got != meta['csv_sha256'] or readme_hash(csv.name) != got:
            raise SystemExit(f'{csv.name}: SHA-256 differs from the meta file or prereg/README.md; scoring refused')
        parts.append(pd.read_csv(csv))
    return pd.concat(parts, ignore_index=True)


def attach_targets(F, panel):
    F = F.copy()
    F['mi'] = F.target_month.map(mi_of)
    F['origin_mi'] = F.origin.map(mi_of)
    tg = panel.set_index(['format', 'level', 'node_id', 'mi']).log_share
    F['y_true'] = tg.reindex(pd.MultiIndex.from_frame(F[['format', 'level', 'node_id', 'mi']])).to_numpy()
    F = F.rename(columns={'ls_t': 'y_t'})
    F['series_group'] = np.where(F.format.isin(SC.PRINT_EBOOK), 'print and ebook', 'audiobook')
    return F


def fmt(x, d=3):
    return '' if x is None or (isinstance(x, float) and not np.isfinite(x)) else f'{x:.{d}f}'


def a2_reference():
    """Main-sample (A2) values for comparison: AvgRelMAE from the stored table, pooled ratio recomputed on the rows of A2 (all 52 pipelines have a forecast)."""
    a2 = pd.read_csv(DB / 'benchmark' / 'stage2_results' / 'A2_table.csv', index_col=0)
    w = pd.read_parquet(DB / 'benchmark' / 'wide2.parquet')
    pipes52 = [p for p in a2.index if p in w.columns]
    w = w[(w.group == 'seattle') & (w.h == 1) & w.format.isin(SC.PRINT_EBOOK)].copy()
    w = w.dropna(subset=pipes52)
    w = w[w.groupby(['format', 'level', 'node_id']).origin_mi.transform('size') >= 12]      # the record's rule: series with at least 12 months common to all 52 pipelines
    w['naive'] = w.y_t
    w['y_true'] = w['y_true']
    ref = {}
    for p in LIST + ['chronos2']:
        if p == 'naive':
            continue
        r = SC.pooled_ratio(w, p, 'naive', n_boot=0)
        ref[p] = dict(pooled=r['ratio'], avg=float(a2.loc[p, 'AvgRelMAE']), rho=float(a2.loc[p, 'rho']))
    ref['rows'] = len(w)
    return ref


def report(F, label, origins, ref, out_md, out_csv, header_lines):
    L = list(header_lines)
    scored = F[F.y_true.notna()]
    L += ['', '## What was scored', '']
    L += ['| Horizon | Series group | Frozen rows | Rows with an observed target | Target months |', '| --- | --- | ---: | ---: | --- |']
    for (h, g), d in F.groupby(['h', 'series_group']):
        s = d[d.y_true.notna()]
        L.append(f'| {h} | {g} | {len(d):,} | {len(s):,} | {", ".join(sorted(s.target_month.unique())) or "none released or usable"} |')
    pe1 = scored[(scored.h == 1) & (scored.series_group == 'print and ebook')]
    L += ['']
    tabs = {}
    for (h, g), d in scored.groupby(['h', 'series_group']):
        tabs[(h, g)] = SC.score_table(d, PIPES, with_spearman=(h == 1))
    # primary
    L += ['## Primary hypothesis', '']
    t = tabs.get((1, 'print and ebook'))
    if t is None or len(pe1) < MIN_ROWS_PRIMARY:
        L += [f'Fewer than {MIN_ROWS_PRIMARY} horizon-1 print and ebook rows with an observed target ({len(pe1)}): the primary hypothesis cannot be judged on these months (addendum d).']
    else:
        r = t[t.pipeline == PRIMARY].iloc[0]
        ok = r.pooled_hi < 1
        L += [f'{PRIMARY} against repeating last month, horizon 1, print and ebook, {len(pe1):,} rows: pooled error ratio {fmt(r.pooled_ratio)} (95% interval {fmt(r.pooled_lo)} to {fmt(r.pooled_hi)}). '
              + ('The upper limit is below 1: supported.' if ok else 'The upper limit is not below 1: not supported by these months.'),
              f'Reference, main comparison (88 months, {ref["rows"]:,} rows): pooled ratio {fmt(ref[PRIMARY]["pooled"])}, AvgRelMAE {fmt(ref[PRIMARY]["avg"])}.']
    # tables
    for (h, g), t in sorted(tabs.items(), key=lambda kv: (kv[0][1] != 'print and ebook', kv[0][0])):
        L += ['', f'## Horizon {h}, {g}', '']
        L += ['Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record\'s geometric mean over series; intervals resample categories (2,000 draws).', '']
        cols = ['| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |' + (' Spearman rise (95%) | Main comparison: pooled ratio, AvgRelMAE |' if h == 1 and g == 'print and ebook' else ''),
                '| --- | ---: | --- | --- | ---: | ---: | ---: |' + (' --- | --- |' if h == 1 and g == 'print and ebook' else '')]
        for r in t.itertuples():
            row = (f'| {r.pipeline} | {r.rows:,} | {fmt(r.pooled_ratio)} ({fmt(r.pooled_lo)} to {fmt(r.pooled_hi)}) | {fmt(r.avg_rel_mae)} ({fmt(r.avg_lo)} to {fmt(r.avg_hi)}) | '
                   f'{"" if pd.isna(r.series) else int(r.series)} | {fmt(r.mae_x100, 2)} | {fmt(r.direction_accuracy, 3)} |')
            if h == 1 and g == 'print and ebook':
                sp = f'{fmt(r.spearman)} ({fmt(r.spearman_lo)} to {fmt(r.spearman_hi)})' if hasattr(r, 'spearman') and not pd.isna(r.spearman) else ''
                rf = ref.get(r.pipeline)
                row += f' {sp} | {fmt(rf["pooled"]) + ", " + fmt(rf["avg"]) if rf else ""} |'
            cols.append(row)
        L += cols
    # paired comparisons (horizon 1 and 2, print and ebook)
    L += ['', '## Paired comparisons, model held fixed (pooled ratio of the first to the second; below 1 = the first is better)', '']
    L += ['| Horizon | First | Second | Rows | Ratio (95%) |', '| --- | --- | --- | ---: | --- |']
    pairs = [('chronos2_cur', 'chronos2'), ('chronos2_curdw', 'chronos2'), ('chronos2_bk', 'chronos2'), ('chronos2_curdw', 'chronos2_cur'), ('catchg_DW', 'catchg_D'), ('catchg_DWS', 'catchg_D'),
             ('chronos2_cur', 'chronos'), ('chronos2_cur', 'catchg_D')]
    for h in (1, 2, 3):
        d = scored[(scored.h == h) & (scored.series_group == 'print and ebook')]
        if len(d) == 0:
            continue
        for a, b in pairs:
            r = SC.pooled_ratio(d, a, b)
            L.append(f'| {h} | {a} | {b} | {r["rows"]:,} | {fmt(r["ratio"])} ({fmt(r["lo"])} to {fmt(r["hi"])}) |')
    # rank agreement
    t = tabs.get((1, 'print and ebook'))
    if t is not None and len(t) > 2:
        x = t[t.pipeline.isin([p for p in LIST + ['chronos2'] if p != 'naive'])].set_index('pipeline')
        common = [p for p in x.index if p in ref]
        if len(common) >= 4:
            from scipy import stats
            rho = stats.spearmanr([x.loc[p, 'pooled_ratio'] for p in common], [ref[p]['pooled'] for p in common])[0]
            rho2 = stats.spearmanr([x.loc[p, 'pooled_ratio'] for p in common], [ref[p]['avg'] for p in common])[0]
            L += ['', '## Agreement of the ordering with the main comparison', '',
                  f'Rank correlation between the pooled error ratios of the {len(common)} pipelines on these months and in the main comparison (horizon 1, print and ebook): {fmt(rho)} against the main pooled ratios, '
                  f'{fmt(rho2)} against the main AvgRelMAE. Descriptive only; with this few rows differences between neighbouring pipelines are within their intervals.']
    L += ['', '## Not computed', '', 'The model confidence set, the surge average precision and the segments (after short or lasting rises, surge months) need more months or more events than the final test has (addendum d).', '']
    pathlib.Path(out_md).write_text('\n'.join(L))
    pd.concat([t.assign(horizon=h, series_group=g) for (h, g), t in tabs.items()], ignore_index=True).to_csv(out_csv, index=False)
    say(f'wrote {out_md} and {out_csv}')
    return tabs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--origins', default='2026-08', help='comma-separated origins whose frozen forecasts are scored')
    ap.add_argument('--panel', default=str(DB / 'final_test' / 'world' / 'db' / 'demand_panel.parquet'))
    ap.add_argument('--rehearsal', default=None, help='origin of STORED forecasts to score against a dry-run world (a test of this script on known months)')
    ap.add_argument('--world', default=None)
    a = ap.parse_args()
    ref = a2_reference()
    if a.rehearsal:
        o = mi_of(a.rehearsal)
        w = pd.read_parquet(DB / 'benchmark' / 'wide2.parquet', columns=['group', 'format', 'level', 'node_id', 'origin_mi', 'h', 'y_t'] + [p for p in PIPES if p != 'naive'])
        w = w[(w.group == 'seattle') & (w.origin_mi == o)].copy()
        w['naive'] = w.y_t
        w['origin'] = a.rehearsal
        w['target_month'] = [f'{(o + h) // 12:04d}-{(o + h) % 12 + 1:02d}' for h in w.h]
        w = w.rename(columns={'y_t': 'ls_t'})
        F = w
        panel = pd.read_parquet(pathlib.Path(a.world) / 'db' / 'demand_panel.parquet')
        header = ['# Final test, scoring rehearsal on known months', '', f'Written {time.strftime("%Y-%m-%d %H:%M")}. Code: code/main_study/benchmark/30_final_test_score.py --rehearsal {a.rehearsal}. '
                  'The stored benchmark forecasts of a known origin are scored against the panel of a dry-run world (targets built by the extension rule). This tests the scoring code and the extension on '
                  'months that are known; it is not a result of the final test.']
        report(attach_targets(F, panel), 'rehearsal', [a.rehearsal], ref, ROOT / 'data' / 'reports' / 'benchmark_final_test_rehearsal.md', DB / 'final_test' / 'rehearsal_scores.csv', header)
        return
    name, sha = guard()
    origins = a.origins.split(',')
    F = load_frozen(origins)
    panel = pd.read_parquet(a.panel)
    n1 = attach_targets(F, panel)
    n1 = n1[(n1.h == 1) & (n1.series_group == 'print and ebook') & n1.y_true.notna()]
    if len(n1) < MIN_ROWS_PRIMARY:
        raise SystemExit(f'only {len(n1)} horizon-1 print and ebook rows have an observed target (addendum d needs {MIN_ROWS_PRIMARY}): not scored yet; wait for the next release')
    header = ['# Final unseen test: results', '', f'Scored {time.strftime("%Y-%m-%d %H:%M")} by code/main_study/benchmark/30_final_test_score.py. Protocol: prereg/addenda_benchmark/2026-10-17_c_final_test_forecasts.json (forecasts, '
              f'SHA-256 d893b6b386b3e7e1cd64f59455681b842457fff981c4fff82a8a30639a1e6729) and {name} (scoring, SHA-256 {sha}). Frozen forecast files: '
              + '; '.join(f'forecasts_origin_{o}.csv {sha256_file(FT / f"forecasts_origin_{o}.csv")}' for o in origins) + '.']
    report(attach_targets(F, panel), 'final', origins, ref, ROOT / 'data' / 'reports' / 'benchmark_final_test.md', DB / 'final_test' / 'final_scores.csv', header)


if __name__ == '__main__':
    main()
