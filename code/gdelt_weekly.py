# GDELT news themes and tone, aggregated to theme x week (BigQuery sandbox, free tier; key kept outside the repo and paper).
import sys, pandas as pd
from google.cloud import bigquery
from config import GCP_KEY
c=bigquery.Client.from_service_account_json(GCP_KEY)
start,end,out=sys.argv[1],sys.argv[2],sys.argv[3]
q=f"""
SELECT DATE_TRUNC(DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S',CAST(DATE AS STRING))),WEEK(MONDAY)) AS week,
       REGEXP_EXTRACT(t,r'^([^,]+)') AS theme,
       COUNT(*) AS mentions,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(0)] AS FLOAT64)) AS tone,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(1)] AS FLOAT64)) AS positive,
       AVG(SAFE_CAST(SPLIT(V2Tone,',')[OFFSET(2)] AS FLOAT64)) AS negative
FROM `gdelt-bq.gdeltv2.gkg_partitioned`, UNNEST(SPLIT(V2Themes,';')) AS t
WHERE _PARTITIONTIME BETWEEN TIMESTAMP('{start}') AND TIMESTAMP('{end}') AND t!='' AND NOT STARTS_WITH(t,'TAX_WORLDLANGUAGES')
GROUP BY week, theme HAVING mentions>=50"""
dry=c.query(q,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False)).total_bytes_processed/1e12
print('estimated scan',round(dry,3),'TB',flush=True)
if '--dry' in sys.argv: raise SystemExit(0)   # estimate only, uses no quota
if dry>0.95: raise SystemExit('Over the free monthly limit; split the range.')
df=c.query(q).to_dataframe(); df.to_parquet(out,index=False); print('rows',len(df),'themes',df.theme.nunique(),'weeks',df.week.nunique(),flush=True)
