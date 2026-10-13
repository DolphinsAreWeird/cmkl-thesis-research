# Theme Attention Database (TAD): standardized, theme-organized, time-safe tables in Parquet.
#   items, observations, themes, item_theme, book_theme, theme_activity, listening
import pandas as pd, numpy as np, json, urllib.parse, re
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from config import D; O=f'{D}/db'
T=json.load(open(f'{D}/raw/wiki_top_monthly.json')); desc=json.load(open(f'{D}/raw/wiki_top_descriptions.json'))
AE=np.load(f'{D}/interim/top_article_emb.npy')
SKIP=('Main_Page','Special:','Wikipedia:','File:','Portal:','Help:','Template:','Category:','Talk:','User:','.xxx','XXX')
arts=sorted({a for m in T.values() for a,v in m if not a.startswith(SKIP) and a not in ('-','Undefined')})
# ---- items
items=pd.DataFrame(dict(item_id=['wiki:'+a for a in arts],source='wikipedia_top',
    text=[urllib.parse.unquote(a).replace('_',' ')+(': '+desc.get(a,'') if desc.get(a) else '') for a in arts]))
B=json.load(open(f'{D}/interim/book_themes.json')); books=B['books']; BE=np.load(f'{D}/interim/book_emb_by_group.npy')
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]; g=lk.groupby('bookgroup')
btitle=g.title.first(); btitle.index=btitle.index.astype(str)
# ---- observations (standardized): share of the source's total that period, ratio to the item's own 12-period median, known-at = period end
rows=[]
for k,lst in T.items():
    lst=[(a,v) for a,v in lst if not a.startswith(SKIP)]; tot=sum(v for a,v in lst); p=pd.Period(f'{k[:4]}-{k[4:]}','M')
    for a,v in lst: rows.append(('wiki:'+a,str(p),v,v/tot,p.end_time.normalize()+pd.Timedelta(days=1)))
obs=pd.DataFrame(rows,columns=['item_id','period','value','share','known_at']); obs['source']='wikipedia_top'
# ---- themes: two-level hierarchy discovered from items and books together, labelled from member words
X=np.vstack([AE,BE]); lab_txt=list(items.text)+list(btitle.reindex(books).fillna(''))
k1=KMeans(24,n_init=6,random_state=0).fit(X); th=[]; parent=k1.labels_; sub=np.zeros(len(X),int)-1; tid=0
tf=TfidfVectorizer(stop_words='english',token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',min_df=2,max_features=30000).fit(lab_txt); Xt=tf.transform(lab_txt); voc=np.array(tf.get_feature_names_out())
def label(idx): w=np.asarray(Xt[idx].mean(0)).ravel(); return ', '.join(voc[np.argsort(-w)[:4]])
cents=[]
for p in range(24):
    idx=np.where(parent==p)[0]; c=X[idx].mean(0); c/=np.linalg.norm(c)
    th.append(dict(theme_id=f'T{p}',level=1,parent=None,label=label(idx),n_items=int((idx<len(AE)).sum()),n_books=int((idx>=len(AE)).sum()))); cents.append(c)
    kk=min(6,max(2,len(idx)//400)); k2=KMeans(kk,n_init=4,random_state=0).fit(X[idx])
    for s in range(kk):
        sidx=idx[k2.labels_==s]; c2=X[sidx].mean(0); c2/=np.linalg.norm(c2)
        th.append(dict(theme_id=f'T{p}.{s}',level=2,parent=f'T{p}',label=label(sidx),n_items=int((sidx<len(AE)).sum()),n_books=int((sidx>=len(AE)).sum()))); cents.append(c2)
themes=pd.DataFrame(th); C=np.stack(cents); np.save(f'{O}/theme_centroids.npy',C)
# ---- soft membership weights (cosine above a calibrated cut-off, then normalized per item)
def member(E):
    S=E@C.T; cut=np.quantile(S,0.97,axis=1,keepdims=True); W=np.clip(S-np.maximum(cut,0.35),0,None)
    W=W/(W.sum(1,keepdims=True)+1e-9); return W
WI=member(AE); WB=member(BE)
ii,jj=np.nonzero(WI); item_theme=pd.DataFrame(dict(item_id=items.item_id.values[ii],theme_id=themes.theme_id.values[jj],weight=WI[ii,jj]))
bi,bj=np.nonzero(WB); book_theme=pd.DataFrame(dict(book_id=np.array(books)[bi],theme_id=themes.theme_id.values[bj],weight=WB[bi,bj]))
# ---- theme activity: per theme, period and source; level = weighted share; momentum vs own 12-period median; spike vs sustained
o=obs.merge(item_theme,on='item_id'); o['w_share']=o.share*o.weight
ta=o.groupby(['theme_id','period','source']).w_share.sum().rename('level').reset_index()
ta['period_p']=pd.PeriodIndex(ta.period,freq='M'); ta=ta.sort_values(['theme_id','source','period_p'])
full=[]
for (t,s),gg in ta.groupby(['theme_id','source']):
    gg=gg.set_index('period_p').reindex(pd.period_range('2016-01','2026-09',freq='M')); gg['level']=gg.level.fillna(gg.level.min()*0.5 if gg.level.notna().any() else 0)
    lv=gg.level.values; base=pd.Series(lv).rolling(12,min_periods=6).median().shift(1).values
    mom=np.log((lv+1e-9)/(base+1e-9)); rising=mom>np.log(1.5)
    prev=pd.Series(rising).rolling(3,min_periods=1).sum().shift(1).fillna(0).values
    x=pd.Series(np.log(lv+1e-9)); tau=x.rolling(6).apply(lambda a: np.sign(a[None,:]-a[:,None])[np.triu_indices(6,1)].sum()/15,raw=True).values
    full.append(pd.DataFrame(dict(theme_id=t,source=s,period=[str(p) for p in gg.index],level=lv,momentum=mom,rising=rising,
        pattern=np.where(~rising,'none',np.where(prev>=2,'sustained','new')),trend_tau=tau,
        known_at=[p.end_time.normalize()+pd.Timedelta(days=1) for p in gg.index])))
theme_activity=pd.concat(full)
# ---- listening (outcome only)
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); idmap={str(k):v.identifier.tolist() for k,v in g}
lm=pd.period_range('2017-01','2026-08',freq='M')
listening=pd.DataFrame([(b,str(p),sum(V.get(i,{}).get(p.strftime('%Y%m'),0) for i in idmap[b])) for b in books for p in lm],columns=['book_id','period','listens'])
books_t=pd.DataFrame(dict(book_id=books,title=btitle.reindex(books).values))
for name,df in dict(items=items,observations=obs,themes=themes,item_theme=item_theme,book_theme=book_theme,theme_activity=theme_activity,listening=listening,books=books_t).items():
    df.to_parquet(f'{O}/{name}.parquet',index=False); print(name,len(df))
print(themes[themes.level==1][['theme_id','label','n_items','n_books']].to_string(index=False))
