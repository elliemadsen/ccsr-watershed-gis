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
| Full record | 67 | Surrogate | -0.178 | 0.356 | no trend |
| Before 2029-12 | 35 | Surrogate | +0.150 | 0.643 | no trend |
| From 2029-12 | 32 | Surrogate | +0.093 | 0.785 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.050 | 0.914 | no trend |
| Before 2024-12 | 30 | Surrogate | -0.200 | 0.381 | no trend |
| From 2024-12 | 37 | Surrogate | +0.745 | 0.001 * | increasing |
