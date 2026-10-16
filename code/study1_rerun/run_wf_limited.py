"""Run the existing walkforward3_fix.py unchanged, with threads capped at 3. usage: run_wf_limited.py START N MODE"""
import sys, os, runpy
code=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,code); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import threads
os.chdir(code); sys.argv=['walkforward3_fix.py']+sys.argv[1:]
runpy.run_path(os.path.join(code,'walkforward3_fix.py'),run_name='__main__')
