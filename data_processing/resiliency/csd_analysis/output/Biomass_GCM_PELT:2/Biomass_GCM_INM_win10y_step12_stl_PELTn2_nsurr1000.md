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
| split_mode | PELTn2 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.034 | 0.828 | no trend |
| Before 2024-12 | 30 | Surrogate | +0.149 | 0.771 | no trend |
| From 2024-12 | 37 | Surrogate | -0.057 | 0.863 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.228 | 0.334 | no trend |
| Before 2014-12 | 20 | Surrogate | +0.642 | 0.017 * | increasing |
| From 2014-12 | 47 | Surrogate | -0.010 | 0.971 | no trend |
