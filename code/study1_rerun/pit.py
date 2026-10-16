"""Point-in-time narrator catalogue count.
For each recording: log1p(number of recordings by the same narrator released STRICTLY BEFORE this recording's
release time). The old features.py counted every recording the narrator ever made (including later ones)."""
import numpy as np, pandas as pd

def narrator_pit_count(narrator_id, release_time):
    """Return log1p(count of the same narrator's recordings with an earlier release time). NaN narrator or date gives 0."""
    df = pd.DataFrame({'n': pd.Series(narrator_id).reset_index(drop=True), 't': pd.to_datetime(pd.Series(release_time).reset_index(drop=True), utc=True)})
    out = np.zeros(len(df))
    ok = df.n.notna() & df.t.notna()
    for _, g in df[ok].groupby('n'):
        ts = np.sort(g.t.values.astype('datetime64[ns]').astype('int64'))
        out[g.index.values] = np.searchsorted(ts, g.t.values.astype('datetime64[ns]').astype('int64'), side='left')
    return np.log1p(out)
