# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | split200610 |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.127 | 0.824 | no trend |
| Before 2006-10 | 15 | Surrogate | -0.543 | 0.083 | no trend |
| From 2006-10 | 10 | Surrogate | +0.733 | 0.021 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.080 | 0.801 | no trend |
| Before 2006-10 | 15 | Surrogate | -0.448 | 0.195 | no trend |
| From 2006-10 | 10 | Surrogate | +0.289 | 0.453 | no trend |
