"""Collect the checked answer lines that stopped sorters saved (scratchpad parts, out/*.partial_*) and put them, in input order and in
the output format, into scratchpad/<job>/saved_NN.tsv, so that the next sorter of that job reuses them. Only jobs not done are touched.
A line is kept only if its id is one of the job's items, the kind (pages) is allowed, there are at most 3 codes, every code is in the
theme guide and every confidence is 1, 2 or 3. The original files are moved to scratchpad/salvage_backup/<stamp>/. Prints a table."""
import csv, glob, os, re, shutil, sys, time
S = '/private/tmp/claude-501/-Users-mac-Documents-CMKL-University-Thesis---Audiobook-Performance-Prediction/3d7e599c-e8eb-44e0-8e7e-9c7619b7026a/scratchpad'
GUIDE = '../../../../prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv'
codes = {r['code'] for r in csv.DictReader(open(GUIDE), delimiter='\t')}
KINDS = {'concept', 'person', 'work', 'event', 'place', 'organization', 'list', 'other'}
HELPERS = re.compile(r'(in_ids|out_ids|used_codes|guide_codes|valid_codes|expected_ids|got_ids|joined)', re.I)
stamp = time.strftime('%Y%m%d_%H%M')
jobs = list(csv.DictReader(open('jobs.tsv'), delimiter='\t'))

def parse(line, kind):
    f = [x for x in re.split(r'[\t|]| +', line.strip()) if x != '']
    if len(f) < 2:
        return None
    pid, rest = f[0], f[1:]
    k = None
    if kind == 'pages':
        if len(rest) < 2 or rest[0] not in KINDS:
            return None
        k, rest = rest[0], rest[1:]
    if len(rest) != 1:
        return None
    ans = rest[0]
    if ans != 'none':
        parts = ans.split(',')
        if len(parts) > 3:
            return None
        seen = set()
        for p in parts:
            m = re.fullmatch(r'(B\d\d\.M\d\d\.N\d\d):([123])', p)
            if not m or m.group(1) not in codes or m.group(1) in seen:
                return None
            seen.add(m.group(1))
    return pid, '\t'.join([pid] + ([k] if k else []) + [ans])

# candidate files: everything the sorters saved since this run began, plus the partial outputs of the first stop
cands = [f for f in glob.glob(S + '/**/*', recursive=True)
         if os.path.isfile(f) and f.endswith(('.tsv', '.txt')) and not HELPERS.search(os.path.basename(f))
         and '/salvage_backup/' not in f and os.path.getmtime(f) > os.path.getmtime('wf_group_1.json')
         and not re.search(r'/saved_\d\d\.tsv$', f)]
cands += glob.glob('out/*.partial_*')
# each file belongs to the one job that holds most of its ids (the reliability sets share ids with the main chunks, so a file is
# never split across jobs and a reliability answer never fills a main job or the reverse)
job_ids = {}
for j in jobs:
    a, b = int(j['from_line']), int(j['to_line'])
    job_ids[j['job']] = set(l.split('\t')[0] for l in open(j['input']).read().splitlines()[a - 1:b])
owner = {}
for f in cands:
    try:
        fids = [re.split(r'[\t| ]', l.strip())[0] for l in open(f).read().splitlines() if l.strip()]
    except UnicodeDecodeError:
        continue
    if not fids:
        continue
    best = max(job_ids, key=lambda k: sum(i in job_ids[k] for i in fids))
    if sum(i in job_ids[best] for i in fids) > 0.5 * len(fids):
        owner[f] = best

rows = []
for j in jobs:
    a, b = int(j['from_line']), int(j['to_line'])
    ids = [l.split('\t')[0] for l in open(j['input']).read().splitlines()[a - 1:b]]
    if os.path.exists(j['output']):
        if [l.split('\t')[0] for l in open(j['output']).read().splitlines() if l.strip()] == ids:
            continue
    idset, kind = set(ids), ('books' if j['kind'] == 'books' else 'pages')
    mine = [f for f in cands if owner.get(f) == j['job']]
    got, bad = {}, 0
    for f in mine:
        for line in open(f).read().splitlines():
            if not line.strip():
                continue
            r = parse(line, kind)
            if r and r[0] in idset:
                got.setdefault(r[0], r[1])
            else:
                bad += 1
    d = os.path.join(S, j['job'])
    old_saved = sorted(glob.glob(d + '/saved_*.tsv'))
    for f in old_saved:  # earlier salvage output counts too
        for line in open(f).read().splitlines():
            r = parse(line, kind)
            if r and r[0] in idset:
                got.setdefault(r[0], r[1])
    if got:
        os.makedirs(d, exist_ok=True)
        for f in mine + old_saved:
            dest = os.path.join(S, 'salvage_backup', stamp, os.path.relpath(f, S) if f.startswith(S) else 'out_' + os.path.basename(f))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(f, dest)
        open(os.path.join(d, 'saved_00.tsv'), 'w').write('\n'.join(got[i] for i in ids if i in got) + '\n')
    rows.append((j['job'], len(ids), len(got), bad, len(mine)))
print(f"{'job':24} items saved rejected files")
for r in rows:
    if r[2] or r[4]:
        print(f'{r[0]:24} {r[1]:5} {r[2]:5} {r[3]:8} {r[4]:5}')
print(f'jobs not done {len(rows)}; with saved lines {sum(1 for r in rows if r[2])}; saved lines {sum(r[2] for r in rows):,} of {sum(r[1] for r in rows):,} items')
