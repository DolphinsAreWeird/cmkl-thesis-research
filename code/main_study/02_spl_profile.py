# 02. Descriptive profile of the SPL files (audiobook complete; ebook = frozen partial snapshot).
# Reads the Parquet tables from 01 and the API reference counts from 00. Writes data/db/taxonomy_v2/profile/*.
import os, collections, numpy as np, pandas as pd
from _common import OUT, split_subjects, save_json, snapshot

P = f'{OUT}/profile'; os.makedirs(P, exist_ok=True)
R = pd.read_parquet(f'{OUT}/spl_records.parquet')
R['format'] = R['format'].astype(str)
rows = pd.concat([pd.read_parquet(f'{OUT}/spl_rows_{f}.parquet') for f in ['audiobook', 'ebook']], ignore_index=True)
rows['format'] = rows['format'].astype(str); rows['usageclass'] = rows['usageclass'].astype(str)
rows = rows.merge(R[['record_id', 'work_key', 'title', 'creator', 'subjects']], on='record_id', how='left')
rows['has_subj'] = rows.subjects.str.strip().ne('')
rows['ym'] = rows.year.astype(int) * 100 + rows.month.astype(int)
api = pd.read_parquet(f'{OUT}/spl_api_counts.parquet')
api['ym'] = api.year * 100 + api.month
S = {'snapshot': snapshot()}

# ---------- A. overall per format ----------
def months_between(a, b):
    p = pd.period_range(pd.Period(f'{a // 100}-{a % 100:02d}', 'M'), pd.Period(f'{b // 100}-{b % 100:02d}', 'M'), freq='M')
    return [x.year * 100 + x.month for x in p]

A = {}
for f, d in rows.groupby('format'):
    have = set(d.ym.unique()); allm = months_between(min(have), max(have))
    Rf = R[R.format == f]
    A[f] = dict(rows=int(len(d)), checkouts=int(d.checkouts.sum()), first_month=int(min(have)), last_month=int(max(have)),
                n_months=len(have), missing_months=[m for m in allm if m not in have],
                distinct_raw_titles=int(Rf.title.nunique()), distinct_clean_titles=int(Rf.title_clean.nunique()),
                distinct_works=int(Rf.work_key.nunique()), distinct_creators=int(Rf.creator_key.nunique()),
                distinct_records=int(len(Rf)), usageclass=d.usageclass.value_counts().to_dict(),
                bad_year_rows=int((d.year < 2005).sum()), zero_checkout_rows=int((d.checkouts <= 0).sum()),
                rows_missing_creator=int((d.creator.fillna('').str.strip() == '').sum()))
A['both'] = dict(distinct_works=int(R.work_key.nunique()),
                 works_in_both_formats=int((R.groupby('work_key').format.nunique() == 2).sum()))
S['overall'] = A

# ---------- B. completeness against the API ----------
loc = rows.groupby(['format', 'ym']).agg(local_rows=('record_id', 'size'), local_checkouts=('checkouts', 'sum')).reset_index()
cmp_ = api.rename(columns={'materialtype': 'format'})[['format', 'ym', 'n_rows', 'checkouts']].merge(loc, on=['format', 'ym'], how='left').fillna(0)
cmp_['row_ratio'] = cmp_.local_rows / cmp_.n_rows
cmp_['status'] = np.where(cmp_.row_ratio >= 0.9999, 'complete', np.where(cmp_.local_rows == 0, 'missing', 'partial'))
cmp_ = cmp_[cmp_.format.isin(['AUDIOBOOK', 'EBOOK'])]
cmp_.to_csv(f'{P}/spl_month_completeness.csv', index=False)
S['completeness'] = {f: dict(d.status.value_counts()) for f, d in cmp_.groupby('format')}
eb = cmp_[cmp_.format == 'EBOOK'].sort_values('ym')
S['ebook_complete_months'] = dict(first=int(eb[eb.status == 'complete'].ym.min()), last=int(eb[eb.status == 'complete'].ym.max()),
                                  last_complete_run_end=int(eb[(eb.status != 'complete')].ym.min() - 1) if (eb.status != 'complete').any() else None,
                                  partial=eb[eb.status == 'partial'][['ym', 'row_ratio']].values.tolist(),
                                  n_missing=int((eb.status == 'missing').sum()))
S['api_totals'] = api.groupby('materialtype')[['n_rows', 'checkouts']].sum().to_dict('index')

# ---------- C. by year and format ----------
y = rows.groupby(['format', 'year']).apply(lambda d: pd.Series(dict(
    rows=len(d), checkouts=int(d.checkouts.sum()), active_works=d.work_key.nunique(), months=d.month.nunique(),
    share_rows_with_subjects=d.has_subj.mean(), share_checkouts_with_subjects=(d.checkouts * d.has_subj).sum() / max(1, d.checkouts.sum()))),
    include_groups=False).reset_index()
y.to_csv(f'{P}/spl_by_year_format.csv', index=False)

# ---------- D. subject field format ----------
rec_terms = R.subjects.map(split_subjects)
R['n_terms'] = rec_terms.map(len)
S['subject_format'] = dict(
    records_with_subjects=int((R.n_terms > 0).sum()), records=len(R),
    terms_per_record=R[R.n_terms > 0].n_terms.describe().round(2).to_dict(),
    records_with_double_dash=int(R.subjects.str.contains('--', regex=False).sum()),
    records_with_semicolon=int(R.subjects.str.contains(';', regex=False).sum()),
    records_with_pipe=int(R.subjects.str.contains('|', regex=False).sum()),
    common_subject_strings=R.subjects.value_counts().head(12).to_dict(),
    random_subject_strings=R[R.n_terms > 0].subjects.sample(12, random_state=0).tolist())

# ---------- E. term table ----------
rows_term = rows.groupby(['record_id']).agg(rows=('ym', 'size'), checkouts=('checkouts', 'sum')).reset_index()
rt = R[['record_id', 'format', 'work_key']].assign(term=rec_terms).explode('term').dropna(subset=['term']).merge(rows_term, on='record_id')
T = rt.groupby('term').agg(rows=('rows', 'sum'), checkouts=('checkouts', 'sum'), n_works=('work_key', 'nunique')).reset_index()
for f in ['AUDIOBOOK', 'EBOOK']:
    t2 = rt[rt.format == f].groupby('term').agg(**{f'checkouts_{f.lower()}': ('checkouts', 'sum'), f'works_{f.lower()}': ('work_key', 'nunique')}).reset_index()
    T = T.merge(t2, on='term', how='left')
# first / last year each term is seen, and share of all checkouts per year (vocabulary changes over time)
ry = rows.groupby(['record_id', 'year']).checkouts.sum().reset_index().merge(R[['record_id']].assign(term=rec_terms), on='record_id').explode('term').dropna(subset=['term'])
ty = ry.groupby(['term', 'year']).checkouts.sum().unstack(fill_value=0)
T = T.merge(ty.apply(lambda r: pd.Series(dict(first_year=int(r[r > 0].index.min()), last_year=int(r[r > 0].index.max()))), axis=1).reset_index(), on='term')
T = T.sort_values('checkouts', ascending=False).reset_index(drop=True)
T['checkout_share'] = T.checkouts / rows.checkouts.sum()
T.to_csv(f'{P}/spl_subject_terms.csv', index=False)
T.head(300).to_csv(f'{P}/spl_subject_terms_top300.csv', index=False)
tot_y = rows.groupby('year').checkouts.sum()
(ty.div(tot_y, axis=1)).round(5).to_csv(f'{P}/spl_subject_term_share_by_year.csv')
S['terms'] = dict(distinct=int(len(T)), distinct_audiobook=int(T.checkouts_audiobook.notna().sum()), distinct_ebook=int(T.checkouts_ebook.notna().sum()),
                  only_ebook=T[T.checkouts_audiobook.isna()].term.tolist(), only_audiobook=T[T.checkouts_ebook.isna()].term.tolist())

# ---------- F. works whose subject string changes ----------
ws = R.groupby('work_key').subjects.nunique()
S['works_with_several_subject_strings'] = dict(n=int((ws > 1).sum()), share=float((ws > 1).mean()))

# ---------- G. duplicates ----------
key = ['format', 'title', 'creator', 'year', 'month', 'usageclass']
dup = rows.groupby(key, observed=True).agg(n=('record_id', 'size'), n_records=('record_id', 'nunique'), checkouts=('checkouts', 'sum')).reset_index()
dd = dup[dup.n > 1]
full_key = ['format', 'record_id', 'year', 'month', 'usageclass', 'checkouts']
exact = rows.duplicated(subset=full_key, keep=False)
# what differs inside duplicate groups
dr = rows.merge(dd[key], on=key).merge(R[['record_id', 'publisher', 'publicationyear', 'isbn']], on='record_id')
diff = {c: int(dr.groupby(key, observed=True)[c].nunique().gt(1).sum()) for c in ['subjects', 'publisher', 'publicationyear', 'isbn']}
same_record = int(dr.groupby(key, observed=True).record_id.nunique().eq(1).sum())
S['duplicates'] = dict(groups=int(len(dd)), rows_in_groups=int(dd.n.sum()), share_rows=float(dd.n.sum() / len(rows)),
                       checkouts_in_groups=int(dd.checkouts.sum()), by_format=dd.groupby('format').size().to_dict(),
                       groups_where_field_differs=diff, groups_with_identical_record=same_record,
                       exact_duplicate_rows=int(exact.sum()))
dd.sort_values('n', ascending=False).head(200).to_csv(f'{P}/spl_duplicate_groups_top200.csv', index=False)
# same work (normalized), same month, several records: expected (editions), but count it
wm = rows.groupby(['format', 'work_key', 'ym']).record_id.nunique()
S['work_month_multi_records'] = dict(share_work_months=float((wm > 1).mean()), n=int((wm > 1).sum()))

# ---------- H. monthly totals, COVID period and dips ----------
m = rows.groupby(['format', 'ym']).agg(rows=('record_id', 'size'), checkouts=('checkouts', 'sum')).reset_index()
m['date'] = pd.to_datetime(m.ym.astype(str), format='%Y%m')
m = m.sort_values(['format', 'date'])
# year-on-year change by calendar month (the source has whole months missing, so row offsets would be wrong)
prev = m[['format', 'date', 'checkouts']].assign(date=m.date + pd.DateOffset(years=1)).rename(columns={'checkouts': 'checkouts_year_before'})
m = m.merge(prev, on=['format', 'date'], how='left')
m['yoy'] = m.checkouts / m.checkouts_year_before - 1
m['local_median_7'] = m.groupby('format').checkouts.transform(lambda s: s.rolling(7, center=True, min_periods=4).median())
m['ratio_to_local_median'] = m.checkouts / m.local_median_7
m.to_csv(f'{P}/spl_monthly_totals.csv', index=False)
S['dips'] = m[(m.ratio_to_local_median < 0.85)][['format', 'ym', 'checkouts', 'ratio_to_local_median']].round(3).values.tolist()
save_json(S, f'{P}/spl_profile.json')
print(pd.Series(S['overall']).to_string()[:3000])
print(S['completeness'], S['ebook_complete_months'])
print(y.round(3).to_string())
print(S['subject_format']); print(S['terms']); print(S['duplicates']); print(S['work_month_multi_records']); print(S['works_with_several_subject_strings'])
print('dips', S['dips'])
