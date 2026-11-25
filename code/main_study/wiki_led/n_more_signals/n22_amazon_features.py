# n22. Addendum n, part 2 (AZ, Amazon reviews), step 3: the record's features at each origin month t per work, and the same features
# at t-12 (placebo, dates moved 12 months later).  DATA ONLY: no model, nothing related to loans; the summary has counts only.
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_2_amazon_reviews.months, common.time_rule,
# common.placebo_dates (read-only; SHA-256 checked).
#
# Record: reviews dated by their UTC month.  Last usable month L = the last month whose total number of reviews is at least half of the
# median of the 12 months before it; later months are missing.  At t: az_n = log(1 + reviews in t); az_r = log((1 + reviews in t) /
# (1 + median of t-6 .. t-1)); az_3 = log(1 + reviews in t-2 .. t); az_cum = log(1 + reviews up to t); az_rating = mean rating over
# t-11 .. t (missing without reviews); all missing for unmatched works and after L.  A work sums all its matched items.
#
# Choices the record leaves open (also in data/db/wiki_led/n_more_signals/notes_amazon.md, with the time they were decided, before
# this script was run):
#   C1 L from the monthly totals of all kept Amazon Books ratings (every item, not only matched ones).  'The 12 months before it' =
#      the calendar months m-12 .. m-1, a month without ratings counting 0; a month qualifies only when that median is above 0 (so a
#      stray month after a long gap cannot qualify).  L = the latest qualifying month.
#   C2 A month without ratings of a matched work counts 0 (also before its first rating); a matched work therefore has values (0 when
#      it has no ratings yet), and only unmatched works and months after L are missing.
#   C3 The median of t-6 .. t-1 is over those six calendar months, zeros included.
#   C4 az_rating = (sum of ratings in t-11 .. t) / (number of ratings in t-11 .. t); missing when that number is 0.
#   C5 log is the natural log.  Features are the same for every format of a work.  float32.
#   C6 Placebo AZl_* at origin t = the same work's features at t-12 by the same rules (missing when t-12 is after L or the work is
#      unmatched).  This uses only data dated by the end of t-12.
#   C7 'Scored rows' in the summary = the keys of l_books_in_time/preds.parquet (origins 2019-01 to 2026-07); the AZ test scores those
#      with origin on or before L (record).
#
# Inputs: data/db/wiki_led/l_books_in_time/rows.parquet (and preds.parquet keys for the counts), n_more_signals/amazon_matches.parquet
#   (n21), n_more_signals/amazon/ratings_item_month.parquet, ratings_month_totals.parquet and the n20/n21 summaries.
# Outputs: data/db/wiki_led/n_more_signals/feat_AZ.parquet (work_id, format, mi, AZ_n, AZ_r, AZ_3, AZ_cum, AZ_rating, AZl_n, AZl_r,
#   AZl_3, AZl_cum, AZl_rating; row order of rows.parquet restricted to mi <= 2026*12+6, asserted) and amazon_summary.json.
# Run from handoff/:  nice -n 10 bash jobs/bg.sh n22_amazon -I main_study/wiki_led/n_more_signals/n22_amazon_features.py
import sys, os, json, time, hashlib, pathlib, resource, warnings
import numpy as np, pandas as pd, pyarrow.parquet as pq

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
DB = ROOT / 'data' / 'db'
L_DIR = DB / 'wiki_led' / 'l_books_in_time'
OUT = DB / 'wiki_led' / 'n_more_signals'
AZ = OUT / 'amazon'
MI_MAX = 2026 * 12 + 6                                          # origins up to 2026-07
FEATS = ['n', 'r', '3', 'cum', 'rating']
T0 = time.time()
warnings.simplefilter('ignore', RuntimeWarning)
try:
    os.nice(5)
except OSError:
    pass


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30:.2f}GB',
          *a, flush=True)


def ym(mi):
    return f'{mi // 12}-{mi % 12 + 1:02d}'


def last_usable(tot):                                           # C1
    t = tot.set_index('mi').n.reindex(range(int(tot.mi.min()), int(tot.mi.max()) + 1), fill_value=0)
    v = t.to_numpy().astype(float)
    mis = t.index.to_numpy()
    med = np.full(len(v), np.nan)
    for i in range(12, len(v)):
        med[i] = np.median(v[i - 12:i])
    ok = (med > 0) & (v >= 0.5 * med)
    assert ok.any()
    L = int(mis[np.flatnonzero(ok)[-1]])
    tail = [dict(month=ym(int(m)), total=int(x), median_12_before=None if np.isnan(d) else float(d), qualifies=bool(q))
            for m, x, d, q in zip(mis[-15:], v[-15:], med[-15:], ok[-15:])]
    return L, tail


def win_sum(A, k):                                              # sum over g-k+1 .. g along axis 1
    c = np.cumsum(A, axis=1)
    out = c.copy()
    out[:, k:] -= c[:, :-k]
    return out


def main():
    assert sys.flags.isolated, 'run with python -I'
    R = pd.read_parquet(L_DIR / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R = R[R.mi <= MI_MAX].reset_index(drop=True)
    log('rows up to 2026-07', len(R), 'works', R.work_id.nunique())
    T = pd.read_parquet(OUT / 'amazon_matches.parquet')
    tot = pd.read_parquet(AZ / 'ratings_month_totals.parquet')
    L, tail = last_usable(tot)
    log('last usable month', ym(L), 'months with ratings', ym(int(tot.mi.min())), 'to', ym(int(tot.mi.max())))
    for x in tail:
        log('  ', x)

    RT = pq.read_table(AZ / 'ratings_item_month.parquet', filters=[('parent_asin', 'in', list(set(T.parent_asin)))]).to_pandas()
    WM = T[['work_id', 'parent_asin']].merge(RT, on='parent_asin').groupby(['work_id', 'mi'])[['n', 'rsum']].sum().reset_index()
    works = np.sort(T.work_id.unique())                         # every matched work (C2), with or without ratings
    widx = pd.Series(np.arange(len(works)), index=works)
    G0 = min(int(tot.mi.min()), int(R.mi.min()) - 24)
    G1 = max(int(tot.mi.max()), int(R.mi.max()))
    G = G1 - G0 + 1
    N = np.zeros((len(works), G), np.float64)
    S = np.zeros((len(works), G), np.float64)
    wi = widx.loc[WM.work_id].to_numpy()
    gi = WM.mi.to_numpy() - G0
    np.add.at(N, (wi, gi), WM.n.to_numpy())
    np.add.at(S, (wi, gi), WM.rsum.to_numpy())
    assert N.sum() == WM.n.sum()
    log('matched works', len(works), 'with ratings', int((N.sum(1) > 0).sum()), 'grid', ym(G0), 'to', ym(G1))

    # features at every grid month g (C2 to C5)
    P = np.pad(N, ((0, 0), (6, 0)))
    win6 = np.lib.stride_tricks.sliding_window_view(P, 6, axis=1)[:, :G]     # months g-6 .. g-1
    med6 = np.median(win6, axis=-1)
    n12 = win_sum(N, 12)
    F = {
        'n': np.log1p(N),
        'r': np.log((1 + N) / (1 + med6)),
        '3': np.log1p(win_sum(N, 3)),
        'cum': np.log1p(np.cumsum(N, axis=1)),
        'rating': np.where(n12 > 0, win_sum(S, 12) / np.where(n12 > 0, n12, 1), np.nan),
    }
    after = (np.arange(G) + G0) > L
    for k in F:
        F[k] = F[k].astype(np.float32)
        F[k][:, after] = np.nan
    # spot check of the definitions, written out directly, on 20 works with ratings and three months each
    ws = np.flatnonzero(N.sum(1) > 0)
    nchk = 0
    for w in ws[::max(1, len(ws) // 20)][:20]:
        for g in (L - G0, L - G0 - 7, int(np.flatnonzero(N[w])[-1]) if np.flatnonzero(N[w])[-1] <= L - G0 else L - G0 - 1):
            c12 = N[w, g - 11:g + 1].sum()
            e = {'n': np.log1p(N[w, g]), 'r': np.log((1 + N[w, g]) / (1 + np.median(N[w, g - 6:g]))), '3': np.log1p(N[w, g - 2:g + 1].sum()),
                 'cum': np.log1p(N[w, :g + 1].sum()), 'rating': S[w, g - 11:g + 1].sum() / c12 if c12 > 0 else np.nan}
            for k in FEATS:
                assert np.isclose(F[k][w, g], e[k], rtol=1e-5, atol=1e-5, equal_nan=True), (k, F[k][w, g], e[k])
            nchk += 1
    log('spot check of the definitions passed on', nchk, 'work-months')

    # rows (C5, C6)
    ri = R.work_id.map(widx).to_numpy()
    matched = ~np.isnan(ri)
    ri = np.where(matched, ri, 0).astype(np.int64)
    out = R[['work_id', 'format', 'mi']].copy()
    for pre, lag in (('AZ', 0), ('AZl', 12)):
        gi = R.mi.to_numpy() - lag - G0
        assert gi.min() >= 0 and gi.max() < G
        for k in FEATS:
            v = F[k][ri, gi]
            v[~matched] = np.nan
            out[f'{pre}_{k}'] = v.astype(np.float32)
    tmp = OUT / 'feat_AZ.tmp'
    out.to_parquet(tmp, index=False)
    os.replace(tmp, OUT / 'feat_AZ.parquet')

    # order check against a fresh read of rows.parquet
    R2 = pd.read_parquet(L_DIR / 'rows.parquet', columns=['work_id', 'format', 'mi'])
    R2 = R2[R2.mi <= MI_MAX].reset_index(drop=True)
    Fx = pd.read_parquet(OUT / 'feat_AZ.parquet')
    assert len(Fx) == len(R2) and (Fx.work_id.to_numpy() == R2.work_id.to_numpy()).all() and (Fx.mi.to_numpy() == R2.mi.to_numpy()).all() \
        and (Fx.format.astype(str).to_numpy() == R2.format.astype(str).to_numpy()).all(), 'feat_AZ rows differ from rows.parquet'
    assert all(Fx[c].dtype == np.float32 for c in Fx.columns[3:])
    g = Fx.groupby(['work_id', 'mi'])[[f'AZ_{k}' for k in FEATS]].nunique(dropna=False)
    assert (g.max() <= 1).all(), 'features differ across formats of a work'
    log('feat_AZ written and checked', len(Fx))

    # summary (counts only)
    PK = pd.read_parquet(L_DIR / 'preds.parquet', columns=['work_id', 'format', 'mi'])
    PK['format'] = PK.format.astype(str)
    X = Fx.assign(format=Fx.format.astype(str)).merge(PK, on=['work_id', 'format', 'mi'], how='inner')
    assert len(X) == len(PK) == 1258807, (len(X), len(PK))
    Xs = X[X.mi <= L]
    rs = json.loads((AZ / 'ratings_summary.json').read_text())
    ms = json.loads((AZ / 'meta_summary.json').read_text())
    mt = json.loads((OUT / 'amazon_match_summary.json').read_text())
    summ = dict(
        record='prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json part_2_amazon_reviews',
        meta_lines_read=ms['lines'], meta_items_kept=ms['items'], meta_lines_dropped={k: ms[k] for k in ('empty', 'bad_json', 'not_object', 'bad_asin', 'too_long')},
        meta_duplicate_parent_asin=ms['duplicate_parent_asin'], meta_items_with_isbn10=ms['with_isbn10'], meta_items_with_isbn13=ms['with_isbn13'],
        meta_items_with_author=ms['with_author'],
        ratings_rows_read=rs['lines'], ratings_rows_kept=rs['kept'],
        ratings_rows_dropped={k: rs[k] for k in ('empty', 'bad_fields', 'bad_asin', 'bad_rating', 'bad_ts', 'ts_out_of_window', 'too_long')},
        ratings_items=rs['items'], ratings_item_months=rs['item_months'],
        months_first=ym(int(tot.mi.min())), months_last=ym(int(tot.mi.max())), months_with_ratings=int((tot.n > 0).sum()),
        last_usable_month=ym(L), last_usable_mi=L, months_tail=tail,
        works_matched=mt['works_matched'], works_matched_by_route=mt['works_matched_by_route'],
        works_matched_isbn_by_source=mt['works_matched_isbn_by_source'], items_matched=mt['items_matched'],
        matched_works_with_ratings_by_last_usable_month=int((N[:, :L - G0 + 1].sum(1) > 0).sum()),
        rows_to_2026_07=int(len(Fx)), rows_with_AZ=int(Fx.AZ_n.notna().sum()), rows_with_AZl=int(Fx.AZl_n.notna().sum()),
        scored_rows=int(len(X)), scored_rows_origin_to_last_usable=int(len(Xs)),
        share_scored_rows_to_last_usable_with_AZ=float(Xs.AZ_n.notna().mean()),
        share_scored_rows_to_last_usable_with_AZ_rating=float(Xs.AZ_rating.notna().mean()),
        share_scored_rows_to_last_usable_with_AZl=float(Xs.AZl_n.notna().mean()),
        share_all_scored_rows_with_AZ=float(X.AZ_n.notna().mean()),
        share_scored_rows_to_last_usable_with_AZ_n_above_0=float((Xs.AZ_n > 0).mean()),
        scored_rows_to_last_usable_by_year=Xs.groupby(Xs.mi // 12).size().to_dict(),
        finished=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    (OUT / 'amazon_summary.json').write_text(json.dumps(summ, indent=1, default=int))
    log(summ)


if __name__ == '__main__':
    main()
