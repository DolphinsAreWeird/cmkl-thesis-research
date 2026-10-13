# Paths, command-line options, step order and reports for the Study 3 scripts.
# Real runs read and write data/db/study3/ and data/reports/study3_*. With --sim DIR every script reads and writes
# DIR instead (a simulated world made by 01_demand_panel.py --sim DIR), so the whole chain can be tested without
# touching real demand.
import sys, os, json, time, argparse, pathlib, hashlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))          # code/  (config.py)
from config import D  # noqa: E402

# step -> report file stem. Order matters: each step needs the report of the step before it.
STEPS = {'01': 'study3_panel_build', '10': 'study3_10_positive_controls', '11': 'study3_11_power',
         '12': 'study3_12_shift_effects', '13': 'study3_13_carryover', '14': 'study3_14_tone'}
ORDER = list(STEPS)
SEATTLE_FILE = {'audiobook': 'audiobook', 'ebook': 'ebook', 'print': 'book'}   # record name -> spl_rows_<file>.parquet
LEVEL_NAME = {1: 'broad', 2: 'middle', 3: 'narrow', 'broad': 'broad', 'middle': 'middle', 'narrow': 'narrow'}


class Paths:
    def __init__(self, sim=None):
        self.sim = sim is not None
        if self.sim:
            base = pathlib.Path(sim).resolve()
            self.db, self.rep, self.interest = base / 'db', base / 'reports', base / 'interest'
            self.taxo_v3 = self.taxo_v2 = base / 'taxonomy'
            self.librivox_listening = base / 'taxonomy' / 'listening.parquet'
        else:
            self.db = pathlib.Path(D) / 'db' / 'study3'
            self.rep = pathlib.Path(D) / 'reports'
            self.interest = pathlib.Path(D) / 'db' / 'interest'
            self.taxo_v3 = pathlib.Path(D) / 'db' / 'taxonomy_v3'
            self.taxo_v2 = pathlib.Path(D) / 'db' / 'taxonomy_v2'
            self.librivox_listening = pathlib.Path(D) / 'db' / 'listening.parquet'
        for p in (self.db, self.rep):
            p.mkdir(parents=True, exist_ok=True)

    panel = property(lambda s: s.db / 'demand_panel.parquet')
    panel_librivox = property(lambda s: s.db / 'demand_panel_librivox.parquet')
    meta = property(lambda s: s.db / 'demand_panel_meta.json')
    nodes = property(lambda s: s.db / 'nodes.parquet')
    overlap = property(lambda s: s.db / 'node_overlap.parquet')

    def report(self, step):
        return self.rep / f'{STEPS[step]}.md'

    def out(self, name):
        return self.db / name


def parser(desc):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument('--sim', metavar='DIR', help='run on the simulated world in DIR (made by 01_demand_panel.py --sim DIR)')
    ap.add_argument('--workers', type=int, default=min(4, max(1, (os.cpu_count() or 2) - 1)), help='parallel workers (default at most 4, to keep the Mac responsive)')
    ap.add_argument('--allow-dev-taxonomy', action='store_true',
                    help='allow a panel built from the taxonomy v2 development fallback (results are not final)')
    return ap


# ---------------- small file helpers ----------------
def read_parquet(path, columns=None, tries=4):
    """Read a Parquet file that another job may be rewriting: retry a few times on a read error."""
    import pandas as pd
    for k in range(tries):
        try:
            return pd.read_parquet(path, columns=columns)
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def save_parquet(df, path):
    path = pathlib.Path(path)
    df.to_parquet(str(path) + '.part', index=False)
    os.replace(str(path) + '.part', path)


def save_csv(df, path):
    path = pathlib.Path(path)
    df.to_csv(str(path) + '.part', index=False)
    os.replace(str(path) + '.part', path)


def save_json(obj, path):
    path = pathlib.Path(path)
    with open(str(path) + '.part', 'w') as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(str(path) + '.part', path)


def load_meta(P):
    if not P.meta.exists():
        raise SystemExit(f'No demand panel found ({P.meta}). Run 01_demand_panel.py first.')
    return json.loads(P.meta.read_text())


def load_panels(P):
    """Seattle panel plus the LibriVox panel when it was built (format 'librivox')."""
    import pandas as pd
    parts = [read_parquet(P.panel)]
    if P.panel_librivox.exists():
        parts.append(read_parquet(P.panel_librivox))
    return pd.concat(parts, ignore_index=True)


def stale_inputs(meta):
    """Input files that changed after the panel was built (the taxonomy job may have rewritten them)."""
    out = []
    for f, t in (meta.get('inputs') or {}).items():
        if not os.path.exists(f) or abs(os.path.getmtime(f) - t) > 1e-6:
            out.append(os.path.basename(f))
    return out


def sim_only(args, name, default):
    """Overrides of record sizes (draws, resamples) are allowed only in simulation runs."""
    v = getattr(args, name)
    if v is None:
        return default
    if not args.sim:
        raise SystemExit(f'--{name.replace("_", "-")} may only be used with --sim; real runs use the record value ({default}).')
    return v


def start(step, ap):
    """Parse options, check the step order and the panel, and return (args, paths, panel meta, warnings)."""
    args = ap.parse_args()
    P = Paths(args.sim)
    meta = load_meta(P)
    require_previous(P, step, meta, args.allow_dev_taxonomy)
    warn = []
    st = stale_inputs(meta)
    if st:
        warn.append(f'inputs changed since the panel was built ({", ".join(st)}); consider rerunning 01_demand_panel.py')
    if meta.get('inputs_changed_during_build'):
        warn.append('inputs changed while the panel was being built; rerun 01_demand_panel.py')
    for w in warn:
        print('WARNING:', w, flush=True)
    return args, P, meta, warn


# ---------------- step order ----------------
def report_field(path, field):
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith(f'- {field}:'):
            return line.split(':', 1)[1].strip().strip('`')
    return None


def require_previous(P, step, meta, allow_dev=False):
    """Refuse to run when the previous step's report is missing or was made on another panel build."""
    prev = ORDER[ORDER.index(step) - 1]
    rp = P.report(prev)
    if not rp.exists():
        raise SystemExit(f'Step {step} refuses to run: the report of step {prev} ({rp.name}) is missing. '
                         f'Run the steps in order: {", ".join(ORDER)}.')
    built = report_field(rp, 'panel build')
    if built != meta['build_id']:
        raise SystemExit(f'Step {step} refuses to run: {rp.name} was made on panel build {built}, '
                         f'but the current panel is {meta["build_id"]}. Rerun step {prev} first.')
    if meta.get('development') and not allow_dev:
        raise SystemExit(f'Step {step} refuses to run: the demand panel was built from the taxonomy v2 development '
                         'fallback (no taxonomy_v3/work_theme.parquet yet). Rebuild it with 01_demand_panel.py once '
                         'v3 is ready, or pass --allow-dev-taxonomy for a non-final run.')
    return rp


def write_report(P, step, title, body_lines, S, meta, extra=None):
    """Markdown report with a fixed header that later steps check."""
    head = [f'# {title}', '',
            f'- step: {step}',
            f'- written: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            f'- mode: {"SIMULATED data (test run)" if P.sim else "real data"}',
            f'- panel build: `{meta["build_id"]}`',
            f'- taxonomy: {meta.get("taxonomy")}{" (DEVELOPMENT fallback, not final)" if meta.get("development") else ""}',
            f'- settings record SHA-256: `{S.sha256}`',
            f'- addenda applied: {", ".join(a[0] for a in S.addenda) or "none"}']
    for k, v in (extra or {}).items():
        head.append(f'- {k}: {v}')
    text = '\n'.join(head + [''] + list(body_lines)) + '\n'
    path = P.report(step)
    with open(str(path) + '.part', 'w') as f:
        f.write(text)
    os.replace(str(path) + '.part', path)
    return path


def build_id(parts):
    h = hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:12]
    return f'{time.strftime("%Y%m%d-%H%M%S")}-{h}'


def md_table(df, floatfmt='{:.3f}'):
    """Small Markdown table without extra dependencies (integers stay integers, NaN shows as blank)."""
    import numpy as np
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '| ' + ' | '.join('---' for _ in cols) + ' |']
    for i in range(len(df)):
        cells = []
        for c in cols:
            v = df[c].iloc[i]
            if isinstance(v, (float, np.floating)):
                cells.append('' if v != v else floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return out
