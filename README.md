# Analytical Protocols for Hydrological Vulnerability Assessment and BMP Targeting in the Cannonsville Watershed

Shared repository for data processing, analysis, modeling, and visualization

The live site is deployed at https://elliemadsen.net/ccsr-watershed-gis/visualization/index.html

## Contributing

- Put raw and processed data files in `data/`
- Put scripts in `data_processing/`
- Put web viz in `visualization/`
- Document your work in README files within subdirectories
  - Include libraries, dependencies, methods, metadata (resolution, year, attributes, etc)
- Follow the established naming convention “variable_stage_resolution.ext"
- Use EPSG:32618 (WGS 84 / UTM zone 18N) for projection
- For large files, either add to LFS (.gitattributes) or .gitignore

---

## Directory Structure

```
ccsr-watershed-gis/
├── data/                      # All raw and processed data files
├── data_processing/           # All processing scripts
└── visualization/             # Web-based visualization tools
```

Where possible, use the same sub-directory structure for data and data processing. E.g. the script and README in `data_processing/precipitation/` refer to `data/precipitation`, and so on.

---

### `data/`

All data files (raw and processed), including rasters, shapefiles, CSVs, NetCDF, etc.

```
data/
├── CDL/                       # Cropland Data Layer
├── climate_models/            # Climate model outputs
├── DEM/                       # Digital Elevation Models
├── hydrography/               # National Hydrography Database
├── NLCD/                      # National Land Cover Database
├── precipitation/             # Precipitation data
├── runoff_coefficient/        # Runoff coefficient rasters
├── stream_proximity/          # Stream network and proximity data
├── sub-basins/                # Watershed boundary shapefiles
└── topographic_wetness_index/ # Topographic Wetness Index data

```

---

### `data_processing/`

Python scripts, Jupyter notebooks, and code that processes or transforms data.

```
data_processing/
├── climate_models/
│   ├── precip_prediction/     # Climate prediction pipeline scripts
│   └── web-viz/               # Scripts for web viz data prep
├── precipitation/             # GRIDMET data processing
└── stream_proximity/          # Flow accumulation, stream network and proximity analysis

```

---

### `visualization/`

HTML, JavaScript, and web-ready data files for interactive visualizations.

```
visualization/
├── index.html                 # Main visualization page
├── script.js                  # Three.js visualization code
├── watershed3d.py             # Helper script for 3D mesh generation
├── web_data/                  # Pre-processed JSON data for web
│   ├── prepare_dem.py         # Script: converts DEM to JSON
│   ├──  ...
│   ├── dem_data.json          # Web-ready elevation data
│   ├── ...
└── README.md
```

---
