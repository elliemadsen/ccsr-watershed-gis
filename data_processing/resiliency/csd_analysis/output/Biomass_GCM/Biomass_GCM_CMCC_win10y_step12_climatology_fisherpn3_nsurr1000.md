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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.312 | 0.244 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.824 | 0.001 * | decreasing |
| 2011-12 – 2052-12 | 41 | Surrogate | +0.412 | 0.015 * | increasing |
| From 2052-12 | 9 | Surrogate | -1.000 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.082 | 0.839 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.971 | 0.001 * | decreasing |
| 2011-12 – 2023-12 | 12 | Surrogate | -0.212 | 0.472 | no trend |
| From 2023-12 | 38 | Surrogate | +0.644 | 0.026 * | increasing |
