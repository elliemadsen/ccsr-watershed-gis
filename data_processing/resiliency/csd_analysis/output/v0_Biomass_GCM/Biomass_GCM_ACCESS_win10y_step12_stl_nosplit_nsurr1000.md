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
| Full record | 67 | Surrogate | +0.143 | 0.723 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.375 | 0.173 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.651 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.281 | 0.473 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.133 | 0.740 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.465 | 0.001 * | decreasing |
