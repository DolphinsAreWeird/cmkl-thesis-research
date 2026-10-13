import pandas as pd, json
from config import D
L=pd.read_parquet(f'{D}/processed/labels.parquet'); F=pd.read_parquet(f'{D}/processed/features.parquet'); m=L.merge(F,on='identifier')
s=m[m.n_authors==1]; a=s[s.publicdate>='2016-07-01']
rep=pd.DataFrame([
 ['Recordings in released file',len(m),''],['Exact release date found (Internet Archive)',int(m.publicdate.notna().sum()),''],
 ['Single-author recordings',len(s),''],['Linked to author Wikipedia article (Wikidata)',int(s.wiki_author.notna().sum()),f'{s.wiki_author.notna().mean():.0%}'],
 ['Linked to book Wikipedia article (Wikidata)',int(s.wiki_book.notna().sum()),f'{s.wiki_book.notna().mean():.0%}'],
 ['Analysis sample (single author, released from Jul 2016)',len(a),''],['  with usable author page-view series',int(a.wa_has.sum()),f'{a.wa_has.mean():.0%}'],
 ['  with usable book page-view series',int(a.wb_has.sum()),f'{a.wb_has.mean():.0%}']],columns=['step','count','share'])
rep.to_csv(f'{D}/reports/match_report.csv',index=False); print(rep.to_string(index=False))
chk=s[s.wiki_author.notna()].sample(200,random_state=7)[['title','author','wiki_author','wiki_book']]
chk['author_link_correct (y/n)']=''; chk['book_link_correct (y/n/blank)']=''
chk.to_csv(f'{D}/reports/match_check_sample_200.csv',index=False)
g=json.load(open(f'{D}/processed/feature_groups.json'))
desc={'log_hours':'log running time in hours','log_sections':'log number of sections','narr_count':'log number of recordings by this narrator',
 'level12':'mean normalized page views, 12 months before release','rel_level':'last 12 months vs all earlier months','spike':'peak / median views in last 12 months',
 'mk_tau':'Mann-Kendall trend strength, last 12 months','sen_slope':"Sen's slope, last 12 months",'mk_rising':'significant rising trend (Mann-Kendall)',
 'stl_slope':'slope of STL trend component, last 12 months','season_strength':'strength of yearly seasonality (STL)','n_breaks':'number of change points (PELT)',
 'months_since_break':'months from last change point to release','last_jump':'level change at last change point','has':'source has a usable series'}
rows=[]
for grpname,cols in g.items():
    for c in cols:
        base=c.split('_',1)[1] if c.startswith(('wa_','wb_')) else c
        src='author article' if c.startswith('wa_') else 'book article' if c.startswith('wb_') else 'LibriVox'
        d=desc.get(base, 'k-Shape cluster of the 12-month pre-release curve' if 'shape' in base else ('genre flag' if c.startswith('g_') else ''))
        rows.append([c,grpname,src,d])
rows+= [['y_view','label','LibriVox','log views per day minus median of release half-year'],['y_fav','label','LibriVox','log favorites per 1,000 days minus median of release half-year'],['text_pca_1..32','TEXT','LibriVox API','description embedding (MiniLM), PCA fitted inside each training fold']]
pd.DataFrame(rows,columns=['column','group','source','meaning']).to_csv(f'{D}/reports/data_dictionary.csv',index=False)
