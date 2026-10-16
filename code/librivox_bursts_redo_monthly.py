# Redo of the monthly burst event study: pre-trend fitted OUT of sample on months -18 to -7, so months -6 to -1 show any pre-trend;
# bootstrap clustered by book (2,000 resamples). Same data, burst rule and exclusions as study2b.py.
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
from config import D
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); PV=json.load(open(f'{D}/raw/wiki_pageviews_monthly.json'))
T={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly_to2026.json'))['items']}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); L=pd.read_parquet(f'{D}/processed/labels.parquet')
lk=lk.merge(L[['identifier','genre1']],on='identifier',how='left')
lm=[p.strftime('%Y%m') for p in pd.period_range('2017-01','2026-08',freq='M')]
am=[p.strftime('%Y%m') for p in pd.period_range('2015-07','2025-06',freq='M')]
books=[]
for bg,g in lk[lk.n_authors==1].groupby('bookgroup'):
    art=g.wiki_book.dropna().iloc[0] if g.wiki_book.notna().any() else None; src='book'
    if not art or art.replace(' ','_') not in PV: art=g.wiki_author.dropna().iloc[0] if g.wiki_author.notna().any() else None; src='author'
    if not art or art.replace(' ','_') not in PV or not PV[art.replace(' ','_')]: continue
    s=PV[art.replace(' ','_')]; a=np.array([s.get(k,0)/T[k]*1e6 for k in am])
    lis=np.array([sum(V.get(i,{}).get(k,0) for i in g.identifier) for k in lm],float)
    books.append(dict(bg=bg,title=g.title.iloc[0],src=src,art=art,att=a,lis=lis,rels=list(g.publicdate.dropna())))
PVraw=lambda art,ym: PV[art.replace(' ','_')].get(ym,0)
ev=[]
for b in books:
    a=b['att']
    for t in range(12,len(am)):
        base=np.median(a[t-12:t])
        if base>0 and a[t]>=2.5*base and a[t]==a[max(0,t-2):t+3].max():
            ym=am[t]; j=lm.index(ym) if ym in lm else None
            if j is None or j<6 or j+6>=len(lm): continue
            win=pd.Period(ym,'M')
            if any(abs((pd.Period(r.strftime('%Y-%m'),'M')-win).n)<=8 for r in b['rels']): continue
            if j<12 or b['lis'][j-12:j-1].mean()<20: continue
            y=np.log1p(b['lis'])
            old=np.polyfit(np.arange(-12,-1),y[j-12:j-1],1)
            r_old=[y[j+k]-np.polyval(old,k) for k in range(-6,7)]
            r_new=None
            if j>=18:
                co=np.polyfit(np.arange(-18,-6),y[j-18:j-6],1)   # months -18..-7 only
                r_new=[y[j+k]-np.polyval(co,k) for k in range(-6,7)]
            ev.append(dict(bg=b['bg'],title=b['title'],src=b['src'],month=ym,ratio=a[t]/base,raw=PVraw(b['art'],ym),old=r_old,new=r_new))
E=pd.DataFrame(ev); print('bursts (old rule set)',len(E),'books',E.bg.nunique())
Ek=E[E.new.notna()].reset_index(drop=True); print('bursts with 18 months of history',len(Ek),'books',Ek.bg.nunique())
Rn=np.array(Ek.new.tolist()); Ro=np.array(Ek.old.tolist()); Roall=np.array(E.old.tolist())
ks=np.arange(-6,7)
def cl(R,df,mask,B=2000,seed=0):
    # cluster bootstrap by book; stat = event-weighted mean of log response, then converted to percent
    sub=np.where(mask)[0]; bgs=df.bg.values[sub]; ub,inv=np.unique(bgs,return_inverse=True)
    S=np.zeros((len(ub),R.shape[1])); n=np.zeros(len(ub))
    np.add.at(S,inv,R[sub]); np.add.at(n,inv,1)
    rng=np.random.RandomState(seed); curve=lambda s,c:(np.exp(s/c)-1)*100
    pt=curve(S.sum(0),n.sum()); bs=np.empty((B,R.shape[1]))
    for i in range(B):
        d=rng.randint(0,len(ub),len(ub)); bs[i]=S[d].sum(0)/n[d].sum()
    bs=(np.exp(bs)-1)*100
    return pt,bs,len(sub),len(ub)
def summ(R,df,mask,label,rows,curves):
    pt,bs,ne,nb=cl(R,df,mask)
    m02=(ks>=0)&(ks<=2); pre=(ks>=-6)&(ks<=-1)
    # window means taken in log space then converted
    sub=np.where(mask)[0]; bgs=df.bg.values[sub]; ub,inv=np.unique(bgs,return_inverse=True)
    S=np.zeros((len(ub),R.shape[1])); n=np.zeros(len(ub)); np.add.at(S,inv,R[sub]); np.add.at(n,inv,1)
    rng=np.random.RandomState(1); res={}
    for nm,msk in [('lift_m0_2',m02),('pre_gap_m-6_-1',pre)]:
        pv=lambda s,c:(np.exp((s[:,msk].mean(1) if s.ndim>1 else s[msk].mean())/c)-1)*100
        est=(np.exp(S.sum(0)[msk].mean()/n.sum())-1)*100
        b=[]
        for _ in range(2000):
            d=rng.randint(0,len(ub),len(ub)); b.append((np.exp(S[d].sum(0)[msk].mean()/n[d].sum())-1)*100)
        res[nm]=(est,np.percentile(b,2.5),np.percentile(b,97.5))
    rows.append(dict(set=label,events=ne,books=nb,**{f'{k}_{s}':v for k,t in res.items() for k,s,v in zip([k]*3,['est','lo','hi'],t)}))
    for i,k in enumerate(ks): curves.append(dict(set=label,k=k,pct=pt[i],lo=np.percentile(bs[:,i],2.5),hi=np.percentile(bs[:,i],97.5),events=ne))
rows=[];curves=[]
strongk=((Ek.src=='book')&(Ek.ratio>=3)&(Ek.raw>=20000)).values
strongall=((E.src=='book')&(E.ratio>=3)&(E.raw>=20000)).values
print('strong bursts: all',strongall.sum(),'with 18m history',strongk.sum())
summ(Rn,Ek,np.ones(len(Ek),bool),'all bursts, NEW out-of-sample trend',rows,curves)
summ(Rn,Ek,strongk,'strongest bursts, NEW out-of-sample trend',rows,curves)
summ(Ro,Ek,np.ones(len(Ek),bool),'all bursts, OLD in-sample trend (same events, clustered)',rows,curves)
summ(Ro,Ek,strongk,'strongest bursts, OLD in-sample trend (same events, clustered)',rows,curves)
summ(Roall,E,np.ones(len(E),bool),'all bursts, OLD in-sample trend (full old set, clustered)',rows,curves)
summ(Roall,E,strongall,'strongest bursts, OLD in-sample trend (full old set, clustered)',rows,curves)
res=pd.DataFrame(rows); res.to_csv(f'{D}/reports/librivox_bursts_redo_monthly.csv',index=False)
pd.DataFrame(curves).to_csv(f'{D}/reports/librivox_bursts_redo_monthly_curves.csv',index=False)
Ek.to_pickle(f'{D}/interim/librivox_bursts_redo_monthly_events.pkl')
Ek.drop(columns=['old','new']).to_csv(f'{D}/reports/librivox_bursts_redo_monthly_events.csv',index=False)
pd.set_option('display.width',250); print(res.round(1).to_string())
