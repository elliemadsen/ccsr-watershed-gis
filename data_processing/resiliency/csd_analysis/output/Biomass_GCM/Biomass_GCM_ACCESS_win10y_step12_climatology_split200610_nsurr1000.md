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
| Full record | 67 | Surrogate | +0.117 | 0.628 | no trend |
| Before 2006-10 | 12 | Surrogate | -0.636 | 0.037 * | decreasing |
| From 2006-10 | 55 | Surrogate | +0.242 | 0.407 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.243 | 0.411 | no trend |
| Before 2006-10 | 12 | Surrogate | -0.424 | 0.100 | no trend |
| From 2006-10 | 55 | Surrogate | +0.255 | 0.421 | no trend |
