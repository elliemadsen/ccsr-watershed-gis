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
| split_mode | fisherpn3 |
| n_surrogates | 1000 |

## Biomass_GCM

### TAC

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.143 | 0.736 | no trend |
| Before 2037-12 | 43 | Surrogate | +0.535 | 0.025 * | increasing |
| 2037-12 – 2045-12 | 8 | Surrogate | +0.929 | 0.005 * | increasing |
| From 2045-12 | 16 | Surrogate | -0.950 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.281 | 0.462 | no trend |
| Before 2004-12 | 10 | Surrogate | +0.378 | 0.238 | no trend |
| 2004-12 – 2047-12 | 43 | Surrogate | +0.453 | 0.151 | no trend |
| From 2047-12 | 14 | Surrogate | -0.846 | 0.001 * | decreasing |
