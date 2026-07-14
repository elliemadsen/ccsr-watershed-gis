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
| Full record | 67 | Surrogate | -0.150 | 0.487 | no trend |
| Before 2006-10 | 12 | Surrogate | +0.727 | 0.006 * | increasing |
| From 2006-10 | 55 | Surrogate | -0.398 | 0.003 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.215 | 0.318 | no trend |
| Before 2006-10 | 12 | Surrogate | +0.636 | 0.021 * | increasing |
| From 2006-10 | 55 | Surrogate | -0.316 | 0.059 | no trend |
