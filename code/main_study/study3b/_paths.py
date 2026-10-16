# Paths, command-line options, step order and reports for the Study 3b scripts.
# Real runs read data/db/study3/ (nothing is changed there), data/db/taxonomy_v3/, data/db/interest/ and write
# data/db/study3b/ and data/reports/study3b_*. With --sim DIR every script reads and writes DIR instead (a simulated
# world made by _simulate.py), so the whole chain can be tested without touching real demand.
# Step order: 01 (count panels) and 02 (value-level interest shifts) come first and are independent; 10 refuses to run
# without the reports of 01 and 02; each later step refuses to run without the report of the step before it.
import sys, os, time, json, argparse, pathlib
import _s3

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))                    # code/ (config.py)
from config import D, UA  # noqa: E402

F3 = _s3.files
read_parquet, save_parquet, save_csv, save_json, md_table, build_id, report_field = (
    F3.read_parquet, F3.save_parquet, F3.save_csv, F3.save_json, F3.md_table, F3.build_id, F3.report_field)

STEPS = {'01': 'study3b_01_panels', '02': 'study3b_02_value_shifts', '10': 'study3b_10_controls', '11': 'study3b_11_power',
         '12': 'study3b_12_shifts', '13': 'study3b_13_carryover', '14': 'study3b_14_sentiment',
         '15': 'study3b_15_backlist', '16': 'study3b_16_value_screened'}      # 15 and 16: robustness runs after the 3b results (addenda_3b b and the screened-p check)
PREVIOUS = {'10': ('01', '02'), '11': ('10',), '12': ('11',), '13': ('12',), '14': ('13',)}
MAX_WORKERS = 3                                              # machine rule: 8 GB RAM, at most 3 workers
LEVEL_CODE = {'narrow': 3, 'middle': 2, 'broad': 1, 'value': 4}       # level numbers in the interest tables (4 = theme value)
SEATTLE_FILE = F3.SEATTLE_FILE


class Paths:
    def __init__(self, sim=None):
        self.sim = sim is not None
        if self.sim:
            base = pathlib.Path(sim).resolve()
            self.db, self.rep, self.interest = base / 'db', base / 'reports', base / 'interest'
            self.study3 = base / 'study3'
            self.taxo_v3 = self.taxo_v2 = base / 'taxonomy'
            self.librivox_listening = base / 'taxonomy' / 'listening.parquet'
        else:
            self.db = pathlib.Path(D) / 'db' / 'study3b'
            self.rep = pathlib.Path(D) / 'reports'
            self.interest = pathlib.Path(D) / 'db' / 'interest'
            self.study3 = pathlib.Path(D) / 'db' / 'study3'
            self.taxo_v3 = pathlib.Path(D) / 'db' / 'taxonomy_v3'
            self.taxo_v2 = pathlib.Path(D) / 'db' / 'taxonomy_v2'
            self.librivox_listening = pathlib.Path(D) / 'db' / 'listening.parquet'
        for p in (self.db, self.rep):
            p.mkdir(parents=True, exist_ok=True)

    meta = property(lambda s: s.db / 'panel_meta.json')
    counts = property(lambda s: s.db / 'counts_seattle.parquet')
    counts_librivox = property(lambda s: s.db / 'counts_librivox.parquet')
    months = property(lambda s: s.db / 'month_status.parquet')
    categories = property(lambda s: s.db / 'categories.parquet')
    shifts_value = property(lambda s: s.db / 'shifts_value.parquet')

    def report(self, step):
        return self.rep / f'{STEPS[step]}.md'

    def out(self, name):
        return self.db / name


def parser(desc):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument('--sim', metavar='DIR', help='run on the simulated world in DIR (made by _simulate.py)')
    ap.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'parallel workers (default and maximum {MAX_WORKERS}; run with nice -n 10)')
    return ap


def workers_of(args):
    return max(1, min(args.workers, MAX_WORKERS))


def sim_only(args, name, default):
    """Overrides of record sizes (draws, resamples) are allowed only in simulation runs."""
    v = getattr(args, name)
    if v is None:
        return default
    if not args.sim:
        raise SystemExit(f'--{name.replace("_", "-")} may only be used with --sim; real runs use the record value ({default}).')
    return v


def load_meta(P):
    if not P.meta.exists():
        raise SystemExit(f'No count panel found ({P.meta}). Run 01_panels.py first.')
    return json.loads(P.meta.read_text())


def start(step, ap):
    """Parse options, check the step order and the panel; returns (args, paths, panel meta, warnings)."""
    args = ap.parse_args()
    P = Paths(args.sim)
    meta = load_meta(P)
    require_previous(P, step, meta)
    warn = []
    for f, t in (meta.get('inputs') or {}).items():
        if not os.path.exists(f) or abs(os.path.getmtime(f) - t) > 1e-6:
            warn.append(f'input {os.path.basename(f)} changed since the panel was built; consider rerunning 01_panels.py')
    if meta.get('inputs_changed_during_build'):
        warn.append('inputs changed while the panel was being built; rerun 01_panels.py')
    for w in warn:
        print('WARNING:', w, flush=True)
    return args, P, meta, warn


def require_previous(P, step, meta):
    """Refuse to run when a required earlier report is missing or was made on another panel build."""
    for prev in PREVIOUS[step]:
        rp = P.report(prev)
        if not rp.exists():
            raise SystemExit(f'Step {step} refuses to run: the report of step {prev} ({rp.name}) is missing. '
                             f'Run the steps in order: 01, 02, 10, 11, 12, 13, 14.')
        built = report_field(rp, 'panel build')
        if prev == '02':                              # interest only: tied to the shifts_value file, not to the panel build
            import hashlib
            want = report_field(rp, 'shifts_value file SHA-256')
            have = hashlib.sha256(P.shifts_value.read_bytes()).hexdigest() if P.shifts_value.exists() else None
            if want != have:
                raise SystemExit(f'Step {step} refuses to run: {rp.name} was made on another shifts_value.parquet than the one on disk. Rerun step 02.')
            continue
        if built != meta['build_id']:
            raise SystemExit(f'Step {step} refuses to run: {rp.name} was made on panel build {built}, '
                             f'but the current panel is {meta["build_id"]}. Rerun step {prev} first.')


def write_report(P, step, title, body_lines, S, meta, extra=None):
    """Markdown report with a fixed header that later steps check."""
    head = [f'# {title}', '', f'- step: {step}', f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            f'- mode: {"SIMULATED data (test run)" if P.sim else "real data"}',
            f'- panel build: `{meta["build_id"]}`', f'- taxonomy: {meta.get("taxonomy")}',
            f'- Study 3b settings record SHA-256: `{S.sha256}`', f'- Study 3 settings record SHA-256: `{S.sha256_study3}`',
            f'- addenda applied: {", ".join(a[0] for a in S.addenda) or "none"}']
    for k, v in (extra or {}).items():
        head.append(f'- {k}: {v}')
    text = '\n'.join(head + [''] + list(body_lines)) + '\n'
    path = P.report(step)
    with open(str(path) + '.part', 'w') as f:
        f.write(text)
    os.replace(str(path) + '.part', path)
    return path


def tidy(df):
    """Integer-valued float columns (made float by missing values) shown as integers in a Markdown table."""
    import numpy as np
    out = df.copy()
    for c in out.columns:
        if out[c].dtype.kind == 'f':
            v = out[c].dropna()
            if len(v) and (v == v.round()).all() and v.abs().max() < 1e12:
                out[c] = out[c].map(lambda x: '' if x != x else str(int(x)))
    return out
