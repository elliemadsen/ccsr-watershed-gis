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
| Full record | 72 | Surrogate | -0.020 | 0.883 | no trend |
| Before 2057-06 | 65 | Surrogate | -0.183 | 0.218 | no trend |
| From 2057-06 | 7 | Surrogate | -0.810 | 0.019 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.019 | 0.934 | no trend |
| Before 2047-06 | 55 | Surrogate | -0.025 | 0.952 | no trend |
| From 2047-06 | 17 | Surrogate | +0.632 | 0.068 | no trend |
