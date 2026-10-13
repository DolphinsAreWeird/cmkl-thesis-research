#!/bin/bash
cd "$(dirname "$0")"; PATH="$PWD/../.venv/bin:$PATH"
for w in "1 3" "2 3" "1 6" "2 6" "1 12" "2 12" "3 6"; do python3 -u walkforward3.py $w robust >> ../data/reports/wf3.log 2>&1; done
python3 -u walkforward3.py 2 6 full >> ../data/reports/wf3.log 2>&1
python3 -u walkforward3.py 2 6 early >> ../data/reports/wf3.log 2>&1
echo ALLDONE >> ../data/reports/wf3.log
