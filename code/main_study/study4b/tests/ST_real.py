# Reads the real Study 3 shift effects once (tests only).
import pandas as pd
from helpers import B
import _settings as ST
_C = {}
def effects():
    if 'e' not in _C:
        _C['e'] = pd.read_parquet(ST.DB / 'study3' / 'shift_effects.parquet', columns=['source', 'analysis', 'sc_ok', 'sc_effect_p', 'node_id', 'format', 'm0'])
    return _C['e']
