# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## LAI_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.003 | 0.982 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.089 | 0.550 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | +0.137 | 0.737 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.137 | 0.710 | no trend |
| First half (before 2028-06) | 36 | Surrogate | -0.400 | 0.055 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | +0.644 | 0.013 * | increasing |
