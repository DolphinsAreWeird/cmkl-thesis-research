# 01. Entities for TweetsKB: the English Wikipedia concept articles mapped to theme values (articles.parquet) plus the
# redirect titles that script 07 (Wikipedia series) adds to an article (old titles after a move, merged pages, redirects
# with real traffic; redirect_screen keep == True). TweetsKB links tweets to DBpedia resources named after the Wikipedia
# titles of the entity linker's dump (Nov 2015, Apr 2020, Aug 2022, Jun 2023), so an article that was renamed since is
# found under its older title. Each title becomes a DBpedia IRI. A probe (no dates) checks which IRIs exist in TweetsKB.
# Output: data/db/interest/tweetskb/entities.parquet (article, title, iri, kind, theme(s), exists_in_tweetskb)
import pandas as pd, sys
from tk_common import *

A = pd.read_parquet(f'{WK}/articles.parquet')
S = pd.read_parquet(f'{WK}/redirect_screen.parquet')
kept = S[S.keep == True].groupby('canonical').redirect.apply(list).to_dict()  # noqa: E712
rows = []
for c in sorted(A.canonical.dropna().unique()):
    rows.append(dict(article=c, title=c, kind='canonical'))
    for r in kept.get(c, []):
        rows.append(dict(article=c, title=r, kind='redirect'))
E = pd.DataFrame(rows).drop_duplicates(['article', 'title'])
E['iri'] = E.title.map(iri)
dup = E.groupby('iri').article.nunique()
print('titles', len(E), 'articles', E.article.nunique(), 'IRIs shared by two articles:', int((dup > 1).sum()))
exists = set()
iris = sorted(E.iri.unique())
for i in range(0, len(iris), 50):
    b = iris[i:i + 50]
    vals = ' '.join(f'<{u}>' for u in b)
    rows = run_query(f"SELECT ?u WHERE {{ VALUES ?u {{ {vals} }} FILTER EXISTS {{ ?e nee:hasMatchedURI ?u }} }}", 'probe')
    if rows is None:
        sys.exit('probe failed')
    exists |= {r['u'] for r in rows}
    print(i, len(exists), flush=True)
E['exists_in_tweetskb'] = E.iri.isin(exists)
save_parquet(E, f'{TK}/entities.parquet')
print('IRIs found in TweetsKB', len(exists), 'of', len(iris))
print('articles with at least one IRI found', E[E.exists_in_tweetskb].article.nunique(), 'of', E.article.nunique())
print(E.groupby('kind').exists_in_tweetskb.agg(['sum', 'size']))
