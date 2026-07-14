# CSD Analysis Report

## Run parameters

| Parameter | Value |
| --- | --- |
| data | LAI_GCM |
| analysis | Var |
| model | all |
| window_years | 10 |
| step | 12 |
| detrend | stl |
| significance | surrogate |
| split_mode | nosplit |
| n_surrogates | 1000 |

## LAI_GCM

### Model: ACCESS

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.254 | 0.574 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.367 | 0.210 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.497 | 0.001 * | decreasing |

### Model: CMCC

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.201 | 0.610 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.413 | 0.029 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.651 | 0.014 * | increasing |

### Model: CNRM

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.009 | 0.947 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.485 | 0.016 * | decreasing |
| Second half (from 2027-12) | 34 | Surrogate | +0.162 | 0.442 | no trend |

### Model: INM

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | -0.230 | 0.402 | no trend |
| First half (before 2027-12) | 33 | Surrogate | -0.227 | 0.573 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | +0.037 | 0.851 | no trend |

### Model: IPSL

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.403 | 0.278 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.273 | 0.449 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.223 | 0.589 | no trend |

### Model: mean

#### Var

| Period | n | Test | tau | p | Trend |
| --- | --- | --- | --- | --- | --- |
| Full record | 67 | Surrogate | +0.119 | 0.267 | no trend |
| First half (before 2027-12) | 33 | Surrogate | +0.106 | 0.620 | no trend |
| Second half (from 2027-12) | 34 | Surrogate | -0.301 | 0.284 | no trend |
