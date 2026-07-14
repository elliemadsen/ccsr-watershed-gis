# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | VOD_VT |
| analysis | all |
| model | all |
| window_years | 5 |
| step | 12 |
| detrend | climatology |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## VOD_VT

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | +0.080 | 0.790 | no trend |
| Before 2011-12 | 17 | Surrogate | +0.529 | 0.004 * | increasing |
| From 2011-12 | 8 | Surrogate | +0.143 | 0.817 | no trend |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 25 | Surrogate | -0.167 | 0.456 | no trend |
| Before 2000-12 | 6 | Surrogate | +1.000 | 0.007 * | increasing |
| From 2000-12 | 19 | Surrogate | +0.076 | 0.763 | no trend |
