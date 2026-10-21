# Status of the Test F sorting jobs: compares each job's output with its input lines (ids, count).
import csv, os, sys
jobs = list(csv.DictReader(open('jobs.tsv'), delimiter='\t'))
done, partial, pending = [], [], []
for j in jobs:
    a, b = int(j['from_line']), int(j['to_line'])
    lines = open(j['input']).read().splitlines()[a - 1:b]
    ids = [l.split('\t')[0] for l in lines]
    if not os.path.exists(j['output']):
        pending.append(j['job']); continue
    out = [l for l in open(j['output']).read().splitlines() if l.strip()]
    oid = [l.split('\t')[0] for l in out]
    (done if oid == ids else partial).append(f"{j['job']} ({len(out)}/{len(ids)})" if oid != ids else j['job'])
print(f'done {len(done)} | partial {len(partial)} | not started {len(pending)} of {len(jobs)}')
if partial: print('partial or mismatched:', ', '.join(partial))
if '-v' in sys.argv: print('pending:', ', '.join(pending))
