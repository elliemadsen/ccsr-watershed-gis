# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD |
| analysis | all |
| model | all |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 30 | Surrogate | +0.021 | 0.970 | no trend |
| Before 2002-12 | 13 | Surrogate | -0.795 | 0.003 * | decreasing |
| From 2002-12 | 17 | Surrogate | +0.544 | 0.059 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 30 | Surrogate | -0.094 | 0.796 | no trend |
| Before 2000-12 | 11 | Surrogate | -0.855 | 0.003 * | decreasing |
| From 2000-12 | 19 | Surrogate | +0.368 | 0.174 | no trend |
