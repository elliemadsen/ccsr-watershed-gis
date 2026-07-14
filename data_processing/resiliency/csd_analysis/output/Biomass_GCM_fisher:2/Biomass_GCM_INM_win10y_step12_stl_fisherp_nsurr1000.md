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
| Full record | 67 | Surrogate | -0.034 | 0.834 | no trend |
| Before 2016-12 | 22 | Surrogate | +0.818 | 0.001 * | increasing |
| From 2016-12 | 45 | Surrogate | +0.065 | 0.727 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.228 | 0.317 | no trend |
| Before 2012-12 | 18 | Surrogate | +0.699 | 0.007 * | increasing |
| From 2012-12 | 49 | Surrogate | -0.088 | 0.639 | no trend |
