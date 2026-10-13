# Weekly event study (spike vs sustained rise) and a hidden-book lift model from attention shape alone.
import pandas as pd, numpy as np, json, warnings, matplotlib
warnings.filterwarnings('ignore'); matplotlib.use('Agg'); import matplotlib.pyplot as plt
import lightgbm as lgb, pymannkendall as mk
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from config import D, FIGS; O=FIGS
S=json.load(open(f'{D}/interim/weekly_scope.json')); W=json.load(open(f'{D}/raw/wiki_book_daily.json')); Lr=json.load(open(f'{D}/raw/ia_views_daily_books.json'))
T={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly_to2026.json'))['items']}
lab=pd.read_parquet(f'{D}/processed/labels.parquet').set_index('identifier')
M=pd.DataFrame(S['map'])
weeks=pd.date_range('2017-01-02','2026-08-24',freq='W-MON')
def weekly(d,fmt):
    s=pd.Series({pd.Timestamp(k if fmt=='iso' else f'{k[:4]}-{k[4:6]}-{k[6:8]}'):v for k,v in d.items()},dtype=float)
    return s.resample('W-MON',label='left',closed='left').sum().reindex(weeks).fillna(0)
books=[]
for bg,g in M.groupby('bookgroup'):
    a=g.art.iloc[0]
    if not W.get(a): continue
    att=weekly(W[a],'ymd'); norm=np.array([T.get(w.strftime('%Y%m'),np.nan) for w in weeks]); att_n=att/norm*1e9
    lis=sum(weekly(Lr.get(i,{}),'iso') for i in g.identifier)
    rels=[lab.publicdate.get(i) for i in g.identifier if i in lab.index]
    books.append(dict(bg=bg,title=g.title.iloc[0],art=a,att=att_n.values,raw=att.values,lis=lis.values,rels=[r.tz_localize(None) for r in rels if pd.notna(r)]))
print('books',len(books))
def near_launch(b,w): return any(-8<=(w-r).days/7<=40 for r in b['rels'])
# ---------- event study ----------
ev=[]
for b in books:
    a=b['att']; last=-99
    for t in range(30,len(weeks)-13):
        base=np.median(a[t-26:t])
        if base<=0 or a[t]<3*base or b['raw'][t]<2000 or a[t]<a[max(0,t-4):t+5].max() or t-last<8: continue
        if near_launch(b,weeks[t]) or b['lis'][t-30:t-8].mean()<5: continue
        last=t; r=a/base
        pre=int((r[t-6:t]>=1.5).sum()); tot=int((r[t-6:t+7]>=1.5).sum())
        cls='sustained' if (pre>=2 or tot>=5) else ('spike' if tot<=2 else 'mixed')
        y=np.log1p(b['lis']); kk=np.arange(-30,-8); co=np.polyfit(kk,y[t-30:t-8],1)
        resp=[y[t+k]-np.polyval(co,k) for k in range(-8,13)]
        ev.append(dict(title=b['title'],week=weeks[t].date(),ratio=r[t],cls=cls,pre=pre,resp=resp))
E=pd.DataFrame(ev); print(E.cls.value_counts().to_dict())
rng=np.random.RandomState(0); out=[]
for c in ['sustained','spike','mixed']:
    R=np.array(E[E.cls==c].resp.tolist())
    if len(R)<5: continue
    bs=np.array([R[rng.randint(0,len(R),len(R))].mean(0) for _ in range(1000)])
    for i,k in enumerate(range(-8,13)): out.append(dict(cls=c,n=len(R),k=k,pct=(np.exp(R[:,i].mean())-1)*100,lo=(np.exp(np.percentile(bs[:,i],2.5))-1)*100,hi=(np.exp(np.percentile(bs[:,i],97.5))-1)*100))
ES=pd.DataFrame(out); ES.to_csv(f'{D}/reports/weekly_event_study.csv',index=False)
print(ES[ES.k.isin([-4,-2,-1,0,1,2,4,8,12])].round(1).pivot(index='k',columns='cls',values='pct').to_string())
lift=E.assign(l=E.resp.map(lambda r:(np.exp(np.mean(r[8:13]))-1)*100)).groupby('cls').l.agg(['count','median',lambda x:(x>20).mean()]).round(2); print(lift)
# ---------- hidden-book lift model ----------
rows=[]
for b in books:
    a=b['att']; L_=b['lis']
    for t in range(30,len(weeks)-5):
        if near_launch(b,weeks[t]): continue
        base=np.median(a[t-26:t]); lb=np.median(L_[t-26:t])
        if base<=0 or lb<3: continue
        r=a[t-8:t+1]/base
        x=a[t-8:t+1]; tau=float(np.sign(x[None,:]-x[:,None])[np.triu_indices(9,1)].sum())/36   # Mann-Kendall tau over 9 weeks
        rows.append(dict(bg=b['bg'],week=weeks[t],r0=np.log(r[-1]+1e-6),r1=np.log(r[-2]+1e-6),r4=np.log(r[-4:].mean()+1e-6),rmax8=np.log(r.max()+1e-6),
            n15=int((r>=1.5).sum()),tau=tau,slope=np.polyfit(np.arange(6),np.log1p(a[t-5:t+1]),1)[0],level=np.log1p(base),cal=weeks[t].month,
            y=np.log((L_[t+1:t+5].sum()+1)/(4*lb+1))))
P=pd.DataFrame(rows); ub=P.bg.unique(); fold=dict(zip(ub,np.random.RandomState(2).randint(0,5,len(ub)))); P['f']=P.bg.map(fold)
FULL=['r0','r1','r4','rmax8','n15','tau','slope','level','cal']; NAIVE=['r0','level','cal']
for name,fs in [('naive (this week only)',NAIVE),('shape (8-week trend)',FULL)]:
    P['p_'+name]=np.nan
    for f in range(5):
        m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=100,verbose=-1,random_state=0).fit(P.loc[P.f!=f,fs],P.loc[P.f!=f,'y'])
        P.loc[P.f==f,'p_'+name]=m.predict(P.loc[P.f==f,fs])
big=(P.y>np.log(1.5)).astype(int); hot=P.r0>np.log(2)
res={}
for name in ['naive (this week only)','shape (8-week trend)']:
    p=P['p_'+name]; res[name]=dict(spearman_all=round(spearmanr(p,P.y).correlation,3),auc_lift50=round(roc_auc_score(big,p),3),
        spearman_hot_weeks=round(spearmanr(p[hot],P.y[hot]).correlation,3),auc_lift50_hot=round(roc_auc_score(big[hot],p[hot]),3))
res['rows']=len(P); res['books']=int(P.bg.nunique()); res['share_weeks_lift50']=round(big.mean(),3)
json.dump(res,open(f'{D}/reports/weekly_lift_model.json','w'),indent=1); print(json.dumps(res,indent=1))
P.to_pickle(f'{D}/interim/weekly_lift_panel.pkl'); E.to_pickle(f'{D}/interim/weekly_events.pkl')
