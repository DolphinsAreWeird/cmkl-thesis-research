# Helper for the figurative-use check (not part of run_all.sh; run once, results cached).
# For candidate driver codes whose word is often used figuratively in news (witch hunt, a gamble, a blind eye, deaf ears,
# icy relations, political earthquake...) or whose rises look like a feed artefact, take a sample of article URLs on the
# middle day of each of the code's two highest-volume weeks (from gdelt/driver_evidence.csv). GDELT article URLs usually
# contain the headline words, which show how the word was used. Source: GDELT GKG 2.0 in BigQuery (the project's sandbox,
# same route as code/gdelt_weekly.py). Each day scanned costs about 0.8 GB of the free monthly quota; the script stops
# if a free dry run says the total would pass BUDGET_GB. URLs are news article addresses only (no personal data).
# Output: data/db/interest/gdelt/figurative_url_samples.csv (code, day, records that day, up to 40 sampled URLs)
import os, sys, json, pandas as pd
from _ci import GD, HERE
sys.path.insert(0, str(HERE.parents[1]))
from config import GCP_KEY  # noqa: E402

BUDGET_GB = 45
CANDIDATES = ['TAX_RELIGION_WITCHCRAFT', 'TAX_DISEASE_GAMBLING', 'TAX_DISEASE_AMNESIA', 'TAX_DISEASE_BLINDNESS', 'TAX_DISEASE_DEAFNESS',
              'NATURAL_DISASTER_ICY', 'NATURAL_DISASTER_EARTHQUAKE', 'SOC_SUICIDE', 'TAX_DISEASE_CANCER', 'TAX_RELIGION_ATHEISM',
              'TAX_RELIGION_OCCULT', 'TAX_DISEASE_GENETIC_DISEASES', 'NATURAL_DISASTER_BLIZZARD', 'WB_1447_GERIATRICS',
              'WB_1532_TEACHER_TRAINING', 'CRISISLEX_O01_WEATHER', 'BULLYING', 'TAX_DISEASE_PSYCHOLOGICAL_TRAUMA', 'TAX_DISEASE_INSECT_BITE',
              'KIDNAP']
OUTF = f'{GD}/figurative_url_samples.csv'
EV = pd.read_csv(f'{GD}/driver_evidence.csv').set_index('code')
DRV = pd.read_csv(f'{GD}/driver_codes.csv', parse_dates=['start_week'])
pairs = []
for c in CANDIDATES:
    if c not in EV.index:
        continue
    weeks = [w.split(' ')[0] for w in str(EV.top_weeks[c]).split(' || ')][:2]           # two highest-volume weeks
    weeks += [str(w.date()) for w in DRV[DRV.driver == c].start_week.unique()]           # and the start week of every shift it drives
    for w in dict.fromkeys(weeks):
        pairs.append((c, str((pd.Timestamp(w) + pd.Timedelta(days=2)).date())))
pairs = list(dict.fromkeys(pairs))
done = pd.read_csv(OUTF) if os.path.exists(OUTF) else pd.DataFrame(columns=['code', 'day', 'records', 'urls'])
todo = [p for p in pairs if not ((done.code == p[0]) & (done.day == p[1])).any()]
days = sorted({d for _, d in todo})
print('code-day pairs to sample', len(todo), 'distinct days', len(days), flush=True)
if not todo:
    raise SystemExit(0)
from google.cloud import bigquery  # noqa: E402
cl = bigquery.Client.from_service_account_json(GCP_KEY)


def query(day, codes):
    arr = ', '.join(f"'{c}'" for c in codes)
    return f"""SELECT code, COUNT(*) AS records,
      ARRAY_AGG(DocumentIdentifier ORDER BY FARM_FINGERPRINT(DocumentIdentifier) LIMIT 40) AS urls
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`, UNNEST([{arr}]) AS code
    WHERE _PARTITIONTIME = TIMESTAMP('{day}') AND REGEXP_CONTAINS(V2Themes, CONCAT(r'(^|;)', code, ','))
    GROUP BY code"""


cost = sum(cl.query(query(d, sorted({c for c, dd in todo if dd == d})), job_config=bigquery.QueryJobConfig(
    dry_run=True, use_query_cache=False)).total_bytes_processed for d in days) / 1e9
print('estimated scan', round(cost, 1), 'GB', flush=True)
if cost > BUDGET_GB:
    raise SystemExit(f'over budget ({cost:.1f} GB > {BUDGET_GB} GB)')
rows = []
for d in days:
    codes = sorted({c for c, dd in todo if dd == d})
    for r in cl.query(query(d, codes)).result():
        rows.append(dict(code=r['code'], day=d, records=r['records'], urls=json.dumps(list(r['urls']))))
    print('day', d, 'done', flush=True)
out = pd.concat([done, pd.DataFrame(rows)], ignore_index=True)
out.to_csv(OUTF, index=False)
print('saved', len(out), 'code-day samples', flush=True)
