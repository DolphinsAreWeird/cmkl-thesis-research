# 16. Score the live October 2026 lists ONCE: the Wikipedia-only list (prereg/live_alert/README.md, frozen 20 Oct 2026 17:00 +07) and the
# library and persistence lists of addendum f (prereg/addenda_wiki_led/2026-10-20_f_live_october_comparison.json, fixed 21:00 +07).
# Written and rehearsed on 6 Nov 2026, before any month after 2026-08 was downloaded (the library's data still ended at 2026-08).
#
# Final mode (no option): L = October 2026 loans of each of the 7,650 books (all formats summed); M6 = median of the monthly loans of April to
#   September 2026, months failing the excluded-month rule left out (missing, not zero).  Guards: the six frozen files have the SHA-256 printed in
#   prereg/README.md and are older than every downloaded 2026-09 and 2026-10 file; both months are complete in
#   data/db/final_test/new_months_api_counts.parquet (28_final_test_download.py); the report does not exist yet (scored once).
#   If October fails the excluded-month rule, nothing is scored and the report says so.
# Rehearsal (--rehearsal): the same code two months earlier, to test it: July 2026 plays September and August plays October (files downloaded with
#   28_final_test_download.py --test-months into data/raw/modern/final_test_known/, treated as new), M6 = February to July.  Checks: August loans and
#   M6 equal the stored book rows at origin 2026-07 (data/db/wiki_led/test_a_rows_c.parquet: L_next, M6), and the library totals of July and August
#   equal the stored panel's.  The frozen October rankings are then scored against August only to test the code; those numbers are not results.
#
# Loans as in Test A (code/main_study/wiki_led/10c_test_a.py): stored months from data/db/study2r/counts_work.parquet; the new months' rows are matched
#   to works by the final test's own function (code/main_study/benchmark/_final_extend.py, extend()) into a world folder; a book's loans in a month are
#   the sum over its records and formats; months before its first loan are not counted, later months without a row are 0.
# Excluded months: a stored month is left out if the panel's month_ok is false for any format (Test A); a new month is left out if, for any format,
#   its library-wide total is below half of the median of that format's totals over the previous 12 months (totals above 0).
# Measures (README): rose: ln(1 + L) - ln(1 + M6) >= ln 1.5; surged: at least ln 2 and L - M6 >= 5.  Shares of the top 20 and top 50 of each list,
#   and of the library list's next picks (ranks 51 to 70), with exact (Clopper-Pearson) 95% intervals, beside the base rate over the 7,650 books.
#   P1: the Wikipedia list's top-20 share that rose has a 95% lower bound above the base rate.  P2: the same for its top-20 books outside the library
#   list's top 50 (not testable with fewer than 5).  P3: descriptive; Wikipedia is said to beat the library only if its top-20 share is higher and the
#   two exact intervals do not overlap.
# Outputs: final data/reports/wiki_led_live_october_2026.md and .json; rehearsal data/reports/wiki_led_live_october_rehearsal.md and .json.
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/16_live_october_score.py [--rehearsal]
import os
os.environ.setdefault('TAXO', 'v3')
import sys, json, time, hashlib, pathlib, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import beta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))                        # code/, for config
sys.path.insert(0, str(HERE.parent / 'benchmark'))              # the final test's helpers
from config import D as DATA_DIR                                # noqa: E402
import _final_extend as X                                       # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
LIVE = ROOT / 'prereg' / 'live_alert'
REP = DATA / 'reports'
FT = DATA / 'db' / 'final_test'
LN15, LN2 = np.log(1.5), np.log(2)
FMTS = ['print', 'ebook', 'audiobook']
LABEL = {'BOOK': 'print', 'EBOOK': 'ebook', 'AUDIOBOOK': 'audiobook'}
FROZEN = ['README.md', 'alert_list_2026-10.csv', 'ranking_all_2026-10.csv', 'library_list_2026-10.csv', 'persistence_list_2026-10.csv',
          'library_rankings_all_2026-10.csv']
BACKTEST = 'top 20: 59% rose, 40% surged; top 50: 48% and 30%; base about 11% and 3% (README, Wikipedia list, 2019 to 2026)'
REH = '--rehearsal' in sys.argv
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


if REH:
    TARGET, RAW = mi_of('2026-08'), DATA / 'raw' / 'modern' / 'final_test_known'
    WORLD = DATA / 'interim' / 'live_october_rehearsal' / 'world'
    NAME = 'wiki_led_live_october_rehearsal'
else:
    TARGET, RAW = mi_of('2026-10'), DATA / 'raw' / 'modern' / 'final_test'
    WORLD = DATA / 'db' / 'wiki_led' / 'live_october' / 'world'
    NAME = 'wiki_led_live_october_2026'
NEW = [TARGET - 1, TARGET]                                      # September and October (rehearsal: July and August)
WIN = list(range(TARGET - 6, TARGET))                           # the six months before the target: M6
raw_files = [RAW / f'seattle_{f.lower()}_{ym_of(m)}.jsonl' for m in NEW for f in X.FILE_OF]

if not REH:
    assert not (REP / f'{NAME}.json').exists(), 'the live October lists have been scored already (scored once)'
    readme = (ROOT / 'prereg' / 'README.md').read_text()
    for f in FROZEN:
        m = re.search(r'live_alert/' + re.escape(f) + r'` SHA-256: ([0-9a-f]{64})', readme)
        assert m and hashlib.sha256((LIVE / f).read_bytes()).hexdigest() == m.group(1), f'{f} changed or not fingerprinted'
    cnt = pd.read_parquet(FT / 'new_months_api_counts.parquet')
    for mi in NEW:
        c = cnt[(cnt.year == mi // 12) & (cnt.month == mi % 12 + 1)]
        assert len(c) == 3 and c.complete.all(), f'{ym_of(mi)} not completely downloaded (28_final_test_download.py)'
    assert all(p.exists() for p in raw_files), 'raw files of September or October missing'
    assert max((LIVE / f).stat().st_mtime for f in FROZEN) < min(p.stat().st_mtime for p in raw_files), 'frozen lists are not older than the new months'

# ---------------------------------------------------------------- the books and the frozen rankings
WR = pd.read_csv(LIVE / 'ranking_all_2026-10.csv')                            # rank, work_id, score (Wikipedia only)
LR = pd.read_csv(LIVE / 'library_rankings_all_2026-10.csv')                   # work_id, library_rank, persistence_rank
B = WR[['work_id', 'rank']].rename(columns={'rank': 'wiki_rank'}).merge(LR[['work_id', 'library_rank', 'persistence_rank']], on='work_id', how='outer')
assert len(B) == 7650 and B.notna().all().all(), 'the three rankings must cover the same 7,650 books'
log('books', len(B))

# ---------------------------------------------------------------- new months -> works (the final test's extend())
raw = {}
for fmt in X.FILE_OF:
    recs = []
    for mi in NEW:
        with open(RAW / f'seattle_{fmt.lower()}_{ym_of(mi)}.jsonl') as fh:
            recs += [json.loads(line) for line in fh]
    df = pd.DataFrame(recs, dtype=object) if recs else pd.DataFrame(columns=X.RAW_COLS)
    for col in X.RAW_COLS:
        if col not in df.columns:
            df[col] = ''
    raw[fmt] = df.fillna('')
    log(fmt, 'rows of the new months', len(df))
WORLD.mkdir(parents=True, exist_ok=True)
ext = X.extend(raw, WORLD, before_mi=NEW[0] if REH else None, hash_cache=FT / 'record_keys.npz', log=lambda s: log(s))
rw = pd.read_parquet(WORLD / 'taxonomy' / 'spl_record_work.parquet').drop_duplicates('record_id').set_index('record_id').work_id
new_loans, new_tot = [], {}
for fmt, fname in X.FILE_OF.items():
    for mi in NEW:
        t = pq.read_table(WORLD / 'taxonomy' / f'spl_rows_{fname}.parquet', filters=[('year', '==', mi // 12), ('month', '==', mi % 12 + 1)]).to_pandas()
        new_tot[(LABEL[fmt], mi)] = int(t.checkouts.sum())
        t['work_id'] = rw.reindex(t.record_id.astype(np.int64).to_numpy()).to_numpy()
        new_loans.append(t.groupby('work_id').checkouts.sum().rename('y').reset_index().assign(mi=mi))
NL = pd.concat(new_loans, ignore_index=True).groupby(['work_id', 'mi']).y.sum()

# ---------------------------------------------------------------- excluded-month rule
P = pd.read_parquet(DATA / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'total_checkouts', 'month_ok']).drop_duplicates(['format', 'mi'])
tot = {(r.format, int(r.mi)): float(r.total_checkouts) for r in P.itertuples() if int(r.mi) < NEW[0]}
tot.update({k: float(v) for k, v in new_tot.items()})
ok_month, rule = {}, {}
for mi in WIN + [TARGET]:
    if mi < NEW[0]:
        ok_month[mi] = bool(P[P.mi == mi].month_ok.all()) and len(P[P.mi == mi]) == 3
    else:
        r = {}
        for f in FMTS:
            prev = [tot[(f, m)] for m in range(mi - 12, mi) if tot.get((f, m), 0) > 0]
            r[f] = dict(total=tot[(f, mi)], median_prev12=float(np.median(prev)), ok=bool(tot[(f, mi)] >= 0.5 * np.median(prev)))
        rule[ym_of(mi)] = r
        ok_month[mi] = all(v['ok'] for v in r.values())
log('months ok:', {ym_of(m): v for m, v in ok_month.items()})
res = dict(mode='rehearsal' if REH else 'final', target=ym_of(TARGET), m6_window=[ym_of(WIN[0]), ym_of(WIN[-1])], extend_report=ext,
           new_month_rule=rule, months_ok={ym_of(m): v for m, v in ok_month.items()}, backtest_for_comparison=BACKTEST)
if REH:
    res['check_totals_equal_stored_panel'] = {f'{f} {ym_of(mi)}': [new_tot[(f, mi)], int(P[(P.format == f) & (P.mi == mi)].total_checkouts.iloc[0])]
                                              for f in FMTS for mi in NEW}

# ---------------------------------------------------------------- loans of the books: stored months + new months
C = pd.read_parquet(DATA / 'db' / 'study2r' / 'counts_work.parquet')
C = C[C.work_id.isin(B.work_id)]
first = C[C.y > 0].groupby('work_id').mi.min()
SL = C[C.mi < NEW[0]].groupby(['work_id', 'mi']).y.sum()
LW = pd.concat([SL, NL[NL.index.get_level_values('work_id').isin(B.work_id)]]).groupby(level=[0, 1]).sum().unstack('mi')
cols = WIN + [TARGET]
LW = LW.reindex(index=B.work_id, columns=cols).fillna(0.0)
for w in LW.index:                                               # months before the first loan: not in the collection
    m0 = first.get(w, np.inf)
    LW.loc[w, [c for c in cols if c < m0]] = np.nan
win_ok = [m for m in WIN if ok_month[m]]
B = B.set_index('work_id')
B['M6'] = LW[win_ok].median(axis=1, skipna=True)
B['L'] = LW[TARGET]
res['books_without_M6'] = int(B.M6.isna().sum())
if REH:
    S = pd.read_parquet(DATA / 'db' / 'wiki_led' / 'test_a_rows_c.parquet', columns=['work_id', 'mi', 'L_next', 'M6'])
    S = S[S.mi == TARGET - 1].set_index('work_id').rename(columns={'M6': 'M6_stored'})
    j = B[['L', 'M6']].join(S[['L_next', 'M6_stored']], how='inner')
    dl, dm = (j.L - j.L_next).abs(), (j.M6 - j.M6_stored).abs()
    res['check_against_stored_rows'] = dict(books=int(len(j)), L_equal=int((dl == 0).sum()), M6_equal=int((dm < 1e-9).sum()),
                                            L_max_abs_diff=float(dl.max()), M6_max_abs_diff=float(dm.max()), books_L_differing=int((dl > 0).sum()))
    log('check against the stored book rows:', res['check_against_stored_rows'])


def cp(k, n):
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return [float(lo), float(hi)]


if not ok_month[TARGET]:
    res['scored'] = False
    res['note'] = 'The target month fails the excluded-month rule, so it is never a target; nothing is scored.'
else:
    Q = B[B.M6.notna()].copy()
    Q['D'] = np.log1p(Q.L) - np.log1p(Q.M6)
    Q['rose'] = (Q.D >= LN15).astype(int)
    Q['surged'] = ((Q.D >= LN2) & ((Q.L - Q.M6) >= 5)).astype(int)
    base_rose, base_surge = float(Q.rose.mean()), float(Q.surged.mean())

    def share(sel):
        n, r, s = int(len(sel)), int(sel.rose.sum()), int(sel.surged.sum())
        return dict(books=n, rose=r / n if n else None, rose_ci=cp(r, n) if n else None, surged=s / n if n else None, surged_ci=cp(s, n) if n else None)

    lists = {}
    for name, col in (('wikipedia', 'wiki_rank'), ('library', 'library_rank'), ('persistence', 'persistence_rank')):
        lists[name] = dict(top20=share(Q[Q[col] <= 20]), top50=share(Q[Q[col] <= 50]))
    lists['library_next_picks_51_70'] = share(Q[(Q.library_rank > 50) & (Q.library_rank <= 70)])
    own = Q[(Q.wiki_rank <= 20) & (Q.library_rank > 50)]
    w20, l20 = lists['wikipedia']['top20'], lists['library']['top20']
    p2 = share(own)
    res.update(scored=True, books_scored=int(len(Q)), base_rose=base_rose, base_surge=base_surge, lists=lists,
               P1_signal=dict(lower_bound=w20['rose_ci'][0], base=base_rose, passed=bool(w20['rose_ci'][0] > base_rose)),
               P2_new_information=dict(books=p2['books'], share=p2['rose'], lower_bound=p2['rose_ci'][0] if p2['books'] else None,
                                       testable=p2['books'] >= 5, passed=bool(p2['books'] >= 5 and p2['rose_ci'][0] > base_rose)),
               P3_comparison=dict(wikipedia_beats_library=bool(w20['rose'] > l20['rose'] and w20['rose_ci'][0] > l20['rose_ci'][1]),
                                  note='descriptive; the claim needs a higher share and non-overlapping exact intervals'))

res['runtime_s'] = round(time.time() - T0, 1)
(REP / f'{NAME}.json').write_text(json.dumps(res, indent=1, default=str))
L_ = [f'# Live October 2026 lists: {"REHEARSAL (code test, not a result)" if REH else "scored once"}', '',
      f'Made by `code/main_study/wiki_led/16_live_october_score.py` on {time.strftime("%Y-%m-%d %H:%M %z")}. Target {res["target"]}, '
      f'M6 over {res["m6_window"][0]} to {res["m6_window"][1]}. Rules: `prereg/live_alert/README.md` and addendum f.', '']
if REH:
    L_ += ['July 2026 plays September and August plays October; the frozen October rankings are scored against August only to test the code. '
           'The library and persistence lists were made from August loans, so their August scores here are trivially high.', '',
           f'- Library totals of the "new" months against the stored panel: {res["check_totals_equal_stored_panel"]}',
           f'- Loans and M6 against the stored book rows at origin 2026-07: {res.get("check_against_stored_rows")}', '']
L_ += [f'Months ok: {res["months_ok"]}', '']
if res.get('scored'):
    L_ += [f'Books scored: {res["books_scored"]} (without an M6: {res["books_without_M6"]}). Base rate: rose {res["base_rose"]:.3f}, surged {res["base_surge"]:.3f}.', '',
           '| List | Books | Rose | 95% interval | Surged | 95% interval |', '| --- | --- | --- | --- | --- | --- |']
    for name, d in res['lists'].items():
        for k, v in ([('', d)] if 'books' in d else d.items()):
            L_.append(f"| {name} {k} | {v['books']} | {v['rose']:.3f} | {v['rose_ci'][0]:.3f} to {v['rose_ci'][1]:.3f} | {v['surged']:.3f} | {v['surged_ci'][0]:.3f} to {v['surged_ci'][1]:.3f} |")
    L_ += ['', f'- P1 (signal): {res["P1_signal"]}', f'- P2 (new information): {res["P2_new_information"]}', f'- P3 (comparison): {res["P3_comparison"]}',
           f'- Backtest for comparison: {BACKTEST}']
else:
    L_ += [res.get('note', '')]
(REP / f'{NAME}.md').write_text('\n'.join(L_) + '\n')
log('written', REP / f'{NAME}.md')
