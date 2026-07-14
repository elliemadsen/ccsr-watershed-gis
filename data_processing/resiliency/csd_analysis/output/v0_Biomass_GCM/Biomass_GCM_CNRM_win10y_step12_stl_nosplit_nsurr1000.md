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
| split_mode | nosplit |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.306 | 0.131 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.572 | 0.007 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | -0.301 | 0.548 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.136 | 0.507 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.542 | 0.089 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.102 | 0.658 | no trend |
