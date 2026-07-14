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
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.210 | 0.114 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.110 | 0.548 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.376 | 0.181 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.038 | 0.859 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.023 | 0.918 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.176 | 0.537 | no trend |
