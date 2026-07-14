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
| Full record | 67 | Surrogate | -0.230 | 0.387 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.227 | 0.589 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.037 | 0.855 | no trend |
