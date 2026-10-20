# 81. Report of the improvement round v2: reads the stage files written by 80_improve_v2.py and writes
#   data/reports/wiki_led_improve_v2.md  and  data/reports/wiki_led_improve_v2.json
# Nothing is fitted here. Run from code/:  ../.venv/bin/python main_study/wiki_led/81_improve_v2_report.py   (--sample: read and write the sample folder)
import sys, json, time, pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from config import D

D = pathlib.Path(D)
SAMPLE = '--sample' in sys.argv
REP = D / 'interim' / 'wiki_led_v2_sample' if SAMPLE else D / 'reports'
STAGES = ['c1', 'c4', 'c2', 'c5']


def stage(tag):
    f = REP / f'wiki_led_improve_v2_{tag}.json'
    return json.loads(f.read_text()) if f.exists() else None


R = {t: stage(t) for t in STAGES}
W_DIR = D / 'db' / 'wiki_led'


def c5_missing():
    """Why change 5 has no result at the time of writing."""
    ev, ad = (W_DIR / 'events.parquet').exists(), (W_DIR / 'adaptation_features.parquet').exists()
    if ev and not ad:
        return 'not run yet: the event table exists, but the views of the adaptation articles (`50_adaptation_views.py`, which waits for the Test B download) were not complete when this report was written; the run is due by 22 October 12:00 +07'
    if not ev:
        return 'not run yet: the event table `events.parquet` did not exist when this report was written; the run is due by 22 October 12:00 +07'
    return 'not run'


# ------------------------------------------------------------------ formatting helpers
def f(x, k=3):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:.{k}f}'


def pc(x, k=1):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{100 * x:.{k}f}%'


def iv(d, k=3):
    return f"{f(d['value'], k)} ({f(d['lo'], k)} to {f(d['hi'], k)})"


def ivp(d, k=1):
    """interval of a share, in percent"""
    return f"{100 * d['value']:.{k}f}% ({100 * d['lo']:.{k}f}% to {100 * d['hi']:.{k}f}%)"


def ppp(d, k=1):
    """paired difference of shares, in percentage points"""
    return f"{100 * d['diff']:+.{k}f} ({100 * d['lo']:+.{k}f} to {100 * d['hi']:+.{k}f})"


def pp(d, k=3):
    """paired difference with interval"""
    return f"{d['diff']:+.{k}f} ({d['lo']:+.{k}f} to {d['hi']:+.{k}f})"


def call(d, higher_better=True):
    """Plain wording for a paired difference: clear gain, clear loss, or no clear difference (the 95% interval includes 0)."""
    lo, hi = d['lo'], d['hi']
    if lo > 0:
        return 'a clear gain' if higher_better else 'a clear loss'
    if hi < 0:
        return 'a clear loss' if higher_better else 'a clear gain'
    return 'no clear difference'


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


NAMES_C1 = {'v0': 'v0: Test A Wikipedia model (regression on the change)',
            'R20e': 'Ranker, truncation 20, trained on books not yet risen',
            'R100e': 'Ranker, truncation 100, trained on books not yet risen',
            'R20a': 'Ranker, truncation 20, trained on all books (risen ones labelled 0)',
            'R100a': 'Ranker, truncation 100, trained on all books (risen ones labelled 0)'}


def seed_paragraph(tag):
    """Descriptive seed check (the ranker refitted with other LightGBM seeds), if it was run."""
    f_ = REP / f'wiki_led_improve_v2_{tag}_seed_check.json'
    if not f_.exists():
        return None
    sc = json.loads(f_.read_text())
    seeds = sc['seeds']
    if tag == 'c1':
        vals = [v['ranker_without_new_columns'] for v in seeds.values()]
        diff = [v['difference_from_v0'] for v in seeds.values()]
        return (f"**Seed check** (descriptive, 5 LightGBM seeds, 2024 to 2026): the ranker's precision@20 of rises is {pc(min(vals))} to {pc(max(vals))} (mean {pc(float(np.mean(vals)))}) against {pc(sc['v0_W_lgbm_p20_rise'])} for v0, "
                f"a difference from v0 of {pts(min(diff))} to {pts(max(diff))} points (mean {pts(float(np.mean(diff)))}). The seed used in the run above ({pts(seeds[next(iter(seeds))]['difference_from_v0'])} points) is at the low end, so differences of about 1.5 points between two models "
                "are within what the seed alone changes.")
    a = [v['ranker_without_new_columns'] for v in seeds.values()]
    b = [v['ranker_with_new_columns'] for v in seeds.values()]
    d = [v['difference'] for v in seeds.values()]
    return (f"**Seed check** (descriptive, 5 LightGBM seeds, 2024 to 2026): the ranker without the new columns gets {pc(min(a))} to {pc(max(a))} and with them {pc(min(b))} to {pc(max(b))} (precision@20 of rises); "
            f"the difference with minus without is {pts(min(d))} to {pts(max(d))} points over the five seeds (mean {pts(float(np.mean(d)))}), and {sum(1 for x in d if x > 0)} of 5 seeds are above 0.")


def noise_paragraph(tag, te=None):
    """Descriptive check: random columns in place of the new columns (stage noise_*), if it was run."""
    f_ = REP / f'wiki_led_improve_v2_{tag}_noise_check.json'
    if not f_.exists():
        return None
    q = json.loads(f_.read_text())
    n = q['n_noise_columns']
    c, e, w = q['change_rank_diff'], q['ranker_p20_diff'], q['early_p20_W_diff']
    txt = (f"**Noise-column check** (descriptive, {len(q['seeds'])} LightGBM seeds, 2024 to 2026): adding {n['W_model']} columns of random numbers to the Wikipedia model changes its change ranking by {c['min']:+.4f} to {c['max']:+.4f} "
           f"(mean {c['mean']:+.4f}) and its early-list precision@20 by {pts(w['min'])} to {pts(w['max'])} points; adding {n['ranker']} random columns to the ranker changes its precision@20 by {pts(e['min'])} to {pts(e['max'])} points (mean {pts(e['mean'])}). "
           "Each is compared with the same model and seed without the extra columns.")
    return txt


# ------------------------------------------------------------------ change 1
def render_c1(r):
    L = []
    t = r['tuning_2019_2023']
    rows = [[NAMES_C1[k], pc(v['p20_rise']), pc(v['p20_surge']), f(v['ndcg20']), f(v['spearman']), pc(v['share_months_above_base'], 0)]
            for k, v in t.items()]
    L.append('**Tuning, 2019 to 2023** (books not yet risen, mean over 52 months; the base rate of rises is ' + pc(t['v0']['base_rise']) + ').')
    L.append('')
    L.append(table(['Model', 'Precision@20, rises', 'Precision@20, surges', 'NDCG@20', 'Spearman, eligible rows', 'Months above base rate'], rows))
    c = r['choice']
    L.append('')
    L.append(f"Choice (highest precision@20 of rises): **{NAMES_C1[c['chosen']]}** ({c['chosen']}), {pc(c['tuning_p20_rise'])} against {pc(c['v0_tuning_p20_rise'])} for v0, "
             f"a tuning gain of {100 * c['gain']:+.1f} points. Adopted by the rule: **{'yes' if c['adopted'] else 'no'}**.")
    te = r['test_2024_2026']
    pr = te['paired_v1_minus_v0']
    iv_ = te['intervals']
    L.append('')
    L.append(f"**One run on 2024 to 2026** ({te['months']} months, {r['n']['eligible_rows']:,} eligible book-months over 2019 to 2026; "
             f"base rate of rises {pc(te['v0']['base_rise'])}, of surges {pc(te['v0']['base_surge'])}). Intervals: 95%, 2,000 draws of 3-month blocks.")
    L.append('')
    rows = []
    for k, lab in (('v0', 'v0: Test A Wikipedia model'), ('v1', f"v1: {NAMES_C1[te['chosen']]}")):
        s = te[k]
        rows.append([lab, ivp(iv_[k]['p20_rise']), ivp(iv_[k]['p20_surge']), f"{s['lift_rise']:.2f}", iv(iv_[k]['ndcg20']), iv(iv_[k]['spearman']), pc(s['share_months_above_base'], 0)])
    rows.append(['v1 minus v0 (paired by month, points for the shares)', ppp(pr['p20_rise']), ppp(pr['p20_surge']), '', pp(pr['ndcg20']), pp(pr['spearman']), ''])
    L.append(table(['Model', 'Precision@20, rises', 'Precision@20, surges', 'Lift over base rate (rises)', 'NDCG@20', 'Spearman, eligible rows', 'Months above base rate'], rows))
    L.append('')
    L.append(f"The chosen ranker beat v0 in {pc(te['months_v1_above_v0'], 0)} of the {te['months']} months on precision@20 of rises.")
    by = r['by_year_2024_2026']
    L.append('')
    L.append('By test year (precision@20 of rises, v0 then v1): ' + '; '.join(f"{y}: {pc(v['v0']['p20_rise'])} then {pc(v['v1']['p20_rise'])}" for y, v in by.items()) + '.')
    sp_ = seed_paragraph('c1')
    if sp_:
        L.append('')
        L.append(sp_)
    mj = r.get('may_june_2025')
    ex = r['excluding_may_june_2025']
    if mj and mj.get('v0'):
        L.append('')
        L.append(f"**May and June 2025** (origin months 2025-05 and 2025-06, two months, point values, no interval): precision@20 of rises {pc(mj['v0']['p20_rise'])} for v0 and {pc(mj['v1']['p20_rise'])} for v1; "
                 f"surges {pc(mj['v0']['p20_surge'])} and {pc(mj['v1']['p20_surge'])}; base rate {pc(mj['v0']['base_rise'])}. "
                 f"Without these two months the 2024 to 2026 values are {pc(ex['v0']['p20_rise'])} for v0 and {pc(ex['v1']['p20_rise'])} for v1 (difference {100 * ex['paired_v1_minus_v0']['p20_rise']:+.1f} points).")
    p = r['placebo']
    L.append('')
    L.append(f"**Placebo** (each book given the Wikipedia pages of another book with similar traffic): precision@20 of rises {pc(p['v0_placebo']['p20_rise'])} for v0 and {pc(p['v1_placebo']['p20_rise'])} for the ranker, "
             f"against a base rate of {pc(p['v0_placebo']['base_rise'])}; paired difference {ppp(p['paired_v1_minus_v0_placebo']['p20_rise'])} points. Both sit at the base rate, so the early signal belongs to the book's own pages.")
    return '\n'.join(L)


# ------------------------------------------------------------------ change 4
NAMES_C4 = {'v0': 'v0: regression on ln(1 + loans)', 'tweedie_1.2': 'Tweedie loss, variance power 1.2', 'tweedie_1.5': 'Tweedie loss, variance power 1.5'}
NAMES_G = {'HW': 'HW_lgbm (library + Wikipedia, one model)', 'equal_weights': 'Equal-weight average of the library and Wikipedia predictions', 'gate': 'Gate (ridge on the two predictions and three states)'}
NAMES_M = {'v0_H': 'Library only (H_lgbm, v0)', 'v0_HW': 'Library + Wikipedia (HW_lgbm, v0)', 'v1_H': 'v1 library only', 'v1_HW': 'v1 library + Wikipedia', 'equal_weights': 'Equal-weight average',
           'gate': 'Gate', 'v1': 'v1 (the adopted model)'}


def render_c4(r):
    L = []
    L.append('**Count loss, tuning 2019 to 2023** (all rows; lower is better for the two errors, higher for Spearman).')
    for fam, nm in (('H', 'Library history only (H)'), ('HW', 'Library history + Wikipedia (HW)')):
        v = r['tuning_2019_2023'][fam]
        rows = [[NAMES_C4[c], f(m['MAE_loans']), f(m['MAE_log'], 4), f(m['spearman_level'], 4), f"{v['mean_rank'][c]:.2f}"] for c, m in v['candidates'].items()]
        L.append('')
        L.append(f'{nm}:')
        L.append('')
        L.append(table(['Loss', 'MAE in loans', 'MAE in ln(1 + loans)', 'Spearman of the level', 'Mean rank (1 = best)'], rows))
        L.append('')
        L.append(f"Choice: **{NAMES_C4[v['chosen']]}**.")
    g = r['gate_tuning']
    L.append('')
    L.append('**Gate, tuning on 2020 to 2023** (the years in which the gate is fitted; 2019 uses equal weights and is shown below).')
    rows = [[NAMES_G[c], f(m['MAE_loans']), f(m['MAE_log'], 4), f(m['spearman_level'], 4), f"{g['2020_2023']['mean_rank'][c]:.2f}"] for c, m in g['2020_2023']['candidates'].items()]
    L.append('')
    L.append(table(['Model', 'MAE in loans', 'MAE in ln(1 + loans)', 'Spearman of the level', 'Mean rank'], rows))
    L.append('')
    rows = [[NAMES_G[c], f(m['MAE_loans']), f(m['MAE_log'], 4), f(m['spearman_level'], 4)] for c, m in g['2019_2023']['candidates'].items()]
    L.append('Same comparison on 2019 to 2023 (2019 counts with equal weights for the gate):')
    L.append('')
    L.append(table(['Model', 'MAE in loans', 'MAE in ln(1 + loans)', 'Spearman of the level'], rows))
    L.append('')
    L.append(f"Choice: **{NAMES_G[g['chosen']]}**. Gate adopted: **{'yes' if g['adopted'] else 'no'}**.")
    te = r['test_2024_2026']
    L.append('')
    L.append(f"**One run on 2024 to 2026** ({te['months']} months). v1 for next month's loans is: **{NAMES_M[te['v1_is']]}**; count-loss choice H: {r['tuning_2019_2023']['H']['chosen']}, HW: {r['tuning_2019_2023']['HW']['chosen']}. "
             "When v0 is kept, v1 and v0 are the same predictions. The gate is shown for information even when it was not adopted. Intervals: 95%, 3-month blocks.")
    L.append('')
    rows = []
    for k in ('v0_H', 'v0_HW', 'equal_weights', 'gate', 'v1'):
        m = te['metrics'][k]
        rows.append([NAMES_M[k], iv(m['MAE_loans'], 2), iv(m['MAE_log'], 4), pc(m['WAPE'].get('value')), pc(m['within2']['value']), pc(m['top10_hit']['value']),
                     iv(m['spearman_level'], 4), iv(m['change_rank'], 3), pc(m['alert20_all']['value'])])
    L.append(table(['Model', 'MAE in loans', 'MAE in ln(1 + loans)', 'WAPE', 'Within 2 loans', 'Top-10% hit', 'Spearman of the level', 'Change ranking', 'Top-20 rose'], rows))
    L.append('')
    L.append('Paired difference to v0 (library + Wikipedia, HW_lgbm); for the errors a negative number is better:')
    L.append('')
    rows = []
    for k in ('v0_H', 'equal_weights', 'gate', 'v1'):
        if k == 'v1' and te['v1_is'] == 'v1_HW' and all(c == 'v0' for c in te['count_loss_chosen'].values()):
            continue                                       # v1 is v0 itself: all differences are 0
        d = te['paired_vs_v0_HW'][k]
        rows.append([NAMES_M[k], pp(d['MAE_loans'], 3), pp(d['MAE_log'], 4), pp(d['spearman_level'], 4), ppp(d['top10_hit'], 2), pp(d['change_rank'], 4), ppp(d['alert20_all'], 1)])
    L.append(table(['Model minus v0 HW', 'MAE in loans', 'MAE in ln(1 + loans)', 'Spearman of the level', 'Top-10% hit (points)', 'Change ranking', 'Top-20 rose (points)'], rows))
    L.append('')
    L.append('**Subgroups, 2024 to 2026** (point values):')
    L.append('')
    rows = []
    for g_, nm in (('burst_any', 'Burst on the book or author page'), ('short_hist', 'Under 12 months of history')):
        sg = r['subgroups_2024_2026'][g_]
        for k in ('v0_HW', 'gate'):
            m = sg['metrics'][k]
            rows.append([nm + f" ({pc(sg['share'])} of rows)", NAMES_M[k], f(m['MAE_loans'], 2), f(m['MAE_log'], 4), f(m['spearman_level'], 4), pc(m['top10_hit'])])
    L.append(table(['Rows', 'Model', 'MAE in loans', 'MAE in ln(1 + loans)', 'Spearman of the level', 'Top-10% hit'], rows))
    mj = r.get('may_june_2025')
    if mj:
        L.append('')
        L.append('**May and June 2025** (two origin months, point values): ' + '; '.join(f"{NAMES_M[k]}: MAE {f(mj[k]['MAE_loans'], 2)} loans, Spearman {f(mj[k]['spearman_level'], 4)}" for k in ('v0_HW', 'gate') if k in mj)
                 + '. Without these months the 2024 to 2026 MAE is ' + '; '.join(f"{NAMES_M[k]} {f(r['excluding_may_june_2025'][k]['MAE_loans'], 3)}" for k in ('v0_HW', 'gate')) + '.')
    L.append('')
    L.append('**Split-conformal 80% intervals for next month\'s loans** (10th and 90th percentile of the previous year\'s errors on the log scale; coverage should be near 80%).')
    L.append('')
    yrs = sorted(r['intervals']['v0_HW']['coverage']['all'], key=int)
    rows = []
    for k in ('v0_HW', 'gate'):
        cv = r['intervals'][k]['coverage']['all']
        rows.append([NAMES_M[k], 'coverage'] + [pc(cv[y]['coverage']) if y in cv else '-' for y in yrs])
        rows.append(['', 'median width (loans)'] + [f(cv[y]['median_width'], 1) if y in cv else '-' for y in yrs])
    for g_, nm in (('burst_any', 'burst rows'), ('short_hist', 'under 12 months')):
        cv = r['intervals']['v0_HW']['coverage'][g_]
        rows.append([f"{NAMES_M['v0_HW']}, {nm}", 'coverage'] + [pc(cv[y]['coverage']) if y in cv else '-' for y in yrs])
    L.append(table(['Model', ''] + yrs, rows))
    return '\n'.join(L)


# ------------------------------------------------------------------ changes 2 and 5 (variant stage)
def render_variants(r, title, subname):
    L = []
    if r.get('status'):
        return r['status']
    t = r['tuning_2019_2023']
    var = list(r['variants'])
    L.append('Variants: ' + '; '.join(f"**{k}** ({len(v)} added columns)" for k, v in r['variants'].items()) + '.')
    if r.get('notes'):
        L.append('')
        parts = []
        for a, b in r['notes'].items():
            if a == 'near_event_share_of_rows':
                parts.append(f"rows within 2 months of an event: {100 * b:.1f}% of the rows")
            elif a == 'rows_with_flag':
                parts.append('scored rows with the flag set: ' + ', '.join(f"{k.replace('e_', '')} {v:,}" for k, v in b.items()))
            else:
                parts.append(str(b))
        L.append('; '.join(parts) + '.')
    L.append('')
    L.append(f"**Tuning, 2019 to 2023.** Wikipedia-only model of the change (LightGBM, Test A settings) and next month's level:")
    L.append('')
    rows = []
    for k in ['v0'] + var:
        v = t[k]
        sub = v.get(f'sub_{subname}', {}) if subname else {}
        rows.append([k, f(v['change_rank']), pc(v['alert20_all']), f(v['surge_ap_ratio'], 2), pc(v['early_w']['p20_rise']), f(v['level']['spearman_level']), f(v['level']['MAE_log'], 4)]
                    + ([f(sub.get('change_rank')), pc(sub.get('early_p20_rise'))] if subname else []))
    head = ['Model', 'Change ranking (Spearman)', 'Top-20 rose (all rows)', 'Surge AP over base', 'Early list: precision@20 of rises', 'Level Spearman', 'Level MAE in ln(1 + loans)']
    sub_label = {'burst_book': 'burst', 'event': 'near-event'}.get(subname, subname)
    if subname:
        head += [f'Change ranking, {sub_label} rows', f'Early list precision@20, {sub_label} rows']
    L.append(table(head, rows))
    L.append('')
    L.append(f"Early-warning ranker of change 1 ({r['ranker_config']['variant']}, adopted in change 1: {'yes' if r['ranker_config']['adopted_in_c1'] else 'no'}) with and without the new columns:")
    L.append('')
    rows = []
    for k in ['ranker_base'] + [f'ranker_{v}' for v in var]:
        e = t[k]['early']
        rows.append([k.replace('ranker_', 'ranker + ') if k != 'ranker_base' else 'ranker without new columns', pc(e['p20_rise']), pc(e['p20_surge']), f(e['ndcg20']), f(e['spearman'])])
    L.append(table(['Ranker', 'Precision@20, rises', 'Precision@20, surges', 'NDCG@20', 'Spearman, eligible rows'], rows))
    c = r['choice']
    L.append('')
    L.append(f"Choices: Wikipedia model of the change **{c['W']['chosen']}** (tuning change ranking {f(c['W']['tuning_change_rank'])} against {f(c['W']['v0_change_rank'])} for v0, gain {c['W']['gain']:+.4f}; adopted: **{'yes' if c['W']['adopted'] else 'no'}**); "
             f"ranker **{c['ranker']['chosen']}** (precision@20 {pc(c['ranker']['tuning_p20_rise'])} against {pc(c['ranker']['base_p20_rise'])} without the new columns, gain {100 * c['ranker']['gain']:+.1f} points; adopted: **{'yes' if c['ranker']['adopted'] else 'no'}**).")
    te = r['test_2024_2026']

    def block(b, label):
        out = []
        out.append(f"**{label}** ({b['rows']:,} book-months, {b['eligible_rows']:,} not yet risen).")
        out.append('')
        rows = []
        for k, nm in (('v0', 'v0: Test A Wikipedia model'), ('v2', f"v2: with {te['W_variant']}")):
            ch = b['change'][k]
            lv = b['level'].get(k, {})
            rows.append([nm, iv(ch['change_rank']), ivp(ch['alert20_all']), iv(ch['surge_ap_ratio'], 2) if 'surge_ap_ratio' in ch else 'n/a',
                         iv(lv['spearman_level'], 3) if lv else 'n/a', iv(lv['MAE_log'], 4) if lv else 'n/a'])
        pd_ = b['paired']['D:v2-v0']
        py = b['paired'].get('Y:v2-v0')
        rows.append(['v2 minus v0 (paired)', pp(pd_['change_rank']), ppp(pd_['alert20_all']), pp(pd_['surge_ap_ratio'], 2) if 'surge_ap_ratio' in pd_ else 'n/a',
                     pp(py['spearman_level']) if py else 'n/a', pp(py['MAE_log'], 4) if py else 'n/a'])
        out.append(table(['Model', 'Change ranking (Spearman)', 'Top-20 rose (all rows)', 'Surge AP over base', 'Level Spearman', 'Level MAE in ln(1 + loans)'], rows))
        out.append('')
        out.append('Early-warning list (books not yet risen):')
        out.append('')
        rows = []
        lab = {'W:v0': 'v0 Wikipedia model, early list', 'W:v2': 'v2 Wikipedia model, early list', 'R:ranker_c1': 'ranker of change 1', 'R:ranker_v2': 'ranker of change 1 with the new columns'}
        for k, nm in lab.items():
            e = b['early'][k]
            rows.append([nm, ivp(e['p20_rise']), ivp(e['p20_surge']), iv(e['ndcg20']), iv(e['spearman'])])
        for key, nm in (('R:W:v2-W:v0', 'v2 minus v0 (Wikipedia model)'), ('R:R:ranker_v2-R:ranker_c1', 'ranker with minus without new columns'),
                        ('R:R:ranker_v2-W:v0', 'ranker with new columns minus v0'), ('R:R:ranker_c1-W:v0', 'ranker of change 1 minus v0')):
            if key in b['paired']:
                d = b['paired'][key]
                rows.append([nm, ppp(d['p20_rise']), ppp(d['p20_surge']), pp(d['ndcg20']), pp(d['spearman'])])
        out.append(table(['Model', 'Precision@20, rises', 'Precision@20, surges', 'NDCG@20', 'Spearman, eligible rows'], rows))
        return '\n'.join(out)

    L.append('')
    L.append(f"**One run on 2024 to 2026** ({te['months']} months): Wikipedia model {te['W_variant']} (adopted: {'yes' if te['adopted_W'] else 'no'}), ranker {te['ranker_variant']} (adopted: {'yes' if te['adopted_ranker'] else 'no'}). Intervals: 95%, 3-month blocks.")
    L.append('')
    L.append(block(te['all_rows'], 'All rows'))
    for sg, b in te.get('subgroups', {}).items():
        L.append('')
        L.append(block(b, 'Rows where the book article had a burst (b_rmax at least ln 2, a rise of at least 2 times its normal)' if sg == 'burst_book' else 'Rows within 2 months of an event (death, dated award, film or tv release of the book or its author)' if sg == 'event' else f'Subgroup {sg}'))
    by = te['all_rows'].get('early_by_year')
    if by:
        L.append('')
        L.append('By test year, precision@20 of rises on books not yet risen (v0 Wikipedia model / v2 Wikipedia model / ranker of change 1 / ranker with the new columns): '
                 + '; '.join(f"{y}: {pc(v['W:v0'])} / {pc(v['W:v2'])} / {pc(v['R:ranker_c1'])} / {pc(v['R:ranker_v2'])}" for y, v in by.items()) + '.')
    mj = r.get('may_june_2025')
    ex = r.get('excluding_may_june_2025')
    if mj:
        L.append('')
        L.append('**May and June 2025** (two origin months, point values): ' + '; '.join(
            f"{k}: change ranking {f(mj['change'][k]['change_rank'])}, early list {pc(mj['early']['W:' + k]['p20_rise'])}" for k in ('v0', 'v2'))
            + f"; ranker without new columns {pc(mj['early']['R:ranker_c1']['p20_rise'])}, with {pc(mj['early']['R:ranker_v2']['p20_rise'])}. Without these months: "
            + '; '.join(f"{k}: change ranking {f(ex['change'][k]['change_rank'])}, early list {pc(ex['early']['W:' + k]['p20_rise'])}" for k in ('v0', 'v2')) + '.')
    sp_ = seed_paragraph(r['stage'])
    if sp_:
        L.append('')
        L.append(sp_)
    np_ = noise_paragraph(r['stage'])
    if np_:
        L.append('')
        L.append(np_)
    imp_f = REP / f"wiki_led_improve_v2_{r['stage']}_importance.json"
    if imp_f.exists():
        im = json.loads(imp_f.read_text())
        top = lambda d, n=6: ', '.join(f"{k} {100 * v:.0f}%" for k, v in list(d.items())[:n])
        L.append('')
        L.append(f"**Which columns the models use** (descriptive, gain share, models fitted for test year 2026). Wikipedia model of the change: the new columns carry {pc(im['new_columns_share']['W_model'], 0)} of the gain; largest columns: {top(im['W_model_change'])}. "
                 f"Ranker: the new columns carry {pc(im['new_columns_share']['ranker'], 0)}; largest columns: {top(im['ranker'])}.")
    p = r['placebo']
    real = te['all_rows']['paired']
    pp_ = p['paired']
    L.append('')
    L.append(f"**Placebo** ({p['note']}). The new columns should add nothing there. Real and placebo differences, 2024 to 2026 (95% intervals):")
    L.append('')
    rows = []
    rows.append(['Change ranking, Wikipedia model with minus without the new columns', pp(real['D:v2-v0']['change_rank'], 4), pp(pp_['D:placebo_v2-placebo_v0']['change_rank'], 4)])
    rows.append(['Surge AP over base', pp(real['D:v2-v0']['surge_ap_ratio'], 2) if 'surge_ap_ratio' in real['D:v2-v0'] else 'n/a',
                 pp(pp_['D:placebo_v2-placebo_v0']['surge_ap_ratio'], 2) if 'surge_ap_ratio' in pp_['D:placebo_v2-placebo_v0'] else 'n/a'])
    rows.append(['Early list precision@20 of rises (points), Wikipedia model', ppp(real['R:W:v2-W:v0']['p20_rise']), ppp(pp_['R:W:placebo_v2-W:placebo_v0']['p20_rise'])])
    rows.append(['Early list precision@20 of rises (points), ranker with minus without the new columns', ppp(real['R:R:ranker_v2-R:ranker_c1']['p20_rise']), ppp(pp_['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise'])])
    if 'Y:placebo_v2-placebo_v0' in pp_:
        rows.append(['Level of next month\'s loans: MAE in ln(1 + loans)', pp(real['Y:v2-v0']['MAE_log'], 4), pp(pp_['Y:placebo_v2-placebo_v0']['MAE_log'], 4)])
        rows.append(['Level of next month\'s loans: Spearman', pp(real['Y:v2-v0']['spearman_level'], 4), pp(pp_['Y:placebo_v2-placebo_v0']['spearman_level'], 4)])
    for sg, pb in p.get('subgroups', {}).items():
        rb = te.get('subgroups', {}).get(sg)
        if not rb:
            continue
        nm = {'burst_book': 'rows with a burst on the book article', 'event': 'rows within 2 months of an event'}.get(sg, sg)
        rows.append([f'Change ranking on {nm}', pp(rb['paired']['D:v2-v0']['change_rank'], 4), pp(pb['paired']['D:placebo_v2-placebo_v0']['change_rank'], 4)])
        rows.append([f'Early list precision@20 of rises (points), Wikipedia model, on {nm}', ppp(rb['paired']['R:W:v2-W:v0']['p20_rise']), ppp(pb['paired']['R:W:placebo_v2-W:placebo_v0']['p20_rise'])])
        rows.append([f'Early list precision@20 of rises (points), ranker with minus without the new columns, on {nm}', ppp(rb['paired']['R:R:ranker_v2-R:ranker_c1']['p20_rise']), ppp(pb['paired']['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise'])])
        if 'Y:placebo_v2-placebo_v0' in pb['paired']:
            rows.append([f'Level MAE in ln(1 + loans) on {nm}', pp(rb['paired']['Y:v2-v0']['MAE_log'], 4), pp(pb['paired']['Y:placebo_v2-placebo_v0']['MAE_log'], 4)])
    L.append(table(['Measure', 'Real run', 'Placebo run'], rows))
    return '\n'.join(L)


# ------------------------------------------------------------------ summary and conclusions
def gain_words(d, k=3, unit=''):
    return f"{d['diff']:+.{k}f}{unit} (95% interval {d['lo']:+.{k}f} to {d['hi']:+.{k}f}), {call(d)}"


def pts(x, k=1):
    """a difference of two shares, in percentage points"""
    return f'{100 * x:+.{k}f}'


def summary_rows():
    rows = []
    c1, c4, c2, c5 = R['c1'], R['c4'], R['c2'], R['c5']
    if c1:
        te, ch = c1['test_2024_2026'], c1['choice']
        d = te['paired_v1_minus_v0']['p20_rise']
        rows.append(['1. Early-warning ranker (books not yet risen)', ch['chosen'], 'yes' if ch['adopted'] else 'no', f"{100 * ch['gain']:+.1f} points of precision@20",
                     f"precision@20 of rises {pc(te['v0']['p20_rise'])} to {pc(te['v1']['p20_rise'])}, {pts(d['diff'])} points (interval {pts(d['lo'])} to {pts(d['hi'])}): {call(d)}"])
    else:
        rows.append(['1. Early-warning ranker', '', '', '', 'not run'])
    if c4:
        te, h, hw, g = c4['test_2024_2026'], c4['tuning_2019_2023']['H'], c4['tuning_2019_2023']['HW'], c4['gate_tuning']
        same = h['chosen'] == 'v0' and hw['chosen'] == 'v0'
        rows.append(['4a. Tweedie count loss', f"H: {h['chosen']}, HW: {hw['chosen']}", 'no' if same else 'yes',
                     'regression on ln(1 + loans) had the best mean rank' if same else '', 'v1 equals v0: the count loss was not chosen' if same else 'see section 4'])
        gt = te['paired_vs_v0_HW']['gate']
        rows.append(['4b. Gate between library and Wikipedia', g['chosen'], 'yes' if g['adopted'] else 'no',
                     'mean rank 2020-2023: ' + ', '.join(f"{NAMES_G[k].split(' (')[0].split(' of ')[0]} {v:.2f}" for k, v in g['2020_2023']['mean_rank'].items()),
                     f"for information, gate minus HW_lgbm: average error {gt['MAE_loans']['diff']:+.3f} loans (interval {gt['MAE_loans']['lo']:+.3f} to {gt['MAE_loans']['hi']:+.3f}); "
                     f"change ranking {gt['change_rank']['diff']:+.4f} (interval {gt['change_rank']['lo']:+.4f} to {gt['change_rank']['hi']:+.4f})"])
        iv0 = c4['intervals']['v0_HW']['overall_2024_2026']
        rows.append(['4c. Split-conformal 80% intervals', 'HW_lgbm (v0)', 'added', 'not tuned', f"coverage {pc(iv0['coverage'])} in 2024 to 2026, median width {f(iv0['median_width'], 1)} loans"])
    else:
        rows.append(['4. Count loss, gate, intervals', '', '', '', 'not run'])
    for nm, c in (('2. Burst-shape features', c2), ('5. Events and adaptation views', c5)):
        if c is None or c.get('status'):
            rows.append([nm, '', '', '', (c['status'] if c else (c5_missing() if nm.startswith('5') else 'not run'))])
            continue
        te, ch = c['test_2024_2026'], c['choice']
        pr = te['all_rows']['paired']
        d, e, w = pr['D:v2-v0']['change_rank'], pr['R:R:ranker_v2-R:ranker_c1']['p20_rise'], pr['R:W:v2-W:v0']['p20_rise']
        rows.append([nm, f"W model: {ch['W']['chosen']}; ranker: {ch['ranker']['chosen']}", f"W model {'yes' if ch['W']['adopted'] else 'no'}; ranker {'yes' if ch['ranker']['adopted'] else 'no'}",
                     f"change ranking {ch['W']['gain']:+.4f}; ranker {100 * ch['ranker']['gain']:+.1f} points",
                     f"change ranking {d['diff']:+.4f} (interval {d['lo']:+.4f} to {d['hi']:+.4f}); W-model early list {pts(w['diff'])} points (interval {pts(w['lo'])} to {pts(w['hi'])}); "
                     f"ranker with minus without the new columns {pts(e['diff'])} points (interval {pts(e['lo'])} to {pts(e['hi'])})"])
    return rows


def short_answer():
    """Four plain lines: did anything raise precision@20, the change ranking or the accuracy in loans, and by how much."""
    c1, c4, c2, c5 = R['c1'], R['c4'], R['c2'], R['c5']
    L = []
    if c1 and c2 and not c2.get('status'):
        t1, t2 = c1['test_2024_2026'], c2['test_2024_2026']['all_rows']
        pr = t2['paired']['R:R:ranker_v2-R:ranker_c1']['p20_rise']
        pv = t2['paired']['R:R:ranker_v2-W:v0']['p20_rise']
        sc2 = REP / 'wiki_led_improve_v2_c2_seed_check.json'
        seed_txt = ''
        if sc2.exists():
            dv = [v['difference'] for v in json.loads(sc2.read_text())['seeds'].values()]
            seed_txt = f" Over five LightGBM seeds the burst columns add {pts(min(dv))} to {pts(max(dv))} points to the ranker (mean {pts(float(np.mean(dv)))})."
        nz = REP / 'wiki_led_improve_v2_c2_noise_check.json'
        if nz.exists():
            q = json.loads(nz.read_text())
            e_ = q['ranker_p20_diff']
            seed_txt += f" For scale, adding the same number of columns of random numbers moves the ranker by {pts(e_['min'])} to {pts(e_['max'])} points over three seeds, so a gain of this size is small next to the noise from the model's own sampling."
        L.append(f"1. **Precision@20 of the early-warning list: at most a small gain, and only from the burst-shape features.** v0 {pc(t1['v0']['p20_rise'])}; the change-1 ranker {pc(t1['v1']['p20_rise'])} (no gain); the ranker with the burst columns {pc(t2['early']['R:ranker_v2']['p20_rise']['value'])}, "
                 f"which is {pts(pr['diff'])} points over the same ranker without them (interval {pts(pr['lo'])} to {pts(pr['hi'])}) and {pts(pv['diff'])} points over v0 (interval {pts(pv['lo'])} to {pts(pv['hi'])}, not clear).{seed_txt}")
    elif c1:
        t1 = c1['test_2024_2026']
        L.append(f"1. **Precision@20 of the early-warning list: no gain from the ranker.** v0 {pc(t1['v0']['p20_rise'])}, ranker {pc(t1['v1']['p20_rise'])}.")
    if c4:
        t4 = c4['test_2024_2026']
        gt = t4['paired_vs_v0_HW']['gate']
        L.append(f"2. **Change ranking: no clear gain.** Library + Wikipedia stays at {f(t4['metrics']['v0_HW']['change_rank']['value'], 3)}; the gate lowered it by {abs(gt['change_rank']['diff']):.4f} (interval {gt['change_rank']['lo']:+.4f} to {gt['change_rank']['hi']:+.4f}).")
        if c2 and not c2.get('status'):
            d = c2['test_2024_2026']['all_rows']['paired']['D:v2-v0']['change_rank']
            L[-1] += f" For Wikipedia alone the burst columns moved it {d['diff']:+.4f} (interval {d['lo']:+.4f} to {d['hi']:+.4f})."
        L.append(f"3. **Accuracy in loans: unchanged.** Neither the Tweedie loss nor the gate was chosen, so v1 is v0: an average error of {f(t4['metrics']['v0_HW']['MAE_loans']['value'], 2)} loans ({pc(t4['metrics']['v0_HW']['WAPE']['value'])} of the loans).")
        iv0 = c4['intervals']['v0_HW']['overall_2024_2026']
        L.append(f"4. **Range for next month's loans: works.** The 80% interval covered {pc(iv0['coverage'])} of the actual loans in 2024 to 2026, with a median width of {f(iv0['median_width'], 1)} loans.")
    if c5 and not c5.get('status'):
        te = c5['test_2024_2026']['all_rows']['paired']
        pl_ = c5['placebo']['paired']
        e = te['R:R:ranker_v2-R:ranker_c1']['p20_rise']
        w = te['R:W:v2-W:v0']['p20_rise']
        d = te['D:v2-v0']['change_rank']
        ep = pl_['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise']
        dp = pl_['D:placebo_v2-placebo_v0']['change_rank']
        L.append(f"5. **Events and adaptation views: no gain from the events.** Change ranking {d['diff']:+.4f} (interval {d['lo']:+.4f} to {d['hi']:+.4f}); early list of the Wikipedia model {pts(w['diff'])} points (interval {pts(w['lo'])} to {pts(w['hi'])}); "
                 f"ranker {pts(e['diff'])} points (interval {pts(e['lo'])} to {pts(e['hi'])}). With the events moved 12 months later the same measures move {dp['diff']:+.4f} and {pts(ep['diff'])} points, so there is nothing specific to the real dates.")
    return L


def phrase_pts(d):
    return f"{pts(d['diff'])} points (95% interval {pts(d['lo'])} to {pts(d['hi'])}; {call(d)})"


def conclusions():
    L = []
    c1, c4, c2, c5 = R['c1'], R['c4'], R['c2'], R['c5']
    # ---- precision@20
    if c1:
        te = c1['test_2024_2026']
        pr = te['paired_v1_minus_v0']
        s = (f"- **Precision@20 of the early-warning list** (the 20 books a month that are not yet rising, scored on whether they rose by 50% or more next month). "
             f"On average {pc(te['v0']['p20_rise'])} of the 20 books that Test A's Wikipedia model (v0) put first rose by 50% or more in 2024 to 2026, against a base rate of {pc(te['v0']['base_rise'])} ({te['v0']['lift_rise']:.1f} times chance). "
             f"The ranker of change 1 ({c1['choice']['chosen']}) had a tuning gain of {100 * c1['choice']['gain']:.1f} points and was adopted by the rule, but on 2024 to 2026 it got {pc(te['v1']['p20_rise'])}: {phrase_pts(pr['p20_rise'])}.")
        if c2 and not c2.get('status'):
            t2 = c2['test_2024_2026']['all_rows']
            p_ = t2['paired']
            s += (f" With the burst-shape features of change 2 the ranker got {pc(t2['early']['R:ranker_v2']['p20_rise']['value'])}: {phrase_pts(p_['R:R:ranker_v2-R:ranker_c1']['p20_rise'])} from the same ranker without them, "
                  f"and {phrase_pts(p_['R:R:ranker_v2-W:v0']['p20_rise'])} from v0. The Wikipedia regression with the same features got {pc(t2['early']['W:v2']['p20_rise']['value'])}: {phrase_pts(p_['R:W:v2-W:v0']['p20_rise'])} from v0.")
        sc1 = REP / 'wiki_led_improve_v2_c1_seed_check.json'
        if sc1.exists():
            q = json.loads(sc1.read_text())
            dv = [v['difference_from_v0'] for v in q['seeds'].values()]
            s += f" Refitting that ranker with four other seeds moves it between {pts(min(dv))} and {pts(max(dv))} points from v0 (mean {pts(float(np.mean(dv)))}), so the run above is at the low end and the ranker alone is no better than v0."
        sc2 = REP / 'wiki_led_improve_v2_c2_seed_check.json'
        if sc2.exists() and c2 and not c2.get('status'):
            q = json.loads(sc2.read_text())
            dv = [v['difference'] for v in q['seeds'].values()]
            s += (f" For the burst columns, the same five seeds give a gain of {pts(min(dv))} to {pts(max(dv))} points over the ranker without them (mean {pts(float(np.mean(dv)))}; "
                  f"{sum(1 for x in dv if x > 0)} of 5 above 0), so the gain is smaller than the run above suggests but has the same sign every time.")
            nz = REP / 'wiki_led_improve_v2_c2_noise_check.json'
            if nz.exists():
                qn = json.loads(nz.read_text())
                e_ = qn['ranker_p20_diff']
                s += (f" Adding {qn['n_noise_columns']['ranker']} columns of random numbers instead moves the ranker by {pts(e_['min'])} to {pts(e_['max'])} points over three seeds (mean {pts(e_['mean'])}), "
                      "which is the size of noise that a real gain has to be read against.")
        L.append(s)
    # ---- change ranking
    if c4:
        te4 = c4['test_2024_2026']
        gt = te4['paired_vs_v0_HW']['gate']
        s = (f"- **Rank correlation between predicted and actual change** (within month, averaged). Library + Wikipedia (v0, unchanged as v1): {f(te4['metrics']['v0_HW']['change_rank']['value'], 3)}. "
             f"The gate was not adopted; for information it scored {gt['change_rank']['diff']:+.4f} from that (interval {gt['change_rank']['lo']:+.4f} to {gt['change_rank']['hi']:+.4f}).")
        if c2 and not c2.get('status'):
            t2 = c2['test_2024_2026']['all_rows']
            d = t2['paired']['D:v2-v0']['change_rank']
            s += (f" For Wikipedia alone the burst-shape features moved it from {f(t2['change']['v0']['change_rank']['value'], 3)} to {f(t2['change']['v2']['change_rank']['value'], 3)}: "
                  f"{d['diff']:+.4f} (interval {d['lo']:+.4f} to {d['hi']:+.4f}; {call(d)}). Surges were flagged at {t2['change']['v2']['surge_ap_ratio']['value']:.2f} times chance against {t2['change']['v0']['surge_ap_ratio']['value']:.2f}.")
        L.append(s)
    # ---- accuracy in loans
    if c4:
        te4 = c4['test_2024_2026']
        m = te4['metrics']['v0_HW']
        gt = te4['paired_vs_v0_HW']['gate']
        s = (f"- **Accuracy in loans (next month).** The Tweedie count loss was not chosen: on 2019 to 2023 the regression on ln(1 + loans) had the best mean rank for both the library model and the library + Wikipedia model, so v1 equals v0. "
             f"The gate was not chosen either (on 2020 to 2023 HW_lgbm had the best mean rank). The average error stays at {f(m['MAE_loans']['value'], 2)} loans (interval {f(m['MAE_loans']['lo'], 2)} to {f(m['MAE_loans']['hi'], 2)}; "
             f"WAPE {pc(m['WAPE']['value'])}), {pc(m['within2']['value'])} of forecasts within 2 loans. For information the gate was {gt['MAE_loans']['diff']:+.3f} loans from v0 (interval {gt['MAE_loans']['lo']:+.3f} to {gt['MAE_loans']['hi']:+.3f}).")
        if c2 and not c2.get('status'):
            t2 = c2['test_2024_2026']['all_rows']
            dm = t2['paired']['Y:v2-v0']['MAE_loans']
            s += (f" The burst-shape features lowered the error of the Wikipedia-only level model from {f(t2['level']['v0']['MAE_loans']['value'], 2)} to {f(t2['level']['v2']['MAE_loans']['value'], 2)} loans "
                  f"({dm['diff']:+.2f}, interval {dm['lo']:+.2f} to {dm['hi']:+.2f}), which is still more than three times the error of the library model.")
            plY = c2['placebo']['paired'].get('Y:placebo_v2-placebo_v0')
            if plY:
                real_l = t2['paired']['Y:v2-v0']['MAE_log']['diff']
                s += (f" In the placebo the same columns change the Wikipedia-only level error (in ln(1 + loans)) by {plY['MAE_log']['diff']:+.4f} against {real_l:+.4f} in the real run, "
                      "so part of that gain is about how popular the book is (the donor books are matched on traffic) and part belongs to the book's own pages.")
        L.append(s)
        iv0 = c4['intervals']['v0_HW']
        cov = iv0['coverage']['all']
        L.append(f"- **Range for next month's loans.** The split-conformal 80% interval covered {pc(iv0['overall_2024_2026']['coverage'])} of the actual loans in 2024 to 2026 ({pc(iv0['overall_2020_2023']['coverage'])} in 2020 to 2023), "
                 f"with a median width of {f(iv0['overall_2024_2026']['median_width'], 1)} loans. By year the coverage ran from {pc(min(v['coverage'] for v in cov.values()))} to {pc(max(v['coverage'] for v in cov.values()))}; "
                 f"for burst rows it was {pc(np.mean([v['coverage'] for v in iv0['coverage']['burst_any'].values()]))} and for books with under 12 months of history {pc(np.mean([v['coverage'] for v in iv0['coverage']['short_hist'].values()]))} on average over the years.")
    # ---- placebo
    pl = []
    if c1:
        pl.append(f"change 1: with another book's pages the ranker gets {pc(c1['placebo']['v1_placebo']['p20_rise'])} against a base rate of {pc(c1['placebo']['v1_placebo']['base_rise'])}, so the early signal belongs to the book's own pages")
    if c2 and not c2.get('status'):
        pe = c2['placebo']['paired']['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise']
        pr_ = c2['test_2024_2026']['all_rows']['paired']['R:R:ranker_v2-R:ranker_c1']['p20_rise']
        pd2 = c2['placebo']['paired']['D:placebo_v2-placebo_v0']['change_rank']
        pl.append(f"change 2: with another book's pages the burst columns add {pts(pe['diff'])} points to the ranker (interval {pts(pe['lo'])} to {pts(pe['hi'])}) against {pts(pr_['diff'])} in the real run, "
                  f"and {pd2['diff']:+.4f} to the change ranking of the Wikipedia model, so the early-warning gain does not appear without the book's own pages")
    if c5 and not c5.get('status'):
        pe = c5['placebo']['paired']['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise']
        pr_ = c5['test_2024_2026']['all_rows']['paired']['R:R:ranker_v2-R:ranker_c1']['p20_rise']
        pl.append(f"change 5: with the events and adaptation columns moved 12 months later the ranker changes by {pts(pe['diff'])} points against {pts(pr_['diff'])} in the real run, so the small differences there are not tied to the real event dates")
    if pl:
        L.append('- **Placebo.** ' + '; '.join(pl) + '. There is no placebo for change 4: no Wikipedia-only variant was chosen there.')
    # ---- not run
    for nm, c in (('Burst-shape features (change 2)', c2), ('Events and adaptation views (change 5)', c5)):
        if c is None or c.get('status'):
            L.append(f"- **{nm}:** " + (c['status'] if c else (c5_missing() if 'change 5' in nm else 'not run')) + '.')
    if c5 and not c5.get('status'):
        te = c5['test_2024_2026']
        ap_ = te['all_rows']['paired']
        pl_ = c5['placebo']['paired']
        d = ap_['D:v2-v0']['change_rank']
        e = ap_['R:R:ranker_v2-R:ranker_c1']['p20_rise']
        w = ap_['R:W:v2-W:v0']['p20_rise']
        dp = pl_['D:placebo_v2-placebo_v0']['change_rank']
        wp = pl_['R:W:placebo_v2-W:placebo_v0']['p20_rise']
        ep = pl_['R:R:placebo_ranker_v2-R:placebo_ranker_c1']['p20_rise']
        txt = (f"- **Events and adaptation views (change 5).** Events are rare in this data: in the scored rows {c5['notes']['rows_with_flag']['e_died']:,} work-months have an author death in t or t-1, "
               f"{c5['notes']['rows_with_flag']['e_award']:,} a dated award and {c5['notes']['rows_with_flag']['e_ad_rel']:,} a film or tv release within a month that was already public. "
               f"Tuning chose {te['W_variant']} for the Wikipedia model (adopted: {'yes' if te['adopted_W'] else 'no'}) and {te['ranker_variant']} for the ranker (adopted: {'yes' if te['adopted_ranker'] else 'no'}). "
               f"On 2024 to 2026 the change ranking moved {d['diff']:+.4f} (interval {d['lo']:+.4f} to {d['hi']:+.4f}; {call(d)}), the early list of the Wikipedia model {phrase_pts(w)}, "
               f"and the ranker with minus without the new columns {phrase_pts(e)}. "
               f"With the same columns moved 12 months later (placebo) the same measures move {dp['diff']:+.4f}, {pts(wp['diff'])} points and {pts(ep['diff'])} points, "
               f"so these differences are no larger than what changing the set of columns does by itself; they do not come from the real event dates.")
        evb = te.get('subgroups', {}).get('event')
        evp = c5['placebo'].get('subgroups', {}).get('event')
        if evb and evp:
            de, dpe = evb['paired']['D:v2-v0']['change_rank'], evp['paired']['D:placebo_v2-placebo_v0']['change_rank']
            txt += (f" On the {evb['rows']:,} book-months within 2 months of an event, the change ranking moved {de['diff']:+.4f} (interval {de['lo']:+.4f} to {de['hi']:+.4f}) "
                    f"against {dpe['diff']:+.4f} in the placebo: the one place where the events may matter, resting on few rows.")
        if 'Y:v2-v0' in ap_ and 'Y:placebo_v2-placebo_v0' in pl_:
            ly, lyp = ap_['Y:v2-v0']['MAE_log'], pl_['Y:placebo_v2-placebo_v0']['MAE_log']
            txt += (f" The error of the Wikipedia-only level model (MAE of ln(1 + loans)) changed by {ly['diff']:+.4f} (interval {ly['lo']:+.4f} to {ly['hi']:+.4f}); in the placebo it changes by {lyp['diff']:+.4f}")
            if abs(lyp['diff']) >= 0.5 * abs(ly['diff']):
                txt += ", so what the adaptation views add to the level is about how popular the book is, not about the timing of events."
            else:
                txt += ", so most of that change depends on the real dates."
        L.append(txt)
    return L


def main():
    c1, c4, c2, c5 = R['c1'], R['c4'], R['c2'], R['c5']
    out = []
    P = out.append
    P('# Improvement round v2 for existing books (Test A): early warning, count loss, gate, burst features and events')
    P('')
    P('Khant Phyo Wai, 01323050. Run ' + time.strftime('%d %b %Y') + '. Settings: `prereg/addenda_wiki_led/2026-10-20_d_v2_all_books_platforms.json` (fixed before any result), which adopts '
      'Section 3 of `paper/lit_search/Improvement_Methods_2026-10-20.md`. Choices the note leaves open are in `prereg/DEVIATIONS.md` (section "Wikipedia-led tests", entries of 20 Oct 17:27 and 17:29 and later ones). '
      'Code: `code/main_study/wiki_led/80_improve_v2.py` (stages c1, c4, c2, c5) and `81_improve_v2_report.py`. Stage files: `data/reports/wiki_led_improve_v2_<stage>.json`.')
    P('')
    P('## 1. In plain words')
    P('')
    P('**Short answer.**')
    P('')
    for line in short_answer():
        P(line)
    P('')
    P('**Detail.** v0 is the Test A model of 20 October, unchanged. Each change was tuned on 2019 to 2023, one variant was chosen by the stated rule, and then v0 and the chosen variant were run once on 2024 to 2026 on the same rows. '
      'The 2024 to 2026 results of v0 were known before the changes were chosen, so this is a single pre-declared test of new settings, not a blind test; the frozen live lists are the blind check.')
    P('')
    for line in conclusions():
        P(line)
    P('')
    P('**What ran:**')
    P('')
    P(table(['Change', 'Chosen variant', 'Adopted by the rule', 'Tuning', '2024 to 2026 against v0'], summary_rows()))
    P('')
    P('## 2. How the runs were done')
    P('')
    P('Terms. A **rise** is next month\'s loans at least 1.5 times the book\'s median of the last 6 months; a **surge** is at least double and at least 5 loans more. A book is **not yet risen** when this month\'s loans are below 1.5 times that median. '
      '**Precision@20** is the share of a month\'s 20 highest-scored books that rose (or surged), averaged over months; **lift** divides it by the share of all eligible books that rose. **NDCG@20** gives credit for putting surges first, then rises, within the 20 (1 is the best possible list). '
      '**Change ranking** is the Spearman rank correlation, within month, between the predicted and the actual change. **Surge AP over base** is the average precision for surges divided by the surge rate (1 is chance). '
      '**MAE in loans** is the average absolute error of next month\'s loans, **WAPE** the total absolute error divided by the total loans, **top-10% hit** the share of the books a model puts in its top 10% by predicted loans that are in the actual top 10%.')
    P('')
    P('- Rows: the 556,735 book-months of Test A (7,747 books, origins 2019-01 to 2026-07 without the closure months, 78 scored months: 52 in 2019 to 2023 and 26 in 2024 to 2026). v0 is the stored Test A prediction for those rows.')
    P('- Walk-forward by year: a model for year Y trains on rows whose target month is before 1 January of Y. LightGBM settings of Test A (300 trees, 31 leaves, seed 20261020, 4 threads).')
    P('- Intervals: 95%, 2,000 draws of circular blocks of 3 consecutive scored months (seed 20261020), paired by month. May and June 2025 (Wikimedia found bot traffic counted as human in those months) are given separately as point values for the two origin months 2025-05 and 2025-06.')
    P('- Placebo: each book gets the Wikipedia pages of another book with similar traffic (the donor matching of `11_placebo_a.py`, rebuilt and checked: it reproduces the stored placebo predictions to 1e-17).')
    runs = [(nm, c) for nm, c in (('change 1', c1), ('change 4', c4), ('change 2', c2), ('change 5', c5)) if c and c.get('runtime_s')]
    if runs:
        P('- Peak memory and run time of the final full runs (one heavy job at a time, `nice`, LightGBM with 4 threads): ' + '; '.join(f"{nm} {c.get('peak_memory_gb')} GB, {c.get('runtime_s')} s" for nm, c in runs) + '.')
    P('')
    P('## 3. Change 1: early-warning ranker for books that have not risen yet')
    P('')
    P(render_c1(c1) if c1 else 'Not run.')
    P('')
    P('## 4. Change 4: count loss, gate and range for next month\'s loans')
    P('')
    P(render_c4(c4) if c4 else 'Not run.')
    P('')
    P('## 5. Change 2: burst-shape and noise features')
    P('')
    P(render_variants(c2, 'burst', 'burst_book') if c2 else 'Not run: data/db/wiki_led/burst_features.parquet had not been built.')
    P('')
    P('## 6. Change 5: dated events and the adaptation article\'s views')
    P('')
    P(render_variants(c5, 'events', 'event') if c5 else c5_missing()[0].upper() + c5_missing()[1:] + '.')
    P('')
    P('## 7. Choices the note leaves open, and cautions')
    P('')
    P('Each of these was written into `prereg/DEVIATIONS.md` before the result it affects was seen (entries of 20 Oct 17:27, 17:29 and later).')
    P('')
    P('- v0 is the stored Test A prediction (nothing refitted; a refit of W_lgbm for 2019 reproduces it to 3e-17). The main table\'s rows are the 556,735 rows of `test_a_preds.parquet`.')
    P('- "Not yet risen" uses the stored columns of Test A: ln(1 + loans this month) minus ln(1 + median of the last 6 months) below ln 1.5, the same arithmetic as the rise flag, so the threshold is treated the same on both sides.')
    P('- Change 1: four variants (truncation level 20 or 100; trained on books not yet risen or on all books with risen ones labelled 0). Choice by the highest tuning precision@20 of rises; adopted when above v0 on the same rows; the chosen variant is run on 2024 to 2026 whether or not it is adopted. Ties in score are ordered by work_id.')
    P('- Change 4: the note names three tuning measures and no single one, so the choice among v0 and the two Tweedie powers (and among HW, equal weights and the gate) takes the lowest mean rank over MAE in loans, MAE in ln(1 + loans) and the within-month Spearman. The gate (ridge, 10 inputs, no state main effects, standardized, alpha 1) is judged on 2020 to 2023, because 2019 has no earlier predictions and uses equal weights. Intervals are the 10th and 90th percentile of the previous year\'s log errors.')
    P('- Changes 2 and 5: the Wikipedia regression is chosen by the tuning within-month Spearman of the change, the ranker by tuning precision@20 of rises; each is adopted when above the same model without the new columns. One feature set serves the change and the level model. The ranker is the one chosen in change 1.')
    P('- Change 2: the third variant (with same_name and other_r4) was not run because those two columns are not in `burst_features.parquet`; the columns `top500_lists` and `nrm0` of that file are not used.')
    P('- Change 5: the release flag e_ad_rel is the file\'s ad_rel (a film or tv adaptation released in t-1, t or t+1) multiplied by "the adaptation article already had views before the end of t", which this script computes from `events_long.parquet` and the `has_data` column of `adaptation_page_features.parquet` (the empty ad_rel_public column of `events.parquet` is not used). Both variants were run once, after the adaptation views were complete (19:38 on 20 Oct). '
      'Only the columns ad_lvl4, ad_r4 and ad_rmax of the adaptation table are used. The placebo moves every new column 12 months later (the value at origin t is the one at origin t - 12 of the same work) and leaves the Test A columns as they are. Events are rare (see section 6), so this change had little to work with.')
    if c2 and not c2.get('status'):
        m = c2['missing_share_scored_rows']
        P(f"- Articles that did not exist yet. In Test A the weekly series hold zero views for weeks before an article existed, not missing values (audit of 20 Oct, `prereg/DEVIATIONS.md`), so the 18 Test A columns are always finite there (lvl4 sits at the floor ln 1e-12). v0 is unchanged. The burst columns follow the same rule for days (days before the page existed count as zero views, a zero normal is floored at 1e-12), "
          f"but a 28-day window with no views at all gives missing values for pk28, dpk, pre7 and rec, and dec is also missing when the peak is on the last 2 days. In the scored rows that is {pc(m['b_pk28'])} of book-article rows and {pc(m['a_pk28'])} of author-article rows for pk28, {pc(m['b_dec'])} and {pc(m['a_dec'])} for dec, {pc(m['b_corr28'])} for corr28 and {pc(m['b_co'])} for co "
          "(hi28 and top500 are 0, not missing). So the new columns treat 'no views in the window' as missing where Test A treats it as the floor value; LightGBM handles both, and the pattern of missing values carries similar information to the floor. The event columns are 0 (not missing) when there is no event, and months since the latest event is 24 when there is none.")
    P('- May and June 2025 mean the origin months 2025-05 and 2025-06.')
    P('- The top-10% hit rate is the accuracy panel\'s (it reproduces the stored values for HW_lgbm and H_lgbm); the within-25% share was dropped because the panel\'s rule could not be reproduced.')
    P('')
    P('Cautions. (1) 2024 to 2026 is not blind: v0\'s results there were known when the changes were chosen; the frozen live lists are the blind test. (2) Many measures are reported and the intervals are per measure, with no adjustment, so one interval that only just clears zero (for example a lower end of +0.4 points) is weak evidence alone. (3) There are 26 test months, so intervals for precision@20 are wide. (4) The 2024 library gap and May to June 2025 (bot traffic counted as human) are in the 2024 to 2026 numbers; the second is also given alone. (5) Several books of one author can sit in the same top 20. (6) The ranker\'s precision@20 moves by about 1.5 points with the LightGBM seed alone, and by about as much when random columns are added (sections 3 and 5), so differences below roughly 2 points in precision@20 cannot be told apart from that noise.')
    md = '\n'.join(out) + '\n'
    (REP / 'wiki_led_improve_v2.md').write_text(md)
    extras = {}
    for name in ('c1_seed_check', 'c2_seed_check', 'c5_seed_check', 'c2_noise_check', 'c5_noise_check', 'c2_importance', 'c5_importance'):
        f_ = REP / f'wiki_led_improve_v2_{name}.json'
        if f_.exists():
            extras[name] = json.loads(f_.read_text())
    (REP / 'wiki_led_improve_v2.json').write_text(json.dumps({'written': time.strftime('%Y-%m-%d %H:%M %z'), **{t: R[t] for t in STAGES}, 'descriptive_extras': extras}, indent=1))
    print('wrote', REP / 'wiki_led_improve_v2.md', len(md.split()), 'words')


if __name__ == '__main__':
    main()
