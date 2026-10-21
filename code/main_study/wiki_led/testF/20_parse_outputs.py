#!/usr/bin/env python3
"""Test F, step 20: read every answer file of the AI sorters and of the judge, check each code against the theme guide, list the lines to
re-ask, and write the assignments; main pages, the one-day sample, books, the second (reliability) pass and the judge are kept apart.

Settings: prereg/addenda_wiki_led/2026-10-21_g_ai_matchmaking.json (sorter): lines with codes not in the guide are re-asked once; what
remains invalid is dropped and counted. Nothing here reads loans.
Inputs (in the Test F folder, data/db/wiki_led/testF/ or a mock world):
  jobs.tsv (job, kind, input, from_line, to_line, output): every sorting job; a job's items are the lines from_line to to_line of its input
      file (line 1 is the header), and its answers are in output (out/<job>.tsv, no header). The group of a job comes from its input:
        pages_chunk_NN.tsv -> main pages        pages_sample1day_chunk_NN.tsv -> one-day sample (coverage only)
        books_chunk_NN.tsv -> books             rel_pages.tsv, rel_books.tsv -> second pass (reliability)
        judge_pages.tsv -> judge                reask_pages_input*.tsv, reask_books_input*.tsv -> re-ask answers
      Answer files out/reask_pages*.tsv and out/reask_books*.tsv that are not in jobs.tsv are read as re-ask answers too.
  Answer lines: pages  id<TAB>kind<TAB>code:conf,code:conf  or  id<TAB>kind<TAB>none
                books  id<TAB>code:conf,...  or  id<TAB>none
                judge  id<TAB>about<TAB>code,code,code or none<TAB>misleading_title: yes|no
  universe.parquet (page ids, titles, set), books.parquet (book ids, work ids), the theme guide (fingerprinted in prereg/README.md).
Rules (the first two are the addendum's; the rest are NOT IN ADDENDUM and were fixed before any sorting output existed):
  - a code must be one of the 242 codes of the guide (prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv); a confidence must be 1, 2
    or 3; weights 1.0, 0.6, 0.3 for confidence 3, 2, 1;
  - a sorter line with any code outside the guide, or a malformed token, is invalid as a whole and goes on the re-ask list; an item with no
    answer line in a job whose answer file exists is 'missing' and goes on the list too. The re-ask input is written as
    reask_pages_input.tsv / reask_books_input.tsv (the input lines with the header of the chunks; a file already named in jobs.tsv is never
    overwritten, later items go to reask_pages_input_2.tsv and so on). After the one re-ask, a line that is still invalid is dropped (the
    item gets no theme) and counted; an item without a re-ask answer stays on the list and has no theme;
  - codes are read case-insensitively; tokens are separated by commas (spaces around them are ignored); a line whose fields are separated
    by spaces instead of a tab is accepted when it still splits into id, (kind,) codes, and counted; a code given twice keeps its first
    confidence; more than 3 codes keep the first 3 (strongest first); both are counted;
  - a page kind outside concept, person, work, event, place, organization, list, other is kept as written and counted (descriptive only);
    blank lines, header lines (first field 'id') and code fences are skipped; an id that is not an item of the group is counted and
    ignored; an id answered twice keeps its first line, counted;
  - the second pass has no re-ask: its invalid lines are left out and counted (step 27); judge codes outside the guide are dropped and
    counted (the judge was not asked for confidences; a ':n' after a code is ignored); a judge line whose 'about' holds a tab is read from
    both ends.
Outputs: assign_pages.parquet (id, title, set, kind, code, conf, weight, rank, n_top_days, prompt_example, source),
         assign_books.parquet (id, work_id, title, code, conf, weight, rank, source), items_pages.parquet, items_books.parquet (one row per
         item with its status), second_pass_pages.parquet, second_pass_books.parquet (id, status, codes, confs), judge_answers.parquet
         (id, about, codes, misleading, n_dropped_codes), reask_pages.tsv, reask_books.tsv (id, reason, answer line), the re-ask input
         files, parse_summary.json; report testF_20_parse.md.
Run from code/ (after all jobs are done, and again after the re-ask):  nice ../.venv/bin/python main_study/wiki_led/testF/20_parse_outputs.py
"""
import sys, re, json, pathlib, argparse
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _testf_analysis as T

ID_RE = re.compile(r'^[pb]\d{5}$')
TOK_RE = re.compile(r'^([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)\s*:\s*(\d+)$')
GROUPS = (('pages_main', 'pages', r'^pages_chunk_\d+\.tsv$'), ('pages_sample', 'pages', r'^pages_sample1day_chunk_\d+\.tsv$'),
          ('books_main', 'books', r'^books_chunk_\d+\.tsv$'), ('rel_pages', 'pages', r'^rel_pages\.tsv$'), ('rel_books', 'books', r'^rel_books\.tsv$'),
          ('judge', 'judge', r'^judge_pages\.tsv$'), ('reask_pages', 'pages', r'^reask_pages_input(_\d+)?\.tsv$'),
          ('reask_books', 'books', r'^reask_books_input(_\d+)?\.tsv$'))


# ---------------------------------------------------------------- one answer line
def parse_codes(field, guide):
    """-> (status, [(code, conf)], notes Counter, reason). status: ok, none, invalid."""
    notes = Counter()
    f = field.strip().strip('`').strip()
    if f.lower().rstrip('.') == 'none':
        return 'none', [], notes, ''
    toks = [t.strip() for t in f.split(',')]
    toks = [t for t in toks if t]
    if not toks:
        return 'invalid', [], notes, 'no codes'
    out, seen = [], set()
    for t in toks:
        m = TOK_RE.match(t)
        if not m:
            return 'invalid', [], notes, f'malformed token {t[:40]!r}'
        code, conf = m.group(1).upper(), int(m.group(2))
        if conf not in (1, 2, 3):
            return 'invalid', [], notes, f'confidence {conf} for {code}'
        if code not in guide:
            return 'invalid', [], notes, f'code not in guide {code}'
        if code in seen:
            notes['duplicate_code'] += 1
            continue
        seen.add(code)
        out.append((code, conf))
    if len(out) > 3:
        notes['more_than_3_codes'] += 1
        out = out[:3]
    return 'ok', out, notes, ''


def split_line(line, n_fields):
    """Fields of an answer line: tab-separated; else whitespace-separated if that gives the right number of fields."""
    parts = line.split('\t')
    if len(parts) == n_fields:
        return [p.strip() for p in parts], False
    if len(parts) > n_fields and all(p.strip() == '' for p in parts[n_fields:]):
        return [p.strip() for p in parts[:n_fields]], False
    alt = re.split(r'\s+', line.strip(), maxsplit=n_fields - 1)
    if len(alt) == n_fields and ID_RE.match(alt[0]):
        return alt, True
    return None, False


def lines_of(files):
    for f in files:
        for raw in pathlib.Path(f).read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw.rstrip('\r')
            s = line.strip()
            if not s or s.startswith('```') or s.startswith('#'):
                continue
            yield pathlib.Path(f).name, line, s


def read_answers(files, kind, guide, ids_known):
    """Sorter answers (kind pages or books), files in the given order. Returns {id: record} (first line per id wins) and notes."""
    n_fields = 3 if kind == 'pages' else 2
    res, notes = {}, Counter()
    for fname, line, s in lines_of(files):
        fields, fixed = split_line(line, n_fields)
        if fields is None:
            first = s.split('\t')[0].split()[0]
            if first.lower() == 'id':
                continue
            if ID_RE.match(first) and first in ids_known:
                notes['malformed_line'] += 1
                if first not in res:
                    res[first] = dict(status='invalid', codes=[], kind=None, reason='wrong number of fields', line=s[:300], file=fname)
                continue
            notes['unreadable_line'] += 1
            continue
        iid = fields[0]
        if iid.lower() == 'id':
            continue
        if not ID_RE.match(iid) or iid not in ids_known:
            notes['id_not_an_item_of_this_group'] += 1
            continue
        if fixed:
            notes['separator_fixed'] += 1
        if iid in res:
            notes['duplicate_line'] += 1
            continue
        kfield = fields[1].lower() if kind == 'pages' else None
        if kind == 'pages' and kfield not in T.KINDS:
            notes['unknown_kind'] += 1
        st, codes, nn, reason = parse_codes(fields[-1], guide)
        notes.update(nn)
        res[iid] = dict(status=st, codes=codes, kind=kfield, reason=reason, line=s[:300], file=fname)
    return res, notes


def read_judge(files, guide, ids_known):
    rows, notes, seen = [], Counter(), set()
    for fname, line, s in lines_of(files):
        parts = line.split('\t')
        if parts[0].strip().lower() == 'id':
            continue
        if len(parts) < 4:
            notes['malformed_line'] += 1
            continue
        iid, codes_f, mis_f = parts[0].strip(), parts[-2].strip(), parts[-1].strip().lower()
        if iid not in ids_known:
            notes['id_not_an_item_of_this_group'] += 1
            continue
        about = '\t'.join(parts[1:-2]).strip()
        if len(parts) > 4:
            notes['about_with_tab'] += 1
        m = re.search(r'\b(yes|no)\b', mis_f)
        if not m:
            notes['misleading_unreadable'] += 1
        codes, dropped = [], 0
        if codes_f.lower().rstrip('.') != 'none':
            for t in [x.strip().upper() for x in codes_f.split(',') if x.strip()]:
                t = t.split(':')[0].strip()
                if t in guide:
                    if t not in codes:
                        codes.append(t)
                else:
                    dropped += 1
                    notes['code_not_in_guide'] += 1
        if len(codes) > 3:
            notes['more_than_3_codes'] += 1
            codes = codes[:3]
        if iid in seen:
            notes['duplicate_line'] += 1
            continue
        seen.add(iid)
        rows.append(dict(id=iid, about=about, codes=codes, misleading=(m.group(1) == 'yes') if m else None, n_dropped_codes=dropped, file=fname))
    return pd.DataFrame(rows, columns=['id', 'about', 'codes', 'misleading', 'n_dropped_codes', 'file']), notes


# ---------------------------------------------------------------- jobs
def load_jobs(P):
    f = P / 'jobs.tsv'
    if not f.exists():
        raise SystemExit(f'{f} not found: the list of sorting jobs (job, kind, input, from_line, to_line, output) is needed')
    J = pd.read_csv(f, sep='\t', dtype=str, keep_default_na=False)
    need = {'job', 'kind', 'input', 'from_line', 'to_line', 'output'}
    if not need <= set(J.columns):
        raise SystemExit(f'jobs.tsv lacks columns {need - set(J.columns)}')
    J = J.drop_duplicates()
    if J.job.duplicated().any():
        raise SystemExit(f'jobs.tsv names a job twice with different rows: {J[J.job.duplicated()].job.tolist()[:5]}')
    J['from_line'] = J.from_line.astype(int)
    J['to_line'] = J.to_line.astype(int)
    J['group'] = None
    for g, _, pat in GROUPS:
        J.loc[J.input.str.match(pat) & J.group.isna(), 'group'] = g
    J['answered'] = [(P / o).exists() for o in J.output]
    cache = {}
    ids = []
    for r in J.itertuples():
        if r.input not in cache:
            cache[r.input] = (P / r.input).read_text(encoding='utf-8').split('\n') if (P / r.input).exists() else None
        lines = cache[r.input]
        ids.append([] if lines is None else [ln.split('\t')[0] for ln in lines[r.from_line - 1:r.to_line] if ln.strip()])
    J['ids'] = ids
    # extra re-ask answer files in out/ that are not jobs
    named = set(J.output)
    extra = [str(p.relative_to(P.root)) for k in ('pages', 'books') for p in sorted((P.root / 'out').glob(f'reask_{k}*.tsv')) if str(p.relative_to(P.root)) not in named]
    return J, extra, {k: v for k, v in cache.items()}


def group_status(J, g, kind, guide, P):
    """First-pass records of one group: answers, notes, and the status of every item of its jobs."""
    Jg = J[J.group == g]
    files = [P / o for o in Jg[Jg.answered].output]
    items_all = [i for ids in Jg.ids for i in ids]
    items_done = {i for ids, a in zip(Jg.ids, Jg.answered) if a for i in ids}
    if kind == 'judge':
        ans, notes = read_judge(files, guide, set(items_all))
        return Jg, ans, notes, items_all, items_done
    ans, notes = read_answers(files, kind, guide, set(items_all))
    st = {}
    for i in items_all:
        st[i] = ans[i]['status'] if i in ans else ('missing' if i in items_done else 'not_sorted')
    return Jg, (ans, st), notes, items_all, items_done


def final_items(key_ids, first, st1, reask):
    """Status after the re-ask; assignments."""
    rows, assign = [], []
    for i in key_ids:
        if i not in st1:
            rows.append(dict(id=i, status='not_in_any_job', source='', kind=None, n_codes=0, reason='', file=''))
            continue
        s, src, rec = st1[i], 'first', first.get(i)
        if s in ('invalid', 'missing'):
            r2 = reask.get(i)
            if r2 is None:
                pass                                          # not re-asked yet: stays invalid or missing (on the re-ask list)
            elif r2['status'] in ('ok', 'none'):
                s, src, rec = ('themes' if r2['status'] == 'ok' else 'none'), 'reask', r2
            else:
                s, rec = 'dropped_invalid', r2                # still invalid after the one re-ask: dropped and counted
        elif s == 'ok':
            s = 'themes'
        rec = rec or {}
        rows.append(dict(id=i, status=s, source=src if s in ('themes', 'none') else '', kind=rec.get('kind'),
                         n_codes=len(rec.get('codes', [])) if s == 'themes' else 0, reason=rec.get('reason', '') if s not in ('themes', 'none') else '',
                         file=rec.get('file', '')))
        if s == 'themes':
            for k, (c, conf) in enumerate(rec['codes']):
                assign.append(dict(id=i, kind=rec.get('kind'), code=c, conf=conf, weight=T.WEIGHT[conf], rank=k + 1, source=src))
    return pd.DataFrame(rows), pd.DataFrame(assign, columns=['id', 'kind', 'code', 'conf', 'weight', 'rank', 'source'])


def write_reask_input(P, J, kind, ids, inputs):
    """Input lines of the items to re-ask, with the chunks' header; never overwrites a file that a job already names."""
    if not len(ids):
        return None
    line_of, header = {}, None
    for name, lines in inputs.items():
        if lines is None or not re.match(rf'^({kind}_chunk_|pages_sample1day_chunk_)' if kind == 'pages' else rf'^{kind}_chunk_', name):
            continue
        header = header or lines[0]
        for ln in lines[1:]:
            if ln.strip():
                line_of[ln.split('\t')[0]] = ln
    used = set(J.input)
    k = 1
    while True:
        name = f'reask_{kind}_input.tsv' if k == 1 else f'reask_{kind}_input_{k}.tsv'
        if name not in used:
            break
        k += 1
    rows = [line_of[i] for i in ids if i in line_of]
    if header is None or not rows:
        return None
    T.write_text('\n'.join([header] + rows) + '\n', P / name)
    return name


def summary(items, A, notes_first, notes_reask, files_first, files_reask, jobs, st1):
    return dict(jobs=int(len(jobs)), jobs_answered=int(jobs.answered.sum()), answer_files_first=files_first, answer_files_reask=files_reask,
                items_in_key=len(items), first_pass=dict(Counter(st1.values())), first_pass_notes=dict(notes_first), reask_notes=dict(notes_reask),
                final=items.status.value_counts().to_dict(), to_reask_now=int(items.status.isin(['invalid', 'missing']).sum()),
                still_invalid_after_reask=int((items.status == 'dropped_invalid').sum()), pairs=len(A),
                pairs_by_conf={str(k): int(v) for k, v in A.conf.value_counts().sort_index().items()} if len(A) else {},
                codes_per_item={str(k): int(v) for k, v in A.groupby('id').size().value_counts().sort_index().items()} if len(A) else {})


def main():
    ap = T.add_root_arg(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--book-key', default=None)
    a = ap.parse_args()
    P = T.Paths(a.root)
    guide, ginfo = T.load_guide(P)
    T.log(f'{P.tag()}; guide: {ginfo["source"]} ({ginfo["codes"]} codes, fingerprinted: {ginfo["fingerprinted"]})')
    J, extra_reask, inputs = load_jobs(P)
    unknown = J[J.group.isna()]
    if len(unknown):
        T.log(f'jobs with an input of no known group (left out): {unknown.job.tolist()[:10]}')
    U = T.page_key(P)
    BK, bname = T.book_key(P, a.book_key)
    ex = T.prompt_example_titles(P)
    out = dict(guide=ginfo, mock=P.mock, jobs={g: dict(jobs=int((J.group == g).sum()), answered=int(J[J.group == g].answered.sum())) for g, _, _ in GROUPS})
    rep = [f'# Test F, step 20: sorting and judge answers parsed ({P.tag()})', '',
           f'- written {pd.Timestamp.now():%Y-%m-%d %H:%M}; code main_study/wiki_led/testF/20_parse_outputs.py',
           f'- theme guide: {ginfo["source"]}, {ginfo["codes"]} codes' + (f', SHA-256 `{ginfo["sha256"]}`, fingerprinted: {ginfo["fingerprinted"]}' if ginfo['sha256'] else ''),
           f'- jobs (jobs.tsv): ' + ', '.join(f'{g} {v["answered"]}/{v["jobs"]} answered' for g, v in out['jobs'].items() if v['jobs']), '']
    # re-ask answers (pages and books)
    reask = {}
    reask_files = {}
    for kind in ('pages', 'books'):
        Jr = J[(J.group == f'reask_{kind}') & J.answered]
        files = [P / o for o in Jr.output] + [P / x for x in extra_reask if f'reask_{kind}' in x]
        reask_files[kind] = [str(f.relative_to(P.root)) for f in files]
        ids_known = set(U.id) if kind == 'pages' else set(BK.id)
        reask[kind] = read_answers(files, kind, guide, ids_known) if files else ({}, Counter())
    # ---------------- pages: main and one-day sample (first pass)
    parts = {}
    for g in ('pages_main', 'pages_sample'):
        Jg, (ans, st), notes, items_all, items_done = group_status(J, g, 'pages', guide, P)
        parts[g] = (Jg, ans, st, notes)
    first = {**parts['pages_main'][1], **parts['pages_sample'][1]}
    st1 = {**parts['pages_main'][2], **parts['pages_sample'][2]}
    notes1 = parts['pages_main'][3] + parts['pages_sample'][3]
    items, A = final_items(U.id, first, st1, reask['pages'][0])
    cols = ['id', 'title', 'set'] + (['n_top_days'] if 'n_top_days' in U else [])
    items = items.merge(U[cols], on='id', how='left')
    A = A.merge(U[cols], on='id', how='left')
    A['prompt_example'] = A.title.isin(ex)
    items['prompt_example'] = items.title.isin(ex)
    T.write_parquet(A, P / 'assign_pages.parquet')
    T.write_parquet(items, P / 'items_pages.parquet')
    RQ = pd.DataFrame([dict(id=i, reason=(first[i]['reason'] if i in first else 'no answer line'), answer_line=(first[i]['line'] if i in first else ''))
                       for i in items.loc[items.status.isin(['invalid', 'missing']), 'id']], columns=['id', 'reason', 'answer_line'])
    RQ.to_csv(P / 'reask_pages.tsv', sep='\t', index=False)
    rq_name = write_reask_input(P, J, 'pages', list(RQ.id), inputs)
    Jp = J[J.group.isin(['pages_main', 'pages_sample'])]
    out['pages'] = summary(items, A, notes1, reask['pages'][1], [o for o in Jp[Jp.answered].output], reask_files['pages'], Jp, st1)
    out['pages']['reask_input'] = rq_name
    out['pages']['by_set'] = {f'{s}|{st}': int(n) for s, st, n in items.groupby(['set', 'status']).size().reset_index().itertuples(index=False)}
    out['pages']['kinds'] = items[items.status.isin(['themes', 'none'])].kind.value_counts().to_dict()
    T.log(f'pages: {out["pages"]["final"]}; pairs {len(A):,}; to re-ask now {len(RQ):,}' + (f' (input {rq_name})' if rq_name else ''))
    # ---------------- books (first pass)
    Jb, (ansb, stb), notesb, _, _ = group_status(J, 'books_main', 'books', guide, P)
    items_b, AB = final_items(BK.id, ansb, stb, reask['books'][0])
    bcols = ['id', 'work_id'] + (['title'] if 'title' in BK else [])
    AB = AB.drop(columns=['kind']).merge(BK[bcols], on='id', how='left')
    items_b = items_b.drop(columns=['kind']).merge(BK[bcols], on='id', how='left')
    T.write_parquet(AB, P / 'assign_books.parquet')
    T.write_parquet(items_b, P / 'items_books.parquet')
    RQb = pd.DataFrame([dict(id=i, reason=(ansb[i]['reason'] if i in ansb else 'no answer line'), answer_line=(ansb[i]['line'] if i in ansb else ''))
                        for i in items_b.loc[items_b.status.isin(['invalid', 'missing']), 'id']], columns=['id', 'reason', 'answer_line'])
    RQb.to_csv(P / 'reask_books.tsv', sep='\t', index=False)
    rqb_name = write_reask_input(P, J, 'books', list(RQb.id), inputs)
    out['books'] = summary(items_b, AB, notesb, reask['books'][1], [o for o in Jb[Jb.answered].output], reask_files['books'], Jb, stb)
    out['books']['reask_input'] = rqb_name
    out['books']['key_file'] = bname
    T.log(f'books: {out["books"]["final"]}; pairs {len(AB):,}; to re-ask now {len(RQb):,}' + (f' (input {rqb_name})' if rqb_name else ''))
    # ---------------- second pass (reliability): parsed apart, no re-ask
    for g, kind in (('rel_pages', 'pages'), ('rel_books', 'books')):
        Jg, (ans, st), notes, items_all, items_done = group_status(J, g, kind, guide, P)
        rows = [dict(id=i, status=st[i], codes=[c for c, _ in ans[i]['codes']] if i in ans else [], confs=[f for _, f in ans[i]['codes']] if i in ans else [])
                for i in items_all]
        S2p = pd.DataFrame(rows, columns=['id', 'status', 'codes', 'confs'])
        T.write_parquet(S2p, P / f'second_pass_{kind}.parquet')
        out[g] = dict(jobs=int(len(Jg)), answered=int(Jg.answered.sum()), items=len(items_all), status=S2p.status.value_counts().to_dict(), notes=dict(notes))
        T.log(f'{g}: {out[g]["status"]}')
    # ---------------- judge: parsed apart
    Jj, Jans, jnotes, j_all, j_done = group_status(J, 'judge', 'judge', guide, P)
    Jans['status'] = 'answered'
    miss = [i for i in j_all if i not in set(Jans.id)]
    T.write_parquet(Jans, P / 'judge_answers.parquet')
    out['judge'] = dict(jobs=int(len(Jj)), answered=int(Jj.answered.sum()), items=len(j_all), lines=len(Jans), without_answer=len(miss),
                        notes=dict(jnotes), none=int((Jans.codes.map(len) == 0).sum()) if len(Jans) else 0,
                        misleading_yes=int((Jans.misleading == True).sum()) if len(Jans) else 0)  # noqa: E712
    T.log(f'judge: {len(Jans)} answers of {len(j_all)} pages; notes {dict(jnotes)}')
    T.write_json(out, P / 'parse_summary.json')
    for k, title in (('pages', 'Pages (main and one-day sample)'), ('books', 'Books')):
        s = out[k]
        rep += [f'## {title}', '',
                f'- jobs answered {s["jobs_answered"]} of {s["jobs"]}; re-ask answer files: {len(s["answer_files_reask"])}',
                f'- items in the key: {s["items_in_key"]:,}',
                '- after the first pass: ' + ', '.join(f'{a_}: {b_:,}' for a_, b_ in sorted(s['first_pass'].items())),
                '- notes on the first pass: ' + (', '.join(f'{a_}: {b_:,}' for a_, b_ in sorted(s['first_pass_notes'].items())) or 'none'),
                '- final: ' + ', '.join(f'{a_}: {b_:,}' for a_, b_ in sorted(s['final'].items())),
                f'- re-ask list now (invalid or missing, not yet re-asked): {s["to_reask_now"]:,} items' + (f', input file {s["reask_input"]}' if s['reask_input'] else '')
                + f'; still invalid after the re-ask (dropped): {s["still_invalid_after_reask"]:,}',
                f'- theme pairs: {s["pairs"]:,}; by confidence {s["pairs_by_conf"]}; themes per item {s["codes_per_item"]}', '']
        if k == 'pages':
            rep += [f'- by set and status: {s["by_set"]}', f'- kinds (sorted pages): {s["kinds"]}', '']
    for g in ('rel_pages', 'rel_books'):
        s = out[g]
        rep.append(f'- second pass {g}: jobs answered {s["answered"]} of {s["jobs"]}; items {s["items"]:,}; status {s["status"]}; notes {s["notes"] or "none"}')
    s = out['judge']
    rep += [f'- judge: jobs answered {s["answered"]} of {s["jobs"]}; answers {s["lines"]} of {s["items"]} pages (without an answer {s["without_answer"]}); '
            f'none {s["none"]}; misleading title {s["misleading_yes"]}; notes {s["notes"] or "none"}', '',
            'Status words: themes (at least one valid code), none, invalid (a code outside the guide or a malformed line, waiting for the re-ask), '
            'missing (no answer line in an answered job, waiting for the re-ask), not_sorted (its job has no answer file yet), dropped_invalid '
            '(still invalid after the one re-ask), not_in_any_job. Only items with status themes have assignments.']
    T.write_text('\n'.join(rep) + '\n', P.report('testF_20_parse.md'))
    T.log(f'wrote the parsed answers and {P.report("testF_20_parse.md")}; peak memory {T.peak_gb():.2f} GB')


if __name__ == '__main__':
    main()
