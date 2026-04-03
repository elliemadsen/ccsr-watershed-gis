#!/usr/bin/env python3
"""
Create bivariate choropleth maps showing temperature and precipitation simultaneously.

Uses a 3x3 bivariate color scheme where:
- X-axis (columns): Temperature (low to high)
- Y-axis (rows): Precipitation (low to high)

Creates maps for:
1. GRIDMET baseline (2015-2025) - all seasons
2. All 5 GCM future projections (2035-2064) - all seasons:
   - ACCESS-ESM1-5
   - IPSL-CM6A-LR
   - CMCC-ESM2
   - CNRM-CM6-1
   - INM-CM5-0
3. Model averages across all seasons

All use the same legend for direct comparison within each season.
"""

import numpy as np
import matplotlib.pyplot as plt
import rasterio
import rioxarray as rxr
from pathlib import Path
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
import json
import os
import tempfile

# Configuration
DATA_DIR = Path(__file__).parent.parent.parent / 'data'

# Seasons to process
SEASONS = {
    'winter': ('djf', 'Winter (DJF)'),
    'spring': ('mam', 'Spring (MAM)'),
    'summer': ('jja', 'Summer (JJA)'),
    'fall': ('son', 'Fall (SON)')
}

# GCM models to process
GCM_MODELS = [
    'ACCESS-ESM1-5',
    'IPSL-CM6A-LR',
    'CMCC-ESM2',
    'CNRM-CM6-1',
    'INM-CM5-0'
]

# Model quadrant labels
MODEL_QUADRANTS = {
    'ACCESS-ESM1-5': 'Hot-Wet',
    'IPSL-CM6A-LR': 'Hot-Dry',
    'CMCC-ESM2': 'Warm-Wet',
    'CNRM-CM6-1': 'Warm-Dry',
    'INM-CM5-0': 'Median'
}

# Output
OUTPUT_DIR = Path(__file__).parent / 'output'
WEB_DATA_DIR = Path(__file__).parent.parent / 'web_data'


# Bivariate color scheme (3x3 grid)
# Rows = Precipitation (low to high, bottom to top)
# Columns = Temperature (low to high, left to right)
BIVARIATE_COLORS = [
    # Low precip (bottom row)
    ['#e8e8e8', '#dfb0d6', '#be64ac'],  # Low temp -> High temp
    # Medium precip (middle row)
    ['#ace4e4', '#a5add3', '#8c62aa'],
    # High precip (top row)
    ['#5ac8c8', '#5698b9', '#3b4994']
]


def create_bivariate_colormap():
    """
    Create a bivariate colormap for 3x3 classification.
    
    Returns:
        ListedColormap with 9 colors (plus transparent for nodata)
    """
    # Flatten the 2D color array to 1D (row-major order)
    colors_flat = []
    for row in BIVARIATE_COLORS:
        colors_flat.extend(row)
    
    # Add transparent color for nodata (index 9)
    colors_flat.append('#00000000')
    
    return ListedColormap(colors_flat)


def load_and_classify_data(temp_path, precip_path, temp_breaks, precip_breaks, label):
    """
    Load temperature and precipitation rasters and classify into bivariate categories.
    
    Args:
        temp_path: Path to temperature raster
        precip_path: Path to precipitation raster
        temp_breaks: Array of temperature class breaks [min, break1, break2, max]
        precip_breaks: Array of precipitation class breaks [min, break1, break2, max]
        label: Label for logging
        
    Returns:
        tuple: (bivariate_array, extent, valid_mask, temp_data, precip_data)
    """
    print(f"\nLoading and classifying {label}...")
    
    # Load temperature
    with rasterio.open(temp_path) as src:
        temp_data = src.read(1)
        temp_nodata = src.nodata
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        print(f"  Temperature: {temp_path.name}")
    
    # Load precipitation
    with rasterio.open(precip_path) as src:
        precip_data = src.read(1)
        precip_nodata = src.nodata
        print(f"  Precipitation: {precip_path.name}")
    
    # Convert temperature from Kelvin to Celsius
    temp_data_c = temp_data - 273.15
    
    # Create valid mask
    valid_mask = (temp_data != temp_nodata) & (precip_data != precip_nodata)
    
    # Initialize bivariate classification array
    bivariate = np.full(temp_data.shape, 9, dtype=np.int8)  # 9 = nodata
    
    # Classify temperature into 3 classes (0=low, 1=medium, 2=high)
    temp_class = np.zeros_like(temp_data_c, dtype=np.int8)
    temp_class[valid_mask] = np.digitize(temp_data_c[valid_mask], temp_breaks) - 1
    temp_class = np.clip(temp_class, 0, 2)
    
    # Classify precipitation into 3 classes (0=low, 1=medium, 2=high)
    precip_class = np.zeros_like(precip_data, dtype=np.int8)
    precip_class[valid_mask] = np.digitize(precip_data[valid_mask], precip_breaks) - 1
    precip_class = np.clip(precip_class, 0, 2)
    
    # Combine into bivariate index (row-major: precip_class * 3 + temp_class)
    bivariate[valid_mask] = precip_class[valid_mask] * 3 + temp_class[valid_mask]
    
    print(f"  Temperature range: {temp_data_c[valid_mask].min():.1f} to {temp_data_c[valid_mask].max():.1f} °C")
    print(f"  Precipitation range: {precip_data[valid_mask].min():.0f} to {precip_data[valid_mask].max():.0f} mm")
    print(f"  Breaks - Temp: {temp_breaks}, Precip: {precip_breaks}")
    
    # Print distribution
    print(f"  Class distribution:")
    for i in range(9):
        count = np.sum(bivariate == i)
        pct = 100 * count / np.sum(valid_mask)
        print(f"    Class {i}: {count:,} pixels ({pct:.1f}%)")
    
    return bivariate, extent, valid_mask, temp_data_c, precip_data


def create_bivariate_legend(temp_breaks, precip_breaks, output_path, season_name=None):
    """
    Create a standalone bivariate legend.
    
    Args:
        temp_breaks: Temperature class breaks
        precip_breaks: Precipitation class breaks
        output_path: Path to save legend image
        season_name: Optional season display name (e.g., 'Summer (JJA)')
    """
    fig = plt.figure(figsize=(5.5, 6.5))
    ax = fig.add_axes([0.15, 0.12, 0.7, 0.65])
    
    ax.set_xlim(-0.2, 3.2)
    ax.set_ylim(-0.8, 3.2)
    ax.set_aspect('equal')
    
    # Draw color squares
    for i in range(3):  # Temperature (columns)
        for j in range(3):  # Precipitation (rows)
            color = BIVARIATE_COLORS[j][i]
            rect = Rectangle((i, j), 1, 1, facecolor=color, edgecolor='black', linewidth=1.5)
            ax.add_patch(rect)
    
    # Title
    title_y = 3.7 if season_name else 3.5
    ax.text(1.5, title_y, 'Bivariate Legend', ha='center', fontsize=13, transform=ax.transData)
    ax.text(1.5, title_y - 0.3, 'Max Temperature × Total Precipitation', ha='center', fontsize=11, transform=ax.transData)
    if season_name:
        ax.text(1.5, title_y - 0.6, season_name, ha='center', fontsize=11, style='italic', transform=ax.transData)
    
    # Axis labels - with spacing
    ax.text(1.5, -0.4, 'Max Temperature (°C)', ha='center', fontsize=11, transform=ax.transData)
    ax.text(-0.5, 1.5, 'Total Precipitation (mm)', ha='center', fontsize=11, rotation=90, va='center', transform=ax.transData)
    
    # Tick labels
    temp_labels = [f'{temp_breaks[0]:.1f}', f'{temp_breaks[1]:.1f}', f'{temp_breaks[2]:.1f}', f'{temp_breaks[3]:.1f}']
    precip_labels = [f'{precip_breaks[0]:.0f}', f'{precip_breaks[1]:.0f}', f'{precip_breaks[2]:.0f}', f'{precip_breaks[3]:.0f}']
    
    for i, label in enumerate(temp_labels):
        ax.text(i, -0.15, label, ha='center', fontsize=9, transform=ax.transData)
    
    for j, label in enumerate(precip_labels):
        ax.text(-0.15, j, label, ha='right', va='center', fontsize=9, transform=ax.transData)
    
    # Directional labels
    ax.text(1.5, -0.65, 'Cooler ← → Warmer', ha='center', fontsize=9, style='italic', transform=ax.transData)
    ax.text(-0.65, 1.5, 'Drier ← → Wetter', ha='center', fontsize=9, style='italic', rotation=90, va='center', transform=ax.transData)
    
    # Turn off axis
    ax.axis('off')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved legend to: {output_path}")
    plt.close()


def create_web_legend_png(temp_breaks, precip_breaks, output_path, season_name=None):
    """
    Create a compact bivariate legend PNG for the web UI.
    Smaller and optimized for sidebar display (~250px wide).
    
    Args:
        temp_breaks: Temperature class breaks
        precip_breaks: Precipitation class breaks
        output_path: Path to save legend image
        season_name: Optional season display name
    """
    fig = plt.figure(figsize=(3.2, 3.8))
    ax = fig.add_axes([0.22, 0.10, 0.65, 0.62])
    
    ax.set_xlim(-0.2, 3.2)
    ax.set_ylim(-0.6, 3.2)
    ax.set_aspect('equal')
    
    # Draw color squares
    for i in range(3):
        for j in range(3):
            color = BIVARIATE_COLORS[j][i]
            rect = Rectangle((i, j), 1, 1, facecolor=color, edgecolor='white', linewidth=1.5)
            ax.add_patch(rect)
    
    # Title
    title_y = 3.5 if season_name else 3.3
    ax.text(1.5, title_y, 'Max Temp × Precipitation', ha='center', fontsize=9, 
            fontweight='normal', transform=ax.transData)
    if season_name:
        ax.text(1.5, title_y - 0.3, season_name, ha='center', fontsize=8, 
                style='italic', color='#666', transform=ax.transData)
    
    # Axis labels
    ax.text(1.5, -0.3, 'Max Temperature (°C)', ha='center', fontsize=8, color='#666', transform=ax.transData)
    ax.text(-0.4, 1.5, 'Precip (mm)', ha='center', fontsize=8, color='#666', rotation=90, va='center', transform=ax.transData)
    
    # Tick labels
    for i, val in enumerate(temp_breaks):
        ax.text(i, -0.12, f'{val:.1f}', ha='center', fontsize=7, color='#888', transform=ax.transData)
    
    for j, val in enumerate(precip_breaks):
        ax.text(-0.1, j, f'{val:.0f}', ha='right', va='center', fontsize=7, color='#888', transform=ax.transData)
    
    # Directional labels
    ax.text(1.5, -0.48, 'Cooler ← → Warmer', ha='center', fontsize=7, style='italic', color='#999', transform=ax.transData)
    ax.text(-0.55, 1.5, 'Drier ← → Wetter', ha='center', fontsize=7, style='italic', color='#999', 
            rotation=90, va='center', transform=ax.transData)
    
    ax.axis('off')
    fig.patch.set_alpha(0)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', transparent=False)
    print(f"  Saved web legend: {output_path}")
    plt.close()


def create_bivariate_map(temp_data, precip_data, valid_mask, temp_breaks, precip_breaks, 
                         extent, title, output_path, gridsize=50):
    """
    Create a bivariate choropleth map using hexagonal binning with matplotlib's hexbin.
    
    Args:
        temp_data: Temperature data array (in Celsius)
        precip_data: Precipitation data array
        valid_mask: Mask of valid pixels
        temp_breaks: Temperature class breaks
        precip_breaks: Precipitation class breaks
        extent: Map extent [left, right, bottom, top]
        title: Map title
        output_path: Path to save the map
        gridsize: Number of hexagons in x direction (default: 50)
    """
    from matplotlib.colors import ListedColormap
    
    # Extract valid data
    valid_temp = temp_data[valid_mask]
    valid_precip = precip_data[valid_mask]
    
    # Get pixel coordinates
    height, width = temp_data.shape
    rows, cols = np.where(valid_mask)
    
    # Convert pixel coordinates to map coordinates
    x_min, x_max, y_min, y_max = extent
    x_coords = x_min + (cols / width) * (x_max - x_min)
    y_coords = y_max - (rows / height) * (y_max - y_min)
    
    # Classify each pixel into bivariate category
    temp_class = np.digitize(valid_temp, temp_breaks) - 1
    temp_class = np.clip(temp_class, 0, 2)
    
    precip_class = np.digitize(valid_precip, precip_breaks) - 1
    precip_class = np.clip(precip_class, 0, 2)
    
    bivariate_class = precip_class * 3 + temp_class
    
    # Create custom colormap from bivariate colors
    # Flatten the 3x3 BIVARIATE_COLORS array to a list of 9 colors
    color_list = []
    for j in range(3):  # precip
        for i in range(3):  # temp
            color_list.append(BIVARIATE_COLORS[j][i])
    
    bivariate_cmap = ListedColormap(color_list)
    
    # Calculate proper figure size to maintain aspect ratio
    x_range = x_max - x_min
    y_range = y_max - y_min
    aspect_ratio = y_range / x_range
    fig_width = 12
    fig_height = fig_width * aspect_ratio
    
    # Create figure with proper aspect ratio
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    print(f"  Creating hexagonal bins...")
    
    # Add padding to extent to prevent edge cropping (5% padding)
    padding_x = x_range * 0.05
    padding_y = y_range * 0.05
    extent_padded = [x_min - padding_x, x_max + padding_x, 
                     y_min - padding_y, y_max + padding_y]
    
    # Use matplotlib's hexbin directly with custom colormap
    hb = ax.hexbin(x_coords, y_coords, C=bivariate_class, 
                   gridsize=gridsize, extent=extent_padded, 
                   reduce_C_function=lambda x: np.median(x),
                   cmap=bivariate_cmap,
                   vmin=0, vmax=8,
                   mincnt=1, 
                   edgecolors='white', 
                   linewidths=0.3)
    
    print(f"  Created {len(hb.get_offsets())} hexagonal bins")
    
    # Set limits with padding
    ax.set_xlim(extent_padded[0], extent_padded[1])
    ax.set_ylim(extent_padded[2], extent_padded[3])
    ax.set_aspect('equal', adjustable='box')
    
    # Title - not bold
    ax.set_title(title, fontsize=16, pad=15)
    
    # Remove axis labels and ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    # Remove the frame/spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Set background color
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved hexbin map to: {output_path}")
    plt.close()


def export_bivariate_web_json(temp_data_c, precip_data, valid_mask, temp_breaks, precip_breaks,
                               reference_tif_path, output_filename):
    """
    Export bivariate classification as JSON for the Three.js web visualization.
    
    Resamples the bivariate classification to match the DEM grid and outputs
    in the same format as cdl_data.json / nlcd_data.json.
    
    Args:
        temp_data_c: Temperature data in Celsius
        precip_data: Precipitation data
        valid_mask: Valid data mask
        temp_breaks: Temperature class breaks
        precip_breaks: Precipitation class breaks
        reference_tif_path: Path to a source TIF (for CRS/bounds info)
        output_filename: Output JSON filename (placed in web_data/)
    """
    print(f"\n  Exporting web JSON: {output_filename}")
    
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Classify into bivariate categories
    temp_class = np.zeros_like(temp_data_c, dtype=np.int8)
    temp_class[valid_mask] = np.digitize(temp_data_c[valid_mask], temp_breaks) - 1
    temp_class = np.clip(temp_class, 0, 2)
    
    precip_class = np.zeros_like(precip_data, dtype=np.int8)
    precip_class[valid_mask] = np.digitize(precip_data[valid_mask], precip_breaks) - 1
    precip_class = np.clip(precip_class, 0, 2)
    
    bivariate = np.full(temp_data_c.shape, -1, dtype=np.int8)
    bivariate[valid_mask] = precip_class[valid_mask] * 3 + temp_class[valid_mask]
    
    # Load DEM to get target grid
    dem_path = DATA_DIR / 'DEM' / 'tif' / 'DEM_UTM.tif'
    dem = rxr.open_rasterio(dem_path, masked=True).squeeze()
    dem_width = len(dem.x)
    dem_height = len(dem.y)
    dem_bounds = {
        'minX': float(dem.x.values.min()),
        'maxX': float(dem.x.values.max()),
        'minY': float(dem.y.values.min()),
        'maxY': float(dem.y.values.max())
    }
    
    # Write bivariate as a temporary GeoTIFF, then resample to DEM grid
    with rasterio.open(reference_tif_path) as src:
        profile = src.profile.copy()
    
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
    
    profile.update(dtype='int8', count=1, nodata=-1)
    with rasterio.open(tmp_path, 'w', **profile) as dst:
        dst.write(bivariate, 1)
    
    # Read back with rioxarray for resampling
    from rasterio.enums import Resampling
    biv_raster = rxr.open_rasterio(tmp_path, masked=False).squeeze()
    
    # Reproject to DEM CRS if needed
    if biv_raster.rio.crs != dem.rio.crs:
        biv_raster = biv_raster.rio.reproject(dem.rio.crs, resampling=0)
    
    # Clip to DEM extent
    biv_clipped = biv_raster.rio.clip_box(
        minx=dem_bounds['minX'], maxx=dem_bounds['maxX'],
        miny=dem_bounds['minY'], maxy=dem_bounds['maxY']
    )
    
    # Resample to exact DEM resolution
    biv_resampled = biv_clipped.rio.reproject(
        biv_clipped.rio.crs,
        shape=(dem_height, dem_width),
        resampling=Resampling.nearest
    )
    
    data = biv_resampled.values
    height, width = data.shape
    
    # Build colormap: class index -> [r, g, b] normalized
    colormap = {}
    for j in range(3):
        for i in range(3):
            idx = j * 3 + i
            hex_color = BIVARIATE_COLORS[j][i]
            r = int(hex_color[1:3], 16) / 255.0
            g = int(hex_color[3:5], 16) / 255.0
            b = int(hex_color[5:7], 16) / 255.0
            colormap[str(idx)] = [round(r, 4), round(g, 4), round(b, 4)]
    
    # Convert to list format
    json_data = []
    for row in data:
        json_data.append([None if val < 0 else int(val) for val in row])
    
    output = {
        'width': int(width),
        'height': int(height),
        'bounds': {
            'minX': float(biv_resampled.x.values[0]),
            'maxX': float(biv_resampled.x.values[-1]),
            'minY': float(biv_resampled.y.values[-1]),
            'maxY': float(biv_resampled.y.values[0])
        },
        'colormap': colormap,
        'temp_breaks': [float(b) for b in temp_breaks],
        'precip_breaks': [float(b) for b in precip_breaks],
        'data': json_data
    }
    
    output_path = WEB_DATA_DIR / output_filename
    with open(output_path, 'w') as f:
        json.dump(output, f)
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"  Saved web JSON: {output_path} ({file_size:.0f} KB)")
    
    # Cleanup temp file
    os.unlink(tmp_path)


def process_season(season_key, season_abbr, season_name):
    """
    Process all models for a specific season.
    
    Args:
        season_key: Season folder name (e.g., 'summer')
        season_abbr: Season abbreviation for filenames (e.g., 'jja')
        season_name: Display name for season (e.g., 'Summer (JJA)')
    """
    print("\n" + "=" * 70)
    print(f"Processing {season_name}")
    print("=" * 70)
    
    # Create season output directory
    season_dir = OUTPUT_DIR / season_key
    season_dir.mkdir(parents=True, exist_ok=True)
    
    # Input paths for baseline
    gridmet_temp = DATA_DIR / 'temp' / 'processed' / 'seasonal' / f'temp_max_final_30m_2015-2025_{season_abbr}.tif'
    gridmet_precip = DATA_DIR / 'precipitation' / 'processed' / 'seasonal' / f'precip_final_30m_2015-2025_{season_abbr}.tif'
    
    if not gridmet_temp.exists() or not gridmet_precip.exists():
        print(f"  Warning: Missing baseline data for {season_name}, skipping...")
        return
    
    # First pass: load all data to determine common breaks across ALL models
    print("\n--- Loading data to determine common class breaks ---")
    
    with rasterio.open(gridmet_temp) as src:
        baseline_temp_data = src.read(1)
        temp_nodata = src.nodata
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    
    with rasterio.open(gridmet_precip) as src:
        baseline_precip_data = src.read(1)
        precip_nodata = src.nodata
    
    # Get valid baseline data
    baseline_valid = (baseline_temp_data != temp_nodata) & (baseline_precip_data != precip_nodata)
    baseline_temp_c = (baseline_temp_data[baseline_valid] - 273.15)
    baseline_precip = baseline_precip_data[baseline_valid]
    
    # Collect all future model data
    all_future_temp = [baseline_temp_c]
    all_future_precip = [baseline_precip]
    
    # Store model data for averaging
    model_temp_arrays = []
    model_precip_arrays = []
    
    for model in GCM_MODELS:
        temp_path = DATA_DIR / 'climate_models' / 'temp_prediction' / '3_future_projections' / f'temp_max_future_{model}_2035-2064_{season_abbr}_30m.tif'
        precip_path = DATA_DIR / 'climate_models' / 'precip_prediction' / '3_future_projections' / f'precip_future_{model}_2035-2064_{season_abbr}_30m.tif'
        
        if not temp_path.exists() or not precip_path.exists():
            print(f"  Warning: Missing data for {model}, skipping from break calculation")
            continue
        
        with rasterio.open(temp_path) as src:
            temp_data = src.read(1)
        with rasterio.open(precip_path) as src:
            precip_data = src.read(1)
        
        valid = (temp_data != temp_nodata) & (precip_data != precip_nodata)
        all_future_temp.append(temp_data[valid] - 273.15)
        all_future_precip.append(precip_data[valid])
        
        # Store full arrays for averaging
        model_temp_arrays.append(temp_data)
        model_precip_arrays.append(precip_data)
    
    # Combine all data for break calculation
    combined_temp = np.concatenate(all_future_temp)
    combined_precip = np.concatenate(all_future_precip)
    
    # Determine common breaks
    temp_breaks = np.percentile(combined_temp, [0, 33.33, 66.67, 100])
    precip_breaks = np.percentile(combined_precip, [0, 33.33, 66.67, 100])
    
    print(f"\nCommon class breaks for {season_name}:")
    print(f"  Temperature: {temp_breaks}")
    print(f"  Precipitation: {precip_breaks}")
    
    # Create legend for this season
    print("\n--- Creating bivariate legend ---")
    create_bivariate_legend(temp_breaks, precip_breaks, 
                           season_dir / f'legend_{season_key}.png',
                           season_name=season_name)
    
    # Create web legend PNG for this season
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    create_web_legend_png(temp_breaks, precip_breaks,
                          WEB_DATA_DIR / f'bivariate_legend_{season_abbr}.png',
                          season_name=season_name)
    
    # Process baseline
    print("\n--- Processing GRIDMET Baseline ---")
    baseline_bivariate, extent, baseline_mask, baseline_temp_c_full, baseline_precip_full = load_and_classify_data(
        gridmet_temp, gridmet_precip, temp_breaks, precip_breaks,
        f'GRIDMET Baseline (2015-2025) - {season_name}'
    )
    
    create_bivariate_map(
        baseline_temp_c_full, baseline_precip_full, baseline_mask, temp_breaks, precip_breaks, extent,
        f'GRIDMET Baseline (2015-2025)\n{season_name}',
        season_dir / f'gridmet_{season_key}_bivariate_map_baseline.png',
        gridsize=80
    )
    
    # Export baseline web raster
    export_bivariate_web_json(
        baseline_temp_c_full, baseline_precip_full, baseline_mask,
        temp_breaks, precip_breaks, gridmet_temp,
        f'bivariate_gridmet_{season_abbr}.json'
    )
    
    # Process all future models
    for model in GCM_MODELS:
        quadrant = MODEL_QUADRANTS[model]
        print(f"\n--- Processing {model} ({quadrant}) Future ---")
        
        temp_path = DATA_DIR / 'climate_models' / 'temp_prediction' / '3_future_projections' / f'temp_max_future_{model}_2035-2064_{season_abbr}_30m.tif'
        precip_path = DATA_DIR / 'climate_models' / 'precip_prediction' / '3_future_projections' / f'precip_future_{model}_2035-2064_{season_abbr}_30m.tif'
        
        if not temp_path.exists() or not precip_path.exists():
            print(f"  Warning: Missing data files for {model}, skipping...")
            continue
        
        future_bivariate, extent, future_mask, future_temp_c, future_precip = load_and_classify_data(
            temp_path, precip_path, temp_breaks, precip_breaks,
            f'{model} ({quadrant}) Future (2035-2064) - {season_name}'
        )
        
        create_bivariate_map(
            future_temp_c, future_precip, future_mask, temp_breaks, precip_breaks, extent,
            f'{model} ({quadrant})\nFuture Projection (2035-2064)\n{season_name}',
            season_dir / f'{model}_{season_key}_bivariate_map_future.png',
            gridsize=80
        )
        
        # Export web raster
        export_bivariate_web_json(
            future_temp_c, future_precip, future_mask,
            temp_breaks, precip_breaks, temp_path,
            f'bivariate_{model}_{season_abbr}.json'
        )
    
    # Create model average if we have model data
    if model_temp_arrays:
        print(f"\n--- Creating model average for {season_name} ---")
        
        # Calculate average across models
        model_temp_stack = np.stack(model_temp_arrays)
        model_precip_stack = np.stack(model_precip_arrays)
        
        # Average only where all models have valid data
        avg_temp = np.mean(model_temp_stack, axis=0)
        avg_precip = np.mean(model_precip_stack, axis=0)
        
        # Create valid mask
        avg_valid = (avg_temp != temp_nodata) & (avg_precip != precip_nodata)
        avg_temp_c = avg_temp - 273.15
        
        print(f"  Average temperature range: {avg_temp_c[avg_valid].min():.1f} to {avg_temp_c[avg_valid].max():.1f} °C")
        print(f"  Average precipitation range: {avg_precip[avg_valid].min():.0f} to {avg_precip[avg_valid].max():.0f} mm")
        
        create_bivariate_map(
            avg_temp_c, avg_precip, avg_valid, temp_breaks, precip_breaks, extent,
            f'Model Average\nFuture Projection (2035-2064)\n{season_name}',
            season_dir / f'model_average_{season_key}_bivariate_map_future.png',
            gridsize=80
        )
        
        # Export web raster for model average
        export_bivariate_web_json(
            avg_temp_c, avg_precip, avg_valid,
            temp_breaks, precip_breaks, gridmet_temp,
            f'bivariate_model_average_{season_abbr}.json'
        )
    
    print(f"\n{season_name} complete!")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Bivariate Choropleth Maps: Temperature × Precipitation")
    print("All Seasons - Individual Models + Model Averages")
    print("=" * 70)
    
    # Create main output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each season
    for season_key, (season_abbr, season_name) in SEASONS.items():
        process_season(season_key, season_abbr, season_name)
    
    # Create aggregate model-mean maps
    create_aggregate_maps()
    
    print("\n" + "=" * 70)
    print("All bivariate maps complete!")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nStructure:")
    print("  output/")
    for season_key in SEASONS.keys():
        print(f"    {season_key}/")
        print(f"      legend_{season_key}.png")
        print(f"      gridmet_{season_key}_bivariate_map_baseline.png")
        for model in GCM_MODELS:
            print(f"      {model}_{season_key}_bivariate_map_future.png")
        print(f"      model_average_{season_key}_bivariate_map_future.png")
    print(f"    aggregate/")
    print(f"      legend_aggregate.png")
    for season_key in SEASONS.keys():
        print(f"      model_mean_{season_key}.png")


def create_aggregate_maps():
    """
    Create model-mean maps across all seasons with a single unified legend.
    
    Produces 4 seasonal maps (each the mean of all 5 GCMs) and 1 legend,
    all using the same class breaks for direct comparison.
    Output: output/aggregate/
    """
    print("\n" + "=" * 70)
    print("Creating Aggregate Model-Mean Maps")
    print("=" * 70)
    
    aggregate_dir = OUTPUT_DIR / 'aggregate'
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    
    # First pass: collect ALL model-average data across ALL seasons to compute unified breaks
    all_temp_values = []
    all_precip_values = []
    season_data = {}  # Store computed averages for second pass
    
    for season_key, (season_abbr, season_name) in SEASONS.items():
        print(f"\n  Loading model data for {season_name}...")
        
        # Need nodata value from baseline
        gridmet_temp = DATA_DIR / 'temp' / 'processed' / 'seasonal' / f'temp_max_final_30m_2015-2025_{season_abbr}.tif'
        with rasterio.open(gridmet_temp) as src:
            temp_nodata = src.nodata
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        
        gridmet_precip = DATA_DIR / 'precipitation' / 'processed' / 'seasonal' / f'precip_final_30m_2015-2025_{season_abbr}.tif'
        with rasterio.open(gridmet_precip) as src:
            precip_nodata = src.nodata
        
        model_temp_arrays = []
        model_precip_arrays = []
        
        for model in GCM_MODELS:
            temp_path = DATA_DIR / 'climate_models' / 'temp_prediction' / '3_future_projections' / f'temp_max_future_{model}_2035-2064_{season_abbr}_30m.tif'
            precip_path = DATA_DIR / 'climate_models' / 'precip_prediction' / '3_future_projections' / f'precip_future_{model}_2035-2064_{season_abbr}_30m.tif'
            
            if not temp_path.exists() or not precip_path.exists():
                print(f"    Warning: Missing data for {model}, skipping")
                continue
            
            with rasterio.open(temp_path) as src:
                model_temp_arrays.append(src.read(1))
            with rasterio.open(precip_path) as src:
                model_precip_arrays.append(src.read(1))
        
        if not model_temp_arrays:
            print(f"    No model data for {season_name}, skipping")
            continue
        
        # Compute model mean
        avg_temp = np.mean(np.stack(model_temp_arrays), axis=0)
        avg_precip = np.mean(np.stack(model_precip_arrays), axis=0)
        avg_valid = (avg_temp != temp_nodata) & (avg_precip != precip_nodata)
        avg_temp_c = avg_temp - 273.15
        
        season_data[season_key] = {
            'avg_temp_c': avg_temp_c,
            'avg_precip': avg_precip,
            'avg_valid': avg_valid,
            'extent': extent,
            'temp_nodata': temp_nodata,
            'precip_nodata': precip_nodata,
            'ref_tif': gridmet_temp
        }
        
        all_temp_values.append(avg_temp_c[avg_valid])
        all_precip_values.append(avg_precip[avg_valid])
        
        print(f"    {season_name}: {len(model_temp_arrays)} models averaged")
    
    if not all_temp_values:
        print("  No data available for aggregate maps!")
        return
    
    # Compute unified breaks across all seasons
    combined_temp = np.concatenate(all_temp_values)
    combined_precip = np.concatenate(all_precip_values)
    
    temp_breaks = np.percentile(combined_temp, [0, 33.33, 66.67, 100])
    precip_breaks = np.percentile(combined_precip, [0, 33.33, 66.67, 100])
    
    print(f"\n  Unified class breaks (all seasons):")
    print(f"    Temperature: {temp_breaks}")
    print(f"    Precipitation: {precip_breaks}")
    
    # Create single unified legend
    create_bivariate_legend(temp_breaks, precip_breaks,
                           aggregate_dir / 'legend_aggregate.png',
                           season_name='All Seasons — Model Mean (2035-2064)')
    
    # Create individual season maps
    for season_key, (season_abbr, season_name) in SEASONS.items():
        if season_key not in season_data:
            continue
        
        sd = season_data[season_key]
        print(f"\n  Creating aggregate map for {season_name}...")
        
        create_bivariate_map(
            sd['avg_temp_c'], sd['avg_precip'], sd['avg_valid'],
            temp_breaks, precip_breaks, sd['extent'],
            f'Model Mean (5 GCMs)\nFuture Projection (2035-2064)\n{season_name}',
            aggregate_dir / f'model_mean_{season_key}.png',
            gridsize=80
        )
    
    print(f"\n  Aggregate maps saved to: {aggregate_dir}")


if __name__ == '__main__':
    main()
