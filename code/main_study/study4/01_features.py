# Step 01: the origin x category x format table (horizons 1 and 2, feature sets D, W, G, T) and a structural report.
# Reads the Study 3 demand panel and the interest series; applies the eligibility rule (the Study 3 minimum-size rule over
# the 24 months before the origin month, already stored as `size_ok` in the panel) at every origin.
# Writes data/db/study4/features.parquet and data/reports/study4_01_features.md (counts only, no target values).
#   .venv/bin/python 01_features.py
import sys, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _settings as ST
import _features as FE


def read_inputs():
    D = ST.DB
    panel = pd.read_parquet(D / 'study3' / 'demand_panel.parquet')
    nodes = pd.read_parquet(D / 'study3' / 'nodes.parquet')
    meta = json.loads((D / 'study3' / 'demand_panel_meta.json').read_text())
    wiki = pd.read_parquet(D / 'interest' / 'wiki' / 'weekly_node.parquet')
    gd = pd.read_parquet(D / 'interest' / 'gdelt' / 'weekly_node.parquet')
    sh = pd.read_parquet(D / 'interest' / 'shifts.parquet')
    sw = pd.read_parquet(D / 'interest' / 'shift_weekly.parquet')
    lv = D / 'study3' / 'demand_panel_librivox.parquet'
    lib = pd.read_parquet(lv) if lv.exists() else None
    return panel, nodes, meta, wiki, gd, sh, sw, lib


def check_panel(meta):
    """The panel must come from the fixed Study 3 record and the final taxonomy."""
    s3 = ST.PREREG / 'study3_settings_2026-10-13.json'
    if meta.get('development'):
        raise SystemExit('the demand panel is a development build (taxonomy v2 fallback); rebuild it first')
    if meta.get('settings_sha256') != ST.sha256_of(s3):
        raise SystemExit('the demand panel was built with a different Study 3 record than the one in prereg/')


def make_report(F, S, meta, n_dropped):
    L = ['# Study 4, step 01: feature table (structure only)', '',
         f'Built {time.strftime("%Y-%m-%d %H:%M")}. Record SHA-256 `{S.sha256}`. Demand panel build `{meta.get("build_id")}`. '
         'Counts only: this report holds no target values and no category-level demand.', '']
    t1, t2, t3 = ST.mi_from_ym(S.test_start), ST.mi_from_ym(S.gdelt_end) + 1, None
    F = F.copy()
    F['range'] = np.where(F.origin_mi < t1, 'before test (training only)',
                          np.where(F.origin_mi < t2, f'{S.test_start} to {S.gdelt_end}', f'{ST.ym_of(t2)} onward'))
    L += ['## Rows (origin x category x format x horizon; eligible at the origin, target month observed)', '']
    for h in S.horizons:
        L += [f'### Horizon {h}', '', '| Group | Format | Level | Origin range | Rows | Categories | Origins |', '| --- | --- | --- | --- | ---: | ---: | ---: |']
        sub = F[F.h == h]
        for (g, f, lv, rg), d in sub.groupby(['group', 'format', 'level', 'range']):
            L.append(f'| {g} | {f} | {lv} | {rg} | {len(d):,} | {d.node_id.nunique()} | {d.origin_mi.nunique()} |')
        L.append('')
    L += ['Rows dropped because the target month (or month t) is missing, closed or partial, or has a zero share '
          '(never scored): ' + ', '.join(f'horizon {h}: {n:,}' for h, n in n_dropped.items()) + '.', '']
    L += ['## Missing rate per feature', '',
          'Share of rows with a missing value, by origin range (all groups, horizon 1). Interest features are missing '
          'before the series have enough history, for categories without a series, and (GDELT) outside July 2017 to June 2021 '
          'or for categories GDELT does not cover. In the shift columns a missing value means no usable interest series; '
          '"no shift in the window" is 0.', '',
          '| Feature | ' + ' | '.join(sorted(F.range.unique())) + ' | All |', '| --- | ' + ' | '.join(['---:'] * (F.range.nunique() + 1)) + ' |']
    h1 = F[F.h == 1]
    num = FE.D_NUM + FE.W_NUM + FE.G_NUM + FE.T_NUM
    for c in num:
        cells = [f'{h1[h1.range == r][c].isna().mean():.3f}' for r in sorted(F.range.unique())]
        L.append(f'| {c} | ' + ' | '.join(cells) + f' | {h1[c].isna().mean():.3f} |')
    L += ['', '## Interest shift states (counts of rows, horizon 1)', '',
          '| Range | Rows with a Wikipedia shift in the last 8 weeks | of which a quality-ok shift (scoring split only) | Rows with a GDELT shift |', '| --- | ---: | ---: | ---: |']
    for r in sorted(F.range.unique()):
        d = h1[h1.range == r]
        L.append(f'| {r} | {int((d.w_shift8 == 1).sum()):,} | {int((d.split_qok_shift8 == 1).sum()):,} | {int((d.g_shift8 == 1).sum()):,} |')
    L += ['', '## Notes', '',
          '- Features at origin t use demand months up to t and interest weeks whose Sunday is on or before the last day of t.',
          '- `seasonal`, `quality_flag` and `title_confusion` are not used. `quality_ok` only sets the scoring split column '
          '`split_qok_shift8`, never a feature.',
          f'- Categorical columns: {", ".join(S.cat_features)}. No category id is a feature.', '']
    return '\n'.join(L)


def main():
    S = ST.settings()
    panel, nodes, meta, wiki, gd, sh, sw, lib = read_inputs()
    check_panel(meta)
    parts, dropped = [], {}
    for group, P in [('seattle', panel[panel.format.isin(S.seattle_formats)])] + ([('librivox', lib)] if lib is not None else []):
        t = time.time()
        full = FE.build_features(P, nodes, wiki, sh, sw, gd, S, group, drop_missing_target=False)
        for h in S.horizons:
            dropped[h] = dropped.get(h, 0) + int(((full.h == h) & ~full.target_ok).sum())
        parts.append(full[full.target_ok])
        print(f'{group}: {len(full):,} rows before dropping missing targets ({time.time() - t:.0f}s)', flush=True)
    F = pd.concat(parts, ignore_index=True)
    ST.OUT.mkdir(parents=True, exist_ok=True)
    F.to_parquet(ST.OUT / 'features.parquet', index=False)
    ST.REPORTS.mkdir(parents=True, exist_ok=True)
    (ST.REPORTS / 'study4_01_features.md').write_text(make_report(F, S, meta, dropped))
    print(f'wrote {ST.OUT / "features.parquet"} ({len(F):,} rows) and {ST.REPORTS / "study4_01_features.md"}')


if __name__ == '__main__':
    main()
