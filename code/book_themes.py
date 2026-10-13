# Book theme map: cluster books by the meaning of their descriptions, and name each cluster from its own words.
import pandas as pd, numpy as np, json, re
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from config import D
lk=pd.read_pickle(f'{D}/interim/recordings_linked.pkl').reset_index(drop=True); E=np.load(f'{D}/interim/description_embeddings_minilm.npy')
lk=lk[lk.n_authors==1]; bg=lk.groupby('bookgroup')
books=list(bg.groups); emb=np.stack([E[g.index].mean(0) for _,g in bg]); emb/=np.linalg.norm(emb,axis=1,keepdims=True)
desc=bg.desc.first().reindex(books).fillna('')+' '+bg.title.first().reindex(books).fillna('')
K=40; km=KMeans(K,n_init=10,random_state=0).fit(emb); lab=km.labels_
tf=TfidfVectorizer(stop_words='english',max_features=20000,min_df=3,token_pattern=r'(?u)\b[a-zA-Z]{4,}\b'); X=tf.fit_transform(desc); vocab=np.array(tf.get_feature_names_out())
themes=[]
for k in range(K):
    idx=np.where(lab==k)[0]; w=np.asarray(X[idx].mean(0)).ravel(); words=vocab[np.argsort(-w)[:8]]
    cen=km.cluster_centers_[k]/np.linalg.norm(km.cluster_centers_[k]); near=idx[np.argsort(-(emb[idx]@cen))[:5]]
    themes.append(dict(theme=k,size=len(idx),keywords=list(words),examples=[bg.title.first()[books[i]] for i in near]))
C=km.cluster_centers_/np.linalg.norm(km.cluster_centers_,axis=1,keepdims=True)
np.save(f'{D}/interim/book_theme_centroids.npy',C); np.save(f'{D}/interim/book_emb_by_group.npy',emb)
json.dump({'books':[str(b) for b in books],'labels':lab.tolist(),'themes':themes},open(f'{D}/interim/book_themes.json','w'))
for t in themes: print(t['theme'],t['size'],', '.join(t['keywords'][:6]),'|',' / '.join(t['examples'][:3]))
