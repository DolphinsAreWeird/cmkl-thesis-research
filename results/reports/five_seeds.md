# Five-seed reruns of the headline results

Made by `code/main_study/wiki_led/93_five_seeds_report.py` on 2026-11-20 17:30 +0700. Record: `prereg/DEVIATIONS.md`, "Five-seed reruns asked for by the advisor (20 November 2026)", written before the reruns. Asked for by Dr. Fawad Asadi on 20 November 2026.

Each model was refitted with five LightGBM seeds (20261020, 20261021, 20261022, 20261023, 20261024); rows, features, test years and all other settings are unchanged. The first seed is the one used for the published results, and its refit reproduced the stored predictions (largest difference 8.9e-16 for the main set, 0.0e+00 for new books). The test years are fixed by time, so the seed changes only the random sampling of rows and columns inside the boosted trees. Re-drawn samples of works for the main set (part 2 of the record) are in their own section below once they are run. New books use every new book, so they have no sample to re-draw.

The "fixed in advance" column is the published value with its 95% interval (blocks of 3 months for the main set, author clusters for new books). SD is the standard deviation over the five seeds (n - 1).


## Main set, books chosen in time (addendum l), all formats, 2019-2026

| Value | Fixed in advance [95% interval] | Seed 20 | Seed 21 | Seed 22 | Seed 23 | Seed 24 | Mean ± SD | Smallest to largest | Gains above 0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wikipedia alone (W14), change rank | 0.0911 [0.0844, 0.0976] | 0.0911 | 0.0910 | 0.0913 | 0.0915 | 0.0914 | 0.0913 ± 0.0002 | 0.0910 to 0.0915 |  |
| Library model (HM), change rank | 0.3474 [0.3396, 0.3554] | 0.3474 | 0.3470 | 0.3474 | 0.3476 | 0.3472 | 0.3473 ± 0.0002 | 0.3470 to 0.3476 |  |
| Library + Wikipedia (HMW14), change rank | 0.3521 [0.3443, 0.3602] | 0.3521 | 0.3521 | 0.3522 | 0.3522 | 0.3523 | 0.3522 ± 0.0001 | 0.3521 to 0.3523 |  |
| Gain from Wikipedia, change rank (L2a) | 0.0047 [0.0036, 0.0057] | 0.0047 | 0.0051 | 0.0048 | 0.0046 | 0.0051 | 0.0049 ± 0.0002 | 0.0046 to 0.0051 | 5 of 5 |
| Gain from Wikipedia, early-warning top 20 (L2b) | -0.0130 [-0.0256, -0.0017] | -0.0130 | -0.0137 | -0.0109 | -0.0120 | -0.0199 | -0.0139 ± 0.0035 | -0.0199 to -0.0109 | 0 of 5 |
| Gain from Wikipedia, top 20 that rose | 0.0021 [-0.0056, 0.0100] | 0.0021 | 0.0094 | 0.0073 | 0.0122 | 0.0064 | 0.0075 ± 0.0037 | 0.0021 to 0.0122 | 5 of 5 |

## Main set, books chosen in time (addendum l), all formats, 2024-2026

| Value | Fixed in advance [95% interval] | Seed 20 | Seed 21 | Seed 22 | Seed 23 | Seed 24 | Mean ± SD | Smallest to largest | Gains above 0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gain from Wikipedia, change rank (L2a) | 0.0039 [0.0028, 0.0050] | 0.0039 | 0.0042 | 0.0034 | 0.0038 | 0.0039 | 0.0038 ± 0.0003 | 0.0034 to 0.0042 | 5 of 5 |
| Gain from Wikipedia, early-warning top 20 (L2b) | 0.0006 [-0.0111, 0.0111] | 0.0006 | 0.0045 | 0.0051 | 0.0160 | -0.0051 | 0.0042 ± 0.0078 | -0.0051 to 0.0160 | 4 of 5 |
| Gain from Wikipedia, top 20 that rose | -0.0045 [-0.0139, 0.0056] | -0.0045 | 0.0058 | 0.0000 | 0.0077 | 0.0000 | 0.0018 ± 0.0049 | -0.0045 to 0.0077 | 2 of 5 |

## New books (Test B), all new books, rank correlation within test year

| Value | Fixed in advance [95% interval] | Seed 20 | Seed 21 | Seed 22 | Seed 23 | Seed 24 | Mean ± SD | Smallest to largest | Gains above 0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wikipedia alone (W) | 0.1273 [0.1152, 0.1383] | 0.1273 | 0.1276 | 0.1273 | 0.1266 | 0.1274 | 0.1272 ± 0.0004 | 0.1266 to 0.1276 |  |
| Library model (L) | 0.3487 [0.3369, 0.3605] | 0.3487 | 0.3486 | 0.3501 | 0.3495 | 0.3495 | 0.3493 ± 0.0006 | 0.3486 to 0.3501 |  |
| Library + Wikipedia (LW) | 0.3724 [0.3624, 0.3828] | 0.3724 | 0.3720 | 0.3725 | 0.3721 | 0.3722 | 0.3723 ± 0.0002 | 0.3720 to 0.3725 |  |
| Gain from Wikipedia over L | 0.0237 [0.0191, 0.0299] | 0.0237 | 0.0235 | 0.0224 | 0.0226 | 0.0226 | 0.0230 ± 0.0006 | 0.0224 to 0.0237 | 5 of 5 |
| Gain over L0, catalogue facts known at first loan (exploratory) | 0.0122 [0.0098, 0.0152] | 0.0122 | 0.0124 | 0.0119 | 0.0121 | 0.0121 | 0.0121 ± 0.0002 | 0.0119 to 0.0124 | 5 of 5 |
| Gain over Lq, the same without the theme (exploratory) | 0.0107 [0.0078, 0.0145] | 0.0107 | 0.0110 | 0.0104 | 0.0107 | 0.0112 | 0.0108 ± 0.0003 | 0.0104 to 0.0112 | 5 of 5 |

## New books (Test B), author article viewed before the first loan, rank correlation within test year

| Value | Fixed in advance [95% interval] | Seed 20 | Seed 21 | Seed 22 | Seed 23 | Seed 24 | Mean ± SD | Smallest to largest | Gains above 0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gain from Wikipedia over L | 0.0504 [0.0423, 0.0593] | 0.0504 | 0.0517 | 0.0500 | 0.0492 | 0.0500 | 0.0502 ± 0.0009 | 0.0492 to 0.0517 | 5 of 5 |
| Gain over L0, catalogue facts known at first loan (exploratory) | 0.0258 [0.0214, 0.0308] | 0.0258 | 0.0265 | 0.0259 | 0.0255 | 0.0263 | 0.0260 ± 0.0004 | 0.0255 to 0.0265 | 5 of 5 |
| Gain over Lq, the same without the theme (exploratory) | 0.0256 [0.0207, 0.0308] | 0.0256 | 0.0260 | 0.0255 | 0.0259 | 0.0275 | 0.0261 ± 0.0008 | 0.0255 to 0.0275 | 5 of 5 |

## In short

- Main set, books chosen in time (addendum l), all formats, 2019-2026: gain from Wikipedia, change rank (L2a): mean 0.0049 ± 0.0002; above zero with 5 of 5 seeds; the seeds spread over 0.0005, against a published interval 0.0021 wide.
- Main set, books chosen in time (addendum l), all formats, 2019-2026: gain from Wikipedia, early-warning top 20 (L2b): mean -0.0139 ± 0.0035; above zero with 0 of 5 seeds; the seeds spread over 0.0090, against a published interval 0.0239 wide.
- Main set, books chosen in time (addendum l), all formats, 2019-2026: gain from Wikipedia, top 20 that rose: mean 0.0075 ± 0.0037; above zero with 5 of 5 seeds; the seeds spread over 0.0100, against a published interval 0.0156 wide.
- Main set, books chosen in time (addendum l), all formats, 2024-2026: gain from Wikipedia, change rank (L2a): mean 0.0038 ± 0.0003; above zero with 5 of 5 seeds; the seeds spread over 0.0008, against a published interval 0.0022 wide.
- Main set, books chosen in time (addendum l), all formats, 2024-2026: gain from Wikipedia, early-warning top 20 (L2b): mean 0.0042 ± 0.0078; above zero with 4 of 5 seeds; the seeds spread over 0.0212, against a published interval 0.0222 wide.
- Main set, books chosen in time (addendum l), all formats, 2024-2026: gain from Wikipedia, top 20 that rose: mean 0.0018 ± 0.0049; above zero with 2 of 5 seeds; the seeds spread over 0.0122, against a published interval 0.0195 wide.
- New books (Test B), all new books: gain from Wikipedia over L: mean 0.0230 ± 0.0006; above zero with 5 of 5 seeds; the seeds spread over 0.0013, against a published interval 0.0108 wide.
- New books (Test B), all new books: gain over L0, catalogue facts known at first loan (exploratory): mean 0.0121 ± 0.0002; above zero with 5 of 5 seeds; the seeds spread over 0.0005, against a published interval 0.0054 wide.
- New books (Test B), all new books: gain over Lq, the same without the theme (exploratory): mean 0.0108 ± 0.0003; above zero with 5 of 5 seeds; the seeds spread over 0.0008, against a published interval 0.0067 wide.
- New books (Test B), author article viewed before the first loan: gain from Wikipedia over L: mean 0.0502 ± 0.0009; above zero with 5 of 5 seeds; the seeds spread over 0.0025, against a published interval 0.0170 wide.
- New books (Test B), author article viewed before the first loan: gain over L0, catalogue facts known at first loan (exploratory): mean 0.0260 ± 0.0004; above zero with 5 of 5 seeds; the seeds spread over 0.0010, against a published interval 0.0094 wide.
- New books (Test B), author article viewed before the first loan: gain over Lq, the same without the theme (exploratory): mean 0.0261 ± 0.0008; above zero with 5 of 5 seeds; the seeds spread over 0.0020, against a published interval 0.0101 wide.
