"""Run all Study 1 reruns one after another (one heavy job at a time, nice 10 set by the caller)."""
import subprocess, sys, os
here=os.path.dirname(os.path.abspath(__file__)); py=sys.executable
def run(*a):
    print('>>',' '.join(a),flush=True); r=subprocess.run([py,'-u',*a]); 
    if r.returncode: print('FAILED',a,flush=True); sys.exit(1)
for w in ['1 3','2 3','1 6','2 6','1 12','2 12','3 6']: run(f'{here}/run_wf_limited.py',*w.split(),'robust')
run(f'{here}/run_wf_limited.py','2','6','early')
run(f'{here}/shapley_fixed.py')
for lab in ['y_view','y_fav']: run(f'{here}/exp1_fixed.py',lab,'3')
print('ALLDONE',flush=True)
