# Study 2R: simulation tests of the outcome pipeline

Simulated worlds only (no real data): 2,600 works, print and ebook, quasi-Poisson-type overdispersion (phi 3), seasonality, trends, closure months; 700 treated works
with a lift injected in months 0 to +2 (both formats), 200 placebo works per test, the pipeline of `_lib2r.run_tests`.

## Lift 0%: 700 tests, 700 usable and not too sparse; mean tau -0.001 (log(1+lift) = 0.000); share p < 0.05 = 0.060; mean p 0.482; median placebos 200
- PASS: lift 0: mean tau near 0 (-0.001)
- PASS: lift 0: about 5% of tests reach p < 0.05 (0.060 among 700 tests, 3.5 SE band 0.021 to 0.079)
- PASS: lift 0: p roughly uniform (rank p is discrete, KS statistic below 0.06) (KS 0.041)
- PASS: lift 0: placebo-year share at or above the treated z is about 0.5 on average (0.480 over 700 tests)
## Lift 10%: 700 tests, 700 usable and not too sparse; mean tau 0.098 (log(1+lift) = 0.095); share p < 0.05 = 0.173; mean p 0.319; median placebos 200
  expected detection from the null z spread and the shift of z: 0.163
- PASS: lift 10%: detection rate close to the shortcut prediction (observed 0.173, expected 0.163)
  (descriptive) detection at +10%: 0.173
- PASS: lift +10%: mean tau near log 1.10 (0.098)
## Lift 30%: 700 tests, 700 usable and not too sparse; mean tau 0.260 (log(1+lift) = 0.262); share p < 0.05 = 0.514; mean p 0.136; median placebos 200
  expected detection from the null z spread and the shift of z: 0.513
- PASS: lift 30%: detection rate close to the shortcut prediction (observed 0.514, expected 0.513)
- PASS: lift +30%: mean tau near log 1.30 (0.260)
- PASS: detection rises with the lift (+30% well above the 5% null) (0.514)
- PASS: H1 slope recovered by the clustered bootstrap (truth 0.10) (est 0.105, 95% interval 0.083 to 0.128)
- PASS: H1 slope with no true slope: one-sided p not tiny (est 0.017, p 0.072)
- PASS: H2 difference recovered (truth about 0.10 * (log2 mean(dur>=6) - log2 mean(dur<=2)) ) (diff 0.315, interval 0.247 to 0.384)
- PASS: Hansen threshold recovered (step after 5 weeks) (gamma 5, bootstrap interval 2.0 to 6.0, LR set [5])
- PASS: BH helper returns q-values ([0.004  0.2667 0.9    0.008 ])

Result: ALL PASS
