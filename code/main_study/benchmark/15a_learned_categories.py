# Method benchmark, stage 2f (f1): categories learned from book text (addendum b, stage2_pipelines.2f.f1_categories_from_book_text).
# Works: Seattle works with at least 20 checkouts in 2016-01 to 2026-08 in any format. Text: title, SPL term phrases, subject-heading phrases and, for works linked
# to Goodreads, the first 500 characters of the description. Embedding: the taxonomy model (paraphrase-multilingual-MiniLM-L12-v2, fastembed), normalised.
# Clusters: k-means (k-means++, 3 initialisations, seed 20261013, mini-batch because of memory) with k = 86 (the number of middle themes) and k = 242 (narrow);
# each work goes to its nearest centroid with strength 1. No demand series is built or read here beyond the checkout totals used for the 20-checkout rule.
# Outputs: data/db/benchmark/stage2/learned/{works_text.parquet, emb_chunks/, clusters_k86.parquet, clusters_k242.parquet, centroids_k*.npy} and
# data/reports/benchmark_stage2_learned_categories.md (counts and cluster descriptions).
#   ../../../.venv/bin/python 15a_learned_categories.py [--phase select|text|embed|cluster|all]      (run under jobs/heavy_lock.sh)
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '3')
import sys, time, pathlib, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import _stage2_common as C

TAXO = C.ST.DB / 'taxonomy_v3'
OUT = C.OUT / 'learned'
EMB_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MIN_CHECKOUTS = 20
MI_LO, MI_HI = 2016 * 12, 2026 * 12 + 7              # 2016-01 .. 2026-08
KS = (86, 242)
CHUNK = 20000


def select_works():
    rw = pd.read_parquet(TAXO / 'spl_record_work.parquet')
    rw = pd.Series(rw.work_id.to_numpy().astype(np.int64), index=rw.record_id.to_numpy().astype(np.int64))
    rw = rw[~rw.index.duplicated()]
    tot = None
    for fmt in ('audiobook', 'ebook', 'book'):
        r = pd.read_parquet(TAXO / f'spl_rows_{fmt}.parquet', columns=['record_id', 'year', 'month', 'checkouts'])
        mi = r.year.to_numpy().astype(np.int64) * 12 + r.month.to_numpy().astype(np.int64) - 1
        r = r[(mi >= MI_LO) & (mi <= MI_HI)]
        r = r.assign(work_id=rw.reindex(r.record_id.to_numpy().astype(np.int64)).to_numpy())
        s = r[r.work_id.notna()].groupby('work_id').checkouts.sum()
        tot = s if tot is None else tot.add(s, fill_value=0)
        print(f'{time.strftime("%H:%M:%S")} {fmt}: {len(r):,} rows in the window', flush=True)
    tot = tot.rename('checkouts_window')
    tot.index = tot.index.astype(np.int64)
    sel = tot[tot >= MIN_CHECKOUTS]
    print(f'{time.strftime("%H:%M:%S")} works with checkouts in the window {len(tot):,}; with at least {MIN_CHECKOUTS}: {len(sel):,}', flush=True)
    return sel


def build_text(sel):
    W = pd.read_parquet(TAXO / 'spl_works.parquet', columns=['work_id', 'title'])
    W = W[W.work_id.isin(sel.index)].set_index('work_id')
    H = pd.read_parquet(TAXO / 'headings.parquet', columns=['heading_id', 'heading']).set_index('heading_id').heading
    wh = pd.read_parquet(TAXO / 'work_headings.parquet')
    wh = wh[wh.work_id.isin(sel.index)].sort_values(['work_id', 'share'], ascending=[True, False])
    wh = wh.groupby('work_id').head(8)
    wh['txt'] = wh.heading_id.map(H)
    heads = wh.groupby('work_id').txt.apply(lambda s: '; '.join(s.dropna().astype(str)))
    wt = pd.read_parquet(TAXO / 'work_terms.parquet')
    wt = wt[wt.work_id.isin(sel.index)].sort_values(['work_id', 'share'], ascending=[True, False]).groupby('work_id').head(6)
    terms = wt.groupby('work_id').term.apply(lambda s: '; '.join(s.astype(str)))
    link = pd.read_parquet(TAXO / 'spl_goodreads_link.parquet')
    gr = pd.read_parquet(TAXO / 'goodreads_works.parquet', columns=['gr_work_id', 'description'])
    d = link.merge(gr, on='gr_work_id', how='left').dropna(subset=['description']).drop_duplicates('work_id').set_index('work_id').description
    d = d[d.index.isin(sel.index)].str.replace(r'\s+', ' ', regex=True).str.slice(0, 500)
    out = W.copy()
    out['terms'] = terms.reindex(out.index).fillna('')
    out['headings'] = heads.reindex(out.index).fillna('')
    out['description'] = d.reindex(out.index).fillna('')
    out['text'] = (out.title.fillna('').astype(str) + '. ' + out.terms + '. ' + out.headings + '. ' + out.description).str.replace(r'(\. )+', '. ', regex=True).str.strip(' .')
    out['checkouts_window'] = sel.reindex(out.index).to_numpy()
    out = out.reset_index()
    print(f'{time.strftime("%H:%M:%S")} text for {len(out):,} works; with headings {(out.headings != "").mean():.0%}, terms {(out.terms != "").mean():.0%}, description {(out.description != "").mean():.0%}', flush=True)
    return out


def embed(T):
    from fastembed import TextEmbedding
    d = OUT / 'emb_chunks'; d.mkdir(parents=True, exist_ok=True)
    m = TextEmbedding(EMB_MODEL)
    t0 = time.time()
    n = len(T)
    for i in range(0, n, CHUNK):
        p = d / f'chunk_{i // CHUNK:04d}.npy'
        if p.exists():
            continue
        E = np.vstack([np.asarray(v, np.float32) for v in m.embed(T.text.iloc[i:i + CHUNK].tolist(), batch_size=128)])
        E /= np.linalg.norm(E, axis=1, keepdims=True)
        np.save(str(p) + '.tmp.npy', E.astype(np.float16)); os.replace(str(p) + '.tmp.npy', p)
        el = time.time() - t0
        print(f'{time.strftime("%H:%M:%S")} embedded {min(i + CHUNK, n):,}/{n:,} ({el / 60:.1f} min)', flush=True)


def cluster(T):
    from sklearn.cluster import MiniBatchKMeans
    E = np.vstack([np.load(f).astype(np.float32) for f in sorted((OUT / 'emb_chunks').glob('chunk_*.npy'))])
    assert len(E) == len(T), (len(E), len(T))
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    lines = ['# Categories learned from book text (stage 2f, f1): structure only', '',
             f'Written {time.strftime("%Y-%m-%d %H:%M")}. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (2f, f1). No demand series is read here.', '',
             f'- Works with at least {MIN_CHECKOUTS} checkouts in 2016-01 to 2026-08: {len(T):,}; text with headings {(T.headings != "").mean():.0%}, terms {(T.terms != "").mean():.0%}, a Goodreads description {(T.description != "").mean():.0%}.']
    for k in KS:
        t0 = time.time()
        km = MiniBatchKMeans(n_clusters=k, init='k-means++', n_init=3, batch_size=8192, max_iter=100, random_state=20261013, reassignment_ratio=0.01)
        lab = km.fit_predict(E)
        np.save(OUT / f'centroids_k{k}.npy', km.cluster_centers_.astype(np.float32))
        A = pd.DataFrame({'work_id': T.work_id.to_numpy(), 'cluster': lab.astype(int)})
        A.to_parquet(OUT / f'clusters_k{k}.parquet', index=False)
        sz = np.bincount(lab, minlength=k)
        lines += ['', f'## k = {k}', '', f'- fitted in {(time.time() - t0) / 60:.1f} min; cluster sizes: min {sz.min():,}, median {int(np.median(sz)):,}, max {sz.max():,}.', '']
        # describe each cluster by its most frequent title words and headings (descriptive)
        for c in np.argsort(-sz)[:25]:
            idx = np.where(lab == c)[0]
            hd = T.headings.iloc[idx].str.split('; ').explode().value_counts().head(4)
            lines.append(f'- cluster {c} ({len(idx):,} works): ' + '; '.join(f'{h} ({n})' for h, n in hd.items() if h))
    pathlib.Path(C.ST.DATA / 'reports' / 'benchmark_stage2_learned_categories.md').write_text('\n'.join(lines) + '\n')
    print(f'{time.strftime("%H:%M:%S")} clusters written', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', default='all')
    a = ap.parse_args()
    C.check_addendum()
    OUT.mkdir(parents=True, exist_ok=True)
    ph = ['select', 'text', 'embed', 'cluster'] if a.phase == 'all' else a.phase.split(',')
    if 'select' in ph:
        sel = select_works(); sel.to_frame().to_parquet(OUT / 'selected_works.parquet')
    if 'text' in ph:
        sel = pd.read_parquet(OUT / 'selected_works.parquet').checkouts_window
        T = build_text(sel); T.to_parquet(OUT / 'works_text.parquet', index=False)
    if 'embed' in ph:
        embed(pd.read_parquet(OUT / 'works_text.parquet', columns=['text']))
    if 'cluster' in ph:
        cluster(pd.read_parquet(OUT / 'works_text.parquet', columns=['work_id', 'headings', 'terms', 'description']))


if __name__ == '__main__':
    main()
