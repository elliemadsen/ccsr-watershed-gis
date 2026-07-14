# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD_VT |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | split200501 |
| n_surrogates | 1000 |

## VOD_VT

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 21 | Surrogate | -0.124 | 0.766 | no trend |
| Before 2005-01 | 9 | Surrogate | +0.556 | 0.065 | no trend |
| From 2005-01 | 12 | Surrogate | -0.636 | 0.019 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 21 | Surrogate | -0.038 | 0.949 | no trend |
| Before 2005-01 | 9 | Surrogate | -0.333 | 0.569 | no trend |
| From 2005-01 | 12 | Surrogate | +0.697 | 0.035 * | increasing |
