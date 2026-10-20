#!/usr/bin/env python3
"""Test B (new books), steps 2 and 3: the outcome (loans in the first six Seattle months) and the library-only features.

Settings: prereg/wiki_led_settings_2026-10-20.json, test_B_new_books (outcome, library_features_for_L_only).  Data only.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/01b_loans_library.py
Reads the record-level monthly checkouts in chunks (8 GB Mac) and keeps only the works of the authors in the population.
Writes data/db/wiki_led/test_b_loans_library.parquet and library_month_totals.csv.

loans6   = loans (all formats) in months first_ym .. first_ym+5;  Y6 = ln(1 + loans6)
fmt_*    = 1 when first_ym_<format> == first_ym (the format is available in the work's first Seattle month)
n_prior_works  = works of the same creator_key (all of spl_works) whose first_ym is before this work's first_ym
ln_prior_loans = ln(1 + loans of the creator's works in months strictly before this work's first_ym).  Loans of a work
                 before its own first_ym are zero, so this equals the sum over the earlier works of their loans before that month.
month    = calendar month of first_ym
flag_months6 = months of the six-month window that the benchmark rule marks as low (the library-wide total of a format is
                 below half of its median over the previous 12 months); a data-quality note only, no row is changed.
"""
import json, time
import numpy as np, pandas as pd, pyarrow.parquet as pq
from _common import TAXO, OUT, log, ym_to_idx, idx_to_ym, T0

FORMATS = ['book', 'ebook', 'audiobook']
NM = 512          # month index < 512 so that work_id * 512 + month index is a unique key
CH = 3_000_000


def main():
    pop = pd.read_parquet(OUT / 'test_b_population.parquet')
    wa = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'creator_key', 'first_ym', 'first_ym_book', 'first_ym_ebook',
                                                              'first_ym_audiobook'])
    log('population', len(pop), 'works in spl_works', len(wa))
    need_keys = set(pop.creator_key[pop.creator_key != ''])
    wa_need = wa[wa.creator_key.isin(need_keys)].copy()
    maxw = int(wa.work_id.max()) + 1
    need = np.zeros(maxw, bool)
    need[wa_need.work_id.to_numpy()] = True
    need[pop.work_id.to_numpy()] = True
    log('works of the population creators (all of spl_works):', len(wa_need), '; works needed in total:', int(need.sum()))

    rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    rec2work = np.full(int(rw.record_id.max()) + 1, -1, np.int32)
    rec2work[rw.record_id.to_numpy()] = rw.work_id.to_numpy().astype(np.int32)
    del rw

    totals = {f: np.zeros(NM) for f in FORMATS}      # library-wide checkouts per month index and format
    parts_k, parts_v = [], []
    unmapped = {}
    nrows = {}
    for f in FORMATS:
        pf = pq.ParquetFile(TAXO / f'spl_rows_{f}.parquet')
        n = 0
        un = 0
        for b in pf.iter_batches(batch_size=CH, columns=['record_id', 'year', 'month', 'checkouts']):
            rid = b.column('record_id').to_numpy()
            mi = ((b.column('year').to_numpy().astype(np.int64) - 2005) * 12 + b.column('month').to_numpy().astype(np.int64) - 1)
            co = b.column('checkouts').to_numpy().astype(np.int64)
            totals[f] += np.bincount(mi, weights=co, minlength=NM)
            ok = rid < len(rec2work)
            wk = np.full(len(rid), -1, np.int64)
            wk[ok] = rec2work[rid[ok]]
            un += int((wk < 0).sum())
            sel = wk >= 0
            sel[sel] = need[wk[sel]]
            key = wk[sel] * NM + mi[sel]
            u, inv = np.unique(key, return_inverse=True)
            parts_k.append(u)
            parts_v.append(np.bincount(inv, weights=co[sel]).astype(np.int64))
            n += len(rid)
        unmapped[f] = un
        nrows[f] = n
        log(f, 'rows', n, 'rows with no work', un, 'chunks so far', len(parts_k))
    key = np.concatenate(parts_k)
    val = np.concatenate(parts_v)
    del parts_k, parts_v
    u, inv = np.unique(key, return_inverse=True)
    sums = np.bincount(inv, weights=val).astype(np.int64)
    del key, val, inv
    work = (u // NM).astype(np.int64)
    ym = (u % NM).astype(np.int64)
    log('work-month cells for the needed works:', len(u))

    # ---- library-wide low months (benchmark rule), per format and any format
    flag_any = np.zeros(NM, bool)
    tot_rows = {'month_idx': np.arange(NM)}
    for f in FORMATS:
        t = totals[f]
        fl = np.zeros(NM, bool)
        nz = np.flatnonzero(t > 0)
        for m in range(max(12, nz[0] + 12), nz[-1] + 1):    # inside the data period of the format, a full 12 months after its start
            med = np.median(t[m - 12:m])
            fl[m] = bool(med > 0 and t[m] < 0.5 * med)
        flag_any |= fl
        tot_rows[f] = t
        tot_rows['flag_' + f] = fl
    lm = pd.DataFrame(tot_rows)
    lm['ym'] = idx_to_ym(lm.month_idx.to_numpy())
    lm = lm[lm.book + lm.ebook + lm.audiobook > 0].drop(columns='month_idx')
    lm['flag_any'] = lm.flag_book | lm.flag_ebook | lm.flag_audiobook
    lm.to_csv(OUT / 'library_month_totals.csv', index=False)
    log('library months flagged by the benchmark rule (2017-01 onward):', lm[(lm.ym >= 201701) & lm.flag_any].ym.tolist())
    cflag = np.concatenate([[0], np.cumsum(flag_any)])

    # ---- outcome
    pop['fidx'] = ym_to_idx(pop.first_ym.to_numpy()).astype(np.int64)
    fidx_by_work = np.full(maxw, -1, np.int64)
    fidx_by_work[pop.work_id.to_numpy()] = pop.fidx.to_numpy()
    fi = fidx_by_work[work]
    in_win = (fi >= 0) & (ym >= fi) & (ym <= fi + 5)
    loans6 = np.bincount(work[in_win], weights=sums[in_win], minlength=maxw)
    before = (fi >= 0) & (ym < fi)
    pop['loans6'] = loans6[pop.work_id.to_numpy()].astype(np.int64)
    pop['Y6'] = np.log1p(pop.loans6.to_numpy())
    first_cell = (fi >= 0) & (ym == fi)
    cells_first = np.zeros(maxw, bool)
    cells_first[work[first_cell]] = True
    n_before = int(before.sum())
    n_no_first = int((~cells_first[pop.work_id.to_numpy()]).sum())
    log('cells of population works before their first_ym:', n_before, '; works with no row in their first_ym:', n_no_first)
    pop['flag_months6'] = (cflag[np.minimum(pop.fidx.to_numpy() + 6, NM)] - cflag[pop.fidx.to_numpy()]).astype(int)

    # ---- first-month format flags
    fl_w = wa.set_index('work_id')
    for f, nm in zip(FORMATS, ['print', 'ebook', 'audiobook']):
        pop['fmt_' + nm] = (fl_w.loc[pop.work_id, 'first_ym_' + f].to_numpy() == pop.first_ym.to_numpy()).astype(int)

    # ---- library features from the creator's whole record in spl_works
    codes, keys = pd.factorize(wa_need.creator_key)
    cc_by_work = np.full(maxw, -1, np.int64)
    cc_by_work[wa_need.work_id.to_numpy()] = codes
    pop_cc = cc_by_work[pop.work_id.to_numpy()]
    pop_cc = np.where(pop.creator_key.to_numpy() == '', -1, pop_cc)      # the 2 works whose creator_key is empty have no author record
    # creator-month loans
    wcc = cc_by_work[work]
    m = wcc >= 0
    ck = wcc[m] * NM + ym[m]
    uc, invc = np.unique(ck, return_inverse=True)
    sc = np.bincount(invc, weights=sums[m]).astype(np.int64)
    ccs = uc // NM
    cs = np.cumsum(sc)
    first_idx = np.searchsorted(ccs, ccs, side='left')
    cum = cs - (cs[first_idx] - sc[first_idx])                          # cumulative loans inside the creator up to and including that month
    q = pop_cc * NM + pop.fidx.to_numpy()
    pos = np.searchsorted(uc, q, side='left') - 1
    okq = (pop_cc >= 0) & (pos >= 0)
    okq[okq] = ccs[pos[okq]] == pop_cc[okq]
    prior_loans = np.where(okq, cum[np.clip(pos, 0, None)], 0)
    pop['ln_prior_loans'] = np.log1p(prior_loans)
    pop['prior_loans'] = prior_loans.astype(np.int64)
    # number of earlier works of the creator
    wfi = ym_to_idx(wa_need.first_ym.to_numpy()).astype(np.int64)
    wk_sorted = np.sort(codes.astype(np.int64) * 1024 + wfi)
    lo = np.searchsorted(wk_sorted, pop_cc * 1024, side='left')
    hi = np.searchsorted(wk_sorted, pop_cc * 1024 + pop.fidx.to_numpy(), side='left')
    pop['n_prior_works'] = np.where(pop_cc >= 0, hi - lo, 0).astype(int)
    pop['month'] = (pop.first_ym % 100).astype(int)

    cols = ['work_id', 'first_ym', 'loans6', 'Y6', 'fmt_print', 'fmt_ebook', 'fmt_audiobook', 'n_prior_works', 'prior_loans',
            'ln_prior_loans', 'month', 'flag_months6']
    pop[cols].to_parquet(OUT / 'test_b_loans_library.parquet', index=False)
    s = dict(population=int(len(pop)), rows_per_format=nrows, rows_without_work=unmapped, cells_needed=int(len(u)),
             cells_before_first_ym=n_before, works_without_row_in_first_ym=n_no_first,
             loans6_zero=int((pop.loans6 == 0).sum()), loans6_median=float(pop.loans6.median()),
             works_with_flagged_months_in_window=int((pop.flag_months6 > 0).sum()),
             flagged_library_months=lm[(lm.ym >= 201701) & lm.flag_any].ym.tolist(), runtime_s=round(time.time() - T0))
    (OUT / 'loans_library_counts.json').write_text(json.dumps(s, indent=1))
    log(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
