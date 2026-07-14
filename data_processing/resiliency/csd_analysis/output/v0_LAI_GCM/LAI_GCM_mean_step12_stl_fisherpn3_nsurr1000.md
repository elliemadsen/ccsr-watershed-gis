# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | all |
| model | mean |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## LAI_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.026 | 0.800 | no trend |
| Before 2006-06 | 14 | Surrogate | -0.604 | 0.064 | no trend |
| 2006-06 – 2022-06 | 16 | Surrogate | -0.800 | 0.002 * | decreasing |
| From 2022-06 | 42 | Surrogate | -0.275 | 0.313 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.020 | 0.833 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.562 | 0.003 * | decreasing |
| 2007-06 – 2022-06 | 15 | Surrogate | -0.943 | 0.001 * | decreasing |
| From 2022-06 | 42 | Surrogate | -0.278 | 0.177 | no trend |
