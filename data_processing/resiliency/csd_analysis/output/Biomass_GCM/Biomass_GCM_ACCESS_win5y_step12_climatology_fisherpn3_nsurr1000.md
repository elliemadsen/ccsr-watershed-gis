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
| Full record | 72 | Surrogate | +0.115 | 0.540 | no trend |
| Before 2002-06 | 10 | Surrogate | +0.644 | 0.054 | no trend |
| 2002-06 – 2048-06 | 46 | Surrogate | +0.318 | 0.074 | no trend |
| From 2048-06 | 16 | Surrogate | -0.600 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.175 | 0.451 | no trend |
| Before 2030-06 | 38 | Surrogate | +0.121 | 0.499 | no trend |
| 2030-06 – 2048-06 | 18 | Surrogate | -0.752 | 0.008 * | decreasing |
| From 2048-06 | 16 | Surrogate | -0.517 | 0.136 | no trend |
