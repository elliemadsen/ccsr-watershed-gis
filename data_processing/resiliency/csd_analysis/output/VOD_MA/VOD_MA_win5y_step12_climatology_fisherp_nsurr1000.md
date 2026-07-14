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
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD_MA

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.545 | 0.040 * | increasing |
| Before 1999-12 | 6 | Surrogate | -0.600 | 0.236 | no trend |
| From 1999-12 | 20 | Surrogate | +0.716 | 0.011 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.249 | 0.306 | no trend |
| Before 2014-12 | 21 | Surrogate | +0.333 | 0.202 | no trend |
| From 2014-12 | 5 | Surrogate | -0.800 | 0.125 | no trend |
