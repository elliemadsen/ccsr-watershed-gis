# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 6 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.106 | 0.678 | no trend |
| Before 2009-12 | 30 | Surrogate | -0.766 | 0.001 * | decreasing |
| 2009-12 – 2033-12 | 48 | Surrogate | +0.658 | 0.003 * | increasing |
| From 2033-12 | 55 | Surrogate | -0.234 | 0.109 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.249 | 0.439 | no trend |
| Before 2017-12 | 46 | Surrogate | -0.629 | 0.006 * | decreasing |
| 2017-12 – 2029-12 | 24 | Surrogate | +0.855 | 0.001 * | increasing |
| From 2029-12 | 63 | Surrogate | -0.456 | 0.077 | no trend |
