# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD_MA |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | split200001 |
| n_surrogates | 1000 |

## VOD_MA

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.545 | 0.043 * | increasing |
| Before 2000-01 | 7 | Surrogate | -0.714 | 0.101 | no trend |
| From 2000-01 | 19 | Surrogate | +0.684 | 0.014 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.249 | 0.304 | no trend |
| Before 2000-01 | 7 | Surrogate | -0.524 | 0.296 | no trend |
| From 2000-01 | 19 | Surrogate | +0.240 | 0.472 | no trend |
