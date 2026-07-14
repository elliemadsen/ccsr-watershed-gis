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
| Full record | 67 | Surrogate | +0.120 | 0.758 | no trend |
| Before 2026-12 | 32 | Surrogate | +0.508 | 0.066 | no trend |
| From 2026-12 | 35 | Surrogate | -0.469 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.254 | 0.545 | no trend |
| Before 2047-12 | 53 | Surrogate | +0.395 | 0.292 | no trend |
| From 2047-12 | 14 | Surrogate | -0.868 | 0.001 * | decreasing |
