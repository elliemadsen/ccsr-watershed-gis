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
| Full record | 133 | Surrogate | -0.139 | 0.481 | no trend |
| Before 2009-06 | 29 | Surrogate | +0.709 | 0.001 * | increasing |
| 2009-06 – 2030-12 | 43 | Surrogate | -0.495 | 0.125 | no trend |
| From 2030-12 | 61 | Surrogate | -0.588 | 0.006 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | -0.216 | 0.313 | no trend |
| Before 2009-12 | 30 | Surrogate | +0.678 | 0.001 * | increasing |
| 2009-12 – 2023-12 | 28 | Surrogate | -0.820 | 0.001 * | decreasing |
| From 2023-12 | 75 | Surrogate | -0.204 | 0.653 | no trend |
