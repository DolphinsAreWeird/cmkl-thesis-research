# Goodreads review-count trend features, using only reviews added before each recording's release.
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
import pymannkendall as mk, ruptures as rpt
from config import D
L=pd.read_parquet(f'{D}/processed/labels.parquet')
G=pd.read_pickle(f'{D}/interim/goodreads_linked.pkl'); R=json.load(open(f'{D}/raw/goodreads_reviews_monthly.json'))
months=pd.period_range('2007-01','2017-10',freq='M'); keys=[p.strftime('%Y%m') for p in months]
m=L[['identifier','publicdate']].merge(G,on='identifier',how='left')
rows=[]
for _,r in m.iterrows():
    d={'identifier':r.identifier,'gr_has':0}
    if isinstance(r.gr_book_ids,list) and pd.notna(r.publicdate):
        v=np.zeros(len(keys))
        for b in r.gr_book_ids:
            for k,c in R.get(b,{}).items():
                if k in keys: v[keys.index(k)]+=c
        cut=sum(1 for p in months if p<r.publicdate.to_period('M'))
        x=np.log1p(v[:cut])
        if cut>=24 and v[:cut].sum()>0:
            l12=x[-12:]
            d.update(gr_has=1,gr_total=np.log1p(v[:cut].sum()),gr_level12=l12.mean(),gr_rel_level=l12.mean()-x.mean(),
                     gr_months_covered=cut)
            t=mk.original_test(x[-24:]); d.update(gr_mk_tau=t.Tau,gr_sen_slope=t.slope)
            if np.var(x)>0:
                bk=[b for b in rpt.Pelt(model='l2',min_size=3).fit(x).predict(pen=2*np.log(len(x))*np.var(x)) if b<len(x)]
                d.update(gr_n_breaks=len(bk),gr_months_since_break=(len(x)-bk[-1]) if bk else len(x))
    rows.append(d)
F=pd.DataFrame(rows); F.to_parquet(f'{D}/processed/features_goodreads.parquet')
grp=json.load(open(f'{D}/processed/feature_groups.json')); grp['GOODREADS']=[c for c in F.columns if c!='identifier']
json.dump(grp,open(f'{D}/processed/feature_groups.json','w'),indent=1)
a=F.merge(L,on='identifier'); a=a[a.publicdate>='2016-07-01']
print('recordings with Goodreads review history before release',int(F.gr_has.sum()),'| in analysis window',int(a.gr_has.sum()))
