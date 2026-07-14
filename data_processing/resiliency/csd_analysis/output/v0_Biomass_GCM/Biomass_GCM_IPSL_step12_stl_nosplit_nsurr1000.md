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
| Full record | 72 | Surrogate | +0.106 | 0.730 | no trend |
| First half (before 2028-06) | 36 | Surrogate | -0.108 | 0.703 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | -0.356 | 0.279 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.044 | 0.882 | no trend |
| First half (before 2028-06) | 36 | Surrogate | -0.216 | 0.320 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | -0.460 | 0.003 * | decreasing |
