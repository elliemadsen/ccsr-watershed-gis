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
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.127 | 0.824 | no trend |
| Before 2000-06 | 8 | Surrogate | -0.857 | 0.006 * | decreasing |
| From 2000-06 | 17 | Surrogate | +0.838 | 0.001 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.080 | 0.807 | no trend |
| Before 2003-06 | 11 | Surrogate | -0.927 | 0.001 * | decreasing |
| From 2003-06 | 14 | Surrogate | +0.275 | 0.240 | no trend |
