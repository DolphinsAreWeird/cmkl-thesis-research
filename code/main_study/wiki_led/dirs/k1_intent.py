#!/usr/bin/env python3
"""K1 of addendum k (reading intent): do Open Library reading-log entries (people putting a book on their Want to Read, Currently
Reading or Already Read shelf), by month, put more books whose Seattle borrowing surges next month into the monthly top-20 alert
list, beyond library history (H), the book's own Wikipedia pages (W) and NYT lists (N)?

Record: prereg/addenda_wiki_led/2026-10-22_k_intent_dates_human.json, section K1_intent (fixed 22 Oct 2026 11:45 +07, read-only;
SHA-256 checked below).  Addendum j's settings apply where k says nothing; its model and scoring code is imported from
j2_alerts.py (same rows, targets, walk-forward refits, LightGBM settings, measures and bootstrap).  D3's NYT check imports d3_nyt.py.
Run from handoff/code (the dump is untrusted data: every Python that reads it runs with -I):
    ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage parse      (reads the dump, counts per work, month, shelf)
    ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage prep       (features I and I' on addendum j's rows)
    bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage fit
    bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage d3_fit
    ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage score      (bootstrap, decision, D3 AUC, examples, JSON)
    ../.venv/bin/python -I main_study/wiki_led/dirs/k1_intent.py --stage report     (data/reports/dir_k1_intent.md)
Outputs: data/db/wiki_led/dirs/k1_intent/ and data/reports/dir_k1_intent.md.

FIXED BY THE RECORD (not repeated in full): the dump (ol_dump_reading-log_2026-09-30.txt.gz, CC0); works mapped by the D4 mapping
with every match-quality flag except low; features I per work and month from 2017-01 (entries in month t by shelf and in total;
want-to-read in t against the median of the 6 months before, 1 added to both; entries in t-2 to t); addendum j's setup with the
ladder H+W+N and H+W+N+I; placebo H+W+N+I' with all intent dates moved 12 months earlier; addendum j's measure (precision at 20 for
next-month surges among works not yet risen, 3-month block bootstrap); primary decision: H+W+N+I minus H+W+N above 0 AND H+W+N+I
minus the placebo above 0; secondary: all works, the 3-month target, and D3's NYT next-month list appearance (AUC) with I added to H
and HW.  Known limit (record): the dump holds only entries that still exist on 2026-09-30, dated by their current shelf.

CHOICES THE RECORD LEAVES OPEN (written 22 Oct 2026 11:50 to 12:00 +07, before any intent feature or model result existed)
 Data
  K1  Dump file: data/raw/openlibrary_dump/ol_dump_reading-log_2026-09-30.txt.gz (downloaded 22 Oct 2026, gunzip -t passed,
      122,565,618 bytes).  Its SHA-256 is recorded; it equals the copy downloaded on 14 Oct (data/raw/openlibrary/), checked
      before parsing.  The file is read as data only: each line must match a strict pattern (work key /works/OL<digits>W, edition
      /books/OL<digits>M or \\N, one of four shelf names, date YYYY-MM-DD); any other line is counted as malformed and skipped.
      Nothing from the file is executed, used as a path or printed beyond counts.  No user field exists in the dump; none is kept.
  K2  Shelves: the record names Want to Read, Currently Reading and Already Read.  The dump also holds a fourth, newer shelf,
      Stopped Reading (1,919 rows in the 14 Oct profile, almost all in 2026).  It is counted in the description and left out of
      the features: "in total" = the three named shelves.
  K3  The month of an entry is the calendar month of its date.  Entries dated before 2017-01 or after 2026-09 (if any) are counted
      in the description and not used.
  K4  Mapping: rows of data/collectors/openlibrary/mapping.parquet with in_test_a and quality high or medium (every flag except low;
      'none' has no work): 7,728 of the 7,747 works.  The mapping gives one Open Library work per Test A work (none has several),
      so each Test A work reads one work's entries.  Where several Test A works share one Open Library work (205 Open Library works
      shared by 452 Test A works: other editions or formats of one book in Seattle), each of them gets that work's full counts.
      The 19 works without a usable work (18 none, 1 low) get missing I (unknown), not 0; a mapped work with no entry in a month
      gets 0 for that month.  Dump keys are matched as they are: entries the dump files under an older, merged key of the same
      book are not found (the dump has no redirect table).  A descriptive check compares each mapped work's total entries in the
      dump with the live shelf counts the weekly collector fetched on 22 Oct 2026 (snapshot reading_log_2026-10-22).
 Features I (known at the end of month t; months are data months of the entries)
  K5  i_wtr, i_cur, i_read: entries dated in month t on Want to Read, Currently Reading, Already Read; i_all = their sum;
      i_wtr_rel = (i_wtr in t + 1) / (median of i_wtr over t-6 .. t-1 + 1); i_all_3m = i_all summed over t-2 .. t ("entries in
      months t-2 to t" read as all three shelves together, like "in total").  Six columns, raw counts (not divided by Open
      Library's activity that month, as the record fixes them; the growth of that activity is described in the report).
  K6  Data months run from 2017-01 (the record's start) to 2026-09 (the dump's last month).  A feature is missing when any month it
      needs lies outside: monthly counts from origin 2017-01, i_all_3m from 2017-03, i_wtr_rel from 2017-07.  Test A's rows start
      at origin 2016-03, so the earliest training rows have missing I (LightGBM's own handling, as addendum j's J4).
  K7  Placebo I' ("all intent dates moved 12 months earlier", addendum j's J8 rule): an entry dated e is treated as dated e - 12, so
      the placebo feature at origin t equals the real feature computed at t + 12; its data months run from 2016-01 to 2025-09, and a
      placebo feature that needs a month after that is missing (origins after 2025-09 for the monthly counts).  As in J8 the
      comparison with the real model is reported on all scored months and, as a check, on origins up to 2025-09.  H, W and N stay
      real in the placebo model, and I' is fed under I's column names in I's order, so only the timing differs.
 Models (addendum j's J1, J2, J3, J9 unchanged; rows, targets and the not-yet-risen flag read from j2's feats_core.parquet)
  K8  HWN = j2's H, W and N columns in j2's order (j2's H+W+E+N without E); HWNI = HWN + the six I columns; placebo_I = HWN + I'.
      Each fitted with j2's LightGBM settings (4 threads), walk-forward by test year 2019 to 2026, on the next-month (S1) and the
      three-month (S3) targets, with j2's training rules.  Check of the copied fit code: j2's H+W is refitted here for S1 and must
      give j2's stored scores (preds_S1_HW.parquet) to 1e-6; the script stops otherwise.
 Measures and decision (addendum j's J11 to J13, j2's functions)
  K9  Per origin month: precision at 20, average precision, coverage in the top 100, among all works and among works not yet risen;
      means over months with j2's circular month-block bootstrap (blocks of 3, 2,000 draws), the draws regenerated exactly as j2
      did (numpy default_rng(20261020): the first draws for the 78 next-month months, the next for the 76 three-month months), so the
      intervals use the same month blocks as addendum j; paired differences use the same draws.  Placebo check on origins up to
      2025-09 with j2's draws for that check (default_rng(20261021)).
  K10 Primary (both needed): precision at 20 among not-yet-risen works, next month: HWNI minus HWN, 95% interval above 0, and HWNI
      minus placebo_I, 95% interval above 0 (all 78 months).  Point differences are reported too.  Everything else is secondary.
  K11 Secondary: the same on all works, average precision and coverage, the three-month target, and HWN beside j2's H, H+W and
      H+W+E+N (j2's stored predictions, not refitted) for context.
  K12 D3 (NYT next-month list appearance): D3's stage (a) rows (a_rows.parquet: Test A rows of works with no NYT week in month t;
      target E = an NYT week in t+1), D3's LightGBM settings and walk-forward; H+I and HW+I fitted on the matched works (D3's
      primary population) and on all works; scored with D3's measures (AUC within each month with an appearance, averaged over months,
      D3's month-block bootstrap with seed 20261020; top-20 share), paired against D3's stored H and HW refits (Hfit_E, HWfit_E).
      Check: H refitted here on the matched works must give D3's stored Hfit_E to 1e-6.  Added, not in the record: the same with
      the placebo I' (H+I', HW+I'), so the I gain on the NYT target can be read against moved dates.
 Description and examples
  K13 Description: entries per year and shelf in the whole dump and among the mapped Test A works; distinct works with entries per
      year; Test A works with any entry (2017-01 to 2026-09) and per year; how often the I inputs are on in the scored rows and the
      next-month surge rate where i_wtr_rel >= 2 and where i_all > 0 (a positive control, descriptive); gain-importance share of I
      in HWNI.  Open Library's activity grew several-fold over these years; this is reported, not corrected.
  K14 Examples (one or two): rows in HWNI's not-yet-risen top 20 that are not in HWN's not-yet-risen top 20 of the same month and that
      surged next month; first the one with the highest HWNI score among those with i_wtr_rel >= 2, then the highest remaining with
      i_all > 0, two different works.  The reason given is the I values at t (and the want-to-read counts of the months before).  An
      example shows what the list contains; it does not prove why the model ranked the book high.
"""
import sys, re, json, time, gzip, pathlib, hashlib, argparse, warnings, resource, importlib.util
from collections import Counter
import numpy as np, pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)
CODE = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(CODE))
from config import D  # noqa: E402

D = pathlib.Path(D)
ROOT = D.parent
HERE = pathlib.Path(__file__).resolve().parent
IN = D / 'db' / 'wiki_led'
JOUT = IN / 'dirs' / 'j_alerts'
D3OUT = IN / 'dirs' / 'd3_nyt'
OUT = IN / 'dirs' / 'k1_intent'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
ADD_K = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_k_intent_dates_human.json'
assert hashlib.sha256(ADD_K.read_bytes()).hexdigest() == '8290202d260dfd845f502c93f779e8a56d54851996cc930da9bbc09e4e99bb90', 'addendum k changed'
DUMP = D / 'raw' / 'openlibrary_dump' / 'ol_dump_reading-log_2026-09-30.txt.gz'
DUMP_OLD = D / 'raw' / 'openlibrary' / 'ol_dump_reading-log_2026-09-30.txt.gz'
MAPF = D / 'collectors' / 'openlibrary' / 'mapping.parquet'
SNAPDIR = D / 'collectors' / 'openlibrary' / 'snapshots'
T0 = time.time()


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


J2 = _load('j2_alerts', 'j2_alerts.py')                  # addendum j's code: settings, per_month, block_draws, block_ci
SEED, SHIFT = J2.SEED, 12
mi_of, ym = J2.mi_of, J2.ym
HCOLS, WCOLS, NCOLS = J2.HCOLS, J2.WCOLS, J2.NCOLS
HWN = HCOLS + WCOLS + NCOLS
ICOLS = ['i_wtr', 'i_cur', 'i_read', 'i_all', 'i_wtr_rel', 'i_all_3m']
PCOLS = ['p_' + c for c in ICOLS]
AV0, AV1 = mi_of('2017-01'), mi_of('2026-09')            # data months of the reading log used (K6)
SHELVES = {b'Want to Read': 'wtr', b'Currently Reading': 'cur', b'Already Read': 'read', b'Stopped Reading': 'stop'}
RX = re.compile(rb'/works/OL([1-9][0-9]{0,9})W\t(?:/books/OL[1-9][0-9]{0,9}M|\\N)\t(Want to Read|Currently Reading|Already Read|Stopped Reading)'
                rb'\t((?:19|20)[0-9]{2})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])')


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def mapping():
    M = pd.read_parquet(MAPF)
    A = M[M.in_test_a].copy()
    assert len(A) == 7747 and A.work_id.is_unique
    use = A.quality.isin(['high', 'medium']) & A.ol_work.notna()
    A['ol_num'] = np.where(use, A.ol_work.str.extract(r'^OL([1-9][0-9]*)W$', expand=False).astype(float), np.nan)
    assert A.loc[use, 'ol_num'].notna().all()
    return A[['work_id', 'ol_work', 'ol_num', 'quality', 'title', 'author']]


# ====================================================================== stage parse (untrusted dump -> counts)
def stage_parse():
    size = DUMP.stat().st_size
    h_new = sha256(DUMP)
    h_old = sha256(DUMP_OLD) if DUMP_OLD.exists() else None
    log('dump', size, 'bytes; same as the 14 Oct copy:', h_new == h_old)
    A = mapping()
    want = set(int(x) for x in A.ol_num.dropna())
    tot = Counter()                                   # (mi, shelf) -> entries, whole dump
    mine = Counter()                                  # (ol_num, mi, shelf) -> entries, mapped Test A works
    years = np.zeros(80_000_000, np.uint16)           # per Open Library work number: bit (year - 2012) set when it has an entry that year
    n = bad = before = after = beyond = 0
    bad_examples = []
    with gzip.open(DUMP, 'rb') as fh:
        for line in fh:
            n += 1
            m = RX.fullmatch(line.rstrip(b'\n'))
            if m is None:
                bad += 1
                if len(bad_examples) < 3:
                    bad_examples.append(repr(line[:80]))
                continue
            ol = int(m.group(1))
            sh = SHELVES[m.group(2)]
            y, mo = int(m.group(3)), int(m.group(4))
            mi = y * 12 + mo - 1
            tot[(mi, sh)] += 1
            if mi < AV0:
                before += 1
            elif mi > AV1:
                after += 1
            if ol >= len(years):
                beyond += 1
            elif 2012 <= y <= 2027:
                years[ol] |= np.uint16(1 << (y - 2012))
            if ol in want:
                mine[(ol, mi, sh)] += 1
            if n % 2_000_000 == 0:
                log('lines', n)
    T = pd.DataFrame([(k[0], k[1], v) for k, v in tot.items()], columns=['mi', 'shelf', 'n']).sort_values(['mi', 'shelf'])
    T.to_parquet(OUT / 'dump_month_totals.parquet', index=False)
    E = pd.DataFrame([(k[0], k[1], k[2], v) for k, v in mine.items()], columns=['ol_num', 'mi', 'shelf', 'n']).sort_values(['ol_num', 'mi', 'shelf'])
    E.to_parquet(OUT / 'ol_entries_mapped.parquet', index=False)
    works_by_year = {y: int(((years >> np.uint16(y - 2012)) & 1).sum()) for y in range(2012, 2028)}
    info = dict(file=str(DUMP.relative_to(ROOT)), bytes=size, sha256=h_new, same_as_14oct_copy=(h_new == h_old), lines=n, malformed=bad,
                entries_with_work_number_beyond_year_table=beyond,
                malformed_examples=bad_examples, entries_before_2017_01=before, entries_after_2026_09=after,
                rows_by_shelf={s: int(T[T.shelf == s].n.sum()) for s in ['wtr', 'cur', 'read', 'stop']},
                distinct_works_any=int((years > 0).sum()), distinct_works_by_year={k: v for k, v in works_by_year.items() if v},
                mapped_ol_works=len(want), mapped_ol_works_with_entries=int(E.ol_num.nunique()), mapped_entries=int(E.n.sum()),
                first_month=ym(T.mi.min()), last_month=ym(T.mi.max()), parsed=time.strftime('%Y-%m-%d %H:%M %z'))
    (OUT / 'parse_info.json').write_text(json.dumps(info, indent=1))
    log('parse done', {k: v for k, v in info.items() if k not in ('malformed_examples',)})


# ====================================================================== stage prep: I and I' on addendum j's rows
def i_features(mi, oi, CNT, shift):
    """the six I columns at origins mi for Open Library row indices oi (-1 = unmapped), reading data months mi + shift - k (K5 to K7)"""
    t = mi + shift

    def get(s, k):
        m = t - k
        ok = (m >= AV0) & (m <= AV1) & (oi >= 0)
        v = np.full(len(t), np.nan, np.float64)
        v[ok] = CNT[s][oi[ok], m[ok] - AV0]
        return v
    w0, c0, r0 = get('wtr', 0), get('cur', 0), get('read', 0)
    a = lambda k: get('wtr', k) + get('cur', k) + get('read', k)
    med6 = np.median(np.vstack([get('wtr', k) for k in range(1, 7)]), axis=0)          # NaN when any of the 6 months is missing
    out = {'i_wtr': w0, 'i_cur': c0, 'i_read': r0, 'i_all': w0 + c0 + r0, 'i_wtr_rel': (w0 + 1) / (med6 + 1), 'i_all_3m': a(0) + a(1) + a(2)}
    return {k: v.astype(np.float32) for k, v in out.items()}


def stage_prep():
    F = pd.read_parquet(JOUT / 'feats_core.parquet', columns=['work_id', 'mi'])
    A = mapping()
    E = pd.read_parquet(OUT / 'ol_entries_mapped.parquet')
    E = E[(E.mi >= AV0) & (E.mi <= AV1) & E.shelf.isin(['wtr', 'cur', 'read'])]
    ols = np.sort(A.ol_num.dropna().astype(np.int64).unique())
    pos = pd.Series(np.arange(len(ols)), index=ols)
    CNT = {}
    for s in ('wtr', 'cur', 'read'):
        x = E[E.shelf == s]
        M = np.zeros((len(ols), AV1 - AV0 + 1), np.float64)
        np.add.at(M, (pos.loc[x.ol_num.to_numpy()].to_numpy(), x.mi.to_numpy() - AV0), x.n.to_numpy())
        CNT[s] = M
    wol = F.work_id.map(A.set_index('work_id').ol_num)
    oi = np.where(wol.notna(), pos.reindex(wol.fillna(-1).astype(np.int64)).fillna(-1).to_numpy(), -1).astype(np.int64)
    mi = F.mi.to_numpy()
    out = F.copy()
    for k, v in i_features(mi, oi, CNT, 0).items():
        out[k] = v
    for k, v in i_features(mi, oi, CNT, SHIFT).items():
        out['p_' + k] = v
    out.to_parquet(OUT / 'feats_i.parquet', index=False)
    # works with entries (K13)
    tot_w = sum(CNT[s] for s in CNT)                        # Open Library works x months, three shelves
    wk = A.dropna(subset=['ol_num']).copy()
    wk['oi'] = pos.loc[wk.ol_num.astype(np.int64)].to_numpy()
    wk['entries'] = tot_w.sum(1)[wk.oi]
    yrs = {}
    for y in range(2017, 2027):
        cols = slice(mi_of(f'{y}-01') - AV0, min(mi_of(f'{y}-12'), AV1) - AV0 + 1)
        e_y = tot_w[:, cols].sum(1)[wk.oi]
        yrs[y] = dict(test_a_works_with_entries=int((e_y > 0).sum()), entries=int(e_y.sum()),
                      entries_wtr=int(CNT['wtr'][:, cols].sum(1)[wk.oi].sum()), median_entries_among_works_with_any=float(np.median(e_y[e_y > 0])) if (e_y > 0).any() else 0.0)
    info = dict(rows=int(len(out)), test_a_works=7747, mapped_works=int(len(wk)), unmapped_works=int(7747 - len(wk)),
                mapped_ol_works=int(len(ols)), test_a_works_with_any_entry=int((wk.entries > 0).sum()),
                share_mapped_with_any_entry=float((wk.entries > 0).mean()),
                entries_per_work_quantiles={q: float(np.quantile(wk.entries, q)) for q in (0.25, 0.5, 0.75, 0.9, 0.99)},
                by_year=yrs, rows_missing_i_all=int(out.i_all.isna().sum()), rows_missing_p_i_all=int(out.p_i_all.isna().sum()),
                rows_i_all_pos=int((out.i_all > 0).sum()))
    (OUT / 'prep_info.json').write_text(json.dumps(info, indent=1))
    wk[['work_id', 'ol_work', 'quality', 'entries']].to_parquet(OUT / 'work_entries.parquet', index=False)
    log('prep done', {k: v for k, v in info.items() if k != 'by_year'})


# ====================================================================== stage fit (j2's walk-forward, copied with this folder as output)
def load_feats():
    F = pd.read_parquet(JOUT / 'feats_core.parquet')
    n = len(F)
    F = F.merge(pd.read_parquet(OUT / 'feats_i.parquet'), on=['work_id', 'mi'], how='left')      # left merge keeps j2's row order
    assert len(F) == n
    return F


def specs():
    return {'HW_check': HCOLS + WCOLS, 'HWN': HWN, 'HWNI': HWN + ICOLS, 'placebo_I': HWN + PCOLS}


def stage_fit(models, targets):
    import lightgbm as lgb
    F = load_feats()
    sp = specs()
    log('features', F.shape)
    for tgt in targets:
        for name in models:
            if name == 'HW_check' and tgt != 'S1':
                continue
            f_out = OUT / f'preds_{tgt}_{name}.parquet'
            if f_out.exists():
                log('exists, skipped', f_out.name)
                continue
            cols = sp[name]
            fit_cols = sp['HWNI'] if name == 'placebo_I' else cols          # the placebo is the real model fed the moved columns
            parts, imps = [], {}
            for Y in J2.TEST_YEARS:
                if tgt == 'S1':
                    te = F[(F.year == Y) & (F.mi >= J2.SCORE0)]
                    tr = F[(F.mi + 1) < Y * 12]
                else:
                    te = F[(F.year == Y) & (F.mi >= J2.SCORE0) & F.obs3]
                    tr = F[((F.mi + 3) < Y * 12) & F.obs3]
                if te.empty:
                    continue
                m = lgb.LGBMRegressor(**J2.LGB).fit(tr[cols].set_axis(fit_cols, axis=1), tr[tgt].astype(float))
                p = te[['work_id', 'mi']].copy()
                p['score'] = m.predict(te[cols].set_axis(fit_cols, axis=1))
                parts.append(p)
                imps[Y] = dict(zip(fit_cols, m.booster_.feature_importance('gain').tolist()))
                log(tgt, name, Y, 'train', len(tr), 'test', len(te), 'train surges', int(tr[tgt].sum()))
            P = pd.concat(parts, ignore_index=True)
            P.to_parquet(f_out, index=False)
            (OUT / f'importance_{tgt}_{name}.json').write_text(json.dumps(imps))
            log('saved', f_out.name, len(P))
            if name == 'HW_check':
                ref = pd.read_parquet(JOUT / 'preds_S1_HW.parquet')
                x = ref.merge(P, on=['work_id', 'mi'], suffixes=('_j2', '_k1'))
                dmax = float(np.abs(x.score_j2 - x.score_k1).max())
                (OUT / 'check_reproduce_j2.json').write_text(json.dumps(dict(model='HW', target='S1', rows=int(len(x)), rows_j2=int(len(ref)), max_abs_diff=dmax)))
                log('reproduction of j2 H+W: rows', len(x), 'of', len(ref), 'max abs diff', dmax)
                assert len(x) == len(ref) and dmax < 1e-6, 'copied fit code does not reproduce j2'


# ====================================================================== stage d3_fit (D3's NYT target with I added)
D3_MODELS = {'Hcheck': (HCOLS, None), 'HI': (HCOLS + ICOLS, None), 'HWI': (HCOLS + WCOLS + ICOLS, None),
             'HIp': (HCOLS + PCOLS, HCOLS + ICOLS), 'HWIp': (HCOLS + WCOLS + PCOLS, HCOLS + WCOLS + ICOLS)}


def d3_rows():
    R = pd.read_parquet(D3OUT / 'a_rows.parquet', columns=['work_id', 'mi', 'year', 'E', 'matched', 'nyt_ever_before'])
    n = len(R)
    X = pd.read_parquet(IN / 'test_a_rows_c.parquet', columns=['work_id', 'mi'] + HCOLS + WCOLS)
    R = R.merge(X, on=['work_id', 'mi'], how='left').merge(pd.read_parquet(OUT / 'feats_i.parquet'), on=['work_id', 'mi'], how='left')
    assert len(R) == n and R.h_lt.notna().any()
    return R


def stage_d3_fit():
    import lightgbm as lgb
    D3 = _load('d3_nyt', 'd3_nyt.py')
    f_out = OUT / 'd3_preds.parquet'
    if f_out.exists():
        log('exists, skipped', f_out.name)
        return
    R = d3_rows()
    preds = []
    for pop in ('matched', 'all'):
        Rp = R[R.matched] if pop == 'matched' else R
        for Y in range(2019, 2027):
            te = Rp[(Rp.year == Y) & (Rp.mi >= D3.SCORE0)]
            if te.empty:
                continue
            tr = Rp[(Rp.mi + 1) < Y * 12]
            p = te[['work_id', 'mi']].copy()
            p['pop'] = pop
            for name, (cols, fit_cols) in D3_MODELS.items():
                if name == 'Hcheck' and pop != 'matched':
                    continue
                fc = fit_cols or cols
                m = lgb.LGBMRegressor(**D3.LGB).fit(tr[cols].set_axis(fc, axis=1), tr['E'])
                p[name] = m.predict(te[cols].set_axis(fc, axis=1))
            preds.append(p)
            log('d3 refit', pop, Y, 'train', len(tr), 'positives', int(tr.E.sum()), 'test', len(te), 'positives', int(te.E.sum()))
    P = pd.concat(preds, ignore_index=True)
    ref = pd.read_parquet(D3OUT / 'a_refit_preds.parquet')
    x = P[P['pop'] == 'matched'].merge(ref[ref['pop'] == 'matched'][['work_id', 'mi', 'Hfit_E']], on=['work_id', 'mi'])
    dmax = float(np.abs(x.Hcheck - x.Hfit_E).max())
    (OUT / 'check_reproduce_d3.json').write_text(json.dumps(dict(model='Hfit_E', population='matched', rows=int(len(x)), max_abs_diff=dmax)))
    log('reproduction of D3 H (matched): rows', len(x), 'max abs diff', dmax)
    assert dmax < 1e-6, 'copied D3 fit does not reproduce D3'
    P.to_parquet(f_out, index=False)


# ====================================================================== stage score
def stage_score():
    F = pd.read_parquet(JOUT / 'feats_core.parquet', columns=['work_id', 'mi', 'year', 'S1', 'S3', 'obs3', 'not_yet', 'L_t', 'M6', 'L_next', 'L3max'])
    F = F[F.mi >= J2.SCORE0]
    rng = np.random.default_rng(SEED)
    res = dict(record=str(ADD_K.relative_to(ROOT)), run=time.strftime('%Y-%m-%d %H:%M %z'), parse=json.loads((OUT / 'parse_info.json').read_text()),
               prep=json.loads((OUT / 'prep_info.json').read_text()), check_j2=json.loads((OUT / 'check_reproduce_j2.json').read_text()))
    PM, MONTHS, BDs = {}, {}, {}
    ours = ['HWN', 'HWNI', 'placebo_I']
    j2ref = ['H', 'HW', 'HWEN']
    for tgt in ('S1', 'S3'):
        G0 = F if tgt == 'S1' else F[F.obs3]
        months = np.sort(G0.mi.unique())
        MONTHS[tgt] = months
        BDs[tgt] = J2.block_draws(len(months), rng)          # same draws as j2 (first S1, then S3)
        G = G0
        for name in ours + j2ref:
            src = OUT if name in ours else JOUT
            P = pd.read_parquet(src / f'preds_{tgt}_{name}.parquet').rename(columns={'score': 's_' + name})
            G = G.merge(P, on=['work_id', 'mi'], how='left')
            assert G['s_' + name].notna().all(), (tgt, name)
        for pop in ('all', 'not_yet'):
            Gp = G if pop == 'all' else G[G.not_yet]
            for name in ours + j2ref:
                PM[(tgt, pop, name)] = J2.per_month(Gp, 's_' + name, tgt, months)
            log('scored', tgt, pop)
        if tgt == 'S1':
            GS1 = G
    MEAS = ['p20', 'ap', 'cov100']
    T = pd.DataFrame([dict(target=t, population=p, model=n, measure=ms, **J2.block_ci(a[:, j], BDs[t])) for (t, p, n), a in PM.items() for j, ms in enumerate(MEAS)])
    T.to_csv(OUT / 'measures.csv', index=False)
    pairs = [('HWNI', 'HWN'), ('HWNI', 'placebo_I'), ('placebo_I', 'HWN'), ('HWN', 'H'), ('HWNI', 'H'), ('HWN', 'HW'), ('HWN', 'HWEN'), ('HWNI', 'HWEN')]
    diffs = []
    end = AV1 - SHIFT                                          # origins with complete placebo data (2025-09)
    for tgt in ('S1', 'S3'):
        for pop in ('all', 'not_yet'):
            for a, b in pairs:
                for j, ms in enumerate(MEAS):
                    diffs.append(dict(target=tgt, population=pop, a=a, b=b, measure=ms, **J2.block_ci(PM[(tgt, pop, a)][:, j] - PM[(tgt, pop, b)][:, j], BDs[tgt])))
            keep = MONTHS[tgt] <= end
            BDk = J2.block_draws(int(keep.sum()), np.random.default_rng(SEED + 1))
            for a, b in (('HWNI', 'placebo_I'), ('placebo_I', 'HWN'), ('HWNI', 'HWN')):
                for j, ms in enumerate(MEAS):
                    d = (PM[(tgt, pop, a)][:, j] - PM[(tgt, pop, b)][:, j])[keep]
                    diffs.append(dict(target=tgt, population=pop, a=a, b=b, measure=ms + f'_origins_to_{ym(end)}', **J2.block_ci(d, BDk)))
    DF = pd.DataFrame(diffs)
    DF.to_csv(OUT / 'paired_differences.csv', index=False)
    res['n_months'] = {k: int(len(v)) for k, v in MONTHS.items()}
    res['months'] = {k: [ym(v[0]), ym(v[-1])] for k, v in MONTHS.items()}
    res['base'] = {}
    for tgt in ('S1', 'S3'):
        G0 = F if tgt == 'S1' else F[F.obs3]
        for pop in ('all', 'not_yet'):
            Gp = G0 if pop == 'all' else G0[G0.not_yet]
            res['base'][f'{tgt}_{pop}'] = dict(rate_mean_over_months=float(Gp.groupby('mi')[tgt].mean().mean()), surges=int(Gp[tgt].sum()), rows=int(len(Gp)),
                                               rows_per_month=float(Gp.groupby('mi').size().mean()))

    def getd(tgt, pop, a, b, ms='p20'):
        r = DF[(DF.target == tgt) & (DF.population == pop) & (DF.a == a) & (DF.b == b) & (DF.measure == ms)]
        return {k: r.iloc[0][k] for k in ('mean', 'lo', 'hi', 'months')}
    g1, g2 = getd('S1', 'not_yet', 'HWNI', 'HWN'), getd('S1', 'not_yet', 'HWNI', 'placebo_I')
    res['decision'] = dict(gain_over_HWN=dict(g1, passed=bool(g1['lo'] > 0)), gain_over_placebo=dict(g2, passed=bool(g2['lo'] > 0)),
                           passed=bool(g1['lo'] > 0 and g2['lo'] > 0),
                           measure='precision at 20, next-month surge, works not yet risen; both intervals above 0 needed')
    log('decision', res['decision'])
    # ------------------------------------------------ description of I in the scored rows (K13)
    FI = pd.read_parquet(OUT / 'feats_i.parquet')
    X = F.merge(FI, on=['work_id', 'mi'], how='left')
    chk = []
    conds = {'i_all > 0': X.i_all > 0, 'i_wtr > 0': X.i_wtr > 0, 'i_wtr_rel >= 2': X.i_wtr_rel >= 2, 'i_wtr_rel >= 3': X.i_wtr_rel >= 3,
             'i_all_3m >= 10': X.i_all_3m >= 10, 'p_i_wtr_rel >= 2 (placebo)': X.p_i_wtr_rel >= 2, 'p_i_all > 0 (placebo)': X.p_i_all > 0}
    for lab, on in conds.items():
        one = on & X.not_yet
        chk.append(dict(condition=lab, rows_on=int(on.sum()), works_on=int(X.loc[on, 'work_id'].nunique()), surge_rate_on=float(X.loc[on, 'S1'].mean()),
                        base=float(X.S1.mean()), rows_on_not_yet=int(one.sum()), surge_rate_on_not_yet=float(X.loc[one, 'S1'].mean()),
                        base_not_yet=float(X.loc[X.not_yet, 'S1'].mean())))
    pd.DataFrame(chk).to_csv(OUT / 'feature_on_surge_rates.csv', index=False)
    res['i_rows'] = dict(scored_rows=int(len(X)), rows_i_missing=int(X.i_all.isna().sum()), rows_i_all_pos=int((X.i_all > 0).sum()),
                         share_rows_i_all_pos=float((X.i_all > 0).mean()), rows_p_missing=int(X.p_i_all.isna().sum()))
    imp = json.loads((OUT / 'importance_S1_HWNI.json').read_text())
    sh = {}
    for Y, d in imp.items():
        tot = sum(d.values())
        for c, v in d.items():
            g = 'H' if c in HCOLS else 'W' if c in WCOLS else 'N' if c in NCOLS else 'I'
            sh.setdefault(g, 0.0)
            sh[g] += v / tot / len(imp)
    res['importance_share_HWNI_S1'] = sh
    res['importance_I_cols_HWNI_S1'] = {c: float(np.mean([d[c] / sum(d.values()) for d in imp.values()])) for c in ICOLS}
    # snapshot check (K4): dump totals against the live counts of 22 Oct
    res['snapshot_check'] = snapshot_check()
    res['d3'] = d3_score()
    res['examples'] = examples(GS1, FI)
    (OUT / 'k1_results.json').write_text(json.dumps(res, indent=1, default=float))
    log('score done')


def snapshot_check():
    fs = sorted(SNAPDIR.glob('reading_log_2026-10-22*.csv.gz')) or sorted(SNAPDIR.glob('_partial_2026-10-22.csv'))
    if not fs:
        return None
    S = pd.read_csv(fs[0], dtype={'ol_work': str, 'ol_work_fetched': str, 'status': str}, keep_default_na=False)
    S = S[S.status == 'ok']
    E = pd.read_parquet(OUT / 'ol_entries_mapped.parquet')
    tw = E[E.shelf == 'wtr'].groupby('ol_num').n.sum()
    S['ol_num'] = S.ol_work.str.extract(r'^OL([1-9][0-9]*)W$', expand=False).astype(float)
    S['dump_wtr'] = S.ol_num.map(tw).fillna(0)
    S = S[S.ol_num.isin(set(mapping().ol_num.dropna()))]                 # the snapshot also holds Test F books; keep the mapped Test A works
    S['want_to_read'] = pd.to_numeric(S.want_to_read, errors='coerce')
    S = S.dropna(subset=['want_to_read'])
    from scipy.stats import spearmanr
    r = spearmanr(S.dump_wtr, S.want_to_read)
    pos = S[S.want_to_read > 0]
    return dict(file=fs[0].name, works=int(len(S)), spearman_want_to_read=float(r.correlation),
                median_ratio_dump_to_live=float(np.median(pos.dump_wtr / pos.want_to_read)) if len(pos) else None,
                share_dump_le_live=float((S.dump_wtr <= S.want_to_read).mean()))


def d3_score():
    """D3's measures (score_a) for the I models, against D3's stored H and HW refits (K12)."""
    D3 = _load('d3_nyt', 'd3_nyt.py')
    R = pd.read_parquet(D3OUT / 'a_rows.parquet', columns=['work_id', 'mi', 'E', 'matched'])
    REF = pd.read_parquet(D3OUT / 'a_refit_preds.parquet', columns=['work_id', 'mi', 'pop', 'Hfit_E', 'HWfit_E'])
    P = pd.read_parquet(OUT / 'd3_preds.parquet')
    out = dict(check=json.loads((OUT / 'check_reproduce_d3.json').read_text()))
    models = ['Hfit_E', 'HWfit_E', 'HI', 'HWI', 'HIp', 'HWIp']
    for pop in ('matched', 'all'):
        X = R[R.mi >= D3.SCORE0] if pop == 'all' else R[(R.mi >= D3.SCORE0) & R.matched]
        X = X.merge(REF[REF['pop'] == pop].drop(columns='pop'), on=['work_id', 'mi'], how='left').merge(
            P[P['pop'] == pop].drop(columns=['pop'] + (['Hcheck'] if 'Hcheck' in P.columns else [])), on=['work_id', 'mi'], how='left')
        rng = np.random.default_rng(D3.SEED_A)
        months = np.sort(X.mi.unique())
        groups = {m: g for m, g in X.groupby('mi')}
        mpos = np.array([groups[m].E.sum() > 0 for m in months])
        BD_all = D3.block_draws(len(months), rng)
        per, o = {}, dict(n_rows=int(len(X)), n_months=int(len(months)), months_with_appearance=int(mpos.sum()), n_appear=int(X.E.sum()), models={}, paired={})
        for c in models:
            assert X[c].notna().all(), (pop, c)
            auc_m, top_m = [], []
            for m in months:
                g = groups[m]
                s_ = g[c].fillna(g[c].min() - 1).values
                auc_m.append(D3.auc_pairs(g.E.values, s_)[0])
                oo = np.lexsort((g.work_id.values, -s_))[:20]
                top_m.append(g.E.values[oo].mean())
            auc_m, top_m = np.array(auc_m), np.array(top_m)
            per[c] = (auc_m, top_m)
            am = auc_m[mpos]
            ba = am[D3.block_draws(len(am), np.random.default_rng(D3.SEED_A))].mean(1)
            bt = top_m[BD_all].mean(1)
            o['models'][c] = dict(auc=float(am.mean()), auc_lo=float(np.percentile(ba, 2.5)), auc_hi=float(np.percentile(ba, 97.5)),
                                  top20=float(top_m.mean()), top20_lo=float(np.percentile(bt, 2.5)), top20_hi=float(np.percentile(bt, 97.5)))
        for a_, b_ in (('HI', 'Hfit_E'), ('HWI', 'HWfit_E'), ('HI', 'HIp'), ('HWI', 'HWIp'), ('HIp', 'Hfit_E'), ('HWIp', 'HWfit_E')):
            da = (per[a_][0] - per[b_][0])[mpos]
            dt = per[a_][1] - per[b_][1]
            ba = da[D3.block_draws(len(da), np.random.default_rng(D3.SEED_A))].mean(1)
            bt = dt[BD_all].mean(1)
            o['paired'][f'{a_}_minus_{b_}'] = dict(auc=float(da.mean()), auc_lo=float(np.percentile(ba, 2.5)), auc_hi=float(np.percentile(ba, 97.5)),
                                                   top20=float(dt.mean()), top20_lo=float(np.percentile(bt, 2.5)), top20_hi=float(np.percentile(bt, 97.5)))
        out[pop] = o
        log('d3 scored', pop, {k: round(v['auc'], 4) for k, v in o['models'].items()})
    return out


def examples(G, FI):
    """K14: one or two rows in HWNI's not-yet-risen top 20, not in HWN's, that surged next month."""
    Ge = G[G.not_yet].copy()
    Ge['rank_I'] = Ge.groupby('mi')['s_HWNI'].rank(ascending=False, method='first')
    Ge['rank_N'] = Ge.groupby('mi')['s_HWN'].rank(ascending=False, method='first')
    top_i = Ge.sort_values(['mi', 's_HWNI', 'work_id'], ascending=[True, False, True]).groupby('mi').head(20)
    top_n = Ge.sort_values(['mi', 's_HWN', 'work_id'], ascending=[True, False, True]).groupby('mi').head(20)
    hk = set(zip(top_n.work_id, top_n.mi))
    cand = top_i[[(w, m) not in hk for w, m in zip(top_i.work_id, top_i.mi)]]
    cand = cand[cand.S1 == 1].merge(FI, on=['work_id', 'mi'], how='left')
    cand = cand.sort_values('s_HWNI', ascending=False)
    stats = dict(rows_in_I_top20_not_in_N_top20=int(len(top_i) - sum((w, m) in hk for w, m in zip(top_i.work_id, top_i.mi))), of_which_surged=int(len(cand)))
    picked = []
    for mask in (cand.i_wtr_rel >= 2, cand.i_all > 0):
        for _, r in cand[mask].iterrows():
            if r.work_id not in [p.work_id for p in picked]:
                picked.append(r)
                break
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'title', 'creator'])
    A = mapping().set_index('work_id')
    E = pd.read_parquet(OUT / 'ol_entries_mapped.parquet')
    out = []
    for r in picked:
        wid = int(r.work_id)
        w = W[W.work_id == wid].iloc[0]
        t = int(r.mi)
        ol = A.loc[wid, 'ol_num']
        e = E[(E.ol_num == ol) & (E.shelf == 'wtr') & (E.mi >= t - 6) & (E.mi <= t)].set_index('mi').n
        ha = pd.read_parquet(JOUT / 'feats_core.parquet', columns=['work_id', 'mi', 'h_age']).query('work_id == @wid and mi == @t').h_age
        out.append(dict(work_id=wid, title=w.title, creator=w.creator, ol_work=A.loc[wid, 'ol_work'], origin=ym(t), h_age=float(ha.iloc[0]) if len(ha) else None,
                        rank_HWNI=int(r.rank_I), rank_HWN=int(r.rank_N), M6=float(r.M6), L_t=float(r.L_t), L_next=float(r.L_next),
                        i=dict({c: (None if pd.isna(r[c]) else float(r[c])) for c in ICOLS}), wtr_months_t6_to_t={ym(m): int(e.get(m, 0)) for m in range(t - 6, t + 1)}))
    return dict(stats=stats, rows=out)


# ====================================================================== report
def pc(x, d=1):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{100 * x:.{d}f}%'


def pt(x, d=1):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 'n/a'
    v = round(100 * float(x), d)
    return f'{(0.0 if v == 0 else v):+.{d}f}'


def iv(lo, hi, d=1):
    return f'{100 * lo:+.{d}f} to {100 * hi:+.{d}f}'


def table(head, rows):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join(['---'] * len(head)) + ' |'] + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


NAMES = {'H': 'H (library history; addendum j)', 'HW': 'H+W (+ own Wikipedia pages; addendum j)', 'HWEN': 'H+W+E+N (addendum j, with the event calendar)',
         'HWN': 'H+W+N (library, own Wikipedia pages, NYT lists)', 'HWNI': 'H+W+N+I (+ reading intent)', 'placebo_I': "Placebo H+W+N+I' (intent dates moved 12 months earlier)"}


def stage_report():
    res = json.loads((OUT / 'k1_results.json').read_text())
    T = pd.read_csv(OUT / 'measures.csv')
    DF = pd.read_csv(OUT / 'paired_differences.csv')
    CH = pd.read_csv(OUT / 'feature_on_surge_rates.csv')
    DT = pd.read_parquet(OUT / 'dump_month_totals.parquet')
    pa, pr, dec = res['parse'], res['prep'], res['decision']

    def m(tgt, pop, model, ms='p20'):
        r = T[(T.target == tgt) & (T.population == pop) & (T.model == model) & (T.measure == ms)]
        return r.iloc[0] if len(r) else None

    def d(tgt, pop, a, b, ms='p20'):
        r = DF[(DF.target == tgt) & (DF.population == pop) & (DF.a == a) & (DF.b == b) & (DF.measure == ms)]
        return r.iloc[0] if len(r) else None

    mtxt = lambda r: 'n/a' if r is None else f'{pc(r["mean"])} ({pc(r["lo"])} to {pc(r["hi"])})'
    dtxt = lambda r: 'n/a' if r is None else f'{pt(r["mean"])} ({iv(r["lo"], r["hi"])})'
    DT['year'] = DT.mi // 12
    yr = DT[DT.shelf != 'stop'].groupby('year').n.sum()
    yw = DT[DT.shelf == 'wtr'].groupby('year').n.sum()
    by = pr['by_year']
    g1, g2 = dec['gain_over_HWN'], dec['gain_over_placebo']
    e_n, e_i, e_p = m('S1', 'not_yet', 'HWN'), m('S1', 'not_yet', 'HWNI'), m('S1', 'not_yet', 'placebo_I')
    a_n, a_i = m('S1', 'all', 'HWN'), m('S1', 'all', 'HWNI')
    s3 = d('S3', 'not_yet', 'HWNI', 'HWN')
    s3p = d('S3', 'not_yet', 'HWNI', 'placebo_I')
    d3m = res['d3']['matched']
    b1e = res['base']['S1_not_yet']['rate_mean_over_months']
    ex = res['examples']['rows']
    L = []
    P_ = L.append
    P_('# K1: does reading intent on Open Library add to the alert list?')
    P_('')
    P_(f"Khant Phyo Wai, 01323050. Run {res['run']}.")
    P_('')
    P_('**In plain words**')
    P_('')
    c3 = CH[CH.condition == 'i_wtr_rel >= 3'].iloc[0]
    cp = CH[CH.condition == 'p_i_wtr_rel >= 2 (placebo)'].iloc[0]
    c2 = CH[CH.condition == 'i_wtr_rel >= 2'].iloc[0]
    hw, hwi, hwip = d3m['models']['HWfit_E'], d3m['models']['HWI'], d3m['models']['HWIp']
    p_hwi, p_pl = d3m['paired']['HWI_minus_HWfit_E'], d3m['paired']['HWI_minus_HWIp']
    lines = [
        f"Open Library's public reading-log dump records the month in which someone put a book on a Want to Read, Currently Reading or Already Read shelf; "
        f"{pr['test_a_works_with_any_entry']:,} of the 7,747 study books ({pc(pr['test_a_works_with_any_entry'] / 7747)}) have at least one entry between October 2017 (the first dated entry) and September 2026. "
        f"Use of the site grew a lot and unevenly: {int(yr.get(2018, 0)):,} entries in 2018, {int(yr.get(2020, 0)):,} in 2020, {int(yr.get(2021, 0)):,} in 2021 and {int(yr.get(2023, 0)):,} in 2023.",
        f"Among books whose Seattle borrowing had not yet started to climb, the alert list from library history, the book's own Wikipedia pages and NYT lists (H+W+N) had "
        f"{pc(e_n['mean'])} surging books in its monthly top 20 (base rate {pc(b1e)}); with reading intent added it had {pc(e_i['mean'])}, a difference of {pt(g1['mean'])} points "
        f"(interval {iv(g1['lo'], g1['hi'])}).",
        f"The same model with every intent date moved 12 months earlier scored {pc(e_p['mean'])}; the real dates beat it by {pt(g2['mean'])} points (interval {iv(g2['lo'], g2['hi'])}). "
        f"By the rule fixed in advance (both intervals above 0), reading intent {'adds' if dec['passed'] else 'does not add'} to the alert list.",
        f"Intent does carry some signal on its own: books whose Want to Read entries reached 3 times their usual level surged next month in {pc(c3.surge_rate_on)} of cases "
        f"(base {pc(c3.base)}; at 2 times, {pc(c2.surge_rate_on)}; the moved-date version at 2 times, {pc(cp.surge_rate_on)}), but library history, Wikipedia and NYT lists already hold that information: "
        f"intent gets {pc(res['importance_share_HWNI_S1']['I'])} of the model's split gain, and over three months the difference is {pt(s3['mean'])} points ({iv(s3['lo'], s3['hi'])}).",
        f"For next month's NYT list appearance (D3), adding intent to library history and Wikipedia moves the AUC from {hw['auc']:.3f} to {hwi['auc']:.3f} "
        f"(difference {p_hwi['auc']:+.3f}, interval {p_hwi['auc_lo']:+.3f} to {p_hwi['auc_hi']:+.3f}), and the moved-date version does the same ({hwip['auc']:.3f}), so this small gain does not "
        "depend on the month of the entries (the moved version keeps how much interest a book has on Open Library in general). Limit: the dump keeps only entries that still exist in September 2026, dated by their current shelf.",
    ]
    for i, s in enumerate(lines, 1):
        P_(f'{i}. {s}')
    P_('')
    if ex:
        P_('**Examples** (books the intent model listed and H+W+N did not, which then surged; picked by the rule fixed in advance, K14):')
        P_('')
        for e in ex:
            wt = e['wtr_months_t6_to_t']
            rel = e['i']['i_wtr_rel']
            reltxt = 'n/a' if rel is None else f'{rel:.1f} times'
            P_(f"- **{e['title']}** ({e['creator']}), list made at the end of {e['origin']}: rank {e['rank_HWNI']} with intent, rank {e['rank_HWN']} without. "
               f"Want to Read entries in the 7 months to {e['origin']}: " + ', '.join(f'{v}' for v in wt.values()) +
               f" (this month {reltxt} the usual level); "
               f"Seattle loans: usual level {e['M6']:.0f} a month, {e['L_t']:.0f} in month t, {e['L_next']:.0f} the next month" +
               (f" (a new book in Seattle, first borrowed in {ym(mi_of(e['origin']) - int(e['h_age']))}, so the usual level is its loans since then)" if e.get('h_age') is not None and e['h_age'] < 6 else '') + '.')
        P_('')
        P_('An example shows what the list contains; it does not prove why the model ranked the book high.')
        P_('')
    P_(f"Addendum k (`{res['record']}`), section K1_intent; addendum j's settings otherwise. Choices the record leaves open: K1 to K14 in the header of "
       "`code/main_study/wiki_led/dirs/k1_intent.py` (written before any result). Every interval is a 95% interval (addendum j's month-block bootstrap). "
       "Tables: `data/db/wiki_led/dirs/k1_intent/`.")
    P_('')
    P_("Terms (as addendum j). **Usual level** (M6): median monthly loans over the six months to t. **Surge**: next month's loans at least 2 times the usual level and at least 5 more. "
       "**Not yet risen**: loans in month t below 1.5 times the usual level. **Precision at 20**: the share of a month's top 20 that surge. "
       "**I** (intent): entries dated in month t by shelf and in total, Want to Read entries in t against the median of the 6 months before (1 added to both), and entries in t-2 to t.")
    P_('')
    P_('## 1. The data')
    P_('')
    P_(f"Dump: `{pa['file']}` ({pa['bytes']:,} bytes, SHA-256 `{pa['sha256'][:16]}...`, the same file as the copy of 14 Oct: {'yes' if pa['same_as_14oct_copy'] else 'no'}); "
       f"{pa['lines']:,} lines, {pa['malformed']:,} malformed; entries dated {pa['first_month']} to {pa['last_month']}; "
       f"{pa['distinct_works_any']:,} distinct works. Shelves: Want to Read {pa['rows_by_shelf']['wtr']:,}, Currently Reading {pa['rows_by_shelf']['cur']:,}, "
       f"Already Read {pa['rows_by_shelf']['read']:,}, Stopped Reading {pa['rows_by_shelf']['stop']:,} (not used, K2). "
       f"Entries dated before 2017-01: {pa['entries_before_2017_01']:,}; after 2026-09: {pa['entries_after_2026_09']:,}.")
    P_('')
    P_(f"Mapping (D4 collector, quality high or medium): {pr['mapped_works']:,} of the 7,747 works, {pr['mapped_ol_works']:,} distinct Open Library works; "
       f"{pr['test_a_works_with_any_entry']:,} works ({pc(pr['share_mapped_with_any_entry'])} of the mapped) have at least one entry. "
       f"Entries per mapped work over the whole period: median {pr['entries_per_work_quantiles']['0.5']:.0f}, 90th percentile {pr['entries_per_work_quantiles']['0.9']:.0f}, "
       f"99th percentile {pr['entries_per_work_quantiles']['0.99']:.0f}.")
    P_('')
    sc = res.get('snapshot_check')
    if sc:
        P_(f"Check of the dump against the live counts (weekly collector, {sc['file']}, {sc['works']:,} works fetched so far): Spearman correlation of Want to Read totals "
           f"{sc['spearman_want_to_read']:.3f}; the dump total is at most the live count for {pc(sc['share_dump_le_live'])} of works (median ratio "
           f"{sc['median_ratio_dump_to_live']:.2f}). Entries added after September and entries under older merged keys explain gaps.")
        P_('')
    rows = []
    dw = DT[DT.shelf != 'stop'].groupby('year').n.sum()
    for y in range(2017, 2027):
        b = by[str(y)]
        rows.append([str(y) + (' (to Sep)' if y == 2026 else ''), f'{int(dw.get(y, 0)):,}', f'{int(yw.get(y, 0)):,}', f"{pa['distinct_works_by_year'].get(str(y), 0):,}",
                     f"{b['entries']:,}", f"{b['test_a_works_with_entries']:,}"])
    P_("Activity by year. Open Library's user base and reading-log use changed a lot over these years (the shelves were new in 2017 and use rose in steps after); "
       "the counts are raw, as the record fixes them, so the relative input (this month against the 6 months before) is the one least affected:")
    P_('')
    P_(table(['Year', 'Entries, whole dump (3 shelves)', 'Want to Read, whole dump', 'Works with an entry, whole dump', 'Entries, study books', 'Study books with an entry'], rows))
    P_('')
    ir = res['i_rows']
    P_(f"In the scored rows (origins 2019-01 to 2026-07, {ir['scored_rows']:,} book-months) a book has at least one entry in month t in {pc(ir['share_rows_i_all_pos'])} of rows; "
       f"I is missing in {ir['rows_i_missing']:,} rows (unmapped books) and the placebo I' in {ir['rows_p_missing']:,} (origins after 2025-09 or unmapped).")
    P_('')
    rows = []
    for _, r in CH.iterrows():
        rows.append([r.condition, f'{int(r.rows_on):,}', f'{int(r.works_on):,}', pc(r.surge_rate_on), pc(r.surge_rate_on_not_yet)])
    P_(f"Next-month surge rate where an intent input is on (base {pc(CH.base.iloc[0])} of all rows, {pc(CH.base_not_yet.iloc[0])} not yet risen; descriptive):")
    P_('')
    P_(table(['Input (on)', 'Rows', 'Books', 'Surge rate where on', 'Same, not yet risen'], rows))
    P_('')
    P_('## 2. Main result: next-month surges')
    P_('')
    for pop, title in (('not_yet', 'Books not yet risen at t (primary)'), ('all', 'All books')):
        P_(f'**{title}**')
        P_('')
        rows = [[NAMES[nm], mtxt(m('S1', pop, nm)), mtxt(m('S1', pop, nm, 'ap')), mtxt(m('S1', pop, nm, 'cov100'))] for nm in ('H', 'HW', 'HWEN', 'HWN', 'HWNI', 'placebo_I')]
        P_(table(['Model', 'Precision at 20', 'Average precision', 'Coverage in top 100'], rows))
        P_('')
    P_('**Paired differences** (points, same months; interval):')
    P_('')
    rows = []
    for a, b in (('HWNI', 'HWN'), ('HWNI', 'placebo_I'), ('placebo_I', 'HWN'), ('HWN', 'H'), ('HWN', 'HWEN'), ('HWNI', 'HWEN')):
        rows.append([f'{a} minus {b}', dtxt(d('S1', 'not_yet', a, b)), dtxt(d('S1', 'all', a, b)), dtxt(d('S1', 'not_yet', a, b, 'ap')), dtxt(d('S1', 'not_yet', a, b, 'cov100'))])
    P_(table(['Comparison', 'Precision at 20, not yet risen', 'Precision at 20, all', 'Average precision, not yet risen', 'Coverage, not yet risen'], rows))
    P_('')
    P_(f"**Decision (fixed in advance).** H+W+N+I minus H+W+N: {pt(g1['mean'])} ({iv(g1['lo'], g1['hi'])}), {'above 0' if g1['passed'] else 'not above 0'}; "
       f"H+W+N+I minus the placebo: {pt(g2['mean'])} ({iv(g2['lo'], g2['hi'])}), {'above 0' if g2['passed'] else 'not above 0'}. "
       f"{'Both pass: reading intent adds to the alert list.' if dec['passed'] else 'Both are needed, so by the rule fixed in advance reading intent does not clearly add to the alert list.'}")
    rr = DF[(DF.target == 'S1') & (DF.population == 'not_yet') & (DF.a == 'HWNI') & (DF.b == 'placebo_I') & DF.measure.str.startswith('p20_origins_to')]
    if len(rr):
        rr = rr.iloc[0]
        P_(f"Check on the origins with complete placebo data ({rr.measure.split('_to_')[1]} and before, {int(rr.months)} months): H+W+N+I minus the placebo {pt(rr['mean'])} ({iv(rr.lo, rr.hi)}).")
    r_ne = d('S1', 'not_yet', 'HWN', 'HWEN')
    P_(f"For context (not part of this test): H+W+N is {pt(r_ne['mean'])} points ({iv(r_ne['lo'], r_ne['hi'])}) against addendum j's H+W+E+N on the primary measure, "
       "the event calendar is not part of this test (addendum j's own E-only placebo comparison, H+W+E+N minus the same with E dates moved, was +1.2, +0.3 to +2.1).")
    P_(f"Fit check: addendum j's H+W refitted with this script's copy of the fit gives j2's scores (largest difference {res['check_j2']['max_abs_diff']:.1e}).")
    P_('')
    P_('## 3. Surges within three months (models refitted on that target)')
    P_('')
    rows = [[NAMES[nm], mtxt(m('S3', 'not_yet', nm)), mtxt(m('S3', 'all', nm))] for nm in ('H', 'HW', 'HWEN', 'HWN', 'HWNI', 'placebo_I')]
    P_(table(['Model', 'Precision at 20, not yet risen', 'Precision at 20, all'], rows))
    P_('')
    rows = [[f'{a} minus {b}', dtxt(d('S3', 'not_yet', a, b)), dtxt(d('S3', 'all', a, b))] for a, b in (('HWNI', 'HWN'), ('HWNI', 'placebo_I'), ('placebo_I', 'HWN'))]
    P_(table(['Comparison', 'Precision at 20, not yet risen', 'Precision at 20, all'], rows))
    P_('')
    P_('## 4. NYT list appearance next month (D3) with intent added')
    P_('')
    P_(f"D3's rows (books not on a list in month t), target an NYT week in month t+1, D3's models and measures. Fit check: D3's H refitted here gives D3's scores "
       f"(largest difference {res['d3']['check']['max_abs_diff']:.1e}). The placebo rows (I') are an extra check, not in the record.")
    P_('')
    lab = {'Hfit_E': 'H (D3)', 'HWfit_E': 'H+W (D3)', 'HI': 'H+I', 'HWI': 'H+W+I', 'HIp': "H+I' (placebo)", 'HWIp': "H+W+I' (placebo)"}
    for pop, title in (('matched', 'Books matched to NYT entries (D3 primary)'), ('all', 'All 7,747 books')):
        o = res['d3'][pop]
        P_(f"**{title}** ({o['n_rows']:,} rows, {o['months_with_appearance']} months with an appearance, {o['n_appear']:,} appearances)")
        P_('')
        rows = [[lab[c], f"{o['models'][c]['auc']:.3f} ({o['models'][c]['auc_lo']:.3f} to {o['models'][c]['auc_hi']:.3f})",
                 f"{pc(o['models'][c]['top20'])} ({pc(o['models'][c]['top20_lo'])} to {pc(o['models'][c]['top20_hi'])})"] for c in lab]
        P_(table(['Model', 'AUC (mean over months)', 'Top-20 share'], rows))
        P_('')
        rows = []
        for k, txt in (('HI_minus_Hfit_E', 'H+I minus H'), ('HWI_minus_HWfit_E', 'H+W+I minus H+W'), ('HI_minus_HIp', "H+I minus H+I'"), ('HWI_minus_HWIp', "H+W+I minus H+W+I'")):
            p = o['paired'][k]
            rows.append([txt, f"{p['auc']:+.4f} ({p['auc_lo']:+.4f} to {p['auc_hi']:+.4f})", f"{pt(p['top20'])} ({iv(p['top20_lo'], p['top20_hi'])})"])
        P_(table(['Comparison', 'AUC difference', 'Top-20 share difference (points)'], rows))
        P_('')
    sh = res['importance_share_HWNI_S1']
    P_('## 5. What the intent model leans on')
    P_('')
    P_('Share of the split gain by input group (H+W+N+I, next-month model, mean over the 8 test years): ' + ', '.join(f'{g} {pc(sh.get(g, 0))}' for g in ['H', 'W', 'N', 'I']) +
       '. Intent inputs: ' + ', '.join(f'`{k}` {pc(v)}' for k, v in res['importance_I_cols_HWNI_S1'].items()) + '.')
    P_('')
    st = res['examples']['stats']
    P_(f"Rows in the intent model's not-yet-risen top 20 that are not in H+W+N's: {st['rows_in_I_top20_not_in_N_top20']:,} over the 78 months, of which {st['of_which_surged']:,} surged.")
    P_('')
    P_('## 6. Limits')
    P_('')
    P_("- The dump holds only entries that still exist on 2026-09-30, dated by the entry's current shelf: entries later removed are missing and books moved between shelves are re-dated "
       "(for example from Want to Read to Already Read). Past months therefore look a little different from what could have been seen at the time (a mild look-ahead, as the record says).")
    P_("- Open Library's activity grew several-fold and unevenly over these years (section 1); the counts are not adjusted for it. The walk-forward refits learn each year from earlier years, "
       "when the counts were smaller.")
    P_("- Open Library users are a small, particular group of readers (often students and library users worldwide); the target is borrowing in one library (Seattle).")
    P_("- Entries under older, merged Open Library keys of the same book are not counted (the dump has no redirect table); the live-count check above gives the size of the gap.")
    P_("- Test A's models, not tuned.")
    P_('')
    P_('## Files')
    P_('')
    P_("`data/db/wiki_led/dirs/k1_intent/`: `parse_info.json`, `dump_month_totals.parquet` (whole dump by month and shelf), `ol_entries_mapped.parquet` (entries of the mapped works by "
       "month and shelf), `feats_i.parquet` (I and I' per book-month), `work_entries.parquet`, `preds_S1_*.parquet`, `preds_S3_*.parquet`, `d3_preds.parquet`, `measures.csv`, "
       "`paired_differences.csv`, `feature_on_surge_rates.csv`, `importance_*.json`, `check_reproduce_j2.json`, `check_reproduce_d3.json`, `k1_results.json`.")
    (REP / 'dir_k1_intent.md').write_text('\n'.join(L) + '\n')
    log('report written', REP / 'dir_k1_intent.md')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['parse', 'prep', 'fit', 'd3_fit', 'score', 'report'])
    ap.add_argument('--models', nargs='*', default=['HW_check', 'HWN', 'HWNI', 'placebo_I'])
    ap.add_argument('--targets', nargs='*', default=['S1', 'S3'])
    a = ap.parse_args()
    {'parse': stage_parse, 'prep': stage_prep, 'd3_fit': stage_d3_fit, 'score': stage_score, 'report': stage_report}.get(a.stage, lambda: stage_fit(a.models, a.targets))()
    log('peak MB', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20))
