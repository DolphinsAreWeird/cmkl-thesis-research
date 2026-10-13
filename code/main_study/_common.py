# Shared helpers for the main-study scripts. Paths come from code/config.py (D = data folder).
import sys, os, re, json, unicodedata, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))   # the parent code/ folder
from config import D, UA   # noqa: E402

RAW = f'{D}/raw/modern'
# Output version: v2 (checkpoint 1, default, unchanged) or v3 (checkpoint 2). Scripts 10+ set TAXO=v3 before importing.
TAXO = os.environ.get('TAXO', 'v2')
OUT = f'{D}/db/taxonomy_{TAXO}'
OUT_V2 = f'{D}/db/taxonomy_v2'
REP = f'{D}/reports'
os.makedirs(OUT, exist_ok=True)

FILES = {'AUDIOBOOK': f'{RAW}/seattle_audiobook.jsonl', 'EBOOK': f'{RAW}/seattle_ebook.jsonl'}
if TAXO != 'v2':
    FILES['BOOK'] = f'{RAW}/seattle_book.jsonl'          # print books (library subject headings)
SNAP = f'{OUT}/spl_snapshot.json'   # fixed line counts, so every later script reads the same rows


def snapshot(refresh=False):
    """Number of complete lines to read per file. The ebook file is still being appended by
    code/seattle.py, so the count is frozen the first time and reused unless refresh=True."""
    if os.path.exists(SNAP) and not refresh:
        return json.load(open(SNAP))
    s = {}
    for fmt, fn in FILES.items():
        size = os.path.getsize(fn)            # bytes present now; a line still being written is not counted
        n = 0; good_bytes = 0
        with open(fn, 'rb') as f:
            while good_bytes < size:
                block = f.read(min(1 << 24, size - good_bytes))
                if not block:
                    break
                k = block.rfind(b'\n')
                if k < 0:
                    break
                n += block.count(b'\n', 0, k + 1); good_bytes += k + 1
                f.seek(good_bytes)
        s[fmt] = dict(lines=n, bytes=good_bytes, taken=time.strftime('%Y-%m-%d %H:%M:%S'))
    json.dump(s, open(SNAP, 'w'), indent=1)
    return s


def iter_rows(fmt, snap=None):
    """Stream rows of one SPL file, stopping at the frozen line count."""
    snap = snap or snapshot()
    n = snap[fmt]['lines']
    with open(FILES[fmt], 'rb') as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            yield json.loads(line)


# ---------- normalization ----------
def ascii_fold(x):
    return unicodedata.normalize('NFKD', str(x)).encode('ascii', 'ignore').decode()

# parenthetical or bracketed edition / format notes, e.g. "(Unabridged)", "[electronic resource]"
FMT_WORDS = (r'unabridged|abridged|dramatized|dramatised|full[- ]cast|mp3|cd|audio ?book|audio|e-?book|'
             r'kindle|large print|movie tie-?in|tv tie-?in|media tie-?in|tie-?in edition|reissue|'
             r'unabridged selections|selections|ebook edition|enhanced edition|enhanced|illustrated edition|'
             r'illustrated|annotated|annotated edition|revised|revised edition|updated|updated edition|'
             r'anniversary edition|\d+(st|nd|rd|th)? anniversary edition|special edition|deluxe edition|'
             r'collector.?s edition|expanded edition|edition|\d+(st|nd|rd|th) edition|first edition|'
             r'second edition|third edition|new edition|international edition|spanish edition|'
             r'english edition|french edition|a novel|novel|ser\.?|series|book club edition|'
             r'young readers.? edition|young readers.? adaptation|adapted for young (readers|people)|'
             r'graphic novel|the graphic novel|book \d+|bk\. \d+|volume \d+|vol\. \d+|no\. \d+|v\. \d+|'
             r'original recording|recorded books|bbc radio|radio dramatization|unabr\.?|abr\.?')
PAREN_RE = re.compile(r'[\(\[]\s*(?:' + FMT_WORDS + r')(?:[^\)\]]*)[\)\]]', re.I)
# OverDrive appends series information after a colon: "Three Days to Dead: Dreg City Series, Book 1"
SERIES_RE = re.compile(r':\s*[^:]*?\b(series|saga|trilogy|chronicles|cycle|sequence|quartet|mysteries|mystery series)\b[^:]*?,?\s*(book|volume|vol\.?|#|no\.?|part)\s*[\w\.\-]+\s*$', re.I)
SERIES_RE2 = re.compile(r':\s*[^:]*?,\s*(book|volume|vol\.?|#|no\.?|part)\s*[\d\.\-]+\s*$', re.I)
TAIL_RE = re.compile(r'\s*[:;,/=]?\s*(a novel|a memoir|a thriller|a mystery|a romance|stories|a novella)\s*$', re.I)
SLASH_RE = re.compile(r'\s+/\s+.*$')   # print records: "Title / by Author"


def clean_title(t):
    """Display title with edition/format and series suffixes removed (keeps the subtitle)."""
    t = str(t or '')
    t = SLASH_RE.sub('', t)
    for _ in range(3):
        t2 = PAREN_RE.sub('', t).strip()
        if t2 == t:
            break
        t = t2
    t = SERIES_RE.sub('', t).strip()
    t = SERIES_RE2.sub('', t).strip()
    t = TAIL_RE.sub('', t).strip()
    return re.sub(r'\s+', ' ', t).strip(' :;,.-')


def norm_text(t):
    """Lowercase, accents removed, punctuation to spaces. Unicode-aware, so Cyrillic, CJK, Korean,
    Arabic etc. are kept (an ASCII-only version turned those titles into empty strings)."""
    t = unicodedata.normalize('NFKD', str(t or ''))
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn').lower().replace('&', ' and ')
    t = re.sub(r"['’`ʼ]", '', t)
    t = re.sub(r'[\W_]+', ' ', t)
    return unicodedata.normalize('NFC', re.sub(r'\s+', ' ', t).strip())


SUB_SPLIT = re.compile(r'\s*[:;：；]\s*|\s+-{1,2}\s+|\s+—\s+')


def title_parts(t):
    """(main title key, subtitle key) from a raw title, after edition/format/series suffixes are removed."""
    c = clean_title(t)
    parts = SUB_SPLIT.split(c, maxsplit=1) if c else ['']
    main = norm_text(parts[0]); sub = norm_text(parts[1]) if len(parts) > 1 else ''
    if len(main) < 2 and sub:          # nothing usable before the colon
        main, sub = norm_text(c), ''
    main = re.sub(r'^(the|a|an) ', '', main)
    return main, sub


def norm_title(t):
    """Main-title key: cleaned, lowercased, punctuation removed, subtitle dropped, leading article dropped."""
    return title_parts(t)[0]


CREATOR_DATES = re.compile(r',?\s*\(?\b(\d{3,4}\??-?(\d{3,4})?\??|b\. ?\d{4}|d\. ?\d{4}|ca\. ?\d{4}|active \d{4}.*)\)?\.?\s*$')
# academic and professional letters after a name; 'ma', 'ms', 'do', 'rd' only count when they follow a comma,
# because they are also surnames (Ling Ma, Anh Do)
DEGREES = {'md', 'phd', 'psyd', 'lmsw', 'lcsw', 'edd', 'mph', 'msw', 'mba', 'jd', 'dmin', 'esq', 'cpa', 'mft', 'lmft', 'lpc', 'pharmd',
           'dvm', 'facs', 'mfa', 'abpp', 'rn', 'bsn', 'msn', 'dnp', 'facp', 'faap', 'np', 'pa', 'dc', 'nd', 'lac', 'cht', 'rdn', 'cdn'}
DEGREES_AFTER_COMMA = DEGREES | {'ma', 'ms', 'do', 'rd', 'ld', 'ba', 'bs', 'msc', 'bsc', 'jr', 'sr', 'ii', 'iii', 'iv', 'dr', 'prof'}


def _letters(x):
    return re.sub(r'[^a-z]', '', ascii_fold(x).lower())


def norm_creator(c):
    """Lowercase 'first last' name: first creator only, life dates, role words and degree letters removed,
    'Last, First' flipped, initials joined ('m c beaton' -> 'mc beaton')."""
    c = str(c or '').strip()
    if not c:
        return ''
    c = re.split(r';|\s+and\s+|\s*&\s*', c, maxsplit=1)[0]         # first creator only
    c = re.sub(r'\(.*?\)', '', c)                                  # fuller form of name
    c = CREATOR_DATES.sub('', c).strip()
    c = re.sub(r'\b(editor|author|narrator|translator|illustrator|ed\.|eds\.|compiler|adapter)\b.*$', '', c, flags=re.I).strip(' ,.')
    parts = [p.strip() for p in c.split(',')]
    keep = [parts[0]] + [p for p in parts[1:] if not all(_letters(t) in DEGREES_AFTER_COMMA for t in p.split() if _letters(t))]
    keep = [p for p in keep if p]
    if len(keep) == 2:                                   # 'Last, First'
        c = f'{keep[1]} {keep[0]}'
    else:
        c = ' '.join(keep)
    c = norm_text(c)
    c = re.sub(r'\b([a-z]) (?=[a-z]\b)', r'\1', c)          # 'm c beaton' -> 'mc beaton'
    toks = [t for t in c.split() if t not in DEGREES and t not in {'jr', 'sr', 'ii', 'iii', 'iv', 'dr', 'mrs', 'mr', 'prof'}]
    return ' '.join(toks)


def creator_match_key(c):
    """Key for grouping a work's records: first and last word of the normalized name, so that middle names and
    middle initials do not split a work ('Octavia E. Butler' = 'Octavia Butler', 'Robin Wall Kimmerer' = 'Robin Kimmerer')."""
    t = c.split()
    if len(t) <= 2:
        return c
    return f'{t[0]} {t[-1]}'


GENERIC_CREATORS = {'', 'various', 'various authors', 'anonymous', 'unknown', 'anon', 'various artists', 'multiple authors'}


def split_subjects(s):
    return [x.strip() for x in str(s or '').split(',') if x.strip()]


def _same_sub(a, b):
    """Two subtitle keys are the same edition family when one is a truncated form of the other, or when
    they share most words and the same numbers (catches punctuation and mojibake differences)."""
    if a.startswith(b) or b.startswith(a):
        return True
    ta, tb = set(a.split()), set(b.split())
    if {x for x in ta if x.isdigit()} != {x for x in tb if x.isdigit()}:
        return False
    jac = len(ta & tb) / max(1, len(ta | tb))
    if a.split()[:2] == b.split()[:2] and jac >= 0.7:       # punctuation or mojibake differences
        return True
    # reworded marketing subtitles of one book ('The Epic Story of the Deadliest Plague in History' vs
    # 'The Story of the Deadliest Pandemic in History'); series volumes have short subtitles that differ in the first word
    return a.split()[0] == b.split()[0] and min(len(a.split()), len(b.split())) >= 5 and jac >= 0.5


def assign_work_keys(title_main, title_sub, creator_key):
    """Work key per record. Records with the same main title and creator are one work when their
    subtitles form at most one family (e.g. 'Leap' and 'Leap: Leaving a Job...'). When they carry two or
    more different subtitle families, the main title is a series or brand name ('Murder, She Wrote: ...',
    'National Geographic Readers: ...'), so each family is its own work and records without a subtitle stay
    on the bare title. Generic or missing creators always keep the full title, so anthologies are not merged."""
    import pandas as pd
    d = pd.DataFrame({'m': list(title_main), 's': list(title_sub), 'c': list(creator_key)})
    fam = {}                       # (m, c, sub) -> family representative
    for (m, c), subs in d[d.s != ''].groupby(['m', 'c']).s:
        reps = []
        for sub in sorted(set(subs), key=lambda x: (-len(x), x)):     # fixed order, so runs are reproducible
            for r in reps:
                if _same_sub(r, sub):
                    fam[(m, c, sub)] = r; break
            else:
                reps.append(sub); fam[(m, c, sub)] = sub
        if len(reps) <= 1:
            for sub in sorted(set(subs)):
                fam[(m, c, sub)] = None      # one family: merge with the bare title
    keys = []
    for m, sub, c in zip(d.m, d.s, d.c):
        if c in GENERIC_CREATORS:
            keys.append((m + (' : ' + sub if sub else '')) + ' | ' + c)
            continue
        r = fam.get((m, c, sub)) if sub else None
        keys.append((m + ' : ' + r if r else m) + ' | ' + c)
    return keys


def save_json(obj, path):
    with open(path + '.part', 'w') as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(path + '.part', path)


# ---------- sentence embeddings with an on-disk cache ----------
EMB_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
EMB_CACHE = f'{OUT}/_embedding_cache.parquet'


def embed(texts):
    """Unit-length embeddings for a list of texts, cached by exact text."""
    import numpy as np, pandas as pd
    cache = {}
    if os.path.exists(EMB_CACHE):
        c = pd.read_parquet(EMB_CACHE)
        cache = dict(zip(c.text, c.vec))
    todo = sorted({t for t in texts if t not in cache})
    if todo:
        from fastembed import TextEmbedding
        m = TextEmbedding(EMB_MODEL)
        for t, v in zip(todo, m.embed(todo, batch_size=64)):
            cache[t] = np.asarray(v, dtype=np.float32)
        pd.DataFrame({'text': list(cache), 'vec': [np.asarray(v, dtype=np.float32) for v in cache.values()]}).to_parquet(EMB_CACHE, index=False)
    E = np.vstack([np.asarray(cache[t], dtype=np.float32) for t in texts])
    return E / np.linalg.norm(E, axis=1, keepdims=True)
