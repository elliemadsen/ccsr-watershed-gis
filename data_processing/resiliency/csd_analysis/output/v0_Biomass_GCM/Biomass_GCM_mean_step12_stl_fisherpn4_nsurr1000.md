# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | mean |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherpn4 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.046 | 0.622 | no trend |
| Before 1999-06 | 7 | Surrogate | +0.524 | 0.260 | no trend |
| 1999-06 – 2012-06 | 13 | Surrogate | +0.897 | 0.001 * | increasing |
| 2012-06 – 2022-06 | 10 | Surrogate | -0.778 | 0.007 * | decreasing |
| From 2022-06 | 42 | Surrogate | -0.310 | 0.084 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.031 | 0.831 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.486 | 0.097 | no trend |
| 2007-06 – 2022-06 | 15 | Surrogate | -0.867 | 0.001 * | decreasing |
| 2022-06 – 2050-06 | 28 | Surrogate | -0.138 | 0.486 | no trend |
| From 2050-06 | 14 | Surrogate | +0.802 | 0.005 * | increasing |
