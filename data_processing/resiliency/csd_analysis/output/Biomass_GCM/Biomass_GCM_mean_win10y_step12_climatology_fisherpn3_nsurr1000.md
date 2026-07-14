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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.097 | 0.610 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.303 | 0.164 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.116 | 0.629 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.207 | 0.482 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.352 | 0.050 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.308 | 0.221 | no trend |
