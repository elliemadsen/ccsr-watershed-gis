# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | all |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | fisherp |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.143 | 0.719 | no trend |
| Before 2044-12 | 50 | Surrogate | +0.402 | 0.126 | no trend |
| From 2044-12 | 17 | Surrogate | -0.941 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.281 | 0.501 | no trend |
| Before 2047-12 | 53 | Surrogate | +0.408 | 0.226 | no trend |
| From 2047-12 | 14 | Surrogate | -0.846 | 0.001 * | decreasing |
