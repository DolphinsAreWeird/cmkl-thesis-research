#!/bin/bash
# Daily collection (started by launchd at 21:00, or on wake if the Mac was asleep then).
cd "$(dirname "$0")"; PY=.venv/bin/python
echo "=== $(date '+%Y-%m-%d %H:%M:%S')"
/usr/bin/caffeinate -i $PY -u bluesky_sample.py 60      # one hour of public posts, identifiers removed on arrival
/usr/bin/caffeinate -i $PY -u nyt_bestsellers.py        # next batch of NYT weeks; stops itself at the daily limit
echo "files: bluesky $(ls data/bluesky 2>/dev/null | wc -l | tr -d ' '), nyt $(ls data/nyt 2>/dev/null | wc -l | tr -d ' '); size $(du -sh data | cut -f1)"
