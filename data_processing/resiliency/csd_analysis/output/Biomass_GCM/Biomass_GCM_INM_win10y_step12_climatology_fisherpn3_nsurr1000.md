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
| Full record | 67 | Surrogate | -0.150 | 0.464 | no trend |
| Before 2007-12 | 13 | Surrogate | +0.769 | 0.001 * | increasing |
| 2007-12 – 2028-12 | 21 | Surrogate | -0.752 | 0.001 * | decreasing |
| From 2028-12 | 33 | Surrogate | -0.500 | 0.108 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.215 | 0.314 | no trend |
| Before 2007-12 | 13 | Surrogate | +0.692 | 0.003 * | increasing |
| 2007-12 – 2023-12 | 16 | Surrogate | -0.917 | 0.001 * | decreasing |
| From 2023-12 | 38 | Surrogate | -0.189 | 0.690 | no trend |
