# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.306 | 0.139 | no trend |
| Before 2017-12 | 23 | Surrogate | -0.613 | 0.030 * | decreasing |
| 2017-12 – 2040-12 | 23 | Surrogate | +0.810 | 0.001 * | increasing |
| From 2040-12 | 21 | Surrogate | -0.343 | 0.416 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.136 | 0.511 | no trend |
| Before 2022-12 | 28 | Surrogate | -0.582 | 0.048 * | decreasing |
| 2022-12 – 2047-12 | 25 | Surrogate | +0.520 | 0.096 | no trend |
| From 2047-12 | 14 | Surrogate | +0.912 | 0.001 * | increasing |
