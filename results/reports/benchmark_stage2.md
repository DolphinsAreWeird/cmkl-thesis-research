# Method benchmark, stage 2

Written 2026-10-15 19:26. Settings: prereg/addenda_benchmark/2026-10-15_b_stage2_metrics_tasks_pipelines.json (SHA-256 9315927d3df0336a534ea0bd248ed68d1fc9a2c5cd30f0ca5c5d6c71d8169a22) and benchmark_settings_2026-10-15.json. Code: code/main_study/benchmark/ (03_evaluate.py --stage2). Result tables: data/db/benchmark/stage2_results/.
AvgRelMAE is the geometric mean over series of MAE(pipeline) / MAE(repeat last month); intervals resample categories (2,000 draws); the confidence sets use the record settings; the Spearman and surge intervals resample months in blocks of 3.

## Comparisons

name | rows | series | months | pipelines | dropped | surge_base_rate | friedman_stat | friedman_p | nemenyi_cd | k | rise_months_mcs | best_ap
A2 | 36081 | 510 | 88 | 52 |  | 0.007 | 5858.625 | 0.0 | 3.806 | 52 |  | 
B2 | 34819 | 510 | 86 | 33 | lgbmchg_DW;lgbmchg_DWS;ridgechg_DVcur;ridgechg_DVtop;ridgechg_DVnli;ridgechg_DVbk;ridgechg_DVcurdw;lgbmchg_DVcur;lgbmchg_DVtop;lgbmchg_DVnli;lgbmchg_DVbk;lgbmchg_DVcurdw;catchg_DVcur;catchg_DVtop;catchg_DVbk;catchg_DVcurdw;median_s2_behavior;lgbmchg_DVdem;ridgechg_DVdem | 0.015 | 4969.183 | 0.0 | 2.298 | 33 |  | 
C2 | 34031 | 508 | 86 | 33 | lgbmchg_DW;lgbmchg_DWS;ridgechg_DVcur;ridgechg_DVtop;ridgechg_DVnli;ridgechg_DVbk;ridgechg_DVcurdw;lgbmchg_DVcur;lgbmchg_DVtop;lgbmchg_DVnli;lgbmchg_DVbk;lgbmchg_DVcurdw;catchg_DVcur;catchg_DVtop;catchg_DVbk;catchg_DVcurdw;median_s2_behavior;lgbmchg_DVdem;ridgechg_DVdem | 0.022 | 4375.574 | 0.0 | 2.303 | 33 |  | 
D2_h1 | 15338 | 225 | 83 | 52 |  | 0.007 | 2077.489 | 0.0 | 5.73 | 52 |  | 
D2_h2 | 14896 | 225 | 81 | 33 | lgbmchg_DW;lgbmchg_DWS;ridgechg_DVcur;ridgechg_DVtop;ridgechg_DVnli;ridgechg_DVbk;ridgechg_DVcurdw;lgbmchg_DVcur;lgbmchg_DVtop;lgbmchg_DVnli;lgbmchg_DVbk;lgbmchg_DVcurdw;catchg_DVcur;catchg_DVtop;catchg_DVbk;catchg_DVcurdw;median_s2_behavior;lgbmchg_DVdem;ridgechg_DVdem | 0.012 | 1496.143 | 0.0 | 3.46 | 33 |  | 
D2_h3 | 14662 | 224 | 80 | 33 | lgbmchg_DW;lgbmchg_DWS;ridgechg_DVcur;ridgechg_DVtop;ridgechg_DVnli;ridgechg_DVbk;ridgechg_DVcurdw;lgbmchg_DVcur;lgbmchg_DVtop;lgbmchg_DVnli;lgbmchg_DVbk;lgbmchg_DVcurdw;catchg_DVcur;catchg_DVtop;catchg_DVbk;catchg_DVcurdw;median_s2_behavior;lgbmchg_DVdem;ridgechg_DVdem | 0.017 | 1187.768 | 0.0 | 3.468 | 33 |  | 
E2_h1 | 12007 | 136 | 91 | 18 |  | 0.139 | 1275.529 | 0.0 | 2.259 | 18 |  | 
E2_h2 | 11871 | 136 | 90 | 18 |  | 0.167 | 1296.188 | 0.0 | 2.259 | 18 |  | 
S1_h1 | 36611 | 510 | 88 | 21 |  | 0.007 | 2862.239 | 0.0 | 1.387 | 21 |  | 
S1_h2 | 35349 | 510 | 86 | 21 |  | 0.015 | 2560.055 | 0.0 | 1.387 | 21 |  | 


### A2. Print and ebook, horizon 1 (main comparison)

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.914 (0.895 to 0.932) | 0.959 | 0.629 | 18.714 | yes | 0.874 (0.841 to 0.905) | 0.916 (0.896 to 0.934) |
| chronos2_bk | 0.917 (0.896 to 0.934) | 0.964 | 0.624 | 19.443 | yes | 0.873 (0.840 to 0.903) | 0.916 (0.895 to 0.934) |
| chronos2_curdw | 0.917 (0.897 to 0.935) | 0.964 | 0.645 | 19.296 | yes | 0.877 (0.844 to 0.907) | 0.919 (0.899 to 0.937) |
| chronos2_nli | 0.918 (0.898 to 0.936) | 0.968 | 0.633 | 19.602 | no | 0.876 (0.843 to 0.906) | 0.918 (0.898 to 0.936) |
| chronos2 | 0.920 (0.900 to 0.938) | 0.966 | 0.618 | 20.600 | no | 0.878 (0.846 to 0.908) | 0.920 (0.899 to 0.938) |
| chronos2_top | 0.920 (0.900 to 0.937) | 0.971 | 0.625 | 20.245 | no | 0.879 (0.846 to 0.908) | 0.921 (0.900 to 0.939) |
| median_s2_all | 0.933 (0.919 to 0.944) | 0.953 | 0.773 | 13.371 | no | 0.892 (0.870 to 0.914) | 0.932 (0.918 to 0.943) |
| median_s2_demand | 0.941 (0.928 to 0.952) | 0.958 | 0.727 | 16.892 | no | 0.907 (0.885 to 0.928) | 0.938 (0.925 to 0.948) |
| median_s2_behavior | 0.941 (0.928 to 0.952) | 0.956 | 0.747 | 16.471 | no | 0.911 (0.889 to 0.931) | 0.939 (0.926 to 0.950) |
| chronos | 0.943 (0.923 to 0.960) | 0.986 | 0.588 | 25.227 | no | 0.916 (0.883 to 0.947) | 0.940 (0.920 to 0.957) |
| catchg_DVnli | 0.950 (0.935 to 0.962) | 0.970 | 0.673 | 22.147 | no | 0.916 (0.892 to 0.941) | 0.947 (0.933 to 0.959) |
| catchg_D | 0.950 (0.937 to 0.962) | 0.971 | 0.684 | 21.380 | no | 0.917 (0.893 to 0.941) | 0.947 (0.934 to 0.958) |
| lgbmchg_D | 0.951 (0.935 to 0.965) | 0.971 | 0.627 | 23.175 | no | 0.911 (0.886 to 0.936) | 0.947 (0.932 to 0.960) |
| catchg_DW | 0.951 (0.938 to 0.963) | 0.969 | 0.669 | 21.955 | no | 0.923 (0.898 to 0.946) | 0.950 (0.936 to 0.961) |
| catchg_DVcur | 0.952 (0.938 to 0.964) | 0.972 | 0.669 | 22.078 | no | 0.924 (0.899 to 0.947) | 0.951 (0.937 to 0.962) |
| catchg_DVbk | 0.952 (0.938 to 0.964) | 0.972 | 0.657 | 21.863 | no | 0.924 (0.900 to 0.948) | 0.951 (0.936 to 0.962) |
| catchg_DVcurdw | 0.952 (0.939 to 0.963) | 0.970 | 0.675 | 21.855 | no | 0.922 (0.899 to 0.945) | 0.950 (0.937 to 0.961) |
| catchg_DVtop | 0.952 (0.939 to 0.964) | 0.971 | 0.661 | 22.602 | no | 0.925 (0.901 to 0.948) | 0.951 (0.937 to 0.962) |
| catchg_DWS | 0.953 (0.940 to 0.964) | 0.970 | 0.678 | 22.384 | no | 0.925 (0.901 to 0.948) | 0.952 (0.940 to 0.963) |
| lgbmchg_DVbk | 0.953 (0.938 to 0.966) | 0.975 | 0.624 | 23.590 | no | 0.922 (0.898 to 0.944) | 0.950 (0.935 to 0.963) |
| catchg_DVdem | 0.954 (0.941 to 0.965) | 0.972 | 0.655 | 22.680 | no | 0.925 (0.901 to 0.948) | 0.951 (0.938 to 0.962) |
| lgbmchg_DW | 0.954 (0.940 to 0.966) | 0.971 | 0.637 | 23.606 | no | 0.920 (0.897 to 0.941) | 0.951 (0.938 to 0.963) |
| lgbmchg_DWS | 0.955 (0.940 to 0.967) | 0.972 | 0.625 | 23.898 | no | 0.919 (0.898 to 0.941) | 0.952 (0.938 to 0.964) |
| lgbmchg_DVcur | 0.955 (0.940 to 0.968) | 0.973 | 0.618 | 24.253 | no | 0.920 (0.898 to 0.942) | 0.952 (0.938 to 0.965) |
| lgbmchg_DVtop | 0.957 (0.943 to 0.969) | 0.972 | 0.624 | 23.755 | no | 0.923 (0.900 to 0.945) | 0.953 (0.938 to 0.965) |
| lgbmchg_DVnli | 0.957 (0.941 to 0.970) | 0.976 | 0.612 | 24.937 | no | 0.922 (0.897 to 0.944) | 0.953 (0.937 to 0.966) |
| lgbmchg_DVcurdw | 0.957 (0.944 to 0.969) | 0.976 | 0.620 | 24.318 | no | 0.922 (0.900 to 0.943) | 0.955 (0.943 to 0.966) |
| median_all | 0.960 (0.947 to 0.971) | 0.967 | 0.669 | 22.700 | no | 0.951 (0.928 to 0.973) | 0.954 (0.942 to 0.965) |
| lgbmchg_DVdem | 0.966 (0.951 to 0.979) | 0.983 | 0.557 | 27.651 | no | 0.931 (0.907 to 0.955) | 0.961 (0.946 to 0.974) |
| invmae_all | 0.967 (0.955 to 0.979) | 0.972 | 0.622 | 25.673 | no | 0.962 (0.935 to 0.989) | 0.962 (0.950 to 0.974) |
| lightgbm_D | 0.969 (0.953 to 0.983) | 0.983 | 0.551 | 27.524 | no | 0.965 (0.933 to 0.997) | 0.963 (0.949 to 0.976) |
| lightgbm_DW | 0.978 (0.961 to 0.992) | 0.988 | 0.535 | 29.716 | no | 0.979 (0.948 to 1.008) | 0.972 (0.956 to 0.985) |
| avg_three_DW | 0.980 (0.967 to 0.991) | 0.976 | 0.606 | 27.920 | no | 1.002 (0.973 to 1.033) | 0.978 (0.965 to 0.991) |
| avg_naive_ridge_D | 0.982 (0.980 to 0.984) | 0.976 | 0.761 | 26.986 | no | 0.984 (0.979 to 0.989) | 0.980 (0.978 to 0.983) |
| ridgechg_D | 0.988 (0.983 to 0.993) | 0.975 | 0.651 | 28.825 | no | 0.991 (0.980 to 1.002) | 0.982 (0.977 to 0.987) |
| ridgechg_DVdem | 0.988 (0.982 to 0.993) | 0.974 | 0.647 | 29.000 | no | 0.991 (0.979 to 1.004) | 0.982 (0.977 to 0.987) |
| ridgechg_DVnli | 0.988 (0.983 to 0.993) | 0.975 | 0.661 | 29.410 | no | 0.991 (0.981 to 1.002) | 0.983 (0.978 to 0.987) |
| ridgechg_DVtop | 0.989 (0.984 to 0.994) | 0.977 | 0.663 | 29.824 | no | 0.994 (0.983 to 1.006) | 0.983 (0.978 to 0.988) |
| ridgechg_DVcur | 0.990 (0.984 to 0.995) | 0.978 | 0.635 | 30.110 | no | 0.995 (0.984 to 1.006) | 0.985 (0.980 to 0.991) |
| ridgechg_DVbk | 0.990 (0.984 to 0.995) | 0.978 | 0.647 | 30.280 | no | 0.995 (0.983 to 1.008) | 0.984 (0.979 to 0.989) |
| ridgechg_DW | 0.990 (0.984 to 0.996) | 0.977 | 0.629 | 29.975 | no | 0.996 (0.984 to 1.007) | 0.985 (0.980 to 0.991) |
| ridgechg_DWS | 0.990 (0.984 to 0.996) | 0.978 | 0.625 | 30.363 | no | 0.997 (0.985 to 1.010) | 0.986 (0.980 to 0.991) |
| ridgechg_DVcurdw | 0.994 (0.988 to 1.000) | 0.982 | 0.618 | 30.765 | no | 1.004 (0.991 to 1.017) | 0.993 (0.985 to 1.002) |
| ridge_D | 0.995 (0.988 to 1.001) | 0.977 | 0.616 | 31.871 | no | 1.001 (0.987 to 1.015) | 0.987 (0.981 to 0.993) |
| ridge_DW | 0.997 (0.991 to 1.005) | 0.979 | 0.592 | 32.943 | no | 1.008 (0.993 to 1.023) | 0.991 (0.984 to 0.997) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 31.925 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| avg_ridge_cat_DW | 1.002 (0.991 to 1.013) | 0.986 | 0.576 | 32.604 | no | 1.050 (1.017 to 1.083) | 1.003 (0.989 to 1.018) |
| avg_ridge_cat_D | 1.005 (0.994 to 1.015) | 0.989 | 0.565 | 32.804 | no | 1.056 (1.022 to 1.091) | 1.005 (0.992 to 1.019) |
| catboost_DW | 1.042 (1.024 to 1.060) | 1.028 | 0.410 | 39.169 | no | 1.150 (1.094 to 1.207) | 1.049 (1.023 to 1.074) |
| catboost_D | 1.047 (1.028 to 1.066) | 1.027 | 0.373 | 39.265 | no | 1.162 (1.101 to 1.225) | 1.055 (1.028 to 1.081) |
| revert6 | 1.315 (1.291 to 1.339) | 1.332 | 0.067 | 49.104 | no | 1.356 (1.325 to 1.390) | 1.268 (1.247 to 1.289) |
| seasonal_naive | 2.083 (2.011 to 2.158) | 2.158 | 0.035 | 51.259 | no | 1.962 (1.850 to 2.069) | 1.986 (1.920 to 2.054) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos2_bk | 0.322 (0.288 to 0.353) | 0.977 | yes |
| chronos2_cur | 0.319 (0.283 to 0.352) | 0.977 | yes |
| chronos2_curdw | 0.317 (0.280 to 0.352) | 0.977 | yes |
| chronos2_nli | 0.316 (0.281 to 0.349) | 0.977 | no |
| chronos2_top | 0.310 (0.273 to 0.345) | 0.977 | no |
| chronos2 | 0.308 (0.274 to 0.340) | 0.977 | no |
| median_s2_all | 0.297 (0.261 to 0.330) | 0.977 | no |
| median_s2_behavior | 0.281 (0.244 to 0.314) | 0.943 | no |
| chronos | 0.280 (0.249 to 0.310) | 0.989 | no |
| median_s2_demand | 0.279 (0.242 to 0.312) | 0.966 | no |
| lgbmchg_D | 0.275 (0.242 to 0.305) | 0.966 | no |
| lgbmchg_DVbk | 0.269 (0.235 to 0.299) | 0.955 | no |
| catchg_DVbk | 0.267 (0.239 to 0.295) | 0.977 | no |
| catchg_D | 0.267 (0.236 to 0.296) | 0.977 | no |
| catchg_DVtop | 0.265 (0.235 to 0.294) | 0.966 | no |
| catchg_DVnli | 0.265 (0.235 to 0.294) | 0.977 | no |
| lgbmchg_DW | 0.264 (0.231 to 0.293) | 0.977 | no |
| catchg_DVcurdw | 0.264 (0.236 to 0.291) | 0.966 | no |
| lgbmchg_DVcur | 0.264 (0.230 to 0.293) | 0.966 | no |
| catchg_DW | 0.263 (0.234 to 0.292) | 0.966 | no |
| catchg_DWS | 0.263 (0.235 to 0.289) | 0.966 | no |
| catchg_DVcur | 0.263 (0.232 to 0.292) | 0.966 | no |
| lightgbm_D | 0.263 (0.229 to 0.294) | 0.943 | no |
| invmae_all | 0.263 (0.224 to 0.298) | 0.943 | no |
| lgbmchg_DWS | 0.263 (0.229 to 0.293) | 0.977 | no |
| catchg_DVdem | 0.262 (0.233 to 0.290) | 0.977 | no |
| lgbmchg_DVcurdw | 0.261 (0.227 to 0.292) | 0.966 | no |
| lgbmchg_DVnli | 0.259 (0.225 to 0.290) | 0.977 | no |
| lgbmchg_DVtop | 0.258 (0.225 to 0.289) | 0.966 | no |
| median_all | 0.257 (0.219 to 0.289) | 0.955 | no |
| lgbmchg_DVdem | 0.257 (0.225 to 0.286) | 0.966 | no |
| lightgbm_DW | 0.254 (0.218 to 0.285) | 0.943 | no |
| avg_three_DW | 0.246 (0.210 to 0.277) | 0.943 | no |
| avg_ridge_cat_DW | 0.218 (0.183 to 0.246) | 0.932 | no |
| avg_ridge_cat_D | 0.215 (0.181 to 0.245) | 0.932 | no |
| catboost_DW | 0.208 (0.175 to 0.235) | 0.943 | no |
| ridge_DW | 0.207 (0.173 to 0.238) | 0.932 | no |
| catboost_D | 0.207 (0.173 to 0.236) | 0.943 | no |
| ridgechg_DW | 0.206 (0.175 to 0.236) | 0.932 | no |
| ridgechg_DVcur | 0.205 (0.173 to 0.234) | 0.932 | no |
| ridgechg_DVdem | 0.205 (0.173 to 0.233) | 0.943 | no |
| ridgechg_DWS | 0.204 (0.174 to 0.233) | 0.932 | no |
| ridgechg_DVcurdw | 0.204 (0.173 to 0.231) | 0.932 | no |
| ridgechg_D | 0.202 (0.171 to 0.232) | 0.932 | no |
| ridgechg_DVnli | 0.201 (0.168 to 0.230) | 0.932 | no |
| ridge_D | 0.200 (0.168 to 0.231) | 0.932 | no |
| avg_naive_ridge_D | 0.200 (0.168 to 0.231) | 0.932 | no |
| ridgechg_DVbk | 0.200 (0.169 to 0.228) | 0.932 | no |
| ridgechg_DVtop | 0.196 (0.164 to 0.226) | 0.920 | no |
| seasonal_naive | 0.173 (0.132 to 0.209) | 0.920 | no |
| revert6 | 0.140 (0.109 to 0.169) | 0.875 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos2_cur | 0.253 (0.155 to 0.344) | 38.606 | yes |
| chronos2_curdw | 0.250 (0.154 to 0.341) | 38.192 | yes |
| chronos2_bk | 0.246 (0.149 to 0.336) | 37.553 | no |
| chronos2_nli | 0.246 (0.149 to 0.337) | 37.540 | no |
| chronos2 | 0.245 (0.151 to 0.334) | 37.520 | no |
| chronos2_top | 0.244 (0.148 to 0.335) | 37.304 | no |
| chronos | 0.236 (0.144 to 0.321) | 36.009 | no |
| median_s2_all | 0.192 (0.107 to 0.271) | 29.377 | no |
| lightgbm_DW | 0.184 (0.097 to 0.269) | 28.086 | no |
| lgbmchg_D | 0.183 (0.101 to 0.264) | 28.002 | no |
| median_s2_behavior | 0.182 (0.100 to 0.260) | 27.813 | no |
| median_s2_demand | 0.182 (0.097 to 0.263) | 27.775 | no |
| lgbmchg_DVdem | 0.174 (0.085 to 0.264) | 26.561 | no |
| lgbmchg_DW | 0.172 (0.094 to 0.249) | 26.325 | no |
| lgbmchg_DWS | 0.172 (0.093 to 0.245) | 26.230 | no |
| catchg_D | 0.172 (0.091 to 0.247) | 26.222 | no |
| lightgbm_D | 0.171 (0.087 to 0.251) | 26.178 | no |
| median_all | 0.171 (0.088 to 0.254) | 26.134 | no |
| lgbmchg_DVcurdw | 0.171 (0.096 to 0.241) | 26.084 | no |
| lgbmchg_DVnli | 0.170 (0.088 to 0.250) | 26.056 | no |
| avg_three_DW | 0.170 (0.081 to 0.259) | 25.997 | no |
| catchg_DVcurdw | 0.167 (0.090 to 0.242) | 25.576 | no |
| lgbmchg_DVtop | 0.167 (0.086 to 0.249) | 25.526 | no |
| catchg_DVnli | 0.167 (0.090 to 0.238) | 25.518 | no |
| catchg_DVtop | 0.166 (0.091 to 0.241) | 25.406 | no |
| lgbmchg_DVcur | 0.166 (0.086 to 0.240) | 25.367 | no |
| lgbmchg_DVbk | 0.164 (0.086 to 0.244) | 25.137 | no |
| catchg_DVdem | 0.158 (0.081 to 0.230) | 24.102 | no |
| catchg_DVcur | 0.157 (0.083 to 0.227) | 24.037 | no |
| invmae_all | 0.151 (0.075 to 0.254) | 23.061 | no |
| catchg_DW | 0.147 (0.079 to 0.217) | 22.521 | no |
| catchg_DWS | 0.145 (0.083 to 0.215) | 22.197 | no |
| catchg_DVbk | 0.144 (0.074 to 0.228) | 21.986 | no |
| catboost_DW | 0.135 (0.063 to 0.209) | 20.636 | no |
| catboost_D | 0.134 (0.062 to 0.217) | 20.433 | no |
| avg_ridge_cat_DW | 0.127 (0.055 to 0.216) | 19.381 | no |
| avg_ridge_cat_D | 0.082 (0.039 to 0.154) | 12.588 | no |
| ridgechg_DWS | 0.064 (0.027 to 0.132) | 9.712 | no |
| ridgechg_DW | 0.058 (0.024 to 0.126) | 8.865 | no |
| ridgechg_DVcur | 0.050 (0.020 to 0.119) | 7.684 | no |
| ridge_DW | 0.048 (0.021 to 0.105) | 7.353 | no |
| ridgechg_DVcurdw | 0.038 (0.015 to 0.095) | 5.743 | no |
| seasonal_naive | 0.024 (0.016 to 0.035) | 3.617 | no |
| ridgechg_DVtop | 0.018 (0.012 to 0.027) | 2.723 | no |
| ridgechg_DVdem | 0.018 (0.012 to 0.028) | 2.677 | no |
| ridgechg_D | 0.017 (0.011 to 0.027) | 2.635 | no |
| ridgechg_DVbk | 0.017 (0.011 to 0.028) | 2.633 | no |
| ridgechg_DVnli | 0.017 (0.011 to 0.026) | 2.573 | no |
| ridge_D | 0.016 (0.010 to 0.025) | 2.427 | no |
| avg_naive_ridge_D | 0.016 (0.010 to 0.025) | 2.427 | no |
| revert6 | 0.007 (0.005 to 0.009) | 1.023 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos2_cur | 4.495 | 0.752 | 0.046 |
| chronos2_curdw | 4.505 | 0.757 | 0.045 |
| chronos2_bk | 4.509 | 0.758 | 0.046 |
| chronos2_nli | 4.515 | 0.757 | 0.046 |
| chronos2 | 4.527 | 0.753 | 0.046 |
| chronos2_top | 4.528 | 0.755 | 0.045 |
| median_s2_all | 4.603 | 0.757 | 0.042 |
| chronos | 4.627 | 0.735 | 0.042 |
| median_s2_behavior | 4.639 | 0.751 | 0.040 |
| median_s2_demand | 4.643 | 0.748 | 0.041 |
| lgbmchg_D | 4.680 | 0.743 | 0.041 |
| catchg_DVnli | 4.681 | 0.731 | 0.038 |
| catchg_D | 4.685 | 0.738 | 0.036 |
| catchg_DVcur | 4.686 | 0.734 | 0.037 |
| catchg_DW | 4.686 | 0.737 | 0.037 |
| lgbmchg_DVbk | 4.686 | 0.744 | 0.045 |
| catchg_DVbk | 4.688 | 0.732 | 0.040 |
| catchg_DVtop | 4.690 | 0.736 | 0.037 |
| catchg_DVcurdw | 4.691 | 0.734 | 0.038 |
| catchg_DWS | 4.692 | 0.733 | 0.037 |
| lgbmchg_DW | 4.696 | 0.736 | 0.042 |
| lgbmchg_DWS | 4.697 | 0.733 | 0.042 |
| lgbmchg_DVcur | 4.697 | 0.733 | 0.044 |
| catchg_DVdem | 4.700 | 0.733 | 0.039 |
| lgbmchg_DVnli | 4.704 | 0.732 | 0.040 |
| lgbmchg_DVtop | 4.706 | 0.734 | 0.043 |
| lgbmchg_DVcurdw | 4.711 | 0.736 | 0.045 |
| median_all | 4.727 | 0.714 | 0.040 |
| lgbmchg_DVdem | 4.748 | 0.737 | 0.048 |
| lightgbm_D | 4.754 | 0.733 | 0.042 |
| invmae_all | 4.762 | 0.749 | 0.043 |
| lightgbm_DW | 4.787 | 0.739 | 0.044 |
| avg_three_DW | 4.811 | 0.735 | 0.041 |
| avg_naive_ridge_D | 4.909 | 0.695 | 0.026 |
| ridgechg_DWS | 4.918 | 0.705 | 0.035 |
| ridgechg_DW | 4.920 | 0.707 | 0.037 |
| ridgechg_DVcur | 4.920 | 0.706 | 0.036 |
| ridgechg_DVdem | 4.922 | 0.698 | 0.027 |
| ridgechg_D | 4.923 | 0.696 | 0.027 |
| ridgechg_DVnli | 4.925 | 0.695 | 0.027 |
| ridgechg_DVtop | 4.926 | 0.697 | 0.028 |
| ridgechg_DVbk | 4.926 | 0.695 | 0.026 |
| avg_ridge_cat_DW | 4.926 | 0.709 | 0.039 |
| ridgechg_DVcurdw | 4.934 | 0.698 | 0.034 |
| avg_ridge_cat_D | 4.945 | 0.710 | 0.041 |
| ridge_DW | 4.955 | 0.707 | 0.037 |
| ridge_D | 4.956 | 0.695 | 0.026 |
| naive | 5.009 |  |  |
| catboost_DW | 5.083 | 0.698 | 0.036 |
| catboost_D | 5.108 | 0.692 | 0.038 |
| revert6 | 6.797 | 0.622 | 0.010 |
| seasonal_naive | 10.631 | 0.690 | 0.032 |

**Paired comparisons, model held fixed (A2)**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision

| pair | question | MAE ratio (95%) | share of series better | Spearman difference (95%) | surge AP difference (95%) |
| --- | --- | --- | --- | --- | --- |
| ridgechg_D -> ridgechg_DVcur | behavior against no behavior | 1.002 (1.000 to 1.004) | 0.451 | +0.003 (-0.003 to +0.008) | +0.033 (+0.004 to +0.097) |
| ridgechg_D -> ridgechg_DW | behavior against no behavior | 1.002 (1.000 to 1.004) | 0.439 | +0.004 (-0.001 to +0.009) | +0.041 (+0.008 to +0.105) |
| ridgechg_D -> ridgechg_DWS | behavior against no behavior | 1.003 (1.000 to 1.005) | 0.445 | +0.002 (-0.004 to +0.009) | +0.046 (+0.011 to +0.113) |
| ridgechg_D -> ridgechg_DVtop | behavior against no behavior | 1.001 (1.000 to 1.002) | 0.398 | -0.006 (-0.010 to -0.001) | +0.001 (-0.001 to +0.001) |
| ridgechg_D -> ridgechg_DVnli | behavior against no behavior | 1.001 (1.000 to 1.001) | 0.461 | -0.002 (-0.004 to +0.001) | -0.000 (-0.001 to +0.000) |
| ridgechg_D -> ridgechg_DVbk | behavior against no behavior | 1.002 (1.001 to 1.003) | 0.425 | -0.002 (-0.006 to +0.002) | -0.000 (-0.001 to +0.001) |
| ridgechg_D -> ridgechg_DVcurdw | behavior against no behavior | 1.006 (1.003 to 1.010) | 0.425 | +0.002 (-0.004 to +0.007) | +0.020 (-0.000 to +0.075) |
| ridgechg_D -> ridgechg_DVdem | behavior against no behavior | 1.000 (0.999 to 1.001) | 0.490 | +0.003 (-0.000 to +0.005) | +0.000 (-0.001 to +0.001) |
| ridgechg_DVcur -> ridgechg_DVtop | routing or representation against curated volume | 0.999 (0.997 to 1.001) | 0.504 | -0.009 (-0.015 to -0.002) | -0.032 (-0.096 to -0.004) |
| ridgechg_DVcur -> ridgechg_DVnli | routing or representation against curated volume | 0.998 (0.997 to 1.000) | 0.547 | -0.004 (-0.010 to +0.001) | -0.033 (-0.098 to -0.004) |
| ridgechg_DVcur -> ridgechg_DVbk | routing or representation against curated volume | 1.000 (0.998 to 1.002) | 0.471 | -0.005 (-0.011 to +0.002) | -0.033 (-0.097 to -0.004) |
| ridgechg_DVcur -> ridgechg_DVcurdw | routing or representation against curated volume | 1.004 (1.002 to 1.006) | 0.449 | -0.001 (-0.005 to +0.002) | -0.013 (-0.031 to -0.003) |
| ridgechg_DVcur -> ridgechg_DVdem | routing or representation against curated volume | 0.998 (0.996 to 1.000) | 0.547 | -0.000 (-0.005 to +0.005) | -0.033 (-0.097 to -0.004) |
| lgbmchg_D -> lgbmchg_DVcur | behavior against no behavior | 1.004 (1.001 to 1.008) | 0.457 | -0.011 (-0.018 to -0.005) | -0.017 (-0.043 to +0.006) |
| lgbmchg_D -> lgbmchg_DW | behavior against no behavior | 1.003 (1.000 to 1.007) | 0.471 | -0.011 (-0.018 to -0.004) | -0.011 (-0.033 to +0.010) |
| lgbmchg_D -> lgbmchg_DWS | behavior against no behavior | 1.004 (1.000 to 1.007) | 0.475 | -0.012 (-0.021 to -0.004) | -0.012 (-0.035 to +0.011) |
| lgbmchg_D -> lgbmchg_DVtop | behavior against no behavior | 1.006 (1.003 to 1.009) | 0.465 | -0.017 (-0.024 to -0.010) | -0.016 (-0.042 to +0.010) |
| lgbmchg_D -> lgbmchg_DVnli | behavior against no behavior | 1.006 (1.004 to 1.009) | 0.445 | -0.016 (-0.023 to -0.009) | -0.013 (-0.032 to +0.005) |
| lgbmchg_D -> lgbmchg_DVbk | behavior against no behavior | 1.002 (0.998 to 1.006) | 0.467 | -0.006 (-0.014 to +0.001) | -0.019 (-0.046 to +0.006) |
| lgbmchg_D -> lgbmchg_DVcurdw | behavior against no behavior | 1.006 (1.002 to 1.011) | 0.476 | -0.014 (-0.020 to -0.007) | -0.013 (-0.035 to +0.011) |
| lgbmchg_D -> lgbmchg_DVdem | behavior against no behavior | 1.015 (1.011 to 1.019) | 0.351 | -0.018 (-0.026 to -0.010) | -0.009 (-0.026 to +0.010) |
| lgbmchg_DVcur -> lgbmchg_DVtop | routing or representation against curated volume | 1.002 (0.999 to 1.005) | 0.514 | -0.005 (-0.014 to +0.003) | +0.001 (-0.023 to +0.030) |
| lgbmchg_DVcur -> lgbmchg_DVnli | routing or representation against curated volume | 1.002 (0.999 to 1.006) | 0.471 | -0.004 (-0.012 to +0.003) | +0.005 (-0.018 to +0.032) |
| lgbmchg_DVcur -> lgbmchg_DVbk | routing or representation against curated volume | 0.998 (0.994 to 1.002) | 0.516 | +0.005 (-0.003 to +0.013) | -0.002 (-0.024 to +0.022) |
| lgbmchg_DVcur -> lgbmchg_DVcurdw | routing or representation against curated volume | 1.002 (1.000 to 1.005) | 0.471 | -0.002 (-0.007 to +0.002) | +0.005 (-0.017 to +0.028) |
| lgbmchg_DVcur -> lgbmchg_DVdem | routing or representation against curated volume | 1.011 (1.007 to 1.016) | 0.398 | -0.007 (-0.016 to +0.003) | +0.008 (-0.018 to +0.036) |
| catchg_D -> catchg_DVcur | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.475 | -0.004 (-0.009 to +0.001) | -0.014 (-0.037 to +0.007) |
| catchg_D -> catchg_DW | behavior against no behavior | 1.001 (0.999 to 1.003) | 0.476 | -0.004 (-0.008 to +0.001) | -0.024 (-0.050 to +0.004) |
| catchg_D -> catchg_DWS | behavior against no behavior | 1.003 (1.000 to 1.005) | 0.449 | -0.004 (-0.009 to +0.002) | -0.026 (-0.056 to +0.007) |
| catchg_D -> catchg_DVtop | behavior against no behavior | 1.002 (1.000 to 1.004) | 0.471 | -0.002 (-0.006 to +0.002) | -0.005 (-0.032 to +0.024) |
| catchg_D -> catchg_DVnli | behavior against no behavior | 0.999 (0.998 to 1.001) | 0.484 | -0.002 (-0.005 to +0.001) | -0.005 (-0.018 to +0.008) |
| catchg_D -> catchg_DVbk | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.484 | +0.000 (-0.004 to +0.005) | -0.028 (-0.057 to +0.008) |
| catchg_D -> catchg_DVcurdw | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.488 | -0.003 (-0.008 to +0.002) | -0.004 (-0.030 to +0.019) |
| catchg_D -> catchg_DVdem | behavior against no behavior | 1.004 (1.001 to 1.006) | 0.424 | -0.005 (-0.010 to +0.000) | -0.014 (-0.032 to +0.002) |
| catchg_DVcur -> catchg_DVtop | routing or representation against curated volume | 1.001 (0.999 to 1.003) | 0.463 | +0.002 (-0.004 to +0.008) | +0.009 (-0.017 to +0.038) |
| catchg_DVcur -> catchg_DVnli | routing or representation against curated volume | 0.998 (0.996 to 1.000) | 0.486 | +0.002 (-0.004 to +0.009) | +0.010 (-0.015 to +0.032) |
| catchg_DVcur -> catchg_DVbk | routing or representation against curated volume | 1.000 (0.998 to 1.002) | 0.502 | +0.004 (-0.001 to +0.009) | -0.013 (-0.041 to +0.024) |
| catchg_DVcur -> catchg_DVcurdw | routing or representation against curated volume | 1.000 (0.998 to 1.002) | 0.510 | +0.001 (-0.003 to +0.005) | +0.010 (-0.002 to +0.024) |
| catchg_DVcur -> catchg_DVdem | routing or representation against curated volume | 1.002 (0.999 to 1.005) | 0.467 | -0.001 (-0.007 to +0.006) | +0.000 (-0.029 to +0.026) |
| chronos2 -> chronos2_cur | behavior against no behavior | 0.994 (0.992 to 0.996) | 0.616 | +0.011 (+0.004 to +0.019) | +0.007 (-0.001 to +0.016) |
| chronos2 -> chronos2_curdw | behavior against no behavior | 0.997 (0.994 to 0.999) | 0.553 | +0.009 (+0.001 to +0.017) | +0.004 (-0.003 to +0.013) |
| chronos2 -> chronos2_bk | behavior against no behavior | 0.996 (0.994 to 0.999) | 0.561 | +0.014 (+0.008 to +0.020) | +0.000 (-0.007 to +0.008) |
| chronos2 -> chronos2_nli | behavior against no behavior | 0.998 (0.996 to 1.000) | 0.527 | +0.008 (+0.003 to +0.014) | +0.000 (-0.005 to +0.006) |
| chronos2 -> chronos2_top | behavior against no behavior | 1.000 (0.998 to 1.002) | 0.488 | +0.002 (-0.004 to +0.008) | -0.001 (-0.009 to +0.007) |
| chronos2_cur -> chronos2_curdw | routing or representation against curated volume | 1.003 (1.001 to 1.005) | 0.457 | -0.002 (-0.006 to +0.002) | -0.003 (-0.007 to +0.002) |
| chronos2_cur -> chronos2_bk | routing or representation against curated volume | 1.002 (1.000 to 1.005) | 0.478 | +0.003 (-0.002 to +0.008) | -0.007 (-0.014 to +0.000) |
| chronos2_cur -> chronos2_nli | routing or representation against curated volume | 1.004 (1.002 to 1.006) | 0.418 | -0.003 (-0.007 to +0.001) | -0.007 (-0.014 to -0.001) |
| chronos2_cur -> chronos2_top | routing or representation against curated volume | 1.006 (1.004 to 1.009) | 0.394 | -0.009 (-0.015 to -0.004) | -0.009 (-0.018 to +0.000) |
| median_s2_demand -> median_s2_behavior | combination: behavior against no behavior | 1.000 (0.998 to 1.002) | 0.476 | +0.002 (-0.002 to +0.006) | +0.000 (-0.021 to +0.023) |

### B2. Print and ebook, horizon 2

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.877 (0.853 to 0.900) | 0.950 | 0.671 | 11.010 | yes | 0.816 (0.776 to 0.855) | 0.884 (0.860 to 0.906) |
| chronos2_bk | 0.879 (0.854 to 0.902) | 0.954 | 0.665 | 11.390 | yes | 0.815 (0.776 to 0.854) | 0.884 (0.860 to 0.905) |
| chronos2_nli | 0.879 (0.854 to 0.902) | 0.950 | 0.663 | 11.063 | yes | 0.816 (0.776 to 0.856) | 0.885 (0.861 to 0.907) |
| chronos2_curdw | 0.881 (0.856 to 0.903) | 0.952 | 0.661 | 11.531 | no | 0.819 (0.780 to 0.858) | 0.887 (0.863 to 0.909) |
| chronos2_top | 0.882 (0.858 to 0.905) | 0.956 | 0.653 | 11.936 | no | 0.820 (0.781 to 0.859) | 0.888 (0.864 to 0.910) |
| chronos2 | 0.884 (0.860 to 0.907) | 0.958 | 0.643 | 12.452 | no | 0.823 (0.783 to 0.862) | 0.890 (0.866 to 0.911) |
| median_s2_all | 0.895 (0.876 to 0.912) | 0.934 | 0.769 | 7.869 | no | 0.835 (0.803 to 0.868) | 0.897 (0.879 to 0.913) |
| chronos | 0.903 (0.878 to 0.926) | 0.968 | 0.614 | 14.547 | no | 0.854 (0.813 to 0.893) | 0.906 (0.882 to 0.927) |
| median_s2_demand | 0.917 (0.899 to 0.933) | 0.945 | 0.692 | 11.384 | no | 0.870 (0.838 to 0.902) | 0.915 (0.899 to 0.930) |
| lgbmchg_D | 0.926 (0.906 to 0.944) | 0.960 | 0.600 | 14.624 | no | 0.871 (0.835 to 0.904) | 0.924 (0.906 to 0.941) |
| catchg_D | 0.928 (0.909 to 0.944) | 0.957 | 0.692 | 13.690 | no | 0.886 (0.853 to 0.920) | 0.928 (0.910 to 0.943) |
| catchg_DVnli | 0.929 (0.910 to 0.946) | 0.958 | 0.678 | 14.392 | no | 0.889 (0.855 to 0.922) | 0.929 (0.911 to 0.945) |
| catchg_DW | 0.929 (0.911 to 0.945) | 0.959 | 0.686 | 13.992 | no | 0.889 (0.856 to 0.920) | 0.929 (0.912 to 0.944) |
| catchg_DWS | 0.929 (0.911 to 0.946) | 0.955 | 0.659 | 14.141 | no | 0.887 (0.853 to 0.919) | 0.929 (0.912 to 0.944) |
| catchg_DVdem | 0.932 (0.914 to 0.949) | 0.961 | 0.673 | 14.839 | no | 0.891 (0.859 to 0.924) | 0.931 (0.914 to 0.946) |
| median_all | 0.937 (0.918 to 0.953) | 0.957 | 0.667 | 14.698 | no | 0.904 (0.872 to 0.937) | 0.931 (0.915 to 0.946) |
| invmae_all | 0.942 (0.926 to 0.957) | 0.964 | 0.633 | 15.594 | no | 0.924 (0.892 to 0.956) | 0.942 (0.926 to 0.956) |
| lightgbm_D | 0.951 (0.930 to 0.971) | 0.981 | 0.561 | 18.204 | no | 0.927 (0.884 to 0.969) | 0.946 (0.926 to 0.963) |
| avg_three_DW | 0.963 (0.946 to 0.978) | 0.971 | 0.606 | 17.967 | no | 0.970 (0.937 to 1.003) | 0.963 (0.946 to 0.978) |
| lightgbm_DW | 0.964 (0.942 to 0.984) | 0.989 | 0.524 | 19.898 | no | 0.936 (0.894 to 0.978) | 0.958 (0.938 to 0.976) |
| avg_naive_ridge_D | 0.971 (0.967 to 0.976) | 0.963 | 0.741 | 16.818 | no | 0.976 (0.965 to 0.987) | 0.969 (0.965 to 0.973) |
| ridgechg_D | 0.977 (0.969 to 0.986) | 0.966 | 0.641 | 18.592 | no | 0.978 (0.960 to 0.998) | 0.969 (0.961 to 0.977) |
| ridgechg_DW | 0.980 (0.971 to 0.989) | 0.969 | 0.614 | 19.165 | no | 0.980 (0.961 to 1.000) | 0.972 (0.963 to 0.980) |
| ridgechg_DWS | 0.980 (0.971 to 0.989) | 0.970 | 0.612 | 19.322 | no | 0.981 (0.962 to 1.003) | 0.972 (0.964 to 0.981) |
| avg_ridge_cat_DW | 0.985 (0.970 to 0.999) | 0.979 | 0.571 | 20.514 | no | 1.023 (0.989 to 1.058) | 0.989 (0.972 to 1.006) |
| avg_ridge_cat_D | 0.987 (0.972 to 1.001) | 0.980 | 0.559 | 20.182 | no | 1.035 (0.998 to 1.073) | 0.997 (0.978 to 1.016) |
| ridge_D | 0.989 (0.979 to 1.000) | 0.977 | 0.580 | 20.947 | no | 0.997 (0.973 to 1.022) | 0.979 (0.969 to 0.989) |
| ridge_DW | 0.991 (0.980 to 1.001) | 0.978 | 0.573 | 21.292 | no | 0.997 (0.973 to 1.022) | 0.981 (0.971 to 0.990) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 20.049 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| catboost_DW | 1.020 (0.995 to 1.042) | 1.012 | 0.459 | 23.765 | no | 1.129 (1.066 to 1.191) | 1.044 (1.012 to 1.076) |
| catboost_D | 1.026 (1.001 to 1.049) | 1.021 | 0.449 | 23.800 | no | 1.152 (1.083 to 1.222) | 1.068 (1.030 to 1.107) |
| revert6 | 1.147 (1.131 to 1.163) | 1.155 | 0.175 | 29.267 | no | 1.152 (1.129 to 1.174) | 1.117 (1.103 to 1.132) |
| seasonal_naive | 1.737 (1.671 to 1.803) | 1.821 | 0.069 | 32.067 | no | 1.598 (1.487 to 1.701) | 1.678 (1.617 to 1.738) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos2_bk | 0.360 (0.323 to 0.393) | 0.988 | yes |
| chronos2_cur | 0.356 (0.315 to 0.393) | 0.988 | yes |
| chronos2_nli | 0.354 (0.317 to 0.389) | 0.988 | yes |
| chronos2_curdw | 0.352 (0.310 to 0.389) | 0.988 | yes |
| median_s2_all | 0.348 (0.303 to 0.388) | 0.953 | yes |
| chronos2 | 0.346 (0.309 to 0.380) | 0.988 | no |
| chronos2_top | 0.344 (0.301 to 0.383) | 0.977 | no |
| chronos | 0.330 (0.298 to 0.362) | 1.000 | no |
| median_s2_demand | 0.317 (0.274 to 0.357) | 0.942 | no |
| lgbmchg_D | 0.315 (0.274 to 0.351) | 0.965 | no |
| catchg_D | 0.311 (0.273 to 0.345) | 0.977 | no |
| catchg_DWS | 0.310 (0.273 to 0.343) | 0.977 | no |
| catchg_DW | 0.309 (0.270 to 0.344) | 0.965 | no |
| catchg_DVdem | 0.306 (0.268 to 0.340) | 0.965 | no |
| catchg_DVnli | 0.306 (0.267 to 0.342) | 0.965 | no |
| invmae_all | 0.302 (0.255 to 0.343) | 0.930 | no |
| lightgbm_D | 0.297 (0.255 to 0.336) | 0.942 | no |
| median_all | 0.295 (0.252 to 0.336) | 0.942 | no |
| lightgbm_DW | 0.286 (0.242 to 0.326) | 0.942 | no |
| avg_three_DW | 0.283 (0.241 to 0.323) | 0.942 | no |
| avg_ridge_cat_D | 0.267 (0.228 to 0.306) | 0.942 | no |
| avg_ridge_cat_DW | 0.264 (0.224 to 0.304) | 0.942 | no |
| catboost_D | 0.264 (0.226 to 0.301) | 0.942 | no |
| catboost_DW | 0.259 (0.219 to 0.297) | 0.942 | no |
| ridgechg_D | 0.249 (0.212 to 0.288) | 0.930 | no |
| avg_naive_ridge_D | 0.246 (0.207 to 0.285) | 0.930 | no |
| ridge_D | 0.246 (0.207 to 0.285) | 0.930 | no |
| ridgechg_DW | 0.244 (0.206 to 0.281) | 0.942 | no |
| ridge_DW | 0.242 (0.204 to 0.281) | 0.942 | no |
| ridgechg_DWS | 0.242 (0.206 to 0.278) | 0.942 | no |
| seasonal_naive | 0.203 (0.152 to 0.246) | 0.895 | no |
| revert6 | 0.154 (0.115 to 0.196) | 0.826 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos2_cur | 0.364 (0.281 to 0.448) | 24.029 | yes |
| chronos2_bk | 0.363 (0.279 to 0.447) | 23.957 | yes |
| chronos2_curdw | 0.362 (0.277 to 0.446) | 23.874 | yes |
| chronos2_nli | 0.359 (0.275 to 0.442) | 23.655 | no |
| chronos2_top | 0.358 (0.273 to 0.442) | 23.612 | no |
| chronos2 | 0.358 (0.275 to 0.441) | 23.580 | no |
| chronos | 0.348 (0.266 to 0.429) | 22.955 | no |
| median_s2_all | 0.325 (0.244 to 0.409) | 21.436 | no |
| median_s2_demand | 0.297 (0.218 to 0.379) | 19.565 | no |
| catchg_DVdem | 0.287 (0.208 to 0.368) | 18.947 | no |
| lgbmchg_D | 0.287 (0.205 to 0.370) | 18.922 | no |
| catchg_DVnli | 0.282 (0.204 to 0.361) | 18.565 | no |
| catchg_D | 0.280 (0.202 to 0.363) | 18.484 | no |
| catchg_DW | 0.280 (0.201 to 0.360) | 18.465 | no |
| catchg_DWS | 0.280 (0.199 to 0.363) | 18.443 | no |
| invmae_all | 0.277 (0.198 to 0.367) | 18.290 | no |
| median_all | 0.273 (0.198 to 0.355) | 18.029 | no |
| lightgbm_D | 0.269 (0.187 to 0.351) | 17.710 | no |
| lightgbm_DW | 0.260 (0.182 to 0.341) | 17.143 | no |
| avg_three_DW | 0.245 (0.168 to 0.327) | 16.144 | no |
| catboost_DW | 0.244 (0.172 to 0.320) | 16.093 | no |
| catboost_D | 0.238 (0.168 to 0.314) | 15.709 | no |
| avg_ridge_cat_DW | 0.206 (0.139 to 0.287) | 13.593 | no |
| avg_ridge_cat_D | 0.203 (0.134 to 0.282) | 13.354 | no |
| ridgechg_DWS | 0.096 (0.064 to 0.140) | 6.344 | no |
| ridgechg_DW | 0.093 (0.063 to 0.134) | 6.161 | no |
| ridge_DW | 0.082 (0.056 to 0.118) | 5.398 | no |
| seasonal_naive | 0.079 (0.056 to 0.111) | 5.226 | no |
| ridgechg_D | 0.072 (0.051 to 0.100) | 4.733 | no |
| avg_naive_ridge_D | 0.064 (0.045 to 0.091) | 4.205 | no |
| ridge_D | 0.064 (0.045 to 0.091) | 4.205 | no |
| revert6 | 0.022 (0.017 to 0.028) | 1.432 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos2_cur | 5.673 | 0.756 | 0.120 |
| chronos2_bk | 5.687 | 0.761 | 0.120 |
| chronos2_nli | 5.688 | 0.759 | 0.119 |
| chronos2_curdw | 5.696 | 0.758 | 0.121 |
| chronos2_top | 5.712 | 0.752 | 0.119 |
| chronos2 | 5.720 | 0.752 | 0.119 |
| median_s2_all | 5.818 | 0.765 | 0.114 |
| chronos | 5.829 | 0.745 | 0.117 |
| median_s2_demand | 5.957 | 0.754 | 0.113 |
| lgbmchg_D | 6.000 | 0.746 | 0.109 |
| catchg_D | 6.011 | 0.742 | 0.108 |
| catchg_DVnli | 6.020 | 0.738 | 0.106 |
| catchg_DWS | 6.022 | 0.743 | 0.106 |
| catchg_DW | 6.024 | 0.740 | 0.105 |
| catchg_DVdem | 6.042 | 0.737 | 0.103 |
| median_all | 6.078 | 0.724 | 0.108 |
| invmae_all | 6.115 | 0.744 | 0.118 |
| lightgbm_D | 6.148 | 0.741 | 0.108 |
| lightgbm_DW | 6.222 | 0.733 | 0.111 |
| avg_three_DW | 6.238 | 0.739 | 0.109 |
| avg_ridge_cat_DW | 6.394 | 0.723 | 0.101 |
| avg_ridge_cat_D | 6.406 | 0.728 | 0.106 |
| avg_naive_ridge_D | 6.442 | 0.720 | 0.087 |
| ridgechg_D | 6.449 | 0.725 | 0.091 |
| ridgechg_DWS | 6.454 | 0.712 | 0.093 |
| ridgechg_DW | 6.456 | 0.718 | 0.098 |
| ridge_D | 6.513 | 0.720 | 0.087 |
| ridge_DW | 6.515 | 0.717 | 0.097 |
| catboost_DW | 6.543 | 0.711 | 0.101 |
| catboost_D | 6.574 | 0.716 | 0.106 |
| naive | 6.674 |  |  |
| revert6 | 7.749 | 0.624 | 0.035 |
| seasonal_naive | 11.596 | 0.683 | 0.087 |

**Paired comparisons, model held fixed (B2)**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision

| pair | question | MAE ratio (95%) | share of series better | Spearman difference (95%) | surge AP difference (95%) |
| --- | --- | --- | --- | --- | --- |
| ridgechg_D -> ridgechg_DW | behavior against no behavior | 1.003 (1.001 to 1.005) | 0.453 | -0.006 (-0.011 to -0.000) | +0.022 (+0.007 to +0.046) |
| ridgechg_D -> ridgechg_DWS | behavior against no behavior | 1.003 (1.001 to 1.005) | 0.473 | -0.007 (-0.015 to +0.001) | +0.024 (+0.007 to +0.052) |
| catchg_D -> catchg_DW | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.500 | -0.002 (-0.006 to +0.002) | -0.000 (-0.015 to +0.012) |
| catchg_D -> catchg_DWS | behavior against no behavior | 1.002 (0.999 to 1.005) | 0.482 | -0.001 (-0.006 to +0.004) | -0.001 (-0.014 to +0.013) |
| catchg_D -> catchg_DVnli | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.451 | -0.004 (-0.008 to -0.001) | +0.001 (-0.005 to +0.008) |
| catchg_D -> catchg_DVdem | behavior against no behavior | 1.005 (1.003 to 1.008) | 0.414 | -0.004 (-0.009 to +0.000) | +0.007 (-0.004 to +0.016) |
| chronos2 -> chronos2_cur | behavior against no behavior | 0.992 (0.990 to 0.994) | 0.618 | +0.010 (+0.003 to +0.017) | +0.007 (+0.001 to +0.012) |
| chronos2 -> chronos2_curdw | behavior against no behavior | 0.996 (0.993 to 0.999) | 0.580 | +0.006 (-0.003 to +0.015) | +0.004 (-0.001 to +0.009) |
| chronos2 -> chronos2_bk | behavior against no behavior | 0.994 (0.991 to 0.997) | 0.582 | +0.014 (+0.008 to +0.020) | +0.006 (+0.002 to +0.009) |
| chronos2 -> chronos2_nli | behavior against no behavior | 0.994 (0.992 to 0.996) | 0.590 | +0.009 (+0.004 to +0.014) | +0.001 (-0.003 to +0.004) |
| chronos2 -> chronos2_top | behavior against no behavior | 0.998 (0.996 to 1.000) | 0.504 | -0.002 (-0.009 to +0.005) | +0.000 (-0.002 to +0.003) |
| chronos2_cur -> chronos2_curdw | routing or representation against curated volume | 1.004 (1.002 to 1.005) | 0.425 | -0.004 (-0.009 to +0.000) | -0.002 (-0.006 to +0.001) |
| chronos2_cur -> chronos2_bk | routing or representation against curated volume | 1.002 (0.999 to 1.004) | 0.502 | +0.004 (-0.002 to +0.010) | -0.001 (-0.005 to +0.003) |
| chronos2_cur -> chronos2_nli | routing or representation against curated volume | 1.002 (0.999 to 1.004) | 0.463 | -0.001 (-0.005 to +0.004) | -0.006 (-0.011 to -0.001) |
| chronos2_cur -> chronos2_top | routing or representation against curated volume | 1.006 (1.003 to 1.008) | 0.418 | -0.012 (-0.017 to -0.006) | -0.006 (-0.011 to -0.001) |

### C2. Print and ebook, horizon 3

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.863 (0.836 to 0.888) | 0.941 | 0.657 | 11.374 | yes | 0.785 (0.737 to 0.831) | 0.867 (0.841 to 0.890) |
| chronos2_bk | 0.863 (0.836 to 0.889) | 0.942 | 0.652 | 11.669 | yes | 0.784 (0.738 to 0.830) | 0.866 (0.840 to 0.890) |
| chronos2_nli | 0.865 (0.837 to 0.890) | 0.943 | 0.648 | 11.728 | no | 0.786 (0.738 to 0.832) | 0.868 (0.842 to 0.891) |
| chronos2_curdw | 0.866 (0.839 to 0.891) | 0.943 | 0.632 | 12.199 | no | 0.788 (0.740 to 0.834) | 0.870 (0.844 to 0.894) |
| chronos2_top | 0.868 (0.840 to 0.893) | 0.948 | 0.640 | 12.438 | no | 0.789 (0.741 to 0.835) | 0.871 (0.845 to 0.894) |
| chronos2 | 0.871 (0.843 to 0.896) | 0.954 | 0.620 | 13.186 | no | 0.792 (0.744 to 0.838) | 0.874 (0.849 to 0.897) |
| median_s2_all | 0.879 (0.856 to 0.899) | 0.926 | 0.754 | 8.323 | no | 0.807 (0.770 to 0.845) | 0.878 (0.856 to 0.896) |
| chronos | 0.886 (0.859 to 0.910) | 0.956 | 0.638 | 14.384 | no | 0.822 (0.777 to 0.866) | 0.887 (0.862 to 0.910) |
| median_s2_demand | 0.900 (0.877 to 0.919) | 0.937 | 0.705 | 11.191 | no | 0.844 (0.807 to 0.880) | 0.896 (0.875 to 0.913) |
| lgbmchg_D | 0.909 (0.885 to 0.930) | 0.954 | 0.644 | 14.419 | no | 0.841 (0.799 to 0.885) | 0.906 (0.883 to 0.925) |
| catchg_D | 0.913 (0.890 to 0.933) | 0.947 | 0.683 | 13.770 | no | 0.864 (0.825 to 0.903) | 0.911 (0.890 to 0.929) |
| catchg_DVnli | 0.914 (0.890 to 0.935) | 0.948 | 0.685 | 14.098 | no | 0.862 (0.823 to 0.901) | 0.912 (0.890 to 0.930) |
| catchg_DW | 0.915 (0.893 to 0.934) | 0.949 | 0.683 | 14.185 | no | 0.865 (0.827 to 0.904) | 0.913 (0.893 to 0.930) |
| catchg_DWS | 0.916 (0.893 to 0.936) | 0.952 | 0.689 | 14.512 | no | 0.864 (0.825 to 0.904) | 0.914 (0.894 to 0.932) |
| median_all | 0.919 (0.897 to 0.938) | 0.950 | 0.661 | 14.276 | no | 0.877 (0.842 to 0.912) | 0.912 (0.891 to 0.930) |
| catchg_DVdem | 0.919 (0.898 to 0.940) | 0.956 | 0.669 | 15.114 | no | 0.870 (0.832 to 0.909) | 0.916 (0.896 to 0.934) |
| invmae_all | 0.922 (0.904 to 0.940) | 0.957 | 0.642 | 15.102 | no | 0.886 (0.853 to 0.920) | 0.919 (0.901 to 0.935) |
| lightgbm_D | 0.930 (0.905 to 0.952) | 0.969 | 0.604 | 17.352 | no | 0.893 (0.847 to 0.938) | 0.923 (0.899 to 0.943) |
| avg_three_DW | 0.948 (0.930 to 0.965) | 0.968 | 0.612 | 17.943 | no | 0.940 (0.906 to 0.974) | 0.945 (0.927 to 0.962) |
| lightgbm_DW | 0.948 (0.923 to 0.969) | 0.980 | 0.543 | 19.490 | no | 0.906 (0.862 to 0.949) | 0.941 (0.917 to 0.961) |
| avg_ridge_cat_D | 0.963 (0.947 to 0.978) | 0.966 | 0.604 | 19.502 | no | 0.970 (0.939 to 1.002) | 0.961 (0.945 to 0.976) |
| avg_naive_ridge_D | 0.964 (0.959 to 0.970) | 0.957 | 0.738 | 16.717 | no | 0.970 (0.958 to 0.983) | 0.961 (0.956 to 0.967) |
| avg_ridge_cat_DW | 0.971 (0.955 to 0.987) | 0.970 | 0.585 | 20.392 | no | 0.996 (0.961 to 1.031) | 0.974 (0.956 to 0.992) |
| ridgechg_D | 0.980 (0.969 to 0.991) | 0.966 | 0.587 | 20.222 | no | 0.998 (0.970 to 1.028) | 0.977 (0.966 to 0.989) |
| ridge_DW | 0.980 (0.968 to 0.993) | 0.970 | 0.585 | 20.789 | no | 0.985 (0.960 to 1.014) | 0.971 (0.959 to 0.982) |
| ridgechg_DWS | 0.982 (0.971 to 0.993) | 0.972 | 0.593 | 20.297 | no | 1.002 (0.975 to 1.031) | 0.979 (0.968 to 0.991) |
| catboost_D | 0.982 (0.958 to 1.005) | 0.993 | 0.520 | 21.854 | no | 1.046 (0.990 to 1.099) | 1.000 (0.970 to 1.028) |
| ridgechg_DW | 0.983 (0.972 to 0.994) | 0.973 | 0.585 | 20.707 | no | 1.003 (0.976 to 1.033) | 0.981 (0.969 to 0.992) |
| ridge_D | 0.984 (0.972 to 0.996) | 0.974 | 0.563 | 21.163 | no | 0.998 (0.969 to 1.028) | 0.978 (0.966 to 0.990) |
| catboost_DW | 0.995 (0.969 to 1.017) | 1.003 | 0.486 | 23.307 | no | 1.071 (1.011 to 1.127) | 1.020 (0.988 to 1.050) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 20.325 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| revert6 | 1.069 (1.056 to 1.081) | 1.062 | 0.321 | 27.132 | no | 1.056 (1.037 to 1.076) | 1.045 (1.033 to 1.057) |
| seasonal_naive | 1.576 (1.513 to 1.638) | 1.661 | 0.098 | 31.839 | no | 1.445 (1.339 to 1.543) | 1.534 (1.475 to 1.591) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos2_bk | 0.378 (0.338 to 0.409) | 1.000 | yes |
| chronos2_cur | 0.374 (0.329 to 0.408) | 0.988 | yes |
| median_s2_all | 0.371 (0.325 to 0.410) | 0.977 | yes |
| chronos2_nli | 0.370 (0.328 to 0.403) | 0.988 | no |
| chronos2_curdw | 0.367 (0.321 to 0.404) | 0.977 | no |
| chronos2 | 0.361 (0.321 to 0.394) | 0.988 | no |
| chronos2_top | 0.360 (0.314 to 0.396) | 0.988 | no |
| chronos | 0.355 (0.317 to 0.385) | 1.000 | no |
| median_s2_demand | 0.346 (0.300 to 0.387) | 0.953 | no |
| lgbmchg_D | 0.342 (0.297 to 0.381) | 0.953 | no |
| catchg_D | 0.338 (0.294 to 0.373) | 0.965 | no |
| catchg_DW | 0.336 (0.293 to 0.371) | 0.977 | no |
| catchg_DWS | 0.333 (0.292 to 0.367) | 0.977 | no |
| catchg_DVdem | 0.332 (0.291 to 0.365) | 0.965 | no |
| catchg_DVnli | 0.331 (0.287 to 0.367) | 0.953 | no |
| invmae_all | 0.328 (0.277 to 0.370) | 0.953 | no |
| lightgbm_D | 0.327 (0.281 to 0.366) | 0.953 | no |
| median_all | 0.326 (0.279 to 0.367) | 0.965 | no |
| avg_three_DW | 0.314 (0.269 to 0.354) | 0.942 | no |
| lightgbm_DW | 0.313 (0.264 to 0.354) | 0.942 | no |
| avg_ridge_cat_D | 0.300 (0.258 to 0.339) | 0.953 | no |
| catboost_D | 0.296 (0.254 to 0.333) | 0.965 | no |
| avg_ridge_cat_DW | 0.296 (0.254 to 0.334) | 0.942 | no |
| catboost_DW | 0.290 (0.247 to 0.327) | 0.942 | no |
| avg_naive_ridge_D | 0.283 (0.242 to 0.322) | 0.953 | no |
| ridge_D | 0.283 (0.242 to 0.322) | 0.953 | no |
| ridgechg_D | 0.280 (0.238 to 0.319) | 0.942 | no |
| ridge_DW | 0.279 (0.239 to 0.318) | 0.953 | no |
| ridgechg_DW | 0.272 (0.232 to 0.312) | 0.942 | no |
| ridgechg_DWS | 0.268 (0.229 to 0.306) | 0.930 | no |
| seasonal_naive | 0.219 (0.161 to 0.262) | 0.907 | no |
| revert6 | 0.186 (0.146 to 0.230) | 0.872 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos2_cur | 0.381 (0.307 to 0.453) | 17.374 | yes |
| chronos2_bk | 0.379 (0.306 to 0.449) | 17.300 | yes |
| chronos2_curdw | 0.379 (0.306 to 0.449) | 17.293 | yes |
| chronos2_nli | 0.376 (0.303 to 0.445) | 17.165 | no |
| chronos2_top | 0.375 (0.302 to 0.445) | 17.095 | no |
| chronos2 | 0.374 (0.302 to 0.444) | 17.059 | no |
| chronos | 0.358 (0.285 to 0.429) | 16.343 | no |
| median_s2_all | 0.334 (0.262 to 0.401) | 15.216 | no |
| median_s2_demand | 0.305 (0.234 to 0.372) | 13.901 | no |
| lgbmchg_D | 0.295 (0.224 to 0.364) | 13.447 | no |
| invmae_all | 0.290 (0.221 to 0.360) | 13.249 | no |
| catchg_DVnli | 0.287 (0.219 to 0.356) | 13.086 | no |
| catchg_DWS | 0.285 (0.218 to 0.353) | 12.987 | no |
| catchg_D | 0.284 (0.215 to 0.351) | 12.956 | no |
| median_all | 0.283 (0.217 to 0.349) | 12.894 | no |
| catchg_DVdem | 0.282 (0.215 to 0.349) | 12.873 | no |
| catchg_DW | 0.282 (0.215 to 0.345) | 12.870 | no |
| lightgbm_D | 0.275 (0.208 to 0.344) | 12.563 | no |
| catboost_D | 0.257 (0.199 to 0.320) | 11.728 | no |
| lightgbm_DW | 0.255 (0.193 to 0.322) | 11.635 | no |
| avg_three_DW | 0.250 (0.187 to 0.317) | 11.399 | no |
| catboost_DW | 0.242 (0.187 to 0.307) | 11.046 | no |
| avg_ridge_cat_D | 0.239 (0.176 to 0.304) | 10.889 | no |
| avg_ridge_cat_DW | 0.228 (0.167 to 0.294) | 10.403 | no |
| ridge_DW | 0.123 (0.087 to 0.167) | 5.629 | no |
| ridgechg_DW | 0.122 (0.084 to 0.170) | 5.565 | no |
| ridgechg_DWS | 0.121 (0.084 to 0.168) | 5.533 | no |
| ridgechg_D | 0.117 (0.078 to 0.163) | 5.315 | no |
| seasonal_naive | 0.114 (0.083 to 0.154) | 5.207 | no |
| avg_naive_ridge_D | 0.112 (0.077 to 0.152) | 5.105 | no |
| ridge_D | 0.112 (0.077 to 0.152) | 5.105 | no |
| revert6 | 0.044 (0.034 to 0.060) | 2.028 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos2_cur | 6.580 | 0.759 | 0.170 |
| chronos2_bk | 6.590 | 0.761 | 0.173 |
| chronos2_nli | 6.599 | 0.755 | 0.164 |
| chronos2_curdw | 6.609 | 0.757 | 0.170 |
| chronos2_top | 6.627 | 0.755 | 0.168 |
| chronos2 | 6.642 | 0.754 | 0.166 |
| median_s2_all | 6.705 | 0.766 | 0.163 |
| chronos | 6.729 | 0.756 | 0.161 |
| median_s2_demand | 6.856 | 0.757 | 0.154 |
| lgbmchg_D | 6.922 | 0.749 | 0.149 |
| catchg_D | 6.929 | 0.748 | 0.146 |
| catchg_DVnli | 6.938 | 0.743 | 0.147 |
| catchg_DW | 6.950 | 0.743 | 0.146 |
| catchg_DWS | 6.955 | 0.742 | 0.145 |
| catchg_DVdem | 6.978 | 0.742 | 0.146 |
| median_all | 6.994 | 0.725 | 0.154 |
| invmae_all | 7.038 | 0.747 | 0.159 |
| lightgbm_D | 7.074 | 0.744 | 0.150 |
| lightgbm_DW | 7.206 | 0.740 | 0.146 |
| avg_three_DW | 7.211 | 0.742 | 0.150 |
| avg_ridge_cat_D | 7.342 | 0.733 | 0.147 |
| avg_ridge_cat_DW | 7.389 | 0.734 | 0.141 |
| catboost_D | 7.393 | 0.726 | 0.143 |
| catboost_DW | 7.482 | 0.726 | 0.139 |
| avg_naive_ridge_D | 7.509 | 0.727 | 0.128 |
| ridgechg_D | 7.553 | 0.727 | 0.132 |
| ridgechg_DWS | 7.556 | 0.719 | 0.124 |
| ridge_DW | 7.561 | 0.723 | 0.129 |
| ridgechg_DW | 7.566 | 0.723 | 0.131 |
| ridge_D | 7.589 | 0.727 | 0.128 |
| naive | 7.864 |  |  |
| revert6 | 8.436 | 0.650 | 0.069 |
| seasonal_naive | 12.359 | 0.681 | 0.121 |

**Paired comparisons, model held fixed (C2)**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision

| pair | question | MAE ratio (95%) | share of series better | Spearman difference (95%) | surge AP difference (95%) |
| --- | --- | --- | --- | --- | --- |
| ridgechg_D -> ridgechg_DW | behavior against no behavior | 1.003 (1.002 to 1.006) | 0.467 | -0.008 (-0.011 to -0.003) | +0.005 (+0.001 to +0.011) |
| ridgechg_D -> ridgechg_DWS | behavior against no behavior | 1.002 (1.000 to 1.004) | 0.514 | -0.012 (-0.020 to -0.004) | +0.005 (-0.001 to +0.013) |
| catchg_D -> catchg_DW | behavior against no behavior | 1.003 (1.000 to 1.005) | 0.441 | -0.002 (-0.005 to +0.002) | -0.002 (-0.009 to +0.003) |
| catchg_D -> catchg_DWS | behavior against no behavior | 1.004 (1.001 to 1.007) | 0.413 | -0.004 (-0.011 to +0.002) | +0.001 (-0.005 to +0.008) |
| catchg_D -> catchg_DVnli | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.470 | -0.007 (-0.011 to -0.004) | +0.003 (-0.002 to +0.008) |
| catchg_D -> catchg_DVdem | behavior against no behavior | 1.007 (1.005 to 1.010) | 0.413 | -0.006 (-0.011 to -0.001) | -0.002 (-0.007 to +0.004) |
| chronos2 -> chronos2_cur | behavior against no behavior | 0.991 (0.989 to 0.994) | 0.648 | +0.012 (+0.005 to +0.019) | +0.007 (+0.002 to +0.011) |
| chronos2 -> chronos2_curdw | behavior against no behavior | 0.995 (0.992 to 0.998) | 0.587 | +0.006 (-0.002 to +0.014) | +0.005 (+0.000 to +0.009) |
| chronos2 -> chronos2_bk | behavior against no behavior | 0.992 (0.989 to 0.995) | 0.620 | +0.016 (+0.009 to +0.024) | +0.005 (+0.001 to +0.008) |
| chronos2 -> chronos2_nli | behavior against no behavior | 0.993 (0.991 to 0.996) | 0.616 | +0.009 (+0.003 to +0.014) | +0.002 (-0.001 to +0.005) |
| chronos2 -> chronos2_top | behavior against no behavior | 0.997 (0.994 to 0.999) | 0.508 | -0.002 (-0.009 to +0.005) | +0.001 (-0.002 to +0.004) |
| chronos2_cur -> chronos2_curdw | routing or representation against curated volume | 1.004 (1.002 to 1.006) | 0.425 | -0.006 (-0.011 to -0.002) | -0.002 (-0.005 to +0.001) |
| chronos2_cur -> chronos2_bk | routing or representation against curated volume | 1.000 (0.998 to 1.003) | 0.508 | +0.004 (-0.001 to +0.010) | -0.002 (-0.006 to +0.001) |
| chronos2_cur -> chronos2_nli | routing or representation against curated volume | 1.002 (1.000 to 1.005) | 0.447 | -0.003 (-0.008 to +0.002) | -0.005 (-0.010 to -0.000) |
| chronos2_cur -> chronos2_top | routing or representation against curated volume | 1.005 (1.003 to 1.008) | 0.402 | -0.014 (-0.020 to -0.008) | -0.006 (-0.010 to -0.001) |

### A2 without the seasonal repeat (sensitivity, level task only)

| pipeline | AvgRelMAE (95%) | in confidence set | mean rank |
| --- | --- | --- | --- |
| chronos2_cur | 0.918 (0.899 to 0.934) | yes | 14.624 |
| chronos2_bk | 0.920 (0.901 to 0.937) | yes | 15.323 |
| chronos2_curdw | 0.921 (0.902 to 0.938) | yes | 15.526 |
| chronos2_nli | 0.922 (0.903 to 0.938) | no | 15.716 |
| chronos2 | 0.923 (0.904 to 0.939) | no | 16.420 |
| chronos2_top | 0.924 (0.905 to 0.940) | no | 16.527 |
| chronos | 0.945 (0.926 to 0.961) | no | 20.290 |
| median_s2_all | 0.953 (0.940 to 0.964) | yes | 12.497 |
| median_s2_behavior | 0.961 (0.948 to 0.972) | no | 15.211 |
| median_s2_demand | 0.962 (0.950 to 0.972) | no | 15.409 |
| median_all | 0.971 (0.959 to 0.981) | no | 18.307 |
| catchg_DVnli | 0.980 (0.966 to 0.992) | no | 21.114 |
| catchg_DW | 0.982 (0.969 to 0.994) | no | 21.360 |
| catchg_DWS | 0.983 (0.970 to 0.994) | no | 21.521 |
| catchg_DVcurdw | 0.983 (0.970 to 0.994) | no | 20.638 |
| catchg_DVcur | 0.984 (0.970 to 0.996) | no | 21.814 |
| invmae_all | 0.985 (0.972 to 0.996) | no | 21.798 |
| catchg_D | 0.986 (0.972 to 0.997) | no | 22.065 |
| catchg_DVbk | 0.986 (0.972 to 0.998) | no | 22.088 |
| lgbmchg_DW | 0.987 (0.972 to 1.000) | yes | 25.432 |
| lgbmchg_DVbk | 0.987 (0.973 to 1.000) | yes | 25.732 |
| catchg_DVtop | 0.988 (0.974 to 1.000) | no | 23.159 |
| lgbmchg_DVcur | 0.989 (0.974 to 1.002) | yes | 26.233 |
| lgbmchg_D | 0.990 (0.974 to 1.004) | yes | 26.771 |
| catchg_DVdem | 0.991 (0.977 to 1.002) | no | 23.401 |
| lgbmchg_DWS | 0.992 (0.977 to 1.005) | yes | 27.037 |
| lgbmchg_DVcurdw | 0.992 (0.979 to 1.005) | no | 26.787 |
| lgbmchg_DVtop | 0.994 (0.980 to 1.006) | yes | 26.691 |
| naive | 1.000 (1.000 to 1.000) | no | 25.280 |
| lgbmchg_DVnli | 1.002 (0.986 to 1.016) | yes | 29.937 |
| lgbmchg_DVdem | 1.005 (0.989 to 1.018) | no | 30.736 |
| lightgbm_D | 1.006 (0.990 to 1.020) | no | 29.123 |
| avg_three_DW | 1.006 (0.993 to 1.019) | no | 24.795 |
| avg_naive_ridge_D | 1.011 (1.004 to 1.018) | no | 23.648 |
| lightgbm_DW | 1.011 (0.994 to 1.025) | no | 30.209 |
| avg_ridge_cat_DW | 1.039 (1.024 to 1.054) | no | 29.421 |
| avg_ridge_cat_D | 1.042 (1.027 to 1.058) | no | 29.808 |
| ridgechg_DVdem | 1.056 (1.044 to 1.070) | no | 32.589 |
| ridgechg_D | 1.056 (1.044 to 1.070) | no | 32.730 |
| ridgechg_DVnli | 1.057 (1.045 to 1.070) | no | 33.006 |
| ridgechg_DVbk | 1.057 (1.044 to 1.071) | no | 33.431 |
| ridgechg_DVcur | 1.057 (1.044 to 1.070) | no | 33.047 |
| ridgechg_DVtop | 1.057 (1.045 to 1.071) | no | 33.372 |
| ridgechg_DW | 1.058 (1.045 to 1.071) | no | 33.159 |
| ridgechg_DWS | 1.058 (1.045 to 1.071) | no | 33.526 |
| ridgechg_DVcurdw | 1.060 (1.046 to 1.073) | no | 33.133 |
| catboost_DW | 1.072 (1.050 to 1.093) | no | 35.973 |
| ridge_D | 1.073 (1.059 to 1.088) | no | 37.661 |
| ridge_DW | 1.075 (1.060 to 1.090) | no | 38.008 |
| catboost_D | 1.078 (1.055 to 1.100) | no | 36.106 |
| revert6 | 1.329 (1.306 to 1.353) | no | 47.812 |

### D2. Seattle audiobooks, horizon 1

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| median_s2_all | 0.968 (0.959 to 0.976) | 0.968 | 0.773 | 14.382 | yes | 0.970 (0.962 to 0.977) | 0.966 (0.957 to 0.974) |
| median_s2_behavior | 0.970 (0.958 to 0.979) | 0.968 | 0.742 | 15.018 | yes | 0.976 (0.966 to 0.986) | 0.967 (0.956 to 0.976) |
| median_s2_demand | 0.971 (0.961 to 0.979) | 0.971 | 0.747 | 15.427 | yes | 0.973 (0.964 to 0.983) | 0.968 (0.959 to 0.976) |
| median_all | 0.977 (0.967 to 0.986) | 0.977 | 0.671 | 18.716 | no | 0.991 (0.978 to 1.003) | 0.974 (0.964 to 0.983) |
| catchg_DW | 0.982 (0.969 to 0.993) | 0.985 | 0.609 | 22.853 | no | 0.997 (0.986 to 1.007) | 0.979 (0.967 to 0.989) |
| catchg_DVcurdw | 0.983 (0.971 to 0.993) | 0.984 | 0.591 | 22.813 | no | 0.994 (0.984 to 1.004) | 0.981 (0.969 to 0.991) |
| catchg_D | 0.983 (0.973 to 0.992) | 0.984 | 0.658 | 22.373 | no | 0.988 (0.981 to 0.995) | 0.979 (0.970 to 0.987) |
| avg_naive_ridge_D | 0.984 (0.981 to 0.988) | 0.980 | 0.804 | 21.329 | no | 0.989 (0.983 to 0.996) | 0.982 (0.979 to 0.985) |
| catchg_DVbk | 0.984 (0.972 to 0.994) | 0.988 | 0.587 | 23.396 | no | 1.000 (0.990 to 1.009) | 0.982 (0.970 to 0.992) |
| catchg_DVnli | 0.985 (0.975 to 0.994) | 0.990 | 0.644 | 23.924 | no | 0.990 (0.981 to 0.999) | 0.980 (0.971 to 0.988) |
| catchg_DWS | 0.986 (0.974 to 0.996) | 0.987 | 0.604 | 24.676 | no | 1.002 (0.991 to 1.012) | 0.984 (0.972 to 0.993) |
| catchg_DVcur | 0.986 (0.973 to 0.997) | 0.988 | 0.596 | 24.800 | no | 1.001 (0.990 to 1.010) | 0.985 (0.972 to 0.995) |
| catchg_DVtop | 0.987 (0.976 to 0.996) | 0.990 | 0.587 | 24.982 | no | 0.997 (0.988 to 1.006) | 0.983 (0.973 to 0.991) |
| lgbmchg_DW | 0.989 (0.975 to 1.001) | 0.987 | 0.587 | 24.707 | no | 0.993 (0.981 to 1.004) | 0.987 (0.974 to 0.998) |
| ridgechg_D | 0.989 (0.983 to 0.996) | 0.983 | 0.698 | 22.969 | no | 1.002 (0.991 to 1.013) | 0.985 (0.980 to 0.991) |
| ridgechg_DVnli | 0.990 (0.983 to 0.996) | 0.982 | 0.702 | 23.400 | no | 1.001 (0.991 to 1.012) | 0.986 (0.980 to 0.991) |
| chronos2_cur | 0.990 (0.977 to 1.000) | 0.998 | 0.529 | 25.160 | no | 0.987 (0.975 to 0.998) | 0.993 (0.981 to 1.004) |
| ridgechg_DVtop | 0.990 (0.984 to 0.996) | 0.982 | 0.684 | 23.764 | no | 1.002 (0.991 to 1.013) | 0.986 (0.981 to 0.991) |
| ridgechg_DVdem | 0.990 (0.984 to 0.996) | 0.984 | 0.689 | 23.520 | no | 1.006 (0.994 to 1.018) | 0.986 (0.981 to 0.992) |
| ridgechg_DVcur | 0.990 (0.983 to 0.997) | 0.982 | 0.636 | 22.960 | no | 1.006 (0.995 to 1.017) | 0.988 (0.982 to 0.994) |
| lgbmchg_DVcur | 0.991 (0.976 to 1.003) | 0.992 | 0.547 | 25.916 | no | 0.998 (0.987 to 1.010) | 0.989 (0.976 to 0.999) |
| lgbmchg_DVcurdw | 0.991 (0.977 to 1.003) | 0.992 | 0.556 | 25.773 | no | 0.999 (0.987 to 1.009) | 0.991 (0.979 to 1.001) |
| ridgechg_DWS | 0.991 (0.984 to 0.998) | 0.986 | 0.644 | 23.778 | no | 1.008 (0.997 to 1.019) | 0.988 (0.982 to 0.994) |
| ridgechg_DW | 0.991 (0.984 to 0.998) | 0.985 | 0.644 | 23.853 | no | 1.007 (0.996 to 1.019) | 0.989 (0.982 to 0.995) |
| lgbmchg_DVbk | 0.992 (0.978 to 1.003) | 0.994 | 0.538 | 26.573 | no | 0.995 (0.984 to 1.006) | 0.989 (0.975 to 1.000) |
| invmae_all | 0.992 (0.980 to 1.003) | 0.987 | 0.573 | 24.076 | no | 1.028 (1.005 to 1.050) | 0.992 (0.979 to 1.003) |
| ridge_D | 0.992 (0.985 to 0.999) | 0.982 | 0.658 | 24.187 | no | 1.011 (0.997 to 1.026) | 0.988 (0.981 to 0.994) |
| lgbmchg_DWS | 0.992 (0.978 to 1.004) | 0.994 | 0.547 | 26.698 | no | 0.996 (0.984 to 1.007) | 0.989 (0.977 to 1.000) |
| ridgechg_DVbk | 0.993 (0.986 to 0.999) | 0.988 | 0.653 | 25.107 | no | 1.011 (0.998 to 1.023) | 0.988 (0.983 to 0.994) |
| chronos2_bk | 0.993 (0.980 to 1.005) | 1.001 | 0.498 | 26.644 | no | 0.990 (0.977 to 1.003) | 0.994 (0.982 to 1.004) |
| catchg_DVdem | 0.994 (0.983 to 1.003) | 0.996 | 0.533 | 26.924 | no | 1.004 (0.993 to 1.014) | 0.994 (0.983 to 1.004) |
| ridge_DW | 0.995 (0.987 to 1.003) | 0.986 | 0.604 | 25.156 | no | 1.018 (1.003 to 1.034) | 0.992 (0.984 to 0.999) |
| ridgechg_DVcurdw | 0.995 (0.988 to 1.003) | 0.984 | 0.613 | 24.822 | no | 1.017 (1.003 to 1.032) | 0.996 (0.988 to 1.006) |
| lgbmchg_DVtop | 0.995 (0.983 to 1.006) | 0.994 | 0.529 | 27.867 | no | 1.003 (0.993 to 1.013) | 0.990 (0.979 to 1.000) |
| chronos2_curdw | 0.995 (0.982 to 1.007) | 1.002 | 0.476 | 27.547 | no | 0.995 (0.982 to 1.008) | 0.997 (0.984 to 1.007) |
| chronos2 | 0.997 (0.984 to 1.007) | 1.007 | 0.449 | 27.593 | no | 0.996 (0.984 to 1.008) | 0.999 (0.988 to 1.010) |
| chronos2_nli | 0.997 (0.984 to 1.008) | 1.007 | 0.467 | 28.162 | no | 0.992 (0.981 to 1.004) | 1.000 (0.988 to 1.011) |
| lgbmchg_D | 0.998 (0.985 to 1.009) | 1.002 | 0.476 | 28.858 | no | 0.998 (0.987 to 1.009) | 0.993 (0.981 to 1.003) |
| avg_three_DW | 0.998 (0.985 to 1.010) | 0.990 | 0.582 | 24.569 | no | 1.059 (1.026 to 1.092) | 1.003 (0.988 to 1.020) |
| chronos2_top | 0.998 (0.985 to 1.010) | 1.006 | 0.453 | 28.498 | no | 0.993 (0.982 to 1.004) | 1.002 (0.990 to 1.014) |
| chronos | 0.999 (0.988 to 1.009) | 1.006 | 0.453 | 28.067 | no | 1.002 (0.990 to 1.014) | 1.001 (0.991 to 1.010) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 29.227 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| lgbmchg_DVnli | 1.000 (0.988 to 1.011) | 0.999 | 0.511 | 30.498 | no | 1.007 (0.997 to 1.016) | 0.996 (0.984 to 1.005) |
| lgbmchg_DVdem | 1.008 (0.995 to 1.019) | 1.012 | 0.382 | 32.244 | no | 1.010 (0.997 to 1.022) | 1.005 (0.992 to 1.016) |
| avg_ridge_cat_DW | 1.011 (0.998 to 1.025) | 0.992 | 0.529 | 27.747 | no | 1.096 (1.055 to 1.137) | 1.025 (1.005 to 1.047) |
| lightgbm_DW | 1.012 (0.996 to 1.026) | 1.008 | 0.458 | 31.560 | no | 1.050 (1.025 to 1.078) | 1.005 (0.990 to 1.018) |
| lightgbm_D | 1.015 (1.000 to 1.028) | 1.016 | 0.418 | 33.582 | no | 1.046 (1.020 to 1.074) | 1.007 (0.993 to 1.019) |
| avg_ridge_cat_D | 1.019 (1.006 to 1.034) | 0.997 | 0.520 | 28.120 | no | 1.124 (1.078 to 1.170) | 1.031 (1.011 to 1.053) |
| catboost_DW | 1.064 (1.042 to 1.086) | 1.033 | 0.338 | 36.742 | no | 1.233 (1.156 to 1.312) | 1.096 (1.061 to 1.136) |
| catboost_D | 1.079 (1.055 to 1.105) | 1.032 | 0.342 | 36.396 | no | 1.289 (1.202 to 1.377) | 1.114 (1.077 to 1.158) |
| revert6 | 1.263 (1.236 to 1.292) | 1.276 | 0.084 | 48.400 | no | 1.280 (1.250 to 1.308) | 1.230 (1.206 to 1.255) |
| seasonal_naive | 2.130 (2.044 to 2.213) | 2.060 | 0.013 | 51.649 | no | 2.056 (1.987 to 2.139) | 2.026 (1.944 to 2.105) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| median_s2_all | 0.245 (0.227 to 0.264) | 1.000 | yes |
| median_s2_behavior | 0.240 (0.221 to 0.259) | 1.000 | yes |
| median_s2_demand | 0.238 (0.221 to 0.259) | 0.988 | no |
| invmae_all | 0.232 (0.213 to 0.254) | 0.988 | no |
| median_all | 0.230 (0.211 to 0.251) | 1.000 | no |
| avg_three_DW | 0.226 (0.206 to 0.248) | 0.988 | no |
| lightgbm_DW | 0.218 (0.199 to 0.239) | 0.988 | no |
| lgbmchg_DVcur | 0.217 (0.198 to 0.236) | 1.000 | no |
| lgbmchg_DW | 0.216 (0.195 to 0.236) | 0.976 | no |
| lgbmchg_D | 0.215 (0.196 to 0.234) | 0.988 | no |
| lgbmchg_DWS | 0.213 (0.193 to 0.231) | 0.988 | no |
| chronos2_bk | 0.212 (0.194 to 0.231) | 0.988 | no |
| avg_ridge_cat_DW | 0.212 (0.192 to 0.235) | 0.988 | no |
| chronos2_cur | 0.212 (0.194 to 0.230) | 0.988 | no |
| lgbmchg_DVcurdw | 0.212 (0.193 to 0.231) | 0.988 | no |
| lightgbm_D | 0.211 (0.193 to 0.232) | 0.976 | no |
| chronos2_curdw | 0.210 (0.193 to 0.228) | 0.976 | no |
| lgbmchg_DVbk | 0.210 (0.190 to 0.230) | 0.988 | no |
| avg_ridge_cat_D | 0.209 (0.188 to 0.230) | 0.988 | no |
| catchg_DVcurdw | 0.208 (0.186 to 0.229) | 0.952 | no |
| catchg_DW | 0.208 (0.187 to 0.228) | 0.988 | no |
| catchg_DVbk | 0.207 (0.186 to 0.227) | 0.952 | no |
| catchg_DWS | 0.207 (0.186 to 0.229) | 0.952 | no |
| catchg_DVtop | 0.206 (0.184 to 0.226) | 0.976 | no |
| catchg_D | 0.206 (0.186 to 0.225) | 0.964 | no |
| lgbmchg_DVdem | 0.206 (0.188 to 0.223) | 0.988 | no |
| catchg_DVcur | 0.205 (0.183 to 0.226) | 0.964 | no |
| catboost_DW | 0.202 (0.182 to 0.226) | 0.964 | no |
| catchg_DVdem | 0.202 (0.183 to 0.221) | 0.952 | no |
| catboost_D | 0.201 (0.178 to 0.225) | 0.976 | no |
| catchg_DVnli | 0.201 (0.179 to 0.222) | 0.940 | no |
| lgbmchg_DVtop | 0.201 (0.183 to 0.218) | 0.988 | no |
| ridge_DW | 0.200 (0.181 to 0.221) | 0.976 | no |
| ridgechg_DWS | 0.199 (0.182 to 0.220) | 0.964 | no |
| ridgechg_DVcur | 0.198 (0.180 to 0.219) | 0.952 | no |
| lgbmchg_DVnli | 0.198 (0.181 to 0.215) | 0.964 | no |
| ridgechg_DW | 0.197 (0.179 to 0.217) | 0.964 | no |
| chronos2_nli | 0.195 (0.179 to 0.212) | 0.988 | no |
| chronos2_top | 0.194 (0.176 to 0.213) | 0.976 | no |
| ridgechg_DVcurdw | 0.194 (0.176 to 0.215) | 0.964 | no |
| chronos2 | 0.193 (0.175 to 0.210) | 0.976 | no |
| avg_naive_ridge_D | 0.192 (0.173 to 0.212) | 0.976 | no |
| ridge_D | 0.192 (0.173 to 0.212) | 0.976 | no |
| ridgechg_DVtop | 0.189 (0.171 to 0.210) | 0.976 | no |
| ridgechg_DVnli | 0.189 (0.170 to 0.209) | 0.976 | no |
| ridgechg_D | 0.188 (0.170 to 0.209) | 0.952 | no |
| ridgechg_DVdem | 0.188 (0.170 to 0.209) | 0.964 | no |
| revert6 | 0.188 (0.160 to 0.215) | 0.952 | no |
| chronos | 0.188 (0.170 to 0.206) | 0.988 | no |
| ridgechg_DVbk | 0.184 (0.167 to 0.205) | 0.952 | no |
| seasonal_naive | 0.165 (0.147 to 0.187) | 0.916 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| lgbmchg_DWS | 0.264 (0.134 to 0.398) | 38.872 | yes |
| median_s2_behavior | 0.263 (0.136 to 0.395) | 38.755 | yes |
| median_s2_all | 0.258 (0.128 to 0.391) | 38.073 | yes |
| catchg_DW | 0.256 (0.131 to 0.389) | 37.695 | yes |
| lgbmchg_DW | 0.251 (0.124 to 0.384) | 37.084 | yes |
| chronos2_bk | 0.250 (0.125 to 0.386) | 36.899 | yes |
| chronos2 | 0.236 (0.116 to 0.371) | 34.756 | yes |
| lgbmchg_DVcur | 0.230 (0.104 to 0.361) | 33.966 | no |
| chronos2_cur | 0.230 (0.111 to 0.366) | 33.955 | yes |
| chronos2_curdw | 0.215 (0.100 to 0.353) | 31.715 | yes |
| chronos2_top | 0.214 (0.101 to 0.350) | 31.584 | yes |
| catchg_DWS | 0.210 (0.090 to 0.350) | 31.014 | yes |
| median_s2_demand | 0.209 (0.087 to 0.339) | 30.828 | yes |
| catchg_DVcur | 0.209 (0.091 to 0.356) | 30.793 | yes |
| chronos2_nli | 0.208 (0.089 to 0.354) | 30.606 | yes |
| catchg_DVcurdw | 0.200 (0.086 to 0.339) | 29.562 | no |
| catchg_DVbk | 0.198 (0.098 to 0.333) | 29.213 | no |
| median_all | 0.197 (0.078 to 0.338) | 28.992 | no |
| chronos | 0.195 (0.092 to 0.334) | 28.825 | yes |
| lgbmchg_DVbk | 0.194 (0.088 to 0.311) | 28.538 | no |
| lightgbm_DW | 0.193 (0.076 to 0.337) | 28.489 | no |
| lgbmchg_D | 0.190 (0.078 to 0.313) | 27.958 | no |
| lgbmchg_DVcurdw | 0.188 (0.080 to 0.329) | 27.789 | no |
| catchg_DVtop | 0.185 (0.085 to 0.291) | 27.253 | no |
| catchg_D | 0.179 (0.082 to 0.311) | 26.438 | no |
| catchg_DVnli | 0.176 (0.080 to 0.303) | 25.997 | no |
| avg_three_DW | 0.176 (0.069 to 0.324) | 25.993 | no |
| lgbmchg_DVtop | 0.175 (0.071 to 0.296) | 25.825 | no |
| catboost_DW | 0.167 (0.061 to 0.290) | 24.636 | no |
| lgbmchg_DVnli | 0.158 (0.062 to 0.287) | 23.367 | no |
| invmae_all | 0.150 (0.055 to 0.311) | 22.194 | no |
| lightgbm_D | 0.143 (0.048 to 0.286) | 21.064 | no |
| lgbmchg_DVdem | 0.140 (0.055 to 0.251) | 20.649 | no |
| avg_ridge_cat_DW | 0.138 (0.051 to 0.273) | 20.288 | no |
| catchg_DVdem | 0.124 (0.051 to 0.264) | 18.221 | no |
| catboost_D | 0.110 (0.035 to 0.247) | 16.250 | no |
| ridgechg_DWS | 0.088 (0.033 to 0.190) | 13.037 | no |
| ridgechg_DW | 0.077 (0.030 to 0.170) | 11.364 | no |
| ridgechg_DVcur | 0.070 (0.028 to 0.156) | 10.305 | no |
| ridge_DW | 0.066 (0.026 to 0.152) | 9.780 | no |
| avg_ridge_cat_D | 0.065 (0.023 to 0.170) | 9.515 | no |
| ridgechg_DVcurdw | 0.044 (0.014 to 0.116) | 6.551 | no |
| seasonal_naive | 0.038 (0.018 to 0.083) | 5.656 | no |
| ridgechg_DVdem | 0.014 (0.008 to 0.030) | 2.116 | no |
| ridgechg_DVtop | 0.014 (0.008 to 0.030) | 2.062 | no |
| ridgechg_D | 0.014 (0.007 to 0.029) | 1.994 | no |
| ridgechg_DVnli | 0.013 (0.007 to 0.028) | 1.955 | no |
| ridgechg_DVbk | 0.013 (0.007 to 0.028) | 1.943 | no |
| ridge_D | 0.011 (0.007 to 0.025) | 1.688 | no |
| avg_naive_ridge_D | 0.011 (0.007 to 0.025) | 1.688 | no |
| revert6 | 0.010 (0.006 to 0.020) | 1.487 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| median_s2_behavior | 4.670 | 0.694 | 0.048 |
| median_s2_all | 4.673 | 0.701 | 0.050 |
| median_s2_demand | 4.686 | 0.691 | 0.048 |
| median_all | 4.716 | 0.658 | 0.045 |
| catchg_DW | 4.724 | 0.689 | 0.049 |
| catchg_DVcurdw | 4.734 | 0.679 | 0.044 |
| catchg_DVbk | 4.741 | 0.699 | 0.048 |
| catchg_DWS | 4.744 | 0.687 | 0.043 |
| catchg_DVcur | 4.745 | 0.692 | 0.046 |
| catchg_D | 4.750 | 0.696 | 0.046 |
| lgbmchg_DW | 4.755 | 0.664 | 0.048 |
| catchg_DVnli | 4.759 | 0.686 | 0.049 |
| lgbmchg_DVcur | 4.763 | 0.679 | 0.049 |
| catchg_DVtop | 4.766 | 0.696 | 0.046 |
| lgbmchg_DVbk | 4.766 | 0.681 | 0.048 |
| lgbmchg_DWS | 4.769 | 0.663 | 0.046 |
| chronos2_cur | 4.769 | 0.661 | 0.048 |
| lgbmchg_DVcurdw | 4.772 | 0.673 | 0.039 |
| invmae_all | 4.781 | 0.691 | 0.051 |
| chronos2_bk | 4.783 | 0.663 | 0.050 |
| chronos2_curdw | 4.796 | 0.670 | 0.049 |
| lgbmchg_DVtop | 4.798 | 0.665 | 0.044 |
| catchg_DVdem | 4.801 | 0.681 | 0.050 |
| lgbmchg_D | 4.802 | 0.684 | 0.044 |
| chronos2 | 4.803 | 0.658 | 0.049 |
| avg_three_DW | 4.804 | 0.692 | 0.046 |
| chronos2_nli | 4.807 | 0.656 | 0.049 |
| chronos2_top | 4.813 | 0.655 | 0.052 |
| avg_naive_ridge_D | 4.816 | 0.661 | 0.023 |
| lgbmchg_DVnli | 4.818 | 0.666 | 0.051 |
| ridgechg_DWS | 4.820 | 0.677 | 0.046 |
| ridgechg_DVcur | 4.821 | 0.677 | 0.044 |
| chronos | 4.822 | 0.644 | 0.042 |
| ridgechg_DW | 4.823 | 0.676 | 0.045 |
| ridgechg_DVtop | 4.832 | 0.660 | 0.023 |
| ridgechg_D | 4.832 | 0.659 | 0.023 |
| ridgechg_DVnli | 4.833 | 0.660 | 0.023 |
| ridgechg_DVdem | 4.835 | 0.661 | 0.024 |
| ridge_DW | 4.836 | 0.673 | 0.046 |
| ridgechg_DVcurdw | 4.839 | 0.671 | 0.039 |
| ridgechg_DVbk | 4.842 | 0.659 | 0.023 |
| ridge_D | 4.844 | 0.661 | 0.023 |
| lgbmchg_DVdem | 4.855 | 0.673 | 0.054 |
| lightgbm_DW | 4.861 | 0.688 | 0.043 |
| avg_ridge_cat_DW | 4.878 | 0.683 | 0.044 |
| lightgbm_D | 4.879 | 0.679 | 0.041 |
| naive | 4.905 |  |  |
| avg_ridge_cat_D | 4.924 | 0.666 | 0.045 |
| catboost_DW | 5.116 | 0.676 | 0.045 |
| catboost_D | 5.187 | 0.661 | 0.046 |
| revert6 | 6.319 | 0.639 | 0.019 |
| seasonal_naive | 10.439 | 0.648 | 0.044 |

**Paired comparisons, model held fixed (D2_h1)**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision

| pair | question | MAE ratio (95%) | share of series better | Spearman difference (95%) | surge AP difference (95%) |
| --- | --- | --- | --- | --- | --- |
| ridgechg_D -> ridgechg_DVcur | behavior against no behavior | 1.001 (0.998 to 1.003) | 0.564 | +0.010 (+0.004 to +0.016) | +0.056 (+0.016 to +0.135) |
| ridgechg_D -> ridgechg_DW | behavior against no behavior | 1.002 (0.999 to 1.005) | 0.502 | +0.008 (+0.002 to +0.015) | +0.064 (+0.019 to +0.149) |
| ridgechg_D -> ridgechg_DWS | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.493 | +0.011 (+0.004 to +0.018) | +0.075 (+0.022 to +0.168) |
| ridgechg_D -> ridgechg_DVtop | behavior against no behavior | 1.000 (0.999 to 1.002) | 0.449 | +0.000 (-0.005 to +0.006) | +0.000 (-0.001 to +0.003) |
| ridgechg_D -> ridgechg_DVnli | behavior against no behavior | 1.000 (0.999 to 1.001) | 0.489 | +0.000 (-0.002 to +0.003) | -0.000 (-0.001 to +0.000) |
| ridgechg_D -> ridgechg_DVbk | behavior against no behavior | 1.003 (1.002 to 1.005) | 0.382 | -0.004 (-0.009 to +0.001) | -0.000 (-0.002 to +0.001) |
| ridgechg_D -> ridgechg_DVcurdw | behavior against no behavior | 1.006 (1.002 to 1.010) | 0.440 | +0.005 (-0.001 to +0.013) | +0.031 (+0.003 to +0.096) |
| ridgechg_D -> ridgechg_DVdem | behavior against no behavior | 1.001 (1.000 to 1.002) | 0.449 | -0.000 (-0.004 to +0.003) | +0.001 (-0.000 to +0.002) |
| ridgechg_DVcur -> ridgechg_DVtop | routing or representation against curated volume | 1.000 (0.997 to 1.002) | 0.418 | -0.009 (-0.017 to -0.003) | -0.056 (-0.135 to -0.016) |
| ridgechg_DVcur -> ridgechg_DVnli | routing or representation against curated volume | 0.999 (0.997 to 1.002) | 0.418 | -0.009 (-0.016 to -0.004) | -0.057 (-0.135 to -0.017) |
| ridgechg_DVcur -> ridgechg_DVbk | routing or representation against curated volume | 1.003 (1.000 to 1.005) | 0.356 | -0.014 (-0.021 to -0.007) | -0.057 (-0.135 to -0.017) |
| ridgechg_DVcur -> ridgechg_DVcurdw | routing or representation against curated volume | 1.005 (1.003 to 1.008) | 0.409 | -0.004 (-0.009 to +0.001) | -0.025 (-0.063 to -0.002) |
| ridgechg_DVcur -> ridgechg_DVdem | routing or representation against curated volume | 1.000 (0.997 to 1.002) | 0.431 | -0.010 (-0.017 to -0.004) | -0.056 (-0.134 to -0.016) |
| lgbmchg_D -> lgbmchg_DVcur | behavior against no behavior | 0.993 (0.988 to 0.998) | 0.573 | +0.001 (-0.010 to +0.011) | +0.041 (-0.008 to +0.095) |
| lgbmchg_D -> lgbmchg_DW | behavior against no behavior | 0.991 (0.987 to 0.996) | 0.591 | +0.001 (-0.014 to +0.013) | +0.062 (+0.004 to +0.126) |
| lgbmchg_D -> lgbmchg_DWS | behavior against no behavior | 0.995 (0.989 to 0.999) | 0.560 | -0.003 (-0.016 to +0.008) | +0.074 (+0.011 to +0.150) |
| lgbmchg_D -> lgbmchg_DVtop | behavior against no behavior | 0.998 (0.993 to 1.002) | 0.556 | -0.015 (-0.027 to -0.004) | -0.014 (-0.070 to +0.048) |
| lgbmchg_D -> lgbmchg_DVnli | behavior against no behavior | 1.002 (0.998 to 1.007) | 0.467 | -0.018 (-0.030 to -0.007) | -0.031 (-0.070 to +0.021) |
| lgbmchg_D -> lgbmchg_DVbk | behavior against no behavior | 0.994 (0.988 to 0.999) | 0.573 | -0.005 (-0.018 to +0.007) | +0.004 (-0.052 to +0.069) |
| lgbmchg_D -> lgbmchg_DVcurdw | behavior against no behavior | 0.993 (0.988 to 0.998) | 0.578 | -0.004 (-0.017 to +0.007) | -0.001 (-0.077 to +0.087) |
| lgbmchg_D -> lgbmchg_DVdem | behavior against no behavior | 1.010 (1.004 to 1.015) | 0.378 | -0.010 (-0.024 to +0.002) | -0.050 (-0.106 to +0.010) |
| lgbmchg_DVcur -> lgbmchg_DVtop | routing or representation against curated volume | 1.004 (1.000 to 1.009) | 0.462 | -0.016 (-0.027 to -0.004) | -0.055 (-0.109 to -0.006) |
| lgbmchg_DVcur -> lgbmchg_DVnli | routing or representation against curated volume | 1.009 (1.004 to 1.014) | 0.382 | -0.019 (-0.029 to -0.009) | -0.072 (-0.133 to -0.005) |
| lgbmchg_DVcur -> lgbmchg_DVbk | routing or representation against curated volume | 1.001 (0.995 to 1.006) | 0.507 | -0.007 (-0.019 to +0.006) | -0.037 (-0.081 to +0.010) |
| lgbmchg_DVcur -> lgbmchg_DVcurdw | routing or representation against curated volume | 1.000 (0.997 to 1.003) | 0.520 | -0.005 (-0.012 to +0.002) | -0.042 (-0.105 to +0.037) |
| lgbmchg_DVcur -> lgbmchg_DVdem | routing or representation against curated volume | 1.017 (1.010 to 1.023) | 0.333 | -0.011 (-0.024 to +0.001) | -0.090 (-0.157 to -0.026) |
| catchg_D -> catchg_DVcur | behavior against no behavior | 1.003 (0.998 to 1.007) | 0.427 | -0.001 (-0.010 to +0.008) | +0.030 (-0.056 to +0.117) |
| catchg_D -> catchg_DW | behavior against no behavior | 0.999 (0.994 to 1.003) | 0.511 | +0.002 (-0.006 to +0.010) | +0.076 (-0.002 to +0.145) |
| catchg_D -> catchg_DWS | behavior against no behavior | 1.003 (0.999 to 1.007) | 0.422 | +0.001 (-0.008 to +0.012) | +0.031 (-0.068 to +0.120) |
| catchg_D -> catchg_DVtop | behavior against no behavior | 1.004 (1.001 to 1.007) | 0.387 | +0.000 (-0.007 to +0.007) | +0.006 (-0.065 to +0.053) |
| catchg_D -> catchg_DVnli | behavior against no behavior | 1.002 (1.000 to 1.005) | 0.440 | -0.005 (-0.012 to +0.003) | -0.003 (-0.023 to +0.013) |
| catchg_D -> catchg_DVbk | behavior against no behavior | 1.001 (0.997 to 1.005) | 0.489 | +0.001 (-0.007 to +0.009) | +0.019 (-0.039 to +0.086) |
| catchg_D -> catchg_DVcurdw | behavior against no behavior | 1.000 (0.996 to 1.003) | 0.489 | +0.003 (-0.006 to +0.011) | +0.021 (-0.072 to +0.112) |
| catchg_D -> catchg_DVdem | behavior against no behavior | 1.011 (1.007 to 1.015) | 0.360 | -0.004 (-0.011 to +0.004) | -0.056 (-0.134 to +0.006) |
| catchg_DVcur -> catchg_DVtop | routing or representation against curated volume | 1.001 (0.997 to 1.005) | 0.484 | +0.001 (-0.008 to +0.009) | -0.024 (-0.121 to +0.055) |
| catchg_DVcur -> catchg_DVnli | routing or representation against curated volume | 0.999 (0.995 to 1.004) | 0.533 | -0.004 (-0.015 to +0.007) | -0.033 (-0.120 to +0.047) |
| catchg_DVcur -> catchg_DVbk | routing or representation against curated volume | 0.998 (0.995 to 1.002) | 0.524 | +0.002 (-0.006 to +0.011) | -0.011 (-0.094 to +0.083) |
| catchg_DVcur -> catchg_DVcurdw | routing or representation against curated volume | 0.997 (0.994 to 0.999) | 0.609 | +0.003 (-0.004 to +0.012) | -0.008 (-0.049 to +0.021) |
| catchg_DVcur -> catchg_DVdem | routing or representation against curated volume | 1.008 (1.002 to 1.014) | 0.427 | -0.003 (-0.012 to +0.006) | -0.085 (-0.184 to +0.019) |
| chronos2 -> chronos2_cur | behavior against no behavior | 0.993 (0.990 to 0.996) | 0.671 | +0.019 (+0.012 to +0.026) | -0.005 (-0.026 to +0.018) |
| chronos2 -> chronos2_curdw | behavior against no behavior | 0.999 (0.996 to 1.002) | 0.533 | +0.018 (+0.010 to +0.026) | -0.021 (-0.069 to +0.034) |
| chronos2 -> chronos2_bk | behavior against no behavior | 0.997 (0.993 to 1.000) | 0.587 | +0.020 (+0.010 to +0.030) | +0.015 (-0.009 to +0.040) |
| chronos2 -> chronos2_nli | behavior against no behavior | 1.000 (0.998 to 1.003) | 0.480 | +0.002 (-0.005 to +0.011) | -0.028 (-0.063 to +0.007) |
| chronos2 -> chronos2_top | behavior against no behavior | 1.002 (0.999 to 1.004) | 0.444 | +0.002 (-0.005 to +0.009) | -0.022 (-0.054 to +0.013) |
| chronos2_cur -> chronos2_curdw | routing or representation against curated volume | 1.006 (1.004 to 1.008) | 0.356 | -0.001 (-0.006 to +0.004) | -0.015 (-0.053 to +0.022) |
| chronos2_cur -> chronos2_bk | routing or representation against curated volume | 1.004 (1.000 to 1.007) | 0.444 | +0.001 (-0.008 to +0.011) | +0.020 (-0.002 to +0.040) |
| chronos2_cur -> chronos2_nli | routing or representation against curated volume | 1.007 (1.004 to 1.010) | 0.373 | -0.017 (-0.024 to -0.009) | -0.023 (-0.061 to +0.008) |
| chronos2_cur -> chronos2_top | routing or representation against curated volume | 1.009 (1.006 to 1.012) | 0.302 | -0.017 (-0.024 to -0.009) | -0.016 (-0.048 to +0.012) |
| median_s2_demand -> median_s2_behavior | combination: behavior against no behavior | 0.999 (0.996 to 1.002) | 0.516 | +0.001 (-0.006 to +0.008) | +0.054 (+0.006 to +0.105) |

### D2. Seattle audiobooks, horizon 2

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| median_s2_all | 0.951 (0.937 to 0.962) | 0.958 | 0.800 | 8.729 | yes | 0.951 (0.940 to 0.960) | 0.951 (0.938 to 0.961) |
| median_s2_demand | 0.964 (0.949 to 0.976) | 0.968 | 0.693 | 11.587 | no | 0.973 (0.960 to 0.984) | 0.960 (0.947 to 0.971) |
| median_all | 0.969 (0.955 to 0.982) | 0.971 | 0.667 | 12.596 | no | 0.984 (0.968 to 1.000) | 0.965 (0.951 to 0.978) |
| catchg_DW | 0.971 (0.955 to 0.983) | 0.979 | 0.644 | 14.413 | no | 0.978 (0.965 to 0.989) | 0.969 (0.955 to 0.981) |
| catchg_DWS | 0.971 (0.955 to 0.983) | 0.979 | 0.644 | 14.467 | no | 0.981 (0.967 to 0.992) | 0.970 (0.955 to 0.981) |
| chronos2_cur | 0.972 (0.957 to 0.986) | 0.983 | 0.587 | 14.587 | no | 0.962 (0.947 to 0.977) | 0.978 (0.964 to 0.990) |
| catchg_D | 0.973 (0.959 to 0.986) | 0.973 | 0.631 | 14.711 | no | 0.980 (0.969 to 0.992) | 0.972 (0.957 to 0.983) |
| catchg_DVnli | 0.974 (0.959 to 0.986) | 0.980 | 0.631 | 15.036 | no | 0.987 (0.974 to 0.999) | 0.973 (0.959 to 0.984) |
| catchg_DVdem | 0.975 (0.959 to 0.987) | 0.978 | 0.631 | 14.862 | no | 0.979 (0.967 to 0.990) | 0.972 (0.958 to 0.983) |
| avg_naive_ridge_D | 0.976 (0.971 to 0.980) | 0.969 | 0.769 | 13.200 | no | 0.987 (0.979 to 0.994) | 0.975 (0.970 to 0.979) |
| chronos2_bk | 0.976 (0.960 to 0.990) | 0.990 | 0.551 | 15.893 | no | 0.963 (0.948 to 0.977) | 0.979 (0.965 to 0.992) |
| chronos2_curdw | 0.977 (0.961 to 0.991) | 0.990 | 0.551 | 15.760 | no | 0.967 (0.952 to 0.982) | 0.983 (0.968 to 0.996) |
| chronos2_nli | 0.981 (0.964 to 0.994) | 0.995 | 0.524 | 16.633 | no | 0.967 (0.952 to 0.982) | 0.987 (0.972 to 1.000) |
| chronos2_top | 0.982 (0.965 to 0.996) | 0.993 | 0.551 | 16.600 | no | 0.968 (0.953 to 0.983) | 0.987 (0.972 to 1.001) |
| invmae_all | 0.982 (0.968 to 0.995) | 0.975 | 0.618 | 14.689 | no | 1.018 (0.994 to 1.041) | 0.982 (0.966 to 0.996) |
| chronos | 0.982 (0.968 to 0.994) | 0.998 | 0.511 | 16.413 | no | 0.984 (0.972 to 0.996) | 0.984 (0.971 to 0.995) |
| chronos2 | 0.983 (0.967 to 0.996) | 0.993 | 0.533 | 17.047 | no | 0.973 (0.957 to 0.989) | 0.987 (0.973 to 0.999) |
| ridgechg_D | 0.984 (0.975 to 0.993) | 0.978 | 0.662 | 14.458 | no | 1.004 (0.990 to 1.018) | 0.979 (0.970 to 0.987) |
| ridgechg_DW | 0.987 (0.978 to 0.997) | 0.983 | 0.627 | 15.222 | no | 1.011 (0.997 to 1.024) | 0.983 (0.973 to 0.991) |
| ridgechg_DWS | 0.988 (0.978 to 0.997) | 0.979 | 0.604 | 15.458 | no | 1.011 (0.996 to 1.024) | 0.983 (0.974 to 0.992) |
| lgbmchg_D | 0.991 (0.974 to 1.006) | 0.998 | 0.511 | 18.009 | no | 0.988 (0.973 to 1.003) | 0.983 (0.966 to 0.997) |
| ridge_D | 0.992 (0.982 to 1.003) | 0.983 | 0.573 | 16.418 | no | 1.027 (1.009 to 1.043) | 0.987 (0.977 to 0.997) |
| avg_three_DW | 0.995 (0.979 to 1.009) | 0.987 | 0.569 | 16.511 | no | 1.060 (1.026 to 1.093) | 0.996 (0.978 to 1.013) |
| ridge_DW | 0.995 (0.983 to 1.006) | 0.993 | 0.538 | 16.920 | no | 1.032 (1.014 to 1.048) | 0.990 (0.979 to 1.000) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 18.533 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| avg_ridge_cat_DW | 1.007 (0.991 to 1.022) | 0.990 | 0.542 | 18.009 | no | 1.097 (1.058 to 1.139) | 1.015 (0.994 to 1.037) |
| avg_ridge_cat_D | 1.007 (0.991 to 1.023) | 0.994 | 0.533 | 17.702 | no | 1.101 (1.057 to 1.143) | 1.021 (1.000 to 1.046) |
| lightgbm_D | 1.010 (0.991 to 1.027) | 1.009 | 0.431 | 20.396 | no | 1.041 (1.014 to 1.070) | 1.001 (0.983 to 1.016) |
| lightgbm_DW | 1.012 (0.992 to 1.030) | 1.015 | 0.449 | 20.511 | no | 1.042 (1.017 to 1.066) | 1.001 (0.983 to 1.018) |
| catboost_DW | 1.055 (1.030 to 1.080) | 1.035 | 0.369 | 23.009 | no | 1.228 (1.154 to 1.304) | 1.085 (1.049 to 1.128) |
| catboost_D | 1.067 (1.040 to 1.093) | 1.049 | 0.338 | 23.924 | no | 1.253 (1.171 to 1.330) | 1.114 (1.072 to 1.164) |
| revert6 | 1.112 (1.092 to 1.133) | 1.113 | 0.222 | 26.311 | no | 1.111 (1.085 to 1.134) | 1.090 (1.071 to 1.109) |
| seasonal_naive | 1.777 (1.700 to 1.848) | 1.788 | 0.027 | 32.387 | no | 1.692 (1.620 to 1.773) | 1.710 (1.638 to 1.778) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| median_s2_all | 0.281 (0.259 to 0.307) | 1.000 | yes |
| invmae_all | 0.260 (0.237 to 0.286) | 1.000 | no |
| median_all | 0.257 (0.235 to 0.284) | 1.000 | no |
| median_s2_demand | 0.257 (0.234 to 0.283) | 0.988 | no |
| avg_three_DW | 0.247 (0.223 to 0.273) | 0.988 | no |
| lightgbm_DW | 0.246 (0.221 to 0.271) | 1.000 | no |
| catchg_DW | 0.242 (0.217 to 0.268) | 1.000 | no |
| lightgbm_D | 0.241 (0.214 to 0.266) | 0.963 | no |
| catchg_DWS | 0.239 (0.216 to 0.262) | 1.000 | no |
| chronos2_cur | 0.238 (0.219 to 0.260) | 1.000 | no |
| catchg_D | 0.237 (0.211 to 0.263) | 0.988 | no |
| catchg_DVdem | 0.236 (0.210 to 0.261) | 0.988 | no |
| avg_ridge_cat_D | 0.236 (0.214 to 0.261) | 0.988 | no |
| avg_ridge_cat_DW | 0.235 (0.212 to 0.262) | 0.988 | no |
| chronos2_bk | 0.235 (0.215 to 0.260) | 1.000 | no |
| lgbmchg_D | 0.234 (0.209 to 0.260) | 0.975 | no |
| catchg_DVnli | 0.233 (0.206 to 0.258) | 0.988 | no |
| chronos2_curdw | 0.232 (0.214 to 0.254) | 1.000 | no |
| chronos | 0.227 (0.208 to 0.249) | 1.000 | no |
| catboost_DW | 0.226 (0.198 to 0.255) | 0.975 | no |
| catboost_D | 0.225 (0.199 to 0.250) | 0.975 | no |
| ridge_D | 0.224 (0.202 to 0.251) | 0.963 | no |
| avg_naive_ridge_D | 0.224 (0.202 to 0.251) | 0.963 | no |
| chronos2_nli | 0.223 (0.204 to 0.247) | 1.000 | no |
| chronos2 | 0.222 (0.203 to 0.243) | 1.000 | no |
| ridgechg_D | 0.221 (0.200 to 0.249) | 0.975 | no |
| chronos2_top | 0.221 (0.200 to 0.244) | 1.000 | no |
| ridgechg_DWS | 0.221 (0.202 to 0.247) | 0.975 | no |
| ridge_DW | 0.221 (0.200 to 0.248) | 0.975 | no |
| ridgechg_DW | 0.217 (0.196 to 0.245) | 0.975 | no |
| revert6 | 0.202 (0.171 to 0.236) | 0.938 | no |
| seasonal_naive | 0.196 (0.174 to 0.220) | 0.951 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| median_s2_all | 0.246 (0.137 to 0.358) | 19.906 | yes |
| catchg_DVdem | 0.234 (0.131 to 0.335) | 18.929 | yes |
| catchg_DWS | 0.233 (0.135 to 0.334) | 18.839 | yes |
| catchg_DVnli | 0.229 (0.131 to 0.329) | 18.561 | no |
| catchg_DW | 0.227 (0.131 to 0.330) | 18.354 | yes |
| catchg_D | 0.227 (0.128 to 0.325) | 18.348 | no |
| median_s2_demand | 0.225 (0.119 to 0.335) | 18.200 | no |
| chronos2_bk | 0.214 (0.109 to 0.331) | 17.352 | yes |
| lgbmchg_D | 0.211 (0.113 to 0.312) | 17.052 | no |
| chronos2_curdw | 0.210 (0.107 to 0.324) | 17.036 | yes |
| chronos2_nli | 0.209 (0.106 to 0.327) | 16.931 | yes |
| median_all | 0.206 (0.097 to 0.325) | 16.657 | no |
| chronos2_cur | 0.202 (0.101 to 0.317) | 16.371 | no |
| chronos2_top | 0.201 (0.099 to 0.319) | 16.240 | yes |
| chronos2 | 0.200 (0.099 to 0.316) | 16.179 | no |
| catboost_D | 0.199 (0.099 to 0.310) | 16.113 | no |
| catboost_DW | 0.197 (0.093 to 0.308) | 15.919 | no |
| chronos | 0.194 (0.097 to 0.305) | 15.713 | no |
| avg_three_DW | 0.189 (0.088 to 0.315) | 15.261 | no |
| lightgbm_DW | 0.186 (0.087 to 0.308) | 15.045 | no |
| invmae_all | 0.185 (0.085 to 0.323) | 14.954 | no |
| lightgbm_D | 0.184 (0.086 to 0.301) | 14.908 | no |
| avg_ridge_cat_D | 0.165 (0.075 to 0.299) | 13.328 | no |
| avg_ridge_cat_DW | 0.162 (0.074 to 0.289) | 13.091 | no |
| ridgechg_DWS | 0.090 (0.041 to 0.187) | 7.324 | no |
| ridgechg_DW | 0.087 (0.039 to 0.179) | 7.060 | no |
| seasonal_naive | 0.079 (0.040 to 0.146) | 6.365 | no |
| ridge_DW | 0.077 (0.036 to 0.163) | 6.270 | no |
| ridgechg_D | 0.055 (0.029 to 0.112) | 4.478 | no |
| avg_naive_ridge_D | 0.047 (0.025 to 0.093) | 3.811 | no |
| ridge_D | 0.047 (0.025 to 0.093) | 3.811 | no |
| revert6 | 0.019 (0.014 to 0.028) | 1.573 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| median_s2_all | 5.959 | 0.714 | 0.076 |
| median_s2_demand | 6.059 | 0.705 | 0.073 |
| chronos2_cur | 6.077 | 0.657 | 0.072 |
| catchg_DWS | 6.086 | 0.688 | 0.067 |
| catchg_DW | 6.091 | 0.691 | 0.070 |
| median_all | 6.099 | 0.679 | 0.073 |
| chronos2_bk | 6.103 | 0.664 | 0.074 |
| chronos2_curdw | 6.107 | 0.656 | 0.072 |
| catchg_DVnli | 6.121 | 0.683 | 0.073 |
| catchg_D | 6.121 | 0.693 | 0.072 |
| chronos2_nli | 6.130 | 0.657 | 0.074 |
| catchg_DVdem | 6.133 | 0.687 | 0.072 |
| chronos2_top | 6.136 | 0.650 | 0.073 |
| chronos2 | 6.146 | 0.651 | 0.067 |
| chronos | 6.153 | 0.656 | 0.067 |
| invmae_all | 6.174 | 0.706 | 0.075 |
| lgbmchg_D | 6.218 | 0.682 | 0.070 |
| avg_three_DW | 6.253 | 0.701 | 0.075 |
| avg_naive_ridge_D | 6.258 | 0.681 | 0.067 |
| ridgechg_D | 6.294 | 0.679 | 0.072 |
| ridgechg_DWS | 6.301 | 0.685 | 0.069 |
| ridgechg_DW | 6.306 | 0.682 | 0.068 |
| lightgbm_D | 6.332 | 0.690 | 0.070 |
| lightgbm_DW | 6.341 | 0.686 | 0.070 |
| ridge_D | 6.342 | 0.681 | 0.067 |
| avg_ridge_cat_DW | 6.347 | 0.693 | 0.074 |
| ridge_DW | 6.348 | 0.683 | 0.069 |
| avg_ridge_cat_D | 6.351 | 0.693 | 0.078 |
| naive | 6.436 |  |  |
| catboost_DW | 6.595 | 0.680 | 0.075 |
| catboost_D | 6.665 | 0.680 | 0.076 |
| revert6 | 7.213 | 0.645 | 0.032 |
| seasonal_naive | 11.304 | 0.663 | 0.075 |

### D2. Seattle audiobooks, horizon 3

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| median_s2_all | 0.947 (0.931 to 0.960) | 0.959 | 0.768 | 9.031 | yes | 0.947 (0.934 to 0.960) | 0.942 (0.927 to 0.954) |
| median_s2_demand | 0.961 (0.945 to 0.975) | 0.964 | 0.679 | 11.978 | no | 0.968 (0.953 to 0.982) | 0.952 (0.937 to 0.965) |
| chronos2_cur | 0.964 (0.946 to 0.980) | 0.984 | 0.580 | 14.335 | no | 0.957 (0.941 to 0.973) | 0.966 (0.950 to 0.980) |
| catchg_DW | 0.967 (0.950 to 0.982) | 0.976 | 0.616 | 13.973 | no | 0.973 (0.960 to 0.988) | 0.962 (0.946 to 0.976) |
| median_all | 0.968 (0.951 to 0.984) | 0.972 | 0.634 | 13.228 | no | 0.981 (0.963 to 0.998) | 0.959 (0.943 to 0.973) |
| chronos2_bk | 0.968 (0.950 to 0.984) | 0.991 | 0.536 | 15.272 | no | 0.957 (0.941 to 0.973) | 0.968 (0.952 to 0.982) |
| chronos2_curdw | 0.970 (0.951 to 0.986) | 0.990 | 0.540 | 15.665 | no | 0.962 (0.946 to 0.978) | 0.972 (0.955 to 0.986) |
| catchg_DWS | 0.970 (0.952 to 0.985) | 0.979 | 0.612 | 14.804 | no | 0.974 (0.959 to 0.988) | 0.964 (0.948 to 0.978) |
| catchg_DVnli | 0.970 (0.953 to 0.985) | 0.977 | 0.616 | 14.531 | no | 0.976 (0.962 to 0.991) | 0.964 (0.948 to 0.978) |
| chronos2_nli | 0.972 (0.954 to 0.988) | 0.991 | 0.540 | 16.027 | no | 0.961 (0.946 to 0.977) | 0.974 (0.957 to 0.988) |
| catchg_DVdem | 0.973 (0.956 to 0.987) | 0.981 | 0.612 | 15.259 | no | 0.976 (0.961 to 0.991) | 0.966 (0.951 to 0.979) |
| avg_naive_ridge_D | 0.974 (0.968 to 0.979) | 0.970 | 0.741 | 13.174 | no | 0.989 (0.977 to 0.999) | 0.970 (0.964 to 0.975) |
| catchg_D | 0.974 (0.957 to 0.988) | 0.977 | 0.612 | 15.219 | no | 0.985 (0.971 to 0.999) | 0.968 (0.952 to 0.981) |
| chronos2_top | 0.974 (0.956 to 0.990) | 0.991 | 0.527 | 16.230 | no | 0.962 (0.946 to 0.977) | 0.976 (0.959 to 0.990) |
| invmae_all | 0.976 (0.960 to 0.991) | 0.981 | 0.607 | 14.330 | no | 0.998 (0.978 to 1.018) | 0.969 (0.954 to 0.983) |
| chronos2 | 0.977 (0.959 to 0.992) | 0.997 | 0.509 | 16.846 | no | 0.970 (0.953 to 0.987) | 0.977 (0.961 to 0.991) |
| chronos | 0.978 (0.962 to 0.993) | 0.996 | 0.522 | 16.299 | no | 0.976 (0.962 to 0.991) | 0.975 (0.960 to 0.989) |
| lgbmchg_D | 0.986 (0.965 to 1.004) | 0.992 | 0.545 | 17.411 | no | 0.980 (0.962 to 0.999) | 0.975 (0.956 to 0.991) |
| avg_three_DW | 0.991 (0.973 to 1.008) | 0.989 | 0.531 | 16.562 | no | 1.046 (1.017 to 1.073) | 0.989 (0.971 to 1.007) |
| ridgechg_D | 0.997 (0.984 to 1.009) | 0.988 | 0.554 | 17.259 | no | 1.042 (1.020 to 1.061) | 0.991 (0.979 to 1.003) |
| ridge_D | 0.999 (0.985 to 1.011) | 0.991 | 0.545 | 17.594 | no | 1.041 (1.017 to 1.064) | 0.994 (0.980 to 1.006) |
| ridge_DW | 0.999 (0.985 to 1.012) | 0.992 | 0.558 | 17.728 | no | 1.040 (1.016 to 1.061) | 0.992 (0.979 to 1.004) |
| ridgechg_DWS | 0.999 (0.987 to 1.011) | 0.996 | 0.518 | 17.549 | no | 1.039 (1.019 to 1.057) | 0.995 (0.982 to 1.006) |
| avg_ridge_cat_D | 0.999 (0.983 to 1.014) | 0.995 | 0.509 | 17.759 | no | 1.063 (1.031 to 1.093) | 1.001 (0.982 to 1.020) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 18.192 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| avg_ridge_cat_DW | 1.002 (0.985 to 1.019) | 0.990 | 0.531 | 17.634 | no | 1.089 (1.051 to 1.124) | 1.011 (0.989 to 1.033) |
| ridgechg_DW | 1.003 (0.990 to 1.015) | 0.997 | 0.513 | 18.424 | no | 1.050 (1.028 to 1.069) | 0.998 (0.986 to 1.011) |
| lightgbm_DW | 1.009 (0.986 to 1.029) | 1.008 | 0.460 | 19.763 | no | 1.030 (1.005 to 1.056) | 0.996 (0.976 to 1.015) |
| lightgbm_D | 1.010 (0.989 to 1.029) | 1.011 | 0.460 | 20.496 | no | 1.025 (1.000 to 1.049) | 0.994 (0.974 to 1.012) |
| catboost_D | 1.038 (1.014 to 1.060) | 1.035 | 0.415 | 22.089 | no | 1.163 (1.108 to 1.215) | 1.058 (1.025 to 1.092) |
| catboost_DW | 1.038 (1.012 to 1.064) | 1.018 | 0.438 | 21.129 | no | 1.201 (1.135 to 1.263) | 1.072 (1.034 to 1.113) |
| revert6 | 1.056 (1.038 to 1.074) | 1.055 | 0.321 | 23.299 | no | 1.057 (1.035 to 1.079) | 1.036 (1.020 to 1.052) |
| seasonal_naive | 1.622 (1.553 to 1.690) | 1.622 | 0.045 | 31.911 | no | 1.546 (1.477 to 1.626) | 1.573 (1.507 to 1.637) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| median_s2_all | 0.283 (0.254 to 0.311) | 1.000 | yes |
| median_s2_demand | 0.265 (0.234 to 0.293) | 1.000 | no |
| invmae_all | 0.264 (0.234 to 0.293) | 0.975 | no |
| median_all | 0.262 (0.233 to 0.291) | 0.975 | no |
| avg_three_DW | 0.253 (0.225 to 0.283) | 0.988 | no |
| catchg_DWS | 0.250 (0.223 to 0.274) | 1.000 | no |
| catchg_DW | 0.249 (0.219 to 0.277) | 0.975 | no |
| catchg_DVdem | 0.248 (0.218 to 0.273) | 0.988 | no |
| lightgbm_DW | 0.245 (0.213 to 0.273) | 0.988 | no |
| catchg_DVnli | 0.245 (0.211 to 0.273) | 0.988 | no |
| lgbmchg_D | 0.244 (0.209 to 0.272) | 0.988 | no |
| avg_ridge_cat_DW | 0.243 (0.217 to 0.273) | 0.963 | no |
| catchg_D | 0.241 (0.210 to 0.270) | 0.975 | no |
| avg_ridge_cat_D | 0.241 (0.214 to 0.271) | 0.975 | no |
| chronos2_cur | 0.240 (0.215 to 0.266) | 1.000 | no |
| lightgbm_D | 0.239 (0.203 to 0.270) | 0.975 | no |
| chronos2_bk | 0.238 (0.211 to 0.267) | 0.988 | no |
| chronos2_curdw | 0.236 (0.212 to 0.262) | 0.988 | no |
| catboost_DW | 0.236 (0.207 to 0.265) | 0.963 | no |
| ridge_D | 0.234 (0.210 to 0.265) | 0.988 | no |
| avg_naive_ridge_D | 0.234 (0.210 to 0.265) | 0.988 | no |
| ridge_DW | 0.229 (0.205 to 0.259) | 0.975 | no |
| catboost_D | 0.229 (0.197 to 0.260) | 0.975 | no |
| ridgechg_D | 0.228 (0.204 to 0.259) | 0.988 | no |
| chronos2_nli | 0.228 (0.199 to 0.257) | 0.975 | no |
| chronos | 0.225 (0.199 to 0.253) | 0.975 | no |
| ridgechg_DWS | 0.224 (0.203 to 0.252) | 0.988 | no |
| chronos2_top | 0.223 (0.194 to 0.253) | 0.963 | no |
| ridgechg_DW | 0.222 (0.199 to 0.252) | 0.988 | no |
| chronos2 | 0.221 (0.196 to 0.247) | 1.000 | no |
| seasonal_naive | 0.196 (0.167 to 0.222) | 0.925 | no |
| revert6 | 0.195 (0.161 to 0.234) | 0.912 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| median_s2_all | 0.211 (0.121 to 0.312) | 12.116 | yes |
| catchg_DVnli | 0.207 (0.121 to 0.296) | 11.916 | yes |
| catchg_DVdem | 0.203 (0.116 to 0.289) | 11.691 | yes |
| catchg_DWS | 0.202 (0.118 to 0.287) | 11.604 | yes |
| catchg_D | 0.201 (0.116 to 0.289) | 11.584 | yes |
| catchg_DW | 0.199 (0.116 to 0.282) | 11.435 | no |
| median_s2_demand | 0.195 (0.110 to 0.287) | 11.190 | no |
| lgbmchg_D | 0.193 (0.109 to 0.283) | 11.106 | no |
| chronos2_bk | 0.185 (0.103 to 0.286) | 10.654 | yes |
| chronos2_nli | 0.177 (0.097 to 0.278) | 10.177 | yes |
| chronos2_top | 0.176 (0.096 to 0.275) | 10.144 | yes |
| chronos2_cur | 0.175 (0.097 to 0.275) | 10.047 | yes |
| chronos2_curdw | 0.174 (0.095 to 0.275) | 10.026 | yes |
| catboost_DW | 0.174 (0.094 to 0.265) | 10.019 | no |
| catboost_D | 0.174 (0.098 to 0.260) | 10.007 | no |
| median_all | 0.173 (0.089 to 0.278) | 9.947 | no |
| chronos2 | 0.169 (0.090 to 0.268) | 9.724 | yes |
| chronos | 0.164 (0.090 to 0.256) | 9.425 | no |
| invmae_all | 0.163 (0.082 to 0.277) | 9.355 | no |
| lightgbm_D | 0.157 (0.081 to 0.262) | 9.018 | no |
| avg_three_DW | 0.149 (0.076 to 0.258) | 8.586 | no |
| avg_ridge_cat_D | 0.149 (0.076 to 0.256) | 8.575 | no |
| avg_ridge_cat_DW | 0.147 (0.074 to 0.256) | 8.455 | no |
| lightgbm_DW | 0.146 (0.076 to 0.248) | 8.393 | no |
| seasonal_naive | 0.104 (0.053 to 0.180) | 5.981 | no |
| ridge_DW | 0.081 (0.044 to 0.155) | 4.675 | no |
| ridgechg_DW | 0.076 (0.042 to 0.147) | 4.386 | no |
| ridgechg_DWS | 0.076 (0.041 to 0.148) | 4.351 | no |
| ridgechg_D | 0.069 (0.039 to 0.133) | 3.949 | no |
| avg_naive_ridge_D | 0.067 (0.039 to 0.123) | 3.849 | no |
| ridge_D | 0.067 (0.039 to 0.123) | 3.849 | no |
| revert6 | 0.032 (0.023 to 0.047) | 1.828 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| median_s2_all | 6.886 | 0.698 | 0.098 |
| chronos2_cur | 6.995 | 0.661 | 0.078 |
| median_s2_demand | 7.008 | 0.696 | 0.096 |
| chronos2_bk | 7.025 | 0.652 | 0.073 |
| catchg_DW | 7.034 | 0.676 | 0.101 |
| chronos2_curdw | 7.038 | 0.660 | 0.075 |
| catchg_DWS | 7.046 | 0.668 | 0.097 |
| chronos2_nli | 7.055 | 0.654 | 0.081 |
| catchg_DVnli | 7.060 | 0.669 | 0.091 |
| median_all | 7.067 | 0.670 | 0.093 |
| chronos2_top | 7.070 | 0.653 | 0.078 |
| catchg_DVdem | 7.079 | 0.673 | 0.091 |
| catchg_D | 7.090 | 0.678 | 0.098 |
| chronos2 | 7.094 | 0.647 | 0.076 |
| chronos | 7.113 | 0.664 | 0.076 |
| invmae_all | 7.130 | 0.686 | 0.098 |
| lgbmchg_D | 7.173 | 0.671 | 0.097 |
| avg_naive_ridge_D | 7.237 | 0.673 | 0.086 |
| avg_three_DW | 7.242 | 0.688 | 0.093 |
| avg_ridge_cat_D | 7.319 | 0.683 | 0.091 |
| avg_ridge_cat_DW | 7.336 | 0.682 | 0.092 |
| lightgbm_D | 7.355 | 0.676 | 0.095 |
| lightgbm_DW | 7.364 | 0.678 | 0.096 |
| ridgechg_D | 7.371 | 0.666 | 0.082 |
| ridgechg_DWS | 7.376 | 0.662 | 0.080 |
| ridge_DW | 7.390 | 0.670 | 0.090 |
| ridge_D | 7.391 | 0.673 | 0.086 |
| ridgechg_DW | 7.399 | 0.659 | 0.081 |
| naive | 7.472 |  |  |
| catboost_D | 7.532 | 0.680 | 0.092 |
| catboost_DW | 7.545 | 0.682 | 0.090 |
| revert6 | 7.947 | 0.638 | 0.052 |
| seasonal_naive | 12.023 | 0.648 | 0.092 |

### E2. LibriVox, horizon 1

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2 | 0.844 (0.832 to 0.856) | 0.841 | 0.971 | 4.206 | yes | 0.850 (0.838 to 0.860) | 0.860 (0.850 to 0.871) |
| chronos2_cur | 0.847 (0.835 to 0.860) | 0.847 | 0.978 | 4.515 | yes | 0.849 (0.837 to 0.860) | 0.863 (0.851 to 0.874) |
| chronos | 0.848 (0.837 to 0.861) | 0.848 | 0.978 | 4.750 | yes | 0.862 (0.848 to 0.875) | 0.863 (0.852 to 0.873) |
| median_all | 0.868 (0.860 to 0.878) | 0.863 | 0.978 | 4.397 | no | 0.854 (0.846 to 0.863) | 0.833 (0.824 to 0.842) |
| invmae_all | 0.882 (0.872 to 0.892) | 0.877 | 0.956 | 6.044 | no | 0.861 (0.852 to 0.870) | 0.837 (0.829 to 0.845) |
| avg_ridge_cat_D | 0.893 (0.883 to 0.904) | 0.885 | 0.926 | 7.441 | no | 0.866 (0.858 to 0.876) | 0.833 (0.824 to 0.842) |
| avg_three_DW | 0.898 (0.886 to 0.911) | 0.891 | 0.912 | 8.301 | no | 0.873 (0.864 to 0.882) | 0.837 (0.827 to 0.847) |
| avg_ridge_cat_DW | 0.898 (0.887 to 0.911) | 0.890 | 0.919 | 8.368 | no | 0.877 (0.868 to 0.887) | 0.836 (0.825 to 0.846) |
| catboost_D | 0.904 (0.890 to 0.918) | 0.891 | 0.875 | 9.088 | no | 0.876 (0.864 to 0.888) | 0.842 (0.833 to 0.852) |
| catboost_DW | 0.910 (0.897 to 0.925) | 0.896 | 0.890 | 9.934 | no | 0.896 (0.881 to 0.910) | 0.843 (0.832 to 0.853) |
| ridge_D | 0.911 (0.900 to 0.921) | 0.908 | 0.882 | 9.934 | no | 0.889 (0.881 to 0.898) | 0.842 (0.831 to 0.851) |
| ridge_DW | 0.916 (0.905 to 0.927) | 0.912 | 0.875 | 10.846 | no | 0.895 (0.886 to 0.904) | 0.849 (0.835 to 0.865) |
| avg_naive_ridge_D | 0.920 (0.915 to 0.924) | 0.921 | 1.000 | 11.074 | no | 0.908 (0.903 to 0.913) | 0.890 (0.885 to 0.894) |
| revert6 | 0.943 (0.928 to 0.959) | 0.935 | 0.735 | 12.221 | no | 0.900 (0.884 to 0.919) | 0.859 (0.845 to 0.872) |
| lightgbm_DW | 0.953 (0.938 to 0.971) | 0.954 | 0.743 | 13.353 | no | 0.922 (0.908 to 0.936) | 0.873 (0.861 to 0.884) |
| lightgbm_D | 0.955 (0.939 to 0.973) | 0.943 | 0.691 | 13.221 | no | 0.910 (0.898 to 0.923) | 0.874 (0.863 to 0.885) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 15.309 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| seasonal_naive | 1.487 (1.446 to 1.533) | 1.443 | 0.000 | 18.000 | no | 1.377 (1.342 to 1.416) | 1.289 (1.263 to 1.317) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos2_cur | 0.406 (0.361 to 0.451) | 0.956 | yes |
| chronos2 | 0.397 (0.351 to 0.445) | 0.956 | yes |
| median_all | 0.393 (0.343 to 0.437) | 0.967 | yes |
| chronos | 0.393 (0.350 to 0.438) | 0.967 | yes |
| invmae_all | 0.391 (0.342 to 0.436) | 0.945 | yes |
| avg_ridge_cat_D | 0.388 (0.338 to 0.431) | 0.956 | yes |
| avg_ridge_cat_DW | 0.385 (0.336 to 0.428) | 0.956 | yes |
| revert6 | 0.382 (0.342 to 0.415) | 0.978 | yes |
| ridge_DW | 0.379 (0.333 to 0.418) | 0.956 | yes |
| avg_three_DW | 0.379 (0.328 to 0.424) | 0.945 | no |
| catboost_D | 0.378 (0.328 to 0.424) | 0.945 | no |
| ridge_D | 0.376 (0.331 to 0.416) | 0.956 | yes |
| avg_naive_ridge_D | 0.376 (0.331 to 0.416) | 0.956 | yes |
| catboost_DW | 0.374 (0.325 to 0.420) | 0.945 | no |
| lightgbm_D | 0.342 (0.294 to 0.388) | 0.956 | no |
| lightgbm_DW | 0.334 (0.287 to 0.380) | 0.934 | no |
| seasonal_naive | 0.299 (0.260 to 0.337) | 0.956 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| avg_ridge_cat_DW | 0.218 (0.183 to 0.258) | 1.565 | yes |
| ridge_DW | 0.218 (0.184 to 0.254) | 1.560 | yes |
| chronos2_cur | 0.214 (0.177 to 0.257) | 1.532 | yes |
| avg_three_DW | 0.211 (0.175 to 0.252) | 1.515 | no |
| revert6 | 0.209 (0.181 to 0.242) | 1.499 | yes |
| median_all | 0.209 (0.174 to 0.247) | 1.497 | no |
| invmae_all | 0.208 (0.173 to 0.247) | 1.493 | no |
| avg_naive_ridge_D | 0.207 (0.175 to 0.242) | 1.488 | no |
| ridge_D | 0.207 (0.175 to 0.242) | 1.488 | no |
| catboost_DW | 0.207 (0.171 to 0.247) | 1.483 | no |
| avg_ridge_cat_D | 0.206 (0.172 to 0.244) | 1.481 | no |
| chronos | 0.203 (0.162 to 0.253) | 1.457 | yes |
| chronos2 | 0.202 (0.166 to 0.246) | 1.450 | no |
| catboost_D | 0.197 (0.161 to 0.236) | 1.415 | no |
| lightgbm_DW | 0.187 (0.151 to 0.228) | 1.342 | no |
| lightgbm_D | 0.176 (0.143 to 0.215) | 1.266 | no |
| seasonal_naive | 0.176 (0.145 to 0.212) | 1.260 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos2 | 21.711 | 0.712 | 0.207 |
| chronos | 21.815 | 0.694 | 0.201 |
| chronos2_cur | 21.822 | 0.710 | 0.224 |
| median_all | 22.503 | 0.665 | 0.187 |
| invmae_all | 22.847 | 0.697 | 0.160 |
| avg_ridge_cat_D | 23.176 | 0.692 | 0.165 |
| avg_three_DW | 23.279 | 0.688 | 0.187 |
| avg_ridge_cat_DW | 23.303 | 0.687 | 0.181 |
| catboost_D | 23.479 | 0.688 | 0.173 |
| ridge_D | 23.606 | 0.684 | 0.174 |
| catboost_DW | 23.609 | 0.678 | 0.198 |
| ridge_DW | 23.759 | 0.683 | 0.188 |
| avg_naive_ridge_D | 23.815 | 0.684 | 0.174 |
| revert6 | 24.494 | 0.685 | 0.162 |
| lightgbm_DW | 24.697 | 0.658 | 0.188 |
| lightgbm_D | 24.796 | 0.662 | 0.176 |
| naive | 25.854 |  |  |
| seasonal_naive | 38.690 | 0.637 | 0.162 |

### E2. LibriVox, horizon 2

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2 | 0.809 (0.798 to 0.822) | 0.806 | 0.978 | 3.721 | yes | 0.811 (0.802 to 0.819) | 0.818 (0.809 to 0.827) |
| chronos2_cur | 0.810 (0.799 to 0.822) | 0.808 | 0.971 | 3.757 | yes | 0.810 (0.801 to 0.819) | 0.818 (0.809 to 0.828) |
| chronos | 0.822 (0.810 to 0.835) | 0.819 | 0.978 | 5.390 | no | 0.830 (0.816 to 0.843) | 0.825 (0.814 to 0.835) |
| median_all | 0.834 (0.826 to 0.844) | 0.835 | 0.993 | 5.051 | no | 0.825 (0.816 to 0.836) | 0.799 (0.791 to 0.807) |
| invmae_all | 0.845 (0.835 to 0.855) | 0.839 | 0.985 | 6.471 | no | 0.829 (0.821 to 0.839) | 0.802 (0.793 to 0.810) |
| avg_ridge_cat_D | 0.856 (0.846 to 0.868) | 0.853 | 0.971 | 7.662 | no | 0.835 (0.826 to 0.845) | 0.799 (0.791 to 0.806) |
| catboost_D | 0.859 (0.847 to 0.873) | 0.857 | 0.963 | 8.507 | no | 0.845 (0.835 to 0.855) | 0.805 (0.796 to 0.814) |
| avg_three_DW | 0.860 (0.848 to 0.874) | 0.852 | 0.963 | 8.331 | no | 0.840 (0.831 to 0.849) | 0.808 (0.798 to 0.819) |
| avg_ridge_cat_DW | 0.862 (0.851 to 0.876) | 0.858 | 0.956 | 8.537 | no | 0.842 (0.834 to 0.851) | 0.808 (0.797 to 0.823) |
| catboost_DW | 0.867 (0.854 to 0.881) | 0.860 | 0.949 | 9.544 | no | 0.859 (0.846 to 0.870) | 0.810 (0.802 to 0.819) |
| revert6 | 0.876 (0.862 to 0.891) | 0.869 | 0.941 | 10.088 | no | 0.842 (0.828 to 0.858) | 0.814 (0.804 to 0.825) |
| ridge_D | 0.878 (0.867 to 0.890) | 0.878 | 0.963 | 10.522 | no | 0.854 (0.842 to 0.866) | 0.812 (0.804 to 0.819) |
| ridge_DW | 0.884 (0.871 to 0.899) | 0.877 | 0.949 | 11.096 | no | 0.860 (0.848 to 0.872) | 0.823 (0.808 to 0.846) |
| avg_naive_ridge_D | 0.896 (0.891 to 0.901) | 0.894 | 0.993 | 12.721 | no | 0.884 (0.878 to 0.890) | 0.861 (0.855 to 0.866) |
| lightgbm_D | 0.901 (0.884 to 0.920) | 0.890 | 0.890 | 12.382 | no | 0.874 (0.863 to 0.887) | 0.839 (0.826 to 0.852) |
| lightgbm_DW | 0.904 (0.889 to 0.922) | 0.897 | 0.919 | 12.904 | no | 0.882 (0.871 to 0.896) | 0.837 (0.826 to 0.848) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 16.375 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| seasonal_naive | 1.359 (1.317 to 1.407) | 1.306 | 0.015 | 17.941 | no | 1.266 (1.235 to 1.301) | 1.210 (1.180 to 1.248) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos2_cur | 0.441 (0.388 to 0.492) | 0.956 | yes |
| median_all | 0.432 (0.383 to 0.479) | 0.978 | yes |
| chronos2 | 0.431 (0.378 to 0.483) | 0.967 | yes |
| avg_ridge_cat_D | 0.429 (0.379 to 0.477) | 0.956 | yes |
| catboost_D | 0.427 (0.379 to 0.474) | 0.978 | yes |
| invmae_all | 0.427 (0.378 to 0.475) | 0.978 | yes |
| chronos | 0.426 (0.380 to 0.473) | 0.978 | yes |
| avg_ridge_cat_DW | 0.424 (0.377 to 0.471) | 0.967 | yes |
| avg_three_DW | 0.422 (0.373 to 0.469) | 0.978 | no |
| revert6 | 0.419 (0.373 to 0.457) | 0.978 | yes |
| catboost_DW | 0.417 (0.369 to 0.464) | 0.978 | no |
| ridge_D | 0.415 (0.366 to 0.462) | 0.956 | no |
| avg_naive_ridge_D | 0.415 (0.366 to 0.462) | 0.956 | no |
| ridge_DW | 0.414 (0.366 to 0.461) | 0.967 | no |
| lightgbm_D | 0.390 (0.338 to 0.440) | 0.978 | no |
| lightgbm_DW | 0.386 (0.337 to 0.433) | 0.978 | no |
| seasonal_naive | 0.305 (0.262 to 0.347) | 0.933 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos2_cur | 0.262 (0.225 to 0.302) | 1.567 | yes |
| avg_ridge_cat_DW | 0.262 (0.230 to 0.296) | 1.565 | yes |
| avg_ridge_cat_D | 0.261 (0.227 to 0.298) | 1.560 | yes |
| median_all | 0.260 (0.225 to 0.298) | 1.556 | yes |
| ridge_DW | 0.260 (0.228 to 0.293) | 1.553 | yes |
| avg_three_DW | 0.259 (0.227 to 0.294) | 1.552 | yes |
| ridge_D | 0.257 (0.225 to 0.291) | 1.540 | yes |
| avg_naive_ridge_D | 0.257 (0.225 to 0.291) | 1.540 | yes |
| invmae_all | 0.257 (0.224 to 0.293) | 1.538 | yes |
| revert6 | 0.255 (0.227 to 0.285) | 1.524 | yes |
| chronos2 | 0.254 (0.216 to 0.295) | 1.522 | no |
| catboost_DW | 0.254 (0.220 to 0.291) | 1.521 | yes |
| catboost_D | 0.253 (0.216 to 0.292) | 1.514 | yes |
| chronos | 0.252 (0.213 to 0.291) | 1.509 | no |
| lightgbm_DW | 0.243 (0.207 to 0.280) | 1.456 | no |
| lightgbm_D | 0.240 (0.201 to 0.280) | 1.434 | no |
| seasonal_naive | 0.208 (0.174 to 0.245) | 1.245 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos2 | 23.967 | 0.717 | 0.267 |
| chronos2_cur | 23.996 | 0.717 | 0.275 |
| chronos | 24.309 | 0.696 | 0.268 |
| median_all | 24.847 | 0.698 | 0.202 |
| invmae_all | 25.195 | 0.723 | 0.203 |
| avg_ridge_cat_D | 25.490 | 0.722 | 0.214 |
| catboost_D | 25.615 | 0.720 | 0.217 |
| avg_three_DW | 25.643 | 0.721 | 0.197 |
| avg_ridge_cat_DW | 25.702 | 0.721 | 0.214 |
| catboost_DW | 25.787 | 0.713 | 0.200 |
| revert6 | 26.073 | 0.715 | 0.195 |
| ridge_D | 26.130 | 0.713 | 0.206 |
| ridge_DW | 26.404 | 0.712 | 0.224 |
| avg_naive_ridge_D | 26.761 | 0.713 | 0.206 |
| lightgbm_D | 26.890 | 0.695 | 0.198 |
| lightgbm_DW | 26.956 | 0.692 | 0.198 |
| naive | 29.853 |  |  |
| seasonal_naive | 40.550 | 0.632 | 0.202 |

### Stage-1 roster alone, horizon 1, with the new metrics

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos | 0.945 (0.926 to 0.962) | 0.987 | 0.569 | 8.637 | yes | 0.920 (0.886 to 0.952) | 0.943 (0.923 to 0.960) |
| catchg_DW | 0.957 (0.944 to 0.969) | 0.971 | 0.659 | 7.416 | yes | 0.937 (0.913 to 0.960) | 0.959 (0.945 to 0.970) |
| catchg_D | 0.959 (0.946 to 0.971) | 0.974 | 0.663 | 7.588 | yes | 0.941 (0.917 to 0.964) | 0.963 (0.949 to 0.975) |
| catchg_DWS | 0.960 (0.947 to 0.971) | 0.973 | 0.663 | 7.773 | yes | 0.944 (0.920 to 0.966) | 0.965 (0.952 to 0.975) |
| median_all | 0.963 (0.951 to 0.974) | 0.969 | 0.647 | 7.110 | no | 0.955 (0.932 to 0.978) | 0.960 (0.947 to 0.970) |
| invmae_all | 0.976 (0.964 to 0.988) | 0.980 | 0.590 | 8.925 | no | 0.990 (0.964 to 1.016) | 0.979 (0.965 to 0.991) |
| lightgbm_D | 0.983 (0.968 to 0.998) | 0.993 | 0.518 | 10.261 | no | 0.984 (0.952 to 1.015) | 0.988 (0.972 to 1.002) |
| avg_naive_ridge_D | 0.984 (0.982 to 0.987) | 0.979 | 0.745 | 9.255 | no | 0.988 (0.983 to 0.993) | 0.983 (0.981 to 0.986) |
| ridgechg_D | 0.989 (0.984 to 0.994) | 0.978 | 0.649 | 9.473 | no | 0.993 (0.983 to 1.004) | 0.984 (0.979 to 0.989) |
| ridgechg_DW | 0.992 (0.986 to 0.998) | 0.980 | 0.618 | 10.027 | no | 0.999 (0.988 to 1.010) | 0.988 (0.982 to 0.993) |
| ridgechg_DWS | 0.992 (0.986 to 0.998) | 0.980 | 0.618 | 10.157 | no | 1.000 (0.988 to 1.013) | 0.988 (0.983 to 0.993) |
| lightgbm_DW | 0.995 (0.978 to 1.010) | 1.006 | 0.475 | 11.516 | no | 0.997 (0.966 to 1.026) | 1.002 (0.984 to 1.016) |
| avg_three_DW | 0.996 (0.983 to 1.009) | 0.988 | 0.551 | 10.176 | no | 1.053 (1.019 to 1.085) | 1.009 (0.992 to 1.027) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 11.704 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| ridge_D | 1.001 (0.995 to 1.008) | 0.985 | 0.578 | 11.494 | no | 1.014 (1.001 to 1.027) | 0.997 (0.991 to 1.004) |
| ridge_DW | 1.005 (0.998 to 1.013) | 0.990 | 0.559 | 12.092 | no | 1.023 (1.008 to 1.037) | 1.003 (0.995 to 1.010) |
| avg_ridge_cat_D | 1.025 (1.011 to 1.038) | 1.002 | 0.486 | 12.259 | no | 1.134 (1.089 to 1.174) | 1.051 (1.028 to 1.076) |
| avg_ridge_cat_DW | 1.027 (1.013 to 1.040) | 1.008 | 0.469 | 12.627 | no | 1.134 (1.091 to 1.174) | 1.054 (1.031 to 1.079) |
| catboost_D | 1.083 (1.060 to 1.107) | 1.047 | 0.310 | 15.618 | no | 1.302 (1.218 to 1.380) | 1.141 (1.099 to 1.187) |
| catboost_DW | 1.090 (1.068 to 1.114) | 1.058 | 0.304 | 16.296 | no | 1.303 (1.222 to 1.375) | 1.155 (1.115 to 1.199) |
| seasonal_naive | 2.086 (2.015 to 2.161) | 2.177 | 0.035 | 20.596 | no | 1.968 (1.856 to 2.075) | 1.987 (1.921 to 2.053) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos | 0.282 (0.251 to 0.311) | 0.989 | yes |
| catchg_D | 0.266 (0.236 to 0.295) | 0.977 | yes |
| invmae_all | 0.264 (0.224 to 0.299) | 0.943 | yes |
| catchg_DW | 0.263 (0.233 to 0.291) | 0.977 | no |
| catchg_DWS | 0.263 (0.235 to 0.289) | 0.977 | no |
| lightgbm_D | 0.263 (0.227 to 0.294) | 0.943 | no |
| median_all | 0.258 (0.220 to 0.290) | 0.955 | no |
| lightgbm_DW | 0.255 (0.219 to 0.286) | 0.932 | no |
| avg_three_DW | 0.246 (0.210 to 0.277) | 0.943 | no |
| avg_ridge_cat_DW | 0.217 (0.183 to 0.245) | 0.932 | no |
| avg_ridge_cat_D | 0.215 (0.182 to 0.245) | 0.932 | no |
| ridge_DW | 0.208 (0.174 to 0.238) | 0.932 | no |
| ridgechg_DW | 0.207 (0.175 to 0.236) | 0.932 | no |
| catboost_DW | 0.207 (0.174 to 0.234) | 0.943 | no |
| catboost_D | 0.206 (0.172 to 0.235) | 0.943 | no |
| ridgechg_DWS | 0.205 (0.175 to 0.234) | 0.932 | no |
| ridgechg_D | 0.203 (0.172 to 0.232) | 0.932 | no |
| ridge_D | 0.201 (0.169 to 0.232) | 0.932 | no |
| avg_naive_ridge_D | 0.201 (0.169 to 0.232) | 0.932 | no |
| seasonal_naive | 0.174 (0.133 to 0.211) | 0.920 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos | 0.235 (0.147 to 0.315) | 34.286 | yes |
| median_all | 0.161 (0.084 to 0.242) | 23.524 | no |
| catchg_D | 0.153 (0.084 to 0.232) | 22.378 | no |
| avg_three_DW | 0.148 (0.071 to 0.242) | 21.636 | no |
| invmae_all | 0.143 (0.073 to 0.239) | 20.843 | no |
| catchg_DW | 0.143 (0.079 to 0.210) | 20.831 | no |
| catchg_DWS | 0.135 (0.080 to 0.199) | 19.676 | no |
| catboost_DW | 0.123 (0.058 to 0.196) | 17.990 | no |
| avg_ridge_cat_DW | 0.121 (0.054 to 0.204) | 17.608 | no |
| catboost_D | 0.114 (0.052 to 0.199) | 16.617 | no |
| lightgbm_D | 0.112 (0.054 to 0.225) | 16.290 | no |
| lightgbm_DW | 0.095 (0.047 to 0.243) | 13.874 | no |
| avg_ridge_cat_D | 0.073 (0.035 to 0.140) | 10.596 | no |
| ridgechg_DWS | 0.069 (0.029 to 0.134) | 9.993 | no |
| ridgechg_DW | 0.062 (0.027 to 0.127) | 9.034 | no |
| ridge_DW | 0.043 (0.023 to 0.094) | 6.219 | no |
| seasonal_naive | 0.026 (0.017 to 0.038) | 3.841 | no |
| ridgechg_D | 0.020 (0.013 to 0.031) | 2.938 | no |
| ridge_D | 0.018 (0.012 to 0.026) | 2.647 | no |
| avg_naive_ridge_D | 0.018 (0.012 to 0.026) | 2.647 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos | 4.681 | 0.736 | 0.044 |
| catchg_DW | 4.752 | 0.732 | 0.037 |
| catchg_D | 4.762 | 0.734 | 0.037 |
| catchg_DWS | 4.763 | 0.727 | 0.038 |
| median_all | 4.787 | 0.708 | 0.041 |
| invmae_all | 4.837 | 0.744 | 0.044 |
| lightgbm_D | 4.851 | 0.727 | 0.042 |
| lightgbm_DW | 4.901 | 0.732 | 0.044 |
| avg_three_DW | 4.917 | 0.729 | 0.041 |
| avg_naive_ridge_D | 4.965 | 0.692 | 0.027 |
| ridgechg_DWS | 4.972 | 0.701 | 0.037 |
| ridgechg_DW | 4.974 | 0.703 | 0.039 |
| ridgechg_D | 4.976 | 0.692 | 0.028 |
| ridge_D | 5.028 | 0.692 | 0.027 |
| ridge_DW | 5.030 | 0.705 | 0.038 |
| naive | 5.059 |  |  |
| avg_ridge_cat_D | 5.066 | 0.706 | 0.040 |
| avg_ridge_cat_DW | 5.072 | 0.704 | 0.040 |
| catboost_D | 5.306 | 0.687 | 0.037 |
| catboost_DW | 5.352 | 0.693 | 0.036 |
| seasonal_naive | 10.717 | 0.690 | 0.034 |

**Paired comparisons, model held fixed (S1_h1)**: MAE ratio of the second to the first (below 1 = the second is better), difference in Spearman and in surge average precision

| pair | question | MAE ratio (95%) | share of series better | Spearman difference (95%) | surge AP difference (95%) |
| --- | --- | --- | --- | --- | --- |
| ridgechg_D -> ridgechg_DW | behavior against no behavior | 1.003 (1.001 to 1.005) | 0.420 | +0.004 (-0.001 to +0.009) | +0.042 (+0.010 to +0.104) |
| ridgechg_D -> ridgechg_DWS | behavior against no behavior | 1.003 (1.001 to 1.005) | 0.427 | +0.002 (-0.004 to +0.009) | +0.048 (+0.013 to +0.112) |
| catchg_D -> catchg_DW | behavior against no behavior | 0.998 (0.996 to 1.000) | 0.529 | -0.003 (-0.008 to +0.001) | -0.011 (-0.045 to +0.022) |
| catchg_D -> catchg_DWS | behavior against no behavior | 1.001 (0.998 to 1.003) | 0.473 | -0.004 (-0.009 to +0.002) | -0.019 (-0.051 to +0.014) |

### Stage-1 roster alone, horizon 2, with the new metrics

**Level task** (AvgRelMAE below 1 beats repeating last month; in_MCS = in the 90% confidence set)

| pipeline | AvgRelMAE (95%) | median ratio | share of series better than naive | mean rank | in confidence set | volume-weighted (95%) | relative RMSE (95%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chronos | 0.905 (0.879 to 0.927) | 0.970 | 0.614 | 7.686 | yes | 0.857 (0.816 to 0.897) | 0.908 (0.884 to 0.929) |
| catchg_DW | 0.935 (0.917 to 0.951) | 0.963 | 0.678 | 7.376 | no | 0.904 (0.871 to 0.936) | 0.939 (0.921 to 0.954) |
| catchg_DWS | 0.937 (0.918 to 0.953) | 0.965 | 0.651 | 7.822 | no | 0.904 (0.871 to 0.937) | 0.941 (0.923 to 0.957) |
| catchg_D | 0.937 (0.918 to 0.954) | 0.963 | 0.671 | 7.445 | no | 0.913 (0.878 to 0.947) | 0.945 (0.927 to 0.961) |
| median_all | 0.940 (0.922 to 0.956) | 0.962 | 0.657 | 7.363 | no | 0.909 (0.877 to 0.940) | 0.936 (0.919 to 0.950) |
| invmae_all | 0.950 (0.933 to 0.966) | 0.974 | 0.616 | 8.410 | no | 0.949 (0.917 to 0.981) | 0.954 (0.937 to 0.969) |
| avg_naive_ridge_D | 0.973 (0.968 to 0.977) | 0.964 | 0.739 | 9.422 | no | 0.977 (0.967 to 0.987) | 0.970 (0.966 to 0.974) |
| avg_three_DW | 0.976 (0.959 to 0.992) | 0.981 | 0.565 | 10.245 | no | 1.007 (0.970 to 1.043) | 0.983 (0.964 to 1.001) |
| lightgbm_D | 0.977 (0.955 to 0.998) | 0.998 | 0.508 | 11.255 | no | 0.952 (0.911 to 0.995) | 0.984 (0.961 to 1.005) |
| ridgechg_D | 0.978 (0.970 to 0.987) | 0.967 | 0.637 | 10.080 | no | 0.982 (0.964 to 1.000) | 0.970 (0.962 to 0.978) |
| ridgechg_DW | 0.981 (0.972 to 0.989) | 0.968 | 0.618 | 10.427 | no | 0.982 (0.964 to 1.002) | 0.972 (0.964 to 0.980) |
| ridgechg_DWS | 0.981 (0.972 to 0.990) | 0.969 | 0.614 | 10.555 | no | 0.984 (0.965 to 1.005) | 0.973 (0.964 to 0.981) |
| lightgbm_DW | 0.989 (0.965 to 1.011) | 1.011 | 0.463 | 12.324 | no | 0.957 (0.916 to 0.999) | 0.993 (0.970 to 1.014) |
| ridge_D | 0.995 (0.985 to 1.006) | 0.984 | 0.569 | 12.392 | no | 1.007 (0.984 to 1.030) | 0.987 (0.977 to 0.997) |
| ridge_DW | 0.997 (0.986 to 1.008) | 0.982 | 0.565 | 12.567 | no | 1.008 (0.986 to 1.031) | 0.989 (0.978 to 0.999) |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 0.000 | 12.106 | no | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |
| avg_ridge_cat_DW | 1.000 (0.984 to 1.016) | 0.989 | 0.533 | 12.010 | no | 1.085 (1.039 to 1.126) | 1.015 (0.993 to 1.038) |
| avg_ridge_cat_D | 1.002 (0.986 to 1.018) | 0.991 | 0.522 | 11.839 | no | 1.098 (1.050 to 1.142) | 1.021 (0.998 to 1.046) |
| catboost_DW | 1.044 (1.017 to 1.070) | 1.031 | 0.420 | 14.596 | no | 1.230 (1.146 to 1.309) | 1.084 (1.045 to 1.124) |
| catboost_D | 1.053 (1.025 to 1.080) | 1.036 | 0.406 | 14.857 | no | 1.257 (1.167 to 1.344) | 1.108 (1.066 to 1.155) |
| seasonal_naive | 1.737 (1.672 to 1.802) | 1.807 | 0.063 | 20.224 | no | 1.597 (1.486 to 1.701) | 1.679 (1.619 to 1.736) |

**Rise task** (cross-theme Spearman of forecast and actual change, mean over months)

| pipeline | Spearman (95%) | share of months above 0 | in confidence set |
| --- | --- | --- | --- |
| chronos | 0.333 (0.300 to 0.363) | 1.000 | yes |
| catchg_D | 0.310 (0.273 to 0.345) | 0.977 | no |
| catchg_DWS | 0.310 (0.273 to 0.343) | 0.977 | no |
| catchg_DW | 0.308 (0.270 to 0.344) | 0.965 | no |
| invmae_all | 0.302 (0.255 to 0.343) | 0.930 | no |
| lightgbm_D | 0.296 (0.254 to 0.335) | 0.942 | no |
| median_all | 0.295 (0.252 to 0.335) | 0.942 | no |
| lightgbm_DW | 0.285 (0.240 to 0.325) | 0.942 | no |
| avg_three_DW | 0.283 (0.241 to 0.323) | 0.942 | no |
| avg_ridge_cat_D | 0.266 (0.227 to 0.305) | 0.942 | no |
| avg_ridge_cat_DW | 0.264 (0.224 to 0.303) | 0.942 | no |
| catboost_D | 0.262 (0.224 to 0.300) | 0.942 | no |
| catboost_DW | 0.258 (0.219 to 0.296) | 0.942 | no |
| ridgechg_D | 0.250 (0.212 to 0.288) | 0.930 | no |
| ridge_D | 0.246 (0.207 to 0.284) | 0.930 | no |
| avg_naive_ridge_D | 0.246 (0.207 to 0.284) | 0.930 | no |
| ridgechg_DW | 0.244 (0.207 to 0.282) | 0.942 | no |
| ridgechg_DWS | 0.243 (0.207 to 0.278) | 0.942 | no |
| ridge_DW | 0.242 (0.204 to 0.281) | 0.942 | no |
| seasonal_naive | 0.204 (0.153 to 0.247) | 0.895 | no |

**Surge task** (average precision of flagging a theme about to rise by 30% or more; lift = average precision / base rate)

| pipeline | average precision (95%) | lift | not distinguishable from the best |
| --- | --- | --- | --- |
| chronos | 0.348 (0.268 to 0.427) | 22.596 | yes |
| invmae_all | 0.272 (0.196 to 0.360) | 17.668 | no |
| median_all | 0.269 (0.195 to 0.349) | 17.463 | no |
| catchg_DW | 0.262 (0.187 to 0.349) | 16.992 | no |
| catchg_DWS | 0.256 (0.180 to 0.350) | 16.629 | no |
| catchg_D | 0.252 (0.170 to 0.346) | 16.380 | no |
| catboost_DW | 0.238 (0.166 to 0.312) | 15.467 | no |
| avg_three_DW | 0.235 (0.165 to 0.315) | 15.271 | no |
| catboost_D | 0.227 (0.154 to 0.307) | 14.761 | no |
| lightgbm_DW | 0.211 (0.142 to 0.317) | 13.693 | no |
| lightgbm_D | 0.209 (0.134 to 0.326) | 13.593 | no |
| avg_ridge_cat_DW | 0.205 (0.139 to 0.284) | 13.318 | no |
| avg_ridge_cat_D | 0.197 (0.131 to 0.275) | 12.804 | no |
| ridgechg_DWS | 0.100 (0.069 to 0.141) | 6.507 | no |
| ridgechg_DW | 0.097 (0.067 to 0.135) | 6.281 | no |
| ridge_DW | 0.082 (0.060 to 0.114) | 5.356 | no |
| seasonal_naive | 0.081 (0.058 to 0.112) | 5.290 | no |
| ridgechg_D | 0.076 (0.055 to 0.102) | 4.911 | no |
| ridge_D | 0.067 (0.049 to 0.092) | 4.343 | no |
| avg_naive_ridge_D | 0.067 (0.049 to 0.092) | 4.343 | no |

**Plain numbers** (pooled over all scored forecasts)

| pipeline | mean absolute error (%) | direction right for moves above 10% | flagged top 5% that surge |
| --- | --- | --- | --- |
| chronos | 5.875 | 0.746 | 0.118 |
| catchg_DW | 6.093 | 0.739 | 0.105 |
| catchg_D | 6.097 | 0.740 | 0.108 |
| catchg_DWS | 6.099 | 0.741 | 0.106 |
| median_all | 6.137 | 0.720 | 0.110 |
| invmae_all | 6.188 | 0.741 | 0.120 |
| lightgbm_D | 6.306 | 0.736 | 0.110 |
| avg_three_DW | 6.334 | 0.736 | 0.110 |
| lightgbm_DW | 6.378 | 0.728 | 0.113 |
| avg_naive_ridge_D | 6.495 | 0.717 | 0.089 |
| ridgechg_D | 6.496 | 0.724 | 0.094 |
| ridgechg_DWS | 6.498 | 0.712 | 0.096 |
| ridgechg_DW | 6.501 | 0.717 | 0.100 |
| avg_ridge_cat_DW | 6.507 | 0.723 | 0.102 |
| avg_ridge_cat_D | 6.526 | 0.726 | 0.107 |
| ridge_D | 6.585 | 0.717 | 0.089 |
| ridge_DW | 6.587 | 0.715 | 0.098 |
| naive | 6.726 |  |  |
| catboost_DW | 6.727 | 0.710 | 0.100 |
| catboost_D | 6.781 | 0.715 | 0.106 |
| seasonal_naive | 11.649 | 0.685 | 0.088 |

## When: segments (print and ebook; segments with fewer than 20 series are not reported)

### h1 quiet (520 series, 34793 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.917 (0.898 to 0.935) | 0.876 | 0.920 | 0.314 | 0.161 |
| chronos2_bk | 0.920 (0.900 to 0.938) | 0.876 | 0.920 | 0.316 | 0.157 |
| chronos2_curdw | 0.920 (0.901 to 0.938) | 0.879 | 0.922 | 0.312 | 0.161 |
| chronos2_nli | 0.922 (0.902 to 0.939) | 0.879 | 0.922 | 0.311 | 0.157 |
| chronos2 | 0.923 (0.904 to 0.941) | 0.880 | 0.924 | 0.303 | 0.159 |
| chronos2_top | 0.924 (0.905 to 0.941) | 0.881 | 0.925 | 0.305 | 0.156 |
| median_s2_all | 0.935 (0.922 to 0.947) | 0.894 | 0.935 | 0.291 | 0.108 |
| median_s2_demand | 0.944 (0.931 to 0.955) | 0.909 | 0.941 | 0.274 | 0.104 |
| median_s2_behavior | 0.944 (0.931 to 0.956) | 0.913 | 0.943 | 0.277 | 0.107 |
| chronos | 0.945 (0.926 to 0.962) | 0.919 | 0.942 | 0.272 | 0.152 |
| catchg_D | 0.952 (0.938 to 0.964) | 0.919 | 0.949 | 0.261 | 0.099 |
| catchg_DVnli | 0.952 (0.938 to 0.965) | 0.917 | 0.950 | 0.260 | 0.099 |
| lgbmchg_D | 0.954 (0.938 to 0.969) | 0.913 | 0.950 | 0.270 | 0.105 |
| catchg_DW | 0.954 (0.940 to 0.966) | 0.923 | 0.952 | 0.259 | 0.103 |
| catchg_DVtop | 0.954 (0.940 to 0.967) | 0.925 | 0.954 | 0.260 | 0.104 |
| catchg_DVbk | 0.954 (0.940 to 0.966) | 0.925 | 0.954 | 0.262 | 0.077 |
| catchg_DVcur | 0.955 (0.940 to 0.967) | 0.924 | 0.953 | 0.258 | 0.099 |
| catchg_DWS | 0.955 (0.941 to 0.966) | 0.925 | 0.954 | 0.258 | 0.101 |
| catchg_DVcurdw | 0.955 (0.942 to 0.966) | 0.923 | 0.953 | 0.259 | 0.103 |
| lgbmchg_DW | 0.956 (0.941 to 0.969) | 0.917 | 0.953 | 0.263 | 0.107 |
| catchg_DVdem | 0.956 (0.943 to 0.968) | 0.926 | 0.954 | 0.257 | 0.086 |
| lgbmchg_DWS | 0.956 (0.941 to 0.970) | 0.917 | 0.954 | 0.261 | 0.102 |
| lgbmchg_DVbk | 0.957 (0.942 to 0.970) | 0.922 | 0.954 | 0.264 | 0.100 |
| lgbmchg_DVcur | 0.958 (0.942 to 0.971) | 0.919 | 0.955 | 0.260 | 0.104 |
| lgbmchg_DVcurdw | 0.960 (0.947 to 0.972) | 0.921 | 0.959 | 0.260 | 0.099 |
| lgbmchg_DVnli | 0.961 (0.945 to 0.975) | 0.922 | 0.957 | 0.256 | 0.097 |
| lgbmchg_DVtop | 0.961 (0.946 to 0.974) | 0.925 | 0.957 | 0.254 | 0.100 |
| median_all | 0.963 (0.950 to 0.974) | 0.954 | 0.958 | 0.251 | 0.096 |
| lgbmchg_DVdem | 0.969 (0.954 to 0.983) | 0.932 | 0.964 | 0.253 | 0.095 |
| invmae_all | 0.971 (0.958 to 0.983) | 0.965 | 0.967 | 0.257 | 0.080 |
| lightgbm_D | 0.972 (0.955 to 0.986) | 0.969 | 0.966 | 0.258 | 0.099 |
| lightgbm_DW | 0.979 (0.961 to 0.995) | 0.980 | 0.974 | 0.251 | 0.103 |
| avg_three_DW | 0.982 (0.970 to 0.994) | 1.006 | 0.982 | 0.242 | 0.091 |
| avg_naive_ridge_D | 0.983 (0.980 to 0.986) | 0.985 | 0.981 | 0.200 | 0.015 |
| ridgechg_DVdem | 0.989 (0.984 to 0.995) | 0.993 | 0.984 | 0.203 | 0.015 |
| ridgechg_D | 0.989 (0.984 to 0.995) | 0.993 | 0.984 | 0.201 | 0.015 |
| ridgechg_DVnli | 0.990 (0.985 to 0.996) | 0.993 | 0.985 | 0.199 | 0.015 |
| ridgechg_DWS | 0.991 (0.985 to 0.997) | 0.996 | 0.986 | 0.202 | 0.031 |
| ridgechg_DVtop | 0.991 (0.985 to 0.996) | 0.996 | 0.985 | 0.193 | 0.015 |
| ridgechg_DVcur | 0.991 (0.985 to 0.997) | 0.995 | 0.986 | 0.203 | 0.037 |
| ridgechg_DW | 0.991 (0.985 to 0.997) | 0.995 | 0.986 | 0.204 | 0.033 |
| ridgechg_DVbk | 0.991 (0.986 to 0.997) | 0.997 | 0.986 | 0.199 | 0.015 |
| ridgechg_DVcurdw | 0.995 (0.988 to 1.001) | 1.003 | 0.993 | 0.201 | 0.026 |
| ridge_D | 0.997 (0.990 to 1.004) | 1.003 | 0.989 | 0.200 | 0.015 |
| ridge_DW | 0.999 (0.992 to 1.006) | 1.007 | 0.992 | 0.205 | 0.029 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| avg_ridge_cat_DW | 1.004 (0.992 to 1.015) | 1.053 | 1.006 | 0.213 | 0.058 |
| avg_ridge_cat_D | 1.007 (0.995 to 1.019) | 1.059 | 1.008 | 0.210 | 0.045 |
| catboost_DW | 1.044 (1.024 to 1.062) | 1.155 | 1.052 | 0.204 | 0.072 |
| catboost_D | 1.049 (1.028 to 1.069) | 1.167 | 1.057 | 0.201 | 0.075 |
| revert6 | 1.310 (1.287 to 1.336) | 1.357 | 1.266 | 0.144 | 0.007 |
| seasonal_naive | 2.093 (2.020 to 2.170) | 1.968 | 1.998 | 0.167 | 0.016 |


### h1 after short rise (292 series, 1217 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_bk | 0.880 (0.821 to 0.938) | 0.836 | 0.878 | 0.449 | 0.284 |
| chronos2_cur | 0.886 (0.826 to 0.944) | 0.855 | 0.883 | 0.523 | 0.279 |
| chronos2_nli | 0.887 (0.827 to 0.948) | 0.861 | 0.886 | 0.482 | 0.263 |
| chronos | 0.892 (0.837 to 0.952) | 0.880 | 0.893 | 0.462 | 0.199 |
| chronos2_curdw | 0.894 (0.841 to 0.948) | 0.844 | 0.894 | 0.412 | 0.283 |
| chronos2_top | 0.896 (0.841 to 0.952) | 0.841 | 0.896 | 0.439 | 0.288 |
| chronos2 | 0.905 (0.854 to 0.955) | 0.862 | 0.902 | 0.461 | 0.268 |
| median_s2_all | 0.933 (0.896 to 0.971) | 0.884 | 0.932 | 0.465 | 0.231 |
| median_s2_behavior | 0.944 (0.895 to 0.993) | 0.925 | 0.937 | 0.422 | 0.166 |
| catchg_DVtop | 0.954 (0.912 to 0.999) | 0.937 | 0.952 | 0.499 | 0.182 |
| median_s2_demand | 0.955 (0.913 to 0.998) | 0.944 | 0.946 | 0.396 | 0.257 |
| catchg_DVnli | 0.963 (0.922 to 1.008) | 0.955 | 0.963 | 0.467 | 0.207 |
| catchg_DVbk | 0.964 (0.920 to 1.009) | 0.963 | 0.959 | 0.446 | 0.204 |
| lgbmchg_DVtop | 0.966 (0.925 to 1.010) | 0.930 | 0.964 | 0.402 | 0.220 |
| median_all | 0.967 (0.923 to 1.013) | 0.990 | 0.958 | 0.362 | 0.214 |
| catchg_D | 0.967 (0.927 to 1.014) | 0.948 | 0.966 | 0.455 | 0.212 |
| catchg_DWS | 0.970 (0.923 to 1.019) | 0.989 | 0.965 | 0.422 | 0.168 |
| catchg_DVdem | 0.972 (0.929 to 1.018) | 0.970 | 0.969 | 0.435 | 0.217 |
| lightgbm_D | 0.976 (0.922 to 1.036) | 0.994 | 0.969 | 0.377 | 0.235 |
| catchg_DVcurdw | 0.977 (0.933 to 1.024) | 0.962 | 0.978 | 0.398 | 0.178 |
| invmae_all | 0.978 (0.922 to 1.035) | 1.000 | 0.968 | 0.389 | 0.215 |
| catchg_DVcur | 0.984 (0.935 to 1.039) | 0.984 | 0.984 | 0.426 | 0.172 |
| catchg_DW | 0.988 (0.943 to 1.040) | 0.994 | 0.985 | 0.383 | 0.164 |
| lgbmchg_D | 0.989 (0.950 to 1.032) | 0.944 | 0.988 | 0.404 | 0.270 |
| lgbmchg_DVbk | 0.990 (0.948 to 1.036) | 0.982 | 0.985 | 0.405 | 0.255 |
| avg_naive_ridge_D | 0.993 (0.971 to 1.016) | 0.994 | 0.988 | 0.246 | 0.045 |
| ridgechg_DW | 0.997 (0.944 to 1.055) | 1.038 | 0.991 | 0.198 | 0.052 |
| avg_ridge_cat_D | 0.997 (0.941 to 1.054) | 1.048 | 0.990 | 0.249 | 0.127 |
| ridgechg_DVtop | 0.999 (0.965 to 1.036) | 1.014 | 0.993 | 0.253 | 0.054 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| ridgechg_DWS | 1.001 (0.950 to 1.058) | 1.040 | 0.994 | 0.205 | 0.047 |
| lgbmchg_DVdem | 1.003 (0.957 to 1.051) | 0.978 | 1.000 | 0.337 | 0.323 |
| catboost_D | 1.005 (0.945 to 1.069) | 1.069 | 0.999 | 0.264 | 0.149 |
| lgbmchg_DVnli | 1.005 (0.959 to 1.056) | 0.951 | 0.996 | 0.363 | 0.207 |
| ridgechg_D | 1.010 (0.977 to 1.047) | 1.024 | 1.003 | 0.261 | 0.054 |
| ridgechg_DVdem | 1.013 (0.980 to 1.049) | 1.026 | 1.006 | 0.275 | 0.056 |
| ridge_DW | 1.014 (0.957 to 1.079) | 1.068 | 1.008 | 0.188 | 0.046 |
| ridgechg_DVnli | 1.015 (0.982 to 1.053) | 1.027 | 1.009 | 0.248 | 0.053 |
| avg_three_DW | 1.017 (0.965 to 1.076) | 1.018 | 1.007 | 0.335 | 0.176 |
| avg_ridge_cat_DW | 1.020 (0.964 to 1.083) | 1.050 | 1.011 | 0.248 | 0.130 |
| ridgechg_DVbk | 1.020 (0.985 to 1.058) | 1.027 | 1.009 | 0.276 | 0.059 |
| ridge_D | 1.027 (0.990 to 1.068) | 1.047 | 1.017 | 0.246 | 0.045 |
| ridgechg_DVcurdw | 1.028 (0.979 to 1.085) | 1.080 | 1.018 | 0.189 | 0.051 |
| lgbmchg_DVcur | 1.042 (0.995 to 1.093) | 1.045 | 1.045 | 0.349 | 0.189 |
| lgbmchg_DVcurdw | 1.051 (1.002 to 1.106) | 1.035 | 1.049 | 0.351 | 0.197 |
| ridgechg_DVcur | 1.052 (1.009 to 1.103) | 1.081 | 1.042 | 0.207 | 0.046 |
| lgbmchg_DW | 1.063 (1.006 to 1.125) | 1.089 | 1.064 | 0.379 | 0.189 |
| lightgbm_DW | 1.064 (0.991 to 1.141) | 1.075 | 1.057 | 0.336 | 0.183 |
| lgbmchg_DWS | 1.065 (1.015 to 1.123) | 1.072 | 1.067 | 0.344 | 0.186 |
| catboost_DW | 1.072 (1.008 to 1.140) | 1.117 | 1.063 | 0.268 | 0.152 |
| revert6 | 1.304 (1.196 to 1.419) | 1.300 | 1.278 | 0.033 | 0.014 |
| seasonal_naive | 1.977 (1.761 to 2.226) | 1.848 | 1.942 | 0.289 | 0.122 |


### h1 after lasting rise (73 series, 143 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| median_s2_all | 0.749 (0.572 to 0.935) | 0.684 | 0.763 | 0.482 | 0.793 |
| chronos2_curdw | 0.768 (0.541 to 1.030) | 0.655 | 0.774 | 0.709 | 0.916 |
| catchg_D | 0.816 (0.662 to 0.988) | 0.778 | 0.825 | 0.409 | 0.781 |
| catchg_DVbk | 0.819 (0.657 to 1.004) | 0.655 | 0.828 | 0.345 | 0.789 |
| chronos2_cur | 0.829 (0.590 to 1.120) | 0.978 | 0.835 | 0.718 | 0.919 |
| chronos | 0.833 (0.627 to 1.086) | 0.764 | 0.838 | 0.709 | 0.888 |
| chronos2_nli | 0.833 (0.628 to 1.089) | 0.896 | 0.842 | 0.664 | 0.908 |
| catchg_DVtop | 0.837 (0.692 to 1.039) | 1.004 | 0.864 | 0.418 | 0.816 |
| chronos2_bk | 0.840 (0.651 to 1.073) | 0.762 | 0.844 | 0.627 | 0.899 |
| catchg_DVnli | 0.850 (0.665 to 1.063) | 1.047 | 0.858 | 0.382 | 0.768 |
| catchg_DWS | 0.851 (0.669 to 1.085) | 1.028 | 0.868 | 0.236 | 0.731 |
| catchg_DVcur | 0.855 (0.675 to 1.072) | 1.106 | 0.859 | 0.318 | 0.672 |
| catchg_DVdem | 0.857 (0.719 to 1.010) | 0.807 | 0.871 | 0.409 | 0.800 |
| median_s2_demand | 0.858 (0.713 to 1.016) | 0.824 | 0.882 | 0.673 | 0.713 |
| chronos2_top | 0.900 (0.686 to 1.152) | 0.956 | 0.903 | 0.736 | 0.905 |
| chronos2 | 0.904 (0.685 to 1.164) | 1.049 | 0.912 | 0.727 | 0.886 |
| catchg_DVcurdw | 0.915 (0.729 to 1.153) | 1.210 | 0.921 | 0.264 | 0.725 |
| lgbmchg_D | 0.916 (0.699 to 1.179) | 0.958 | 0.950 | 0.664 | 0.714 |
| lgbmchg_DVtop | 0.925 (0.750 to 1.130) | 1.013 | 0.946 | 0.591 | 0.740 |
| median_s2_behavior | 0.932 (0.741 to 1.158) | 1.187 | 0.944 | 0.773 | 0.787 |
| catchg_DW | 0.937 (0.738 to 1.174) | 1.306 | 0.946 | 0.436 | 0.605 |
| invmae_all | 0.938 (0.742 to 1.182) | 1.253 | 0.944 | 0.318 | 0.702 |
| avg_ridge_cat_D | 0.947 (0.757 to 1.191) | 1.356 | 0.964 | 0.036 | 0.683 |
| ridgechg_DVdem | 0.960 (0.829 to 1.129) | 1.072 | 0.981 | 0.445 | 0.326 |
| lgbmchg_DVbk | 0.965 (0.742 to 1.222) | 1.087 | 0.982 | 0.755 | 0.633 |
| ridgechg_DVnli | 0.965 (0.836 to 1.107) | 1.027 | 0.983 | 0.409 | 0.304 |
| ridgechg_DVbk | 0.969 (0.826 to 1.145) | 1.144 | 0.986 | 0.536 | 0.319 |
| ridgechg_D | 0.981 (0.843 to 1.146) | 1.144 | 1.001 | 0.482 | 0.315 |
| ridgechg_DVtop | 0.984 (0.829 to 1.170) | 1.252 | 1.002 | 0.409 | 0.358 |
| median_all | 0.993 (0.812 to 1.213) | 1.099 | 1.011 | 0.497 | 0.679 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| avg_naive_ridge_D | 1.004 (0.875 to 1.155) | 1.066 | 1.009 | 0.082 | 0.235 |
| ridgechg_DVcurdw | 1.010 (0.808 to 1.289) | 1.423 | 1.008 | 0.455 | 0.638 |
| lgbmchg_DVnli | 1.021 (0.801 to 1.287) | 1.149 | 1.042 | 0.655 | 0.739 |
| catboost_D | 1.021 (0.740 to 1.384) | 1.402 | 1.056 | -0.136 | 0.696 |
| lightgbm_D | 1.035 (0.771 to 1.372) | 1.279 | 1.057 | 0.345 | 0.620 |
| lgbmchg_DWS | 1.039 (0.685 to 1.465) | 1.326 | 1.061 | 0.291 | 0.691 |
| ridgechg_DVcur | 1.059 (0.875 to 1.302) | 1.470 | 1.076 | 0.336 | 0.644 |
| lgbmchg_DVdem | 1.063 (0.806 to 1.438) | 1.463 | 1.091 | 0.664 | 0.712 |
| lightgbm_DW | 1.069 (0.789 to 1.439) | 1.085 | 1.084 | 0.227 | 0.632 |
| ridge_D | 1.086 (0.910 to 1.304) | 1.212 | 1.112 | 0.082 | 0.235 |
| avg_three_DW | 1.112 (0.870 to 1.430) | 1.634 | 1.128 | 0.273 | 0.670 |
| lgbmchg_DVcur | 1.114 (0.864 to 1.415) | 1.356 | 1.117 | 0.455 | 0.603 |
| lgbmchg_DVcurdw | 1.169 (0.892 to 1.522) | 1.610 | 1.194 | 0.364 | 0.694 |
| avg_ridge_cat_DW | 1.178 (0.872 to 1.626) | 1.733 | 1.207 | -0.009 | 0.693 |
| lgbmchg_DW | 1.214 (0.964 to 1.516) | 1.647 | 1.233 | 0.355 | 0.612 |
| catboost_DW | 1.381 (1.038 to 1.855) | 2.091 | 1.408 | 0.164 | 0.733 |
| ridgechg_DW | 1.542 (1.201 to 2.053) | 2.709 | 1.547 | 0.382 | 0.646 |
| ridge_DW | 1.633 (1.246 to 2.201) | 2.711 | 1.644 | 0.027 | 0.457 |
| ridgechg_DWS | 1.751 (1.333 to 2.392) | 3.246 | 1.728 | 0.455 | 0.644 |
| seasonal_naive | 1.951 (1.378 to 2.789) | 2.183 | 1.937 | 0.518 | 0.697 |


### h1 surge months (outcome-defined) (139 series, 238 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| seasonal_naive | 0.731 (0.635 to 0.832) | 0.678 | 0.756 |  |  |
| chronos2_bk | 0.838 (0.749 to 0.915) | 0.759 | 0.847 |  |  |
| chronos2_nli | 0.839 (0.749 to 0.918) | 0.754 | 0.848 |  |  |
| chronos2_top | 0.839 (0.749 to 0.917) | 0.756 | 0.848 |  |  |
| chronos2 | 0.841 (0.749 to 0.922) | 0.754 | 0.851 |  |  |
| chronos2_curdw | 0.842 (0.752 to 0.920) | 0.757 | 0.851 |  |  |
| chronos2_cur | 0.842 (0.751 to 0.922) | 0.756 | 0.851 |  |  |
| chronos | 0.866 (0.783 to 0.937) | 0.782 | 0.875 |  |  |
| lgbmchg_D | 0.893 (0.822 to 0.950) | 0.820 | 0.902 |  |  |
| lgbmchg_DVdem | 0.900 (0.840 to 0.948) | 0.837 | 0.906 |  |  |
| lgbmchg_DVtop | 0.901 (0.838 to 0.952) | 0.833 | 0.906 |  |  |
| lightgbm_DW | 0.903 (0.830 to 0.959) | 0.843 | 0.909 |  |  |
| lgbmchg_DVbk | 0.903 (0.841 to 0.953) | 0.841 | 0.907 |  |  |
| lgbmchg_DVnli | 0.904 (0.837 to 0.958) | 0.835 | 0.911 |  |  |
| lightgbm_D | 0.905 (0.840 to 0.956) | 0.847 | 0.910 |  |  |
| lgbmchg_DW | 0.911 (0.844 to 0.961) | 0.858 | 0.918 |  |  |
| lgbmchg_DVcurdw | 0.913 (0.850 to 0.961) | 0.857 | 0.918 |  |  |
| lgbmchg_DVcur | 0.913 (0.845 to 0.963) | 0.856 | 0.919 |  |  |
| lgbmchg_DWS | 0.913 (0.850 to 0.960) | 0.865 | 0.919 |  |  |
| catboost_DW | 0.913 (0.856 to 0.960) | 0.883 | 0.920 |  |  |
| catchg_DWS | 0.919 (0.861 to 0.964) | 0.883 | 0.925 |  |  |
| catboost_D | 0.920 (0.868 to 0.962) | 0.881 | 0.925 |  |  |
| catchg_DW | 0.920 (0.862 to 0.965) | 0.886 | 0.925 |  |  |
| catchg_DVcur | 0.921 (0.863 to 0.965) | 0.883 | 0.927 |  |  |
| invmae_all | 0.922 (0.883 to 0.955) | 0.901 | 0.924 |  |  |
| catchg_DVcurdw | 0.922 (0.864 to 0.967) | 0.884 | 0.926 |  |  |
| catchg_DVbk | 0.923 (0.868 to 0.965) | 0.880 | 0.926 |  |  |
| median_s2_demand | 0.924 (0.869 to 0.965) | 0.878 | 0.927 |  |  |
| catchg_D | 0.924 (0.870 to 0.965) | 0.881 | 0.926 |  |  |
| median_s2_behavior | 0.924 (0.865 to 0.969) | 0.880 | 0.929 |  |  |
| median_s2_all | 0.925 (0.867 to 0.968) | 0.877 | 0.928 |  |  |
| median_all | 0.925 (0.874 to 0.966) | 0.885 | 0.929 |  |  |
| catchg_DVnli | 0.927 (0.877 to 0.965) | 0.889 | 0.928 |  |  |
| catchg_DVtop | 0.927 (0.875 to 0.966) | 0.887 | 0.931 |  |  |
| catchg_DVdem | 0.928 (0.883 to 0.963) | 0.893 | 0.931 |  |  |
| avg_three_DW | 0.930 (0.885 to 0.965) | 0.907 | 0.933 |  |  |
| avg_ridge_cat_DW | 0.940 (0.907 to 0.969) | 0.932 | 0.943 |  |  |
| avg_ridge_cat_D | 0.950 (0.925 to 0.971) | 0.945 | 0.951 |  |  |
| ridge_DW | 0.961 (0.942 to 0.979) | 0.967 | 0.962 |  |  |
| ridgechg_DWS | 0.965 (0.947 to 0.981) | 0.968 | 0.966 |  |  |
| ridgechg_DW | 0.966 (0.949 to 0.981) | 0.969 | 0.967 |  |  |
| ridgechg_DVcur | 0.967 (0.952 to 0.982) | 0.970 | 0.969 |  |  |
| ridgechg_DVcurdw | 0.969 (0.955 to 0.983) | 0.971 | 0.971 |  |  |
| ridge_D | 0.969 (0.954 to 0.985) | 0.981 | 0.970 |  |  |
| ridgechg_DVbk | 0.973 (0.960 to 0.986) | 0.982 | 0.973 |  |  |
| ridgechg_DVdem | 0.974 (0.961 to 0.986) | 0.982 | 0.974 |  |  |
| ridgechg_DVtop | 0.974 (0.962 to 0.986) | 0.982 | 0.974 |  |  |
| ridgechg_D | 0.974 (0.962 to 0.986) | 0.983 | 0.974 |  |  |
| ridgechg_DVnli | 0.975 (0.962 to 0.987) | 0.983 | 0.975 |  |  |
| revert6 | 0.978 (0.934 to 1.024) | 1.038 | 0.987 |  |  |
| avg_naive_ridge_D | 0.986 (0.978 to 0.993) | 0.991 | 0.986 |  |  |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |


### h2 quiet (519 series, 33567 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.881 (0.857 to 0.903) | 0.819 | 0.888 | 0.351 | 0.271 |
| chronos2_bk | 0.883 (0.859 to 0.905) | 0.818 | 0.887 | 0.355 | 0.269 |
| chronos2_nli | 0.883 (0.859 to 0.905) | 0.820 | 0.888 | 0.351 | 0.264 |
| chronos2_curdw | 0.884 (0.861 to 0.907) | 0.822 | 0.890 | 0.348 | 0.268 |
| chronos2_top | 0.886 (0.863 to 0.908) | 0.823 | 0.892 | 0.340 | 0.263 |
| chronos2 | 0.888 (0.864 to 0.910) | 0.825 | 0.893 | 0.342 | 0.263 |
| median_s2_all | 0.899 (0.880 to 0.916) | 0.839 | 0.901 | 0.342 | 0.227 |
| chronos | 0.906 (0.882 to 0.928) | 0.857 | 0.909 | 0.323 | 0.258 |
| median_s2_demand | 0.919 (0.902 to 0.935) | 0.873 | 0.917 | 0.312 | 0.200 |
| lgbmchg_D | 0.929 (0.910 to 0.948) | 0.874 | 0.927 | 0.311 | 0.191 |
| catchg_D | 0.930 (0.912 to 0.947) | 0.890 | 0.930 | 0.305 | 0.183 |
| catchg_DWS | 0.933 (0.915 to 0.950) | 0.888 | 0.933 | 0.304 | 0.175 |
| catchg_DW | 0.934 (0.915 to 0.950) | 0.890 | 0.933 | 0.303 | 0.179 |
| catchg_DVnli | 0.935 (0.915 to 0.953) | 0.893 | 0.934 | 0.301 | 0.182 |
| catchg_DVdem | 0.938 (0.919 to 0.955) | 0.895 | 0.936 | 0.301 | 0.193 |
| median_all | 0.939 (0.922 to 0.955) | 0.908 | 0.933 | 0.289 | 0.173 |
| invmae_all | 0.943 (0.927 to 0.959) | 0.928 | 0.943 | 0.296 | 0.176 |
| lightgbm_D | 0.954 (0.933 to 0.974) | 0.931 | 0.949 | 0.292 | 0.172 |
| avg_three_DW | 0.964 (0.948 to 0.980) | 0.972 | 0.965 | 0.277 | 0.143 |
| lightgbm_DW | 0.966 (0.943 to 0.986) | 0.938 | 0.960 | 0.281 | 0.161 |
| avg_naive_ridge_D | 0.971 (0.966 to 0.976) | 0.976 | 0.969 | 0.242 | 0.054 |
| ridgechg_D | 0.977 (0.969 to 0.986) | 0.979 | 0.969 | 0.245 | 0.058 |
| ridgechg_DWS | 0.978 (0.969 to 0.987) | 0.979 | 0.970 | 0.239 | 0.056 |
| ridgechg_DW | 0.978 (0.970 to 0.988) | 0.978 | 0.970 | 0.241 | 0.057 |
| avg_ridge_cat_DW | 0.986 (0.971 to 1.000) | 1.025 | 0.990 | 0.258 | 0.111 |
| avg_ridge_cat_D | 0.988 (0.973 to 1.002) | 1.039 | 0.998 | 0.261 | 0.124 |
| ridge_D | 0.989 (0.979 to 1.000) | 0.998 | 0.979 | 0.242 | 0.054 |
| ridge_DW | 0.989 (0.979 to 1.000) | 0.995 | 0.979 | 0.239 | 0.053 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| catboost_DW | 1.023 (1.000 to 1.044) | 1.134 | 1.047 | 0.252 | 0.143 |
| catboost_D | 1.028 (1.002 to 1.051) | 1.160 | 1.069 | 0.257 | 0.150 |
| revert6 | 1.145 (1.128 to 1.163) | 1.151 | 1.114 | 0.155 | 0.024 |
| seasonal_naive | 1.744 (1.678 to 1.811) | 1.601 | 1.683 | 0.196 | 0.054 |


### h2 after short rise (293 series, 1180 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_nli | 0.848 (0.782 to 0.915) | 0.787 | 0.855 | 0.473 | 0.732 |
| chronos2_top | 0.851 (0.783 to 0.919) | 0.794 | 0.854 | 0.469 | 0.735 |
| median_s2_all | 0.856 (0.808 to 0.904) | 0.791 | 0.851 | 0.414 | 0.718 |
| chronos2_curdw | 0.864 (0.806 to 0.927) | 0.816 | 0.864 | 0.438 | 0.729 |
| chronos2_cur | 0.865 (0.805 to 0.929) | 0.823 | 0.866 | 0.522 | 0.733 |
| chronos2_bk | 0.870 (0.806 to 0.936) | 0.820 | 0.867 | 0.485 | 0.725 |
| chronos2 | 0.874 (0.813 to 0.938) | 0.831 | 0.873 | 0.476 | 0.730 |
| median_all | 0.876 (0.815 to 0.937) | 0.838 | 0.874 | 0.344 | 0.652 |
| chronos | 0.881 (0.820 to 0.943) | 0.820 | 0.880 | 0.470 | 0.704 |
| invmae_all | 0.886 (0.825 to 0.944) | 0.849 | 0.881 | 0.321 | 0.680 |
| catchg_D | 0.887 (0.826 to 0.951) | 0.854 | 0.885 | 0.359 | 0.672 |
| catchg_DVdem | 0.895 (0.836 to 0.953) | 0.861 | 0.895 | 0.371 | 0.652 |
| median_s2_demand | 0.897 (0.845 to 0.949) | 0.847 | 0.887 | 0.323 | 0.671 |
| catchg_DWS | 0.903 (0.843 to 0.964) | 0.892 | 0.903 | 0.355 | 0.699 |
| catchg_DVnli | 0.909 (0.850 to 0.968) | 0.870 | 0.913 | 0.305 | 0.672 |
| lightgbm_D | 0.922 (0.852 to 0.992) | 0.914 | 0.910 | 0.330 | 0.645 |
| catchg_DW | 0.923 (0.860 to 0.984) | 0.926 | 0.921 | 0.342 | 0.695 |
| lgbmchg_D | 0.925 (0.864 to 0.988) | 0.864 | 0.911 | 0.293 | 0.682 |
| avg_three_DW | 0.939 (0.884 to 0.996) | 0.940 | 0.931 | 0.333 | 0.644 |
| avg_ridge_cat_DW | 0.943 (0.894 to 0.996) | 0.962 | 0.942 | 0.303 | 0.586 |
| avg_naive_ridge_D | 0.952 (0.927 to 0.978) | 0.954 | 0.952 | 0.296 | 0.159 |
| catboost_D | 0.955 (0.886 to 1.021) | 0.929 | 0.951 | 0.245 | 0.553 |
| avg_ridge_cat_D | 0.957 (0.903 to 1.010) | 0.966 | 0.952 | 0.241 | 0.557 |
| catboost_DW | 0.975 (0.915 to 1.037) | 0.995 | 0.974 | 0.348 | 0.618 |
| lightgbm_DW | 0.982 (0.896 to 1.067) | 0.946 | 0.958 | 0.347 | 0.632 |
| ridgechg_D | 0.983 (0.941 to 1.024) | 0.994 | 0.975 | 0.302 | 0.190 |
| ridge_D | 0.989 (0.944 to 1.036) | 1.004 | 0.979 | 0.296 | 0.159 |
| ridgechg_DW | 0.992 (0.943 to 1.046) | 1.018 | 0.986 | 0.215 | 0.303 |
| ridgechg_DWS | 0.995 (0.946 to 1.047) | 1.016 | 0.987 | 0.212 | 0.280 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| ridge_DW | 1.008 (0.956 to 1.062) | 1.044 | 1.000 | 0.226 | 0.246 |
| revert6 | 1.168 (1.084 to 1.260) | 1.135 | 1.146 | 0.057 | 0.019 |
| seasonal_naive | 1.619 (1.446 to 1.807) | 1.501 | 1.594 | 0.282 | 0.416 |


### h2 after lasting rise (71 series, 138 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| catchg_DVnli | 0.666 (0.492 to 0.870) | 0.490 | 0.681 | 0.409 | 0.979 |
| chronos2 | 0.722 (0.541 to 0.951) | 0.703 | 0.736 | 0.809 | 0.988 |
| chronos2_nli | 0.727 (0.566 to 0.930) | 0.611 | 0.744 | 0.655 | 0.989 |
| chronos2_top | 0.731 (0.554 to 0.956) | 0.517 | 0.750 | 0.827 | 0.988 |
| chronos2_cur | 0.734 (0.536 to 0.984) | 0.527 | 0.745 | 0.709 | 0.988 |
| chronos2_bk | 0.737 (0.570 to 0.922) | 0.466 | 0.754 | 0.700 | 0.987 |
| median_s2_all | 0.750 (0.592 to 0.925) | 0.699 | 0.762 | 0.791 | 0.986 |
| chronos2_curdw | 0.771 (0.597 to 0.983) | 0.608 | 0.784 | 0.664 | 0.988 |
| chronos | 0.775 (0.601 to 0.993) | 0.748 | 0.797 | 0.745 | 0.978 |
| median_s2_demand | 0.777 (0.602 to 0.979) | 0.918 | 0.801 | 0.755 | 0.959 |
| catchg_D | 0.797 (0.652 to 0.954) | 0.687 | 0.815 | 0.482 | 0.979 |
| catchg_DVdem | 0.799 (0.668 to 0.934) | 0.739 | 0.818 | 0.355 | 0.978 |
| avg_ridge_cat_D | 0.850 (0.616 to 1.145) | 1.116 | 0.866 | 0.491 | 0.910 |
| catchg_DWS | 0.875 (0.696 to 1.091) | 0.898 | 0.888 | 0.527 | 0.990 |
| catchg_DW | 0.882 (0.714 to 1.101) | 0.925 | 0.899 | 0.600 | 0.983 |
| ridgechg_D | 0.980 (0.834 to 1.173) | 1.303 | 0.985 | 0.645 | 0.739 |
| invmae_all | 0.984 (0.740 to 1.289) | 1.126 | 0.994 | 0.709 | 0.955 |
| median_all | 0.999 (0.790 to 1.261) | 1.109 | 1.026 | 0.673 | 0.958 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| lightgbm_D | 1.009 (0.737 to 1.352) | 0.959 | 1.034 | 0.491 | 0.852 |
| lgbmchg_D | 1.016 (0.823 to 1.242) | 0.943 | 1.052 | 0.873 | 0.962 |
| catboost_DW | 1.041 (0.813 to 1.339) | 1.217 | 1.069 | 0.091 | 0.917 |
| catboost_D | 1.041 (0.788 to 1.353) | 1.301 | 1.080 | 0.400 | 0.916 |
| avg_three_DW | 1.048 (0.767 to 1.399) | 1.252 | 1.058 | 0.555 | 0.942 |
| avg_naive_ridge_D | 1.051 (0.915 to 1.243) | 1.262 | 1.053 | 0.409 | 0.593 |
| ridge_D | 1.120 (0.902 to 1.410) | 1.376 | 1.133 | 0.409 | 0.593 |
| lightgbm_DW | 1.128 (0.831 to 1.549) | 0.993 | 1.157 | 0.400 | 0.896 |
| avg_ridge_cat_DW | 1.177 (0.873 to 1.589) | 1.605 | 1.183 | 0.255 | 0.920 |
| seasonal_naive | 1.481 (1.075 to 2.047) | 1.219 | 1.497 | 0.500 | 0.922 |
| ridgechg_DW | 1.611 (1.182 to 2.228) | 2.667 | 1.616 | 0.691 | 0.698 |
| ridge_DW | 1.636 (1.182 to 2.291) | 2.557 | 1.632 | 0.491 | 0.562 |
| ridgechg_DWS | 1.763 (1.276 to 2.491) | 3.085 | 1.770 | 0.691 | 0.685 |


### h2 surge months (outcome-defined) (199 series, 531 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| seasonal_naive | 0.684 (0.608 to 0.768) | 0.612 | 0.712 |  |  |
| chronos2_bk | 0.797 (0.732 to 0.859) | 0.714 | 0.812 |  |  |
| chronos2_curdw | 0.802 (0.736 to 0.865) | 0.716 | 0.818 |  |  |
| chronos2_nli | 0.803 (0.737 to 0.867) | 0.714 | 0.819 |  |  |
| chronos2_top | 0.804 (0.737 to 0.868) | 0.716 | 0.820 |  |  |
| chronos2_cur | 0.804 (0.739 to 0.867) | 0.715 | 0.820 |  |  |
| chronos2 | 0.812 (0.746 to 0.876) | 0.722 | 0.828 |  |  |
| chronos | 0.813 (0.740 to 0.881) | 0.706 | 0.827 |  |  |
| lightgbm_DW | 0.838 (0.784 to 0.885) | 0.765 | 0.849 |  |  |
| lgbmchg_D | 0.843 (0.792 to 0.888) | 0.766 | 0.853 |  |  |
| lightgbm_D | 0.846 (0.797 to 0.888) | 0.786 | 0.857 |  |  |
| catboost_D | 0.852 (0.803 to 0.896) | 0.787 | 0.861 |  |  |
| catboost_DW | 0.857 (0.812 to 0.898) | 0.790 | 0.866 |  |  |
| catchg_DVdem | 0.868 (0.822 to 0.907) | 0.814 | 0.875 |  |  |
| catchg_D | 0.869 (0.820 to 0.909) | 0.805 | 0.876 |  |  |
| median_all | 0.870 (0.825 to 0.909) | 0.808 | 0.879 |  |  |
| catchg_DVnli | 0.871 (0.821 to 0.912) | 0.807 | 0.879 |  |  |
| median_s2_demand | 0.871 (0.825 to 0.910) | 0.812 | 0.878 |  |  |
| median_s2_all | 0.872 (0.820 to 0.913) | 0.806 | 0.879 |  |  |
| invmae_all | 0.876 (0.843 to 0.907) | 0.834 | 0.882 |  |  |
| avg_three_DW | 0.879 (0.845 to 0.911) | 0.834 | 0.884 |  |  |
| catchg_DWS | 0.879 (0.838 to 0.915) | 0.826 | 0.885 |  |  |
| catchg_DW | 0.881 (0.841 to 0.914) | 0.831 | 0.886 |  |  |
| avg_ridge_cat_DW | 0.894 (0.865 to 0.921) | 0.861 | 0.899 |  |  |
| avg_ridge_cat_D | 0.896 (0.869 to 0.923) | 0.869 | 0.901 |  |  |
| revert6 | 0.922 (0.888 to 0.956) | 0.962 | 0.931 |  |  |
| ridge_DW | 0.922 (0.900 to 0.943) | 0.913 | 0.926 |  |  |
| ridge_D | 0.926 (0.903 to 0.947) | 0.918 | 0.929 |  |  |
| ridgechg_DW | 0.933 (0.914 to 0.950) | 0.926 | 0.935 |  |  |
| ridgechg_DWS | 0.933 (0.914 to 0.951) | 0.927 | 0.936 |  |  |
| ridgechg_D | 0.937 (0.918 to 0.954) | 0.930 | 0.939 |  |  |
| avg_naive_ridge_D | 0.966 (0.956 to 0.976) | 0.964 | 0.967 |  |  |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |


### h3 quiet (519 series, 32819 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_cur | 0.866 (0.839 to 0.892) | 0.785 | 0.871 | 0.370 | 0.348 |
| chronos2_bk | 0.867 (0.838 to 0.892) | 0.784 | 0.870 | 0.374 | 0.345 |
| chronos2_nli | 0.868 (0.840 to 0.894) | 0.786 | 0.872 | 0.366 | 0.342 |
| chronos2_curdw | 0.870 (0.842 to 0.895) | 0.788 | 0.874 | 0.364 | 0.346 |
| chronos2_top | 0.871 (0.843 to 0.897) | 0.789 | 0.875 | 0.356 | 0.341 |
| chronos2 | 0.874 (0.846 to 0.899) | 0.791 | 0.878 | 0.357 | 0.340 |
| median_s2_all | 0.881 (0.858 to 0.902) | 0.809 | 0.881 | 0.366 | 0.297 |
| chronos | 0.888 (0.860 to 0.914) | 0.824 | 0.890 | 0.348 | 0.324 |
| median_s2_demand | 0.902 (0.880 to 0.922) | 0.847 | 0.898 | 0.341 | 0.267 |
| lgbmchg_D | 0.913 (0.888 to 0.936) | 0.843 | 0.909 | 0.337 | 0.257 |
| catchg_D | 0.915 (0.892 to 0.936) | 0.866 | 0.913 | 0.332 | 0.245 |
| catchg_DWS | 0.915 (0.892 to 0.937) | 0.862 | 0.914 | 0.329 | 0.246 |
| catchg_DVnli | 0.918 (0.894 to 0.941) | 0.863 | 0.917 | 0.326 | 0.247 |
| catchg_DW | 0.919 (0.895 to 0.940) | 0.864 | 0.917 | 0.331 | 0.244 |
| median_all | 0.920 (0.898 to 0.941) | 0.880 | 0.914 | 0.320 | 0.243 |
| catchg_DVdem | 0.923 (0.900 to 0.945) | 0.871 | 0.920 | 0.327 | 0.244 |
| invmae_all | 0.925 (0.906 to 0.943) | 0.890 | 0.921 | 0.322 | 0.251 |
| lightgbm_D | 0.931 (0.905 to 0.955) | 0.897 | 0.923 | 0.321 | 0.235 |
| avg_three_DW | 0.948 (0.928 to 0.967) | 0.942 | 0.946 | 0.309 | 0.211 |
| lightgbm_DW | 0.951 (0.924 to 0.974) | 0.908 | 0.943 | 0.307 | 0.216 |
| avg_ridge_cat_D | 0.964 (0.948 to 0.979) | 0.974 | 0.962 | 0.294 | 0.203 |
| avg_naive_ridge_D | 0.965 (0.960 to 0.971) | 0.972 | 0.962 | 0.279 | 0.102 |
| avg_ridge_cat_DW | 0.971 (0.955 to 0.988) | 0.998 | 0.974 | 0.291 | 0.191 |
| ridge_DW | 0.979 (0.967 to 0.992) | 0.985 | 0.970 | 0.277 | 0.110 |
| ridgechg_D | 0.980 (0.969 to 0.992) | 1.001 | 0.977 | 0.275 | 0.102 |
| ridgechg_DWS | 0.981 (0.969 to 0.992) | 1.002 | 0.977 | 0.266 | 0.104 |
| ridgechg_DW | 0.982 (0.971 to 0.994) | 1.004 | 0.979 | 0.270 | 0.105 |
| catboost_D | 0.984 (0.957 to 1.008) | 1.052 | 1.001 | 0.289 | 0.219 |
| ridge_D | 0.984 (0.972 to 0.998) | 1.000 | 0.978 | 0.279 | 0.102 |
| catboost_DW | 0.995 (0.968 to 1.020) | 1.075 | 1.020 | 0.284 | 0.204 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| revert6 | 1.070 (1.057 to 1.085) | 1.058 | 1.045 | 0.184 | 0.047 |
| seasonal_naive | 1.584 (1.521 to 1.650) | 1.450 | 1.540 | 0.212 | 0.095 |


### h3 after short rise (291 series, 1159 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| chronos2_curdw | 0.832 (0.758 to 0.910) | 0.772 | 0.836 | 0.338 | 0.705 |
| chronos2_bk | 0.839 (0.769 to 0.912) | 0.785 | 0.845 | 0.400 | 0.707 |
| chronos2_cur | 0.846 (0.774 to 0.921) | 0.794 | 0.848 | 0.422 | 0.705 |
| chronos2_top | 0.848 (0.777 to 0.923) | 0.804 | 0.852 | 0.391 | 0.704 |
| chronos2_nli | 0.849 (0.777 to 0.924) | 0.791 | 0.853 | 0.385 | 0.705 |
| chronos2 | 0.856 (0.786 to 0.930) | 0.821 | 0.861 | 0.404 | 0.702 |
| chronos | 0.860 (0.788 to 0.929) | 0.792 | 0.863 | 0.381 | 0.698 |
| median_s2_all | 0.870 (0.806 to 0.939) | 0.798 | 0.873 | 0.373 | 0.682 |
| lgbmchg_D | 0.878 (0.801 to 0.958) | 0.815 | 0.883 | 0.381 | 0.661 |
| median_s2_demand | 0.884 (0.817 to 0.957) | 0.808 | 0.889 | 0.365 | 0.668 |
| lightgbm_D | 0.885 (0.808 to 0.966) | 0.793 | 0.888 | 0.369 | 0.666 |
| median_all | 0.901 (0.835 to 0.978) | 0.832 | 0.906 | 0.338 | 0.642 |
| invmae_all | 0.904 (0.841 to 0.979) | 0.821 | 0.912 | 0.347 | 0.652 |
| catchg_D | 0.907 (0.839 to 0.984) | 0.873 | 0.917 | 0.395 | 0.669 |
| catchg_DVdem | 0.909 (0.841 to 0.987) | 0.902 | 0.913 | 0.414 | 0.646 |
| catchg_DW | 0.916 (0.842 to 0.999) | 0.950 | 0.922 | 0.369 | 0.656 |
| catchg_DVnli | 0.922 (0.858 to 0.996) | 0.907 | 0.929 | 0.368 | 0.679 |
| catchg_DWS | 0.925 (0.857 to 1.003) | 0.951 | 0.929 | 0.375 | 0.653 |
| catboost_D | 0.943 (0.868 to 1.026) | 0.899 | 0.955 | 0.421 | 0.620 |
| avg_three_DW | 0.946 (0.872 to 1.025) | 0.910 | 0.948 | 0.332 | 0.616 |
| avg_naive_ridge_D | 0.949 (0.888 to 1.012) | 0.933 | 0.954 | 0.266 | 0.258 |
| lightgbm_DW | 0.952 (0.867 to 1.048) | 0.903 | 0.963 | 0.367 | 0.600 |
| avg_ridge_cat_D | 0.960 (0.892 to 1.038) | 0.931 | 0.966 | 0.371 | 0.589 |
| catboost_DW | 0.964 (0.888 to 1.048) | 0.949 | 0.977 | 0.347 | 0.617 |
| avg_ridge_cat_DW | 0.968 (0.892 to 1.052) | 0.967 | 0.972 | 0.311 | 0.600 |
| ridgechg_D | 0.979 (0.909 to 1.055) | 0.961 | 0.979 | 0.263 | 0.343 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| ridge_D | 1.004 (0.937 to 1.080) | 0.997 | 1.006 | 0.266 | 0.258 |
| ridgechg_DW | 1.016 (0.944 to 1.096) | 1.038 | 1.021 | 0.230 | 0.417 |
| ridgechg_DWS | 1.019 (0.944 to 1.100) | 1.046 | 1.022 | 0.205 | 0.393 |
| ridge_DW | 1.025 (0.950 to 1.109) | 1.060 | 1.030 | 0.230 | 0.353 |
| revert6 | 1.030 (0.942 to 1.134) | 0.962 | 1.035 | 0.205 | 0.026 |
| seasonal_naive | 1.471 (1.300 to 1.671) | 1.357 | 1.483 | 0.268 | 0.401 |


### h3 after lasting rise (72 series, 136 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| catchg_D | 0.660 (0.511 to 0.855) | 0.777 | 0.667 | 0.627 | 0.942 |
| median_s2_all | 0.706 (0.532 to 0.919) | 0.438 | 0.712 | 0.755 | 0.939 |
| catchg_DVnli | 0.710 (0.577 to 0.881) | 0.648 | 0.722 | 0.536 | 0.935 |
| chronos2_top | 0.733 (0.555 to 0.952) | 0.780 | 0.742 | 0.882 | 0.939 |
| median_s2_demand | 0.735 (0.555 to 0.958) | 0.837 | 0.742 | 0.700 | 0.941 |
| catchg_DVdem | 0.771 (0.612 to 0.976) | 0.864 | 0.775 | 0.518 | 0.940 |
| lgbmchg_D | 0.782 (0.578 to 1.015) | 0.840 | 0.789 | 0.436 | 0.928 |
| catchg_DWS | 0.796 (0.568 to 1.098) | 1.102 | 0.814 | 0.600 | 0.930 |
| chronos2_cur | 0.807 (0.611 to 1.059) | 0.911 | 0.808 | 0.845 | 0.941 |
| chronos2_bk | 0.826 (0.639 to 1.054) | 0.892 | 0.829 | 0.882 | 0.939 |
| chronos | 0.829 (0.644 to 1.063) | 0.786 | 0.839 | 0.764 | 0.938 |
| chronos2_curdw | 0.837 (0.635 to 1.097) | 0.861 | 0.842 | 0.818 | 0.940 |
| chronos2_nli | 0.843 (0.648 to 1.096) | 0.965 | 0.852 | 0.782 | 0.940 |
| chronos2 | 0.853 (0.650 to 1.094) | 1.072 | 0.858 | 0.864 | 0.941 |
| ridgechg_D | 0.855 (0.690 to 1.058) | 0.942 | 0.862 | 0.645 | 0.776 |
| catchg_DW | 0.864 (0.684 to 1.104) | 0.954 | 0.882 | 0.582 | 0.931 |
| avg_ridge_cat_D | 0.901 (0.688 to 1.168) | 1.090 | 0.910 | 0.682 | 0.907 |
| median_all | 0.909 (0.705 to 1.174) | 0.878 | 0.914 | 0.645 | 0.926 |
| catboost_D | 0.932 (0.692 to 1.213) | 1.154 | 0.946 | 0.600 | 0.943 |
| invmae_all | 0.948 (0.719 to 1.257) | 1.035 | 0.949 | 0.691 | 0.918 |
| avg_naive_ridge_D | 0.993 (0.821 to 1.215) | 0.881 | 0.999 | 0.609 | 0.425 |
| ridgechg_DWS | 0.997 (0.773 to 1.320) | 1.466 | 1.007 | 0.709 | 0.717 |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |
| catboost_DW | 1.001 (0.722 to 1.344) | 1.127 | 1.009 | 0.636 | 0.935 |
| ridgechg_DW | 1.005 (0.794 to 1.296) | 1.413 | 1.018 | 0.736 | 0.716 |
| lightgbm_D | 1.014 (0.753 to 1.374) | 0.927 | 1.026 | 0.682 | 0.667 |
| avg_ridge_cat_DW | 1.034 (0.799 to 1.366) | 1.226 | 1.029 | 0.618 | 0.905 |
| ridge_D | 1.056 (0.818 to 1.366) | 1.159 | 1.067 | 0.609 | 0.425 |
| avg_three_DW | 1.121 (0.851 to 1.489) | 1.260 | 1.118 | 0.618 | 0.871 |
| seasonal_naive | 1.130 (0.770 to 1.653) | 1.091 | 1.132 | 0.518 | 0.955 |
| ridge_DW | 1.175 (0.848 to 1.620) | 1.383 | 1.187 | 0.609 | 0.364 |
| lightgbm_DW | 1.261 (0.911 to 1.732) | 1.109 | 1.267 | 0.609 | 0.660 |


### h3 surge months (outcome-defined) (231 series, 749 forecasts)

| pipeline | AvgRelMAE (95%) | volume-weighted | relative RMSE |
| --- | --- | --- | --- | --- | --- |
| seasonal_naive | 0.657 (0.591 to 0.725) | 0.586 | 0.685 |  |  |
| chronos2_curdw | 0.740 (0.673 to 0.801) | 0.596 | 0.758 |  |  |
| chronos2_bk | 0.741 (0.674 to 0.801) | 0.604 | 0.759 |  |  |
| chronos2_cur | 0.745 (0.679 to 0.807) | 0.601 | 0.763 |  |  |
| chronos2_nli | 0.746 (0.678 to 0.807) | 0.606 | 0.764 |  |  |
| chronos2_top | 0.749 (0.681 to 0.811) | 0.608 | 0.768 |  |  |
| chronos2 | 0.758 (0.693 to 0.818) | 0.619 | 0.776 |  |  |
| lightgbm_DW | 0.772 (0.720 to 0.823) | 0.665 | 0.782 |  |  |
| lgbmchg_D | 0.779 (0.725 to 0.833) | 0.676 | 0.792 |  |  |
| lightgbm_D | 0.781 (0.730 to 0.829) | 0.673 | 0.791 |  |  |
| chronos | 0.782 (0.718 to 0.839) | 0.667 | 0.799 |  |  |
| avg_three_DW | 0.795 (0.731 to 0.853) | 0.693 | 0.799 |  |  |
| median_s2_demand | 0.806 (0.754 to 0.854) | 0.699 | 0.814 |  |  |
| catboost_D | 0.807 (0.761 to 0.850) | 0.716 | 0.816 |  |  |
| catboost_DW | 0.808 (0.765 to 0.850) | 0.724 | 0.816 |  |  |
| catchg_DWS | 0.811 (0.757 to 0.861) | 0.708 | 0.819 |  |  |
| catchg_D | 0.811 (0.760 to 0.858) | 0.705 | 0.819 |  |  |
| catchg_DW | 0.812 (0.758 to 0.863) | 0.712 | 0.820 |  |  |
| median_all | 0.814 (0.768 to 0.858) | 0.723 | 0.821 |  |  |
| catchg_DVnli | 0.818 (0.766 to 0.866) | 0.718 | 0.825 |  |  |
| catchg_DVdem | 0.821 (0.774 to 0.865) | 0.729 | 0.827 |  |  |
| median_s2_all | 0.823 (0.773 to 0.866) | 0.732 | 0.830 |  |  |
| invmae_all | 0.825 (0.789 to 0.859) | 0.756 | 0.829 |  |  |
| avg_ridge_cat_D | 0.838 (0.801 to 0.874) | 0.777 | 0.842 |  |  |
| avg_ridge_cat_DW | 0.842 (0.806 to 0.876) | 0.788 | 0.846 |  |  |
| ridge_DW | 0.879 (0.853 to 0.905) | 0.860 | 0.882 |  |  |
| ridge_D | 0.879 (0.855 to 0.905) | 0.861 | 0.883 |  |  |
| revert6 | 0.885 (0.860 to 0.910) | 0.909 | 0.893 |  |  |
| ridgechg_DWS | 0.905 (0.882 to 0.929) | 0.885 | 0.908 |  |  |
| ridgechg_DW | 0.905 (0.883 to 0.928) | 0.884 | 0.908 |  |  |
| ridgechg_D | 0.905 (0.883 to 0.928) | 0.885 | 0.908 |  |  |
| avg_naive_ridge_D | 0.946 (0.934 to 0.958) | 0.937 | 0.947 |  |  |
| naive | 1.000 (1.000 to 1.000) | 1.000 | 1.000 |  |  |


## By format and level (leaders of A2, horizon 1; node intervals)

### print, narrow themes (183 series)

| pipeline | AvgRelMAE (95%) | volume-weighted | Spearman |
| --- | --- | --- | --- |
| chronos2_cur | 0.876 (0.849 to 0.901) | 0.813 | 0.421 |
| chronos2_curdw | 0.878 (0.851 to 0.903) | 0.817 | 0.419 |
| chronos2_bk | 0.880 (0.853 to 0.904) | 0.814 | 0.422 |
| naive | 1.000 (1.000 to 1.000) | 1.000 |  |


### print, middle themes (86 series)

| pipeline | AvgRelMAE (95%) | volume-weighted | Spearman |
| --- | --- | --- | --- |
| chronos2_cur | 0.850 (0.807 to 0.889) | 0.800 | 0.457 |
| chronos2_bk | 0.851 (0.807 to 0.890) | 0.798 | 0.458 |
| chronos2_curdw | 0.853 (0.811 to 0.892) | 0.804 | 0.456 |
| naive | 1.000 (1.000 to 1.000) | 1.000 |  |


### ebook, narrow themes (158 series)

| pipeline | AvgRelMAE (95%) | volume-weighted | Spearman |
| --- | --- | --- | --- |
| chronos2_cur | 0.990 (0.968 to 1.007) | 1.000 | 0.213 |
| chronos2_bk | 0.993 (0.971 to 1.010) | 1.000 | 0.218 |
| chronos2_curdw | 0.994 (0.972 to 1.011) | 1.001 | 0.213 |
| naive | 1.000 (1.000 to 1.000) | 1.000 |  |


### ebook, middle themes (84 series)

| pipeline | AvgRelMAE (95%) | volume-weighted | Spearman |
| --- | --- | --- | --- |
| chronos2_cur | 0.971 (0.934 to 0.999) | 0.987 | 0.255 |
| chronos2_bk | 0.973 (0.934 to 1.001) | 0.987 | 0.253 |
| chronos2_curdw | 0.976 (0.940 to 1.004) | 0.993 | 0.251 |
| naive | 1.000 (1.000 to 1.000) | 1.000 |  |


## By calendar year of the forecast origin (leaders of A2, horizon 1, AvgRelMAE)

| pipeline | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chronos2_bk | 0.893 | 0.985 | 0.929 | 0.900 | 0.910 | 0.892 | 0.905 | 0.938 |
| chronos2_cur | 0.894 | 0.979 | 0.932 | 0.900 | 0.904 | 0.889 | 0.899 | 0.923 |
| chronos2_curdw | 0.896 | 0.985 | 0.937 | 0.900 | 0.912 | 0.889 | 0.903 | 0.922 |
| naive | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |


## Routing coverage (counts only)

See data/reports/benchmark_stage2_routing_coverage.md.

## Context-reading routing (outcome-free checks)

See data/reports/benchmark_stage2_nli_routing.md.

## Categories learned from book text (structure)

See data/reports/benchmark_stage2_learned_categories.md.

## Categories learned from book text against subject-heading themes (scores)

See data/reports/benchmark_stage2_learned.md.

