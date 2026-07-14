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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.115 | 0.533 | no trend |
| Before 2048-06 | 56 | Surrogate | +0.229 | 0.114 | no trend |
| From 2048-06 | 16 | Surrogate | -0.600 | 0.002 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.175 | 0.444 | no trend |
| Before 2049-06 | 57 | Surrogate | +0.291 | 0.203 | no trend |
| From 2049-06 | 15 | Surrogate | -0.524 | 0.104 | no trend |
