# Test F, check G1: agreement with the independent judge (real data)

- written 2026-10-21 19:22; judged pages scored 400 (example pages left out 0; judged pages without an answer 0); judge key judge_set_info.csv
- pages every method could route: 400; judge says none on 0; misleading title on 114
- notes on the judge lines: none

Precision: share of the method's page-theme pairs the judge also gives. Recall: share of the judge's pairs the method gives. Misleading: on pages with a misleading title, share the method sends to a theme the judge does not give (lower is better). 95% intervals from 2,000 draws of pages.

## common pages

| group | method | level | pages | method_pairs | judge_pairs | precision | precision_lo | precision_hi | recall | recall_lo | recall_hi | misleading_pages | misleading_wrong_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | AI sorter (all pairs) | narrow | 400 | 828 | 863 | 0.849 | 0.826 | 0.871 | 0.815 | 0.792 | 0.837 | 114 | 0.368 |
| all | AI sorter (all pairs) | middle | 400 | 759 | 777 | 0.867 | 0.844 | 0.889 | 0.847 | 0.824 | 0.870 | 114 | 0.316 |
| all | AI sorter (confidence 2 or 3) | narrow | 400 | 588 | 863 | 0.951 | 0.934 | 0.966 | 0.648 | 0.622 | 0.673 | 114 | 0.105 |
| all | AI sorter (confidence 2 or 3) | middle | 400 | 552 | 777 | 0.958 | 0.941 | 0.973 | 0.681 | 0.653 | 0.709 | 114 | 0.096 |
| all | zero-shot routing (p >= 0.50) | narrow | 400 | 145 | 863 | 0.717 | 0.643 | 0.789 | 0.121 | 0.096 | 0.145 | 114 | 0.123 |
| all | zero-shot routing (p >= 0.50) | middle | 400 | 142 | 777 | 0.768 | 0.693 | 0.841 | 0.140 | 0.113 | 0.167 | 114 | 0.114 |
| all | embedding routing (cos >= 0.70) | narrow | 400 | 45 | 863 | 0.711 | 0.574 | 0.837 | 0.037 | 0.025 | 0.050 | 114 | 0.105 |
| all | embedding routing (cos >= 0.70) | middle | 400 | 48 | 777 | 0.708 | 0.577 | 0.829 | 0.044 | 0.030 | 0.059 | 114 | 0.114 |
| hard case | AI sorter (all pairs) | narrow | 100 | 246 | 252 | 0.793 | 0.750 | 0.835 | 0.774 | 0.732 | 0.815 | 47 | 0.468 |
| hard case | AI sorter (all pairs) | middle | 100 | 229 | 237 | 0.834 | 0.792 | 0.876 | 0.806 | 0.766 | 0.845 | 47 | 0.362 |
| hard case | AI sorter (confidence 2 or 3) | narrow | 100 | 186 | 252 | 0.892 | 0.850 | 0.933 | 0.659 | 0.616 | 0.700 | 47 | 0.170 |
| hard case | AI sorter (confidence 2 or 3) | middle | 100 | 176 | 237 | 0.909 | 0.867 | 0.949 | 0.675 | 0.630 | 0.718 | 47 | 0.149 |
| hard case | zero-shot routing (p >= 0.50) | narrow | 100 | 68 | 252 | 0.691 | 0.571 | 0.800 | 0.187 | 0.137 | 0.240 | 47 | 0.191 |
| hard case | zero-shot routing (p >= 0.50) | middle | 100 | 69 | 237 | 0.696 | 0.580 | 0.806 | 0.203 | 0.151 | 0.259 | 47 | 0.191 |
| hard case | embedding routing (cos >= 0.70) | narrow | 100 | 35 | 252 | 0.629 | 0.467 | 0.784 | 0.087 | 0.057 | 0.124 | 47 | 0.255 |
| hard case | embedding routing (cos >= 0.70) | middle | 100 | 36 | 237 | 0.639 | 0.475 | 0.792 | 0.097 | 0.063 | 0.138 | 47 | 0.255 |
| hard: adaptation | AI sorter (all pairs) | narrow | 33 | 95 | 97 | 0.705 | 0.638 | 0.772 | 0.691 | 0.626 | 0.750 | 16 | 0.688 |
| hard: adaptation | AI sorter (all pairs) | middle | 33 | 88 | 94 | 0.784 | 0.723 | 0.849 | 0.734 | 0.681 | 0.791 | 16 | 0.500 |
| hard: adaptation | AI sorter (confidence 2 or 3) | narrow | 33 | 72 | 97 | 0.792 | 0.718 | 0.870 | 0.588 | 0.525 | 0.657 | 16 | 0.375 |
| hard: adaptation | AI sorter (confidence 2 or 3) | middle | 33 | 68 | 94 | 0.838 | 0.766 | 0.912 | 0.606 | 0.543 | 0.674 | 16 | 0.312 |
| hard: adaptation | zero-shot routing (p >= 0.50) | narrow | 33 | 9 | 97 | 0.333 | 0.000 | 0.800 | 0.031 | 0.000 | 0.071 | 16 | 0.125 |
| hard: adaptation | zero-shot routing (p >= 0.50) | middle | 33 | 9 | 94 | 0.333 | 0.000 | 0.800 | 0.032 | 0.000 | 0.071 | 16 | 0.125 |
| hard: adaptation | embedding routing (cos >= 0.70) | narrow | 33 | 1 | 97 | 1.000 | 1.000 | 1.000 | 0.010 | 0.000 | 0.031 | 16 | 0.000 |
| hard: adaptation | embedding routing (cos >= 0.70) | middle | 33 | 1 | 94 | 1.000 | 1.000 | 1.000 | 0.011 | 0.000 | 0.033 | 16 | 0.000 |
| hard: routing disagreement | AI sorter (all pairs) | narrow | 33 | 76 | 77 | 0.842 | 0.781 | 0.905 | 0.831 | 0.756 | 0.901 | 18 | 0.389 |
| hard: routing disagreement | AI sorter (all pairs) | middle | 33 | 71 | 71 | 0.845 | 0.779 | 0.912 | 0.845 | 0.762 | 0.920 | 18 | 0.333 |
| hard: routing disagreement | AI sorter (confidence 2 or 3) | narrow | 33 | 57 | 77 | 0.947 | 0.891 | 1.000 | 0.701 | 0.620 | 0.781 | 18 | 0.111 |
| hard: routing disagreement | AI sorter (confidence 2 or 3) | middle | 33 | 53 | 71 | 0.943 | 0.885 | 1.000 | 0.704 | 0.628 | 0.782 | 18 | 0.111 |
| hard: routing disagreement | zero-shot routing (p >= 0.50) | narrow | 33 | 22 | 77 | 0.818 | 0.643 | 0.960 | 0.234 | 0.150 | 0.329 | 18 | 0.167 |
| hard: routing disagreement | zero-shot routing (p >= 0.50) | middle | 33 | 23 | 71 | 0.783 | 0.591 | 0.950 | 0.254 | 0.162 | 0.359 | 18 | 0.167 |
| hard: routing disagreement | embedding routing (cos >= 0.70) | narrow | 33 | 21 | 77 | 0.429 | 0.211 | 0.632 | 0.117 | 0.053 | 0.181 | 18 | 0.611 |
| hard: routing disagreement | embedding routing (cos >= 0.70) | middle | 33 | 22 | 71 | 0.455 | 0.250 | 0.647 | 0.141 | 0.072 | 0.209 | 18 | 0.611 |
| hard: title review | AI sorter (all pairs) | narrow | 34 | 75 | 78 | 0.853 | 0.778 | 0.925 | 0.821 | 0.753 | 0.886 | 13 | 0.308 |
| hard: title review | AI sorter (all pairs) | middle | 34 | 70 | 72 | 0.886 | 0.811 | 0.955 | 0.861 | 0.794 | 0.928 | 13 | 0.231 |
| hard: title review | AI sorter (confidence 2 or 3) | narrow | 34 | 57 | 78 | 0.965 | 0.917 | 1.000 | 0.705 | 0.639 | 0.773 | 13 | 0.000 |
| hard: title review | AI sorter (confidence 2 or 3) | middle | 34 | 55 | 72 | 0.964 | 0.914 | 1.000 | 0.736 | 0.667 | 0.809 | 13 | 0.000 |
| hard: title review | zero-shot routing (p >= 0.50) | narrow | 34 | 37 | 78 | 0.703 | 0.556 | 0.846 | 0.333 | 0.230 | 0.449 | 13 | 0.308 |
| hard: title review | zero-shot routing (p >= 0.50) | middle | 34 | 37 | 72 | 0.730 | 0.600 | 0.867 | 0.375 | 0.268 | 0.492 | 13 | 0.308 |
| hard: title review | embedding routing (cos >= 0.70) | narrow | 34 | 13 | 78 | 0.923 | 0.733 | 1.000 | 0.154 | 0.080 | 0.247 | 13 | 0.077 |
| hard: title review | embedding routing (cos >= 0.70) | middle | 34 | 13 | 72 | 0.923 | 0.733 | 1.000 | 0.167 | 0.084 | 0.273 | 13 | 0.077 |
| random | AI sorter (all pairs) | narrow | 300 | 582 | 611 | 0.873 | 0.847 | 0.896 | 0.831 | 0.805 | 0.859 | 67 | 0.299 |
| random | AI sorter (all pairs) | middle | 300 | 530 | 540 | 0.881 | 0.853 | 0.907 | 0.865 | 0.838 | 0.892 | 67 | 0.284 |
| random | AI sorter (confidence 2 or 3) | narrow | 300 | 402 | 611 | 0.978 | 0.964 | 0.990 | 0.643 | 0.613 | 0.674 | 67 | 0.060 |
| random | AI sorter (confidence 2 or 3) | middle | 300 | 376 | 540 | 0.981 | 0.968 | 0.994 | 0.683 | 0.650 | 0.719 | 67 | 0.060 |
| random | zero-shot routing (p >= 0.50) | narrow | 300 | 77 | 611 | 0.740 | 0.657 | 0.831 | 0.093 | 0.068 | 0.120 | 67 | 0.075 |
| random | zero-shot routing (p >= 0.50) | middle | 300 | 73 | 540 | 0.836 | 0.750 | 0.919 | 0.113 | 0.084 | 0.145 | 67 | 0.060 |
| random | embedding routing (cos >= 0.70) | narrow | 300 | 10 | 611 | 1.000 | 1.000 | 1.000 | 0.016 | 0.008 | 0.027 | 67 | 0.000 |
| random | embedding routing (cos >= 0.70) | middle | 300 | 12 | 540 | 0.917 | 0.750 | 1.000 | 0.020 | 0.009 | 0.032 | 67 | 0.015 |

## pages each method covers

| group | method | level | pages | method_pairs | judge_pairs | precision | precision_lo | precision_hi | recall | recall_lo | recall_hi | misleading_pages | misleading_wrong_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | AI sorter (all pairs) | narrow | 400 | 828 | 863 | 0.849 | 0.827 | 0.870 | 0.815 | 0.792 | 0.836 | 114 | 0.368 |
| all | AI sorter (all pairs) | middle | 400 | 759 | 777 | 0.867 | 0.844 | 0.888 | 0.847 | 0.823 | 0.869 | 114 | 0.316 |
| all | AI sorter (confidence 2 or 3) | narrow | 400 | 588 | 863 | 0.951 | 0.933 | 0.967 | 0.648 | 0.622 | 0.672 | 114 | 0.105 |
| all | AI sorter (confidence 2 or 3) | middle | 400 | 552 | 777 | 0.958 | 0.942 | 0.974 | 0.681 | 0.653 | 0.708 | 114 | 0.096 |
| all | zero-shot routing (p >= 0.50) | narrow | 400 | 145 | 863 | 0.717 | 0.643 | 0.788 | 0.121 | 0.096 | 0.145 | 114 | 0.123 |
| all | zero-shot routing (p >= 0.50) | middle | 400 | 142 | 777 | 0.768 | 0.696 | 0.835 | 0.140 | 0.112 | 0.167 | 114 | 0.114 |
| all | embedding routing (cos >= 0.70) | narrow | 400 | 45 | 863 | 0.711 | 0.574 | 0.838 | 0.037 | 0.026 | 0.050 | 114 | 0.105 |
| all | embedding routing (cos >= 0.70) | middle | 400 | 48 | 777 | 0.708 | 0.577 | 0.838 | 0.044 | 0.031 | 0.059 | 114 | 0.114 |
| hard case | AI sorter (all pairs) | narrow | 100 | 246 | 252 | 0.793 | 0.749 | 0.834 | 0.774 | 0.732 | 0.814 | 47 | 0.468 |
| hard case | AI sorter (all pairs) | middle | 100 | 229 | 237 | 0.834 | 0.795 | 0.874 | 0.806 | 0.765 | 0.845 | 47 | 0.362 |
| hard case | AI sorter (confidence 2 or 3) | narrow | 100 | 186 | 252 | 0.892 | 0.847 | 0.933 | 0.659 | 0.614 | 0.702 | 47 | 0.170 |
| hard case | AI sorter (confidence 2 or 3) | middle | 100 | 176 | 237 | 0.909 | 0.867 | 0.949 | 0.675 | 0.629 | 0.717 | 47 | 0.149 |
| hard case | zero-shot routing (p >= 0.50) | narrow | 100 | 68 | 252 | 0.691 | 0.569 | 0.811 | 0.187 | 0.138 | 0.238 | 47 | 0.191 |
| hard case | zero-shot routing (p >= 0.50) | middle | 100 | 69 | 237 | 0.696 | 0.584 | 0.809 | 0.203 | 0.152 | 0.259 | 47 | 0.191 |
| hard case | embedding routing (cos >= 0.70) | narrow | 100 | 35 | 252 | 0.629 | 0.459 | 0.788 | 0.087 | 0.056 | 0.125 | 47 | 0.255 |
| hard case | embedding routing (cos >= 0.70) | middle | 100 | 36 | 237 | 0.639 | 0.474 | 0.791 | 0.097 | 0.062 | 0.138 | 47 | 0.255 |
| hard: adaptation | AI sorter (all pairs) | narrow | 33 | 95 | 97 | 0.705 | 0.639 | 0.768 | 0.691 | 0.626 | 0.753 | 16 | 0.688 |
| hard: adaptation | AI sorter (all pairs) | middle | 33 | 88 | 94 | 0.784 | 0.723 | 0.847 | 0.734 | 0.681 | 0.787 | 16 | 0.500 |
| hard: adaptation | AI sorter (confidence 2 or 3) | narrow | 33 | 72 | 97 | 0.792 | 0.720 | 0.870 | 0.588 | 0.520 | 0.657 | 16 | 0.375 |
| hard: adaptation | AI sorter (confidence 2 or 3) | middle | 33 | 68 | 94 | 0.838 | 0.764 | 0.913 | 0.606 | 0.537 | 0.673 | 16 | 0.312 |
| hard: adaptation | zero-shot routing (p >= 0.50) | narrow | 33 | 9 | 97 | 0.333 | 0.000 | 0.833 | 0.031 | 0.000 | 0.063 | 16 | 0.125 |
| hard: adaptation | zero-shot routing (p >= 0.50) | middle | 33 | 9 | 94 | 0.333 | 0.000 | 0.833 | 0.032 | 0.000 | 0.065 | 16 | 0.125 |
| hard: adaptation | embedding routing (cos >= 0.70) | narrow | 33 | 1 | 97 | 1.000 | 1.000 | 1.000 | 0.010 | 0.000 | 0.032 | 16 | 0.000 |
| hard: adaptation | embedding routing (cos >= 0.70) | middle | 33 | 1 | 94 | 1.000 | 1.000 | 1.000 | 0.011 | 0.000 | 0.033 | 16 | 0.000 |
| hard: routing disagreement | AI sorter (all pairs) | narrow | 33 | 76 | 77 | 0.842 | 0.780 | 0.908 | 0.831 | 0.756 | 0.901 | 18 | 0.389 |
| hard: routing disagreement | AI sorter (all pairs) | middle | 33 | 71 | 71 | 0.845 | 0.775 | 0.913 | 0.845 | 0.761 | 0.917 | 18 | 0.333 |
| hard: routing disagreement | AI sorter (confidence 2 or 3) | narrow | 33 | 57 | 77 | 0.947 | 0.889 | 1.000 | 0.701 | 0.622 | 0.779 | 18 | 0.111 |
| hard: routing disagreement | AI sorter (confidence 2 or 3) | middle | 33 | 53 | 71 | 0.943 | 0.881 | 1.000 | 0.704 | 0.627 | 0.779 | 18 | 0.111 |
| hard: routing disagreement | zero-shot routing (p >= 0.50) | narrow | 33 | 22 | 77 | 0.818 | 0.636 | 0.957 | 0.234 | 0.157 | 0.325 | 18 | 0.167 |
| hard: routing disagreement | zero-shot routing (p >= 0.50) | middle | 33 | 23 | 71 | 0.783 | 0.600 | 0.944 | 0.254 | 0.169 | 0.355 | 18 | 0.167 |
| hard: routing disagreement | embedding routing (cos >= 0.70) | narrow | 33 | 21 | 77 | 0.429 | 0.211 | 0.650 | 0.117 | 0.055 | 0.184 | 18 | 0.611 |
| hard: routing disagreement | embedding routing (cos >= 0.70) | middle | 33 | 22 | 71 | 0.455 | 0.261 | 0.667 | 0.141 | 0.078 | 0.216 | 18 | 0.611 |
| hard: title review | AI sorter (all pairs) | narrow | 34 | 75 | 78 | 0.853 | 0.778 | 0.924 | 0.821 | 0.750 | 0.889 | 13 | 0.308 |
| hard: title review | AI sorter (all pairs) | middle | 34 | 70 | 72 | 0.886 | 0.812 | 0.956 | 0.861 | 0.790 | 0.928 | 13 | 0.231 |
| hard: title review | AI sorter (confidence 2 or 3) | narrow | 34 | 57 | 78 | 0.965 | 0.918 | 1.000 | 0.705 | 0.641 | 0.773 | 13 | 0.000 |
| hard: title review | AI sorter (confidence 2 or 3) | middle | 34 | 55 | 72 | 0.964 | 0.915 | 1.000 | 0.736 | 0.663 | 0.810 | 13 | 0.000 |
| hard: title review | zero-shot routing (p >= 0.50) | narrow | 34 | 37 | 78 | 0.703 | 0.545 | 0.857 | 0.333 | 0.224 | 0.456 | 13 | 0.308 |
| hard: title review | zero-shot routing (p >= 0.50) | middle | 34 | 37 | 72 | 0.730 | 0.595 | 0.875 | 0.375 | 0.266 | 0.500 | 13 | 0.308 |
| hard: title review | embedding routing (cos >= 0.70) | narrow | 34 | 13 | 78 | 0.923 | 0.750 | 1.000 | 0.154 | 0.080 | 0.246 | 13 | 0.077 |
| hard: title review | embedding routing (cos >= 0.70) | middle | 34 | 13 | 72 | 0.923 | 0.750 | 1.000 | 0.167 | 0.085 | 0.269 | 13 | 0.077 |
| random | AI sorter (all pairs) | narrow | 300 | 582 | 611 | 0.873 | 0.847 | 0.898 | 0.831 | 0.805 | 0.858 | 67 | 0.299 |
| random | AI sorter (all pairs) | middle | 300 | 530 | 540 | 0.881 | 0.854 | 0.908 | 0.865 | 0.837 | 0.892 | 67 | 0.284 |
| random | AI sorter (confidence 2 or 3) | narrow | 300 | 402 | 611 | 0.978 | 0.963 | 0.990 | 0.643 | 0.611 | 0.675 | 67 | 0.060 |
| random | AI sorter (confidence 2 or 3) | middle | 300 | 376 | 540 | 0.981 | 0.967 | 0.994 | 0.683 | 0.647 | 0.718 | 67 | 0.060 |
| random | zero-shot routing (p >= 0.50) | narrow | 300 | 77 | 611 | 0.740 | 0.658 | 0.831 | 0.093 | 0.068 | 0.121 | 67 | 0.075 |
| random | zero-shot routing (p >= 0.50) | middle | 300 | 73 | 540 | 0.836 | 0.745 | 0.919 | 0.113 | 0.084 | 0.146 | 67 | 0.060 |
| random | embedding routing (cos >= 0.70) | narrow | 300 | 10 | 611 | 1.000 | 1.000 | 1.000 | 0.016 | 0.007 | 0.027 | 67 | 0.000 |
| random | embedding routing (cos >= 0.70) | middle | 300 | 12 | 540 | 0.917 | 0.727 | 1.000 | 0.020 | 0.009 | 0.033 | 67 | 0.015 |

