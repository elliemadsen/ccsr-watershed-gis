# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | TAC |
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
| Full record | 67 | Surrogate | +0.120 | 0.788 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.523 | 0.048 * | increasing |
| Second half (from 2027-12) | 34 | Surrogate | -0.444 | 0.001 * | decreasing |
