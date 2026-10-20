# 51. Test E data: independent checks of the rows and the report data/reports/wiki_led_test_e_data.md.
# Reads the files written by 50_test_e_data.py (rows, links, months, needed articles, build info); fits nothing and relates no feature
# to listens. The checks recompute a random sample of rows book by book from data/db/listening.parquet and the Internet Archive
# public dates in data/interim/recordings_linked.pkl with code written separately from the vectorised build, and compare the
# rows kept and dropped with the rules.
#   nice ../.venv/bin/python main_study/wiki_led/51_test_e_report.py        (from code/; about 30 seconds)
import sys, json, time, pathlib, hashlib, resource, warnings
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

warnings.filterwarnings('ignore', category=RuntimeWarning)
D = pathlib.Path(D)
OUT = D / 'db' / 'wiki_led'
REP = D / 'reports'
T0 = time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), f'{time.time() - T0:6.0f}s', *a, flush=True)


def mi_of(ym):
    return int(ym[:4]) * 12 + int(ym[5:7]) - 1


def ym_of(mi):
    return f'{int(mi) // 12}-{int(mi) % 12 + 1:02d}'


R = pd.read_parquet(OUT / 'test_e_rows.parquet')
L = pd.read_parquet(OUT / 'test_e_links.parquet')
M = pd.read_csv(OUT / 'test_e_months.csv')
NEED = pd.read_csv(OUT / 'test_e_articles_needed.csv')
INFO = json.loads((OUT / 'test_e_build_info.json').read_text())
NCOL = R.shape[1]
EXCL = sorted(M.mi[M.excluded])
EXCL_YM = [ym_of(m) for m in EXCL]
assert EXCL_YM == sorted(INFO['excluded'])

# ---------------------------------------------------------------- independent check of the rows
lis = pd.read_parquet(D / 'db' / 'listening.parquet')
lis = lis[lis.book_id != '-1']
lis['mi'] = lis.period.str[:4].astype(int) * 12 + lis.period.str[5:7].astype(int) - 1
LK = pd.read_pickle(D / 'interim' / 'recordings_linked.pkl')
LK = LK[(LK.n_authors == 1) & (LK.bookgroup != -1)].copy()
LK['book_id'] = LK.bookgroup.astype(str)
pm_ = pd.to_datetime(LK.publicdate, utc=True).dt.tz_localize(None)
LK['pub_mi'] = pm_.dt.year * 12 + pm_.dt.month - 1
pub_first = LK.groupby('book_id').pub_mi.min()
rec_pub = LK.groupby('book_id').pub_mi.apply(lambda s: sorted(s.fillna(-1e9)))
W0 = mi_of('2017-01')
rng = np.random.default_rng(20261020)
all_books = np.array(sorted(lis.book_id.unique(), key=int))
origins = [m for m in range(mi_of('2017-12'), mi_of('2026-07') + 1) if m not in EXCL and (m + 1) not in EXCL]
near = [e + d for e in EXCL for d in (-12, -11, -6, -5, -2, -1, 1, 2, 11, 12) if (e + d) in origins]
pairs = {(str(b), int(m)) for b, m in zip(rng.choice(all_books, 1500), rng.choice(origins, 1500))}      # random book and origin
pairs |= {(str(b), int(m)) for b in rng.choice(all_books, 60, replace=False) for m in near}            # origins around excluded months
full_books = {str(b) for b in rng.choice(all_books, 60, replace=False)}                                 # every origin of these books
need_books = {b for b, _ in pairs} | full_books
series = {b: g.set_index('mi').listens for b, g in lis[lis.book_id.isin(need_books)].groupby('book_id')}
rows_idx = R.set_index(['book_id', 'mi'])
bad, n_in, n_out, n_cmp = {}, 0, 0, 0


def expected(b, m):
    s = series[b]
    pm = pub_first.get(b)
    dated = bool(pd.notna(pm)) and pm >= W0

    def val(k):                                    # missing: excluded month or before the first public month
        if k in EXCL or (dated and k < pm):
            return np.nan
        return float(s[k])

    def raw(k):                                    # the recorded value, 0 before the first public month
        return 0.0 if (dated and k < pm) else float(s[k])

    w12 = [val(k) for k in range(m - 11, m + 1)]
    w6 = [val(k) for k in range(m - 5, m + 1)]
    Lt, Ln = val(m), val(m + 1)
    M6 = np.nanmedian(w6) if np.isfinite(w6).any() else np.nan
    ok = bool(np.isfinite(Lt) and np.isfinite(Ln) and np.isfinite(M6) and np.nansum(w12) >= 24)
    first = next((k for k in range(W0, m + 2) if s[k] > 0), np.nan)       # nan: no listens yet (book not public)
    exp = dict(L_t=Lt, L_next=Ln, M6=M6, h_lt=np.log1p(Lt), h_m6=np.log1p(M6), h_m12=np.log1p(np.nanmean(w12)),
               h_lt1=np.nan if (m - 1) in EXCL else np.log1p(raw(m - 1)),
               h_lyago=np.nan if (m - 11) in EXCL else np.log1p(raw(m - 11)),
               h_age=m - first, h_age_pub=m - (pm if pd.notna(pm) else first), D=np.log1p(Ln) - np.log1p(M6), Y=np.log1p(Ln),
               Sg=float(np.log1p(np.float32(Ln)) - np.log1p(np.float32(M6)) >= np.log(2) and np.float32(Ln) - np.float32(M6) >= 5),   # float32 as Test A
               n_rec=sum(1 for x in rec_pub[b] if x <= m))
    return ok, exp


def close(a, b):
    if np.isnan(a) and np.isnan(b):
        return True
    return (not np.isnan(a)) and (not np.isnan(b)) and abs(a - b) <= 1e-4 * (1 + abs(b))


for b, m in sorted(pairs):
    ok, exp = expected(b, m)
    present = (b, m) in rows_idx.index
    if ok != present:
        bad['membership'] = bad.get('membership', 0) + 1
        continue
    if present:
        n_in += 1
        row = rows_idx.loc[(b, m)]
        for c, v in exp.items():
            n_cmp += 1
            if not close(float(row[c]), float(v)):
                bad[c] = bad.get(c, 0) + 1
    else:
        n_out += 1
mem_bad, n_full = 0, 0
for b in sorted(full_books, key=int):
    got = set(R.mi[R.book_id == b])
    exp_set = {m for m in origins if expected(b, m)[0]}
    mem_bad += len(got ^ exp_set)
    n_full += len(origins)
CHECK = dict(pairs=len(pairs), rows_in_file=n_in, rows_not_in_file=n_out, values_compared=n_cmp, mismatches=bad,
             full_books=len(full_books), full_book_origin_cells=n_full, full_book_membership_errors=mem_bad)
log('independent check', json.dumps(CHECK))
assert not bad and mem_bad == 0, 'independent check failed'
assert R.duplicated(['book_id', 'mi']).sum() == 0
assert not R.mi.isin(EXCL).any() and not (R.mi + 1).isin(EXCL).any()
assert R.groupby('mi').book_id.apply(lambda s: s.map(int).is_monotonic_increasing).all()
assert (np.diff(R.mi.values) >= 0).all()

# ---------------------------------------------------------------- the Wikipedia columns in the rows equal the feature table
WFt = pd.read_parquet(OUT / 'test_e_wiki_features.parquet')
FEATS = ['lvl4', 'r4', 'r1', 'rmax', 'nrise8', 'run', 'dw', 'chg', 'valid4']
mchk = {}
for kind, key, pre in [('book', 'article', 'b_'), ('author', 'author_article', 'a_')]:
    ft_ = WFt[WFt.kind == kind].drop(columns=['kind', 'src'])
    x = R[R[key].notna()][[key, 'mi'] + [pre + c for c in FEATS]].rename(columns={key: 'article'})
    m = x.merge(ft_, on=['article', 'mi'], how='left', suffixes=('', '_f'))
    nonnull = m[pre + 'lvl4'].notna() | m['lvl4'].notna()
    diff = max(float(np.nanmax(np.abs(m.loc[nonnull, pre + c].values - m.loc[nonnull, c].values))) for c in FEATS)
    nanmis = int(sum((m[pre + c].isna() != m[c].isna()).sum() for c in FEATS))
    mchk[kind] = dict(rows_with_link=int(len(x)), rows_with_features=int(m[pre + 'lvl4'].notna().sum()), max_abs_diff=diff, nan_mismatch=nanmis)
src_missing = dict(book=int(((R.b_src > 0) & R.b_lvl4.isna()).sum()), author=int(((R.a_src > 0) & R.a_lvl4.isna()).sum()))
assert all(v['max_abs_diff'] == 0 and v['nan_mismatch'] == 0 for v in mchk.values()), mchk
del WFt
log('feature merge check', json.dumps(mchk), 'rows with a stored series but no feature', src_missing)

# ---------------------------------------------------------------- surge share the excluded target months would have had (outcome-only)
Pm = lis.pivot(index='book_id', columns='mi', values='listens')
BK = list(Pm.index)
MIc = np.array(Pm.columns)
A = Pm.values.astype(float)
for i, b in enumerate(BK):
    pm = pub_first.get(b)
    if pd.notna(pm) and pm >= W0:
        A[i, MIc < pm] = np.nan
ex_cols = np.isin(MIc, EXCL)


def surge_if_kept(m):
    j = int(m - W0)
    w6 = A[:, j - 5:j + 1].copy()
    w6[:, ex_cols[j - 5:j + 1]] = np.nan
    w12 = A[:, j - 11:j + 1].copy()
    w12[:, ex_cols[j - 11:j + 1]] = np.nan
    M6 = np.nanmedian(w6, axis=1)
    Lt, Ln = A[:, j], A[:, j + 1]
    ok = np.isfinite(M6) & np.isfinite(Lt) & np.isfinite(Ln) & (np.nansum(w12, axis=1) >= 24)
    Dd = np.log1p(Ln) - np.log1p(M6)
    sg = (Dd >= np.log(2)) & (Ln - M6 >= 5)
    return float(sg[ok].mean()), float(np.median(Dd[ok])), int(ok.sum())


kept_if = {ym_of(e - 1): surge_if_kept(e - 1) for e in EXCL}
del A, Pm
Ln_ = R.L_next.astype(np.float64)
M6_ = R.M6.astype(np.float64)
sg64 = ((np.log1p(Ln_) - np.log1p(M6_)) >= np.log(2)) & (Ln_ - M6_ >= 5)
dbl = (Ln_ == 2 * M6_ + 1)
ROUND = dict(exact_doublings=int(dbl.sum()), doublings_with_5_more=int((dbl & (Ln_ - M6_ >= 5)).sum()), surge_among_them=int(R.Sg[dbl & (Ln_ - M6_ >= 5)].sum()),
             differ_from_float64=int((sg64.astype(int) != R.Sg).sum()), surge_rate_if_all_count=float(((R.Sg == 1) | (dbl & (Ln_ - M6_ >= 5))).mean()))
del Ln_, M6_, sg64, dbl
ta = pd.read_parquet(OUT / 'test_a_rows.parquet', columns=['mi', 'Sg'])
sg_test_a = float(ta.Sg[ta.mi >= mi_of('2019-01')].mean())
del ta

# ---------------------------------------------------------------- numbers for the report
ft = '{:,}'.format
pc = lambda x, d=1: f'{100 * x:.{d}f}%'
n_rows = len(R)
rows_file = OUT / 'test_e_rows.parquet'
sha = hashlib.sha256(rows_file.read_bytes()).hexdigest()
R['hasb'] = R.b_lvl4.notna()
R['hasa'] = R.a_lvl4.notna()
R['rise15'] = R.D >= np.log(1.5)
scored = R.mi >= mi_of('2019-01')
by_year = R.groupby('year').agg(books=('book_id', 'nunique'), rows=('mi', 'size'), origins=('mi', 'nunique'), bookpage=('has_book_page', 'mean'),
                                hasb=('hasb', 'mean'), authpage=('has_author_page', 'mean'), hasa=('hasa', 'mean'), sg=('Sg', 'mean'),
                                rise=('rise15', 'mean'), jump=('flag_jump', 'mean'))


def year_table(df):
    out = ['| target year | books | rows | origin months | rows per month | book page flag | b_ features present | author page flag | a_ features present | surge rate (Sg) | D >= ln 1.5 | rows with flag_jump |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for y, r in df.iterrows():
        out.append(f'| {y} | {ft(int(r.books))} | {ft(int(r.rows))} | {int(r.origins)} | {ft(int(r.rows / r.origins))} | {pc(r.bookpage)} | {pc(r.hasb)} | {pc(r.authpage)} | {pc(r.hasa)} | {pc(r.sg, 2)} | {pc(r.rise)} | {pc(r.jump)} |')
    t = R
    out.append(f'| **all** | **{ft(t.book_id.nunique())}** | **{ft(len(t))}** | **{t.mi.nunique()}** | **{ft(int(len(t) / t.mi.nunique()))}** | **{pc(t.has_book_page.mean())}** | **{pc(t.hasb.mean())}** | **{pc(t.has_author_page.mean())}** | **{pc(t.hasa.mean())}** | **{pc(t.Sg.mean(), 2)}** | **{pc(t.rise15.mean())}** | **{pc(t.flag_jump.mean())}** |')
    return '\n'.join(out)


lt = L.listens_total.values
tot_listens = lt.sum()
has_b = (L.book_src > 0).values
has_a = (L.author_src > 0).values
inrows = (L.rows > 0).values
cov = [('book article linked', L.book_article.notna().values),
       ('book article linked and weekly views stored', has_b),
       ('author article linked', L.author_article.notna().values),
       ('author article linked and weekly views stored', has_a),
       ('weekly views stored for the book or the author article', has_b | has_a),
       ('weekly views stored for both', has_b & has_a)]


def cov_table():
    out = ['| group of books | books | of these with at least one row | share of all listens | rows | share of rows |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name, m in cov:
        out.append(f'| {name} | {ft(int(m.sum()))} | {ft(int((m & inrows).sum()))} | {pc(lt[m].sum() / tot_listens)} | {ft(int(L.rows.values[m].sum()))} | {pc(L.rows.values[m].sum() / n_rows)} |')
    out.append(f'| all books | {ft(len(L))} | {ft(int(inrows.sum()))} | 100.0% | {ft(n_rows)} | 100.0% |')
    return '\n'.join(out)


# months table
MT = M.copy()
jump_m = MT.median_jump.fillna(False).astype(bool)


def status(r, isj):
    t = []
    if r.excluded:
        t.append('excluded')
    elif isj:
        t.append('break and jump' if r.ym == '2018-08' else 'jump')
    if r.sample_days_above_3x > 0 and not r.excluded:
        t.append('flood day')
    if r.ym in ('2018-11', '2018-12'):
        t.append("Test A rule fires")
    return ', '.join(t)


MT['status'] = [status(r, bool(j)) for r, j in zip(MT.itertuples(), jump_m)]


def month_table():
    out = ['| month | listens, all books | median book, books public before 2017 | ratio to trailing 12-month median of the total | origin rows | surge share (target = next month) | median D | note |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in MT.itertuples():
        rr = '' if pd.isna(r.ratio_to_trailing12) else f'{r.ratio_to_trailing12:.2f}'
        org = '' if pd.isna(r.rows_as_origin) else ft(int(r.rows_as_origin))
        sg = '' if pd.isna(r.share_Sg) else pc(r.share_Sg)
        md = '' if pd.isna(r.median_D) else f'{r.median_D:+.2f}'
        out.append(f'| {r.ym} | {ft(int(r.total_listens))} | {int(r.median_older_books)} | {rr} | {org} | {sg} | {md} | {r.status} |')
    return '\n'.join(out)


MT = MT.assign(p10_prev=MT.p10_older_books.shift(1), med_prev=MT.median_older_books.shift(1), tot_prev=MT.total_listens.shift(1),
               sg_before=MT.share_Sg.shift(1))
jump_rows = MT[jump_m & ~MT.excluded]


def jump_table():
    out = ['| month | median book | month before | ratio | 10th percentile ratio | total ratio | surge share at the origin before |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in jump_rows.itertuples():
        sgb = '' if pd.isna(r.sg_before) else pc(r.sg_before)
        out.append(f'| {r.ym} | {int(r.median_older_books)} | {int(r.med_prev)} | {r.median_older_books / r.med_prev:.2f} | {r.p10_older_books / r.p10_prev:.2f} | {r.total_listens / r.tot_prev:.2f} | {sgb} |')
    return '\n'.join(out)


MT['year'] = MT.ym.str[:4]
yr = MT.groupby('year').agg(med=('median_older_books', 'median'), tot=('total_listens', 'median'))
flood = MT[(MT.sample_days_above_3x > 0) & ~MT.excluded]
nm = L.author_name_exact
linked_a = L.author_article.notna()
n_conf_b, n_conf_a = int((L.book_link == 'conflict').sum()), int((L.author_link == 'conflict').sum())
n_part_b, n_part_a = int((L.book_link == 'partial').sum()), int((L.author_link == 'partial').sum())
paren_books = int(L.author_article_paren.sum())
paren_titles = L.author_article[L.author_article_paren].nunique()
tag = L[L.book_title_tag_nonbook & L.book_article.notna()]
tag_s = tag[tag.book_src > 0]
doubt = tag_s[tag_s.book_article.str.startswith(('A Christmas Carol', 'The Great Gatsby', 'Porgy', 'The Wonderful Wizard of Oz'))]
n_cc = int(doubt.book_article.str.startswith('A Christmas Carol').sum())
n_gg = int(doubt.book_article.str.startswith('The Great Gatsby').sum())
n_po = int(doubt.book_article.str.startswith('Porgy').sum())
n_oz = int(doubt.book_article.str.startswith('The Wonderful Wizard of Oz').sum())
clean_a = int(L.author_link_clean.sum())
name_paren = int(((nm == True) & L.author_article_paren).sum())
need_a, need_b = NEED[NEED.kind == 'author'], NEED[NEED.kind == 'book']
ok_a = need_a[need_a.likely_ok]
curve = []
for n in (50, 100, 200, 500, len(ok_a)):
    top = ok_a.sort_values('priority_in_kind').head(n)
    curve.append((min(n, len(ok_a)), int(top.n_books.sum()), int(top.n_rows.sum())))
rows_no_a = int((~R.hasa).sum())
sg_flag = R.groupby('flag_jump').Sg.mean()
reg_rows = R.groupby('regime').size()
older_n = int(M.older_books.iloc[0])
med_first = M.set_index('ym').median_older_books
tot_by_ym = M.set_index('ym').total_listens
sg_o = M.dropna(subset=['share_Sg'])
hi_sg = sg_o.sort_values('share_Sg', ascending=False).head(10)
n_neg_D = int((sg_o.median_D < 0).sum())
b_distinct_s2 = int(L[L.book_src == 1].book_article.nunique())
b_distinct_raw = int(L[L.book_src == 2].book_article.nunique())
a_distinct = int(L[L.author_src == 1].author_article.nunique())
multi = int((L.n_rec > 1).sum())
n_new_in_window = int((L.pub_known & (L.pub_mi >= mi_of('2017-01'))).sum())
after_zero = INFO['zero_cells'] - INFO['pre_pub_cells']
jan = INFO['flood']
cb = INFO['check']
log('numbers ready')

ts = time.strftime('%Y-%m-%d %H:%M')
lines = []
w = lines.append
w('# Test E rows (LibriVox, another platform): data build\n')
w(f"Built {ts} by `code/main_study/wiki_led/50_test_e_data.py` ({INFO['runtime_s']} s); the independent checks and this report come from `code/main_study/wiki_led/51_test_e_report.py`. "
  f"Rows file: `data/db/wiki_led/test_e_rows.parquet` ({ft(n_rows)} rows, {NCOL} columns, {rows_file.stat().st_size / 1e6:.0f} MB, SHA-256 {sha[:16]}..., one row per book and origin month, ordered by origin month and book number). "
  "Data only: no model was fitted and no feature was related to an outcome; every number below is a count, the distribution of one column, or the base rate of the outcome by month (used to find bad months). "
  "Settings: addendum d of 20 Oct 2026, section test_E_librivox (Test A definitions with listens in place of loans, at least 24 listens over t-11..t, Wikipedia features where links and stored views exist, no new downloads). "
  "Nothing was downloaded. Rebuild: `cd code && nice ../.venv/bin/python main_study/wiki_led/50_test_e_data.py && nice ../.venv/bin/python main_study/wiki_led/51_test_e_report.py` "
  "(add `--raw-hist` to the first for the other reading of `h_lt1` and `h_lyago`, see the choices at the end).\n")

w('## In short\n')
w(f"- **Rows.** {ft(n_rows)} rows for {ft(R.book_id.nunique())} LibriVox books, {R.mi.nunique()} origin months from {ym_of(R.mi.min())} to {ym_of(R.mi.max())}; {ft(int(scored.sum()))} rows have an origin from 2019-01 on (Test A's scored period). "
  f"The first origin is 2017-12 because the listening data start in 2017-01 and a row needs 12 months. Three months are not used as origin or target ({', '.join(EXCL_YM)}).")
w(f"- **Wikipedia features.** Only series that were already stored were used. Book-article features `b_*` exist for {ft(int(has_b.sum()))} books ({pc(R.hasb.mean())} of rows), author-article features `a_*` for {ft(int(has_a.sum()))} books ({pc(R.hasa.mean())} of rows), either for {ft(int((has_b | has_a).sum()))} books ({pc((R.hasb | R.hasa).mean())} of rows). "
  f"The other rows have these columns missing, as in Test D. Not stored, and not downloaded: {ft(len(need_b))} book articles and {ft(len(need_a))} author articles, listed in `data/db/wiki_led/test_e_articles_needed.csv`.")
w(f"- **Counts.** The 12-month eligibility rule (24 listens) removes only {INFO['n_drop_elig']} book-months, because after its first public month a LibriVox book almost always has views. The surge rate (Sg) is {pc(R.Sg.mean(), 2)} over all rows and {pc(R.Sg[scored].mean(), 2)} from 2019-01 (Test A: {pc(sg_test_a, 2)} on its scored rows).")
w("- **Problems to know before scoring** (details in section 7): "
  f"(1) the Internet Archive level halved on 2 Aug 2018: rows with an origin up to 2018-06 sit wholly before it and rows with an origin from 2018-07 to 2019-06 straddle it (column `regime`); "
  f"(2) in {len(jump_rows) - 1} further months the listens of the typical book jump or fall by a factor of 1.5 or more while the total moves much less, which looks like automated traffic spread over small books and not demand (column `flag_jump`; the surge rate is {pc(sg_flag.get(1, np.nan))} on flagged rows and {pc(sg_flag.get(0, np.nan))} on the others); "
  f"(3) the author links are wrong for some authors with common names, and only the {a_distinct} authors with stored views are known to be right; (4) the book links point to an adaptation page for {len(doubt)} of the most listened books.\n")

w('## 1. What was found and where\n')
w('| Path | What it holds | Rows | Dates |')
w('| --- | --- | ---: | --- |')
w(f"| `data/db/listening.parquet` | `book_id` (text), `period` (text `YYYY-MM`), `listens` (integer). `period` is a calendar month. `listens` is the Internet Archive Views API count (non-robot, per day) summed over the days of the month and over all single-author recordings of the book (`code/ia_views.py`, `code/build_db.py`). The thesis notes that these views count page visits and downloads, not time spent listening. | {ft(INFO['n_listen_rows'])} | 2017-01 to 2026-08, 116 months for each of 7,849 book ids; no missing cell |")
w("| `data/db/books.parquet` | `book_id`, `title` (the title of the book's first recording). `book_id` is the LibriVox book group number (`bookgroup`). Group -1 collects 304 unrelated recordings and is dropped here. | 7,849 | |")
w(f"| `data/interim/recordings_linked.pkl` | The 8,854 English LibriVox recordings with `identifier` (Internet Archive item), `bookgroup`, `n_authors`, `author`, `publicdate`, `wiki_author`, `wiki_book`. Made by `code/link_titles.py` from `data/raw/wikidata_author_match.json` and `wikidata_author_works.json`. 8,568 recordings have one author (the ones summed into the listening table). `wiki_author` is set on 6,662 recordings and `wiki_book` on 1,802. | 8,854 | public dates {INFO['pub_min']} to {INFO['pub_max']}; 27 recordings without a date |")
w(f"| `data/raw/ia_views_monthly.json` | Monthly sums per recording, the source of `listening.parquet`. Rebuilt here for all {ft(len(L))} books: {INFO['bad_vs_raw']} differences. | 8,854 recordings | 2017-01 to 2026-09; 2026-09 is partial (data to {INFO['sample_last_day']}, {pc(INFO['raw_sep_over_aug'], 0)} of August) and is not used |")
w(f"| `data/raw/ia_views_daily_books.json` | Daily views of {INFO['n_sample']} recordings (the books that have a book article; {pc(INFO['sample_share_of_views'])} of all views). Used here only to date outages and floods. | {INFO['n_sample']} recordings | 2017-01-01 to {INFO['sample_last_day']} |")
w("| `data/raw/wiki_book_daily.json` | Daily English Wikipedia user views of 615 LibriVox book articles (`code/weekly_collect.py`). | 615 articles | 2016-07-01 to 2026-08-31 |")
w("| `data/db/study2r/weekly_book.parquet`, `weekly_author.parquet` | The weekly shares Test A uses (own title plus redirects kept by the screen for books). 168 LibriVox book articles and 139 LibriVox author articles are in them. | 7,427 and 3,004 articles | weeks from 2015-06-29 to 2026-09-28 |")
w("| `data/db/interest/wiki/weekly_total.parquet` | Weekly totals of all English Wikipedia user views (the denominator of the shares). | 588 weeks | 2015-06-29 to 2026-09-28 |")
w("| `data/raw/wiki_pageviews_monthly.json`, `wiki_author_pageviews_monthly.json` | Monthly views only: 615 book articles and 1,803 LibriVox author articles in the first file (885 author articles in the second). They cannot feed the weekly features and stop in 2025-06, 13 months before the last origin, so they are not used. | | 2015-07 to 2025-06 |")
w("| `data/interim/study2_panel.pkl`, `weekly_lift_panel.pkl`, `weekly_events.pkl`, `weekly_scope.json` | Derived tables of the earlier LibriVox burst studies (monthly attention, weekly panel, event list, the 615 articles and 887 recordings). Not used: the raw series they came from are stored. In the first two, `bg` = -1 is the dropped catch-all group. | | |")
w('')

w('## 2. The links\n')
w("- **One link per book.** A book (book group) is one or more recordings. A link is kept when all linked recordings of the book agree. "
  f"{n_conf_b} books have recordings with different book articles and {n_conf_a} have different author articles (for example one group holds Aristotle's Magna Moralia and his Eudemian Ethics, another holds stories by Schiller, Musaeus and Goethe); they get no link. "
  f"A further {n_part_b} books (book article) and {n_part_a} books (author article) are linked on only some of their recordings and keep the link.")
w(f"- **Counts.** Of {ft(len(L))} books, {ft(int(L.book_article.notna().sum()))} have a book article and {ft(int(linked_a.sum()))} have an author article ({ft(int((L.book_article.notna() & linked_a).sum()))} have both).")
w("- **How they were made** (`code/link_titles.py`, stored, not redone): the author's name was matched to a Wikidata person with that label or alias, and the recording's title to that person's works. The matching code took the first person returned for a name, not the best known one (its sitelink count was always 1), so a common name can land on the wrong person.")
w(f"- **Author links.** The English Wikipedia title equals the LibriVox author's name (ignoring accents, punctuation, initials and honorifics) for {ft(int((nm == True).sum()))} of {ft(int(linked_a.sum()))} linked books ({pc((nm == True).sum() / linked_a.sum())}); it differs for {ft(int((nm == False).sum()))}. "
  f"{ft(paren_books)} linked books ({paren_titles} titles) point to a title with a disambiguator such as '(footballer)', which usually means the wrong person; {ft(name_paren)} of the name matches carry one (the name is compared without it), so a clean match (same name, no disambiguator) holds for {ft(clean_a)} books ({pc(clean_a / linked_a.sum())}). Wrong persons found at the top of the list of needed articles: H. G. Wells linked to Henry Gordon Wells, William Shakespeare to William Harold Nelson Shakespeare, Joseph Conrad to a French colonel, James Allen to an Alabama politician, Henry James to a Regius Professor, Andrew Murray to a golfer. "
  f"All {a_distinct} authors that have stored weekly views are right (the {int(((L.author_src > 0) & (nm == False)).sum())} books whose name differs only spell it differently: Dostoyevsky, Le Fanu, John D. MacDonald). So the `a_*` features are safe; the author links without stored views are not, which is why `test_e_articles_needed.csv` carries `name_exact` and `likely_ok`.")
w(f"- **Book links.** In a random sample of 70 books with stored weekly book views (pandas seed 11, read by hand against title and author), 2 pointed to an adaptation page instead of the book (The Great Gatsby to the opera, A Christmas Carol to a 1988 play); multi-volume works point to the work's article, which I counted as right. "
  f"Titles ending in a tag for a play, film, opera or similar are on {len(tag)} books, {len(tag_s)} of them with stored views. My read of those {len(tag_s)}: A Christmas Carol (1988 play) on {n_cc} books, The Great Gatsby (opera) on {n_gg}, The Wonderful Wizard of Oz (2005 graphic novel) on {n_oz} and Porgy (play) on {n_po} point to an adaptation ({len(doubt)} books, {ft(int(doubt.listens_total.sum()))} listens in all, among the most listened books), "
  "while Peter Pan, Saint Joan, Antigone and Candida are plays and fit. `test_e_links.parquet` carries `book_title_tag_nonbook` so they can be dropped or checked.")
w("- The books with a book article were chosen by having an article in 2026, a look-ahead in the choice of books (not in their views or listens), as in Test A.")
w('')

w('## 3. Coverage of the Wikipedia views\n')
w(cov_table())
w('')
w(f"- Book articles: {b_distinct_s2} come from Study 2R's weekly file (the Test A pipeline) and {b_distinct_raw} from the raw daily file (the article's own title, no redirect screen). "
  f"On the {cb['raw_vs_study2r']['articles']} articles that are in both, the two sources agree on every common day; the weekly features agree to {cb['raw_vs_study2r']['max_abs_diff_without_redirects']:.0e} on {cb['raw_vs_study2r']['articles_without_redirects']} of them and differ on the "
  f"{cb['raw_vs_study2r']['articles'] - cb['raw_vs_study2r']['articles_without_redirects']} that have a redirect with traffic. So about one article in ten from the raw file may miss some redirect traffic.")
w(f"- Author articles: {a_distinct} authors, all from Study 2R's weekly file. Most LibriVox authors are not authors of Seattle books, so most are missing. An author's features are shared by all of the author's books.")
w("- Missing features are NaN (the columns are double precision, as in Test A). `b_src` is 1 (Study 2R weekly file), 2 (raw daily file) or 0 (none); `a_src` is 1 or 0.\n")

w('## 4. What the rows are\n')
w("- **Books.** The 7,848 book groups of the listening table without group -1. Listens of a book are the sum over its recordings "
  f"({ft(len(L) - multi)} books have one recording, {ft(multi)} have more; {ft(INFO['groups_new_recording_in_window'])} books gained {ft(INFO['new_recordings_in_window'])} recordings after their first public month and inside the window, which adds views from that month on). `n_rec` is the number of recordings public at the origin.")
w("- **Months.** `mi` = year x 12 + month - 1 of the origin month t; `year` and `test_year` are the year of the target month t+1. Months before a book's first public month are missing, not zero (the Internet Archive date of its earliest recording; "
  f"{ft(INFO['pre_pub_cells'])} cells, every one a stored zero; {int((L.pub_known == False).sum())} books have no date and are treated as public from 2017-01).")
w(f"- **Excluded months** (never an origin or a target, missing inside every window and in the eligibility sum, and missing for `h_lt1` and `h_lyago` when t-1 or t-11 is one): {', '.join(EXCL_YM)}. Why: " + '; '.join(f'{k}: {v}' for k, v in INFO['excluded'].items()) + '.')
w(f"- **Origins.** {R.mi.nunique()} months, {ym_of(R.mi.min())} to {ym_of(R.mi.max())}: the 104 months from 2017-12 to 2026-07 minus the 6 whose month t or t+1 is excluded ({', '.join(ym_of(m) for m in sorted({e + d for e in EXCL for d in (-1, 0)}))}). Test A's origins start in 2016-03; no LibriVox origin can come before 2017-12.")
w("- **Eligible** at t when the listens over t-11..t sum to at least 24 (excluded months and months before the first public month add nothing).")
w("- **Columns** (as Test A unless noted): `L_t`, `L_next`, `M6` (median of the listens over t-5..t, missing months skipped), `h_lt` = ln(1+L_t), `h_lt1` = ln(1+L(t-1)), `h_m6` = ln(1+M6), `h_m12` = ln(1 + mean over t-11..t, missing months skipped), `h_lyago` = ln(1+L(t-11)), "
  "`h_age` = t minus the first month with listens > 0 in this panel (Test A's formula; it is 2017-01 for every book public before 2017, so it is cut off at the start of the data), `D` = ln(1+L_next) - ln(1+M6), `Sg` = 1 when D >= ln 2 and L_next - M6 >= 5, `Y` = ln(1+L_next), `article`, `author_article`, "
  "`b_*` and `a_*` (lvl4, r4, r1, rmax, nrise8, run, dw, chg, valid4 from a verbatim copy of `article_features` in `10_test_a.py`, weeks ending on or before the origin month's end), `year`, `test_year`. "
  "Extra columns: `h_age_pub` (months since the book's first public month, the true age), `n_rec`, `regime` (0 = target before 2018-08, 1 = the span from t-11 to t+1 crosses 2018-08, 2 = after), `flag_jump` (see section 7, item 5), `has_book_page`, `has_author_page` (a link exists, whether or not views are stored), `b_src`, `a_src`.")
w("- `book_id` is text, as in `listening.parquet` and `books.parquet`. L, M6, h_* and D are float32 as in Test A. The other tables are `test_e_links.parquet` (one row per book: links, public month, flags, listens total, rows), `test_e_months.csv` (one row per month: totals, the rules, flags, outcome base rates by origin month) and `test_e_wiki_features.parquet` (features by article and origin month).\n")

w('## 5. Counts by year of the target month\n')
w("Shares are shares of rows. `flag_jump` is defined in section 7, item 5.\n")
w(year_table(by_year))
w('')
sc = R[scored]
w(f"From 2019-01 (Test A's scored period): {ft(len(sc))} rows, surge rate {pc(sc.Sg.mean(), 2)}, D >= ln 1.5 in {pc(sc.rise15.mean())}. Rows by `regime`: {ft(int(reg_rows[0]))} before the 2018 break (0), {ft(int(reg_rows[1]))} straddling it (1), {ft(int(reg_rows[2]))} after it (2).\n")

w('## 6. Month by month\n')
w("Listens are the total over the 7,848 books (all months, including the excluded ones). The median book is the median over the "
  f"{ft(older_n)} books that were public before 2017-01. The ratio is the month's total over the median of the totals of the 12 months before it (Test A's rule fires below 0.50). "
  "Origin rows, surge share and median D are by origin month t, so they describe the change from t to t+1 (empty where t or t+1 is excluded). 'flood day' = a day of the 887-recording sample above 3 times its 29-day median.\n")
w(month_table())
w('')

w('## 7. Gaps and quality problems in the listening data\n')
w(f"1. **What a listen is.** Internet Archive views count page visits and downloads of a recording, not time spent listening, and the Archive filters automated traffic with its own rule (the non-robot count used here). After a book's first public month there are only {after_zero} zero cells in the whole table, so there is no zero inflation. "
  f"The typical book (median of the {ft(older_n)} books public before 2017, median of the monthly medians) gets {int(yr.med['2019'])} views a month in 2019, {int(yr.med['2022'])} in 2022 and {int(yr.med['2025'])} in 2025.")
w(f"2. **A level break on 2 Aug 2018.** In the 887-recording daily sample the daily total halves overnight (3 to 31 August averages {INFO['break_ratio']:.2f} times July). Monthly totals fall from {ft(int(tot_by_ym['2018-07']))} in July to {ft(int(tot_by_ym['2018-08']))} in August, after rising {tot_by_ym['2018-07'] / tot_by_ym['2017-01']:.1f} times from 2017-01. "
  "It looks like a change in how the Archive classes robot traffic, not a change in demand. Rows with an origin up to 2018-06 sit entirely before it, rows with an origin from 2018-07 to 2019-06 have a span that crosses it (`regime` 1), and the 12-month features of those rows (`M6`, `h_m12`, `h_lyago`) mix both. "
  f"Test A's half-of-median rule fires on 2018-11 and 2018-12 for this reason (the trailing median still holds months from before the break), which is not missing data, so those two months stay in. The median D at the origin 2018-07 is {M.median_D[M.ym == '2018-07'].iloc[0]:+.2f}, an effect of the break and not of any book.")
w(f"3. **Outages (excluded).** {EXCL_YM[0]}: the sample has {int(M.sample_days_below_half[M.ym == EXCL_YM[0]].iloc[0])} days under half of normal and the total is {M.ratio_to_trailing12[M.ym == EXCL_YM[0]].iloc[0]:.2f} of its trailing median. "
  f"{EXCL_YM[1]}: the sample has {int(M.sample_days_below_half[M.ym == EXCL_YM[1]].iloc[0])} days under half of normal, 10 of them with no views at all (11 to 18, 20 and 23 Oct 2024); the total is {M.ratio_to_trailing12[M.ym == EXCL_YM[1]].iloc[0]:.2f} of its trailing median, so Test A's rule alone would not catch it. Both months are missing data, not low demand. "
  f"If they were kept as target months, the median D would be {kept_if['2023-11'][1]:+.2f} (origin 2023-11, {pc(1 - np.exp(kept_if['2023-11'][1]), 0)} below the usual level) and {kept_if['2024-09'][1]:+.2f} (origin 2024-09, {pc(1 - np.exp(kept_if['2024-09'][1]), 0)} below), with almost no surges ({pc(kept_if['2023-11'][0])} and {pc(kept_if['2024-09'][0])}).")
w(f"4. **One-day flood (excluded).** On 12 Jan 2025 the sample total is {M.sample_max_day_ratio[M.ym == '2025-01'].iloc[0]:.0f} times normal, {pc(jan['jan12_share_over_100'], 0)} of the {jan['jan12_n_recordings']} sampled recordings received more than 100 views that day (one received {ft(int(jan['jan12_max']))}), and the month total is {M.ratio_to_trailing12[M.ym == '2025-01'].iloc[0]:.1f} times its trailing median. "
  f"Kept as a target month, 2025-01 would give a surge share of {pc(kept_if['2024-12'][0])} (origin 2024-12, median D {kept_if['2024-12'][1]:+.2f}). Smaller flood days (more than 3 times the 29-day median in the sample) occur in "
  + ', '.join(f"{r.ym} ({int(r.sample_days_above_3x)}, up to {r.sample_max_day_ratio:.0f} times)" for r in flood.itertuples()) + ". They are kept; they move the month total by 10 to 40% and the median book by much less.")
w("5. **Months in which the typical book jumps (flagged, not removed).** The median listens of the books public before 2017 change by a factor of 1.5 or more from one month to the next in the months below (months after an excluded month have no ratio). "
  "'10th percentile ratio' is the same ratio for the 10th percentile of those books, 'total ratio' for the sum over all books.\n")
w(jump_table())
w('')
up = MT[MT.ym.isin(['2023-04', '2024-06', '2024-08'])]
w(f"   In 2023-04, 2024-06 and 2024-08 the median book is {(up.median_older_books / up.med_prev).min():.1f} to {(up.median_older_books / up.med_prev).max():.1f} times its level of the month before and the 10th percentile rises more ({(up.p10_older_books / up.p10_prev).min():.1f} to {(up.p10_older_books / up.p10_prev).max():.1f} times), while the total moves by {100 * ((up.total_listens / up.tot_prev).min() - 1):.0f} to {100 * ((up.total_listens / up.tot_prev).max() - 1):.0f}%, and the level is back within one or two months; "
  f"the median book gains {int((up.median_older_books - up.med_prev).min())} to {int((up.median_older_books - up.med_prev).max())} views and the 10th percentile book {int((up.p10_older_books - up.p10_prev).min())} to {int((up.p10_older_books - up.p10_prev).max())}. "
  f"From 2026-04 the median book stays above its earlier level ({int(med_first['2026-03'])} in 2026-03, then {int(med_first['2026-04'])}, {int(med_first['2026-05'])}, {int(med_first['2026-06'])}, {int(med_first['2026-07'])}, {int(med_first['2026-08'])}). "
  "That pattern fits automated traffic spread over the catalogue, not demand for single books, but these tables cannot prove it. In such months the surge label is true for a large share of all books (surge share by origin month, highest: "
  + ', '.join(f"{r.ym} {pc(r.share_Sg)}" for r in hi_sg.itertuples()) + f"), so a pooled surge average depends on them (flagged rows are {pc(R.flag_jump.mean())} of the rows and hold {pc((R.Sg * R.flag_jump).sum() / R.Sg.sum(), 0)} of the surge rows). "
  f"`flag_jump` = 1 when the origin month or the target month is one of the months in the table (2018-08 is the level break). It looks at the target month's platform-wide median, so it is a filter for scoring and never a feature. "
  "A within-month rank measure is not affected by a shift that moves all books alike; pooled level, change and surge measures are.")
w(f"6. **A long fall of the typical book.** The median book (public before 2017) has {int(med_first['2017-12'])} listens in 2017-12, {int(med_first['2018-07'])} in 2018-07, {int(med_first['2019-12'])} in 2019-12, {int(med_first['2021-12'])} in 2021-12, {int(med_first['2022-12'])} in 2022-12 and {int(med_first['2025-03'])} in 2025-03. "
  f"Median D is below zero in {n_neg_D} of the {len(sg_o)} origin months, so a book's own recent level is above next month's level for most of the period. The median monthly total (all books) is {yr.tot['2019'] / 1e6:.1f} million in 2019, {yr.tot['2022'] / 1e6:.1f} in 2022, {yr.tot['2024'] / 1e6:.1f} in 2024 and {yr.tot['2025'] / 1e6:.1f} in 2025.")
w(f"7. **Books that appear inside the window.** {ft(n_new_in_window)} books ({pc(n_new_in_window / len(L))}) were first public in 2017-01 or later. For them the months before the public month are missing and `h_age_pub` is the true age. The public dates end on {INFO['pub_max']}, so the data hold no book published after that and the months from 2025 on contain only older books; a new-book test is not possible on this source. The books are the 8,854 English recordings of the Spotify Research LibriVox dataset (Elisha et al., 2026; `data/raw/librivox_spotify_dataset.csv`), not the whole LibriVox catalogue, and I did not find in the project files how that set was chosen.")
w(f"8. **What a book is.** LibriVox's group number sometimes joins different works (plays by one author, a collection and one story in it, volumes of one work). {ft(multi)} books have more than one recording; they are one unit here, and a link may fit only part of them (section 2). The 304 unrelated recordings of group -1 are dropped; that group was the most listened single 'book' of the table ({ft(INFO['minus1_listens'])} views in all).")
w(f"9. **Dates.** The Internet Archive `publicdate` is the upload date of the recording, not the LibriVox release date; {INFO['recordings_without_date']} recordings of the single-author set have none. The Internet Archive API had data to {INFO['sample_last_day']} when it was pulled on 12 Oct 2026 (a lag of about three weeks), which is why 2026-08 is the last full month.")
lt_ = INFO['late_articles']
w(f"10. **Wikipedia side.** The weekly shares carry the known issues of the Wikipedia series: the Wikipedia-led work reports May to June 2025 separately (addendum d: Wikimedia bot traffic), redirect traffic is missing from the raw-file series, and weeks before an article existed count as 0 views (as in Test A), so the features of a young article show a jump when its views start. Articles whose first week with views is after 2017-06: {lt_['book_study2r'][0]} of {lt_['book_study2r'][1]} book articles from Study 2R's file, {lt_['book_raw'][0]} of {lt_['book_raw'][1]} from the raw file, {lt_['author'][0]} of {lt_['author'][1]} author articles.\n")

w('## 8. What was looked at while building (for the record)\n')
w("Before any Test E model result, in this order: the listening table (shape, zeros, totals by month); the first public month against the first month with listens; the daily sample (outage and flood days); the month totals against their trailing median (Test A's rule); the median, 10th and 90th percentile of listens of the older books by month; "
  "after the rows existed, the surge share and median D of the rows by origin month (section 6) and the shares by year (section 5), and the surge share the excluded months would have had. These are outcome-only statistics; no feature was compared with an outcome. The excluded months and `flag_jump` were chosen from the traffic series (totals, the daily sample, the median book), not from any feature or model; "
  "the factor 1.5 of `flag_jump` was set after seeing the monthly medians and is a judgement. The links, the book-link sample and the author-name check use no listening data.\n")

w('## 9. Checks (no model involved)\n')
w(f"1. **Listening table against the raw file.** Rebuilding `listens` for every book from `ia_views_monthly.json` (sum over its recordings, 116 months): {INFO['bad_vs_raw']} differing books.")
w(f"2. **Features against Test A.** The copy of `article_features` run on Study 2R's weekly series reproduces `test_a_wiki_features.parquet` exactly: book articles {cb['study2r_book']['articles']} articles, {ft(cb['study2r_book']['rows'])} article-month cells, maximum absolute difference {cb['study2r_book']['max_abs_diff']:.1f}, {cb['study2r_book']['nan_mismatch']} missing-pattern differences; author articles {cb['study2r_author']['articles']} articles, {ft(cb['study2r_author']['rows'])} cells, maximum difference {cb['study2r_author']['max_abs_diff']:.1f}, {cb['study2r_author']['nan_mismatch']} differences.")
w(f"3. **Raw daily series against Study 2R.** On the {cb['raw_vs_study2r']['articles']} articles in both sources, from origin 2017-12: {cb['raw_vs_study2r']['articles_without_redirects']} articles without a kept redirect agree to {cb['raw_vs_study2r']['max_abs_diff_without_redirects']:.0e} on every feature; the others differ because Study 2R adds redirect traffic.")
w(f"4. **Rows against an independent recomputation.** {ft(CHECK['pairs'])} random (book, origin) pairs plus the origins around the excluded months for 60 books were recomputed one book at a time from `listening.parquet` and the public dates with separate code; {ft(CHECK['rows_in_file'])} of them are in the rows file and {ft(CHECK['rows_not_in_file'])} are not, both as the rules say, and {ft(CHECK['values_compared'])} values (L_t, L_next, M6, h_lt, h_lt1, h_m6, h_m12, h_lyago, h_age, h_age_pub, D, Y, Sg, n_rec) agree: {sum(CHECK['mismatches'].values())} mismatches. "
  f"For {CHECK['full_books']} further books every origin was checked: the set of origins in the file equals the set the rules give ({ft(CHECK['full_book_origin_cells'])} cells, {CHECK['full_book_membership_errors']} differences).")
w(f"5. **Features in the rows against the feature table.** Every `b_*` and `a_*` value of the rows equals the value of `test_e_wiki_features.parquet` for the same article and origin month (book articles: {ft(mchk['book']['rows_with_features'])} rows with features out of {ft(mchk['book']['rows_with_link'])} with a link; author articles: {ft(mchk['author']['rows_with_features'])} of {ft(mchk['author']['rows_with_link'])}; maximum difference {mchk['book']['max_abs_diff']:.1f} and {mchk['author']['max_abs_diff']:.1f}, no difference in which cells are missing). Rows whose article has a stored series but no feature: {src_missing['book']} (book), {src_missing['author']} (author).")
w(f"6. **Structure.** No duplicate (book, origin); no excluded month as origin or target; rows ordered by origin month and book number; {INFO['n_drop_elig']} book-months dropped by the 24-listen rule; no row dropped for a missing M6.\n")

w('## 10. Choices where the request left room\n')
w("1. **Excluded months.** The request says only 'months where the listening data are complete'. I used documented outages and one flood (rules: at least 3 days of the sample under half of its 29-day median, or a month total above twice its trailing 12-month median). "
  f"Test A's rule (below half of the trailing median) alone would exclude {' and '.join([', '.join(list(M.ym[M.test_a_rule_low])[:-1]), list(M.ym[M.test_a_rule_low])[-1]])}, which keeps 2024-10 and 2025-01 and drops 2018-11 and 2018-12 for the wrong reason. To change the list, edit `EXCL` in `50_test_e_data.py` (a check stops the build if the rules and the list disagree).")
w("2. **Missing, not zero.** Excluded months and months before a book's first public month are missing inside M6, the 12-month mean and the eligibility sum, as Test A and Test D treat excluded months.")
w(f"3. **`h_lt1` and `h_lyago` in excluded months.** Test A and Test D read the recorded value of an excluded month for these two columns. Here they are missing ({pc(R.h_lt1.isna().mean())} and {pc(R.h_lyago.isna().mean())} of rows): the recorded value of an outage month is about half of the true one and that of 2025-01 is inflated many times. `--raw-hist` builds `test_e_rows_rawhist.parquet` with Test A's reading. A month before the first public month counts as 0, as in Test A.")
w("4. **`h_age`.** Test A's formula (months since the first month with listens in the panel) is `h_age`; the true age is `h_age_pub`. With the first formula every book public before 2017 has the same first month, so `h_age` is a calendar-time count for those books.")
w("5. **Level break and jump months.** Not removed: the request did not give a rule for them, and rows before 2019-07 are a large part of the training data of the first test years. `regime` and `flag_jump` let the analysis drop or keep them with one filter.")
w("6. **Books without a stored series.** They are in the file (the H models need them), with `b_*` and `a_*` missing. A Wikipedia-only model has nothing to predict from on those rows, so a W or HW score on this file should say which rows it uses (`b_src > 0` or `a_src > 0`).")
w("7. **Links.** Reused as stored; no new match and no clean-up of wrong ones. Conflicting links are dropped, not guessed.")
w("8. **Features for raw-file articles.** Built from the article's own title only (as `code/weekly_collect.py` fetched them); the weekly shares are made exactly as in `study2r/04_weekly_series.py`; the series starts 2016-07-01.")
w(f"9. **Rounding.** D and Sg are computed in float32 as in Test A and Test D. Exact doublings (L_next = 2 x M6 + 1, with L_next - M6 >= 5) sit on the boundary D = ln 2: {ft(ROUND['doublings_with_5_more'])} rows ({pc(ROUND['doublings_with_5_more'] / n_rows, 2)}); float32 rounding labels {ft(ROUND['surge_among_them'])} of them as surges and {ft(ROUND['doublings_with_5_more'] - ROUND['surge_among_them'])} as not (a float64 computation would differ from the stored Sg on {ft(ROUND['differ_from_float64'])} rows). The pooled surge rate is {pc(R.Sg.mean(), 3)} and would be {pc(ROUND['surge_rate_if_all_count'], 3)} if every one of them counted as a surge.")
w("10. **Prereg bookkeeping.** Choices 1, 3, 4 and 5 are not in addendum d; `prereg/DEVIATIONS.md` has no entry for them yet (this build did not touch `prereg/`).\n")

ta_cols = pd.read_parquet(OUT / 'test_a_rows.parquet', columns=['L_t', 'h_m6', 'h_age', 'mi'])
ta_sc = ta_cols[ta_cols.mi >= mi_of('2019-01')]
wrow = R[R.hasb | R.hasa]
per_m = wrow.groupby('mi').size()
train2019 = R[R.year <= 2018]
w('## 11. For the models of addendum d (E1 and E2)\n')
w("- **Columns.** The history columns of Test A (`h_lt`, `h_lt1`, `h_m6`, `h_m12`, `h_lyago`, `h_age`) and the 18 Wikipedia columns (`b_*`, `a_*`) have Test A's names and definitions, so Seattle-trained models can be applied unchanged (E2) and the same code can be retrained here (E1). "
  f"`h_lt1` and `h_lyago` have NaN in {pc(R.h_lt1.isna().mean())} and {pc(R.h_lyago.isna().mean())} of rows (LightGBM takes NaN).")
w(f"- **Scale.** The Seattle-trained models were fitted on loans: in Test A's scored rows the median `L_t` is {ta_sc.L_t.median():.0f} and the median `h_m6` is {ta_sc.h_m6.median():.2f}; here the median `L_t` is {R.L_t[scored].median():.0f} and the median `h_m6` is {R.h_m6[scored].median():.2f} (rows from 2019-01). Tree models do not extrapolate, so E2 will see inputs far above most of what the Seattle models were trained on. `h_age` is {ta_sc.h_age.median():.0f} (median, Test A) against {R.h_age[scored].median():.0f} here; `h_age_pub` has a median of {R.h_age_pub[scored].median():.0f}, closer to Test A, so which of the two columns feeds the Seattle models in E2 matters and should be fixed before the run.")
w(f"- **Rows with Wikipedia features.** {ft(len(wrow))} rows have `b_*` or `a_*` ({pc(len(wrow) / n_rows)}); per origin month: smallest {ft(int(per_m.min()))}, median {ft(int(per_m.median()))}, largest {ft(int(per_m.max()))}. A top-20 or top-50 list drawn from these rows in one month is therefore drawn from about {ft(int(per_m.median()))} books, against about {ft(int(R.groupby('mi').size().median()))} in the full file.")
w(f"- **First test year.** Rows whose target month is before 2019-01 number {ft(len(train2019))} (origins 2017-12 to 2018-11, all of regime 0 or 1, i.e. before or across the 2018 break); that is all that a model for test year 2019 can train on, and {ft(int(train2019.hasb.sum()))} of them have `b_*` and {ft(int(train2019.hasa.sum()))} have `a_*`.")
w('')
w('## 12. Articles still needed (not downloaded)\n')
w(f"The Wikimedia REST API is busy with another job, so nothing was fetched. `data/db/wiki_led/test_e_articles_needed.csv` lists the {ft(len(NEED))} linked articles with no stored weekly series: {ft(len(need_a))} author articles and {ft(len(need_b))} book articles "
  "(columns: kind, priority by listens within kind, article, api_title, LibriVox author and title of the most listened book that uses it, number of books, number of rows, listens, `likely_ok`, `name_exact`, `title_has_parenthesis`, `tag_nonbook`, `monthly_views_stored`). "
  "One daily per-article request each for 2016-07-01 to 2026-08-31 gives the series (the weekly shares are then made as here); about 2,800 requests, roughly 15 to 20 minutes at 3 a second.")
w(f"- `likely_ok` marks the articles whose title equals the LibriVox author's name and has no disambiguator (authors: {ft(len(ok_a))} of {ft(len(need_a))}) or has no play or film tag (books: {ft(int(need_b.likely_ok.sum()))} of {ft(len(need_b))}). The rest include the wrong persons named above and should not be fetched without a look.")
w(f"- Rows that would gain `a_*` features if the most listened `likely_ok` authors were fetched ({ft(rows_no_a)} rows have no `a_*` now):\n")
w('| authors fetched | books | rows | share of the rows without `a_*` |')
w('| ---: | ---: | ---: | ---: |')
for n, b, r in curve:
    w(f'| {ft(n)} | {ft(b)} | {ft(r)} | {pc(r / rows_no_a)} |')
w('')
w(f"- Monthly views to 2025-06 are stored for {ft(int(need_a.monthly_views_stored.sum()))} of the needed authors and none of the needed books; they do not replace the weekly series.\n")

w('## 13. Memory and runtime\n')
w(f"- `50_test_e_data.py`: {INFO['runtime_s']} s, peak resident memory {INFO['peak_rss_mb']} MB (limit 1,500 MB), run with `nice` 10 beside the Wikipedia views download. `51_test_e_report.py`: {round(time.time() - T0)} s, peak {round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)} MB.")
(REP / 'wiki_led_test_e_data.md').write_text('\n'.join(lines) + '\n')
log('report written', REP / 'wiki_led_test_e_data.md', '| seconds', round(time.time() - T0))
