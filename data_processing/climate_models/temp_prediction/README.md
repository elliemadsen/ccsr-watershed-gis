# Temperature Prediction Analysis

This pipeline extends the climate change analysis to temperature projections, following the same delta-change approach used for precipitation. It processes **minimum (tasmin)** and **maximum (tasmax)** temperature data separately from the same five GCMs from the NASA NEX-GDDP-CMIP6 v2 dataset.

## Model Selection

The analysis uses the same five representative GCM models selected for precipitation:

| Climate Quadrant | Model Name    |
| ---------------- | ------------- |
| Hot-Wet          | ACCESS-ESM1-5 |
| Hot-Dry          | IPSL-CM6A-LR  |
| Warm-Wet         | CMCC-ESM2     |
| Warm-Dry         | CNRM-CM6-1    |
| Median           | INM-CM5-0     |

## Downscaling Protocol (Delta-Change Approach)

The GCM temperature projections from NEX-GDDP-CMIP6 v2 are at ~25 km (0.25°) resolution. The delta-change method downscales these projections by computing how much future temperature changes relative to a historical baseline within the same GCM (to preserve model-specific biases), then applying that change ratio to the observed high-resolution GRIDMET data.

**Three Time Periods:**

1. **Historical period (1990-2019)**: GCM modeled historical data at grid points (denominator for change factors)
2. **Future period (2035-2064)**: GCM future projections at grid points (numerator for change factors)
3. **Present baseline period (2015-2025)**: High-resolution GRIDMET observed rasters (30m) that get multiplied by change factors

### Step 1: Compute seasonal means at the GCM grid scale

For each GCM, aggregate daily minimum and maximum temperature separately to seasonal averages (DJF, MAM, JJA, SON), then compute the multi-year mean of each season for:

- **Historical period**: 1990-2019 (GCM modeled historical at 6 grid points)
- **Future period**: 2035-2064 (GCM future projection at 6 grid points)

### Step 2: Compute temperature change factors

For each GCM and each season, compute the change factor at each GCM grid cell:

```
CF_temp = GCM_future (2035–2064) / GCM_historical (1990-2019)
```

### Step 3: Apply change factors to GRIDMET baseline

**Interpolation Method**: Inverse Distance Weighting (IDW) with power=2

The change factors are interpolated from the sparse GCM grid (~6 points covering the watershed) to the 30m resolution using IDW.

For each GCM and each season, multiply the present baseline GRIDMET raster (2015-2025 @ 30m) by the interpolated change factor. This is done separately for minimum and maximum temperature:

```
temp_min_future_30m (2035-2064) = temp_min_baseline_30m (2015-2025) × CF_tasmin
temp_max_future_30m (2035-2064) = temp_max_baseline_30m (2015-2025) × CF_tasmax
```

---

## Implementation

### Scripts

All scripts are located in `data_processing/climate_models/temp_prediction/` and use the conda `geo` environment.

1. **1_compute_seasonal_means.py**
   - Computes GCM historical seasonal means (1990-2019) for each model and variable (tasmin, tasmax)
   - Computes GCM future seasonal means (2035-2064) for each model and variable
   - Handles unit conversion: GCM temperature is already in Kelvin (K), no conversion needed
   - Input: GCM CSVs from `data/climate_models/raw/daily_1990_2015/` and `daily_2015_2065/`
     - `Catskills_{model}_tasmin_historical_daily_avg.csv`
     - `Catskills_{model}_tasmax_historical_daily_avg.csv`
     - `Catskills_{model}_tasmin_ssp370_daily_avg.csv`
     - `Catskills_{model}_tasmax_ssp370_daily_avg.csv`
   - Output: Seasonal means in `data/climate_models/temp_prediction/1_seasonal_means/`
   - Note: GRIDMET baseline (2015-2025) rasters already exist at 30m resolution for both tmmn (min) and tmmx (max)

2. **2_compute_change_factors.py**
   - Computes change factors (CF = GCM_future/GCM_historical) for each GCM, season, and variable (tasmin, tasmax)
   - Keeps GCM biases consistent by comparing within the same model
   - Input: Seasonal means from step 1 in `data/climate_models/temp_prediction/1_seasonal_means/`
   - Output: Change factors in `data/climate_models/temp_prediction/2_change_factors/`
     - CSV files: `change_factors_{model}_tasmin_ssp370.csv`, `change_factors_{model}_tasmax_ssp370.csv`
     - GeoJSON files: `change_factors_{model}_tasmin_ssp370.geojson`, `change_factors_{model}_tasmax_ssp370.geojson`

3. **3_apply_change_factors.py**
   - Applies change factors to present baseline (2015-2025) using IDW interpolation
   - Interpolates change factors from 6 GCM grid points to 30m resolution
   - Multiplies interpolated change factors by baseline rasters (separately for min and max temp)
   - Outputs use EPSG:32618 (WGS84 / UTM zone 18N)
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

- **Coordinate Reference System**: All rasters use EPSG:32618 (WGS 84 / UTM zone 18N)
- **IDW power parameter**: Set to 2 (inverse square distance) for balance between smoothness and local influence
- **Output resolution**: 30m to match GRIDMET baseline and watershed analysis requirements

## Comparison with Precipitation

This temperature pipeline mirrors the precipitation analysis with these differences:

1. **Variables**: Minimum and maximum temperature (tasmin, tasmax) vs precipitation (pr)
2. **Aggregation**: Seasonal **averages** (temperature) vs seasonal **totals** (precipitation)
3. **GRIDMET variables**: `tmmn` (min temp) and `tmmx` (max temp) vs `pr` (precipitation)
4. **Units**: Kelvin (K) vs mm

### Running the Pipeline

To generate future temperature projections:

```bash
# 1. Process GRIDMET baseline data (if not already done)
cd data_processing/temp
python process_gridmet.py

# 2. Compute seasonal means for GCM historical and future periods
cd ../climate_models/temp_prediction
python 1_compute_seasonal_means.py

# 3. Compute change factors
python 2_compute_change_factors.py

# 4. Apply change factors to GRIDMET baseline
python 3_apply_change_factors.py
```

### Results Summary

Change factors represent the multiplicative change in temperature (in Kelvin) between GCM historical (1990-2019) and future (2035-2064) periods under SSP3-7.0 emissions scenario.

#### Change Factor Summary by Model and Season

**Minimum Temperature (tasmin):**

| Model         | DJF    | MAM    | JJA    | SON    |
| ------------- | ------ | ------ | ------ | ------ |
| ACCESS-ESM1-5 | +0.19% | +0.63% | +0.20% | +0.33% |
| IPSL-CM6A-LR  | +0.53% | +0.66% | +0.59% | +0.86% |
| CMCC-ESM2     | +0.78% | +0.43% | +0.86% | +0.86% |
| CNRM-CM6-1    | +0.88% | +0.51% | +0.63% | +0.52% |
| INM-CM5-0     | +0.93% | +0.68% | +0.59% | +0.62% |

**Maximum Temperature (tasmax):**

| Model         | DJF    | MAM    | JJA    | SON    |
| ------------- | ------ | ------ | ------ | ------ |
| ACCESS-ESM1-5 | +0.32% | +0.95% | +0.97% | +0.88% |
| IPSL-CM6A-LR  | +0.20% | +0.89% | +0.62% | +0.93% |
| CMCC-ESM2     | +0.62% | +0.64% | +0.40% | +0.60% |
| CNRM-CM6-1    | +0.73% | +0.52% | +0.65% | +0.60% |
| INM-CM5-0     | +0.64% | +0.65% | +0.44% | +0.61% |

**Key Findings:**

- **Overall warming**: All models show temperature increases across all seasons for both minimum and maximum temperatures
- **Seasonal variation**:
  - Spring (MAM) and Fall (SON) generally show stronger warming signals
  - Summer (JJA) shows variable warming across models
  - Winter (DJF) shows lower warming for most models except INM-CM5-0 and CNRM-CM6-1 for tasmin
- **Model spread**: Change factors range from +0.19% to +0.97%, indicating moderate warming
- **Temperature asymmetry**: Maximum temperatures (tasmax) show slightly stronger warming trends in spring/summer compared to minimum temperatures (tasmin)
- **Hottest projections**: CMCC-ESM2 and INM-CM5-0 show the strongest minimum temperature warming in summer/fall
