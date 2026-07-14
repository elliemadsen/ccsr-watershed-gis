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
| Full record | 67 | Surrogate | -0.150 | 0.493 | no trend |
| Before 2002-12 | 8 | Surrogate | +0.857 | 0.005 * | increasing |
| From 2002-12 | 59 | Surrogate | -0.350 | 0.016 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.215 | 0.314 | no trend |
| Before 2002-12 | 8 | Surrogate | +0.786 | 0.032 * | increasing |
| From 2002-12 | 59 | Surrogate | -0.313 | 0.082 | no trend |
