# n01. Addendum n, part 3a, data: donor articles for the book-page and author-page placebos.  DATA ONLY (no loans related to anything).
# Settings: prereg/addenda_wiki_led/2026-11-25_n_more_signals_and_models.json, part_3_models.3a (read-only; SHA-256 checked), and the
# DEVIATIONS entry of 16:40 +07:00 on donor matching (articles first seen after 2018; donor features masked to the real missing pattern).
# Real features: rows.parquet's b_* and a_* (addendum l, F14 set).  Donor features at origin t: the donor article's features at t from
#   l_books_in_time/wiki_features.parquet, set to missing wherever the row's real feature is missing.
# Output (row order of rows.parquet up to origin 2026-07): data/db/wiki_led/n_more_signals/feat_BA.parquet (Bd_*, Ad_*), donors_BA.csv;
#   report data/reports/more_signals_n01_book_author.md
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/n_more_signals/n01_book_author.py
import sys, os, json, time, hashlib, pathlib
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-11-25_n_more_signals_and_models.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == 'f0b8650d091b94d92e9e16e46c1257b0dbf007878253e5c3e35e5f86c45fe78e', 'addendum n changed'
L = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
OUT = DATA / 'db' / 'wiki_led' / 'n_more_signals'
OUT.mkdir(parents=True, exist_ok=True)
REP = DATA / 'reports'
F14 = ['lvl4', 'r4', 'r1', 'run', 'dw', 'chg', 'valid4']
W0, W1 = 2016 * 12 + 2, 2018 * 12 + 11                       # origins 2016-03 .. 2018-12
os.nice(5)

WF = pd.read_parquet(L / 'wiki_features.parquet')
WA = pd.read_parquet(L / 'work_articles.parquet')            # work_id, book_canonical, author_canonical
M = pd.read_parquet(L / 'matches.parquet', columns=['work_id', 'creator_key'])
WA = WA.merge(M, on='work_id')


def level_table(kind):
    g = WF[(WF.kind == kind) & WF.lvl4.notna()]
    first = g.groupby('article').mi.min()
    pre = g[(g.mi >= W0) & (g.mi <= W1)].groupby('article').lvl4.median()
    g2 = g.sort_values(['article', 'mi'])
    g2['k'] = g2.groupby('article').cumcount()
    early = g2[g2.k < 24].groupby('article').lvl4.median()
    lev = pre.reindex(first.index)
    lev = lev.fillna(early)                                    # articles first seen after 2018: first 24 origins with a feature
    return pd.DataFrame({'first': first, 'level': lev, 'pre_window': first.index.isin(pre.index)})


rng = np.random.default_rng(20261125)


def donors(kind, col):
    T = level_table(kind)
    arts = T.index.to_numpy()
    lev = T.level.to_numpy(); first = T['first'].to_numpy()
    creators = WA.groupby(col).creator_key.apply(lambda s: set(s.fillna(''))) if kind == 'book' else None
    used = np.zeros(len(arts), int)
    order = rng.permutation(len(arts))
    sort_ix = np.argsort(lev)
    out = {}
    for i in order:
        a = arts[i]
        # candidates by closeness of level, eligible: first feature no later, not the same article, under 3 uses, different creator
        pos = np.searchsorted(lev[sort_ix], lev[i])
        best = None
        for step in range(1, len(arts)):
            cand = []
            for j in (pos - step, pos + step - 1):
                if 0 <= j < len(arts):
                    cand.append(sort_ix[j])
            if not cand:
                break
            for c in sorted(cand, key=lambda c: abs(lev[c] - lev[i])):
                if c == i or used[c] >= 3 or first[c] > first[i]:
                    continue
                if kind == 'book' and (creators.get(arts[c], set()) & creators.get(a, set()) - {''}):
                    continue
                best = c
                break
            if best is not None:
                break
        if best is not None:
            out[a] = arts[best]; used[best] += 1
    return out, T


DB, TB = donors('book', 'book_canonical')
DA, TA = donors('author', 'author_canonical')
pd.concat([pd.DataFrame({'kind': 'book', 'article': list(DB), 'donor': list(DB.values())}),
           pd.DataFrame({'kind': 'author', 'article': list(DA), 'donor': list(DA.values())})]).to_csv(OUT / 'donors_BA.csv', index=False)

R = pd.read_parquet(L / 'rows.parquet', columns=['work_id', 'format', 'mi'] + ['b_' + c for c in F14] + ['a_' + c for c in F14])
R = R[R.mi <= 2026 * 12 + 6].reset_index(drop=True)
R = R.merge(WA[['work_id', 'book_canonical', 'author_canonical']], on='work_id', how='left', validate='many_to_one')
out = pd.DataFrame({'work_id': R.work_id, 'format': R.format.astype(str), 'mi': R.mi})
for kind, pre, col, DMAP, dname in (('book', 'b_', 'book_canonical', DB, 'Bd_'), ('author', 'a_', 'author_canonical', DA, 'Ad_')):
    g = WF[WF.kind == kind].set_index(['article', 'mi'])[F14]
    don = R[col].map(DMAP)
    key = pd.MultiIndex.from_arrays([don.fillna('__none__'), R.mi])
    V = np.array(g.reindex(key).to_numpy(np.float32), copy=True)
    real = R[[pre + c for c in F14]].to_numpy(np.float32)
    V[np.isnan(real)] = np.nan                                 # same missing pattern as the real article
    for k, c in enumerate(F14):
        out[dname + c] = V[:, k]
sc = (out.mi >= 2019 * 12).to_numpy()
summ = dict(book_articles=len(TB), book_donors=len(DB), book_pre_window=int(TB.pre_window.sum()),
            author_articles=len(TA), author_donors=len(DA), author_pre_window=int(TA.pre_window.sum()),
            scored_rows_real_book=float(R.loc[sc, 'b_r4'].notna().mean()), scored_rows_donor_book=float(np.mean(~np.isnan(out.loc[sc, 'Bd_r4']))),
            scored_rows_real_author=float(R.loc[sc, 'a_r4'].notna().mean()), scored_rows_donor_author=float(np.mean(~np.isnan(out.loc[sc, 'Ad_r4']))))
out.to_parquet(OUT / 'feat_BA.parquet', index=False)
(OUT / 'ba_summary.json').write_text(json.dumps(summ, indent=1))
(REP / 'more_signals_n01_book_author.md').write_text('# Addendum n, part 3a: donor articles for the placebos (counts only)\n\n' +
    f'Made by `code/main_study/wiki_led/n_more_signals/n01_book_author.py` on {time.strftime("%Y-%m-%d %H:%M")} (+07:00).\n\n' +
    '\n'.join(f'- {k}: {v}' for k, v in summ.items()) + '\n')
print(json.dumps(summ, indent=1))
