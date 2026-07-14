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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.118 | 0.691 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.580 | 0.033 * | decreasing |
| From 2019-12 | 42 | Surrogate | +0.447 | 0.003 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.064 | 0.885 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.693 | 0.003 * | decreasing |
| From 2019-12 | 42 | Surrogate | +0.431 | 0.024 * | increasing |
