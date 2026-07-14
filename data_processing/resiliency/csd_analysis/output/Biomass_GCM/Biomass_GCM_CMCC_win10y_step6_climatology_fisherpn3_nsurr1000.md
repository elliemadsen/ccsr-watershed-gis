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
| Full record | 133 | Surrogate | +0.315 | 0.224 | no trend |
| Before 2010-12 | 32 | Surrogate | -0.770 | 0.001 * | decreasing |
| 2010-12 – 2052-06 | 83 | Surrogate | +0.406 | 0.005 * | increasing |
| From 2052-06 | 18 | Surrogate | -0.895 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 133 | Surrogate | +0.085 | 0.834 | no trend |
| Before 2012-06 | 35 | Surrogate | -0.862 | 0.001 * | decreasing |
| 2012-06 – 2026-06 | 28 | Surrogate | -0.519 | 0.107 | no trend |
| From 2026-06 | 70 | Surrogate | +0.588 | 0.048 * | increasing |
