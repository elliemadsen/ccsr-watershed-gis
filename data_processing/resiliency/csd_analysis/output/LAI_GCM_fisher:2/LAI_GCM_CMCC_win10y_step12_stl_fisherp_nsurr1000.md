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
| Full record | 67 | Surrogate | +0.017 | 0.937 | no trend |
| Before 2033-12 | 39 | Surrogate | +0.422 | 0.209 | no trend |
| From 2033-12 | 28 | Surrogate | +0.471 | 0.211 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.201 | 0.591 | no trend |
| Before 2035-12 | 41 | Surrogate | -0.615 | 0.001 * | decreasing |
| From 2035-12 | 26 | Surrogate | +0.834 | 0.001 * | increasing |
