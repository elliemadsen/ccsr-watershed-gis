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
| Full record | 67 | Surrogate | -0.181 | 0.391 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.534 | 0.055 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.198 | 0.632 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.009 | 0.970 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.485 | 0.016 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.162 | 0.449 | no trend |
