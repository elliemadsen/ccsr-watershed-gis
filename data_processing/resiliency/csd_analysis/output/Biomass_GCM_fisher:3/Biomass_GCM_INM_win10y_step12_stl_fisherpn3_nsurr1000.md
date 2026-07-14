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
| Full record | 67 | Surrogate | -0.034 | 0.840 | no trend |
| Before 2015-12 | 21 | Surrogate | +0.819 | 0.001 * | increasing |
| 2015-12 – 2024-12 | 9 | Surrogate | -0.944 | 0.001 * | decreasing |
| From 2024-12 | 37 | Surrogate | -0.057 | 0.873 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.228 | 0.348 | no trend |
| Before 2010-12 | 16 | Surrogate | +0.683 | 0.009 * | increasing |
| 2010-12 – 2024-12 | 14 | Surrogate | -0.868 | 0.001 * | decreasing |
| From 2024-12 | 37 | Surrogate | -0.153 | 0.736 | no trend |
