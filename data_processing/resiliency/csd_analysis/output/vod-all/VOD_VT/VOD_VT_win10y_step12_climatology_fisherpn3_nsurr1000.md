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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## VOD_VT

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 21 | Surrogate | -0.124 | 0.763 | no trend |
| Before 2002-06 | 6 | Surrogate | +1.000 | 0.008 * | increasing |
| 2002-06 – 2007-06 | 5 | Surrogate | +0.800 | 0.175 | no trend |
| From 2007-06 | 10 | Surrogate | -0.511 | 0.010 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 21 | Surrogate | -0.038 | 0.947 | no trend |
| Before 2001-06 | 5 | Surrogate | +1.000 | 0.033 * | increasing |
| 2001-06 – 2006-06 | 5 | Surrogate | -0.600 | 0.269 | no trend |
| From 2006-06 | 11 | Surrogate | +0.636 | 0.091 | no trend |
