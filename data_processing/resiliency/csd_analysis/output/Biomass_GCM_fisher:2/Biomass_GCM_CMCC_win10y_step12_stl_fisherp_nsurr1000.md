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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.178 | 0.366 | no trend |
| Before 2049-12 | 55 | Surrogate | -0.269 | 0.357 | no trend |
| From 2049-12 | 12 | Surrogate | -0.909 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.050 | 0.907 | no trend |
| Before 2030-12 | 36 | Surrogate | -0.410 | 0.002 * | decreasing |
| From 2030-12 | 31 | Surrogate | +0.746 | 0.001 * | increasing |
