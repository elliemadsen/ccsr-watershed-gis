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
| Full record | 67 | Surrogate | -0.178 | 0.315 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.189 | 0.584 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.023 | 0.950 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.050 | 0.905 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.326 | 0.050 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.747 | 0.001 * | increasing |
