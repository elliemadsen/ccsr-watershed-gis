# Climate Change Analysis

The vulnerability framework is extended to evaluate how spatial patterns of nutrient and sediment loss risk shift under future climate conditions. This analysis uses five GCMs from the NASA NEX-GDDP-CMIP6 v2 dataset, each selected to represent a distinct climate trajectory.

## 6.1 GCM Selection Rationale

Twenty-one GCMs from the NEX-GDDP v2 archive were evaluated, and five representative models were selected based on their position in the temperature-precipitation change space for the Cannonsville watershed region. Each model represents one of five quadrants:

| Climate Quadrant | Model Name    |
| ---------------- | ------------- |
| Hot-Wet          | ACCESS-ESM1-5 |
| Hot-Dry          | IPSL-CM6A-LR  |
| Warm-Wet         | CMCC-ESM2     |
| Warm-Dry         | CNRM-CM6-1    |
| Median           | INM-CM5-0     |

This selection strategy captures the envelope of plausible futures without requiring all 21 models, and ensures that both temperature and precipitation extremes are represented.

## 6.2 Downscaling Protocol (Delta-Change Approach)

The GCM projections from NEX-GDDP-CMIP6 v2 are at ~25 km (0.25°) resolution. The delta-change method downscales these projections by computing how much future precipitation changes relative to a historical baseline within the same GCM (to preserve model-specific biases), then applying that change ratio to the observed high-resolution GRIDMET data.

**Three Time Periods:**

1. **Historical period (1990-2019)**: GCM modeled historical data at grid points (denominator for change factors)
2. **Future period (2035-2064)**: GCM future projections at grid points (numerator for change factors)
3. **Present baseline period (2006-2020)**: High-resolution GRIDMET observed rasters (30m) that get multiplied by change factors

**Key principle**: Change factors are computed from GCM historical to GCM future (not observed historical to GCM future) to keep GCM biases consistent. This ensures we're using the GCM's projection of change, not comparing biased GCM output directly to observations.

### Step 1: Compute seasonal means at the GCM grid scale

For each GCM, aggregate daily precipitation to seasonal totals (DJF, MAM, JJA, SON), then compute the multi-year mean of each season for:

- **Historical period**: 1990-2019 (GCM modeled historical at 6 grid points)
- **Future period**: 2035-2064 (GCM future projection at 6 grid points)

Note: GRIDMET observed data (2006-2020) is kept separate as the high-resolution baseline to which change factors will be applied.

### Step 2: Compute precipitation change factors

For each GCM and each season, compute the change factor at each GCM grid cell:

```
CF_precip = GCM_future (2035–2064) / GCM_historical (1990-2019)
```

- Both periods use the same 6 GCM grid points covering the watershed
- Historical baseline: GCM modeled historical data (1990-2019)
- Future projection: GCM future data (2035-2064) from the same model
- By comparing within the same model, GCM biases cancel out and only the projected change is captured
- A value of 1.15 means a 15% increase; 0.90 means a 10% decrease
- If the historical mean < 1e-6 kg/m²/s, set CF = 1.0 to avoid division instability

**Output:** 20 change factors (5 GCMs × 4 seasons), saved as CSV and GeoJSON

### Step 3: Apply change factors to GRIDMET baseline

**Interpolation Method**: Inverse Distance Weighting (IDW) with power=2

The change factors are interpolated from the sparse GCM grid (~6 points covering the watershed) to the 30m resolution using IDW. This method:

- Creates smooth gradients between GCM grid points
- Weights each pixel by all GCM points based on inverse square distance
- More physically realistic than nearest neighbor (avoids sharp Voronoi boundaries)
- Consistent with atmospheric processes that vary continuously in space

For each GCM and each season, multiply the present baseline GRIDMET raster (2006-2020 @ 30m) by the interpolated change factor:

```
precip_future_30m (2035-2064) = precip_baseline_30m (2006-2020) × CF_precip
```

**Output**: 20 rasters (5 GCMs × 4 seasons)

**File naming**: `precip_future_ACCESS-ESM1-5_2035-2064_mam_30m.tif`

---

## Implementation

### Scripts

All scripts are located in `data_processing/climate_models/precip_prediction/` and use the conda `geo` environment.

1. **1_compute_seasonal_means.py**
   - Computes GCM historical seasonal means (1990-2019) for each model
   - Computes GCM future seasonal means (2035-2064) for each model
   - Handles unit conversion: GCM (kg/m²/s → kg/m² daily)
   - Input: GCM CSVs from `data/climate_models/raw/daily_1990_2015/` and `daily_2015_2065/`
   - Output: Seasonal means in `data/climate_models/precip_prediction/1_seasonal_means/`
   - Note: GRIDMET baseline (2006-2020) rasters already exist at 30m resolution

2. **2_compute_change_factors.py**
   - Computes change factors (CF = GCM_future/GCM_historical) for each GCM and season
   - Keeps GCM biases consistent by comparing within the same model
   - Input: Seasonal means from step 1 in `data/climate_models/precip_prediction/1_seasonal_means/`
   - Output: Change factors in `data/climate_models/precip_prediction/2_change_factors/`

3. **3_apply_change_factors.py**
   - Applies change factors to present baseline (2006-2020) using IDW interpolation
   - Interpolates change factors from 6 GCM grid points to 30m resolution
   - Multiplies interpolated change factors by baseline rasters
   - Outputs use EPSG:32618 (WGS84 / UTM zone 18N)
   - Input: Change factors (GeoJSON) from `data/climate_models/precip_prediction/2_change_factors/` and GRIDMET baseline rasters (2006-2020) from `data/precipitation/processed/seasonal/`
   - Output: Future projection rasters (2035-2064) in `data/climate_models/precip_prediction/3_future_projections/`
   - Note: outputs generated with the previous 2015-2025 baseline are archived in `data/climate_models/old_baseline_dates/precip_prediction/`

**Utility Scripts:**

- **reproject_baseline_to_32618.py**: Reprojects baseline seasonal rasters from EPSG:26918 to EPSG:32618
- **reproject_future_to_32618.py**: Reprojects future projection rasters from EPSG:26918 to EPSG:32618

### Data Paths

```
ccsr-watershed-gis/
├── data/
│   ├── climate_models/
│   │   ├── raw/
│   │   │   ├── daily_1990_2015/   # GCM historical daily precipitation (CSV)
│   │   │   └── daily_2015_2065/   # GCM future daily precipitation (CSV)
│   │   └── precip_prediction/
│   │       ├── 1_seasonal_means/  # Step 1 output: seasonal means
│   │       ├── 2_change_factors/  # Step 2 output: change factors (CSV & GeoJSON)
│   │       └── 3_future_projections/  # Step 3 output: future precipitation rasters (30m)
│   └── precipitation/
│       └── processed/
│           └── seasonal/          # GRIDMET baseline rasters (30m, 2006-2020)
├── data_processing/
│   └── climate_models/
│       └── precip_prediction/     # This directory: processing scripts
```

### Results Summary

**Step 2: GCM Change Factors**

Change factors (future/historical) and percentage changes by model and season (averaged across 6 points):

| Model         | Quadrant | DJF         | MAM         | JJA        | SON         |
| ------------- | -------- | ----------- | ----------- | ---------- | ----------- |
| ACCESS-ESM1-5 | Hot-Wet  | 1.07 (+7%)  | 1.14 (+14%) | 1.00 (0%)  | 1.13 (+13%) |
| IPSL-CM6A-LR  | Hot-Dry  | 1.10 (+10%) | 1.02 (+2%)  | 0.98 (−2%) | 0.98 (−2%)  |
| CMCC-ESM2     | Warm-Wet | 1.14 (+14%) | 1.11 (+11%) | 1.03 (+3%) | 0.97 (−3%)  |
| CNRM-CM6-1    | Warm-Dry | 1.07 (+7%)  | 1.03 (+3%)  | 1.00 (+0%) | 0.99 (−1%)  |
| INM-CM5-0     | Median   | 1.05 (+5%)  | 1.02 (+2%)  | 1.07 (+7%) | 1.00 (+0%)  |

**Key Patterns:**

- All models show **winter (DJF) increases** (+5% to +14%)
- **Summer (JJA)** shows mixed signals: slight decreases for IPSL-CM6A-LR (−2%), increases for ACCESS-ESM1-5 (0%), CMCC-ESM2 (+3%), CNRM-CM6-1 (+0%), and INM-CM5-0 (+7%)
- **Fall (SON)** varies: −3% (CMCC-ESM2) to +13% (ACCESS-ESM1-5)
- **Spring (MAM)** shows consistent increases (+2% to +14%)

### Technical Notes

- **Coordinate Reference System**: All rasters use EPSG:32618 (WGS84 / UTM zone 18N)
- **Coordinate transformation**: GCM data (EPSG:4326) is transformed to EPSG:32618 before interpolation
- **IDW power parameter**: Set to 2 (inverse square distance) for balance between smoothness and local influence
- **Spatial coverage**: ~6 GCM grid points cover the watershed at ~25km resolution
- **Output resolution**: 30m to match GRIDMET baseline and watershed analysis requirements
