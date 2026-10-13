# Evaluate theme-based scores from the database: any-theme, overlap (narrowing) and parent-child narrowing,
# plus a table model (LightGBM) trained walk-forward by year. Placebo: scores taken from a different month.
import pandas as pd, numpy as np, json
from sklearn.metrics import roc_auc_score
import lightgbm as lgb
from config import D; O=f'{D}/db'
th=pd.read_parquet(f'{O}/themes.parquet'); bt=pd.read_parquet(f'{O}/book_theme.parquet'); ta=pd.read_parquet(f'{O}/theme_activity.parquet')
L=pd.read_parquet(f'{O}/listening.parquet'); lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
books=sorted(L.book_id.unique()); tids=list(th.theme_id); tix={t:i for i,t in enumerate(tids)}; bix={b:i for i,b in enumerate(books)}
Wb=np.zeros((len(books),len(tids)))
for r in bt.itertuples():
    if r.book_id in bix: Wb[bix[r.book_id],tix[r.theme_id]]=r.weight
lvl2=(th.level==2).values; parent=th.parent.map(tix).values
per=sorted(ta.period.unique()); pix={p:i for i,p in enumerate(per)}
MOM=np.zeros((len(per),len(tids))); RIS=np.zeros_like(MOM); SUS=np.zeros_like(MOM)
for r in ta.itertuples():
    i,j=pix[r.period],tix[r.theme_id]; MOM[i,j]=r.momentum if np.isfinite(r.momentum) else 0; RIS[i,j]=r.rising; SUS[i,j]=r.pattern=='sustained'
M=np.clip(MOM,0,None)*RIS
Lw=L.pivot(index='book_id',columns='period',values='listens').reindex(books); lper=list(Lw.columns); LL=np.log1p(Lw.values); MK=np.median(LL,axis=0)
rels={str(k):[x.tz_localize(None).to_period('M') for x in v.publicdate.dropna()] for k,v in lk.groupby('bookgroup')}
def scores(pi):
    m=M[pi]; any_=Wb@m
    m2=np.where(lvl2,m,0); sq=np.sqrt(m2)
    # overlap: sum over pairs of rising level-2 themes of min(weight_i, weight_j) * sqrt(m_i * m_j)
    act=np.where(m2>0)[0]; ov=np.zeros(len(books))
    for a in range(len(act)):
        for b in range(a+1,len(act)):
            i,j=act[a],act[b]; ov+=np.minimum(Wb[:,i],Wb[:,j])*sq[i]*sq[j]
    # parent-child narrowing: a child theme counts only when its parent theme is also rising
    pm=np.array([m[p] if lvl2[k] and p==p and not np.isnan(p) else 0 for k,p in enumerate(parent)]) if False else np.array([m[int(p)] if lvl2[k] and not pd.isna(p) else 0 for k,p in enumerate(parent)])
    nar=Wb@(m2*np.sqrt(pm))
    return any_,ov,nar,(Wb>0)@(m>0),Wb@(SUS[pi]*m)
rows=[]
for p in pd.period_range('2018-01','2026-05',freq='M'):
    ps=str(p); j=lper.index(ps); pi=pix[ps]
    base=np.median(LL[:,j-12:j],axis=1); y=(LL[:,j+1:j+4].mean(1)-base)-(MK[j+1:j+4].mean()-np.median(MK[j-12:j]))
    ok=(np.expm1(base)>=5)&np.array([not any(-8<=(p-r).n<=3 for r in rels.get(b,[])) for b in books])
    a,o,n,cnt,sus=scores(pi)
    rows.append(pd.DataFrame(dict(month=ps,book=np.array(books)[ok],any_theme=a[ok],overlap=o[ok],narrow=n[ok],n_rising=cnt[ok],sustained=sus[ok],y=y[ok])))
R=pd.concat(rows); R.to_parquet(f'{O}/eval_panel.parquet')
def ev(R,col):
    out=[]
    for m,gm in R.groupby('month'):
        top=(gm.y>=gm.y.quantile(0.95)).astype(int); hot=gm[col]>gm[col].quantile(0.95)
        out.append(dict(auc=roc_auc_score(top,gm[col]) if gm[col].std()>0 else 0.5,lift=np.exp(gm.y[hot].mean()-gm.y[~hot].mean())))
    E=pd.DataFrame(out); return round(E.auc.mean(),3),round(float(np.exp(np.log(E.lift).mean())),3),round(float((E.lift>1).mean()),2)
rng=np.random.RandomState(0); Rp=R.copy(); mons=sorted(R.month.unique())
shift={m:mons[(i+rng.randint(12,36))%len(mons)] for i,m in enumerate(mons)}
for col in ['any_theme','overlap','narrow','sustained']:
    s=R.set_index(['month','book'])[col]; Rp[col]=[s.get((shift[m],b),0) for m,b in zip(R.month,R.book)]
res={}
for col in ['any_theme','overlap','narrow','sustained']:
    res[col]=dict(real=ev(R,col),placebo=ev(Rp,col))
print('metric: (mean AUC for top-5% risers, listening lift of top-5% scored books vs others, share of months lift>1)')
print(json.dumps(res,indent=1))
# table model, trained walk-forward by year on theme features (+ month calendar), scored on next year
F=['any_theme','overlap','narrow','n_rising','sustained']; R['yr']=R.month.str[:4].astype(int); R['top']=0
for m,gm in R.groupby('month'): R.loc[gm.index[gm.y>=gm.y.quantile(0.95)] if False else gm.index,'top']=(gm.y>=gm.y.quantile(0.95)).astype(int).values
R=R.reset_index(drop=True); R['top']=R.groupby('month').y.transform(lambda s:(s>=s.quantile(0.95)).astype(int))
aucs=[]
for yr in range(2020,2027):
    tr=R[(R.yr<yr)&(R.month<f'{yr-1}-10')]; te=R[R.yr==yr]
    if len(te)==0: continue
    mdl=lgb.LGBMClassifier(n_estimators=300,learning_rate=0.05,num_leaves=15,min_child_samples=200,verbose=-1).fit(tr[F],tr.top)
    p=mdl.predict_proba(te[F])[:,1]; te=te.assign(p=p)
    aucs+= [roc_auc_score(gm.top,gm.p) for m,gm in te.groupby('month') if gm.top.nunique()>1]
res['lightgbm_table']=round(float(np.mean(aucs)),3); print('LightGBM table model, walk-forward by year, mean monthly AUC:',res['lightgbm_table'])
json.dump(res,open(f'{D}/reports/db_eval.json','w'),indent=1)
