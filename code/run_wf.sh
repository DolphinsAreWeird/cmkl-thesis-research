#!/bin/bash
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
python3 -u walkforward2.py 6 > ../data/reports/wf.log 2>&1
python3 -u walkforward2.py 6 early >> ../data/reports/wf.log 2>&1
echo ALLDONE >> ../data/reports/wf.log
