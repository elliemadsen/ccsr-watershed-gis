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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.150 | 0.474 | no trend |
| Before 2009-12 | 15 | Surrogate | +0.810 | 0.001 * | increasing |
| From 2009-12 | 52 | Surrogate | -0.329 | 0.074 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.215 | 0.306 | no trend |
| Before 2009-12 | 15 | Surrogate | +0.752 | 0.002 * | increasing |
| From 2009-12 | 52 | Surrogate | -0.238 | 0.094 | no trend |
