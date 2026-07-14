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
| Full record | 67 | Surrogate | +0.035 | 0.857 | no trend |
| Before 2002-12 | 8 | Surrogate | -0.571 | 0.227 | no trend |
| From 2002-12 | 59 | Surrogate | +0.068 | 0.704 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.159 | 0.502 | no trend |
| Before 2002-12 | 8 | Surrogate | -0.786 | 0.026 * | decreasing |
| From 2002-12 | 59 | Surrogate | +0.213 | 0.445 | no trend |
