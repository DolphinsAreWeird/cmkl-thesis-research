"""Watch for the Seattle library's next months (Checkouts by Title, data.seattle.gov, resource tmmm-ytt6) for the final unseen
tests: addendum l (September 2026 only) and the benchmark's final test (addendum d, September to November 2026).
Counts only, the same query as 28_final_test_download.py --list: rows and loans per material type and month, plus the dataset's
last-update time. It reads no title, subject or loan value of any month, downloads nothing and changes nothing in the project.
4 requests a run, 1 s apart. When a month after 2026-08 has rows for all three material types (the downloader's rule for
'released'), it shows a macOS notification once for that month and records it.
Data: ~/thesis-collectors/data/seattle_release/ (data/collectors/seattle_release/ in the project): status.json (latest check,
latest month, months released and when each was first seen), checks.csv (one line a run). Log: ~/thesis-collectors/logs/seattle_release.log.
  python seattle_release_watch.py               (one check; launchd runs it at 09:00 and 21:00)
  python seattle_release_watch.py --test-alert  (one check, then a test notification)"""
import sys, json, time, pathlib, subprocess, requests
from ol_common import user_agent

URL = 'https://data.seattle.gov/resource/tmmm-ytt6.json'
META = 'https://data.seattle.gov/api/views/tmmm-ytt6.json'
TYPES = ['AUDIOBOOK', 'EBOOK', 'BOOK']
LAST_KNOWN = 2026 * 12 + 8                     # August 2026: the last month inside the frozen data
OUT = pathlib.Path.home() / 'thesis-collectors' / 'data' / 'seattle_release'
H = {'User-Agent': user_agent(), 'Accept': 'application/json'}


def log(*a):
    print(time.strftime('%Y-%m-%d %H:%M'), *a, flush=True)


def get(url, params=None, tries=3):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=120)
            if r.status_code == 200:
                return r.json()
            log('status', r.status_code, r.text[:200])
        except Exception as e:
            log('retry', str(e)[:100])
        time.sleep(20 * (k + 1))
    return None


def notify(title, text):
    subprocess.run(['osascript', '-e', f'display notification {json.dumps(text)} with title {json.dumps(title)} sound name "Glass"'],
                   check=False, timeout=30)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = get(META)
    updated = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(meta['rowsUpdatedAt'])) if meta and meta.get('rowsUpdatedAt') else None
    months = {}                                # (year, month) -> {material type: [rows, loans]}
    for mt in TYPES:
        time.sleep(1)
        j = get(URL, {'$select': 'checkoutyear,checkoutmonth,count(*) AS n_rows,sum(checkouts) AS checkouts',
                      '$where': f"materialtype='{mt}' AND checkoutyear>='2026'", '$group': 'checkoutyear,checkoutmonth', '$limit': 5000})
        if j is None:
            log('API failed; next scheduled check tries again')
            return
        for x in j:
            months.setdefault((int(x['checkoutyear']), int(x['checkoutmonth'])), {})[mt] = [int(x['n_rows']), int(float(x['checkouts']))]
    latest = max(months, default=None)
    sf = OUT / 'status.json'
    st = json.loads(sf.read_text()) if sf.exists() else {'released': {}}
    now = time.strftime('%Y-%m-%d %H:%M', time.gmtime()) + ' UTC'
    new = []
    for (y, m), c in sorted(months.items()):
        ym = f'{y}-{m:02d}'
        if y * 12 + m <= LAST_KNOWN:
            continue
        if set(c) == set(TYPES):
            if ym not in st['released']:
                st['released'][ym] = {'first_seen': now, 'counts': c}
                new.append(ym)
        else:
            log(f'{ym} partly released ({sorted(c)}); not counted until all three material types have rows')
    st.update(last_check=now, library_last_update=updated, latest_month=f'{latest[0]}-{latest[1]:02d}' if latest else None)
    sf.write_text(json.dumps(st, indent=1))
    cf = OUT / 'checks.csv'
    if not cf.exists():
        cf.write_text('checked_utc,library_last_update,latest_month,months_after_2026_08\n')
    with open(cf, 'a') as f:
        f.write(f"{now},{updated},{st['latest_month']},{' '.join(st['released']) or '-'}\n")
    log(f"latest month {st['latest_month']}, library last updated {updated}, released after 2026-08: {list(st['released']) or 'none'}")
    for ym in new:
        notify('Seattle library: new month released', f'{ym} is out. Tell Claude "{ym} is out" to run the final-test steps.')
        log('ALERT', ym, 'released; notification shown')
    if '--test-alert' in sys.argv:
        notify('Seattle library watch (test)', f"Watcher works. Latest month: {st['latest_month']}. You will get an alert like this when September 2026 is out.")
        log('test notification shown')


if __name__ == '__main__':
    main()
