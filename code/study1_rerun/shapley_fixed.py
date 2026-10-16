# FIXED copy of shapley4.py (old untouched): point-in-time narrator count, threads capped, outputs shapley3fix_*.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threads
from pit import narrator_pit_count
import pandas as pd, numpy as np, json, itertools, warnings
from math import factorial
warnings.filterwarnings('ignore')
from sklearn.model_selection import GroupKFold
from sklearn.decomposition import PCA
from scipy.stats import spearmanr
import lightgbm as lgb
from config import D
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet'); grp=json.load(open(f'{D}/processed/feature_groups.json'))
L['narr_pit']=narrator_pit_count(L.narrator_id,L.publicdate)
E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
m=L.merge(F,on='identifier'); m['narr_count']=m.narr_pit; m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&(m.publicdate>='2016-07-01')].reset_index(drop=True)
EMB=E[m.emb_row.values]; y=m.y_view.values
P={'Metadata':grp['META'],'Wiki volume':grp['VOL'],'Wiki trend':grp['TREND'],'Text':'TEXT'}
names=list(P); rows=[]
for rep in range(3):
    for fold,(tr,te) in enumerate(GroupKFold(5,shuffle=True,random_state=rep).split(m,groups=m.bookgroup)):
        for k in range(1,5):
            for S in itertools.combinations(names,k):
                cols=[c for s in S if s!='Text' for c in P[s]]
                a=m.loc[tr,cols].fillna(0).values if cols else np.zeros((len(tr),0)); b=m.loc[te,cols].fillna(0).values if cols else np.zeros((len(te),0))
                if 'Text' in S:
                    p=PCA(32,random_state=0).fit(EMB[tr]); a=np.hstack([a,p.transform(EMB[tr])]); b=np.hstack([b,p.transform(EMB[te])])
                pr=lgb.LGBMRegressor(n_estimators=500,learning_rate=0.03,num_leaves=31,min_child_samples=20,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=rep,verbose=-1).fit(a,y[tr]).predict(b)
                rows.append(dict(rep=rep,fold=fold,S='|'.join(S),sp=spearmanr(pr,y[te]).correlation))
r=pd.DataFrame(rows); r.to_csv(f'{D}/reports/shapley3fix_coalitions.csv',index=False)
v=r.groupby('S').sp.mean().to_dict(); v['']=0.0
key=lambda S:'|'.join(n for n in names if n in S)
out={}
for i in names:
    others=[n for n in names if n!=i]; phi=0
    for k in range(4):
        for S in itertools.combinations(others,k):
            w=factorial(len(S))*factorial(3-len(S))/factorial(4); phi+=w*(v[key(set(S)|{i})]-v[key(S)])
    out[i]=round(phi,4)
json.dump({'shapley':out,'coalitions':{k:round(x,4) for k,x in v.items()}},open(f'{D}/reports/shapley3fix_sources.json','w'),indent=1)
print(out)
