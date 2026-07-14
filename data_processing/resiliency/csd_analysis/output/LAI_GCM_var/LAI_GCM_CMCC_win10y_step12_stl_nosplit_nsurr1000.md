# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | Var |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## LAI_GCM

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.201 | 0.620 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.413 | 0.024 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.651 | 0.016 * | increasing |
