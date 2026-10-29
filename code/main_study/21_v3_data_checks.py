# 21. (v3) Data checks of the Seattle snapshot against the AIC-400 data wrangling checklist (30 Oct 2026). Read-only:
# nothing that other scripts read is changed. Writes data/reports/seattle_data_checks.md and the list of placeholder
# works data/db/taxonomy_v3/quality/placeholder_works.csv (for leaving them out of per-book work from now on).
#   1. Placeholder records (checklist 2.4, mixed granularity): titles starting 'Uncataloged' (bundles of uncatalogued
#      items, mostly one per branch) and '<Unknown Title>' records with no subjects. Their loans, themes, membership of
#      Test A and Test D, and Test D's scores recomputed without them from the stored corrected predictions.
#   2. Key of the row tables (2.2): is (record, year, month) unique in each format?
#   3. Ranges (3.2): checkouts at or below 0, months outside 1 to 12, years.
#   4. Exact duplicate lines in the frozen raw snapshots (3.7): every line hashed to 64 bits (blake2b), and lines whose
#      hash repeats are compared byte for byte, so a hash collision is never counted as a duplicate.
import os
os.environ['TAXO'] = 'v3'
import re, json, time, hashlib, resource
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import spearmanr
from _common import OUT, REP, FILES, snapshot
from config import D

t0 = time.time()
snap = snapshot()
L = ['# Seattle data checks (taxonomy v3 snapshot)', '',
     f'Made by `code/main_study/21_v3_data_checks.py` on {time.strftime("%Y-%m-%d %H:%M")}. Read-only checks of the frozen '
     'snapshot against the AIC-400 data wrangling checklist (items 2.2, 2.4, 3.2 and 3.7); nothing other scripts read was changed.', '']

# ---------- 1. placeholder records ----------
rec = pd.read_parquet(f'{OUT}/spl_records.parquet', columns=['record_id', 'format', 'title', 'subjects'])
has_subj = rec.subjects.fillna('').str.strip().str.len() > 0
bundle = rec.title.str.match(r'\s*uncataloged', case=False, na=False)
unknown = rec.title.str.contains(r'<unknown title>', case=False, na=False, regex=False)
ph = rec[bundle | (unknown & ~has_subj)].assign(kind=np.where(bundle[bundle | (unknown & ~has_subj)], 'uncataloged', 'unknown title, no subjects'))
rw = pd.read_parquet(f'{OUT}/spl_record_work.parquet')
W = pd.read_parquet(f'{OUT}/spl_works.parquet', columns=['work_id', 'title', 'checkouts_book', 'checkouts_total', 'n_records'])
pw = rw[rw.record_id.isin(ph.record_id)].merge(ph[['record_id', 'kind']], on='record_id').merge(W, on='work_id')
themed = set(pd.read_parquet(f'{OUT}/work_theme.parquet', columns=['work_id']).work_id)
pw['themed'] = pw.work_id.isin(themed)
pw[['work_id', 'kind', 'title', 'checkouts_total', 'n_records', 'themed']].sort_values('checkouts_total', ascending=False) \
    .to_csv(f'{OUT}/quality/placeholder_works.csv', index=False)
tot_print = int(pq.read_table(f'{OUT}/spl_rows_book.parquet', columns=['checkouts'])['checkouts'].to_numpy().sum())
unk_subj = rec[unknown & has_subj]
L += ['## 1. Placeholder records (checklist 2.4)', '',
      '| Kind | Records | Works | Loans | Share of print loans | Works with a theme |', '| --- | --- | --- | --- | --- | --- |']
for k, g in pw.groupby('kind'):
    L.append(f'| {k} | {g.record_id.nunique():,} | {g.work_id.nunique():,} | {int(g.checkouts_total.sum()):,} | '
             f'{g.checkouts_total.sum() / tot_print:.2%} | {int(g.themed.sum()):,} |')
L += ['', f'Placeholder records by format: {ph.format.value_counts().to_dict()}. Not counted as placeholders: {len(unk_subj):,} '
      '"<Unknown Title>" records that carry subject headings, which are real items whose title is missing.', '']

ta = set(pd.read_parquet(f'{D}/db/study2r/works.parquet', columns=['work_id']).work_id)
pids = set(pw.work_id)
td = pq.read_table(f'{D}/db/wiki_led/test_d_rows_c.parquet', columns=['work_id']).to_pandas()
P = pd.read_parquet(f'{D}/db/wiki_led/test_d_preds_c.parquet')
inP = P.work_id.isin(pids)
L += [f'Test A works among them: {len(ta & pids)}. Test D corrected rows from them: {int(td.work_id.isin(pids).sum()):,} of '
      f'{len(td):,} ({td.loc[td.work_id.isin(pids), "work_id"].nunique()} works: '
      f'{", ".join(pw[pw.work_id.isin(set(td.work_id))].title.unique())}); scored rows {int(inP.sum()):,} of {len(P):,}.', '',
      'Test D scores from `data/db/wiki_led/test_d_preds_c.parquet`, as in `61c_test_d_models.py` (lists of 20 within each '
      'format and month, share that rose; mean within-month rank correlation with the change D), with and without the '
      'placeholder works. Ties are broken by a stable sort here, so a list can differ from the stored report only among tied rows.', '',
      '| Model | Top 20, all rows | Top 20, without | Placeholder slots | Not yet risen, top 20, all | without | Rank corr., all | without |',
      '| --- | --- | --- | --- | --- | --- | --- | --- |']


def top_rose(df, col, k=20):
    t = df.sort_values(col, ascending=False, kind='stable').groupby(['format', 'mi'], sort=False).head(k)
    return t.rose.mean(), int(t.work_id.isin(pids).sum())


def rank(df, col):
    return np.nanmean([spearmanr(g[col], g.D).statistic for _, g in df.groupby(['format', 'mi'])])


Q = P[~inP]
for m in ['H', 'HW', 'W']:
    a, n = top_rose(P, m); b, _ = top_rose(Q, m)
    e, _ = top_rose(P[P.not_yet], m); f, _ = top_rose(Q[Q.not_yet], m)
    L.append(f'| {m} | {a:.4f} | {b:.4f} | {n} | {e:.4f} | {f:.4f} | {rank(P, m):.4f} | {rank(Q, m):.4f} |')
L.append('')
print('placeholders done', round(time.time() - t0), 's', flush=True)

# ---------- 2 and 3. key and ranges of the row tables ----------
L += ['## 2 and 3. Key and ranges of the row tables (checklist 2.2 and 3.2)', '',
      '| Format | Rows | Distinct (record, month) | Repeated keys | Extra rows | Checkouts at or below 0 | Month outside 1-12 | Years |',
      '| --- | --- | --- | --- | --- | --- | --- | --- |']
for f in ['book', 'ebook', 'audiobook']:
    t = pq.read_table(f'{OUT}/spl_rows_{f}.parquet', columns=['record_id', 'year', 'month', 'checkouts'])
    r, y, mo, c = (t[x].to_numpy().astype(np.int64) for x in ['record_id', 'year', 'month', 'checkouts'])
    u, cnt = np.unique(r * 1_000_000 + y * 100 + mo, return_counts=True)
    L.append(f'| {f} | {len(r):,} | {len(u):,} | {int((cnt > 1).sum()):,} | {int((cnt[cnt > 1] - 1).sum()):,} | '
             f'{int((c <= 0).sum()):,} | {int(((mo < 1) | (mo > 12)).sum()):,} | {y.min()}-{y.max()} |')
    del t, r, y, mo, c, u, cnt
L += ['', 'Print records are keyed by title, creator and subjects only (`10_v3_spl_rows.py`), so editions that differ in '
      'publisher or year share a record and repeat within a month; their loans are summed, which is intended.', '']
print('keys and ranges done', round(time.time() - t0), 's', flush=True)

# ---------- 4. exact duplicate lines in the raw snapshots ----------
L += ['## 4. Exact duplicate lines in the raw snapshots (checklist 3.7)', '',
      '| File | Lines read (frozen count) | Exact duplicate lines beyond the first copy |', '| --- | --- | --- |']
examples = []
for fmt, fn in FILES.items():
    n = snap[fmt]['lines']
    h = np.empty(n, dtype=np.uint64)
    with open(fn, 'rb') as fh:
        for i, line in enumerate(fh):
            if i >= n:
                break
            h[i] = int.from_bytes(hashlib.blake2b(line.rstrip(b'\n'), digest_size=8).digest(), 'little')
    _, inv, cnt = np.unique(h, return_inverse=True, return_counts=True)
    cand = set(np.nonzero(cnt[inv] > 1)[0].tolist())
    del h, inv, cnt
    seen, dups = set(), 0
    if cand:
        with open(fn, 'rb') as fh:
            for i, line in enumerate(fh):
                if i >= n:
                    break
                if i in cand:
                    b = line.rstrip(b'\n')
                    if b in seen:
                        dups += 1
                        if len(examples) < 3:
                            examples.append(f'{fmt}: {b[:240].decode("utf-8", "replace")}')
                    else:
                        seen.add(b)
    L.append(f'| {os.path.basename(fn)} | {n:,} | {dups:,} |')
    print(fmt, 'lines', n, 'duplicates', dups, round(time.time() - t0), 's', flush=True)
L.append('')
if examples:
    L += ['Examples (first 240 characters):', ''] + [f'- `{e}`' for e in examples] + ['']
L.append(f'Run time {time.time() - t0:.0f} s; peak resident memory {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20:,.0f} MB.')
open(f'{REP}/seattle_data_checks.md', 'w').write('\n'.join(L) + '\n')
print('wrote', f'{REP}/seattle_data_checks.md', flush=True)
