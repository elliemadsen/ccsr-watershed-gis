# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | Var |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## Biomass_GCM

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.729 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.223 | 0.434 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.554 | 0.006 * | decreasing |
