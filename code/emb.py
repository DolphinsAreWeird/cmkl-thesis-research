import pandas as pd, numpy as np, time
from fastembed import TextEmbedding
m=pd.read_pickle('base2.pkl')
texts=(m.title.fillna('')+'. '+m.desc.fillna('').str.slice(0,1200)).tolist()
model=TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
t=time.time()
E=np.array(list(model.embed(texts,batch_size=64)))
np.save('emb.npy',E); print(E.shape, round(time.time()-t),'s')
