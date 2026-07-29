# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD_ME |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## VOD_ME

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.553 | 0.003 * | increasing |
| First half (before 2006-12) | 12 | Surrogate | +0.545 | 0.176 | no trend |
| Second half (from 2006-12) | 13 | Surrogate | +0.641 | 0.051 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.153 | 0.579 | no trend |
| First half (before 2006-12) | 12 | Surrogate | +0.030 | 0.946 | no trend |
| Second half (from 2006-12) | 13 | Surrogate | +0.538 | 0.149 | no trend |
