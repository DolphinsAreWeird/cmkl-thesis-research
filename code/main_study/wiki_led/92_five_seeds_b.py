# 92. Five-seed rerun of the new-book test (Test B and the library models of its review), asked for by the advisor on 20 Nov 2026.
# Record: prereg/DEVIATIONS.md, "Five-seed reruns asked for by the advisor (20 November 2026)", part 1.2 (written before this ran).
# Runs part_b() of 90_robustness.py unchanged except LightGBM's random_state (20261020 to 20261024).  Files are tagged _fs<seed>
#   (db/wiki_led/robustness_b_preds_fs<seed>.parquet, robustness_part_b_fs<seed>.json); the stored files are not touched.
#   50 bootstrap draws (the point values used here do not depend on the draws; the bootstrap seed stays 20261020).
# Check: with seed 20261020 the refits must equal the stored predictions (test_b_preds.parquet; robustness_b_preds.parquet) to 1e-9.
# Output: data/reports/five_seeds_b.json
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/92_five_seeds_b.py
import sys, json, time, pathlib, importlib.util
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rob', HERE / '90_robustness.py')
rob = importlib.util.module_from_spec(spec)
sys.modules['rob'] = rob
spec.loader.exec_module(rob)                               # checks addendum e's SHA-256, sets nice(10)

SEEDS = [20261020 + i for i in range(5)]
OUT, REP = rob.OUT, rob.REP
rob.NB = 50
T0 = time.time()
res = dict(record='prereg/DEVIATIONS.md, Five-seed reruns asked for by the advisor (20 November 2026), part 1.2', seeds={}, check={})
KEEP = ['W_lgbm', 'L_lgbm', 'LW_lgbm', 'L0_lgbm', 'L0W_lgbm', 'Lq_lgbm', 'LqW_lgbm', 'Lp_lgbm', 'LpW_lgbm']
for seed in SEEDS:
    tag = f'_fs{seed}'
    fpart = OUT / f'robustness_part_b{tag}.json'
    if not fpart.exists() or 'writer_type' not in json.loads(fpart.read_text()).get('subsets', {}):
        rob.TAG = tag
        rob.LGB['random_state'] = seed
        rob.log('five seeds: seed', seed)
        rob.part_b()
    part = json.loads(fpart.read_text())
    if seed == SEEDS[0]:
        P = pd.read_parquet(OUT / f'robustness_b_preds{tag}.parquet')
        S1 = pd.read_parquet(OUT / 'test_b_preds.parquet', columns=['work_id', 'W_lgbm', 'L_lgbm', 'LW_lgbm'])
        S2 = pd.read_parquet(OUT / 'robustness_b_preds.parquet', columns=['work_id'] + KEEP)
        M1 = P[['work_id', 'W_lgbm', 'L_lgbm', 'LW_lgbm']].merge(S1, on='work_id', suffixes=('', '_s'), validate='one_to_one')
        M2 = P[['work_id'] + KEEP].merge(S2, on='work_id', suffixes=('', '_s'), validate='one_to_one')
        res['check'] = dict(rows=int(len(P)), vs_test_b={c: float((M1[c] - M1[c + '_s']).abs().max()) for c in ['W_lgbm', 'L_lgbm', 'LW_lgbm']},
                            vs_robustness_b={c: float((M2[c] - M2[c + '_s']).abs().max()) for c in KEEP}, matched=[int(len(M1)), int(len(M2))])
        rob.log('check against stored predictions', res['check'])
        assert len(M1) == len(M2) == len(P), 'rows differ'
        assert max(res['check']['vs_test_b'].values()) < 1e-9 and max(res['check']['vs_robustness_b'].values()) < 1e-9, 'seed 20261020 does not reproduce'
    res['seeds'][str(seed)] = {lab: dict(models={c: part['subsets'][lab]['models'][c]['spearman'] for c in KEEP},
                                         diffs={k: v['mean'] for k, v in part['subsets'][lab]['diffs'].items()})
                               for lab in ('all', 'matched', 'writer_type')}
    a = res['seeds'][str(seed)]['all']
    rob.log('seed', seed, 'W', round(a['models']['W_lgbm'], 4), 'LW-L', round(a['diffs']['LW_minus_L'], 4),
            'L0W-L0', round(a['diffs']['L0W_minus_L0'], 4), 'LqW-Lq', round(a['diffs']['LqW_minus_Lq'], 4))
res['runtime_s'] = round(time.time() - T0)
(REP / 'five_seeds_b.json').write_text(json.dumps(res, indent=1))
rob.log('done')
