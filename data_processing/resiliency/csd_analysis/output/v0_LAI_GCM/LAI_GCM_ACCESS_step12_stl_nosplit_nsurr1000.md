# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## LAI_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.142 | 0.554 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.349 | 0.034 * | increasing |
| Second half (from 2028-06) | 36 | Surrogate | -0.311 | 0.017 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.224 | 0.498 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.190 | 0.437 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | -0.375 | 0.031 * | decreasing |
