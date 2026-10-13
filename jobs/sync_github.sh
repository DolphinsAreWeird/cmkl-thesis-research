#!/bin/bash
# Copies the public parts of the project into a clone of the GitHub repo, checks them for secrets and large
# files, and commits them on a new branch. Pushing and the pull request are separate steps (see the end).
# Only what is listed here is ever copied: context/, paper/, CLAUDE.md, data/ (except reports), .env and
# secrets/ never leave this Mac.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLONE="${CLONE:-$HOME/cmkl-thesis-research}"
REPO="DolphinsAreWeird/cmkl-thesis-research"

[ -d "$CLONE/.git" ] || gh repo clone "$REPO" "$CLONE"
cd "$CLONE"
git checkout -q main && git pull -q --ff-only

EX=(--exclude __pycache__ --exclude '*.pyc' --exclude .env --exclude catboost_info --exclude .DS_Store
    --exclude data --exclude .venv --exclude '*.log' --exclude '*.pid' --exclude '*.parquet')
rsync -a --delete "${EX[@]}" "$ROOT/code/" "$CLONE/code/"
rsync -a --delete "${EX[@]}" --exclude TASK_PROMPT.md "$ROOT/collectors/" "$CLONE/collectors/"
rsync -a --delete "${EX[@]}" "$ROOT/jobs/" "$CLONE/jobs/"
rsync -a --delete "${EX[@]}" "$ROOT/prereg/" "$CLONE/prereg/"
mkdir -p "$CLONE/results/reports"
rsync -a --delete --include '*.md' --include '*.csv' --exclude '*' "$ROOT/data/reports/" "$CLONE/results/reports/"
# public root files (README, PRIVACY, TERMS, .gitignore, collect/) live in repo_public/
rsync -a --exclude requirements.txt "$ROOT/repo_public/" "$CLONE/"
cp "$ROOT/requirements.txt" "$ROOT/requirements.lock" "$CLONE/"

# checks: stop before committing anything that looks like a key or is too big for GitHub
PAT='AIza[0-9A-Za-z_-]{20,}|api-key=[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|BEGIN (RSA )?PRIVATE KEY|"private_key"|private_key_id'
if grep -rIlE "$PAT" --exclude-dir=.git --exclude=sync_github.sh . ; then echo "STOP: possible secret in the files above"; exit 1; fi
for k in NYT_API_KEY YOUTUBE_API_KEY TUMBLR_CONSUMER_KEY; do
  v=$(grep -h "^$k=" "$ROOT/.env" "$ROOT/collectors/.env" 2>/dev/null | head -1 | cut -d= -f2- | cut -d' ' -f1 || true)
  if [ -n "${v:-}" ] && [ ${#v} -ge 12 ] && grep -rIlF --exclude-dir=.git --exclude=sync_github.sh -- "$v" . ; then echo "STOP: the value of $k appears above"; exit 1; fi
done
big=$(find . -path ./.git -prune -o -type f -size +50M -print)
if [ -n "$big" ]; then echo "STOP: files over 50 MB: $big"; exit 1; fi

BRANCH="sync-$(date +%Y%m%d-%H%M)"
git checkout -q -b "$BRANCH"
git add -A
if git diff --cached --quiet; then echo "nothing changed"; git checkout -q main; git branch -q -D "$BRANCH"; exit 0; fi
git -c core.quotepath=off diff --cached --stat | tail -3
echo "branch: $BRANCH  (next: git commit, git push -u origin $BRANCH, gh pr create)"
