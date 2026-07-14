# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | split200610 |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.180 | 0.748 | no trend |
| Before 2006-10 | 15 | Surrogate | -0.771 | 0.001 * | decreasing |
| From 2006-10 | 10 | Surrogate | +0.644 | 0.054 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.147 | 0.627 | no trend |
| Before 2006-10 | 15 | Surrogate | +0.105 | 0.790 | no trend |
| From 2006-10 | 10 | Surrogate | -0.600 | 0.007 * | decreasing |
