#!/usr/bin/env python3
"""Test B (new books), step 1: the population of works and the first-author name of each.

Settings: prereg/wiki_led_settings_2026-10-20.json, test_B_new_books.population.  Data only: no model, no outcome.
Run from handoff/code:   nice -n 10 ../.venv/bin/python main_study/wiki_led/01_population.py
Writes data/db/wiki_led/test_b_population.parquet and population_counts.json.
"""
import re, json
import pandas as pd
from _common import TAXO, OUT, log


# ---- copied unchanged from code/study1_seattle/00_coverage_check.py (that script has side effects, so it is not imported);
# ---- parse_author uses only `re`, it has no other helper.
def parse_author(c):
    """Return (display name 'First Last', family name) for the FIRST author of a Seattle creator string, or (None, None)."""
    c = (c or '').strip()
    if not c:
        return None, None
    c = c.split(';')[0]
    c = re.sub(r',?\s*(\(?\d{4}\??\)?\s*-\s*(\d{4})?\)?|\(?b\.\s*\d{4}\)?|\(?d\.\s*\d{4}\)?)\s*\.?$', '', c.strip())
    c = c.strip(' ,.')
    if not c:
        return None, None
    if ',' in c:
        fam, given = [x.strip() for x in c.split(',', 1)]
        given = given.split(',')[0].strip()
        return (f'{given} {fam}'.strip(), fam)
    c = re.split(r'\s+(?:and|&|with)\s+|,\s*', c)[0].strip()
    toks = c.split()
    return (c, toks[-1] if toks else None)


def main():
    w = pd.read_parquet(TAXO / 'spl_works.parquet',
                        columns=['work_id', 'creator', 'creator_key', 'first_ym', 'pub_year_min', 'creator_from_title_only'])
    counts = {'works_in_spl_works': int(len(w))}
    x = w[w.first_ym.between(201701, 202602)]
    counts['first_ym_201701_202602'] = int(len(x))
    x = x[x.pub_year_min.notna()]
    counts['with_pub_year'] = int(len(x))
    x = x[x.pub_year_min >= x.first_ym // 100 - 1]
    counts['new_releases'] = int(len(x))
    counts['new_releases_distinct_creator_key_incl_empty'] = int(x.creator_key.nunique())
    empty = x[x.creator.fillna('').str.strip() == '']
    counts['empty_creator_dropped'] = int(len(empty))
    counts['empty_creator_dropped_by_year'] = {int(k): int(v) for k, v in (empty.first_ym // 100).value_counts().sort_index().items()}
    x = x[x.creator.fillna('').str.strip() != ''].copy()
    counts['nonempty_creator'] = int(len(x))
    counts['nonempty_creator_distinct_creator_key'] = int(x.creator_key.nunique())
    counts['nonempty_creator_empty_creator_key'] = int((x.creator_key == '').sum())
    counts['nonempty_creator_from_title_only'] = int(x.creator_from_title_only.sum())
    x['test_year'] = (x.first_ym // 100).astype(int)
    parsed = x.creator.map(parse_author)
    x['display_name'] = parsed.map(lambda t: t[0])
    x['family'] = parsed.map(lambda t: t[1])
    ok = x.display_name.notna() & (x.display_name.fillna('').str.strip() != '')
    fail = x[~ok]
    counts['parse_failures'] = int((~ok).sum())
    counts['parse_failure_examples'] = fail.creator.head(10).tolist()
    counts['parse_failures_by_year'] = {int(k): int(v) for k, v in fail.groupby('test_year').size().items()}
    pop = x[ok].copy()
    pop['display_name'] = pop.display_name.str.strip()
    pop['first_ym'] = pop.first_ym.astype(int)
    pop['pub_year_min'] = pop.pub_year_min.astype(int)
    pop = pop[['work_id', 'creator', 'creator_key', 'display_name', 'family', 'first_ym', 'test_year', 'pub_year_min',
               'creator_from_title_only']].sort_values('work_id').reset_index(drop=True)
    counts['population_works'] = int(len(pop))
    counts['population_distinct_creator_key'] = int(pop.creator_key.nunique())
    counts['population_distinct_display_name'] = int(pop.display_name.nunique())
    counts['population_by_year'] = {int(k): int(v) for k, v in pop.groupby('test_year').size().items()}
    counts['distinct_display_name_by_year'] = {int(k): int(v) for k, v in pop.groupby('test_year').display_name.nunique().items()}
    pop.to_parquet(OUT / 'test_b_population.parquet', index=False)
    (OUT / 'population_counts.json').write_text(json.dumps(counts, indent=1))
    log(json.dumps({k: v for k, v in counts.items() if not isinstance(v, (dict, list))}, indent=1))
    log('by year', counts['population_by_year'])


if __name__ == '__main__':
    main()
