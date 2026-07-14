# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GIMMS |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## LAI_GIMMS

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.132 | 0.790 | no trend |
| Before 1998-06 | 14 | Surrogate | +0.934 | 0.001 * | increasing |
| From 1998-06 | 12 | Surrogate | -0.394 | 0.431 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | -0.003 | 1.000 | no trend |
| Before 2002-06 | 18 | Surrogate | +0.229 | 0.462 | no trend |
| From 2002-06 | 8 | Surrogate | +0.571 | 0.059 | no trend |
