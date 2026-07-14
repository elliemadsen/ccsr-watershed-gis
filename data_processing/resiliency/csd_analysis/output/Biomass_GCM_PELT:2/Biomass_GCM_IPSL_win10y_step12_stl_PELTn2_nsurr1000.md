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
| split_mode | PELTn2 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.707 | no trend |
| Before 2024-12 | 30 | Surrogate | -0.379 | 0.091 | no trend |
| From 2024-12 | 37 | Surrogate | -0.330 | 0.314 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.727 | no trend |
| Before 2024-12 | 30 | Surrogate | -0.476 | 0.013 * | decreasing |
| From 2024-12 | 37 | Surrogate | -0.498 | 0.024 * | decreasing |
