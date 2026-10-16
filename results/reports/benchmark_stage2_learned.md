# Learned categories against subject-heading themes (stage 2f, demand-only pipelines, horizon 1)

Written 2026-10-15 19:21. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (2f, f1). The two category sets have different series; values are compared side by side only.

source | formats | level | series | rows | months | dropped
learned from book text | print and ebook | middle | 171 | 13063 | 88 | 
subject-heading themes | print and ebook | middle | 170 | 12752 | 88 | 
learned from book text | print and ebook | narrow | 438 | 31205 | 88 | 
subject-heading themes | print and ebook | narrow | 340 | 23329 | 88 | 
learned from book text | audiobooks | middle | 76 | 5898 | 83 | 
subject-heading themes | audiobooks | middle | 82 | 6272 | 83 | 
learned from book text | audiobooks | narrow | 162 | 11918 | 83 | 
subject-heading themes | audiobooks | narrow | 143 | 9066 | 83 | 


## print and ebook, middle themes

 | learned AvgRelMAE | subject AvgRelMAE | learned volume-weighted | subject volume-weighted | learned rank corr. | subject rank corr. | learned surge AP | subject surge AP | learned error % | subject error %
naive | 1.0 | 1.0 | 1.0 | 1.0 |  |  |  |  | 6.092 | 4.389
seasonal_naive | 2.085 | 2.053 | 2.147 | 1.947 | 0.206 | 0.18 | 0.03 | 0.04 | 12.86 | 9.061
revert6 | 1.345 | 1.329 | 1.4 | 1.364 | 0.155 | 0.13 | 0.015 | 0.004 | 8.279 | 6.032
ridge_D | 1.01 | 0.999 | 1.048 | 1.005 | 0.22 | 0.199 | 0.045 | 0.014 | 6.082 | 4.357
catboost_D | 1.114 | 1.089 | 1.388 | 1.222 | 0.187 | 0.203 | 0.024 | 0.197 | 6.578 | 4.598
lightgbm_D | 1.044 | 0.969 | 1.231 | 0.974 | 0.213 | 0.269 | 0.037 | 0.266 | 6.233 | 4.124
ridgechg_D | 1.004 | 0.99 | 1.037 | 0.993 | 0.222 | 0.203 | 0.046 | 0.017 | 6.053 | 4.321
lgbmchg_D | 0.996 | 0.937 | 1.006 | 0.899 | 0.229 | 0.288 | 0.053 | 0.292 | 6.026 | 4.017
catchg_D | 1.006 | 0.94 | 1.029 | 0.907 | 0.226 | 0.28 | 0.031 | 0.266 | 6.065 | 4.037
chronos | 0.96 | 0.927 | 1.002 | 0.908 | 0.297 | 0.295 | 0.141 | 0.382 | 5.782 | 3.944
chronos2 | 0.916 | 0.905 | 0.93 | 0.872 | 0.339 | 0.325 | 0.167 | 0.394 | 5.537 | 3.858
median_s2_demand | 0.975 | 0.933 | 0.986 | 0.903 | 0.249 | 0.288 | 0.047 | 0.279 | 5.91 | 4.007


- confidence set, level task (learned): chronos2
- confidence set, level task (subject-heading): chronos2

## print and ebook, narrow themes

 | learned AvgRelMAE | subject AvgRelMAE | learned volume-weighted | subject volume-weighted | learned rank corr. | subject rank corr. | learned surge AP | subject surge AP | learned error % | subject error %
naive | 1.0 | 1.0 | 1.0 | 1.0 |  |  |  |  | 7.847 | 5.349
seasonal_naive | 1.955 | 2.099 | 2.067 | 1.98 | 0.202 | 0.165 | 0.068 | 0.02 | 15.841 | 11.489
revert6 | 1.264 | 1.308 | 1.328 | 1.347 | 0.181 | 0.15 | 0.03 | 0.008 | 10.401 | 7.215
ridge_D | 0.996 | 0.992 | 1.025 | 0.996 | 0.237 | 0.202 | 0.071 | 0.018 | 7.751 | 5.284
catboost_D | 1.012 | 1.027 | 1.085 | 1.097 | 0.24 | 0.21 | 0.091 | 0.109 | 7.781 | 5.387
lightgbm_D | 0.991 | 0.969 | 1.009 | 0.956 | 0.258 | 0.257 | 0.123 | 0.131 | 7.658 | 5.098
ridgechg_D | 0.993 | 0.986 | 1.018 | 0.988 | 0.234 | 0.202 | 0.074 | 0.019 | 7.732 | 5.252
lgbmchg_D | 0.978 | 0.958 | 0.984 | 0.925 | 0.262 | 0.262 | 0.127 | 0.14 | 7.569 | 5.042
catchg_D | 0.984 | 0.956 | 1.007 | 0.929 | 0.253 | 0.254 | 0.115 | 0.131 | 7.599 | 5.039
chronos | 0.948 | 0.95 | 0.984 | 0.925 | 0.286 | 0.265 | 0.228 | 0.172 | 7.313 | 5.001
chronos2 | 0.911 | 0.928 | 0.922 | 0.885 | 0.327 | 0.291 | 0.25 | 0.18 | 7.046 | 4.893
median_s2_demand | 0.963 | 0.945 | 0.97 | 0.911 | 0.273 | 0.27 | 0.135 | 0.14 | 7.459 | 4.991


- confidence set, level task (learned): chronos2
- confidence set, level task (subject-heading): chronos2

## audiobooks, middle themes

 | learned AvgRelMAE | subject AvgRelMAE | learned volume-weighted | subject volume-weighted | learned rank corr. | subject rank corr. | learned surge AP | subject surge AP | learned error % | subject error %
naive | 1.0 | 1.0 | 1.0 | 1.0 |  |  |  |  | 5.806 | 4.388
seasonal_naive | 2.058 | 2.102 | 2.117 | 2.048 | 0.186 | 0.172 | 0.038 | 0.066 | 11.974 | 9.134
revert6 | 1.26 | 1.268 | 1.353 | 1.269 | 0.216 | 0.187 | 0.021 | 0.008 | 7.269 | 5.686
ridge_D | 1.017 | 0.996 | 1.063 | 1.014 | 0.188 | 0.198 | 0.028 | 0.013 | 5.835 | 4.345
catboost_D | 1.173 | 1.132 | 1.486 | 1.367 | 0.173 | 0.202 | 0.018 | 0.202 | 6.614 | 4.818
lightgbm_D | 1.064 | 1.02 | 1.264 | 1.058 | 0.184 | 0.212 | 0.029 | 0.215 | 6.051 | 4.378
ridgechg_D | 1.013 | 0.991 | 1.053 | 1.004 | 0.18 | 0.196 | 0.027 | 0.017 | 5.82 | 4.327
lgbmchg_D | 1.031 | 0.995 | 1.072 | 0.996 | 0.201 | 0.221 | 0.047 | 0.254 | 5.902 | 4.278
catchg_D | 1.04 | 0.983 | 1.075 | 0.991 | 0.181 | 0.205 | 0.026 | 0.258 | 5.947 | 4.231
chronos | 0.999 | 0.999 | 1.029 | 0.997 | 0.223 | 0.186 | 0.035 | 0.231 | 5.728 | 4.305
chronos2 | 1.001 | 0.991 | 1.03 | 0.993 | 0.234 | 0.203 | 0.056 | 0.307 | 5.758 | 4.256
median_s2_demand | 0.989 | 0.968 | 1.026 | 0.972 | 0.212 | 0.247 | 0.043 | 0.299 | 5.681 | 4.17


- confidence set, level task (learned): lgbmchg_D, catchg_D, chronos, chronos2, median_s2_demand
- confidence set, level task (subject-heading): median_s2_demand

## audiobooks, narrow themes

 | learned AvgRelMAE | subject AvgRelMAE | learned volume-weighted | subject volume-weighted | learned rank corr. | subject rank corr. | learned surge AP | subject surge AP | learned error % | subject error %
naive | 1.0 | 1.0 | 1.0 | 1.0 |  |  |  |  | 6.913 | 5.263
seasonal_naive | 2.031 | 2.147 | 2.082 | 2.067 | 0.183 | 0.159 | 0.033 | 0.033 | 14.371 | 11.342
revert6 | 1.239 | 1.261 | 1.298 | 1.294 | 0.228 | 0.188 | 0.018 | 0.012 | 8.645 | 6.757
ridge_D | 1.007 | 0.99 | 1.04 | 1.007 | 0.19 | 0.185 | 0.022 | 0.012 | 6.939 | 5.189
catboost_D | 1.051 | 1.049 | 1.146 | 1.202 | 0.212 | 0.201 | 0.028 | 0.079 | 7.188 | 5.442
lightgbm_D | 1.005 | 1.012 | 1.039 | 1.031 | 0.212 | 0.21 | 0.065 | 0.115 | 6.913 | 5.225
ridgechg_D | 1.004 | 0.989 | 1.031 | 1.0 | 0.184 | 0.181 | 0.024 | 0.014 | 6.924 | 5.182
lgbmchg_D | 1.004 | 0.999 | 1.035 | 1.001 | 0.214 | 0.21 | 0.064 | 0.156 | 6.908 | 5.164
catchg_D | 1.01 | 0.983 | 1.042 | 0.985 | 0.203 | 0.206 | 0.059 | 0.143 | 6.933 | 5.109
chronos | 0.998 | 0.999 | 1.012 | 1.008 | 0.21 | 0.19 | 0.062 | 0.175 | 6.864 | 5.18
chronos2 | 0.996 | 1.0 | 1.011 | 1.0 | 0.221 | 0.183 | 0.068 | 0.2 | 6.849 | 5.182
median_s2_demand | 0.977 | 0.972 | 0.994 | 0.974 | 0.227 | 0.229 | 0.08 | 0.161 | 6.73 | 5.042


- confidence set, level task (learned): median_s2_demand
- confidence set, level task (subject-heading): median_s2_demand

