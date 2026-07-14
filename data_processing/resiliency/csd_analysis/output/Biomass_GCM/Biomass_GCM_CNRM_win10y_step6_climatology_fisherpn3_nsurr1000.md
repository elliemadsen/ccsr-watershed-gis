# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 6 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.114 | 0.702 | no trend |
| Before 2004-12 | 20 | Surrogate | +0.305 | 0.300 | no trend |
| 2004-12 – 2018-06 | 27 | Surrogate | -0.823 | 0.001 * | decreasing |
| From 2018-06 | 86 | Surrogate | +0.468 | 0.001 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.051 | 0.891 | no trend |
| Before 2022-06 | 55 | Surrogate | -0.669 | 0.006 * | decreasing |
| 2022-06 – 2027-06 | 10 | Surrogate | -1.000 | 0.001 * | decreasing |
| From 2027-06 | 68 | Surrogate | +0.390 | 0.012 * | increasing |
