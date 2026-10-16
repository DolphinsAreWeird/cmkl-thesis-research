"""Launcher for jobs/bg.sh: runs a Study 2R script under jobs/heavy_lock.sh with nice -n 10.  usage: bg.sh NAME study2r/_locked.py study2r/13_effects.py [args]"""
import sys, subprocess, pathlib
root = pathlib.Path(__file__).resolve().parents[2]
sys.exit(subprocess.call(['bash', str(root / 'jobs' / 'heavy_lock.sh'), 'nice', '-n', '10', str(root / '.venv' / 'bin' / 'python'), '-u',
                          str(root / 'code' / 'study2r' / sys.argv[1])] + sys.argv[2:]))
