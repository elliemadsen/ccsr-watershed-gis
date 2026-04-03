# Bivariate Temperature × Precipitation Choropleth Maps

Bivariate choropleth maps for the Cannonsville watershed showing seasonal
maximum temperature and total precipitation on a single 3×3 color grid.

## Color Scheme

A 3×3 bivariate palette where:

|         | Cool      | Moderate  | Warm      |
| ------- | --------- | --------- | --------- |
| **Wet** | `#5ac8c8` | `#5698b9` | `#3b4994` |
| **Mid** | `#ace4e4` | `#a5add3` | `#8c62aa` |
| **Dry** | `#e8e8e8` | `#dfb0d6` | `#be64ac` |

- **X-axis (columns):** Maximum temperature (°C) — low → high
- **Y-axis (rows):** Total precipitation (mm) — low → high

Temperature and precipitation are each divided into three equal-frequency
(tercile) bins per season, giving 9 classes.

## Data Sources

| Dataset                 | Period               | Resolution |
| ----------------------- | -------------------- | ---------- |
| GRIDMET baseline        | 2015–2025            | ~4 km      |
| ACCESS-ESM1-5 (Hot-Wet) | 2035–2064, SSP3-7.0  | ~4 km      |
| IPSL-CM6A-LR (Hot-Dry)  | 2035–2064, SSP3-7.0  | ~4 km      |
| CMCC-ESM2 (Warm-Wet)    | 2035–2064, SSP3-7.0  | ~4 km      |
| CNRM-CM6-1 (Warm-Dry)   | 2035–2064, SSP3-7.0  | ~4 km      |
| INM-CM5-0 (Median)      | 2035–2064, SSP3-7.0  | ~4 km      |
| Model Average           | mean of 5 GCMs above | ~4 km      |

All GCM data is bias-corrected and statistically downscaled (BCSD) from
CMIP6 via the MACA v2 dataset.

## Seasons

| Abbreviation | Months                               |
| ------------ | ------------------------------------ |
| DJF          | December, January, February (Winter) |
| MAM          | March, April, May (Spring)           |
| JJA          | June, July, August (Summer)          |
| SON          | September, October, November (Fall)  |

## Directory Structure

```
bivariate_temp_precip_map/
├── create_bivariate_maps.py   # Main processing script
├── README.md                  # This file
├── output/
│   ├── winter/                # Per-model maps + legend for DJF
│   ├── spring/                # Per-model maps + legend for MAM
│   ├── summer/                # Per-model maps + legend for JJA
│   ├── fall/                  # Per-model maps + legend for SON
│   └── aggregate/             # Model-mean maps (all seasons) + shared legend
└── (legacy root-level PNGs)   # Earlier single-season outputs
```

### Per-Season Outputs (`output/{season}/`)

Each season directory contains:

- `gridmet_{season}_bivariate_map_baseline.png` — GRIDMET baseline map
- `{model}_{season}_bivariate_map_future.png` — one per GCM
- `model_average_{season}_bivariate_map_future.png` — mean of 5 GCMs
- `legend_{season}.png` — bivariate legend with break values

### Aggregate Outputs (`output/aggregate/`)

Model-mean maps averaged across all 5 GCMs with a single unified legend:

- `model_mean_{season}.png` — one map per season
- `legend_aggregate.png` — shared legend for all aggregate maps

### Web Legend PNGs (`../web_data/`)

Compact 150-dpi legends for the 3D web visualization sidebar:

- `bivariate_legend_{djf,mam,jja,son}.png`

## Running the Script

```bash
conda activate geo
cd ccsr-watershed-gis/visualization/bivariate_temp_precip_map
python create_bivariate_maps.py
```

### Dependencies

- Python 3.9+
- numpy, matplotlib, rasterio, rioxarray, xarray
- Conda environment `geo` (or equivalent with the above packages)

### What the Script Does

1. **Loads** seasonal climate rasters (temperature & precipitation) for
   GRIDMET baseline and 5 GCMs from `data/climate_models/`.
2. **Computes** tercile breaks per season across the baseline.
3. **Classifies** each pixel into one of 9 bivariate classes.
4. **Renders** per-model choropleth PNGs with the watershed boundary overlay.
5. **Exports** JSON data files for the Three.js web visualization
   (`../web_data/bivariate_{model}_{season}.json`).
6. **Generates** compact PNG legends for the web sidebar.
7. **Creates** aggregate (model-mean) maps with a unified color scale.

## Web Integration

The JSON files are consumed by the Three.js 3D terrain viewer in
`../visualization/`. Each JSON contains:

- `data`: 2D array matching the DEM grid (2556×1688), class index 0–8
- `colormap`: dict mapping class index → `[r, g, b]` (0–1 floats)
- `temp_breaks`: 4 temperature bin edges
- `precip_breaks`: 4 precipitation bin edges
- `width`, `height`: grid dimensions

The web viewer loads these via the bivariate data layer selector, with
season and model controlled by sliders.
