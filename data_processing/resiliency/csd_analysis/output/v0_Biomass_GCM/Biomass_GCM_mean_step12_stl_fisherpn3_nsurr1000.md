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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.046 | 0.614 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.143 | 0.804 | no trend |
| 2007-06 – 2022-06 | 15 | Surrogate | -0.752 | 0.006 * | decreasing |
| From 2022-06 | 42 | Surrogate | -0.310 | 0.085 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | +0.031 | 0.839 | no trend |
| Before 2007-06 | 15 | Surrogate | -0.486 | 0.114 | no trend |
| 2007-06 – 2022-06 | 15 | Surrogate | -0.867 | 0.001 * | decreasing |
| From 2022-06 | 42 | Surrogate | -0.164 | 0.391 | no trend |
