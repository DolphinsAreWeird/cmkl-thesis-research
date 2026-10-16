"""Exploratory (theme level, outcomes already seen; not in any record): the Study 2R joint model on theme shifts.
Regress each theme shift's borrowing effect on log2(whole duration in weeks) and log2(whole peak ratio) together, bootstrap clustered by theme
(node) with 2,000 resamples, seed 20261013. Effects: Study 3 synthetic-control effect months 0 to +2 (sc_effect_p; Wikipedia, narrow and middle,
main non-seasonal analysis, per format), and Study 3b tau months 0 to +2 (tau_p; Seattle, Wikipedia, narrow and middle; value-level (book subject) shifts have no whole duration or peak in the interest table and are left out).
Whole duration and whole peak come from data/db/interest/shifts.parquet (joined on source, node and start week).
Writes data/reports/theme_size_vs_duration.md and theme_size_vs_duration.csv."""
import pathlib, sys, time
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[2]; D = ROOT / 'data'
B = 2000; SEED = 20261013
sh = pd.read_parquet(D / 'db/interest/shifts.parquet', columns=['source', 'node_id', 'start_week', 'whole_duration', 'whole_peak', 'level', 'label'])
sh = sh.rename(columns={'level': 'lvl_i', 'label': 'label_i'})


def prep(df, ycol):
    d = df.merge(sh.drop_duplicates(['source', 'node_id', 'start_week']), on=['source', 'node_id', 'start_week'], how='left', suffixes=('', '_i'))
    n0 = len(d)
    wd = d['whole_duration_i'] if 'whole_duration_i' in d else d['whole_duration']
    d['dur'] = pd.to_numeric(wd, errors='coerce'); d['peak'] = pd.to_numeric(d['whole_peak'], errors='coerce')
    d = d[np.isfinite(d[ycol]) & (d.dur >= 1) & (d.peak > 0)].copy()
    d['ld'] = np.log2(d.dur); d['lp'] = np.log2(d.peak); d['y'] = d[ycol].astype(float)
    return d, n0


def ols_boot(d, cl, label, rows, extra=''):
    x = np.column_stack([np.ones(len(d)), d.ld.to_numpy(), d.lp.to_numpy()]); y = d.y.to_numpy()
    codes, uniq = pd.factorize(d[cl]); K = len(uniq)
    XtX = np.zeros((K, 3, 3)); Xty = np.zeros((K, 3)); n_k = np.zeros(K)
    for k in range(K):
        m = codes == k; xk = x[m]; XtX[k] = xk.T @ xk; Xty[k] = xk.T @ y[m]; n_k[k] = m.sum()
    def solve(sx, sy):
        try:
            return np.linalg.solve(sx, sy)
        except np.linalg.LinAlgError:
            return np.full(3, np.nan)
    est = solve(XtX.sum(0), Xty.sum(0))
    rs = np.random.default_rng(SEED); bs = np.empty((B, 3))
    for b in range(B):
        idx = rs.integers(0, K, K)
        bs[b] = solve(XtX[idx].sum(0), Xty[idx].sum(0))
    ok = np.isfinite(bs).all(1); bs = bs[ok]
    # single-predictor fits for reference
    def one(col):
        xx = np.column_stack([np.ones(len(d)), d[col].to_numpy()]); return np.linalg.lstsq(xx, y, rcond=None)[0][1]
    rows.append(dict(set=label, tests=len(d), themes=K, b_dur=est[1], dur_lo=np.percentile(bs[:, 1], 2.5), dur_hi=np.percentile(bs[:, 1], 97.5),
                     b_peak=est[2], peak_lo=np.percentile(bs[:, 2], 2.5), peak_hi=np.percentile(bs[:, 2], 97.5),
                     p_dur_le0=(1 + (bs[:, 1] <= 0).sum()) / (len(bs) + 1), p_peak_le0=(1 + (bs[:, 2] <= 0).sum()) / (len(bs) + 1),
                     corr_ld_lp=float(np.corrcoef(d.ld, d.lp)[0, 1]), corr_coefs_boot=float(np.corrcoef(bs[:, 1], bs[:, 2])[0, 1]),
                     dur_alone=one('ld'), peak_alone=one('lp'), mean_y=float(y.mean())))


rows = []
# ---------------- Study 3 (synthetic control, months 0 to +2)
S3 = pd.read_parquet(D / 'db/study3/shift_effects.parquet')
S3 = S3[(S3.analysis == 'main') & (S3.source == 'wikipedia') & S3.level.isin(['narrow', 'middle']) & (S3.skip == '') & S3.sc_ok.astype(bool)]
S3 = S3.drop(columns=['size'], errors='ignore')
d3, n3 = prep(S3, 'sc_effect_p')
notes = [f'Study 3 rows (Wikipedia, narrow and middle, main analysis, tested, synthetic control ok): {len(S3)}; with a finite effect and a joined duration and peak: {len(d3)}.']
for fmt in ('print', 'ebook', 'audiobook', 'librivox'):
    g = d3[d3.format == fmt]; ols_boot(g, 'node_id', f'Study 3 SC, {fmt}', rows)
g = d3[d3.format.isin(['print', 'ebook'])]; ols_boot(g, 'node_id', 'Study 3 SC, print + ebook stacked', rows)
for lv in ('narrow', 'middle'):
    g = d3[(d3.format.isin(['print', 'ebook'])) & (d3.level == lv)]; ols_boot(g, 'node_id', f'Study 3 SC, print + ebook, {lv} only', rows)
g = d3[d3.format.isin(['print', 'ebook'])]; ols_boot(g, 'broad_id', 'Study 3 SC, print + ebook, clustered by broad theme', rows)
# ---------------- Study 3b (count event study tau, months 0 to +2)
S3b = pd.read_parquet(D / 'db/study3b/shift_effects.parquet')
S3b = S3b[(S3b.analysis == 'main') & (S3b.source == 'wikipedia') & (S3b.skip == '') & ~S3b.too_sparse.astype(bool) & ~S3b.y_zero.astype(bool) & S3b.level.isin(['narrow', 'middle'])]
S3b = S3b.drop(columns=['size'], errors='ignore')
d3b, n3b = prep(S3b, 'tau_p')
notes.append(f'Study 3b rows (Wikipedia, narrow and middle, main analysis, tested, not sparse, finite tau): {len(S3b)}; with duration and peak: {len(d3b)}.')
ols_boot(d3b, 'node_id', 'Study 3b tau, Seattle (all formats jointly)', rows)
for lv in ('narrow', 'middle'):
    ols_boot(d3b[d3b.level == lv], 'node_id', f'Study 3b tau, {lv} only', rows)
ols_boot(d3b, 'broad_id', 'Study 3b tau, clustered by broad theme', rows)
R = pd.DataFrame(rows); R.to_csv(D / 'reports/theme_size_vs_duration.csv', index=False)
print(R.round(3).to_string()); print(notes)
open(D / 'reports/_theme_notes.txt', 'w').write('\n'.join(notes))
