# Scheduled collectors (run on Khant's Mac by launchd)

These scripts are the source. `jobs/deploy_collectors.sh` copies them to `~/thesis-collectors` (with its own `.venv`, a copy of `.env` and `secrets/gcp_key.json`, both chmod 600) and loads the launchd schedules in `jobs/launchd/`. They run from outside Documents because macOS blocks background jobs from reading the Documents folder unless a privacy permission is changed. Rerun the deploy script after editing anything here.

| Schedule | What | Limit it respects |
|---|---|---|
| Daily 21:00 (`run_daily.sh`) | `bluesky_sample.py 60`: one hour of public posts; then `nyt_bestsellers.py`: next batch of NYT weeks | NYT 500 calls a day: capped at 480 in any 24 hours (`data/nyt/_calls.json`) |
| Mondays 10:00 (`gdelt_update.py`) | GDELT themes and tone per week, up to the last full week | BigQuery free tier 1 TB a month: free dry run first, 0.9 TB cap, splits across months if needed |

If the Mac is asleep at the scheduled time, launchd runs the job once when it wakes. Logs: `~/thesis-collectors/logs/`. Data: `~/thesis-collectors/data/`, also visible as `data/collectors/` in the project.

## What is kept
- Bluesky: post time, language and text only. Account IDs, handles, @mentions and links are removed before saving.
- NYT: list name, rank, weeks on list, title, author, ISBN, publisher, description. The overview endpoint has no lists before 2009; those weeks are saved empty.
- GDELT: theme, week, mention count, average tone (overall, positive, negative). Seed range 2017-01-01 to 2021-06-30 is in `data/raw/gdelt_weekly_2017_2021H1.parquet`; the week of 28 Jun 2021 is split across that file and the next one (add mentions, weight tone by mentions when joining).

## Useful commands
`launchctl print gui/$(id -u)/com.khant.thesis.daily` (state), `launchctl kickstart gui/$(id -u)/com.khant.thesis.daily` (run now), `launchctl bootout gui/$(id -u)/com.khant.thesis.daily` (turn off).

## Privacy
Do not publish the raw Bluesky files. Only aggregated, anonymous results (counts and sentiment by topic and week) go into the thesis. Delete raw social text within three months after the thesis.
