"""Sample public Bluesky posts for a fixed number of minutes (default 60) from the Jetstream firehose.
Keeps ONLY: post time, languages and text. Account identifiers (DIDs), handles, links and media are discarded on arrival.
Usage:  python bluesky_sample.py [minutes]
Output: data/bluesky/YYYY-MM-DD_HHMM.jsonl.gz"""
import asyncio, json, gzip, sys, time, datetime, pathlib, re
import websockets
HERE=pathlib.Path(__file__).parent; OUT=HERE/'data'/'bluesky'; OUT.mkdir(parents=True,exist_ok=True)
URL='wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post'
MENTION=re.compile(r'@[\w.\-]+'); LINK=re.compile(r'https?://\S+')
async def run(minutes):
    end=time.time()+minutes*60; n=0
    fn=OUT/f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d_%H%M}.jsonl.gz"
    with gzip.open(fn,'wt',encoding='utf-8') as f:
        while time.time()<end:
            try:
                async with websockets.connect(URL,max_size=2**22,ping_interval=20) as ws:
                    while time.time()<end:
                        m=json.loads(await asyncio.wait_for(ws.recv(),timeout=60))
                        c=m.get('commit') or {}
                        if c.get('operation')!='create': continue
                        rec=c.get('record') or {}; text=(rec.get('text') or '').strip()
                        if not text: continue
                        text=LINK.sub('',MENTION.sub('@user',text))[:1000]     # remove links and @mentions of people
                        f.write(json.dumps(dict(t=rec.get('createdAt'),langs=rec.get('langs'),text=text),ensure_ascii=False)+'\n'); n+=1
                        if n%20000==0: print(n,'posts',flush=True)
            except Exception as e:
                print('reconnecting:',str(e)[:80]); await asyncio.sleep(5)
    print('saved',n,'posts to',fn)
if __name__=='__main__': asyncio.run(run(float(sys.argv[1]) if len(sys.argv)>1 else 60))
