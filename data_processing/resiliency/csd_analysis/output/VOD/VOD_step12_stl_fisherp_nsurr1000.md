# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 30 | Surrogate | -0.094 | 0.716 | no trend |
| Before 2012-12 | 23 | Surrogate | -0.557 | 0.001 * | decreasing |
| From 2012-12 | 7 | Surrogate | +0.048 | 1.000 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 30 | Surrogate | -0.172 | 0.307 | no trend |
| Before 2000-12 | 11 | Surrogate | -0.527 | 0.206 | no trend |
| From 2000-12 | 19 | Surrogate | -0.532 | 0.034 * | decreasing |
