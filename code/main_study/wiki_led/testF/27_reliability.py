#!/usr/bin/env python3
"""Test F, step 27: agreement between the first sorting pass and an independent second pass (1,000 pages and 500 books).

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (sorter.reliability): reported are the agreement of the first theme,
any overlap and agreement on none. Nothing here reads loans.
First pass: the assignments used in the analysis (assign_*.parquet and items_*.parquet of step 20, re-ask answers included).
Second pass: second_pass_pages.parquet and second_pass_books.parquet, the answers of the jobs on rel_pages.tsv and rel_books.tsv
(out/rel_*.tsv) parsed and checked against the guide by step 20; the second pass has no re-ask, so its invalid lines are left out and
counted.
Measures (NOT IN ADDENDUM in detail, fixed here before any second-pass answer existed), on items with a usable answer in both passes:
  first theme   among items where both passes give at least one theme: share whose first (strongest) theme is the same; also with the
                first themes moved to their middle theme
  any overlap   among the same items: share sharing at least one theme
  none          over all items: the 2 x 2 table of none against some theme, the share agreeing and Cohen's kappa
The three example pages of the page instructions are left out (the reliability set already leaves them out).
Outputs: reliability.csv, reliability_summary.json; report testF_27_reliability.md.
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/27_reliability.py [--root DIR]
"""
import sys, pathlib, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T


def first_pass(P, kind):
    items = pd.read_parquet(P / f'items_{kind}.parquet')
    A = pd.read_parquet(P / f'assign_{kind}.parquet').sort_values(['id', 'rank'])
    codes = A.groupby('id').code.apply(list).to_dict()
    ok = items[items.status.isin(['themes', 'none'])]
    return {i: (codes.get(i, []) if s == 'themes' else []) for i, s in zip(ok.id, ok.status)}, items


def measures(first, second, par):
    ids = sorted(set(first) & set(second))
    a = [first[i] for i in ids]
    b = [second[i] for i in ids]
    some_a = np.array([len(x) > 0 for x in a], dtype=bool); some_b = np.array([len(x) > 0 for x in b], dtype=bool)
    both = some_a & some_b
    same1 = np.array([x[0] == y[0] for x, y, k in zip(a, b, both) if k])
    same1m = np.array([par.get(x[0]) == par.get(y[0]) for x, y, k in zip(a, b, both) if k])
    overlap = np.array([len(set(x) & set(y)) > 0 for x, y, k in zip(a, b, both) if k])
    n = len(ids)
    t = dict(both_none=int((~some_a & ~some_b).sum()), first_none_only=int((~some_a & some_b).sum()), second_none_only=int((some_a & ~some_b).sum()),
             both_some=int(both.sum()))
    po = (t['both_none'] + t['both_some']) / n if n else np.nan
    pa_, pb_ = ((~some_a).mean(), (~some_b).mean()) if n else (np.nan, np.nan)
    pe = pa_ * pb_ + (1 - pa_) * (1 - pb_) if n else np.nan
    kappa = (po - pe) / (1 - pe) if n and pe < 1 else np.nan
    return dict(items_both_usable=n, **t, first_theme_same=float(same1.mean()) if len(same1) else np.nan,
                first_theme_same_middle=float(same1m.mean()) if len(same1m) else np.nan,
                any_overlap=float(overlap.mean()) if len(overlap) else np.nan, none_agreement=float(po), none_kappa=float(kappa))


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    a = ap.parse_args()
    P = T.Paths(a.root)
    par = T.parent_map()
    ex = T.prompt_example_titles(P)
    rows, summ = [], dict(mock=P.mock)
    for kind in ('pages', 'books'):
        f = P / f'second_pass_{kind}.parquet'
        if not f.exists():
            T.log(f'{kind}: {f.name} not found (run 20_parse_outputs.py after the second-pass jobs); skipped')
            summ[kind] = dict(second_pass=0)
            continue
        S2p = pd.read_parquet(f)
        use = S2p[S2p.status.isin(['ok', 'none'])]
        second = {i: ([str(c) for c in cs] if st == 'ok' else []) for i, cs, st in zip(use.id, use.codes, use.status)}
        first, items = first_pass(P, kind)
        if kind == 'pages':
            drop = set(items[items.title.isin(ex)].id)
            first = {k: v for k, v in first.items() if k not in drop}
            second = {k: v for k, v in second.items() if k not in drop}
        m = measures(first, second, par)
        m.update(kind=kind, second_pass_items=len(S2p), second_pass_invalid=int((S2p.status == 'invalid').sum()),
                 second_pass_without_answer=int(S2p.status.isin(['missing', 'not_sorted']).sum()),
                 second_usable_but_first_not=len(set(second) - set(first)))
        rows.append(m)
        summ[kind] = m
        T.log(f'{kind}: {m["items_both_usable"]} items in both passes; first theme same {m["first_theme_same"]:.3f}; any overlap {m["any_overlap"]:.3f}; '
              f'none agreement {m["none_agreement"]:.3f}')
    R = pd.DataFrame(rows)
    R.to_csv(P / 'reliability.csv', index=False)
    T.write_json(summ, P / 'reliability_summary.json')
    L = [f'# Test F: agreement of two independent sorting passes ({P.tag()})', '', f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}', '',
         'First theme: among items both passes put in at least one theme, the share with the same strongest theme (and the same middle theme). '
         'Any overlap: the share sharing at least one theme. None: the share on which both passes agree that no theme fits or that some theme '
         'fits, with Cohen\'s kappa.', '']
    if len(R):
        L += T.md_table(R[['kind', 'items_both_usable', 'both_some', 'both_none', 'first_none_only', 'second_none_only', 'first_theme_same',
                           'first_theme_same_middle', 'any_overlap', 'none_agreement', 'none_kappa', 'second_pass_invalid', 'second_pass_without_answer']])
    T.write_text('\n'.join(L) + '\n', P.report('testF_27_reliability.md'))


if __name__ == '__main__':
    main()
