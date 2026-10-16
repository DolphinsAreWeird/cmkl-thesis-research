# Step 01 (Study 4b): the origin x category x format table for horizons 1, 2 and 3 with the D, W and S features, the change
# target and the surge label. Seattle formats only (LibriVox is not part of Study 4b).
# Takes the Study 4 feature table for h = 1, 2 (data/db/study4/features.parquet), builds h = 3 with the same Study 4 code
# from the Study 3 panel and the interest series, checks that the rebuilt h = 1, 2 rows equal the Study 4 table, and adds the
# S features, `change` = y - ls_t and `surge` = change >= log(1.3).
# Writes data/db/study4b/features.parquet and data/reports/study4b_01_features.md (counts only).
#   .venv/bin/python 01_features.py
import sys, json, copy, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _settings as ST
import _s4
import _b_features as BF

FE = _s4.features


def main():
    B = ST.settings()
    S4 = B.s4
    D = ST.DB
    panel = pd.read_parquet(D / 'study3' / 'demand_panel.parquet')
    nodes = pd.read_parquet(D / 'study3' / 'nodes.parquet')
    meta = json.loads((D / 'study3' / 'demand_panel_meta.json').read_text())
    if meta.get('development') or meta.get('settings_sha256') != ST.sha256_of(ST.PREREG / 'study3_settings_2026-10-13.json'):
        raise SystemExit('the demand panel is a development build or was built with another Study 3 record')
    wiki = pd.read_parquet(D / 'interest' / 'wiki' / 'weekly_node.parquet')
    shifts = pd.read_parquet(D / 'interest' / 'shifts.parquet')
    sw = pd.read_parquet(D / 'interest' / 'shift_weekly.parquet')
    effects = pd.read_parquet(D / 'study3' / 'shift_effects.parquet')
    F4 = pd.read_parquet(ST.S4_FEATURES)
    F4 = F4[F4.group == 'seattle']
    S4h = copy.copy(S4)
    S4h.horizons = B.horizons
    t = time.time()
    built = FE.build_features(panel[panel.format.isin(S4.seattle_formats)], nodes, wiki, shifts, sw, None, S4h, 'seattle', True)
    print(f'rebuilt {len(built):,} rows for h = {B.horizons} ({time.time() - t:.0f}s)', flush=True)
    BF.check_inputs(F4, built)
    print('rebuilt h = 1, 2 rows equal the Study 4 feature table', flush=True)
    keep = ['group', 'format', 'level', 'node_id', 'broad_id', 'origin_mi', 'origin', 'h', 'target_mi', 'tmonth', 'target_ok', 'y'] \
        + FE.D_NUM + ['m12_last', 'm12_prev'] + FE.W_NUM + ['split_qok_shift8', 'last_week']
    F = pd.concat([F4[keep], built[built.h == 3][keep]], ignore_index=True)
    F = BF.add_s_and_targets(F, shifts, effects, B)
    F = F.sort_values(['h', 'origin_mi', 'format', 'node_id']).reset_index(drop=True)
    ST.OUT.mkdir(parents=True, exist_ok=True)
    F.to_parquet(ST.OUT / 'features.parquet', index=False)
    ST.REPORTS.mkdir(parents=True, exist_ok=True)
    L = ['# Study 4b, step 01: feature table (structure only)', '',
         f'Built {time.strftime("%Y-%m-%d %H:%M")}. 4b record SHA-256 `{B.sha256}`; Study 4 record `{B.sha256_study4}`. Counts only: no target values.', '',
         '| Horizon | Format | Level | Rows | Categories | Origins | Share with surge label (training and test rows) | Rows with s_sustained = 1 | Rows with s_resp != 0 |',
         '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for (h, f, lv), d in F.groupby(['h', 'format', 'level']):
        L.append(f'| {h} | {f} | {lv} | {len(d):,} | {d.node_id.nunique()} | {d.origin_mi.nunique()} | {d.surge.mean():.4f} | '
                 f'{int((d.s_sustained == 1).sum()):,} | {int((d.s_resp != 0).sum()):,} |')
    L += ['', 'The rebuilt h = 1, 2 rows were checked equal to `data/db/study4/features.parquet` (D and W columns, targets).', '']
    (ST.REPORTS / 'study4b_01_features.md').write_text('\n'.join(L))
    print(f'wrote {ST.OUT / "features.parquet"} ({len(F):,} rows)')


if __name__ == '__main__':
    main()
