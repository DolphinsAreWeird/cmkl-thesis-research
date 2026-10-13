#!/bin/bash
# Start a long job detached from this session (survives closing Claude/Terminal), keep the Mac awake while it runs.
# usage: jobs/bg.sh NAME script.py [args...]      log: data/reports/NAME.log   pid: data/reports/NAME.pid
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; NAME=$1; shift
LOG="$ROOT/data/reports/$NAME.log"; PID="$ROOT/data/reports/$NAME.pid"
if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "$NAME already running (pid $(cat "$PID"))"; exit 1; fi
cd "$ROOT/code"
echo "=== start $(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"
/usr/bin/perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or die $!' /usr/bin/caffeinate -i "$ROOT/.venv/bin/python" -u "$@" >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PID"; echo "$NAME started (pid $!), log data/reports/$NAME.log"
