"""Launcher for jobs/bg.sh: runs a benchmark script under jobs/heavy_lock.sh (one heavy job at a time) with nice -n 10.
usage: bash jobs/bg.sh NAME main_study/benchmark/_locked.py 09_chronos2.py [args]      (log data/reports/NAME.log)"""
import sys, os, subprocess, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
env = dict(os.environ, HF_HUB_DISABLE_PROGRESS_BARS='1', TOKENIZERS_PARALLELISM='false')
sys.exit(subprocess.call(['bash', str(root / 'jobs' / 'heavy_lock.sh'), 'nice', '-n', '10', str(root / '.venv' / 'bin' / 'python'), '-u',
                          str(root / 'code' / 'main_study' / 'benchmark' / sys.argv[1])] + sys.argv[2:], env=env))
