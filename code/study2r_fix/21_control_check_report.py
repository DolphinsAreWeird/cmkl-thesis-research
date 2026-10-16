"""Writes data/reports/study2r_control_check.md: the data and mapping check of the 7 positive controls (old mapping vs the article-level fix) and old vs new main results."""
import pathlib, re, time
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[2]; D = ROOT / 'data'; T = D / 'db/taxonomy_v3'
OLD = D / 'db/study2r'; FIX = D / 'db/study2r_fix'
CT = {"The Queen's Gambit": (47460, '2020-10-23'), 'The Duke and I': (40237, '2020-12-25'), 'Dune': (13343, '2021-10-22'), 'Where the Crawdads Sing': (36910, '2022-07-15'),
      'American Prometheus': (5121, '2023-07-21'), 'Killers of the Flower Moon': (30993, '2023-10-20'), 'Shogun': (547, '2024-02-27')}
G = pd.read_parquet(FIX / 'group_members.parquet'); oc = pd.read_csv(OLD / 'controls.csv'); nc = pd.read_csv(FIX / 'controls.csv')
C0 = pd.read_parquet(OLD / 'counts_work.parquet'); C1 = pd.read_parquet(FIX / 'counts_work.parquet')
W = pd.read_parquet(T / 'spl_works.parquet', columns=['work_id', 'title', 'creator', 'checkouts_book', 'checkouts_ebook', 'checkouts_audiobook'])
L = ['# Study 2R: positive-control check (data and mapping only)', '', 'Khant Phyo Wai, student ID 01323050. Built ' + time.strftime('%Y-%m-%d %H:%M') + ' by code/study2r_fix/21_control_check_report.py. Nothing was tuned: no setting, window, rule or threshold of the record changed. Only the list of Seattle works behind each article changed, for every book alike.', '']
# ---- summary
a0 = (oc.p_p < 0.05).sum(); a1 = (nc.p_p < 0.05).sum()
L += ['## Short answer', '',
      '- A mapping error exists. The first run tested one Seattle work per book (the largest one). The same book often sits in several Seattle works: other editions, film tie-in editions, a "with 2nd Epilogue" edition, "Part One" and "Part Two" audio and ebook editions, other spellings of the creator. Loans that moved from one edition to another looked like a fall, and loans of omitted editions were lost.',
      f'- Fix (same for all 7,427 articles): one test unit per Wikipedia article, its checkouts summed over all Seattle works attached to it. 433 originally matched works shared an article with another work; 468 further Seattle works (most below the 500-checkout floor) were attached by the record\'s own matching rules (ISBN, or full title and author family name, plus plain edition markers, plus a given-name check); {int((G.groupby("group_id").how.apply(lambda s: (s != "original").any())).sum())} articles gained works.',
      f'- Controls, old to new: {a0} of 7 with one-sided p < 0.05 became {a1} of 7. Pooled tau changed from {oc.tau_p[np.isfinite(oc.tau_p)].mean():.3f} (mean of the seven) to {nc.tau_p[np.isfinite(nc.tau_p)].mean():.3f}. The record\'s pass rule (pooled interval above 0 and at least 4 of 7) is met after the fix. See the table below.',
      '- Not a mapping error: The Queen\'s Gambit. Its 0.7 expected checkouts are real. The work has no ebook or audiobook record before November 2020 and 0 to 7 print loans a month in the 24 fit months (April 2018 to September 2019), so any model of its own past expects almost nothing. Observed 42, tau 4.1. The one-sided rank p (0.07 old, 0.09 new) is weak only because placebo works with a near-zero base also vary a lot. Dune: the expected count (738) is high because Dune\'s loans stepped up in mid-2020 inside the 24 fit months and the log-linear trend carries that step forward; that is the model, not the data.',
      '- The Duke and I: its ebook loans stop in September 2020 (the "with 2nd Epilogue" edition took some, but with no loans in the window) so the fall is real in Seattle\'s data; the model expects 105 and sees 46 in months 0 to +2 (audiobook jumped after Bridgerton but audiobooks are not in the primary model). This control still fails after the fix.', '']
# ---- per control
L += ['## Control by control', '', 'Month 0 is the release month for all seven (addendum c: no shift of the ratio 1.5 table within 8 weeks of release was found). Release months used: ' + '; '.join(f'{k} {v[1][:7]}' for k, v in CT.items()) + '.', '']
for k, (wid, rel) in CT.items():
    g = G[G.group_id == wid]
    o = oc[oc.control == k].iloc[0]; n = nc[nc.control == k].iloc[0]
    L += [f'### {k}', '',
          f'- Article: {n.get("article", "")}. Release {rel}, month 0 = {rel[:7]}.',
          f'- Seattle works used in the first run: {wid} only ("{g[g.work_id == wid].title.iloc[0]}", {int(W[W.work_id == wid].checkouts_book.iloc[0] + 0)} print, {int(W[W.work_id == wid].checkouts_ebook.iloc[0])} ebook, {int(W[W.work_id == wid].checkouts_audiobook.iloc[0])} audiobook checkouts over the full catalogue period).',
          f'- Seattle works after the fix ({len(g)}): ' + '; '.join(f'{r.work_id} "{r.title[:60]}" ({r.how.replace("title_author_or_edition_marker", "title+edition marker")}, {int(r.checkouts_total)})' for r in g.itertuples()) + '.']
    # other Seattle works of the same book still left out: look for the book's title among creator's works
    others = {"The Queen's Gambit": 'Das Damengambit (19 audiobook loans, German edition) and Gambito de dama (3 print loans, Spanish): other languages, not added.',
              'The Duke and I': 'Bridgerton Collection, Volume 1 (203 ebook loans, a box set that contains three books): not added.',
              'Dune': 'Dune: Der Wüstenplanet and Dune: Livre premier (about 20 loans, German and French) were not added (title split at a colon is not allowed); Dune Messiah and the other Dune novels have their own articles. Brian Herbert prequels are other books and stay out.',
              'Where the Crawdads Sing': 'La chica salvaje (6 audiobook loans, Spanish): not added.',
              'American Prometheus': 'none missing; the Oppenheimer film tie-in edition (1,155 ebook loans) was matched in the first run but not summed.',
              'Killers of the Flower Moon': 'Adapted for Young Readers (403 loans) is a different edition for children and stays out; the 11-loan audiobook was added.',
              'Shogun': 'Shōgun: the epic novel of Japan (157 print loans, Clavell, James), Polish edition (17) and James Clavell\'s Shōgun (141 print loans) were not added (colon split or different title).'}[k]
    L += [f'- Left out on purpose or not found: {others}']
    def win(C, ids):
        c = C[C.work_id.isin(ids)]
        m0 = int(rel[:4]) * 12 + int(rel[5:7]) - 1
        r = {}
        for f in ('print', 'ebook', 'audiobook'):
            x = c[c.format == f]
            r[f] = (int(x[(x.mi >= m0 - 30) & (x.mi <= m0 - 7)].y.sum()), int(x[(x.mi >= m0) & (x.mi <= m0 + 2)].y.sum()))
        return r
    w0 = win(C0, [wid]); w1 = win(C1, [wid])
    L += [f'- Checkouts in the 24 fit months (month -30 to -7) and in months 0 to +2, first run: ' + ', '.join(f'{f} {a}/{b}' for f, (a, b) in w0.items()) + '; after the fix: ' + ', '.join(f'{f} {a}/{b}' for f, (a, b) in w1.items()) + '.',
          f'- Expected and observed checkouts, months 0 to +2, print + ebook model: first run {o.summu_p:.1f} expected, {o.sumy_p:.0f} observed (tau {o.tau_p:.2f}, p {o.p_p:.3f}); after the fix {n.summu_p:.1f} expected, {n.sumy_p:.0f} observed (tau {n.tau_p:.2f}, p {n.p_p:.3f}).', '']
# ---- table
L += ['## Controls, old and new', '', '| control | expected old | observed old | tau old | p old | expected new | observed new | tau new | p new |', '|---|---|---|---|---|---|---|---|---|']
for k in CT:
    o = oc[oc.control == k].iloc[0]; n = nc[nc.control == k].iloc[0]
    L.append(f'| {k} | {o.summu_p:.1f} | {o.sumy_p:.0f} | {o.tau_p:.2f} | {o.p_p:.3f} | {n.summu_p:.1f} | {n.sumy_p:.0f} | {n.tau_p:.2f} | {n.p_p:.3f} |')
rd = lambda p: (p.read_text() if p.exists() else '')
ro, rn = rd(D / 'reports/study2r_results.md'), rd(D / 'reports/study2r_fix_results.md')
def res(t):
    m = re.search(r'\*\*Result: (\w+)\.\*\* Pooled mean tau = ([\-\d.]+) \(95% bootstrap interval ([\-\d.]+) to ([\-\d.]+).*?(\d) of 7', t, re.S)
    return m.groups() if m else None
L += ['', f'Record pass rule, first run: {res(ro)}; after the fix: {res(rn)} (result, pooled tau, interval low, high, number of tests with p < 0.05).', '']
# ---- main results old vs new
def grab(t):
    d = {}
    for key, pat in (('H1', r'H1, slope of tau on log2 whole duration in weeks: (.*?)\n'), ('H2', r'H2, 6\+ weeks minus 1 to 2 weeks: (.*?)\n'),
                     ('size', r'Coefficient of log2 peak size given log2 duration \(not tested\): (.*?)\n'), ('Hansen', r'Hansen threshold regression.*?\): (threshold .*?)\n')):
        m = re.search(pat, t.split('<!-- begin main -->')[-1].split('<!-- end main -->')[0]); d[key] = m.group(1)[:420] if m else 'n/a'
    m = re.search(r'Tests: (\d+) work-shift rows, (\d+) with a usable fit and window.*?(\d+) tests in the pooled analysis, (\d+) works', t.split('<!-- begin main -->')[-1], re.S)
    d['tests'] = m.group(0)[:260] if m else ''
    m = re.search(r'\| all shifts \| (\d+) \| (\d+) \| ([\-\d.]+) \| ([\-\d.]+ to [\-\d.]+)', t.split('<!-- begin main -->')[-1]); d['pooled'] = f'{m.group(1)} tests, {m.group(2)} works, mean tau {m.group(3)} ({m.group(4)})' if m else ''
    return d
go, gn = grab(ro), grab(rn)
L += ['## Full 2R analysis, old and new (steps 10 to 15 rerun on the article-level counts; main set, print and ebook)', '', '| quantity | first run | after the fix |', '|---|---|---|']
for k in ('tests', 'pooled', 'H1', 'H2', 'size', 'Hansen'):
    L.append(f'| {k} | {go[k]} | {gn[k]} |')
L += ['', 'Full tables: data/reports/study2r_fix_results.md (new) and study2r_results.md (first run, unchanged). Code: code/study2r_fix/ (09 builds the article-level counts; 12 to 15 are the 2R steps with outputs redirected to data/db/study2r_fix and data/reports/study2r_fix_*). The log row is in prereg/DEVIATIONS.md (Study 2R, 21:12). The simulation tests (step 11) test the tools, not the mapping, and were not rerun.',
      '', 'Limits. The attached editions follow the record\'s own matching rules, made stricter for added works; some editions with colon subtitles or other languages are still missing, so a few books remain partly under-counted. The article list is the original one (articles with a single work of at least 500 checkouts); books whose editions only reach 500 together are not added. Works on a series article (for example several books redirecting to one series page) are now one unit, as the user asked.']
(D / 'reports/study2r_control_check.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L))
