import pandas as pd, numpy as np, json, matplotlib, lightgbm as lgb
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from config import D, FIGS; O=FIGS
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
INK='#1E2A36'; ACC='#B04F24'; BLUE='#2C5A84'; GRAY='#9AA3AB'
P=pd.read_pickle(f'{D}/interim/study2_panel.pkl'); lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl')
T={x['timestamp'][:6]:x['views'] for x in json.load(open(f'{D}/raw/wiki_total_enwiki_monthly_to2026.json'))['items']}
lm=[p.strftime('%Y%m') for p in pd.period_range('2017-01','2026-08',freq='M')]
V=json.load(open(f'{D}/raw/ia_views_monthly.json'))
bgl=[g.identifier.tolist() for _,g in lk[lk.n_authors==1].groupby('bookgroup')]
Mk=pd.Series({j:np.median([np.log1p(sum(V.get(i,{}).get(m,0) for i in ids)) for ids in bgl]) for j,m in enumerate(lm)})
# keep the training panel's market values; the recomputed series extends it past mid-2025
Mk.update(P.groupby('j').market.first())
fb=set(lk[lk.title.str.contains('Frankenstein',case=False,na=False)].bookgroup)
feats=['genre','src','cal','att','att_prev','ratio','base','market']
tr=P[~P.bg.isin(fb)]; mdl=lgb.LGBMRegressor(n_estimators=400,learning_rate=0.05,num_leaves=31,min_child_samples=50,verbose=-1,random_state=0).fit(tr[feats],tr.y)
# Frankenstein attention from the case pull (2024-2026) plus earlier months from the stored series
c=pd.read_csv(f'{D}/reports/case_frankenstein.csv',index_col=0); c.index=c.index.astype(str)
PV=json.load(open(f'{D}/raw/wiki_pageviews_monthly.json')); old=PV.get('Frankenstein',{})
allm=[p.strftime('%Y%m') for p in pd.period_range('2023-01','2026-08',freq='M')]
raw={k:(c.wiki.get(k) if k in c.index else old.get(k,0)) for k in allm}
a=np.array([raw[k]/T[k]*1e6 for k in allm])
rows=[]
for t in range(12,len(allm)-1):
    nxt=allm[t+1]; j=lm.index(nxt)-1 if nxt in lm else None
    if j is None or j not in Mk.index: continue
    base=np.median(a[t-12:t])
    rows.append(dict(month=nxt,genre=P.genre.mode()[0],src=1,cal=int(allm[t][4:]),att=np.log1p(a[t]),att_prev=np.log1p(a[t-1]),ratio=np.log1p(a[t])-np.log1p(base),base=np.log1p(base),market=Mk[j]))
X=pd.DataFrame(rows); X['genre']=pd.Categorical(X.genre,categories=P.genre.cat.categories)
X['pred']=np.expm1(mdl.predict(X[feats]))
cases=[('Frankenstein (film, Oct to Nov 2025)','frankenstein',['202506','202507','202508']),('Wuthering Heights (film, Feb 2026)','wuthering',['202510','202511','202512']),('The Great Gatsby (centenary, Apr 2025)','gatsby',['202501','202502','202503'])]
wh=pd.read_csv(f'{D}/reports/wuthering_case.csv',index_col=0); wh.index=wh.index.astype(str)
whc=pd.DataFrame({'listens':wh.iloc[:,0],'wiki':wh['Wikipedia: Wuthering_Heights']})
fig,axs=plt.subplots(1,3,figsize=(15,4.3))
for ax,(name,key,basem) in zip(axs,cases):
    d=whc if key=='wuthering' else pd.read_csv(f'{D}/reports/case_{key}.csv',index_col=0)
    d.index=d.index.astype(str); start=pd.Period(basem[0][:4]+'-'+basem[0][4:],'M')
    ms=[(start+k).strftime('%Y%m') for k in range(0,14) if (start+k).strftime('%Y%m') in d.index]
    bl=d.loc[basem].mean(); x=np.arange(len(ms))
    ax.plot(x,d.loc[ms,'wiki']/bl.wiki*100,color=GRAY,marker='o',ms=3,label='Wikipedia views')
    ax.plot(x,d.loc[ms,'listens']/bl.listens*100,color=ACC,marker='o',ms=3,label='LibriVox listens (actual)')
    if key=='frankenstein':
        fx=X.set_index('month').pred; pr=fx.reindex(ms); ax.plot(x,pr/fx.reindex(basem).mean()*100,color=BLUE,ls='--',label='Hidden-book forecast (relative)')
    ax.set_yscale('log'); ax.axhline(100,color=GRAY,lw=0.6); ax.set_xticks(x[::2]); ax.set_xticklabels([f'{m[4:]}/{m[2:4]}' for m in ms][::2],fontsize=8)
    ax.set_title(name,loc='left',fontsize=10); ax.set_ylabel('Index, 100 = normal' if key=='frankenstein' else '')
axs[0].legend(frameon=False,fontsize=8,loc='upper left')
fig.tight_layout(); fig.savefig(f'{O}/fig4_cases.png',dpi=160)
f=X.set_index('month'); print(f.loc[['202509','202510','202511','202512','202601'],'pred'].round(0).to_dict())
