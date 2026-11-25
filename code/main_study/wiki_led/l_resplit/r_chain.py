# Runs part 2 of the five-seed reruns step by step (record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor
# (20 November 2026)", part 2).  Waits until part 1 (l07_five_seeds.py, 92_five_seeds_b.py) has finished, then:
#   r00 (works of each quarter, check q0), then for q1, q2, q3: r01 links, r02 views, r03 rows (a step whose output exists is
#   skipped), then r04 (five re-drawn samples and the four quarters) and the report 93_five_seeds_report.py.  Stops at the first failure.
# One heavy job at a time; the downloads keep the rate limits of the copied scripts.
#   Start from handoff/:  bash jobs/bg.sh wl_resplit main_study/wiki_led/l_resplit/r_chain.py
import subprocess, sys, time, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CODE = HERE.parents[2]
PY = str(CODE.parent / '.venv' / 'bin' / 'python')
DB = CODE.parent / 'data' / 'db' / 'wiki_led' / 'l_resplit'


def log(*a):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), *a, flush=True)


def busy():
    r = subprocess.run(['pgrep', '-f', 'l07_five_seeds.py|92_five_seeds_b.py'], capture_output=True, text=True)
    return bool(r.stdout.strip())


while busy():
    log('waiting for part 1 to finish')
    time.sleep(120)


def step(script, *args, done=None):
    if done is not None and done.exists():
        log('skip', script, *args, '(output exists)')
        return
    log('start', script, *args)
    r = subprocess.run([PY, '-u', str(HERE / script), *map(str, args)], cwd=str(CODE))
    if r.returncode != 0:
        log('FAILED', script, *args, 'exit', r.returncode)
        sys.exit(r.returncode)
    log('done', script, *args)


step('r00_works.py', done=DB / 'works_summary.json')
for k in (1, 2, 3):
    step('r01_match.py', k, done=DB / f'q{k}' / 'match_summary.json')
    step('r02_views.py', k, done=DB / f'q{k}' / 'views_summary.json')
    step('r03_rows.py', k, done=DB / f'q{k}' / 'rows_summary.json')
step('r04_resplit.py')
r = subprocess.run([PY, '-u', str(HERE.parent / '93_five_seeds_report.py')], cwd=str(CODE))
log('report exit', r.returncode)
log('chain finished')
