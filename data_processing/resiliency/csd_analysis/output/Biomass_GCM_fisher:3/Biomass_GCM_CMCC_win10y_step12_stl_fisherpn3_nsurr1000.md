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
| Full record | 67 | Surrogate | -0.178 | 0.336 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.309 | 0.332 | no trend |
| 2011-12 – 2049-12 | 38 | Surrogate | -0.519 | 0.090 | no trend |
| From 2049-12 | 12 | Surrogate | -0.909 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.050 | 0.918 | no trend |
| Before 2013-12 | 19 | Surrogate | -0.450 | 0.205 | no trend |
| 2013-12 – 2028-12 | 15 | Surrogate | -0.829 | 0.002 * | decreasing |
| From 2028-12 | 33 | Surrogate | +0.742 | 0.001 * | increasing |
