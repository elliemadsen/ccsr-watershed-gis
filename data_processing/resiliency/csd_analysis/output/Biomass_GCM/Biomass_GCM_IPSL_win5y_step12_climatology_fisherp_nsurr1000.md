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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.016 | 0.951 | no trend |
| Before 2027-06 | 35 | Surrogate | -0.472 | 0.019 * | decreasing |
| From 2027-06 | 37 | Surrogate | -0.387 | 0.038 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.049 | 0.799 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.905 | 0.001 * | decreasing |
| From 2007-06 | 57 | Surrogate | +0.076 | 0.762 | no trend |
