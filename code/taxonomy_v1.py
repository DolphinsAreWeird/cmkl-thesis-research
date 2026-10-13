# Interest taxonomy v1 from LibriVox books: two levels, clustered on what each book is about, labelled from its own words.
import pandas as pd, numpy as np, json
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from config import D
B=json.load(open(f'{D}/interim/book_themes.json')); books=B['books']; BE=np.load(f'{D}/interim/book_emb_by_group.npy')
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl'); lk=lk[lk.n_authors==1]; g=lk.groupby('bookgroup')
title=g.title.first(); title.index=title.index.astype(str); desc=g.desc.first(); desc.index=desc.index.astype(str)
L=pd.read_parquet(f'{D}/db/listening.parquet'); tot=L.groupby('book_id').listens.sum()
txt=(title.reindex(books).fillna('')+'. '+desc.reindex(books).fillna('')).values
stop=list(ENGLISH_STOP_WORDS|{'librivox','recording','recordings','version','volume','chapter','chapters','book','books','read','reader','readers','story','stories','collection','author','written','work','works','published','edition','public','domain','audio','title','titles','text','note','notes','including','includes','various','second','third','thus','also','well','first','many','great','life','time','years','year','new','old','little','good','long','called','like','come','came','make','made','just','shall','said','says','tells','told','famous','known','english','american'})
tf=TfidfVectorizer(stop_words=stop,token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',min_df=3,max_df=0.15,sublinear_tf=True); X=tf.fit_transform(txt); voc=np.array(tf.get_feature_names_out())
def words(idx,n=6): w=np.asarray(X[idx].mean(0)).ravel(); return list(voc[np.argsort(-w)[:n]])
def exemplars(idx,cen,n=4):
    o=idx[np.argsort(-(BE[idx]@cen))]; return [title[books[i]] for i in o[:n]]
k1=KMeans(14,n_init=10,random_state=0).fit(BE); rows=[]; assign=[]
for a in range(14):
    idx=np.where(k1.labels_==a)[0]; c=k1.cluster_centers_[a]/np.linalg.norm(k1.cluster_centers_[a])
    rows.append(dict(id=f'C{a}',level=1,parent='',n_books=len(idx),listens=int(tot.reindex([books[i] for i in idx]).sum()),keywords=', '.join(words(idx)),examples=' | '.join(exemplars(idx,c))))
    kk=int(np.clip(round(len(idx)/150),2,8)); k2=KMeans(kk,n_init=6,random_state=0).fit(BE[idx])
    for s in range(kk):
        sidx=idx[k2.labels_==s]; c2=k2.cluster_centers_[s]/np.linalg.norm(k2.cluster_centers_[s])
        rows.append(dict(id=f'C{a}.{s}',level=2,parent=f'C{a}',n_books=len(sidx),listens=int(tot.reindex([books[i] for i in sidx]).sum()),keywords=', '.join(words(sidx)),examples=' | '.join(exemplars(sidx,c2))))
        for i in sidx: assign.append((books[i],f'C{a}',f'C{a}.{s}'))
T=pd.DataFrame(rows); T.to_csv(f'{D}/db/taxonomy_v1_raw.csv',index=False)
pd.DataFrame(assign,columns=['book_id','level1','level2']).to_csv(f'{D}/db/taxonomy_v1_assign.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_colwidth',110)
print(T[['id','n_books','keywords','examples']].to_string(index=False))
