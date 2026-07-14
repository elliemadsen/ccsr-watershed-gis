# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.108 | 0.654 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.254 | 0.029 * | increasing |
| Second half (from 2028-06) | 36 | Surrogate | -0.375 | 0.088 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.206 | 0.502 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.121 | 0.469 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | -0.381 | 0.039 * | decreasing |
