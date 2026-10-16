# Method benchmark, stage 2e: which stage-2 change-trained pipelines are run at horizons 2 and 3 (rule of addendum b, 2e_horizons.rule):
# (i) every pipeline in the 90% confidence set of the level task or of the rise task of comparison A2, or
# (ii) the pipeline with the lowest AvgRelMAE in A2 within each model (ridgechg, lgbmchg, catchg, chronos2 versions) and within each routing
#      (curated, top-500 embedding, context-reading, book-anchored, duration-weighted, demand-aligned).
# Chronos-2 variants already forecast all three horizons in one call, the Study 4b change models (D, DW, DWS) and the level models at horizon 3 exist; this script
# lists the missing change-trained (model, feature set) pairs and prints the commands for 10_change_models.py (it does not run them).
#   ../../../.venv/bin/python 17_leaders_h23.py
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'study4'))
import pandas as pd
import _settings as ST

RES = ST.DB / 'benchmark' / 'stage2_results'
MODELS = ('ridgechg', 'lgbmchg', 'catchg')
ROUTING = {'curated': (('DVcur', 'DW', 'DWS'), ['chronos2_cur']), 'top-500 embedding': (('DVtop',), ['chronos2_top']), 'context-reading': (('DVnli',), ['chronos2_nli']),
           'book-anchored': (('DVbk',), ['chronos2_bk']), 'duration-weighted': (('DVcurdw',), ['chronos2_curdw']), 'demand-aligned': (('DVdem',), [])}


def main():
    T = pd.read_csv(RES / 'A2_table.csv', index_col=0)
    T = T[~T.index.isin(['naive', 'seasonal_naive', 'revert6'])]
    lead = set(T[T.in_MCS_level.fillna(False).astype(bool) | T.in_MCS_rise.fillna(False).astype(bool)].index)
    why = {p: 'in a confidence set' for p in lead}

    def best(sub, tag):
        if len(sub):
            p = sub.AvgRelMAE.idxmin()
            lead.add(p); why.setdefault(p, tag)
    for m in MODELS:
        best(T[T.index.str.startswith(m + '_')], f'best {m}')
    best(T[T.index.str.startswith('chronos2')], 'best Chronos-2 version')
    for r, (fsets, extra) in ROUTING.items():
        ids = [f'{m}_{f}' for m in MODELS for f in fsets] + extra
        best(T[T.index.isin(ids)], f'best {r} routing')
    have3 = {'ridgechg_D', 'ridgechg_DW', 'ridgechg_DWS', 'catchg_D', 'catchg_DW', 'catchg_DWS'}      # Study 4b already has horizons 1 to 3 for these
    todo = sorted(p for p in lead if p.split('_')[0] in MODELS and p not in have3)
    by_fs = {}
    for p in todo:
        m, fs = p.split('_', 1)
        by_fs.setdefault(fs, []).append(m)
    print('Leaders for horizons 2 and 3:')
    for p in sorted(lead):
        print(f'  {p}: {why[p]}')
    print('\nChange-trained pipelines to run at horizons 2 and 3 (Chronos-2 variants and the 4b models need no run):')
    cmds = []
    for fs, ms in by_fs.items():
        cmds.append(f'10_change_models.py --models {",".join(sorted(ms))} --fsets {fs} --horizons 2,3 --tag h23_{fs} --workers 3')
        print('  ' + cmds[-1])
    json.dump(dict(leaders=sorted(lead), why=why, commands=cmds), open(RES / 'leaders_h23.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
