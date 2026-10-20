# 90c. Report of the corrected reruns (addendum e): original value, corrected value and difference for every headline number of
# Test A, the placebo, Test C and Test D, the decisions re-read on the corrected values, and the checks that the corrected runs used the
# same rows, settings and seeds.  Reads the stored result files of the original runs and of the corrected runs (suffix _c); fits nothing.
# Output: data/reports/wiki_led_corrected_reruns.md and wiki_led_corrected_reruns.json (every number of the tables).
#   python main_study/wiki_led/90c_corrected_reruns_report.py      (from code/, with ../.venv/bin/python)
import sys, json, pathlib, datetime, re
import numpy as np, pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
REP, DB = D / 'reports', D / 'db' / 'wiki_led'
TMP = D / 'interim' / 'wiki_led_panels_orig_recomputed'


def jl(name):
    return json.loads((REP / name).read_text())


A0, A1 = jl('wiki_led_test_a.json'), jl('wiki_led_test_a_c.json')
P0, P1 = jl('wiki_led_placebo_a.json'), jl('wiki_led_placebo_a_c.json')
C0, C1 = jl('wiki_led_test_c.json'), jl('wiki_led_test_c_c.json')
T0, T1 = jl('wiki_led_test_d.json'), jl('wiki_led_test_d_c.json')
CHK20 = (REP / 'wiki_led_features_check_c.md').read_text()
CHKF = jl('wiki_led_features_check_full_c.json')
ACC0, ACC1 = pd.read_csv(REP / 'wiki_led_test_a_accuracy.csv', index_col=0), pd.read_csv(REP / 'wiki_led_test_a_accuracy_c.csv', index_col=0)
AL0, AL1 = pd.read_csv(REP / 'wiki_led_test_a_alert_list.csv', index_col=[0, 1]), pd.read_csv(REP / 'wiki_led_test_a_alert_list_c.csv', index_col=[0, 1])
ACC0r = pd.read_csv(TMP / 'wiki_led_test_a_accuracy.csv', index_col=0)
AL0r = pd.read_csv(TMP / 'wiki_led_test_a_alert_list.csv', index_col=[0, 1])

CMP = []                                                                  # every compared number, for the json file


def nan(x):
    return x is None or (isinstance(x, float) and np.isnan(x))


def f(x, d=4):
    return 'n/a' if nan(x) else f'{x:.{d}f}'


def sf(x, d=4):
    return 'n/a' if nan(x) else f'{x:+.{d}f}'


def row(section, label, o, c, d=4):
    CMP.append(dict(section=section, label=label, original=None if nan(o) else float(o), corrected=None if nan(c) else float(c),
                    difference=None if nan(o) or nan(c) else float(c - o)))
    return [label, f(o, d), f(c, d), sf(c - o, d) if not (nan(o) or nan(c)) else 'n/a']


def ci(lo, hi, d=4):
    return f'[{f(lo, d)}, {f(hi, d)}]'


def table(header, rows, left=1):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join([' --- '] * left + [' ---: '] * (len(header) - left)) + '|']
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def yn(b):
    return 'yes' if b else 'no'


L = []
add = L.append
DECISIONS = []                                                            # (name, original, corrected)


def dec(name, o, c):
    DECISIONS.append((name, bool(o), bool(c)))
    return [name, yn(o), yn(c), 'no' if bool(o) == bool(c) else 'YES']


# ================================================================ same rows, settings and seeds
def same_cols(a, b, cols):
    bad = {}
    for c in cols:
        x, y = a[c].to_numpy(np.float64), b[c].to_numpy(np.float64)
        bad[c] = int((~((x == y) | (np.isnan(x) & np.isnan(y)))).sum())
    return bad


LIB = ['L_t', 'L_next', 'M6', 'h_lt', 'h_lt1', 'h_m6', 'h_m12', 'h_lyago', 'h_age', 'D', 'Sg', 'Y', 'mi', 'work_id', 'year']
WIKI = ['b_lvl4', 'b_r4', 'b_r1', 'b_rmax', 'b_nrise8', 'b_run', 'b_dw', 'b_chg', 'b_valid4', 'a_lvl4', 'a_r4', 'a_r1', 'a_rmax', 'a_nrise8', 'a_run', 'a_dw', 'a_chg', 'a_valid4']
Ra, Rb = pd.read_parquet(DB / 'test_a_rows.parquet'), pd.read_parquet(DB / 'test_a_rows_c.parquet')
rows_same = len(Ra) == len(Rb)
lib_bad = same_cols(Ra, Rb, LIB) if rows_same else {'rows': 1}
rows_ok = rows_same and sum(lib_bad.values()) == 0
share = lambda R_, c: float(R_[c].notna().mean())
sc0, sc1 = Ra[Ra.mi >= 2019 * 12], Rb[Rb.mi >= 2019 * 12]
Pa, Pb = pd.read_parquet(DB / 'test_a_preds.parquet'), pd.read_parquet(DB / 'test_a_preds_c.parquet')
key_same = len(Pa) == len(Pb) and bool((Pa.work_id.to_numpy() == Pb.work_id.to_numpy()).all() and (Pa.mi.to_numpy() == Pb.mi.to_numpy()).all())
nowiki = ['N0_D', 'N0_Y', 'Hnaive_D', 'Hnaive_Y', 'Hlgbm_D', 'Hlgbm_Y']
maxd_h = {c: float(np.abs(Pa[c].to_numpy(np.float64) - Pb[c].to_numpy(np.float64)).max()) for c in nowiki}
# independent recomputation of three headline change ranks from the saved predictions (per-month Spearman, averaged)
RECOMP = {}
for c in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D'):
    for tag, P_ in (('original', Pa), ('corrected', Pb)):
        RECOMP[(c, tag)] = float(np.mean([spearmanr(g[c], g.D).statistic for _, g in P_.groupby('mi')]))
del Ra, Rb
Da = pd.read_parquet(DB / 'test_d_rows.parquet', columns=['work_id', 'format', 'mi', 'L_t', 'L_next', 'M6', 'D', 'Sg', 'Y', 'h_lt', 'h_m6', 'loans12', 'b_lvl4', 'a_lvl4'])
Db = pd.read_parquet(DB / 'test_d_rows_c.parquet', columns=['work_id', 'format', 'mi', 'L_t', 'L_next', 'M6', 'D', 'Sg', 'Y', 'h_lt', 'h_m6', 'loans12', 'b_lvl4', 'a_lvl4'])
d_rows_same = len(Da) == len(Db) and bool((Da.work_id.to_numpy() == Db.work_id.to_numpy()).all() and (Da.mi.to_numpy() == Db.mi.to_numpy()).all()
                                          and (Da.format.astype(str).to_numpy() == Db.format.astype(str).to_numpy()).all())
d_lib_bad = same_cols(Da, Db, ['L_t', 'L_next', 'M6', 'D', 'Sg', 'Y', 'h_lt', 'h_m6', 'loans12']) if d_rows_same else {'rows': 1}
d_shares = dict(b0=float(Da.b_lvl4.notna().mean()), b1=float(Db.b_lvl4.notna().mean()), a0=float(Da.a_lvl4.notna().mean()), a1=float(Db.a_lvl4.notna().mean()))
n_d_rows = len(Db)
del Da, Db
Qa, Qb = pd.read_parquet(DB / 'test_d_preds.parquet', columns=['work_id', 'format', 'mi', 'H', 'naive', 'H_Y', 'naive_Y']), \
    pd.read_parquet(DB / 'test_d_preds_c.parquet', columns=['work_id', 'format', 'mi', 'H', 'naive', 'H_Y', 'naive_Y'])
dq_same = len(Qa) == len(Qb) and bool((Qa.work_id.to_numpy() == Qb.work_id.to_numpy()).all() and (Qa.mi.to_numpy() == Qb.mi.to_numpy()).all())
maxd_dh = {c: float(np.abs(Qa[c].to_numpy(np.float64) - Qb[c].to_numpy(np.float64)).max()) for c in ['H', 'naive', 'H_Y', 'naive_Y']} if dq_same else {}
del Qa, Qb
# Test C: same rows and the same reference forecasts (they do not use Wikipedia)
CREF = ['y_true', 'y_t', 'naive', 'seasonal_naive', 'revert6', 'chronos2', 'chronos2_cur', 'median_all']
Ca, Cb = pd.read_parquet(DB / 'test_c_preds.parquet'), pd.read_parquet(DB / 'test_c_preds_c.parquet')
c_rows_same = len(Ca) == len(Cb) and all(bool((Ca[k].astype(str).to_numpy() == Cb[k].astype(str).to_numpy()).all()) for k in ['format', 'level', 'node_id', 'origin_mi'])
c_ref_bad = same_cols(Ca, Cb, [c for c in CREF if c in Ca.columns]) if c_rows_same else {'rows': 1}
del Ca, Cb
# placebo: same scored rows, and the library-history predictions it carries are the same
PLa, PLb = pd.read_parquet(DB / 'placebo_a_preds.parquet', columns=['work_id', 'mi', 'D', 'Hlgbm_D']), pd.read_parquet(DB / 'placebo_a_preds_c.parquet', columns=['work_id', 'mi', 'D', 'Hlgbm_D'])
pl_rows_same = len(PLa) == len(PLb) and bool((PLa.work_id.to_numpy() == PLb.work_id.to_numpy()).all() and (PLa.mi.to_numpy() == PLb.mi.to_numpy()).all())
pl_bad = same_cols(PLa, PLb, ['D']) if pl_rows_same else {'rows': 1}
pl_maxd_h = float(np.abs(PLa.Hlgbm_D.to_numpy(np.float64) - PLb.Hlgbm_D.to_numpy(np.float64)).max()) if pl_rows_same else float('nan')
n_pl_rows = len(PLb)
del PLa, PLb

# ================================================================ header and what was corrected
WFc_ = pd.read_parquet(DB / 'test_a_wiki_features_c.parquet', columns=['kind', 'article'])
n_art_c = WFc_.groupby('kind').article.nunique().to_dict()
del WFc_
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
add('# Corrected reruns of Test A, the placebo, Test C and Test D (addendum e)')
add('')
add(f'Khant Phyo Wai, 01323050. Written {now} by `code/main_study/wiki_led/90c_corrected_reruns_report.py` from the stored result files of the original runs and of the corrected runs. '
    'It fits nothing. Rules: `prereg/addenda_wiki_led/2026-10-20_e_corrections_robustness.json` (fixed 20 Oct 2026 20:34 +07); the background is in `data/reports/wiki_led_code_audit_2026-10-20.md` (items A1, P1, C1) '
    'and `prereg/DEVIATIONS.md`, section "Wikipedia-led tests". The original runs and their files are untouched; every corrected file and job has the suffix `_c`.')
add('')
add('## 1. What was corrected, and how')
add('')
add('- **A1, weeks before an article existed.** In the weekly series of the book and author articles, the weeks before the article\'s first week with at least one view are now missing, not zero '
    '(the settings record says they are missing). In `article_features` (Test A, and through it the placebo and Test D) these weeks are removed before any rolling computation, so an origin month '
    'that falls before the first view has no features at all (all nine are missing), and every later feature is computed from the article\'s own weeks only. In Test C the same weeks are removed '
    'from the candidate series before the monthly means are made. Nothing else in the feature definitions changed.')
add('- **P1, placebo donors.** Books are sorted by their matching value (as in addendum b); each book in that order takes the nearest book in the order with a different author key, searching one step down, '
    'one step up, two steps down and so on; ties in the matching value are ordered by a fixed random order (seed 20261020); a donor serves at most 3 books. Two choices the addendum left open: books are '
    'processed in the sorted order, and a donor must also have a different book article (4 articles are shared by works with different creator strings; without this rule such a work could be given its own article).')
add('- **C1, time-safe candidates in Test C.** For test year Y the candidate book and author articles come only from works whose first Seattle loan (first month with loans in `counts_work.parquet`) is before 1 January of Y. '
    'The look-ahead version `Wsel_insample` (used only for C2) keeps the full pool, because it is the version that deliberately uses everything.')
add('')
add('Scripts (all in `code/main_study/wiki_led/`, each a copy of the original with only these changes, every one asserts the SHA-256 of its record and of addendum e and runs with `nice`): '
    '`10c_test_a.py`, `11c_placebo_a.py`, `20c_test_c.py`, `60c_test_d_rows.py`, `61c_test_d_models.py`, `13c_accuracy_alert_panels.py`, the checks `10c_check_features.py` and `20c_check_series.py`, and this report script. '
    f'Run times and peak memory of the corrected jobs: Test A {A1["runtime_s"]} s and {A1["peak_rss_mb"]:,} MB; placebo {P1["runtime_s"]} s and {P1["peak_rss_mb"]:,} MB; '
    f'Test C {C1["runtime_s"]} s and {C1["peak_rss_mb"]:,} MB; Test D models {T1["runtime_s"]} s and {T1["peak_rss_mb"]:,} MB (the Test D rows build prints its own footprint in `wiki_led_test_d_data_c.md`).')
add('')
add('### Same rows, settings and seeds')
add('')
n_rows_a = int(A1['n']['rows'])
add(f'- **Test A rows.** The rows of the corrected run are the rows of the original run: same number of rows ({"yes" if rows_same else "NO"}), and every library column (loans, M6, history features, D, surge flag, level, origin month, work, year) is identical '
    f'({"all 15 columns, 0 differing values" if rows_ok else "DIFFERENCES: " + str(lib_bad)}). Only the Wikipedia columns differ. Share of scored rows with a book-article feature: '
    f'{share(sc0, "b_lvl4"):.4f} original, {share(sc1, "b_lvl4"):.4f} corrected; with an author-article feature: {share(sc0, "a_lvl4"):.4f} original, {share(sc1, "a_lvl4"):.4f} corrected '
    '(the record\'s rule would give about 0.93 for the book articles).')
add(f'- **Models that do not use Wikipedia.** The predictions of N0, the naive repeat and the library-history LightGBM must not change. Largest absolute difference between the original and the corrected predictions: '
    + ', '.join(f'{c} {v:.2e}' for c, v in maxd_h.items()) + f' (same rows in the same order: {yn(key_same)}). Same seed, same settings, same walk-forward years.')
add(f'- **Test D rows.** {n_d_rows:,} rows in both files; same rows in the same order: {yn(d_rows_same)}; library columns with a differing value: {sum(d_lib_bad.values())}. Share of rows with a book-article feature: '
    f'{d_shares["b0"]:.4f} original, {d_shares["b1"]:.4f} corrected; with an author-article feature: {d_shares["a0"]:.4f} original, {d_shares["a1"]:.4f} corrected. '
    + ('Predictions of the models that do not use Wikipedia (H, naive): largest absolute difference ' + ', '.join(f'{c} {v:.2e}' for c, v in maxd_dh.items()) + '.' if maxd_dh else ''))
add(f'- **Test C rows.** Same rows (format, level, theme, origin) in the same order: {yn(c_rows_same)}; differing values in the target and in the forecasts that do not use Wikipedia (repeat last month, seasonal repeat, mean of 6 months, Chronos-2, Chronos-2 + concept pages, median): '
    f'{sum(c_ref_bad.values())}.')
add(f'- **Placebo rows.** {n_pl_rows:,} scored rows in both runs, same rows in the same order: {yn(pl_rows_same)}; differing values of the outcome D: {sum(pl_bad.values())}; '
    f'library-history predictions carried beside the placebo (from Test A): largest absolute difference {pl_maxd_h:.2e}.')
add('- **Recomputation from the saved predictions.** The change rank of W LightGBM, library history and history + Wikipedia, recomputed here from `test_a_preds.parquet` and `test_a_preds_c.parquet` '
    '(Spearman within each month, averaged over the 78 months): ' + '; '.join(f'{c.replace("_D", "")} {RECOMP[(c, "original")]:.4f} original, {RECOMP[(c, "corrected")]:.4f} corrected' for c in ('Wlgbm_D', 'Hlgbm_D', 'HWlgbm_D'))
    + '; the values in the tables below come from the result files and agree to four decimals: ' + yn(all(abs(RECOMP[(c, "original")] - A0["change_rank"][c]["mean"]) < 5e-5 and abs(RECOMP[(c, "corrected")] - A1["change_rank"][c]["mean"]) < 5e-5 for c in ("Wlgbm_D", "Hlgbm_D", "HWlgbm_D"))) + '.')
add('- **The corrected feature function.** On 20 articles (10 whose first view is in the first week of the data, 10 later) the corrected function gives exactly the original features for all 10 of the first group, in every origin month; '
    'the table is in `data/reports/wiki_led_features_check_c.md`. For every article, from the stored files (`wiki_led_features_check_full_c.md`): '
    f'the {CHKF["book"]["week1_articles"] + CHKF["author"]["week1_articles"]:,} articles whose first view is in the first week of the data have {CHKF["book"]["week1_rows"] + CHKF["author"]["week1_rows"]:,} origin-month rows, '
    f'of which {CHKF["book"]["week1_rows_differing"] + CHKF["author"]["week1_rows_differing"]} differ between the original and the corrected file; for the other articles the last row that differs by more than rounding is at most '
    f'{max(CHKF["book"]["weeks_after_first_view_of_last_difference_max"], CHKF["author"]["weeks_after_first_view_of_last_difference_max"]):.0f} weeks after the first view (median '
    f'{CHKF["book"]["weeks_after_first_view_of_last_difference_median"]:.0f}), the time the original needed to forget the zero weeks. The corrected file has {CHKF["rows_corrected"]:,} rows against '
    f'{CHKF["rows_original"]:,}: the {CHKF["rows_original"] - CHKF["rows_corrected"]:,} origin months before an article\'s first view no longer carry features; the corrected file has no row that the original lacks.')
add('')

# ================================================================ Test A
add('## 2. Test A (existing books): Wikipedia predicting next month\'s change')
add('')
add(f'Rows scored: {n_rows_a:,} (78 months, {A1["n"]["books"]:,} books, surge rate {A1["n"]["surge_rate"]:.4f}); the same in both runs. Difference = corrected minus original. Intervals are 95% month-block intervals of the corrected run.')
add('')
NAMES_D = {'Wrule_D': 'W rule (no fitting)', 'Wridge_D': 'W ridge', 'Wlgbm_D': 'W LightGBM', 'Hnaive_D': 'H naive (repeat last month)', 'Hlgbm_D': 'H LightGBM (library history)', 'HWlgbm_D': 'HW LightGBM (history + Wikipedia)'}
add('### Change rank (Spearman of predicted and actual next-month change, per month, averaged)')
add('')
rows = []
for k, nm in NAMES_D.items():
    r = row('test_a.change_rank', nm, A0['change_rank'][k]['mean'], A1['change_rank'][k]['mean'])
    rows.append(r + [ci(A1['change_rank'][k]['lo'], A1['change_rank'][k]['hi'])])
add(table(['model', 'original', 'corrected', 'difference', 'corrected 95% interval'], rows))
add('')
add('### Surge average precision, as a ratio to the base rate')
add('')
rows = []
for k, nm in NAMES_D.items():
    r = row('test_a.surge_ap_ratio', nm, A0['surge_ap'][k]['ratio'], A1['surge_ap'][k]['ratio'], 3)
    rows.append(r + [ci(A1['surge_ap'][k]['ratio_lo'], A1['surge_ap'][k]['ratio_hi'], 3)])
add(table(['model', 'original', 'corrected', 'difference', 'corrected 95% interval'], rows))
add('')
add('### Level of next month\'s borrowing (rank correlation within month, and mean absolute error of ln(1 + loans))')
add('')
NAMES_Y = {'N0_Y': 'N0 (average book)', 'Wridge_Y': 'W ridge', 'Wlgbm_Y': 'W LightGBM', 'Hnaive_Y': 'H naive (repeat last month)', 'Hlgbm_Y': 'H LightGBM', 'HWlgbm_Y': 'HW LightGBM'}
rows = []
for k, nm in NAMES_Y.items():
    r1 = row('test_a.level_rank', nm + ': level rank', A0['level'][k]['spearman'], A1['level'][k]['spearman'])
    r2 = row('test_a.level_mae', nm + ': MAE (log scale)', A0['level'][k]['mae'], A1['level'][k]['mae'])
    rows.append(r1 + [ci(A1['level'][k]['lo'], A1['level'][k]['hi'])])
    rows.append(r2 + [''])
add(table(['model and measure', 'original', 'corrected', 'difference', 'corrected 95% interval of the rank'], rows))
add('')
add('### Paired differences (by month, month-block interval)')
add('')
rows = []
for k, nm in (('HW_minus_H_change_rank', 'HW minus H, change rank (the gain of Wikipedia over library history)'),
              ('Wlgbm_minus_Wrule_change_rank', 'W LightGBM minus W rule, change rank')):
    r = row('test_a.paired', nm, A0['paired'][k]['mean'], A1['paired'][k]['mean'])
    rows.append(r + [ci(A0['paired'][k]['lo'], A0['paired'][k]['hi']), ci(A1['paired'][k]['lo'], A1['paired'][k]['hi'])])
add(table(['difference', 'original', 'corrected', 'change', 'original 95% interval', 'corrected 95% interval'], rows))
add('')
add('### The three decisions of the record')
add('')
rows = [dec('A1 (primary): W LightGBM change rank, interval above 0', A0['decisions']['A1_primary_W_alone_predicts_rises'], A1['decisions']['A1_primary_W_alone_predicts_rises']),
        dec('A2: HW minus H change rank, interval above 0', A0['decisions']['A2_W_adds_to_history'], A1['decisions']['A2_W_adds_to_history']),
        dec('A3: W LightGBM surge AP ratio, interval above 1', A0['decisions']['A3_W_flags_surges'], A1['decisions']['A3_W_flags_surges'])]
add(table(['decision', 'original', 'corrected', 'changed'], rows))
add('')

# ---------------------------------------------------------------- panels
add('### Accuracy panel (level predictions, 13_accuracy_alert_panels.py logic on the corrected predictions)')
add('')
MEAS = ['MAE_loans', 'median_err', 'WAPE', 'within_2', 'within_25pct', 'R2_log', 'rank_corr', 'direction_right', 'top10_hit']
NOWIKI_ROWS = ['No information (average book)', 'Repeat last month', 'Median of last 6 months', 'Library history (trees)']
WIKI_ROWS = ['Wikipedia only (ridge)', 'Wikipedia only (trees)', 'Library + Wikipedia (trees)']
maxd_acc = float(np.abs(ACC0.loc[NOWIKI_ROWS, MEAS].astype(float).to_numpy() - ACC1.loc[NOWIKI_ROWS, MEAS].astype(float).to_numpy()).max())
maxd_acc_r = float(np.abs(ACC0r.loc[:, MEAS].astype(float).to_numpy() - ACC0.loc[:, MEAS].astype(float).to_numpy()).max())
add(f'The four models that do not use Wikipedia (no information, repeat last month, median of the last 6 months, library history) are unchanged: largest absolute difference over all nine measures {maxd_acc:.2e}. '
    f'The stored original file and a recomputation of the original predictions with the same code agree to {maxd_acc_r:.1e}. The three models that use Wikipedia:')
add('')
rows = []
for m_ in WIKI_ROWS:
    for c in MEAS:
        rows.append(row('accuracy_panel', f'{m_}: {c}', ACC0.loc[m_, c], ACC1.loc[m_, c], 4))
add(table(['model and measure', 'original', 'corrected', 'difference'], rows))
add('')
add('### Alert lists (top 20 and top 50 books by predicted rise each month; share that rose at least 50% above M6, share that surged)')
add('')
tie = float(np.abs(AL0.to_numpy(float)[:, :2] - AL0r.to_numpy(float)[:, :2]).max()) if AL0.shape == AL0r.shape else float('nan')
add(f'The same code, run on the original predictions (`13c_accuracy_alert_panels.py --orig`), reproduces the stored original alert file with a largest difference of {tie:.1e} and the stored accuracy file with {maxd_acc_r:.1e}, '
    'so the original column below is the file written on 20 Oct 17:52 and the differences contain no change of method.')
add('')
rows = []
for (name, k) in AL1.index:
    for c, cn in (('rose', 'rose'), ('surged', 'surged'), ('months_beating_base', 'months beating the base rate')):
        o_s, cc = AL0.loc[(name, k), c], AL1.loc[(name, k), c]
        if nan(o_s) and nan(cc):
            continue
        rows.append(row('alert_list', f'{name}, top {k}: {cn}', o_s, cc, 4))
add(table(['list and measure', 'original', 'corrected', 'difference'], rows))
add('')

# ================================================================ placebo
add('## 3. Placebo: each book given another book\'s Wikipedia pages (corrected rows, P1 donors)')
add('')
p1 = P1['p1_donors']
n_pass2 = int(p1['recipients_second_pass'])                              # books matched on the author-article value
n_nodonor = int(A1['n']['books'] - P1['donors'])                         # books with neither matching value
def books(n):
    return f'{n:,} book' + ('' if n == 1 else 's')


add(f'Donors: {P1["donors"]:,} of the {A1["n"]["books"]:,} books have one (the other {books(n_nodonor)} have no Wikipedia feature at all, {P1["rows_without_donor"]} rows, and keep their own); {p1["donors_used"]:,} different donors are used, no donor serves more than {p1["max_books_per_donor"]} books '
    f'(donors by number of books served: {", ".join(f"{k}: {v:,}" for k, v in p1["donor_reuse_counts"].items())}). In the original run one donor served 1,564 books, 19% of the scored rows; now the most used donor has '
    f'{p1["rows_of_most_used_donor_scored"]:,} scored rows ({100 * p1["share_of_scored_rows_of_most_used_donor"]:.2f}%). The nearest donor in the order was found after a median of {p1["median_search_steps"]:.0f} '
    f'step{"" if p1["median_search_steps"] == 1 else "s"} (at most {p1["max_search_steps"]}); the median absolute gap in matching value is {p1["median_abs_gap_matching_value"]:.4f} (90th percentile {p1["p90_abs_gap_matching_value"]:.4f}). '
    f'The different-article rule changes the donor of {books(p1["recipients_whose_donor_changes_with_different_article_rule"])}; without it {books(p1["recipients_that_would_get_their_own_article_without_that_rule"])} would have been given its own article.')
add('')
rows = []
for k, nm in (('Wlgbm_D', 'W LightGBM, real pages'), ('pW_D', 'W LightGBM, placebo pages'), ('HWlgbm_D', 'HW LightGBM, real pages'), ('pHW_D', 'HW LightGBM, placebo pages'), ('Hlgbm_D', 'H LightGBM (library history)')):
    r = row('placebo.change_rank', nm + ': change rank', P0[k]['change_rank'], P1[k]['change_rank'])
    rows.append(r + [ci(P1[k]['lo'], P1[k]['hi'])])
for k, nm in (('Wlgbm_D', 'W LightGBM, real pages'), ('pW_D', 'W LightGBM, placebo pages'), ('HWlgbm_D', 'HW LightGBM, real pages'), ('pHW_D', 'HW LightGBM, placebo pages'), ('Hlgbm_D', 'H LightGBM')):
    r = row('placebo.surge_ap_ratio', nm + ': surge AP ratio', P0[k]['surge_ap_ratio'], P1[k]['surge_ap_ratio'], 3)
    rows.append(r + [''])
add(table(['model and measure', 'original', 'corrected', 'difference', 'corrected 95% interval'], rows))
add('')
rows = []
for k, nm in (('Wlgbm_D_minus_pW_D', 'W real minus W placebo, change rank'), ('HWlgbm_D_minus_pHW_D', 'HW real minus HW placebo, change rank'), ('pHW_D_minus_Hlgbm_D', 'HW placebo minus H, change rank')):
    r = row('placebo.differences', nm, P0[k]['mean'], P1[k]['mean'])
    rows.append(r + [ci(P0[k]['lo'], P0[k]['hi']), ci(P1[k]['lo'], P1[k]['hi'])])
add(table(['difference', 'original', 'corrected', 'change', 'original 95% interval', 'corrected 95% interval'], rows))
add('')
rows = []
for k, nm in (('Wlgbm_Y', 'W LightGBM, real pages'), ('pW_Y', 'W LightGBM, placebo pages')):
    for c, cn, d_ in (('mae_loans', 'MAE in loans', 3), ('wape', 'WAPE', 4), ('level_rank', 'level rank', 4)):
        rows.append(row('placebo.level', f'{nm}: {cn}', P0[k][c], P1[k][c], d_))
add(table(['model and measure', 'original', 'corrected', 'difference'], rows))
add('')
add('Reading rule of addendum b: the signal is specific to the book\'s own pages when the interval of "real minus placebo" lies above 0.')
add('')
rows = [dec('W real minus W placebo, interval above 0 (signal belongs to the book\'s own pages)', P0['Wlgbm_D_minus_pW_D']['lo'] > 0, P1['Wlgbm_D_minus_pW_D']['lo'] > 0),
        dec('HW real minus HW placebo, interval above 0', P0['HWlgbm_D_minus_pHW_D']['lo'] > 0, P1['HWlgbm_D_minus_pHW_D']['lo'] > 0)]
add(table(['reading', 'original', 'corrected', 'changed'], rows))
add('')

# ================================================================ Test C
add('## 4. Test C (themes): Wikipedia-only forecasts of theme changes, library-guided choice of articles (A1 and C1)')
add('')
c1c = C1['c1_check']
add(f'Rows scored: {C1["coverage"]["series"]} series, {C1["rank"]["Wsel_ridge"]["groups"]} groups; share of rows with a Wikipedia forecast {C0["coverage"]["rows_with_selection"]:.4f} original, '
    f'{C1["coverage"]["rows_with_selection"]:.4f} corrected. C1 check on the corrected selection: of {c1c["selected_book_articles"]:,} selected book articles {c1c["not_first_lent_before_test_year_book"]} and of '
    f'{c1c["selected_author_articles"]:,} selected author articles {c1c["not_first_lent_before_test_year_author"]} came only from works first lent on or after 1 January of the test year (the original run: 0.8% and 7.9%).')
add('')
NAMES_C = {'N0': 'N0 (no change; rank 0 by definition)', 'Wsel_ridge': 'Wsel ridge (Wikipedia only, library-chosen articles)', 'Wsel_index': 'Wsel index (no fitting)',
           'Wsel_insample': 'Wsel in-sample (look-ahead, for C2 only)', 'seasonal_naive': 'seasonal naive', 'revert6': 'mean of the last 6 months', 'chronos2': 'Chronos-2 alone',
           'chronos2_cur': 'Chronos-2 + concept pages', 'median_all': 'median of all months'}
rows = []
for k, nm in NAMES_C.items():
    r = row('test_c.rank', nm, C0['rank'][k]['mean'], C1['rank'][k]['mean'])
    rows.append(r + [ci(C0['rank'][k]['lo'], C0['rank'][k]['hi']), ci(C1['rank'][k]['lo'], C1['rank'][k]['hi'])])
add(table(['forecast (rank correlation of forecast and actual change)', 'original', 'corrected', 'difference', 'original 95% interval', 'corrected 95% interval'], rows))
add('')
add('The references (seasonal naive, mean of 6 months, Chronos-2, median) do not use Wikipedia and are the same rows in both runs; they are listed so that the Wikipedia rows can be read against them.')
add('')
rows = [row('test_c.avgrelmae', 'Wsel ridge level (y_t + forecast change), error ratio against repeating last month (AvgRelMAE)', C0['avgrelmae']['Wsel_ridge'], C1['avgrelmae']['Wsel_ridge'], 4),
        row('test_c.C2', 'C2: in-sample minus walk-forward rank (descriptive)', C0['decisions']['C2_lookahead'], C1['decisions']['C2_lookahead'], 4)]
add(table(['measure', 'original', 'corrected', 'difference'], rows))
add('')
rows = [dec('C1 (primary): Wsel ridge rank correlation, interval above 0', C0['decisions']['C1_primary'], C1['decisions']['C1_primary'])]
add(table(['decision', 'original', 'corrected', 'changed'], rows))
add('')

# ================================================================ Test D
add('## 5. Test D (all books by format): the Test A models on a 25% sample of all Seattle works plus the Test A works')
add('')
add(f'Rows scored: {sum(T1["n"].values()):,} (print {T1["n"]["print"]:,}, ebook {T1["n"]["ebook"]:,}, audiobook {T1["n"]["audiobook"]:,}), the same in both runs. Wikipedia features exist only for the Test A works '
    f'(book pages) and for works sharing their author; these are the features that changed.')
add('')
FM = ['print', 'ebook', 'audiobook', 'all']
MD = {'W': 'W (Wikipedia only)', 'H': 'H (library history)', 'HW': 'HW (history + Wikipedia)', 'naive': 'naive (repeat last month)'}
add('Base rates (same rows in both runs, so unchanged): share of rows that rose ' + ', '.join(f'{f_} {T1["base_rose"][f_]:.4f}' for f_ in FM)
    + '; share that surged ' + ', '.join(f'{f_} {T1["base_surge"][f_]:.4f}' for f_ in FM)
    + f'. Same in the original file: {yn(all(abs(T0["base_rose"][f_] - T1["base_rose"][f_]) < 1e-12 and abs(T0["base_surge"][f_] - T1["base_surge"][f_]) < 1e-12 for f_ in FM))}.')
add('')
for key_, title_, sec_ in (('alert', 'Alert hit rate: share of each month\'s top 20 and top 50 books (drawn within the format) that rose at least 50% above M6', 'test_d.alert'),
                           ('early', 'Early-warning hit rate: the same, among rows that had not yet risen (ln(1 + L_t) - ln(1 + M6) below ln 1.5)', 'test_d.early')):
    add(f'### {title_}')
    add('')
    rows = []
    for f_ in FM:
        for m_ in MD:
            k_ = f'{f_}|{m_}'
            r20 = row(f'{sec_}_top20', f'{f_}, {MD[m_]}', T0[key_][k_]['top20']['rose'], T1[key_][k_]['top20']['rose'])
            r50 = row(f'{sec_}_top50', f'{f_}, {MD[m_]}', T0[key_][k_]['top50']['rose'], T1[key_][k_]['top50']['rose'])
            rows.append(r20 + [ci(*T1[key_][k_]['top20']['ci'])] + r50[1:])
    add(table(['format and model', 'top 20 original', 'top 20 corrected', 'difference', 'corrected exact 95% interval', 'top 50 original', 'top 50 corrected', 'difference'], rows))
    add('')
add('### Accuracy of the level predictions in loans (models that predict the level; W has no level model in Test D)')
add('')
rows = []
for f_ in FM:
    for m_, nm_ in (('naive', 'naive (repeat last month)'), ('H', 'H (library history)'), ('HW', 'HW (history + Wikipedia)')):
        k_ = f'{f_}|{m_}'
        for c_, cn_, d_ in (('mae_loans', 'MAE in loans', 3), ('wape', 'WAPE', 4), ('within_25pct', 'within 25%', 4)):
            rows.append(row('test_d.accuracy', f'{f_}, {nm_}: {cn_}', T0['accuracy'][k_][c_], T1['accuracy'][k_][c_], d_))
add(table(['format, model and measure', 'original', 'corrected', 'difference'], rows))
add('')
add('### Change rank (Spearman of predicted and actual change within format and month, averaged) and surge AP ratio')
add('')
rows = []
for f_ in FM:
    for m_ in MD:
        rows.append(row('test_d.change_rank', f'{f_}, {MD[m_]}: change rank', T0['change_rank'][f'{f_}|{m_}'], T1['change_rank'][f'{f_}|{m_}']))
rows.append(row('test_d.paired', 'HW minus H, change rank (paired by month, all formats)', T0['HW_minus_H_change_rank']['mean'], T1['HW_minus_H_change_rank']['mean']))
for f_ in FM:
    for m_ in MD:
        rows.append(row('test_d.surge_ap_ratio', f'{f_}, {MD[m_]}: surge AP ratio', T0['surge_ap_ratio'][f'{f_}|{m_}'], T1['surge_ap_ratio'][f'{f_}|{m_}'], 3))
add(table(['format, model and measure', 'original', 'corrected', 'difference'], rows))
add('')
add(f'Paired HW minus H, change rank: original {ci(T0["HW_minus_H_change_rank"]["lo"], T0["HW_minus_H_change_rank"]["hi"])}, corrected {ci(T1["HW_minus_H_change_rank"]["lo"], T1["HW_minus_H_change_rank"]["hi"])}.')
add('')
add('### The 90% question (addendum d): is the HW top-20 hit rate at least 0.90?')
add('')
rows = []
for k in T1['q90']:
    o, c = T0['q90'][k], T1['q90'][k]
    CMP.append(dict(section='test_d.q90', label=k, original=o['hit_rate'], corrected=c['hit_rate'], difference=c['hit_rate'] - o['hit_rate']))
    DECISIONS.append((f'Test D q90: {k}', o['at_least_90'], c['at_least_90']))
    rows.append([k.replace('|', ', '), f'{o["slots"]:,}', f(o['hit_rate'], 4), ci(*o['ci'], 4), yn(o['at_least_90']), f(c['hit_rate'], 4), ci(*c['ci'], 4), yn(c['at_least_90']),
                 sf(c['hit_rate'] - o['hit_rate'], 4), 'no' if o['at_least_90'] == c['at_least_90'] else 'YES'])
add(table(['format, period', 'list slots', 'original hit rate', 'original interval', 'at least 0.90', 'corrected hit rate', 'corrected interval', 'at least 0.90', 'difference', 'answer changed'], rows))
add('')
FMT3 = ['print', 'ebook', 'audiobook']
q_each = {(tag, per): all(T_['q90'][f'{f_}|{per}']['at_least_90'] for f_ in FMT3) for tag, T_ in (('original', T0), ('corrected', T1)) for per in ('2019-2026', '2024-2026')}
for per in ('2019-2026', '2024-2026'):
    DECISIONS.append((f'Test D q90, every format at least 0.90, {per}', q_each[('original', per)], q_each[('corrected', per)]))
txt = ('Addendum d asks whether the rate is at least 0.90 in each format. Every format at least 0.90: '
       + '; '.join(f'{per}: {yn(q_each[("original", per)])} in the original run, {yn(q_each[("corrected", per)])} in the corrected run' for per in ('2019-2026', '2024-2026')) + '.')
flips = [k for k in T1['q90'] if T0['q90'][k]['at_least_90'] != T1['q90'][k]['at_least_90']]
for k in flips:
    o, c = T0['q90'][k], T1['q90'][k]
    ho, hc = int(round(o['hit_rate'] * o['slots'])), int(round(c['hit_rate'] * c['slots']))
    inside = (o['ci'][0] <= 0.9 <= o['ci'][1]) and (c['ci'][0] <= 0.9 <= c['ci'][1])
    txt += (f' The line that changes is {k.replace("|", ", ")}: {ho:,} of {o["slots"]:,} list slots rose in the original run and {hc:,} in the corrected run ({hc - ho:+d} slots), '
            f'which moves the rate from {o["hit_rate"]:.4f} to {c["hit_rate"]:.4f}, across 0.90; the exact 95% interval contains 0.90 in {"both runs" if inside else "only one run"}.')
add(txt)
add('')

# ================================================================ what changed
changed = [n for n, o, c in DECISIONS if o != c]
wl_o, wl_c = A0['change_rank']['Wlgbm_D']['mean'], A1['change_rank']['Wlgbm_D']['mean']
add('## 6. What changed, in plain English')
add('')
SUMMARY_PLACEHOLDER = '@@SUMMARY@@'
add(SUMMARY_PLACEHOLDER)
add('')
add('## 7. Choices made while coding (logged in `prereg/DEVIATIONS.md`, section "Wikipedia-led tests", entry of 20 Oct 2026 21:30 +07)')
add('')
add('The addendum fixes the three corrections; these are the points it left open. They were written into the scripts before the run that uses them (the scripts are saved under the `c` names) and were not changed after a result was seen.')
add('')
add(f'1. **A1, how "missing" is represented.** The weeks before the first week with views are removed from the weekly series before any rolling computation. An origin month that ends before the article has a complete week of views therefore has all nine features missing together '
    f'(not a mix of missing values and zero counts), which is what the record says and what removes the look-ahead group of author articles that appear later. An article with no view in any week up to the last origin month has no features: '
    f'{7427 - n_art_c["book"]} of the 7,427 book articles and {3001 - n_art_c["author"]} of the 3,001 author articles of Test A with weekly data (1 book and 2 author articles have no view at all; the others have their first view in the last weeks of the data). '
    'In an article\'s first months some features are still missing because their windows need data (r4, r1 and rmax need 13 weekly values before the last 4 weeks, chg needs 5 weeks), exactly as at the start of the original series.')
add('2. **P1, open points.** Books are processed in the sorted order (matching value, then the fixed random order). The random order is `numpy.random.default_rng(20261020).permutation` over the 7,747 work ids in ascending order. '
    f'A donor must also have a different book article than the recipient (this changes the donor of {p1["recipients_whose_donor_changes_with_different_article_rule"]} book). '
    f'The {n_pass2 + n_nodonor} books with no book-article matching value are matched on the author-article value in a second pass over the same rule ({n_pass2} books); '
    f'the other {n_nodonor} have neither value, have no Wikipedia feature in any row, and keep their own features, which are all missing ({P1["rows_without_donor"]} rows). '
    'The stepwise donor search is checked in the script against an independent brute-force search (identical donors).')
add('3. **C1, open points.** An article is a candidate in test year Y when at least one of the theme\'s works that carries it (strength at least 0.25 on that theme) had its first loan before 1 January of Y. '
    'The look-ahead version `Wsel_insample` keeps the full pool, as it is the version that uses everything on purpose. The concept-term series are not article series and are unchanged.')
add('4. **Test D rows, checks.** The data script checks the rows against fixed rules; two of them said "all b_ (or a_) features present or all missing". With corrected features an article\'s first months have some features missing, so these rules now read: features are missing for works without the page, and lvl4 is missing exactly when the whole set is.')
add('5. **Alert and accuracy panels.** The corrected panels are written by `13c_accuracy_alert_panels.py`, the same logic as `13_accuracy_alert_panels.py`. The original panels were also recomputed with this code (`--orig`, written to `data/interim/wiki_led_panels_orig_recomputed/`): '
    'they equal the stored original files exactly, so the differences in section 2 contain no change of method. (The code audit\'s own recomputation of the alert list had differed by up to 0.0007 because it ordered tied scores differently.)')
add('')
add('## 8. Not rerun here')
add('')
add('The live October list (frozen and published) is not changed; improvement rounds v1 and v2 keep their stored results and are labelled as run on the uncorrected features; Test B is unaffected (monthly author views, `matched_pre` already time-safe). '
    'The robustness checks R1 to R7 of addendum e are reported separately (`data/reports/wiki_led_robustness.md`), not here. Figures quoted in the results draft that are not stored in the result files compared above '
    '(for example the overlap of the Wikipedia and library lists, or the share of each list already up at the origin) are not recomputed here; the summary-checks task (`data/reports/handoff_summary_checks.md`) plans to report them for the original and the corrected files.')
add('')
add(f'Decisions compared: {len(DECISIONS)}; changed: {len(changed)}' + (' (' + '; '.join(changed) + ')' if changed else '') + '.')
add('')

def body(path):                                                          # a report file without its first heading line
    lines_ = path.read_text().split('\n')
    return '\n'.join(lines_[1:]).strip()


add('## Appendix: the checks of the corrected feature functions')
add('')
add('### A. The 20-article test of `article_features` (written before the Test A rerun was started)')
add('')
add(body(REP / 'wiki_led_features_check_c.md'))
add('')
add('### B. All articles, original and corrected feature files compared (after the rerun)')
add('')
add(body(REP / 'wiki_led_features_check_full_c.md'))
add('')
add('### C. Test C: the monthly candidate series, original and corrected')
add('')
add(body(REP / 'wiki_led_test_c_series_check_c.md'))
add('')

summary_file = REP / 'wiki_led_corrected_reruns_summary_c.txt'
summary = summary_file.read_text().strip() if summary_file.exists() else '(summary not written yet)'
text = '\n'.join(L).replace(SUMMARY_PLACEHOLDER, summary)
(REP / 'wiki_led_corrected_reruns.md').write_text(text + '\n')
(REP / 'wiki_led_corrected_reruns.json').write_text(json.dumps(dict(comparisons=CMP, decisions=[dict(decision=n, original=o, corrected=c, changed=o != c) for n, o, c in DECISIONS]), indent=1))
print('wrote', REP / 'wiki_led_corrected_reruns.md', '| comparisons', len(CMP), '| decisions', len(DECISIONS), '| changed', changed)
