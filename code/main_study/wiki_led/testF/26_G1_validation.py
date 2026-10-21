#!/usr/bin/env python3
"""Test F, step 26, check G1: how well the AI sorter, the zero-shot routing and the embedding routing agree with an independent judge.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (G1_validation): an independent Opus judge labels 400 pages (up to 100
hard cases, the rest random). Reported for the AI sorter, the zero-shot classifier routing of the benchmark (entailment p >= 0.50,
benchmark/stage2/nli_routing/pairs.parquet) and the embedding routing (cosine >= 0.70, benchmark/top_routing/routes.parquet):
  precision  the share of a method's page-theme pairs that the judge also gives,
  recall     the share of the judge's page-theme pairs that the method gives,
  misleading on pages the judge marks as having a misleading title, the share of pages the method routes to a theme the judge does not give.
Descriptive; nothing is tuned on it. The three example pages of the sorter's instructions (and titles redirecting to them) are left out.
Choices NOT IN ADDENDUM (fixed here before any judge answer exists):
  - the judge and the AI give narrow themes; the routings place pages on theme values whose node can be narrow, middle or broad. Scores
    are given at the narrow level (a routing pair counts only when its node is narrow) and at the middle level (every pair moved up to its
    middle theme: a narrow node to its parent, a middle node as it is; broad nodes are left out and counted);
  - the AI's pairs are all its pairs (confidence 1 to 3); a second row uses confidence 2 or 3 only (the pairs S2 is built from);
  - methods are compared on the judged pages that every method could route (sorted by the AI, and in the benchmark's top-500 routing
    pool); a page the method sends nowhere counts as no pair (it lowers recall, never precision);
  - 95% intervals: 2,000 bootstrap draws of judged pages (seed 20261023), percentile;
  - judge lines (read by step 20): codes outside the guide are dropped and counted; a page without a judge answer is left out and counted.
Inputs: judge_answers.parquet (the judge's answers to judge_pages.tsv, out/judge_*.tsv, parsed and checked by step 20); judge_set_info.csv of 05_chunks.py (id, title, part, drawn_as: scores are
also given for the random part, the hard cases, and each source of hard cases); assign_pages.parquet and items_pages.parquet of step 20.
Outputs: g1_scores.csv, g1_summary.json; report testF_26_G1.md.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/26_G1_validation.py [--root DIR] [--judge-key PATH]
"""
import sys, re, json, pathlib, argparse
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T

ROUTES = T.D / 'db' / 'benchmark' / 'top_routing' / 'routes.parquet'
NLI = T.D / 'db' / 'benchmark' / 'stage2' / 'nli_routing' / 'pairs.parquet'
EMB_COS, NLI_P = 0.70, 0.50
SEED, NB = 20261023, 2000


def read_judge(P):
    """The judge's answers as parsed by step 20 (judge_answers.parquet: id, about, codes checked against the guide, misleading) and the
    notes of that parse."""
    f = P / 'judge_answers.parquet'
    if not f.exists():
        raise SystemExit(f'{f} not found: run 20_parse_outputs.py after the judge jobs are answered')
    J = pd.read_parquet(f)
    J['codes'] = J.codes.map(lambda c: [str(x) for x in c] if c is not None else [])
    ps = json.loads((P / 'parse_summary.json').read_text()) if (P / 'parse_summary.json').exists() else {}
    return J[['id', 'about', 'codes', 'misleading']], Counter((ps.get('judge') or {}).get('notes') or {})


def judge_pages(P, path):
    """The judged pages: judge_set_info.csv of 05_chunks.py (id, title, part 'hard case' or 'random', drawn_as) -> id, title, group, source;
    or another file with id and title."""
    f = pathlib.Path(path) if path else P / 'judge_set_info.csv'
    if f.exists():
        K = pd.read_csv(f) if f.suffix == '.csv' else pd.read_parquet(f)
        if {'id', 'title'} <= set(K.columns):
            K['group'] = K['part'] if 'part' in K else 'all'
            K['source'] = K['drawn_as'].str.split(' ').str[0].map({'A': 'hard: title review', 'B': 'hard: adaptation', 'C': 'hard: routing disagreement',
                                                                   'random': 'random'}) if 'drawn_as' in K else 'all'
            return K[['id', 'title', 'group', 'source']], f.name
    U = T.page_key(P)
    return U[['id', 'title']].assign(group='all', source='all'), 'universe.parquet (no judge key file found; group unknown)'


def to_middle(pairs, par):
    """(id, node) pairs moved to the middle level; broad nodes dropped."""
    x = pairs.copy()
    lv = x.node.map(T.level_of)
    x.loc[lv == 3, 'node'] = x.loc[lv == 3, 'node'].map(par)
    return x[lv >= 2].drop_duplicates(), int((lv == 1).sum())


def score(method_pairs, judge_pairs, pages, misleading, rng_idx):
    """precision, recall, misleading-title share with page-bootstrap intervals, on the given pages."""
    pages = list(pages)
    pid = {p: i for i, p in enumerate(pages)}
    mp = method_pairs[method_pairs.id.isin(pid)]
    jp = judge_pairs[judge_pairs.id.isin(pid)]
    js = set(zip(jp.id, jp.node))
    hit_m = np.array([(i, n) in js for i, n in zip(mp.id, mp.node)], dtype=float)
    ms = set(zip(mp.id, mp.node))
    hit_j = np.array([(i, n) in ms for i, n in zip(jp.id, jp.node)], dtype=float)
    n = len(pages)
    # per-page sums for the bootstrap
    m_n = np.bincount(mp.id.map(pid).to_numpy(), minlength=n).astype(float)
    m_h = np.bincount(mp.id.map(pid).to_numpy(), weights=hit_m, minlength=n)
    j_n = np.bincount(jp.id.map(pid).to_numpy(), minlength=n).astype(float)
    j_h = np.bincount(jp.id.map(pid).to_numpy(), weights=hit_j, minlength=n)
    wrong = (m_n - m_h) > 0                                      # the page goes to at least one theme the judge does not give
    mis = np.array([bool(misleading.get(p, False)) for p in pages])
    out = dict(pages=n, method_pairs=int(m_n.sum()), judge_pairs=int(j_n.sum()), pages_routed=int((m_n > 0).sum()),
               precision=float(m_h.sum() / m_n.sum()) if m_n.sum() else np.nan, recall=float(j_h.sum() / j_n.sum()) if j_n.sum() else np.nan,
               misleading_pages=int(mis.sum()), misleading_wrong_share=float(wrong[mis].mean()) if mis.any() else np.nan)
    bp, br, bm = [], [], []
    for ix in rng_idx:
        a_, b_ = m_h[ix].sum(), m_n[ix].sum()
        c_, d_ = j_h[ix].sum(), j_n[ix].sum()
        bp.append(a_ / b_ if b_ else np.nan)
        br.append(c_ / d_ if d_ else np.nan)
        mm = mis[ix]
        bm.append(wrong[ix][mm].mean() if mm.any() else np.nan)
    for k, v in (('precision', bp), ('recall', br), ('misleading_wrong_share', bm)):
        v = np.array(v, dtype=float)
        v = v[~np.isnan(v)]
        out[f'{k}_lo'], out[f'{k}_hi'] = (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)
    return out


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--judge-key', default=None)
    a = ap.parse_args()
    P = T.Paths(a.root)
    guide, ginfo = T.load_guide(P)
    par = T.parent_map()
    J, notes = read_judge(P)
    K, kname = judge_pages(P, a.judge_key)
    n_unanswered = len(set(K.id) - set(J.id))
    J = J.merge(K, on='id', how='left')
    if J.title.isna().any():
        T.log(f'{int(J.title.isna().sum())} judge ids not in the judge key; left out')
        notes['id_not_in_key'] += int(J.title.isna().sum())
        J = J[J.title.notna()]
    ex = T.prompt_example_titles(P)
    n_ex = int(J.title.isin(ex).sum())
    J = J[~J.title.isin(ex)]
    # method pairs (title, node)
    A = T.read_assign(P, 'pages')
    items = pd.read_parquet(P / 'items_pages.parquet')
    sorted_titles = set(items[items.status.isin(['themes', 'none'])].title)
    R = pd.read_parquet(ROUTES, columns=['title', 'node_id', 'cos'])
    pool = set(R.title)
    emb = R[R.cos >= EMB_COS][['title', 'node_id']]
    N = pd.read_parquet(NLI, columns=['title', 'node_id', 'p_entail'])
    nli = N[N.p_entail >= NLI_P][['title', 'node_id']].drop_duplicates()
    t2id = dict(zip(J.title, J.id))
    def pairs_of(df, tcol='title', ncol='node_id'):
        x = df[df[tcol].isin(t2id)]
        return pd.DataFrame({'id': x[tcol].map(t2id).to_numpy(), 'node': x[ncol].to_numpy()}).drop_duplicates()
    methods = {'AI sorter (all pairs)': pairs_of(A, ncol='code'), 'AI sorter (confidence 2 or 3)': pairs_of(A[A.conf >= 2], ncol='code'),
               'zero-shot routing (p >= 0.50)': pairs_of(nli), 'embedding routing (cos >= 0.70)': pairs_of(emb)}
    jp = pd.DataFrame([(i, c) for i, cs in zip(J.id, J.codes) for c in cs], columns=['id', 'node'])
    covered = {'AI sorter (all pairs)': set(J[J.title.isin(sorted_titles)].id), 'AI sorter (confidence 2 or 3)': set(J[J.title.isin(sorted_titles)].id),
               'zero-shot routing (p >= 0.50)': set(J[J.title.isin(pool)].id), 'embedding routing (cos >= 0.70)': set(J[J.title.isin(pool)].id)}
    common = sorted(set.intersection(*covered.values()))
    misleading = dict(zip(J.id, J.misleading.fillna(False).astype(bool)))
    rng = np.random.default_rng(SEED)
    rows, broad_dropped = [], {}
    gof = {i: {g, s} for i, g, s in zip(J.id, J.group, J.source)}
    groups = ['all'] + sorted({g for g in J.group.dropna().unique()} | {s for s in J.source.dropna().unique()} - {'all'})
    for scope, pages_of in (('common pages', lambda m: common), ('pages each method covers', lambda m: sorted(covered[m]))):
        for grp in groups:
            for m, mp in methods.items():
                pg = [p for p in pages_of(m) if grp == 'all' or grp in gof.get(p, set())]
                if not pg:
                    continue
                idx = rng.integers(0, len(pg), size=(NB, len(pg)))
                for level in ('narrow', 'middle'):
                    if level == 'narrow':
                        mpl = mp[mp.node.map(T.level_of) == 3]
                        jpl = jp
                    else:
                        mpl, nb_ = to_middle(mp[mp.id.isin(pg)], par)
                        jpl, _ = to_middle(jp, par)
                        if scope == 'common pages' and grp == 'all':
                            broad_dropped[m] = nb_
                    rows.append(dict(scope=scope, group=grp, method=m, level=level, **score(mpl, jpl, pg, misleading, idx)))
    S = pd.DataFrame(rows)
    S.to_csv(P / 'g1_scores.csv', index=False)
    summ = dict(judge_lines=len(J) + n_ex, judged_pages_without_answer=n_unanswered, judge_notes=dict(notes), judge_key=kname,
                prompt_examples_left_out=n_ex, pages_scored=len(J),
                common_pages=len(common), covered={k: len(v) for k, v in covered.items()}, misleading_pages=int(J.misleading.fillna(False).sum()),
                judge_none=int((J.codes.map(len) == 0).sum()), broad_routings_left_out_at_middle=broad_dropped, mock=P.mock)
    T.write_json(summ, P / 'g1_summary.json')
    L = [f'# Test F, check G1: agreement with the independent judge ({P.tag()})', '',
         f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; judged pages scored {len(J)} (example pages left out {n_ex}; judged pages without an '
         f'answer {n_unanswered}); judge key {kname}',
         f'- pages every method could route: {len(common)}; judge says none on {summ["judge_none"]}; misleading title on {summ["misleading_pages"]}',
         f'- notes on the judge lines: {dict(notes) or "none"}', '',
         'Precision: share of the method\'s page-theme pairs the judge also gives. Recall: share of the judge\'s pairs the method gives. '
         'Misleading: on pages with a misleading title, share the method sends to a theme the judge does not give (lower is better). '
         '95% intervals from 2,000 draws of pages.', '']
    for scope in S.scope.unique():
        L += [f'## {scope}', '']
        L += T.md_table(S[S.scope == scope][['group', 'method', 'level', 'pages', 'method_pairs', 'judge_pairs', 'precision', 'precision_lo', 'precision_hi',
                                             'recall', 'recall_lo', 'recall_hi', 'misleading_pages', 'misleading_wrong_share']])
        L.append('')
    T.write_text('\n'.join(L) + '\n', P.report('testF_26_G1.md'))
    T.log(f'G1 scored on {len(common)} common pages; wrote g1_scores.csv')


if __name__ == '__main__':
    main()
