#!/usr/bin/env python3
"""
Create bivariate choropleth maps showing temperature and precipitation simultaneously.

Uses a 3x3 bivariate color scheme where:
- X-axis (columns): Temperature (low to high)
- Y-axis (rows): Precipitation (low to high)

Creates two maps:
1. GRIDMET baseline (2015-2025)
2. INM-CM5-0 future projection (2035-2064)

Both use the same legend for direct comparison.
"""

import numpy as np
import matplotlib.pyplot as plt
import rasterio
from pathlib import Path
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Configuration
DATA_DIR = Path(__file__).parent.parent.parent / 'data'

# Input files
GRIDMET_TEMP = DATA_DIR / 'temp' / 'processed' / 'seasonal' / 'temp_max_final_30m_2015-2025_jja.tif'
GRIDMET_PRECIP = DATA_DIR / 'precipitation' / 'processed' / 'seasonal' / 'precip_final_30m_2015-2025_jja.tif'

GCM_TEMP = DATA_DIR / 'climate_models' / 'temp_prediction' / '3_future_projections' / 'temp_max_future_INM-CM5-0_2035-2064_jja_30m.tif'
GCM_PRECIP = DATA_DIR / 'climate_models' / 'precip_prediction' / '3_future_projections' / 'precip_future_INM-CM5-0_2035-2064_jja_30m.tif'

# Output
OUTPUT_DIR = Path(__file__).parent


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


def create_bivariate_legend(temp_breaks, precip_breaks, output_path):
    """
    Create a standalone bivariate legend.
    
    Args:
        temp_breaks: Temperature class breaks
        precip_breaks: Precipitation class breaks
        output_path: Path to save legend image
    """
    fig = plt.figure(figsize=(5.5, 6))
    ax = fig.add_axes([0.15, 0.15, 0.7, 0.7])
    
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
    ax.text(1.5, 3.5, 'Bivariate Legend', ha='center', fontsize=13, transform=ax.transData)
    ax.text(1.5, 3.2, 'Temperature × Precipitation', ha='center', fontsize=11, transform=ax.transData)
    
    # Axis labels - with spacing
    ax.text(1.5, -0.4, 'Temperature (°C)', ha='center', fontsize=11, transform=ax.transData)
    ax.text(-0.5, 1.5, 'Precipitation (mm)', ha='center', fontsize=11, rotation=90, va='center', transform=ax.transData)
    
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


def determine_common_breaks(baseline_temp, baseline_precip, future_temp, future_precip):
    """
    Determine common class breaks for both datasets using quantiles.
    
    Args:
        baseline_temp: Baseline temperature array
        baseline_precip: Baseline precipitation array
        future_temp: Future temperature array
        future_precip: Future precipitation array
        
    Returns:
        tuple: (temp_breaks, precip_breaks)
    """
    # Combine both datasets to get overall range
    all_temp = np.concatenate([baseline_temp, future_temp])
    all_precip = np.concatenate([baseline_precip, future_precip])
    
    # Use quantiles for equal-area classification
    temp_breaks = np.percentile(all_temp, [0, 33.33, 66.67, 100])
    precip_breaks = np.percentile(all_precip, [0, 33.33, 66.67, 100])
    
    print("\nCommon class breaks (quantile-based):")
    print(f"  Temperature: {temp_breaks}")
    print(f"  Precipitation: {precip_breaks}")
    
    return temp_breaks, precip_breaks


def main():
    """Main execution function."""
    print("=" * 70)
    print("Bivariate Choropleth Maps: Temperature × Precipitation")
    print("Summer (JJA) Season")
    print("=" * 70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # First pass: load data to determine common breaks
    print("\n--- Loading data to determine common class breaks ---")
    
    with rasterio.open(GRIDMET_TEMP) as src:
        baseline_temp_data = src.read(1)
        temp_nodata = src.nodata
    
    with rasterio.open(GRIDMET_PRECIP) as src:
        baseline_precip_data = src.read(1)
        precip_nodata = src.nodata
    
    with rasterio.open(GCM_TEMP) as src:
        future_temp_data = src.read(1)
    
    with rasterio.open(GCM_PRECIP) as src:
        future_precip_data = src.read(1)
    
    # Get valid data
    baseline_valid = (baseline_temp_data != temp_nodata) & (baseline_precip_data != precip_nodata)
    future_valid = (future_temp_data != temp_nodata) & (future_precip_data != precip_nodata)
    
    baseline_temp_c = (baseline_temp_data[baseline_valid] - 273.15)
    baseline_precip = baseline_precip_data[baseline_valid]
    future_temp_c = (future_temp_data[future_valid] - 273.15)
    future_precip = future_precip_data[future_valid]
    
    # Determine common breaks
    temp_breaks, precip_breaks = determine_common_breaks(
        baseline_temp_c, baseline_precip, future_temp_c, future_precip
    )
    
    # Create legend
    print("\n--- Creating bivariate legend ---")
    create_bivariate_legend(temp_breaks, precip_breaks, 
                           OUTPUT_DIR / 'bivariate_legend.png')
    
    # Process baseline
    print("\n--- Processing GRIDMET Baseline ---")
    baseline_bivariate, extent, baseline_mask, baseline_temp_c, baseline_precip = load_and_classify_data(
        GRIDMET_TEMP, GRIDMET_PRECIP, temp_breaks, precip_breaks,
        'GRIDMET Baseline (2015-2025)'
    )
    
    create_bivariate_map(
        baseline_temp_c, baseline_precip, baseline_mask, temp_breaks, precip_breaks, extent,
        'GRIDMET Baseline (2015-2025)\n\nSummer (JJA)',
        OUTPUT_DIR / 'bivariate_map_baseline_jja.png',
        gridsize=80  # Number of hexagons
    )
    
    # Process future
    print("\n--- Processing INM-CM5-0 Future ---")
    future_bivariate, extent, future_mask, future_temp_c, future_precip = load_and_classify_data(
        GCM_TEMP, GCM_PRECIP, temp_breaks, precip_breaks,
        'INM-CM5-0 Future (2035-2064)'
    )
    
    create_bivariate_map(
        future_temp_c, future_precip, future_mask, temp_breaks, precip_breaks, extent,
        'INM-CM5-0 Future Projection (2035-2064)\n\nSummer (JJA)',
        OUTPUT_DIR / 'bivariate_map_future_INM-CM5-0_jja.png',
        gridsize=80  # Number of hexagons
    )
    
    print("\n" + "=" * 70)
    print("Bivariate maps complete!")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nFiles created:")
    print("  - bivariate_legend.png")
    print("  - bivariate_map_baseline_jja.png")
    print("  - bivariate_map_future_INM-CM5-0_jja.png")


if __name__ == '__main__':
    main()
