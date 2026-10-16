# Redo of the weekly spike vs sustained split using only weeks up to and including the peak (no post-peak weeks).
# Same data, burst rule, exclusions and listening response as weekly_analysis.py; only the class rule and the bootstrap differ.
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
from config import D
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
    books.append(dict(bg=bg,title=g.title.iloc[0],att=att_n.values,raw=att.values,lis=lis.values,rels=[r.tz_localize(None) for r in rels if pd.notna(r)]))
print('books',len(books))
def near_launch(b,w): return any(-8<=(w-r).days/7<=40 for r in b['rels'])
ev=[]
for b in books:
    a=b['att']; last=-99
    for t in range(30,len(weeks)-13):
        base=np.median(a[t-26:t])
        if base<=0 or a[t]<3*base or b['raw'][t]<2000 or a[t]<a[max(0,t-4):t+5].max() or t-last<8: continue
        if near_launch(b,weeks[t]) or b['lis'][t-30:t-8].mean()<5: continue
        last=t; r=a/base
        old_pre=int((r[t-6:t]>=1.5).sum()); old_tot=int((r[t-6:t+7]>=1.5).sum())
        oldc='sustained' if (old_pre>=2 or old_tot>=5) else ('spike' if old_tot<=2 else 'mixed')
        # new rule: only weeks before the peak
        if (r[t-3:t]>=1.5).all(): cls='sustained'
        elif r[t-1]<1.5: cls='spike'
        else: cls='mixed'
        y=np.log1p(b['lis']); kk=np.arange(-30,-8); co=np.polyfit(kk,y[t-30:t-8],1)
        resp=[y[t+k]-np.polyval(co,k) for k in range(-8,13)]
        ev.append(dict(bg=b['bg'],title=b['title'],week=weeks[t].date(),ratio=r[t],cls=cls,oldcls=oldc,resp=resp))
E=pd.DataFrame(ev); print('new',E.cls.value_counts().to_dict(),'old',E.oldcls.value_counts().to_dict())
print(pd.crosstab(E.oldcls,E.cls))
R=np.array(E.resp.tolist()); k0=8
peak=R[:,k0]; w04=R[:,k0:k0+5].mean(1)
def stats(idx_by_book,bk):
    # idx_by_book: list of arrays of event indices per book; bk: bootstrap book draw
    ids=np.concatenate([idx_by_book[i] for i in bk]) if len(bk) else np.array([],int)
    if len(ids)==0: return [np.nan]*4
    l=np.exp(w04[ids])-1
    return [len(ids),(np.exp(peak[ids].mean())-1)*100,np.median(l)*100,(l>0.2).mean()*100]
rng=np.random.RandomState(0); rows=[]; curves=[]
def run(name,mask,label):
    sub=np.where(mask)[0]; bgs=E.bg.values[sub]; ub=np.unique(bgs)
    groups=[sub[bgs==u] for u in ub]
    pt=stats(groups,range(len(groups)))
    bs=np.array([stats(groups,rng.randint(0,len(groups),len(groups))) for _ in range(2000)])
    r=dict(set=label,cls=name,events=len(sub),books=len(ub))
    for j,m in enumerate(['peak_week_lift_pct','median_wk0to4_lift_pct','share_above_20pct']):
        r[m]=pt[j+1]; r[m+'_lo']=np.nanpercentile(bs[:,j+1],2.5); r[m+'_hi']=np.nanpercentile(bs[:,j+1],97.5)
    rows.append(r)
for col,label in [('cls','new rule (weeks up to peak)'),('oldcls','old rule (reproduced)')]:
    for c in ['sustained','spike','mixed']: run(c,(E[col]==c).values,label)
res=pd.DataFrame(rows); res.to_csv(f'{D}/reports/librivox_bursts_redo_weekly.csv',index=False)
E.drop(columns='resp').to_csv(f'{D}/reports/librivox_bursts_redo_weekly_events.csv',index=False)
# mean response curves by new class
cur=[]
for c in ['sustained','spike','mixed']:
    m=(E.cls==c).values
    for i,k in enumerate(range(-8,13)): cur.append(dict(cls=c,k=k,pct=(np.exp(R[m,i].mean())-1)*100))
pd.DataFrame(cur).to_csv(f'{D}/reports/librivox_bursts_redo_weekly_curves.csv',index=False)
print(res.round(1).to_string())
