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
| Full record | 67 | Surrogate | +0.254 | 0.216 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.080 | 0.739 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.102 | 0.828 | no trend |
