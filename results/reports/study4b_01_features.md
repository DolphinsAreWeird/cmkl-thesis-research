# Study 4b, step 01: feature table (structure only)

Built 2026-10-14 01:39. 4b record SHA-256 `a34ab8e2279d4f13409a8786848a1179bd28964d35766c647acbefd44eab9bb4`; Study 4 record `040a7c7a7416d4a652b9fe5c52ef947447c1a5653db3839757819164f8917bd6`. Counts only: no target values.

| Horizon | Format | Level | Rows | Categories | Origins | Share with surge label (training and test rows) | Rows with s_sustained = 1 | Rows with s_resp != 0 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | audiobook | middle | 9,218 | 83 | 203 | 0.0046 | 24 | 2,973 |
| 1 | audiobook | narrow | 11,403 | 151 | 201 | 0.0063 | 48 | 4,181 |
| 1 | ebook | middle | 11,884 | 85 | 179 | 0.0035 | 29 | 3,576 |
| 1 | ebook | narrow | 17,312 | 160 | 175 | 0.0050 | 60 | 5,804 |
| 1 | print | middle | 19,796 | 86 | 234 | 0.0052 | 23 | 2,680 |
| 1 | print | narrow | 42,172 | 204 | 234 | 0.0054 | 67 | 6,757 |
| 2 | audiobook | middle | 9,054 | 83 | 201 | 0.0077 | 24 | 2,880 |
| 2 | audiobook | narrow | 11,117 | 151 | 199 | 0.0120 | 47 | 4,038 |
| 2 | ebook | middle | 11,718 | 85 | 177 | 0.0073 | 29 | 3,472 |
| 2 | ebook | narrow | 17,009 | 160 | 173 | 0.0088 | 58 | 5,625 |
| 2 | print | middle | 19,542 | 86 | 231 | 0.0126 | 23 | 2,582 |
| 2 | print | narrow | 41,662 | 204 | 231 | 0.0139 | 64 | 6,508 |
| 3 | audiobook | middle | 8,971 | 83 | 200 | 0.0107 | 24 | 2,829 |
| 3 | audiobook | narrow | 10,968 | 151 | 198 | 0.0176 | 48 | 3,959 |
| 3 | ebook | middle | 11,636 | 85 | 176 | 0.0094 | 29 | 3,419 |
| 3 | ebook | narrow | 16,854 | 160 | 172 | 0.0127 | 59 | 5,529 |
| 3 | print | middle | 19,373 | 86 | 229 | 0.0167 | 23 | 2,521 |
| 3 | print | narrow | 41,324 | 204 | 229 | 0.0210 | 63 | 6,354 |

The rebuilt h = 1, 2 rows were checked equal to `data/db/study4/features.parquet` (D and W columns, targets).
