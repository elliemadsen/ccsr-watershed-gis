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
| Full record | 67 | Surrogate | +0.152 | 0.732 | no trend |
| Before 2041-12 | 47 | Surrogate | +0.362 | 0.351 | no trend |
| From 2041-12 | 20 | Surrogate | -0.842 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.737 | no trend |
| Before 2036-12 | 42 | Surrogate | +0.168 | 0.711 | no trend |
| From 2036-12 | 25 | Surrogate | -0.760 | 0.001 * | decreasing |
