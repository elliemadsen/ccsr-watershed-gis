# Temperature Prediction Analysis

This pipeline extends the GCM analysis to temperature projections. It processes minimum (tasmin) and maximum (tasmax) temperature data separately from the same five GCMs from the NASA NEX-GDDP-CMIP6 v2 dataset.

## Climate Models

The analysis uses the same five representative GCM models selected for precipitation:

| Climate Quadrant | Model Name    |
| ---------------- | ------------- |
| Hot-Wet          | ACCESS-ESM1-5 |
| Hot-Dry          | IPSL-CM6A-LR  |
| Warm-Wet         | CMCC-ESM2     |
| Warm-Dry         | CNRM-CM6-1    |
| Median           | INM-CM5-0     |

## Downscaling Protocol (Delta-Change Approach)

The GCM temperature projections from NEX-GDDP-CMIP6 v2 are at ~25 km resolution. The delta-change method downscales these projections by computing how much future temperature changes relative to a historical baseline within the same GCM, then applying that change ratio to the observed high-resolution GRIDMET data.

**Three Time Periods:**

1. **Historical period (1990-2019)**: GCM modeled historical data at grid points
2. **Future period (2035-2064)**: GCM future projections at grid points
3. **Present baseline period (2015-2025)**: High-resolution GRIDMET observed rasters (30m) that get multiplied by change factors

### Step 1: Compute seasonal means at the GCM grid scale

For each GCM, aggregate daily minimum and maximum temperature separately to seasonal averages (DJF, MAM, JJA, SON), then compute the multi-year mean of each season for:

- **Historical period**: 1990-2019 (GCM modeled historical at 6 grid points)
- **Future period**: 2035-2064 (GCM future projection at 6 grid points)

### Step 2: Compute temperature change factors

For each GCM and each season, compute the additive change factor at each GCM grid cell:

```
ΔT = GCM_future (2035–2064) - GCM_historical (1990-2019)
```

### Step 3: Apply change factors to GRIDMET baseline

**Interpolation Method**: Inverse Distance Weighting (IDW) with power=2

The change factors are interpolated from the sparse GCM grid (~6 points covering the watershed) to the 30m resolution using IDW.

For each GCM and each season, add the interpolated change factors to the present baseline GRIDMET raster (2015-2025 @ 30m). This is done separately for minimum and maximum temperature:

```
temp_min_future_30m (2035-2064) = temp_min_baseline_30m (2015-2025) + ΔT_tasmin
temp_max_future_30m (2035-2064) = temp_max_baseline_30m (2015-2025) + ΔT_tasmax
```

---

## Implementation

### Scripts

All scripts are located in `data_processing/climate_models/temp_prediction/` and use the conda `geo` environment.

1. **1_compute_seasonal_means.py**
   - Input: GCM CSVs from `data/climate_models/raw/daily_1990_2015/` and `daily_2015_2065/`
     - `Catskills_{model}_tasmin_historical_daily_avg.csv`
     - `Catskills_{model}_tasmax_historical_daily_avg.csv`
     - `Catskills_{model}_tasmin_ssp370_daily_avg.csv`
     - `Catskills_{model}_tasmax_ssp370_daily_avg.csv`
   - Output: Seasonal means in `data/climate_models/temp_prediction/1_seasonal_means/`

2. **2_compute_change_factors.py**
   - Input: Seasonal means from step 1 in `data/climate_models/temp_prediction/1_seasonal_means/`
   - Output: Change factors in `data/climate_models/temp_prediction/2_change_factors/`
     - CSV files: `change_factors_{model}_tasmin_ssp370.csv`, `change_factors_{model}_tasmax_ssp370.csv`
     - GeoJSON files: `change_factors_{model}_tasmin_ssp370.geojson`, `change_factors_{model}_tasmax_ssp370.geojson`

3. **3_apply_change_factors.py**
   - Input: Change factors (GeoJSON) from `data/climate_models/temp_prediction/2_change_factors/` and GRIDMET baseline rasters (2015-2025) from `data/temp/processed/seasonal/`
     - Baseline files: `temp_min_final_30m_2015-2025_{season}.tif`, `temp_max_final_30m_2015-2025_{season}.tif`
   - Output: Future projection rasters (2035-2064) in `data/climate_models/temp_prediction/3_future_projections/`
     - `temp_min_future_{model}_2035-2064_{season}_30m.tif`
     - `temp_max_future_{model}_2035-2064_{season}_30m.tif`

**GRIDMET Baseline Processing Script:**

Located in `data_processing/temp/`:

- **process_gridmet.py**: Downloads GRIDMET minimum (tmmn) and maximum (tmmx) temperature data from 2015-2025, processes them separately, clips to watershed, aggregates to seasonal and monthly averages, and reprojects to 30m resolution in UTM Zone 18N (EPSG:32618)

### Data Paths

```
ccsr-watershed-gis/
├── data/
│   ├── climate_models/
│   │   ├── raw/
│   │   │   ├── daily_1990_2015/   # GCM historical daily temperature (CSV)
│   │   │   │   ├── Catskills_{model}_tasmin_historical_daily_avg.csv
│   │   │   │   └── Catskills_{model}_tasmax_historical_daily_avg.csv
│   │   │   └── daily_2015_2065/   # GCM future daily temperature (CSV)
│   │   │       ├── Catskills_{model}_tasmin_ssp370_daily_avg.csv
│   │   │       └── Catskills_{model}_tasmax_ssp370_daily_avg.csv
│   │   └── temp_prediction/
│   │       ├── 1_seasonal_means/  # Step 1 output: seasonal means (tasmin, tasmax)
│   │       ├── 2_change_factors/  # Step 2 output: change factors (CSV & GeoJSON)
│   │       └── 3_future_projections/  # Step 3 output: future temperature rasters (30m)
│   └── temp/
│       ├── raw/
│       │   ├── min/               # GRIDMET tmmn NetCDF files (minimum temperature)
│       │   └── max/               # GRIDMET tmmx NetCDF files (maximum temperature)
│       └── processed/
│           └── seasonal/          # GRIDMET baseline rasters (30m, 2015-2025)
│               ├── temp_min_final_30m_2015-2025_{season}.tif
│               └── temp_max_final_30m_2015-2025_{season}.tif
├── data_processing/
│   ├── climate_models/
│   │   └── temp_prediction/       # This directory: GCM processing scripts
│   └── temp/
│       └── process_gridmet.py     # GRIDMET baseline processing
```

### Technical Notes

## Comparison with Precipitation

This temperature pipeline mirrors the precipitation analysis with these key differences:

1. **Variables**: Minimum and maximum temperature (tasmin, tasmax) vs precipitation (pr)
2. **Aggregation**: Seasonal **averages** (temperature) vs seasonal **totals** (precipitation)
3. **GRIDMET variables**: `tmmn` (min temp) and `tmmx` (max temp) vs `pr` (precipitation)
4. **Units**: Kelvin (K) vs mm
5. **Change factor methodology**: ADDITIVE (ΔT = future - historical) vs MULTIPLICATIVE (CF = future/historical)
   - Temperature uses absolute differences because warming is additive and percentages are misleading with Kelvin's non-arbitrary zero
   - Precipitation uses ratios because percentage changes are meaningful for a ratio-scale variable

### Results Summary

Additive temperature change factors (ΔT in Kelvin) represent the absolute temperature increase between GCM historical (1990-2019) and future (2035-2064) periods under SSP3-7.0 emissions scenario.

#### Temperature Change Summary by Model and Season

**Minimum Temperature (tasmin):**

| Model         | DJF     | MAM     | JJA     | SON     |
| ------------- | ------- | ------- | ------- | ------- |
| ACCESS-ESM1-5 | +0.51 K | +1.74 K | +0.56 K | +0.92 K |
| IPSL-CM6A-LR  | +1.39 K | +1.81 K | +1.69 K | +2.37 K |
| CMCC-ESM2     | +2.07 K | +1.19 K | +2.47 K | +2.39 K |
| CNRM-CM6-1    | +2.32 K | +1.40 K | +1.79 K | +1.44 K |
| INM-CM5-0     | +2.46 K | +1.87 K | +1.68 K | +1.72 K |

**Maximum Temperature (tasmax):**

| Model         | DJF     | MAM     | JJA     | SON     |
| ------------- | ------- | ------- | ------- | ------- |
| ACCESS-ESM1-5 | +0.88 K | +2.73 K | +2.91 K | +2.55 K |
| IPSL-CM6A-LR  | +0.56 K | +2.56 K | +1.87 K | +2.67 K |
| CMCC-ESM2     | +1.70 K | +1.84 K | +1.19 K | +1.73 K |
| CNRM-CM6-1    | +2.00 K | +1.50 K | +1.95 K | +1.74 K |
| INM-CM5-0     | +1.76 K | +1.87 K | +1.32 K | +1.76 K |

**Key Findings:**

- **Overall warming**: All models show temperature increases across all seasons for both minimum and maximum temperatures, ranging from **+0.51 K to +2.91 K**
- **Seasonal variation**:
  - **Spring (MAM)** and **Summer (JJA)** show the strongest warming signals for maximum temperatures (up to +2.91 K)
  - **Winter (DJF)** shows variable warming: ACCESS-ESM1-5 projects modest warming (+0.51-0.88 K), while INM-CM5-0 and CNRM-CM6-1 project stronger winter warming (+2.00-2.46 K)
  - **Fall (SON)** shows consistent warming across all models (+0.92 to +2.67 K)
- **Model spread**: Substantial variation between models, with ACCESS-ESM1-5 (Hot-Wet quadrant) projecting the smallest winter/summer minimum temperature increases, while CMCC-ESM2, CNRM-CM6-1, and INM-CM5-0 project larger warming
- **Temperature asymmetry**:
  - Maximum temperatures show stronger warming in spring/summer for ACCESS-ESM1-5 and IPSL-CM6A-LR
  - Minimum temperatures show stronger warming in winter/fall for CMCC-ESM2, CNRM-CM6-1, and INM-CM5-0
