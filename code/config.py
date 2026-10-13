# Shared paths and keys for every script. Keys come from ../.env and are never printed.
import os, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
f=ROOT/'.env'
if f.exists():
    for line in f.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.split(' #',1)[0].strip())
D=os.environ.get('THESIS_DATA',str(ROOT/'data'))
FIGS=str(ROOT/'paper'/'figures')
UA=os.environ.get('USER_AGENT') or 'CMKL-thesis-research/0.1 (student project; CMKL University; kwai@cmkl.ac.th)'
GCP_KEY=str(ROOT/os.environ.get('GOOGLE_APPLICATION_CREDENTIALS','secrets/gcp_key.json'))
def key(name):
    v=os.environ.get(name)
    if not v: raise SystemExit(f'{name} missing from .env')
    return v
