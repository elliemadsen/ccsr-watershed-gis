# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## LAI_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.017 | 0.924 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.318 | 0.446 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.084 | 0.870 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.201 | 0.607 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.413 | 0.026 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.651 | 0.018 * | increasing |
