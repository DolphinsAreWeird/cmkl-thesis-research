# Redo of the LibriVox weekly hidden-book model with (1) an own-recent-listening baseline and (2) a time-blocked split.
# Leaves old code untouched. Panel and label are rebuilt exactly as in weekly_analysis.py (same filters, same attention features).
# Label: listening over the next 4 weeks >= 1.5x the book's own 26-week median. Hot = attention this week >= 2x its 26-week median.
import pandas as pd, numpy as np, json, warnings, sys
warnings.filterwarnings('ignore')
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
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
    books.append(dict(bg=bg,att=att_n.values,lis=lis.values,rels=[r.tz_localize(None) for r in rels if pd.notna(r)]))
print('books',len(books),flush=True)
def near_launch(b,w): return any(-8<=(w-r).days/7<=40 for r in b['rels'])
rows=[]
for b in books:
    a=b['att']; L_=b['lis']
    for t in range(30,len(weeks)-5):
        if near_launch(b,weeks[t]): continue
        base=np.median(a[t-26:t]); lb=np.median(L_[t-26:t])
        if base<=0 or lb<3: continue
        r=a[t-8:t+1]/base
        x=a[t-8:t+1]; tau=float(np.sign(x[None,:]-x[:,None])[np.triu_indices(9,1)].sum())/36
        # own recent listening, known at week t (this week included), never beyond t
        o0=np.log((L_[t]+1)/(lb+1)); o1=np.log((L_[t-1]+1)/(lb+1)); o4=np.log((L_[t-3:t+1].mean()+1)/(lb+1)); o8=np.log((L_[t-7:t+1].mean()+1)/(lb+1))
        rows.append(dict(bg=b['bg'],week=weeks[t],r0=np.log(r[-1]+1e-6),r1=np.log(r[-2]+1e-6),r4=np.log(r[-4:].mean()+1e-6),rmax8=np.log(r.max()+1e-6),
            n15=int((r>=1.5).sum()),tau=tau,slope=np.polyfit(np.arange(6),np.log1p(a[t-5:t+1]),1)[0],level=np.log1p(base),cal=weeks[t].month,
            o0=o0,o1=o1,o4=o4,o8=o8,olevel=np.log1p(lb),
            y=np.log((L_[t+1:t+5].sum()+1)/(4*lb+1))))
P=pd.DataFrame(rows); print('rows',len(P),'books',P.bg.nunique(),flush=True)
ub=P.bg.unique(); fold=dict(zip(ub,np.random.RandomState(2).randint(0,5,len(ub)))); P['f']=P.bg.map(fold)   # same folds as old code
P['big']=(P.y>np.log(1.5)).astype(int); P['hot']=(P.r0>np.log(2)); P['year']=P.week.dt.year
ATT=['r0','r1','r4','rmax8','n15','tau','slope','level','cal']
OWN=['o0','o1','o4','o8','olevel','cal']
MODELS={'attention only':ATT,'own listening only':OWN,'both':ATT+[c for c in OWN if c!='cal']}
def fit(tr,fs): return lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=100,verbose=-1,random_state=0,n_jobs=2).fit(P.loc[tr,fs],P.loc[tr,'y'])
# split A: book split (as old)
for n,fs in MODELS.items():
    P['A_'+n]=np.nan
    for f in range(5):
        m=fit(P.f!=f,fs); P.loc[P.f==f,'A_'+n]=m.predict(P.loc[P.f==f,fs])
# split B: walk-forward by year 2020..2026, train weeks before the year start minus a 4-week gap (label looks 4 weeks ahead), books held out too
GAP=pd.Timedelta(weeks=5)
for n in MODELS: P['B_'+n]=np.nan
for Y in range(2020,2027):
    start=pd.Timestamp(f'{Y}-01-01'); te_t=(P.year==Y)
    for f in range(5):
        tr=(P.f!=f)&(P.week<start-GAP); te=te_t&(P.f==f)
        if te.sum()==0: continue
        for n,fs in MODELS.items():
            m=fit(tr,fs); P.loc[te,'B_'+n]=m.predict(P.loc[te,fs])
    print('year',Y,flush=True)
# simple rule baseline (no fitting): own 4-week ratio, own 1-week ratio
P['A_rule: own 4-week ratio']=P.o4; P['B_rule: own 4-week ratio']=P.o4
def auc(d,col):
    return roc_auc_score(d.big,d[col]) if d.big.nunique()==2 else np.nan
names=list(MODELS)+['rule: own 4-week ratio']
rows=[]
for sp,sub0 in [('A book split (5 folds)',P),('B walk-forward 2020-2026 (time + books held out)',P[P.year>=2020])]:
    pre=sp[0]
    for n in names:
        for sc,d in [('all weeks',sub0),('attention >= 2x',sub0[sub0.hot])]:
            rows.append(dict(split=sp,model=n,subset=sc,rows=len(d),base_rate=round(d.big.mean(),3),auc=round(auc(d,f'{pre}_{n}'),3)))
R=pd.DataFrame(rows); R.to_csv(f'{D}/reports/hidden_book_redo_auc.csv',index=False); print(R.to_string())
# per-year walk-forward
yr=[]
for Y in range(2020,2027):
    d=P[P.year==Y]
    for n in names:
        for sc,dd in [('all weeks',d),('attention >= 2x',d[d.hot])]:
            yr.append(dict(year=Y,model=n,subset=sc,rows=len(dd),base_rate=round(dd.big.mean(),3),auc=round(auc(dd,f'B_{n}'),3)))
pd.DataFrame(yr).to_csv(f'{D}/reports/hidden_book_redo_by_year.csv',index=False)
# book-cluster bootstrap: gain of 'both' over 'own listening only' and over 'attention only'
rng=np.random.RandomState(0); idx=P.groupby('bg').indices; keys=list(idx); bt=[]
for sp,pre,mask in [('A book split','A',np.ones(len(P),bool)),('B walk-forward','B',(P.year>=2020).values)]:
    for sc in ['all weeks','attention >= 2x']:
        m=mask&(P.hot.values if sc!='all weeks' else True)
        pos=[np.intersect1d(idx[k],np.where(m)[0]) for k in keys]
        y=P.big.values; pb=P['%s_both'%pre].values; po=P['%s_own listening only'%pre].values; pa=P['%s_attention only'%pre].values
        def stat(sel):
            ii=np.concatenate([pos[i] for i in sel]); return roc_auc_score(y[ii],pb[ii])-roc_auc_score(y[ii],po[ii]),roc_auc_score(y[ii],pb[ii])-roc_auc_score(y[ii],pa[ii])
        pt=stat(range(len(keys))); bs=np.array([stat(rng.randint(0,len(keys),len(keys))) for _ in range(200)])
        for j,lbl in enumerate(['both minus own listening only (what attention adds)','both minus attention only (what own listening adds)']):
            bt.append(dict(split=sp,subset=sc,contrast=lbl,diff=round(pt[j],4),lo=round(np.percentile(bs[:,j],2.5),4),hi=round(np.percentile(bs[:,j],97.5),4)))
        print(bt[-2:],flush=True)
pd.DataFrame(bt).to_csv(f'{D}/reports/hidden_book_redo_attention_gain.csv',index=False)
P[['bg','week','y','big','hot','A_attention only','A_own listening only','A_both','B_attention only','B_own listening only','B_both']].to_pickle(f'{D}/interim/hidden_book_redo_preds.pkl')
