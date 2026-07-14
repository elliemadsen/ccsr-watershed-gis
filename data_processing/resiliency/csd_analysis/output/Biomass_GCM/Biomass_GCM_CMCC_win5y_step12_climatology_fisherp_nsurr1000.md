# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.052 | 0.744 | no trend |
| Before 2053-06 | 61 | Surrogate | +0.117 | 0.558 | no trend |
| From 2053-06 | 11 | Surrogate | -0.782 | 0.009 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.048 | 0.877 | no trend |
| Before 2037-06 | 45 | Surrogate | -0.485 | 0.009 * | decreasing |
| From 2037-06 | 27 | Surrogate | -0.043 | 0.881 | no trend |
