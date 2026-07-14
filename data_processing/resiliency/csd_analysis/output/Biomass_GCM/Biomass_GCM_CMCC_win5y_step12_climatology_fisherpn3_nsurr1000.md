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
| Full record | 72 | Surrogate | +0.052 | 0.725 | no trend |
| Before 2005-06 | 13 | Surrogate | -0.692 | 0.026 * | decreasing |
| 2005-06 – 2053-06 | 48 | Surrogate | +0.255 | 0.083 | no trend |
| From 2053-06 | 11 | Surrogate | -0.782 | 0.009 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.048 | 0.866 | no trend |
| Before 2038-06 | 46 | Surrogate | -0.449 | 0.026 * | decreasing |
| 2038-06 – 2045-06 | 7 | Surrogate | -1.000 | 0.007 * | decreasing |
| From 2045-06 | 19 | Surrogate | -0.275 | 0.441 | no trend |
