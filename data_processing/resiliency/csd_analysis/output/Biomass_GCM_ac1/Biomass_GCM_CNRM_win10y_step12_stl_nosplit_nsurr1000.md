# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | TAC |
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
| Full record | 67 | Surrogate | -0.306 | 0.146 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.572 | 0.003 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | -0.301 | 0.552 | no trend |
