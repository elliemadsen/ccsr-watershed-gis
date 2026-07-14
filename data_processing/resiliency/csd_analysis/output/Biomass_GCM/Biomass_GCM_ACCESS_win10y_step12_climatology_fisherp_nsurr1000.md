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
| Full record | 67 | Surrogate | +0.117 | 0.674 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.620 | 0.014 * | decreasing |
| From 2019-12 | 42 | Surrogate | -0.185 | 0.486 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.243 | 0.410 | no trend |
| Before 2019-12 | 25 | Surrogate | -0.687 | 0.006 * | decreasing |
| From 2019-12 | 42 | Surrogate | -0.159 | 0.558 | no trend |
