# Study 1 label-window check: walk-forward for labels L0, L2, L3, L4 with Ridge and CatBoost, three feature stages.
# Data preparation, features, quarters rule, model settings and metrics copy code/walkforward3_fix.py.
# usage (from code/):  python study1_label_check/run_check.py [--reproduce]
#   --reproduce : one quarter, the OLD label (log of summed views, months 2-7), Ridge only, printed beside the
#                 stored wf3fix result. A pipeline fidelity check; writes nothing.
import os
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[k] = '3'      # machine rule: at most 3 threads
import sys, json, time, warnings
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from catboost import CatBoostRegressor
from config import D, ROOT
import labels as LB

REPRO = '--reproduce' in sys.argv
PREREG = os.path.join(ROOT, 'prereg')
REC = os.path.join(PREREG, 'study1_label_check_2026-10-13.json')
ADD = os.path.join(PREREG, 'addenda_study1', '2026-10-13_a_partial_pooling_label.json')
sha = LB.verify_record(REC, LB.expected_hash_from_readme(os.path.join(PREREG, 'README.md')))
add = json.load(open(ADD)); assert add['results_seen'] is False
print('record hash ok', sha, '| addendum sha', LB.sha256_file(ADD), flush=True)
OUT = f'{D}/reports/study1_label_check'

# ---- data (as walkforward3_fix.py) ----
Lb = pd.read_parquet(f'{D}/processed/labels.parquet'); F = pd.read_parquet(f'{D}/processed/features.parquet')
GR = pd.read_parquet(f'{D}/processed/features_goodreads.parquet'); grp = json.load(open(f'{D}/processed/feature_groups.json'))
V = json.load(open(f'{D}/raw/ia_views_monthly.json')); E = np.load(f'{D}/interim/description_embeddings_minilm.npy')
m = Lb.merge(F, on='identifier').merge(GR, on='identifier', how='left')
m = m[(m.n_authors == 1) & (~m.author.isin(['Various', 'Unknown', 'Anonymous'])) & m.identifier.isin(V) & m.publicdate.notna()].copy()
m['rel_m'] = m.publicdate.dt.tz_localize(None).dt.to_period('M'); last = pd.Period('2026-08', 'M')
allrec = Lb[['identifier', 'narrator_id', 'publicdate']].dropna().sort_values('publicdate')
allrec['narr_pit'] = np.log1p(allrec.groupby('narrator_id').cumcount())
m = m.merge(allrec[['identifier', 'narr_pit']], on='identifier', how='left'); m['narr_count'] = m.narr_pit.fillna(0)
# same rows as the earlier run for the months 2-7 window (release from 2017-01, window complete); all later windows
# are complete for these titles too (checked below)
m = m[(m.rel_m >= pd.Period('2017-01', 'M')) & (m.rel_m + 7 <= last)].copy()
m = m.sort_values('rel_m').reset_index(drop=True)
assert (m.rel_m + 14 <= last).all(), 'some titles lack a complete months 9-14 window'
COUNTS, MOY = LB.build_panel([V[i] for i in m.identifier], list(m.rel_m))     # months 1..14, calendar month of months 1..12
EMB = E[m.emb_row.values]
rel_int = np.array([p.ordinal for p in m.rel_m]); last_int = last.ordinal
print('titles', len(m), flush=True)

def history(y, label_end):
    """Prior-label features, point in time (as walkforward3_fix.py): only titles whose window closed before this release."""
    d = {}
    for key, name in [('narrator_id', 'narr'), ('author', 'auth'), ('bookgroup', 'book')]:
        mean = np.full(len(m), np.nan); cnt = np.zeros(len(m))
        for k, g in m.groupby(key):
            e = label_end[g.index.values]; ys = y[g.index.values]
            for idx, r in zip(g.index, rel_int[g.index.values]):
                ok = (e < r) & ~np.isnan(ys)
                if ok.any(): mean[idx] = ys[ok].mean(); cnt[idx] = ok.sum()
        d[f'{name}_prior'] = mean; d[f'{name}_prior_n'] = np.log1p(cnt); d[f'{name}_has_prior'] = (cnt > 0).astype(int)
    return pd.DataFrame(d)

HISTCOLS = [f'{n}_{s}' for n in ('narr', 'auth', 'book') for s in ('prior', 'prior_n', 'has_prior')]
W = grp['META'] + grp['VOL'] + grp['TREND']; G = grp['GOODREADS']
STAGES = {'S0 metadata': (grp['META'], False), 'S4 +social+text': (W + G, True), 'S5 +history': (W + G + HISTCOLS, True)}
MODELS = ['Ridge', 'CatBoost']

def run_label(name, y_fun, wend, quarters, store, titles_out, stagesel=None, models=MODELS, only_q=None):
    """y_fun(q, qs, tr, te) -> (y over all titles, extra dict). Training = windows closed before the quarter starts."""
    label_end = rel_int + wend
    for q in quarters:
        qs = q.asfreq('M', 'start'); qe = q.asfreq('M', 'end')
        if only_q and str(q) != only_q: continue
        if qe.ordinal + wend > last_int: continue                      # window not complete for the whole quarter
        te = np.where((rel_int >= qs.ordinal) & (rel_int <= qe.ordinal))[0]; tr = np.where(label_end < qs.ordinal)[0]
        if len(te) < 30 or len(tr) < 300: print(name, q, 'skipped', len(te), len(tr), flush=True); continue
        t0 = time.time(); y, extra = y_fun(q, qs, tr, te)
        h = history(y, label_end); hm = h.copy()
        mm = pd.concat([m, hm], axis=1)
        top = (y[te] >= np.quantile(y[te], 0.8)).astype(int)
        pca = PCA(32, random_state=0).fit(EMB[tr]); k = max(1, int(0.1 * len(te)))
        for st, (cols, text) in (stagesel or STAGES).items():
            a = mm.loc[tr, cols].fillna(0).values.astype(float); b = mm.loc[te, cols].fillna(0).values.astype(float)
            if text: a = np.hstack([a, pca.transform(EMB[tr])]); b = np.hstack([b, pca.transform(EMB[te])])
            sc = StandardScaler().fit(a); P = {}
            P['Ridge'] = Ridge(10).fit(sc.transform(a), y[tr]).predict(sc.transform(b))
            if 'CatBoost' in models:
                ca = pd.DataFrame(a); cb = pd.DataFrame(b)
                if st == 'S5 +history':
                    ca['narr'] = m.narrator_id.values[tr].astype(str); cb['narr'] = m.narrator_id.values[te].astype(str)
                ca['g1'] = m.genre1.values[tr]; cb['g1'] = m.genre1.values[te]
                # thread_count=3 added for the machine rule; every other setting as in walkforward3_fix.py
                P['CatBoost'] = CatBoostRegressor(iterations=400, depth=6, learning_rate=0.05, verbose=0, random_seed=0, thread_count=3,
                                                  cat_features=[c for c in ['narr', 'g1'] if c in ca.columns]).fit(ca, y[tr]).predict(cb)
            for mdl, p in P.items():
                o = np.argsort(-p)[:k]; base_rate = (y[te] >= np.quantile(y[te], 0.9)).mean()
                store.append(dict(label=name, quarter=str(q), n_train=len(tr), n_test=len(te), stage=st, model=mdl,
                                  spearman=spearmanr(p, y[te]).correlation, auc_top20=roc_auc_score(top, p),
                                  hit_rate_top10=(y[te][o] >= np.quantile(y[te], 0.9)).mean(), hit_base=base_rate))
        if titles_out is not None:
            titles_out.append((q, te, extra))
        print(name, q, f'{time.time() - t0:.0f}s', flush=True)
    return store

QUARTERS = pd.period_range('2020Q1', '2024Q4', freq='Q')    # same grid as the earlier run; each label drops quarters whose window is incomplete

if REPRO:
    old = pd.read_csv(f'{D}/reports/wf3fix_full_m2to7.csv'); r = old[(old.quarter == '2020Q1') & (old.model == 'Ridge')]
    yold = np.log1p(COUNTS[:, 1:7].sum(1))
    rows = run_label('OLD', lambda q, qs, tr, te: (yold, {}), 7, QUARTERS, [], None, models=['Ridge'], only_q='2020Q1')
    print(pd.DataFrame(rows)[['stage', 'n_test', 'spearman', 'auc_top20', 'hit_rate_top10']].round(4).to_string())
    print(r[['stage', 'n_test', 'spearman', 'auc_top20', 'hit_rate_top10']].round(4).to_string()); sys.exit()

rows = []; step_cache = {}; titles = {'L3': [], 'L4': []}; params = []
def get_step(q, qs, tr, te):
    if str(q) not in step_cache:
        s = LB.step_labels(COUNTS, MOY, tr); step_cache[str(q)] = s
        params.append(dict(quarter=str(q), n_train=len(tr), theta=s['p4']['theta'], sigma_beta=s['p4']['sigma_beta'],
                           **{f'f{a}': s['p4']['f'][a - 1] for a in range(1, 13)}, **{f'g{k}': s['p4']['g'][k] for k in range(12)}))
        pd.DataFrame(params).to_csv(f'{OUT}_l4_params.csv', index=False)
    return step_cache[str(q)]
def save():
    pd.DataFrame(rows).to_csv(f'{OUT}_quarters.csv', index=False)

stat0 = np.log1p  # keep numpy imported name used
y0 = LB.label_L0(COUNTS); y2 = LB.label_L2(COUNTS)
for name, wend, fun in [('L0', 7, lambda q, qs, tr, te: (y0, {})), ('L2', 14, lambda q, qs, tr, te: (y2, {})),
                        ('L3', 12, lambda q, qs, tr, te: (get_step(q, qs, tr, te)['L3'], {})),
                        ('L4', 12, lambda q, qs, tr, te: (get_step(q, qs, tr, te)['L4'], {}))]:
    run_label(name, fun, wend, QUARTERS, rows, None); save()

# per-title test records for the label correlations and launch strength (labels as computed inside each step)
recs = []; corr = []
for q in QUARTERS:
    qs = q.asfreq('M', 'start'); qe = q.asfreq('M', 'end')
    if str(q) not in step_cache: continue
    te = np.where((rel_int >= qs.ordinal) & (rel_int <= qe.ordinal))[0]; s = step_cache[str(q)]
    df = pd.DataFrame(dict(identifier=m.identifier.values[te], quarter=str(q), year=q.year, L0=s['L0'][te], L2=s['L2'][te],
                           L3=s['L3'][te], L4=s['L4'][te], launch_strength=s['launch'][te], beta4=s['beta'][te],
                           views_m1_2=COUNTS[te, :2].sum(1), views_m1_12=COUNTS[te, :12].sum(1)))
    recs.append(df)
    c = df[['L0', 'L2', 'L3', 'L4']].corr(method='spearman'); c['quarter'] = str(q); corr.append(c.reset_index().rename(columns={'index': 'label'}))
pd.concat(recs).to_csv(f'{OUT}_titles.csv', index=False); pd.concat(corr).to_csv(f'{OUT}_label_corr_by_quarter.csv', index=False)

R = pd.DataFrame(rows)
S = R.groupby(['label', 'model', 'stage'])[['spearman', 'auc_top20', 'hit_rate_top10', 'hit_base']].mean().round(4)
S['n_quarters'] = R.groupby(['label', 'model', 'stage']).quarter.nunique(); S.to_csv(f'{OUT}_summary.csv')
print(S.to_string()); print('DONE', flush=True)
