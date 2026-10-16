# Conversation sources, talk pages, step 1: daily edit counts of "Talk:<title>" for every English Wikipedia concept article
# in data/db/interest/wiki/articles.parquet (canonical titles), from the Wikimedia REST API
#   https://wikimedia.org/api/rest_v1/metrics/edits/per-page/en.wikipedia/<page>/<editor-type>/daily/<start>/<end>
# Editor types fetched separately: user (registered, not bot), anonymous, group-bot, name-bot. Human edits = user + anonymous;
# the API has no single "all except bots" value, so bots are excluded by leaving out the two bot types (the bot counts are
# kept to report the bot share). A 404 means "no edits in the range" and counts as zero. Counts only: the API returns no
# editor names and none are stored. Cache: one small JSON per page and editor type under data/interim/talk_edits_cache/,
# so a rerun resumes. At most 4 requests a second in total (a shared 0.25 s gap; 4 threads overlap the 2 to 3 s answer time), project User-Agent with kwai@cmkl.ac.th, nice 10.
# Range: 2015-01-01 to 2026-09-30 (2015 is burn-in for the 52-week normaliser; see DEVIATIONS.md).
import os, sys, json, time, hashlib, pathlib, threading, urllib.parse, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from config import D, UA  # noqa: E402

os.nice(10)
API = 'https://wikimedia.org/api/rest_v1/metrics/edits/per-page/en.wikipedia'
START, END = '20150101', '20260930'
TYPES = ['user', 'anonymous', 'group-bot', 'name-bot']
CACHE = pathlib.Path(f'{D}/interim/talk_edits_cache')
CACHE.mkdir(parents=True, exist_ok=True)
GAP = 0.25
last = [0.0]
lock = threading.Lock()
sess = requests.Session()
sess.headers['User-Agent'] = UA


def fid(title, typ):
    return hashlib.sha1(f'Talk:{title}|{typ}'.encode()).hexdigest()[:20] + '.json'


def get(title, typ):
    url = f"{API}/{urllib.parse.quote('Talk:' + title.replace(' ', '_'), safe=':')}/{typ}/daily/{START}/{END}"
    for k in range(8):
        with lock:                       # one shared clock: requests start at least GAP seconds apart
            w = last[0] + GAP - time.time()
            if w > 0:
                time.sleep(w)
            last[0] = time.time()
        try:
            r = sess.get(url, timeout=60)
        except Exception:
            time.sleep(3 * (k + 1)); continue
        if r.status_code == 200:
            res = r.json()['items'][0]['results']
            return dict(status=200, daily={x['timestamp'][:10]: x['edits'] for x in res if x['edits']})
        if r.status_code == 404:
            return dict(status=404, daily={})
        time.sleep(int(r.headers.get('retry-after', 4 * (k + 1))) + 1)
    return None


A = pd.read_parquet(f'{D}/db/interest/wiki/articles.parquet')
titles = sorted(A.canonical.dropna().unique())
t0 = time.time()


def work(job):
    title, typ = job
    f = CACHE / fid(title, typ)
    if f.exists():
        return None
    out = get(title, typ)
    if out is None:
        return job
    out.update(title=title, type=typ)
    tmp = f.with_suffix('.part')
    tmp.write_text(json.dumps(out))
    os.replace(tmp, f)
    return True


jobs = [(t, y) for t in titles for y in TYPES]
for p in range(3):
    failed, done = [], 0
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(work, jobs):
            if r is True:
                done += 1
                if done % 200 == 0:
                    print(f'pass {p} fetched {done} calls, {time.time() - t0:.0f}s', flush=True)
            elif r is not None:
                failed.append(r)
    print(f'pass {p} done, new calls {done}, failed {len(failed)}', flush=True)
    if not failed:
        break
    jobs = failed
    time.sleep(120)
n_have = sum((CACHE / fid(t, y)).exists() for t in titles for y in TYPES)
print(f'DONE cached {n_have} of {len(titles) * len(TYPES)} calls, failed {len(failed)}, {time.time() - t0:.0f}s', flush=True)
