# Conversation sources, step 10: positive controls (COVID-19 Mar 2020, George Floyd Jun 2020, #MeToo Oct 2017) for each source,
# written FIRST into data/reports/conversation_sources_results.md. Control = narrow node of the control theme, month 0 = month of the
# first rise inside the interest-side window; Study 3b model and pass rule (tau > 0 and one-sided placebo-category p < 0.05).
# Middle node tested descriptively. Run: bash jobs/heavy_lock.sh nice -n 10 .venv/bin/python code/conversation/10_controls.py
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import conv_common as C
from conv_common import S, B3, INF, IO

EVENTS = [('COVID-19, March 2020', '2020-03-11', 'B15.M04.N05', 'B15.M04'),
          ('George Floyd, June 2020', '2020-05-25', 'B05.M02.N02', 'B05.M02'),
          ('#MeToo, October 2017', '2017-10-15', 'B12.M01.N02', 'B12.M01')]
WINDOW_DAYS = {'tweetskb': (-56, 56), 'talk_edits': (-14, 56)}      # as on the interest side (DEVIATIONS rows)
SHOW = ['formats', 'phi', 'sumy_p', 'summu_p', 'tau_p', 'z_p', 'p_cat_p', 'n_placebos', 'too_sparse', 'tau_s']


def first_rise(X, node, ev, win):
    ev = pd.Timestamp(ev)
    d = (X.start_week - ev).dt.days
    g = X[(X.node_id == node) & d.between(*win) & (X.duration_class != 'none')].sort_values('start_week')
    return g.iloc[0] if len(g) else None


def main():
    t0 = time.time()
    P, meta, world = C.make_world()
    rows, lines = [], []
    head = []
    for src, info in C.SOURCES.items():
        X = C.conv_shifts(src)
        lines += [f'### {info["title"]}', '']
        for name, ev, nar, mid in EVENTS:
            for level, node in (('narrow', nar), ('middle', mid)):
                r = first_rise(X, node, ev, C.INF and WINDOW_DAYS[src])
                lab = world.cats[level].label.get(node)
                rec = dict(source=src, control=name, event=ev, level=level, node_id=node, label=lab)
                if r is None:
                    rec.update(rise='none', verdict='NO RISE, CONTROL NOT TESTABLE' if level == 'narrow' else 'no rise (descriptive)')
                else:
                    flags = ('near break; ' if r.near_break else '') + ('seasonal; ' if r.seasonal else '')
                    m0 = int(r.m0)
                    t = INF.test_unit(world, 'seattle', level, node, m0)
                    rec.update(rise=f'{r.start_week:%Y-%m-%d} {r.duration_class} size {r["size"]:.2f} {flags}'.strip(), month0=B3.ym_of(m0))
                    rec.update({k: t.get(k) for k in SHOW + ['skip']})
                    if t.get('skip', 'no counts') != '':
                        rec['verdict'] = f'NOT TESTABLE ({t.get("skip")})'
                    else:
                        rec['verdict'] = ('PASS' if (t['tau_p'] > 0 and t['p_cat_p'] < S.alpha) else 'FAIL') + ('' if level == 'narrow' else ' (descriptive)')
                    for f in S.seattle_formats:
                        rec[f'tau_p_{f}'] = t.get(f'tau_p_{f}')
                rows.append(rec)
    R = pd.DataFrame(rows)
    R.to_csv(C.OUTDIR / 'controls.csv', index=False)
    for src, info in C.SOURCES.items():
        sub = R[R.source == src]
        head.append(f'- {info["title"]}: ' + '; '.join(f'{r.control.split(",")[0]}: {r.verdict}' for r in sub[sub.level == 'narrow'].itertuples()))
    body = ['# Conversation sources: borrowing test results', '',
            'Khant Phyo Wai, CMKL University, ID 01323050. Second, informed analysis: it repeats the Study 3b design on two new interest sources; it is not an independent replication of the Wikipedia result. Settings: `prereg/conversation_sources_settings_2026-10-14.json` (read only). Code: `code/conversation/10` to `12`. Choices the record does not make: `prereg/DEVIATIONS.md`, Conversation sources, rows dated 2026-10-15.', '',
            '## 1. Positive controls (written before any other result)', '',
            'Rule (Study 3b): tau > 0 and one-sided placebo-category p < 0.05 in the joint Seattle model (print, ebook, audiobook), months 0 to +2. The control is the narrow node of the theme; month 0 is the month of the first rise that starts within 8 weeks before to 8 weeks after the event (talk edits: 2 weeks before to 8 weeks after, as on the interest side). The middle node is tested the same way but is descriptive only. A source with no rise in the narrow node cannot be tested for that event.', ''] + head + ['']
    cols = ['source', 'control', 'level', 'label', 'rise', 'month0', 'tau_p', 'p_cat_p', 'n_placebos', 'summu_p', 'too_sparse', 'verdict']
    body += IO.md_table(R.reindex(columns=cols).assign(**{c: R[c].map(lambda x: '' if pd.isna(x) else (f'{x:.3f}' if isinstance(x, float) else x)) for c in ['tau_p', 'p_cat_p', 'summu_p']} if len(R) else {}))
    body += ['', 'Per-format tau of the tested controls (descriptive):', '']
    body += IO.md_table(R[R.rise != 'none'].reindex(columns=['source', 'control', 'level'] + [f'tau_p_{f}' for f in S.seattle_formats]).round(3))
    body += ['', f'Run time {time.time() - t0:.0f} s. Panel build `{meta["build_id"]}`.', '', '<!-- TESTS -->']
    C.REPORT.write_text('\n'.join(body) + '\n')
    print('\n'.join(head))


if __name__ == '__main__':
    main()
