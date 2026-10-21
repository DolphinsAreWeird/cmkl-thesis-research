"""Thinking-level pilot of Test F (DEVIATIONS.md, Test F item 8): compare the 250 pilot answers of each level with the original
full-level answers (first 250 lines of out/pages_chunk_05_a.tsv). Writes data/reports/testF_effort_pilot.md and prints the decision."""
import glob, json, os, sys
def load(path, n=None):
    out = {}
    for line in open(path).read().splitlines()[:n]:
        f = line.split('\t')
        if len(f) < 3:
            continue
        codes = [] if f[2].strip() == 'none' else [c.split(':')[0] for c in f[2].split(',')]
        out[f[0]] = codes
    return out
orig = load('out/pages_chunk_05_a.tsv', 250)
ids = list(orig)
def first(c): return c[0] if c else 'none'
def mid(c): return c[0].rsplit('.', 1)[0] if c else 'none'
rows = {}
for level in ['max', 'high', 'medium']:
    p = f'pilot_effort/{level}.tsv'
    if not os.path.exists(p):
        continue
    a = load(p)
    ok = [i for i in ids if i in a]
    n = len(ok)
    rows[level] = dict(
        n=n,
        first=sum(first(a[i]) == first(orig[i]) for i in ok) / n,
        middle=sum(mid(a[i]) == mid(orig[i]) for i in ok) / n,
        any=sum((not a[i] and not orig[i]) or bool(set(a[i]) & set(orig[i])) for i in ok) / n,
        none=sum(not a[i] for i in ok) / n,
        themes=sum(len(a[i]) for i in ok) / n)
tok = json.load(open('pilot_effort/tokens.json')) if os.path.exists('pilot_effort/tokens.json') else {}
base = rows.get('max', {}).get('first')
choice = 'max'
if base is not None:
    for level in ['medium', 'high']:
        if level in rows and rows[level]['first'] >= base - 0.05:
            choice = level
            break
orig_none = sum(not orig[i] for i in ids) / len(ids)
L = ['# Test F: thinking-level pilot', '',
     'Same 250 pages (lines 2 to 251 of pages_chunk_05.tsv), same instructions; compared with the original full-level answers. '
     'Rule fixed before the answers were read (prereg/DEVIATIONS.md, Test F item 8): a lower level passes if its first-theme agreement '
     'is at least the full-level rerun minus 5 points; the cheapest passing level is used.', '',
     '| level | pages | same first theme | same middle group | any theme shared | none | themes per page | output tokens |',
     '|---|---|---|---|---|---|---|---|']
for level, r in rows.items():
    L.append(f"| {level} | {r['n']} | {r['first']:.1%} | {r['middle']:.1%} | {r['any']:.1%} | {r['none']:.1%} | {r['themes']:.2f} | {tok.get(level, 'n/a')} |")
L += ['', f'Original answers: none {orig_none:.1%}, themes per page {sum(len(orig[i]) for i in ids)/len(ids):.2f}.', '',
      f'Decision: **{choice}** for the remaining jobs.']
open('../../../reports/testF_effort_pilot.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
