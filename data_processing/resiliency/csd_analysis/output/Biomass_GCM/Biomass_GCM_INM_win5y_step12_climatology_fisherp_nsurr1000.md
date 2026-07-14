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
| Full record | 72 | Surrogate | +0.011 | 0.964 | no trend |
| Before 2014-06 | 22 | Surrogate | +0.628 | 0.002 * | increasing |
| From 2014-06 | 50 | Surrogate | -0.123 | 0.506 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.075 | 0.582 | no trend |
| Before 2049-06 | 57 | Surrogate | +0.066 | 0.615 | no trend |
| From 2049-06 | 15 | Surrogate | +0.619 | 0.041 * | increasing |
