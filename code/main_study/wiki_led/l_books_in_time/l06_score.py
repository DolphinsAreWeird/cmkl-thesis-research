# l06. Addendum l, step 5: score the blind test ONCE.  Settings: prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json, blind_test
# (read-only; SHA-256 checked).  Written and rehearsed on 30 Oct 2026, before any month after 2026-08 was downloaded.
#
# Final mode (no option): target 2026-09.  Guards: the forecasts prereg/blind_l/forecasts_origin_2026-08.csv must have the SHA-256 printed in
#   prereg/README.md and be older than every downloaded 2026-09 file; the month must be complete in data/db/final_test/new_months_api_counts.parquet
#   (28_final_test_download.py); the report must not exist yet (scored once).
# Rehearsal mode (--rehearsal): target 2026-08, a known month, from the files downloaded with 28_final_test_download.py --test-months
#   (data/raw/modern/final_test_known/), with rehearsal forecasts at origin 2026-07 (l05_freeze.py --rehearsal); August is treated as new.
#   Checks: the August loans found here equal the stored rows' L_next at origin 2026-07, and the library totals equal the stored panel's.
#
# Target loans: the downloaded rows of the target month are matched to works by the final test's own function (code/main_study/benchmark/
#   _final_extend.py, extend(): record key of 10_v3_spl_rows.py, new records grouped into works by the work key, a new record whose key equals a
#   stored work's key joins that work), written to a world folder; a work and format's loans are the sum over its records; a forecast row
#   whose work has no row in the target month has 0 loans (Test D: months after the first loan without a row are 0).
# Excluded month (parent rule): if, for any format, the target month's library-wide total is below half of the median of that format's totals
#   over the previous 12 months (stored panel, months with a total above 0), the month is never a target: nothing is scored and the report says so.
# Measures (record): D = ln(1 + L(target)) - ln(1 + M6) in float32 as Test D; rose: D >= ln 1.5; surge: D >= ln 2 and L - M6 >= 5.
#   Change rank: Spearman of prediction and D within each format over all forecast rows, averaged over the three formats.  Top 20 that rose:
#   lists within each format (60 slots), exact (Clopper-Pearson) 95% intervals; the same among rows not yet risen; level: mean absolute error
#   of Y = ln(1 + L) and in loans.  Bootstrap: 2,000 draws of works with replacement (all formats of a drawn work together), seed 20261030.
# Decision LB: HMW14 minus HM change rank, paired over works, has a 95% interval above 0.  All else is descriptive.
# Outputs: final data/reports/wiki_led_l_blind_2026-09.md and .json; rehearsal data/reports/wiki_led_l_blind_rehearsal_2026-08.md and .json.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/l_books_in_time/l06_score.py [--rehearsal]
import os
os.environ.setdefault('TAXO', 'v3')
import sys, json, time, hashlib, pathlib, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import spearmanr, beta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))                       # code/, for config
sys.path.insert(0, str(HERE.parents[1] / 'benchmark'))         # the final test's helpers
from config import D as DATA_DIR                               # noqa: E402
import _final_extend as X                                      # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
REH = '--rehearsal' in sys.argv
OUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
REP = DATA / 'reports'
FT = DATA / 'db' / 'final_test'
SEED, NB = 20261030, 2000
LN15, LN2 = np.log(1.5), np.log(2)
FMTS = ['print', 'ebook', 'audiobook']
LABEL = {'BOOK': 'print', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


if REH:
    TY, TM = 2026, 8
    RAW = DATA / 'raw' / 'modern' / 'final_test_known'
    CSV = DATA / 'interim' / 'l_rehearsal' / 'forecasts_origin_2026-07.csv'
    WORLD = DATA / 'interim' / 'l_rehearsal' / 'world_2026-08'
    BEFORE = TY * 12 + TM - 1                                  # August and later treated as new
    NAME = 'wiki_led_l_blind_rehearsal_2026-08'
else:
    TY, TM = 2026, 9
    RAW = DATA / 'raw' / 'modern' / 'final_test'
    CSV = ROOT / 'prereg' / 'blind_l' / 'forecasts_origin_2026-08.csv'
    WORLD = OUT / 'world_2026-09'
    BEFORE = None
    NAME = 'wiki_led_l_blind_2026-09'
    assert not (REP / f'{NAME}.json').exists(), 'the blind test has been scored already (scored once)'
    readme = (ROOT / 'prereg' / 'README.md').read_text()
    m = re.search(r'blind_l/forecasts_origin_2026-08\.csv` SHA-256: ([0-9a-f]{64})', readme)
    assert m and hashlib.sha256(CSV.read_bytes()).hexdigest() == m.group(1), 'frozen forecasts changed or not fingerprinted'
    cnt = pd.read_parquet(FT / 'new_months_api_counts.parquet')
    c = cnt[(cnt.year == TY) & (cnt.month == TM)]
    assert len(c) == 3 and c.complete.all(), 'target month not completely downloaded (28_final_test_download.py)'
    raw_files = [RAW / f'seattle_{f.lower()}_{TY}-{TM:02d}.jsonl' for f in X.FILE_OF]
    assert all(p.exists() for p in raw_files), 'raw files of the target month missing'
    assert CSV.stat().st_mtime < min(p.stat().st_mtime for p in raw_files), 'forecasts are not older than the downloaded month'
TMI = TY * 12 + TM - 1
YM = f'{TY}-{TM:02d}'

# ---------------------------------------------------------------- target-month rows -> works (the final test's extend())
raw = {}
for fmt in X.FILE_OF:
    with open(RAW / f'seattle_{fmt.lower()}_{YM}.jsonl') as fh:
        recs = [json.loads(line) for line in fh]
    df = pd.DataFrame(recs, dtype=object) if recs else pd.DataFrame(columns=X.RAW_COLS)
    for col in X.RAW_COLS:
        if col not in df.columns:
            df[col] = ''
    raw[fmt] = df.fillna('')
    log(fmt, 'rows', len(df))
WORLD.mkdir(parents=True, exist_ok=True)
ext = X.extend(raw, WORLD, before_mi=BEFORE, hash_cache=FT / 'record_keys.npz', log=lambda s: log(s))
rw = pd.read_parquet(WORLD / 'taxonomy' / 'spl_record_work.parquet').drop_duplicates('record_id').set_index('record_id').work_id
loans, totals = [], {}
for fmt, fname in X.FILE_OF.items():
    t = pq.read_table(WORLD / 'taxonomy' / f'spl_rows_{fname}.parquet', filters=[('year', '==', TY), ('month', '==', TM)]).to_pandas()
    totals[LABEL[fmt]] = int(t.checkouts.sum())
    t['work_id'] = rw.reindex(t.record_id.astype(np.int64).to_numpy()).to_numpy()
    loans.append(t.groupby('work_id').checkouts.sum().rename('L_next').reset_index().assign(format=LABEL[fmt]))
LOANS = pd.concat(loans, ignore_index=True)

# ---------------------------------------------------------------- excluded-month rule
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'total_checkouts', 'month_ok']).drop_duplicates(['format', 'mi'])
excl = {}
for f in FMTS:
    prev = P[(P.format == f) & (P.mi >= TMI - 12) & (P.mi < TMI) & (P.total_checkouts > 0)].total_checkouts
    excl[f] = dict(total=totals[f], median_prev12=float(prev.median()), ok=bool(totals[f] >= 0.5 * prev.median()))
month_ok = all(v['ok'] for v in excl.values())
log('target totals and rule:', excl)
res = dict(mode='rehearsal' if REH else 'final', target=YM, forecasts=str(CSV.relative_to(ROOT)), extend_report=ext, excluded_rule=excl,
           month_ok=month_ok)
if REH:
    st = P[P.mi == TMI].set_index('format').total_checkouts
    res['check_totals_equal_stored_panel'] = {f: [totals[f], int(st[f])] for f in FMTS}

if not month_ok:
    res['scored'] = False
    res['note'] = 'The target month fails the excluded-month rule of the parent record, so it is never a target; nothing is scored.'
else:
    F = pd.read_csv(CSV)
    F['format'] = F.format.astype(str)
    F = F.merge(LOANS, on=['work_id', 'format'], how='left')
    F['L_next'] = F.L_next.fillna(0).astype(np.float32)
    M6 = F.M6.astype(np.float32).to_numpy()
    F['D'] = np.log1p(F.L_next.to_numpy(np.float32)) - np.log1p(M6)
    F['rose'] = (F.D >= LN15).astype(int)
    F['Sg'] = ((F.D >= LN2) & ((F.L_next - F.M6) >= 5)).astype(int)
    F['Y'] = np.log1p(F.L_next.astype(float))
    F['not_yet'] = F.not_yet.astype(bool)
    if REH:
        S = pd.read_parquet(OUT / 'rows.parquet', columns=['work_id', 'format', 'mi', 'L_next'])
        S = S[S.mi == TMI - 1].assign(format=lambda x: x.format.astype(str))
        cm = F[['work_id', 'format', 'L_next']].merge(S, on=['work_id', 'format'], how='outer', suffixes=('', '_stored'), indicator=True)
        both = cm[cm._merge == 'both']
        dd = (both.L_next - both.L_next_stored).abs()
        res['check_loans_equal_stored'] = dict(rows_both=int(len(both)), only_here=int((cm._merge == 'left_only').sum()),
                                               only_stored=int((cm._merge == 'right_only').sum()), equal=int((dd == 0).sum()),
                                               max_abs_diff=float(dd.max()), rows_differing=int((dd > 0).sum()))
        log('check: loans of the target month against the stored rows', res['check_loans_equal_stored'])

    def cp(k, n):
        lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
        hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
        return [float(lo), float(hi)]

    def rank(q, col):
        return float(np.mean([spearmanr(g[col], g.D).statistic for _, g in q.groupby('format')]))

    def top(q, col, k=20):
        t = q.sort_values(col, ascending=False, kind='stable').groupby('format', sort=False).head(k)
        h, n = int(t.rose.sum()), len(t)
        return dict(share=h / n, hits=h, slots=n, ci=cp(h, n))

    MOD_D = ['naive_D', 'H_D', 'HM_D', 'W14_D', 'HMW14_D']
    sc = dict(rows=int(len(F)), base_rose=float(F.rose.mean()), base_surge=float(F.Sg.mean()),
              rows_by_format=F.format.value_counts().to_dict(), rows_with_article_feature=int(((F.has_book_page == 1) | (F.has_author_page == 1)).sum()))
    for m in MOD_D:
        sc[m] = dict(change_rank=rank(F, m), by_format={f: float(spearmanr(F.loc[F.format == f, m], F.loc[F.format == f, 'D']).statistic) for f in FMTS},
                     top20=top(F, m), early_top20=top(F[F.not_yet], m))
    for m in ['H_Y', 'HM_Y', 'HMW14_Y']:
        e = (np.expm1(F[m]).clip(lower=0) - F.L_next).abs()
        sc[m] = dict(mae_y=float((F[m] - F.Y).abs().mean()), mae_loans=float(e.mean()), median_err_loans=float(e.median()))

    # bootstrap over works, paired
    rng = np.random.default_rng(SEED)
    grp = F.groupby('work_id').indices
    wids = np.array(list(grp))
    idx_of = [grp[w] for w in wids]
    fmt_arr = F.format.to_numpy()
    Dv = F.D.to_numpy(float)
    cols = {m: F[m].to_numpy(float) for m in ['HMW14_D', 'HM_D', 'W14_D', 'H_D']}
    ae = {m: np.abs(F[m].to_numpy(float) - F.Y.to_numpy(float)) for m in ['HM_Y', 'H_Y']}
    draws = {k: [] for k in ('lb', 'w14', 'hm_minus_h_mae')}
    for b in range(NB):
        ii = np.concatenate([idx_of[j] for j in rng.integers(0, len(wids), len(wids))])
        rk = {}
        for m in ('HMW14_D', 'HM_D', 'W14_D'):
            rk[m] = np.mean([spearmanr(cols[m][ii][fmt_arr[ii] == f], Dv[ii][fmt_arr[ii] == f]).statistic for f in FMTS])
        draws['lb'].append(rk['HMW14_D'] - rk['HM_D'])
        draws['w14'].append(rk['W14_D'])
        draws['hm_minus_h_mae'].append(ae['HM_Y'][ii].mean() - ae['H_Y'][ii].mean())
        if (b + 1) % 500 == 0:
            log('bootstrap', b + 1)
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    lb_est = sc['HMW14_D']['change_rank'] - sc['HM_D']['change_rank']
    sc['LB'] = dict(rule='HMW14 minus HM change rank, paired over works, 95% interval above 0', est=lb_est, ci=q(draws['lb']),
                    passed=bool(q(draws['lb'])[0] > 0))
    sc['W14_change_rank_ci'] = q(draws['w14'])
    sc['HM_minus_H_mae_y'] = dict(est=sc['HM_Y']['mae_y'] - sc['H_Y']['mae_y'], ci=q(draws['hm_minus_h_mae']))
    res['scored'] = True
    res['scores'] = sc
res['runtime_s'] = round(time.time() - T0)
res['made'] = time.strftime('%Y-%m-%d %H:%M') + ' +06:30 (' + time.strftime('%H:%M', time.gmtime()) + ' UTC)'
(REP / f'{NAME}.json').write_text(json.dumps(res, indent=1, default=str))

# ---------------------------------------------------------------- report
L = [f'# Addendum l, blind test{" (REHEARSAL on a known month)" if REH else ""}: target {YM}', '',
     f'Made by `code/main_study/wiki_led/l_books_in_time/l06_score.py{" --rehearsal" if REH else ""}` on {res["made"]}. Forecasts: `{res["forecasts"]}`.',
     ('Rehearsal: August 2026 is a known month that the backtest has already scored, so these numbers are not a test; they check the code.' if REH
      else 'Scored once, as fixed in the record.'), '',
     f'- Library totals and the excluded-month rule: ' + '; '.join(f'{f} {v["total"]:,} against half of {v["median_prev12"]:,.0f}: {"ok" if v["ok"] else "EXCLUDED"}' for f, v in excl.items())]
if REH:
    L.append(f'- Check, totals against the stored panel (here, stored): {res["check_totals_equal_stored_panel"]}')
if not res['scored']:
    L += ['', res['note']]
else:
    sc = res['scores']
    if REH:
        L.append(f'- Check, target loans against the stored rows: {res["check_loans_equal_stored"]}')
    L += [f'- Forecast rows {sc["rows"]:,} {sc["rows_by_format"]}; with an article feature {sc["rows_with_article_feature"]:,}; base rate rose {sc["base_rose"]:.3f}, surged {sc["base_surge"]:.4f}.', '',
          '## Decision LB', '', f'{sc["LB"]["rule"]}: {sc["LB"]["est"]:+.4f} [{sc["LB"]["ci"][0]:+.4f}, {sc["LB"]["ci"][1]:+.4f}]; passed: {"yes" if sc["LB"]["passed"] else "no"}.', '',
          '## Scores (descriptive)', '', '| Model | Change rank | print | ebook | audiobook | Top 20 rose [exact 95%] | Not yet risen, top 20 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for m in MOD_D:
        s = sc[m]
        L.append(f'| {m[:-2]} | {s["change_rank"]:.4f} | {s["by_format"]["print"]:.4f} | {s["by_format"]["ebook"]:.4f} | {s["by_format"]["audiobook"]:.4f} | '
                 f'{s["top20"]["share"]:.3f} ({s["top20"]["hits"]}/{s["top20"]["slots"]}) [{s["top20"]["ci"][0]:.3f}, {s["top20"]["ci"][1]:.3f}] | '
                 f'{s["early_top20"]["share"]:.3f} ({s["early_top20"]["hits"]}/{s["early_top20"]["slots"]}) |')
    L += ['', f'W14 change rank, interval over works: [{sc["W14_change_rank_ci"][0]:.4f}, {sc["W14_change_rank_ci"][1]:.4f}].', '',
          '| Level model | MAE of Y | MAE in loans | Median error in loans |', '| --- | --- | --- | --- |']
    for m in ['H_Y', 'HM_Y', 'HMW14_Y']:
        L.append(f'| {m[:-2]} | {sc[m]["mae_y"]:.4f} | {sc[m]["mae_loans"]:.2f} | {sc[m]["median_err_loans"]:.2f} |')
    L.append(f'\nHM minus H, MAE of Y: {sc["HM_minus_H_mae_y"]["est"]:+.4f} [{sc["HM_minus_H_mae_y"]["ci"][0]:+.4f}, {sc["HM_minus_H_mae_y"]["ci"][1]:+.4f}].')
L.append(f'\nRun time {res["runtime_s"]} s.')
(REP / f'{NAME}.md').write_text('\n'.join(L) + '\n')
log('wrote', REP / f'{NAME}.md')
