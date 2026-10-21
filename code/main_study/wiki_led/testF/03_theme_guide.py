#!/usr/bin/env python3
"""Test F data, step 3: the theme guide that the AI sorters and the judge read.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (theme_guide).  Data only: no loans are read, nothing is sorted.
Input: data/db/taxonomy_v3/theme_nodes.parquet, the 242 narrow themes (level 3), their middle (level 2) and broad (level 1) parents.
Columns (the names the instruction files use): code (node_id), theme, broader group (middle label), broadest group (broad label),
example subject headings (up to 8 member terms in stored order, from values_v3, else values, joined by '; ').
Labels: the stored label of each node.  The middle and broad labels are written by hand and are kept as they are.  Most narrow labels are
the node's two top member terms in lower case ('vampires / superheroes'); to make them plain and readable, the first letter is made a capital
and the capitals of proper names and abbreviations are restored (CASING below, for example 'world war ii' -> 'World War II', 'hiv aids' ->
'HIV/AIDS').  No word is added, removed or changed.  The member terms are kept exactly as stored.
Rows are sorted by code.  Output: prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv (UTF-8, tab-separated, header line), made read-only.
The script refuses to overwrite an existing guide (the guide is fingerprinted in prereg/README.md before any sorting).
Run from code/:  nice ../.venv/bin/python main_study/wiki_led/testF/03_theme_guide.py [--check]   (--check: print, write nothing)
"""
import sys, re, os, stat, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import _testf_common as F

CASING = {
    'african american': 'African American', 'african': 'African', 'american civil war': 'American Civil War',
    'american revolution': 'American Revolution', 'amish': 'Amish', 'arthurian': 'Arthurian', 'asian american': 'Asian American',
    'black life': 'Black life', 'buddhism': 'Buddhism', 'celtic': 'Celtic', 'christianity': 'Christianity', 'christmas': 'Christmas',
    'cold war': 'Cold War', 'french revolution': 'French Revolution', 'great depression': 'Great Depression', 'greek': 'Greek',
    'hiv aids': 'HIV/AIDS', 'holocaust': 'Holocaust', 'islam': 'Islam', 'islamic': 'Islamic', 'jewish': 'Jewish', 'jfk': 'JFK',
    'judaism': 'Judaism', 'latino': 'Latino', 'latter day saints': 'Latter Day Saints', 'lgbtq': 'LGBTQ', 'mars': 'Mars', 'marxism': 'Marxism',
    'napoleonic wars': 'Napoleonic Wars', 'native americans': 'Native Americans', 'nazis': 'Nazis', 'paris commune': 'Paris Commune',
    'ptsd': 'PTSD', 'puritans': 'Puritans', 'robin hood': 'Robin Hood', 'russian revolution': 'Russian Revolution',
    'september 11': 'September 11', 'sufism': 'Sufism', 'titanic': 'Titanic', 'ufos': 'UFOs', 'vietnam war': 'Vietnam War',
    'wars of the roses': 'Wars of the Roses', 'wicca': 'Wicca', 'world war i': 'World War I', 'world war ii': 'World War II',
}
_PAT = re.compile(r'\b(' + '|'.join(re.escape(k) for k in sorted(CASING, key=len, reverse=True)) + r')\b')


def readable(label):
    s = _PAT.sub(lambda m: CASING[m.group(1)], label)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    # only letter case (and the slash of HIV/AIDS) may differ from the stored label
    assert s.lower().replace('hiv/aids', 'hiv aids') == label.lower(), (label, s)
    return s


def build():
    N = pd.read_parquet(F.D / 'db' / 'taxonomy_v3' / 'theme_nodes.parquet')
    lab = N.set_index('node_id').label
    n3 = N[N.level == 3].sort_values('node_id')
    assert len(n3) == 242 and (N.level == 2).sum() == 86 and (N.level == 1).sum() == 19
    rows = []
    for _, r in n3.iterrows():
        mid, broad = r.parent, r.parent.split('.')[0]
        assert mid in lab.index and broad in lab.index and N.set_index('node_id').level[mid] == 2
        v3 = list(r.values_v3) if r.values_v3 is not None else []
        terms = v3 if len(v3) else list(r['values'])
        terms = [F.clean(t) for t in terms[:8]]
        assert terms and all(terms) and not any(';' in t for t in terms)
        rows.append([r.node_id, F.clean(readable(r.label)), F.clean(lab[mid]), F.clean(lab[broad]), '; '.join(terms)])
    return rows


def main():
    rows = build()
    header = ['code', 'theme', 'broader group', 'broadest group', 'example subject headings']
    if '--check' in sys.argv:
        for r in rows:
            print(' | '.join(r))
        return
    if F.GUIDE.exists():
        raise SystemExit(f'{F.GUIDE} exists already; the guide is not rewritten (fixed before any sorting)')
    F.write_tsv(F.GUIDE, header, rows)
    back = F.read_tsv(F.GUIDE)
    assert back[0] == header and back[1:] == rows
    os.chmod(F.GUIDE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    F.log(f'wrote {F.GUIDE.name}: {len(rows)} themes; SHA-256 {F.sha256(F.GUIDE)}')


if __name__ == '__main__':
    main()
