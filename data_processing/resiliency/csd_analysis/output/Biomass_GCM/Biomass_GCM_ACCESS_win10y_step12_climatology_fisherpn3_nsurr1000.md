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
| Full record | 67 | Surrogate | +0.117 | 0.667 | no trend |
| Before 2009-12 | 15 | Surrogate | -0.771 | 0.003 * | decreasing |
| 2009-12 – 2033-12 | 24 | Surrogate | +0.638 | 0.012 * | increasing |
| From 2033-12 | 28 | Surrogate | -0.249 | 0.097 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.243 | 0.432 | no trend |
| Before 2015-12 | 21 | Surrogate | -0.619 | 0.002 * | decreasing |
| 2015-12 – 2034-12 | 19 | Surrogate | +0.895 | 0.001 * | increasing |
| From 2034-12 | 27 | Surrogate | -0.293 | 0.053 | no trend |
