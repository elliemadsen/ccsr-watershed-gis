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
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.180 | 0.715 | no trend |
| Before 2009-06 | 17 | Surrogate | -0.794 | 0.002 * | decreasing |
| From 2009-06 | 8 | Surrogate | +0.643 | 0.064 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.147 | 0.637 | no trend |
| Before 2004-06 | 12 | Surrogate | -0.394 | 0.197 | no trend |
| From 2004-06 | 13 | Surrogate | -0.641 | 0.019 * | decreasing |
