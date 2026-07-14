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
| Full record | 72 | Surrogate | +0.011 | 0.966 | no trend |
| Before 2009-06 | 17 | Surrogate | +0.471 | 0.179 | no trend |
| 2009-06 – 2027-06 | 18 | Surrogate | -0.699 | 0.012 * | decreasing |
| From 2027-06 | 37 | Surrogate | -0.297 | 0.261 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.075 | 0.605 | no trend |
| Before 2009-06 | 17 | Surrogate | +0.235 | 0.520 | no trend |
| 2009-06 – 2027-06 | 18 | Surrogate | -0.712 | 0.002 * | decreasing |
| From 2027-06 | 37 | Surrogate | -0.240 | 0.296 | no trend |
