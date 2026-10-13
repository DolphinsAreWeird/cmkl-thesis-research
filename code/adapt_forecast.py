# Code adaptations as faithful or loose, use only pre-release attention, fit a small lift model, and forecast The Odyssey blind.
import pandas as pd, numpy as np, requests, time, urllib.parse, json
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from config import UA
H={"User-Agent":UA}
R=pd.read_csv('reports/adaptation_wide.csv'); R['date']=pd.to_datetime(R.date)
faithful={'Nosferatu_(2024_film)','Wuthering_Heights_(2026_film)','Little_Women_(2019_film)','Frankenstein_(2025_film)','Persuasion_(2022_film)','Emma_(2020_film)',
 'The_Secret_Garden_(2020_film)',"The_Three_Musketeers:_D'Artagnan",'The_Count_of_Monte_Cristo_(2024_film)','The_Three_Musketeers:_Milady','Passing_(film)',
 "Virginia_Woolf's_Night_and_Day",'The_Personal_History_of_David_Copperfield','Carmilla_(film)','Pinocchio_(2019_film)','The_Velveteen_Rabbit_(2023_film)','White_Fang_(2018_film)'}
R['faithful']=R.adaptation.isin(faithful).astype(int)
R['precise_date']=~((R.date.dt.month==1)&(R.date.dt.day==1))
def pre_peak(a,d):
    s=(d-pd.Timedelta(days=120)).strftime('%Y%m%d'); e=(d-pd.Timedelta(days=7)).strftime('%Y%m%d')
    for k in range(5):
        r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/daily/{s}/{e}",headers=H,timeout=30)
        if r.status_code==200:
            v=pd.Series({pd.Timestamp(x['timestamp'][:8]):x['views'] for x in r.json()['items']}); return float(v.resample('W').sum().max()) if len(v) else 0.0
        if r.status_code==404: return 0.0
        time.sleep(int(r.headers.get('retry-after',5))+1)
    return np.nan
R['pre_peak']=[(time.sleep(0.9) or pre_peak(a,d)) for a,d in zip(R.adaptation,R.date)]
U=R[R.precise_date].copy(); U['x']=np.log1p(U.pre_peak); U['y']=np.log(U.lift)
print('usable (precise dates)',len(U),'| faithful',U.faithful.sum())
big=U.ad_peak>=100000
print(pd.crosstab([big.rename('big'),U.faithful.rename('faithful')],(U.lift>=1.3).rename('lift>=1.3')))
for f in [1,0]:
    g=U[big&(U.faithful==f)]; print('big & faithful' if f else 'big & loose', 'n',len(g),'median lift',round(g.lift.median(),2),'share>=1.3',round((g.lift>=1.3).mean(),2))
# small linear model: log lift = a + b*x*faithful + c*x*(1-faithful), leave-one-out
X=np.c_[np.ones(len(U)),U.x*U.faithful,U.x*(1-U.faithful)]; y=U.y.values; loo=[]
for i in range(len(U)):
    m=np.ones(len(U),bool); m[i]=False; co=np.linalg.lstsq(X[m],y[m],rcond=None)[0]; loo.append(X[i]@co)
U['loo']=loo
print('LOO Spearman',round(spearmanr(U.loo,U.y).correlation,2),'| LOO AUC lift>=1.3',round(roc_auc_score((U.lift>=1.3),U.loo),3))
base_x=np.c_[np.ones(len(U)),U.x*0,U.x]; 
co=np.linalg.lstsq(X,y,rcond=None)[0]; co_size=np.linalg.lstsq(np.c_[np.ones(len(U)),U.x],y,rcond=None)[0]
loo2=[]
for i in range(len(U)):
    m=np.ones(len(U),bool); m[i]=False; c=np.linalg.lstsq(np.c_[np.ones(m.sum()),U.x[m]],y[m],rcond=None)[0]; loo2.append(c[0]+c[1]*U.x.iloc[i])
print('size-only LOO Spearman',round(spearmanr(loo2,U.y).correlation,2),'| AUC',round(roc_auc_score((U.lift>=1.3),loo2),3))
print('coefficients (intercept, faithful slope, loose slope):',np.round(co,3))
# blind forecast for The Odyssey (faithful), using attention up to one week before release
od_pre=pre_peak('The_Odyssey_(2026_film)',pd.Timestamp('2026-07-17'))
pred=float(np.exp(co[0]+co[1]*np.log1p(od_pre)))
w=pd.read_csv('reports/odyssey_weekly.csv',index_col=0,parse_dates=True).listens
d=w.resample('MS').sum(); d.loc['2026-09-01']=w.loc['2026-09-01':'2026-09-14'].sum()*30/14
base=d.loc['2025-07-01':'2026-01-01'].median(); actual=d.loc['2026-07-01':'2026-09-01'].mean()/base
out=dict(odyssey_pre_release_peak_weekly_views=od_pre,predicted_lift=round(pred,2),actual_lift=round(float(actual),2))
print(json.dumps(out)); U.to_csv('reports/adaptation_coded.csv',index=False); json.dump(out,open('reports/odyssey_blind_forecast.json','w'))
