"""Weekly snapshot of Open Library reading-log counts for the study's books (addendum i, D4_intent_collection).
For every Open Library work in mapping.parquet (made once by openlibrary_map.py) it saves the public totals of the
work's reading log: want to read, currently reading, already read (and stopped reading, which the API also gives).
Endpoint: https://openlibrary.org/works/OL...W/bookshelves.json  ->  {"counts": {"want_to_read": n, ...}}
These are totals per work; no user, list or account data is requested or stored.
Weeks run Thursday to Wednesday (the first snapshot is Thursday 22 Oct 2026); a snapshot is named by its Thursday.
launchd starts this script every day at 09:30; it does nothing when this week's snapshot is finished, so a run cut short
(sleep, network) carries on the next day from where it stopped. A snapshot still unfinished when the next week starts is
closed as '_incomplete'. Before fetching, the week's keys are checked in batches (search API, 100 a request) so merged
works are followed to their new key (otherwise the old key reads 0). At most 1 request a second (1.05 s gap), the project
user agent with a contact address; the lock shared with openlibrary_map.py keeps the two from running together.
Output (data/openlibrary/): snapshots/reading_log_YYYY-MM-DD.csv.gz, one file a week, columns
  snapshot_date, ol_work, ol_work_fetched (only when the key was merged), want_to_read, currently_reading, already_read,
  stopped_reading, status (ok, merged, gone, failed), fetched_at_utc
and snapshot_log.csv (one line a week). Join to the study books with mapping.parquet (work_id -> ol_work)."""
import sys, csv, gzip, json, time, hashlib, pathlib, datetime as dt
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import ol_common as C

ANCHOR = 3                                  # Thursday
SNAP = C.OUT / 'snapshots'
LOGF = C.OUT / 'snapshot_log.csv'
COLS = ['ol_work', 'ol_work_fetched', 'want_to_read', 'currently_reading', 'already_read', 'stopped_reading', 'status', 'fetched_at_utc']
SHELVES = ['want_to_read', 'currently_reading', 'already_read', 'stopped_reading']


def log(*a):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), *a, flush=True)


def week_of(d):
    return d - dt.timedelta(days=(d.weekday() - ANCHOR) % 7)


def read_part(p):
    return pd.read_csv(p, dtype={'ol_work': str, 'ol_work_fetched': str, 'status': str}, keep_default_na=False) if p.exists() else pd.DataFrame(columns=COLS)


def finish(wk, keys, meta, complete):
    part = SNAP / f'_partial_{wk}.csv'
    df = read_part(part).drop_duplicates('ol_work', keep='last').sort_values('ol_work')
    df.insert(0, 'snapshot_date', str(wk))
    out = SNAP / (f'reading_log_{wk}.csv.gz' if complete else f'reading_log_{wk}_incomplete.csv.gz')
    with gzip.open(out, 'wt', newline='') as fh:
        df.to_csv(fh, index=False)
    num = df[df.status.isin(['ok', 'merged'])]
    line = dict(snapshot_date=str(wk), started=meta.get('started', ''), finished=dt.datetime.now().isoformat(timespec='seconds'),
                complete=complete, works=len(keys), rows=len(df), ok=int((df.status == 'ok').sum()), merged=int((df.status == 'merged').sum()),
                gone=int((df.status == 'gone').sum()), failed=len(keys) - len(num) - int((df.status == 'gone').sum()),
                **{f'sum_{s}': int(pd.to_numeric(num[s], errors='coerce').fillna(0).sum()) for s in SHELVES},
                requests=meta.get('requests', 0), mapping_sha256=meta.get('mapping_sha256', ''), file=out.name)
    new = not LOGF.exists()
    with open(LOGF, 'a', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(line))
        if new:
            w.writeheader()
        w.writerow(line)
    part.unlink(missing_ok=True)
    (SNAP / f'_check_{wk}.json').unlink(missing_ok=True)
    (SNAP / f'_meta_{wk}.json').unlink(missing_ok=True)
    log(f'saved {out.name}: {len(df):,} works, {line["ok"]:,} ok, {line["merged"]} merged, {line["gone"]} gone, {line["failed"]} failed')


def main():
    lock = C.take_lock()
    if lock is None:
        log('another Open Library job is running; trying again tomorrow'); return
    sf = C.OUT / 'mapping_summary.json'
    if not sf.exists() or not json.loads(sf.read_text()).get('complete'):
        log('the mapping (openlibrary_map.py) is not finished; nothing to do'); return
    keys = sorted(pd.read_parquet(C.OUT / 'mapping.parquet', columns=['ol_work']).ol_work.dropna().unique())
    msha = json.loads(sf.read_text()).get('sha256_mapping_csv', '')
    SNAP.mkdir(parents=True, exist_ok=True)
    wk = week_of(dt.date.today())
    for p in sorted(SNAP.glob('_partial_*.csv')):                    # unfinished snapshot of an earlier week
        old = dt.date.fromisoformat(p.stem.rsplit('_', 1)[-1])
        if old != wk:
            mf = SNAP / f'_meta_{old}.json'
            finish(old, keys, json.loads(mf.read_text()) if mf.exists() else {}, complete=False)
    if (SNAP / f'reading_log_{wk}.csv.gz').exists():
        log(f'snapshot of the week starting {wk} is already finished'); return

    mf = SNAP / f'_meta_{wk}.json'
    meta = json.loads(mf.read_text()) if mf.exists() else dict(started=dt.datetime.now().isoformat(timespec='seconds'), requests=0, mapping_sha256=msha)
    cli, base = C.Client(gap=1.05, log=log), meta.get('requests', 0)
    mf.write_text(json.dumps(meta))
    cf = SNAP / f'_check_{wk}.json'
    if cf.exists():
        chk = json.loads(cf.read_text())
    else:
        log(f'week {wk}: checking {len(keys):,} work keys for merges')
        chk = C.check_keys(cli, keys, log=log)
        cf.write_text(json.dumps({k: dict(status=v['status'], work=v['work']) for k, v in chk.items()}))
    n_red = sum(v['status'] == 'redirect' for v in chk.values()); n_gone = sum(v['status'] == 'gone' for v in chk.values())
    part = SNAP / f'_partial_{wk}.csv'
    done = set(read_part(part).query("status != 'failed'").ol_work)
    todo = [k for k in keys if k not in done]
    log(f'week {wk}: {len(keys):,} works, {len(done):,} already saved, {len(todo):,} to fetch ({n_red} merged, {n_gone} gone); '
        f'about {len(todo) * 1.05 / 3600:.1f} h')
    new = not part.exists()
    fh = open(part, 'a', newline='')
    w = csv.writer(fh)
    if new:
        w.writerow(COLS)
    t0, stopped = time.time(), False
    for n, k in enumerate(todo, 1):
        c = chk.get(k, {'status': 'unknown', 'work': k})
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
        if c['status'] == 'gone':
            w.writerow([k, '', '', '', '', '', 'gone', now]); fh.flush(); continue
        tgt = c['work'] or k
        j = cli.get(f'{C.OL}/works/{tgt}/bookshelves.json')
        cnt = j.get('counts') if isinstance(j, dict) else None
        if not isinstance(cnt, dict):
            w.writerow([k, tgt if tgt != k else '', '', '', '', '', 'failed', now]); fh.flush()
            if cli.fail_run >= 15:
                log('Open Library has not answered 15 works in a row; stopping, the next run carries on'); stopped = True; break
            continue
        w.writerow([k, tgt if tgt != k else '', *[cnt.get(s, '') for s in SHELVES], 'merged' if tgt != k else 'ok', now]); fh.flush()
        if n % 1000 == 0:
            el = time.time() - t0
            log(f'  {n:,} of {len(todo):,} ({el / n:.2f} s a work, about {(len(todo) - n) * el / n / 3600:.1f} h left)')
    fh.close()
    if stopped:
        meta['requests'] = base + cli.n; mf.write_text(json.dumps(meta))
        return
    df = read_part(part).drop_duplicates('ol_work', keep='last')
    failed = sorted(set(df[df.status == 'failed'].ol_work) | (set(keys) - set(df.ol_work)))
    if failed:                                                         # one more try for the works that failed
        log(f'retrying {len(failed)} works that failed')
        with open(part, 'a', newline='') as fh:
            w = csv.writer(fh)
            for k in failed:
                tgt = chk.get(k, {}).get('work') or k
                j = cli.get(f'{C.OL}/works/{tgt}/bookshelves.json')
                cnt = j.get('counts') if isinstance(j, dict) else None
                now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
                if isinstance(cnt, dict):
                    w.writerow([k, tgt if tgt != k else '', *[cnt.get(s, '') for s in SHELVES], 'merged' if tgt != k else 'ok', now]); fh.flush()
    meta['requests'] = base + cli.n
    finish(wk, keys, meta, complete=True)


if __name__ == '__main__':
    main()
