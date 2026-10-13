# Theme radar: what society is paying attention to (Wikipedia's monthly top 1,000 articles), matched by meaning to books,
# scored only from information available at month t, and tested against each book's listening in months t+1 to t+3.
import pandas as pd, numpy as np, json, os, time, requests, urllib.parse, collections
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from config import D, UA; H={"User-Agent":UA}
while True:
    try:
        if 'months' in open(f'{D}/reports/top_articles.log').read(): break
    except Exception: pass
    time.sleep(20)
T=json.load(open(f'{D}/raw/wiki_top_monthly.json'))
SKIP=('Main_Page','Special:','Wikipedia:','File:','Portal:','Help:','Template:','Category:','Talk:','User:','.xxx','XXX')
arts=sorted({a for m in T.values() for a,v in m if not a.startswith(SKIP) and a not in ('-','Undefined')})
print('articles',len(arts),flush=True)
# 1. short descriptions, 50 titles per call
fd=f'{D}/raw/wiki_top_descriptions.json'; desc=json.load(open(fd)) if os.path.exists(fd) else {}
todo=[a for a in arts if a not in desc]
for i in range(0,len(todo),50):
    chunk=todo[i:i+50]
    for k in range(5):
        try:
            r=requests.get("https://en.wikipedia.org/w/api.php",params=dict(action='query',prop='description',titles='|'.join(urllib.parse.unquote(c).replace('_',' ') for c in chunk),format='json',redirects=1),headers=H,timeout=30)
            if r.status_code==200:
                j=r.json()['query']; nm={x['to']:x['from'] for x in j.get('redirects',[])}; nm.update({x['to']:x['from'] for x in j.get('normalized',[])})
                got={}
                for p in j['pages'].values():
                    t=p.get('title',''); t0=nm.get(t,t); t0=nm.get(t0,t0); got[t0.replace(' ','_')]=p.get('description','')
                for c in chunk: desc[c]=got.get(urllib.parse.unquote(c),got.get(c,''))
                break
            time.sleep(int(r.headers.get('retry-after',5))+1)
        except Exception: time.sleep(5)
    if i%2000==0: json.dump(desc,open(fd,'w')); print('desc',i,flush=True)
    time.sleep(1.0)
json.dump(desc,open(fd,'w'))
# 2. embed "Title: description"
from fastembed import TextEmbedding
fe=f'{D}/interim/top_article_emb.npy'
if os.path.exists(fe) and len(np.load(fe))==len(arts): AE=np.load(fe)
else:
    m=TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    txt=[urllib.parse.unquote(a).replace('_',' ')+(': '+desc.get(a,'') if desc.get(a) else '') for a in arts]
    AE=np.array(list(m.embed(txt,batch_size=128))); AE/=np.linalg.norm(AE,axis=1,keepdims=True); np.save(fe,AE)
print('embedded',AE.shape,flush=True)
# 3. article momentum per month (share of top-1000 views, vs its own median share over the previous 12 months)
months=pd.period_range('2016-01','2026-09',freq='M'); ai={a:i for i,a in enumerate(arts)}
S=np.zeros((len(months),len(arts))); floor=np.zeros(len(months))
for mi,p in enumerate(months):
    lst=[(a,v) for a,v in T.get(p.strftime('%Y%m'),[]) if a in ai]
    if not lst: continue
    tot=sum(v for a,v in lst); floor[mi]=0.5*min(v for a,v in lst)/tot
    for a,v in lst: S[mi,ai[a]]=v/tot
Sf=np.where(S>0,S,floor[:,None])
MOM=np.zeros_like(S)
for mi in range(12,len(months)):
    base=np.median(Sf[mi-12:mi],axis=0); MOM[mi]=np.where(S[mi]>0,np.log(Sf[mi]/base),0)
RISE=np.clip(MOM,0,None)*(MOM>np.log(2))
# 4. books, similarity, listening
B=json.load(open(f'{D}/interim/book_themes.json')); books=B['books']; BE=np.load(f'{D}/interim/book_emb_by_group.npy')
SIM=BE@AE.T; tau=np.quantile(SIM,0.999); print('similarity threshold (top 0.1% of pairs):',round(float(tau),3),flush=True)
W=np.clip(SIM-tau,0,None)
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]; V=json.load(open(f'{D}/raw/ia_views_monthly.json'))
lm=pd.period_range('2017-01','2026-08',freq='M')
g=lk.groupby('bookgroup'); idmap={str(k):v.identifier.tolist() for k,v in g}; rels={str(k):[r.tz_localize(None).to_period('M') for r in v.publicdate.dropna()] for k,v in g}
L=np.log1p(np.array([[sum(V.get(i,{}).get(p.strftime('%Y%m'),0) for i in idmap[b]) for p in lm] for b in books]))
MK=np.median(L,axis=0)
SCORE=(W@RISE.T)                                   # books x months (on the attention month grid)
mpos={p:i for i,p in enumerate(months)}; lpos={p:i for i,p in enumerate(lm)}
rows=[]
for p in pd.period_range('2018-01','2026-05',freq='M'):
    j=lpos[p]; s=SCORE[:,mpos[p]]
    base=np.median(L[:,j-12:j],axis=1); post=L[:,j+1:j+4].mean(1); y=(post-base)-(MK[j+1:j+4].mean()-np.median(MK[j-12:j]))
    ok=(np.expm1(base)>=5)&np.array([not any(-8<=(p-r).n<=3 for r in rels[b]) for b in books])
    rows.append(pd.DataFrame(dict(month=str(p),book=np.array(books)[ok],score=s[ok],y=y[ok])))
R=pd.concat(rows); R.to_parquet(f'{D}/processed/theme_radar_panel.parquet')
def evaluate(R,col):
    res=[]
    for m,gm in R.groupby('month'):
        hot=gm[col]>0
        if hot.sum()<10: continue
        top=(gm.y>=gm.y.quantile(0.95)).astype(int)
        res.append(dict(month=m,n_hot=int(hot.sum()),lift_hot=float(np.exp(gm.y[hot].mean()-gm.y[~hot].mean())),auc=roc_auc_score(top,gm[col]) if top.nunique()>1 else np.nan,
                        sp_hot=spearmanr(gm[col][hot],gm.y[hot]).correlation))
    return pd.DataFrame(res)
E=evaluate(R,'score')
# placebo: each month scored with the radar from a random other month (12 to 48 months away)
rng=np.random.RandomState(0); Rp=R.copy()
for m in Rp.month.unique():
    p=pd.Period(m,'M'); q=p+int(rng.choice([-1,1]))*int(rng.randint(12,48))
    if q not in mpos: q=p-int(rng.randint(12,24))
    sc=pd.Series(SCORE[:,mpos[q]],index=books); Rp.loc[Rp.month==m,'score']=Rp.loc[Rp.month==m,'book'].map(sc).values
Ep=evaluate(Rp,'score')
summ=dict(months=len(E),books_flagged_per_month=float(E.n_hot.median()),
          real=dict(listening_lift_flagged_vs_others=round(float(np.exp(np.log(E.lift_hot).mean())),3),auc_top5pct=round(float(E.auc.mean()),3),share_months_lift_above_1=round(float((E.lift_hot>1).mean()),2)),
          placebo=dict(listening_lift_flagged_vs_others=round(float(np.exp(np.log(Ep.lift_hot).mean())),3),auc_top5pct=round(float(Ep.auc.mean()),3),share_months_lift_above_1=round(float((Ep.lift_hot>1).mean()),2)))
print(json.dumps(summ,indent=1),flush=True); json.dump(summ,open(f'{D}/reports/theme_radar_summary.json','w'),indent=1); E.to_csv(f'{D}/reports/theme_radar_by_month.csv',index=False)
# 5. explain the strongest months: which rising topics drove which books
title=g.title.first(); expl=[]
for m in E.sort_values('lift_hot',ascending=False).month.head(6):
    mi=mpos[pd.Period(m,'M')]; s=SCORE[:,mi]; topb=np.argsort(-s)[:5]
    for bi in topb:
        contrib=W[bi]*RISE[mi]; ta=np.argsort(-contrib)[:3]
        yy=R[(R.month==m)&(R.book==books[bi])].y
        expl.append(dict(month=m,book=title[int(books[bi])] if books[bi].isdigit() and int(books[bi]) in title.index else title.get(books[bi],books[bi]),
                         driven_by=[urllib.parse.unquote(arts[k]) for k in ta if contrib[k]>0],listening_change=round(float(np.exp(yy.iloc[0])),2) if len(yy) else None))
json.dump(expl,open(f'{D}/reports/theme_radar_examples.json','w'),indent=1,ensure_ascii=False)
for e in expl: print(e,flush=True)
print('ALLDONE',flush=True)
