# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | split200610 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.312 | 0.240 | no trend |
| Before 2006-10 | 12 | Surrogate | -0.697 | 0.003 * | decreasing |
| From 2006-10 | 55 | Surrogate | +0.467 | 0.030 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.082 | 0.839 | no trend |
| Before 2006-10 | 12 | Surrogate | -0.939 | 0.001 * | decreasing |
| From 2006-10 | 55 | Surrogate | +0.345 | 0.292 | no trend |
