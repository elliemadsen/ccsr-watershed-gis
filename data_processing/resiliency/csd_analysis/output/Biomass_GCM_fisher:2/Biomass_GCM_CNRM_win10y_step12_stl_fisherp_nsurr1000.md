# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.306 | 0.142 | no trend |
| Before 2030-12 | 36 | Surrogate | -0.559 | 0.022 * | decreasing |
| From 2030-12 | 31 | Surrogate | -0.445 | 0.277 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.136 | 0.498 | no trend |
| Before 2048-12 | 54 | Surrogate | -0.115 | 0.781 | no trend |
| From 2048-12 | 13 | Surrogate | +0.949 | 0.001 * | increasing |
