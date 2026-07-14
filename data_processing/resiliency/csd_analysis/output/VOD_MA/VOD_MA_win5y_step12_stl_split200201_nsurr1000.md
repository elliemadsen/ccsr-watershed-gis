# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD_MA |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | split200201 |
| n_surrogates | 1000 |

## VOD_MA

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.335 | 0.368 | no trend |
| Before 2002-01 | 9 | Surrogate | -0.833 | 0.003 * | decreasing |
| From 2002-01 | 17 | Surrogate | +0.456 | 0.189 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.009 | 0.977 | no trend |
| Before 2002-01 | 9 | Surrogate | -0.444 | 0.416 | no trend |
| From 2002-01 | 17 | Surrogate | +0.132 | 0.743 | no trend |
