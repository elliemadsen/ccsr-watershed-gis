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
| Full record | 67 | Surrogate | -0.181 | 0.365 | no trend |
| Before 2020-12 | 26 | Surrogate | -0.729 | 0.001 * | decreasing |
| From 2020-12 | 41 | Surrogate | +0.017 | 0.970 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.009 | 0.963 | no trend |
| Before 2048-12 | 54 | Surrogate | -0.015 | 0.972 | no trend |
| From 2048-12 | 13 | Surrogate | +0.923 | 0.001 * | increasing |
