# 06. Brisbane replication: assemble data/reports/brisbane_replication.md from the step reports and tables. Run with `python -I`.
import sys, pathlib, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import _bris as B

REP, DB = B.REP, B.DB
rd = lambda n: (REP / n).read_text()
def body(txt):                       # drop the title and header bullets of a step report, demote headings by one level
    lines = txt.split('\n')[1:]
    return '\n'.join(('#' + l if l.startswith('#') else l) for l in lines).strip()
P = pd.read_csv(DB / 'pooled_effects.csv')
m = P[P.set.str.startswith('main') & (P.level == 'both')].set_index('duration_class')
se1 = (m.loc['sustained', 'ci_high'] - m.loc['sustained', 'ci_low']) / 3.92
mde1 = 2.49 * se1
Y = pd.read_csv(DB / 'match_by_year.csv')
dl = rd('brisbane_download_profile.md').split('\n', 2)[2].strip()
power = pd.read_csv(DB / 'power_summary.csv')
ctrl = pd.read_csv(DB / 'controls.csv')
h2 = [l for l in rd('brisbane_04_hypotheses.md').split('\n') if l.startswith('- **H2')][0]
h2line = re.sub(r'\*\*H2 (.*?)\*\*: ', lambda mm: mm.group(1).lower() + ': ', h2).lstrip('- ')
text = f'''# Brisbane replication: do sustained rises in Wikipedia interest predict more borrowing in a second city?

Khant Phyo Wai, student ID 01323050. Written {time.strftime("%Y-%m-%d %H:%M")}. Record: `prereg/brisbane_replication_settings_2026-10-15.json` (SHA-256 `{B.SHA}`, checked on every run). Code: `code/brisbane/` (steps 01 to 06; the Study 3b count model and inference are reused unchanged from `code/main_study/study3b/`). Outputs: `data/db/brisbane/`. Every choice the record does not make is a row in `prereg/DEVIATIONS.md` (Brisbane replication section).

## What this is

A second-city replication of the Seattle theme-level design: Brisbane City Council library loans (Australia, CC BY 4.0), matched to Seattle works to inherit theme profiles, tested against the same global English Wikipedia interest shifts. Brisbane publishes three sampled days a month (the 7th to 9th), so each month is a small sample, and the loans per theme are small. That limits what can be detected (see power).

## Short answer

- Data: Brisbane loans June 2015 to December 2025, {int(Y.loans.sum()):,} loans, {100 * Y.matched_loans.sum() / Y.loans.sum():.1f}% matched to Seattle works ({100 * Y.loans_with_theme_profile.sum() / Y.loans.sum():.1f}% carry a theme profile). {int(body(rd("brisbane_02_panel.md")).count("source file") + 0)} placeholder removed below.
- Positive controls: neither control can be tested as the record specifies, because Brisbane was closed or had no titles in most of the months 0 to +2 (details below). They are reported, not passed.
- H1 (sustained rises, pooled tau above 0): {"supported" if (m.loc["sustained","tau_mean"] > 0 and m.loc["sustained","ci_low"] > 0) else "not supported"}: tau {m.loc["sustained","tau_mean"]:.3f} (95% interval {m.loc["sustained","ci_low"]:.3f} to {m.loc["sustained","ci_high"]:.3f}), {int(m.loc["sustained","tests"])} tests.
- H2 (sustained minus fading above 0): {h2line}
- Power: with this little data a single theme test needs about +50% (middle) to +100% (narrow) loans to be found; the pooled sustained estimate has a 95% interval of about plus or minus {1.96 * se1:.2f} in log units, so the smallest pooled lift it could reliably show (80% power, one sided 5%) is about {100 * (np.exp(mde1) - 1):.0f}%. A null here is therefore weak evidence against a small effect, not strong evidence against it.

## Download

{dl}

The distinct-day counts in this list are UTC dates, which include a few stray dates with a handful of loans each; the sampled days by Brisbane local date (about 36 a year, three a month) are in the match table below.

All years are in `data/raw/brisbane/` as parquet with the columns of the 2023 to 2025 files. New files for 2015 to 2022: about 0.17 GB. Raw CSVs (457 MB) were deleted after conversion.

{body(rd("brisbane_02_panel.md"))}

{body(rd("brisbane_03_controls.md"))}

{body(rd("brisbane_04_hypotheses.md"))}

{body(rd("brisbane_05_power.md"))}

## Reading and limits

- Months and sampling: three days a month; loans per theme per month are in the tens, so each test has a wide error. The model's dispersion and the placebo-category rank handle this, and the false-positive rate of the tests in the power run is about 5% as it should be.
- Match rate: about one third of loans match a Seattle work by exact normalised title and author family name; about 15% of loans have no author (magazines, DVDs), and the rest are mostly books Seattle never lent or spelled differently. Matched titles are a selected sample of the collection (popular, English, published in the US market); this is the record's rule and was not tuned.
- Months out of the data: closures (April to June 2020, August 2021, April 2023, March 2025) and five months where the source file has few or no titles (March and August 2017, July 2020, October 2022, August 2023). The title rule was added after the first control table; see DEVIATIONS.
- Controls: the 2020 closures fall inside both control windows, so the record's primary window has only one usable month each. The secondary window 0 to +5 is shown for information only.
- Brisbane does not publish item type in the 2023 to 2025 files, so the print versus other split was not possible.
- The Wikipedia interest series is global English, as in the record; Brisbane readers are a small part of it.
'''
text = text.replace(f' {int(body(rd("brisbane_02_panel.md")).count("source file") + 0)} placeholder removed below.', '')
(REP / 'brisbane_replication.md').write_text(text)
print(text[:3500])
