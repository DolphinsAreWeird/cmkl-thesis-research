"""Print Workflow args for the Test F sorting jobs that are not done yet, split round-robin into up to 3 groups.
A job is done when its output file has exactly one line per input item with the ids in order (as in track.py)."""
import csv, json, os, sys
groups = int(sys.argv[1]) if len(sys.argv) > 1 else 3
todo = []
for j in csv.DictReader(open('jobs.tsv'), delimiter='\t'):
    a, b = int(j['from_line']), int(j['to_line'])
    ids = [l.split('\t')[0] for l in open(j['input']).read().splitlines()[a - 1:b]]
    if os.path.exists(j['output']):
        out = [l.split('\t')[0] for l in open(j['output']).read().splitlines() if l.strip()]
        if out == ids:
            continue
    todo.append([j['job'], j['kind'], j['input'], a, b, j['output'], len(ids)])
# order: judge (G1), main page chunks (G2, G3), main book chunks (G4), then the reliability and one-day coverage sets
rank = lambda r: 0 if r[1] == 'judge' else 3 if r[0].startswith(('rel_', 'sample1day')) else 1 if r[1] == 'pages' else 2
todo.sort(key=lambda r: (rank(r), r[0]))
for g in range(groups):
    part = todo[g::groups]
    if part:
        print(json.dumps(part, separators=(',', ':')))
print(f'# {len(todo)} jobs not done', file=sys.stderr)
