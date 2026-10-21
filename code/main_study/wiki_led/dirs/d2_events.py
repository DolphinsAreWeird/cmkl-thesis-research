#!/usr/bin/env python3
"""D2 of addendum i (event calendar): do known events (a film or television adaptation's release, the author's death, a dated award)
let us flag books whose borrowing will jump, before or as it happens, better than the library's own history?

Settings: prereg/addenda_wiki_led/2026-10-22_i_directions.json, section D2_event_calendar (read-only; SHA-256 checked below).
Exploratory and descriptive.  No model is fitted; no download is made; the inputs exist.  Every interval is a 95% interval.
Run from handoff/code:   ../.venv/bin/python main_study/wiki_led/dirs/d2_events.py      (about 30 seconds, light; plain pandas and numpy)
Outputs: data/db/wiki_led/dirs/d2_events/ (tables, d2_results.json, figure) and the report data/reports/dir_d2_events.md
(the report is written by this script from the same numbers).

Inputs
  events_long.parquet   one row per dated event (made by 71_wikidata_events.py from Wikidata on 20 Oct 2026): deaths (P570 of the author item),
                        awards (P166 with a point-in-time date, book or author item), adaptation items with type group (film, tv, other) and the
                        release month (earliest best-rank P577 or P580 date at month precision or finer).  Only film and tv adaptations are used,
                        as in 71.  Year-only dates cannot be placed in a month and are not used (95% of dated award statements are year-only).
  events.parquet        only for each work's book item and author item.  Its ad_rel flag (a release in t-1, t or t+1) is NOT used: the addendum
                        asks for releases in t+1..t+3, which are built here from events_long.  Its ad_rel_public column is empty on purpose;
                        the "public" check is computed here as in 80_improve_v2.py: the adaptation's English article (events_long en_title, spaces
                        to underscores) has data (adaptation_page_features.parquet, has_data: first week with views ended by the end of t) at origin t.
  loans                 monthly loans per work summed over formats, exactly as 10c_test_a.py builds them (data/db/study2r/counts_work.parquet; months
                        before a work's first loan are missing; the library-wide excluded months of the benchmark, data/db/study3/demand_panel.parquet
                        month_ok: 2020-04 to 2020-09, 2024-05 to 2024-07, 2025-08, are missing).
  Test A                test_a_rows_c.parquet (all origins 2016-03 to 2026-07) and test_a_preds_c.parquet (scored origins 2019-01 to 2026-07, with the
                        library-history model Hlgbm_D = "H").

Fixed by the addendum: the event types, the window (months -3 to +12), the baseline "six-month median before the event", matching within origin
month and loan decile against works without an event, rose = 1.5 times M6, surged = 2 times M6 and 5 loans or more, the alert lists
(adaptation release in t+1..t+3; deaths and awards in month t), the comparison with the base rate and with H's top picks, adding the alert
works to H's top 20, and the improvement round v2 reported beside.

Choices the addendum leaves open (made here before any result was looked at):
  C1 Rose and surged use Test A's arithmetic: D = ln(1 + L) - ln(1 + M6) in float32, rose = D >= ln 1.5, surged = D >= ln 2 and L - M6 >= 5
     (so the rule is the same as Test A's stored D and Sg, including rows exactly on the boundary).
  C2 Event study baseline: M6 = median of the six months t0-5..t0 with t0 = e-4, so every window month -3..+12 lies after the baseline and the
     months -3..-1 show any rise before the event (trailers, premieres abroad).  A work is eligible at t0 when it had a loan in the 12 months to
     t0 (Test A's "present" rule) and at least 3 of the 6 baseline months are available (not excluded, after the first loan).
  C3 Loan decile = decile of M6 among all eligible works at t0 (average ranks, so tied works share a decile).  Matched controls = eligible works
     in the same t0 and decile with no dated event of any type (film or tv release, author death, dated award) in months t0-5 to e+12.  A window
     month after 2026-08 or excluded is missing for event and controls alike.  Excess = event flag minus the mean flag of its controls,
     averaged over events.  The control means are treated as fixed in the bootstrap (they rest on hundreds of works per cell).
  C4 Events from 2006-07 (the first event month with 12 months of loans before t0) to 2026-08.  A work's events of one type in the same month
     count once (film wins over tv when both).  All events are kept, also several per work (the bootstrap resamples works).
  C5 Intervals: 2,000 bootstrap draws over works (numpy default_rng(20261020)); for deaths also over authors, because one death touches all
     of an author's works.  Month-level comparisons with H (top 20, swap) use Test A's circular blocks of 3 scored months, 2,000 draws.
  C6 Placebo: every event moved 24 months earlier, dropping fake events whose work has a real event in the fake baseline or window; the same
     matching and measures.  The excess there should be near 0.
  C7 Prediction outcome: "rose (surged) in t+1..t+3" = rose (surged) in at least one available month of t+1..t+3, each month against M6 at t;
     only origins with t+3 <= 2026-08 (2019-01 to 2026-05).  The next-month outcome of Test A (t+1, all 78 scored months) is also reported.
  C8 Alert lists at origin t: adapt (a film or tv release in t+1..t+3), adapt_public (same, and the adaptation's article already had views by the
     end of t), death (author died in month t), award (dated award in month t), any (union of adapt, death, award); extra, not in the addendum:
     adapt_now (release in month t, the "as it happens" case).  Measures: share rose and surged, the base rate of the same months (each alert
     row against all rows of its month), the excess over works of the same month and H-score decile (does the alert add to H?), and H's top-20
     share.  Checks: the same with hundredths of H's score, and alert works against the other works by band of H's score.
  C9 Swap into H's top 20: per month, the alert works ordered by H's score come first (at most 20), then H's own picks fill the list to 20.
     A second version swaps in at most 5 alert works (the five with the highest H score replace H's places 16 to 20).  Reported for all months
     (unchanged lists count) and for the months where the list changed.
  C10 Coverage: among Test A rows (2016-03 to 2026-07) with a surge next month (month s = t+1), the share with a dated event of the work or its
     author in months s-2..s+2, against the same share among all rows (chance) and with the events moved 24 months earlier.  Precision = share
     of alert rows that surged in t+1..t+3 (all Test A origins 2016-03 to 2026-05).
  C11 Added at 03:24 after the first run had been seen (so not fixed in advance): H's top 20 turned out to be mostly books that had
     already risen in month t (92% rose next month), so the alert lists, H's top 20 and the swap are also compared among the books that have
     not risen yet at t (ln(1 + L_t) - ln(1 + M6) < ln 1.5), the "early list" of the improvement round v2.  Both versions are reported.
Limit (in the report): Wikidata entries may have been added or corrected after the event, so today's calendar is not exactly what one
would have known at t.  The public check covers adaptations in part (the article existed and had views); deaths and awards are known from their
month.  The release month is the earliest dated release (often a festival premiere or the first broadcast), not always the US release.
"""
import sys, json, time, pathlib, hashlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore', category=RuntimeWarning)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))          # code/
from config import D

D = pathlib.Path(D)
ROOT = D.parent
IN = D / 'db' / 'wiki_led'
OUT = IN / 'dirs' / 'd2_events'
OUT.mkdir(parents=True, exist_ok=True)
REP = D / 'reports'
ADD_I = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-22_i_directions.json'
assert hashlib.sha256(ADD_I.read_bytes()).hexdigest() == '5659fbc6e63f5c477603564971dd9e4cb82bfcda57d1e9f1ae03915460ddb58e', 'addendum i changed'
SET = json.loads(ADD_I.read_text())['D2_event_calendar']
SEED = 20261020
NB = 2000
T0 = time.time()
LN15, LN2 = np.log(1.5), np.log(2)
KS = np.arange(-3, 13)                    # relative months of the event window
WINDOWS = {'-3 to -1': (-3, -1), '0 to 2': (0, 2), '3 to 5': (3, 5), '6 to 12': (6, 12)}
TYPES = ['adaptation', 'film', 'tv', 'death', 'award']


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:5.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym(mi):
    mi = int(mi)
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def dflag(L, M6):
    """Test A's arithmetic (float32): D, rose, surged.  NaN L gives D NaN and both flags False."""
    L32 = np.asarray(L, dtype=np.float32)
    M32 = np.asarray(M6, dtype=np.float32)
    Dv = np.log1p(L32) - np.log1p(M32)
    with np.errstate(invalid='ignore'):
        rose = Dv >= LN15
        surge = (Dv >= LN2) & ((L32 - M32) >= 5)
    return Dv, rose, surge


# ====================================================================== loans panel (as 10c_test_a.py)
P = pd.read_parquet(D / 'db' / 'study3' / 'demand_panel.parquet', columns=['format', 'mi', 'month_ok']).drop_duplicates(['format', 'mi'])
EXCL = {int(m) for m in P.loc[~P.month_ok, 'mi'] if m >= mi_of('2015-01')}
assert {mi_of('2020-05'), mi_of('2024-06')} <= EXCL
assert not {int(m) for m in P.loc[~P.month_ok, 'mi'] if m < mi_of('2015-01')}, 'excluded months before 2015 exist: decide how to treat them'
W = pd.read_parquet(D / 'db' / 'study2r' / 'works.parquet', columns=['work_id', 'title', 'creator', 'item', 'article', 'author_article'])
C = pd.read_parquet(D / 'db' / 'study2r' / 'counts_work.parquet')
Lc = C.groupby(['work_id', 'mi']).y.sum()
first = Lc[Lc > 0].reset_index().groupby('work_id').mi.min()
MI = np.arange(mi_of('2005-04'), mi_of('2026-08') + 1)
LAST = int(MI[-1])
LW = Lc.unstack('mi').reindex(columns=MI).fillna(0).astype(np.float32).reindex(W.work_id).fillna(0)
A = LW.to_numpy(dtype=np.float32).copy()
f_arr = first.reindex(W.work_id).to_numpy(dtype=float)
A[(MI[None, :] < f_arr[:, None])] = np.nan                                     # before the first loan: not in the collection
ex_mask = np.isin(MI, sorted(EXCL))
Aex = A.copy()
Aex[:, ex_mask] = np.nan                                                        # excluded months are missing
NW = len(W)
widx = pd.Series(np.arange(NW), index=W.work_id.to_numpy())
log('loans panel', A.shape, 'months', ym(MI[0]), 'to', ym(LAST), 'excluded', [ym(m) for m in sorted(EXCL)])


def col(m):
    return int(m) - int(MI[0])


# ====================================================================== events
EV = pd.read_parquet(IN / 'events.parquet', columns=['work_id', 'item', 'author_item']).drop_duplicates('work_id')
EL = pd.read_parquet(IN / 'events_long.parquet')
EV = EV[EV.work_id.isin(widx.index)]
ad = EL[(EL.event == 'adaptation') & EL.type_group.isin(['film', 'tv']) & EL.mi_event.notna()].copy()
ad = ad.merge(EV[['work_id', 'item']], left_on='subject', right_on='item')
ad['e'] = ad.mi_event.astype(int)
ad['page'] = ad.en_title.astype('string').str.replace(' ', '_')
ADP = ad[['work_id', 'e', 'type_group', 'detail', 'label', 'en_title', 'page', 'date']].copy()        # one row per work, adaptation item
de = EL[(EL.event == 'death') & EL.mi_event.notna()].merge(EV[['work_id', 'author_item']], left_on='subject', right_on='author_item')
de['e'] = de.mi_event.astype(int)
aw = EL[(EL.event == 'award') & EL.mi_event.notna()].copy()
aw_b = aw[aw.subject_kind == 'book'].merge(EV[['work_id', 'item']], left_on='subject', right_on='item')
aw_a = aw[aw.subject_kind == 'author'].merge(EV[['work_id', 'author_item']], left_on='subject', right_on='author_item')
awx = pd.concat([aw_b, aw_a], ignore_index=True)
awx['e'] = awx.mi_event.astype(int)

ad1 = ADP.sort_values(['work_id', 'e', 'type_group']).groupby(['work_id', 'e'], as_index=False).agg(
    sub=('type_group', 'first'), label=('label', 'first'), en_title=('en_title', 'first'), n_items=('detail', 'nunique'))   # 'film' < 'tv'
EVT = pd.concat([
    ad1.assign(type='adaptation', cluster=ad1.work_id.astype(str))[['work_id', 'e', 'type', 'sub', 'label', 'cluster']],
    de.drop_duplicates(['work_id', 'e']).assign(type='death', sub='death', label=None, cluster=lambda x: x.author_item)[['work_id', 'e', 'type', 'sub', 'label', 'cluster']],
    awx.sort_values('label').drop_duplicates(['work_id', 'e']).assign(type='award', sub='award', cluster=lambda x: x.work_id.astype(str))[['work_id', 'e', 'type', 'sub', 'label', 'cluster']],
], ignore_index=True)
EVT['wi'] = EVT.work_id.map(widx).astype(int)
log('dated events (any year):', EVT.groupby('type').size().to_dict())

# any real dated event per work and month (for the control rule and the coverage measure), on an extended month grid
G0, G1 = mi_of('1990-01'), mi_of('2030-12')
GRID = np.arange(G0, G1 + 1)
EANY = np.zeros((NW, len(GRID)), np.int16)
ev_in = EVT[(EVT.e >= G0) & (EVT.e <= G1)]
np.add.at(EANY, (ev_in.wi.to_numpy(), (ev_in.e - G0).to_numpy()), 1)
ECUM = np.concatenate([np.zeros((NW, 1), np.int32), np.cumsum(EANY, axis=1, dtype=np.int32)], axis=1)


def n_events(wi, a, b):
    """number of real dated events of works wi in months a..b (arrays or scalars)."""
    n = len(GRID)
    ia = np.clip(np.asarray(a) - G0, 0, n)
    ib = np.clip(np.asarray(b) - G0 + 1, 0, n)
    return np.maximum(ECUM[wi, ib] - ECUM[wi, ia], 0)


# ====================================================================== event study
def baseline(t0):
    """M6, eligibility and loan decile of every work at t0 (C2, C3)."""
    j = col(t0)
    w6 = Aex[:, j - 5:j + 1]
    navail = np.sum(~np.isnan(w6), axis=1)
    with np.errstate(all='ignore'):
        M6 = np.nanmedian(w6, axis=1)
        present = np.nansum(A[:, j - 11:j + 1], axis=1) > 0
    elig = present & (navail >= 3) & ~np.isnan(M6)
    dec = np.full(NW, -1, int)
    if elig.sum() >= 10:
        from scipy.stats import rankdata
        r = rankdata(M6[elig], method='average')
        dec[elig] = np.minimum((10 * (r - 0.5) / elig.sum()).astype(int), 9)
    return M6, elig, dec


def window_flags(e, M6):
    """D, rose, surged of every work at months e-3..e+12 against M6 (works x 16); missing months NaN / False, plus the availability mask."""
    ms = e + KS
    ok = (ms <= LAST) & ~np.isin(ms, sorted(EXCL)) & (ms >= MI[0])
    Lm = np.full((NW, len(KS)), np.nan, np.float32)
    Lm[:, ok] = Aex[:, [col(m) for m in ms[ok]]]
    Dv, rose, surge = dflag(Lm, M6[:, None])
    avail = ~np.isnan(Lm)
    return Dv, rose, surge, avail


def event_study(evt, label):
    """One row per event with its flags and the mean flags of its matched controls (arrays events x 16)."""
    evt = evt[(evt.e >= mi_of('2006-07')) & (evt.e <= LAST)].copy()
    out = []
    for e, g in evt.groupby('e'):
        t0 = e - 4
        M6, elig, dec = baseline(t0)
        Dv, rose, surge, avail = window_flags(e, M6)
        clean = n_events(np.arange(NW), t0 - 5, e + 12) == 0
        ctrl = elig & clean
        wi = g.wi.to_numpy()
        keep = elig[wi]
        g = g[keep]
        wi = wi[keep]
        if not len(g):
            continue
        cm = {}
        for d in np.unique(dec[wi]):
            cmask = ctrl & (dec == d)
            n_c = cmask.sum()
            a = avail[cmask]
            with np.errstate(all='ignore'):
                cm[d] = dict(n=n_c, rose=np.where(a.sum(0) > 0, (rose[cmask] & a).sum(0) / a.sum(0), np.nan),
                             surge=np.where(a.sum(0) > 0, (surge[cmask] & a).sum(0) / a.sum(0), np.nan),
                             D=np.nanmean(np.where(a, Dv[cmask], np.nan), axis=0))
        for r, w in zip(g.itertuples(), wi):
            c = cm[dec[w]]
            if c['n'] < 20:                                                  # too few controls in the cell: not used (counted)
                out.append(dict(r._asdict(), t0=t0, M6=float(M6[w]), dec=int(dec[w]), n_ctrl=int(c['n']), used=False))
                continue
            a = avail[w]
            out.append(dict(r._asdict(), t0=t0, M6=float(M6[w]), dec=int(dec[w]), n_ctrl=int(c['n']), used=True,
                            avail=a, rose=np.where(a, rose[w], np.nan), surge=np.where(a, surge[w], np.nan), D=np.where(a, Dv[w], np.nan),
                            c_rose=np.where(a, c['rose'], np.nan), c_surge=np.where(a, c['surge'], np.nan), c_D=np.where(a, c['D'], np.nan)))
    X = pd.DataFrame(out)
    log(f'event study {label}: events {len(X)}, used {int(X.used.sum()) if len(X) else 0}')
    return X


def boot_excess(X, clusters, rng):
    """excess (event minus control) by relative month and window, with cluster bootstrap intervals."""
    U = X[X.used]
    res = {}
    if not len(U):
        return res
    cl = pd.factorize(U[clusters])[0]
    nc = cl.max() + 1
    draws = rng.integers(0, nc, size=(NB, nc))
    cnt = np.stack([np.bincount(d, minlength=nc) for d in draws]).astype(float)         # NB x clusters
    for meas in ('rose', 'surge', 'D'):
        ev = np.stack(U[meas].to_numpy())                 # events x 16
        cv = np.stack(U['c_' + meas].to_numpy())
        ok = ~np.isnan(ev) & ~np.isnan(cv)
        diff = np.where(ok, ev - cv, 0.0)
        S = np.zeros((nc, len(KS)))
        N = np.zeros((nc, len(KS)))
        E_ = np.zeros((nc, len(KS)))
        Cc = np.zeros((nc, len(KS)))
        np.add.at(S, cl, diff)
        np.add.at(N, cl, ok.astype(float))
        np.add.at(E_, cl, np.where(ok, ev, 0.0))
        np.add.at(Cc, cl, np.where(ok, cv, 0.0))
        bym = []
        bS, bN = cnt @ S, cnt @ N
        for k in range(len(KS)):
            n = N[:, k].sum()
            est = S[:, k].sum() / n if n else np.nan
            with np.errstate(all='ignore'):
                b = bS[:, k] / bN[:, k]
            bym.append(dict(k=int(KS[k]), n_events=int(n), event=float(E_[:, k].sum() / n) if n else np.nan,
                            control=float(Cc[:, k].sum() / n) if n else np.nan, excess=float(est),
                            lo=float(np.nanpercentile(b, 2.5)), hi=float(np.nanpercentile(b, 97.5))))
        win = {}
        for wn, (a, b_) in WINDOWS.items():
            ks = (KS >= a) & (KS <= b_)
            s, n = S[:, ks].sum(1), N[:, ks].sum(1)
            e_, c_ = E_[:, ks].sum(1), Cc[:, ks].sum(1)
            bb = (cnt @ s) / (cnt @ n)
            win[wn] = dict(n_event_months=int(n.sum()), event=float(e_.sum() / n.sum()), control=float(c_.sum() / n.sum()),
                           excess=float(s.sum() / n.sum()), lo=float(np.nanpercentile(bb, 2.5)), hi=float(np.nanpercentile(bb, 97.5)))
        res[meas] = dict(by_month=bym, windows=win)
    res['n'] = dict(events=int(len(U)), works=int(U.work_id.nunique()), clusters=int(nc), clusters_by=clusters,
                    events_dropped_few_controls=int((~X.used).sum()), first_event=ym(U.e.min()), last_event=ym(U.e.max()),
                    median_controls=float(U.n_ctrl.median()))
    return res


rng = np.random.default_rng(SEED)
ES, ESP, XS = {}, {}, {}
sel = {'adaptation': EVT.type == 'adaptation', 'film': (EVT.type == 'adaptation') & (EVT['sub'] == 'film'),
       'tv': (EVT.type == 'adaptation') & (EVT['sub'] == 'tv'), 'death': EVT.type == 'death', 'award': EVT.type == 'award'}
for tname in TYPES:
    X = event_study(EVT[sel[tname]], tname)
    XS[tname] = X
    ES[tname] = boot_excess(X, 'work_id', rng)
    if tname == 'death':
        ES['death_by_author'] = boot_excess(X, 'cluster', rng)
    # placebo C6: events moved 24 months earlier; drop fake events whose work has a real event in the fake baseline or window
    F = EVT[sel[tname]].copy()
    F['e'] = F.e - 24
    F = F[(F.e >= mi_of('2006-07')) & (F.e <= LAST)]
    F = F[n_events(F.wi.to_numpy(), (F.e - 9).to_numpy(), (F.e + 12).to_numpy()) == 0]
    ESP[tname] = boot_excess(event_study(F, tname + ' placebo'), 'work_id', rng)


def flat_es(E, kind):
    rows = []
    for t, r in E.items():
        if not r:
            continue
        for meas in ('rose', 'surge', 'D'):
            for x in r[meas]['by_month']:
                rows.append(dict(kind=kind, type=t, measure=meas, **x))
    return rows


def flat_win(E, kind):
    rows = []
    for t, r in E.items():
        if not r:
            continue
        for meas in ('rose', 'surge', 'D'):
            for wn, x in r[meas]['windows'].items():
                rows.append(dict(kind=kind, type=t, measure=meas, window=wn, **x))
    return rows


ESM = pd.DataFrame(flat_es(ES, 'real') + flat_es(ESP, 'placebo'))
ESW = pd.DataFrame(flat_win(ES, 'real') + flat_win(ESP, 'placebo'))
ESM.to_csv(OUT / 'event_study_by_month.csv', index=False)
ESW.to_csv(OUT / 'event_study_windows.csv', index=False)
evt_used = pd.concat([X.assign(study=t) for t, X in XS.items() if len(X)], ignore_index=True)
evt_used = evt_used[['study', 'work_id', 'e', 'type', 'sub', 'label', 'cluster', 't0', 'M6', 'dec', 'n_ctrl', 'used']].copy()
evt_used['event_month'] = evt_used.e.map(ym)
evt_used.to_parquet(OUT / 'event_study_events.parquet', index=False)
log('event study written')

# ====================================================================== prediction test (scored months of Test A, H = Hlgbm_D)
PR = pd.read_parquet(IN / 'test_a_preds_c.parquet', columns=['work_id', 'mi', 'year', 'D', 'Sg', 'L_t', 'M6', 'Hlgbm_D', 'HWlgbm_D', 'Wlgbm_D'])
RW = pd.read_parquet(IN / 'test_a_rows_c.parquet', columns=['work_id', 'mi', 'L_t', 'L_next', 'M6', 'D', 'Sg'])


def add_outcomes(R):
    """rose1 / surge1 (Test A, t+1) and rose3 / surge3 (any available month of t+1..t+3), C1 and C7."""
    R = R.copy()
    wi = R.work_id.map(widx).to_numpy()
    R['rose1'] = (R.D >= LN15).astype(int)
    R['surge1'] = R.Sg.astype(int)
    r3 = R.rose1.to_numpy().astype(bool)
    s3 = R.surge1.to_numpy().astype(bool)
    for k in (2, 3):
        m = R.mi.to_numpy() + k
        Lk = np.full(len(R), np.nan, np.float32)
        okm = m <= LAST
        Lk[okm] = Aex[wi[okm], m[okm] - MI[0]]
        _, rk, sk = dflag(Lk, R.M6.to_numpy())
        r3 |= rk
        s3 |= sk
    R['rose3'] = r3.astype(int)
    R['surge3'] = s3.astype(int)
    R['obs3'] = (R.mi + 3 <= LAST)
    return R


# check that the loans rebuilt here give Test A's stored D exactly
_wi = PR.work_id.map(widx).to_numpy()
_Dchk, _, _ = dflag(Aex[_wi, PR.mi.to_numpy() + 1 - MI[0]], PR.M6.to_numpy())
D_CHECK = dict(rows=int(len(PR)), max_abs_diff=float(np.nanmax(np.abs(_Dchk - PR.D.to_numpy()))), rose_flag_agree=float(np.mean((_Dchk >= LN15) == (PR.D.to_numpy() >= LN15))))
log('check of the rebuilt loans against Test A D:', D_CHECK)
assert D_CHECK['rose_flag_agree'] == 1.0
PR = add_outcomes(PR)
RW = add_outcomes(RW)

# alert rows (work, origin t) per list (C8)
PG = pd.read_parquet(IN / 'adaptation_page_features.parquet', columns=['article', 'mi', 'has_data'])
PGs = set(map(tuple, PG.loc[PG.has_data, ['article', 'mi']].astype({'article': str}).itertuples(index=False, name=None)))
rel = []
for k in (1, 2, 3):
    x = ADP[['work_id', 'e', 'type_group', 'page', 'label']].copy()
    x['mi'] = x.e - k
    rel.append(x)
REL = pd.concat(rel, ignore_index=True)
REL['public'] = [((str(p), int(m)) in PGs) if isinstance(p, str) else False for p, m in zip(REL.page, REL.mi)]
ALERTS = {
    'adapt': REL[['work_id', 'mi']].drop_duplicates(),
    'adapt_public': REL.loc[REL.public, ['work_id', 'mi']].drop_duplicates(),
    'adapt_now': ADP.assign(mi=ADP.e)[['work_id', 'mi']].drop_duplicates(),
    'death': EVT.loc[EVT.type == 'death'].assign(mi=lambda x: x.e)[['work_id', 'mi']].drop_duplicates(),
    'award': EVT.loc[EVT.type == 'award'].assign(mi=lambda x: x.e)[['work_id', 'mi']].drop_duplicates(),
}
ALERTS['any'] = pd.concat([ALERTS['adapt'], ALERTS['death'], ALERTS['award']]).drop_duplicates()
ALERT_NAMES = {'adapt': 'film or tv release in t+1..t+3', 'adapt_public': 'same, adaptation article already public at t',
               'adapt_now': 'film or tv release in month t (extra)', 'death': 'author died in month t', 'award': 'dated award in month t',
               'any': 'any of release t+1..t+3, death t, award t'}
for nm, a in ALERTS.items():
    a = a.assign(**{'al_' + nm: 1})
    PR = PR.merge(a, on=['work_id', 'mi'], how='left')
    RW = RW.merge(a, on=['work_id', 'mi'], how='left')
    PR['al_' + nm] = PR['al_' + nm].fillna(0).astype(int)
    RW['al_' + nm] = RW['al_' + nm].fillna(0).astype(int)
PR = PR.sort_values(['mi', 'work_id']).reset_index(drop=True)
from scipy.stats import rankdata
PR['h_rank'] = PR.groupby('mi').Hlgbm_D.rank(ascending=False, method='first')
PR['h_dec'] = PR.groupby('mi').Hlgbm_D.transform(lambda s: np.minimum((10 * (rankdata(s) - 0.5) / len(s)).astype(int), 9))
months_all = np.sort(PR.mi.unique())
months3 = months_all[months_all + 3 <= LAST]
log('prediction rows', len(PR), 'months', len(months_all), 'with t+3 observed', len(months3), {k: int(PR['al_' + k].sum()) for k in ALERTS})


def block_draws(n, rng, block=3):
    k = int(np.ceil(n / block))
    out = []
    for _ in range(NB):
        s = rng.choice(np.arange(n), k)
        out.append(np.concatenate([np.arange(a, a + block) % n for a in s])[:n])
    return np.array(out)


def alert_measures(R, nm, out_cols, rng, months, with_h=True):
    """share rose/surged of the alert rows, matched base, excess, lift, H-decile excess; work-cluster bootstrap."""
    R = R[R.mi.isin(months)]
    al = R['al_' + nm] == 1
    res = dict(rows=int(al.sum()), works=int(R.loc[al, 'work_id'].nunique()), months_with_alert=int(R.loc[al, 'mi'].nunique()), months=int(len(months)))
    if not al.any():
        return res
    cl = pd.factorize(R.loc[al, 'work_id'])[0]
    nc = cl.max() + 1
    cnt = np.stack([np.bincount(d, minlength=nc) for d in rng.integers(0, nc, size=(NB, nc))]).astype(float)
    n_c = np.bincount(cl, minlength=nc).astype(float)
    for o in out_cols:
        base_m = R.groupby('mi')[o].mean()
        y = R.loc[al, o].to_numpy().astype(float)
        b = R.loc[al, 'mi'].map(base_m).to_numpy()
        S_y, S_b = np.bincount(cl, y, nc), np.bincount(cl, b, nc)
        share, base = y.mean(), b.mean()
        bs_y, bs_b, bs_n = cnt @ S_y, cnt @ S_b, cnt @ n_c
        d = dict(share=float(share), share_lo=float(np.percentile(bs_y / bs_n, 2.5)), share_hi=float(np.percentile(bs_y / bs_n, 97.5)),
                 base=float(base), excess=float(share - base), excess_lo=float(np.percentile((bs_y - bs_b) / bs_n, 2.5)),
                 excess_hi=float(np.percentile((bs_y - bs_b) / bs_n, 97.5)), lift=float(share / base) if base > 0 else np.nan,
                 lift_lo=float(np.percentile(bs_y / bs_b, 2.5)), lift_hi=float(np.percentile(bs_y / bs_b, 97.5)))
        if with_h:
            nonal = R[~al]
            bh = nonal.groupby(['mi', 'h_dec'])[o].mean()
            bhv = pd.MultiIndex.from_arrays([R.loc[al, 'mi'], R.loc[al, 'h_dec']]).map(lambda t: bh.get(t, np.nan))
            bhv = np.asarray(bhv, dtype=float)
            S_h = np.bincount(cl, np.nan_to_num(bhv), nc)
            bs_h = cnt @ S_h
            d.update(base_same_H_decile=float(np.nanmean(bhv)), excess_over_H=float(share - np.nanmean(bhv)),
                     excess_over_H_lo=float(np.percentile((bs_y - bs_h) / bs_n, 2.5)), excess_over_H_hi=float(np.percentile((bs_y - bs_h) / bs_n, 97.5)))
        res[o] = d
    return res


def top20_hits(R, months, outs, order_col='Hlgbm_D'):
    """per month share of H's top 20 that rose / surged."""
    rows = []
    for m in months:
        g = R[R.mi == m].sort_values([order_col, 'work_id'], ascending=[False, True]).head(20)
        rows.append({o: g[o].mean() for o in outs} | dict(mi=m))
    return pd.DataFrame(rows).set_index('mi')


def swap_hits(R, nm, months, outs, cap=20):
    """per month share of the swapped list (C9) and whether the list changed."""
    rows = []
    for m in months:
        g = R[R.mi == m].sort_values(['Hlgbm_D', 'work_id'], ascending=[False, True])
        top = g.head(20)
        al = g[g['al_' + nm] == 1]
        al_out = al[~al.work_id.isin(top.work_id)]
        if cap >= 20:
            new = pd.concat([al.head(20), g[~g.work_id.isin(al.head(20).work_id)]]).head(20)
        else:
            add = al_out.head(cap)
            new = pd.concat([top.head(20 - len(add)), add])
        changed = not set(new.work_id) == set(top.work_id)
        rows.append({o: new[o].mean() for o in outs} | {'H_' + o: top[o].mean() for o in outs} | dict(mi=m, changed=changed, n_swapped=int(len(set(new.work_id) - set(top.work_id)))))
    return pd.DataFrame(rows).set_index('mi')


def block_mean_ci(x, BD, mask=None):
    x = np.asarray(x, float)
    if mask is None:
        b = x[BD].mean(1)
        return float(x.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))
    mk = np.asarray(mask, float)
    with np.errstate(all='ignore'):
        b = (x[BD] * mk[BD]).sum(1) / mk[BD].sum(1)
    return float(x[mk > 0].mean()) if mk.sum() else np.nan, float(np.nanpercentile(b, 2.5)), float(np.nanpercentile(b, 97.5))


PRED = {}
OUTS1, OUTS3 = ['rose1', 'surge1'], ['rose3', 'surge3']
for nm in ALERTS:
    PRED[nm] = dict(next_month=alert_measures(PR, nm, OUTS1, rng, months_all), three_months=alert_measures(PR, nm, OUTS3, rng, months3))
BD_all = block_draws(len(months_all), rng)
BD_3 = block_draws(len(months3), rng)
H1 = top20_hits(PR, months_all, OUTS1)
H3 = top20_hits(PR, months3, OUTS3)
HTOP = {o: dict(zip(['mean', 'lo', 'hi'], block_mean_ci(H1[o].to_numpy(), BD_all))) for o in OUTS1}
HTOP |= {o: dict(zip(['mean', 'lo', 'hi'], block_mean_ci(H3[o].to_numpy(), BD_3))) for o in OUTS3}
HTOP['base_rose1'] = float(PR.groupby('mi').rose1.mean().mean())
HTOP['base_surge1'] = float(PR.groupby('mi').surge1.mean().mean())
HTOP['base_rose3'] = float(PR[PR.mi.isin(months3)].groupby('mi').rose3.mean().mean())
HTOP['base_surge3'] = float(PR[PR.mi.isin(months3)].groupby('mi').surge3.mean().mean())
# H's top-20 share in the months that had at least one adaptation alert (same months as the alert list)
am = PR.loc[PR.al_adapt == 1, 'mi'].unique()
HTOP['rose3_alert_months'] = float(H3.loc[H3.index.isin(am), 'rose3'].mean())
HTOP['surge3_alert_months'] = float(H3.loc[H3.index.isin(am), 'surge3'].mean())

SWAP = {}
swap_rows = []
for nm in ('adapt', 'adapt_public', 'any'):
    for cap in (20, 5):
        for outs, months, BD in ((OUTS1, months_all, BD_all), (OUTS3, months3, BD_3)):
            S_ = swap_hits(PR, nm, months, outs, cap)
            for o in outs:
                dlt = (S_[o] - S_['H_' + o]).to_numpy()
                ch = S_.changed.to_numpy()
                m_all = block_mean_ci(dlt, BD)
                m_ch = block_mean_ci(dlt, BD, ch)
                r = dict(alert=nm, cap=cap, outcome=o, months=int(len(S_)), months_changed=int(ch.sum()), mean_swapped=float(S_.n_swapped[ch].mean()) if ch.any() else 0.0,
                         H=float(S_['H_' + o].mean()), swapped=float(S_[o].mean()), diff_all=m_all[0], diff_all_lo=m_all[1], diff_all_hi=m_all[2],
                         H_changed=float(S_.loc[ch, 'H_' + o].mean()) if ch.any() else np.nan, swapped_changed=float(S_.loc[ch, o].mean()) if ch.any() else np.nan,
                         diff_changed=m_ch[0], diff_changed_lo=m_ch[1], diff_changed_hi=m_ch[2])
                swap_rows.append(r)
SWAPT = pd.DataFrame(swap_rows)
SWAPT.to_csv(OUT / 'swap_into_H_top20.csv', index=False)
log('swap done')

# ---------------------------------------------------------------- C11 (extra, added after the first run showed that H's top 20 are mostly books that
# had already risen in month t): the same comparisons among books that have not risen yet at t (ln(1 + L_t) - ln(1 + M6) < ln 1.5, Test A's
# arithmetic; the "early list" of the improvement round v2).  H's early top 20 = the 20 highest H scores among these books.
_, _r_t, _ = dflag(PR.L_t.to_numpy(), PR.M6.to_numpy())
PR['not_yet'] = ~_r_t
PRe = PR[PR.not_yet].copy()
PRe['h_dec'] = PRe.groupby('mi').Hlgbm_D.transform(lambda s: np.minimum((10 * (rankdata(s) - 0.5) / len(s)).astype(int), 9))
PRED_E = {nm: dict(next_month=alert_measures(PRe, nm, OUTS1, rng, months_all), three_months=alert_measures(PRe, nm, OUTS3, rng, months3)) for nm in ALERTS}
H1e = top20_hits(PRe, months_all, OUTS1)
H3e = top20_hits(PRe, months3, OUTS3)
HTOP_E = {o: dict(zip(['mean', 'lo', 'hi'], block_mean_ci(H1e[o].to_numpy(), BD_all))) for o in OUTS1}
HTOP_E |= {o: dict(zip(['mean', 'lo', 'hi'], block_mean_ci(H3e[o].to_numpy(), BD_3))) for o in OUTS3}
HTOP_E['base_rose1'] = float(PRe.groupby('mi').rose1.mean().mean())
HTOP_E['base_surge1'] = float(PRe.groupby('mi').surge1.mean().mean())
HTOP_E['base_rose3'] = float(PRe[PRe.mi.isin(months3)].groupby('mi').rose3.mean().mean())
HTOP_E['base_surge3'] = float(PRe[PRe.mi.isin(months3)].groupby('mi').surge3.mean().mean())
HTOP_E['share_not_yet'] = float(PR.not_yet.mean())
swap_rows_e = []
for nm in ('adapt', 'adapt_public', 'any'):
    for cap in (20, 5):
        for outs, months, BD in ((OUTS1, months_all, BD_all), (OUTS3, months3, BD_3)):
            S_ = swap_hits(PRe, nm, months, outs, cap)
            for o in outs:
                dlt = (S_[o] - S_['H_' + o]).to_numpy()
                ch = S_.changed.to_numpy()
                m_all = block_mean_ci(dlt, BD)
                m_ch = block_mean_ci(dlt, BD, ch)
                swap_rows_e.append(dict(alert=nm, cap=cap, outcome=o, months=int(len(S_)), months_changed=int(ch.sum()),
                                        mean_swapped=float(S_.n_swapped[ch].mean()) if ch.any() else 0.0, H=float(S_['H_' + o].mean()), swapped=float(S_[o].mean()),
                                        diff_all=m_all[0], diff_all_lo=m_all[1], diff_all_hi=m_all[2],
                                        H_changed=float(S_.loc[ch, 'H_' + o].mean()) if ch.any() else np.nan,
                                        swapped_changed=float(S_.loc[ch, o].mean()) if ch.any() else np.nan,
                                        diff_changed=m_ch[0], diff_changed_lo=m_ch[1], diff_changed_hi=m_ch[2]))
SWAPTE = pd.DataFrame(swap_rows_e)
SWAPTE.to_csv(OUT / 'swap_into_H_top20_not_yet_risen.csv', index=False)
log('early-list comparisons done')

# ====================================================================== coverage and precision (all Test A rows, C10)
RW = RW.sort_values(['mi', 'work_id']).reset_index(drop=True)
wiR = RW.work_id.map(widx).to_numpy()
s_m = RW.mi.to_numpy() + 1


def near_count(wi, s, shift=0, types=None):
    if types is None:
        return n_events(wi, s - 2 + shift, s + 2 + shift)
    E2 = np.zeros((NW, len(GRID)), np.int16)
    sub = EVT[EVT.type.isin(types) & (EVT.e >= G0) & (EVT.e <= G1)]
    np.add.at(E2, (sub.wi.to_numpy(), (sub.e - G0).to_numpy()), 1)
    C2 = np.concatenate([np.zeros((NW, 1), np.int32), np.cumsum(E2, axis=1, dtype=np.int32)], axis=1)
    n = len(GRID)
    return np.maximum(C2[wi, np.clip(s + 2 + shift - G0 + 1, 0, n)] - C2[wi, np.clip(s - 2 + shift - G0, 0, n)], 0)


COV = {}
surge = RW.surge1.to_numpy() == 1
for tn, types in (('any', None), ('adaptation', ['adaptation']), ('death', ['death']), ('award', ['award'])):
    near = near_count(wiR, s_m, 0, types) > 0
    near_p = near_count(wiR, s_m, 24, types) > 0          # events moved 24 months earlier: an event at e counts for the surge month e - 24 + ...
    COV[tn] = dict(surges=int(surge.sum()), coverage=float(near[surge].mean()), chance_all_rows=float(near.mean()),
                   coverage_events_moved_24_months=float(near_p[surge].mean()), chance_moved=float(near_p.mean()),
                   surges_with_event=int((near & surge).sum()))
# work-cluster interval for the coverage (resample works)
clR = pd.factorize(RW.work_id)[0]
ncR = clR.max() + 1
cntR = np.stack([np.bincount(d, minlength=ncR) for d in rng.integers(0, ncR, size=(NB, ncR))]).astype(float)
for tn, types in (('any', None), ('adaptation', ['adaptation']), ('death', ['death']), ('award', ['award'])):
    near = near_count(wiR, s_m, 0, types) > 0
    a = np.bincount(clR, (near & surge).astype(float), ncR)
    b = np.bincount(clR, surge.astype(float), ncR)
    cv = (cntR @ a) / (cntR @ b)
    COV[tn].update(coverage_lo=float(np.percentile(cv, 2.5)), coverage_hi=float(np.percentile(cv, 97.5)))
months_rw3 = np.sort(RW.mi.unique())
months_rw3 = months_rw3[months_rw3 + 3 <= LAST]
PREC = {nm: alert_measures(RW, nm, OUTS3 + OUTS1, rng, months_rw3, with_h=False) for nm in ALERTS}
COVT = pd.DataFrame([dict(events=k, **v) for k, v in COV.items()])
COVT.to_csv(OUT / 'coverage_of_surges.csv', index=False)
log('coverage', COV)

# alert table for the report
pred_rows = []
for nm, r in PRED.items():
    for hz, outs in (('three_months', OUTS3), ('next_month', OUTS1)):
        x = r[hz]
        for o in outs:
            if o in x:
                pred_rows.append(dict(alert=nm, horizon=hz, outcome=o, rows=x['rows'], works=x['works'], months_with_alert=x['months_with_alert'], **x[o]))
for nm, r in PRED_E.items():
    for hz, outs in (('three_months', OUTS3), ('next_month', OUTS1)):
        x = r[hz]
        for o in outs:
            if o in x:
                pred_rows.append(dict(alert=nm, horizon=hz + '_not_yet_risen', outcome=o, rows=x['rows'], works=x['works'], months_with_alert=x['months_with_alert'], **x[o]))
PREDT = pd.DataFrame(pred_rows)
PREDT.to_csv(OUT / 'alert_lists_scored_months.csv', index=False)
prec_rows = []
for nm, x in PREC.items():
    for o in OUTS3 + OUTS1:
        if o in x:
            prec_rows.append(dict(alert=nm, outcome=o, rows=x['rows'], works=x['works'], **x[o]))
PRECT = pd.DataFrame(prec_rows)
PRECT.to_csv(OUT / 'alert_precision_all_months.csv', index=False)

# ====================================================================== examples (positive controls): large film or tv releases 2016-2026
cand = XS['adaptation']
cand = cand[cand.used & (cand.e >= mi_of('2016-01')) & (cand.e <= LAST - 6)].copy()
cand['early'] = [np.nanmean(r[3:6]) for r in cand.D]                                   # months 0..2
cand['L_pre'] = [float(np.nanmean(A[widx[w], col(e) - 9:col(e) - 3])) for w, e in zip(cand.work_id, cand.e)]
cand['L_post'] = [float(np.nanmean(Aex[widx[w], col(e):col(e) + 3])) for w, e in zip(cand.work_id, cand.e)]
cand = cand.merge(W[['work_id', 'title', 'creator']], on='work_id')
cand['gain'] = cand.L_post - cand.L_pre
EXC = cand.sort_values('gain', ascending=False).head(25)[['work_id', 'title', 'creator', 'e', 'sub', 'label', 'M6', 'L_pre', 'L_post', 'gain', 'early']]
EXC['event_month'] = EXC.e.map(ym)
EXC.to_csv(OUT / 'example_candidates.csv', index=False)


def series(work_id, e, a=-6, b=12):
    """monthly loans of a work around month e (None after the last month or before the first loan; excluded months flagged in the report)."""
    w = widx[work_id]
    out = {}
    for k in range(a, b + 1):
        m = e + k
        v = A[w, col(m)] if MI[0] <= m <= LAST else np.nan
        out[ym(m)] = None if np.isnan(v) else int(v)
    return out


# ====================================================================== alert works by band of H's score (does the alert add to H at every level?)
PR['h_pct'] = PR.groupby('mi').Hlgbm_D.rank(pct=True)
BANDS = [('below the median', 0, 0.5), ('50th to 90th percentile', 0.5, 0.9), ('90th to 99th percentile', 0.9, 0.99), ('top 1%', 0.99, 1.01)]
P3 = PR[PR.obs3].copy()
band_rows = []
for nm in ('adapt', 'adapt_public', 'death'):
    for bn, lo, hi in BANDS:
        x = P3[(P3.h_pct >= lo) & (P3.h_pct < hi)]
        a, o = x[x['al_' + nm] == 1], x[x['al_' + nm] == 0]
        band_rows.append(dict(alert=nm, band=bn, alert_rows=int(len(a)), alert_rose3=float(a.rose3.mean()), alert_surge3=float(a.surge3.mean()),
                              other_rows=int(len(o)), other_rose3=float(o.rose3.mean()), other_surge3=float(o.surge3.mean())))
BAND = pd.DataFrame(band_rows)
BAND.to_csv(OUT / 'alert_by_H_band.csv', index=False)
P3['h_pc'] = np.minimum((P3.h_pct * 100).astype(int), 99)
PCT = {}
for nm in ALERTS:
    a, o = P3[P3['al_' + nm] == 1], P3[P3['al_' + nm] == 0]
    if len(a):
        PCT[nm] = {}
        for oc in OUTS3:
            b = o.groupby(['mi', 'h_pc'])[oc].mean()
            PCT[nm][oc] = dict(share=float(a[oc].mean()), base_same_H_percentile=float(np.nanmean([b.get(k, np.nan) for k in zip(a.mi, a.h_pc)])))
log('H bands and percentile check done')

# ====================================================================== improvement round v2 (reported beside; numbers from data/reports/wiki_led_improve_v2.md, section 6)
V2 = dict(source='data/reports/wiki_led_improve_v2.md, section 6 (change 5), and wiki_led_improve_v2_c5.json',
          text=('the event flags (author death in t or t-1, dated award in t or t-1, a film or tv release in t-1..t+1 whose article was already '
                'public, months since the last event) and the adaptation-page views were added to the models as columns. On 2024 to 2026 the change '
                'ranking moved +0.0012 (interval -0.0005 to +0.0028), the early list of the Wikipedia model +1.2 points (-1.7 to +3.7) and the ranker '
                '+1.0 points (-2.1 to +3.8); with the same columns moved 12 months later the moves were +0.0012, +1.2 and +1.0 points, so no gain was '
                'tied to the real dates. On the 1,215 book-months within 2 months of an event the change ranking moved +0.0204 (+0.0006 to +0.0398) '
                'against +0.0037 in the placebo.'))

# ====================================================================== figure: event study by type, real against placebo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BLUE, ORANGE, INK, INK2, GRIDC, SURF = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
FIG_TYPES = [('film', 'Film release'), ('tv', 'TV release'), ('death', "Author's death"), ('award', 'Dated award')]
fig, axes = plt.subplots(2, 4, figsize=(13, 6.4), sharex=True, sharey='row', facecolor=SURF)
for r, meas, ylab in ((0, 'rose', 'Rose (1.5 x usual)\nevent minus matched, points'), (1, 'surge', 'Surged (2 x and 5+ loans)\nevent minus matched, points')):
    for c, (t, ttl) in enumerate(FIG_TYPES):
        ax = axes[r, c]
        ax.set_facecolor(SURF)
        for E_, colr, lab in ((ESP, ORANGE, 'Placebo: same books, dates moved 24 months earlier'), (ES, BLUE, 'Real event dates')):
            bm = pd.DataFrame(E_[t][meas]['by_month'])
            ax.fill_between(bm.k, 100 * bm.lo, 100 * bm.hi, color=colr, alpha=0.16, linewidth=0)
            ax.plot(bm.k, 100 * bm.excess, color=colr, lw=2, marker='o', ms=3.5, label=lab)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvline(-0.5, color=INK2, lw=0.8, ls=(0, (3, 3)))
        ax.grid(axis='y', color=GRIDC, lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        for sp in ('left', 'bottom'):
            ax.spines[sp].set_color(INK2)
        ax.tick_params(colors=INK2, labelsize=9)
        if r == 0:
            ax.set_title(f"{ttl} ({ES[t]['n']['events']:,} events)", fontsize=11, color=INK, loc='left')
        if c == 0:
            ax.set_ylabel(ylab, fontsize=9.5, color=INK2)
        if r == 1:
            ax.set_xlabel('Months from the event (0 = event month)', fontsize=9.5, color=INK2)
        ax.set_xticks([-3, 0, 3, 6, 9, 12])
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h[::-1], l[::-1], loc='upper center', ncol=2, frameon=False, fontsize=10, labelcolor=INK)
fig.tight_layout(rect=(0, 0, 1, 0.94))
FIG = OUT / 'd2_event_study.png'
fig.savefig(FIG, dpi=150, facecolor=SURF)
plt.close(fig)
log('figure', FIG)

# ====================================================================== examples (picked by hand from example_candidates.csv: well-known releases with a clean before and after)
EXAMPLES = [(5126, mi_of('2024-12')), (5121, mi_of('2023-07'))]
EXR = []
for w, e in EXAMPLES:
    a = ADP[(ADP.work_id == w) & (ADP.e == e)].iloc[0]
    rows = PR[(PR.work_id == w) & PR.mi.between(e - 3, e - 1)].sort_values('mi')
    EXR.append(dict(work_id=w, title=W.set_index('work_id').title[w], creator=W.set_index('work_id').creator[w], adaptation=a.en_title, kind=a.type_group,
                    release=a.date, e=e, loans=series(w, e, -5, 6),
                    origins=[dict(origin=ym(r.mi), h_rank=int(r.h_rank), books=int((PR.mi == r.mi).sum()), not_yet=bool(r.not_yet), alert=bool(r.al_adapt),
                                  public=bool(r.al_adapt_public), rose3=bool(r.rose3), surge3=bool(r.surge3)) for r in rows.itertuples()]))

RES = dict(settings=SET, choices='C1 to C11 in the header of code/main_study/wiki_led/dirs/d2_events.py', d_check=D_CHECK,
           excluded_months=[ym(m) for m in sorted(EXCL)], event_counts_any_year=EVT.groupby('type').size().to_dict(),
           event_study=ES, event_study_placebo=ESP, prediction=PRED, H_top20=HTOP, prediction_not_yet_risen=PRED_E, H_top20_not_yet_risen=HTOP_E,
           alert_same_H_percentile=PCT, coverage=COV, precision_all_months=PREC, examples=EXR,
           months_scored=[ym(months_all[0]), ym(months_all[-1]), int(len(months_all))], months_three=[ym(months3[0]), ym(months3[-1]), int(len(months3))],
           v2=V2, runtime_s=round(time.time() - T0))
(OUT / 'd2_results.json').write_text(json.dumps(RES, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
PR[['work_id', 'mi', 'Hlgbm_D', 'h_rank', 'h_pct', 'not_yet', 'rose1', 'surge1', 'rose3', 'surge3', 'obs3'] + ['al_' + k for k in ALERTS]].to_parquet(OUT / 'scored_rows_alerts.parquet', index=False)
log('results written', OUT)

# ====================================================================== report (data/reports/dir_d2_events.md), written from the numbers above
def pc(x):
    return f'{100 * x:.1f}%'


def pt(x):
    return f'{100 * x:+.1f}'


def iv(lo, hi):
    return f'{100 * lo:+.1f} to {100 * hi:+.1f}'


def table(head, rows):
    return ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join(['---'] * len(head)) + ' |'] + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]


def win(E_, t, meas, w='0 to 2'):
    return E_[t][meas]['windows'][w]


TNAME = {'adaptation': 'Film or TV release', 'film': '  film', 'tv': '  TV', 'death': "Author's death", 'award': 'Dated award'}
ANAME = {'adapt': 'Film or TV release in t+1..t+3', 'adapt_public': 'Film or TV release in t+1..t+3, article already public at t',
         'adapt_now': 'Film or TV release in month t (extra)', 'death': 'Author died in month t', 'award': 'Dated award in month t',
         'any': 'Any of the three alerts above'}
a3 = PRED['adapt']['three_months']
ap3 = PRED['adapt_public']['three_months']
w_ad, w_adp = win(ES, 'adaptation', 'rose'), win(ESP, 'adaptation', 'rose')
w_de, w_aw = win(ES, 'death', 'rose'), win(ES, 'award', 'rose')
best_swap = SWAPTE[(SWAPTE.alert == 'adapt_public') & (SWAPTE.cap == 5) & (SWAPTE.outcome == 'surge3')].iloc[0]
n_swaps = len(SWAPT) + len(SWAPTE)
n_pos = int(((SWAPT.diff_all_lo > 0).sum() + (SWAPTE.diff_all_lo > 0).sum()))
n_neg = int(((SWAPT.diff_all_hi < 0).sum() + (SWAPTE.diff_all_hi < 0).sum()))
n_mid = n_swaps - n_pos - n_neg
cov = COV['any']
Lr = []
P_ = Lr.append
P_('# D2: an event calendar (films, TV series, deaths, awards) to flag books whose borrowing will jump')
P_('')
P_('Khant Phyo Wai, 01323050. Run ' + time.strftime('%d %b %Y %H:%M') + ' +07. Direction D2 of addendum i (`prereg/addenda_wiki_led/2026-10-22_i_directions.json`, '
   'section D2_event_calendar). Choices the addendum leaves open: C1 to C11 in the header of `code/main_study/wiki_led/dirs/d2_events.py`, also logged in '
   '`prereg/DEVIATIONS.md` (Addendum i). Exploratory and descriptive; every interval is a 95% interval. Tables and the figure: `data/db/wiki_led/dirs/d2_events/`.')
P_('')
P_('**In plain words**')
P_('')
P_(f"1. When a film or TV version of a book comes out, its borrowing jumps and stays up for a year: in the release month and the two months after, "
   f"{pc(w_ad['event'])} of these books were borrowed at least 1.5 times their usual amount, against {pc(w_ad['control'])} of books with the same usual level and no event "
   f"(made-up dates two years earlier give a gap of {pt(w_adp['excess'])} points instead of {pt(w_ad['excess'])}). An author's death does the same "
   f"({pc(w_de['event'])} against {pc(w_de['control'])}) with no rise before it; an award dated to the month in Wikidata barely moves borrowing ({pt(w_aw['excess'])} points).")
P_(f"2. Known release dates work as an alert: of the books with a film or TV release in the next three months, {pc(a3['rose3']['share'])} rose and "
   f"{pc(a3['surge3']['share'])} surged (at least double and 5 loans more) in those months, against {pc(a3['rose3']['base'])} and {pc(a3['surge3']['base'])} of all books, "
   f"and against {pc(a3['rose3']['base_same_H_decile'])} and {pc(a3['surge3']['base_same_H_decile'])} of books that the library's own model (H) scored about the same. So the calendar knows something the loan history does not.")
P_(f"3. Still, the alert list does not beat H's own top 20, which are mostly books whose borrowing is already climbing ({pc(HTOP['rose3']['mean'])} of them rose in the next three months). "
   f"Putting the alert books into H's top 20 lowered its hit rate clearly in {n_neg} of the {n_swaps} versions tried and left it within noise in {n_mid}; the {'one gain is' if n_pos == 1 else str(n_pos) + ' gains are'} small "
   f"(surges among books not yet risen, at most 5 public releases swapped in: {pt(best_swap.diff_all)} points, interval {iv(best_swap.diff_all_lo, best_swap.diff_all_hi)}).")
P_(f"4. Events explain few of the big jumps: {pc(cov['coverage'])} of the {cov['surges']:,} surges of 2016 to 2026 had a known event of the book or its author within two months "
   f"(chance: {pc(cov['chance_all_rows'])} of all book-months). Events are rare (about {a3['rows'] / a3['months']:.0f} release alerts a month among about 7,100 books), which helps explain why "
   "the improvement round v2, which gave similar event flags to the models as extra columns, found no gain.")
P_(f"5. Limit: Wikidata dates may have been entered after the event, so this calendar is not exactly what was known at the time. Keeping only adaptations whose Wikipedia article "
   f"already had views at the alert month gives the same picture ({pc(ap3['rose3']['share'])} rose, {pc(ap3['surge3']['share'])} surged).")
P_('')
P_('Terms. **Usual level** (M6): the median of a book\'s monthly loans over six months (all formats, as in Test A). **Rose**: loans at least 1.5 times the usual level; '
   '**surged**: at least 2 times and at least 5 loans more (Test A\'s arithmetic, ln(1 + loans) against ln(1 + M6)). **H**: Test A\'s library-history model (LightGBM on the '
   'book\'s own loan history), whose predictions for 2019-01 to 2026-07 are in `test_a_preds_c.parquet`. A month **t** is the month at whose end the list is made.')
P_('')
# ---------------------------------------------------------------- 1. events
nE = {t: ES[t]['n'] for t in TYPES}
P_('## 1. Events used')
P_('')
P_(f"From `data/db/wiki_led/events_long.parquet` (Wikidata, fetched 20 Oct 2026 for the 7,747 Test A works): film and TV adaptations with a release month "
   f"(earliest best-rank P577 or P580 date at month precision), the death month of the author (P570), and awards with a month-precision date (P166 with P585, "
   f"book or author). Year-only dates cannot be placed in a month and are not used: that leaves out 95% of the dated award statements, including the Booker, Pulitzer, "
   f"Hugo and Newbery prizes, so the award result is about honorary degrees, orders, fellowships and the Nebula Award, not about the big book prizes. "
   f"Event study events, 2006-07 to 2026-08: film {nE['film']['events']:,} ({nE['film']['works']:,} works), TV {nE['tv']['events']:,} ({nE['tv']['works']:,} works), "
   f"deaths {nE['death']['events']:,} ({nE['death']['works']:,} works, {ES['death_by_author']['n']['clusters']:,} authors), dated awards {nE['award']['events']:,} "
   f"({nE['award']['works']:,} works). The `ad_rel` flag of `events.parquet` (a release in t-1, t or t+1) is not used: the alert here needs releases in t+1 to t+3, "
   f"built from the release months. Its `ad_rel_public` column is empty on purpose; the 'already public' check is made here as in v2 (the adaptation's English article had views by the end of t).")
P_('')
# ---------------------------------------------------------------- 2. event study
P_('## 2. Event study: borrowing from 3 months before to 12 months after the event')
P_('')
P_('Each event is compared with books that had no dated event from 9 months before to 12 months after it, matched on the same month and the same tenth of usual loan level '
   '(usual level M6 = median of months -9 to -4, so the months -3 to -1 show any rise before the event). The difference is the event books\' share minus the matched books\' share. '
   'Placebo: the same books with their dates moved 24 months earlier (fake events with a real event in their window dropped). Intervals: 2,000 bootstrap draws over works '
   '(deaths also over authors, since one death touches all of an author\'s books).')
P_('')
P_('![Event study](../db/wiki_led/dirs/d2_events/d2_event_study.png)')
P_('')
rows = []
for t in TYPES:
    r_, s_, d_ = win(ES, t, 'rose'), win(ES, t, 'surge'), win(ES, t, 'D')
    rp, sp = win(ESP, t, 'rose'), win(ESP, t, 'surge')
    rows.append([TNAME[t].strip() if t not in ('film', 'tv') else 'of which ' + t.replace('tv', 'TV'), f"{ES[t]['n']['events']:,} ({ES[t]['n']['works']:,})",
                 f"{pc(r_['event'])} / {pc(r_['control'])}", f"{pt(r_['excess'])} ({iv(r_['lo'], r_['hi'])})", pt(rp['excess']),
                 f"{pc(s_['event'])} / {pc(s_['control'])}", f"{pt(s_['excess'])} ({iv(s_['lo'], s_['hi'])})", pt(sp['excess']), f"{np.exp(d_['excess']):.2f}x"])
P_('**Months 0 to 2** (the event month and the two after):')
P_('')
Lr += table(['Event', 'Events (works)', 'Rose: event / matched', 'Difference, points (interval)', 'Placebo difference', 'Surged: event / matched',
             'Difference, points (interval)', 'Placebo difference', 'Loans against usual level, relative to matched'], rows)
dA = win(ES, 'death_by_author', 'rose')
P_('')
P_(f"For deaths, resampling authors instead of works gives a wider interval for the rose difference: {iv(dA['lo'], dA['hi'])}. The last column is exp of the difference in mean "
   "ln((1 + loans) / (1 + usual level)): 1.77x means the event books' loans relative to their usual level were about 1.77 times those of the matched books.")
P_('')
rows = []
for t in TYPES:
    for meas, mn in (('rose', 'rose'), ('surge', 'surged')):
        rows.append([TNAME[t].strip() if t not in ('film', 'tv') else 'of which ' + t.replace('tv', 'TV'), mn] +
                    [f"{pt(win(ES, t, meas, w)['excess'])} ({iv(win(ES, t, meas, w)['lo'], win(ES, t, meas, w)['hi'])})" for w in WINDOWS])
P_('**Difference in points by window** (event minus matched; interval):')
P_('')
Lr += table(['Event', 'Measure'] + [f'months {w}' for w in WINDOWS], rows)
P_('')
fp, dp = win(ES, 'film', 'rose', '-3 to -1'), win(ES, 'death', 'rose', '-3 to -1')
P_(f"Reading. Film and TV releases lift borrowing before the release month (films {pt(fp['excess'])} points in months -3 to -1: trailers, premieres abroad, tie-in editions) "
   f"and the lift lasts: still {pt(win(ES, 'adaptation', 'rose', '6 to 12')['excess'])} points in months 6 to 12. Deaths give no rise before ({pt(dp['excess'])} points in months -3 to -1), "
   f"a peak in the month after the death, and a slow fade ({pt(win(ES, 'death', 'rose', '6 to 12')['excess'])} points in months 6 to 12). "
   f"The placebo is near 0 for deaths and awards but not for adaptations ({pt(w_adp['excess'])} points in months 0 to 2, {pt(win(ESP, 'adaptation', 'rose', '6 to 12')['excess'])} in months 6 to 12): "
   "books that will be adapted were already gaining readers two years before, which matching on the usual level does not remove. So about "
   f"{100 * (w_ad['excess'] - w_adp['excess']):.0f} of the {100 * w_ad['excess']:.0f} points in months 0 to 2 belong to the release itself.")
P_('')
# ---------------------------------------------------------------- 3. prediction test
P_('## 3. Prediction test: alert lists against the base rate and against H')
P_('')
P_(f"Rows: Test A's scored book-months (origins {RES['months_scored'][0]} to {RES['months_scored'][1]}, {RES['months_scored'][2]} months with library data, about 7,100 books a month). "
   f"'Rose in t+1..t+3' means rose in at least one of the next three months (each against the usual level at t); it needs month t+3, so origins {RES['months_three'][0]} to "
   f"{RES['months_three'][1]} ({RES['months_three'][2]} months). Base = all books of the same months. 'Same H tenth' = books that are not on the alert list in the same month and the same "
   "tenth of H's score: the difference against them is what the alert adds to the library's own history. Intervals: bootstrap over works (alert lists) or over blocks of 3 months (H's top 20).")
P_('')
rows = []
for nm in ('adapt', 'adapt_public', 'adapt_now', 'death', 'award', 'any'):
    x = PRED[nm]['three_months']
    rows.append([ANAME[nm], f"{x['rows']:,} ({x['works']:,})", f"{pc(x['rose3']['share'])} ({pc(x['rose3']['share_lo'])} to {pc(x['rose3']['share_hi'])})",
                 f"{pc(x['surge3']['share'])} ({pc(x['surge3']['share_lo'])} to {pc(x['surge3']['share_hi'])})", f"{pc(x['rose3']['base'])} / {pc(x['surge3']['base'])}",
                 f"{x['surge3']['lift']:.1f}", f"{pt(x['rose3']['excess_over_H'])} ({iv(x['rose3']['excess_over_H_lo'], x['rose3']['excess_over_H_hi'])})",
                 f"{pt(x['surge3']['excess_over_H'])} ({iv(x['surge3']['excess_over_H_lo'], x['surge3']['excess_over_H_hi'])})"])
rows.append(["H's top 20 each month", f"{20 * RES['months_three'][2]:,}", f"{pc(HTOP['rose3']['mean'])} ({pc(HTOP['rose3']['lo'])} to {pc(HTOP['rose3']['hi'])})",
             f"{pc(HTOP['surge3']['mean'])} ({pc(HTOP['surge3']['lo'])} to {pc(HTOP['surge3']['hi'])})", f"{pc(HTOP['base_rose3'])} / {pc(HTOP['base_surge3'])}",
             f"{HTOP['surge3']['mean'] / HTOP['base_surge3']:.1f}", '', ''])
P_('**All books; outcome in t+1..t+3:**')
P_('')
Lr += table(['Alert list at the end of month t', 'Book-months (books)', 'Rose in t+1..t+3', 'Surged in t+1..t+3', 'Base: rose / surged', 'Surged: times base',
             'Rose: difference to same H tenth, points', 'Surged: difference to same H tenth, points'], rows)
P_('')
rows = []
for nm in ('adapt', 'adapt_public', 'adapt_now', 'death', 'award', 'any'):
    x = PRED[nm]['next_month']
    rows.append([ANAME[nm], f"{x['rows']:,}", pc(x['rose1']['share']), pc(x['surge1']['share']), f"{pc(x['rose1']['base'])} / {pc(x['surge1']['base'])}",
                 f"{pt(x['surge1']['excess_over_H'])} ({iv(x['surge1']['excess_over_H_lo'], x['surge1']['excess_over_H_hi'])})"])
rows.append(["H's top 20 each month", f"{20 * RES['months_scored'][2]:,}", pc(HTOP['rose1']['mean']), pc(HTOP['surge1']['mean']), f"{pc(HTOP['base_rose1'])} / {pc(HTOP['base_surge1'])}", ''])
P_(f"**All books; next month only (Test A's own target, {RES['months_scored'][2]} months):**")
P_('')
Lr += table(['Alert list', 'Book-months', 'Rose next month', 'Surged next month', 'Base: rose / surged', 'Surged: difference to same H tenth, points'], rows)
P_('')
pa = PCT['adapt_public']
P_(f"Check of the H matching with hundredths of H's score instead of tenths: public release alerts {pc(pa['rose3']['share'])} rose against {pc(pa['rose3']['base_same_H_percentile'])} "
   f"of books in the same hundredth; {pc(pa['surge3']['share'])} surged against {pc(pa['surge3']['base_same_H_percentile'])}. By band of H's score (alert books against the other books of the band, outcome in t+1..t+3):")
P_('')
rows = []
for r in BAND[BAND.alert.isin(['adapt_public', 'death'])].itertuples():
    rows.append([ANAME[r.alert], r.band, f"{r.alert_rows:,}", f"{pc(r.alert_rose3)} / {pc(r.other_rose3)}", f"{pc(r.alert_surge3)} / {pc(r.other_surge3)}"])
Lr += table(['Alert list', "Band of H's score that month", 'Alert book-months', 'Rose: alert / others', 'Surged: alert / others'], rows)
P_('')
P_(f"Only {100 * (PR.loc[PR.al_adapt == 1, 'h_rank'] <= 20).mean():.1f}% of the release alerts were already in H's top 20, and {100 * (PR.loc[PR.al_adapt == 1, 'h_pct'] < 0.5).mean():.0f}% sat below H's median. "
   "In every band the alert books rose and surged more often than the other books, and the alerted books that H also scores in its top 10% surged most often.")
P_('')
P_('**Swapping the alert books into H\'s top 20.** Version 20: the alert books of the month, in H\'s order (at most 20), go first and H\'s own picks fill the rest. '
   'Version 5: at most 5 alert books (those H scores highest) replace H\'s places 16 to 20. Difference = swapped list minus H\'s top 20, mean over months, in points '
   '(the list changed in every month). "Not yet risen" (C11, added after the first run): the same among books whose loans in month t were below 1.5 times the usual level '
   f"({pc(HTOP_E['share_not_yet'])} of the book-months), where H's top 20 rose in {pc(HTOP_E['rose3']['mean'])} of cases in t+1..t+3 and surged in {pc(HTOP_E['surge3']['mean'])}.")
P_('')
rows = []
for lab, T_ in (('All books', SWAPT), ('Not yet risen', SWAPTE)):
    for nm in ('adapt', 'adapt_public', 'any'):
        for cap in (20, 5):
            x = T_[(T_.alert == nm) & (T_.cap == cap)].set_index('outcome')
            rows.append([lab, ANAME[nm], f'up to {cap}', f"{x.loc['rose3', 'mean_swapped']:.1f}"] +
                        [f"{pc(x.loc[o, 'H'])} to {pc(x.loc[o, 'swapped'])}: {pt(x.loc[o, 'diff_all'])} ({iv(x.loc[o, 'diff_all_lo'], x.loc[o, 'diff_all_hi'])})" for o in ('rose1', 'rose3', 'surge3')])
Lr += table(['Books', 'Alert list', 'Version', 'Books swapped in a month', 'Rose next month: H to swapped, difference', 'Rose in t+1..t+3', 'Surged in t+1..t+3'], rows)
P_('')
P_(f"Of the {n_swaps} differences in the two swap tables (`swap_into_H_top20*.csv`, which also hold the surged-next-month column), {n_neg} have an interval below 0, {n_mid} an interval that holds 0 and {n_pos} an interval above 0. "
   "H's top 20 are hard to beat because they are mostly books already climbing: a book at 1.4 times its usual level this month very often passes 1.5 times next month. "
   "Release alerts point to books that have not started to climb yet, which is earlier but less certain.")
P_('')
# ---------------------------------------------------------------- 4. practical summary
P_('## 4. Practical summary: coverage and precision')
P_('')
P_(f"Coverage: of the next-month surges in Test A's rows (origins 2016-03 to 2026-07), the share with a dated event of the book or its author within two months of the surge month. "
   "Chance: the same share among all book-months. Moved: with every event moved 24 months earlier.")
P_('')
rows = []
for k, nmk in (('any', 'Any event'), ('adaptation', 'Film or TV release'), ('death', "Author's death"), ('award', 'Dated award')):
    c = COV[k]
    rows.append([nmk, f"{c['surges_with_event']:,} of {c['surges']:,}", f"{pc(c['coverage'])} ({pc(c['coverage_lo'])} to {pc(c['coverage_hi'])})", pc(c['chance_all_rows']),
                 pc(c['coverage_events_moved_24_months'])])
Lr += table(['Event', 'Surges with an event within 2 months', 'Coverage', 'Chance (all book-months)', 'Coverage, events moved 24 months'], rows)
P_('')
P_('Precision: of the flagged book-months (all Test A origins 2016-03 to 2026-05), the share that surged or rose in t+1..t+3.')
P_('')
rows = []
for nm in ('adapt', 'adapt_public', 'adapt_now', 'death', 'award', 'any'):
    x = PREC[nm]
    rows.append([ANAME[nm], f"{x['rows']:,} ({x['works']:,})", f"{pc(x['surge3']['share'])} ({pc(x['surge3']['share_lo'])} to {pc(x['surge3']['share_hi'])})",
                 pc(x['surge3']['base']), f"{x['surge3']['lift']:.1f}", f"{pc(x['rose3']['share'])} ({pc(x['rose3']['share_lo'])} to {pc(x['rose3']['share_hi'])})", pc(x['rose3']['base'])])
Lr += table(['Flag', 'Book-months (books)', 'Surged in t+1..t+3', 'Base', 'Times base', 'Rose in t+1..t+3', 'Base'], rows)
P_('')
P_(f"So a release or a death is a strong flag when it happens (about 4 in 10 flagged books surge), but it touches few books: about 1 in 20 big surges has a known event nearby.")
P_('')
# ---------------------------------------------------------------- 5. examples
P_('## 5. Two real examples')
P_('')
for x in EXR:
    lo = [k for k in x['loans']]
    P_(f"**{x['title']}** ({x['creator']}). Adaptation: *{x['adaptation']}*, first released {x['release']} according to Wikidata. Monthly loans, all formats, Seattle Public Library:")
    P_('')
    Lr += table(['Month'] + [m + (' (excluded)' if mi_of(m) in EXCL else '') + (' (release)' if mi_of(m) == x['e'] else '') for m in lo], [['Loans'] + ['' if v is None else f'{v:,}' for v in x['loans'].values()]])
    P_('')
    s_ = '; '.join(f"end of {o['origin']}: H rank {o['h_rank']:,} of {o['books']:,}, {'not yet risen' if o['not_yet'] else 'already risen'}, "
                   f"{'alert' if o['alert'] else 'no alert'}{' (article public)' if o['public'] else ''}, {'surged' if o['surge3'] else ('rose' if o['rose3'] else 'did not rise')} in the next three months"
                   for o in x['origins'])
    P_(f"Alert months: {s_}.")
    P_('')
P_('Excluded months are the library-wide gaps of the benchmark (missing, not low). In both cases the release calendar flagged the book one to three months before its loans moved, '
   'while H, which only sees the loan history, ranked it in the thousands until the climb had started. Not every case is this clean: Wuthering Heights (2026 film, February 2026) was already '
   'climbing five months before the release (443 loans in 2025-09 against about 110 a month earlier in 2025), and H had it around place 150 to 280 in the three alert months.')
P_('')
# ---------------------------------------------------------------- 6. v2
P_('## 6. Beside: the improvement round v2 (events as model columns)')
P_('')
P_('In v2 (' + V2['source'] + '), ' + V2['text'])
P_('')
P_(f"The two results agree. The events carry real information about the few books they touch (sections 2 and 3), but those books are {100 * PR.al_any.mean():.1f}% of the scored book-months, so "
   "model-wide measures (Spearman over all books, top-20 hit rates) can hardly move. v2 also used flags at t-1..t+1, which often fall on books already climbing that H sees anyway: "
   f"{100 * (1 - PR.loc[PR.al_adapt_now == 1, 'not_yet'].mean()):.0f}% of the books with a release in month t had already risen at t, against {100 * (1 - PR.not_yet.mean()):.0f}% of all books. "
   "The rows near an event are the one place where v2 saw a gain, which fits what is found here.")
P_('')
# ---------------------------------------------------------------- 7. limits
P_('## 7. Limits')
P_('')
P_('- **Wikidata dates may have been entered after the event.** The calendar is today\'s Wikidata, not what was known at t. For releases, the "already public" list keeps only adaptations '
   'whose Wikipedia article had views by the end of t, and it does as well as the full list; it shows that the film or series was known, not that its date was. Deaths and awards are '
   'used in their own month, so they are known by the end of t, but a death in the last days of a month leaves little time to act.')
P_('- The release month is the earliest dated release (often a festival premiere or the first broadcast), not always the US release (Dune: 2021-09 Venice premiere, US release 2021-10).')
P_('- Awards: 95% of dated award statements are year-only and were not used, so the big book prizes are not tested; placing them in their usual announcement month would be a next step.')
P_('- Matching is on month and usual loan level only. Books that will be adapted were already gaining readers (placebo), so part of the release gap is selection; the placebo gives its size.')
P_('- One book item can have several Seattle works, and one death touches all of an author\'s works; intervals resample works (and authors for deaths).')
P_('- The event study uses 2006-07 to 2026-08 (longer than Test A); the comparison with H uses Test A\'s scored months only.')
P_('- Many measures are reported without adjustment; one interval that just clears 0 among many (the swap gain) is weak evidence.')
P_('- C11 (books not yet risen) was added after the first run had been seen; the addendum\'s comparison on all books is the main one.')
P_('')
P_('## 8. Files')
P_('')
P_('- Code: `code/main_study/wiki_led/dirs/d2_events.py` (run from `code/`: `../.venv/bin/python main_study/wiki_led/dirs/d2_events.py`, about 30 seconds).')
P_('- `data/db/wiki_led/dirs/d2_events/`: `event_study_by_month.csv`, `event_study_windows.csv`, `event_study_events.parquet`, `alert_lists_scored_months.csv`, '
   '`swap_into_H_top20.csv`, `swap_into_H_top20_not_yet_risen.csv`, `alert_by_H_band.csv`, `coverage_of_surges.csv`, `alert_precision_all_months.csv`, '
   '`example_candidates.csv`, `scored_rows_alerts.parquet`, `d2_results.json`, `d2_event_study.png`.')
P_(f"- Check: the loans rebuilt here reproduce Test A's stored change D exactly on all {D_CHECK['rows']:,} scored rows (largest difference {D_CHECK['max_abs_diff']}).")
(REP / 'dir_d2_events.md').write_text('\n'.join(Lr) + '\n')
log('report', REP / 'dir_d2_events.md')
