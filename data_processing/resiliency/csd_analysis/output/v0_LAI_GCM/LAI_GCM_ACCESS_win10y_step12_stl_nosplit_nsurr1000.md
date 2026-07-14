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
| Full record | 67 | Surrogate | +0.120 | 0.780 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.523 | 0.062 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.444 | 0.002 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.254 | 0.536 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.367 | 0.206 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.497 | 0.001 * | decreasing |
