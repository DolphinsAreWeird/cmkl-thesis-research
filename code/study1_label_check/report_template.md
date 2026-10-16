# Study 1 label-window check: does the outcome label change which recordings the models can predict?

Fixed record: `prereg/study1_label_check_2026-10-13.json` (SHA-256 checked at the start of the run: 60944e46ad5d878481b4916d91ddafea306598141dee7cf63cb1c9d625a2b756), plus addendum `prereg/addenda_study1/2026-10-13_a_partial_pooling_label.json`. Code: `code/study1_label_check/`. Run log: `data/reports/s1_labels.log`. Study 1 results with the months 2 to 7 label were known beforehand, so this is a robustness check, reported in full.

## What was run

- Walk-forward over 20 quarters (2020Q1 to 2024Q4), same titles, features, models, model settings and quarter rule as `walkforward3_fix.py`; 3,804 recordings, {{n_test}} in the test quarters. Training uses only titles whose label window closed before the test quarter began. Window ends: L0 month 7, L2 month 14, L3 and L4 month 12 after the release month. Every release is early enough that all four windows are complete for all 20 quarters, so every label has the same 20 test quarters.
- Models: ridge and CatBoost. Stages: S0 metadata only; S4 plus social and text; S5 plus history (author, book and narrator prior labels, built from the label under test).
- Labels: L0 mean of log(1+views) in months 2 to 7; L2 the same in months 9 to 14; L3 the common-curve level (precision weighted, log(1+views), months 1 to 12); L4 the negative binomial level with a book-specific decay slope shrunk toward the common curve. L3 and L4 are fitted inside each step from training titles only, then applied to every title using that title's own views.
- Pipeline check: with the old label (log of summed views, months 2 to 7) the new code reproduces the stored 2020Q1 ridge results exactly (Spearman 0.2387, 0.2051, 0.2154).
- Fitted L4 settings (examples): theta and sigma_beta are re-estimated at every step.

{{params}}

## 1. Mean metrics per label, model and stage (20 quarters)

AUC is for the top 20%, hit rate is for the top 10% (realised base rate about 0.104). The last six rows are the stored months 2 to 7 run (label = log of summed views), for reference.

{{means}}

How large are the label differences? Paired over the 20 quarters (mean difference in AUC, standard error over quarters in brackets, not a formal test): L4 minus L3 is between -0.011 (0.007) and +0.004 (0.004) across the six model-stage cells, so L3 and L4 are not distinguishable. L4 minus L0 is -0.027 to -0.042 (standard errors 0.005 to 0.009), and L4 minus L2 is +0.004 to +0.043 (standard errors 0.007 to 0.011); L2 minus L0 is -0.032 to -0.072.

## 2. How alike the labels are

Spearman correlation between labels on the titles of each test quarter, averaged over quarters:

{{corr_q}}

The same on all {{n_test}} pooled: 

{{corr_pool}}

Share of a label's top 20% that is also in another label's top 20% (per quarter, averaged):

{{overlap}}

## 3. Source gains (differences between stages)

Mean over 20 quarters of the stage difference, per label. The last column is the stored months 2 to 7 run.

{{gains}}

Number of quarters out of 20 in which the gain was positive:

{{gains_pos}}

## 4. Launch strength (descriptive only)

Launch strength is log(views in months 1 and 2 + 0.5) minus log(fitted views in months 1 and 2 + 0.5) from the L4 model of each step. Zero means the first two months sat where the book's own level and decay predict. Tiers are quartiles of L4 over all {{n_test}} pooled. Spearman correlation of launch strength with L4: {{launch_corr}}.

By performance tier:

{{launch_tier}}

By year of release:

{{launch_year}}

What sits in each tier (views are Internet Archive views in months 1 to 12; slope is the shrunk book-specific decay slope beta, where larger means slower fading than the common curve):

{{zero_share}}

## 5. Where the results agree with the months 2 to 7 run, and where they differ

{{interpretation}}

## 6. Choices the record leaves open (all marked `# NOT IN RECORD:` in the code)

{{notinrecord}}
