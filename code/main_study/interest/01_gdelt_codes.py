# 01. GDELT GKG theme codes: readable text, family, rule-based exclusions, and similarity to every theme value.
# Steps
#  1) One row per code with its volume (all mentions 2017-01 to 2021-06, weeks present).
#  2) Readable text: family prefixes stripped (WB_1234_, TAX_FNCACT_, EPU_POLICY_, CRISISLEX_T03_, UNGP_, SOC_, ECON_ ...),
#     lowercased, underscores to spaces, glued words split (CLIMATECHANGE -> climate change) with a word list built
#     from the codes themselves plus the system dictionary, a few acronyms spelled out, repeated words removed.
#  3) Family rules (_gdelt_rules.FAMILY_RULES): codes that are lists of actors or entities rather than topics
#     (job titles, ethnic and national groups, party, militant and aid-group names, weapons, military ranks, species,
#     currencies, food commodities, place types) are excluded unless whitelisted by hand (_gdelt_rules.ALLOW).
#  4) Embedding: 'books about <text>' with the taxonomy model, centered with the taxonomy's own mean and compared by
#     cosine with every theme value (specific and general), in the same space as the taxonomy embeddings.
# Output: data/db/interest/gdelt/codes.parquet (one row per code with text, family, rule, top-3 values and cosines)
import re, numpy as np, pandas as pd, pyarrow.parquet as pq
from _ci import D, GD, load_taxonomy, value_space, embed, save_parquet
import _gdelt_rules as R

raw = pq.read_table(f'{D}/raw/gdelt_weekly_2017_2021H1.parquet').to_pandas(ignore_metadata=True)
C = raw.groupby('theme').agg(mentions=('mentions', 'sum'), weeks=('week', 'nunique'), first_week=('week', 'min'),
                             last_week=('week', 'max')).reset_index().rename(columns={'theme': 'code'})
C['mean_weekly'] = C.mentions / raw.week.nunique()

# ---- family and readable text ----
def family(c):
    for name, rx in R.FAMILIES:
        if re.match(rx, c):
            return name
    return 'OTHER'


C['family'] = C.code.map(family)

# word list for splitting glued tokens (CLIMATECHANGE -> climate change): dictionary words of 4+ letters, their simple
# inflections, and protected modern words. Disease names are never split (medical words are not in the dictionary).
try:
    dict_words = {w.strip().lower() for w in open('/usr/share/dict/words') if len(w.strip()) >= 4}
except OSError:
    dict_words = set()
SUFFIXES = ('s', 'es', 'ed', 'ing', 'ers', 'er', 'ies', 'ism', 'ist', 'ists', 'ly', 'ation', 'ations', 'al')
SHORT = {'at', 'of', 'in', 'on', 'to', 'an', 'and', 'for', 'the', 'oil', 'gas', 'war', 'law', 'tax', 'aid', 'gun', 'art', 'sea', 'sex', 'big'}


def is_word(w):
    if w in R.EXTRA_WORDS or w in dict_words:
        return True
    return any(w.endswith(x) and len(w) - len(x) >= 3 and (w[:-len(x)] in dict_words or w[:-len(x)] + 'e' in dict_words or
                                                          w[:-len(x)] + 'y' in dict_words) for x in SUFFIXES)


def split_glued(tok):
    """'climatechange' -> 'climate change'. Known words (with simple inflections) are kept whole; otherwise the split
    with the fewest pieces wins, each piece a known word of 3+ letters or a short function word."""
    if len(tok) < 9 or is_word(tok):
        return tok
    n = len(tok); best = [None] * (n + 1); best[0] = []
    for i in range(1, n + 1):
        for j in range(max(0, i - 25), i):
            piece = tok[j:i]
            if piece == tok or best[j] is None:
                continue
            if (len(piece) >= 3 and is_word(piece)) or piece in SHORT:
                cand = best[j] + [piece]
                if best[i] is None or len(cand) < len(best[i]):
                    best[i] = cand
    return ' '.join(best[n]) if best[n] and len(best[n]) > 1 else tok


def readable(c):
    if c in R.TEXT_FIX:
        return R.TEXT_FIX[c]
    s = c.replace('SELF_IDENTIFIED_', '').replace('_SELF_IDENTIFIED', '')
    for rx, rep in R.STRIP:
        s2 = re.sub(rx, rep, s)
        if s2 != s:
            s = s2
            break
    no_split = c.startswith(('TAX_DISEASE_', 'TAX_CHRONICDISEASE_'))
    words = []
    for t in s.lower().split('_'):
        if not t:
            continue
        t = R.ACRONYMS.get(t, t)
        words.extend(t.split() if (' ' in t or no_split) else split_glued(t).split())
    out = []
    for w in words:                               # 'migration fear fear' -> 'migration fear'
        if not out or out[-1] != w:
            out.append(w)
    return ' '.join(out).strip() or c.lower()


C['text'] = C.code.map(readable)

# ---- family rules ----
def rule(row):
    if row.code in R.ALLOW:
        return ''
    for name, rx, why in R.FAMILY_RULES:
        if re.match(rx, row.code):
            return name
    return ''


C['rule_excluded'] = C.apply(rule, axis=1)

# ---- similarity to every theme value ----
V, _ = load_taxonomy()
EV, mu = value_space(V)
EC = embed([f'books about {t}' for t in C.text]) - mu
EC /= np.linalg.norm(EC, axis=1, keepdims=True)
S = EC @ EV.T
order = np.argsort(-S, axis=1)[:, :3]
vals = V.theme.to_numpy(); nodes = V.node_id.to_numpy()
for k in range(3):
    C[f'v{k + 1}'] = vals[order[:, k]]
    C[f'n{k + 1}'] = nodes[order[:, k]]
    C[f's{k + 1}'] = S[np.arange(len(C)), order[:, k]]
# margin to the best value in a different narrow/mid node (a code close to two unrelated nodes is ambiguous)
best_other = []
for i in range(len(C)):
    n1 = nodes[order[i, 0]]
    o = np.argsort(-S[i])
    j = next(j for j in o if nodes[j] != n1)
    best_other.append(S[i, j])
C['s_other_node'] = best_other
C['margin'] = C.s1 - C.s_other_node
save_parquet(C, f'{GD}/codes.parquet')
np.save(f'{GD}/code_value_cos.npy', S.astype(np.float32))
print('codes', len(C), 'families', C.family.value_counts().to_dict())
print('excluded by family rules', (C.rule_excluded != '').sum(), C[C.rule_excluded != ''].rule_excluded.value_counts().to_dict())
print('mentions share excluded by rules', round(C[C.rule_excluded != ''].mentions.sum() / C.mentions.sum(), 3))
