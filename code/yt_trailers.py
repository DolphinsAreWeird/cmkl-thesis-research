# Step 3: YouTube trailer engagement for each adaptation (trailers published before release; counts as of today).
import pandas as pd, numpy as np, requests, json, re, os
from config import D, key; K=key('YOUTUBE_API_KEY')
U=pd.read_csv(f'{D}/reports/adaptation_coded.csv')
U=pd.concat([U,pd.DataFrame([dict(book='Odyssey',adaptation='The_Odyssey_(2026_film)',date='2026-07-17',faithful=1)])],ignore_index=True)
out=json.load(open(f'{D}/raw/yt_trailers.json')) if os.path.exists(f'{D}/raw/yt_trailers.json') else {}
for _,r in U.iterrows():
    if r.adaptation in out: continue
    name=re.sub(r'_\(.*?\)','',r.adaptation).replace('_',' ')
    yr=str(r.date)[:4]
    s=requests.get("https://www.googleapis.com/youtube/v3/search",params=dict(part='snippet',q=f'{name} {yr} official trailer',type='video',maxResults=10,publishedBefore=f'{str(r.date)[:10]}T00:00:00Z',key=K),timeout=30).json()
    if 'error' in s: print('stop',s['error'].get('message','')[:80]); break
    ids=[i['id']['videoId'] for i in s.get('items',[])]
    vids=[]
    if ids:
        v=requests.get("https://www.googleapis.com/youtube/v3/videos",params=dict(part='statistics,snippet',id=','.join(ids),key=K),timeout=30).json()
        for it in v.get('items',[]):
            t=it['snippet']['title'].lower()
            if 'trailer' in t and all(w in re.sub(r'[^a-z0-9 ]',' ',t) for w in re.sub(r'[^a-z0-9 ]',' ',name.lower()).split()[:2]):
                st=it['statistics']; vids.append(dict(views=int(st.get('viewCount',0)),likes=int(st.get('likeCount',0)),comments=int(st.get('commentCount',0)),published=it['snippet']['publishedAt'][:10],title=it['snippet']['title']))
    out[r.adaptation]=vids; json.dump(out,open(f'{D}/raw/yt_trailers.json','w'))
print('adaptations with trailer data:',sum(1 for v in out.values() if v),'of',len(out))
U['trailer_views']=U.adaptation.map(lambda a: max([x['views'] for x in out.get(a,[])],default=0))
U['first_trailer']=U.adaptation.map(lambda a: min([x['published'] for x in out.get(a,[])],default=None))
U['lead_weeks']=[(pd.Timestamp(d)-pd.Timestamp(f)).days/7 if f else np.nan for d,f in zip(U.date,U.first_trailer)]
U.to_csv(f'{D}/reports/adaptation_with_trailers.csv',index=False)
from scipy.stats import spearmanr
k=U[U.lift.notna()]
print('Spearman trailer views vs lift:',round(spearmanr(k.trailer_views,k.lift).correlation,2),'| Wikipedia pre-release peak vs lift:',round(spearmanr(k.pre_peak,k.lift).correlation,2),'n',len(k))
for th in [1e6,5e6,20e6]:
    g=k.trailer_views>=th; print(f'trailer >= {th/1e6:.0f}M views: n={g.sum()} share lift>=1.3 {(k[g].lift>=1.3).mean():.0%} | faithful among them lift>=1.3 {(k[g&(k.faithful==1)].lift>=1.3).mean() if (g&(k.faithful==1)).any() else float("nan"):.0%}')
print(U.sort_values('trailer_views',ascending=False)[['adaptation','faithful','trailer_views','lead_weeks','lift']].head(12).round(2).to_string(index=False))
