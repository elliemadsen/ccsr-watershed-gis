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
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD_ME

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.553 | 0.002 * | increasing |
| Before 2004-12 | 10 | Surrogate | +0.911 | 0.002 * | increasing |
| From 2004-12 | 15 | Surrogate | +0.695 | 0.019 * | increasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.153 | 0.566 | no trend |
| Before 2004-12 | 10 | Surrogate | +0.378 | 0.116 | no trend |
| From 2004-12 | 15 | Surrogate | +0.486 | 0.179 | no trend |
