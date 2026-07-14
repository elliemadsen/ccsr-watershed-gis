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
| Full record | 67 | Surrogate | +0.143 | 0.723 | no trend |
| Before 2009-12 | 15 | Surrogate | -0.600 | 0.065 | no trend |
| From 2009-12 | 52 | Surrogate | -0.163 | 0.575 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.281 | 0.505 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.507 | 0.043 * | decreasing |
| From 2019-12 | 42 | Surrogate | -0.168 | 0.497 | no trend |
