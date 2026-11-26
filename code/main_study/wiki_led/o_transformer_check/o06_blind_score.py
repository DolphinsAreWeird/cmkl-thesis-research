# o06. Addendum o, step 7: score the blind month ONCE.  Settings: prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json,
# tests.O3_blind_month (read-only; SHA-256 checked).  Written and rehearsed on 26 Nov 2026, before any month after 2026-08 was downloaded.
#
# Final mode (no option): target 2026-09.  Run AFTER addendum l's l06_score.py (final mode), which downloads nothing itself but builds the
#   September world folder (data/db/wiki_led/l_books_in_time/world_2026-09/) from the files of 28_final_test_download.py and applies the
#   excluded-month rule.  Guards: prereg/blind_o/forecasts_origin_2026-08.csv must have the SHA-256 printed in prereg/README.md and be older
#   than every downloaded 2026-09 file; l06's report must exist; this report must not exist yet (scored once).
# Rehearsal mode (--rehearsal): target 2026-08, a known month, from addendum l's rehearsal world (data/interim/l_rehearsal/world_2026-08/),
#   with forecasts taken from the walk-forward predictions at origin 2026-07 (five-seed means; HMW14 and HMW14Z from addendum n, HMW14C and
#   HMW14CZ from o02).  Check: the August loans found here equal the stored rows' L_next.  Writes only a rehearsal report.
#
# Target loans and the excluded-month rule are l06_score.py's (code copied): a work and format's loans are the sum over its records in the
#   world folder; a forecast row whose work has no row in the target month has 0 loans.  D = ln(1 + L) - ln(1 + M6) in float32.
# Measures: change rank = Spearman of prediction and D within each format over all forecast rows, averaged over the formats; top 20 that rose
#   (lists within format, 60 slots, Clopper-Pearson intervals), also among rows not yet risen.  Paired bootstrap over works (all formats of a
#   drawn work together), 2,000 draws, seed 20261126.
# Decision O3: HMW14Z minus HMW14 and HMW14CZ minus HMW14C change rank, each with a 95% interval above 0.  One month is a small test.
# Outputs: final data/reports/transformer_check_blind_2026-09.md and .json; rehearsal ..._blind_rehearsal_2026-08.md and .json.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/o_transformer_check/o06_blind_score.py [--rehearsal]
import sys, json, time, hashlib, pathlib, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import spearmanr, beta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from config import D as DATA_DIR                               # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_o_transformer_inputs_check.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'ad6a417b47cc60b21b59742fbf79574a5370150ff78ba617e932c0a8a7fc62d6', 'addendum o changed'
REH = '--rehearsal' in sys.argv
LOUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
REP = DATA / 'reports'
SEED, NB = 20261126, 2000
SEEDS = [20261020 + i for i in range(5)]
LN15, LN2 = np.log(1.5), np.log(2)
FMTS = ['print', 'ebook', 'audiobook']
FILE_OF = {'BOOK': 'book', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
LABEL = {'BOOK': 'print', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
MOD = ['naive_D', 'HMW14_D', 'HMW14Z_D', 'HMW14C_D', 'HMW14CZ_D']
PAIRS = {'O3_Z': ('HMW14Z_D', 'HMW14_D'), 'O3_CZ_vs_C': ('HMW14CZ_D', 'HMW14C_D'), 'C_gain': ('HMW14C_D', 'HMW14_D')}
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


if REH:
    TY, TM = 2026, 8
    WORLD = DATA / 'interim' / 'l_rehearsal' / 'world_2026-08'
    NAME = 'transformer_check_blind_rehearsal_2026-08'
    keys = pd.read_parquet(NOUT / 'preds' / 'keys.parquet', columns=['work_id', 'format', 'mi', 'L_next'])
    sel = (keys.mi == 2026 * 12 + 6).to_numpy()
    R = pd.read_parquet(LOUT / 'rows.parquet', columns=['work_id', 'format', 'mi', 'L_t', 'M6', 'h_lt', 'h_m6', 'has_book_page', 'has_author_page'])
    R = R[R.mi == 2026 * 12 + 6].assign(format=lambda x: x.format.astype(str))
    F = keys[sel][['work_id', 'format', 'L_next']].rename(columns={'L_next': 'L_next_stored'}).reset_index(drop=True)
    F['format'] = F.format.astype(str)
    for m in ('HMW14', 'HMW14Z', 'HMW14C', 'HMW14CZ'):
        d = NOUT if m in ('HMW14', 'HMW14Z') else OUT
        F[m + '_D'] = np.mean([np.load(d / 'preds' / str(s) / f'{m}.npy')[sel] for s in SEEDS], axis=0)
    F = F.merge(R.drop(columns='mi'), on=['work_id', 'format'], how='left', validate='one_to_one')
    assert F.M6.notna().all()
    F['not_yet'] = (F.h_lt - F.h_m6) < LN15
    F['naive_D'] = F.h_lt - F.h_m6
    CSV_NAME = 'walk-forward predictions at origin 2026-07 (rehearsal)'
else:
    TY, TM = 2026, 9
    RAW = DATA / 'raw' / 'modern' / 'final_test'
    CSV = ROOT / 'prereg' / 'blind_o' / 'forecasts_origin_2026-08.csv'
    WORLD = LOUT / 'world_2026-09'
    NAME = 'transformer_check_blind_2026-09'
    assert not (REP / f'{NAME}.json').exists(), 'the blind month has been scored already (scored once)'
    readme = (ROOT / 'prereg' / 'README.md').read_text()
    m = re.search(r'blind_o/forecasts_origin_2026-08\.csv` SHA-256: ([0-9a-f]{64})', readme)
    assert m and hashlib.sha256(CSV.read_bytes()).hexdigest() == m.group(1), 'frozen forecasts changed or not fingerprinted'
    raw_files = [RAW / f'seattle_{f.lower()}_{TY}-{TM:02d}.jsonl' for f in FILE_OF]
    assert all(p.exists() for p in raw_files), 'raw files of the target month missing (28_final_test_download.py)'
    assert CSV.stat().st_mtime < min(p.stat().st_mtime for p in raw_files), 'forecasts are not older than the downloaded month'
    lrep = REP / 'wiki_led_l_blind_2026-09.json'
    assert lrep.exists() and (WORLD / 'taxonomy' / 'spl_record_work.parquet').exists(), 'run l06_score.py (final) first'
    F = pd.read_csv(CSV)
    F['format'] = F.format.astype(str)
    F['not_yet'] = F.not_yet.astype(bool)
    CSV_NAME = str(CSV.relative_to(ROOT))
TMI = TY * 12 + TM - 1
YM = f'{TY}-{TM:02d}'

# ---------------------------------------------------------------- target loans (as l06_score.py)
rw = pd.read_parquet(WORLD / 'taxonomy' / 'spl_record_work.parquet').drop_duplicates('record_id').set_index('record_id').work_id
loans, totals = [], {}
for fmt, fname in FILE_OF.items():
    t = pq.read_table(WORLD / 'taxonomy' / f'spl_rows_{fname}.parquet', filters=[('year', '==', TY), ('month', '==', TM)]).to_pandas()
    totals[LABEL[fmt]] = int(t.checkouts.sum())
    t['work_id'] = rw.reindex(t.record_id.astype(np.int64).to_numpy()).to_numpy()
    loans.append(t.groupby('work_id').checkouts.sum().rename('L_next').reset_index().assign(format=LABEL[fmt]))
LOANS = pd.concat(loans, ignore_index=True)
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'total_checkouts']).drop_duplicates(['format', 'mi'])
excl = {}
for f in FMTS:
    prev = P[(P.format == f) & (P.mi >= TMI - 12) & (P.mi < TMI) & (P.total_checkouts > 0)].total_checkouts
    excl[f] = dict(total=totals[f], median_prev12=float(prev.median()), ok=bool(totals[f] >= 0.5 * prev.median()))
month_ok = all(v['ok'] for v in excl.values())
res = dict(mode='rehearsal' if REH else 'final', target=YM, forecasts=CSV_NAME, excluded_rule=excl, month_ok=month_ok)
log('target totals and rule', excl)

if not month_ok:
    res['scored'] = False
    res['note'] = 'The target month fails the excluded-month rule of the parent record, so it is never a target; nothing is scored.'
else:
    F = F.merge(LOANS, on=['work_id', 'format'], how='left')
    F['L_next'] = F.L_next.fillna(0).astype(np.float32)
    F['D'] = np.log1p(F.L_next.to_numpy(np.float32)) - np.log1p(F.M6.astype(np.float32).to_numpy())
    F['rose'] = (F.D >= LN15).astype(int)
    if REH:
        dd = (F.L_next - F.L_next_stored).abs()
        res['check_loans_equal_stored'] = dict(rows=int(len(F)), equal=int((dd == 0).sum()), max_abs_diff=float(dd.max()))
        log('check: August loans against the stored rows', res['check_loans_equal_stored'])
        assert (dd == 0).mean() > 0.999

    def cp(k, n):
        return [float(beta.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0, float(beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0]

    def rank(q, col):
        return float(np.mean([spearmanr(g[col], g.D).statistic for _, g in q.groupby('format')]))

    def top(q, col, k=20):
        t = q.sort_values(col, ascending=False, kind='stable').groupby('format', sort=False).head(k)
        h, n = int(t.rose.sum()), len(t)
        return dict(share=h / n, hits=h, slots=n, ci=cp(h, n))

    sc = dict(rows=int(len(F)), base_rose=float(F.rose.mean()), rows_by_format=F.format.value_counts().to_dict())
    for m in MOD:
        sc[m] = dict(change_rank=rank(F, m), by_format={f: float(spearmanr(F.loc[F.format == f, m], F.loc[F.format == f, 'D']).statistic) for f in FMTS},
                     top20=top(F, m), early_top20=top(F[F.not_yet], m))
    rng = np.random.default_rng(SEED)
    grp = F.groupby('work_id').indices
    wids = np.array(list(grp)); idx_of = [grp[w] for w in wids]
    fmt_arr, Dv = F.format.to_numpy(), F.D.to_numpy(float)
    cols = {m: F[m].to_numpy(float) for m in MOD[1:]}
    dr = {k: [] for k in PAIRS}
    for b in range(NB):
        ii = np.concatenate([idx_of[j] for j in rng.integers(0, len(wids), len(wids))])
        rk = {m: np.mean([spearmanr(cols[m][ii][fmt_arr[ii] == f], Dv[ii][fmt_arr[ii] == f]).statistic for f in FMTS]) for m in cols}
        for k, (a, b_) in PAIRS.items():
            dr[k].append(rk[a] - rk[b_])
        if (b + 1) % 500 == 0:
            log('bootstrap', b + 1)
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    for k, (a, b_) in PAIRS.items():
        est = sc[a]['change_rank'] - sc[b_]['change_rank']
        sc[k] = dict(est=est, ci=q(dr[k]), passed=bool(q(dr[k])[0] > 0) if k.startswith('O3') else None)
    res['scored'] = True
    res['scores'] = sc
res['runtime_s'] = round(time.time() - T0)
res['made'] = time.strftime('%Y-%m-%d %H:%M %z') + ' (' + time.strftime('%H:%M', time.gmtime()) + ' UTC)'
(REP / f'{NAME}.json').write_text(json.dumps(res, indent=1, default=str))

# ---------------------------------------------------------------- report
NAMES = {'naive_D': 'This month minus the six-month average (no model)', 'HMW14_D': 'Library + own and author pages',
         'HMW14Z_D': '... + the two Transformer forecasts', 'HMW14C_D': '... + the same 60 months in plain form',
         'HMW14CZ_D': '... + plain 60 months + the two Transformer forecasts'}
L = [f'# The Transformer check, blind month{" (REHEARSAL on a known month)" if REH else ""}: {YM}', '',
     f'Made by `code/main_study/wiki_led/o_transformer_check/o06_blind_score.py{" --rehearsal" if REH else ""}` on {res["made"]}. '
     f'Forecasts: {res["forecasts"]}. Rules: `prereg/addenda_wiki_led/2026-11-26_o_transformer_inputs_check.json`, O3.', '']
if not res['scored']:
    L += [res['note'], '']
else:
    sc = res['scores']
    L += [f'{sc["rows"]:,} book-format rows; {sc["base_rose"]:.1%} of them rose by half or more.', '',
          '| Model | Change rank | Print | Ebook | Audiobook | Top 20 that rose | Early-warning top 20 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for m in MOD:
        s = sc[m]
        L.append(f'| {NAMES[m]} | {s["change_rank"]:.3f} | ' + ' | '.join(f'{s["by_format"][f]:.3f}' for f in FMTS) +
                 f' | {s["top20"]["share"]:.2f} ({s["top20"]["ci"][0]:.2f} to {s["top20"]["ci"][1]:.2f}) | {s["early_top20"]["share"]:.2f} |')
    L += ['', '| Comparison | Difference (95% interval) | Rule |', '| --- | --- | --- |']
    for k, lab in (('O3_Z', 'Transformer forecasts added to library + own pages'), ('O3_CZ_vs_C', 'Transformer forecasts added on top of the plain 60 months'),
                   ('C_gain', 'Plain 60 months added to library + own pages')):
        s = sc[k]
        rule = ('passed' if s['passed'] else 'not passed') if s['passed'] is not None else 'no rule'
        L.append(f'| {lab} | {s["est"]:+.4f} ({s["ci"][0]:+.4f} to {s["ci"][1]:+.4f}) | {rule} |')
    L += ['', 'One month is a small test; it adds to the backtest, it does not replace it.', '']
(REP / f'{NAME}.md').write_text('\n'.join(L) + '\n')
print('written', REP / f'{NAME}.md')
