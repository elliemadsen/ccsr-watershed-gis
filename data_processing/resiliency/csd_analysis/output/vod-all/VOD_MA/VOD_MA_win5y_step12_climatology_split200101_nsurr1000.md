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
| split_mode | split200101 |
| n_surrogates | 1000 |

## VOD_MA

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.545 | 0.042 * | increasing |
| Before 2001-01 | 8 | Surrogate | -0.714 | 0.125 | no trend |
| From 2001-01 | 18 | Surrogate | +0.647 | 0.027 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.249 | 0.316 | no trend |
| Before 2001-01 | 8 | Surrogate | -0.357 | 0.488 | no trend |
| From 2001-01 | 18 | Surrogate | +0.229 | 0.552 | no trend |
