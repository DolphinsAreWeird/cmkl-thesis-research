#!/usr/bin/env python3
"""Test F, step 90 (tests only): a mock world for testing steps 20 to 28 without any real sorting and without any real effect.

A mock world is a folder with a file MOCK (holding the mock seed); every analysis script that is pointed at it with --root switches to mock
mode: borrowing is shuffled across themes and months before use, reports stay inside the folder, mock-only options are allowed.
The layout is the real one: input chunks with a header line (pages_chunk_NN.tsv, pages_sample1day_chunk_NN.tsv, books_chunk_NN.tsv,
rel_pages.tsv, rel_books.tsv, judge_pages.tsv), jobs.tsv (job, kind, input, from_line, to_line, output; pages in parts of 1,250 lines,
books in parts of 625, reliability in parts of 500, the judge in parts of 200) and the answers out/<job>.tsv without a header.
  --stage sort   random theme assignments of real page titles and real Seattle works, written as answer files with deliberate faults
                 (codes outside the guide, malformed tokens, a missing line, a duplicate line, spaces for tabs, lower-case codes, four
                 codes, an unknown kind, a header line, a code fence, one unanswered job), a second pass, and judge answers.
  --stage reask  (after 20_parse_outputs.py) answers to reask_pages_input.tsv as the main session would add them: a new job in jobs.tsv,
                 every item fixed except one still invalid and two not answered.
  --stage views  (after 20_parse_outputs.py) synthetic daily views for the S2 pages in views_store/, the batch layout of
                 22_download_views.py, leaving out the first --leave-for-download pages so that 22 can fetch them for real (a live check).
                 Thirty themes get theme-wide bursts of 4 to 10 weeks so that lasting rises exist.
Titles and work ids are real (the top-500 list and the 20,000 most borrowed works, chosen as 04_books.py does); everything else is random.
Run from code/:  ../.venv/bin/python main_study/wiki_led/testF/90_mock_world.py --out DIR --stage sort|reask|views [--seed 7]
"""
import sys, pathlib, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T

PAGE_HDR = ['id', 'title', 'description', 'first_sentence']
BOOK_HDR = ['id', 'title', 'author', 'headings', 'tags', 'description']


def answer_codes(rng, codes, k=None):
    k = k or int(rng.choice([1, 2, 3], p=[0.45, 0.35, 0.2]))
    cs = list(rng.choice(codes, k, replace=False))
    conf = sorted(rng.choice([1, 2, 3], k, p=[0.2, 0.35, 0.45]), reverse=True)
    return cs, conf


def fmt(cs, conf):
    return ','.join(f'{c}:{f}' for c, f in zip(cs, conf))


def write_input(out, name, header, rows):
    (out / name).write_text('\n'.join('\t'.join(map(str, r)) for r in [header] + rows) + '\n')


def chunk_inputs(out, prefix, ids_titles, header, size=2500):
    """Write prefix_chunk_NN.tsv files; returns [(input name, number of data lines)]."""
    files = []
    for k in range(0, len(ids_titles), size):
        part = ids_titles[k:k + size]
        name = f'{prefix}_chunk_{k // size + 1:02d}.tsv'
        write_input(out, name, header, [[i, t] + [''] * (len(header) - 2) for i, t in part])
        files.append((name, len(part)))
    return files


def jobs_for(inp, n, part, kind, stem):
    """Jobs over the data lines 2..n+1 of an input file, in parts of `part` lines, suffixes a, b, c, d."""
    rows = []
    for j, a in enumerate(range(2, n + 2, part)):
        b = min(a + part - 1, n + 1)
        job = f'{stem}_{"abcdefgh"[j]}'
        rows.append(dict(job=job, kind=kind, input=inp, from_line=a, to_line=b, output=f'out/{job}.tsv'))
    return rows


def page_answers(rng, codes, ids, first, faults, with_header=False, with_fence=False):
    kinds = list(T.KINDS)
    lines = ['id\tkind\tcodes'] if with_header else []
    if with_fence:
        lines.append('```')
    for k, i in enumerate(ids):
        kind = rng.choice(kinds)
        if rng.random() < 0.22:
            line = f'{i}\t{kind}\tnone'; first[i] = []
        else:
            cs, conf = answer_codes(rng, codes); first[i] = cs; line = f'{i}\t{kind}\t{fmt(cs, conf)}'
        if k == 3:
            line = f'{i}\t{kind}\tB99.M99.N99:3'; faults[i] = 'code not in guide'
        elif k == 5:
            line = f'{i}\t{kind}\t{codes[0]}-3'; faults[i] = 'malformed'
        elif k == 7:
            faults[i] = 'missing'; continue
        elif k == 9:
            line = line.replace('\t', ' ')                              # spaces instead of tabs (accepted)
        elif k == 11:
            line = line.lower()                                        # lower-case codes (accepted)
        elif k == 13:
            cs, conf = answer_codes(rng, codes, 3)
            extra = rng.choice([c for c in codes if c not in cs])
            line = f'{i}\t{kind}\t{fmt(cs, conf)},{extra}:1'; first[i] = cs  # four codes: the first three are kept
        elif k == 15:
            line = f'{i}\tfranchise\t{codes[1]}:3'; first[i] = [codes[1]]      # unknown kind (kept)
        elif k == 17:
            lines.append(line)                                         # duplicate line (the first is kept)
        lines.append(line)
    if with_fence:
        lines.append('```')
    return lines


def stage_sort(out, seed, n_pages, n_one):
    rng = np.random.default_rng(seed)
    codes = sorted(T.load_guide(None, strict=False)[0])
    td = T.top_days_count()
    uni = td[td.top_days >= 2].sort_values('title')
    one = td[td.top_days == 1].sort_values('title')
    ex = [t for t in T.PROMPT_EXAMPLES if t in set(uni.title)]
    pick = uni[~uni.title.isin(ex)].sample(n_pages - len(ex), random_state=seed)
    U = pd.concat([uni[uni.title.isin(ex)], pick]).sample(frac=1, random_state=seed + 1)
    O = one.sample(n_one, random_state=seed + 2)
    U = pd.concat([U.assign(set='universe'), O.assign(set='sample1day')], ignore_index=True)
    U['id'] = [f'p{k + 1:05d}' for k in range(len(U))]
    U = U.rename(columns={'top_days': 'n_top_days'})
    U['order'] = np.arange(len(U))
    U[['id', 'title', 'set', 'n_top_days', 'order']].to_parquet(out / 'universe.parquet', index=False)
    Pg = U[['id', 'title', 'set']].copy()
    Pg['prompt_example'] = Pg.title.isin(T.PROMPT_EXAMPLES)
    Pg.to_parquet(out / 'pages.parquet', index=False)
    (out / 'out').mkdir(exist_ok=True)
    jobs = []
    for prefix, sub, stem in (('pages', Pg[Pg.set == 'universe'], 'pages'), ('pages_sample1day', Pg[Pg.set == 'sample1day'], 'sample1day')):
        for name, n in chunk_inputs(out, prefix, list(zip(sub.id, sub.title.str.replace('_', ' '))), PAGE_HDR):
            jobs += jobs_for(name, n, 1250, 'pages', stem + name[len(prefix):-4])
    W = pd.read_parquet(T.D / 'db' / 'taxonomy_v3' / 'spl_works.parquet', columns=['work_id', 'title', 'checkouts_total'])
    W = W.sort_values(['checkouts_total', 'work_id'], ascending=[False, True], kind='stable').head(20000)[['work_id', 'title']]
    W = W.sample(frac=1, random_state=seed + 3).reset_index(drop=True)
    W['id'] = [f'b{k + 1:05d}' for k in range(len(W))]
    W[['id', 'work_id', 'title']].to_parquet(out / 'books.parquet', index=False)
    for name, n in chunk_inputs(out, 'books', list(zip(W.id, W.title)), BOOK_HDR):
        jobs += jobs_for(name, n, 625, 'books', name[:-4])
    # reliability and judge inputs
    rel_p = Pg[(Pg.set == 'universe') & ~Pg.prompt_example].sample(1000, random_state=seed + 4)
    write_input(out, 'rel_pages.tsv', PAGE_HDR, [[i, t, '', ''] for i, t in zip(rel_p.id, rel_p.title)])
    jobs += jobs_for('rel_pages.tsv', 1000, 500, 'pages', 'rel_pages')
    rel_b = W.sample(500, random_state=seed + 5)
    write_input(out, 'rel_books.tsv', BOOK_HDR, [[i, t, '', '', '', ''] for i, t in zip(rel_b.id, rel_b.title)])
    jobs += jobs_for('rel_books.tsv', 500, 500, 'books', 'rel_books')
    jp = Pg[(Pg.set == 'universe') & ~Pg.prompt_example].sample(400, random_state=seed + 6).reset_index(drop=True)
    jp['part'] = ['hard case'] * 100 + ['random'] * 300
    jp['drawn_as'] = ['A review (same-named page)'] * 34 + ['B adaptation'] * 33 + ['C routing disagreement (unrelated)'] * 33 + ['random'] * 300
    jp = jp.sample(frac=1, random_state=seed + 7).reset_index(drop=True)
    jp['position'] = np.arange(1, 401)
    jp[['position', 'id', 'title', 'part', 'drawn_as']].to_csv(out / 'judge_set_info.csv', index=False)
    write_input(out, 'judge_pages.tsv', PAGE_HDR, [[i, t, '', ''] for i, t in zip(jp.id, jp.title)])
    jobs += [dict(job='judge_a', kind='judge', input='judge_pages.tsv', from_line=2, to_line=201, output='out/judge_a.tsv'),
             dict(job='judge_b', kind='judge', input='judge_pages.tsv', from_line=202, to_line=401, output='out/judge_b.tsv')]
    J = pd.DataFrame(jobs)
    J.to_csv(out / 'jobs.tsv', sep='\t', index=False)
    # answers: every job answered except the last part of the main pages (its items stay 'not sorted')
    first, faults = {}, {}
    page_jobs = J[(J.kind == 'pages') & ~J.input.str.startswith('rel_')]
    skip = page_jobs[page_jobs.input.str.startswith('pages_chunk_')].job.iloc[-1]
    def ids_of(r):
        lines = (out / r.input).read_text().split('\n')
        return [ln.split('\t')[0] for ln in lines[r.from_line - 1:r.to_line] if ln.strip()]
    for k, r in enumerate(page_jobs.itertuples()):
        if r.job == skip:
            continue
        lines = page_answers(rng, codes, ids_of(r), first, faults, with_header=(k == 0), with_fence=(k == 1))
        (out / r.output).write_text('\n'.join(lines) + '\n')
    bfirst = {}
    for r in J[(J.kind == 'books') & ~J.input.str.startswith('rel_')].itertuples():
        lines = []
        for k, i in enumerate(ids_of(r)):
            if rng.random() < 0.08:
                lines.append(f'{i}\tnone'); bfirst[i] = []; continue
            cs, conf = answer_codes(rng, codes)
            bfirst[i] = cs
            lines.append(f'{i}\t{fmt(cs, conf)}' if k != 10 else f'{i}\tB01.M01:3')        # one invalid (a middle code) per job
        (out / r.output).write_text('\n'.join(lines) + '\n')
    # second pass
    for r in J[J.input == 'rel_pages.tsv'].itertuples():
        lines = []
        for k, i in enumerate(ids_of(r)):
            u = rng.random()
            if k == 4:
                lines.append(f'{i}\tconcept\tB98.M01.N01:3'); continue                # invalid
            if k == 6:
                continue                                                            # missing
            if u < 0.55 and first.get(i):
                cs = first[i]; conf = [3] * len(cs)
            elif u < 0.65:
                lines.append(f'{i}\tconcept\tnone'); continue
            else:
                cs, conf = answer_codes(rng, codes)
            lines.append(f'{i}\tconcept\t{fmt(cs, conf)}')
        (out / r.output).write_text('\n'.join(lines) + '\n')
    for r in J[J.input == 'rel_books.tsv'].itertuples():
        lines = []
        for i in ids_of(r):
            cs, conf = (bfirst[i], [3] * len(bfirst[i])) if (rng.random() < 0.6 and bfirst.get(i)) else answer_codes(rng, codes)
            lines.append(f'{i}\t{fmt(cs, conf)}')
        (out / r.output).write_text('\n'.join(lines) + '\n')
    # judge
    for r in J[J.kind == 'judge'].itertuples():
        lines = []
        for k, i in enumerate(ids_of(r)):
            if r.job == 'judge_b' and k == 8:
                continue                                                            # one page without an answer
            mis = 'yes' if rng.random() < 0.15 else 'no'
            f1 = first.get(i, [])
            u = rng.random()
            cs = list(f1[:2]) if (u < 0.5 and f1) else ([] if u < 0.6 else answer_codes(rng, codes)[0])
            about = 'a mock topic' if k != 2 else 'a mock\ttopic with a tab'
            if k == 4:
                cs = cs + ['B97.M01.N01']
            lines.append(f'{i}\t{about}\t{",".join(cs) if cs else "none"}\tmisleading_title: {mis}')
        (out / r.output).write_text('\n'.join(lines) + '\n')
    T.write_json(dict(seed=seed, pages=len(Pg), books=len(W), faults=faults, unanswered_job=skip), out / 'mock_info.json')
    T.log(f'mock sort written: {len(Pg):,} pages ({(Pg.set == "universe").sum():,} universe), {len(W):,} books, {len(J)} jobs '
          f'({skip} left unanswered), {len(faults)} faulty page lines')


def stage_reask(out, seed):
    rng = np.random.default_rng(seed + 50)
    codes = sorted(T.load_guide(None, strict=False)[0])
    f = out / 'reask_pages_input.tsv'
    if not f.exists():
        raise SystemExit('reask_pages_input.tsv not found: run 20_parse_outputs.py first')
    ids = [ln.split('\t')[0] for ln in f.read_text().split('\n')[1:] if ln.strip()]
    lines = []
    for k, i in enumerate(ids[:-2]):                                               # the last two are not answered
        if k == 0:
            lines.append(f'{i}\tconcept\tB98.M01.N01:2')                           # still invalid after the re-ask
        else:
            cs, conf = answer_codes(rng, codes)
            lines.append(f'{i}\tconcept\t{fmt(cs, conf)}')
    (out / 'out' / 'reask_pages_a.tsv').write_text('\n'.join(lines) + '\n')
    J = pd.read_csv(out / 'jobs.tsv', sep='\t')
    J = pd.concat([J, pd.DataFrame([dict(job='reask_pages_a', kind='pages', input='reask_pages_input.tsv', from_line=2, to_line=len(ids) + 1,
                                         output='out/reask_pages_a.tsv')])], ignore_index=True)
    J.to_csv(out / 'jobs.tsv', sep='\t', index=False)
    T.log(f're-ask answers written for {len(ids) - 2} of {len(ids)} items (one still invalid)')


def stage_views(out, seed, leave):
    rng = np.random.default_rng(seed + 100)
    P = T.Paths(out)
    A = T.read_assign(P, 'pages')
    sel = T.s2_selection(A, T.top_days_count())
    sel = sel[sel.selected].reset_index(drop=True)
    titles = list(sel.title[leave:])
    n = len(T.DAYS)
    dow = np.array([1.0, 1.05, 1.05, 1.0, 0.95, 0.85, 0.9])[T.DAYS.weekday]
    par = A[(A.conf >= 2) & A.title.isin(set(titles))]
    themes = rng.choice(sorted(par.code.unique()), min(30, par.code.nunique()), replace=False)
    burst_pages = {}
    for th in themes:
        for _ in range(int(rng.integers(1, 3))):
            st = int(rng.integers(400, n - 120)); ln = int(rng.integers(28, 71)); mult = float(rng.uniform(3, 6))
            for t in par[par.code == th].title:
                burst_pages.setdefault(t, []).append((st, ln, mult))
    for b in range(0, len(titles), 500):
        tt = titles[b:b + 500]
        V = np.zeros((len(tt), n), dtype=np.int64)
        for i, t in enumerate(tt):
            base = np.exp(rng.normal(5.0, 1.2))
            x = base * dow * np.exp(rng.normal(0, 0.25, n))
            born = int(rng.integers(0, n // 3)) if rng.random() < 0.2 else 0
            for _ in range(int(rng.poisson(1.5))):
                st = int(rng.integers(0, n - 60)); ln = int(rng.integers(3, 60)); x[st:st + ln] *= rng.uniform(2, 10)
            for st, ln, mult in burst_pages.get(t, []):
                x[st:st + ln] *= mult
            x[:born] = 0
            V[i] = np.round(x)
        np.savez_compressed(P.views / f'batch_mock_{b // 500:04d}.npz', titles=np.array(tt), views=V.astype(np.int32), status=np.full(len(tt), 200, dtype=np.int16))
    T.log(f'mock views written for {len(titles):,} pages (left for the live download: {leave}); theme bursts in {len(themes)} themes')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', required=True)
    ap.add_argument('--stage', choices=['sort', 'reask', 'views'], required=True)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--pages', type=int, default=10500)
    ap.add_argument('--one-day', type=int, default=600)
    ap.add_argument('--leave-for-download', type=int, default=5)
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    if out == T.REAL_DIR.resolve():
        raise SystemExit('refusing to write a mock world into the real Test F folder')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'MOCK').write_text(str(a.seed))
    if a.stage == 'sort':
        stage_sort(out, a.seed, a.pages, a.one_day)
    elif a.stage == 'reask':
        stage_reask(out, a.seed)
    else:
        stage_views(out, a.seed, a.leave_for_download)


if __name__ == '__main__':
    main()
