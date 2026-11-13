# 97. LibriVox new recordings: Wikipedia alone and added to the platform's own record (exploratory; prereg/DEVIATIONS.md,
# "LibriVox new recordings: Wikipedia alone and added (14 November 2026)", written before this ran).
# Data preparation copied from code/walkforward3_fix.py (single-author recordings from 2017, target ln(1 + views in months 2 to 7 after
# the release month), point-in-time narrator count, history features from earlier recordings whose windows had ended).
# Inputs: W = Study 1 Wikipedia volume and trend features without the shape-cluster flags; R = metadata + history; R+W.
# Models: LightGBM (Study 1 settings, main) and ridge (penalty 10, check). Measures: AUC for the top 20% and Spearman per test quarter,
# averaged over quarters; 95% intervals from 2,000 draws of authors within each quarter (seed 20261114), paired for R+W minus R.
# Output: data/reports/librivox_new_recordings.json and .md; predictions in data/interim/librivox_new_recordings_preds.parquet.
#   Run from code/:  nice ../.venv/bin/python main_study/wiki_led/97_librivox_new_recordings.py
import sys, json, pathlib, time, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy.stats import spearmanr, rankdata
import lightgbm as lgb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D                                         # noqa: E402

t0 = time.time()
S, N = 2, 6
L = pd.read_parquet(f'{D}/processed/labels.parquet'); F = pd.read_parquet(f'{D}/processed/features.parquet')
grp = json.load(open(f'{D}/processed/feature_groups.json'))
V = json.load(open(f'{D}/raw/ia_views_monthly.json'))
m = L.merge(F, on='identifier')
m = m[(m.n_authors == 1) & (~m.author.isin(['Various', 'Unknown', 'Anonymous'])) & m.identifier.isin(V) & m.publicdate.notna()].copy()
m['rel_m'] = m.publicdate.dt.tz_localize(None).dt.to_period('M'); last = pd.Period('2026-08', 'M')
allrec = L[['identifier', 'narrator_id', 'publicdate']].dropna().sort_values('publicdate')
allrec['narr_pit'] = np.log1p(allrec.groupby('narrator_id').cumcount())
m = m.merge(allrec[['identifier', 'narr_pit']], on='identifier', how='left'); m['narr_count'] = m.narr_pit.fillna(0)


def lab(r):
    if r.rel_m < pd.Period('2017-01', 'M') or r.rel_m + S + N - 1 > last:
        return np.nan
    return np.log1p(sum(V[r.identifier].get((r.rel_m + k).strftime('%Y%m'), 0) for k in range(S, S + N)))


m['y'] = m.apply(lab, axis=1); m = m.dropna(subset=['y']); m['label_end'] = m.rel_m + S + N - 1
m = m.sort_values('rel_m').reset_index(drop=True)
for key, name in [('narrator_id', 'narr'), ('author', 'auth'), ('bookgroup', 'book')]:
    mean = np.full(len(m), np.nan); cnt = np.zeros(len(m))
    for k, g in m.groupby(key):
        e = g.label_end.values; ys = g.y.values
        for idx, r in zip(g.index, g.rel_m.values):
            ok = e < r
            if ok.any():
                mean[idx] = ys[ok].mean(); cnt[idx] = ok.sum()
    m[f'{name}_prior'] = mean; m[f'{name}_prior_n'] = np.log1p(cnt); m[f'{name}_has_prior'] = (cnt > 0).astype(int)
HIST = [c for c in m.columns if c.endswith(('_prior', '_prior_n', '_has_prior'))]
WIKI = [c for c in grp['VOL'] + grp['TREND'] if '_shape' not in c]
SETS = {'W': WIKI, 'R': grp['META'] + HIST, 'RW': grp['META'] + HIST + WIKI}
print('recordings', len(m), '| wikipedia features', len(WIKI), '| with an author article', int(m.wa_has.sum()), '| with a book article', int(m.wb_has.sum()))

preds = []
for q in pd.period_range('2020Q1', (last - (S + N - 1)).asfreq('Q'), freq='Q'):
    qs = q.asfreq('M', 'start')
    te = m.index[(m.rel_m >= qs) & (m.rel_m <= q.asfreq('M', 'end'))]; tr = m.index[m.label_end < qs]
    if len(te) < 30 or len(tr) < 300:
        continue
    y = m.y.values
    for st, cols in SETS.items():
        a = m.loc[tr, cols].fillna(0).values.astype(float); b = m.loc[te, cols].fillna(0).values.astype(float)
        sc = StandardScaler().fit(a)
        p_r = Ridge(10).fit(sc.transform(a), y[tr]).predict(sc.transform(b))
        p_l = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.03, num_leaves=31, min_child_samples=20, subsample=0.8, subsample_freq=1,
                                colsample_bytree=0.8, random_state=0, verbose=-1).fit(a, y[tr]).predict(b)
        for mdl, p in (('LightGBM', p_l), ('Ridge', p_r)):
            preds.append(pd.DataFrame({'quarter': str(q), 'identifier': m.identifier.values[te], 'author': m.author.values[te],
                                       'new_author': (m.auth_has_prior.values[te] == 0), 'y': y[te], 'set': st, 'model': mdl, 'p': p}))
    print(q, len(te), f'{time.time() - t0:.0f}s', flush=True)
P = pd.concat(preds, ignore_index=True)
P.to_parquet(f'{D}/interim/librivox_new_recordings_preds.parquet', index=False)


def auc(top, p):
    r = rankdata(p); n1 = top.sum(); n0 = len(top) - n1
    return np.nan if n1 == 0 or n0 == 0 else (r[top == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def scores(g):
    """Per quarter: the top 20% is defined within the rows scored (all recordings of the quarter, or the subgroup)."""
    out = {}
    for (q, st), h in g.groupby(['quarter', 'set']):
        top = (h.y.values >= np.quantile(h.y.values, 0.8)).astype(int)
        out[(q, st)] = (auc(top, h.p.values), spearmanr(h.p.values, h.y.values).correlation)
    return out


rng = np.random.default_rng(20261114)
res = {}
for mdl in ('LightGBM', 'Ridge'):
    for part in ('all', 'new_author'):
        g = P[(P.model == mdl) & ((P.new_author) if part == 'new_author' else True)]
        base = scores(g)
        qs = sorted({q for q, _ in base})
        est = {st: (np.nanmean([base[(q, st)][0] for q in qs]), np.nanmean([base[(q, st)][1] for q in qs])) for st in SETS}
        # author bootstrap within each quarter: every input set holds the same rows in the same order, so one draw serves all three
        prep = []
        for q in qs:
            h = {st: g[(g.quarter == q) & (g.set == st)] for st in SETS}
            assert all((h[st].identifier.values == h['W'].identifier.values).all() for st in SETS)
            codes, uniq = pd.factorize(h['W'].author)
            prep.append((h['W'].y.values, {st: h[st].p.values for st in SETS}, [np.flatnonzero(codes == i) for i in range(len(uniq))]))
        draws = {k: [] for k in ('W', 'R', 'RW', 'RW-R')}
        for _ in range(2000):
            per = {st: [] for st in SETS}
            for ys_all, ps_all, groups in prep:
                sel = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
                ys = ys_all[sel]
                top = (ys >= np.quantile(ys, 0.8)).astype(int) if len(ys) >= 10 else None
                for st in SETS:
                    per[st].append(auc(top, ps_all[st][sel]) if top is not None else np.nan)
            for st in SETS:
                draws[st].append(np.nanmean(per[st]))
            draws['RW-R'].append(np.nanmean(np.array(per['RW']) - np.array(per['R'])))
        ci = {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) for k, v in draws.items()}
        n_rows = int(g[g.set == 'W'].shape[0])
        res[f'{mdl}|{part}'] = dict(quarters=len(qs), first=qs[0], last=qs[-1], rows=n_rows,
                                    auc={st: dict(est=float(est[st][0]), lo=ci[st][0], hi=ci[st][1]) for st in SETS},
                                    auc_RW_minus_R=dict(est=float(est['RW'][0] - est['R'][0]), lo=ci['RW-R'][0], hi=ci['RW-R'][1]),
                                    spearman={st: float(est[st][1]) for st in SETS})
        print(mdl, part, json.dumps(res[f'{mdl}|{part}']['auc_RW_minus_R']), {st: round(est[st][0], 3) for st in SETS}, flush=True)

res['_meta'] = dict(recordings=int(len(m)), wikipedia_features=WIKI, with_author_article=int(m.wa_has.sum()), with_book_article=int(m.wb_has.sum()),
                    runtime_s=int(time.time() - t0), record='prereg/DEVIATIONS.md, LibriVox new recordings (14 November 2026)')
json.dump(res, open(f'{D}/reports/librivox_new_recordings.json', 'w'), indent=1)
L_ = ['# LibriVox new recordings: Wikipedia alone and added (exploratory)', '',
      f"Record: {res['_meta']['record']}. Recordings: {res['_meta']['recordings']:,}; with an author article {res['_meta']['with_author_article']:,}, "
      f"with a book article {res['_meta']['with_book_article']:,}. AUC for the top 20% of each test quarter, averaged over quarters; 95% intervals from "
      'author draws within quarters. W: Wikipedia alone; R: platform record (metadata and earlier recordings); RW: both.', '',
      '| Model | Recordings | Quarters | Rows | W | R | RW | RW minus R | Spearman W / R / RW |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for k, v in res.items():
    if k.startswith('_'):
        continue
    mdl, part = k.split('|')
    a = v['auc']; d = v['auc_RW_minus_R']
    f = lambda x: f"{x['est']:.3f} ({x['lo']:.3f} to {x['hi']:.3f})"
    L_.append(f"| {mdl} | {'all' if part == 'all' else 'author with no earlier recording'} | {v['quarters']} ({v['first']} to {v['last']}) | {v['rows']:,} | "
              f"{f(a['W'])} | {f(a['R'])} | {f(a['RW'])} | {d['est']:+.3f} ({d['lo']:+.3f} to {d['hi']:+.3f}) | "
              f"{v['spearman']['W']:.3f} / {v['spearman']['R']:.3f} / {v['spearman']['RW']:.3f} |")
pathlib.Path(f'{D}/reports/librivox_new_recordings.md').write_text('\n'.join(L_) + '\n')
print('\n'.join(L_))
