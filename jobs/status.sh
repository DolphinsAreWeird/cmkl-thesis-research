#!/bin/bash
# Show each background job: running or stopped, and the last lines of its log.  usage: jobs/status.sh [lines]
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; N=${1:-2}
for p in "$ROOT"/data/reports/*.pid; do
  [ -e "$p" ] || continue; name=$(basename "$p" .pid); pid=$(cat "$p")
  if kill -0 "$pid" 2>/dev/null; then st="RUNNING pid $pid"; else st="stopped"; fi
  echo "[$name] $st"; tail -n "$N" "$ROOT/data/reports/$name.log" | sed 's/^/    /'
done
