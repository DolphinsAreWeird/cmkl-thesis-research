"""Cap library threads at 3 (8 GB Mac, shared with other jobs) without editing the old scripts."""
import os
os.environ.setdefault('OMP_NUM_THREADS','3'); os.environ.setdefault('VECLIB_MAXIMUM_THREADS','3'); os.environ.setdefault('OPENBLAS_NUM_THREADS','3')
import lightgbm as lgb
from catboost import CatBoostRegressor
import functools, catboost
for n in ('LGBMRegressor','LGBMClassifier','LGBMRanker'): setattr(lgb,n,functools.partial(getattr(lgb,n),n_jobs=3))
catboost.CatBoostRegressor=functools.partial(CatBoostRegressor,thread_count=3)
