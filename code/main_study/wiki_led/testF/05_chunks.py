#!/usr/bin/env python3
"""Test F data, step 5: chunk files for the AI sorters, the key file, the reliability sets and the judge set for check G1.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (sorter, G1_validation).  Data only: no loans are read, nothing is sorted.
Inputs (data/db/wiki_led/testF/): universe.parquet (step 1), page_text.parquet (step 2), books.parquet (step 4); for the judge set also
data/db/interest/wiki/review_title_confusion.csv, data/db/wiki_led/adaptations.parquet, the stored embedding routing of the benchmark
(data/db/benchmark/top_routing/routes.parquet, a page goes to the theme of its closest theme term when the cosine is at least 0.70) and the
stored zero-shot routing (data/db/benchmark/stage2/nli_routing/pairs.parquet, a page goes to every candidate theme with an entailment
probability of at least 0.50).

Chunk files (tab-separated, UTF-8, header line, rows in id order, 2,500 rows each, the last one shorter):
  pages_chunk_NN.tsv            id, title, description, first_sentence     the 84,577 universe pages (p00001 to p84577)
  pages_sample1day_chunk_NN.tsv same columns                               the 3,000 one-day pages (p84578 to p87577), coverage check only
  books_chunk_NN.tsv            id, title, author, headings, tags, description   the 20,000 books (b00001 to b20000)
The page title is the title of the top-500 list with spaces for underscores (the final title after redirects is in the key file); the
description and first sentence are those of the page the title leads to today.
Key: key.tsv (id, set, chunk_file, title, final_title, work_id) and pages.parquet (every page with its flags).
Reliability sets (seed 20261022, a fresh numpy default_rng for each draw, over the ids in ascending order, rows in the order drawn):
  rel_pages.tsv   1,000 universe pages, leaving out the three pages named as examples in the page instructions and every title that
                  redirects to one of them; rel_books.tsv  500 books.  Same columns as the chunks.
Judge set (seed 20261023, one numpy default_rng used in this order: A, B, C, random part, final order), 400 universe pages, the excluded
examples left out:
  up to 100 hard cases, about a third from each source:
    A  pages of review_title_confusion.csv: the 'same-named pages in top 500' of its evidence column and the pages named in the reason of a
       title-confusion verdict (the concept pages of the review are the themes' own pages, for example Mathematics, and are not used as
       hard cases); every page tied to a title-confusion verdict is taken, the rest of 34 drawn at random from the other same-named pages
    B  adaptation pages: 33 drawn from the universe pages whose title, or final title, is an article of adaptations.parquet
    C  routing disagreements: 33 drawn, 11 from each kind: both routings route the page but to unrelated themes (no theme of one equal to,
       above or below a theme of the other); only the embedding routes it; only the zero-shot classifier routes it
  the rest drawn at random from the universe; then the 400 are put in a random order.
  judge_pages.tsv (same columns as the page chunks) and judge_set_info.csv (why each page is in the set; never shown to the judge).
Also manifest.json: every file written here with its rows and SHA-256.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/05_chunks.py
"""
import sys, re, json, time, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_common as F

N_REL_PAGES, N_REL_BOOKS, N_JUDGE = 1000, 500, 400
QUOTA = dict(A=34, B=33, C=33)
C_KINDS = ('unrelated', 'embedding_only', 'zeroshot_only')
KIND_LABEL = dict(unrelated='unrelated themes', embedding_only='embedding only', zeroshot_only='zero-shot only')
PAGE_COLS = ['id', 'title', 'description', 'first_sentence']
BOOK_COLS = ['id', 'title', 'author', 'headings', 'tags', 'description']
MANIFEST = {}


def put(name, header, rows):
    p = F.OUT / name
    F.write_tsv(p, header, rows)
    back = F.read_tsv(p)
    assert back[0] == header and len(back) == len(rows) + 1
    assert all(b == [str(x) for x in r] for b, r in zip(back[1:], rows)), f'{name} does not read back as written'
    MANIFEST[name] = dict(rows=len(rows), sha256=F.sha256(p))


def page_rows(P):
    return [[r.id, r.title.replace('_', ' '), r.description, r.first_sentence] for r in P.itertuples()]


def book_rows(B):
    return [[r.id, r.title, r.author, r.headings, r.tags, r.description] for r in B.itertuples()]


def chunks(df, prefix, rows_fn, header):
    names = []
    for k in range(0, len(df), F.CHUNK):
        name = f'{prefix}_chunk_{k // F.CHUNK + 1:02d}.tsv'
        put(name, header, rows_fn(df.iloc[k:k + F.CHUNK]))
        names += [name] * len(df.iloc[k:k + F.CHUNK])
    return names


def related(a, b):
    return a == b or a.startswith(b + '.') or b.startswith(a + '.')


def review_pages(universe):
    """Pages of review_title_confusion.csv: same-named pages of the evidence and pages named in title-confusion reasons."""
    R = pd.read_csv(F.D / 'db' / 'interest' / 'wiki' / 'review_title_confusion.csv')
    rows_of = collections.defaultdict(list)          # title -> list of (row index, how)
    for i, x in R.iterrows():
        for part in str(x.evidence).split(' || '):
            m = re.search(r'same-named pages in top 500: (.*)$', part)
            if m:
                for item in m.group(1).split('; '):
                    mm = re.match(r'^(\S+) [\d,]+ \(\d\d-\d\d\)$', item.strip())
                    assert mm, f'evidence item not understood: {item!r}'
                    rows_of[mm.group(1)].append((i, 'same-named page'))
        if x.verdict == 'title_confusion':
            for tok in str(x.reason).split():
                for t in (tok, tok.rstrip(',;:.'), tok.strip(',;:.()')):
                    if '_' in t and t in universe:
                        rows_of[t].append((i, 'named in the reason'))
                        break
    info = {}
    for t, lst in rows_of.items():
        if t not in universe:
            continue
        idx = sorted(set(i for i, _ in lst))
        confusion = any(R.verdict[i] == 'title_confusion' for i in idx)
        det = '; '.join(f'{R.node_id[i]} {R.node_label[i]}, rise from {R.start_week[i]}, verdict {R.verdict[i]}' for i in idx[:3])
        hows = sorted(set(h for _, h in lst))
        info[t] = dict(confusion=confusion, detail=f'{"/".join(hows)} in review rows: {det}' + (f' (+{len(idx) - 3} more)' if len(idx) > 3 else ''))
    return info


def adaptation_pages(P):
    A = pd.read_parquet(F.D / 'db' / 'wiki_led' / 'adaptations.parquet', columns=['adapt', 'article', 'book', 'adaptLabel'])
    A = A.dropna(subset=['article']).drop_duplicates(['article', 'adapt', 'book'])
    by_art = A.groupby('article').apply(lambda g: '; '.join(f'{a} "{l}" (based on {b})' for a, l, b in zip(g.adapt[:2], g.adaptLabel[:2], g.book[:2]))
                                        + (f' (+{len(g) - 2} more)' if len(g) > 2 else ''), include_groups=False)
    out = {}
    for r in P.itertuples():
        fu = r.final_title.replace(' ', '_') if isinstance(r.final_title, str) else ''
        if r.title in by_art.index:
            out[r.title] = f'adaptation article (Wikidata {by_art[r.title]})'
        elif fu and fu in by_art.index:
            out[r.title] = f'redirects to the adaptation article {fu} (Wikidata {by_art[fu]})'
    return out


def routing_disagreements(universe):
    R = pd.read_parquet(F.D / 'db' / 'benchmark' / 'top_routing' / 'routes.parquet', columns=['title', 'node_id', 'cos', 'routed'])
    R = R[R.routed & R.title.isin(universe)]
    emb = dict(zip(R.title, zip(R.node_id, R.cos)))
    Z = pd.read_parquet(F.D / 'db' / 'benchmark' / 'stage2' / 'nli_routing' / 'pairs.parquet', columns=['title', 'node_id', 'p_entail'])
    Z = Z[(Z.p_entail >= 0.5) & Z.title.isin(universe)].sort_values(['title', 'p_entail'], ascending=[True, False], kind='stable')
    Z = Z.drop_duplicates(['title', 'node_id'])                  # two candidate terms of one theme: the theme once, with its highest p
    zs = {t: list(zip(g.node_id, g.p_entail)) for t, g in Z.groupby('title')}
    out, counts = {}, collections.Counter()
    for t in sorted(set(emb) | set(zs)):
        e, z = emb.get(t), zs.get(t, [])
        if e is None:
            kind = 'zeroshot_only'
        elif not z:
            kind = 'embedding_only'
        elif any(related(e[0], n) for n, _ in z):
            kind = 'agree'
        else:
            kind = 'unrelated'
        counts[kind] += 1
        if kind != 'agree':
            det = ('embedding: ' + (f'{e[0]} (cosine {e[1]:.2f})' if e else 'none') + '; zero-shot: '
                   + (', '.join(f'{n} (p {p:.2f})' for n, p in z) if z else 'none'))
            out[t] = (kind, det)
    return out, dict(counts)


def main():
    t0 = time.time()
    U = pd.read_parquet(F.OUT / 'universe.parquet')
    T = pd.read_parquet(F.OUT / 'page_text.parquet')
    assert len(T) == len(U) == 87577
    P = U.merge(T.drop(columns=['set']), on=['id', 'title'], how='left', validate='one_to_one').sort_values('id').reset_index(drop=True)
    assert P.status.notna().all()
    B = pd.read_parquet(F.OUT / 'books.parquet').sort_values('id').reset_index(drop=True)

    # prompt examples and every title that leads to the same page
    ex_final = set(P.loc[P.title.isin(F.PROMPT_EXAMPLES), 'final_title'])
    assert len(ex_final) == 3, ex_final
    P['prompt_example'] = P.final_title.isin(ex_final) & (P.status == 'page')
    F.log(f'prompt examples and titles leading to them: {P.loc[P.prompt_example, "title"].tolist()}')

    # ---- chunk files
    Pu = P[P.set == 'universe']
    Ps = P[P.set == 'sample1day']
    assert (Pu.id.str[1:].astype(int) == np.arange(1, len(Pu) + 1)).all()
    P['chunk_file'] = chunks(Pu, 'pages', page_rows, PAGE_COLS) + chunks(Ps, 'pages_sample1day', page_rows, PAGE_COLS)
    B['chunk_file'] = chunks(B, 'books', book_rows, BOOK_COLS)

    # ---- reliability sets
    elig = np.sort(P.loc[(P.set == 'universe') & ~P.prompt_example, 'id'].to_numpy())
    rel_p = elig[np.random.default_rng(F.SEED_REL).choice(len(elig), N_REL_PAGES, replace=False)]
    rel_b = np.sort(B.id.to_numpy())[np.random.default_rng(F.SEED_REL).choice(len(B), N_REL_BOOKS, replace=False)]
    Pi, Bi = P.set_index('id'), B.set_index('id')
    put('rel_pages.tsv', PAGE_COLS, page_rows(Pi.loc[rel_p].reset_index()))
    put('rel_books.tsv', BOOK_COLS, book_rows(Bi.loc[rel_b].reset_index()))
    P['in_rel'] = P.id.isin(rel_p)
    B['in_rel'] = B.id.isin(rel_b)

    # ---- judge set
    Ue = P[(P.set == 'universe') & ~P.prompt_example]
    uni = set(Ue.title)
    id_of = dict(zip(Ue.title, Ue.id))
    rev = review_pages(uni)
    ada = adaptation_pages(Ue)
    dis, dis_counts = routing_disagreements(uni)
    F.log(f'hard-case candidates in the universe: review {len(rev)} ({sum(v["confusion"] for v in rev.values())} tied to a title-confusion '
          f'verdict), adaptation {len(ada)}, routing disagreement {len(dis)} {dis_counts}')
    rng = np.random.default_rng(F.SEED_JUDGE)
    chosen = {}                                                   # title -> drawn_as

    def draw(cands, k, label):
        cands = sorted(t for t in cands if t not in chosen)
        k = min(k, len(cands))
        for i in rng.choice(len(cands), k, replace=False) if k else []:
            chosen[cands[i]] = label
        return k

    a1 = sorted(t for t, v in rev.items() if v['confusion'])
    for t in a1:
        chosen[t] = 'A review (title-confusion verdict)'
    draw([t for t in rev if t not in a1], QUOTA['A'] - len(a1), 'A review (same-named page)')
    draw(ada, QUOTA['B'], 'B adaptation')
    per = [QUOTA['C'] // 3 + (1 if i < QUOTA['C'] % 3 else 0) for i in range(3)]
    for kind, k in zip(C_KINDS, per):
        draw([t for t, (kd, _) in dis.items() if kd == kind], k, f'C routing disagreement ({KIND_LABEL[kind]})')
    n_hard = len(chosen)
    draw(uni, N_JUDGE - n_hard, 'random')
    assert len(chosen) == N_JUDGE and n_hard <= 100
    titles = list(chosen)
    order = rng.permutation(len(titles))
    jt = [titles[i] for i in order]
    J = P.set_index('title').loc[jt].reset_index()
    put('judge_pages.tsv', PAGE_COLS, page_rows(J))
    info = pd.DataFrame(dict(position=np.arange(1, len(jt) + 1), id=[id_of[t] for t in jt], title=jt,
                             final_title=J.final_title.to_numpy(), part=['random' if chosen[t] == 'random' else 'hard case' for t in jt],
                             drawn_as=[chosen[t] for t in jt], in_review=[t in rev for t in jt], in_adaptations=[t in ada for t in jt],
                             routing_disagreement=[dis[t][0] if t in dis else '' for t in jt],
                             review_detail=[rev[t]['detail'] if t in rev else '' for t in jt],
                             adaptation_detail=[ada.get(t, '') for t in jt],
                             routing_detail=[dis[t][1] if t in dis else '' for t in jt]))
    info.to_csv(F.OUT / 'judge_set_info.csv', index=False)
    MANIFEST['judge_set_info.csv'] = dict(rows=len(info), sha256=F.sha256(F.OUT / 'judge_set_info.csv'))
    P['in_judge'] = P.id.isin(info.id)
    assert not P.loc[P.in_judge, 'prompt_example'].any() and not P.loc[P.in_rel, 'prompt_example'].any()

    # ---- key and page table
    key = [[r.id, r.set, r.chunk_file, r.title, r.final_title if isinstance(r.final_title, str) else '', ''] for r in P.itertuples()]
    key += [[r.id, 'books', r.chunk_file, r.title, '', str(r.work_id)] for r in B.itertuples()]
    put('key.tsv', ['id', 'set', 'chunk_file', 'title', 'final_title', 'work_id'], key)
    P.drop(columns=['order']).to_parquet(F.OUT / 'pages.parquet', index=False)
    B.to_parquet(F.OUT / 'books.parquet', index=False)

    # ---- checks over all chunk files
    seen = collections.Counter()
    for name in sorted(MANIFEST):
        if '_chunk_' in name:
            seen.update(r[0] for r in F.read_tsv(F.OUT / name)[1:])
    assert max(seen.values()) == 1 and set(seen) == set(P.id) | set(B.id)
    summ = dict(chunk_files={k: v['rows'] for k, v in MANIFEST.items() if '_chunk_' in k},
                prompt_example_titles=P.loc[P.prompt_example, 'title'].tolist(),
                hard_candidates=dict(review=len(rev), review_title_confusion=len(a1), adaptation=len(ada),
                                     adaptation_by_own_title=sum(v.startswith('adaptation article') for v in ada.values()),
                                     adaptation_through_redirect=sum(v.startswith('redirects to') for v in ada.values()),
                                     routing_disagreement=len(dis), routing_counts=dis_counts),
                invalid_titles=P.loc[P.status == 'invalid', 'title'].tolist(),
                chunk_bytes={k: (F.OUT / k).stat().st_size for k in MANIFEST if k.endswith('.tsv')},
                judge_drawn_as=info.drawn_as.value_counts().to_dict(), judge_hard=int(n_hard), judge_random=int(N_JUDGE - n_hard),
                judge_in_review=int(info.in_review.sum()), judge_in_adaptations=int(info.in_adaptations.sum()),
                judge_routing_disagreement=info.routing_disagreement[info.routing_disagreement != ''].value_counts().to_dict(),
                rel_pages=len(rel_p), rel_books=len(rel_b), seconds=round(time.time() - t0, 1))
    json.dump(dict(files=MANIFEST, summary=summ), open(F.OUT / 'manifest.json', 'w'), indent=1)
    F.log(f'wrote {len(MANIFEST)} files; {summ}')


if __name__ == '__main__':
    main()
