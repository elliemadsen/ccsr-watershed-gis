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
| split_mode | nosplit |
| n_surrogates | 1000 |

## VOD_MA

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.545 | 0.029 * | increasing |
| First half (before 2006-12) | 13 | Surrogate | -0.205 | 0.742 | no trend |
| Second half (from 2006-12) | 13 | Surrogate | +0.308 | 0.545 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.249 | 0.319 | no trend |
| First half (before 2006-12) | 13 | Surrogate | -0.179 | 0.480 | no trend |
| Second half (from 2006-12) | 13 | Surrogate | +0.231 | 0.539 | no trend |
