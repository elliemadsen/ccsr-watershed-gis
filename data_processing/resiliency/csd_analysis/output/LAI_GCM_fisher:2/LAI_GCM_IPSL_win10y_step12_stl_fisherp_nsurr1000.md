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
| Full record | 67 | Surrogate | +0.440 | 0.249 | no trend |
| Before 2044-12 | 50 | Surrogate | +0.522 | 0.050 * | increasing |
| From 2044-12 | 17 | Surrogate | -0.794 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.403 | 0.294 | no trend |
| Before 2037-12 | 43 | Surrogate | +0.488 | 0.081 | no trend |
| From 2037-12 | 24 | Surrogate | -0.703 | 0.001 * | decreasing |
