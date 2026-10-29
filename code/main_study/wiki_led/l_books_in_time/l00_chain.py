# l00. Runs steps l02 (views and features), l03 (rows) and l04 (backtest) of addendum l one after the other, once l01 (matching) has
# finished; stops at the first step that fails (each step checks itself against Test A or Test D and stops on a mismatch).
#   Run from code/:  bash ../jobs/bg.sh wl_l_chain main_study/wiki_led/l_books_in_time/l00_chain.py [--wait-pid PID]
import sys, time, subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable
if '--wait-pid' in sys.argv:
    pid = int(sys.argv[sys.argv.index('--wait-pid') + 1])
    while subprocess.run(['kill', '-0', str(pid)], capture_output=True).returncode == 0:
        time.sleep(20)
summ = HERE.parents[3] / 'data' / 'db' / 'wiki_led' / 'l_books_in_time' / 'match_summary.json'
if not summ.exists():
    sys.exit('l01 did not finish (no match_summary.json)')
for step in ('l02_views.py', 'l03_rows.py', 'l04_backtest.py'):
    print(time.strftime('%H:%M:%S'), '=== start', step, flush=True)
    r = subprocess.run([PY, '-u', str(HERE / step)])
    print(time.strftime('%H:%M:%S'), '=== end', step, 'exit', r.returncode, flush=True)
    if r.returncode != 0:
        sys.exit(f'{step} failed')
print(time.strftime('%H:%M:%S'), '=== chain done', flush=True)
