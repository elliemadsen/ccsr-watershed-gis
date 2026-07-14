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
| Full record | 67 | Surrogate | +0.152 | 0.688 | no trend |
| Before 2014-12 | 20 | Surrogate | -0.221 | 0.508 | no trend |
| 2014-12 – 2045-12 | 31 | Surrogate | +0.776 | 0.001 * | increasing |
| From 2045-12 | 16 | Surrogate | -0.817 | 0.001 * | decreasing |

### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.731 | no trend |
| Before 2011-12 | 17 | Surrogate | -0.603 | 0.020 * | decreasing |
| 2011-12 – 2037-12 | 26 | Surrogate | +0.563 | 0.014 * | increasing |
| From 2037-12 | 24 | Surrogate | -0.754 | 0.001 * | decreasing |
