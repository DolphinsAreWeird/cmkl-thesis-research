# YouTube feasibility sample: videos about each book published before its recording's release (quota-limited).
import pandas as pd, requests, json, time, os
from config import D, key; K=key('YOUTUBE_API_KEY')
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet'); m=L.merge(F,on='identifier')
m=m[(m.n_authors==1)&(~m.author.isin(['Various','Unknown','Anonymous']))&(m.publicdate>='2016-07-01')]
s=m.sample(85,random_state=11)
out=f'{D}/raw/youtube_sample.json'; res=json.load(open(out)) if os.path.exists(out) else {}
used=0
def get(url,p):
    global used
    p['key']=K; r=requests.get(url,params=p,timeout=30); return r.json() if r.ok else {'error':r.json().get('error',{}).get('message')}
for _,r in s.iterrows():
    if r.identifier in res: continue
    before=r.publicdate.strftime('%Y-%m-%dT00:00:00Z')
    q=f'"{r.title}" {r.author.split()[-1]}'
    j=get("https://www.googleapis.com/youtube/v3/search",{"part":"snippet","q":q,"type":"video","maxResults":50,"publishedBefore":before,"order":"relevance"}); used+=100
    if 'error' in j: print('stop',j['error']); break
    ids=[i['id']['videoId'] for i in j.get('items',[])]
    vids=[]
    if ids:
        v=get("https://www.googleapis.com/youtube/v3/videos",{"part":"statistics,snippet","id":",".join(ids)}); used+=1
        for it in v.get('items',[]):
            st=it.get('statistics',{}); vids.append(dict(id=it['id'],published=it['snippet']['publishedAt'],views=int(st.get('viewCount',0)),comments=int(st.get('commentCount',0)),likes=int(st.get('likeCount',0)),title=it['snippet']['title']))
    pre_comments=[]
    for vd in sorted(vids,key=lambda x:-x['views'])[:3]:
        c=get("https://www.googleapis.com/youtube/v3/commentThreads",{"part":"snippet","videoId":vd['id'],"maxResults":100,"order":"time","textFormat":"plainText"}); used+=1
        for it in c.get('items',[]):
            sn=it['snippet']['topLevelComment']['snippet']
            if sn['publishedAt']<before: pre_comments.append(dict(video=vd['id'],published=sn['publishedAt'],likes=sn.get('likeCount',0),text=sn['textDisplay'][:500]))
    res[r.identifier]=dict(query=q,before=before,total_results=j.get('pageInfo',{}).get('totalResults'),videos=vids,pre_release_comments=pre_comments)
    json.dump(res,open(out,'w'))
    time.sleep(0.3)
print('titles',len(res),'units used this run ~',used)
