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
| split_mode | fisherp |
| n_surrogates | 1000 |

## LAI_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.056 | 0.736 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.212 | 0.338 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.169 | 0.524 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.119 | 0.268 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.106 | 0.640 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.301 | 0.295 | no trend |
