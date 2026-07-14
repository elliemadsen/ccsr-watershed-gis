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
| Full record | 67 | Surrogate | +0.035 | 0.838 | no trend |
| Before 2024-12 | 30 | Surrogate | -0.549 | 0.061 | no trend |
| From 2024-12 | 37 | Surrogate | -0.369 | 0.312 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.159 | 0.520 | no trend |
| Before 2024-12 | 30 | Surrogate | -0.536 | 0.002 * | decreasing |
| From 2024-12 | 37 | Surrogate | -0.408 | 0.241 | no trend |
