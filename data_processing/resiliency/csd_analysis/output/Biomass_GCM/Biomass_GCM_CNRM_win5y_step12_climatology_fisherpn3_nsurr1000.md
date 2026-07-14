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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.020 | 0.891 | no trend |
| Before 2040-06 | 48 | Surrogate | -0.124 | 0.486 | no trend |
| 2040-06 – 2057-06 | 17 | Surrogate | -0.824 | 0.001 * | decreasing |
| From 2057-06 | 7 | Surrogate | -0.810 | 0.029 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.019 | 0.936 | no trend |
| Before 2029-06 | 37 | Surrogate | -0.219 | 0.579 | no trend |
| 2029-06 – 2046-06 | 17 | Surrogate | +0.632 | 0.025 * | increasing |
| From 2046-06 | 18 | Surrogate | +0.621 | 0.067 | no trend |
