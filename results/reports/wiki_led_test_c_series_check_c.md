# Check of correction A1 in Test C: the monthly candidate series, original and corrected

Written by `code/main_study/wiki_led/20c_check_series.py`. `monthly()` of `20_test_c.py` and of `20c_test_c.py` are read from the files with `ast` and run on the weekly series of every Test A book and author article; x(t) is the month-on-month change of ln(mean weekly share). Exact equality with NaN equal to NaN.

| kind | articles | first view in week 1 | differing months among them | other articles | months before the first view month that are missing in the corrected series | months from two months after the first view month that are identical | articles without any view | as expected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| book | 7,427 | 4,282 | 0 | 3,144 | 198,687 of 198,687 | 222,609 of 222,609 | 1 | yes |
| author | 3,001 | 2,310 | 0 | 689 | 36,529 of 36,529 | 55,797 of 55,797 | 2 | yes |
