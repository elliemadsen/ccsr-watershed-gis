# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GIMMS |
| analysis | all |
| model | all |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## LAI_GIMMS

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.292 | 0.524 | no trend |
| Before 2002-06 | 18 | Surrogate | +0.908 | 0.001 * | increasing |
| From 2002-06 | 8 | Surrogate | +0.571 | 0.092 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 26 | Surrogate | +0.034 | 0.880 | no trend |
| Before 2002-06 | 18 | Surrogate | +0.033 | 0.931 | no trend |
| From 2002-06 | 8 | Surrogate | +0.857 | 0.016 * | increasing |
