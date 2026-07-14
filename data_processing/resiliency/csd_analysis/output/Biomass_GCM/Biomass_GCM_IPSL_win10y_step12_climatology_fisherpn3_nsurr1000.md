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
| Full record | 67 | Surrogate | +0.035 | 0.869 | no trend |
| Before 2025-12 | 31 | Surrogate | -0.480 | 0.138 | no trend |
| 2025-12 – 2054-12 | 29 | Surrogate | -0.778 | 0.001 * | decreasing |
| From 2054-12 | 7 | Surrogate | +0.048 | 1.000 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.159 | 0.489 | no trend |
| Before 2004-12 | 10 | Surrogate | -0.867 | 0.001 * | decreasing |
| 2004-12 – 2024-12 | 20 | Surrogate | -0.600 | 0.002 * | decreasing |
| From 2024-12 | 37 | Surrogate | -0.408 | 0.240 | no trend |
