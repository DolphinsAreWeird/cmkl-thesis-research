#!/bin/bash
# Copy the scheduled collectors to ~/thesis-collectors and (re)load their launchd schedules.
# They live outside Documents because macOS blocks background jobs from reading Documents without a permission change.
# Source of truth stays in handoff/collectors; rerun this after editing anything there.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; DST="$HOME/thesis-collectors"
mkdir -p "$DST/data" "$DST/logs" "$DST/secrets"
cp "$ROOT"/collectors/{bluesky_sample.py,nyt_bestsellers.py,gdelt_update.py,run_daily.sh,requirements.txt,ol_common.py,openlibrary_reading_log.py,seattle_release_watch.py} "$DST/"
[ -f "$DST/.env" ] || cp "$ROOT/.env" "$DST/.env"
[ -f "$DST/secrets/gcp_key.json" ] || cp "$ROOT/secrets/gcp_key.json" "$DST/secrets/gcp_key.json"
chmod 600 "$DST/.env" "$DST/secrets/gcp_key.json"; chmod 700 "$DST/secrets"
[ -x "$DST/.venv/bin/python" ] || uv venv -q --python 3.12 "$DST/.venv"
uv pip install -q --python "$DST/.venv/bin/python" -r "$DST/requirements.txt"
[ -L "$ROOT/data/collectors" ] || ln -s "$DST/data" "$ROOT/data/collectors"     # analysis sees the collected data here
for p in "$ROOT"/jobs/launchd/*.plist; do
  label=$(basename "$p" .plist)
  # a schedule that is loaded and unchanged is left alone, so a deploy never stops a collector that is running
  if cmp -s "$p" "$HOME/Library/LaunchAgents/$label.plist" && launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then echo "unchanged $label"; continue; fi
  cp "$p" "$HOME/Library/LaunchAgents/"
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$label.plist"; echo "scheduled $label"
done
