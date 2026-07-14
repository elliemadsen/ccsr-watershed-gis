# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.103 | 0.254 | no trend |
| First half (before 2028-06) | 36 | Surrogate | +0.105 | 0.373 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | +0.013 | 0.953 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 72 | Surrogate | -0.044 | 0.901 | no trend |
| First half (before 2028-06) | 36 | Surrogate | -0.286 | 0.116 | no trend |
| Second half (from 2028-06) | 36 | Surrogate | +0.556 | 0.050 * | increasing |
