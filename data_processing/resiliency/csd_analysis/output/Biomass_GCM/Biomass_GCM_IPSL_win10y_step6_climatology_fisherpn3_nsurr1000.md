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
| Full record | 133 | Surrogate | +0.034 | 0.848 | no trend |
| Before 2024-12 | 60 | Surrogate | -0.505 | 0.101 | no trend |
| 2024-12 – 2048-12 | 48 | Surrogate | -0.684 | 0.002 * | decreasing |
| From 2048-12 | 25 | Surrogate | +0.527 | 0.126 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.177 | 0.482 | no trend |
| Before 2004-12 | 20 | Surrogate | -0.832 | 0.001 * | decreasing |
| 2004-12 – 2024-12 | 40 | Surrogate | -0.574 | 0.001 * | decreasing |
| From 2024-12 | 73 | Surrogate | -0.393 | 0.286 | no trend |
