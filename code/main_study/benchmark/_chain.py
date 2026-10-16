"""Runs several benchmark scripts one after another, each under jobs/heavy_lock.sh with nice -n 10 (so other heavy jobs never overlap).
usage: bash jobs/bg.sh NAME main_study/benchmark/_chain.py "09_chronos2.py --variants chronos2_nli" "10_change_models.py --fsets DVcur --tag h1_a" ...
Each quoted argument is one script with its arguments. A failure is logged and the chain goes on with the next step."""
import sys, os, shlex, subprocess, pathlib, time
root = pathlib.Path(__file__).resolve().parents[3]
env = dict(os.environ, HF_HUB_DISABLE_PROGRESS_BARS='1', TOKENIZERS_PARALLELISM='false')
for step in sys.argv[1:]:
    args = shlex.split(step)
    print(f'=== {time.strftime("%H:%M:%S")} step: {step}', flush=True)
    rc = subprocess.call(['bash', str(root / 'jobs' / 'heavy_lock.sh'), 'nice', '-n', '10', str(root / '.venv' / 'bin' / 'python'), '-u',
                          str(root / 'code' / 'main_study' / 'benchmark' / args[0])] + args[1:], env=env)
    print(f'=== {time.strftime("%H:%M:%S")} exit {rc}: {step}', flush=True)
