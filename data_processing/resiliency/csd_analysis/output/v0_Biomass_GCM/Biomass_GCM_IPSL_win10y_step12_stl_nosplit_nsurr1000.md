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
| Full record | 67 | Surrogate | +0.152 | 0.680 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.136 | 0.596 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.376 | 0.289 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.736 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.223 | 0.412 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.554 | 0.005 * | decreasing |
