# Proof of concept: theme-level demand. Books are matched to a theme by meaning (embeddings), not by title keywords.
# A social event raises attention to a theme; does listening to the theme's books rise, compared with random books?
import pandas as pd, numpy as np, json, requests
from fastembed import TextEmbedding
from config import D, UA; H={"User-Agent":UA}
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl').reset_index(drop=True); E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
V=json.load(open(f'{D}/raw/ia_views_monthly.json')); months=pd.period_range('2017-01','2026-08',freq='M')
lk=lk[lk.n_authors==1]
# book-level embedding (mean of its recordings) and monthly listening
bg=lk.groupby('bookgroup'); books=list(bg.groups)
emb=np.stack([E[g.index].mean(0) for _,g in bg]); emb/=np.linalg.norm(emb,axis=1,keepdims=True)
lis=pd.DataFrame({b:[sum(V.get(i,{}).get(p.strftime('%Y%m'),0) for i in g.identifier) for p in months] for b,g in bg},index=months)
title=bg.title.first(); rel=bg.publicdate.min()
market=np.log1p(lis).median(axis=1)
model=TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
THEMES={
 'Plague and epidemics':('A story about plague, epidemic disease, contagion, quarantine and a city struck by pestilence.','2020-03','Pandemic'),
 'Slavery and racial justice':('A narrative of slavery, abolition, racial injustice and the struggle of enslaved Black people for freedom.','2020-06','Slavery_in_the_United_States'),
 "Women's rights and motherhood":("A book about women's rights, the role of wives and mothers, marriage, gender roles and a woman's independence.",'2022-06','Feminism'),
}
def wiki(a):
  import time
  for k in range(6):
    try:
      r=requests.get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{a}/monthly/2016010100/2025123100",headers=H,timeout=30).json()
      return pd.Series({pd.Period(x['timestamp'][:6],'M'):x['views'] for x in r.get('items',[])})
    except Exception: time.sleep(8)
  return pd.Series(dtype=float)
rng=np.random.RandomState(0); out={}
eligible=[b for b in books if lis[b]['2018-01':'2019-12'].median()>=20]
for name,(q,ev,art) in THEMES.items():
    qv=np.array(list(model.embed([q])))[0]; qv/=np.linalg.norm(qv)
    sim=pd.Series(emb@qv,index=books)
    top=[b for b in sim.sort_values(ascending=False).index if b in eligible][:30]
    m0=pd.Period(ev,'M')
    def lift(bs):  # listening in event month and next 2, vs same books 12-7 months earlier, adjusted for the market
        x=np.log1p(lis[bs]); post=x.loc[m0:m0+2].mean().mean()-market.loc[m0:m0+2].mean(); pre=x.loc[m0-12:m0-7].mean().mean()-market.loc[m0-12:m0-7].mean()
        return np.exp(post-pre)
    obs=lift(top); plc=np.array([lift(list(rng.choice(eligible,30,replace=False))) for _ in range(500)])
    w=wiki(art); wr=(w.loc[m0:m0+1].mean()/w.loc[m0-12:m0-7].mean()) if len(w) else np.nan
    out[name]=dict(event=ev,theme_article=art,theme_attention_ratio=round(float(wr),2),basket_lift=round(float(obs),2),
                   placebo_median=round(float(np.median(plc)),2),placebo_p=round(float((plc>=obs).mean()),3),
                   example_books=[title[b] for b in top[:8]])
    print(name,json.dumps(out[name],ensure_ascii=False),flush=True)
json.dump(out,open(f'{D}/reports/theme_poc.json','w'),indent=1,ensure_ascii=False)
