# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | Biomass_GCM |
| analysis | Var |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## Biomass_GCM

### Model: ACCESS

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.281 | 0.515 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.133 | 0.730 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.465 | 0.002 * | decreasing |

### Model: CMCC

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.050 | 0.910 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.326 | 0.057 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.747 | 0.001 * | increasing |

### Model: CNRM

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.136 | 0.495 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.542 | 0.077 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.102 | 0.656 | no trend |

### Model: INM

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.228 | 0.350 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.197 | 0.652 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.237 | 0.603 | no trend |

### Model: IPSL

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.152 | 0.737 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.223 | 0.452 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.554 | 0.003 * | decreasing |

### Model: mean

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.038 | 0.869 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.023 | 0.913 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.176 | 0.543 | no trend |
