I want a chart that has four columns [ one per season - Winter (DJF), Spring (MAM), Summer (JJA), Fall (SON) ]
And five rows - one for each model. Each quadrant of the chart (season x model) will show five variables - temp, precip, ET, LAI.
Each will be a colored bar, with a length that corresponds to that variables value for said season and model.

Below is the data.

Step 1: process this data into a json that stores it all.
Step 2: write a python script that reads from that json and produces the diagram.

For LAI and ET, suggest whether its better to use max, mean or median and justify the logic.

-- Change Factors --

Precipitation (seasonal total):

| Model         | Quadrant | DJF         | MAM         | JJA        | SON         |
| ------------- | -------- | ----------- | ----------- | ---------- | ----------- |
| ACCESS-ESM1-5 | Hot-Wet  | 1.07 (+7%)  | 1.14 (+14%) | 1.00 (0%)  | 1.13 (+13%) |
| IPSL-CM6A-LR  | Hot-Dry  | 1.10 (+10%) | 1.02 (+2%)  | 0.98 (−2%) | 0.98 (−2%)  |
| CMCC-ESM2     | Warm-Wet | 1.14 (+14%) | 1.11 (+11%) | 1.03 (+3%) | 0.97 (−3%)  |
| CNRM-CM6-1    | Warm-Dry | 1.07 (+7%)  | 1.03 (+3%)  | 1.00 (+0%) | 0.99 (−1%)  |
| INM-CM5-0     | Median   | 1.05 (+5%)  | 1.02 (+2%)  | 1.07 (+7%) | 1.00 (+0%)  |

Temperature (seasonal avg - max daily temp):

| Model         | DJF     | MAM     | JJA     | SON     |
| ------------- | ------- | ------- | ------- | ------- |
| ACCESS-ESM1-5 | +0.88 K | +2.73 K | +2.91 K | +2.55 K |
| IPSL-CM6A-LR  | +0.56 K | +2.56 K | +1.87 K | +2.67 K |
| CMCC-ESM2     | +1.70 K | +1.84 K | +1.19 K | +1.73 K |
| CNRM-CM6-1    | +2.00 K | +1.50 K | +1.95 K | +1.74 K |
| INM-CM5-0     | +1.76 K | +1.87 K | +1.32 K | +1.76 K |

LAI:

| Model                | Season | Min    | Max    | Mean   | Median |
| -------------------- | ------ | ------ | ------ | ------ | ------ |
| ACCESS_EMS1_5_SSP370 | DJF    | 0.0000 | 1.1123 | 0.8610 | 0.8547 |
| ACCESS_EMS1_5_SSP370 | MAM    | 0.0000 | 1.4239 | 1.1477 | 1.1417 |
| ACCESS_EMS1_5_SSP370 | JJA    | 0.0000 | 1.3768 | 1.0334 | 1.0203 |
| ACCESS_EMS1_5_SSP370 | SON    | 0.0000 | 1.2522 | 0.9294 | 0.9174 |
| CMCC_EMS2_SSP370     | DJF    | 0.0000 | 1.1469 | 0.9376 | 0.9427 |
| CMCC_EMS2_SSP370     | MAM    | 0.0000 | 1.3096 | 1.1089 | 1.1150 |
| CMCC_EMS2_SSP370     | JJA    | 0.0000 | 1.3590 | 1.1122 | 1.1150 |
| CMCC_EMS2_SSP370     | SON    | 0.0000 | 1.2421 | 1.0034 | 1.0038 |
| CNRM_CM6_1_SSP370    | DJF    | 0.0000 | 1.1169 | 0.9198 | 0.9253 |
| CNRM_CM6_1_SSP370    | MAM    | 0.0000 | 1.2667 | 1.0655 | 1.0706 |
| CNRM_CM6_1_SSP370    | JJA    | 0.0000 | 1.3210 | 1.0563 | 1.0589 |
| CNRM_CM6_1_SSP370    | SON    | 0.0000 | 1.2340 | 0.9820 | 0.9885 |
| INM_CM5_0_SSP370     | DJF    | 0.0000 | 1.2664 | 0.9608 | 0.9505 |
| INM_CM5_0_SSP370     | MAM    | 0.0000 | 1.3898 | 1.1147 | 1.1101 |
| INM_CM5_0_SSP370     | JJA    | 0.0000 | 1.4824 | 1.1012 | 1.0833 |
| INM_CM5_0_SSP370     | SON    | 0.0000 | 1.3938 | 1.0227 | 1.0042 |
| IPSL_CM6A_LR_SSP370  | DJF    | 0.0000 | 1.2523 | 0.9501 | 0.9506 |
| IPSL_CM6A_LR_SSP370  | MAM    | 0.0000 | 1.4835 | 1.2132 | 1.2199 |
| IPSL_CM6A_LR_SSP370  | JJA    | 0.0000 | 1.4459 | 1.1222 | 1.1219 |
| IPSL_CM6A_LR_SSP370  | SON    | 0.0000 | 1.3509 | 1.0156 | 1.0130 |

ET:

| Model                | Season | Min    | Max    | Mean   | Median |
| -------------------- | ------ | ------ | ------ | ------ | ------ |
| ACCESS_EMS1_5_SSP370 | DJF    | 1.1090 | 1.6150 | 1.2251 | 1.1112 |
| ACCESS_EMS1_5_SSP370 | MAM    | 0.9951 | 1.4022 | 1.2081 | 1.1678 |
| ACCESS_EMS1_5_SSP370 | JJA    | 0.8803 | 1.0175 | 1.0044 | 1.0056 |
| ACCESS_EMS1_5_SSP370 | SON    | 1.0387 | 1.1955 | 1.1211 | 1.1212 |
| CMCC_EMS2_SSP370     | DJF    | 2.5891 | 4.9253 | 3.4659 | 3.4028 |
| CMCC_EMS2_SSP370     | MAM    | 1.0047 | 1.3996 | 1.1876 | 1.1594 |
| CMCC_EMS2_SSP370     | JJA    | 0.9422 | 1.0441 | 1.0320 | 1.0311 |
| CMCC_EMS2_SSP370     | SON    | 1.0106 | 1.1525 | 1.0854 | 1.0856 |
| CNRM_CM6_1_SSP370    | DJF    | 1.6191 | 3.5332 | 2.2112 | 1.8951 |
| CNRM_CM6_1_SSP370    | MAM    | 0.8241 | 1.2457 | 1.0481 | 1.0457 |
| CNRM_CM6_1_SSP370    | JJA    | 0.9209 | 1.0053 | 0.9943 | 0.9953 |
| CNRM_CM6_1_SSP370    | SON    | 1.0167 | 1.1272 | 1.0621 | 1.0611 |
| INM_CM5_0_SSP370     | DJF    | 1.6177 | 2.7924 | 2.3654 | 2.5875 |
| INM_CM5_0_SSP370     | MAM    | 0.9996 | 1.3969 | 1.2175 | 1.2460 |
| INM_CM5_0_SSP370     | JJA    | 0.9234 | 1.0539 | 1.0260 | 1.0252 |
| INM_CM5_0_SSP370     | SON    | 1.0387 | 1.2139 | 1.1380 | 1.1387 |
| IPSL_CM6A_LR_SSP370  | DJF    | 0.2353 | 0.9131 | 0.3256 | 0.2983 |
| IPSL_CM6A_LR_SSP370  | MAM    | 1.0260 | 1.3604 | 1.1701 | 1.1588 |
| IPSL_CM6A_LR_SSP370  | JJA    | 0.9056 | 1.0188 | 0.9951 | 0.9931 |
| IPSL_CM6A_LR_SSP370  | SON    | 0.9658 | 1.1068 | 1.0324 | 1.0319 |
