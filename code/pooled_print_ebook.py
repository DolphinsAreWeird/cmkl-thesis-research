# Pooled synthetic-control effect by duration, main outcome formats only (print and ebook),
# next to the all-format pooling of study3 step 12. Same per-test effects, same bootstrap
# (2,000 resamples clustered by theme, seed 20261013). Descriptive check for the thesis text.
import pandas as pd, numpy as np
from config import ROOT
DATA = ROOT / "data"
d = pd.read_parquet(DATA / 'db/study3/shift_effects.parquet')
d = d[(d.analysis == 'main') & d.sc_ok.fillna(False) & d.sc_effect_p.notna()]
rng = np.random.default_rng(20261013)
def boot(x):
    g = x.groupby('node_id').sc_effect_p.agg(['sum', 'count']); s, c, k = g['sum'].values, g['count'].values, len(g)
    b = [s[i].sum() / c[i].sum() for i in (rng.integers(0, k, k) for _ in range(2000))]
    return len(x), k, x.sc_effect_p.mean(), *np.percentile(b, [2.5, 97.5])
rows = []
for name, fs in [('all formats', None), ('print + ebook', ['print', 'ebook'])]:
    for (src, lev, dc), x in d.groupby(['source', 'level', 'duration_class']):
        x = x if fs is None else x[x.format.isin(fs)]
        if len(x) >= 5: rows.append((name, src, lev, dc, *boot(x)))
t = pd.DataFrame(rows, columns=['formats', 'source', 'level', 'duration', 'tests', 'themes', 'mean', 'ci_low', 'ci_high']).round(3)
out = DATA / 'reports/pooled_print_ebook_check.md'
out.write_text('# Pooled effect by duration: all formats against print and ebook only\n\n'
    'Synthetic-control effect, months 0 to 2, log share; 95% interval from 2,000 resamples clustered by theme. '
    'The all-format rows reproduce the means of study3_12_shift_effects.md. Print and ebook are the main outcome.\n\n'
    + '| ' + ' | '.join(t.columns) + ' |\n|' + ' --- |' * len(t.columns) + '\n'
    + ''.join('| ' + ' | '.join(map(str, r)) + ' |\n' for r in t.itertuples(index=False)))
print(out); print(t[t.duration == 'sustained'].to_string(index=False))
