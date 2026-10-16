# Final test, scoring rehearsal on known months

Written 2026-10-17 03:18. Code: code/main_study/benchmark/30_final_test_score.py --rehearsal 2026-05. The stored benchmark forecasts of a known origin are scored against the panel of a dry-run world (targets built by the extension rule). This tests the scoring code and the extension on months that are known; it is not a result of the final test.

## What was scored

| Horizon | Series group | Frozen rows | Rows with an observed target | Target months |
| --- | --- | ---: | ---: | --- |
| 1 | audiobook | 234 | 234 | 2026-06 |
| 1 | print and ebook | 479 | 479 | 2026-06 |
| 2 | audiobook | 234 | 234 | 2026-07 |
| 2 | print and ebook | 479 | 479 | 2026-07 |
| 3 | audiobook | 234 | 234 | 2026-08 |
| 3 | print and ebook | 479 | 479 | 2026-08 |

## Primary hypothesis

chronos2_cur against repeating last month, horizon 1, print and ebook, 479 rows: pooled error ratio 0.911 (95% interval 0.854 to 0.977). The upper limit is below 1: supported.
Reference, main comparison (88 months, 36,138 rows): pooled ratio 0.898, AvgRelMAE 0.914.

## Horizon 1, print and ebook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy | Spearman rise (95%) | Main comparison: pooled ratio, AvgRelMAE |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| naive | 479 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 4.91 | 0.000 |  |  |
| chronos | 479 | 0.943 (0.888 to 1.007) | 0.882 (0.797 to 0.976) | 479 | 4.63 | 0.702 | 0.332 (0.225 to 0.428) | 0.924, 0.943 |
| chronos2 | 479 | 0.935 (0.874 to 1.003) | 0.861 (0.779 to 0.955) | 479 | 4.59 | 0.638 | 0.306 (0.208 to 0.389) | 0.904, 0.920 |
| chronos2_cur | 479 | 0.911 (0.854 to 0.977) | 0.810 (0.730 to 0.902) | 479 | 4.48 | 0.660 | 0.335 (0.235 to 0.414) | 0.898, 0.914 |
| chronos2_curdw | 479 | 0.900 (0.843 to 0.967) | 0.778 (0.700 to 0.867) | 479 | 4.43 | 0.681 | 0.361 (0.261 to 0.440) | 0.900, 0.917 |
| chronos2_bk | 479 | 0.920 (0.866 to 0.982) | 0.827 (0.752 to 0.907) | 479 | 4.52 | 0.745 | 0.335 (0.242 to 0.418) | 0.900, 0.917 |
| catchg_D | 479 | 0.964 (0.927 to 1.005) | 0.934 (0.861 to 1.016) | 479 | 4.74 | 0.617 | 0.249 (0.152 to 0.335) | 0.935, 0.950 |
| catchg_DW | 479 | 0.967 (0.934 to 1.003) | 0.954 (0.887 to 1.028) | 479 | 4.75 | 0.553 | 0.227 (0.130 to 0.306) | 0.936, 0.951 |
| catchg_DWS | 479 | 0.963 (0.931 to 0.997) | 0.964 (0.901 to 1.036) | 479 | 4.73 | 0.617 | 0.239 (0.140 to 0.326) | 0.937, 0.953 |

## Horizon 2, print and ebook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| naive | 479 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 6.07 | 0.000 |
| chronos | 479 | 0.963 (0.904 to 1.029) | 0.911 (0.815 to 1.017) | 479 | 5.85 | 0.742 |
| chronos2 | 479 | 0.966 (0.901 to 1.040) | 0.912 (0.809 to 1.017) | 479 | 5.86 | 0.727 |
| chronos2_cur | 479 | 0.945 (0.879 to 1.017) | 0.912 (0.812 to 1.019) | 479 | 5.74 | 0.742 |
| chronos2_curdw | 479 | 0.940 (0.877 to 1.008) | 0.904 (0.807 to 1.012) | 479 | 5.71 | 0.727 |
| chronos2_bk | 479 | 0.959 (0.899 to 1.025) | 0.975 (0.883 to 1.074) | 479 | 5.82 | 0.773 |
| catchg_D | 479 | 0.940 (0.899 to 0.985) | 0.907 (0.813 to 1.014) | 479 | 5.71 | 0.697 |
| catchg_DW | 479 | 0.931 (0.892 to 0.973) | 0.899 (0.814 to 1.000) | 479 | 5.65 | 0.742 |
| catchg_DWS | 479 | 0.933 (0.896 to 0.972) | 0.913 (0.828 to 1.013) | 479 | 5.66 | 0.742 |

## Horizon 3, print and ebook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| naive | 479 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 6.95 | 0.000 |
| chronos | 479 | 0.987 (0.926 to 1.058) | 1.040 (0.924 to 1.167) | 479 | 6.86 | 0.710 |
| chronos2 | 479 | 0.973 (0.907 to 1.054) | 1.003 (0.889 to 1.142) | 479 | 6.76 | 0.700 |
| chronos2_cur | 479 | 0.947 (0.884 to 1.022) | 0.943 (0.835 to 1.069) | 479 | 6.58 | 0.720 |
| chronos2_curdw | 479 | 0.945 (0.885 to 1.018) | 0.942 (0.838 to 1.066) | 479 | 6.57 | 0.720 |
| chronos2_bk | 479 | 0.977 (0.915 to 1.051) | 1.029 (0.918 to 1.155) | 479 | 6.79 | 0.690 |
| catchg_D | 479 | 0.972 (0.925 to 1.026) | 1.047 (0.933 to 1.185) | 479 | 6.75 | 0.700 |
| catchg_DW | 479 | 0.977 (0.930 to 1.030) | 1.073 (0.961 to 1.209) | 479 | 6.79 | 0.720 |
| catchg_DWS | 479 | 0.981 (0.936 to 1.030) | 1.079 (0.962 to 1.218) | 479 | 6.81 | 0.680 |

## Horizon 1, audiobook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| naive | 234 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 3.91 | 0.000 |
| chronos | 234 | 1.028 (0.943 to 1.115) | 0.996 (0.865 to 1.142) | 234 | 4.01 | 0.571 |
| chronos2 | 234 | 0.996 (0.924 to 1.075) | 0.983 (0.860 to 1.125) | 234 | 3.89 | 0.643 |
| chronos2_cur | 234 | 0.979 (0.910 to 1.053) | 0.976 (0.853 to 1.117) | 234 | 3.82 | 0.643 |
| chronos2_curdw | 234 | 0.997 (0.927 to 1.073) | 1.018 (0.892 to 1.160) | 234 | 3.89 | 0.643 |
| chronos2_bk | 234 | 1.008 (0.930 to 1.091) | 1.015 (0.887 to 1.161) | 234 | 3.94 | 0.643 |
| catchg_D | 234 | 1.046 (0.999 to 1.093) | 1.084 (0.972 to 1.210) | 234 | 4.09 | 0.429 |
| catchg_DW | 234 | 1.044 (0.998 to 1.091) | 1.059 (0.939 to 1.193) | 234 | 4.08 | 0.429 |
| catchg_DWS | 234 | 1.032 (0.981 to 1.081) | 1.028 (0.897 to 1.171) | 234 | 4.03 | 0.429 |

## Horizon 2, audiobook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| naive | 234 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 5.39 | 0.000 |
| chronos | 234 | 1.065 (0.997 to 1.141) | 1.025 (0.878 to 1.197) | 234 | 5.74 | 0.680 |
| chronos2 | 234 | 1.035 (0.972 to 1.105) | 0.995 (0.850 to 1.159) | 234 | 5.57 | 0.600 |
| chronos2_cur | 234 | 0.999 (0.943 to 1.060) | 0.984 (0.859 to 1.122) | 234 | 5.38 | 0.640 |
| chronos2_curdw | 234 | 1.016 (0.957 to 1.080) | 1.062 (0.941 to 1.201) | 234 | 5.47 | 0.640 |
| chronos2_bk | 234 | 1.072 (1.007 to 1.146) | 1.096 (0.952 to 1.262) | 234 | 5.77 | 0.680 |
| catchg_D | 234 | 1.040 (0.995 to 1.093) | 1.119 (1.017 to 1.239) | 234 | 5.60 | 0.480 |
| catchg_DW | 234 | 1.045 (0.999 to 1.094) | 1.065 (0.944 to 1.191) | 234 | 5.63 | 0.560 |
| catchg_DWS | 234 | 1.042 (0.999 to 1.088) | 1.047 (0.932 to 1.167) | 234 | 5.61 | 0.560 |

## Horizon 3, audiobook

Pooled ratio = sum of absolute errors of the pipeline / of repeating last month (below 1 beats it); AvgRelMAE = the record's geometric mean over series; intervals resample categories (2,000 draws).

| Pipeline | Rows | Pooled ratio (95%) | AvgRelMAE (95%) | Series | Mean abs error x100 | Direction accuracy |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| naive | 234 | 1.000 (1.000 to 1.000) | 1.000 (1.000 to 1.000) |  | 7.19 | 0.000 |
| chronos | 234 | 1.019 (0.942 to 1.093) | 1.097 (0.972 to 1.245) | 234 | 7.32 | 0.635 |
| chronos2 | 234 | 0.982 (0.914 to 1.048) | 1.011 (0.885 to 1.153) | 234 | 7.06 | 0.692 |
| chronos2_cur | 234 | 0.961 (0.899 to 1.022) | 0.993 (0.874 to 1.124) | 234 | 6.91 | 0.673 |
| chronos2_curdw | 234 | 0.971 (0.903 to 1.036) | 1.013 (0.894 to 1.147) | 234 | 6.98 | 0.692 |
| chronos2_bk | 234 | 1.015 (0.946 to 1.088) | 1.071 (0.943 to 1.212) | 234 | 7.30 | 0.615 |
| catchg_D | 234 | 1.078 (1.019 to 1.142) | 1.203 (1.066 to 1.357) | 234 | 7.75 | 0.558 |
| catchg_DW | 234 | 1.072 (1.019 to 1.128) | 1.162 (1.030 to 1.313) | 234 | 7.71 | 0.558 |
| catchg_DWS | 234 | 1.061 (1.008 to 1.118) | 1.141 (0.999 to 1.303) | 234 | 7.63 | 0.558 |

## Paired comparisons, model held fixed (pooled ratio of the first to the second; below 1 = the first is better)

| Horizon | First | Second | Rows | Ratio (95%) |
| --- | --- | --- | ---: | --- |
| 1 | chronos2_cur | chronos2 | 479 | 0.975 (0.956 to 0.996) |
| 1 | chronos2_curdw | chronos2 | 479 | 0.964 (0.937 to 0.991) |
| 1 | chronos2_bk | chronos2 | 479 | 0.984 (0.960 to 1.008) |
| 1 | chronos2_curdw | chronos2_cur | 479 | 0.989 (0.974 to 1.002) |
| 1 | catchg_DW | catchg_D | 479 | 1.003 (0.990 to 1.016) |
| 1 | catchg_DWS | catchg_D | 479 | 0.999 (0.985 to 1.012) |
| 1 | chronos2_cur | chronos | 479 | 0.966 (0.932 to 1.004) |
| 1 | chronos2_cur | catchg_D | 479 | 0.945 (0.892 to 1.004) |
| 2 | chronos2_cur | chronos2 | 479 | 0.978 (0.959 to 0.998) |
| 2 | chronos2_curdw | chronos2 | 479 | 0.973 (0.947 to 0.999) |
| 2 | chronos2_bk | chronos2 | 479 | 0.992 (0.969 to 1.016) |
| 2 | chronos2_curdw | chronos2_cur | 479 | 0.995 (0.981 to 1.009) |
| 2 | catchg_DW | catchg_D | 479 | 0.990 (0.981 to 0.999) |
| 2 | catchg_DWS | catchg_D | 479 | 0.992 (0.979 to 1.004) |
| 2 | chronos2_cur | chronos | 479 | 0.981 (0.947 to 1.018) |
| 2 | chronos2_cur | catchg_D | 479 | 1.005 (0.946 to 1.065) |
| 3 | chronos2_cur | chronos2 | 479 | 0.973 (0.954 to 0.992) |
| 3 | chronos2_curdw | chronos2 | 479 | 0.971 (0.945 to 0.998) |
| 3 | chronos2_bk | chronos2 | 479 | 1.004 (0.981 to 1.028) |
| 3 | chronos2_curdw | chronos2_cur | 479 | 0.999 (0.984 to 1.012) |
| 3 | catchg_DW | catchg_D | 479 | 1.005 (0.990 to 1.020) |
| 3 | catchg_DWS | catchg_D | 479 | 1.009 (0.992 to 1.026) |
| 3 | chronos2_cur | chronos | 479 | 0.959 (0.930 to 0.991) |
| 3 | chronos2_cur | catchg_D | 479 | 0.974 (0.918 to 1.036) |

## Agreement of the ordering with the main comparison

Rank correlation between the pooled error ratios of the 8 pipelines on these months and in the main comparison (horizon 1, print and ebook): 0.905 against the main pooled ratios, 0.857 against the main AvgRelMAE. Descriptive only; with this few rows differences between neighbouring pipelines are within their intervals.

## Not computed

The model confidence set, the surge average precision and the segments (after short or lasting rises, surge months) need more months or more events than the final test has (addendum d).
