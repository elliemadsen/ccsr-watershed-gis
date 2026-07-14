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
| Full record | 67 | Surrogate | +0.097 | 0.598 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.303 | 0.197 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.116 | 0.644 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.207 | 0.430 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.352 | 0.049 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.308 | 0.209 | no trend |
