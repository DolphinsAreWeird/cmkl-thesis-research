# Build label and feature tables, including Wikipedia trend features computed only from months before each release.
import pandas as pd, numpy as np, json, ast, warnings, re
warnings.filterwarnings('ignore')
import pymannkendall as mk, ruptures as rpt
from statsmodels.tsa.seasonal import STL
from tslearn.clustering import KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from config import D
m=pd.read_pickle(f'{D}/interim/recordings_linked.pkl').reset_index(drop=True)
m['emb_row']=np.arange(len(m))
pv=json.load(open(f'{D}/raw/wiki_pageviews_monthly.json'))
tot={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly.json'))['items']}
months=pd.period_range('2015-07','2025-06',freq='M'); mkeys=[p.strftime('%Y%m') for p in months]
T=np.array([tot[k] for k in mkeys],dtype=float)
# ---------- labels ----------
m['days']=m.days_since_published
m['cohort']=m.publicdate.dt.year.astype('Int64').astype(str)+'H'+((m.publicdate.dt.month>6).astype(int)+1).astype(str)
m['log_view_rate']=np.log(m.views/m.days)
m['log_fav_rate']=np.log1p(1000*m.favorites/m.days)
for c in ['log_view_rate','log_fav_rate']:
    m['y_'+c.split('_')[1]]=m[c]-m.groupby('cohort')[c].transform('median')
# ---------- metadata ----------
def hrs(s):
    try: h,mi,se=[int(x) for x in str(s).split(':')]; return h+mi/60+se/3600
    except: return np.nan
m['log_hours']=np.log1p(m.totaltime.map(hrs))
m['log_sections']=np.log1p(m.num_sections)
m['narr_count']=np.log1p(m.groupby('narrator_id').narrator_id.transform('count'))
gc=m.genre_categories.map(lambda s: ast.literal_eval(s) if isinstance(s,str) else [])
top=pd.Series([g for l in gc for g in l]).value_counts().index[:20]
for g in top: m['g_'+re.sub(r'\W+','_',g).strip('_')]=gc.map(lambda l: int(g in l))
m['genre1']=gc.map(lambda l: l[0] if l else 'None')
# ---------- trend features ----------
def series(art):
    s=pv.get(art) if isinstance(art,str) else None
    if s is None: return None
    v=np.array([s.get(k,0) for k in mkeys],dtype=float)
    return np.log1p(v/T*1e6), v
def feats(art, rel):
    out={}
    r=series(art)
    if r is None or pd.isna(rel): return out
    x,raw=r
    idx=sum(1 for p in months if p<rel.to_period('M'))   # months strictly before release month
    if idx<12: return out
    xs,rs=x[:idx],raw[:idx]; l12=xs[-12:]
    out['level12']=l12.mean()
    out['rel_level']=l12.mean()-xs.mean()
    out['spike']=rs[-12:].max()/max(np.median(rs[-12:]),1)
    t=mk.original_test(l12); out['mk_tau']=t.Tau; out['sen_slope']=t.slope; out['mk_rising']=int(t.trend=='increasing')
    if idx>=24:
        st=STL(xs,period=12,robust=True).fit()
        out['stl_slope']=np.polyfit(np.arange(12),st.trend[-12:],1)[0]
        out['season_strength']=max(0.0,1-np.var(st.resid)/max(np.var(st.seasonal+st.resid),1e-9))
    if np.var(xs)>0:
        bk=rpt.Pelt(model='l2',min_size=3).fit(xs).predict(pen=2*np.log(len(xs))*np.var(xs))
        cps=[b for b in bk if b<len(xs)]
        out['n_breaks']=len(cps)
        if cps:
            last=cps[-1]; out['months_since_break']=len(xs)-last
            out['last_jump']=xs[last:].mean()-xs[max(0,last-6):last].mean()
        else: out['months_since_break']=len(xs); out['last_jump']=0.0
    out['_shape']=l12
    return out
rows=[]
for _,r in m.iterrows():
    d={}
    for src,col in [('wa_','wiki_author'),('wb_','wiki_book')]:
        f=feats(r[col],r.publicdate)
        d[src+'has']=int(bool(f))
        for k,v in f.items(): d[src+k]=v
    rows.append(d)
F=pd.DataFrame(rows)
for src in ['wa_','wb_']:
    S=F[src+'_shape'].dropna()
    S=S[S.map(lambda a: np.var(a)>0)]
    if len(S)>50:
        X=TimeSeriesScalerMeanVariance().fit_transform(np.stack(S.values)[:,:,None])
        ks=KShape(n_clusters=4,random_state=0,max_iter=50).fit(X)
        lab=pd.Series(ks.labels_,index=S.index)
        cen=ks.cluster_centers_[:,:,0]
        desc={k:('rising' if c[-3:].mean()-c[:3].mean()>0.5 else 'falling' if c[:3].mean()-c[-3:].mean()>0.5 else 'spike' if c.max()>2 else 'flat') for k,c in enumerate(cen)}
        for k in range(4): F[f'{src}shape{k}_{desc[k]}']=(lab==k).reindex(F.index).fillna(False).astype(int)
    F=F.drop(columns=[src+'_shape'])
m=pd.concat([m,F],axis=1)
G=[c for c in m.columns if c.startswith('g_')]
META=['log_hours','log_sections','narr_count']+G
VOL=['wa_has','wb_has','wa_level12','wb_level12']
TREND=[c for c in F.columns if c.startswith(('wa_','wb_')) and c not in VOL]
lab=m[['identifier','title','author','bookgroup','narrator_id','genre1','cohort','publicdate','days','views','favorites','log_view_rate','log_fav_rate','y_view','y_fav']]
fea=m[['identifier','emb_row','n_authors','wiki_author','wiki_book']+META+VOL+TREND]
lab.to_parquet(f'{D}/processed/labels.parquet'); fea.to_parquet(f'{D}/processed/features.parquet')
json.dump({'META':META,'VOL':VOL,'TREND':TREND},open(f'{D}/processed/feature_groups.json','w'),indent=1)
print('rows',len(m),'| META',len(META),'VOL',len(VOL),'TREND',len(TREND))
print('author series usable',m.wa_has.sum(),'book series usable',m.wb_has.sum())
