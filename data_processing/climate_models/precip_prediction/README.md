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

The GCM projections from NEX-GDDP-CMIP6 v2 are at ~25 km (0.25°) resolution. The delta-change method downscales these projections by computing how much future precipitation changes relative to a historical baseline, then applying that change ratio to the observed high-resolution GRIDMET data.

**Three Time Periods:**

1. **Historical period (1990-2019)**: GRIDMET observed data at GCM grid points, used as denominator for change factors
2. **Future period (2035-2064)**: GCM projections at grid points, used as numerator for change factors
3. **Present baseline period (2015-2025)**: High-resolution GRIDMET rasters (30m) that get multiplied by change factors

### Step 1: Compute seasonal means at the GCM grid scale

For each GCM, aggregate daily precipitation to seasonal totals (DJF, MAM, JJA, SON), then compute the multi-year mean of each season for:

- **Historical period**: 1990-2019 (GRIDMET at 6 grid points)
- **Future period**: 2035-2064 (GCM at 6 grid points)

### Step 2: Compute precipitation change factors

For each GCM and each season, compute the change factor at each GCM grid cell:

```
CF_precip = GCM_future (2035–2064) / GRIDMET_historical (1990-2019)
```

- Both periods use the same 6 GCM grid points covering the watershed
- Historical baseline: GRIDMET observed data (1990-2019) extracted at grid points
- Future projection: GCM data (2035-2064) at the same grid points
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

For each GCM and each season, multiply the present baseline GRIDMET raster (2015-2025 @ 30m) by the interpolated change factor:

```
precip_future_30m (2035-2064) = precip_baseline_30m (2015-2025) × CF_precip
```

**Output**: 20 rasters (5 GCMs × 4 seasons)

**File naming**: `precip_future_ACCESS-ESM1-5_2035-2064_mam_30m.tif`

---

## Implementation

### Scripts

All scripts are located in `data_processing/climate_models/precip_prediction/` and use the conda `geo` environment.

1. **1_compute_seasonal_means.py**
   - Downloads GRIDMET observed data (1990-2019) at the 6 GCM grid points
   - Computes GRIDMET historical baseline seasonal means (shared across all models)
   - Computes GCM future seasonal means (2035-2064) for each model
   - Handles unit conversion: GRIDMET (mm = kg/m²), GCM (kg/m²/s → kg/m² daily)
   - Input: GRIDMET NetCDF from northwestknowledge.net, GCM CSVs from `data/precipitation/raw/`
   - Output: Seasonal means in `data/precipitation/processed/seasonal/` and `data/climate_models/seasonal_means/`

2. **2_compute_change_factors.py**
   - Computes change factors (CF = GCM_future/GRIDMET_historical) for each GCM and season
   - Input: Seasonal means from step 1 in `data/climate_models/seasonal_means/`
   - Output: Change factors in `data/climate_models/change_factors/`

3. **3_apply_change_factors.py**
   - Applies change factors to present baseline (2015-2025) using IDW interpolation
   - Interpolates change factors from 6 GCM grid points to 30m resolution
   - Multiplies interpolated change factors by baseline rasters
   - Outputs use EPSG:32618 (WGS84 / UTM zone 18N)
   - Input: Change factors (GeoJSON) from `data/climate_models/change_factors/` and GRIDMET baseline rasters (2015-2025) from `data/precipitation/processed/seasonal/`
   - Output: Future projection rasters (2035-2064) in `data/climate_models/future_projections/`

**Utility Scripts:**

- **reproject_baseline_to_32618.py**: Reprojects baseline seasonal rasters from EPSG:26918 to EPSG:32618
- **reproject_future_to_32618.py**: Reprojects future projection rasters from EPSG:26918 to EPSG:32618

### Data Paths

```
ccsr-watershed-gis/
├── data/
│   ├── climate_models/
│   │   ├── daily/                 # Raw GCM daily precipitation (CSV)
│   │   ├── seasonal_means/        # Step 1 output: seasonal means
│   │   ├── change_factors/        # Step 2 output: change factors (CSV & GeoJSON)
│   │   └── future_projections/    # Step 3 output: future precipitation rasters (30m)
│   └── precipitation/
│       └── raw/                   # GRIDMET historical NetCDF files (4km)
├── data_processing/
│   └── climate_models/
│       └── precip_prediction/     # This directory: processing scripts
```

### Results Summary

**Step 1: GRIDMET Historical Baseline (1990-2019)**

Mean seasonal precipitation (kg/m² per season, averaged across 6 grid points):

| Season | DJF | MAM | JJA | SON |
| ------ | --- | --- | --- | --- |
| kg/m²  | 226 | 290 | 354 | 314 |

**Step 2 & 3: GCM Change Factors and Projections**

Change factors (future/historical) and percentage changes by model and season (averaged across 6 points):

| Model         | Quadrant | DJF         | MAM         | JJA        | SON         |
| ------------- | -------- | ----------- | ----------- | ---------- | ----------- |
| ACCESS-ESM1-5 | Hot-Wet  | 1.13 (+13%) | 1.17 (+17%) | 0.94 (−6%) | 1.07 (+7%)  |
| IPSL-CM6A-LR  | Hot-Dry  | 1.16 (+16%) | 1.04 (+4%)  | 0.92 (−8%) | 0.91 (−9%)  |
| CMCC-ESM2     | Warm-Wet | 1.29 (+29%) | 1.08 (+8%)  | 1.01 (+1%) | 0.90 (−10%) |
| CNRM-CM6-1    | Warm-Dry | 1.13 (+13%) | 1.08 (+8%)  | 0.91 (−9%) | 0.86 (−14%) |
| INM-CM5-0     | Median   | 1.15 (+15%) | 1.05 (+5%)  | 1.04 (+4%) | 0.97 (−3%)  |

**Key Patterns:**

- All models show **winter (DJF) increases** (+13% to +29%)
- Most models show **summer (JJA) decreases** (−9% to −6%), except CMCC-ESM2 (+1%) and INM-CM5-0 (+4%)
- **Fall (SON)** varies widely: −14% (CNRM-CM6-1) to +7% (ACCESS-ESM1-5)
- **Spring (MAM)** shows consistent modest increases (+4% to +17%)

### Technical Notes

- **Coordinate Reference System**: All rasters use EPSG:32618 (WGS84 / UTM zone 18N)
- **Coordinate transformation**: GCM data (EPSG:4326) is transformed to EPSG:32618 before interpolation
- **IDW power parameter**: Set to 2 (inverse square distance) for balance between smoothness and local influence
- **Spatial coverage**: ~6 GCM grid points cover the watershed at ~25km resolution
- **Output resolution**: 30m to match GRIDMET baseline and watershed analysis requirements
