# Positive controls for theme-level demand, with the four fixes:
# long-tail theme attention, event month included, matched comparison books (difference-in-differences), placebo dates.
import pandas as pd, numpy as np, json, requests, time, urllib.parse
from fastembed import TextEmbedding
from config import D, UA; O=f'{D}/db'; H={"User-Agent":UA}
B=json.load(open(f'{D}/interim/book_themes.json')); books=np.array(B['books']); BE=np.load(f'{D}/interim/book_emb_by_group.npy')
L=pd.read_parquet(f'{O}/listening.parquet'); Lw=L.pivot(index='book_id',columns='period',values='listens').reindex(books)
lper=[pd.Period(p,'M') for p in Lw.columns]; LL=np.log1p(Lw.values.astype(float))
lab=pd.read_parquet(f'{D}/processed/labels.parquet'); lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]
g1=lk.merge(lab[['identifier','genre1']],on='identifier').groupby('bookgroup').genre1.agg(lambda s:s.mode().iloc[0]); g1.index=g1.index.astype(str); genre=g1.reindex(books).fillna('None').values
title=lk.groupby('bookgroup').title.first(); title.index=title.index.astype(str)
rel={str(k):[x.tz_localize(None).to_period('M') for x in v.publicdate.dropna()] for k,v in lk.groupby('bookgroup')}
model=TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
EVENTS=[
 ('COVID-19 and epidemics','2020-03','A story about plague, epidemic disease, contagion, quarantine and a city struck by pestilence.',['Pandemic','Epidemic','Plague_(disease)','Spanish_flu','Quarantine']),
 ('Black Lives Matter and slavery','2020-06','A narrative of slavery, abolition, racial injustice and the struggle of enslaved Black people for freedom.',['Slavery_in_the_United_States','Racism','Abolitionism','Juneteenth','Systemic_racism']),
 ('Roe v. Wade overturned and women\'s rights',"2022-06","A book about women's rights, the role of wives and mothers, marriage, gender roles and a woman's independence.",['Abortion_in_the_United_States','Roe_v._Wade','Women\'s_rights','Feminism','Reproductive_rights']),
 ('Titan submersible and shipwrecks','2023-06','A story of a shipwreck, a great ocean liner sinking and disaster at sea.',['RMS_Titanic','Shipwreck','Sinking_of_the_Titanic','Submarine','Deep-sea_exploration'])]
def pv(a):
    for k in range(6):
        try:
            r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{urllib.parse.quote(a,safe='')}/monthly/2016010100/2026083100",headers=H,timeout=30)
            if r.status_code==200: return pd.Series({pd.Period(x['timestamp'][:6],'M'):x['views'] for x in r.json()['items']})
            if r.status_code==404: return pd.Series(dtype=float)
        except Exception: pass
        time.sleep(6)
    return pd.Series(dtype=float)
def did(basket,m0,rng,n_ctrl=10):
    j=lper.index(m0); pre=slice(j-12,j-2); post=slice(j,j+3)
    ok=np.array([not any(-3<=(m0-r).n<=12 for r in rel.get(b,[])) for b in books])&(np.expm1(np.median(LL[:,pre],axis=1))>=5)
    lvl=np.median(LL[:,pre],axis=1); slope=np.polyfit(np.arange(10),LL[:,pre].T,1)[0]; chg=LL[:,post].mean(1)-LL[:,pre].mean(1)
    bs=[b for b in basket if ok[b]]; pool=np.where(ok&~np.isin(np.arange(len(books)),basket))[0]
    effects=[]
    for b in bs:
        cand=pool[genre[pool]==genre[b]]
        if len(cand)<n_ctrl: cand=pool
        d=((lvl[cand]-lvl[b])/0.8)**2+((slope[cand]-slope[b])/0.05)**2; c=cand[np.argsort(d)[:n_ctrl]]
        effects.append(chg[b]-chg[c].mean())
    effects=np.array(effects)
    if len(effects)<3: return np.nan,np.nan,len(effects)
    bsamp=[rng.choice(effects,len(effects)).mean() for _ in range(2000)]
    return float(np.exp(effects.mean())),float(np.mean(np.array(bsamp)<=0)),len(effects)
rng=np.random.RandomState(0); out=[]
for name,ev,q,pages in EVENTS:
    m0=pd.Period(ev,'M')
    att=sum((pv(p).reindex(pd.period_range('2016-01','2026-08',freq='M')).fillna(0) for p in pages))
    surge=float(att[m0:m0+1].mean()/att[m0-12:m0-3].median())
    qv=np.array(list(model.embed([q])))[0]; qv/=np.linalg.norm(qv); sim=BE@qv; basket=np.argsort(-sim)[:30]
    eff,p,n=did(basket,m0,rng)
    plac=[did(basket,m0+s,rng)[0] for s in (-24,-12,12,24) if (m0+s)>=pd.Period('2018-03','M') and (m0+s+3)<=lper[-1]]
    out.append(dict(event=name,month=ev,theme_attention_surge=round(surge,2),books_used=n,listening_effect_vs_matched=round(eff,3),one_sided_p=round(p,3),
                    same_books_other_years=[round(x,3) for x in plac if x==x],example_books=[title.get(b,'') for b in books[basket[:5]]]))
    print(json.dumps(out[-1],ensure_ascii=False),flush=True)
json.dump(out,open(f'{D}/reports/positive_controls.json','w'),indent=1,ensure_ascii=False)
