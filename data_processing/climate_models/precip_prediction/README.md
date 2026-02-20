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

The GCM projections from NEX-GDDP-CMIP6 v2 are at ~25 km (0.25°) resolution. The delta-change method downscales these projections by computing how much future precipitation changes relative to the GCM's own historical baseline, then applying that change ratio to the observed high-resolution GRIDMET data. This preserves the observed spatial detail (e.g., local variability) while shifting magnitudes to reflect future conditions.

### Step 1: Compute seasonal means at the GCM grid scale

For each GCM, aggregate daily precipitation to seasonal totals (DJF, MAM, JJA, SON), then compute the multi-year mean of each season for:

- **Historical period**: 1990-2019
- **Future period**: 2035-2064

### Step 2: Compute precipitation change factors

For each GCM and each season, compute the change factor at each GCM grid cell:

```
CF_precip = mean_future_season (2035–2064) / mean_historical_season
```

- A value of 1.15 means a 15% increase
- A value of 0.90 means a 10% decrease
- If the historical mean for any cell-season is near-zero (< 0.1 mm), set CF = 1.0 to avoid division instability

This gives 20 change factors (5 GCMs × 4 seasons).

### Step 3: Apply change factors to observed GRIDMET baseline

**Interpolation Method**: Inverse Distance Weighting (IDW) with power=2

The change factors are interpolated from the sparse GCM grid (~6 points covering the watershed) to the 30m resolution using IDW. This method:

- Creates smooth gradients between GCM grid points
- Weights each pixel by all GCM points based on inverse square distance
- More physically realistic than nearest neighbor (avoids sharp Voronoi boundaries)
- Consistent with atmospheric processes that vary continuously in space

For each GCM and each season, multiply the observed GRIDMET baseline precipitation raster (1990-2019) by the change factor:

```
precip_future_30m = precip_baseline_30m × CF_precip
```

**Output**: 20 rasters (5 GCMs × 4 seasons)

**File naming**: `precip_future_ACCESS-ESM1-5_2035-2064_mam_30m.tif`

---

## Implementation

### Current Status

**Implemented Models**: 2 of 5

- ✓ ACCESS-ESM1-5 (Hot-Wet)
- ✓ IPSL-CM6A-LR (Hot-Dry)
- ⧗ CMCC-ESM2 (Warm-Wet) - pending data
- ⧗ CNRM-CM6-1 (Warm-Dry) - pending data
- ⧗ INM-CM5-0 (Median) - pending data

### Scripts

All scripts are located in `precipitation/climate_models/` and use the conda `geo` environment.

1. **1_compute_seasonal_means.py**
   - Downloads GRIDMET observed data (1990-2019) at the 6 GCM grid points
   - Computes GRIDMET historical baseline seasonal means (shared across all models)
   - Computes GCM future seasonal means (2035-2064) for each model
   - Handles unit conversion: GRIDMET (mm = kg/m²), GCM (kg/m²/s → kg/m² daily)
   - Input: GRIDMET NetCDF from northwestknowledge.net, GCM CSVs from `climate_models/data/daily/`
   - Output: Seasonal means in `climate_models/data/seasonal_means/`

2. **2_compute_change_factors.py**
   - Computes change factors (CF = GCM_future/GRIDMET_historical) for each GCM and season
   - Uses GRIDMET historical baseline (shared) and GCM-specific future projections
   - Outputs both CSV and GeoJSON formats
   - Input: Seasonal means from step 1
   - Output: Change factors in `climate_models/data/change_factors/`

3. **3_apply_change_factors.py**
   - Applies change factors to GRIDMET baseline using IDW interpolation
   - Input: Change factors (GeoJSON) and GRIDMET baseline (`precipitation/gridmet/processed/`)
   - Output: Future projection rasters in `future_projections/`

### Data Paths

```
ccsr-watershed-gis/
├── climate_models/data/           # Raw GCM data (shared resource)
│   ├── daily/                     # Daily GCM precipitation data
│   ├── seasonal_means/            # Computed seasonal means
│   └── change_factors/            # Change factors (CSV & GeoJSON)
├── precipitation/
│   ├── gridmet/processed/         # GRIDMET baseline rasters (30m)
│   └── climate_models/            # Processing scripts
│       └── future_projections/    # Output: future precipitation rasters
```

### Key Results

**ACCESS-ESM1-5** (Hot-Wet scenario):

- Winter (DJF): +13% increase
- Spring (MAM): +17% increase
- Summer (JJA): -6% decrease
- Fall (SON): +7% increase

**IPSL-CM6A-LR** (Hot-Dry scenario):

- Winter (DJF): +16% increase
- Spring (MAM): +4% increase
- Summer (JJA): -8% decrease
- Fall (SON): -9% decrease

### Technical Notes

- **Coordinate transformation**: GCM data (EPSG:4326) is transformed to match GRIDMET CRS (EPSG:26918) before interpolation
- **IDW power parameter**: Set to 2 (inverse square distance) for balance between smoothness and local influence
- **Spatial coverage**: ~6 GCM grid points cover the watershed at ~25km resolution
- **Output resolution**: 30m to match GRIDMET baseline and watershed analysis requirements
