#!/usr/bin/env python3
"""J2 of addendum j (combined alert list): do the library history (H), the book's own Wikipedia pages (W), a calendar of known
events (E), the New York Times lists (N) and the bursts of book-linked Wikipedia pages (L), added one after another, put more books
whose borrowing surges next month into a monthly top-20 list?

Record: prereg/addenda_wiki_led/2026-10-22_j_combined_alerts.json (fixed 22 Oct 2026 07:30 +07, read-only; SHA-256 checked below);
the parent record and addenda a to i apply where j says nothing.  This script covers the record's sections features, models,
targets, measures and decision.  The book-linked pages (sections book_links, linked_page_attention and the anniversaries of
scheduled_calendar) are built by J1 and read here from data/db/wiki_led/dirs/j_links/ (anniversaries.parquet, linked_bursts.parquet).
Run from handoff/code:
    ../.venv/bin/python main_study/wiki_led/dirs/j2_alerts.py --stage prep          (light: targets, H, W, E, N)
    ../.venv/bin/python main_study/wiki_led/dirs/j2_alerts.py --stage prep_l        (light: L from linked_bursts.parquet)
    bash ../jobs/heavy_lock.sh nice -n 10 ../.venv/bin/python main_study/wiki_led/dirs/j2_alerts.py --stage fit --models H HW ...
    ../.venv/bin/python main_study/wiki_led/dirs/j2_alerts.py --stage score         (bootstrap, examples, results JSON)
    ../.venv/bin/python main_study/wiki_led/dirs/j2_alerts.py --stage report        (data/reports/dir_j2_alerts.md from the JSON)
Outputs: data/db/wiki_led/dirs/j_alerts/ and data/reports/dir_j2_alerts.md.

FIXED BY THE RECORD (not repeated in full): units and rows (Test A's 7,747 works, test_a_rows_c.parquet, Test A's training and test
years, walk-forward refits by test year, seed 20261020); features H, W, E, N, L; LightGBM with Test A's settings, no tuning; the
ladder H, H+W, H+W+E, H+W+E+N, H+W+E+N+L; the placebo (E and L with all dates moved 12 months earlier, in the full model); the two
surge targets; precision at 20 among all works and among works not yet risen, average precision, coverage in the top 100; month-block
bootstrap (blocks of 3 months, 2,000 draws, paired for differences); the primary decision and the secondary comparisons.

CHOICES THE RECORD LEAVES OPEN (written 22 Oct 2026 09:15 to 09:45 +07, before any result of this test was computed)
 Rows and targets
  J1  Rows: every row of test_a_rows_c.parquet (origins 2016-03 to 2026-07; 750,501 rows).  Scored rows: origins 2019-01 to 2026-07 of
      the test years 2019 to 2026, exactly the rows Test A scored (test year = calendar year of month t+1).  Training for test year Y:
      rows whose outcome months all lie before 1 January of Y (next-month target: t+1 < Y*12, Test A's rule; three-month target:
      t+3 < Y*12).
  J2  "L_next >= 2 x M6" and "L_t < 1.5 x M6" use Test A's arithmetic, as in D2: D = ln(1 + L) - ln(1 + M6) in float32; surge =
      D >= ln 2 and L - M6 >= 5 (Test A's stored Sg); not yet risen at t = ln(1 + L_t) - ln(1 + M6) < ln 1.5 (D2's C11 rule, which
      suggested this measure).  The literal L_t < 1.5 x M6 would call every book with M6 = 0 "already risen", even with no loan.
      Check before going on: the stored Sg gives 20,484 next-month surges in the rows of 2016 to 2026 (D2's count); the script stops
      if not.
  J3  Three-month target: S3 = surge judged on the largest month of t+1, t+2, t+3 (each against M6 at t, Test A's arithmetic);
      excluded months (the benchmark's library-wide rule) and months after 2026-08 are missing, the largest available month is used;
      a row needs t+3 <= 2026-08 (origins up to 2026-05), as D2's C7.  Since both conditions rise with L, this equals "surged in at
      least one of the three months" (checked).
 Features (all known at the end of month t)
  J4  H and W: Test A's columns unchanged (h_lt, h_lt1, h_m6, h_m12, h_lyago, h_age; b_ and a_ of lvl4, r4, r1, rmax, nrise8, run,
      dw, chg, valid4), missing values left missing (LightGBM's own handling, as in Test A).
  J5  E, the scheduled calendar, from D2's events (events_long.parquet: film and TV adaptations with a release month, the earliest
      best-rank P577 or P580 date at month precision; author deaths P570 at month precision) and J1's anniversaries.parquet:
        e_rel_film, e_rel_tv   1 if a film (TV) adaptation of the book is released in t+1..t+3 (D2's release alert, split by type);
        e_rel_soon             3, 2 or 1 when the first release in t+1..t+3 falls in t+1, t+2 or t+3; 0 when none;
        e_death                1 if the author died in month t (D2's death alert);
        e_ann_event            number of linked dated events (J1) with a round anniversary (a multiple of 25 years) in t+1..t+3;
        e_ann_birth, e_ann_death  1 if the author's birth (death) has a round anniversary in t+1..t+3.
      Missing event = 0 (no known event).  D2's other lists (dated awards, release "already public", release in month t) are not
      part of E: the record names releases, anniversaries and deaths only.
  J6  N, from D3's monthly table (nyt_monthly.parquet: matched works by month, weeks on any non-series list): n_on = on any list in
      month t; n_enter = on a list in t and on none in t-1; n_weeks = distinct list weeks in t.  Works never matched = 0.
  J7  L, from J1's linked_bursts.parquet (work, month, link type, page category: n_pages, n_burst, any_top500, max_ratio): for month t
      and month t-1, the number of bursting linked pages and "any" (number > 0), by each link type, by each page category and in total
      (counts and any, as the record says; n_pages, any_top500 and max_ratio are not used as features).  A work-month with no row has
      0 bursts; a month outside J1's burst months is missing.  Category totals are summed over link types and the total over all
      rows, as J1's file gives them (a page linked to the same book in two ways can count twice; see J1's report).
  J8  Placebo ("all dates moved 12 months earlier"): an event or burst dated month e is treated as dated e - 12, so the placebo feature
      at origin t equals the real feature computed at t + 12 (releases in t+13..t+15, the death in t+12, anniversaries in t+13..t+15,
      bursts in t+11 and t+12).  Where that needs data after the data end (bursts after J1's last burst month, deaths after 2026-09)
      the placebo feature is missing, not 0.  So the placebo has full data only for origins up to 2025-09 (with bursts to 2026-09); its
      comparison with the full model is reported on all scored months and, as a check, on the origins up to 2025-09.  H, W and N stay
      real in the placebo model, so placebo minus full isolates the timing of E and L.
 Models
  J9  LightGBM regressor with Test A's settings and seed (n_estimators 300, learning rate 0.05, 31 leaves, min_child_samples 50,
      subsample 0.8 every iteration, colsample_bytree 0.8, random_state 20261020, 4 threads), fitted on the 0/1 surge target itself
      (squared loss, as D3 did for its 0/1 target), once for the next-month target and again for the three-month target.  The record
      says the models are "refitted on that target"; Test A's own change-target model (Hlgbm_D, the H that D2 compared against) is
      scored beside as a reference, from test_a_preds_c.parquet, without refitting.
  J10 Models: next-month target: H, HW, HWE, HWEN, HWENL (full), placebo (H+W+E'+N+L', same column order as the full model), and
      HW + one page category's L columns (counts and any, t and t-1) for each category in J1's file.  Three-month target: the ladder and
      the placebo (the category models only for the next-month target).
 Measures
  J11 Per origin month, ranking by the model's score (ties by work_id): precision at 20 = share of the 20 highest that surge; average
      precision = sklearn's average_precision_score within the month; coverage = surges among the 100 highest / all surges of the
      month.  "Among works not yet risen": the same, computed on the not-yet-risen rows of the month only (their own top 20 and top
      100, their own surges).  Months with no surge in the population are left out of average precision and coverage.
  J12 Means over months; 95% intervals from Test A's circular month-block bootstrap (blocks of 3, 2,000 draws; numpy default_rng(
      20261020), the first draws for the 78 next-month months, the next for the 76 three-month months); paired differences use the
      same draws on the per-month differences.
 Decision
  J13 Primary: precision at 20 among not-yet-risen works, next-month target, full minus H: the 95% interval above 0.
      Event and linked-page information counts only if the full model beats the placebo model on the same measure: the interval of
      full minus placebo above 0 (equivalently, the gain over H of the full model exceeds that of the placebo).  The point
      difference is reported as well.  Every other comparison is secondary and reported whatever it shows.
 Examples
  J14 Three examples from the primary lists: rows in the full model's not-yet-risen top 20 that are not in H's not-yet-risen top 20 of
      the same month and that surged next month.  First the one with the highest full-model score among those with an E feature on,
      then the highest among those with an L burst, then the highest remaining with an E or L feature (N if none), three different
      works.  The reason given is the active E, N and L features at t (and, for L, the linked pages that burst, from J1's page-level
      files when they exist).  An example shows what the list contains; it does not prove why the model ranked the book high.
 Extra, descriptive (not in the record): per feature, the surge rate next month of the scored rows where it is on (positive control
 for real features, near the base rate for placebo features); gain importance by feature group for the full model.
 Interim (added 22 Oct 2026 09:25 +07, before any result of a model with E, N or L; coordinator's change of plan, see prereg/DEVIATIONS.md,
 Addendum j, 09:20): the ladder without L (H, H+W, H+W+E, H+W+E+N) is scored and reported first.
  J15 For that interim report a placebo of the E inputs alone is fitted: placebo_E = H+W+E'+N (E' = E with all dates moved 12 months
      earlier, J8; same column order as H+W+E+N).  In the interim, "full" means H+W+E+N and the placebo rule compares it with placebo_E.
      With L, the record's full model and placebo (E and L moved) decide; placebo_E is kept beside as a check.  Its complete-data origins
      run to 2025-09 (deaths are known to 2026-09).
Limit (in the report): Wikidata dates may have been entered after the event, so the calendar is a little better than what was known
at the time (D2).
"""
import sys, os, json, time, pathlib, hashlib, argparse, warnings, resource
import numpy as np, pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))          # code/
from config import D  # noqa: E402

D = pathlib.Path(D)
ROOT = D.parent
IN = D / 'db' / 'wiki_led'
JL = IN / 'dirs' / 'j_links'
OUT = IN / 'dirs' / 'j_alerts'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
ADD_J = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_j_combined_alerts.json'
assert hashlib.sha256(ADD_J.read_bytes()).hexdigest() == '9a7384ab706ac318ecebc518c801e98c67ee6c7b4e3b8f981ee59fb5c46725b3', 'addendum j changed'
SET = json.loads(ADD_J.read_text())
SEED = 20261020
NB = 2000
T0 = time.time()
LN15, LN2 = np.log(1.5), np.log(2)
SHIFT = 12                                         # placebo: dates moved 12 months earlier
DEATH_END = 2026 * 12 + 8                          # 2026-09: last month of known deaths (events fetched 20 Oct 2026)
TEST_YEARS = list(range(2019, 2027))
HCOLS = ['h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age']
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
WCOLS = ['b_' + c for c in FEATS] + ['a_' + c for c in FEATS]
ECOLS = ['e_rel_film', 'e_rel_tv', 'e_rel_soon', 'e_death', 'e_ann_event', 'e_ann_birth', 'e_ann_death']
NCOLS = ['n_on', 'n_enter', 'n_weeks']
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, random_state=SEED, n_jobs=4, verbose=-1)


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(s):
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def ym(mi):
    mi = int(mi)
    return f'{mi // 12}-{mi % 12 + 1:02d}'


SCORE0 = mi_of('2019-01')
PLACEBO_FULL_END = None                             # set from J1's burst months in prep_l (origins with full placebo data)


def dflag(L, M6):
    """Test A's arithmetic (float32): D, rose, surged.  NaN L gives D NaN and both flags False."""
    L32 = np.asarray(L, dtype=np.float32)
    M32 = np.asarray(M6, dtype=np.float32)
    Dv = np.log1p(L32) - np.log1p(M32)
    with np.errstate(invalid='ignore'):
        rose = Dv >= LN15
        surge = (Dv >= LN2) & ((L32 - M32) >= 5)
    return Dv, rose, surge


# ====================================================================== stage prep: targets, H, W, E (without anniversaries), N
def loans_panel():
    """Monthly loans per work, all formats, exactly as 10c_test_a.py and d2_events.py (excluded months missing)."""
    P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
    EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id'])
    C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
    Lc = C.groupby(['work_id', 'mi']).y.sum()
    first = Lc[Lc > 0].reset_index().groupby('work_id').mi.min()
    MI = np.arange(mi_of('2005-04'), mi_of('2026-08') + 1)
    A = Lc.unstack('mi').reindex(columns=MI).fillna(0).astype(np.float32).reindex(W.work_id).fillna(0).to_numpy(dtype=np.float32).copy()
    f_arr = first.reindex(W.work_id).to_numpy(dtype=float)
    A[(MI[None, :] < f_arr[:, None])] = np.nan
    A[:, np.isin(MI, sorted(EXCL))] = np.nan
    widx = pd.Series(np.arange(len(W)), index=W.work_id.to_numpy())
    return A, MI, widx, EXCL


def event_tables():
    """D2's adaptation releases (film, tv) and author deaths, one row per work and event month."""
    EV = pd.read_parquet(IN / 'events.parquet', columns=['work_id', 'item', 'author_item']).drop_duplicates('work_id')
    EL = pd.read_parquet(IN / 'events_long.parquet')
    ad = EL[(EL.event == 'adaptation') & EL.type_group.isin(['film', 'tv']) & EL.mi_event.notna()].copy()
    ad = ad.merge(EV[['work_id', 'item']], left_on='subject', right_on='item')
    ad['e'] = ad.mi_event.astype(int)
    REL = ad[['work_id', 'e', 'type_group', 'detail', 'label', 'en_title']].drop_duplicates(['work_id', 'e', 'type_group', 'detail'])
    de = EL[(EL.event == 'death') & EL.mi_event.notna()].merge(EV[['work_id', 'author_item']], left_on='subject', right_on='author_item')
    de['e'] = de.mi_event.astype(int)
    DEA = de[['work_id', 'e', 'author_item']].drop_duplicates(['work_id', 'e'])
    return REL, DEA


def e_core(keys, REL, DEA, shift):
    """e_rel_film, e_rel_tv, e_rel_soon, e_death at origin t, with all event dates moved `shift` months earlier."""
    out = keys[['work_id', 'mi']].copy()
    rel = []
    for k in (1, 2, 3):
        x = REL[['work_id', 'e', 'type_group']].copy()
        x['mi'] = x.e - shift - k                         # the (moved) release month e - shift falls in t + k
        x['soon'] = 4 - k
        rel.append(x)
    rel = pd.concat(rel, ignore_index=True)
    g = rel.groupby(['work_id', 'mi'])
    f = pd.DataFrame({'e_rel_film': g.type_group.agg(lambda s: int((s == 'film').any())),
                      'e_rel_tv': g.type_group.agg(lambda s: int((s == 'tv').any())),
                      'e_rel_soon': g.soon.max()}).reset_index()
    out = out.merge(f, on=['work_id', 'mi'], how='left')
    d = DEA.assign(mi=DEA.e - shift)[['work_id', 'mi']].drop_duplicates().assign(e_death=1)
    out = out.merge(d, on=['work_id', 'mi'], how='left')
    for c in ['e_rel_film', 'e_rel_tv', 'e_rel_soon', 'e_death']:
        out[c] = out[c].fillna(0).astype(np.float32)
    # deaths are known to 2026-09: a (moved) death month t + shift after that is unknown -> missing
    out.loc[out.mi + shift > DEATH_END, 'e_death'] = np.nan
    return out


def n_feats(keys):
    T = pd.read_parquet(IN / 'dirs' / 'd3_nyt' / 'nyt_monthly.parquet', columns=['work_id', 'mi', 'weeks'])
    T = T[T.weeks > 0]
    out = keys[['work_id', 'mi']].copy()
    cur = T.rename(columns={'weeks': 'n_weeks'})
    prev = T.assign(mi=T.mi + 1)[['work_id', 'mi']].assign(_prev=1)
    out = out.merge(cur, on=['work_id', 'mi'], how='left').merge(prev, on=['work_id', 'mi'], how='left')
    out['n_weeks'] = out.n_weeks.fillna(0).astype(np.float32)
    out['n_on'] = (out.n_weeks > 0).astype(np.float32)
    out['n_enter'] = ((out.n_weeks > 0) & out._prev.isna()).astype(np.float32)
    return out.drop(columns='_prev')


def stage_prep():
    R = pd.read_parquet(IN / 'test_a_rows_c.parquet')
    R = R.drop(columns=['article', 'author_article', 'test_year'])
    n_surge = int(R.Sg.sum())
    log('rows', len(R), 'next-month surges in the rows of', ym(R.mi.min() + 1), 'to', ym(R.mi.max() + 1), ':', n_surge)
    assert n_surge == 20484, f'next-month surge count {n_surge} differs from D2 (20,484)'
    A, MI, widx, EXCL = loans_panel()
    LAST = int(MI[-1])
    wi = R.work_id.map(widx).to_numpy()
    Dchk, _, s1 = dflag(A[wi, R.mi.to_numpy() + 1 - MI[0]], R.M6.to_numpy())
    chk = dict(rows=int(len(R)), max_abs_diff_D=float(np.nanmax(np.abs(Dchk - R.D.to_numpy()))), surge_agree=float(np.mean(s1 == (R.Sg.to_numpy() == 1))))
    log('rebuilt loans against Test A D:', chk)
    assert chk['surge_agree'] == 1.0
    # three-month target J3: the largest available month of t+1..t+3
    Ls = []
    for k in (1, 2, 3):
        m = R.mi.to_numpy() + k
        Lk = np.full(len(R), np.nan, np.float32)
        ok = m <= LAST
        Lk[ok] = A[wi[ok], m[ok] - MI[0]]
        Ls.append(Lk)
    Ls = np.vstack(Ls)
    Lmax = np.nanmax(Ls, axis=0)
    _, _, S3 = dflag(Lmax, R.M6.to_numpy())
    anyk = np.zeros(len(R), bool)
    for k in range(3):
        anyk |= dflag(Ls[k], R.M6.to_numpy())[2]
    assert np.array_equal(S3, anyk), 'largest-month rule differs from any-month rule'
    R['S1'] = R.Sg.astype(np.int8)
    R['S3'] = S3.astype(np.int8)
    R['obs3'] = (R.mi + 3 <= LAST)
    R['L3max'] = Lmax
    Dt, rose_t, _ = dflag(R.L_t.to_numpy(), R.M6.to_numpy())
    R['not_yet'] = ~rose_t
    # E core (real and placebo) and N
    REL, DEA = event_tables()
    keys = R[['work_id', 'mi']]
    Er = e_core(keys, REL, DEA, 0)
    Ep = e_core(keys, REL, DEA, SHIFT).rename(columns={c: 'p_' + c for c in ['e_rel_film', 'e_rel_tv', 'e_rel_soon', 'e_death']})
    N = n_feats(keys)
    F = R.merge(Er, on=['work_id', 'mi']).merge(Ep, on=['work_id', 'mi']).merge(N, on=['work_id', 'mi'])
    assert len(F) == len(R)
    for c in F.columns:
        if F[c].dtype == np.float64:
            F[c] = F[c].astype(np.float32)
    F.to_parquet(OUT / 'feats_core.parquet', index=False)
    REL.to_parquet(OUT / 'events_releases.parquet', index=False)
    DEA.to_parquet(OUT / 'events_deaths.parquet', index=False)
    info = dict(check_D=chk, surges_next_month_all_rows=n_surge, surges_3m_rows_observed=int(F.loc[F.obs3, 'S3'].sum()),
                rows=int(len(F)), rows_obs3=int(F.obs3.sum()), share_not_yet=float(F.not_yet.mean()),
                excluded_months=[ym(m) for m in sorted(EXCL)], last_loan_month=ym(LAST),
                e_rows_on={c: int((F[c] > 0).sum()) for c in ['e_rel_film', 'e_rel_tv', 'e_death', 'p_e_rel_film', 'p_e_rel_tv', 'p_e_death']},
                n_rows_on={c: int((F[c] > 0).sum()) for c in ['n_on', 'n_enter']},
                scored_rows=int((F.mi >= SCORE0).sum()), scored_surges=int(F.loc[F.mi >= SCORE0, 'S1'].sum()))
    (OUT / 'prep_info.json').write_text(json.dumps(info, indent=1))
    log('prep done', info)


# ====================================================================== stage prep_ann: anniversaries (J1) -> e_ann_* (real and placebo)
def stage_prep_ann():
    F = pd.read_parquet(OUT / 'feats_core.parquet', columns=['work_id', 'mi'])
    AN = pd.read_parquet(JL / 'anniversaries.parquet')
    log('anniversaries.parquet', AN.shape, list(AN.columns))
    A2 = ann_normalise(AN)                     # -> work_id, mi (anniversary month), kind in {event, birth, death}, n (count)
    out = F.copy()
    for shift, pre in ((0, ''), (SHIFT, 'p_')):
        rows = []
        for k in (1, 2, 3):
            x = A2.copy()
            x['mi'] = x.mi - shift - k
            rows.append(x)
        x = pd.concat(rows, ignore_index=True)
        x = x.drop_duplicates(['work_id', 'mi', 'kind', 'key'])        # one anniversary counts once per origin
        g = x.groupby(['work_id', 'mi', 'kind']).size().unstack('kind', fill_value=0)
        for kd in ('event', 'birth', 'death'):
            if kd not in g.columns:
                g[kd] = 0
        g = g[['event', 'birth', 'death']].reset_index()
        g.columns = ['work_id', 'mi', pre + 'e_ann_event', pre + 'e_ann_birth', pre + 'e_ann_death']
        g[pre + 'e_ann_birth'] = (g[pre + 'e_ann_birth'] > 0).astype(int)
        g[pre + 'e_ann_death'] = (g[pre + 'e_ann_death'] > 0).astype(int)
        out = out.merge(g, on=['work_id', 'mi'], how='left')
        for c in ['e_ann_event', 'e_ann_birth', 'e_ann_death']:
            out[pre + c] = out[pre + c].fillna(0).astype(np.float32)
    out.to_parquet(OUT / 'feats_ann.parquet', index=False)
    log('anniversary features', {c: int((out[c] > 0).sum()) for c in out.columns[2:]})


def ann_normalise(AN):
    """Map J1's anniversaries.parquet (work_id, mi = anniversary month, kind in event / author_birth / author_death, years, source_item,
    link_type, page_title, event_mi; months 2015-01 to 2027-12; J1's header J7) to (work_id, mi, kind, key)."""
    km = {'event': 'event', 'author_birth': 'birth', 'author_death': 'death'}
    assert set(AN.kind.unique()) <= set(km), AN.kind.unique()
    assert (AN.years % 25 == 0).all() and (AN.years > 0).all()
    assert int(AN.mi.max()) >= mi_of('2026-07') + SHIFT + 3, 'anniversary months do not reach the placebo window'
    return pd.DataFrame({'work_id': AN.work_id.astype(np.int64), 'mi': AN.mi.astype(int), 'kind': AN.kind.map(km), 'key': AN.source_item.astype(str)})


# ====================================================================== stage prep_l: L from linked_bursts.parquet (real and placebo)
def stage_prep_l():
    F = pd.read_parquet(OUT / 'feats_core.parquet', columns=['work_id', 'mi'])
    LB = pd.read_parquet(JL / 'linked_bursts.parquet')
    log('linked_bursts.parquet', LB.shape, list(LB.columns))
    LB = LB[LB.work_id.isin(F.work_id.unique())]
    m0, m1 = int(LB.mi.min()), int(LB.mi.max())
    lts = sorted(LB.link_type.astype(str).unique())
    cats = sorted(LB.category.astype(str).unique())
    log('burst months', ym(m0), 'to', ym(m1), 'link types', lts, 'categories', cats)
    LB = LB.assign(link_type=LB.link_type.astype(str), category=LB.category.astype(str))
    # monthly tables: works x months, by link type, by category, total
    tabs = {}
    for lt in lts:
        tabs['lt_' + lt] = LB[LB.link_type == lt].groupby(['work_id', 'mi']).n_burst.sum()
    for c in cats:
        tabs['cat_' + c] = LB[LB.category == c].groupby(['work_id', 'mi']).n_burst.sum()
    tabs['all'] = LB.groupby(['work_id', 'mi']).n_burst.sum()
    out = F.copy()
    cols_real = []
    for shift, pre in ((0, ''), (SHIFT, 'p_')):
        for name, s in tabs.items():
            s = s.reset_index()
            for lag in (0, 1):                                 # month t (lag 0) and t-1 (lag 1)
                # value at origin t = bursts in month t - lag + shift (dates moved `shift` months earlier)
                x = s.assign(mi=s.mi + lag - shift).rename(columns={'n_burst': '_v'})
                col_n = f'{pre}l_{name}_n{lag}'
                col_a = f'{pre}l_{name}_a{lag}'
                out = out.merge(x, on=['work_id', 'mi'], how='left')
                src = out.mi - lag + shift                       # the burst month the feature reads
                inside = (src >= m0) & (src <= m1)
                v = out._v.fillna(0).astype(np.float32).where(inside, np.nan)
                out[col_n] = v
                out[col_a] = (v > 0).astype(np.float32).where(inside, np.nan)
                out = out.drop(columns='_v')
                if pre == '':
                    cols_real += [col_n, col_a]
    for c in out.columns[2:]:
        out[c] = out[c].astype(np.float32)
    out.to_parquet(OUT / 'feats_l.parquet', index=False)
    info = dict(burst_months=[ym(m0), ym(m1)], link_types=lts, categories=cats, columns=cols_real,
                placebo_full_data_origins_to=ym(m1 - SHIFT),
                rows_any_burst_t=int((out['l_all_n0'] > 0).sum()), rows_missing_t=int(out['l_all_n0'].isna().sum()),
                placebo_rows_missing_t=int(out['p_l_all_n0'].isna().sum()),
                works_with_rows=int(LB.work_id.nunique()), file_rows=int(len(LB)),
                bursts_by_link_type={lt: int(LB.loc[LB.link_type == lt, 'n_burst'].sum()) for lt in lts},
                bursts_by_category={c: int(LB.loc[LB.category == c, 'n_burst'].sum()) for c in cats},
                file_mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime((JL / 'linked_bursts.parquet').stat().st_mtime)),
                file_sha256=hashlib.sha256((JL / 'linked_bursts.parquet').read_bytes()).hexdigest(),
                j1_coverage=(json.loads((JL / 'bursts_summary.json').read_text()).get('coverage') if (JL / 'bursts_summary.json').exists() else None))
    (OUT / 'prep_l_info.json').write_text(json.dumps(info, indent=1))
    log('L features', info)


# ====================================================================== stage fit
def load_features(need_ann, need_l):
    F = pd.read_parquet(OUT / 'feats_core.parquet')
    if need_ann:
        F = F.merge(pd.read_parquet(OUT / 'feats_ann.parquet'), on=['work_id', 'mi'], how='left')
    if need_l:
        F = F.merge(pd.read_parquet(OUT / 'feats_l.parquet'), on=['work_id', 'mi'], how='left')
    return F


def model_specs():
    """name -> list of columns (the placebo maps to the placebo columns, in the full model's order)."""
    linfo = json.loads((OUT / 'prep_l_info.json').read_text()) if (OUT / 'prep_l_info.json').exists() else None
    LCOLS = linfo['columns'] if linfo else []
    specs = {'H': HCOLS, 'HW': HCOLS + WCOLS, 'HWE': HCOLS + WCOLS + ECOLS, 'HWEN': HCOLS + WCOLS + ECOLS + NCOLS,
             'placebo_E': HCOLS + WCOLS + ['p_' + c for c in ECOLS] + NCOLS}                     # J15
    if linfo:
        specs['HWENL'] = HCOLS + WCOLS + ECOLS + NCOLS + LCOLS
        specs['placebo'] = HCOLS + WCOLS + ['p_' + c for c in ECOLS] + NCOLS + ['p_' + c for c in LCOLS]
        for c in linfo['categories']:
            specs['HW+L_' + c] = HCOLS + WCOLS + [x for x in LCOLS if x.startswith(f'l_cat_{c}_')]
    return specs


def stage_fit(models, targets):
    import lightgbm as lgb
    specs = model_specs()
    need_ann = any(m not in ('H', 'HW') and not m.startswith('HW+L_') for m in models)
    need_l = any(m in ('HWENL', 'placebo') or m.startswith('HW+L_') for m in models)
    F = load_features(need_ann, need_l)
    log('features', F.shape)
    for tgt in targets:
        for name in models:
            if tgt == 'S3' and name.startswith('HW+L_'):
                continue
            f_out = OUT / f'preds_{tgt}_{name}.parquet'
            if f_out.exists():
                log('exists, skipped', f_out.name)
                continue
            cols = specs[name]
            fit_cols = specs['HWENL'] if name == 'placebo' else specs['HWEN'] if name == 'placebo_E' else cols   # placebos: the real model fed the moved columns
            parts, imps = [], {}
            for Y in TEST_YEARS:
                if tgt == 'S1':
                    te = F[(F.year == Y) & (F.mi >= SCORE0)]
                    tr = F[(F.mi + 1) < Y * 12]
                else:
                    te = F[(F.year == Y) & (F.mi >= SCORE0) & F.obs3]
                    tr = F[((F.mi + 3) < Y * 12) & F.obs3]
                if te.empty:
                    continue
                Xtr = tr[cols].set_axis(fit_cols, axis=1)
                Xte = te[cols].set_axis(fit_cols, axis=1)
                m = lgb.LGBMRegressor(**LGB).fit(Xtr, tr[tgt].astype(float))
                p = te[['work_id', 'mi']].copy()
                p['score'] = m.predict(Xte)
                parts.append(p)
                imps[Y] = dict(zip(fit_cols, m.booster_.feature_importance('gain').tolist()))
                log(tgt, name, Y, 'train', len(tr), 'test', len(te), 'train surges', int(tr[tgt].sum()))
            P = pd.concat(parts, ignore_index=True)
            P.to_parquet(f_out, index=False)
            (OUT / f'importance_{tgt}_{name}.json').write_text(json.dumps(imps))
            log('saved', f_out.name, len(P))


# ====================================================================== stage score
def block_draws(n, rng, block=3):
    k = int(np.ceil(n / block))
    out = []
    for _ in range(NB):
        s = rng.choice(np.arange(n), k)
        out.append(np.concatenate([np.arange(a, a + block) % n for a in s])[:n])
    return np.array(out)


def block_ci(x, BD):
    """mean over months with a value, and the 2.5 / 97.5 percentiles of the block-bootstrap means (months without a value skipped)."""
    x = np.asarray(x, float)
    ok = ~np.isnan(x)
    xs = np.where(ok, x, 0.0)
    with np.errstate(all='ignore'):
        b = xs[BD].sum(1) / ok[BD].sum(1)
    return dict(mean=float(np.nanmean(x)), lo=float(np.nanpercentile(b, 2.5)), hi=float(np.nanpercentile(b, 97.5)), months=int(ok.sum()))


def per_month(G, score_col, y_col, months):
    """precision at 20, average precision, coverage in the top 100, per month (J11)."""
    from sklearn.metrics import average_precision_score
    out = np.full((len(months), 3), np.nan)
    for i, (m, g) in enumerate(G.groupby('mi', sort=True)):
        assert m == months[i]
        g = g.sort_values([score_col, 'work_id'], ascending=[False, True])
        y = g[y_col].to_numpy()
        out[i, 0] = y[:20].mean()
        if y.sum() > 0:
            out[i, 1] = average_precision_score(y, g[score_col].to_numpy())
            out[i, 2] = y[:100].sum() / y.sum()
    return out


def stage_score():
    F = pd.read_parquet(OUT / 'feats_core.parquet', columns=['work_id', 'mi', 'year', 'S1', 'S3', 'obs3', 'not_yet', 'L_t', 'M6', 'L_next', 'L3max'])
    F = F[F.mi >= SCORE0]
    TA = pd.read_parquet(IN / 'test_a_preds_c.parquet', columns=['work_id', 'mi', 'Hlgbm_D', 'HWlgbm_D'])
    rng = np.random.default_rng(SEED)
    res = dict(record=str(ADD_J.relative_to(ROOT)), run=time.strftime('%Y-%m-%d %H:%M %z'), prep=json.loads((OUT / 'prep_info.json').read_text()))
    if (OUT / 'prep_l_info.json').exists():
        res['prep_l'] = json.loads((OUT / 'prep_l_info.json').read_text())
    PM = {}                                                # (target, population, model) -> per-month array (months x 3)
    MONTHS = {}
    BDs = {}
    for tgt in ('S1', 'S3'):
        G0 = F if tgt == 'S1' else F[F.obs3]
        months = np.sort(G0.mi.unique())
        MONTHS[tgt] = months
        BDs[tgt] = block_draws(len(months), rng)
        models = sorted(p.stem.split('_', 2)[2] for p in OUT.glob(f'preds_{tgt}_*.parquet'))
        G = G0.merge(TA, on=['work_id', 'mi'], how='left')
        for name in models:
            P = pd.read_parquet(OUT / f'preds_{tgt}_{name}.parquet').rename(columns={'score': 's_' + name})
            G = G.merge(P, on=['work_id', 'mi'], how='left')
            assert G['s_' + name].notna().all(), name
        G = G.rename(columns={'Hlgbm_D': 's_TestA_H_change', 'HWlgbm_D': 's_TestA_HW_change'})
        names = models + ['TestA_H_change', 'TestA_HW_change']
        for pop in ('all', 'not_yet'):
            Gp = G if pop == 'all' else G[G.not_yet]
            for name in names:
                PM[(tgt, pop, name)] = per_month(Gp, 's_' + name, tgt, months)
            log('scored', tgt, pop, len(names), 'models')
        if tgt == 'S1':
            GS1 = G
    MEAS = ['p20', 'ap', 'cov100']
    table = []
    for (tgt, pop, name), arr in PM.items():
        for j, ms in enumerate(MEAS):
            r = block_ci(arr[:, j], BDs[tgt])
            table.append(dict(target=tgt, population=pop, model=name, measure=ms, **r))
    T = pd.DataFrame(table)
    T.to_csv(OUT / 'measures.csv', index=False)
    # base rates per month
    res['base'] = {}
    for tgt in ('S1', 'S3'):
        G0 = F if tgt == 'S1' else F[F.obs3]
        for pop in ('all', 'not_yet'):
            Gp = G0 if pop == 'all' else G0[G0.not_yet]
            res['base'][f'{tgt}_{pop}'] = dict(rate_mean_over_months=float(Gp.groupby('mi')[tgt].mean().mean()), surges=int(Gp[tgt].sum()),
                                               rows=int(len(Gp)), rows_per_month=float(Gp.groupby('mi').size().mean()))
    # paired differences
    pairs = [('HW', 'H'), ('HWE', 'HW'), ('HWEN', 'HWE'), ('HWENL', 'HWEN'), ('HWE', 'H'), ('HWEN', 'H'), ('HWENL', 'H'),
             ('placebo', 'H'), ('HWENL', 'placebo'), ('H', 'TestA_H_change'), ('HWENL', 'TestA_H_change'),
             ('placebo_E', 'H'), ('HWEN', 'placebo_E'), ('HWEN', 'TestA_H_change')]
    cats = res.get('prep_l', {}).get('categories', [])
    pairs += [(f'HW+L_{c}', 'HW') for c in cats]
    diffs = []
    for tgt in ('S1', 'S3'):
        for pop in ('all', 'not_yet'):
            for a, b in pairs:
                if (tgt, pop, a) not in PM or (tgt, pop, b) not in PM:
                    continue
                for j, ms in enumerate(MEAS):
                    d = PM[(tgt, pop, a)][:, j] - PM[(tgt, pop, b)][:, j]
                    diffs.append(dict(target=tgt, population=pop, a=a, b=b, measure=ms, **block_ci(d, BDs[tgt])))
            # placebo check on the origins with full placebo data (J8)
            for plname, fname in (('placebo', 'HWENL'), ('placebo_E', 'HWEN')):
                if (tgt, pop, plname) not in PM or (tgt, pop, fname) not in PM:
                    continue
                end = DEATH_END - SHIFT
                if plname == 'placebo':
                    end = min(end, mi_of(res['prep_l']['placebo_full_data_origins_to']))
                keep = MONTHS[tgt] <= end
                BDk = block_draws(int(keep.sum()), np.random.default_rng(SEED + 1))
                for a, b in ((fname, plname), (plname, 'H'), (fname, 'H')):
                    for j, ms in enumerate(MEAS):
                        d = (PM[(tgt, pop, a)][:, j] - PM[(tgt, pop, b)][:, j])[keep]
                        diffs.append(dict(target=tgt, population=pop, a=a, b=b, measure=ms + f'_origins_to_{ym(end)}', **block_ci(d, BDk)))
    DF = pd.DataFrame(diffs)
    DF.to_csv(OUT / 'paired_differences.csv', index=False)
    res['n_months'] = {k: int(len(v)) for k, v in MONTHS.items()}
    res['months'] = {k: [ym(v[0]), ym(v[-1])] for k, v in MONTHS.items()}

    def get(tgt, pop, model, ms='p20'):
        r = T[(T.target == tgt) & (T.population == pop) & (T.model == model) & (T.measure == ms)]
        return r.iloc[0].to_dict() if len(r) else None

    def getd(tgt, pop, a, b, ms='p20'):
        r = DF[(DF.target == tgt) & (DF.population == pop) & (DF.a == a) & (DF.b == b) & (DF.measure == ms)]
        return r.iloc[0].to_dict() if len(r) else None

    full = 'HWENL' if ('S1', 'not_yet', 'HWENL') in PM else 'HWEN'
    prim = getd('S1', 'not_yet', full, 'H')
    plac = getd('S1', 'not_yet', full, 'placebo' if full == 'HWENL' else 'placebo_E')
    res['full_model'] = full
    res['decision'] = dict(
        primary=dict(measure='precision at 20, next-month surge, works not yet risen, full minus H', full=full, **({k: prim[k] for k in ('mean', 'lo', 'hi', 'months')} if prim else {}),
                     passed=bool(prim and prim['lo'] > 0)),
        placebo=dict(measure='same measure, full minus placebo (' + ('E and L' if full == 'HWENL' else 'E only, interim') + ' dates moved 12 months earlier)',
                     placebo_model='placebo' if full == 'HWENL' else 'placebo_E', **({k: plac[k] for k in ('mean', 'lo', 'hi', 'months')} if plac else {}),
                     passed=bool(plac and plac['lo'] > 0), point_gain_exceeds=bool(plac and plac['mean'] > 0)) if plac else 'placebo not fitted',
    )
    log('decision', res['decision'])
    # ---------------------------------------------------------------- feature checks: surge rate where each feature is on (descriptive)
    FF = load_features((OUT / 'feats_ann.parquet').exists(), (OUT / 'feats_l.parquet').exists())
    FF = FF[FF.mi >= SCORE0]
    chk = []
    on_cols = [c for c in ECOLS + NCOLS + ['p_' + c for c in ECOLS] if c in FF.columns]
    on_cols += [c for c in FF.columns if (c.startswith('l_') or c.startswith('p_l_')) and c.endswith('_a0')]
    base1 = FF.S1.mean()
    base1e = FF.loc[FF.not_yet, 'S1'].mean()
    for c in on_cols:
        on = FF[c] > 0
        one = on & FF.not_yet
        chk.append(dict(feature=c, rows_on=int(on.sum()), works_on=int(FF.loc[on, 'work_id'].nunique()), surge_rate_on=float(FF.loc[on, 'S1'].mean()) if on.any() else np.nan,
                        base=float(base1), rows_on_not_yet=int(one.sum()), surge_rate_on_not_yet=float(FF.loc[one, 'S1'].mean()) if one.any() else np.nan,
                        base_not_yet=float(base1e)))
    CH = pd.DataFrame(chk)
    CH.to_csv(OUT / 'feature_on_surge_rates.csv', index=False)
    # ---------------------------------------------------------------- importance by group (full model, next month)
    imp_f = OUT / f'importance_S1_{full}.json'
    if imp_f.exists():
        imp = json.loads(imp_f.read_text())
        grp = {}
        for Y, d in imp.items():
            tot = sum(d.values())
            for c, v in d.items():
                g = 'H' if c in HCOLS else 'W' if c in WCOLS else 'E' if c in ECOLS else 'N' if c in NCOLS else 'L'
                grp.setdefault(g, []).append(v / tot)
        res['importance_share_full_S1'] = {g: float(np.sum(v) / len(imp)) for g, v in grp.items()}
        top = pd.DataFrame(imp).mean(axis=1).sort_values(ascending=False)
        res['importance_top15_full_S1'] = {k: float(v / top.sum()) for k, v in top.head(15).items()}
    # ---------------------------------------------------------------- examples (J14)
    res['examples'] = examples(GS1, FF, full) if 's_' + full in GS1.columns else []
    (OUT / 'j2_results.json').write_text(json.dumps(res, indent=1, default=float))
    log('score done')


def examples(G, FF, full):
    Ge = G[G.not_yet].copy()
    top_f = Ge.sort_values(['mi', 's_' + full, 'work_id'], ascending=[True, False, True]).groupby('mi').head(20)
    top_h = Ge.sort_values(['mi', 's_H', 'work_id'], ascending=[True, False, True]).groupby('mi').head(20)
    Ge['rank_full'] = Ge.groupby('mi')['s_' + full].rank(ascending=False, method='first')
    Ge['rank_H'] = Ge.groupby('mi')['s_H'].rank(ascending=False, method='first')
    hk = set(zip(top_h.work_id, top_h.mi))
    cand = top_f[[(w, m) not in hk for w, m in zip(top_f.work_id, top_f.mi)]]
    cand = cand[cand.S1 == 1].merge(Ge[['work_id', 'mi', 'rank_full', 'rank_H']], on=['work_id', 'mi'])
    ecols = [c for c in ECOLS if c in FF.columns]
    lcols = [c for c in FF.columns if c.startswith('l_') and (c.endswith('_n0') or c.endswith('_n1'))]
    cand = cand.merge(FF[['work_id', 'mi'] + ecols + NCOLS + lcols], on=['work_id', 'mi'], how='left')
    cand['has_E'] = (cand[ecols].fillna(0) > 0).any(axis=1)
    cand['has_L'] = (cand[[c for c in lcols if c.startswith('l_all_')]].fillna(0) > 0).any(axis=1) if lcols else False
    cand['has_N'] = (cand[NCOLS].fillna(0) > 0).any(axis=1)
    cand = cand.sort_values('s_' + full, ascending=False)
    picked = []

    def take(mask):
        for _, r in cand[mask].iterrows():
            if r.work_id not in [p.work_id for p in picked]:
                picked.append(r)
                return
    take(cand.has_E)
    take(cand.has_L)
    take(cand.has_E | cand.has_L)
    if len(picked) < 3:
        take(cand.has_N)
    W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'title', 'creator', 'article', 'author_article'])
    REL = pd.read_parquet(OUT / 'events_releases.parquet')
    out = []
    for r in picked:
        w = W[W.work_id == r.work_id].iloc[0]
        t = int(r.mi)
        why = []
        rel = REL[(REL.work_id == r.work_id) & (REL.e >= t + 1) & (REL.e <= t + 3)]
        for _, x in rel.iterrows():
            why.append(f"{x.type_group} adaptation '{x.en_title if isinstance(x.en_title, str) else x.label}' released {ym(x.e)}")
        if r.get('e_death', 0) > 0:
            why.append(f'author died in {ym(t)}')
        for c, txt in (('e_ann_event', 'a round anniversary of a linked event'), ('e_ann_birth', "a round anniversary of the author's birth"),
                       ('e_ann_death', "a round anniversary of the author's death")):
            if c in r and r[c] > 0:
                why.append(f'{txt} in {ym(t + 1)} to {ym(t + 3)}')
        if r.n_on > 0:
            why.append(f'on an NYT list in {ym(t)} ({int(r.n_weeks)} week{"s" if r.n_weeks > 1 else ""}' + (', entered that month)' if r.n_enter > 0 else ')'))
        lpages = linked_pages_bursting(r.work_id, t)
        for c in lcols:
            if r[c] > 0 and c.startswith('l_lt_'):
                lt, lag = c[5:-3], int(c[-1])
                why.append(f"{int(r[c])} linked {lt.replace('_', ' or ')} page{'s' if r[c] > 1 else ''} bursting in {ym(t - lag)}")
        out.append(dict(work_id=int(r.work_id), title=w.title, creator=w.creator, article=w.article, origin=ym(t), rank_full=int(r.rank_full),
                        rank_H=int(r.rank_H), M6=float(r.M6), L_t=float(r.L_t), L_next=float(r.L_next), score_full=float(r['s_' + full]),
                        score_H=float(r.s_H), reasons=why, bursting_linked_pages=lpages))
    return out


_LP_CACHE = {}


def linked_pages_bursting(work_id, t):
    """The linked pages of a work that burst in month t or t-1, with J1's rule (J1 header J10) recomputed for this work's pages from
    J1's view stores (J1's own loader, load_stores, and Test F's daily top-500 table).  Only J1's selected pages with views count."""
    if not (JL / 'links.parquet').exists() or not (JL / 'pages_wanted.parquet').exists():
        return []
    try:
        import importlib.util
        if 'j1' not in _LP_CACHE:
            spec = importlib.util.spec_from_file_location('j1_links', pathlib.Path(__file__).resolve().parent / 'j1_links.py')
            j1 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(j1)
            _LP_CACHE['j1'] = j1
            _LP_CACHE['L'] = pd.read_parquet(JL / 'links.parquet', columns=['work_id', 'link_type', 'page_title', 'category'])
            _LP_CACHE['sel'] = set(pd.read_parquet(JL / 'pages_wanted.parquet').query('selected').page_title)
        j1, Lk, sel = _LP_CACHE['j1'], _LP_CACHE['L'], _LP_CACHE['sel']
        lk = Lk[(Lk.work_id == work_id) & Lk.page_title.isin(sel)].drop_duplicates('page_title')
        if lk.empty:
            return []
        titles = list(lk.page_title)
        M, src, status, MI0, T = j1.load_stores(titles)
        TL, _ = T.top_long(set(titles))
        TL['mi'] = TL.date.dt.year * 12 + TL.date.dt.month - 1
        out = []
        for i, (ttl, lt, cat) in enumerate(zip(lk.page_title, lk.link_type, lk.category)):
            if status[i] != 200:
                continue
            for mm in (t, t - 1):
                j = mm - MI0
                if j < 6 or j >= M.shape[1]:
                    continue
                v, m6 = float(M[i, j]), float(np.median(M[i, j - 6:j]))
                top = bool(((TL.title == ttl) & (TL.mi == mm)).any())
                if (v >= 3 * m6 and v >= 3000) or top:
                    out.append(f"{ttl.replace('_', ' ')} ({lt}, {cat}; {ym(mm)}: {v:,.0f} views, {v / max(m6, 1):.1f} times its usual month{', in the daily top 500' if top else ''})")
        return out
    except Exception as ex:                                              # the examples must not stop the scoring
        log('linked pages of the example not read:', repr(ex))
        return []


# ====================================================================== report (data/reports/dir_j2_alerts.md), written from j2_results.json and the CSVs
NAMES = {'H': 'H (library history)', 'HW': 'H+W (+ own Wikipedia pages)', 'HWE': 'H+W+E (+ event calendar)', 'HWEN': 'H+W+E+N (+ NYT lists)',
         'HWENL': 'H+W+E+N+L (full: + linked pages)', 'placebo': 'Placebo (full, E and L dates moved 12 months earlier)',
         'placebo_E': 'Placebo E (H+W+E+N, E dates moved 12 months earlier)',
         'TestA_H_change': "Test A's H (change target, reference)", 'TestA_HW_change': "Test A's H+W (change target, reference)"}


def pc(x, d=1):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{100 * x:.{d}f}%'


def pt(x, d=1):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{100 * x:+.{d}f}'


def iv(lo, hi, d=1):
    return f'{100 * lo:+.{d}f} to {100 * hi:+.{d}f}'


def table(head, rows):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join(['---'] * len(head)) + ' |'] + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


def stage_report():
    res = json.loads((OUT / 'j2_results.json').read_text())
    T = pd.read_csv(OUT / 'measures.csv')
    DF = pd.read_csv(OUT / 'paired_differences.csv')
    CH = pd.read_csv(OUT / 'feature_on_surge_rates.csv')
    full = res['full_model']
    has_l = full == 'HWENL'
    pl = res.get('prep_l')
    pr = res['prep']

    def m(tgt, pop, model, ms='p20'):
        r = T[(T.target == tgt) & (T.population == pop) & (T.model == model) & (T.measure == ms)]
        return r.iloc[0] if len(r) else None

    def d(tgt, pop, a, b, ms='p20'):
        r = DF[(DF.target == tgt) & (DF.population == pop) & (DF.a == a) & (DF.b == b) & (DF.measure == ms)]
        return r.iloc[0] if len(r) else None

    def mtxt(r):
        return 'n/a' if r is None else f'{pc(r["mean"])} ({pc(r["lo"])} to {pc(r["hi"])})'

    def dtxt(r):
        return 'n/a' if r is None else f'{pt(r["mean"])} ({iv(r["lo"], r["hi"])})'

    ladder = ['H', 'HW', 'HWE', 'HWEN', 'placebo_E'] + (['HWENL', 'placebo'] if has_l else [])
    dec = res['decision']
    prim = dec['primary']
    plac = dec['placebo'] if isinstance(dec['placebo'], dict) else None
    b1e = res['base']['S1_not_yet']['rate_mean_over_months']
    b1 = res['base']['S1_all']['rate_mean_over_months']
    H_e, F_e = m('S1', 'not_yet', 'H'), m('S1', 'not_yet', full)
    H_a, F_a = m('S1', 'all', 'H'), m('S1', 'all', full)
    steps = [(a, b) for a, b in (('HW', 'H'), ('HWE', 'HW'), ('HWEN', 'HWE'), ('HWENL', 'HWEN')) if d('S1', 'not_yet', a, b) is not None]
    best_step = max(steps, key=lambda s: d('S1', 'not_yet', *s)['mean'])
    L = []
    P_ = L.append
    P_('# J2: one alert list from library history, Wikipedia, an event calendar, NYT lists and book-linked Wikipedia pages')
    P_('')
    P_(f"Khant Phyo Wai, 01323050. Run {res['run']}.")
    P_('')
    P_('**In plain words**')
    P_('')
    lines = plain_lines(res, m, d, full, has_l, b1e, b1, best_step)
    for i, s in enumerate(lines, 1):
        P_(f'{i}. {s}')
    P_('')
    P_(f"Addendum j (`{res['record']}`), sections features, models, targets, measures and decision. "
       "Choices the record leaves open: J1 to J14 in the header of `code/main_study/wiki_led/dirs/j2_alerts.py`, also logged in `prereg/DEVIATIONS.md` (Addendum j). "
       "The book-linked pages come from J1 (`data/reports/dir_j1_links.md`). Every interval is a 95% interval. Tables: `data/db/wiki_led/dirs/j_alerts/`.")
    if not has_l:
        P_('')
        P_('**Interim report: the linked-page bursts (L) are not in yet. The ladder stops at H+W+E+N, which stands in for the full model, and the placebo moves the E dates only (J15).**')
    P_('')
    P_("Terms. **Usual level** (M6): the median of a book's monthly loans over the six months to t (all formats, Test A). **Surge**: next month's loans at least 2 times the usual level "
       "and at least 5 loans more (Test A's arithmetic, ln(1 + loans) against ln(1 + M6)). **Not yet risen**: loans in month t below 1.5 times the usual level (same arithmetic), "
       f"{pc(pr['share_not_yet'])} of the rows. **Precision at 20**: the share of a month's top 20 that surge. **Coverage**: the share of a month's surges that are in the top 100. "
       "A month **t** is the month at whose end the list is made; every input is known by then.")
    P_('')
    P_('## 1. Rows, targets and inputs')
    P_('')
    P_(f"Rows: Test A's corrected rows (`test_a_rows_c.parquet`), {pr['rows']:,} book-months of the 7,747 works, origins 2016-03 to 2026-07; scored: {pr['scored_rows']:,} rows of "
       f"{res['n_months']['S1']} origin months ({res['months']['S1'][0]} to {res['months']['S1'][1]}), each test year fitted on the years before (Test A's walk-forward). "
       f"Check: the surge rule gives {pr['surges_next_month_all_rows']:,} next-month surges in all rows, the same as D2. Three-month target (surge in the largest of months t+1 to t+3): "
       f"{res['n_months']['S3']} origin months ({res['months']['S3'][0]} to {res['months']['S3'][1]}).")
    P_('')
    P_(f"Base rates (mean over months): next-month surge {pc(b1)} of all books and {pc(b1e)} of books not yet risen; three-month surge {pc(res['base']['S3_all']['rate_mean_over_months'])} and "
       f"{pc(res['base']['S3_not_yet']['rate_mean_over_months'])}. About {res['base']['S1_all']['rows_per_month']:,.0f} books are ranked each month, {res['base']['S1_not_yet']['rows_per_month']:,.0f} of them not yet risen.")
    P_('')
    P_("Inputs. **H**: the book's own loans (6 columns of Test A). **W**: the book's and author's own Wikipedia pages (18 columns of Test A, corrected). "
       "**E**: film or TV releases in the next three months (D2's dates), the author's death this month, and round anniversaries (25, 50, 75 ... years) in the next three months of "
       "dated events linked to the book and of the author's birth and death (J1). **N**: on an NYT list this month, entered a list this month, weeks on lists (D3). "
       "**L**: bursts of the book's linked Wikipedia pages this month and last month (a month with at least 3 times the page's usual views and 3,000 views, or a day in the top 500), "
       "by link type and by page kind (J1).")
    P_('')
    rows = []
    for c in ECOLS + NCOLS:
        r = CH[CH.feature == c]
        if len(r):
            r = r.iloc[0]
            rows.append([f'`{c}`', f'{int(r.rows_on):,}', f'{int(r.works_on):,}', pc(r.surge_rate_on), pc(r.surge_rate_on_not_yet)])
    if has_l:
        for c in ['l_all_a0'] + [f'l_lt_{x}_a0' for x in pl['link_types']] + [f'l_cat_{x}_a0' for x in pl['categories']]:
            r = CH[CH.feature == c]
            if len(r):
                r = r.iloc[0]
                rows.append([f'`{c}`', f'{int(r.rows_on):,}', f'{int(r.works_on):,}', pc(r.surge_rate_on), pc(r.surge_rate_on_not_yet)])
    P_(f"How often each input is on in the scored rows, and the next-month surge rate where it is on (base: {pc(CH.base.iloc[0])} of all rows, {pc(CH.base_not_yet.iloc[0])} of rows not yet risen). "
       "A check that the inputs carry signal (descriptive, not a test):")
    P_('')
    P_(table(['Input (on)', 'Rows', 'Books', 'Surge rate where on', 'Same, not yet risen'], rows))
    P_('')
    if has_l:
        cv = pl.get('j1_coverage') or {}
        if cv:
            P_(f"Linked pages (J1, file of {pl['file_mtime']}): {cv.get('pages_linked', 0):,} pages linked, {cv.get('pages_selected', 0):,} selected, {cv.get('pages_with_views', 0):,} with views used here; "
               f"{cv.get('works_with_views', 0):,} works have at least one linked page with views; download complete: {'yes' if cv.get('complete') else 'no (built from the pages stored by the cut, as the time rule says)'}.")
            P_('')
        P_(f"L covers burst months {pl['burst_months'][0]} to {pl['burst_months'][1]}; {pl['works_with_rows']:,} of the 7,747 works have linked pages with views in J1's file. "
           f"Placebo inputs (dates moved 12 months earlier) have complete data for origins up to {pl['placebo_full_data_origins_to']}; later they are missing.")
        P_('')
    P_('## 2. Main result: the ladder, next-month surges')
    P_('')
    for pop, title in (('not_yet', 'Books not yet risen at t (primary)'), ('all', 'All books')):
        P_(f'**{title}**')
        P_('')
        rows = []
        for nm in ladder + ['TestA_H_change']:
            rows.append([NAMES[nm], mtxt(m('S1', pop, nm)), mtxt(m('S1', pop, nm, 'ap')), mtxt(m('S1', pop, nm, 'cov100'))])
        P_(table(['Model', 'Precision at 20', 'Average precision', 'Coverage in top 100'], rows))
        P_('')
    P_('**Paired differences** (points, same months; interval):')
    P_('')
    rows = []
    prs = [('HW', 'H'), ('HWE', 'HW'), ('HWEN', 'HWE'), ('HWENL', 'HWEN'), (full, 'H'), ('placebo_E', 'H'), ('HWEN', 'placebo_E')] + ([('placebo', 'H'), ('HWENL', 'placebo')] if has_l else [])
    seen = set()
    for a, b in prs:
        if (a, b) in seen:
            continue
        seen.add((a, b))
        rows.append([f'{a} minus {b}', dtxt(d('S1', 'not_yet', a, b)), dtxt(d('S1', 'all', a, b)), dtxt(d('S1', 'not_yet', a, b, 'ap')), dtxt(d('S1', 'not_yet', a, b, 'cov100'))])
    P_(table(['Comparison', 'Precision at 20, not yet risen', 'Precision at 20, all', 'Average precision, not yet risen', 'Coverage, not yet risen'], rows))
    P_('')
    P_(f"**Decision (fixed in advance).** Primary: precision at 20 among books not yet risen, full model ({full}) minus H: {dtxt(d('S1', 'not_yet', full, 'H'))} points; "
       f"{'the interval is above 0: passed' if prim['passed'] else 'the interval is not above 0: not passed'}.")
    if plac:
        P_(f"Placebo rule: full minus the placebo model ({'E and L' if has_l else 'E'} dates moved 12 months earlier) on the same measure {dtxt(d('S1', 'not_yet', full, plac['placebo_model']))} points; "
           f"{'the interval is above 0, so the ' + ('event and linked-page' if has_l else 'event') + ' information counts' if plac['passed'] else 'the interval is not above 0, so by the rule fixed in advance the ' + ('event and linked-page' if has_l else 'event') + ' information does not count'}"
           f"{' (the point gain is above the placebo)' if (not plac['passed'] and plac['point_gain_exceeds']) else ''}.")
        rr = DF[(DF.target == 'S1') & (DF.population == 'not_yet') & (DF.a == full) & (DF.b == plac['placebo_model']) & DF.measure.str.startswith('p20_origins_to')]
        if len(rr):
            rr = rr.iloc[0]
            P_(f"Check on the origins with complete placebo data ({rr.measure.split('_to_')[1]} and before, {int(rr.months)} months): full minus placebo {pt(rr['mean'])} ({iv(rr.lo, rr.hi)}).")
        if has_l and d('S1', 'not_yet', 'HWEN', 'placebo_E') is not None:
            r2 = d('S1', 'not_yet', 'HWEN', 'placebo_E')
            P_(f"Beside it (J15, the interim test): H+W+E+N minus its E-only placebo {pt(r2['mean'])} ({iv(r2.lo, r2.hi)}). The interim report read this as the event information counting; "
               "with L added, the record's full model and placebo decide, and they do not pass the rule.")
    else:
        P_('Placebo rule: not tested (no placebo model scored).')
    P_('')
    if has_l:
        P_('## 3. Each kind of linked page added alone to H+W (next month)')
        P_('')
        rows = []
        for c in pl['categories']:
            nm = f'HW+L_{c}'
            note = {'event': ' (note a)', 'place': ' (note b)', 'person': ' (note b)'}.get(c, '')
            rows.append([f'H+W + {c.replace("_", " or ")} pages{note}', mtxt(m('S1', 'not_yet', nm)), dtxt(d('S1', 'not_yet', nm, 'HW')), dtxt(d('S1', 'all', nm, 'HW')), dtxt(d('S1', 'not_yet', nm, 'HW', 'ap'))])
        rows.insert(0, ['H+W (reference)', mtxt(m('S1', 'not_yet', 'HW')), '', '', ''])
        P_(table(['Model', 'Precision at 20, not yet risen', 'Minus H+W, not yet risen', 'Minus H+W, all', 'Average precision minus H+W, not yet risen'], rows))
        P_('')
        P_("Notes from J1 (the fixed inputs were not changed because of them). (a) The event kind follows Wikidata's occurrence class, which also holds concepts such as "
           "marriage, love, sleep and crime: of 148 event items that Test F's AI also sorted, it called 88 events and 54 concepts (`ai_kind` in `links.parquet`). "
           "(b) The top-500 part of the burst rule saturates for very popular pages (China, New York City, World War II and Donald Trump burst in all 129 months), so for big "
           "place and person pages a burst says little; place pages burst in 35% of their months and person pages in 26%.")
        P_('')
    P_(f"## {4 if has_l else 3}. Surges within three months (models refitted on that target)")
    P_('')
    rows = []
    for nm in ladder:
        rows.append([NAMES[nm], mtxt(m('S3', 'not_yet', nm)), mtxt(m('S3', 'all', nm)), mtxt(m('S3', 'not_yet', nm, 'cov100'))])
    P_(table(['Model', 'Precision at 20, not yet risen', 'Precision at 20, all', 'Coverage in top 100, not yet risen'], rows))
    P_('')
    rows = []
    for a, b in prs:
        r1 = d('S3', 'not_yet', a, b)
        if r1 is not None:
            rows.append([f'{a} minus {b}', dtxt(r1), dtxt(d('S3', 'all', a, b))])
    P_(table(['Comparison', 'Precision at 20, not yet risen', 'Precision at 20, all'], rows))
    P_('')
    sec = 5 if has_l else 4
    if 'importance_share_full_S1' in res:
        P_(f'## {sec}. What the full model leans on')
        P_('')
        sh = res['importance_share_full_S1']
        P_('Share of the split gain by input group (next-month model, mean over the 8 test years): ' + ', '.join(f'{g} {pc(sh.get(g, 0))}' for g in ['H', 'W', 'E', 'N', 'L'] if g in sh) + '. '
           'Top inputs: ' + ', '.join(f'`{k}` {pc(v)}' for k, v in list(res['importance_top15_full_S1'].items())[:10]) + '.')
        P_('')
        sec += 1
    P_(f'## {sec}. Three books the full model listed and H did not')
    P_('')
    P_("Picked by the rule fixed in advance (J14): books in the full model's top 20 among books not yet risen, not in H's top 20 of the same month, that surged next month; "
       "first the highest-scored one with an event input on, then one with a linked-page burst, then the next with either. The reasons are the inputs that were on at t; "
       "they show what the list contains, not proof of why the model ranked the book high.")
    P_('')
    for i, e in enumerate(res['examples'], 1):
        P_(f"{i}. **{e['title']}** ({e['creator']}), list made at the end of {e['origin']}: rank {e['rank_full']} in the full model's list, rank {e['rank_H']} in H's. "
           f"Usual level {e['M6']:.0f} loans a month, {e['L_t']:.0f} in month t, {e['L_next']:.0f} the next month. Inputs on: " + '; '.join(e['reasons']) +
           ('. Linked pages that burst: ' + ', '.join(e['bursting_linked_pages'][:6]) if e['bursting_linked_pages'] else '') + '.')
    if not res['examples']:
        P_('No book met the rule.')
    elif has_l:
        P_('')
        P_("A page listed at about its usual level (1.0 to 1.2 times) counts as bursting only through the daily top 500 (note b in section 3), as World War II and The Holocaust do above.")
    P_('')
    sec += 1
    P_(f'## {sec}. Limits')
    P_('')
    P_("- Wikidata dates (releases, deaths, linked events) may have been entered after the event, so the calendar is a little better than what was known at the time (as in D2).")
    P_("- The placebo inputs at the last origins need months after the data end and are missing there; the check on the origins with complete placebo data is given above.")
    P_("- NYT matches cover 2,892 of the 7,747 works (D3); other works count as never listed.")
    P_("- One library (Seattle). The models are Test A's, not tuned; a tuned model might use the new inputs better or worse.")
    if has_l:
        P_("- L: each (book, page) pair counts once, under its first link type (J1). The event kind includes concepts that Wikidata files under occurrence, and very popular place and "
           "person pages burst almost every month through the top-500 rule (notes a and b in section 3).")
    P_('')
    P_('## Files')
    P_('')
    P_("`data/db/wiki_led/dirs/j_alerts/`: `measures.csv` (every model, target, population and measure), `paired_differences.csv`, `feature_on_surge_rates.csv`, `preds_S1_*.parquet` and "
       "`preds_S3_*.parquet` (scores per book-month), `importance_*.json`, `j2_results.json`, `feats_*.parquet` (inputs), `prep_info.json`, `prep_l_info.json`.")
    (REP / 'dir_j2_alerts.md').write_text('\n'.join(L) + '\n')
    log('report written', REP / 'dir_j2_alerts.md')


def plain_lines(res, m, d, full, has_l, b1e, b1, best_step):
    """The five plain-language lines, from the numbers."""
    He, Fe = m('S1', 'not_yet', 'H'), m('S1', 'not_yet', full)
    Ha, Fa = m('S1', 'all', 'H'), m('S1', 'all', full)
    dp = d('S1', 'not_yet', full, 'H')
    prim = res['decision']['primary']
    out = []
    out.append(f"Among books whose borrowing had not yet started to climb, the library model alone (H) put {pc(He['mean'])} surging books in its monthly top 20 "
               f"(against a base rate of {pc(b1e)}); the combined model with Wikipedia, the event calendar{', NYT lists and linked pages' if has_l else ' and NYT lists'} put {pc(Fe['mean'])}, "
               f"a difference of {pt(dp['mean'])} points (interval {iv(dp['lo'], dp['hi'])}): {'a clear gain' if prim['passed'] else 'not a clear gain'} by the test fixed in advance.")
    steps = {s: d('S1', 'not_yet', *s) for s in (('HW', 'H'), ('HWE', 'HW'), ('HWEN', 'HWE'), ('HWENL', 'HWEN')) if d('S1', 'not_yet', *s) is not None}
    sname = {('HW', 'H'): "the book's own Wikipedia pages", ('HWE', 'HW'): 'the event calendar', ('HWEN', 'HWE'): 'the NYT lists', ('HWENL', 'HWEN'): 'the linked pages'}
    out.append('Step by step (points of precision at 20, books not yet risen): ' + '; '.join(
        f"{sname[s]} {pt(r['mean'])} ({iv(r['lo'], r['hi'])})" for s, r in steps.items()) + '.')
    if isinstance(res['decision']['placebo'], dict):
        pl = res['decision']['placebo']
        what = 'event and linked-page date' if has_l else 'event date'
        out.append(f"The cleanest test of the dates is the placebo, the same model with every {what} moved 12 months earlier (same inputs in the same order, so only the timing differs): it scored {pc(m('S1', 'not_yet', pl['placebo_model'])['mean'])}, and the real dates beat it by "
                   f"{pt(pl['mean'])} points (interval {iv(pl['lo'], pl['hi'])}), so the timing of {'events and linked-page bursts' if has_l else 'the events'} {'adds' if pl['passed'] else 'does not clearly add'} information by the rule fixed in advance." +
                   (f" Most of the gain over H does not depend on the dates: the placebo itself is {pt(d('S1', 'not_yet', pl['placebo_model'], 'H')['mean'])} points above H, from the book's own Wikipedia pages and the NYT lists, which it keeps."
                    + (f" For surges within three months the real dates do beat the placebo ({pt(d('S3', 'not_yet', full, pl['placebo_model'])['mean'])}, {iv(d('S3', 'not_yet', full, pl['placebo_model'])['lo'], d('S3', 'not_yet', full, pl['placebo_model'])['hi'])}; a secondary measure)."
                       if d('S3', 'not_yet', full, pl['placebo_model'])['lo'] > 0 else '') if has_l else ''))
    else:
        out.append('No placebo model was scored, so the event information is not yet tested against moved dates.')
    s3 = d('S3', 'not_yet', full, 'H')
    if has_l:
        cats = res.get('prep_l', {}).get('categories', [])
        cd = [(c, d('S1', 'not_yet', f'HW+L_{c}', 'HW')) for c in cats]
        cd = [(c, r) for c, r in cd if r is not None]
        out.append('Each kind of linked page added alone to H+W (points of precision at 20, books not yet risen): ' + '; '.join(
            f"{c.replace('_', ' or ')} {pt(r['mean'])} ({iv(r['lo'], r['hi'])})" for c, r in cd) +
            f". Over three months the combined model minus H is {pt(s3['mean'])} points ({iv(s3['lo'], s3['hi'])}) among books not yet risen.")
        out.append(f"Among all books, most of every model's top 20 are books already climbing (H {pc(Ha['mean'])}, combined {pc(Fa['mean'])} surge next month, base rate {pc(b1)}). "
                   "Limit: Wikidata dates may have been entered after the event, so the calendar is a little better than what was known at the time; one library (Seattle), Test A's untuned models.")
    else:
        out.append(f"Among all books, most of every model's top 20 are books already climbing: H {pc(Ha['mean'])}, combined {pc(Fa['mean'])} surge next month "
                   f"(base rate {pc(b1)}); over three months the combined model minus H is {pt(s3['mean'])} points ({iv(s3['lo'], s3['hi'])}) among books not yet risen.")
        out.append('Limit: event dates come from Wikidata and may have been entered after the event, so the calendar is a little better than what was known at the time; '
                   'one library (Seattle), and Test A\'s untuned models.')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['prep', 'prep_ann', 'prep_l', 'fit', 'score', 'report'])
    ap.add_argument('--models', nargs='*', default=[])
    ap.add_argument('--targets', nargs='*', default=['S1', 'S3'])
    a = ap.parse_args()
    if a.stage == 'prep':
        stage_prep()
    elif a.stage == 'prep_ann':
        stage_prep_ann()
    elif a.stage == 'prep_l':
        stage_prep_l()
    elif a.stage == 'fit':
        stage_fit(a.models, a.targets)
    elif a.stage == 'score':
        stage_score()
    elif a.stage == 'report':
        stage_report()
    log('peak MB', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20))
