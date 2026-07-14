# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.016 | 0.931 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.848 | 0.001 * | decreasing |
| 2007-06 – 2017-06 | 10 | Surrogate | -1.000 | 0.001 * | decreasing |
| From 2017-06 | 47 | Surrogate | +0.088 | 0.735 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.049 | 0.801 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.905 | 0.001 * | decreasing |
| 2007-06 – 2027-06 | 20 | Surrogate | -0.526 | 0.023 * | decreasing |
| From 2027-06 | 37 | Surrogate | -0.450 | 0.016 * | decreasing |
