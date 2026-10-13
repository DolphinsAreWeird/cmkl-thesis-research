"""Keep GDELT news themes and tone (theme x week) up to date inside the BigQuery free tier (1 TB a month, no billing).
Runs weekly. Each run fills from the day after the last covered date to the most recent full week (Monday to Sunday),
after checking the cost with a free dry run. If the gap is too large for one month it takes the largest part that fits
and the rest follows after the next monthly reset. Same query as code/gdelt_weekly.py.
State: data/gdelt/state.json   Output: data/gdelt/gdelt_weekly_START_END.parquet"""
import json, datetime as dt, pathlib, sys
from google.cloud import bigquery
HERE=pathlib.Path(__file__).parent; OUT=HERE/'data'/'gdelt'; OUT.mkdir(parents=True,exist_ok=True)
STATE=OUT/'state.json'; CAP_TB=0.9
# Seed: 2017-01-01 to 2021-06-30 was collected on 13 Oct 2026 (data/raw/gdelt_weekly_2017_2021H1.parquet, 0.885 TB),
# which used up October's free quota, so the next run must wait for the 1 November reset.
st=json.loads(STATE.read_text()) if STATE.exists() else {'covered_end':'2021-06-30','not_before':'2026-11-02','runs':[]}
Q="""SELECT DATE_TRUNC(DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S',CAST(DATE AS STRING))),WEEK(MONDAY)) AS week,
       REGEXP_EXTRACT(t,r'^([^,]+)') AS theme, COUNT(*) AS mentions,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(0)] AS FLOAT64)) AS tone,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(1)] AS FLOAT64)) AS positive,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(2)] AS FLOAT64)) AS negative
FROM `gdelt-bq.gdeltv2.gkg_partitioned`, UNNEST(SPLIT(V2Themes,';')) AS t
WHERE _PARTITIONTIME BETWEEN TIMESTAMP('{s}') AND TIMESTAMP('{e}') AND t!='' AND NOT STARTS_WITH(t,'TAX_WORLDLANGUAGES')
GROUP BY week, theme HAVING mentions>=50"""
today=dt.date.today()
if today<dt.date.fromisoformat(st['not_before']): print(f"{today}: waiting for the quota reset ({st['not_before']})"); sys.exit(0)
start=dt.date.fromisoformat(st['covered_end'])+dt.timedelta(days=1)
end=today-dt.timedelta(days=2); end-=dt.timedelta(days=(end.weekday()+1)%7)          # last full Sunday, 2+ days old
if end<start: print(f'{today}: up to date (covered to {st["covered_end"]})'); sys.exit(0)
c=bigquery.Client.from_service_account_json(str(HERE/'secrets'/'gcp_key.json'))
cost=lambda s,e: c.query(Q.format(s=s,e=e),job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False)).total_bytes_processed/1e12
tb=cost(start,end)
while tb>CAP_TB:                                                                      # too big for one month: halve, keep Sunday ends
    end=start+(end-start)/2; end-=dt.timedelta(days=(end.weekday()+1)%7)
    if end<start: sys.exit('cannot fit even one week under the cap')
    tb=cost(start,end)
print(f'{today}: querying {start} to {end}, estimated {tb:.3f} TB',flush=True)
df=c.query(Q.format(s=start,e=end)).to_dataframe()
f=OUT/f'gdelt_weekly_{start}_{end}.parquet'; df.to_parquet(f,index=False)
st['covered_end']=str(end); st['runs'].append(dict(ran=str(today),start=str(start),end=str(end),tb=round(tb,3),rows=len(df)))
if end<today-dt.timedelta(days=9): st['not_before']=str((today.replace(day=1)+dt.timedelta(days=32)).replace(day=2))   # rest after next reset
STATE.write_text(json.dumps(st,indent=1))
print(f'saved {f.name}: {len(df)} rows, {df.theme.nunique()} themes, {df.week.nunique()} weeks',flush=True)
