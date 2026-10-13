# Adapter for the interest-side inputs (made by code/main_study/interest/, another agent). This is the only place
# that knows their file names and columns; if they change, change this module and nothing else.
#
# Shifts: data/db/interest/shifts.parquet. Two layouts are accepted.
#  (a) The interest side's own table (code/main_study/interest/08_shift_labels.py): source, level (1/2/3), node_id,
#      start_week (Monday), label (sustained / intermediate / fading, or interrupted / censored when no real-time label
#      could be given), size, dur_rt (real-time duration count), seasonal, large, and for GDELT label_gdelt_scaled and
#      size_gdelt_scaled (labels with the GDELT-scaled durations); optional whole_duration, strict_start, main_set.
#  (b) The minimal layout: source, node_id, level, start_week, duration_class, size, large, seasonal, optional
#      duration_count.
# Both are turned into (b) plus m0 (month index of month 0), shift_id and `labelled` (a record duration class).
#
# Weekly GDELT tone: data/db/interest/gdelt/weekly_node.parquet: node_id, level, week (Monday), tone, positive,
#   negative (mention-weighted), mentions, partial_week. Columns tone_pos / tone_neg are accepted as well.
import numpy as np, pandas as pd
from _files import LEVEL_NAME, read_parquet
from _build import month_of_date
from _settings import find_key

SHIFTS_FILE = 'shifts.parquet'
TONE_FILE = 'gdelt/weekly_node.parquet'
SCALING_FILE = 'gdelt_duration_scaling.json'
CHECKPOINT_REPORT = 'main_study_checkpoint_2_interest.md'
SHIFT_COLUMNS = ['source', 'node_id', 'level', 'start_week', 'duration_class', 'size', 'large', 'seasonal']
CLASSES = ('sustained', 'intermediate', 'fading')          # the record's duration classes
UNLABELLED = ('interrupted', 'censored')                   # interest-side outcomes without a record class


def _mondays(x, what):
    d = pd.to_datetime(x).dt.normalize()
    if (d.dt.weekday != 0).any():
        raise SystemExit(f'{what}: some dates are not Mondays (ISO week start expected)')
    return d


def gdelt_thresholds(S):
    """Duration thresholds for GDELT labels once the record carries them (addendum), else None."""
    g = S.gdelt_durations
    if not g:
        return None
    smin, fmax = find_key(g, 'sustained_min'), find_key(g, 'fading_max')
    return None if smin is None or fmax is None else (int(smin), int(fmax))


def from_interest_schema(X, S):
    """Layout (a) -> layout (b). GDELT rows take the GDELT-scaled label and size when present (record:
    gdelt_durations); their real-time count is then not comparable with the scaled thresholds and is not checked.
    NOT IN RECORD (adapter): a shift without a seasonal verdict (NaN) is treated as not seasonal."""
    if 'duration_class' in X.columns:
        return X
    X = X.copy()
    gd = X.source.astype(str).str.lower().eq('gdelt').to_numpy()
    scaled = gd & X.label_gdelt_scaled.notna().to_numpy() if 'label_gdelt_scaled' in X.columns else np.zeros(len(X), bool)
    X['duration_class'] = np.where(scaled, X.get('label_gdelt_scaled', X.label), X.label)
    X['size'] = np.where(scaled, X.get('size_gdelt_scaled', X['size']), X['size'])
    X['duration_count'] = np.where(scaled, np.nan, X['dur_rt'].astype(float)) if 'dur_rt' in X.columns else np.nan
    X['large'] = X['size'].astype(float) >= S.large_ratio
    X['seasonal'] = X.seasonal.astype('boolean').fillna(False).astype(bool)
    X['label_rule'] = np.where(scaled, 'GDELT-scaled durations', 'record durations')
    return X


def normalise_shifts(X, S):
    """Check and normalise a shifts table; adds m0, shift_id and labelled."""
    X = from_interest_schema(X, S)
    miss = [c for c in SHIFT_COLUMNS if c not in X.columns]
    if miss:
        raise SystemExit(f'shifts table lacks columns {miss}; expected {SHIFT_COLUMNS}')
    X = X.copy()
    X['source'] = X.source.astype(str).str.lower()
    X['level'] = X.level.map(LEVEL_NAME)
    if X.level.isna().any():
        raise SystemExit('shifts table: unknown level values')
    X['start_week'] = _mondays(X.start_week, 'shifts.start_week')
    X['duration_class'] = X.duration_class.astype(str).str.lower()
    bad = set(X.duration_class) - set(CLASSES) - set(UNLABELLED)
    if bad:
        raise SystemExit(f'shifts table: unknown duration classes {bad}')
    X['labelled'] = X.duration_class.isin(CLASSES)
    X['size'] = X['size'].astype(float)
    if (X.loc[X.labelled, 'size'] <= 0).any() or X.loc[X.labelled, 'size'].isna().any():
        raise SystemExit('shifts table: size must be > 0 (peak ratio to normal) for every labelled shift')
    X['large'] = X.large.astype(bool)
    if (X.large != (X['size'] >= S.large_ratio)).any():
        raise SystemExit(f'shifts table: "large" disagrees with size >= {S.large_ratio} (record)')
    X['seasonal'] = X.seasonal.astype(bool)
    # addendum h: Wikipedia shifts flagged by the interest side's quality check (one day carried the week, a
    # desktop-only rise, or a page title shared with a TV series, film, game, song or person) are not tested in the
    # main analysis; they still count in the donor and placebo-year screens, and a robustness run keeps them.
    X['quality_ok'] = X.quality_ok.astype('boolean').fillna(True).astype(bool) if 'quality_ok' in X.columns else True
    X['quality_flag'] = X.quality_flag.fillna('').astype(str) if 'quality_flag' in X.columns else ''
    if 'gdelt_feed_artifact' in X.columns:     # addendum i: GDELT shifts carried by one website, same treatment
        art = X.gdelt_feed_artifact.astype('boolean').fillna(False).astype(bool)
        X.loc[art, 'quality_ok'] = False
        X.loc[art, 'quality_flag'] = (X.loc[art, 'quality_flag'] + ',single_site').str.lstrip(',')
    _check_counts(X, S)
    # month 0 = calendar month containing the shift start week (record).
    # NOT IN RECORD: the week's Monday decides the month when a week spans two months.
    X['m0'] = month_of_date(X.start_week)
    X['shift_id'] = X.source + ':' + X.node_id + ':' + X.start_week.dt.strftime('%Y-%m-%d')
    if X.shift_id.duplicated().any():
        raise SystemExit('shifts table: duplicate (source, node_id, start_week)')
    return X.reset_index(drop=True)


def _check_counts(X, S):
    """Labelled shifts with a real-time count must agree with the duration thresholds (record values for Wikipedia
    and unscaled rows; the appended GDELT values for GDELT rows when the record has them)."""
    if 'duration_count' not in X.columns:
        return
    th = {'record': (S.sustained_min, S.fading_max), 'gdelt': gdelt_thresholds(S)}
    for _, r in X[X.labelled & X.duration_count.notna()].iterrows():
        smin, fmax = th['record'] if r.source != 'gdelt' or th['gdelt'] is None else th['gdelt']
        d = r.duration_count
        cls = 'sustained' if d >= smin else ('fading' if d <= fmax else 'intermediate')
        if cls != r.duration_class:
            raise SystemExit(f'shifts table: {r.source} {r.node_id} {r.start_week:%Y-%m-%d} has class {r.duration_class} '
                             f'but a real-time count of {d:g} weeks')


def load_shifts(P, S):
    """Shifts table, normalised; None when the interest side has not written it yet."""
    f = P.interest / SHIFTS_FILE
    if not f.exists():
        return None
    return normalise_shifts(read_parquet(f), S)


def normalise_tone(T):
    """NOT IN RECORD (adapter): partial GDELT weeks are treated as missing, as on the interest side."""
    T = T.rename(columns={'positive': 'tone_pos', 'negative': 'tone_neg'}).copy()
    need = ['node_id', 'level', 'week', 'tone', 'tone_pos', 'tone_neg']
    miss = [c for c in need if c not in T.columns]
    if miss:
        raise SystemExit(f'tone table lacks columns {miss}; expected {need} (or positive / negative)')
    if 'source' in T.columns:
        T = T[T.source.astype(str).str.lower() == 'gdelt']
    T['level'] = T.level.map(LEVEL_NAME)
    T['week'] = _mondays(T.week, 'tone.week')
    if 'partial_week' in T.columns:
        T.loc[T.partial_week.astype(bool), ['tone', 'tone_pos', 'tone_neg']] = np.nan
    return T.sort_values(['node_id', 'week']).reset_index(drop=True)


def load_tone(P):
    f = P.interest / TONE_FILE
    if not f.exists():
        return None
    return normalise_tone(read_parquet(f))


def status_line(P):
    """One line for the reports: which interest inputs exist."""
    have = [n for n in (SHIFTS_FILE, TONE_FILE, SCALING_FILE) if (P.interest / n).exists()]
    rep = (P.rep / CHECKPOINT_REPORT).exists()
    return (f'interest inputs present: {", ".join(have) or "none"}; '
            f'interest checkpoint report {"present" if rep else "not yet written"}')


def require_gdelt_durations(S, shifts, step, sim=False):
    """The record appends the GDELT durations before any demand data are read. Refuse while GDELT shifts are
    present and no addendum carries those values (not checked in simulated runs, which read no real demand)."""
    if not sim and shifts is not None and (shifts.source == 'gdelt').any() and S.gdelt_durations is None:
        raise SystemExit(f'Step {step} refuses to run: the record says the GDELT shift durations, computed from interest '
                         'data alone, are appended to it before any demand data are read, and no addendum in '
                         'prereg/addenda/ carries them yet (the interest side proposes them in '
                         f'data/db/interest/{SCALING_FILE}). Add that addendum (and a DEVIATIONS.md line) first.')


def shifts_for_step(P, S, without_shifts, step):
    """Shifts table for a step whose donor rule needs it. Without the table the step refuses, unless
    --without-shifts was given; then the report flags that the shift part of the donor rule was not applied."""
    X = load_shifts(P, S)
    if X is None and not without_shifts:
        raise SystemExit(f'Step {step} refuses to run: the donor rule (no shift start in months '
                         f'{S.donor_no_shift[0]} to +{S.donor_no_shift[1]}) needs {P.interest / SHIFTS_FILE}, which does '
                         'not exist yet. Pass --without-shifts to run without that part of the rule; the report then '
                         'flags it, and it must be logged in prereg/DEVIATIONS.md if the results are kept.')
    if without_shifts:
        return None, ('NOT APPLIED (--without-shifts): donors, placebo years and power draws were not screened for '
                      'interest shifts. Log this in prereg/DEVIATIONS.md if these results are kept.')
    require_gdelt_durations(S, X, step, P.sim)
    return X, f'applied ({len(X)} shifts in the interest table, all classes and both sources)'
