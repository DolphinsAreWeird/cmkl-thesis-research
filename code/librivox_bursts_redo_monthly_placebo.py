# Placebo check for the out-of-sample monthly event study: same trend fit (months -18..-7), same book filters,
# but centred on non-burst months of the same books. Shows how much of the gap is a bias of the method (selection on level + extrapolation).
# Each book's placebo months are averaged and weighted by that book's number of real bursts; bootstrap clustered by book.
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
from config import D
exec(open('librivox_bursts_redo_monthly.py').read().split("PVraw=")[0].split("from config import D")[1])
bursts=pd.read_csv(f'{D}/reports/librivox_bursts_redo_monthly_events.csv',dtype={'month':str})
ks=np.arange(-6,7); ev_bg=set(bursts.bg)
# all burst candidate months per book (old rule set incl. those dropped for history), to keep placebo months away from any burst
allb={}
for b in books:
    a=b['att']
    for t in range(12,len(am)):
        base=np.median(a[t-12:t])
        if base>0 and a[t]>=2.5*base and a[t]==a[max(0,t-2):t+3].max() and am[t] in lm: allb.setdefault(b['bg'],[]).append(lm.index(am[t]))
nb={bg:len(g) for bg,g in bursts.groupby('bg')}; strong=set(bursts[(bursts.src=='book')&(bursts.ratio>=3)&(bursts.raw>=20000)].bg)
S={};N={}
for b in books:
    if b['bg'] not in nb: continue
    y=np.log1p(b['lis']); rs=[]
    for j in range(18,len(lm)-6):
        if any(abs(j-x)<=8 for x in allb.get(b['bg'],[])): continue
        if any(abs((pd.Period(lm[j][:4]+'-'+lm[j][4:],'M')-pd.Period(r.strftime('%Y-%m'),'M')).n)<=8 for r in b['rels']): continue
        if b['lis'][j-12:j-1].mean()<20: continue
        co=np.polyfit(np.arange(-18,-6),y[j-18:j-6],1); rs.append([y[j+k]-np.polyval(co,k) for k in ks])
    if rs: S[b['bg']]=np.mean(rs,0); N[b['bg']]=len(rs)
print('books with placebo months',len(S),'of',len(nb))
Ek=pd.read_pickle(f'{D}/interim/librivox_bursts_redo_monthly_events.pkl')
Rb=np.array(Ek.new.tolist()); bgs=Ek.bg.values
use=np.array([bg in S for bg in bgs]); 
def run(mask,label):
    m=mask&use; ub=np.unique(bgs[m]); sb=np.array([Rb[m&(bgs==u)].sum(0) for u in ub]); n=np.array([ (m&(bgs==u)).sum() for u in ub])
    sp=np.array([S[u]*n_ for u,n_ in zip(ub,n)])
    w02=(ks>=0)&(ks<=2); pre=ks<0
    def est(d):
        out=[]
        for msk in (w02,pre):
            out.append((np.exp(sb[d].sum(0)[msk].mean()/n[d].sum())-1)*100); out.append((np.exp(sp[d].sum(0)[msk].mean()/n[d].sum())-1)*100)
            out.append(((np.exp((sb[d].sum(0)-sp[d].sum(0))[msk].mean()/n[d].sum()))-1)*100)
        return out
    allk=np.arange(len(ub)); pt=est(allk); rng=np.random.RandomState(3); bs=np.array([est(rng.randint(0,len(ub),len(ub))) for _ in range(2000)])
    names=['m0_2_burst','m0_2_placebo','m0_2_burst_minus_placebo','pre_burst','pre_placebo','pre_burst_minus_placebo']
    r=dict(set=label,events=int(n.sum()),books=len(ub))
    for i,nm in enumerate(names): r[nm]=pt[i]; r[nm+'_lo']=np.percentile(bs[:,i],2.5); r[nm+'_hi']=np.percentile(bs[:,i],97.5)
    return r
res=pd.DataFrame([run(np.ones(len(Ek),bool),'all bursts'),run(((Ek.src=='book')&(Ek.ratio>=3)&(Ek.raw>=20000)).values,'strongest bursts')])
res.to_csv(f'{D}/reports/librivox_bursts_redo_monthly_placebo.csv',index=False); pd.set_option('display.width',250); print(res.round(1).T.to_string())
