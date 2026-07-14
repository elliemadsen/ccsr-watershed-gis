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
| split_mode | split200212 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.312 | 0.238 | no trend |
| Before 2002-12 | 8 | Surrogate | -0.571 | 0.181 | no trend |
| From 2002-12 | 59 | Surrogate | +0.500 | 0.036 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.082 | 0.839 | no trend |
| Before 2002-12 | 8 | Surrogate | -1.000 | 0.002 * | decreasing |
| From 2002-12 | 59 | Surrogate | +0.338 | 0.275 | no trend |
