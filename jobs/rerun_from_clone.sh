#!/bin/bash
# Rerun from a fresh copy of the public repository (prereg/DEVIATIONS.md, "Checks asked for by an outside review of the draft
# (19 November 2026)", part C). Not independent of the author.
#   1. clones https://github.com/DolphinsAreWeird/cmkl-thesis-research at COMMIT into a new folder;
#   2. makes a new environment from the clone's requirements.lock on Python 3.12 (uv);
#   3. copies the stored input tables of 30_test_b.py (new books) and l_books_in_time/l04_backtest.py (main set) into a separate data
#      folder and runs both scripts unchanged from the clone, with THESIS_DATA pointing there (the scripts read the settings records from
#      the clone's prereg/, linked beside that data folder);
#   4. compares every number of the rerun reports with the stored reports and the rerun predictions with the stored predictions, and
#      writes data/reports/rerun_from_clone.md and .json.
# Run from handoff/:  bash jobs/rerun_from_clone.sh      (about 20 minutes; COMMIT and WORK can be set in the environment)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMMIT="${COMMIT:-e3b3032}"
WORK="${WORK:-$ROOT/data/interim/rerun_from_clone}"
rm -rf "$WORK"; mkdir -p "$WORK"
echo "$(date '+%F %T %z') clone at $COMMIT"
git clone -q https://github.com/DolphinsAreWeird/cmkl-thesis-research "$WORK/repo"
git -C "$WORK/repo" checkout -q "$COMMIT"
echo "$(date '+%F %T %z') environment from requirements.lock"
uv venv -q -p 3.12 "$WORK/venv"
uv pip install -q -p "$WORK/venv/bin/python" -r "$WORK/repo/requirements.lock"
PY="$WORK/venv/bin/python"

DD="$WORK/data"
mkdir -p "$DD/db/wiki_led/l_books_in_time" "$DD/db/study3" "$DD/reports"
ln -s "$WORK/repo/prereg" "$WORK/prereg"                       # the scripts read ROOT/prereg with ROOT = parent of THESIS_DATA
cp "$ROOT/data/db/wiki_led/test_b_rows.parquet" "$ROOT/data/db/wiki_led/author_monthly_views.parquet" "$DD/db/wiki_led/"
cp "$ROOT/data/db/study3/demand_panel.parquet" "$DD/db/study3/"
cp "$ROOT/data/db/wiki_led/l_books_in_time/rows.parquet" "$DD/db/wiki_led/l_books_in_time/"
cp "$ROOT/data/db/wiki_led/test_d_preds_c.parquet" "$DD/db/wiki_led/"
cp "$ROOT/data/reports/wiki_led_test_d_c.json" "$DD/reports/"

cd "$WORK/repo/code"
echo "$(date '+%F %T %z') 30_test_b.py"
THESIS_DATA="$DD" bash "$ROOT/jobs/heavy_lock.sh" nice -n 10 "$PY" main_study/wiki_led/30_test_b.py > "$WORK/test_b.log" 2>&1
echo "$(date '+%F %T %z') l04_backtest.py"
THESIS_DATA="$DD" bash "$ROOT/jobs/heavy_lock.sh" nice -n 10 "$PY" main_study/wiki_led/l_books_in_time/l04_backtest.py > "$WORK/l04.log" 2>&1
echo "$(date '+%F %T %z') compare"

"$PY" - "$ROOT/data" "$DD" "$COMMIT" <<'PYEOF'
import sys, json, pathlib, platform
import numpy as np, pandas as pd
orig, new, commit = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
SKIP = {'runtime_s', 'peak_rss_mb'}


def leaves(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP:
                yield from leaves(v, f'{p}/{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f'{p}[{i}]')
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield p, float(x)


res, lines = dict(commit=commit, python=platform.python_version()), []
for rep in ('wiki_led_test_b.json', 'wiki_led_l_backtest.json'):
    a = dict(leaves(json.loads((orig / 'reports' / rep).read_text())))
    b = dict(leaves(json.loads((new / 'reports' / rep).read_text())))
    common = sorted(set(a) & set(b))
    d = np.array([abs(a[k] - b[k]) for k in common if np.isfinite(a[k]) and np.isfinite(b[k])])
    res[rep] = dict(numbers=len(common), only_stored=len(set(a) - set(b)), only_rerun=len(set(b) - set(a)),
                    max_abs_diff=float(d.max()) if len(d) else None, n_diff_over_1e9=int((d > 1e-9).sum()),
                    n_diff_over_5e4=int((d > 5e-4).sum()))
for name, path in (('test_b_preds', 'db/wiki_led/test_b_preds.parquet'), ('l_preds', 'db/wiki_led/l_books_in_time/preds.parquet')):
    a, b = pd.read_parquet(orig / path), pd.read_parquet(new / path)
    same_shape = a.shape == b.shape and list(a.columns) == list(b.columns)
    num = [c for c in a.columns if pd.api.types.is_float_dtype(a[c])] if same_shape else []
    md = {c: float(np.nanmax(np.abs(a[c].to_numpy(float) - b[c].to_numpy(float)))) for c in num}
    res[name] = dict(rows=len(a), same_shape=same_shape, max_abs_diff=max(md.values()) if md else None, by_column=md)
# the printed numbers of Table 5.1 (main set and new books)
tb = json.loads((new / 'reports' / 'wiki_led_test_b.json').read_text())['all']
lb = json.loads((new / 'reports' / 'wiki_led_l_backtest.json').read_text())['by_period']['2019-2026']['all']
printed = {'main set, Wikipedia alone': (lb['W14']['rank']['est'], '0.091'), 'main set, library model': (lb['HM']['rank']['est'], '0.347'),
           'main set, library and Wikipedia': (lb['HMW14']['rank']['est'], '0.352'),
           'main set, added by Wikipedia': (lb['_diff']['L2a_HMW14_minus_HM_rank']['est'], '0.005'),
           'new books, Wikipedia alone': (tb['W_lgbm']['spearman'], '0.127'), 'new books, library model': (tb['L_lgbm']['spearman'], '0.349'),
           'new books, library and Wikipedia': (tb['LW_lgbm']['spearman'], '0.372'), 'new books, added by Wikipedia': (tb['LW_minus_L']['mean'], '0.024')}
res['table_5_1'] = {k: dict(rerun=v, printed=p, match=f'{v:.3f}' == p) for k, (v, p) in printed.items()}
(orig / 'reports' / 'rerun_from_clone.json').write_text(json.dumps(res, indent=1))
L = ['# Rerun from a fresh copy of the public repository', '',
     f"Record: prereg/DEVIATIONS.md, 19 November 2026, part C. Repository commit `{commit}`, a new environment from `requirements.lock` "
     f"(Python {res['python']}), `30_test_b.py` and `l_books_in_time/l04_backtest.py` run unchanged on copies of their stored inputs. "
     'Not independent of the author.', '', '| Table 5.1 | Printed | Rerun | Same at printed precision |', '| --- | --- | --- | --- |']
L += [f"| {k} | {v['printed']} | {v['rerun']:.4f} | {'yes' if v['match'] else 'no'} |" for k, v in res['table_5_1'].items()]
L += ['', '| Output | Numbers or rows compared | Largest absolute difference | Differences above 1e-9 |', '| --- | --- | --- | --- |']
for rep in ('wiki_led_test_b.json', 'wiki_led_l_backtest.json'):
    r = res[rep]
    L.append(f"| report `{rep}` | {r['numbers']:,} numbers | {r['max_abs_diff']:.2e} | {r['n_diff_over_1e9']:,} |")
for name in ('test_b_preds', 'l_preds'):
    r = res[name]
    L.append(f"| predictions `{name}` | {r['rows']:,} rows (same shape: {'yes' if r['same_shape'] else 'no'}) | "
             f"{(r['max_abs_diff'] if r['max_abs_diff'] is not None else float('nan')):.2e} | |")
(orig / 'reports' / 'rerun_from_clone.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L))
PYEOF
echo "$(date '+%F %T %z') done"
