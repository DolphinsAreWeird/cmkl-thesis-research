# Simulated worlds for the tests: a demand panel and weekly interest series in the same layout as the real inputs.
# Demand follows y(t+1) = mu + phi (y(t) - mu) + beta s(t) + noise, where s(t) is the log of the mean weekly interest share over
# the 4 weeks that end at the last complete week of month t (exactly the W feature w_logmean4, centred). beta = 0 gives a
# null world in which interest is noise.
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import numpy as np, pandas as pd
import _features as FE

FIRST_WEEK = pd.Timestamp('2015-06-29')


def make_world(beta=1.0, seed=0, n_broad=2, n_mid=2, n_narrow=3, start='2016-01', end='2023-12', formats=('ebook',),
               missing=(), zero_share=(), with_gdelt=False, phi=0.5, noise=0.08, sd_week=0.35):
    rng = np.random.default_rng(seed)
    node_rows = []
    for b in range(n_broad):
        node_rows.append(dict(node_id=f'B{b + 1:02d}', level='broad', parent=None, broad_id=f'B{b + 1:02d}', label=f'Broad {b + 1}'))
        for m in range(n_mid):
            mid = f'B{b + 1:02d}.M{m + 1:02d}'
            node_rows.append(dict(node_id=mid, level='middle', parent=f'B{b + 1:02d}', broad_id=f'B{b + 1:02d}', label=f'Middle {b + 1}.{m + 1}'))
            for n in range(n_narrow):
                node_rows.append(dict(node_id=f'{mid}.N{n + 1:02d}', level='narrow', parent=mid, broad_id=f'B{b + 1:02d}',
                                      label=f'Narrow {b + 1}.{m + 1}.{n + 1}'))
    nodes = pd.DataFrame(node_rows)
    leaf = nodes[nodes.level == 'narrow'].node_id.tolist()
    # weekly interest (narrow nodes), AR(1) in logs
    weeks = pd.date_range(FIRST_WEEK, '2024-02-26', freq='7D')
    X = np.zeros((len(weeks), len(leaf)))
    for t in range(1, len(weeks)):
        X[t] = 0.8 * X[t - 1] + sd_week * rng.standard_normal(len(leaf))
    share = np.exp(X - 10.0)
    mids = nodes[nodes.level == 'middle'].node_id.tolist()
    # middle nodes' interest = mean of their narrow children
    cols = {n: share[:, i] for i, n in enumerate(leaf)}
    for m in mids:
        cols[m] = np.mean([cols[n] for n in leaf if n.startswith(m + '.')], axis=0)
    wiki = pd.concat([pd.DataFrame(dict(node_id=n, week=weeks, share=v, partial_week=False)) for n, v in cols.items()], ignore_index=True)
    wiki.loc[wiki.week == FIRST_WEEK, 'partial_week'] = True
    wiki['level'] = wiki.node_id.map(dict(zip(nodes.node_id, nodes.level))).map({'broad': 1, 'middle': 2, 'narrow': 3})
    wiki['source'] = 'wikipedia'
    # demand
    m0, m1 = FE.mi_of_ts(start + '-01'), FE.mi_of_ts(end + '-01')
    grid = np.arange(m0, m1 + 1)
    wk_index = {w: i for i, w in enumerate(weeks)}
    sig = {}
    for n in leaf:
        v = cols[n]
        s = []
        for mi in grid:
            L = FE.last_week_monday(mi)
            i = wk_index[L]
            s.append(np.log(v[i - 3:i + 1].mean()) + 10.0)
        sig[n] = np.array(s)
    ydem = {}
    for n in leaf:
        mu = -6.0 + rng.normal(0, 0.5)
        y = np.empty(len(grid)); y[0] = mu
        for k in range(len(grid) - 1):
            y[k + 1] = mu + phi * (y[k] - mu) + beta * sig[n][k] + noise * rng.standard_normal()
        ydem[n] = y
    for m in mids:
        ydem[m] = np.mean([ydem[n] for n in leaf if n.startswith(m + '.')], axis=0)
    rows = []
    miss = {FE.mi_of_ts(x + '-01') for x in missing}
    for f in formats:
        total = 10000 * np.exp(0.05 * rng.standard_normal(len(grid)))
        for n, y in ydem.items():
            lv = nodes.set_index('node_id').level[n]
            for k, mi in enumerate(grid):
                ok = mi not in miss
                ls = y[k] if ok else np.nan
                if (n, f, mi) in set(zero_share):
                    ls = np.nan
                rows.append((lv, n, nodes.set_index('node_id').broad_id[n], f, int(mi), ok, total[k] if ok else np.nan, ls, True))
    panel = pd.DataFrame(rows, columns=['level', 'node_id', 'broad_id', 'format', 'mi', 'month_ok', 'total_checkouts', 'log_share', 'size_ok'])
    panel['ym'] = [f'{m // 12:04d}-{m % 12 + 1:02d}' for m in panel.mi]
    shifts = empty_shifts()
    sw = empty_sw()
    gdelt = None
    if with_gdelt:
        gw = pd.date_range('2016-12-26', '2021-06-28', freq='7D')
        gd = []
        for n in leaf[:max(1, len(leaf) // 2)]:
            gd.append(pd.DataFrame(dict(node_id=n, week=gw, share=np.exp(rng.normal(-11, 0.3, len(gw))), tone=rng.normal(-1, 0.5, len(gw)),
                                        positive=rng.normal(3, 0.5, len(gw)), negative=rng.normal(4, 0.5, len(gw)), partial_week=False)))
        gdelt = pd.concat(gd, ignore_index=True)
        gdelt.loc[(gdelt.week == gw[0]) | (gdelt.week == gw[-1]), 'partial_week'] = True
        gdelt['source'] = 'gdelt'
    return dict(panel=panel, nodes=nodes, wiki=wiki, shifts=shifts, sw=sw, gdelt=gdelt, leaf=leaf)


def empty_shifts():
    return pd.DataFrame(dict(source=pd.Series(dtype=str), node_id=pd.Series(dtype=str), id=pd.Series(dtype=int),
                             start_week=pd.Series(dtype='datetime64[us]'), label=pd.Series(dtype=str),
                             label_week=pd.Series(dtype='datetime64[us]'), quality_ok=pd.Series(dtype=bool),
                             seasonal=pd.Series(dtype=bool), quality_flag=pd.Series(dtype=str)))


def empty_sw():
    return pd.DataFrame(dict(source=pd.Series(dtype=str), node_id=pd.Series(dtype=str), shift_id=pd.Series(dtype=int),
                             week=pd.Series(dtype='datetime64[us]'), ratio=pd.Series(dtype=float), phase=pd.Series(dtype=str)))


def add_shift(world, node, start, label, label_week, ratios, sid=0, source='wikipedia', quality_ok=True, seasonal=False, quality_flag=''):
    """Add one shift: `ratios` are the weekly ratios to normal from the start week on (the shift's own weeks)."""
    start = pd.Timestamp(start)
    sh = pd.DataFrame([dict(source=source, node_id=node, id=sid, start_week=start, label=label,
                            label_week=pd.Timestamp(label_week) if label_week is not None else pd.NaT, quality_ok=quality_ok,
                            seasonal=seasonal, quality_flag=quality_flag)])
    sh['start_week'] = sh.start_week.astype('datetime64[us]'); sh['label_week'] = sh.label_week.astype('datetime64[us]')
    wk = [dict(source=source, node_id=node, shift_id=sid, week=start + pd.Timedelta(weeks=i), ratio=r, phase='start' if i == 0 else 'in shift')
          for i, r in enumerate(ratios)]
    swn = pd.DataFrame(wk)
    swn['week'] = swn.week.astype('datetime64[us]')
    world['shifts'] = pd.concat([world['shifts'], sh], ignore_index=True)
    world['sw'] = pd.concat([world['sw'], swn], ignore_index=True)
    return world


def build(world, S, drop_missing_target=True, group='seattle'):
    return FE.build_features(world['panel'], world['nodes'], world['wiki'], world['shifts'], world['sw'], world['gdelt'], S, group,
                             drop_missing_target)
