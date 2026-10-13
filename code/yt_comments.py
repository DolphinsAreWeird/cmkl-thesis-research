# Real social discussion: timestamped YouTube comments on each adaptation's top trailer (no author names stored).
import json, requests, re, os, pandas as pd, time
from config import D, key; K=key('YOUTUBE_API_KEY')
T=json.load(open(f'{D}/raw/yt_trailers.json'))
out=json.load(open(f'{D}/raw/yt_trailer_comments.json')) if os.path.exists(f'{D}/raw/yt_trailer_comments.json') else {}
units=0
for ad,vids in T.items():
    if not vids or ad in out: continue
    s=requests.get("https://www.googleapis.com/youtube/v3/search",params=dict(part='id',q=vids[0]['title'],type='video',maxResults=1,key=K),timeout=30).json() if False else None
    top=max(vids,key=lambda v:v['views'])
    # find the video id again from the stored search (ids not stored earlier): one cheap videos lookup by title is not possible, so re-run search once
    q=requests.get("https://www.googleapis.com/youtube/v3/search",params=dict(part='id',q=top['title'],type='video',maxResults=1,key=K),timeout=30).json(); units+=100
    if 'error' in q: print('quota/err:',q['error'].get('message','')[:80]); break
    vid=q['items'][0]['id']['videoId'] if q.get('items') else None
    if not vid: out[ad]={'video':None,'comments':[]}; continue
    com=[]; tok=None
    for page in range(60):                       # up to 6,000 newest-first comments; enough to reach pre-release for most trailers
        p=dict(part='snippet',videoId=vid,maxResults=100,order='time',textFormat='plainText',key=K)
        if tok: p['pageToken']=tok
        r=requests.get("https://www.googleapis.com/youtube/v3/commentThreads",params=p,timeout=30).json(); units+=1
        if 'error' in r: break
        for it in r.get('items',[]):
            c=it['snippet']['topLevelComment']['snippet']; com.append(dict(t=c['publishedAt'][:10],likes=c.get('likeCount',0),replies=it['snippet'].get('totalReplyCount',0),text=c['textDisplay'][:300]))
        tok=r.get('nextPageToken')
        if not tok: break
    out[ad]={'video':vid,'trailer_published':top['published'],'comments':com}
    json.dump(out,open(f'{D}/raw/yt_trailer_comments.json','w')); print(ad,len(com),'comments',flush=True)
print('units used ~',units,'| adaptations done',len(out))
