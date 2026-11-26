# q05. Addendum q, step 6: score the blind month ONCE.  Settings: prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json,
# tests.Q3_blind_month (read-only; SHA-256 checked).  Written and rehearsed on 26 Nov 2026, before any month after 2026-08 was downloaded.
# Code copied from o06_blind_score.py (target loans, excluded-month rule, measures, paired bootstrap over works).
#
# Final mode (no option): target 2026-09.  Run AFTER addendum l's l06_score.py (final mode), which builds the September world folder.
#   Forecasts: HM60_D from prereg/blind_q/, HMW14C_D and HMW14_D from prereg/blind_o/, HM_D from prereg/blind_l/ (same 20,122 rows).
#   Guards: each frozen CSV has the SHA-256 printed in prereg/README.md and is older than every downloaded 2026-09 file; l06's report exists;
#   this report does not exist yet (scored once).
# Rehearsal mode (--rehearsal): target 2026-08 from addendum l's rehearsal world, forecasts from the walk-forward predictions at origin 2026-07
#   (five-seed means; HM and HMW14 from addendum n, HMW14C from o02, HM60 from q01).  Check: the August loans equal the stored rows' L_next.
# Samples: all books, and books with a page (has_book_page or has_author_page), each scored on its own rows.
# Decision Q3: HMW14C minus HM60 change rank with a 95% interval above 0, for each sample read on its own.  One month is a small test.
# Outputs: final data/reports/wiki_on_5_years_blind_2026-09.md and .json; rehearsal ..._blind_rehearsal_2026-08.md and .json.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/q_wiki_on_5_years/q05_blind_score.py [--rehearsal]
import sys, json, time, hashlib, pathlib, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import spearmanr, beta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from config import D as DATA_DIR                               # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-26_q_wikipedia_on_top_of_5_years.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f4dffc8f803fd86e6914db73d32924052e044a1b9050b0d02b48d6dae0c77c4a', 'addendum q changed'
REH = '--rehearsal' in sys.argv
LOUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
NOUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OOUT = DATA / 'db' / 'wiki_led' / 'o_transformer_check'
OUT = DATA / 'db' / 'wiki_led' / 'q_wiki_on_5_years'
REP = DATA / 'reports'
SEED, NB = 20261126, 2000
SEEDS = [20261020 + i for i in range(5)]
LN15, LN2 = np.log(1.5), np.log(2)
FMTS = ['print', 'ebook', 'audiobook']
FILE_OF = {'BOOK': 'book', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
LABEL = {'BOOK': 'print', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
MOD = ['naive_D', 'HM_D', 'HMW14_D', 'HM60_D', 'HMW14C_D']
PAIRS = {'Q3_wiki_on_5y': ('HMW14C_D', 'HM60_D'), 'W_wiki_on_1y': ('HMW14_D', 'HM_D'), 'C_without_wiki': ('HM60_D', 'HM_D')}
SRC = {'HM': NOUT, 'HMW14': NOUT, 'HMW14C': OOUT, 'HM60': OUT}
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


if REH:
    TY, TM = 2026, 8
    WORLD = DATA / 'interim' / 'l_rehearsal' / 'world_2026-08'
    NAME = 'wiki_on_5_years_blind_rehearsal_2026-08'
    keys = pd.read_parquet(NOUT / 'preds' / 'keys.parquet', columns=['work_id', 'format', 'mi', 'L_next'])
    sel = (keys.mi == 2026 * 12 + 6).to_numpy()
    R = pd.read_parquet(LOUT / 'rows.parquet', columns=['work_id', 'format', 'mi', 'L_t', 'M6', 'h_lt', 'h_m6', 'has_book_page', 'has_author_page'])
    R = R[R.mi == 2026 * 12 + 6].assign(format=lambda x: x.format.astype(str))
    F = keys[sel][['work_id', 'format', 'L_next']].rename(columns={'L_next': 'L_next_stored'}).reset_index(drop=True)
    F['format'] = F.format.astype(str)
    for m in ('HM', 'HMW14', 'HMW14C', 'HM60'):
        F[m + '_D'] = np.mean([np.load(SRC[m] / 'preds' / str(s) / f'{m}.npy')[sel] for s in SEEDS], axis=0)
    F = F.merge(R.drop(columns='mi'), on=['work_id', 'format'], how='left', validate='one_to_one')
    assert F.M6.notna().all()
    F['not_yet'] = (F.h_lt - F.h_m6) < LN15
    F['naive_D'] = F.h_lt - F.h_m6
    CSV_NAME = 'walk-forward predictions at origin 2026-07 (rehearsal)'
else:
    TY, TM = 2026, 9
    RAW = DATA / 'raw' / 'modern' / 'final_test'
    WORLD = LOUT / 'world_2026-09'
    NAME = 'wiki_on_5_years_blind_2026-09'
    assert not (REP / f'{NAME}.json').exists(), 'the blind month has been scored already (scored once)'
    readme = (ROOT / 'prereg' / 'README.md').read_text()
    raw_files = [RAW / f'seattle_{f.lower()}_{TY}-{TM:02d}.jsonl' for f in FILE_OF]
    assert all(p.exists() for p in raw_files), 'raw files of the target month missing (28_final_test_download.py)'
    CSVS = {b: ROOT / 'prereg' / b / 'forecasts_origin_2026-08.csv' for b in ('blind_q', 'blind_o', 'blind_l')}
    for b, csv in CSVS.items():
        m = re.search(b + r'/forecasts_origin_2026-08\.csv` SHA-256: ([0-9a-f]{64})', readme)
        assert m and hashlib.sha256(csv.read_bytes()).hexdigest() == m.group(1), f'{b}: frozen forecasts changed or not fingerprinted'
        assert csv.stat().st_mtime < min(p.stat().st_mtime for p in raw_files), f'{b}: forecasts are not older than the downloaded month'
    lrep = REP / 'wiki_led_l_blind_2026-09.json'
    assert lrep.exists() and (WORLD / 'taxonomy' / 'spl_record_work.parquet').exists(), 'run l06_score.py (final) first'
    F = pd.read_csv(CSVS['blind_q'])
    for b, cols in (('blind_o', ['HMW14_D', 'HMW14C_D']), ('blind_l', ['HM_D'])):
        F = F.merge(pd.read_csv(CSVS[b], usecols=['work_id', 'format'] + cols), on=['work_id', 'format'], how='left', validate='one_to_one')
        assert F[cols].notna().all().all()
    F['format'] = F.format.astype(str)
    F['not_yet'] = F.not_yet.astype(bool)
    CSV_NAME = 'prereg/blind_q, blind_o and blind_l forecasts_origin_2026-08.csv'
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

    def score_sample(F):
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
            sc[k] = dict(est=est, ci=q(dr[k]), passed=bool(q(dr[k])[0] > 0) if k.startswith('Q3') else None)
        return sc

    page = (F.has_book_page.astype(bool) | F.has_author_page.astype(bool)).to_numpy()
    res['scored'] = True
    res['scores'] = {'all_books': score_sample(F), 'books_with_a_page': score_sample(F[page].reset_index(drop=True))}
res['runtime_s'] = round(time.time() - T0)
res['made'] = time.strftime('%Y-%m-%d %H:%M %z') + ' (' + time.strftime('%H:%M', time.gmtime()) + ' UTC)'
(REP / f'{NAME}.json').write_text(json.dumps(res, indent=1, default=str))

# ---------------------------------------------------------------- report
NAMES = {'naive_D': 'This month minus the six-month average (no model)', 'HM_D': 'Library, about 1 year of loans (no Wikipedia)',
         'HMW14_D': 'Library, about 1 year + own and author pages', 'HM60_D': 'Library + 5 years of loans (no Wikipedia)',
         'HMW14C_D': 'Library + 5 years of loans + own and author pages'}
L = [f'# Wikipedia on top of 5 years of loans, blind month{" (REHEARSAL on a known month)" if REH else ""}: {YM}', '',
     f'Made by `code/main_study/wiki_led/q_wiki_on_5_years/q05_blind_score.py{" --rehearsal" if REH else ""}` on {res["made"]}. '
     f'Forecasts: {res["forecasts"]}. Rules: `prereg/addenda_wiki_led/2026-11-26_q_wikipedia_on_top_of_5_years.json`, Q3.', '']
if not res['scored']:
    L += [res['note'], '']
else:
    for s, lab in (('all_books', 'All books'), ('books_with_a_page', 'Books with a page (own or author)')):
        sc = res['scores'][s]
        L += [f'## {lab}', '', f'{sc["rows"]:,} book-format rows; {sc["base_rose"]:.1%} of them rose by half or more.', '',
              '| Model | Change rank | Print | Ebook | Audiobook | Top 20 that rose | Early-warning top 20 |', '| --- | --- | --- | --- | --- | --- | --- |']
        for m in MOD:
            d = sc[m]
            L.append(f'| {NAMES[m]} | {d["change_rank"]:.3f} | ' + ' | '.join(f'{d["by_format"][f]:.3f}' for f in FMTS) +
                     f' | {d["top20"]["share"]:.2f} ({d["top20"]["ci"][0]:.2f} to {d["top20"]["ci"][1]:.2f}) | {d["early_top20"]["share"]:.2f} |')
        L += ['', '| Comparison | Difference (95% interval) | Rule |', '| --- | --- | --- |']
        for k, lab2 in (('Q3_wiki_on_5y', 'Wikipedia pages added, with 5 years of loans'), ('W_wiki_on_1y', 'Wikipedia pages added, with about 1 year'),
                        ('C_without_wiki', '5 years of loans added, without Wikipedia')):
            d = sc[k]
            rule = ('passed' if d['passed'] else 'not passed') if d['passed'] is not None else 'no rule'
            L.append(f'| {lab2} | {d["est"]:+.4f} ({d["ci"][0]:+.4f} to {d["ci"][1]:+.4f}) | {rule} |')
        L += ['']
    L += ['One month is a small test; it adds to the backtest, it does not replace it.', '']
(REP / f'{NAME}.md').write_text('\n'.join(L) + '\n')
print('written', REP / f'{NAME}.md')
