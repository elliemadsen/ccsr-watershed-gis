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
| Full record | 67 | Surrogate | +0.312 | 0.292 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.824 | 0.001 * | decreasing |
| From 2011-12 | 50 | Surrogate | +0.381 | 0.049 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.082 | 0.863 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.971 | 0.001 * | decreasing |
| From 2011-12 | 50 | Surrogate | +0.316 | 0.455 | no trend |
