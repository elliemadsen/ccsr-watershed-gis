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
| Full record | 67 | Surrogate | +0.403 | 0.266 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.273 | 0.470 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.223 | 0.589 | no trend |
