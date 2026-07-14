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
| Full record | 67 | Surrogate | +0.118 | 0.722 | no trend |
| Before 2016-12 | 22 | Surrogate | -0.472 | 0.176 | no trend |
| 2016-12 – 2047-12 | 31 | Surrogate | +0.725 | 0.001 * | increasing |
| From 2047-12 | 14 | Surrogate | +0.319 | 0.465 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.064 | 0.903 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.693 | 0.004 * | decreasing |
| 2019-12 – 2048-12 | 29 | Surrogate | +0.438 | 0.205 | no trend |
| From 2048-12 | 13 | Surrogate | +0.641 | 0.013 * | increasing |
