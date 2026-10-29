# l05. Addendum l, step 4: the frozen forecasts of the blind test.  Settings: prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json,
# blind_test (read-only; SHA-256 checked).  H, HM, W14 and HMW14 (change D) and H, HM and HMW14 (level Y) are fitted with the backtest's
# settings (l04_backtest.py) on every row of the frame whose target month is 2026-08 or earlier, and rank every eligible sampled work and
# format at origin 2026-08 (target 2026-09).  Refuses to run if any month after 2026-08 has been downloaded (data/raw/modern/final_test/).
# Outputs: prereg/blind_l/forecasts_origin_2026-08.csv and forecasts_origin_2026-08_meta.json (their SHA-256 go into prereg/README.md and
#   the public repository before any month after 2026-08 is downloaded).
#   Run from code/:  ../.venv/bin/python main_study/wiki_led/l_books_in_time/l05_freeze.py
import sys, os, json, time, hashlib, pathlib, importlib.util
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from config import D as DATA_DIR                             # noqa: E402

DATA = pathlib.Path(DATA_DIR)
ROOT = DATA.parent
REC = ROOT / 'prereg' / 'addenda_wiki_led' / '2026-10-30_l_books_in_time.json'
assert hashlib.sha256(REC.read_bytes()).hexdigest() == '36778f86ced0550c90e8578813ae476c6ae1d4d7220c430ef140244e5d5e028a', 'addendum l changed'
NEW = DATA / 'raw' / 'modern' / 'final_test'
assert not NEW.exists() or not any(NEW.iterdir()), 'a month after 2026-08 has been downloaded: the blind test moves to origin 2026-09 (record, fallback)'
OUT = DATA / 'db' / 'wiki_led' / 'l_books_in_time'
FZ = ROOT / 'prereg' / 'blind_l'
FZ.mkdir(exist_ok=True)
CSV = FZ / 'forecasts_origin_2026-08.csv'
assert not CSV.exists(), 'forecasts already frozen; never overwritten'
T0 = time.time()
ORIGIN = 2026 * 12 + 7

# the backtest's settings and helpers, read from l04 without running it
src = (pathlib.Path(__file__).parent / 'l04_backtest.py').read_text()
head = src.split("R = pd.read_parquet(OUT / 'rows.parquet')")[0]
ns = {'__file__': str(pathlib.Path(__file__).parent / 'l04_backtest.py')}
exec(compile(head, 'l04_backtest.py (settings)', 'exec'), ns)
LGB, HC, HMC, W14C, FMTS = ns['LGB'], ns['HC'], ns['HMC'], ns['W14C'], ns['FMTS']

R = pd.read_parquet(OUT / 'rows.parquet')
R['format'] = R.format.astype(str)
R['fmt'] = R.format.map({f: i for i, f in enumerate(FMTS)}).astype('int8')
tr = R[R.mi + 1 <= ORIGIN].copy()                            # target month 2026-08 or earlier
te = R[R.mi == ORIGIN].copy()
assert te.D.isna().all() and len(te) > 0
import lightgbm as lgb                                       # noqa: E402


def fit(cols, target):
    cat = ['cal_month'] if 'cal_month' in cols else 'auto'
    return lgb.LGBMRegressor(**LGB).fit(tr[cols], tr[target], categorical_feature=cat).predict(te[cols])


out = te[['work_id', 'format', 'mi', 'L_t', 'M6', 'h_lt', 'h_m6', 'has_book_page', 'has_author_page']].copy()
out['origin'] = '2026-08'; out['target'] = '2026-09'
out['not_yet'] = ((te.h_lt - te.h_m6) < np.log(1.5)).astype(int)
out['naive_D'] = (te.h_lt - te.h_m6).to_numpy()
for name, cols in (('H', HC), ('HM', HMC), ('W14', W14C + ['fmt']), ('HMW14', HMC + W14C)):
    out[name + '_D'] = fit(cols, 'D')
for name, cols in (('H', HC), ('HM', HMC), ('HMW14', HMC + W14C)):
    out[name + '_Y'] = fit(cols, 'Y')
out = out.drop(columns=['mi']).sort_values(['format', 'work_id']).reset_index(drop=True)
out.to_csv(CSV, index=False, float_format='%.10g')
sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
meta = dict(record='prereg/addenda_wiki_led/2026-10-30_l_books_in_time.json', made=time.strftime('%Y-%m-%d %H:%M') + ' +06:30',
            made_utc=time.strftime('%Y-%m-%d %H:%M', time.gmtime()) + ' UTC', origin='2026-08', target='2026-09',
            training_rows=int(len(tr)), forecast_rows=int(len(out)), by_format=out.format.value_counts().to_dict(),
            rows_with_article_feature=int(((out.has_book_page == 1) | (out.has_author_page == 1)).sum()), csv_sha256=sha,
            no_month_after_2026_08=True, lightgbm_settings=LGB,
            columns='X_D: predicted change D = ln(1 + L(2026-09)) - ln(1 + M6); X_Y: predicted level ln(1 + L(2026-09)); naive_D: ln(1+L_t) - ln(1+M6)')
(FZ / 'forecasts_origin_2026-08_meta.json').write_text(json.dumps(meta, indent=1, default=str))
os.chmod(CSV, 0o444)
print(json.dumps(meta, indent=1, default=str))
print('meta sha256', hashlib.sha256((FZ / 'forecasts_origin_2026-08_meta.json').read_bytes()).hexdigest())
